"""Recognise a search query that names a root, in the ways people type one.

Search used to decide what a query was from its shape alone, and "S-W-M" has
the shape of a five-letter English word: it led with verses matched by meaning
(the dense model paired the hyphenated letters with "Alif. Lam. Meem.") and
listed the root last. Two kinds of evidence now say "this query IS a root":

  spelled   the query spells the root's letters: "S-W-M", "s w m", "ṣ-w-m",
            "sh-k-r", "3-l-m", "Swm", "ص و م". Letters carry no meaning of
            their own, so verse search answers these with the root's own
            verses instead of embedding them.
  word      the query is a word of the root in Latin letters: "sawm", "siyam",
            "taqwa", "rahma". Resolved through the match keys of
            `word_translit` (translit.translit_key), the keys the note-citation
            aligner already uses, so "ṣawman" in 19:26 is what "sawm" finds.

Neither is claimed for an ordinary English word. Folded to root letters "elm"
spells ʿ-l-m, and "bad" is the key of baʿd; the English vocabulary (every word
of the site's English translation and word-by-word glosses) keeps those
English.
"""

from __future__ import annotations

import re
import sqlite3
import threading
import unicodedata
from collections import Counter
from itertools import product

from translit import translit_key

# The letters a root_buckwalter is written in (all 1,642 roots use only these;
# hamza is "A").
BW_ROOT_CHARS = set("$*ADEHSTZbdfghjklmnqrstvwxyz")

# One typed letter -> the Buckwalter root letters it can stand for. A plain
# "s" is ambiguous between س and ص because most people don't mark emphatics;
# a dotted "ṣ", or Buckwalter's own case ("S"), is not.
_LATIN = {
    'b': 'b', 't': 'tT', 'j': 'j', 'h': 'hH', 'd': 'dD', 'r': 'r', 'z': 'zZ',
    's': 'sS', 'f': 'f', 'q': 'q', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
    'w': 'w', 'y': 'y', 'g': 'gj', 'x': 'x', 'v': 'v', 'e': 'E', 'a': 'A',
    'ṣ': 'S', 'ḍ': 'D', 'ṭ': 'T', 'ẓ': 'Z', 'ḥ': 'H', 'ḫ': 'x', 'ḵ': 'x',
    'ẖ': 'x', 'ṯ': 'v', 'ḏ': '*', 'š': '$', 'ġ': 'g', 'ǧ': 'j', 'ǰ': 'j',
    'ā': 'A',
    # hamza and ʿayn marks, and the Arabizi digits for letters Latin lacks
    "'": 'A', 'ʾ': 'A', '’': 'A', 'ʼ': 'A', 'ˀ': 'A', '2': 'A',
    'ʿ': 'E', '‘': 'E', '`': 'E', 'ʕ': 'E', 'ˁ': 'E', '3': 'E',
    '7': 'H', '5': 'x', '6': 'T', '9': 'S',
    '$': '$', '*': '*',
}
# Two-letter spellings of one letter; only read as such when the letters are
# written apart ("sh-k-r"), since run together "shkr" could be s-h-k-r.
_DIGRAPHS = {'sh': '$', 'th': 'v', 'dh': '*', 'kh': 'x', 'gh': 'g'}

_SEP = re.compile(r'[\s\-‐‑‒–—―.·•_/,+،]+')
_AR_MARKS = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
_AR_FOLD = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ء': 'ا',
                          'ؤ': 'ا', 'ئ': 'ا', 'ى': 'ي'})
_AR_LETTER = re.compile(r'^[ء-ي]$')
_ASCII_VOWEL = re.compile(r'[aeiouAEIOU]')
_WORD_TOKEN = re.compile(r"^[^\W\d_]+(?:['’ʼ\-][^\W\d_]+)*$")


def is_mixed_case(q: str) -> bool:
    """Both cases present ("Swm", "rHm"): Buckwalter, where case is a letter."""
    letters = [c for c in q if c.isascii() and c.isalpha()]
    return any(c.isupper() for c in letters) and any(c.islower() for c in letters)


def _letter_options(seg: str, mixed: bool) -> str | None:
    """Candidate Buckwalter letters for one written-apart segment, or None if
    the segment isn't one letter."""
    low = seg.lower()
    if len(seg) == 2:
        return _DIGRAPHS.get(low)
    if len(seg) != 1:
        return None
    if mixed and seg.isascii() and seg.isalpha():
        if seg in BW_ROOT_CHARS:
            return seg
        return low if low in BW_ROOT_CHARS else None
    return _LATIN.get(low)


