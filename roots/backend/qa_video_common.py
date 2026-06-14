"""Shared, import-safe helpers for the Q&A video pipeline.

DELIBERATELY does not `import app` — importing app.py boots Flask, the
scheduler threads, and the IDF engine (~2s + side effects). Like
educational_pipeline.py duplicates _BW_TO_SR "so this module is
import-safe", we re-implement the two small text helpers here. They
are byte-for-byte copies of:
    - app._strip_bismillah               (verse-1 basmala strip)
    - educational_render_remotion._strip_uthmani_marks
so the Arabic string this module produces is the EXACT string the
renderer is handed — which is what makes the highlight match-gate
sound. Keep them in sync if the originals ever change.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import unicodedata
from functools import lru_cache

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_FULL_DB = os.path.join(_DATA_DIR, "quran.db")
_SLIM_DB = os.path.join(_DATA_DIR, "qa_video_source.db")


def _resolve_db() -> str:
    """Pick the source DB. Explicit env wins; otherwise the full quran.db
    when present (local dev); otherwise the slim committed export
    (qa_video_source.db) — which is what a cloud Routine has, since the
    718MB quran.db is gitignored. Build the slim file with
    qa_video_export_db.py."""
    env = os.environ.get("QA_VIDEO_DB")
    if env:
        return env
    if os.path.exists(_FULL_DB):
        return _FULL_DB
    return _SLIM_DB


DB_PATH = _resolve_db()


def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
#  Arabic text shaping — must mirror the renderer's input exactly
# ---------------------------------------------------------------------------

# Same mark range the renderer/libass path strips. NOTE this keeps the
# basic harakat (U+064B–U+0652): it only removes the small-high marks,
# superscript alef, maddah, and hamza-above, plus alef-wasla→alef. The
# match-gate therefore compares words by consonantal skeleton (see
# normalize_ar), which is robust to whichever marks survive.
_UTHMANI_MARK_RE = re.compile(r"[ٰٓٔۖ-ۭ]")


def strip_uthmani_marks(text: str) -> str:
    """Copy of educational_render_remotion._strip_uthmani_marks."""
    if not text:
        return text
    out = text.replace("ٱ", "ا")  # alef wasla → plain alef
    return _UTHMANI_MARK_RE.sub("", out)


@lru_cache(maxsize=1)
def _bismillah(db_path: str = DB_PATH) -> str:
    conn = get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter=1 AND verse=1"
        ).fetchone()
    finally:
        conn.close()
    return row["text_uthmani"] if row else ""


@lru_cache(maxsize=1)
def _bismillah_skeleton(db_path: str = DB_PATH) -> tuple[str, ...]:
    bis = _bismillah(db_path)
    return tuple(c for c in bis if not unicodedata.combining(c) and not c.isspace())


def strip_bismillah(text: str, surah: int, ayah: int, db_path: str = DB_PATH) -> str:
    """Copy of app._strip_bismillah (skeleton match, diacritic-insensitive
    — handles the 95:1 / 97:1 shadda-variant basmala)."""
    if ayah != 1 or surah == 1:
        return text
    bis = _bismillah(db_path)
    if bis and text.startswith(bis):
        return text[len(bis):].strip()
    skel = _bismillah_skeleton(db_path)
    ti = 0
    for i, ch in enumerate(text):
        if unicodedata.combining(ch) or ch.isspace():
            continue
        if ti < len(skel) and ch == skel[ti]:
            ti += 1
            if ti == len(skel):
                j = i + 1
                while j < len(text) and unicodedata.combining(text[j]):
                    j += 1
                return text[j:].strip()
        else:
            return text
    return text


def display_arabic(text_uthmani: str, surah: int, ayah: int, db_path: str = DB_PATH) -> str:
    """The exact Arabic string the renderer receives as `arabicText`:
    basmala stripped (verse 1) on the marked text, THEN Uthmani marks
    stripped. Order matters — strip_bismillah skeleton-matches the
    marked text."""
    return strip_uthmani_marks(strip_bismillah(text_uthmani, surah, ayah, db_path))


def verse_tokens(arabic_text: str) -> list[str]:
    """Tokenize the SAME way the renderer does: `arabicText.split(/\\s+/)`.
    No trim — mirror JS split semantics so 1-based indices align."""
    return re.split(r"\s+", arabic_text)


def normalize_ar(s: str) -> str:
    """Consonantal skeleton: NFC, drop ALL combining marks, drop tatweel,
    normalize alef-wasla→alef, collapse/strip space. Used to compare an
    intended word against the token the renderer would light, tolerant
    of harakat differences (the same strength app uses for the basmala)."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("ٱ", "ا").replace("ـ", "")  # alef-wasla, tatweel
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.strip()


