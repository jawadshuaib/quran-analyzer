#!/usr/bin/env python3
"""Apply _dict_harmonize.js output into dictionary_entries as pending drafts.

Usage: python3 _apply_dict_drafts.py <workflow_output.json>

Writes translation_en + harmonized_en + confidence + gen_meta (the verify verdict)
onto each entry by id. review_status stays 'pending' (admin review gate). Entries
whose verifier returned ok=false are still written but flagged low-confidence and
listed, so a human sees them first. Nothing is auto-approved; nothing syncs to prod.
"""
import datetime
import json
import sqlite3
import sys

DB = "data/quran.db"

if len(sys.argv) < 2:
    sys.exit("usage: _apply_dict_drafts.py <output.json>")
raw = json.load(open(sys.argv[1], encoding="utf-8"))
rows = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(rows, str):
    rows = json.loads(rows)

conn = sqlite3.connect(DB, timeout=60)   # tolerate the scraper's brief per-root write locks
now = datetime.datetime.now().isoformat(timespec="seconds")

applied, flagged, skipped = [], [], []
for e in rows:
    eid = e.get("id")
    tr = (e.get("translation_en") or "").strip()
    ha = (e.get("harmonized_en") or "").strip()
    if not eid or not ha or not tr:
        skipped.append((eid, "missing id/translation/harmonized"))
        continue
    v = e.get("verify") or {}
    ok = bool(v.get("ok", True))
    conf = e.get("confidence")
    if v.get("ok") is False and conf is not None:
        conf = min(conf, 0.4)   # push failed-verify drafts down the review queue
    conn.execute(
        "UPDATE dictionary_entries SET translation_en=?, harmonized_en=?, confidence=?, "
        "gen_meta=?, edited_at=? WHERE id=?",
        (tr, ha, conf,
         json.dumps({"verify": v, "issues": e.get("issues", [])}, ensure_ascii=False),
         now, eid))
    (applied if ok else flagged).append((eid, v.get("severity"), v.get("reason")))

conn.commit()
conn.close()
print(f"APPLIED {len(applied)+len(flagged)}/{len(rows)} (pending)  clean={len(applied)}  flagged={len(flagged)}")
for eid, sev, why in flagged:
    print(f"  FLAG entry {eid} [{sev}] {why}")
for eid, why in skipped:
    print(f"  SKIP entry {eid}: {why}")
