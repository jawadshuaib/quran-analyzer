"""Educational pipeline — Phase 2: script generation.

Given an `educational_videos` row in status='candidate', this module
calls Claude to produce a 4-beat script (hook, verse_intro, insight,
close) plus two voiceover variants:

    - voiceover_long  : 250-340 words, ~120-150s of narration
                        (regular YouTube uploads, no length cap)
    - voiceover_short : ≤120 words, ≤45s of narration
                        (YouTube Shorts / TikTok — capped at <60s
                         total because adding the reciter's voice
                         pushes the upper bound to ~55s, and Shorts
                         policy treats >60s with someone-else-audio
                         as a copyright risk).

Hard guardrails against hallucination:
    - Word Origins: every cognate language named in the script must
                    exist in the payload's derivatives. Validator
                    rejects scripts that invent languages.
    - Translation Hides: insight body must paraphrase the departure
                    note actually in the payload, not free-form.
    - Grammar Insights: must reference the V7 insight's claim/counter-
                    factual fields; we pass the structured insight to
                    the LLM and ask it to NOT introduce new claims.

Public surface:
    enrich_payload(conn, row)  → fetches the full structured grounding
                                 (cognates, departure note, V7 insight)
                                 from existing tables, given an
                                 educational_videos row.
    generate_script(payload, vtype, *, api_key, model)
                               → returns dict {hook, verse_intro,
                                 insight, close, voiceover_long,
                                 voiceover_short, cognates_referenced,
                                 raw_response} on success, raises
                                 ScriptGenError otherwise.
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import requests


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5"


# Style guide injected at the top of every prompt — keeps the voice
# consistent across the three series and rules out the failure modes
# we know hurt watch time (rambly intros, doctrinal asides, vague
# language).
SYSTEM_PROMPT = """You write tight, factual narration for short Quran-research videos on al-nuqta.com.

Tone & framing:
- Curiosity-led, never preachy. The hook should make the viewer think "wait, really?"
- Linguistic and historical only. Never doctrinal, never sectarian, never tafsir.
- Plain English, second-person OK. No archaic "thee/thou".
- Don't open with "Did you know" — show, don't tell.

Hard rules:
- ONLY use facts present in the structured payload provided.
- Never invent etymological dates, cognate languages, or grammatical claims.
- If the payload doesn't support the insight you'd like to make, say so honestly in `notes` and we'll skip the candidate.
- Output STRICT JSON. No markdown, no commentary outside the JSON.

Voiceover discipline (CRITICAL — voiceover_long and voiceover_short are read aloud by ElevenLabs TTS):
- Use natural English. NEVER include academic IPA marks: ʕ, ʔ, ʿ, ʾ, ḥ, ḫ, ṯ, ḏ, ṣ, ḍ, ṭ, ẓ, ġ, ā, ē, ī, ō, ū, s¹, s².
- NEVER include Buckwalter (e.g. "Eyn", "Hmd") or hyphenated transliterations (e.g. "ʕ-y-n", "ḥ-m-d") in the voiceover.
- For an Arabic root, say it phonetically in plain English: "the root ayn-ya-nun" or "the three-letter root meaning eye". Avoid letter-by-letter spellouts that aren't pronounceable.
- For an Arabic word, give an English-friendly transliteration ("a-yun" not "aʕyun") followed by its meaning, OR skip the Arabic and just say what it means.
- NEVER drop Arabic-script characters into the voiceover — the reciter's audio handles the Arabic. Voiceover is English only.
- Other beats (hook / verse_intro / insight / close) may use proper transliterations sparingly because they're for on-screen display, not narration. But voiceover_long and voiceover_short must read aloud cleanly.

