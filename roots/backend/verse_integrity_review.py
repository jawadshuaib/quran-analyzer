#!/usr/bin/env python3
"""Verse-integrity review via Ollama cloud.

For every verse, ask a strong multilingual model whether the (display) Arabic
text and the conventional English translation are the SAME verse — catching
data corruption like wrong/duplicated text, unstripped basmala, truncation,
or misaligned rows (the class of bug found on 95:1).

Resumable: results stream to reviews/verse_integrity.jsonl, one record per
batch; already-reviewed batches are skipped on restart. Mismatches are also
collected into reviews/verse_integrity_flags.json at the end.

Usage:
  OLLAMA_API_KEY=... python verse_integrity_review.py [--batch 20] [--workers 3] [--limit N]
"""
import argparse
import json
import os
import sqlite3
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

DB = os.path.join(os.path.dirname(__file__), "data", "quran.db")
OUT_DIR = os.path.join(os.path.dirname(__file__), "reviews")
OUT_JSONL = os.path.join(OUT_DIR, "verse_integrity.jsonl")
OUT_FLAGS = os.path.join(OUT_DIR, "verse_integrity_flags.json")
API_URL = "https://ollama.com/api/chat"
PRIMARY_MODEL = "qwen3.5:397b"
FALLBACK_MODEL = "deepseek-v3.1:671b"

SYSTEM = (
    "You are auditing a Quran database for DATA CORRUPTION. For each numbered item "
    "you get an Arabic verse text and an English translation that SHOULD be the same verse. "
    "Judge ONLY correspondence: is the Arabic plausibly the verse the English translates? "
    "Translation looseness, interpretive glosses, bracketed additions are all FINE. "
    "Flag MISMATCH only for real corruption: the Arabic is a different verse than the English, "
    "the Arabic contains a large extra chunk that the English lacks (e.g. an unstripped basmala "
    "before the verse), the Arabic is truncated/garbled/empty, or the pair is plainly misaligned. "
    'Reply with STRICT JSON only — a list like [{"n":1,"v":"OK"},{"n":2,"v":"MISMATCH","why":"..."}] '
    "with one entry per item, no markdown, no commentary."
)


def strip_bismillah(bis_text, text, ch, v):
    if v != 1 or ch == 1:
        return text
    skel = [c for c in bis_text if not unicodedata.combining(c) and not c.isspace()]
    ti = 0
    for i, chr_ in enumerate(text):
        if unicodedata.combining(chr_) or chr_.isspace():
            continue
        if ti < len(skel) and chr_ == skel[ti]:
            ti += 1
            if ti == len(skel):
                j = i + 1
                while j < len(text) and unicodedata.combining(text[j]):
                    j += 1
                return text[j:].strip()
        else:
            return text
    return text


def load_verses():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    bis = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=1 AND verse=1"
    ).fetchone()["text_uthmani"]
    rows = conn.execute(
        "SELECT v.chapter AS c, v.verse AS a, v.text_uthmani AS ar, t.text_en AS en "
        "FROM verses v LEFT JOIN translations t ON t.chapter=v.chapter AND t.verse=v.verse "
        "ORDER BY v.chapter, v.verse"
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        ar = strip_bismillah(bis, r["ar"] or "", r["c"], r["a"])
        out.append({"ref": f"{r['c']}:{r['a']}", "ar": ar, "en": (r["en"] or "").strip()})
    return out


def call_model(model, key, batch, timeout=180):
    lines = []
    for i, item in enumerate(batch, 1):
        lines.append(f"{i}. [{item['ref']}]\nARABIC: {item['ar']}\nENGLISH: {item['en']}")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "\n\n".join(lines)},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }
    resp = requests.post(
        API_URL,
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    content = resp.json()["message"]["content"].strip()
    # tolerate code fences
    if content.startswith("```"):
        content = content.strip("`")
        content = content[content.find("["):]
    start, end = content.find("["), content.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON list in reply: {content[:200]}")
    verdicts = json.loads(content[start:end + 1])
    if not isinstance(verdicts, list):
        raise ValueError("reply not a list")
    return verdicts


def review_batch(args_tuple):
    bi, batch, key = args_tuple
    last_err = None
    for attempt, model in enumerate([PRIMARY_MODEL, PRIMARY_MODEL, FALLBACK_MODEL], 1):
        try:
            verdicts = call_model(model, key, batch)
            flags = []
            seen = set()
            for v in verdicts:
                n = v.get("n")
                seen.add(n)
                if str(v.get("v", "")).upper() != "OK":
                    if 1 <= (n or 0) <= len(batch):
                        flags.append({
                            "ref": batch[n - 1]["ref"],
                            "why": v.get("why", ""),
                        })
            missing = [i for i in range(1, len(batch) + 1) if i not in seen]
            return {
                "batch": bi,
                "refs": [b["ref"] for b in batch],
                "model": model,
                "flags": flags,
                "missing_verdicts": missing,
                "ok": True,
            }
        except Exception as e:  # noqa
            last_err = str(e)[:200]
            time.sleep(2 * attempt)
    return {"batch": bi, "refs": [b["ref"] for b in batch], "ok": False, "error": last_err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="review only first N batches (smoke test)")
    args = ap.parse_args()

    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        sys.exit("OLLAMA_API_KEY not set")

    os.makedirs(OUT_DIR, exist_ok=True)
    verses = load_verses()
    batches = [verses[i:i + args.batch] for i in range(0, len(verses), args.batch)]
    if args.limit:
        batches = batches[:args.limit]

    done = set()
    if os.path.exists(OUT_JSONL):
        with open(OUT_JSONL) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if rec.get("ok"):
                        done.add(rec["batch"])
                except Exception:
                    pass
    todo = [(i, b, key) for i, b in enumerate(batches) if i not in done]
    print(f"verses={len(verses)} batches={len(batches)} done={len(done)} todo={len(todo)}", flush=True)

    t0 = time.time()
    n_flags = 0
    with open(OUT_JSONL, "a") as out, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(review_batch, t): t[0] for t in todo}
        completed = 0
        for fut in as_completed(futures):
            rec = fut.result()
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            completed += 1
            if rec.get("ok"):
                n_flags += len(rec.get("flags", []))
                if rec.get("flags"):
                    print(f"[{completed}/{len(todo)}] batch {rec['batch']} FLAGS: {rec['flags']}", flush=True)
            else:
                print(f"[{completed}/{len(todo)}] batch {rec['batch']} FAILED: {rec.get('error')}", flush=True)
            if completed % 20 == 0:
                rate = completed / max(1, time.time() - t0)
                print(f"[{completed}/{len(todo)}] {rate*60:.1f} batches/min, flags so far: {n_flags}", flush=True)

    # collate
    all_flags, failed = [], []
    with open(OUT_JSONL) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("ok"):
                all_flags.extend(rec.get("flags", []))
            else:
                failed.append(rec.get("batch"))
    with open(OUT_FLAGS, "w") as f:
        json.dump({"flags": all_flags, "failed_batches": sorted(set(failed))}, f, ensure_ascii=False, indent=2)
    print(f"DONE: {len(all_flags)} flagged verses, {len(set(failed))} failed batches -> {OUT_FLAGS}", flush=True)


if __name__ == "__main__":
    main()
