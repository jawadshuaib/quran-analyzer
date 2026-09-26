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
    "sch": [("$", 0)], "dsch": [("j", 0)], "tsch": [("$", 1)], "dj": [("j", 0)],
    "b": [("b", 0)], "t": [("t", 0), ("T", 1)], "j": [("j", 0)],
    "h": [("h", 0), ("H", 0)], "d": [("d", 0), ("D", 1)], "r": [("r", 0)],
    "z": [("z", 0), ("Z", 1), ("*", 2)], "s": [("s", 0), ("S", 1)],
    "f": [("f", 0)], "q": [("q", 0)], "k": [("k", 0), ("q", 2)],
    "l": [("l", 0)], "m": [("m", 0)], "n": [("n", 0)], "w": [("w", 0)],
    "y": [("y", 0)], "g": [("g", 1), ("j", 1)], "v": [("v", 0), ("w", 1)], "x": [("x", 0)],
    "c": [("k", 2), ("j", 1)], "p": [("b", 2)],
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
    "root", "roots", "word", "words", "meaning", "means", "mean", "arabic", "quran", "qur'an",
    "something", "someone", "one", "thing", "what", "how", "whats", "say", "said", "called",
    "term", "english", "translate", "translation", "define", "definition", "does", "do",
    "i", "you", "me", "my", "your", "there", "please", "find", "search", "look", "up",
}
# English words so general they should only break ties inside a phrase
# ("remembrance of God", "hobble a camel", "water trough")
GENERIC = {"god", "allah", "lord", "camel", "water", "man", "person", "people", "thing", "day",
           "make", "give", "take", "go", "come", "good", "great", "ask", "seek", "want", "get",
           "have", "keep", "put", "turn", "being"}
IRREGULAR = {
    "wives": "wife", "knives": "knife", "lives": "life", "leaves": "leaf", "halves": "half",
    "thieves": "thief", "wolves": "wolf", "calves": "calf", "children": "child", "men": "man",
    "women": "woman", "feet": "foot", "teeth": "tooth", "mice": "mouse", "geese": "goose",
    "oxen": "ox", "people": "person", "brethren": "brother", "kine": "cow", "dice": "die",
    "judgement": "judgment", "honour": "honor", "colour": "color", "favour": "favor",
    "behaviour": "behavior", "labour": "labor", "neighbour": "neighbor", "worshipper": "worshiper",
}

# Letters other Arabic-script keyboards use for the same sounds, and the
# single glyph ﷲ (NFKC turns presentation forms and ligatures into letters)
_AR_EQUIV = str.maketrans({
    "\u06A9": "ك", "\u06AA": "ك", "\u06CC": "ي", "\u06D2": "ي", "\u06D0": "ي",
    "\u06C1": "ه", "\u06BE": "ه", "\u06D5": "ه", "\u06C3": "ة", "\u06BA": "ن",
    "\u067E": "ب", "\u0686": "ج", "\u0698": "ز", "\u06AF": "ك",
})
# Scholarly single letters that stand for a digraph elsewhere, so both
# spellings meet (ḫayr = khayr, šukr = shukr, ǧanna = janna)
_LAT_PREMAP = [("ḫ", "kh"), ("ẖ", "kh"), ("š", "sh"), ("ş", "sh"), ("ġ", "gh"), ("ğ", "gh"),
               ("ǧ", "j"), ("ĝ", "j"), ("ṯ", "th"), ("ḏ", "dh"), ("č", "ch"), ("ç", "ch"),
               ("ı", "i"), ("ö", "o"), ("ü", "u"), ("ʻ", "ʿ"), ("‘", "ʿ"), ("’", "'"), ("ʼ", "ʾ")]


# The English that standard Qur'an translations use for a root's words
# (Sahih International, Yusuf Ali, Pickthall, Arberry…), where the generated
# aliases have gaps or errors. Keys are stem sequences (see _stem).
TRANSLATION_TERMS = {
    "most gracious": ["rHm"], "gracious": ["rHm", "nEm"], "beneficent": ["rHm"],
    "compassionate": ["rHm"], "merciful": ["rHm"], "most merciful": ["rHm"],
    "entirely merciful": ["rHm"], "especially merciful": ["rHm"],
    "wrongdoer": ["Zlm"], "unjust": ["Zlm"], "transgressor": ["Edw", "bgy"],
    "idolater": ["$rk"], "polytheist": ["$rk"], "associator": ["$rk"], "idolatry": ["$rk"],
    "hypocrite": ["nfq"], "hypocrisy": ["nfq"], "disbeliever": ["kfr"], "unbeliever": ["kfr"],
    "infidel": ["kfr"], "believer": ["Amn"], "faithful": ["Amn"],
    "righteous": ["SlH", "brr"], "righteousness": ["brr", "SlH"], "good deed": ["SlH", "Hsn"],
    "tawhid": ["wHd"], "tawheed": ["wHd"], "tauhid": ["wHd"], "tevhid": ["wHd"], "tawḥid": ["wHd"],
    "god conscious": ["wqy"], "god consciousness": ["wqy"], "mindful of god": ["wqy"],
    "mindfulness of god": ["wqy"], "god fearing": ["wqy"], "pious": ["wqy"], "piety": ["wqy"],
    "satan": ["$Tn"], "devil": ["$Tn"], "iblis": ["bls"], "jinn": ["jnn"], "angel": ["mlk"],
    "prophet": ["nbA"], "messenger": ["rsl"], "apostle": ["rsl"], "scripture": ["ktb"],
    "revelation": ["wHy", "nzl"], "resurrection": ["bEv", "qwm"], "day of resurrection": ["qwm"],
    "day of judgment": ["dyn"], "judgment day": ["dyn"], "reckoning": ["Hsb"], "hereafter": ["Axr"],
    "paradise": ["jnn"], "garden": ["jnn"], "prayer": ["Slw"], "alm": ["zkw", "Sdq"],
    "poor due": ["zkw"], "charity": ["Sdq", "zkw"], "fasting": ["Swm"], "pilgrimage": ["Hjj"],
    "strive": ["jhd"], "striving": ["jhd"], "repentance": ["twb"], "forgiveness": ["gfr"],
    "ask forgiveness": ["gfr"], "seek forgiveness": ["gfr"], "patience": ["Sbr"],
    "gratitude": ["$kr"], "thankful": ["$kr"], "remembrance": ["*kr"], "remembrance of god": ["*kr"],
    "worship": ["Ebd"], "worshiper": ["Ebd"], "servant": ["Ebd"], "idol": ["Snm", "wvn"],
    "monk": ["rhb"], "priest": ["qss"], "christian": ["nSr"], "nazarene": ["nSr"], "jew": ["hwd"],
    "oneness of god": ["wHd"], "monotheism": ["wHd"], "one": ["wHd"], "trust in god": ["wkl"],
    "rely on god": ["wkl"], "guidance": ["hdy"], "misguidance": ["Dll"], "go astray": ["Dll"],
    "spirit": ["rwH"], "soul": ["nfs"], "supplication": ["dEw"], "invocation": ["dEw"],
    "prayer of supplication": ["dEw"], "weep": ["bky"], "cry": ["bky"], "caliph": ["xlf"],
    "successor": ["xlf"], "vicegerent": ["xlf"], "lord": ["rbb"], "god": ["Alh"],
}


