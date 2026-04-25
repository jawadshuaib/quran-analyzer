"""Revise ai_word_meanings entries for ritualistic-narrowed roots so that
meaning_short / meaning_detailed / preferred_translation align with the
canonical Qur'an-only methodology.

Two modes:
  --hard-cases-only   Apply transliteration treatment to the 27 hard
                      cases (35 word entries). Fast, cheap, surgical.
  --all-surveyed      Apply canonical or transliteration to every word
                      whose root is in the 13 surveyed list. ~1,371
                      entries, ~$4 in Sonnet calls, ~75 min.

For each entry we send Claude:
  - the current meaning_short / meaning_detailed / preferred_translation
  - the root + canonical
  - hard-case info if applicable

Original values are preserved in *_original backup columns so changes
can be reverted if needed.

Usage:
    python revise_word_meanings.py --hard-cases-only --dry-run
    python revise_word_meanings.py --hard-cases-only
    python revise_word_meanings.py --all-surveyed
    python revise_word_meanings.py --verse "55:6" --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

import requests

from app import get_db, _get_claude_api_key

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"

SURVEYED_ROOTS = ["Slw", "zkw", "Swm", "Hjj", "sjd", "rkE", "snn", "nsk",
                  "qwm", "$Er", "Emr", "*kr", "Thr"]

SYSTEM_PROMPT = """\
You are revising a per-word meaning entry in a Qur'an study app. The
word's root has been surveyed across the corpus and given a canonical
abstract English rendering. Your job is to update the three fields of
this word entry — meaning_short, meaning_detailed, preferred_translation
— so they reflect the canonical (or, for hard-case verses, the Arabic
transliteration) instead of the conventional ritualistic English.

Two cases:

CASE A — HARD CASE VERSE (transliteration treatment):
  - meaning_short: lead with the transliteration as the headline,
    optionally followed by a brief gloss in canonical English. Format:
        "yasjudāni — they both submit"
        "yuṣallūna — the divine connecting"
        "qayyūm — the Self-Standing"
  - meaning_detailed: rewrite the analysis to use the canonical
    semantic field instead of ritualistic terms. Preserve all
    grammatical observations (verb form, mood, syntactic role, dual,
    plural, etc.). Add a short note at the end explaining why this
    verse uses transliteration: "Conventional English would have to
    invent a word here..." or similar — the existing translation_note
    on the root captures the right tone, mirror it briefly.
  - preferred_translation: the bare transliteration (e.g. "yasjudāni",
    "ḥajj", "qayyūm").

CASE B — NORMAL VERSE (canonical treatment):
  - meaning_short: the canonical English with brief context. Format:
        "submit (in dual)" or "submission" or "they submit"
    Whatever fits the morphology naturally.
  - meaning_detailed: rewrite to use the canonical instead of the
    ritualistic English. Preserve grammatical analysis exactly. Use
    the canonical's word family (submit/submitting/submission for sjd,
    connect/connection for Slw, etc.). Do not invent new analytical
    content; just swap the vocabulary.
  - preferred_translation: the canonical word in the form that fits
    this word's morphology (e.g. "submit", "submitting", "submission",
    "they submit").

CRITICAL preservation rules:
  - Keep all grammatical/morphological observations (root identification,
    verb forms, agreement, syntactic role).
  - Don't change the semantic substance — only swap ritualistic English
    for canonical/transliteration.
  - Keep meaning_detailed roughly the same length; this is minimal-edit.

Output ONLY a single JSON object:

{
  "meaning_short": "...",
  "meaning_detailed": "...",
  "preferred_translation": "..."
}

