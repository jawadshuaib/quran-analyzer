#!/usr/bin/env python3
"""Backfill `word_translit`: one canonical romanization + match keys per
Qur'anic word, derived deterministically from the morphology segmentation.

    python3 build_word_translit.py            # build/refresh every word
    python3 build_word_translit.py --verse 11:114   # one verse, prints a table

This is a pure derivation — no network, no model, no API. Re-running is safe
and idempotent; it rebuilds every row from `morphology`.

Keyed by (chapter, verse, word_pos) to match the `position` field the verse API
already emits in its `words[]` array, which is what the reader renders. That
keeps highlight anchors aligned with the rendered tokens (note that verse 1 of
each surah carries the Bismillah in `verses.text_uthmani` but not in `words[]`,
so anchoring on rendered *text* offsets instead would be off by four words).
"""

import argparse
import collections
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translit import rom_word, translit_key, arabic_plain, arabic_key  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS word_translit (
    chapter       INTEGER NOT NULL,
    verse         INTEGER NOT NULL,
    word_pos      INTEGER NOT NULL,
    translit      TEXT NOT NULL,   -- display form, house style: al-ḥasanāti
    translit_key  TEXT NOT NULL,   -- normalised for matching: hasanat
    arabic_plain  TEXT NOT NULL,   -- diacritics stripped: الحسنت
    arabic_key    TEXT NOT NULL,   -- normalised for matching
    PRIMARY KEY (chapter, verse, word_pos)
);
CREATE INDEX IF NOT EXISTS idx_word_translit_key ON word_translit(translit_key);
CREATE INDEX IF NOT EXISTS idx_word_translit_arkey ON word_translit(arabic_key);
"""


def ensure_schema(conn):
    conn.executescript(SCHEMA)


def load_words(conn, chapter=None, verse=None):
    """(chapter, verse, word_pos) -> ordered [(buckwalter, tag, arabic)]."""
    sql = ("SELECT chapter, verse, word_pos, form_buckwalter, tag, form_arabic "
           "FROM morphology")
    args = []
    if chapter is not None:
        sql += " WHERE chapter=? AND verse=?"
        args = [chapter, verse]
    sql += " ORDER BY chapter, verse, word_pos, segment"
    out = collections.OrderedDict()
    for ch, v, wp, bw, tag, ar in conn.execute(sql, args):
        out.setdefault((ch, v, wp), []).append((bw, tag, ar))
    return out


def build_rows(words):
    rows = []
    for (ch, v, wp), segs in words.items():
        pairs = [(b, t) for b, t, _ in segs]
        ar = ''.join(a or '' for _, _, a in segs)
        rows.append((
            ch, v, wp,
            rom_word(pairs),
            translit_key(rom_word(pairs, pausal=True)),
            arabic_plain(ar),
            arabic_key(ar),
        ))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verse', help='only this verse, e.g. 11:114 (dry run, prints a table)')
    ap.add_argument('--db', default=DB)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        if args.verse:
            ch, v = (int(x) for x in args.verse.split(':'))
            rows = build_rows(load_words(conn, ch, v))
            print(f"{'pos':>4}  {'arabic':<20} {'translit':<24} {'key':<16} arabic_key")
            for r in rows:
                print(f"{r[2]:>4}  {r[5]:<20} {r[3]:<24} {r[4]:<16} {r[6]}")
            return

        ensure_schema(conn)
        rows = build_rows(load_words(conn))
        conn.execute("DELETE FROM word_translit")
        conn.executemany(
            "INSERT INTO word_translit "
            "(chapter, verse, word_pos, translit, translit_key, arabic_plain, arabic_key) "
            "VALUES (?,?,?,?,?,?,?)", rows)
        conn.commit()
        blank = sum(1 for r in rows if not r[4])
        print(f"word_translit: {len(rows)} rows written, {blank} with an empty match key")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
