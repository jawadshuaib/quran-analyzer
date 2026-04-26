"""Detect candidates where conventional translations treat descriptive
Arabic phrases as proper nouns (e.g. "Abu Lahab" left untranslated when
the underlying Arabic literally means "father of [burning] flame").

Two-stage pipeline (this script):

  Stage 0 — Mechanical pre-filter, free, full corpus.
            Walks morphology + ai_word_meanings looking for capitalized
            tokens whose underlying Arabic root has descriptive uses
            elsewhere. Indefiniteness, compound-name markers (Abu/Ibn/
            Dhu/etc.), and root-frequency profiles are tallied per row.

  Stage 1 — Ollama cloud detector, cheap. For each Stage-0 candidate
            we ask Qwen 397B and (optionally) gpt-oss 120B:
                "Is this a proper name or a descriptive Arabic phrase?"
            with the verse, word, transliteration, and a sample of
            cross-references where the same root is used non-name-like.
            Both verdicts are stored per-row.

Stage 2 (Sonnet adjudication) lives in proper_noun_adjudicate.py.
Stage 3 (operator review) is the admin UI at /admin/proper-nouns.

Usage:
    python proper_noun_detect.py --stage 0
    python proper_noun_detect.py --stage 1 --models qwen
    python proper_noun_detect.py --stage 1 --models qwen,gptoss --limit 50
    python proper_noun_detect.py --stage 1 --refresh   # re-run on already-stage1 rows
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
import time

import requests

from app import get_db


# ---------------------------------------------------------------------------
# Stage 0 configuration
# ---------------------------------------------------------------------------

# --- Morphology pos filtering -------------------------------------------
# Only these "content word" parts of speech can ever be proper-noun
# calques. Filters out prefixes/suffixes/particles/pronouns/demonstratives
# at the SQL level so we never even consider وَ / ٱل / ذَٰلِكَ / إِيَّاكَ /
# ٱلَّذِينَ / مَا / لَا — the dominant noise source in the first run.
CONTENT_POS = ("Proper Noun", "Noun", "Adjective", "Verb")

# Prefer Proper Noun > Noun > Adjective > Verb when picking one row per
# (chapter, verse, word_pos). The CASE expression below uses these ranks.
POS_RANK = {"Proper Noun": 1, "Noun": 2, "Adjective": 3, "Verb": 4}


# --- Compound markers (high-signal: Abu/Ibn/Dhu + X is a calque template) ---
COMPOUND_MARKERS_EN = {"abu", "abi", "ibn", "bin", "ben", "umm", "bint",
                      "dhul", "dhu", "dhat", "dhi", "dhāt", "dhū",
                      "banu", "bani", "ahl", "aal", "al-",
                      "ash-", "as-", "an-", "at-", "ath-", "adh-"}


# --- Diacritic / transliteration signature ---------------------------------
# Real proper-noun transliterations frequently carry these characters.
# Plain English religious titles (Merciful, Wise, Fire) almost never do.
TRANSLITERATION_PATTERN = re.compile(
    # Underdots, macrons, ʿayn / hamza, characteristic Arabicist letters
    r"[\u0100-\u017F\u1E00-\u1EFF\u02BB-\u02BD\u02BE\u02BFḤḥṢṣṬṭḌḍẒẓʿʾāēīōūĀĒĪŌŪñǧǦġĠḳḲ]"
)


# --- English allowlist of words that are CAPITALIZED but never proper-noun
#     calques. We only consult this when no positive marker (compound /
#     diacritic) is present — the positive markers are the primary filter.
KNOWN_NAMES = {
    # Divine names / forms commonly capitalized
    "allah", "god", "lord", "creator", "fashioner", "originator",
    "ever-living", "self-subsisting", "self-sustaining",
    # Prophets / persons (English + transliterations we already classify
    # as known names)
    "muhammad", "mohammed", "ahmad",
    "moses", "musa", "aaron", "harun",
    "abraham", "ibrahim",
    "ishmael", "ismail",
    "isaac", "ishaq",
    "jacob", "yaqub", "israel",
    "joseph", "yusuf",
    "david", "dawud",
    "solomon", "sulayman",
    "jesus", "isa", "messiah", "christ",
    "mary", "maryam",
    "adam", "eve",
    "noah", "nuh",
    "lot", "lut",
    "job", "ayub",
    "jonah", "yunus",
    "zechariah", "zakariyya",
    "john", "yahya",
    "elias", "elijah", "ilyas",
    "elisha", "alyasa",
    "shu'aib", "shuaib", "shoaib",
    "salih", "hud", "luqman", "khidr", "imran",
    "pharaoh", "firawn",
    # Locales / tribes
    "mecca", "makka", "bakka",
    "medina", "yathrib",
    "egypt", "misr",
    "babylon", "babil",
    "jerusalem", "bayt",
}


# Plain English words / religious titles that are commonly capitalized in
# translations but are NOT proper-noun calques. They occur as labels for
# divine attributes (the Merciful), eschatological referents (the Fire),
# scriptural objects (the Book), and so on. We're aggressive here because
# the positive signals (compound or diacritic) handle the real cases.
COMMON_ENGLISH_TITLES = {
    # Divine attributes / epithets
    "merciful", "compassionate", "wise", "knowing", "mighty", "powerful",
    "all-knowing", "all-wise", "all-mighty", "all-powerful", "all-hearing",
    "all-seeing", "ever-watchful", "most", "exalted", "high", "great",
    "supreme", "absolute", "unique", "everlasting", "eternal",
    "self-subsisting", "self-sustaining", "ever-living", "subtle",
    "appreciative", "forbearing", "forgiving", "oft-forgiving", "loving",
    "gentle", "patient", "just", "true", "rich", "praiseworthy",
    "majestic", "noble", "kind", "sublime", "first", "last",
    "manifest", "hidden", "watchful", "guardian", "protector",
    "preserver", "reckoner", "judge", "ruler", "sovereign", "king",
    "originator", "evolver", "fashioner",
    "oft-turning", "oft-returning", "ever-turning-back", "ever-watchful",
    "self-standing", "self-existent",
    "specially", "entirely", "especially",
    # Eschatology / world / cosmos
    "fire", "garden", "paradise", "hell", "hellfire", "hereafter",
    "heaven", "heavens", "earth", "world", "blaze", "flame",
    "throne", "footstool", "house", "mosque", "mount", "cave", "valley",
    "ark", "tablet", "tablets", "scripture", "book", "scrolls",
    "day", "night", "morning", "evening", "hour", "moment",
    "judgment", "resurrection", "reckoning", "balance", "scale",
    "later", "later-life", "now",
    # Scriptural / theological terms
    "spirit", "spirits", "angel", "angels", "messenger", "messengers",
    "prophet", "prophets", "warner", "warners", "witness", "witnesses",
    "believer", "believers", "disbeliever", "disbelievers", "hypocrite",
    "hypocrites", "polytheist", "polytheists", "muslim", "muslims",
    "jew", "jews", "christian", "christians", "nazarene", "nazarenes",
    "magian", "sabian", "people", "children",
    "covenant", "promise", "warning", "tidings", "news", "command",
    "commands", "law", "laws", "decree", "decrees",
    "sign", "signs", "verse", "verses", "remembrance", "reminder",
    "guidance", "misguidance", "truth", "falsehood", "right", "wrong",
    "religion", "faith", "belief", "trust", "deeds", "deed",
    # Common English stopwords / sentence-initial capitalization
    "the", "a", "an", "of", "and", "or", "but", "yet", "so", "if",
    "as", "at", "by", "in", "on", "to", "for", "with", "from",
    "into", "onto", "upon", "over", "under", "before", "after",
    "during", "until", "since", "because", "while", "though", "although",
    "even", "ever", "never", "only", "just", "also", "too",
    "indeed", "truly", "verily", "behold", "rather", "now", "then",
    "here", "there", "where", "why", "how", "when",
    "who", "whom", "whose", "which", "what", "this", "that", "these",
    "those", "such", "some", "every", "all", "each", "any", "no",
    "both", "either", "neither", "one", "another", "other",
    "shall", "will", "may", "must", "should", "could", "would",
    "ought", "might", "can", "do", "does", "did", "done",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "praise", "praised", "thanks", "glory", "glorified",
    "indeed", "indeed,",
    # Pronouns — capitalized in religious translations as a stylistic
    # convention (referring to God/the Prophet) but never proper nouns.
    "i", "me", "my", "mine", "myself",
    "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    "ye", "thou", "thee", "thy", "thine", "thyself",
}


_ENGLISH_TITLE_PREFIXES = ("ever-", "all-", "oft-", "most-", "self-")


def _is_english_title_word(low: str) -> bool:
    """True when a lowercased token (or hyphen-joined compound) is an
    English religious epithet pattern that's never a proper-noun calque.
    Catches: 'ever-merciful', 'all-knowing', 'oft-forgiving', 'self-
    subsisting', 'most-merciful', etc. — without listing every variant."""
    if not low:
        return False
    # Normalize Unicode hyphens to ASCII before matching
    norm = low.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    if norm in KNOWN_NAMES or norm in COMMON_ENGLISH_TITLES:
        return True
    for p in _ENGLISH_TITLE_PREFIXES:
        if norm.startswith(p):
            return True
    # Hyphenated compound where ALL parts are stoplisted English (e.g.
    # "in-forgiveness", "covering-in-forgiveness", "turning-back").
    if "-" in norm:
        parts = [p for p in norm.split("-") if p]
        if parts and all(p in KNOWN_NAMES or p in COMMON_ENGLISH_TITLES for p in parts):
            return True
    return False


