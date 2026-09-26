#!/usr/bin/env python3
"""Look-ups for writing and verifying the classical-dictionary guides
(/classical-dictionaries/<slug>). Read-only against data/quran.db.

Only entries the site actually DISPLAYS count: review_status='approved',
not hidden, harmonized_en non-empty (the same filter as
/api/root/<bw>/dictionaries).

  python3 _dict_guide_tool.py dicts
      every dictionary: slug, title, author, displayed-entry count
  python3 _dict_guide_tool.py entry <root_bw> <dictionary_slug>
      the full displayed entry: original text, faithful translation, harmonized
      English, source URL, deep link
  python3 _dict_guide_tool.py roots <dictionary_slug> [--limit N] [--sort freq|len]
      displayed roots for one dictionary, with Qur'an frequency and text length
  python3 _dict_guide_tool.py grep <dictionary_slug> <regex> [--field original|translation|harmonized]
      displayed roots whose entry matches a regex (Python re, case-insensitive;
      Arabic vowel marks are ignored on both sides, context shown unvowelled)
  python3 _dict_guide_tool.py both <dictionary_slug_a> <dictionary_slug_b> [--limit N]
      roots displayed in BOTH dictionaries (for comparisons), by Qur'an frequency
  python3 _dict_guide_tool.py root <root_bw>
      which dictionaries display this root (and the Arabic spelling)
  python3 _dict_guide_tool.py find-root <arabic letters, e.g. دخن or د خ ن>
      the site's Buckwalter identifier(s) for an Arabic root
"""
import os
import re
import sqlite3
import sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "quran.db")
SHOWN = ("e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
         "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> ''")


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


HARAKAT = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")


def plain(t):
    """Arabic without short vowels, shadda, sukun, tatweel -- so a search for
    أصلان finds أَصْلَانِ."""
    return HARAKAT.sub("", t or "")


def freq_map(c):
    return {r[0]: r[1] for r in c.execute(
        "SELECT root_buckwalter, COUNT(*) FROM morphology "
        "WHERE root_buckwalter IS NOT NULL GROUP BY root_buckwalter")}


def arg_opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def cmd_dicts(c, args):
    for r in c.execute(
            "SELECT d.slug, d.name_en, d.name_ar, d.author, d.author_death_year, d.language, "
            "(SELECT COUNT(*) FROM dictionary_entries e WHERE e.dictionary_slug = d.slug AND "
            + SHOWN + ") AS shown FROM dictionaries d ORDER BY d.author_death_year"):
        print(f"{r['slug']}\n    {r['name_en']} | {r['name_ar']} | {r['author']} "
              f"(site date {r['author_death_year']}) | lang={r['language']} | displayed entries={r['shown']}")


def cmd_entry(c, args):
    bw, slug = args[0], args[1]
    r = c.execute(
        "SELECT e.*, d.name_en FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
        "WHERE e.root_buckwalter = ? AND e.dictionary_slug = ?", (bw, slug)).fetchone()
    if not r:
        print(f"NO ENTRY for root {bw!r} in {slug}")
        return
    shown = (r["review_status"] == "approved" and not r["hidden"] and (r["harmonized_en"] or "").strip())
    print(f"entry_id={r['id']}  root={r['root_buckwalter']} ({r['root_arabic']})  dictionary={r['name_en']}")
    print(f"status={r['review_status']} hidden={r['hidden']}  DISPLAYED ON SITE: {'YES' if shown else 'NO'}")
    print(f"source_url={r['source_url']}")
    print(f"deep link: /root/{bw}#dict-{slug}")
    print("\n===== ORIGINAL TEXT (as displayed under 'Original Text') =====")
    print(r["original_text_ar"] or "")
    print("\n===== FAITHFUL TRANSLATION (site, AI-drafted + reviewed) =====")
    print(r["translation_en"] or "")
    print("\n===== HARMONIZED ENGLISH (the default view on the site) =====")
    print(r["harmonized_en"] or "")


