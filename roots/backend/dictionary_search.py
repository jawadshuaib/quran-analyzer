"""Search for the Qur'anic Dictionary page (/dictionary): /api/dictionary/search.

A reader types whatever they have — a root in any notation, a word of the
Qur'an, a transliteration, an English meaning, or a sense they half-remember
from a dictionary — and gets the roots it points to, each with the reason it
matched. Every query runs through all of these arms; the scores are fused:

  identity   the query IS a root or a word of one
             - root notation, any spelling: kfr, k-f-r, k f r, K.F.R, Elm, $kr,
               ḥ-m-d, ʿ-l-m, 'lm, 3lm, 7md, ك ف ر, كفر, أمن / امن
             - an Arabic word of the Qur'an (vowelled or not, with clitics):
               كَفَرُوا, يعلمون, والكتاب
             - a transliterated word: kafaru, rahma, istighfar, jannah
  meaning    - curated English aliases (forgive -> غ ف ر)
             - the root's short gloss and semantic field
             - the classical dictionaries' own English (full-text), which knows
               senses no gloss mentions ("millet" -> د خ ن)
             - semantic similarity to the root's profile and to each dictionary
               entry (Voyage multilingual vectors when the key works, else the
               local MiniLM vectors, else skipped)

Constraints, mirroring search_v2: no network at import; nothing here may 5xx
— every arm degrades to "no signal" on error; the in-memory indices are built
lazily on first use and refreshed when the dictionary tables change. Derived
tables (dictionary_search_fts, root_search_vectors) are built per host by
build_dictionary_search_index.py; when absent those arms are simply off.
"""

import math
import os
import re
import sqlite3
import threading
import time
import unicodedata
from collections import Counter, defaultdict

import numpy as np

import translit

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "quran.db")

SHOWN = ("e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
         "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> ''")

# --------------------------------------------------------------------------
# Letters
# --------------------------------------------------------------------------
# Root ids are Buckwalter with one letter per radical; a hamza radical is 'A'
# and is written ا in root_arabic. The mapping is one-to-one.
AR2BW = {
    "ا": "A", "ب": "b", "ت": "t", "ث": "v", "ج": "j", "ح": "H", "خ": "x", "د": "d",
    "ذ": "*", "ر": "r", "ز": "z", "س": "s", "ش": "$", "ص": "S", "ض": "D", "ط": "T",
    "ظ": "Z", "ع": "E", "غ": "g", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m",
    "ن": "n", "ه": "h", "و": "w", "ي": "y",
    # hamza carriers and alif variants all stand for the hamza radical
    "أ": "A", "إ": "A", "آ": "A", "ٱ": "A", "ء": "A", "ؤ": "A", "ئ": "A",
    "ى": "y",
}
BW_LETTERS = set("AbtvjHxd*rzs$SDTZEgfqklmnhwy")
# Buckwalter hamza spellings a user might paste
BW_HAMZA = {">": "A", "<": "A", "|": "A", "{": "A", "'": "A", "&": "A", "}": "A", "Y": "y"}

_AR_CHAR = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
_AR_DIAC = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_SEPARATORS = re.compile(r"[\s\-‐‑‒–—_.,/\\|·•+:;()\[\]{}<>]+")

# Latin spellings of one radical -> [(buckwalter letter, penalty)]. Penalty 0
# is the plain reading; >0 is a looser one (an undotted s read as ص, k read as
# ق). Frequency breaks ties between equally plausible readings.
LATIN_UNITS = {
    "th": [("v", 0)], "kh": [("x", 0)], "dh": [("*", 0), ("Z", 1), ("D", 2)],
    "sh": [("$", 0)], "gh": [("g", 0)], "ch": [("$", 2)],
    "b": [("b", 0)], "t": [("t", 0), ("T", 1)], "j": [("j", 0)],
    "h": [("h", 0), ("H", 0)], "d": [("d", 0), ("D", 1)], "r": [("r", 0)],
    "z": [("z", 0), ("Z", 1), ("*", 2)], "s": [("s", 0), ("S", 1)],
    "f": [("f", 0)], "q": [("q", 0)], "k": [("k", 0), ("q", 2)],
    "l": [("l", 0)], "m": [("m", 0)], "n": [("n", 0)], "w": [("w", 0)],
    "y": [("y", 0)], "g": [("g", 1), ("j", 1)], "v": [("v", 0)], "x": [("x", 0)],
    "c": [("k", 2)], "p": [("b", 2)],
    # scholarly transliteration
    "ḥ": [("H", 0)], "ṣ": [("S", 0)], "ḍ": [("D", 0)], "ṭ": [("T", 0)],
    "ẓ": [("Z", 0)], "ṯ": [("v", 0)], "ḫ": [("x", 0)], "ẖ": [("x", 0)],
    "ḏ": [("*", 0)], "š": [("$", 0)], "ġ": [("g", 0)], "ǧ": [("j", 0)],
    "ĝ": [("j", 0)], "ž": [("Z", 1)],
    # hamza and ʿayn marks (and what people type for them)
    "ʾ": [("A", 0)], "ʼ": [("A", 0)], "ˀ": [("A", 0)], "´": [("A", 0)],
    "'": [("A", 0), ("E", 1)], "’": [("A", 0), ("E", 1)],
    "ʿ": [("E", 0)], "ʻ": [("E", 0)], "ˁ": [("E", 0)], "`": [("E", 0)],
    "‘": [("E", 0), ("A", 1)],
    # a vowel standing for a whole radical (a-m-n, e-l-m)
    "a": [("A", 0)], "ā": [("A", 0)], "â": [("A", 0)], "e": [("E", 0), ("A", 1)],
    "i": [("A", 1), ("y", 1)], "ī": [("y", 0)], "u": [("w", 1), ("A", 1)],
    "ū": [("w", 0)], "o": [("w", 1)],
    # Arabizi digits
    "3'": [("g", 0)], "7'": [("x", 0)], "6'": [("Z", 0)], "9'": [("D", 0)],
    "2": [("A", 0)], "3": [("E", 0)], "5": [("x", 0)], "6": [("T", 0)],
    "7": [("H", 0)], "8": [("g", 1), ("q", 1)], "9": [("S", 0)], "4": [("$", 1)],
}
_UNIT_KEYS = sorted(LATIN_UNITS, key=len, reverse=True)
_VOWELS = set("aeiouāīūâêîôûáéíóúàèìòù")

STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "is", "are",
    "be", "as", "at", "by", "from", "it", "its", "that", "this", "which", "who",
    "root", "roots", "word", "words", "meaning", "means", "arabic", "quran", "qur'an",
    "something", "someone", "one", "thing", "what", "how",
}


def _fold(s):
    """Lowercase + strip combining marks, keeping the scholarly letters whole:
    ḥ ṣ ḍ ṭ ẓ are looked up before folding, so this is only for words."""
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def _stem(w):
    """A small English stemmer — enough to meet 'forgiveness', 'forgiving',
    'forgave'? (no) half way: suffixes only."""
    w = w.lower()
    for suf, rep in (("iness", "y"), ("fulness", ""), ("ousness", ""), ("iveness", "ive"),
                     ("ness", ""), ("ments", ""), ("ment", ""), ("ings", ""), ("ing", ""),
                     ("ities", ""), ("ity", ""), ("ies", "y"), ("ied", "y"), ("ers", ""),
                     ("er", ""), ("edly", ""), ("ed", ""), ("ly", ""), ("ful", ""),
                     ("es", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)] + rep
            break
    if w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w


_WORD_RE = re.compile(r"[a-zA-ZÀ-ɏḀ-ỿ]+")


def _en_tokens(s):
    return [t.lower() for t in _WORD_RE.findall(_fold(s or ""))]


# --------------------------------------------------------------------------
# The index (lazy; refreshed when the dictionary tables change)
# --------------------------------------------------------------------------
class _Index:
    pass


_idx = None
_idx_lock = threading.Lock()
_idx_checked = 0.0
_REFRESH_EVERY = 300


def _connect():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def _signature(conn):
    r = conn.execute(
        "SELECT COUNT(*), COALESCE(MAX(id),0), COALESCE(MAX(edited_at),'') FROM dictionary_entries e WHERE "
        + SHOWN).fetchone()
    try:
        v = conn.execute("SELECT COUNT(*), COALESCE(MAX(rowid),0) FROM root_search_vectors").fetchone()
    except sqlite3.OperationalError:
        v = (0, 0)
    return (r[0], r[1], r[2], v[0], v[1])


def _clean_gloss(g):
    try:
        import app
        return app._clean_root_gloss(g)
    except Exception:
        return (g or "").strip() or None