def _has_transliteration_marker(text: str) -> bool:
    """True when text contains a non-ASCII letter (diacritic / macron /
    underdot / hamza-letter / etc.) characteristic of Arabicist
    transliterations. Plain English doesn't trip this."""
    return bool(TRANSLITERATION_PATTERN.search(text or ""))


# Buckwalter consonant → rough Latin character set. Used to decide
# whether a capitalized English token "looks like" a transliteration of
# the Arabic root vs an actual English translation. The Latin set is
# intentionally generous (multiple plausible mappings per BW char) so we
# accept variant transliterations.
BW_LATIN_EQUIV = {
    "A": "aā", "a": "aā", "i": "iī", "u": "uū", "o": "", "e": "e",
    "y": "y", "w": "w",
    "b": "b", "t": "t", "p": "h",
    "g": "g", "d": "d", "D": "dḍ", "r": "r", "z": "z",
    "s": "s", "S": "sṣ", "f": "f", "k": "k", "l": "l",
    "m": "m", "n": "n",
    "h": "h", "H": "hḥ", "q": "q",
    "x": "kḵ", "$": "s",  # sh — match against 's' approximately
    "T": "tṭ", "Z": "zẓ",
    "E": "ʿ",  # ayn — often dropped in English; ʿ is a marker
    "G": "g",  # gh
    "`": "", "|": "aā",
    ">": "aā", "<": "iī",
    "&": "w", "*": "td",  # th/dh
    "'": "ʾ",
    "~": "", "F": "n", "N": "n", "K": "n",
    "{": "aā", "}": "iʾ",
}