No preamble, no commentary outside the JSON.
"""


def parse_verse_arg(spec: str) -> tuple[int, int] | None:
    if not spec:
        return None
    m = re.match(r"^(\d+):(\d+)$", spec.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def load_hard_cases_index(conn) -> dict[tuple[str, int, int], dict]:
    """Map (root_bw, chapter, verse) → hard case info."""
    index = {}
    for r in conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, hard_cases_json "
        "FROM term_surveys WHERE hard_cases_json IS NOT NULL"
    ):
        try:
            cases = json.loads(r["hard_cases_json"]) or []
        except Exception:
            continue
        for hc in cases:
            ref = hc.get("ref", "")
            m = re.match(r"^(\d+):(\d+)$", ref)
            if not m:
                continue
            ch, vs = int(m.group(1)), int(m.group(2))
            index[(r["root_buckwalter"], ch, vs)] = {
                "root_buckwalter": r["root_buckwalter"],
                "root_arabic": r["root_arabic"],
                "canonical_english": r["canonical_english"],
                "arabic_word": hc.get("arabic_word"),
                "transliteration": hc.get("transliteration"),
                "reason": hc.get("reason"),
            }
    return index


def load_canonical_index(conn) -> dict[str, dict]:
    out = {}
    for r in conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, translation_note "
        "FROM term_surveys"
    ):
        out[r["root_buckwalter"]] = dict(r)
    return out


def collect_targets(conn, mode: str, verse_filter: tuple[int, int] | None,
                    force: bool) -> list[dict]:
    """Return word_meanings rows that should be revised, joined with
    morphology so we know each word's root."""
    sql = """
        SELECT w.id, w.chapter, w.verse, w.word_pos,
               w.meaning_short, w.meaning_detailed, w.preferred_translation,
               w.meaning_short_original, w.preferred_source,
               m.root_buckwalter, m.root_arabic, m.form_arabic, m.pos, m.tag
        FROM ai_word_meanings w
        JOIN morphology m ON m.chapter = w.chapter
                          AND m.verse = w.verse
                          AND m.word_pos = w.word_pos
        WHERE m.root_buckwalter IS NOT NULL
    """
    params: list = []
    if mode == "hard-cases-only":
        # only verses that appear in any hard_cases_json
        placeholders = ",".join(["?"] * len(SURVEYED_ROOTS))
        sql += f" AND m.root_buckwalter IN ({placeholders})"
        params.extend(SURVEYED_ROOTS)
    elif mode == "all-surveyed":
        placeholders = ",".join(["?"] * len(SURVEYED_ROOTS))
        sql += f" AND m.root_buckwalter IN ({placeholders})"
        params.extend(SURVEYED_ROOTS)
    if verse_filter:
        sql += " AND w.chapter = ? AND w.verse = ?"
        params.extend(list(verse_filter))
    sql += " GROUP BY w.id ORDER BY w.chapter, w.verse, w.word_pos"

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

    # If hard-cases-only, intersect with hard case index
    if mode == "hard-cases-only":
        hc_index = load_hard_cases_index(conn)
        rows = [r for r in rows
                if (r["root_buckwalter"], r["chapter"], r["verse"]) in hc_index]

    # Skip already-revised unless --force
    if not force:
        rows = [r for r in rows if not r.get("meaning_short_original")]
    return rows


def build_prompt(row: dict, hc: dict | None, canon: dict) -> str:
    parts = [
        f"WORD: {row['chapter']}:{row['verse']} pos={row['word_pos']}",
        f"Arabic word: {row.get('form_arabic', '?')}",
        f"Root: {canon['root_arabic']} ({canon['root_buckwalter']})",
        f"Canonical English: '{canon['canonical_english']}'",
        f"POS: {row.get('pos', '?')}, Tag: {row.get('tag', '?')}",
        "",
    ]
    if hc:
        parts += [
            "*** THIS IS A HARD-CASE VERSE — use transliteration treatment. ***",
            f"Hard-case Arabic word: {hc['arabic_word']}",
            f"Transliteration to use: {hc['transliteration']}",
            f"Why hard: {hc['reason']}",
            "",
        ]
    else:
        parts += [
            "Normal verse — use canonical treatment (canonical word family).",
            f"Translation note context (apply tone, don't quote): {canon.get('translation_note', '')[:300]}",
            "",
        ]
    parts += [
        "CURRENT FIELDS (revise these):",
        f"meaning_short:        {row.get('meaning_short') or ''}",
        f"meaning_detailed:     {row.get('meaning_detailed') or ''}",
        f"preferred_translation:{row.get('preferred_translation') or ''}",
        "",
        "Return the revised JSON only.",
    ]
    return "\n".join(parts)


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                ANTHROPIC_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=60,
            )
        except requests.RequestException as e:
            last_err = f"req: {e}"
        else:
            if resp.status_code == 200:
                return "".join(b.get("text", "") for b in resp.json().get("content", [])
                               if b.get("type") == "text").strip()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude failed: {last_err}")