def _norm_query(q):
    q = unicodedata.normalize("NFKC", q or "")
    q = q.translate(_AR_EQUIV).replace("\u0640", "")
    return re.sub(r"\s+", " ", q).strip()


def _premap_latin(s):
    s = s.lower()
    for a, b in _LAT_PREMAP:
        s = s.replace(a, b)
    return s


def _fold(s):
    """Lowercase + strip combining marks (after the scholarly digraph letters
    have been spelled out, so ḫ does not collapse into h)."""
    s = unicodedata.normalize("NFKD", _premap_latin(s))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def _stem(w):
    """A light English stemmer: enough for forgiveness/forgiving, merciful/
    mercy, wrongdoers/wrongdoing, consciousness/conscious, worshipper/worship."""
    w = w.lower()
    w = IRREGULAR.get(w, w)
    if w.endswith("'s"):
        w = w[:-2]
    for suf, rep in (("fulness", "ful"), ("ousness", "ous"), ("iveness", "ive"), ("ational", "ate"),
                     ("ization", "ize"), ("iness", "y"), ("ness", ""), ("ments", ""), ("ment", ""),
                     ("ings", ""), ("ing", ""), ("ities", ""), ("ity", ""), ("ies", "y"), ("ied", "y"),
                     ("ers", ""), ("er", ""), ("edly", ""), ("ed", ""), ("ful", ""), ("ly", ""),
                     ("es", ""), ("s", "")):
        need = 5 if suf in ("er", "ers") else 3      # liver, water, river stay whole
        if suf in ("s", "es") and re.search(r"(ss|us|is)$", w):
            continue                                    # conscious, grievous, tennis
        if w.endswith(suf) and len(w) - len(suf) >= need:
            w = w[: -len(suf)] + rep
            break
    if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "lsz":
        w = w[:-1]                      # worshipp -> worship
    if w.endswith("y") and len(w) > 3:
        w = w[:-1] + "i"                # mercy -> merci (= merciful)
    elif w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w


_WORD_RE = re.compile(r"[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+")


def _en_tokens(s):
    s = re.sub(r"['’]s\b", "", s or "")          # camel's -> camel
    return [t.lower() for t in _WORD_RE.findall(_fold(s)) if len(t) >= 3 or t.lower() in ("ox",)]


# --- Arabic spelling keys -------------------------------------------------
_AR_MARKUP = re.compile(r"[\^@\[\]{}#*,.:;!?~]")


def _ar_norm(s):
    """Spelling-insensitive Arabic key: no vowels, one alif-less skeleton for
    modern and Uthmani spellings (كلام ~ كَلَٰم -> كلم), hamza seats folded."""
    s = _AR_DIAC.sub("", _norm_query(s))
    s = _AR_MARKUP.sub("", s)
    s = s.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    s = re.sub(r"[^\u0621-\u064A]", "", s)
    return s.replace("ا", "")


_AR_ARTICLE = re.compile(r"^(?:وال|فال|بال|كال|لل|ال)(?=..)")


def _ar_strict(s):
    """Like _ar_norm but keeping alif (the Uthmani dagger alif written as ا),
    to tell أدراك (adrāka) from الدرك (al-darak) once both are alif-less."""
    s = _norm_query(s).replace("\u0670", "ا")
    s = _AR_MARKUP.sub("", _AR_DIAC.sub("", s))
    s = s.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    return re.sub(r"[^\u0621-\u064A]", "", s)