def _token_looks_like_transliteration(token: str, root_bw: str | None) -> bool:
    """True when the lowercased token contains enough of the Arabic
    root's consonant skeleton in order to plausibly BE a transliteration
    of that root (vs an English translation). The threshold is purposely
    generous: any 2+ consonants from the root that appear in the token
    in the right order count as a match.

    Discriminates "Lahab" (root lhb → l, h, b all in 'lahab') from
    English glosses like "Possessor" (root mlk → m, l, k — only 'l' in
    'possessor', miss).
    """
    if not token or not root_bw:
        return False
    # Pick out the consonant skeleton from BW (strip vowels + diacritics)
    consonants = []
    for c in root_bw:
        latin = BW_LATIN_EQUIV.get(c, "").lower()
        # Skip the BW chars that map to nothing or to vowels only
        if latin and any(ch.isalpha() and ch not in "aeiouāēīōūʿʾ" for ch in latin):
            consonants.append(latin)
    if len(consonants) < 2:
        return False

    low = token.lower()
    # Match consonants in order — try each consonant set against the rest
    # of the token starting from the previous match position.
    cursor = 0
    matched = 0
    for cset in consonants:
        # cset can be a multi-char set of valid Latin chars (e.g. "ḥh")
        for letter in cset:
            if not letter.isalpha():
                continue
            idx = low.find(letter, cursor)
            if idx >= 0:
                cursor = idx + 1
                matched += 1
                break
    return matched >= 2 and matched >= len(consonants) // 2 + (1 if len(consonants) <= 3 else 0)