def _build(conn, sig):
    ix = _Index()
    ix.sig = sig
    # roots with displayed entries
    rows = conn.execute(
        "SELECT e.root_buckwalter AS bw, MAX(e.root_arabic) AS ar, COUNT(*) AS n FROM dictionary_entries e WHERE "
        + SHOWN + " GROUP BY e.root_buckwalter").fetchall()
    ix.roots = {}
    for r in rows:
        ix.roots[r["bw"]] = {"bw": r["bw"], "arabic": (r["ar"] or "").replace(" ", ""), "entries": r["n"],
                             "gloss": None, "field": "", "freq": 0}
    for r in conn.execute("SELECT root_buckwalter, COUNT(*) FROM morphology WHERE root_buckwalter IS NOT NULL "
                          "GROUP BY root_buckwalter"):
        if r[0] in ix.roots:
            ix.roots[r[0]]["freq"] = r[1]
    try:
        for r in conn.execute("SELECT root_buckwalter, primary_meaning, semantic_field FROM ai_root_meanings "
                              "ORDER BY id"):
            d = ix.roots.get(r[0])
            if d and d["gloss"] is None:
                d["gloss"] = _clean_gloss(r[1])
                d["field"] = (r[2] or "")
    except sqlite3.OperationalError:
        pass
    for d in ix.roots.values():
        text = " ".join(filter(None, [d["gloss"], d["field"]]))
        d["gloss_stems"] = {_stem(t) for t in _en_tokens(text) if t not in STOPWORDS}
        d["gloss_text"] = _fold(text)

    # words of the Qur'an -> roots (per word position, then by spelling key)
    word_root = {}
    for r in conn.execute("SELECT chapter, verse, word_pos, root_buckwalter FROM morphology "
                          "WHERE root_buckwalter IS NOT NULL AND root_buckwalter <> ''"):
        word_root[(r[0], r[1], r[2])] = r[3]
    ix.ar_words = defaultdict(Counter)   # arabic_key -> roots
    ix.tr_words = defaultdict(Counter)   # translit_key -> roots
    ix.word_example = {}                 # (key, root) -> displayed spelling
    try:
        for r in conn.execute("SELECT chapter, verse, word_pos, translit, translit_key, arabic_plain, arabic_key "
                              "FROM word_translit"):
            root = word_root.get((r[0], r[1], r[2]))
            if not root or root not in ix.roots:
                continue
            if r["arabic_key"]:
                ix.ar_words[r["arabic_key"]][root] += 1
                ix.word_example.setdefault(("ar", r["arabic_key"], root), r["arabic_plain"])
            if r["translit_key"]:
                ix.tr_words[r["translit_key"]][root] += 1
                ix.word_example.setdefault(("tr", r["translit_key"], root), r["translit"])
    except sqlite3.OperationalError:
        pass
    # lemmas (dictionary headwords as a reader might type them)
    ix.ar_lemmas = defaultdict(Counter)
    for r in conn.execute("SELECT lemma_arabic, root_buckwalter, COUNT(*) FROM morphology "
                          "WHERE root_buckwalter IS NOT NULL AND lemma_arabic IS NOT NULL "
                          "GROUP BY lemma_arabic, root_buckwalter"):
        if r[1] in ix.roots:
            k = translit.arabic_key(r[0])
            if k:
                ix.ar_lemmas[k][r[1]] += r[2]

    # aliases (curated English words and phrases, some transliterations)
    ix.alias = defaultdict(list)
    ix.alias_stem = defaultdict(set)
    try:
        for r in conn.execute("SELECT alias, root_buckwalter, source FROM root_search_aliases"):
            if r[1] not in ix.roots or not r[0]:
                continue
            a = _fold(r[0]).strip()
            ix.alias[a].append((r[1], r[2]))
            toks = [t for t in _en_tokens(a) if t not in STOPWORDS]
            if len(toks) == 1:
                ix.alias_stem[_stem(toks[0])].add(r[1])
    except sqlite3.OperationalError:
        pass

    # which optional arms exist on this host
    try:
        conn.execute("SELECT 1 FROM dictionary_search_fts LIMIT 1").fetchone()
        ix.has_fts = True
    except sqlite3.OperationalError:
        ix.has_fts = False
    ix.vectors = {}
    try:
        models = [r[0] for r in conn.execute("SELECT DISTINCT model_name FROM root_search_vectors")]
    except sqlite3.OperationalError:
        models = []
    ix.vector_models = models
    ix.dict_names = {r[0]: r[1] for r in conn.execute("SELECT slug, name_en FROM dictionaries")}
    return ix


def warm_up():
    """Build the index in the background (called when the Dictionary page
    loads its root list, so it is ready by the time the reader types)."""
    if _idx is not None:
        return
    threading.Thread(target=_index, name="dictionary-search-warmup", daemon=True).start()


def _index():
    """The current index, rebuilt at most every _REFRESH_EVERY seconds when
    the underlying tables changed. Returns None if it can't be built."""
    global _idx, _idx_checked
    now = time.time()
    if _idx is not None and now - _idx_checked < _REFRESH_EVERY:
        return _idx
    if not _idx_lock.acquire(timeout=15):
        return _idx
    try:
        if _idx is not None and time.time() - _idx_checked < _REFRESH_EVERY:
            return _idx
        conn = _connect()
        try:
            sig = _signature(conn)
            if _idx is None or _idx.sig != sig:
                _idx = _build(conn, sig)
                _vec_cache.clear()
        finally:
            conn.close()
        _idx_checked = time.time()
        return _idx
    except Exception as e:  # never let the page 5xx
        print(f"[dictionary_search] index build failed: {e}")
        return _idx
    finally:
        _idx_lock.release()


# --------------------------------------------------------------------------
# Identity arms
# --------------------------------------------------------------------------
def _freq_bonus(ix, bw):
    return min(20.0, 2.0 * math.log2(ix.roots[bw]["freq"] + 1))


def _latin_units(s):
    """All ways to read a Latin string as a sequence of radical spellings.
    Returns a list of unit lists (digraphs optional: 'kh' as خ or as k+h)."""
    out = []

    def rec(i, acc):
        if len(acc) > 5 or len(out) > 64:
            return
        if i == len(s):
            if 2 <= len(acc) <= 5:
                out.append(list(acc))
            return
        for u in _UNIT_KEYS:
            if s.startswith(u, i):
                acc.append(u)
                rec(i + len(u), acc)
                acc.pop()

    rec(0, [])
    return out


def _expand(units, cap=400):
    """Unit spellings -> candidate root keys with a penalty each."""
    combos = [("", 0)]
    for u in units:
        opts = LATIN_UNITS.get(u)
        if not opts:
            return []
        combos = [(k + b, p + q) for k, p in combos for b, q in opts][:cap]
    return combos


