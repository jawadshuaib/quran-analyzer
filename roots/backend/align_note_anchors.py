#!/usr/bin/env python3
"""Resolve transliterated / Arabic citations inside exegesis prose back to the
exact word range of the verse they quote, and persist them as hover anchors.

    python3 align_note_anchors.py                 # rebuild every anchor
    python3 align_note_anchors.py --verse 11:114  # dry run, prints what it finds

Entirely deterministic string alignment over the `word_translit` index — no
network, no model, no API tokens. The whole corpus resolves in a few seconds.

Only citations that quote *this* verse are stored: those are the ones the reader
can highlight. Citations of other verses, bare lexical/lemma mentions and root
forms are deliberately left alone and render as ordinary prose.
"""

import argparse
import collections
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translit import translit_key, arabic_key  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')

# Spans are matched against these; both are produced by build_word_translit.py.
ITALIC = re.compile(r'\*([^*\n]{2,160})\*')
ARABIC_RUN = re.compile(r'[؀-ۿ][؀-ۿ\sـ]*[؀-ۿ]')
HAS_ARABIC = re.compile(r'[؀-ۿ]')
DIACRITICS = 'ḥṣḍṭẓʿʾāīūḏṯḫšġ'
TRAILING_PUNCT = r'[.,;:?!"”“…()\[\]]'

# `word_pos` is the anchor because the reader renders one span per whitespace
# token of the (Bismillah-stripped) Uthmani text and labels it idx+1. That holds
# for 6,232 of 6,236 verses; in these four the corpus' word count and the
# rendered token count disagree by one, so an anchor could highlight the wrong
# word. Skipped rather than risk it.
MISALIGNED = {(2, 181), (8, 6), (13, 37), (37, 130)}

# The two note bodies a reader sees under a verse. Translation Notes quote the
# Arabic directly far more often than the (English-prose) exegesis does, so most
# of the Arabic anchors come from here. `max(created_at)` per verse mirrors the
# "most recent translation wins" rule the /ai-translation endpoint applies, so
# the anchored spans are the ones actually rendered.
SOURCES = (
    ('exegesis',
     "SELECT chapter, verse, exegesis_markdown FROM verse_exegesis"),
    ('translation_notes',
     "SELECT chapter, verse, departure_notes FROM ("
     "  SELECT chapter, verse, departure_notes, max(created_at)"
     "  FROM ai_translations GROUP BY chapter, verse)"),
    # The pre-Islamic poetry note quotes the verse the same way the other two
    # do, so its citations deserve the same hover-to-highlight. It is the one
    # source that also quotes NON-Qur'anic Arabic - the poetry itself - which
    # is why strip_foreign_arabic below exists.
    ('poetry',
     "SELECT chapter, verse, note_markdown FROM verse_poetry_notes"),
)

# A poetry note carries the poets' lines inline as [[q:<id>|<arabic>]]. Those are
# not the verse and must never be aligned to it: a line sharing a word or two
# with the verse would otherwise light up the wrong thing on hover. They are
# removed before the note is scanned for citations.
POETRY_MARKER = re.compile(r'\[\[q:\d+\|[^\]]*\]\]')


def strip_foreign_arabic(source: str, md: str) -> str:
    return POETRY_MARKER.sub(' ', md or '') if source == 'poetry' else (md or '')

SCHEMA = """
CREATE TABLE IF NOT EXISTS note_word_anchors (
    source      TEXT NOT NULL,      -- which note carried the citation
    chapter     INTEGER NOT NULL,
    verse       INTEGER NOT NULL,
    span_text   TEXT NOT NULL,      -- literal text as it appears in the prose
    script      TEXT NOT NULL,      -- 'translit' | 'arabic'
    word_start  INTEGER NOT NULL,
    word_end    INTEGER NOT NULL,
    PRIMARY KEY (source, chapter, verse, span_text)
);
CREATE INDEX IF NOT EXISTS idx_note_anchors_verse
    ON note_word_anchors(chapter, verse);
"""


def load_verse_words(conn):
    out = collections.defaultdict(list)
    for ch, v, wp, tk, ak in conn.execute(
            "SELECT chapter, verse, word_pos, translit_key, arabic_key "
            "FROM word_translit ORDER BY chapter, verse, word_pos"):
        out[(ch, v)].append((wp, tk, ak))
    return out


def _strip_conj(key: str) -> str:
    """Drop a leading conjunction wāw/fāʾ, but only when what remains is still
    long enough to identify a word. Guards against turning و + فى into a match
    on فى itself."""
    return key[1:] if len(key) > 3 and key[0] in 'وف' else key