def _is_capitalized_token(s: str) -> bool:
    """A token is 'capitalized' if it has any uppercase ASCII letter
    AND its leading alphabetic char is uppercase. We use this on per-token
    pieces of preferred_translation to flag possible name-like renderings."""
    if not s:
        return False
    # Strip surrounding punctuation for the test (but keep apostrophes inside)
    core = s.strip(".,;:!?\"'()[]{}<>‘’“”—–-")
    if not core:
        return False
    # Reject tokens that are pure punctuation or numbers
    if not any(c.isalpha() for c in core):
        return False
    first_alpha = next((c for c in core if c.isalpha()), '')
    return first_alpha.isupper()


def _looks_like_proper_noun(translation: str, root_bw: str | None = None,
                            morph_pos: str | None = None) -> tuple[bool, str | None]:
    """Decide whether a per-word translation looks like a transliterated
    proper noun. Returns (flagged, compound_marker_or_None).

    Stricter version. Requires at least ONE positive marker:
      (a) compound prefix (Abu / Ibn / Dhu / Bani / etc.) — high signal
      (b) transliteration diacritic / macron / underdot anywhere
      (c) morph_pos == "Proper Noun" (morphology already says it's a name)
      (d) capitalized token whose letters resemble the Arabic root's
          consonant skeleton (i.e. it BE a transliteration, not an
          English translation that just happens to be capitalized).

    Sentence-initial capitalization (i = 0) is ignored on its own.
    Multi-token translations with no compound and no diacritic are
    rejected unless one of their non-initial tokens resembles the root.
    """
    if not translation:
        return False, None
    text = translation.strip()
    if not text:
        return False, None

    # Strong signal: any diacritic anywhere is enough.
    if _has_transliteration_marker(text):
        # Still need to detect compound marker for type/labeling.
        for tok in re.split(r"\s+", text):
            tok_norm = tok.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
            clean = re.sub(r"[^A-Za-z'’\-]", "", tok_norm).strip().lower()
            if clean in COMPOUND_MARKERS_EN:
                return True, clean
        return True, None

    tokens = [t for t in re.split(r"\s+", text) if t]
    if not tokens:
        return False, None

    # Special case: single-token gloss like "Lahab" / "Iram" / "Iblis".
    # We need a stricter signal here because plain English single-token
    # imperatives ("Eat" / "Strike" / "Say") and divine attributes
    # ("Possessor" / "Holy") are commonly capitalized in translations.
    # Accept only when one of:
    #   - morph_pos == "Proper Noun" (morphology already classified it)
    #   - the token resembles the Arabic root's consonant skeleton
    if len(tokens) == 1:
        tok = tokens[0]
        # Normalize Unicode hyphens to ASCII before sanitizing — otherwise
        # 'Ever‑turning‑back' (U+2011) gets stripped to 'Everturningback'
        # and slips past the title-word allowlist.
        tok_norm = tok.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
        clean = re.sub(r"[^A-Za-z'’\-]", "", tok_norm).strip()
        low = clean.lower()
        if not _is_capitalized_token(tok):
            return False, None
        if _is_english_title_word(low):
            return False, None
        if low in COMPOUND_MARKERS_EN:
            return False, None
        if (morph_pos or "").strip() == "Proper Noun":
            return True, None
        if _token_looks_like_transliteration(low, root_bw):
            return True, None
        return False, None

    compound: str | None = None
    candidate_capitalized = False
    for i, tok in enumerate(tokens):
        # Normalize Unicode hyphens to ASCII before sanitizing — otherwise
        # 'Ever‑turning‑back' (U+2011) gets stripped to 'Everturningback'
        # and slips past the title-word allowlist.
        tok_norm = tok.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
        clean = re.sub(r"[^A-Za-z'’\-]", "", tok_norm).strip()
        if not clean:
            continue
        low = clean.lower()

        # Bare compound marker (token "Abu" / "Dhu" / "Bani") — high
        # signal regardless of position.
        if low in COMPOUND_MARKERS_EN:
            compound = low
            continue

        # Hyphenated compound calque ("Dhul-Qarnayn", "Abu-Lahab",
        # "Bani-Israel"). Treat regardless of position — the compound
        # marker is itself a positive signal that overrides sentence-
        # initial capitalization heuristics.
        if "-" in low:
            parts = [p for p in low.split("-") if p]
            marker_parts = [p for p in parts if p in COMPOUND_MARKERS_EN]
            if marker_parts:
                compound = compound or marker_parts[0]
                tail_parts = [p for p in parts if p not in COMPOUND_MARKERS_EN]
                if any(t and t not in KNOWN_NAMES and t not in COMMON_ENGLISH_TITLES for t in tail_parts):
                    candidate_capitalized = True
                continue

        # For non-compound tokens: sentence-initial uppercase isn't a
        # signal — it's just convention. Skip i=0 unless it carried a
        # compound marker (handled above).
        if i == 0:
            continue
        if not _is_capitalized_token(tok):
            continue
        if _is_english_title_word(low):
            continue
        # Multi-token branch needs the same transliteration check —
        # otherwise "in the Garden" passes (Garden capitalized at i=2).
        if (morph_pos or "").strip() == "Proper Noun":
            candidate_capitalized = True
        elif _token_looks_like_transliteration(low, root_bw):
            candidate_capitalized = True

    if compound:
        return True, compound
    if candidate_capitalized:
        return True, None
    return False, None


