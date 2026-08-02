"""Deterministic Buckwalter -> house-style romanization, plus the match keys
used to align transliterated / Arabic citations in prose notes back to the
exact words of a verse.

Why rules and not a model: `morphology.form_buckwalter` is a lossless 1:1
encoding of the Uthmani orthography (letters *and* diacritics) for all 77,429
words. Romanization is therefore a pure function of data we already hold. The
hover-to-highlight feature depends on the transliteration in a note and the
transliteration on a word being the *same string*, so a generative step would
be actively harmful here — it would break that invariant at scale and still
need a rule engine to verify it.

Two layers:

  rom_word()      canonical display form, in the house style the exegesis notes
                  already use  ->  "al-ḥasanāti", "yudhhibna", "ṭarafayi"
  translit_key()  aggressive normaliser that collapses every spelling variation
                  a note might use (al-/l-, pausal endings, dropped hamza,
                  sun-letter doubling, ā/a) down to one comparable form
  arabic_key()    the same idea for Arabic citations: strip diacritics and
                  normalise letter variants

The keys are deliberately lossy. Matching is done on keys; display uses rom.
Storing one canonical form + one key beats storing a table of "variations":
variations are unbounded, a normaliser is finite.
"""

import re
import unicodedata

# --- Buckwalter -> Arabic (used to repair rows whose Buckwalter is corrupt) ---

BW2AR = {
    "'": 'ء', '|': 'آ', '>': 'أ', '&': 'ؤ', '<': 'إ',
    '}': 'ئ', 'A': 'ا', 'b': 'ب', 'p': 'ة', 't': 'ت',
    'v': 'ث', 'j': 'ج', 'H': 'ح', 'x': 'خ', 'd': 'د',
    '*': 'ذ', 'r': 'ر', 'z': 'ز', 's': 'س', '$': 'ش',
    'S': 'ص', 'D': 'ض', 'T': 'ط', 'Z': 'ظ', 'E': 'ع',
    'g': 'غ', '_': 'ـ', 'f': 'ف', 'q': 'ق', 'k': 'ك',
    'l': 'ل', 'm': 'م', 'n': 'ن', 'h': 'ه', 'w': 'و',
    'Y': 'ى', 'y': 'ي', 'F': 'ً', 'N': 'ٌ', 'K': 'ٍ',
    'a': 'َ', 'u': 'ُ', 'i': 'ِ', '~': 'ّ', 'o': 'ْ',
    '`': 'ٰ', '{': 'ٱ',
}
AR2BW = {v: k for k, v in BW2AR.items()}


def arabic_to_buckwalter(text: str) -> str:
    """Inverse of the table above; unknown glyphs are dropped. Used only by the
    repair pass for rows whose stored Buckwalter carries the `_#` placeholder."""
    return ''.join(AR2BW.get(ch, '') for ch in (text or ''))


# --- romanization -------------------------------------------------------------

CONS = {
    "'": 'ʾ', '>': 'ʾ', '<': 'ʾ', '&': 'ʾ', '}': 'ʾ',
    'b': 'b', 't': 't', 'v': 'th', 'j': 'j', 'H': 'ḥ', 'x': 'kh', 'd': 'd',
    '*': 'dh', 'r': 'r', 'z': 'z', 's': 's', '$': 'sh', 'S': 'ṣ', 'D': 'ḍ',
    'T': 'ṭ', 'Z': 'ẓ', 'E': 'ʿ', 'g': 'gh', 'f': 'f', 'q': 'q', 'k': 'k',
    'l': 'l', 'm': 'm', 'n': 'n', 'h': 'h', 'w': 'w', 'y': 'y',
}
VOWELS = ('a', 'u', 'i', 'ā', 'ū', 'ī')
# Buckwalter forms the definite-article prefix segment can take.
ARTICLE = {'{l', '{lo', '{l~', 'Al', 'Alo', 'l', 'lo', '{', 'A'}