def _root_notation(ix, q, hits):
    raw = q.strip()
    if not raw or len(raw) > 24:
        return
    # 1. Buckwalter exactly as typed (case matters: rHm vs rhm, Elm, $kr)
    bw = "".join(BW_HAMZA.get(ch, ch) for ch in _SEPARATORS.sub("", raw))
    if bw in ix.roots and re.search(r"[A-Z$*'>|<{&}]", raw):
        # Uppercase or $ * ' mark Buckwalter (rHm, Elm, $kr). An all-lowercase
        # string is read phonetically below, where "hmd" can be ح as well as ه.
        hits.add(bw, 1000, "root", "Root id " + bw)

    # 2. Arabic letters (ك ف ر, كفر, ك-ف-ر, أمن)
    if _AR_CHAR.search(raw):
        # only the Arabic: "the root ر ح م" is a root, whatever surrounds it
        letters = "".join(ch for ch in _AR_DIAC.sub("", raw) if ch in AR2BW)
        if 2 <= len(letters) <= 5 and all(ch in AR2BW for ch in letters):
            key = "".join(AR2BW[ch] for ch in letters)
            if key in ix.roots:
                spaced = len(_SEPARATORS.findall(raw)) > 0
                hits.add(key, 985 if spaced or len(letters) == 3 else 960, "root",
                         "Root letters " + " ".join(ix.roots[key]["arabic"]))
        return

    # 3. Latin: each radical spelled out (k-f-r, ḥ-m-d, 'lm, 3lm, KFR, khlq)
    lower = raw.lower()
    parts = [p for p in _SEPARATORS.split(lower) if p]
    unit_lists = []
    if len(parts) >= 2 and all(p in LATIN_UNITS for p in parts):
        unit_lists.append(parts)                 # explicitly separated radicals
    joined = "".join(parts)
    if 2 <= len(joined) <= 10:
        unit_lists.extend(_latin_units(joined))  # an unseparated string
    seen = {}
    for units in unit_lists:
        separated = units is parts
        for key, pen in _expand(units):
            if key in ix.roots:
                has_vowel_unit = any(u in _VOWELS for u in units)
                score = (955 if separated else 935) - 8 * pen - (60 if has_vowel_unit and not separated else 0)
                score += _freq_bonus(ix, key)
                if score > seen.get(key, -1):
                    seen[key] = score
    for key, score in seen.items():
        hits.add(key, score, "root", "Root " + "-".join(_translit_root(key)))


_BW2LATIN = {"A": "ʾ", "b": "b", "t": "t", "v": "th", "j": "j", "H": "ḥ", "x": "kh", "d": "d",
             "*": "dh", "r": "r", "z": "z", "s": "s", "$": "sh", "S": "ṣ", "D": "ḍ", "T": "ṭ",
             "Z": "ẓ", "E": "ʿ", "g": "gh", "f": "f", "q": "q", "k": "k", "l": "l", "m": "m",
             "n": "n", "h": "h", "w": "w", "y": "y"}


def _translit_root(bw):
    return [_BW2LATIN.get(ch, ch) for ch in bw]


def _arabic_word(ix, q, hits):
    """An Arabic word of the Qur'an (any vowelling, clitics) -> its root."""
    if not _AR_CHAR.search(q):
        return
    for tok in q.split():
        plain = _AR_DIAC.sub("", tok)
        # modern spelling -> the Qur'an's (Uthmani) spelling of the same word:
        # الصلاة/الزكاة/الحياة are written with a waw there (الصلوة, الزكوة, الحيوة)
        spellings = [plain]
        if re.search(r"اة$", plain):
            spellings.append(plain[:-2] + "وة")
        found = False
        for sp in spellings:
            key = translit.arabic_key(sp)
            if not key or len(key) < 2:
                continue
            found = _lookup_ar_key(ix, key, tok, hits) or found
        if not found:
            _skeleton_arabic(ix, tok, hits)


def _lookup_ar_key(ix, key, tok, hits):
    found = False
    if True:
        for table, label, base in ((ix.ar_words, "Qurʾānic word", 900), (ix.ar_lemmas, "Word", 870)):
            c = table.get(key)
            if not c:
                continue
            total = sum(c.values())
            for root, n in c.most_common(4):
                share = n / total
                ex = ix.word_example.get(("ar", key, root)) or tok
                hits.add(root, base * (0.75 + 0.25 * share), "word", f"{label} {ex}")
                found = True
    return found


_AR_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك", "س")
_AR_SUFFIXES = ("كما", "هما", "تما", "هم", "هن", "كم", "كن", "نا", "ها", "ون", "ين", "ان", "ات", "وا",
                "تم", "ه", "ك", "ي", "ة", "ت", "ا", "ن")