def _is_indefinite_morphology_tag(tag: str | None) -> int:
    """Best-effort indefinite detector from morphology.tag string. The
    tagging convention varies; we look for the absence of 'DEF' / 'AL' /
    presence of explicit 'INDEF' as conservative signals."""
    if not tag:
        return 0
    t = tag.upper()
    if "INDEF" in t:
        return 1
    # Many tags include "DEF" for words with al-. Absence is suggestive
    # but not decisive — return 0 in that case so we don't over-claim.
    return 0


# ---------------------------------------------------------------------------
# Stage 0 implementation
# ---------------------------------------------------------------------------

def stage0_detect(conn) -> dict:
    """Run Stage 0 mechanical pre-filter over the entire corpus.

    Picks ONE content-word morphology row per (chapter, verse, word_pos)
    — preferring Proper Noun > Noun > Adjective > Verb — and only flags
    a candidate when the per-word English translation carries a positive
    proper-noun signal (compound marker like Abu/Ibn/Dhu, or a
    transliteration diacritic, or a capitalized token outside our
    common-English-titles allowlist).

    Inserts rows into proper_noun_candidates (UNIQUE on chapter, verse,
    word_pos prevents duplicates). Returns counts.
    """
    print("Stage 0: building root-frequency index…")
    root_freq: dict[str, int] = {}
    for r in conn.execute(
        "SELECT root_buckwalter FROM morphology "
        "WHERE root_buckwalter IS NOT NULL AND root_buckwalter != ''"
    ):
        root_freq[r["root_buckwalter"]] = root_freq.get(r["root_buckwalter"], 0) + 1
    print(f"  {len(root_freq)} roots in morphology")

    # Pick one content-word row per (chapter, verse, word_pos), favoring
    # Proper Noun > Noun > Adjective > Verb. Filters out Prefix / Suffix /
    # Pronoun / Demonstrative / Particle / Conjunction / etc. at the SQL
    # level so we never even look at them.
    print("Stage 0: collecting content-word rows + translations…")
    pos_placeholders = ",".join(["?"] * len(CONTENT_POS))
    pos_case = (
        "CASE m.pos "
        + " ".join(f"WHEN '{p}' THEN {POS_RANK[p]}" for p in CONTENT_POS)
        + " ELSE 99 END"
    )
    sql = f"""
        WITH ranked AS (
            SELECT m.chapter, m.verse, m.word_pos,
                   m.form_arabic, m.root_buckwalter, m.lemma_buckwalter,
                   m.tag, m.pos,
                   ROW_NUMBER() OVER (
                     PARTITION BY m.chapter, m.verse, m.word_pos
                     ORDER BY {pos_case}
                   ) AS rn
            FROM morphology m
            WHERE m.root_buckwalter IS NOT NULL
              AND m.root_buckwalter != ''
              AND m.pos IN ({pos_placeholders})
        )
        SELECT r.chapter, r.verse, r.word_pos,
               r.form_arabic, r.root_buckwalter, r.lemma_buckwalter,
               r.tag, r.pos,
               w.preferred_translation, w.meaning_short
        FROM ranked r
        LEFT JOIN ai_word_meanings w
               ON w.chapter=r.chapter AND w.verse=r.verse AND w.word_pos=r.word_pos
        WHERE r.rn = 1
        ORDER BY r.chapter, r.verse, r.word_pos
    """
    rows = conn.execute(sql, list(CONTENT_POS)).fetchall()
    print(f"  {len(rows)} content-word positions to scan")

    inserted = 0
    skipped_existing = 0
    skipped_no_translation = 0
    skipped_no_signal = 0
    by_type: dict[str, int] = {"compound": 0, "single": 0}
    by_pos: dict[str, int] = {}

    for row in rows:
        translation = (row["preferred_translation"] or row["meaning_short"] or "").strip()
        if not translation:
            skipped_no_translation += 1
            continue
        flagged, compound = _looks_like_proper_noun(
            translation, row["root_buckwalter"], row["pos"],
        )
        if not flagged:
            skipped_no_signal += 1
            continue

        ctype = "compound" if compound else "single"
        rfreq = root_freq.get(row["root_buckwalter"], 0)

        try:
            conn.execute(
                "INSERT INTO proper_noun_candidates ("
                "  chapter, verse, word_pos, "
                "  arabic_word, root_buckwalter, lemma_buckwalter, "
                "  surface_translation, candidate_type, "
                "  is_indefinite, root_quran_frequency, has_compound_marker"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["chapter"], row["verse"], row["word_pos"],
                    row["form_arabic"], row["root_buckwalter"], row["lemma_buckwalter"],
                    translation, ctype,
                    _is_indefinite_morphology_tag(row["tag"]),
                    rfreq, compound,
                ),
            )
            inserted += 1
            by_type[ctype] = by_type.get(ctype, 0) + 1
            by_pos[row["pos"]] = by_pos.get(row["pos"], 0) + 1
        except sqlite3.IntegrityError:
            skipped_existing += 1

    conn.commit()
    print(f"\nStage 0 complete:")
    print(f"  Inserted:           {inserted}")
    print(f"  Already existed:    {skipped_existing}")
    print(f"  No translation:     {skipped_no_translation}")
    print(f"  No proper-noun sig: {skipped_no_signal}")
    print(f"  By type:            {by_type}")
    print(f"  By morphology pos:  {by_pos}")
    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_no_translation": skipped_no_translation,
        "skipped_no_signal": skipped_no_signal,
        "by_type": by_type,
        "by_pos": by_pos,
    }