def _arabic_letters(q: str) -> tuple[str | None, str]:
    """('separated' | 'compact' | None, folded letters) for an Arabic query."""
    segs = [s for s in _SEP.split(_AR_MARKS.sub('', q)) if s]
    if not segs or not all(re.fullmatch(r'[ء-ي]+', s) for s in segs):
        return None, ''
    letters = ''.join(segs).translate(_AR_FOLD)
    if len(segs) >= 2 and all(_AR_LETTER.match(s) for s in segs):
        return 'separated', letters
    if len(segs) == 1:
        return 'compact', letters
    return None, ''


_ar_index: dict[str, list[str]] | None = None
_ar_index_src: int | None = None


def _roots_by_arabic(root_map: dict) -> dict[str, list[str]]:
    """Folded Arabic root letters ("صوم") -> root_buckwalter keys."""
    global _ar_index, _ar_index_src
    if _ar_index is None or _ar_index_src != len(root_map):
        idx: dict[str, list[str]] = {}
        for rbw, rar in root_map.items():
            key = (rar or '').replace(' ', '').translate(_AR_FOLD)
            if key:
                idx.setdefault(key, []).append(rbw)
        _ar_index, _ar_index_src = idx, len(root_map)
    return _ar_index


def spelled_roots(q: str, root_map: dict) -> tuple[str | None, list[str]]:
    """Read `q` as a root spelled out letter by letter.

    Returns (shape, roots). shape is 'separated' for letters written apart
    ("S-W-M", "ص و م"), 'compact' for a short run with no vowels ("swm",
    "ṣwm", "3lm", "صوم"), else None. roots are the existing roots it spells;
    empty when the shape fits but no root does ("x-q-z"). Only three or four
    letters count, as every root has three or four: two letters apart ("T H")
    are more likely Ṭā-Hā than a root.
    """
    q = unicodedata.normalize('NFC', (q or '').strip())
    if not q or len(q) > 24:
        return None, []

    if re.search(r'[؀-ۿ]', q):
        shape, letters = _arabic_letters(q)
        if shape is None or not 3 <= len(letters) <= 4:
            return None, []
        return shape, list(_roots_by_arabic(root_map).get(letters, []))

    mixed = is_mixed_case(q)
    segs = [s for s in _SEP.split(q) if s]
    if len(segs) >= 2:
        if not 3 <= len(segs) <= 4 or all(s.isdigit() for s in segs):
            return None, []
        options = [_letter_options(s, mixed) for s in segs]
        shape = 'separated'
    elif len(segs) == 1 and 3 <= len(q) <= 4:
        options = [_letter_options(c, mixed) for c in q]
        # Run together, only a vowel-less string reads as root letters ("ktb"),
        # the same rule the client's classifier applies. "Elm"/"Amn" are still
        # found by the exact Buckwalter match in the root search itself.
        if any(o is None for o in options) or _ASCII_VOWEL.search(q):
            return None, []
        shape = 'compact'
    else:
        return None, []
    if any(o is None for o in options):
        return None, []
    roots = [''.join(p) for p in product(*options)]
    return shape, [r for r in roots if r in root_map]


def spelled_query_roots(q: str, root_map: dict, conn) -> list[str] | None:
    """The roots `q` spells: letter by letter ("S-W-M", "ṣ w m", "ص و م",
    "ktb") or as a root's Buckwalter key ("Elm", "Swm"). None when it doesn't
    spell one; [] when it has the shape but no root fits ("x-q-z"). A run of
    letters that is also an English word ("why", "dew") doesn't count."""
    shape, roots = spelled_roots(q, root_map)
    if shape == 'separated':
        return roots
    english = is_english_word(q, conn)
    if shape == 'compact' and roots and not english:
        return roots
    key = (q or '').strip()
    exact = [r for r in root_map if r.lower() == key.lower()]
    if exact and not english:
        # Buckwalter's case is a letter: "Swm" is ص, so it names ṣ-w-m alone.
        return [r for r in exact if r == key] or exact
    return None


def named_roots(q: str, root_map: dict, conn) -> list[str]:
    """The roots a query names outright: spelled (spelled_query_roots) or as
    one of their words in Latin letters ("sawm", "taqwa"). Empty for anything
    else, English words included. A verse result highlights their words."""
    spelled = spelled_query_roots(q, root_map, conn)
    if spelled is not None:
        return spelled
    return [r for r, _n in word_roots(q, conn)]


