"""Human-style review of pending root core meanings, one batch per tick.

  --next N            print the next N pending rows (with gate + audit notes)
  --apply FILE.json   [{"id":..,"action":"approve"|"edit"|"reject","passage":..}]
  --report            counts by status
"""
import json, sqlite3, sys, unicodedata

from _root_core_prompt import MAX_CHARS
from _root_core_terms import check as contested_check

DB = "data/quran.db"


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def nxt(n):
    c = _conn()
    rows = c.execute(
        "SELECT m.id, m.root_buckwalter, m.sense_key, m.lemmas_json, m.passage, "
        "m.gates_json, r.grounded, r.unsupported_json, r.worth_showing, r.why, "
        "r.judged_passage "
        "FROM root_core_meanings m LEFT JOIN root_core_review r "
        "ON r.root_buckwalter = m.root_buckwalter AND r.sense_key = m.sense_key "
        "WHERE m.review_status = 'pending' ORDER BY m.id LIMIT ?", (n,)).fetchall()
    left = c.execute("SELECT count(*) FROM root_core_meanings "
                     "WHERE review_status='pending'").fetchone()[0]
    print(f"# pending={left}")
    for r in rows:
        flags = [g for g in json.loads(r["gates_json"] or "[]")] if r["gates_json"] else []
        audit = ""
        if r["judged_passage"] == r["passage"]:
            if r["grounded"] == 0:
                audit += f" UNGROUNDED:{r['unsupported_json']}"
            if r["worth_showing"] == 0:
                audit += f" NOT-WORTH:{r['why']}"
        print(f"\n[{r['id']}] {r['root_buckwalter']} | {r['sense_key'][:40]} "
              f"| lemmas={r['lemmas_json']}{(' | gates=' + str(flags)) if flags else ''}{audit}")
        print(r["passage"])


def apply(path):
    items = json.load(open(path))
    c = _conn()
    n = {"approve": 0, "edit": 0, "reject": 0, "bad": 0}
    for it in items:
        a, i = it["action"], it["id"]
        if a == "approve":
            c.execute("UPDATE root_core_meanings SET review_status='approved', hidden=0 "
                      "WHERE id=? AND review_status='pending'", (i,))
        elif a == "reject":
            c.execute("UPDATE root_core_meanings SET review_status='rejected', hidden=1 "
                      "WHERE id=?", (i,))
        elif a == "edit":
            p = unicodedata.normalize("NFC", it["passage"].strip())
            probs = []
            if len(p) > MAX_CHARS:
                probs.append(f"len {len(p)}")
            hits = contested_check(p)
            if hits:
                probs.append(f"contested {hits}")
            if probs:
                print(f"  [{i}] edit refused: {probs}")
                n["bad"] += 1
                continue
            c.execute("UPDATE root_core_meanings SET passage=?, review_status='approved', "
                      "hidden=0, edited_at=CURRENT_TIMESTAMP WHERE id=?", (p, i))
        n[a] += 1
    c.commit()
    print(n)


def report():
    c = _conn()
    for r in c.execute("SELECT review_status, count(*) FROM root_core_meanings GROUP BY 1"):
        print(tuple(r))


if __name__ == "__main__":
    if sys.argv[1] == "--next":
        nxt(int(sys.argv[2]))
    elif sys.argv[1] == "--apply":
        apply(sys.argv[2])
    else:
        report()