def _rom_segment(bw: str, no_initial_gemination: bool = False) -> str:
    """Romanize one Buckwalter segment. `no_initial_gemination` suppresses the
    doubling written on a stem-initial sun letter, which encodes assimilation of
    the article's lām rather than a real geminate (ٱلصَّلَوٰة -> al-ṣalāh)."""
    bw = (bw or '').replace('_#', "'").replace('_', '')
    out: list[str] = []
    i = 0
    first_cons_done = False
    while i < len(bw):
        ch = bw[i]

        if ch in ('{', 'o'):                       # waṣla / sukūn: no sound
            i += 1
            continue

        if ch == '|':                              # آ  = hamza + long ā
            out.extend(['ʾ', 'ā'])
            first_cons_done = True
            i += 1
            continue

        if ch == '`':                              # dagger alif -> ā
            if out and out[-1] in ('w', 'y'):      # silent carrier (صَلَوٰة)
                out.pop()
            if out and out[-1] == 'ā':             # already long: don't stack
                pass
            elif out and out[-1] == 'a':
                out[-1] = 'ā'
            else:
                out.append('ā')
            i += 1
            continue

        if ch == 'A':
            if out and out[-1] in ('an', 'ā'):     # tanwīn alif silent / already long
                pass
            elif out and out[-1] == 'a':
                out[-1] = 'ā'
            else:
                out.append('ā')
            i += 1
            continue

        if ch == 'Y':                              # alif maqṣūra
            if i + 1 < len(bw) and bw[i + 1] in 'aui':
                out.append('y')                    # consonantal yāʾ (طَرَفَىِ)
            elif out and out[-1] == 'ā':
                pass
            elif out and out[-1] == 'a':
                out[-1] = 'ā'
            else:
                out.append('ā')
            i += 1
            continue

        if ch == 'p':                              # tāʾ marbūṭa
            out.append('t' if (i + 1 < len(bw) and bw[i + 1] in 'auiFNK') else 'h')
            i += 1
            continue

        if ch == 'w' and out and out[-1] == 'u' and (i + 1 >= len(bw) or bw[i + 1] not in 'aui~'):
            out[-1] = 'ū'
            i += 1
            continue

        if ch == 'y' and out and out[-1] == 'i' and (i + 1 >= len(bw) or bw[i + 1] not in 'aui~'):
            out[-1] = 'ī'
            i += 1
            continue

        if ch == '~':                              # shadda -> double the consonant
            j = len(out) - 1
            while j >= 0 and out[j] in VOWELS:
                j -= 1
            # nothing to double (word-initial shadda carried over from an
            # assimilated preceding word, e.g. مِّنَ) — or the stem's first
            # consonant under the article, where the doubling is the article's
            # lām assimilating rather than a real geminate.
            # A shadda on the very first consonant is never a real geminate: it
            # is either the article's lām assimilating, or (مِّنَ) assimilation
            # carried over from the preceding word. Either way, don't double.
            if j > 0 or (j == 0 and not no_initial_gemination and i > 1):
                if j >= 0:
                    out.insert(j + 1, out[j])
            i += 1
            continue

        if ch in 'aui':
            out.append(ch)
            i += 1
            continue
        if ch == 'F':
            out.append('an')
            i += 1
            continue
        if ch == 'N':
            out.append('un')
            i += 1
            continue
        if ch == 'K':
            out.append('in')
            i += 1
            continue

        if ch in CONS:
            out.append(CONS[ch])
            first_cons_done = True
            i += 1
            continue
        i += 1
    return ''.join(out)


def rom_word(segments, pausal: bool = False) -> str:
    """Romanize one whole word from its ordered morphology segments.

    `segments` is a list of (buckwalter, tag). Using the corpus' own
    segmentation — rather than guessing proclitics with a regex — is what makes
    the hyphenation reliable: wa-, bi-, li-, and the article are tagged PREFIX.

    `pausal=True` returns the waqf form (tanwīn and the final short vowel
    dropped), which is how notes usually cite a word at the end of a quote. The
    stored match key is built from this form.
    """
    prefixes: list[str] = []
    stem_bw = ''
    had_article = False
    carry = ''          # consonant+vowel pulled out of an assimilated article

    for bw, tag in segments:
        bw = (bw or '')
        is_prefix = (tag or '').upper() == 'PREFIX'
        if is_prefix:
            # The article carries waṣla/alif ({l, Al) or is a bare lām (possibly
            # with assimilating shadda). A lām with its own kasra is the
            # preposition li-, not the article — لِلذَّٰكِرِينَ is li- + l- + stem.
            m = re.fullmatch(r'(?:[\{A]l|l)(~?)([aui]?)o?', bw)
            if m and bw not in ('li', 'la', 'lu'):
                prefixes.append('al' if not prefixes else 'l')
                had_article = True
                # ٱلَّيْلِ is segmented "{l~a" + "yoli": the doubled lām is the
                # stem's own first letter absorbed into the prefix, so hand it
                # back to the stem rather than losing it.
                if m and m.group(1) == '~':
                    carry = 'l' + (m.group(2) or '')
                continue
            prefixes.append(_rom_segment(bw))
            continue
        stem_bw += bw

    # Some words are not segmented at all and carry the article inside the stem
    # (ٱللَّهُ is a single PN segment "{ll~ahu"), so peel it off here too.
    if not had_article and re.match(r'^[\{A]l.', stem_bw):
        prefixes.append('al' if not prefixes else 'l')
        had_article = True
        stem_bw = stem_bw[2:]

    # Romanize stem + all suffixes as one string: long vowels and geminates
    # routinely straddle the corpus' segment boundaries (ya*uwqu|wna -> yadhūqūna).
    stem = _rom_segment(carry + stem_bw, no_initial_gemination=had_article and not carry)

    # The divine name is the one place the rasm withholds a vowel the reading
    # supplies: ٱللَّه carries no dagger alif, so the long ā cannot be derived.
    # It is also the corpus' most frequent noun, so special-case it rather than
    # ship "al-lahu" on every occurrence.
    m = re.fullmatch(r'(l+)ah([uai]?)', stem)
    if m and had_article:
        stem = 'lāh' + m.group(2)
    elif m and not had_article and len(m.group(1)) >= 1 and re.match(r'^l~a', stem_bw):
        stem = 'llāh' + m.group(2)

    if pausal and stem:
        # Guard the length: in ʾan / ʾin / ʿan the "an" is the whole word, not
        # a tanwīn ending, and stripping it erases the word entirely.
        if len(stem) >= 5:
            stem = re.sub(r'(?:an|un|in)$', '', stem)
        if len(stem) > 2:
            stem = re.sub(r'[aui]$', '', stem)

    out = ''
    for i, p in enumerate(prefixes):
        out += p if i == 0 else '-' + p
    if stem:
        out = (out + '-' + stem) if out else stem
    return out