# Arabic proclitic letters that glue onto the FRONT of a whitespace
# token (wa-, fa-, bi-, ka-, li-, sa-, and the al- article). The
# renderer can only highlight a whole whitespace token, so the intended
# content word may differ from the on-screen token by a leading
# proclitic — and lighting the whole token is the correct behaviour.
_PROCLITIC_CHARS = set("وفبكلاس")


def token_matches_form(token: str, form: str) -> bool:
    """True if the on-screen `token` is the intended `form`, allowing the
    token to carry a leading proclitic the form omits (e.g. token
    'وَنَصَرْنَٰهُمْ' matches form 'نَصَرْنَهُمْ'). Used IDENTICALLY by the
    compiler (to resolve indices) and the match-gate (to validate them)
    so the two can never disagree."""
    t, f = normalize_ar(token), normalize_ar(form)
    if not f:
        return False
    if t == f:
        return True
    if t.endswith(f):
        pre = t[: len(t) - len(f)]
        if 1 <= len(pre) <= 3 and all(ch in _PROCLITIC_CHARS for ch in pre):
            return True
    return False


# ---------------------------------------------------------------------------
#  Verse data (Arabic + the same translation the website shows)
# ---------------------------------------------------------------------------


def verse_data(conn, c: int, v: int) -> dict | None:
    """Mirror educational_render_remotion._verse_data: raw text_uthmani +
    best translation (ai_translations.revised_text||translation_text,
    newest; falls back to translations.text_en). Returns None if the
    verse doesn't exist."""
    arow = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (c, v)
    ).fetchone()
    if not arow:
        return None
    translation = ""
    ai_row = conn.execute(
        "SELECT revised_text, translation_text FROM ai_translations "
        "WHERE chapter=? AND verse=? ORDER BY id DESC LIMIT 1",
        (c, v),
    ).fetchone()
    if ai_row:
        translation = (ai_row["revised_text"] or ai_row["translation_text"] or "").strip()
    if not translation:
        erow = conn.execute(
            "SELECT text_en FROM translations WHERE chapter=? AND verse=? LIMIT 1",
            (c, v),
        ).fetchone()
        if erow:
            translation = (erow["text_en"] or "").strip()
    return {"arabic_raw": arow["text_uthmani"], "translation": translation}


def verse_exists(conn, c: int, v: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM verses WHERE chapter=? AND verse=?", (c, v)
    ).fetchone() is not None


def parse_ref(ref: str) -> tuple[int, int]:
    """'39:42' -> (39, 42). Raises ValueError on malformed refs."""
    m = re.match(r"^\s*(\d+)\s*:\s*(\d+)\s*$", str(ref))
    if not m:
        raise ValueError(f"bad verse ref: {ref!r}")
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------------------
#  TTS hygiene (light, import-safe). The structured script's narration
#  should already be voice-ready; this is the safety net.
# ---------------------------------------------------------------------------

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
         "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _num_to_words(n: int) -> str:
    if n < 0:
        return "minus " + _num_to_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return (_TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")).strip("-")
    if n < 1000:
        rem = n % 100
        return _ONES[n // 100] + " hundred" + (" " + _num_to_words(rem) if rem else "")
    return str(n)


def _spoken_ref(m: re.Match) -> str:
    c, v = int(m.group(1)), int(m.group(2))
    return f"{_num_to_words(c)}, verse {_num_to_words(v)}"


def sanitize_for_tts(text: str) -> str:
    """Strip markdown emphasis, voice verse refs ('39:42' -> 'thirty-nine,
    verse forty-two'), collapse whitespace. Conservative — leaves Arabic
    transliterations intact for ElevenLabs multilingual."""
    if not text:
        return ""
    t = text
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)   # **bold**
    t = re.sub(r"\*(.+?)\*", r"\1", t)         # *italic*
    t = re.sub(r"`(.+?)`", r"\1", t)
    t = re.sub(r"\b(\d{1,3}):(\d{1,3})\b", _spoken_ref, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------------------------------------------------------
#  Hashing (provenance lock / drift detection)
# ---------------------------------------------------------------------------


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
#  Duration estimate (the 60-90s budget is narration-driven)
# ---------------------------------------------------------------------------

# Default ElevenLabs speaking rate. Refine with calibrate_wps() against
# the renderer's audio-cache (real text+duration pairs) when available.
DEFAULT_WPS = 2.6  # words per second (~156 wpm)


def estimate_duration_sec(spoken_text: str, wps: float = DEFAULT_WPS) -> float:
    words = [w for w in re.split(r"\s+", sanitize_for_tts(spoken_text)) if w]
    return len(words) / max(wps, 0.1)


def word_count(spoken_text: str) -> int:
    return len([w for w in re.split(r"\s+", sanitize_for_tts(spoken_text)) if w])
