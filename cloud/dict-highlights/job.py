#!/usr/bin/env python3
"""Highlights for the dictionary entries that open first on al-nuqta root pages.

  python3 job.py status          batches done / left
  python3 job.py next [K]        the next K batch ids without an output file (default 4)
  python3 job.py show BATCH      the batch's entries, line-numbered, with their context
  python3 job.py check BATCH     validate out/BATCH.json against the rules (exit 1 on errors)
  python3 job.py check all       validate every output file
  python3 job.py merge           write highlights.jsonl from every valid batch

Read TASK.md first. Everything here is deterministic; the checker is the judge of
whether a batch is acceptable.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "entries.csv")
OUT = os.path.join(HERE, "out")
LIMITS = {"core": 2, "quran": 4, "early": 2, "later": 3}
MAX_TOTAL = 10
MIN_LEN, MAX_LEN = 8, 300
NOTE_MAX = 100
COVER_SHARE, COVER_FLOOR = 0.20, 160      # highlighted characters (core+quran+early) allowed
LINE_MARKER = re.compile(r"^(\s*(?:[-*]|\d+\.|#{2,3})\s+)")
MARKUP_RUN = re.compile(r"\*\*[^*]+\*\*|\*[^*\n]+\*|\[\[[^\]]*\]\]")

csv.field_size_limit(10 ** 8)


def load():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_batch(rows):
    out = {}
    for r in rows:
        out.setdefault(r["batch"], []).append(r)
    return dict(sorted(out.items()))


def cmd_status(rows):
    b = by_batch(rows)
    done = [k for k in b if os.path.exists(os.path.join(OUT, k + ".json")) and not errors_for(k, b[k])]
    bad = [k for k in b if os.path.exists(os.path.join(OUT, k + ".json")) and k not in done]
    print(f"{len(done)}/{len(b)} batches valid ({sum(len(b[k]) for k in done)}/{len(rows)} entries); "
          f"{len(bad)} with errors: {' '.join(bad) or '-'}; {len(b) - len(done) - len(bad)} not started")


def cmd_next(rows, k):
    b = by_batch(rows)
    todo = [x for x in b if not os.path.exists(os.path.join(OUT, x + ".json"))]
    print(" ".join(todo[:k]) or "(none left)")


def cmd_show(rows, batch):
    b = by_batch(rows)
    if batch not in b:
        sys.exit(f"no batch {batch}")
    print(f"BATCH {batch}: {len(b[batch])} entries. Write out/{batch}.json (see TASK.md, Part B).\n")
    for r in b[batch]:
        print("=" * 100)
        print(f"entry_id {r['entry_id']} | root {r['root_ar']} ({r['root_letters']}, {r['root_bw']}) | {r['dictionary']}")
        print(f"The Qur'an uses this root {r['quran_occurrences']} times: {r['quran_words'] or '(no word list)'}")
        print(f"Poets the entry names (era): {r['poets_named'] or 'none'}")
        print("-" * 100)
        for i, line in enumerate(r["text"].split("\n"), 1):
            print(f"L{i}: {line}")
        print()


def errors_for(batch, entries):
    path = os.path.join(OUT, batch + ".json")
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"{batch}: cannot read {path}: {e}"]
    errs = []
    if not isinstance(data, dict) or data.get("batch") != batch or not isinstance(data.get("entries"), list):
        return [f'{batch}: the file must be {{"batch": "{batch}", "entries": [...]}}']
    want = {int(r["entry_id"]): r for r in entries}
    seen = set()
    for item in data["entries"]:
        eid = item.get("entry_id") if isinstance(item, dict) else None
        if eid not in want:
            errs.append(f"{batch}: entry_id {eid!r} is not in this batch")
            continue
        if eid in seen:
            errs.append(f"{batch}: entry_id {eid} appears twice")
        seen.add(eid)
        errs += entry_errors(want[eid], item.get("highlights"))
    for eid in want:
        if eid not in seen:
            errs.append(f"{batch}: entry_id {eid} is missing (give it \"highlights\": [] if nothing qualifies)")
    return errs


def entry_errors(row, hls):
    eid = row["entry_id"]
    text = row["text"]
    lines = text.split("\n")
    if not isinstance(hls, list):
        return [f"entry {eid}: \"highlights\" must be a list"]
    errs, spans, counts, cover = [], [], {}, 0
    for n, h in enumerate(hls, 1):
        tag = f"entry {eid} highlight {n}"
        if not isinstance(h, dict):
            errs.append(f"{tag}: must be an object"); continue
        kind, t, note = h.get("kind"), h.get("text"), h.get("note", "")
        if kind not in LIMITS:
            errs.append(f"{tag}: kind must be one of {sorted(LIMITS)}"); continue
        counts[kind] = counts.get(kind, 0) + 1
        if not isinstance(t, str) or not (MIN_LEN <= len(t) <= MAX_LEN):
            errs.append(f"{tag}: text must be {MIN_LEN}-{MAX_LEN} characters"); continue
        if t != t.strip():
            errs.append(f"{tag}: text has leading/trailing spaces"); continue
        if "\n" in t:
            errs.append(f"{tag}: text spans more than one line"); continue
        if not isinstance(note, str) or len(note) > NOTE_MAX:
            errs.append(f"{tag}: note must be a string of at most {NOTE_MAX} characters"); continue
        if kind in ("early", "later") and not note.strip():
            errs.append(f"{tag}: {kind} needs a note (who or what the source is)"); continue
        hits = [(li, m.start()) for li, line in enumerate(lines) for m in re.finditer(re.escape(t), line)]
        if not hits:
            errs.append(f"{tag}: text is not an exact substring of any single line: {t[:70]!r}"); continue
        if len(hits) > 1:
            errs.append(f"{tag}: text occurs {len(hits)} times; lengthen it so it is unique: {t[:70]!r}"); continue
        li, start = hits[0]
        line, end = lines[li], hits[0][1] + len(t)
        mk = LINE_MARKER.match(line)
        if mk and start < mk.end():
            errs.append(f"{tag}: starts inside the line's list/heading marker; begin after {mk.group(1)!r}")
        for m in MARKUP_RUN.finditer(line):
            inside = start <= m.start() and m.end() <= end
            outside = m.end() <= start or end <= m.start()
            if not (inside or outside):
                errs.append(f"{tag}: cuts through the markup {m.group(0)[:40]!r}; include all of it or none"); break
        offset = sum(len(x) + 1 for x in lines[:li]) + start
        spans.append((offset, offset + len(t), n))
        if kind != "later":
            cover += len(t)
    for kind, n in counts.items():
        if n > LIMITS[kind]:
            errs.append(f"entry {eid}: {n} {kind} highlights (at most {LIMITS[kind]})")
    if len(hls) > MAX_TOTAL:
        errs.append(f"entry {eid}: {len(hls)} highlights (at most {MAX_TOTAL})")
    spans.sort()
    for (a1, b1, n1), (a2, b2, n2) in zip(spans, spans[1:]):
        if a2 < b1:
            errs.append(f"entry {eid}: highlights {n1} and {n2} overlap")
    allowed = max(COVER_SHARE * len(text), COVER_FLOOR)
    if cover > allowed:
        errs.append(f"entry {eid}: highlights cover {cover} characters; at most {int(allowed)} for this entry")
    return errs


def cmd_check(rows, which):
    b = by_batch(rows)
    targets = [k for k in b if os.path.exists(os.path.join(OUT, k + ".json"))] if which == "all" else [which]
    total = 0
    for k in targets:
        if k not in b:
            sys.exit(f"no batch {k}")
        errs = errors_for(k, b[k])
        total += len(errs)
        for e in errs:
            print(e)
        if not errs:
            data = json.load(open(os.path.join(OUT, k + ".json"), encoding="utf-8"))
            n = sum(len(x["highlights"]) for x in data["entries"])
            print(f"{k}: OK ({len(data['entries'])} entries, {n} highlights)")
    sys.exit(1 if total else 0)


def cmd_merge(rows):
    b = by_batch(rows)
    out, skipped = [], []
    for k, entries in b.items():
        if not os.path.exists(os.path.join(OUT, k + ".json")) or errors_for(k, entries):
            skipped.append(k); continue
        info = {int(r["entry_id"]): r for r in entries}
        for item in json.load(open(os.path.join(OUT, k + ".json"), encoding="utf-8"))["entries"]:
            r = info[item["entry_id"]]
            out.append({"entry_id": item["entry_id"], "root_bw": r["root_bw"], "dictionary_slug": r["dictionary_slug"],
                        "text_hash": r["text_hash"], "highlights": item["highlights"]})
    with open(os.path.join(HERE, "highlights.jsonl"), "w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"{len(out)} entries merged into highlights.jsonl; batches skipped (missing or invalid): {' '.join(skipped) or 'none'}")


def main():
    rows = load()
    a = sys.argv[1:] or ["status"]
    if a[0] == "status":
        cmd_status(rows)
    elif a[0] == "next":
        cmd_next(rows, int(a[1]) if len(a) > 1 else 4)
    elif a[0] == "show":
        cmd_show(rows, a[1])
    elif a[0] == "check":
        cmd_check(rows, a[1] if len(a) > 1 else "all")
    elif a[0] == "merge":
        cmd_merge(rows)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
