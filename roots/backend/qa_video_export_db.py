#!/usr/bin/env python3
"""Export a SLIM, committable source DB for the Q&A video pipeline.

The full quran.db is 718MB and gitignored, so a cloud Routine (which runs
on a fresh git checkout) can't read it. This builds a small SQLite file
(`data/qa_video_source.db`, a few MB) containing ONLY what the pipeline
reads:

    verses                 chapter, verse, text_uthmani         (all 6236)
    translations           chapter, verse, text_en              (all)
    ai_translations        id, chapter, verse, revised_text,
                           translation_text                      (needed cols only)
    assistant_conversations the rated-5 verse Q&A candidate pool (~550 rows),
                           with only the columns the pipeline uses

morphology / word_glosses / ai_word_meanings are NOT needed — the gate
tokenizes the displayed verse text on whitespace, not the morphology table.

Commit the output so a cloud Routine can run `/qa-video-draft` unattended.
Re-run whenever new rated-5 Q&A are graded.

Usage:
    python qa_video_export_db.py            # -> data/qa_video_source.db
    python qa_video_export_db.py --out /path/to/slim.db --full data/quran.db
"""

from __future__ import annotations

import argparse
import os
import sqlite3

_HERE = os.path.dirname(os.path.abspath(__file__))
FULL_DB = os.path.join(_HERE, "data", "quran.db")
SLIM_DB = os.path.join(_HERE, "data", "qa_video_source.db")


def export(full_path: str, slim_path: str) -> None:
    if not os.path.exists(full_path):
        raise SystemExit(f"full DB not found: {full_path}")
    if os.path.exists(slim_path):
        os.remove(slim_path)

    src = sqlite3.connect(full_path)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(slim_path)

    dst.executescript(
        """
        CREATE TABLE verses (chapter INT, verse INT, text_uthmani TEXT);
        CREATE TABLE translations (chapter INT, verse INT, text_en TEXT);
        CREATE TABLE ai_translations (
            id INTEGER PRIMARY KEY, chapter INT, verse INT,
            revised_text TEXT, translation_text TEXT);
        CREATE TABLE assistant_conversations (
            id INTEGER PRIMARY KEY, page_type TEXT, page_key TEXT,
            question TEXT, answer TEXT, category TEXT, quality_score REAL,
            source TEXT, generation_meta TEXT, hidden INT, review_status TEXT);
        """
    )

    def copy(query, insert, table):
        rows = src.execute(query).fetchall()
        dst.executemany(insert, [tuple(r) for r in rows])
        print(f"  {table}: {len(rows)} rows")

    print(f"exporting {full_path} -> {slim_path}")
    copy("SELECT chapter, verse, text_uthmani FROM verses ORDER BY chapter, verse",
         "INSERT INTO verses VALUES (?,?,?)", "verses")
    copy("SELECT chapter, verse, text_en FROM translations ORDER BY chapter, verse",
         "INSERT INTO translations VALUES (?,?,?)", "translations")
    copy("SELECT id, chapter, verse, revised_text, translation_text FROM ai_translations",
         "INSERT INTO ai_translations VALUES (?,?,?,?,?)", "ai_translations")
    # Only the rated-5 verse Q&A — the candidate pool. Keeps the file small
    # and avoids shipping unreviewed / unrelated Q&A into the cloud sandbox.
    copy(
        "SELECT id, page_type, page_key, question, answer, category, quality_score, "
        "       source, generation_meta, COALESCE(hidden,0), review_status "
        "FROM assistant_conversations "
        "WHERE source='ai' AND quality_score=5.0 AND page_type='verse' "
        "  AND COALESCE(hidden,0)=0",
        "INSERT INTO assistant_conversations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        "assistant_conversations(rated-5 verse)",
    )

    dst.executescript(
        """
        CREATE INDEX ix_verses ON verses(chapter, verse);
        CREATE INDEX ix_translations ON translations(chapter, verse);
        CREATE INDEX ix_ai_tr ON ai_translations(chapter, verse, id);
        CREATE INDEX ix_ac ON assistant_conversations(source, quality_score, page_type);
        """
    )
    dst.commit()
    dst.execute("VACUUM")
    dst.commit()
    dst.close()
    src.close()
    mb = os.path.getsize(slim_path) / 1e6
    print(f"done: {slim_path} ({mb:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", default=FULL_DB)
    ap.add_argument("--out", default=SLIM_DB)
    args = ap.parse_args()
    export(args.full, args.out)


if __name__ == "__main__":
    main()
