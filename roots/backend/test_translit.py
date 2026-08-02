#!/usr/bin/env python3
"""Regression tests for translit.py.

Run:  python3 test_translit.py

The expectations are taken from real spans in the exegesis corpus, so a failure
here means the hover-to-highlight alignment is about to regress on live notes.
"""

import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translit import translit_key, arabic_key, rom_word  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')

# (chapter, verse, word_pos) -> expected display romanization
ROM_CASES = [
    (11, 114, 2, 'al-ṣalāta'),      # sun letter: article lām not doubled
    (11, 114, 3, 'ṭarafayi'),       # alif maqṣūra before a vowel is consonantal
    (11, 114, 6, 'mina'),           # word-initial shadda carried from مِّن is not a geminate
    (11, 114, 7, 'al-layli'),       # assimilated article: stem lām handed back
    (11, 114, 10, 'yudhhibna'),
    (11, 114, 13, 'dhikrā'),        # alif maqṣūra + dagger alif must not stack
    (11, 114, 14, 'li-l-dhākirīna'),  # li- is the preposition, not the article
    (44, 56, 2, 'yadhūqūna'),       # long ū straddles a segment boundary
    (112, 1, 3, 'al-lāhu'),         # article inside an unsegmented stem
]

# A cited span and the word range it must resolve to.
SPAN_CASES = [
    (11, 114, 'inna l-ḥasanāti yudhhibna l-sayyiʾāt', 8, 11),
    (11, 114, 'طَرَفَىِ ٱلنَّهَارِ', 3, 4),          # Arabic citation
    (11, 114, 'yudhhibna', 10, 10),
    (1, 2, 'al-ḥamdu lillāhi rabbi l-ʿālamīn', 1, 4),
    (44, 56, 'wa-waqāhum ʿadhāba l-jaḥīm', 8, 10),
    (44, 56, 'lā yadhūqūna fīhā l-mawta', 1, 4),
]

# Keys that must NOT collapse together, or hovering one word would light another.
DISTINCT_KEYS = [
    ('al-muttaqīn', 'mutaq'),        # sound plural -īn is not tanwīn
    ('ʾan', ''),                     # 2-letter function words keep their key
    ('ʿan', ''),
]


def _words(conn, ch, v):
    return [dict(zip(('word_pos', 'translit', 'translit_key', 'arabic_key'), r))
            for r in conn.execute(
                "SELECT word_pos, translit, translit_key, arabic_key FROM word_translit "
                "WHERE chapter=? AND verse=? ORDER BY word_pos", (ch, v))]


def _resolve(ws, span):
    is_ar = bool(re.search(r'[؀-ۿ]', span))
    fld, col = (arabic_key, 'arabic_key') if is_ar else (translit_key, 'translit_key')
    toks = [t for t in (fld(x) for x in re.sub(r'[.,;:?!"”“…]', '', span).split()) if t]
    if not toks:
        return None
    for i in range(len(ws) - len(toks) + 1):
        ok = True
        for k, t in enumerate(toks):
            w = ws[i + k][col]
            if not (w == t or (len(t) >= 3 and (w.startswith(t) or t.startswith(w)))):
                ok = False
                break
        if ok:
            return ws[i]['word_pos'], ws[i + len(toks) - 1]['word_pos']
    return None


def main():
    conn = sqlite3.connect(DB)
    fails = []

    for ch, v, wp, want in ROM_CASES:
        got = conn.execute(
            "SELECT translit FROM word_translit WHERE chapter=? AND verse=? AND word_pos=?",
            (ch, v, wp)).fetchone()
        got = got[0] if got else None
        if got != want:
            fails.append(f"rom {ch}:{v}:{wp}  want {want!r}  got {got!r}")

    for ch, v, span, a, b in SPAN_CASES:
        got = _resolve(_words(conn, ch, v), span)
        if got != (a, b):
            fails.append(f"span {ch}:{v} {span!r}  want ({a}, {b})  got {got}")

    # Every word must carry a usable key, else it can never be a hover target.
    empties = conn.execute(
        "SELECT COUNT(*) FROM word_translit WHERE translit_key='' OR arabic_key=''").fetchone()[0]
    if empties:
        fails.append(f"{empties} rows have an empty match key")

    n = conn.execute("SELECT COUNT(*) FROM word_translit").fetchone()[0]
    m = conn.execute("SELECT COUNT(DISTINCT chapter||':'||verse||':'||word_pos) FROM morphology").fetchone()[0]
    if n != m:
        fails.append(f"word_translit has {n} rows, morphology has {m} words")

    if translit_key('al-muttaqīn') != 'mutaqin':
        fails.append(f"al-muttaqīn key regressed: {translit_key('al-muttaqīn')!r} (tanwīn rule eating -īn?)")

    conn.close()
    if fails:
        print(f"FAIL ({len(fails)})")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"ok — {len(ROM_CASES)} romanizations, {len(SPAN_CASES)} span resolutions, {n} rows keyed")


if __name__ == '__main__':
    main()