def cmd_roots(c, args):
    slug = args[0]
    limit = int(arg_opt(args, "--limit", 60))
    sort = arg_opt(args, "--sort", "freq")
    fm = freq_map(c)
    rows = c.execute(
        "SELECT e.root_buckwalter, e.root_arabic, LENGTH(e.original_text_ar) AS n FROM dictionary_entries e "
        "WHERE e.dictionary_slug = ? AND " + SHOWN, (slug,)).fetchall()
    key = (lambda r: -fm.get(r["root_buckwalter"], 0)) if sort == "freq" else (lambda r: -(r["n"] or 0))
    rows = sorted(rows, key=key)
    print(f"{len(rows)} displayed roots in {slug} (showing {min(limit, len(rows))}, sorted by {sort})")
    for r in rows[:limit]:
        print(f"  {r['root_buckwalter']:8} {r['root_arabic'] or '':6} quran_freq={fm.get(r['root_buckwalter'], 0):5}  original_len={r['n']}")


def cmd_grep(c, args):
    slug, pat = args[0], args[1]
    field = {"original": "original_text_ar", "translation": "translation_en",
             "harmonized": "harmonized_en"}[arg_opt(args, "--field", "original")]
    rx = re.compile(plain(pat), re.I)
    fm = freq_map(c)
    hits = []
    for r in c.execute("SELECT e.root_buckwalter, e.root_arabic, e." + field + " AS t FROM dictionary_entries e "
                       "WHERE e.dictionary_slug = ? AND " + SHOWN, (slug,)):
        t = plain(r["t"])  # vowel marks ignored on both sides
        m = rx.search(t)
        if m:
            s = max(0, m.start() - 60)
            hits.append((fm.get(r["root_buckwalter"], 0), r["root_buckwalter"], r["root_arabic"],
                         t[s:m.end() + 60].replace("\n", " ")))
    hits.sort(reverse=True)
    print(f"{len(hits)} displayed entries match")
    for f, bw, ar, ctx in hits[:80]:
        print(f"  {bw:8} {ar or '':6} freq={f:5}  …{ctx}…")


def cmd_both(c, args):
    a, b = args[0], args[1]
    limit = int(arg_opt(args, "--limit", 60))
    fm = freq_map(c)
    rows = c.execute(
        "SELECT e.root_buckwalter, e.root_arabic FROM dictionary_entries e WHERE e.dictionary_slug = ? AND " + SHOWN
        + " AND e.root_buckwalter IN (SELECT e.root_buckwalter FROM dictionary_entries e WHERE e.dictionary_slug = ? AND "
        + SHOWN + ")", (a, b)).fetchall()
    rows = sorted(rows, key=lambda r: -fm.get(r["root_buckwalter"], 0))
    print(f"{len(rows)} roots displayed in both")
    for r in rows[:limit]:
        print(f"  {r['root_buckwalter']:8} {r['root_arabic'] or '':6} quran_freq={fm.get(r['root_buckwalter'], 0)}")


def cmd_root(c, args):
    bw = args[0]
    rows = c.execute(
        "SELECT e.dictionary_slug, e.root_arabic, e.review_status, e.hidden, LENGTH(e.harmonized_en) AS h "
        "FROM dictionary_entries e WHERE e.root_buckwalter = ? ORDER BY e.dictionary_slug", (bw,)).fetchall()
    if not rows:
        print(f"no dictionary entries for {bw!r}")
    for r in rows:
        shown = r["review_status"] == "approved" and not r["hidden"] and (r["h"] or 0) > 0
        print(f"  {'SHOWN ' if shown else 'hidden'} {r['dictionary_slug']}  ({r['root_arabic']}, {r['review_status']})")


def cmd_find_root(c, args):
    ar = re.sub(r"[\s\-‑]", "", " ".join(args))
    rows = c.execute("SELECT DISTINCT root_buckwalter, root_arabic FROM dictionary_entries").fetchall()
    rows += c.execute("SELECT DISTINCT root_buckwalter, root_arabic FROM morphology WHERE root_arabic IS NOT NULL").fetchall()
    seen = set()
    for r in rows:
        if re.sub(r"\s", "", r["root_arabic"] or "") == ar and r["root_buckwalter"] not in seen:
            seen.add(r["root_buckwalter"])
            print(f"  {r['root_buckwalter']}  ({r['root_arabic']})  root page: /root/{r['root_buckwalter']}")
    if not seen:
        print("no match")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    fn = {"dicts": cmd_dicts, "entry": cmd_entry, "roots": cmd_roots, "grep": cmd_grep,
          "both": cmd_both, "root": cmd_root, "find-root": cmd_find_root}.get(cmd)
    if not fn:
        print(__doc__)
        sys.exit(2)
    c = db()
    try:
        fn(c, args)
    finally:
        c.close()


if __name__ == "__main__":
    main()
