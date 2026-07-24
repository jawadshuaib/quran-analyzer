#!/usr/bin/env python3
"""Apply the translation-only backfill drafts.

Reads the newest dict-translate-backfill workflow journal, writes translation_en
into rows that still have it blank, and clears the `translation_pending` flag
from gen_meta on success. Idempotent: re-running only fills rows still blank.

Prints one JSON line: {"applied": n, "remaining_pending": n, "skipped": [ids]}.
"""
import glob
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
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
        # translation-only drafts have translation_en + id but NO harmonized_en
        if isinstance(r, dict) and "translation_en" in r and "id" in r and "harmonized_en" not in r:
            drafts[r["id"]] = r
    return drafts


def apply_latest():
    journals = sorted(glob.glob(WF_GLOB), key=os.path.getmtime, reverse=True)
    for jp in journals[:8]:
        drafts = _drafts_from_journal(jp)
        if not drafts:
            continue
        conn = sqlite3.connect(DB, timeout=60)
        conn.row_factory = sqlite3.Row
        applied, skipped = 0, []
        for e in drafts.values():
            tr = (e.get("translation_en") or "").strip()
            if len(tr) < 40 or tr.lower() in _STUBS:
                skipped.append(e["id"])
                continue
            row = conn.execute("SELECT gen_meta FROM dictionary_entries WHERE id=?", (e["id"],)).fetchone()
            if row is None:
                continue
            try:
                meta = json.loads(row["gen_meta"]) if row["gen_meta"] else {}
            except Exception:
                meta = {}
            meta.pop("translation_pending", None)
            cur = conn.execute(
                "UPDATE dictionary_entries SET translation_en=?, gen_meta=? "
                "WHERE id=? AND (translation_en IS NULL OR translation_en='')",
                (tr, json.dumps(meta, ensure_ascii=False), e["id"]))
            applied += cur.rowcount
        conn.commit()
        conn.close()
        return applied, skipped, jp
    return 0, [], None


if __name__ == "__main__":
    applied, skipped, jp = apply_latest()
    conn = sqlite3.connect(DB)
    remaining = conn.execute(
        "SELECT COUNT(*) FROM dictionary_entries WHERE harmonized_en!='' "
        "AND (translation_en IS NULL OR translation_en='') AND gen_meta LIKE '%translation_pending%'"
    ).fetchone()[0]
    conn.close()
    print(json.dumps({"applied": applied, "remaining_pending": remaining,
                      "skipped": skipped, "journal": os.path.basename(os.path.dirname(jp)) if jp else None},
                     ensure_ascii=False))