def _skeleton_arabic(ix, tok, hits):
    """No known word: strip likely clitics and look for a root whose letters
    run through what is left, in order (a weak guess; ranked below identity)."""
    w = "".join(AR2BW.get(ch, "") for ch in _AR_DIAC.sub("", tok))
    if len(w) < 3:
        return
    stems = {w}
    ar = _AR_DIAC.sub("", tok)
    for p in _AR_PREFIXES:
        if ar.startswith(p) and len(ar) - len(p) >= 3:
            stems.add("".join(AR2BW.get(ch, "") for ch in ar[len(p):]))
    for s in list(stems):
        for suf in _AR_SUFFIXES:
            sbw = "".join(AR2BW.get(ch, "") for ch in suf)
            if s.endswith(sbw) and len(s) - len(sbw) >= 3:
                stems.add(s[: -len(sbw)])
    _skeleton_match(ix, stems, hits, "Arabic letters")


def _skeleton_match(ix, stems, hits, why, base=700):
    best = {}
    for s in stems:
        if s in ix.roots:
            sc = base + 20 + _freq_bonus(ix, s)
            if sc > best.get(s, 0):
                best[s] = sc
            continue
        n = len(s)
        if n > 9:
            continue
        # contiguous 3- and 4-letter runs, then gapped subsequences
        for L in (4, 3):
            for i in range(0, n - L + 1):
                k = s[i:i + L]
                if k in ix.roots:
                    sc = base - 10 * (n - L) + _freq_bonus(ix, k)
                    if sc > best.get(k, 0):
                        best[k] = sc
        if n <= 7:
            import itertools
            for comb in itertools.combinations(range(n), 3):
                k = "".join(s[i] for i in comb)
                if k in ix.roots:
                    gaps = comb[2] - comb[0] - 2
                    sc = base - 60 - 15 * gaps - 8 * (n - 3) + _freq_bonus(ix, k)
                    if sc > best.get(k, 0):
                        best[k] = sc
    for k, sc in best.items():
        hits.add(k, sc, "guess", f"{why} contain {'-'.join(_translit_root(k))}")


_LAT_PREFIXES = ("al-", "el-", "al", "el", "wal", "fal", "bil", "lil", "wa", "fa", "bi", "li", "ist", "mus",
                 "mu", "ma", "ta", "ya", "tu", "yu", "na", "nu", "i", "a")
_LAT_SUFFIXES = ("iyyah", "iyya", "iyyat", "ūna", "īna", "una", "ina", "oon", "een", "uun", "iin", "ūn", "īn",
                 "un", "in", "an", "at", "ah", "āt", "iyy", "īy", "ī", "ā", "a", "u", "i", "h", "t", "n")


def _latin_word(ix, q, hits):
    """A transliterated word (kafaru, rahmah, istighfar, jannat) -> root."""
    if _AR_CHAR.search(q):
        return
    toks = [t for t in re.split(r"\s+", q.strip()) if t]
    if not toks or len(toks) > 3:
        return
    for tok in toks:
        low = tok.lower()
        if len(low) < 3 or not re.search(r"[a-zʾʿ'’`āīūḥṣḍṭẓ]", low):
            continue
        # 1. a spelling of a Qur'anic word (the corpus' own romanization keys)
        low = re.sub(r"ee|ei|ie", "i", low)
        low = re.sub(r"oo|ou", "u", low)
        low = re.sub(r"aa", "a", low)
        variants = {low, low + "h", low + "t", low + "a", low + "u", low + "i"}
        if low.endswith("h") or low.endswith("t"):
            variants.add(low[:-1])
        if len(low) > 4 and low[0] in "ia":
            # the verse writes wasl forms without their opening vowel:
            # istighfār -> (wa-mā kāna) stighfāru
            variants |= {v[1:] for v in list(variants)}
        keys = {translit.translit_key(v) for v in variants}
        keys.discard("")
        matched = False
        for key in keys:
            c = ix.tr_words.get(key)
            if not c or len(key) < 3:
                continue
            total = sum(c.values())
            for root, n in c.most_common(3):
                share = n / total
                ex = ix.word_example.get(("tr", key, root)) or tok
                exact = translit.translit_key(low) == key
                hits.add(root, (880 if exact else 850) * (0.75 + 0.25 * share), "word",
                         f"Qurʾānic word {ex}")
                matched = True
        # 2. consonant skeleton after likely affixes (a weaker guess)
        _latin_skeleton(ix, low, hits, weak=matched)