def _ar_variants(tok):
    """The typed word plus its likely Uthmani spellings: -اة -> -وة
    (الصلاة ~ ٱلصَّلَوٰة), a medial ا -> ى (أدراك ~ أَدْرَىٰكَ)."""
    plain = _AR_MARKUP.sub("", _AR_DIAC.sub("", _norm_query(tok)))
    out = [plain]
    if plain.endswith("ت") and len(plain) >= 4:
        out.append(plain[:-1] + "ة")               # Persian/Urdu قیامت ~ قيامة
    for v in list(out):
        if v.endswith("اة"):
            out.append(v[:-2] + "وة")
    idx = [i for i, ch in enumerate(plain) if ch == "ا" and 0 < i < len(plain) - 1]
    for i in idx[:3]:
        out.append(plain[:i] + "ى" + plain[i + 1:])
    return out


AR_PARTICLES = {_ar_norm(w) for w in (
    "من في على إلى الى عن ما لا لم لن إن أن ان أو او ثم قد هل يا إذا اذا إذ لما كلما ألا الا إلا "
    "أفلا افلا أولئك هذا هذه ذلك تلك الذي التي الذين هو هي هم أنتم نحن أنا كل بل حتى لقد فلا ولا "
    "وما فما إنما إنا إنه لعل كأن وإن فإن").split()} - {""}


# --- Latin consonant skeletons (spelling-convention tolerant) ---------------
_LOOSE_COMMON = [("dsch", "j"), ("tsch", "$"), ("sch", "$"), ("kh", "x"), ("gh", "g"), ("sh", "$"),
                 ("sy", "$"), ("th", "s"), ("ts", "s"), ("dh", "z"), ("dz", "z"), ("dj", "j"), ("ch", "$"),
                 ("ou", "u"), ("au", "aw"), ("ai", "ay"), ("ei", "ay"), ("ee", "i"), ("oo", "u"),
                 ("ḥ", "h"), ("ṣ", "s"), ("ḍ", "d"), ("ṭ", "t"), ("ẓ", "z"), ("q", "k"), ("v", "w")]
_LOOSE_VARIANTS = [[("c", "k")], [("c", "j")]]   # English/Malay vs Turkish c
_PARTICLE_SEGS = {"wa", "fa", "bi", "li", "ka", "la", "sa", "a", "al", "el", "ul", "l", "wal", "fal", "bil", "lil"}


def _loose_one(word, extra, marks=False):
    w = _premap_latin(word)
    if marks:
        w = re.sub(r"[ʿʾ'`´]", "7", w)       # one glottal marker, kept as a consonant
    for a, b in _LOOSE_COMMON[:13]:          # consonant digraphs first
        w = w.replace(a, b)
    for a, b in extra:
        w = w.replace(a, b)
    for a, b in _LOOSE_COMMON[13:]:
        w = w.replace(a, b)
    w = unicodedata.normalize("NFKD", w)
    w = "".join(ch for ch in w if not unicodedata.combining(ch))
    w = re.sub(r"[ʿʾ'`´]", "", w)
    w = re.sub(r"[aeiouy]", lambda m: "y" if m.group(0) == "y" else "", w)
    return w.replace("7", "'") if marks else w


def _loose_keys(word, corpus=False):
    """Consonant skeletons of a romanised word under the common spelling
    conventions (English, Malay/Indonesian, Turkish, French, German), with the
    article and proclitics removed; both with and without doubled letters."""
    w = word.strip().lower()
    segs = [x for x in re.split(r"[-\s]+", w) if x]
    while len(segs) > 1 and segs[0] in _PARTICLE_SEGS:
        segs = segs[1:]
    bases = {"".join(segs)}
    if len(segs) == 1:
        m = re.match(r"^(?:wal|fal|bil|lil|al|el|ul)(?=[^aeiou-]{0,1}[a-zḥṣḍṭẓʿʾ]{3})", segs[0])
        if m and not corpus:
            bases.add(segs[0][m.end():])
    keys = set()
    has_marks = bool(re.search(r"[ʿʾ'`´’]", w))
    for b in bases:
        for extra in _LOOSE_VARIANTS:
            if has_marks:
                km = re.sub(r"[^a-z$']", "", _loose_one(b, extra, marks=True))
                if len(km) >= 3 and "'" in km:
                    keys.add(km)                       # shu'ara' ~ shuʿarāʾu
            k = _loose_one(b, extra)
            k = re.sub(r"[^a-z$]", "", k)
            if not k:
                continue
            keys.add(k)
            keys.add(re.sub(r"(.)\1+", r"\1", k))
            if corpus:
                if "x" in k:
                    keys.add(k.replace("x", "h"))     # Turkish/Malay h for kh: ahiret
                # case endings and tanwīn: al-jannati / jannatun ~ janna(h)
                if k.endswith("n") and re.search(r"(an|un|in)$", b):
                    keys.add(k[:-1])
                if re.search(r"at(u|a|i|an|un|in)?$", b):
                    kt = k[:-1] if k.endswith("t") else k
                    kt = kt[:-1] if kt.endswith("t") else kt
                    keys.add(kt)
            else:
                if k.endswith("h") and re.search(r"[aeiou]h$", b):
                    keys.add(k[:-1])          # rahmah ~ rahma
    return {k for k in keys if len(k.replace("'", "")) >= 2 and len(k) >= 3}


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