# ---------------------------------------------------------------------------
# Stage 1 — Ollama cloud detector
# ---------------------------------------------------------------------------

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
QWEN_MODEL = "qwen3.5:397b-cloud"
GPTOSS_MODEL = "gpt-oss:120b-cloud"  # adjust if exact tag differs

STAGE1_SYSTEM_PROMPT = """\
You are an Arabic-and-Quran expert helping decide whether a particular
translated word in an English Quran translation is being treated as a
PROPER NOUN (an actual person/place name) when it might more
faithfully be rendered as a literal Arabic descriptive phrase.

You will see:
  - The verse reference (e.g. 111:1)
  - The Arabic word (with diacritics)
  - The Arabic root (Buckwalter-transliterated) and lemma
  - The current English rendering
  - A short list of OTHER verses where the same root appears, with
    their conventional English translations — to show how the root is
    used elsewhere in the corpus

Your job is to deliver ONE verdict from this set:
  - "literal"   - the word looks more like a descriptive Arabic phrase
                  that the translator calqued as a name (e.g. "Abu Lahab"
                  for "father of flame", "Dhul-Qarnayn" for "the two-horned
                  one"). Translation should likely be revised.
  - "name"      - the word really is a proper name (person, place,
                  tribe). Leave it as-is.
  - "ambiguous" - genuinely uncertain — reasonable translators could
                  go either way.

Output ONLY a single JSON object, no preamble, no commentary:

{
  "verdict": "literal" | "name" | "ambiguous",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<2-4 sentences citing concrete evidence — frequency,
                indefiniteness, cross-references, compound structure>"
}
"""