def _tok_eq(word_key: str, cited_key: str) -> bool:
    """A cited token matches a verse word when the keys agree, or when one is a
    prefix of the other — notes routinely cite the pausal form (l-jaḥīm) of a
    word the verse carries fully inflected (l-jaḥīmi).

    A citation also normally drops the verse's leading conjunction: a note
    quotes أوفوا بعهدي where the verse reads وأوفوا بعهدي, because the wāw joins
    the phrase to what came before and is no part of what is being quoted. So a
    leading wāw/fāʾ is stripped from either side before comparing."""
    if not word_key or not cited_key:
        return False
    if word_key == cited_key:
        return True
    if _strip_conj(word_key) == _strip_conj(cited_key):
        return True
    return len(cited_key) >= 3 and (word_key.startswith(cited_key)
                                    or cited_key.startswith(word_key))


def find_range(tokens, words, idx):
    """First contiguous run of verse words matching `tokens`; None if absent."""
    n = len(tokens)
    if not n or n > len(words):
        return None
    for i in range(len(words) - n + 1):
        if all(_tok_eq(words[i + k][idx], t) for k, t in enumerate(tokens)):
            return words[i][0], words[i + n - 1][0]
    return None


def spans_in(text):
    """Yield (span_text, script) for every citation candidate in a note."""
    for m in ITALIC.finditer(text):
        s = m.group(1).strip()
        if HAS_ARABIC.search(s):
            continue                       # handled by the Arabic pass
        if not any(ch in s for ch in DIACRITICS):
            continue                       # plain-English emphasis, not a citation
        parts = s.split('-')
        if len(parts) >= 3 and ' ' not in s and all(len(p) <= 3 for p in parts):
            continue                       # bare root form (f-ṭ-r) -> /root/ page
        yield s, 'translit'
    for m in ARABIC_RUN.finditer(text):
        s = m.group(0).strip()
        toks = s.split()
        if len(toks) >= 3 and all(len(t) <= 1 for t in toks):
            continue                       # spaced root letters (د ع و)
        yield s, 'arabic'


def resolve(span, script, words):
    keyer = arabic_key if script == 'arabic' else translit_key
    idx = 2 if script == 'arabic' else 1
    raw = re.sub(TRAILING_PUNCT, '', span)
    tokens = [k for k in (keyer(t) for t in raw.split()) if k]
    if not tokens:
        return None
    return find_range(tokens, words, idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verse', help='dry run for one verse, e.g. 11:114')
    ap.add_argument('--db', default=DB)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        verse_words = load_verse_words(conn)

        if args.verse:
            ch, v = (int(x) for x in args.verse.split(':'))
            words = verse_words.get((ch, v), [])
            plain = {w[0]: t for w, t in zip(words, [r[0] for r in conn.execute(
                "SELECT arabic_plain FROM word_translit WHERE chapter=? AND verse=? "
                "ORDER BY word_pos", (ch, v))])}
            for source, sql in SOURCES:
                md = next((r[2] for r in conn.execute(sql)
                           if (r[0], r[1]) == (ch, v)), None)
                print(f"[{source}]" + ('' if md else '  (none)'))
                for span, script in spans_in(strip_foreign_arabic(source, md or '')):
                    r = resolve(span, script, words)
                    if r:
                        txt = ' '.join(plain.get(p, '') for p in range(r[0], r[1] + 1))
                        print(f"  [{script:8}] {span!r}\n       -> words {r[0]}–{r[1]}  {txt}")
                    else:
                        print(f"  [{script:8}] {span!r}\n       -> (left as prose)")
            return

        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM note_word_anchors")

        rows, stats = [], collections.Counter()
        seen = set()
        for source, sql in SOURCES:
            for ch, v, md in conn.execute(sql):
                if not md:
                    continue
                if (ch, v) in MISALIGNED:
                    stats['skipped (verse word-count drift)'] += 1
                    continue
                words = verse_words.get((ch, v))
                if not words:
                    continue
                for span, script in spans_in(strip_foreign_arabic(source, md)):
                    stats[f'{source}/{script}: seen'] += 1
                    r = resolve(span, script, words)
                    if not r:
                        stats[f'{source}/{script}: left as prose'] += 1
                        continue
                    key = (source, ch, v, span)
                    if key in seen:        # same phrase cited twice in one note
                        continue
                    seen.add(key)
                    rows.append((source, ch, v, span, script, r[0], r[1]))
                    stats[f'{source}/{script}: anchored'] += 1

        conn.executemany(
            "INSERT INTO note_word_anchors "
            "(source, chapter, verse, span_text, script, word_start, word_end) "
            "VALUES (?,?,?,?,?,?,?)", rows)
        conn.commit()

        verses = len({(r[1], r[2]) for r in rows})
        print(f"note_word_anchors: {len(rows)} anchors across {verses} verses\n")
        for k in sorted(stats):
            print(f"  {stats[k]:>6}  {k}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