def _alias_norm(a):
    a = _fold(a)
    a = re.sub(r"['’]s\b", "", a)
    a = re.sub(r"[-‐–—_/]+", " ", a)
    return re.sub(r"\s+", " ", a).strip()


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
    ix.gloss_df = Counter()
    ix.english_vocab = set()
    for d in ix.roots.values():
        text = " ".join(filter(None, [d["gloss"], d["field"]]))
        toks = [t for t in _en_tokens(text) if t not in STOPWORDS]
        d["gloss_stems"] = {_stem(t) for t in toks}
        d["gloss_lead"] = _stem(toks[0]) if toks else ""
        d["gloss_text"] = _fold(text)
        ix.gloss_df.update(d["gloss_stems"])
        ix.english_vocab.update(toks)

    # words of the Qur'an -> roots (per word position, then by spelling key)
    word_root = {}
    for r in conn.execute("SELECT chapter, verse, word_pos, root_buckwalter FROM morphology "
                          "WHERE root_buckwalter IS NOT NULL AND root_buckwalter <> ''"):
        word_root[(r[0], r[1], r[2])] = r[3]
    # whole vowelled words (segments joined) keep the dagger alif that
    # word_translit.arabic_plain has stripped: كَلَٰمَ -> كلام
    forms = defaultdict(list)
    for r in conn.execute("SELECT chapter, verse, word_pos, form_arabic, root_buckwalter FROM morphology ORDER BY id"):
        forms[(r[0], r[1], r[2])].append(((r[3] or "").replace("#", "ء"), r[4] or ""))
    ix.ar_words = defaultdict(Counter)   # arabic_key -> roots (clitics stripped)
    ix.ar_spell = defaultdict(Counter)   # _ar_norm spelling -> roots (whole word)
    ix.ar_strict = defaultdict(set)      # _ar_strict spelling -> roots
    ix.tr_words = defaultdict(Counter)   # translit_key -> roots
    ix.loose = defaultdict(Counter)      # consonant skeleton -> roots
    ix.word_example = {}                 # (kind, key, root) -> displayed spelling
    try:
        for r in conn.execute("SELECT chapter, verse, word_pos, translit, translit_key, arabic_plain, arabic_key "
                              "FROM word_translit"):
            root = word_root.get((r[0], r[1], r[2]))
            if not root or root not in ix.roots:
                continue
            ar_show = _AR_MARKUP.sub("", r["arabic_plain"] or "")
            if r["arabic_key"]:
                ix.ar_words[r["arabic_key"]][root] += 1
                ix.word_example.setdefault(("ar", r["arabic_key"], root), ar_show)
            if r["translit_key"]:
                ix.tr_words[r["translit_key"]][root] += 1
                ix.word_example.setdefault(("tr", r["translit_key"], root), r["translit"])
            if r["translit"]:
                for k in _loose_keys(r["translit"], corpus=True):
                    ix.loose[k][root] += 1
                    ix.word_example.setdefault(("lo", k, root), r["translit"])
    except sqlite3.OperationalError:
        pass
    # every word three ways, by the corpus' own segmentation: whole
    # (وَتَقْوَىٰهَا), without its proclitics (تَقْوَىٰهَا), and the stem (تَقْوَىٰ)
    for key, segs in forms.items():
        root = word_root.get(key)
        if not root or root not in ix.roots:
            continue
        si = next((i for i, sg in enumerate(segs) if sg[1]), None)
        if si is None:
            continue
        parts = [sg[0] for sg in segs]
        show = _AR_MARKUP.sub("", _AR_DIAC.sub("", "".join(parts[si:]))).replace("ٱ", "ا")
        for cand in {"".join(parts), "".join(parts[si:]), parts[si]}:
            n = _ar_norm(cand)
            if len(n) >= 2:
                ix.ar_spell[n][root] += 1
                ix.word_example.setdefault(("sp", n, root), show)
            st = _ar_strict(cand)
            if st:
                ix.ar_strict[st].add(root)
    del forms
    # lemmas (dictionary headwords as a reader might type them)
    ix.ar_lemmas = defaultdict(Counter)
    for r in conn.execute("SELECT lemma_arabic, root_buckwalter, COUNT(*) FROM morphology "
                          "WHERE root_buckwalter IS NOT NULL AND lemma_arabic IS NOT NULL "
                          "GROUP BY lemma_arabic, root_buckwalter"):
        if r[1] in ix.roots:
            k = _ar_norm(r[0])
            if k:
                ix.ar_lemmas[k][r[1]] += r[2]
                ix.word_example.setdefault(("le", k, r[1]), _AR_MARKUP.sub("", _AR_DIAC.sub("", r[0])))

    # aliases (curated English words and phrases, some transliterations)
    ix.alias = defaultdict(list)          # normalised alias -> [(root, source)]
    ix.alias_stem = defaultdict(set)      # stem sequence ("god conscious") -> roots
    try:
        for r in conn.execute("SELECT alias, root_buckwalter, source FROM root_search_aliases"):
            if r[1] not in ix.roots or not r[0]:
                continue
            a = _alias_norm(r[0])
            if not a:
                continue
            ix.alias[a].append((r[1], r[2]))
            toks = [t for t in _en_tokens(a) if t not in STOPWORDS]
            if toks and (len(toks) > 1 or len(toks[0]) >= 5):
                ix.alias_stem[" ".join(_stem(t) for t in toks)].add(r[1])
    except sqlite3.OperationalError:
        pass

    ix.terms = defaultdict(list)
    for phrase, roots in TRANSLATION_TERMS.items():
        key = " ".join(_stem(t) for t in _en_tokens(phrase))
        ix.terms[key] += [r for r in roots if r in ix.roots]
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


def _warm(delay=0.0):
    if delay:
        time.sleep(delay)
    ix = _index()
    if not ix:
        return
    # the vectors the semantic arm will use (no network: just the matrix)
    try:
        import search_v2
        name = search_v2.active_model_name()
    except Exception:
        name = None
    if name not in (ix.vector_models or []):
        name = next((m for m in ix.vector_models if "MiniLM" in m), None)
    if name:
        _load_vectors(name)


