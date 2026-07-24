#!/usr/bin/env python3
"""Harmonization prep for the Lexicon Library.

`prep` dumps the PENDING `dictionary_entries` that still need harmonization
(no `harmonized_en` yet) to a JSON worklist that the `_dict_harmonize.js`
workflow reads per-entry (by id, via the dump path) — keeping the big raw Arabic
out of prompts/args. The workflow drafts translation_en + harmonized_en, a verify
stage checks faithfulness, and `_apply_dict_drafts.py` writes the result back
(still `pending`) for admin review.

Usage:
    python3 dict_harmonize.py prep Amn qwl        # dump pending entries for these roots
    python3 dict_harmonize.py prep --top 300      # dump pending for top-300 frequency roots
    python3 dict_harmonize.py prep --limit 40     # dump first 40 pending entries
    python3 dict_harmonize.py prep --redo Amn     # re-dump even already-harmonized entries
    python3 dict_harmonize.py status              # harmonization progress
"""
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
DUMP = os.path.join(HERE, "data", "dict_harmonize_dump.json")   # the workflow reads THIS


def _conn():
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _top_roots(conn, n):
    return [r[0] for r in conn.execute(
        "SELECT root_buckwalter FROM morphology WHERE root_buckwalter IS NOT NULL "
        "AND root_buckwalter!='' GROUP BY root_buckwalter ORDER BY COUNT(*) DESC LIMIT ?",
        (n,)).fetchall()]


def prep(roots=None, limit=None, redo=False):
    conn = _conn()
    q = ("SELECT e.id, e.root_buckwalter, e.root_arabic, e.dictionary_slug, "
         "e.original_text_ar, d.name_en, d.author, d.author_death_year, "
         "d.is_quran_specific, d.language "
         "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
         "WHERE e.original_text_ar IS NOT NULL AND LENGTH(e.original_text_ar) >= 3 ")
    args = []
    if not redo:
        q += "AND (e.harmonized_en IS NULL OR e.harmonized_en = '') "
    if roots:
        q += "AND e.root_buckwalter IN (%s) " % ",".join("?" * len(roots))
        args += roots
    q += "ORDER BY e.root_buckwalter, d.author_death_year"
    if limit:
        q += " LIMIT ?"
        args.append(limit)
    rows = [dict(r) for r in conn.execute(q, args).fetchall()]
    conn.close()
    with open(DUMP, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    ids = [r["id"] for r in rows]
    print(json.dumps({"dump": DUMP, "count": len(rows), "roots": sorted({r["root_buckwalter"] for r in rows}),
                      "ids": ids}, ensure_ascii=False))
    return ids


def next_chunk(n):
    """Dump ALL still-pending entries to the worklist and print the next N ids
    (frequency-ordered) as a JSON array — one paced /loop tick's batch."""
    conn = _conn()
    freq = {r[0]: r[1] for r in conn.execute(
        "SELECT root_buckwalter, COUNT(*) FROM morphology WHERE root_buckwalter!='' "
        "GROUP BY root_buckwalter").fetchall()}
    rows = [dict(r) for r in conn.execute(
        "SELECT e.id, e.root_buckwalter, e.root_arabic, e.dictionary_slug, e.original_text_ar, "
        "d.name_en, d.author, d.author_death_year, d.is_quran_specific, d.language "
        "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
        "WHERE e.original_text_ar IS NOT NULL AND LENGTH(e.original_text_ar) >= 3 "
        "AND (e.harmonized_en IS NULL OR e.harmonized_en = '')").fetchall()]
    conn.close()
    with open(DUMP, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    # frequency-ordered so the most load-bearing roots harmonize first; whole
    # roots kept together within the chunk for a coherent panel.
    rows.sort(key=lambda r: (-freq.get(r["root_buckwalter"], 0), r["root_buckwalter"], r["author_death_year"] or 0))
    ids = [r["id"] for r in rows[:n]]
    print(json.dumps({"remaining": len(rows), "chunk": ids}, ensure_ascii=False))


def status():
    conn = _conn()
    tot = conn.execute("SELECT COUNT(*) FROM dictionary_entries").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM dictionary_entries WHERE harmonized_en IS NOT NULL AND harmonized_en!=''").fetchone()[0]
    appr = conn.execute("SELECT COUNT(*) FROM dictionary_entries WHERE review_status='approved'").fetchone()[0]
    roots = conn.execute("SELECT COUNT(DISTINCT root_buckwalter) FROM dictionary_entries").fetchone()[0]
    print(f"entries: {tot}  harmonized: {done}  approved: {appr}  distinct roots: {roots}")
    conn.close()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "prep":
        rest = sys.argv[2:]
        redo = "--redo" in rest
        rest = [a for a in rest if a != "--redo"]
        limit = None
        roots = None
        if "--top" in rest:
            i = rest.index("--top")
            conn = _conn(); roots = _top_roots(conn, int(rest[i + 1])); conn.close()
        elif "--limit" in rest:
            i = rest.index("--limit"); limit = int(rest[i + 1])
        else:
            roots = rest or None
        prep(roots=roots, limit=limit, redo=redo)
    elif cmd == "next":
        next_chunk(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
    elif cmd == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
