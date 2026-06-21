#!/usr/bin/env python3
"""Hand back the next K un-done grade-3/4/5 verses with everything needed to
write their exegesis note — for the paced, in-main-loop generation job.

A verse is in scope if it has >=1 AI gem graded 3, 4, or 5. "un-done" means:
  - it has no row yet in verse_exegesis (net-new), OR
  - it has a grade-5 gem but its existing note is still the grade-3/4-only pass
    (template_version != 'v2') and is still 'pending' — so it must be REDONE
    with the grade-5 gem now in the gem set (which can anchor the note).
Grade-3/4-only verses that already have a note (template_version='v1') are
satisfied and never re-offered; approved/non-pending notes are never touched.
Grade-5-aware notes are written with template_version='v2'.

Returned in mushaf order. Prints one JSON object:

  {"remaining": <int>, "verses": [ {page_key, chapter, verse,
      gems:[{id,score,category,question,answer}], arabic, translation,
      departure, grammar} , ... ]}

Usage:  python exeg_next.py [K]      (default K=4)
"""
import json
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(__file__), "data", "quran.db")


def main(k):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # existing notes: page_key -> (template_version, review_status)
    notes = {r["page_key"]: (r["template_version"], r["review_status"])
             for r in conn.execute(
                 "SELECT page_key, template_version, review_status FROM verse_exegesis")}
    rows = conn.execute(
        "SELECT page_key, id, CAST(quality_score AS INT) AS score, category, question, answer "
        "FROM assistant_conversations "
        "WHERE source='ai' AND CAST(quality_score AS INT) IN (3,4,5) AND page_key LIKE '%:%'"
    ).fetchall()

    by_verse = {}
    for r in rows:
        by_verse.setdefault(r["page_key"], []).append(r)

    def needs_note(pk):
        note = notes.get(pk)
        if note is None:
            return True                       # net-new: no note yet
        has_g5 = any(g["score"] == 5 for g in by_verse[pk])
        if not has_g5:
            return False                      # grade-3/4-only: existing v1 note is fine
        tv, status = note
        if tv == "v2":
            return False                      # already redone with grade-5 in play
        if status != "pending":
            return False                      # never overwrite approved/edited notes
        return True                           # grade-5 verse with a v1 pending note -> REDO

    todo = [pk for pk in by_verse if needs_note(pk)]
    todo.sort(key=lambda pk: (int(pk.split(":")[0]), int(pk.split(":")[1])))

    out = []
    for pk in todo[:k]:
        ch, v = (int(x) for x in pk.split(":"))
        gems = [
            {"id": g["id"], "score": g["score"], "category": g["category"],
             "question": g["question"], "answer": g["answer"]}
            for g in sorted(by_verse[pk], key=lambda g: g["id"])
        ]
        ar = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (ch, v)).fetchone()
        en = conn.execute(
            "SELECT text_en FROM translations WHERE chapter=? AND verse=?", (ch, v)).fetchone()
        dep = conn.execute(
            "SELECT departure_notes FROM ai_translations WHERE chapter=? AND verse=?", (ch, v)).fetchone()
        gr = conn.execute(
            "SELECT notes_markdown FROM ai_grammar_notes WHERE chapter=? AND verse=?", (ch, v)).fetchone()
        out.append({
            "page_key": pk, "chapter": ch, "verse": v,
            "gems": gems,
            "arabic": ar["text_uthmani"] if ar else None,
            "translation": en["text_en"] if en else None,
            "departure": (dep["departure_notes"] if dep and dep["departure_notes"] else None),
            "grammar": (gr["notes_markdown"] if gr and gr["notes_markdown"] else None),
        })

    conn.close()
    print(json.dumps({"remaining": len(todo), "verses": out}, ensure_ascii=False))


if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    main(k)