def _latin_skeleton(ix, low, hits, weak=False):
    word = _fold(low).replace("-", "")
    word = re.sub(r"(.)\1+", r"\1\1", word)
    stems = {word}
    for p in _LAT_PREFIXES:
        if word.startswith(p.replace("-", "")) and len(word) - len(p) >= 3:
            stems.add(word[len(p.replace("-", "")):])
    for s in list(stems):
        for suf in _LAT_SUFFIXES:
            if s.endswith(suf) and len(s) - len(suf) >= 2:
                stems.add(s[: -len(suf)])
    cands = set()
    for s in stems:
        # drop vowels except a word-initial one (which stands for a hamza)
        cons = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch in "aeiou":
                if i == 0:
                    cons.append("a")
                i += 1
                continue
            cons.append(ch)
            i += 1
        cs = "".join(cons)
        for units in _latin_units(cs) if 2 <= len(cs) <= 10 else []:
            # weak radicals hidden in long vowels: q_l -> qwl / qyl, h_d -> hdy
            unit_sets = [units]
            if len(units) == 2:
                a, b = units
                unit_sets += [[a, "w", b], [a, "y", b], [a, b, "w"], [a, b, "y"], ["w", a, b], [a, b, b]]
            for us in unit_sets:
                for key, pen in _expand(us, cap=120):
                    if 3 <= len(key) <= 4:
                        cands.add((key, pen, len(us) != len(units)))
    best = {}
    for key, pen, weakened in cands:
        if key in ix.roots:
            sc = (600 if weak else 680) - 8 * pen - (30 if weakened else 0) + _freq_bonus(ix, key)
            if sc > best.get(key, 0):
                best[key] = sc
        elif 5 <= len(key) <= 7 and not weakened:
            # a derived form with its affixes still on (istighfar -> ʾ s t gh f r):
            # a contiguous three-letter run is the likeliest root
            for i in range(len(key) - 2):
                k = key[i:i + 3]
                if k in ix.roots:
                    sc = (560 if weak else 620) - 8 * pen - 12 * (len(key) - 3) + (15 if i == len(key) - 3 else 0) \
                        + _freq_bonus(ix, k)
                    if sc > best.get(k, 0):
                        best[k] = sc
    for k, sc in best.items():
        hits.add(k, sc, "guess", f"Consonants of “{low}” point to {'-'.join(_translit_root(k))}")


# --------------------------------------------------------------------------
# Meaning arms
# --------------------------------------------------------------------------
def _meaning_query(q):
    return [t for t in _en_tokens(q) if t not in STOPWORDS]


def _aliases(ix, q, hits):
    if _AR_CHAR.search(q):
        return
    a = _fold(q).strip()
    for root, source in ix.alias.get(a, []):
        hits.add(root, 800 if source == "ai" else 780, "alias", f"“{q.strip()}”")
    toks = _meaning_query(q)
    if len(toks) == 1:
        for root in ix.alias_stem.get(_stem(toks[0]), ()):
            hits.add(root, 640, "alias", f"“{toks[0]}”")


def _typo(ix, q, hits):
    import difflib
    toks = _meaning_query(q)
    if len(toks) != 1 or len(toks[0]) < 5 or _AR_CHAR.search(q):
        return
    t = toks[0]
    if not hasattr(ix, "alias_vocab"):
        vocab = defaultdict(list)
        for a in ix.alias:
            if a.isalpha() and len(a) >= 4:
                vocab[a[0]].append(a)
        ix.alias_vocab = vocab
    pool = ix.alias_vocab.get(t[0], []) + ix.alias_vocab.get(t[1], [])
    for m in difflib.get_close_matches(t, pool, n=2, cutoff=0.8):
        for root, source in ix.alias.get(m, []):
            hits.add(root, 600 if source == "ai" else 580, "alias", f"“{m}” (spelling corrected)")


def _gloss(ix, q, hits):
    toks = _meaning_query(q)
    if not toks or _AR_CHAR.search(q):
        return
    stems = [_stem(t) for t in toks]
    phrase = " ".join(toks)
    for bw, d in ix.roots.items():
        if not d["gloss_stems"]:
            continue
        got = sum(1 for s in stems if s in d["gloss_stems"])
        if not got:
            continue
        frac = got / len(stems)
        sc = 420 + 140 * frac
        if len(toks) > 1 and phrase in d["gloss_text"]:
            sc += 40
        if frac == 1.0 and d["gloss"] and _stem(_en_tokens(d["gloss"])[0] if _en_tokens(d["gloss"]) else "") in stems:
            sc += 20  # the gloss leads with it
        hits.add(bw, sc + _freq_bonus(ix, bw) * 0.5, "gloss", d["gloss"] or "")


def _fts_query(toks):
    safe = [re.sub(r"[^a-z]", "", t) for t in toks]
    safe = [t for t in safe if len(t) >= 2]
    return safe


