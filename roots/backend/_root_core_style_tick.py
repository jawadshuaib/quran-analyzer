"""Rewrite the stock "these letters" framing in approved root-core passages.

The tooltip already shows the root and a Root Sense heading, so a passage
opening "X is where these letters begin" restates the frame instead of
saying something. This walks every approved passage that still leans on
"letters" and records a decision for each, so the pass is resumable.

  --next N            print the next N unhandled passages
  --apply FILE.json   [{"id":..,"from":..,"to":..}]   replace one phrase
                      [{"id":..,"passage":..}]        replace the whole text
                      [{"id":..,"keep":true}]         leave as is (the word is earned)
  --report            progress, and how often "letters" still appears
"""
import json, re, sqlite3, sys, unicodedata

from _root_core_prompt import MAX_CHARS
from _root_core_terms import check as contested_check

DB = "data/quran.db"
LETTERS = re.compile(r"\bletters\b", re.I)


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS root_core_style_log ("
              "id INTEGER PRIMARY KEY, action TEXT, at TEXT DEFAULT CURRENT_TIMESTAMP)")
    return c


def _todo(c):
    done = {r[0] for r in c.execute("SELECT id FROM root_core_style_log")}
    return [r for r in c.execute(
        "SELECT id, root_buckwalter, lemmas_json, passage FROM root_core_meanings "
        "WHERE review_status='approved' ORDER BY id")
        if r["id"] not in done and LETTERS.search(r["passage"] or "")]


def nxt(n):
    c = _conn()
    rows = _todo(c)
    print(f"# remaining={len(rows)}")
    for r in rows[:n]:
        print(f"\n[{r['id']}] {r['root_buckwalter']} {r['lemmas_json'] or ''}")
        print(r["passage"])


def apply(path):
    c = _conn()
    n = {"edit": 0, "keep": 0, "bad": 0}
    for it in json.load(open(path)):
        i = it["id"]
        row = c.execute("SELECT passage FROM root_core_meanings WHERE id=?", (i,)).fetchone()
        if row is None:
            print(f"  [{i}] no such row"); n["bad"] += 1; continue
        if it.get("keep"):
            c.execute("INSERT OR REPLACE INTO root_core_style_log (id, action) VALUES (?, 'keep')", (i,))
            n["keep"] += 1
            continue
        old = row["passage"]
        if "passage" in it:
            new = it["passage"]
        else:
            if it["from"] not in old:
                print(f"  [{i}] phrase not found: {it['from']!r}"); n["bad"] += 1; continue
            new = old.replace(it["from"], it["to"], 1)
        new = unicodedata.normalize("NFC", re.sub(r"\s+", " ", new).strip())
        probs = []
        if len(new) > MAX_CHARS:
            probs.append(f"len {len(new)}")
        hits = contested_check(new)
        if hits:
            probs.append(f"contested {hits}")
        if probs:
            print(f"  [{i}] refused: {probs}"); n["bad"] += 1; continue
        c.execute("UPDATE root_core_meanings SET passage=?, edited_at=CURRENT_TIMESTAMP WHERE id=?", (new, i))
        c.execute("INSERT OR REPLACE INTO root_core_style_log (id, action) VALUES (?, 'edit')", (i,))
        n["edit"] += 1
    c.commit()
    print(n)


def report():
    c = _conn()
    rows = c.execute("SELECT passage FROM root_core_meanings WHERE review_status='approved'").fetchall()
    have = sum(1 for r in rows if LETTERS.search(r[0] or ""))
    print(f"remaining={len(_todo(c))}  handled={c.execute('SELECT count(*) FROM root_core_style_log').fetchone()[0]}"
          f"  still say 'letters'={have}/{len(rows)}")


if __name__ == "__main__":
    {"--next": lambda: nxt(int(sys.argv[2])),
     "--apply": lambda: apply(sys.argv[2]),
     "--report": report}[sys.argv[1]]()