def warm_up(delay=0.0):
    """Build the index (and load the vectors) in the background — at worker
    start, and again when the Dictionary page loads its root list — so no
    reader's first search pays for it."""
    if _idx is not None and (not _idx.vector_models or _vec_cache):
        return
    threading.Thread(target=_warm, args=(delay,), name="dictionary-search-warmup", daemon=True).start()


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
    # "root k-f-r", "the root kfr": the notation is what is left
    if not _AR_CHAR.search(raw):
        kept = [t for t in raw.split() if t.lower() not in STOPWORDS]
        if kept and len(kept) < len(raw.split()):
            raw = " ".join(kept)
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
        letters = "".join(ch for ch in _AR_DIAC.sub("", _norm_query(raw)) if ch in AR2BW)
        spaced = len(_SEPARATORS.findall(raw)) > 0
        if 3 <= len(letters) <= 5:
            key = "".join(AR2BW[ch] for ch in letters)
            if key in ix.roots:
                hits.add(key, 985 if spaced or len(letters) == 3 else 960, "root",
                         "Root letters " + " ".join(ix.roots[key]["arabic"]))
        elif len(letters) == 2:
            # two letters: a doubled root (دب -> د ب ب) or one with a weak or
            # hamza radical left out (قل -> ق و ل)
            a, b = (AR2BW[ch] for ch in letters)
            for key, sc in ((a + b + b, 950), (a + "w" + b, 900), (a + "y" + b, 900), (a + b + "y", 890),
                            (a + b + "w", 890), ("A" + a + b, 880), (a + "A" + b, 880), (a + b + "A", 880)):
                if key in ix.roots:
                    hits.add(key, sc + _freq_bonus(ix, key) / 2, "root",
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
                if score > seen.get(key, (-1, False))[0]:
                    # "awl", "owl", "elm" read as roots only by taking a vowel
                    # for a radical — an English word may be meant instead
                    seen[key] = (score, has_vowel_unit and not separated)
    for key, (score, soft) in seen.items():
        hits.add(key, score, "root", "Root " + "-".join(_translit_root(key)), soft=soft)


_BW2LATIN = {"A": "ʾ", "b": "b", "t": "t", "v": "th", "j": "j", "H": "ḥ", "x": "kh", "d": "d",
             "*": "dh", "r": "r", "z": "z", "s": "s", "$": "sh", "S": "ṣ", "D": "ḍ", "T": "ṭ",
             "Z": "ẓ", "E": "ʿ", "g": "gh", "f": "f", "q": "q", "k": "k", "l": "l", "m": "m",
             "n": "n", "h": "h", "w": "w", "y": "y"}


def _translit_root(bw):
    return [_BW2LATIN.get(ch, ch) for ch in bw]


def _arabic_word(ix, q, hits):
    """An Arabic word of the Qur'an (any vowelling, modern or Uthmani spelling,
    clitics, Persian/Urdu letters) -> its root."""
    if not _AR_CHAR.search(q):
        return
    toks = _norm_query(q).split()
    content = [t for t in toks if _ar_norm(t) not in AR_PARTICLES] if len(toks) > 1 else toks
    for tok in content or toks:
        found = False
        variants = _ar_variants(tok)
        # 1. the whole word, spelling-insensitive (كلام ~ كَلَٰم; الصلاة ~
        #    ٱلصَّلَوٰة; أدراك ~ أَدْرَىٰكَ), every likely spelling tried; a match
        #    that also agrees on the alifs is preferred
        typed_found = False
        for i, v in enumerate(variants):
            key = _ar_norm(v)
            if len(key) < 2:
                continue
            strict = ix.ar_strict.get(_ar_strict(v), set()) | ix.ar_strict.get(_AR_ARTICLE.sub("", _ar_strict(v)), set())
            for table, kind, label, base in ((ix.ar_spell, "sp", "Qurʾānic word", 900),
                                             (ix.ar_lemmas, "le", "Word", 880)):
                c = table.get(key)
                if not c:
                    continue
                total = sum(c.values())
                for root, n in c.most_common(4):
                    ex = ix.word_example.get((kind, key, root)) or tok
                    variant_pen = 0 if i == 0 else (40 if typed_found else 10)
                    sc = (base - variant_pen - (25 if root not in strict else 0)) * (0.75 + 0.25 * n / total)
                    hits.add(root, sc, "word", f"{label} {ex}")
                    found = True
                    if i == 0 and root in strict:
                        typed_found = True   # the typed spelling itself is a Qur'anic word
        if found:
            continue
        # 2. clitics stripped (the verse-matching key): وليعلم, فأنزلنا
        for v in variants:
            key = translit.arabic_key(v)
            c = ix.ar_words.get(key) if key and len(key) >= 3 else None
            if not c:
                continue
            total = sum(c.values())
            for root, n in c.most_common(3):
                ex = ix.word_example.get(("ar", key, root)) or tok
                hits.add(root, 860 * (0.75 + 0.25 * n / total), "word", f"Qurʾānic word {ex}")
                found = True
            break
        if not found:
            _skeleton_arabic(ix, tok, hits)


_AR_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك", "س")
_AR_SUFFIXES = ("كما", "هما", "تما", "هم", "هن", "كم", "كن", "نا", "ها", "ون", "ين", "ان", "ات", "وا",
                "تم", "ه", "ك", "ي", "ة", "ت", "ا", "ن")


def _skeleton_arabic(ix, tok, hits):
    """No known word: strip likely clitics and look for a root whose letters
    run through what is left, in order (a weak guess; ranked below identity)."""
    ar = _AR_MARKUP.sub("", _AR_DIAC.sub("", _norm_query(tok)))
    w = "".join(AR2BW.get(ch, "") for ch in ar)
    if len(w) < 3:
        return
    stems = {w}
    for p in _AR_PREFIXES:
        if ar.startswith(p) and len(ar) - len(p) >= 3:
            stems.add("".join(AR2BW.get(ch, "") for ch in ar[len(p):]))
    for s in list(stems):
        for suf in _AR_SUFFIXES:
            sbw = "".join(AR2BW.get(ch, "") for ch in suf)
            if s.endswith(sbw) and len(s) - len(sbw) >= 3:
                stems.add(s[: -len(sbw)])
    # a long vowel written with ا/و/ي is more often a vowel than a radical
    # (الدبور -> د ب ر)
    for s in list(stems):
        for i, ch in enumerate(s):
            if ch in "Awy" and 0 < i < len(s) - 0 and len(s) - 1 >= 3:
                stems.add(s[:i] + s[i + 1:])
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
                 "mu", "ma", "ta", "te", "ya", "tu", "yu", "na", "nu", "i", "a")