def _dictionary_text(ix, q, hits):
    """The dictionaries' own English (full text, porter-stemmed)."""
    if not ix.has_fts or _AR_CHAR.search(q):
        return
    toks = _fts_query(_meaning_query(q))
    if not toks or len(toks) > 8:
        return
    conn = _connect()
    try:
        rows = []
        for expr in (" AND ".join(toks), " OR ".join(toks)) if len(toks) > 1 else (toks[0],):
            try:
                rows = conn.execute(
                    "SELECT root_bw, dictionary_slug, bm25(dictionary_search_fts) AS s, "
                    "snippet(dictionary_search_fts, 2, '«', '»', '…', 14) AS snip "
                    "FROM dictionary_search_fts WHERE dictionary_search_fts MATCH ? "
                    "ORDER BY s LIMIT 400", (expr,)).fetchall()
            except sqlite3.OperationalError:
                rows = []
            if rows:
                break
    finally:
        conn.close()
    if not rows:
        return
    per_root = defaultdict(list)
    for r in rows:
        if r["root_bw"] in ix.roots:
            per_root[r["root_bw"]].append(r)
    if not per_root:
        return
    # A term every other entry mentions says little; one a handful mention
    # says a lot. Scale by how concentrated the hits are.
    spread = len(per_root)
    concentration = 1.0 if spread <= 5 else max(0.35, 1.0 - math.log10(spread / 5) / 2)
    # strength and breadth together: the three best entries per root (bm25 is
    # negative, lower = better), so one entry built around the word beats a
    # passing mention in many
    def strength(rs):
        # measured on the eval's dictionary-sense queries: the plain sum beat
        # both a breadth bonus and a "defined up front" bonus
        return sum(sorted(-x["s"] for x in rs)[-3:])
    ranked = sorted(per_root.items(), key=lambda kv: -strength(kv[1]))
    # one root whose entries are clearly about the word (sieve -> ن خ ل)
    # beats a crowd of passing mentions
    clear = len(ranked) == 1 or strength(ranked[0][1]) >= 1.3 * strength(ranked[1][1])
    for rank, (bw, rs) in enumerate(ranked[:40]):
        ndicts = len({x["dictionary_slug"] for x in rs})
        sc = 350 + 190 * concentration / (1.0 + 0.45 * rank) + 5 * min(ndicts, 4)
        if rank == 0 and clear:
            sc += 90
        best = min(rs, key=lambda x: x["s"])
        hits.add(bw, sc, "dictionary", ix.dict_names.get(best["dictionary_slug"], ""),
                 dictionary_slug=best["dictionary_slug"], snippet=_clean_snip(best["snip"]),
                 extra=f"{ndicts} dictionar{'y' if ndicts == 1 else 'ies'}")


def _clean_snip(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    s = s.replace("**", "")
    return s[:220]


# --- semantic arm ----------------------------------------------------------
_vec_cache = {}
_vec_lock = threading.Lock()
_DENSE_FLOOR = {"voyage": 0.30, "minilm": 0.28}
_DENSE_CEIL = {"voyage": 0.62, "minilm": 0.60}


def _load_vectors(model_name):
    with _vec_lock:
        if model_name in _vec_cache:
            return _vec_cache[model_name]
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT root_bw, doc_type, dictionary_slug, dim, embedding FROM root_search_vectors "
                "WHERE model_name = ?", (model_name,)).fetchall()
        except sqlite3.OperationalError:
            rows = []
        finally:
            conn.close()
        if not rows:
            _vec_cache[model_name] = None
            return None
        dim = rows[0]["dim"]
        keep = [r for r in rows if r["dim"] == dim]
        mat = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in keep])
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        mat = (mat / norms).astype(np.float32)
        meta = [(r["root_bw"], r["doc_type"], r["dictionary_slug"]) for r in keep]
        _vec_cache[model_name] = (mat, meta, dim)
        return _vec_cache[model_name]


def _embed(ix, q):
    """(family, model_name, vector) for the best available model, or None."""
    try:
        import search_v2
        vname = search_v2.active_model_name()
        if vname and vname in ix.vector_models:
            v = search_v2.embed_query(q)
            if v is not None:
                return "voyage", vname, np.asarray(v, dtype=np.float32)
    except Exception:
        pass
    try:
        import app
        mname = getattr(app, "_SEMANTIC_MODEL_NAME", "all-MiniLM-L6-v2")
        if mname in ix.vector_models and not _AR_CHAR.search(q):
            model = app._get_embedding_model()
            if model is not None:
                v = model.encode([q], normalize_embeddings=True)[0]
                return "minilm", mname, np.asarray(v, dtype=np.float32)
    except Exception:
        pass
    return None


def _semantic(ix, q, hits, info):
    if not ix.vector_models or len(q.strip()) < 3:
        return
    got = _embed(ix, q)
    if not got:
        return
    family, model_name, qv = got
    if family == "minilm" and _AR_CHAR.search(q):
        return  # MiniLM is an English model; Arabic queries give it noise
    loaded = _load_vectors(model_name)
    if not loaded:
        return
    mat, meta, dim = loaded
    if qv.shape[0] != dim:
        return
    sims = mat @ qv
    floor, ceil = _DENSE_FLOOR[family], _DENSE_CEIL[family]
    order = np.argsort(-sims)[:400]
    best = {}
    for i in order:
        s = float(sims[i])
        if s < floor:
            break
        bw, doc_type, slug = meta[i]
        if bw not in ix.roots:
            continue
        if bw not in best or s > best[bw][0]:
            best[bw] = (s, doc_type, slug)
    info["dense"] = family
    for bw, (s, doc_type, slug) in best.items():
        norm = max(0.0, min(1.0, (s - floor) / (ceil - floor)))
        sc = 300 + 380 * norm
        if doc_type == "entry" and slug:
            hits.add(bw, sc, "semantic", ix.dict_names.get(slug, ""), dictionary_slug=slug)
        else:
            hits.add(bw, sc, "semantic", "")


# --------------------------------------------------------------------------
# Fusion
# --------------------------------------------------------------------------
_KIND_ORDER = ("root", "word", "alias", "gloss", "dictionary", "semantic", "guess")


