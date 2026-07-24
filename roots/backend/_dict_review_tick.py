#!/usr/bin/env python3
"""One paced Lexicon-Library SELF-REVIEW loop tick.

  1. Apply the newest dict-review workflow's verdicts into dictionary_entries
     (idempotent — a row already carrying gen_meta.ai_review is skipped).
       approve -> review_status='approved'
       edit    -> update harmonized_en/translation_en (if provided), then 'approved'
       reject  -> review_status='rejected', hidden=1
       defer   -> stays 'pending' (a human call), flagged ai_review='deferred'
     Every reviewed row gets gen_meta.ai_review = {decision, severity, reason, at}.
  2. Re-dump all still-unreviewed entries (review_status='pending' AND no
     ai_review flag) to the review worklist and print the next N ids.

Prints one JSON line: {"applied": n, "counts": {...}, "remaining": n, "chunk": [ids]}.
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
DUMP = os.path.join(HERE, "data", "dict_review_dump.json")
WF_GLOB = os.path.expanduser(
    "~/.claude/projects/-Users-jawadshuaib-Desktop-projects-quran-related/*/subagents/workflows/wf_*/journal.jsonl")
_STUBS = {"placeholder", "unused", "n/a", "na", "see above", "see harmonized", "todo", "..."}
_DECISIONS = {"approve", "edit", "reject", "defer"}


def _verdicts_from_journal(jp):
    out = {}
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
        if isinstance(r, dict) and r.get("decision") in _DECISIONS and "id" in r:
            out[r["id"]] = r
    return out


def apply_latest():
    journals = sorted(glob.glob(WF_GLOB), key=os.path.getmtime, reverse=True)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    for jp in journals[:8]:
        verdicts = _verdicts_from_journal(jp)
        if not verdicts:
            continue
        conn = sqlite3.connect(DB, timeout=60)
        conn.row_factory = sqlite3.Row
        counts = {"approve": 0, "edit": 0, "reject": 0, "defer": 0}
        applied = 0
        for v in verdicts.values():
            row = conn.execute(
                "SELECT review_status, gen_meta, harmonized_en, translation_en "
                "FROM dictionary_entries WHERE id=?", (v["id"],)).fetchone()
            if row is None:
                continue
            try:
                meta = json.loads(row["gen_meta"]) if row["gen_meta"] else {}
            except Exception:
                meta = {}
            if "ai_review" in meta:          # already reviewed -> idempotent skip
                continue
            if row["review_status"] != "pending":
                continue                      # human already touched it
            decision = v["decision"]
            meta["ai_review"] = {"decision": decision, "severity": v.get("severity"),
                                 "reason": v.get("reason", ""), "at": now}
            sets = ["gen_meta=?"]
            params = [json.dumps(meta, ensure_ascii=False)]
            if decision == "approve":
                sets.append("review_status='approved'")
            elif decision == "edit":
                ha = (v.get("harmonized_en") or "").strip()
                tr = (v.get("translation_en") or "").strip()
                if len(ha) >= 40 and ha.lower() not in _STUBS:
                    sets.append("harmonized_en=?"); params.append(ha)
                if len(tr) >= 40 and tr.lower() not in _STUBS:
                    sets.append("translation_en=?"); params.append(tr)
                sets.append("review_status='approved'")
                sets.append("edited_at=?"); params.append(now)
            elif decision == "reject":
                sets.append("review_status='rejected'")
                sets.append("hidden=1")
            # defer: leave review_status='pending', only the ai_review flag written
            params.append(v["id"])
            cur = conn.execute(
                "UPDATE dictionary_entries SET %s WHERE id=? AND review_status='pending'"
                % ", ".join(sets), params)
            if cur.rowcount:
                applied += 1
                counts[decision] += 1
        conn.commit()
        conn.close()
        return applied, counts
    return 0, {"approve": 0, "edit": 0, "reject": 0, "defer": 0}


def remaining_and_chunk(n):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    freq = {r[0]: r[1] for r in conn.execute(
        "SELECT root_buckwalter, COUNT(*) FROM morphology WHERE root_buckwalter!='' "
        "GROUP BY root_buckwalter").fetchall()}
    rows = [dict(r) for r in conn.execute(
        "SELECT e.id, e.root_buckwalter, e.root_arabic, e.dictionary_slug, e.original_text_ar, "
        "e.translation_en, e.harmonized_en, d.name_en, d.author, d.author_death_year, "
        "d.is_quran_specific, d.language "
        "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
        "WHERE e.review_status='pending' AND e.harmonized_en IS NOT NULL AND e.harmonized_en<>'' "
        "AND (e.gen_meta IS NULL OR e.gen_meta NOT LIKE '%\"ai_review\"%')").fetchall()]
    conn.close()
    with open(DUMP, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    rows.sort(key=lambda r: (-freq.get(r["root_buckwalter"], 0), r["root_buckwalter"],
                             r["author_death_year"] or 0))
    return len(rows), [r["id"] for r in rows[:n]]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    applied, counts = apply_latest()
    remaining, chunk = remaining_and_chunk(n)
    print(json.dumps({"applied": applied, "counts": counts,
                      "remaining": remaining, "chunk": chunk}, ensure_ascii=False))
