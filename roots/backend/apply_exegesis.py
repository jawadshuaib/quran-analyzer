#!/usr/bin/env python3
"""Load generated exegesis notes into the verse_exegesis table.

Reads one or more JSON files, each a single object:
  {chapter, verse, page_key, exegesis_markdown, source_gem_ids[], source_scores[],
   model?, template_version?, flags?[]}

Upserts one row per verse (UNIQUE chapter,verse), review_status='pending',
so nothing reaches the public verse until an admin approves it in /admin/exegesis.

Usage:  python apply_exegesis.py /tmp/exeg_out/*.json
"""
import glob
import json
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(__file__), "data", "quran.db")

DDL = """
CREATE TABLE IF NOT EXISTS verse_exegesis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    page_key TEXT NOT NULL,
    exegesis_markdown TEXT NOT NULL,
    source_gem_ids TEXT,
    source_scores TEXT,
    model_used TEXT,
    review_status TEXT DEFAULT 'pending',
    hidden INTEGER DEFAULT 0,
    template_version TEXT,
    generation_meta TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    edited_at TEXT,
    UNIQUE(chapter, verse)
)
"""


def main(patterns):
    files = []
    for p in patterns:
        files.extend(sorted(glob.glob(p)))
    if not files:
        sys.exit("no exegesis files matched")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(DDL)
    conn.commit()

    loaded = bad = 0
    for f in files:
        try:
            o = json.load(open(f))
        except Exception as e:
            print(f"  SKIP {f}: {e}"); bad += 1; continue
        md = (o.get("exegesis_markdown") or "").strip()
        if not md or not o.get("chapter") or not o.get("verse"):
            print(f"  SKIP {f}: missing fields"); bad += 1; continue
        ch, v = int(o["chapter"]), int(o["verse"])
        pk = o.get("page_key") or f"{ch}:{v}"
        meta = {"template_version": o.get("template_version", "v1"),
                "flags": o.get("flags", []),
                "source_scores": o.get("source_scores", [])}
        conn.execute(
            "INSERT INTO verse_exegesis "
            "(chapter, verse, page_key, exegesis_markdown, source_gem_ids, source_scores, "
            " model_used, review_status, hidden, template_version, generation_meta, created_at) "
            "VALUES (?,?,?,?,?,?,?, 'pending', 0, ?, ?, datetime('now')) "
            "ON CONFLICT(chapter, verse) DO UPDATE SET "
            "  exegesis_markdown=excluded.exegesis_markdown, "
            "  source_gem_ids=excluded.source_gem_ids, source_scores=excluded.source_scores, "
            "  model_used=excluded.model_used, template_version=excluded.template_version, "
            "  generation_meta=excluded.generation_meta, edited_at=datetime('now')",
            (ch, v, pk, md[:50000],
             json.dumps(o.get("source_gem_ids", [])),
             json.dumps(o.get("source_scores", [])),
             o.get("model", "opus-4.8-exegesis"),
             o.get("template_version", "v1"),
             json.dumps(meta, ensure_ascii=False)),
        )
        loaded += 1
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM verse_exegesis").fetchone()[0]
    conn.close()
    print(json.dumps({"files": len(files), "loaded": loaded, "skipped": bad,
                      "verse_exegesis_total_rows": n}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:] or ["/tmp/exeg_out/*.json"])