def parse_response(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON: {text[:300]!r}")
    return json.loads(m.group())


def revise_one(conn, row: dict, hc: dict | None, canon: dict,
               model: str, api_key: str, dry_run: bool) -> str:
    prompt = build_prompt(row, hc, canon)
    ref = f"{row['chapter']}:{row['verse']}/p{row['word_pos']}"

    if dry_run:
        print(f"\n--- {ref} {'[HARD]' if hc else ''} ---")
        print(prompt[:800])
        return "dry-run"

    try:
        raw = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
        verdict = parse_response(raw)
    except Exception as e:
        print(f"  {ref} ERROR: {e}", file=sys.stderr)
        return "error"

    new_short = (verdict.get("meaning_short") or "").strip()
    new_detailed = (verdict.get("meaning_detailed") or "").strip()
    new_preferred = (verdict.get("preferred_translation") or "").strip()
    if not (new_short and new_detailed and new_preferred):
        print(f"  {ref} ERROR: missing fields in response", file=sys.stderr)
        return "error"

    # Save originals on first revision
    if not row.get("meaning_short_original"):
        conn.execute(
            "UPDATE ai_word_meanings SET "
            "  meaning_short_original = ?, "
            "  meaning_detailed_original = ?, "
            "  preferred_translation_original = ? "
            "WHERE id = ?",
            (
                row.get("meaning_short"),
                row.get("meaning_detailed"),
                row.get("preferred_translation"),
                row["id"],
            ),
        )
    conn.execute(
        "UPDATE ai_word_meanings SET "
        "  meaning_short = ?, meaning_detailed = ?, "
        "  preferred_translation = ? "
        "WHERE id = ?",
        (new_short, new_detailed, new_preferred, row["id"]),
    )
    conn.commit()

    print(f"  → {ref} {'[HARD]' if hc else ''}")
    print(f"    short: {row.get('meaning_short', '')[:60]} → {new_short[:60]}")
    return "revised"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--hard-cases-only", action="store_true")
    p.add_argument("--all-surveyed", action="store_true")
    p.add_argument("--verse", help="single verse 'X:Y'")
    p.add_argument("--limit", type=int)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not (args.hard_cases_only or args.all_surveyed or args.verse):
        print("ERROR: pass --hard-cases-only, --all-surveyed, or --verse",
              file=sys.stderr)
        return 1

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    conn = get_db()
    conn.row_factory = __import__("sqlite3").Row

    mode = "hard-cases-only" if args.hard_cases_only else (
        "all-surveyed" if args.all_surveyed else "verse"
    )
    verse_filter = parse_verse_arg(args.verse) if args.verse else None
    rows = collect_targets(conn, mode, verse_filter, args.force)
    if args.limit:
        rows = rows[: args.limit]

    print(f"Revising {len(rows)} word_meanings entries (mode={mode})")

    hc_index = load_hard_cases_index(conn)
    canon_index = load_canonical_index(conn)

    stats = {"revised": 0, "error": 0, "dry-run": 0}
    for row in rows:
        canon = canon_index.get(row["root_buckwalter"])
        if not canon:
            continue
        hc_key = (row["root_buckwalter"], row["chapter"], row["verse"])
        hc = hc_index.get(hc_key)
        result = revise_one(conn, row, hc, canon, args.model, api_key, args.dry_run)
        stats[result] = stats.get(result, 0) + 1

    print(f"\n=== Summary ({mode}) ===")
    for k, v in stats.items():
        if v:
            print(f"  {k}: {v}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
