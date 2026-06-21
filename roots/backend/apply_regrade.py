#!/usr/bin/env python3
"""Apply honest re-grades to the old-voice AI drafts.

Reads one or more JSON files, each a list of {"id": int, "score": int}.
For each row: set quality_score to the honest score, and stamp the audit
in generation_meta WITHOUT touching the question/answer text, the voice,
or the needs_voice_revision flag (the old-voice rewrite is a separate
backlog the user is NOT running here).

  prev_score      -> the quality_score this row had before this pass
  score_honest    -> the new honest score
  regraded_honest -> True

Usage:
  python apply_regrade.py /tmp/regrade/scores_*.json
"""
import glob
import json
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(__file__), "data", "quran.db")


def main(patterns):
    files = []
    for p in patterns:
        files.extend(sorted(glob.glob(p)))
    if not files:
        sys.exit("no score files matched")

    grades = {}
    for f in files:
        with open(f) as fh:
            for it in json.load(fh):
                gid = int(it["id"])
                sc = int(it["score"])
                if not (1 <= sc <= 5):
                    sys.exit(f"bad score {sc} for id {gid} in {f}")
                grades[gid] = sc  # last write wins; ids are unique anyway

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    applied = 0
    skipped_missing = 0
    not_flagged = 0
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for gid, sc in grades.items():
        row = conn.execute(
            "SELECT quality_score, generation_meta FROM assistant_conversations "
            "WHERE id=? AND source='ai'", (gid,)
        ).fetchone()
        if not row:
            skipped_missing += 1
            continue
        try:
            meta = json.loads(row["generation_meta"]) if row["generation_meta"] else {}
        except Exception:
            meta = {}
        # Safety: only touch the flagged old-voice batch.
        if not meta.get("needs_voice_revision"):
            not_flagged += 1
            continue
        meta["prev_score"] = row["quality_score"]
        meta["score_honest"] = sc
        meta["regraded_honest"] = True
        conn.execute(
            "UPDATE assistant_conversations SET quality_score=?, generation_meta=? "
            "WHERE id=?",
            (float(sc), json.dumps(meta, ensure_ascii=False), gid),
        )
        applied += 1
        dist[sc] += 1
    conn.commit()
    conn.close()
    print(json.dumps({
        "files": len(files), "grades_in": len(grades), "applied": applied,
        "skipped_missing_id": skipped_missing, "skipped_not_flagged": not_flagged,
        "new_score_distribution": dist,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:] or ["/tmp/regrade/scores_*.json"])