PROCLITICS = {'wa', 'fa', 'bi', 'li', 'ka', 'la', 'sa', 'ta', 'a'}


def _is_proclitic(p: str) -> bool:
    return p in PROCLITICS


# --- match keys ---------------------------------------------------------------

_FOLD = {
    'ā': 'a', 'ī': 'i', 'ū': 'u', 'ḥ': 'h', 'ṣ': 's', 'ḍ': 'd', 'ṭ': 't',
    'ẓ': 'z', 'ḏ': 'd', 'ṯ': 't', 'ḫ': 'h', 'š': 's', 'ġ': 'g', 'ʾ': '',
    'ʿ': '', 'ẖ': 'h', 'ḳ': 'k', 'ẓ̄': 'z',
}


def translit_key(s: str) -> str:
    """Collapse every spelling variation a note might plausibly use down to one
    comparable token. Deliberately lossy — precision is recovered by matching
    whole contiguous runs of words, not single tokens."""
    if not s:
        return ''
    s = unicodedata.normalize('NFC', s).lower()
    for a, b in _FOLD.items():
        s = s.replace(a, b)
    s = s.replace('’', '').replace('‘', '').replace("'", '').replace('`', '')
    s = re.sub(r'[^a-z]', '', s)
    s = re.sub(r'^a?l(?=[a-z]{3})', '', s)     # leading definite article
    s = re.sub(r'(.)\1+', r'\1', s)            # sun-letter / shadda doubling
    # NB: no tanwīn stripping here. After folding ī->i the tanwīn ending -in is
    # indistinguishable from the sound-plural -īn (al-muttaqīn), so removing it
    # blindly destroys real words. Tanwīn *is* knowable from the Buckwalter, so
    # it is dropped at generation time via rom_word(pausal=True) instead.
    # These two are mutually exclusive: applying both in sequence shaves twice
    # (ṣalāta -> sala -> sal) and leaves a stub that collides with unrelated
    # words. Only ever remove one final element.
    if len(s) > 3:
        if re.search(r'a[ht]$', s):
            s = s[:-1]                         # tāʾ marbūṭa: -ah / -at -> -a
        else:
            # Pausal forms drop the final short vowel; safe only once the stem
            # is long enough to still identify the word (lā, illā stay put).
            s = re.sub(r'[aui]$', '', s)
    return s


_AR_DIAC = re.compile(r'[ً-ٰٟۖ-ۭـ]')
_AR_FOLD = {
    'آ': 'ا', 'أ': 'ا', 'إ': 'ا', 'ٱ': 'ا',
    'ى': 'ي', 'ة': 'ه', 'ؤ': 'ء', 'ئ': 'ء',
}


def arabic_plain(s: str) -> str:
    """Strip diacritics and tatweel; keep letters as written.

    496 rows of `morphology.form_arabic` carry a `#` where a hamza carrier
    should be (شَيْـ#ًا for شَيْـًٔا). The displayed text in `verses.text_uthmani`
    is clean, so this is normalised here at read time rather than by rewriting
    the stored Qur'anic text.
    """
    if not s:
        return ''
    s = unicodedata.normalize('NFC', s).replace('#', 'ء')
    return _AR_DIAC.sub('', s).strip()


def arabic_key(s: str) -> str:
    """Undotted-ish skeleton for matching Arabic citations against verse words."""
    s = arabic_plain(s)
    s = ''.join(_AR_FOLD.get(ch, ch) for ch in s)
    s = re.sub(r'[^ء-ي]', '', s)
    s = re.sub(r'^ا?ل(?=.{2})', '', s)         # definite article
    s = re.sub(r'(.)\1+', r'\1', s)
    return s