_LAT_SUFFIXES = ("iyyah", "iyya", "iyyat", "ūna", "īna", "una", "ina", "oon", "een", "uun", "iin", "ūn", "īn",
                 "un", "in", "an", "at", "ah", "āt", "iyy", "īy", "ī", "ā", "a", "u", "i", "h", "t", "n")


_ALLAH_TAIL = re.compile(r"^(.{3,}?)(?:u|i|a)?(?:ll|l)ah$")


def _latin_word(ix, q, hits):
    """A transliterated word (kafaru, rahmah, istighfar, cennet, solat,
    tauhid, ḫayr) -> root."""
    if _AR_CHAR.search(q):
        return
    toks = [t for t in re.split(r"\s+", _premap_latin(q.strip())) if t]
    if not toks or len(toks) > 3:
        return
    if len(toks) > 1:
        # a phrase with English words in it is English ("wild ass", "a saw")
        if any(t in ix.english_vocab or t in STOPWORDS for t in toks):
            return
    expanded = []
    for t in toks:
        segs = [x for x in t.split("-") if x]
        if len(segs) > 1 and re.fullmatch(r"(?:li|bi|fi)?(?:a|u|i)?l?lah", segs[-1]):
            head = "".join(x for x in segs[:-1] if x not in _PARTICLE_SEGS)
            expanded += [head, "allah"] if head else ["allah"]
            continue
        m = _ALLAH_TAIL.match(t)                  # astaghfirullah, bismillah, alhamdulillah
        if m and len(t) > 6:
            head = m.group(1)
            head = re.sub(r"(?:li|bi|fi|l)$", "", head) or head   # alhamdu-li-llah
            expanded += [head, "allah"]
        else:
            expanded.append(t)
    for tok in expanded:
        low = tok.lower()
        if len(low) < 3 or not re.search(r"[a-zʾʿ'`āīūḥṣḍṭẓ]", low):
            continue
        matched = False
        # 1. a spelling of a Qur'anic word (the corpus' own romanization keys)
        norm = re.sub(r"ee|ei|ie", "i", low)
        norm = re.sub(r"oo", "u", norm)
        norm = re.sub(r"aa", "a", norm)
        variants = {norm, norm + "h", norm + "t", norm + "a", norm + "u", norm + "i"}
        if norm.endswith("h") or norm.endswith("t"):
            variants.add(norm[:-1])
        if len(norm) > 4 and norm[0] in "ia":
            # the verse writes wasl forms without their opening vowel:
            # istighfār -> (wa-mā kāna) stighfāru
            variants |= {v[1:] for v in list(variants)}
        keys = {translit.translit_key(v) for v in variants}
        keys.discard("")
        exact_key = translit.translit_key(norm)
        for key in keys:
            c = ix.tr_words.get(key)
            if not c or len(key) < 3:
                continue
            total = sum(c.values())
            for root, n in c.most_common(3):
                ex = ix.word_example.get(("tr", key, root)) or tok
                hits.add(root, (880 if key == exact_key else 850) * (0.75 + 0.25 * n / total), "word",
                         f"Qurʾānic word {ex}", soft=len(key) <= 4)
                matched = True
        # 2. the consonants, whatever the spelling convention (cennet, solat,
        #    tauhid, tövbe, chirk, mescid)
        for key in _loose_keys(low):
            c = ix.loose.get(key)
            if not c:
                continue
            total = sum(c.values())
            for root, n in c.most_common(3):
                ex = ix.word_example.get(("lo", key, root)) or tok
                hits.add(root, 820 * (0.75 + 0.25 * n / total), "word", f"Qurʾānic word {ex}",
                         soft=len(key) <= 3)
                matched = True
        # 3. consonant skeleton after likely affixes (a weaker guess)
        _latin_skeleton(ix, low, hits, weak=matched)


