#!/usr/bin/env python3
"""One paced Lexicon-Library harmonization loop tick.

  1. Apply the newest dict-harmonize workflow's drafts into dictionary_entries
     (idempotent — only fills rows that are still un-harmonized).
  2. Re-dump all still-pending entries to the workflow worklist and print the
     next N frequency-ordered ids for the caller to launch.

Prints one JSON line: {"applied": n, "remaining": n, "chunk": [ids]}.
When remaining == 0 the loop is done — stop.
"""
import datetime
import glob
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
DUMP = os.path.join(HERE, "data", "dict_harmonize_dump.json")
WF_GLOB = os.path.expanduser(
    "~/.claude/projects/-Users-jawadshuaib-Desktop-projects-quran-related/*/subagents/workflows/wf_*/journal.jsonl")
_STUBS = {"placeholder", "unused", "n/a", "na", "see above", "see harmonized", "todo", "..."}


def _drafts_from_journal(jp):
    drafts = {}
    for line in open(jp, encoding="utf-8"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") != "result":
            continue
        r = o.get("result")
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except Exception:
                pass
        if isinstance(r, dict) and "translation_en" in r and "id" in r:
            drafts[r["id"]] = r
    return drafts


def apply_latest():
    """Apply the most recent workflow journal that holds dict-harmonize drafts."""
    journals = sorted(glob.glob(WF_GLOB), key=os.path.getmtime, reverse=True)
    for jp in journals[:6]:
        drafts = _drafts_from_journal(jp)
        if not drafts:
            continue
        conn = sqlite3.connect(DB, timeout=60)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        changed = 0
        for e in drafts.values():
            ha = (e.get("harmonized_en") or "").strip()
            tr = (e.get("translation_en") or "").strip()
            # harmonized_en is the core View-1 content — must be real, else re-draft.
            if len(ha) < 40 or ha.lower() in _STUBS:
                continue
            # If only the faithful-translation field stubbed (happens on the giant
            # Lisān/Tāj entries at the output limit), store the harmonized text now
            # and leave translation blank + flagged for a later backfill — so the
            # entry stops cycling the queue.
            tr_ok = len(tr) >= 40 and tr.lower() not in _STUBS
            meta = {"issues": e.get("issues", [])}
            if not tr_ok:
                meta["translation_pending"] = True
            cur = conn.execute(
                "UPDATE dictionary_entries SET translation_en=?, harmonized_en=?, confidence=?, "
                "gen_meta=?, edited_at=? WHERE id=? AND (harmonized_en IS NULL OR harmonized_en='')",
                (tr if tr_ok else "", ha, e.get("confidence"),
                 json.dumps(meta, ensure_ascii=False), now, e["id"]))
            changed += cur.rowcount
        conn.commit()
        conn.close()
        return changed
    return 0


def remaining_and_chunk(n):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
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
    rows.sort(key=lambda r: (-freq.get(r["root_buckwalter"], 0), r["root_buckwalter"],
                             r["author_death_year"] or 0))
    return len(rows), [r["id"] for r in rows[:n]]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    applied = apply_latest()
    remaining, chunk = remaining_and_chunk(n)
    print(json.dumps({"applied": applied, "remaining": remaining, "chunk": chunk}, ensure_ascii=False))