Output schema (all keys required, all strings unless noted):
{
  "hook":          "1 sentence, ≤22 words. For Word Origins, MUST start with 'Did you know'. Other types may use any opener.",
  "tidbit_about_root": "(Word Origins ONLY) 1-2 sentences with one striking fact about the root's meaning, history, or oldest attestation. Empty string '' for other types.",
  "tidbit_about_quran_usage": "(Word Origins ONLY) 1-2 sentences about how the Quran uses this word across different verses — the unifying theme, or a surprising contrast. Empty string '' for other types.",
  "tidbit_about_semitic": "(Word Origins ONLY) 1-2 sentences zooming out to Semitic-language depth: how the cognates trace the meaning across cultures and millennia. Empty string '' for other types.",
  "selected_verse_refs": "(Word Origins ONLY) Array of EXACTLY two {\"chapter\":N,\"verse\":N,\"why\":\"<short reason\"} objects. MUST be picked from `other_verses` in the payload — do not invent references. Each `why` is a 4-8 word note for the operator. Empty array [] for other types.",
  "verse_intro":   "(non-Word Origins) 1 sentence introducing the verse reference and what it says. Empty for Word Origins.",
  "insight":       "(non-Word Origins) 2-4 sentences delivering the payload. Empty for Word Origins.",
  "close":         "1 sentence reflective close. End on the meaning, not on a doctrinal claim.",
  "voiceover_long":  "Concatenated narration 220-340 words (target ~280; absolute minimum 180), smooth flow, suitable for ElevenLabs TTS. DO NOT include Arabic recitation — the reciter's audio plays separately. For Word Origins, structure the narration as: (1) hook + tidbit_about_root narrated over the source verse on screen, (2) tidbit_about_quran_usage narrated over selected_verse_refs[0], (3) tidbit_about_semitic narrated over selected_verse_refs[1]. The video shows the verses; the narration is the connective tissue.",
  "voiceover_short": "Concatenated narration ≤120 words, suitable for a sub-55-second Short. Same Word Origins structure compressed; one short tidbit per verse on screen. Same exclusion: no Arabic recitation in the narration.",
  "languages_referenced": ["list of language names actually mentioned in voiceover_long, copied exactly from the payload"],
  "notes": "any caveats; empty string if none"
}
"""


class ScriptGenError(Exception):
    """Raised when generation or validation fails."""


# --------------------------------------------------------------------------
#  Voiceover sanitizer — last line of defense before ElevenLabs
# --------------------------------------------------------------------------

# Order matters: longer / digraph keys first so they win over single
# characters. We want "s²" → "sh" before any "s" rule fires.
_VOICEOVER_REPLACEMENTS: list[tuple[str, str]] = [
    # Buckwalter-style superscripts (sin variants)
    ("s¹", "s"),
    ("s²", "sh"),
    # IPA marks for ayin/hamza adjacent to a hyphen → "a" so that
    # hyphenated root spellouts (ʕ-y-n / ʔ-k-l) collapse to a
    # pronounceable English form (ayn / akl) instead of "yn"/"kl".
    # Order: these MUST come before the unconditional drops below.
    ("ʕ-", "a-"), ("ʔ-", "a-"), ("ʿ-", "a-"), ("ʾ-", "a-"),
    # Word-initial IPA followed by a vowel → drop ("ʕayn" → "ayn",
    # "ʔakl" → "akl"). The drop alone is fine because the next char
    # is a vowel that English speakers naturally voice.
    # Word-medial IPA → drop entirely. The vowel before/after carries
    # the sound in English approximation.
    ("ʿ", ""),  # ayin (academic)
    ("ʾ", ""),  # hamza (academic)
    ("ʕ", ""),  # IPA pharyngeal (ayin)
    ("ʔ", ""),  # IPA glottal stop
    ("ʼ", ""), ("ʻ", ""),  # modifier letter apostrophes
    # Single-letter consonants with diacritics → English approximations
    ("ḥ", "h"), ("Ḥ", "H"),
    ("ḫ", "kh"), ("Ḫ", "Kh"),
    ("ṯ", "th"), ("Ṯ", "Th"),
    ("ḏ", "dh"), ("Ḏ", "Dh"),
    ("ṣ", "s"), ("Ṣ", "S"),
    ("ḍ", "d"), ("Ḍ", "D"),
    ("ṭ", "t"), ("Ṭ", "T"),
    ("ẓ", "z"), ("Ẓ", "Z"),
    ("ġ", "gh"), ("Ġ", "Gh"),
    # Long vowels with macron — TTS reads "ā" as a literal a-with-macron
    ("ā", "a"), ("Ā", "A"),
    ("ē", "e"), ("Ē", "E"),
    ("ī", "i"), ("Ī", "I"),
    ("ō", "o"), ("Ō", "O"),
    ("ū", "u"), ("Ū", "U"),
]

# Hyphenated root forms like "ʕ-y-n" or "ḫ-y-n" — once IPA marks are
# stripped or replaced (ʕ→"", ḫ→"kh"), what remains is patterns like
# "-y-n" or "kh-y-n". Match any sequence of 2+ chunks of 1-3 ASCII
# letters separated by single hyphens, optionally with a leading
# orphan hyphen (when the first letter was stripped to empty).
_HYPHEN_LETTER_RE = re.compile(
    r"-?\b(?:[a-z]{1,3}-){1,}[a-z]{1,3}\b",
    re.IGNORECASE,
)
# Strip Arabic-script blocks entirely — voiceover is English only and
# ElevenLabs would either skip them (creating weird pauses) or stumble.
_ARABIC_BLOCK_RE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def sanitize_for_tts(text: str) -> str:
    """Strip academic transliteration / IPA / Arabic script from a
    voiceover string before handing it to ElevenLabs.

    Best-effort: the LLM is told upfront to write TTS-friendly English,
    so this should mostly be a no-op. When it isn't, we'd rather a
    slightly awkward English word than a literal "schwa-yod-nun" reading.
    """
    if not text:
        return text
    out = text
    # 1) Drop inline Arabic script (the reciter's audio carries the Arabic)
    out = _ARABIC_BLOCK_RE.sub("", out)
    # 2) Replace academic marks
    for a, b in _VOICEOVER_REPLACEMENTS:
        if a in out:
            out = out.replace(a, b)
    # 3) Collapse hyphenated letter spellouts ("a-y-n" → "ayn",
    #    "kh-y-n" → "khyn", "-y-n" → "yn"). Without this, ElevenLabs
    #    reads each hyphen as "dash" or as a long pause.
    def _collapse(m):
        return m.group(0).lstrip("-").replace("-", "")
    out = _HYPHEN_LETTER_RE.sub(_collapse, out)
    # 4) Tidy whitespace introduced by stripped Arabic blocks etc.
    #    Real hyphens (al-nuqta, hand-written) are left alone — by
    #    this point all "academic" hyphenated forms have collapsed
    #    via step 3.
    out = _MULTI_SPACE_RE.sub(" ", out).strip()
    return out


# --------------------------------------------------------------------------
#  Payload enrichment — pulls the structured grounding fresh from the DB
# --------------------------------------------------------------------------

# Buckwalter→semiticroots mirror. Keep in sync with educational_pipeline.py.
_BW_TO_SR = {
    "'": "ʔ", ">": "ʔ", "<": "ʔ", "&": "ʔ", "}": "ʔ", "A": "ʔ",
    "b": "b", "t": "t", "v": "ṯ", "j": "g",
    "H": "ḥ", "x": "ḫ", "d": "d", "*": "ḏ",
    "r": "r", "z": "z", "s": "s¹", "$": "s²",
    "S": "ṣ", "D": "ḍ", "T": "ṭ", "Z": "ẓ",
    "E": "ʕ", "g": "ġ", "f": "f", "q": "q",
    "k": "k", "l": "l", "m": "m", "n": "n",
    "h": "h", "w": "w", "y": "y",
}


def _bw_to_sr(bw: str) -> str:
    return "-".join(_BW_TO_SR.get(c, c) for c in bw or "")


def _fetch_verse(conn, chapter: int, verse: int) -> dict:
    out = {"chapter": chapter, "verse": verse}
    v = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    if v:
        out["text_uthmani"] = v["text_uthmani"]
    t = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    if t:
        out["translation"] = t["text_en"]
    return out


def _fetch_word(conn, chapter: int, verse: int, word_pos: int) -> dict | None:
    """Get the surface form + root + lemma for a given word position."""
    row = conn.execute(
        """
        SELECT form_arabic, form_buckwalter,
               root_arabic, root_buckwalter,
               lemma_arabic, lemma_buckwalter, pos
        FROM morphology
        WHERE chapter = ? AND verse = ? AND word_pos = ?
          AND pos NOT IN ('Prefix','Suffix','Pronoun')
        ORDER BY segment ASC LIMIT 1
        """,
        (chapter, verse, word_pos),
    ).fetchone()
    return dict(row) if row else None


def _fetch_other_quran_verses_with_root(
    conn, root_buckwalter: str, *, exclude_chapter: int, exclude_verse: int,
    limit: int = 8,
) -> list[dict]:
    """Find other Quran verses that contain the given Buckwalter root.
    Returns up to `limit` rows: chapter, verse, word_pos (where the
    root sits in that verse), text_uthmani, translation. Used to give
    the LLM a pool of "other verses with this word" to cite — the
    new Word Origins template features 2 of them inline."""
    rows = conn.execute(
        """
        SELECT m.chapter, m.verse, MIN(m.word_pos) AS word_pos,
               v.text_uthmani,
               (SELECT text_en FROM translations t
                WHERE t.chapter = m.chapter AND t.verse = m.verse) AS translation
        FROM morphology m
        JOIN verses v ON v.chapter = m.chapter AND v.verse = m.verse
        WHERE m.root_buckwalter = ?
          AND NOT (m.chapter = ? AND m.verse = ?)
        GROUP BY m.chapter, m.verse
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (root_buckwalter, exclude_chapter, exclude_verse, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_cognate_chain(conn, root_buckwalter: str) -> list[dict]:
    """All derivatives for a root, ordered oldest first."""
    sr = _bw_to_sr(root_buckwalter)
    rows = conn.execute(
        """
        SELECT d.language, d.word, d.meaning, d.concept,
               cl.family AS language_family,
               cl.date_from, cl.date_to
        FROM semitic_roots r
        JOIN semitic_derivatives d ON d.root_id = r.id
        LEFT JOIN cognate_languages cl ON d.language_id = cl.id
        WHERE r.transliteration = ?
          AND d.language IS NOT NULL AND d.language != ''
        ORDER BY cl.date_from ASC, d.language
        """,
        (sr,),
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_v7_insight(conn, chapter: int, verse: int, insight_id: str) -> dict | None:
    """Pull a single V7 insight from verse_grammar_insights.insights_v7_json."""
    row = conn.execute(
        "SELECT insights_v7_json FROM verse_grammar_insights "
        "WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    if not row or not row["insights_v7_json"]:
        return None
    try:
        insights = json.loads(row["insights_v7_json"])
    except Exception:
        return None
    for ins in insights or []:
        if ins.get("id") == insight_id:
            return ins
    return None


def _fetch_departure_note(conn, chapter: int, verse: int) -> str | None:
    row = conn.execute(
        "SELECT departure_notes FROM ai_translations "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY id DESC LIMIT 1",
        (chapter, verse),
    ).fetchone()
    return row["departure_notes"] if row else None


def enrich_payload(conn: sqlite3.Connection, row: dict) -> dict:
    """Build the LLM grounding payload for a candidate row.

    The Phase 1 row stores a small payload at queue time; here we
    re-fetch the canonical data so the LLM sees fresh values even if
    the underlying tables have been edited since the queue moment.
    Returns a dict shaped per type:

      word_origins:
        { type, verse, word, root, derivatives: [...] }
      translation_hides:
        { type, verse, departure_notes }
      grammar_insights:
        { type, verse, insight: {V7 dict} }
    """
    vtype = row["type"]
    chapter = row["chapter"]
    verse = row["verse"]
    base = {"type": vtype, "verse": _fetch_verse(conn, chapter, verse)}

    if vtype == "word_origins":
        word_pos = row.get("anchor_word_pos")
        if word_pos is None:
            raise ScriptGenError("word_origins payload missing word_pos anchor")
        word = _fetch_word(conn, chapter, verse, word_pos)
        if not word:
            raise ScriptGenError(
                f"no morphology row for {chapter}:{verse}/p{word_pos}"
            )
        derivs = _fetch_cognate_chain(conn, word["root_buckwalter"])
        if not derivs:
            raise ScriptGenError(
                f"no cognate derivatives for root {word['root_buckwalter']}"
            )
        base["word"] = word
        base["root"] = {
            "buckwalter": word["root_buckwalter"],
            "arabic": word["root_arabic"],
            "transliteration": _bw_to_sr(word["root_buckwalter"]),
        }
        base["derivatives"] = derivs
        # Other verses in the Quran that use the same root — the LLM
        # picks two of these to feature in the new Word Origins
        # template (one per "tidbit" segment after the source verse).
        base["other_verses"] = _fetch_other_quran_verses_with_root(
            conn, word["root_buckwalter"],
            exclude_chapter=chapter, exclude_verse=verse, limit=8,
        )

    elif vtype == "translation_hides":
        note = _fetch_departure_note(conn, chapter, verse)
        if not note:
            raise ScriptGenError(
                f"no departure note for {chapter}:{verse} in ai_translations"
            )
        base["departure_notes"] = note

    elif vtype == "grammar_insights":
        iid = row.get("anchor_insight_id")
        if not iid:
            raise ScriptGenError("grammar_insights payload missing insight_id anchor")
        insight = _fetch_v7_insight(conn, chapter, verse, iid)
        if not insight:
            raise ScriptGenError(
                f"V7 insight {iid} not found for {chapter}:{verse}"
            )
        base["insight"] = insight
    else:
        raise ScriptGenError(f"unknown type: {vtype}")

    return base


# --------------------------------------------------------------------------
#  Per-type prompt building
# --------------------------------------------------------------------------

def _build_user_prompt(payload: dict) -> str:
    vtype = payload["type"]
    verse = payload["verse"]
    header = (
        f"Verse: Quran {verse['chapter']}:{verse['verse']}\n"
        f"Arabic: {verse.get('text_uthmani', '(unavailable)')}\n"
        f"Conventional translation: {verse.get('translation', '(unavailable)')}\n"
    )

    if vtype == "word_origins":
        word = payload["word"]
        root = payload["root"]
        derivs = payload["derivatives"]
        other_verses = payload.get("other_verses", [])
        # Compact derivative listing — one line each, dates included so
        # the LLM can build a timeline.
        deriv_lines = []
        for d in derivs:
            df = d.get("date_from")
            dt = d.get("date_to")
            era = ""
            if df is not None:
                era = f" [{df}–{dt}]" if dt is not None else f" [{df}+]"
            mn = d.get("meaning") or d.get("concept") or ""
            fam = d.get("language_family") or ""
            line = f"- {d.get('language')}{era}: {d.get('word')} = '{mn}'"
            if fam:
                line += f"  (family: {fam})"
            deriv_lines.append(line)

        # Other Quran verses with the same root. We hand the LLM the
        # full list and ask it to pick the two most thematically
        # interesting ones to feature on screen.
        other_lines = []
        for ov in other_verses:
            tr = (ov.get("translation") or "").strip().replace("\n", " ")
            if len(tr) > 220:
                tr = tr[:217] + "..."
            other_lines.append(
                f"- {ov['chapter']}:{ov['verse']} — {tr}"
            )
        other_block = (
            "\n".join(other_lines)
            if other_lines
            else "(none — root only appears in the source verse)"
        )

        body = (
            "Series: Word Origins. The video shows three Arabic verses on screen "
            "with the target word highlighted; your narration is the connective "
            "tissue that plays over them.\n\n"
            "VIDEO STRUCTURE you are writing for:\n"
            "  Segment 1: Source verse on screen — narration is "
            "    [hook starting with 'Did you know...'] + [tidbit_about_root].\n"
            "  Segment 2: selected_verse_refs[0] on screen — narration is "
            "    [tidbit_about_quran_usage] explaining how the Quran uses this word.\n"
            "  Segment 3: selected_verse_refs[1] on screen — narration is "
            "    [tidbit_about_semitic] connecting the root to its Semitic cognates.\n"
            "  (al-nuqta outro card — not your concern.)\n\n"
            f"{header}\n"
            f"Word in this verse: {word['form_arabic']} ({word['form_buckwalter']})\n"
            f"Root: {root['arabic']} (Buckwalter: {root['buckwalter']}, "
            f"transliteration: {root['transliteration']})\n\n"
            "Cognate derivatives (oldest first — pick 2-4 to weave into "
            "tidbit_about_semitic):\n"
            + "\n".join(deriv_lines)
            + "\n\nOther Quran verses that use this same root — pick TWO for "
            "selected_verse_refs (segments 2 and 3 of the video). Choose verses "
            "whose context contrasts or expands the meaning shown in the source "
            "verse, so each on-screen verse adds something new:\n"
            f"{other_block}"
            + "\n\nGuidance:\n"
            "- The hook MUST start with 'Did you know'.\n"
            "- selected_verse_refs[0] is the verse for tidbit_about_quran_usage.\n"
            "- selected_verse_refs[1] is the verse for tidbit_about_semitic.\n"
            "- selected_verse_refs MUST come from the list above — do not invent.\n"
            "- Languages_referenced must contain ONLY languages from the cognate list.\n"
            "- Leave verse_intro and insight as empty strings ''."
        )

    elif vtype == "translation_hides":
        body = (
            "Series: What Translators Hide. Show the nuance the conventional rendering flattens.\n\n"
            f"{header}\n"
            "Departure note (the nuance our AI translator flagged):\n"
            f"\"\"\"\n{payload['departure_notes']}\n\"\"\"\n\n"
            "Guidance for this script:\n"
            "- Hook on the gap between conventional and nuanced.\n"
            "- Insight section: paraphrase the departure note as your own argument; do not quote it verbatim.\n"
            "- Close on what the nuance unlocks, not on a doctrinal claim.\n"
            "- languages_referenced: [] (this series doesn't cite languages)."
        )

    elif vtype == "grammar_insights":
        ins = payload["insight"]
        claim = ins.get("claim", {})
        cf = ins.get("counterfactual", {})
        payoff = ins.get("meaning_payoff", {})
        evidence = ins.get("evidence_trace", []) or []
        ev_lines = []
        for ev in evidence[:6]:
            ev_lines.append(
                f"- {ev.get('surface_ar', '')} ({ev.get('buckwalter', '')}): "
                f"{ev.get('feature_type', '')}={ev.get('feature_value', '')} "
                f"[{ev.get('role', '')}]"
            )
        cf_block = ""
        if cf.get("present") and cf.get("text"):
            cf_block = f"\nCounterfactual ({cf.get('type','')}): {cf['text']}\n"
        body = (
            f"Series: Grammar Insights. Walk the viewer through one grammatical move.\n\n"
            f"{header}\n"
            f"Insight title: {ins.get('title','')}\n"
            f"Category: {ins.get('category','')}\n"
            f"Claim: {claim.get('observation','')}\n"
            f"Scope: {claim.get('scope','')}, strength: {claim.get('strength','')}"
            f"{cf_block}"
            f"\nMeaning payoff: {payoff.get('text','')}\n\n"
            "Evidence tokens:\n"
            + ("\n".join(ev_lines) if ev_lines else "(none)")
            + "\n\nGuidance for this script:\n"
            "- If a counterfactual is present, build the script around it. "
            "  'It could have said X — but it said Y. Here's what changes.'\n"
            "- Reference at most 1-2 evidence tokens by their Arabic form.\n"
            "- Don't introduce grammatical claims that aren't in the structured insight.\n"
            "- languages_referenced: [] (this series doesn't cite cognates)."
        )
    else:
        raise ScriptGenError(f"unknown type: {vtype}")

    return body


# --------------------------------------------------------------------------
#  LLM call + validation
# --------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Extract a JSON object from a Claude response, tolerating common
    markdown wrappings."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    # Some models leak a leading "json" tag inside the fence.
    if s.lower().startswith("json\n"):
        s = s.split("\n", 1)[-1]
    return json.loads(s)


def _word_count(s: str) -> int:
    return len(re.findall(r"\b\w[\w'-]*\b", s or ""))


# Apostrophes / quote-marks / academic transliteration marks the LLM
# might use interchangeably for the same language. ʿ (U+02BF) and ʾ
# (U+02BE) are the canonical IPA-ish marks for ayin / hamza; the LLM
# also ships curly quotes, modifier letters, plain ASCII, etc.
_LANG_PUNCT_RE = re.compile(r"['‘’ʼʻʿʾ`.\-]", re.UNICODE)
_LANG_WS_RE = re.compile(r"\s+", re.UNICODE)


def _normalize_lang(s: str) -> str:
    """Lowercase, drop apostrophes/dots/hyphens entirely (Ge'ez ≈ Geez ≈ Geʿez),
    then collapse whitespace. Multi-word names stay separated so
    'Modern Hebrew' still substring-matches 'hebrew'."""
    s = (s or "").lower()
    s = _LANG_PUNCT_RE.sub("", s)  # drop, don't replace with space
    s = _LANG_WS_RE.sub(" ", s).strip()
    return s


def _lang_matches(declared: str, allowed_pool: list[str]) -> str | None:
    """Return the canonical (payload) language name that this declared
    language matches, or None if no match. Match logic is bidirectional
    substring: declared∈allowed OR allowed∈declared, on normalized
    strings. Bidirectional because 'Hebrew' ⇄ 'Biblical Hebrew' should
    both succeed; 'Greek' against {'Akkadian','Hebrew',...} should
    fail (no substring overlap with any)."""
    nd = _normalize_lang(declared)
    if not nd:
        return None
    for canon in allowed_pool:
        nc = _normalize_lang(canon)
        if not nc:
            continue
        if nd == nc or nd in nc or nc in nd:
            return canon
    return None


def _validate(script: dict, payload: dict) -> list[str]:
    """Return list of validation errors. Empty = OK."""
    errors: list[str] = []

    # Required fields differ by type. Word Origins now uses the
    # 3-segment template (did_you_know via hook, three tidbits, two
    # selected_verse_refs); the legacy beats verse_intro and insight
    # are not required for it. Other types still use the original
    # 4-beat template.
    if payload.get("type") == "word_origins":
        required = (
            "hook",
            "tidbit_about_root",
            "tidbit_about_quran_usage",
            "tidbit_about_semitic",
            "close",
            "voiceover_long", "voiceover_short",
        )
    else:
        required = (
            "hook", "verse_intro", "insight", "close",
            "voiceover_long", "voiceover_short",
        )
    for k in required:
        v = script.get(k)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"missing or empty: {k}")

    # Word Origins extras: hook framing + selected_verse_refs grounding.
    if payload.get("type") == "word_origins":
        hook = (script.get("hook") or "").strip().lower()
        if hook and not hook.startswith("did you know"):
            errors.append("hook must start with 'Did you know' for Word Origins")

        refs = script.get("selected_verse_refs")
        if not isinstance(refs, list) or len(refs) != 2:
            errors.append("selected_verse_refs must be an array of exactly 2 entries")
        else:
            allowed = {(o["chapter"], o["verse"]) for o in payload.get("other_verses", [])}
            for i, r in enumerate(refs):
                if not isinstance(r, dict):
                    errors.append(f"selected_verse_refs[{i}] is not an object")
                    continue
                try:
                    c = int(r.get("chapter"))
                    v = int(r.get("verse"))
                except (TypeError, ValueError):
                    errors.append(f"selected_verse_refs[{i}] missing chapter/verse")
                    continue
                if (c, v) not in allowed:
                    errors.append(
                        f"selected_verse_refs[{i}] {c}:{v} is not in payload "
                        f"other_verses pool — pick from the candidate list"
                    )

    # Voiceover must be TTS-friendly. Scan for academic/IPA marks
    # and inline Arabic — both will trip ElevenLabs. The sanitizer
    # below cleans them as a safety net, but we'd rather the LLM
    # rewrite the line so the operator sees a clean preview.
    forbidden_re = re.compile(
        r"[ʔʕʾʿʼʻ"  # IPA / modifier letters
        r"á-ſ"                            # Latin extended (macrons etc.)
        r"Ḁ-ỿ"                            # Latin extended additional (dotted)
        r"¹²"                             # superscript 1/2
        r"؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]"  # Arabic
    )
    for fld in ("voiceover_long", "voiceover_short"):
        text = script.get(fld) or ""
        bad = sorted(set(forbidden_re.findall(text)))
        if bad:
            errors.append(
                f"{fld} contains TTS-unfriendly characters: {bad}. "
                f"Rewrite using plain English transliteration."
            )

    # Length budgets. Floor of 180 (~75s narration at 150 wpm) is the
    # minimum that justifies a long-form video over a Short. Ceiling of
    # 380 keeps the long form under ~2:30 to fit YT recommendation
    # patterns. Short form ≤130 leaves room for the ~10s recitation
    # overlay so the rendered Short stays under 60s (someone-else-audio
    # policy).
    long_wc = _word_count(script.get("voiceover_long", ""))
    short_wc = _word_count(script.get("voiceover_short", ""))
    if long_wc < 180 or long_wc > 380:
        errors.append(f"voiceover_long word count {long_wc} outside 180-380")
    if short_wc > 130:
        errors.append(f"voiceover_short word count {short_wc} exceeds 130 (Shorts cap)")

    # Type-specific grounding checks.
    if payload["type"] == "word_origins":
        allowed_pool = [d["language"] for d in payload.get("derivatives", []) if d.get("language")]
        declared = script.get("languages_referenced") or []
        if not isinstance(declared, list):
            declared = []
        unknown = [d for d in declared if not _lang_matches(d, allowed_pool)]
        if unknown:
            errors.append(
                f"declared cognate languages not in payload: {unknown}. "
                f"Allowed pool: {allowed_pool}"
            )

    return errors


def _validation_retry_message(errors: list[str], payload: dict) -> str:
    """Build a follow-up turn that tells the LLM exactly what failed and
    what's allowed, so the second attempt is grounded."""
    msg = (
        "Your previous response failed validation:\n"
        + "\n".join(f"  - {e}" for e in errors)
        + "\n\nFix and respond with the corrected JSON. Keep ALL fields from "
        "the previous response that were valid; only modify what's broken. "
        "Output the FULL JSON object again."
    )
    # Spell out the length budget concretely — the most common retry
    # failure is undershooting the long voiceover.
    msg += (
        "\n\nLength budgets:"
        "\n  - voiceover_long: must be 220-340 words (aim for ~280). "
        "If you're under, expand by adding context to the insight or close — "
        "more concrete examples from the structured payload."
        "\n  - voiceover_short: ≤120 words. Keep it tight."
    )
    # Voiceover TTS rules — repeat them with concrete examples so the
    # second attempt actually fixes them. The first-attempt failure
    # is almost always "the LLM forgot we said no IPA in voiceover".
    msg += (
        "\n\nVoiceover TTS rules (these apply ONLY to voiceover_long and "
        "voiceover_short — the other beats can keep proper transliterations):"
        "\n  - Replace ʕ / ʔ / ʿ / ʾ with English approximation. "
        "'ʕayn' becomes 'ayn'. 'ʔakl' becomes 'akl'. 'aʕyun' becomes 'ayun'."
        "\n  - Replace IPA letters with English digraphs. "
        "'ḥ' → 'h'. 'ḫ' → 'kh'. 'ṯ' → 'th'. 'ḏ' → 'dh'. 'ġ' → 'gh'. "
        "'ṣ' / 'ḍ' / 'ṭ' / 'ẓ' → 's' / 'd' / 't' / 'z'."
        "\n  - Replace long-vowel macrons. 'īnu' becomes 'eenu' or 'inu'. "
        "'ālōm' becomes 'alom'."
        "\n  - Replace s¹ / s² with 's' / 'sh'."
        "\n  - NEVER spell out roots letter-by-letter with hyphens "
        "('ʕ-y-n', 'ḥ-m-d'). Either say it as one word ('ayn', 'hmd') "
        "or describe it ('the three-letter root meaning eye')."
        "\n  - NEVER include Arabic-script characters in voiceover. The "
        "reciter's audio plays the Arabic separately."
    )
    if payload.get("type") == "word_origins":
        langs = sorted({d["language"] for d in payload.get("derivatives", []) if d.get("language")})
        msg += (
            "\n\nThe ONLY languages you may name in voiceover_long, voiceover_short, "
            "or languages_referenced are these — copy the spelling exactly, "
            "including any apostrophes:\n"
            + ", ".join(langs)
        )
        ovs = payload.get("other_verses") or []
        if ovs:
            msg += (
                "\n\nThe ONLY verses you may put in selected_verse_refs are "
                "from this list (chapter:verse, exact integers):\n"
                + ", ".join(f"{o['chapter']}:{o['verse']}" for o in ovs)
            )
    return msg


def _claude_call(
    *,
    api_key: str,
    model: str,
    messages: list[dict],
    timeout: int,
) -> str:
    resp = requests.post(
        CLAUDE_API_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": 1500,
            "temperature": 0.55,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        },
        timeout=timeout,
    )
    if not resp.ok:
        raise ScriptGenError(
            f"Claude API {resp.status_code}: {resp.text[:200]}"
        )
    body = resp.json()
    content = body.get("content") or []
    text_blocks = [b.get("text", "") for b in content if b.get("type") == "text"]
    raw = "\n".join(text_blocks).strip()
    if not raw:
        raise ScriptGenError("empty response from Claude")
    return raw


def generate_script(
    payload: dict,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 90,
) -> dict:
    """Call Claude and return a validated script. One automatic retry
    if validation fails — the failure reasons + allowed pool are fed
    back as a follow-up message. Raises ScriptGenError if both attempts
    fail."""
    if not api_key:
        raise ScriptGenError("Claude API key not configured (admin → settings)")

    user_prompt = _build_user_prompt(payload)
    messages: list[dict] = [{"role": "user", "content": user_prompt}]
    raw = _claude_call(api_key=api_key, model=model, messages=messages, timeout=timeout)

    try:
        script = _extract_json(raw)
    except json.JSONDecodeError as e:
        raise ScriptGenError(f"non-JSON response: {e}\n\n{raw[:300]}")

    errs = _validate(script, payload)
    if errs:
        # One retry — feed the exact failures + allowed pool back so the
        # model can correct without re-reasoning the whole prompt.
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": _validation_retry_message(errs, payload),
        })
        raw2 = _claude_call(api_key=api_key, model=model, messages=messages, timeout=timeout)
        try:
            script = _extract_json(raw2)
        except json.JSONDecodeError as e:
            raise ScriptGenError(
                f"retry returned non-JSON: {e}\n\n{raw2[:300]}"
            )
        errs2 = _validate(script, payload)
        if errs2:
            raise ScriptGenError(
                "validation failed after retry: " + "; ".join(errs2)
                + f"\n\nFirst attempt errors: {'; '.join(errs)}"
            )
        raw = raw2  # the surviving response

    # Sanitize voiceover bodies for TTS consumption. The LLM has been
    # instructed to do this itself, but we apply it as a safety net so
    # ElevenLabs never sees IPA marks or hyphenated root spellouts.
    # Other beats (hook/insight/close) keep their original text — they
    # may surface in on-screen captions where proper transliterations
    # are useful.
    if isinstance(script.get("voiceover_long"), str):
        script["voiceover_long_raw"] = script["voiceover_long"]
        script["voiceover_long"] = sanitize_for_tts(script["voiceover_long"])
    if isinstance(script.get("voiceover_short"), str):
        script["voiceover_short_raw"] = script["voiceover_short"]
        script["voiceover_short"] = sanitize_for_tts(script["voiceover_short"])

    script["raw_response"] = raw
    script["model"] = model
    return script