def _latin_skeleton(ix, low, hits, weak=False):
    word = _fold(low).replace("-", "").replace("'", "")
    word = word.replace("au", "aw").replace("ai", "ay")    # tauhid ~ tawhid
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
                unit_sets += [[a, "w", b], [a, "y", b], [a, b, "w"], [a, b, "y"], ["w", a, b], [a, b, b],
                              [a, b, "ʿ"], [a, "ʿ", b], ["ʿ", a, b], [a, b, "ʾ"], [a, "ʾ", b], ["ʾ", a, b]]
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
    a = _alias_norm(q)
    toks = _meaning_query(q)
    core = " ".join(toks)
    seen = set()
    for key in (a, core):
        for root, source in ix.alias.get(key, []) if key else []:
            if (root, key) in seen:
                continue
            seen.add((root, key))
            hits.add(root, 800 if source == "ai" else 780, "alias", f"“{key}”")
    if toks and (len(toks) > 1 or len(toks[0]) >= 5):
        for root in ix.alias_stem.get(" ".join(_stem(t) for t in toks), ()):
            hits.add(root, 700, "alias", f"“{core}”")
    if toks:
        stemmed = " ".join(_stem(t) for t in toks)
        for i, root in enumerate(ix.terms.get(stemmed, [])):
            # a standard translation's word for the root: the first listed
            # is the root most translators mean
            hits.add(root, 840 - 15 * i, "term", f"Common translation: “{core}”")


def _typo(ix, q, hits):
    """A misspelt English word (patiance, hipocrisy, arrogence): the nearest
    word the site knows, offered as a correction — never above real matches."""
    import difflib
    toks = _meaning_query(q)
    if len(toks) != 1 or len(toks[0]) < 5 or _AR_CHAR.search(q) or re.search(r"[ʿʾ'`’]", q):
        return
    t = toks[0]
    if t in ix.english_vocab or t in ix.alias:
        return
    if not hasattr(ix, "typo_vocab"):
        vocab = defaultdict(set)
        for w in list(ix.english_vocab) + [x for x in ix.alias if x.isalpha()]:
            if len(w) >= 4:
                vocab[w[0]].add(w)
        ix.typo_vocab = {k: sorted(v) for k, v in vocab.items()}
    pool = ix.typo_vocab.get(t[0], []) + ix.typo_vocab.get(t[1], [])
    for m in difflib.get_close_matches(t, pool, n=1, cutoff=0.8):
        ratio = difflib.SequenceMatcher(None, t, m).ratio()
        ceiling = 500 + 300 * (ratio - 0.8) / 0.2        # compasion ~ compassion: ~725
        sub = _Hits()
        _aliases(ix, m, sub)
        _gloss(ix, m, sub)
        for bw, sc in sorted(sub.best.items(), key=lambda kv: -kv[1])[:8]:
            hits.add(bw, min(ceiling, sc - 60), "typo", f"Did you mean “{m}”?")


def _stem_match(qs, gloss_stems):
    if qs in gloss_stems:
        return 1.0
    for g in gloss_stems:
        if len(g) >= 4 and len(qs) >= 4 and (qs.startswith(g) or g.startswith(qs)):
            return 0.7                  # idolater ~ idol, prostration ~ prostrat
    return 0.0


def _gloss(ix, q, hits):
    toks = _meaning_query(q)
    if not toks or _AR_CHAR.search(q):
        return
    n_roots = max(1, len(ix.roots))
    stems = [_stem(t) for t in toks]
    # rare words carry a phrase; generic ones ("God", "camel") only break ties
    weights = []
    for t, st in zip(toks, stems):
        w = math.log(n_roots / (1 + ix.gloss_df.get(st, 0)))
        if t in GENERIC or st in GENERIC:
            w *= 0.25
        weights.append(max(w, 0.2))
    total = sum(weights)
    phrase = " ".join(toks)
    for bw, d in ix.roots.items():
        if not d["gloss_stems"]:
            continue
        got = sum(w * _stem_match(st, d["gloss_stems"]) for st, w in zip(stems, weights))
        if not got:
            continue
        frac = got / total
        sc = 420 + 140 * frac
        if len(toks) > 1 and phrase in d["gloss_text"]:
            sc += 40
        if frac >= 0.99 and d["gloss_lead"] in stems:
            # the root's primary meaning leads with the word ("Sun", "Mercy/
            # compassion", "Water"): as strong as a curated alias
            sc = 800 if len(toks) == 1 else sc + 60
        hits.add(bw, sc + _freq_bonus(ix, bw) * 0.5, "gloss", d["gloss"] or "")


def _fts_query(toks):
    safe = [re.sub(r"[^a-z]", "", t) for t in toks]
    safe = [t for t in safe if len(t) >= 3]
    return safe


def _dictionary_text(ix, q, hits):
    """The dictionaries' own English (full text, porter-stemmed)."""
    if not ix.has_fts or _AR_CHAR.search(q):
        return
    toks = _fts_query(_meaning_query(q))
    if not toks or len(toks) > 8:
        return
    conn = _connect()
    all_terms = False
    try:
        rows = []
        for expr in (" AND ".join(toks), " OR ".join(toks)) if len(toks) > 1 else (toks[0],):
            all_terms = " AND " in expr or len(toks) == 1
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
        if len(toks) > 1 and all_terms and rank < 5:
            sc += 60   # every word of the phrase in one entry ("hobble a camel")
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


_embed_pool = None
_EMBED_BUDGET = 1.5   # seconds the reader waits for the hosted embedding