class _Hits:
    def __init__(self):
        self.best = {}                    # bw -> best score
        self.reasons = defaultdict(dict)  # bw -> kind -> reason (best of that kind)

    def add(self, bw, score, kind, label, dictionary_slug=None, snippet=None, extra=None):
        if score > self.best.get(bw, 0):
            self.best[bw] = score
        cur = self.reasons[bw].get(kind)
        if cur is None or score > cur["score"]:
            r = {"kind": kind, "label": label, "score": score}
            if dictionary_slug:
                r["dictionary_slug"] = dictionary_slug
            if snippet:
                r["snippet"] = snippet
            if extra:
                r["detail"] = extra
            self.reasons[bw][kind] = r

    def cap(self, kind, ceiling, only_if_best=False):
        """Lower one kind of evidence to at most `ceiling` (recomputing each
        root's best score). only_if_best: touch roots where it is the lead."""
        for bw, kinds in self.reasons.items():
            r = kinds.get(kind)
            if not r or r["score"] <= ceiling:
                continue
            if only_if_best and max(x["score"] for x in kinds.values()) != r["score"]:
                continue
            r["score"] = ceiling
            self.best[bw] = max(x["score"] for x in kinds.values())

    def ranked(self):
        out = []
        for bw, top in self.best.items():
            kinds = self.reasons[bw]
            # agreement between independent arms is worth a little
            meaning = [k for k in ("alias", "gloss", "dictionary", "semantic") if k in kinds]
            bonus = 25 * max(0, len(meaning) - 1)
            out.append((top + bonus, bw))
        out.sort(key=lambda x: -x[0])
        return out


def search(q, limit=30):
    """Returns {"results": [...], "engine": {...}} — never raises."""
    q = (q or "").strip()[:200]
    info = {"lexical": True, "dense": None, "fts": False}
    if not q:
        return {"query": q, "results": [], "engine": info}
    ix = _index()
    if ix is None:
        return {"query": q, "results": [], "engine": info, "degraded": True}
    info["fts"] = ix.has_fts
    hits = _Hits()
    for arm in (_root_notation, _arabic_word, _latin_word, _aliases, _gloss, _dictionary_text):
        try:
            arm(ix, q, hits)
        except Exception as e:
            print(f"[dictionary_search] {arm.__name__} failed for {q!r}: {e}")
    try:
        _semantic(ix, q, hits, info)
    except Exception as e:
        print(f"[dictionary_search] semantic failed for {q!r}: {e}")
    # a misspelt English word ("patiance"): nothing lexical matched, so try
    # the nearest curated English word
    if not any(k in ("root", "word", "alias", "gloss", "dictionary") for kinds in hits.reasons.values() for k in kinds):
        try:
            _typo(ix, q, hits)
        except Exception as e:
            print(f"[dictionary_search] typo failed for {q!r}: {e}")

    # A query that IS a root notation (kfr, k-f-r) is about that root; an
    # alias that happens to spell the same string for another root (the AI
    # aliases map "kfr" to ن ك ر as well) should not sit beside it.
    if any(r.get("root", {}).get("score", 0) >= 930 for r in hits.reasons.values()):
        hits.cap("alias", 560, only_if_best=True)
    # Consonant-skeleton guesses must not outrank genuine meaning evidence:
    # an English word like "millet" or "smoke" also reads as m-l-l, s-m-k.
    if not _AR_CHAR.search(q):
        english = [r["score"] for kinds in hits.reasons.values() for k, r in kinds.items()
                   if k in ("alias", "gloss", "dictionary")]
        if english and max(english) >= 400:
            # the query is an English word the site knows: consonant guesses
            # drop out (below the relevance floor) unless something else agrees
            hits.cap("guess", 370)

    results = []
    ranked = hits.ranked()
    # nothing but faint semantic neighbours means nothing was found
    ranked = [(s, bw) for s, bw in ranked
              if s >= 380 or set(hits.reasons[bw]) - {"semantic", "guess"}]
    # When the query spells a root or a word of one, it is not a meaning
    # query: vectors and aliases of the letters "k-f-r" are noise. Keep the
    # identity matches and only meaning matches nearly as strong.
    identity = max((r["score"] for kinds in hits.reasons.values() for k, r in kinds.items()
                    if k in ("root", "word")), default=0)
    if identity >= 900:
        ranked = [(s, bw) for s, bw in ranked
                  if {"root", "word"} & set(hits.reasons[bw])
                  or ("guess" in hits.reasons[bw] and s >= identity - 250)
                  or s >= identity - 120]
    for score, bw in ranked[:limit]:
        d = ix.roots[bw]
        reasons = sorted(hits.reasons[bw].values(), key=lambda r: -r["score"])
        # show the strongest few, dropping a bare "semantic" when something
        # more specific already explains the match
        shown = []
        has_identity = any(r["kind"] in ("root", "word") for r in reasons)
        for r in reasons:
            if r["kind"] == "semantic" and (has_identity or (shown and not r.get("dictionary_slug"))):
                continue
            if r["kind"] in ("guess", "alias") and has_identity:
                continue
            shown.append({k: v for k, v in r.items() if k != "score"})
            if len(shown) == 3:
                break
        results.append({
            "buckwalter": bw, "arabic": d["arabic"], "gloss": d["gloss"], "entries": d["entries"],
            "score": round(score, 1), "reasons": shown,
        })
    return {"query": q, "results": results, "engine": info}