def _gather_cross_references(conn, root_bw: str, exclude_chapter: int, exclude_verse: int, n: int = 6) -> list[dict]:
    """Pick up to N other verses where this root appears, with English
    translation. Used as evidence for the LLM."""
    rows = conn.execute(
        "SELECT m.chapter, m.verse, t.translation_text "
        "FROM morphology m "
        "LEFT JOIN ai_translations t ON t.chapter=m.chapter AND t.verse=m.verse "
        "WHERE m.root_buckwalter = ? "
        "  AND NOT (m.chapter = ? AND m.verse = ?) "
        "  AND t.translation_text IS NOT NULL "
        "GROUP BY m.chapter, m.verse "
        "ORDER BY m.chapter, m.verse",
        (root_bw, exclude_chapter, exclude_verse),
    ).fetchall()
    # Sample evenly across the corpus: take every Nth so we get diverse
    # examples rather than just the first N (which tend to cluster early).
    if len(rows) > n:
        step = max(1, len(rows) // n)
        rows = rows[::step][:n]
    return [
        {"ref": f"{r['chapter']}:{r['verse']}", "translation": (r["translation_text"] or "")[:300]}
        for r in rows
    ]


def _build_stage1_prompt(conn, candidate: dict) -> str:
    refs = _gather_cross_references(
        conn, candidate["root_buckwalter"], candidate["chapter"], candidate["verse"], n=6,
    )
    parts = [
        f"VERSE: {candidate['chapter']}:{candidate['verse']}",
        f"ARABIC WORD: {candidate['arabic_word']}",
        f"ROOT (Buckwalter): {candidate['root_buckwalter']}",
        f"LEMMA: {candidate.get('lemma_buckwalter') or '(unknown)'}",
        f"CURRENT ENGLISH: {candidate['surface_translation']}",
        "",
        f"COMPOUND MARKER PRESENT: {candidate.get('has_compound_marker') or '(none)'}",
        f"ROOT INDEFINITE IN ARABIC: {'yes' if candidate.get('is_indefinite') else 'unknown'}",
        f"ROOT FREQUENCY IN CORPUS: {candidate.get('root_quran_frequency')}",
        "",
        "OTHER VERSES USING THIS ROOT (for context):",
    ]
    if refs:
        for r in refs:
            parts.append(f"  - {r['ref']}: {r['translation']}")
    else:
        parts.append("  (none with translations)")
    parts += [
        "",
        "Decide whether the current English rendering is a proper name or a"
        " descriptive phrase being calqued as a name. Output JSON only.",
    ]
    return "\n".join(parts)


def call_ollama(model: str, system: str, user: str, api_key: str, timeout: int = 120) -> tuple[str, int]:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    t0 = time.time()
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(OLLAMA_CLOUD_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                return content, int((time.time() - t0) * 1000)
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise RuntimeError(f"Ollama {resp.status_code}: {resp.text[:300]}")
            last_err = f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            last_err = f"req: {e}"
        if attempt < 3:
            time.sleep(random.uniform(2, 6) * attempt)
    raise RuntimeError(f"Ollama failed: {last_err}")


def _parse_stage1_response(raw: str) -> dict:
    """Extract { verdict, confidence, reasoning } from model output.
    Tolerant of code fences and surrounding text."""
    text = (raw or "").strip()
    # Strip <think>...</think> blocks Qwen sometimes emits
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON found: {text[:300]!r}")
    obj = json.loads(m.group())
    verdict = (obj.get("verdict") or "").strip().lower()
    if verdict not in ("literal", "name", "ambiguous"):
        raise ValueError(f"bad verdict: {verdict!r}")
    confidence = float(obj.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": (obj.get("reasoning") or "").strip()[:2000],
    }


def stage1_run(conn, api_key: str, models: list[str], limit: int | None, refresh: bool) -> dict:
    """Run Stage 1 detector on candidates without stage1_run_at (or all
    if refresh). One row updated per (candidate, model)."""
    where = "WHERE stage1_run_at IS NULL" if not refresh else ""
    sql = (
        "SELECT id, chapter, verse, word_pos, arabic_word, "
        "       root_buckwalter, lemma_buckwalter, surface_translation, "
        "       candidate_type, is_indefinite, root_quran_frequency, "
        "       has_compound_marker "
        f"FROM proper_noun_candidates {where} "
        "ORDER BY id"
    )
    candidates = [dict(r) for r in conn.execute(sql).fetchall()]
    if limit:
        candidates = candidates[:limit]

    print(f"Stage 1: processing {len(candidates)} candidates with models: {models}")
    stats = {"qwen_ok": 0, "qwen_err": 0, "gptoss_ok": 0, "gptoss_err": 0, "total": len(candidates)}

    for i, c in enumerate(candidates, 1):
        prompt = _build_stage1_prompt(conn, c)
        ref = f"{c['chapter']}:{c['verse']}/p{c['word_pos']}"
        print(f"\n[{i}/{len(candidates)}] {ref}  '{c['surface_translation']}'  (root={c['root_buckwalter']})")

        if "qwen" in models:
            try:
                raw, ms = call_ollama(QWEN_MODEL, STAGE1_SYSTEM_PROMPT, prompt, api_key)
                parsed = _parse_stage1_response(raw)
                conn.execute(
                    "UPDATE proper_noun_candidates SET "
                    "  qwen_verdict = ?, qwen_confidence = ?, qwen_reasoning = ?, "
                    "  stage1_run_at = COALESCE(stage1_run_at, datetime('now')) "
                    "WHERE id = ?",
                    (parsed["verdict"], parsed["confidence"], parsed["reasoning"], c["id"]),
                )
                conn.commit()
                stats["qwen_ok"] += 1
                print(f"  qwen: {parsed['verdict']} ({parsed['confidence']:.2f}) [{ms} ms]")
            except Exception as e:
                stats["qwen_err"] += 1
                print(f"  qwen ERROR: {e}", file=sys.stderr)

        if "gptoss" in models:
            try:
                raw, ms = call_ollama(GPTOSS_MODEL, STAGE1_SYSTEM_PROMPT, prompt, api_key)
                parsed = _parse_stage1_response(raw)
                conn.execute(
                    "UPDATE proper_noun_candidates SET "
                    "  gptoss_verdict = ?, gptoss_confidence = ?, gptoss_reasoning = ?, "
                    "  stage1_run_at = COALESCE(stage1_run_at, datetime('now')) "
                    "WHERE id = ?",
                    (parsed["verdict"], parsed["confidence"], parsed["reasoning"], c["id"]),
                )
                conn.commit()
                stats["gptoss_ok"] += 1
                print(f"  gptoss: {parsed['verdict']} ({parsed['confidence']:.2f}) [{ms} ms]")
            except Exception as e:
                stats["gptoss_err"] += 1
                print(f"  gptoss ERROR: {e}", file=sys.stderr)

    print(f"\nStage 1 complete: {stats}")
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _get_ollama_api_key(conn) -> str:
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key='ollama_api_key'"
    ).fetchone()
    return (row["value"] if row else "") or ""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--stage", type=int, choices=[0, 1], required=True)
    p.add_argument("--models", default="qwen", help="comma-separated: qwen,gptoss")
    p.add_argument("--limit", type=int)
    p.add_argument("--refresh", action="store_true",
                   help="(stage 1) re-run on already-completed candidates")
    args = p.parse_args()

    conn = get_db()
    conn.row_factory = sqlite3.Row

    if args.stage == 0:
        stage0_detect(conn)
    else:
        api_key = _get_ollama_api_key(conn)
        if not api_key:
            print("ERROR: no ollama_api_key in admin_preferences.", file=sys.stderr)
            return 1
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models:
            print("ERROR: --models cannot be empty", file=sys.stderr)
            return 1
        stage1_run(conn, api_key, models, args.limit, args.refresh)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
