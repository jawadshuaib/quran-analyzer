#!/usr/bin/env python3
"""Load reader highlights for dictionary entries into dictionary_highlights.

The highlights are made by the cloud job on the claude/dict-highlights branch
(cloud/dict-highlights/: TASK.md has the rules, job.py the checker). This loads
its batch files, checks every highlight again against the entry's CURRENT
readable text, and stores the ones that still fit. Sync to production with
./sync_tables_to_prod.sh dictionary_highlights.

  python3 _dict_highlights_import.py <job dir>            # the cloud/dict-highlights folder
  python3 _dict_highlights_import.py <job dir> --dry-run
"""
import csv
import glob
import hashlib
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
KINDS = {"core", "quran", "early", "later"}

csv.field_size_limit(10 ** 8)


def text_hash(text):
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    job = sys.argv[1]
    dry = "--dry-run" in sys.argv
    rows = {int(r["entry_id"]): r for r in csv.DictReader(open(os.path.join(job, "entries.csv"), encoding="utf-8", newline=""))}
    made = {}
    for path in sorted(glob.glob(os.path.join(job, "out", "*.json"))):
        for item in json.load(open(path, encoding="utf-8"))["entries"]:
            made[item["entry_id"]] = item["highlights"]
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS dictionary_highlights ("
              "entry_id INTEGER PRIMARY KEY, root_buckwalter TEXT, dictionary_slug TEXT, "
              "text_hash TEXT NOT NULL, highlights TEXT NOT NULL, source TEXT, "
              "created_at TEXT DEFAULT (datetime('now')))")
    stored = changed = dropped_spans = 0
    for eid, hls in made.items():
        row = c.execute("SELECT harmonized_en, root_buckwalter, dictionary_slug FROM dictionary_entries WHERE id = ?",
                        (eid,)).fetchone()
        if not row or eid not in rows:
            print(f"entry {eid}: not found, skipped"); continue
        text, root, slug = row
        if text_hash(text) != rows[eid]["text_hash"]:
            changed += 1
            print(f"entry {eid} ({root}): text edited since the job was made, skipped"); continue
        keep = [h for h in hls if h.get("kind") in KINDS and text.count(h.get("text", "")) == 1]
        dropped_spans += len(hls) - len(keep)
        if not dry:
            c.execute("INSERT OR REPLACE INTO dictionary_highlights "
                      "(entry_id, root_buckwalter, dictionary_slug, text_hash, highlights, source) VALUES (?,?,?,?,?,?)",
                      (eid, root, slug, text_hash(text), json.dumps(keep, ensure_ascii=False),
                       "cloud job claude/dict-highlights (Claude Opus 5.5, then Sonnet 5.5)"))
        stored += 1
    if not dry:
        c.commit()
    print(f"{stored} entries {'would be ' if dry else ''}stored; {changed} skipped (text edited); "
          f"{dropped_spans} highlights dropped (no longer an exact, unique span)")


if __name__ == "__main__":
    main()