def _embed(ix, q):
    """(family, model_name, vector) for the best available model, or None.
    The hosted call gets a time budget; a slow answer still lands in
    search_v2's cache for the next keystroke."""
    global _embed_pool
    try:
        import search_v2
        vname = search_v2.active_model_name()
        if vname and vname in ix.vector_models:
            if _embed_pool is None:
                from concurrent.futures import ThreadPoolExecutor
                _embed_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dict-embed")
            fut = _embed_pool.submit(search_v2.embed_query, q)
            try:
                v = fut.result(timeout=_EMBED_BUDGET)
            except Exception:
                v = None
            if v is not None:
                return "voyage", vname, np.asarray(v, dtype=np.float32)
            if not _AR_CHAR.search(q) and any(m for m in ix.vector_models if "MiniLM" in m):
                pass  # fall through to MiniLM below
            else:
                return None
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
    if not _AR_CHAR.search(q):
        core = " ".join(t for t in re.split(r"\s+", q) if t.lower() not in STOPWORDS)
        q = core or q
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
_KIND_ORDER = ("root", "word", "term", "alias", "gloss", "dictionary", "semantic", "guess", "typo")


class _Hits:
    def __init__(self):
        self.best = {}                    # bw -> best score
        self.reasons = defaultdict(dict)  # bw -> kind -> reason (best of that kind)

    def add(self, bw, score, kind, label, dictionary_slug=None, snippet=None, extra=None, soft=False):
        if score > self.best.get(bw, 0):
            self.best[bw] = score
        cur = self.reasons[bw].get(kind)
        if cur is None or score > cur["score"]:
            r = {"kind": kind, "label": label, "score": score}
            if soft:
                r["soft"] = True
            if dictionary_slug:
                r["dictionary_slug"] = dictionary_slug
            if snippet:
                r["snippet"] = snippet
            if extra:
                r["detail"] = extra
            self.reasons[bw][kind] = r

    def cap(self, kind, ceiling, only_if_best=False, only_soft=False, roots=None):
        """Lower one kind of evidence to at most `ceiling` (recomputing each
        root's best score). only_if_best: touch roots where it is the lead;
        only_soft: only reasons marked soft; roots: only these roots."""
        for bw, kinds in self.reasons.items():
            r = kinds.get(kind)
            if not r or r["score"] <= ceiling:
                continue
            if roots is not None and bw not in roots:
                continue
            if only_soft and not r.get("soft"):
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
            meaning = [k for k in ("alias", "term", "gloss", "dictionary", "semantic") if k in kinds
                       and (k != "semantic" or kinds[k]["score"] >= 420)]
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
    def scores(*kinds):
        return [r["score"] for ks in hits.reasons.values() for k, r in ks.items() if k in kinds]

    # A misspelt English word ("patiance"): nothing recognised it as a root,
    # a word, an alias or a gloss, and the dictionaries barely mention it.
    strong = max(scores("root", "word", "alias", "gloss", "term"), default=0)
    if strong < 700 and max(scores("dictionary"), default=0) < 560:
        try:
            _typo(ix, q, hits)
        except Exception as e:
            print(f"[dictionary_search] typo failed for {q!r}: {e}")

    # An alias counts in full only when something independent agrees — the
    # root's gloss, the dictionaries' own text, the vectors, or the root
    # itself. (Some generated aliases are simply wrong: "liver" -> roots of
    # living, "lamb" -> لمز.)
    for bw, ks in hits.reasons.items():
        a = ks.get("alias")
        if not a:
            continue
        agreed = ("gloss" in ks or "dictionary" in ks or "root" in ks or "word" in ks or "term" in ks
                  or ks.get("semantic", {}).get("score", 0) >= 520)
        cap = 700 if " " in a["label"] else 540   # a whole phrase is rarely a stray alias
        if not agreed and a["score"] > cap:
            a["score"] = cap
            hits.best[bw] = max(x["score"] for x in ks.values())

    # A query that IS a root notation (kfr, k-f-r) is about that root; an
    # alias that happens to spell the same string for another root (the AI
    # aliases map "kfr" to ن ك ر as well) should not sit beside it.
    if any(r.get("root", {}).get("score", 0) >= 930 and not r["root"].get("soft") for r in hits.reasons.values()):
        hits.cap("alias", 560, only_if_best=True)

    if not _AR_CHAR.search(q):
        english = max(scores("alias", "gloss", "term"), default=0)
        if english >= 560:
            # an English word the site knows ("sun", "moon", "owl") beats an
            # accidental match with a short Qur'anic word key (ṣunʿan) or a
            # root read by taking a vowel for a radical (ʾ-w-l)
            hits.cap("word", english - 20, only_soft=True)
            hits.cap("root", english - 20, only_soft=True)
        # Consonant-skeleton guesses must not outrank genuine meaning
        # evidence: "millet" and "smoke" also read as m-l-l, s-m-k.
        if max(scores("alias", "gloss", "dictionary", "term") + [x - 250 for x in scores("typo")], default=0) >= 400:
            hits.cap("guess", 370)

    results = []
    ranked = hits.ranked()
    # nothing but faint semantic neighbours means nothing was found
    ranked = [(s, bw) for s, bw in ranked
              if s >= 380 or set(hits.reasons[bw]) - {"semantic", "guess", "typo"}]
    # When the query spells a root or a word of one, it is not a meaning
    # query: vectors and aliases of the letters "k-f-r" are noise. Keep the
    # identity matches and only meaning matches nearly as strong.
    identity = max((r["score"] for kinds in hits.reasons.values() for k, r in kinds.items()
                    if k in ("root", "word") and not r.get("soft")), default=0)
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
            if r["kind"] in ("guess", "alias", "term") and has_identity:
                continue
            shown.append({k: v for k, v in r.items() if k not in ("score", "soft")})
            if len(shown) == 3:
                break
        results.append({
            "buckwalter": bw, "arabic": d["arabic"], "gloss": d["gloss"], "entries": d["entries"],
            "score": round(score, 1), "reasons": shown,
        })
    return {"query": q, "results": results, "engine": info}