def spelled_forms(q: str) -> set[str]:
    """The usual ways of writing a Latin letter-by-letter query ("s w m" ->
    {"s-w-m", "swm"}), for looking it up among the root aliases."""
    q = unicodedata.normalize('NFC', (q or '').strip()).lower()
    segs = [s for s in _SEP.split(q) if s]
    if len(segs) == 1:
        segs = list(segs[0])
    return {'-'.join(segs), ''.join(segs)}


# --- words of a root, typed in Latin letters -----------------------------------

_lock = threading.Lock()
_translit_index: dict[str, Counter] | None = None
_english: set[str] | None = None

# Everyday English words the site's own English never uses, whose spelling is
# nonetheless the key of a Qur'anic word ("ram" is ramā, "main" is ʿayn,
# "altar" is tarā) or a root's Buckwalter key ("dew" is d-ʿ-w). Found by
# running a 175k-word English dictionary through word_roots() and the root
# keys; of their hits these are the ones a reader would type as English.
# Arabic terms in that dictionary (kitab, imam, sura, shirk, halal, and tin for
# al-Tīn) are left out on purpose, as is "elm": the site writes ʿ-l-m "Elm".
_ENGLISH_EXTRA = frozenset("""
    ail alkali alt altar anti aqua arid ash ashy ass assay awl ball ballad ban
    bar bard bass bay bid bin bra bud bye dab dank dew dim dye fad fan fiat fry
    fuzz habit habitat hall harass hash hat haw hay hub hut jail jam jar jaw jazz
    kilt labia lad lamina lard layman libra limn lint llama lurid main mall mamma
    mania mat mill mitt mutt nab nut qua radii raffia ram raw ray rib rid rub rye
    safari sir sly stall tab tad tariff thaw tub tuba turf tusk tutu ward wasabi
    watt wry yak yam yard
""".split())


def _build(conn) -> None:
    """Build both lookups on first use (~77k words; well under a second)."""
    global _translit_index, _english
    with _lock:
        if _translit_index is not None and _english is not None:
            return
        idx: dict[str, Counter] = {}
        try:
            rows = conn.execute(
                "SELECT t.translit_key AS k, m.root_buckwalter AS r "
                "FROM word_translit t JOIN morphology m "
                "  ON m.chapter = t.chapter AND m.verse = t.verse "
                " AND m.word_pos = t.word_pos "
                "WHERE m.root_buckwalter IS NOT NULL AND m.root_buckwalter != '' "
                "  AND t.translit_key != ''"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []  # table not there yet: word matching just stays off
        for k, r in rows:
            idx.setdefault(k, Counter())[r] += 1
        english: set[str] = set()
        for sql in ("SELECT text_en FROM translations",
                    "SELECT translation_en FROM word_glosses"):
            try:
                for (text,) in conn.execute(sql):
                    if text:
                        english.update(re.findall(r'[a-z]+', text.lower()))
            except sqlite3.OperationalError:
                pass
        _translit_index, _english = idx, english


def is_english_word(q: str, conn) -> bool:
    """True when `q` is one word of the site's English (translation or
    word-by-word glosses)."""
    _build(conn)
    w = (q or '').strip().lower()
    return bool(w) and w.isascii() and w.isalpha() and (w in _english or w in _ENGLISH_EXTRA)


def word_roots(q: str, conn) -> list[tuple[str, int]]:
    """Roots whose Qur'anic words are spelled `q` in Latin letters, most
    frequent first, as (root_buckwalter, occurrences). Empty for anything that
    isn't one Latin word, or is English."""
    q = unicodedata.normalize('NFC', (q or '').strip())
    if len(q) < 3 or not _WORD_TOKEN.match(q) or re.search(r'[؀-ۿ]', q):
        return []
    if is_english_word(q, conn):
        return []
    keys = {translit_key(q)}
    # A final -a may be a tāʾ marbūṭa written without its h ("rahma" for
    # raḥmah); the stored keys keep that a, the bare query loses it.
    if q.lower().endswith('a'):
        keys.add(translit_key(q + 'h'))
    counts: Counter = Counter()
    for k in keys:
        if len(k) >= 3:
            counts.update(_translit_index.get(k, {}))
    ranked = counts.most_common()
    if not ranked:
        return []
    # Keys are lossy, so a common word's key also catches the odd word of
    # another root (jannah: j-n-n 125 times, j-n-ḥ once). Keep the roots the
    # spelling actually belongs to.
    floor = ranked[0][1] * 0.1
    return [(r, n) for r, n in ranked if n >= floor]
