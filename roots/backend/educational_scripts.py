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


# Languages a general viewer is reasonably likely to recognize. The
# Word Origins prompt-builder filters the cognate-derivatives list to
# THIS subset before handing it to the LLM, unless filtering leaves
# fewer than 2 entries — in which case the full list is used so we
# don't strand a candidate root with no cognates to discuss.
#
# Languages deliberately EXCLUDED (kept out of viewer-facing scripts):
#   Ugaritic, Eblaite, Amorite, Samalian, Hatran, Punic, Edomite,
#   Moabite, Ammonite, Nabataean, Palmyrene, Maʕlula, Hasaitic,
#   Hismaic, Safaitic, Taymanitic, Thamudic B, Dadanitic, Sabaic,
#   Minaic, Qatabanic, Ḥaḍramitic, Epigraphic South Arabian,
#   Amharic, Tigre, Tigrinya, Argobba, Gafat, Gurage, Harari,
#   Wolane, East Ethiopic, Ge'ez, Mandaic, Mandaic Aramaic,
#   Harsusi, Jibbali, Mehri, Shehri, Soqotri, Maltese, Deir Alla.
#
# Add to this set if a future series reaches a viewer audience for
# whom one of those is recognizable (e.g. Maltese for European
# viewers, Ge'ez for Ethiopian-Orthodox viewers).
VIEWER_FRIENDLY_LANGUAGES: frozenset[str] = frozenset({
    "Akkadian",
    "Hebrew", "Biblical Hebrew", "Modern Hebrew",
    "Aramaic", "Biblical Aramaic", "Old Aramaic", "Modern Aramaic",
    "Judaic Aramaic", "Syrian Aramaic",
    "Syriac",
    "Phoenician",
    "Canaanite",
    "Arabic", "Modern Arabic",
})

# Minimum cognate count after viewer-friendly filtering before we'd
# rather show the unfiltered list than starve the script.
_MIN_FILTERED_DERIVS = 2


def _viewer_friendly_derivatives(derivatives: list[dict]) -> tuple[list[dict], bool]:
    """Apply the VIEWER_FRIENDLY_LANGUAGES filter, falling back to the
    full list if it would leave fewer than _MIN_FILTERED_DERIVS entries.
    Returns (filtered_or_full_list, was_filtered_flag)."""
    friendly = [
        d for d in derivatives
        if d.get("language") in VIEWER_FRIENDLY_LANGUAGES
    ]
    if len(friendly) >= _MIN_FILTERED_DERIVS:
        return friendly, len(friendly) < len(derivatives)
    return derivatives, False


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

QURAN-ONLY GROUNDING (CRITICAL — applies to every script):
- Every interpretive claim must be grounded in the Quran's own text or
  in linguistic/grammatical facts about the Arabic. Nothing else is
  in scope.
- DO NOT cite hadith, sunnah, sira, tafsir, classical commentators,
  or any post-Quranic Islamic tradition. Even paraphrased.
- DO NOT use post-Quranic religious vocabulary in the script:
    forbidden sources/concepts: hadith, sunnah, sira, ummah, sharia,
               halal, haram, ijma, fiqh, madhhab, sahaba, "the prophet
               said", "Muslims believe", "in Islamic tradition",
               "scholars hold", "classical commentators", "according
               to the sunnah", "the four schools".
    forbidden practice vocabulary: "congregational prayer/s",
               "ritual prayer/s", "ritual ablution", "the five
               pillars", "pillars of Islam", "five daily prayers",
               "the daily prayers". These are tradition-systematized
               concepts. The Quran tells you to "establish prayer"
               and "stand in prayer" and describes washing for prayer
               — describe what the verse says, not the later
               systematized practice. For 1:5's "we serve" / "we seek
               help", say "we worship together" or "the speaker
               stands with others before God", NOT "this verse refers
               to congregational prayer".
  Find Quran-only phrasing instead — e.g. "the verse says",
  "elsewhere in the Quran", "in this text", "the chosen Arabic
  form", "the speaker", "those who do X".
- "Stand within the community of believers", "the community of
  followers", and similar phrases lean on the post-Quranic Ummah
  concept and are out of scope. Stick to what the verse itself
  actually says.
- When meaning needs cross-reference, cross-reference OTHER VERSES
  in the Quran (the payload provides them) — never external sources.
- The Quran is presented as a self-contained text speaking on its
  own terms. We illuminate it with Arabic linguistics and intra-
  Quranic comparison, never with later interpretive layers.

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
  "tidbit_about_root": "(Word Origins ONLY) 45-65 words, 2-3 sentences with ONE striking fact about the root's meaning, history, or oldest attestation. Empty string '' for other types.",
  "tidbit_about_quran_usage": "(Word Origins ONLY) 55-75 words, 2-3 sentences on how the Quran uses this word across 1-2 specific verses (quote ≤6 words from each) — the unifying theme or surprising contrast. Empty string '' for other types.",
  "tidbit_about_semitic": "(Word Origins ONLY) 45-60 words, AT MOST 3 SENTENCES. Pick 1-2 most striking cognates — NOT a 4-language inventory. End on a concrete image, not a recap of the root beat. Empty string '' for other types.",
  "selected_verse_refs": "(Word Origins ONLY) Array of EXACTLY two {\"chapter\":N,\"verse\":N,\"why\":\"<short reason\"} objects. MUST be picked from `other_verses` in the payload — do not invent references. Each `why` is a 4-8 word note for the operator. Empty array [] for other types.",
  "verse_intro":   "(non-Word Origins) 1 sentence introducing the verse reference and what it says. Empty for Word Origins.",
  "insight":       "(non-Word Origins) Up to 65 words, AT MOST 3 sentences. Deliver the payload then STOP. Forbidden: 'First/Second' enumeration, restating the same move with different verbs, meta-commentary like 'the grammar quietly assigns roles'. Empty for Word Origins.",
  "close":         "1 sentence reflective close. End on the meaning, not on a doctrinal claim.",
  "english_emphases": "(Grammar Insights AND Translation Hides) Array of 1-4 short phrases pulled VERBATIM from the verse's English translation that you want highlighted on the verse card. For Grammar Insights, pick phrases that carry the grammatical move you're explaining. For Translation Hides, pick the phrases the viewer should LOOK AT while you reveal the hidden nuance (typically the conventionally-translated phrase whose meaning you're refining). Each phrase MUST appear character-for-character in the translation, and the phrases MUST NOT overlap each other in the translation (no phrase's text can sit inside another phrase's span). The renderer highlights every occurrence of each disjoint phrase. Empty array [] for Word Origins.",
  "selected_word_pos": "(Translation Hides ONLY) Integer 1-based position of the primary 'lens' word in the verse's Arabic text (split on whitespace), if a single word carries the hidden nuance. The renderer uses this to drive the Word Lens slide (conventional gloss vs AI gloss side-by-side) and to highlight the matching Arabic word on the verse-flow slide. Set to null or 0 if the nuance is phrase-level or purely grammatical and no single word is the focus. For all other types, set to null.",
  "reveal_conventional": "(Translation Hides ONLY) ≤80 chars. The conventional rendering as a SHORT noun phrase or quotation — what most viewers think the verse says. Renders as the top muted row of the opening reveal slide. Examples: \"a beautiful patience\" / \"those who believe and do good deeds\" / \"His Lord, in mercy\". Keep it tight; this is a glance-read, not a sentence. Empty string '' for other types.",
  "reveal_hidden": "(Translation Hides ONLY) ≤80 chars. The actual nuance the conventional rendering flattens, as a SHORT contrasting phrase. Renders as the bottom saturated rose row. Examples: \"patience that is beautiful by being\" / \"those who believed and built\" / \"His Lord, whose mercy IS Him\". Must contrast meaningfully with reveal_conventional — same topic, different angle. Keep it tight; one phrase, not a sentence. Empty string '' for other types.",
  "evidence_chip": "(Translation Hides ONLY, optional) ≤60 chars. One-line provenance label rendered as a small pill below the AI gloss on the Word Lens slide. Names WHY the AI gloss is preferred. Use one of these forms: \"morphology: <thing>\" / \"lexical: <thing>\" / \"context: <thing>\" / \"cognate: <thing>\". Examples: \"morphology: passive voice, agent omitted\" / \"lexical: root sense across Semitic\" / \"context: contrasts 2:155 usage\". Empty string '' if you can't name a specific evidence kind, or for other types.",
  "additional_examples": "(Grammar Insights ONLY) Array of 0-2 cross-reference verses that show the same grammatical move elsewhere in the Quran. STRONG DEFAULT IS 1 entry. Pick a second ONLY if leaving it out would noticeably weaken the argument — i.e. the second verse demonstrates something the first doesn't (different rhetorical register, different scope, surprising context). If the second example would just re-prove what the first already proved, leave it out. Each entry: {\"chapter\": N, \"verse\": N, \"narration\": \"...\", \"english_emphases\": [...]}. Picks MUST come from `additional_example_candidates` in the payload — do not invent references. Narration is SHORT (≤55 words, ≈12-15s of voiceover): open with 'In another verse,' or 'Elsewhere,'; quote ≤8 words from the example translation; one sentence on how the pattern shows up here. Do NOT re-explain the grammatical concept — the viewer already heard it on the main verse. english_emphases follows the top-level rules but matches THIS example's translation. Empty array [] when no candidate fits.",
  "voiceover_long":  "Concatenated narration 220-340 words (target ~280; absolute minimum 180), smooth flow, suitable for ElevenLabs TTS. DO NOT include Arabic recitation — the reciter's audio plays separately. For Word Origins, structure the narration as: (1) hook + tidbit_about_root narrated over the source verse on screen, (2) tidbit_about_quran_usage narrated over selected_verse_refs[0], (3) tidbit_about_semitic narrated over selected_verse_refs[1]. The video shows the verses; the narration is the connective tissue.",
  "voiceover_short": "Concatenated narration up to 200 words (target 140-180), suitable for a punchy short-form video that may run a bit over a minute. Same Word Origins structure compressed; one short tidbit per verse on screen. Same exclusion: no Arabic recitation in the narration.",
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


# TTS pronunciation overrides. ElevenLabs eleven_multilingual_v2
# mis-stresses certain English words common in our scripts —
# "Akkadian" tends to come out with a German-style /a/ rather than
# the standard English /əˈkeɪdiən/ (uh-KAY-dee-un). Respelling the
# word the way English phonotactics expect coaxes the right phonemes
# out without needing SSML markup the model doesn't always honor.
#
# Add to this map as the operator catches more mispronunciations.
# Keys/values are case-paired so capital-cased and lowercase forms
# both get covered. Substitution runs only over voiceover_* fields,
# never over the on-screen beat texts (which keep proper spelling).
_TTS_PRONUNCIATION_MAP: dict[str, str] = {
    "Akkadian": "Akaydian",
    "akkadian": "akaydian",
    "AKKADIAN": "AKAYDIAN",
    "Akkadians": "Akaydians",
    "akkadians": "akaydians",
}
_TTS_PRONUNCIATION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _TTS_PRONUNCIATION_MAP) + r")\b",
)


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
    # 5) Apply pronunciation respellings ("Akkadian" → "Akaydian"
    #    etc.) so ElevenLabs lands on the right English phonemes.
    out = _TTS_PRONUNCIATION_RE.sub(
        lambda m: _TTS_PRONUNCIATION_MAP[m.group(1)], out,
    )
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
    """Pull Arabic + English for a verse, prioritising the same source
    the renderer uses (ai_translations, most recent run, prefer
    revised_text). Falls back to the conventional `translations` row
    when no AI translation is available.

    Critical for grammar_insights: the LLM picks `english_emphases`
    phrases from this string and the renderer matches them in the
    rendered translation. Sourcing them from the same place guarantees
    every emphasis is a real substring on the slide."""
    out = {"chapter": chapter, "verse": verse}
    v = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    if v:
        out["text_uthmani"] = v["text_uthmani"]

    translation = ""
    ai_row = conn.execute(
        "SELECT revised_text, translation_text FROM ai_translations "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY id DESC LIMIT 1",
        (chapter, verse),
    ).fetchone()
    if ai_row:
        translation = (ai_row["revised_text"] or ai_row["translation_text"] or "").strip()
    if not translation:
        t = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ? LIMIT 1",
            (chapter, verse),
        ).fetchone()
        if t and t["text_en"]:
            translation = t["text_en"].strip()
    if translation:
        out["translation"] = translation
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


def _find_grammar_example_candidates(
    conn, insight: dict, *, exclude_chapter: int, exclude_verse: int,
    limit: int = 8,
) -> list[dict]:
    """Pool of OTHER verses that contain the same grammatical lemma(s)
    as the anchor insight — used as candidate cross-references for the
    "In another verse... / Elsewhere..." beats in grammar_insights
    videos. The script writer gets to pick 0-2 from this pool.

    Strategy: for each evidence entry, derive a lemma. Two paths:
      1. Direct — feature_type=lemma_bw gives us the lemma already.
      2. Indirect — for evidence pointing at a position via
         feature_type=feature/form_bw/root_bw or surface_ar, we
         resolve to a word_pos in the anchor verse and pull THAT
         word's lemma from morphology. This catches cases like
         80:5's exception/conditional particles where V7's
         evidence carries only the POS tag, not a lemma.
    Then find verses (excluding the anchor) where any segment
    carries one of those lemmas. Translation comes from
    ai_translations (latest run) with conventional fallback.

    Returns dicts with chapter, verse, word_pos (where the matching
    lemma sits), text_uthmani, translation. Empty list when no
    lemma is derivable.
    """
    lemmas: set[str] = set()

    # Path 1: direct lemma_bw evidence
    for ev in insight.get("evidence_trace") or []:
        if ev.get("feature_type") == "lemma_bw":
            v = (ev.get("feature_value") or "").strip()
            if v:
                lemmas.add(v)

    # Path 2: resolve evidence to a position in the anchor verse,
    # then pull the lemma from morphology. Needed for evidence
    # types that only carry a POS tag or a feature like COND/PERF.
    if not lemmas:
        try:
            from educational_render_remotion import _resolve_evidence_position
            for ev in insight.get("evidence_trace") or []:
                pos = _resolve_evidence_position(conn, exclude_chapter, exclude_verse, ev)
                if pos is None:
                    continue
                row = conn.execute(
                    "SELECT lemma_buckwalter FROM morphology "
                    "WHERE chapter=? AND verse=? AND word_pos=? "
                    "  AND lemma_buckwalter IS NOT NULL "
                    "  AND lemma_buckwalter != '' "
                    "ORDER BY segment LIMIT 1",
                    (exclude_chapter, exclude_verse, pos),
                ).fetchone()
                if row and row["lemma_buckwalter"]:
                    lemmas.add(row["lemma_buckwalter"])
        except Exception:
            pass

    if not lemmas:
        return []

    placeholders = ",".join("?" * len(lemmas))
    rows = conn.execute(
        f"""
        SELECT m.chapter, m.verse, MIN(m.word_pos) AS word_pos
        FROM morphology m
        WHERE m.lemma_buckwalter IN ({placeholders})
          AND NOT (m.chapter = ? AND m.verse = ?)
        GROUP BY m.chapter, m.verse
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (*lemmas, exclude_chapter, exclude_verse, limit * 3),
    ).fetchall()

    out: list[dict] = []
    for r in rows:
        verse_data = _fetch_verse(conn, r["chapter"], r["verse"])
        if not verse_data:
            continue
        translation = (verse_data.get("translation") or "").strip()
        text = (verse_data.get("text_uthmani") or "").strip()
        if not translation or not text:
            continue
        # Skip very long verses (>240 chars) so candidate slides
        # don't blow the layout. Exclude bismillah (1:1) which is
        # a fixed phrase, not a useful grammar exemplar.
        if len(text) > 240:
            continue
        if r["chapter"] == 1 and r["verse"] == 1:
            continue
        out.append({
            "chapter": r["chapter"],
            "verse": r["verse"],
            "word_pos": r["word_pos"],
            "text_uthmani": text,
            "translation": translation,
        })
        if len(out) >= limit:
            break
    return out


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
    """Pull a single V7 insight from verse_grammar_insights.insights_v7_json.

    Multiple rows can exist per (chapter, verse) — one per
    grammar_insight_configs entry. Older configs may have
    insights_v7_json = NULL; pick the newest non-null row that contains
    the requested insight id. (The candidate sampler upstream only
    yields ids from non-null rows, but a queued row may be re-fetched
    after the underlying configs change, so the search is robust.)"""
    rows = conn.execute(
        "SELECT insights_v7_json FROM verse_grammar_insights "
        "WHERE chapter = ? AND verse = ? "
        "  AND insights_v7_json IS NOT NULL AND insights_v7_json != '' "
        "ORDER BY id DESC",
        (chapter, verse),
    ).fetchall()
    for row in rows:
        try:
            insights = json.loads(row["insights_v7_json"])
        except Exception:
            continue
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


def _fetch_translation_hides_word_lens(conn, chapter: int, verse: int) -> list[dict]:
    """Per-word AI-preferred meanings for the 'translation hides' lens.

    Returns the words on this verse where the AI judge picked the AI's
    meaning over the conventional gloss (preferred_source = 'ai' or 'judge'),
    sorted by word position. Each entry carries enough context for the
    script writer to decide which word(s) to spotlight in the video:
      - conventional gloss (from word_glosses or morphology surface)
      - AI short meaning
      - AI detailed explanation (the prose paragraph)
      - the Arabic form

    Returns [] when no per-word AI meanings exist for the verse, or when
    every word's preferred translation matches the conventional one
    (i.e. nothing is being hidden at the word level).
    """
    rows = conn.execute(
        """
        SELECT awm.word_pos,
               awm.meaning_short,
               awm.meaning_detailed,
               awm.preferred_translation,
               awm.preferred_source,
               wg.translation_en AS conv_gloss
        FROM ai_word_meanings awm
        LEFT JOIN word_glosses wg
          ON wg.chapter = awm.chapter AND wg.verse = awm.verse
         AND wg.word_pos = awm.word_pos
        WHERE awm.chapter = ? AND awm.verse = ?
          AND awm.preferred_source IN ('ai', 'judge')
          AND TRIM(COALESCE(awm.meaning_short, '')) != ''
        ORDER BY awm.word_pos
        """,
        (chapter, verse),
    ).fetchall()

    out: list[dict] = []
    for r in rows:
        # Fetch the Arabic surface form for this word position. The
        # morphology table has one row per (chapter, verse, word_pos,
        # segment) — concatenate segments to get the visible word.
        seg_rows = conn.execute(
            "SELECT form_arabic FROM morphology "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? "
            "ORDER BY segment",
            (chapter, verse, r["word_pos"]),
        ).fetchall()
        arabic = "".join((s["form_arabic"] or "") for s in seg_rows)

        conv = (r["conv_gloss"] or "").strip()
        ai_short = (r["meaning_short"] or "").strip()
        # Skip words where the AI gloss is essentially identical to the
        # conventional one — nothing is hidden there, just confirmed.
        if conv and ai_short and conv.lower() == ai_short.lower():
            continue
        out.append({
            "word_pos": int(r["word_pos"]),
            "arabic": arabic,
            "conventional_gloss": conv,
            "ai_meaning_short": ai_short,
            "ai_meaning_detailed": (r["meaning_detailed"] or "").strip(),
            "preferred_source": r["preferred_source"],
        })
    return out


def _fetch_translation_hides_grammar_insight(conn, chapter: int, verse: int) -> dict | None:
    """Best V7 grammar insight on this verse, if one exists and is
    high-quality enough to corroborate the translation-hides reveal.

    Looks for an eligible insight from the most recent v7-unified
    config; returns None if no such row, no V7 JSON, or no eligible
    insights with confidence ≥ 0.7. Optional context — the script
    works without it; presence just sharpens the prompt.
    """
    row = conn.execute(
        """
        SELECT gi.insights_v7_json
        FROM verse_grammar_insights gi
        JOIN grammar_insight_configs c ON gi.config_id = c.id
        WHERE gi.chapter = ? AND gi.verse = ?
          AND c.config_name = 'grammar-insights-quran-only-v7-unified'
          AND gi.insights_v7_json IS NOT NULL
          AND gi.insights_v7_json != ''
        ORDER BY gi.created_at DESC
        LIMIT 1
        """,
        (chapter, verse),
    ).fetchone()
    if not row:
        return None
    try:
        insights = json.loads(row["insights_v7_json"]) or []
    except Exception:
        return None
    # Pick the highest-confidence eligible insight.
    best = None
    best_conf = -1.0
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        if not (ins.get("display") or {}).get("eligible"):
            continue
        conf = float((ins.get("quality") or {}).get("overall_confidence") or 0.0)
        if conf >= 0.7 and conf > best_conf:
            best, best_conf = ins, conf
    return best


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
        # Over-fetch (24) so the safety filter has room to drop
        # controversial verses without starving the prompt.
        candidates = _fetch_other_quran_verses_with_root(
            conn, word["root_buckwalter"],
            exclude_chapter=chapter, exclude_verse=verse, limit=24,
        )
        # Filter through the safety cache — controversial verses are
        # dropped so the LLM physically cannot pick one. Permissive on
        # Ollama failure (returns the verse as safe) so the pipeline
        # doesn't deadlock when the moderation server is unreachable.
        try:
            import educational_safety as _safety
            safe_pairs = set(
                _safety.bulk_filter_safe(
                    conn, [(c["chapter"], c["verse"]) for c in candidates],
                )
            )
            filtered = [c for c in candidates if (c["chapter"], c["verse"]) in safe_pairs]
        except Exception as e:
            print(f"[script-gen] safety filter failed, accepting all: {e}")
            filtered = candidates
        # Cap at the original pool size (8) so the prompt doesn't
        # bloat. If the safety filter cut us below 2, fall back to
        # the unfiltered pool — better an occasional miss than no
        # script.
        if len(filtered) < 2:
            filtered = candidates
        base["other_verses"] = filtered[:8]

    elif vtype == "translation_hides":
        note = _fetch_departure_note(conn, chapter, verse)
        if not note:
            raise ScriptGenError(
                f"no departure note for {chapter}:{verse} in ai_translations"
            )
        base["departure_notes"] = note
        # Optional corroborating signals — per-word AI-preferred meanings
        # (which word actually carries the hidden nuance?) and the V7
        # grammar insight on the verse (if any). Both are non-fatal:
        # the script still generates without them, the prompt is just
        # less sharp.
        word_lens = _fetch_translation_hides_word_lens(conn, chapter, verse)
        if word_lens:
            base["word_lens"] = word_lens
        gi = _fetch_translation_hides_grammar_insight(conn, chapter, verse)
        if gi:
            base["grammar_insight"] = gi

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
        # Translation note (verse-level departure note from
        # ai_translations) is corroborating context — if it exists, the
        # LLM gets to see "this is also why translators historically
        # render this verse as X". Optional — most verses don't have
        # one and the script still works.
        note = _fetch_departure_note(conn, chapter, verse)
        if note:
            base["translation_note"] = note
        # Cross-reference example pool — other verses where the same
        # grammatical lemma appears, so the script writer can pick 0-2
        # to feature as "In another verse... / Elsewhere..." beats
        # between the verse_intro and insight slides. Drives the point
        # home by showing the pattern is a real Quranic device, not a
        # one-off.
        base["additional_example_candidates"] = _find_grammar_example_candidates(
            conn, insight, exclude_chapter=chapter, exclude_verse=verse, limit=8,
        )
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
        derivs_all = payload["derivatives"]
        other_verses = payload.get("other_verses", [])
        # Filter cognates to the viewer-friendly allowlist. If the
        # filter leaves too few entries to build a video around, fall
        # back to the unfiltered list so we don't starve the LLM.
        derivs, is_filtered = _viewer_friendly_derivatives(derivs_all)
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
            + ("\n\n(This list has been pre-filtered to the languages most "
               "viewers will recognize. Don't ask for others.)" if is_filtered else "")
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
            "- Leave verse_intro and insight as empty strings ''.\n"
            "\n"
            "TIDBIT WORD BUDGETS — keep each beat punchy. Operator feedback "
            "from published Word Origins shorts: the videos start strong but "
            "the last narrated beat (tidbit_about_semitic) tends to drag, "
            "and viewers swipe.\n"
            "- tidbit_about_root:        45-65 words. One striking fact.\n"
            "- tidbit_about_quran_usage: 55-75 words. The unifying thread\n"
            "  across 1-2 specific verses. Quote ≤6 words from each.\n"
            "- tidbit_about_semitic:     45-60 WORDS, AT MOST 3 SENTENCES.\n"
            "  This is the beat that loses steam most often. Tighten it.\n"
            "\n"
            "TIDBIT_ABOUT_SEMITIC — what to AVOID:\n"
            "- Cognate inventory: 'Hebrew X, Phoenician Y, Aramaic Z, Syriac W,\n"
            "  Akkadian V — all mean the same thing.' Four+ cognate names in\n"
            "  a row reads as a list-of-languages, not a story. Pick the ONE\n"
            "  or TWO most striking cognates (oldest + most surprising) and\n"
            "  drop the rest. Languages_referenced can still list all of them\n"
            "  for the on-screen chip; the narration names the highlight.\n"
            "- Repeating the thread already in tidbit_about_root. If the root\n"
            "  beat already said 'qaf-waw-mim means to stand,' the semitic\n"
            "  beat should ADD something — a surprising domain shift, a\n"
            "  metaphorical extension, an older-than-expected attestation —\n"
            "  not loop back to 'all these languages mean to stand.'\n"
            "- Tacked-on summary clauses: 'Across millennia, the meaning\n"
            "  endured / the thread held / a single idea traveled.' One such\n"
            "  closing image is fine; chaining two is filler.\n"
            "\n"
            "VERBOSE (82w, v56 published — cognate inventory + restatement):\n"
            "  \"Across the Semitic family, the root keeps that vertical core.\n"
            "   Hebrew qum, Phoenician qm, Syriac qam — all mean to rise, to\n"
            "   stand, to establish. The Aramaic forms carry the same sense.\n"
            "   What began as a word for the body's posture became a word for\n"
            "   moral posture: to stand firm, to keep standing, to establish\n"
            "   something that endures. The Quran inherits that full range —\n"
            "   physical, moral, communal — and uses it to describe the act\n"
            "   of holding yourself upright before God.\"\n"
            "TIGHT REWRITE (~50w, same arc, one image):\n"
            "  \"The root traveled. In Akkadian clay tablets, 4500 years ago,\n"
            "   it described hair standing on end — the body going vertical\n"
            "   under shock. Hebrew and Aramaic kept the same core: to rise,\n"
            "   to stand firm. The Quran's 'standing' inherits that whole\n"
            "   physical reflex, then turns it moral.\"\n"
            "Notice: the tight version names ONE Akkadian image (hair on\n"
            "end), groups Hebrew + Aramaic into one phrase, and lands on the\n"
            "physical → moral pivot. The verbose version names four\n"
            "languages, restates 'to rise / to stand' three times, and ends\n"
            "with a recap of the root beat."
        )

    elif vtype == "translation_hides":
        # Optional rich context: the per-word AI meanings flag which
        # specific word(s) carry the hidden nuance, and the V7 grammar
        # insight (if any) names the grammatical move that creates it.
        # When either is present, the LLM gets a much sharper picture
        # of WHAT the translation actually hides, instead of having to
        # infer it from prose alone.
        word_lens_block = ""
        wl = payload.get("word_lens") or []
        if wl:
            lines = []
            for w in wl[:6]:
                pos = w.get("word_pos")
                ar = w.get("arabic") or ""
                conv = (w.get("conventional_gloss") or "").strip()
                ai = (w.get("ai_meaning_short") or "").strip()
                detail = (w.get("ai_meaning_detailed") or "").strip()
                lines.append(
                    f"- word {pos} ({ar}): conventional='{conv}' → AI='{ai}'"
                    + (f"\n    detail: {detail[:240]}" if detail else "")
                )
            word_lens_block = (
                "\nPer-word AI-preferred meanings (the most likely 'lens' words for this video):\n"
                + "\n".join(lines)
                + "\n"
            )

        grammar_block = ""
        gi = payload.get("grammar_insight") or {}
        if gi:
            claim = (gi.get("claim", {}) or {}).get("observation") or gi.get("insight") or ""
            payoff = (gi.get("meaning_payoff", {}) or {}).get("text") or ""
            if claim or payoff:
                grammar_block = (
                    "\nGrammar move at play (V7 insight on this verse):\n"
                    f"- observation: {(claim or '').strip()[:400]}\n"
                    f"- payoff: {(payoff or '').strip()[:400]}\n"
                )

        body = (
            "Series: What Translation Hides. Reveal a meaningful nuance that the conventional English translation flattens — what only the underlying Arabic, word usage, or grammar makes visible.\n\n"
            f"{header}\n"
            "Departure note (the nuance our AI translator flagged):\n"
            f"\"\"\"\n{payload['departure_notes']}\n\"\"\"\n"
            f"{word_lens_block}{grammar_block}\n"
            "VIDEO STRUCTURE you are writing for (4 narration beats, ~55s total):\n"
            "  hook        (~8s, ≤22 words): A YouTube-style thumb-stop opener. LEAD WITH CONTEXT, then tease the twist. The viewer has zero background; they need to know WHICH verse and WHAT the conventional reading is BEFORE they care what's hidden. DO NOT deliver the contrast yet (the slide will land it visually a few seconds later); just establish enough that the curiosity is grounded, not floating.\n"
            "                Pick one of these registers and write naturally — these are SHAPES not templates:\n"
            "                • PREFERRED — investigative invitation. Name a familiar phrasing the audience MIGHT have heard, soften the contrast with hedge language ('appears to', 'seems to be', 'might be'), then INVITE the viewer to look together. E.g. 'You MIGHT have heard this verse translated as guarded her chastity — but the Arabic appears to be doing something far more physical. Let’s take a closer look.' / 'You might have come across Quran 25:58 translated as aware of his sins. The Arabic seems to be saying something stranger. Let’s look.' Use 'you might have heard / you might have come across' instead of the absolute 'you’ve heard' — many viewers haven’t actually seen that exact translation, and the absolute form alienates them from the hook. This register reads as curious co-investigation rather than correction, which is the tone the channel wants.\n"
            "                • Name the verse + quote the familiar reading, then plant a doubt. E.g. 'Quran 25:58 says God is aware of His servants’ sins — but the Arabic literally says aware of their tails.' / 'Quran 33:5 commands: call them to their fathers. The verb isn’t about names at all.'\n"
            "                • Pose a sharp factual question grounded in a specific Arabic word the viewer's translation almost certainly handles a particular way. E.g. 'Why does the Quran’s word for sin literally come from the word for tail?' (Use this only when the bare question itself names enough context to ground the viewer.)\n"
            "             FORBIDDEN OPENERS:\n"
            "                • 'What if this verse isn’t about X, but about Y?' — too abstract, no anchor; nobody was already thinking about X. Operator feedback on 33:5: 'completely without context, you immediately lose the audience.'\n"
            "                • 'Most translations say X but the Arabic says Y' — that’s the slide’s job, not the hook’s.\n"
            "                • 'Most translations miss this' or any variant that calls translators wrong/dishonest — comes off as dismissive.\n"
            "                • 'You’ve heard X' / 'You know X' — assumptive. Plenty of viewers haven’t encountered X specifically; the absolute form pushes them away from the hook. Use 'You might have heard X' / 'You might have come across X' instead — the hedged version stays inclusive without losing the curiosity.\n"
            "             Keep the hook tight, verse-specific, and grounded in the actual conventional English the viewer has likely seen. Not preachy.\n"
            "  verse_intro (~12s, 2-3 sentences): Now NAME the verse (Surah + number) and read the conventional translation, with a beat on the specific word or phrase the reveal is about. This is the moment the slide changes from hook to the Arabic word in big type — describe the word you're showing if there is one. Sets the baseline the viewer thinks they know.\n"
            "  insight     (~25s, 3-4 sentences): The reveal. Paraphrase the departure note (NEVER quote it verbatim) as if you're explaining it to a smart non-specialist. If a single word is the lens, name it, give its conventional vs AI gloss, then explain what that swap unlocks. If grammar is the lens, name the move and what it does. Be concrete — point at the Arabic, the morphology, or the cross-reference, not at vague 'depth.'\n"
            "  close       (~5s, 1 sentence): What the verse actually conveys when you read it this way. End on the meaning, NOT a doctrinal claim.\n\n"
            "Required output fields:\n"
            "- reveal_conventional: ≤80 chars. The conventional rendering as a short noun phrase / glance-read quotation. Top row of the opening slide.\n"
            "- reveal_hidden: ≤80 chars. The actual nuance as a short contrasting phrase. Bottom row of the opening slide. MUST contrast meaningfully with reveal_conventional — same topic, different angle. Don't repeat reveal_conventional.\n"
            "- selected_word_pos: integer 1-based position of the primary 'lens' word in the verse's Arabic (split on whitespace), if a single word carries the nuance. If the nuance is phrase-level or purely grammatical, set to null/0.\n"
            "- evidence_chip (optional, ≤60 chars): ONE phrase naming WHY the AI gloss is preferred. Format: \"morphology: …\", \"lexical: …\", \"context: …\", or \"cognate: …\". Empty string '' if you can't name a clear evidence kind.\n"
            "- english_emphases: 1-3 short phrases from the conventional translation that you want highlighted on the verse slide (the words the viewer should look at while you talk). Each MUST appear verbatim. Non-overlapping.\n\n"
            "Guidance:\n"
            "- Be confident, not academic. The viewer is curious, not a scholar.\n"
            "- No tafsir, no hadith, no schools-of-thought references — only what's grounded in the verse's morphology, lexical evidence, or cross-references in the Quran itself.\n"
            "- voiceover_long is the concatenated narration (hook + verse_intro + insight + close), 220-340 words.\n"
            "- voiceover_short is the same compressed to ≤200 words for the 55-65s short.\n"
            "- languages_referenced: [] (this series doesn't cite languages).\n"
            "- selected_verse_refs: [] (this series doesn't cross-reference other verses on screen).\n"
            "- additional_examples: [] (Grammar Insights only)."
        )

    elif vtype == "grammar_insights":
        ins = payload["insight"]
        claim = ins.get("claim", {})
        cf = ins.get("counterfactual", {})
        payoff = ins.get("meaning_payoff", {})
        evidence = ins.get("evidence_trace", []) or []
        translation_note = payload.get("translation_note") or ""

        ev_lines = []
        for ev in evidence[:6]:
            ev_lines.append(
                f"- {ev.get('surface_ar', '')} ({ev.get('buckwalter', '')}): "
                f"{ev.get('feature_type', '')}={ev.get('feature_value', '')} "
                f"[{ev.get('role', '')}]"
            )

        # Candidate pool for the cross-reference example slides.
        # Pick 0-2 of these for `additional_examples`. Picking 1 is
        # the sweet spot for short videos; pick 2 only when the
        # second adds something the first doesn't (e.g. shows the
        # pattern in a very different rhetorical register).
        examples = payload.get("additional_example_candidates") or []
        example_block = ""
        if examples:
            example_lines = ["\nAdditional-example candidates (pick 0-2 for `additional_examples`):"]
            for ex in examples:
                tr = (ex.get("translation") or "").strip().replace("\n", " ")
                if len(tr) > 200:
                    tr = tr[:197] + "..."
                example_lines.append(f"  - {ex['chapter']}:{ex['verse']} — {tr}")
            example_lines.append(
                "  These verses share at least one grammatical lemma with the\n"
                "  anchor insight, so they're candidates for showing the same\n"
                "  move in another context. Pick the ones that ARE actually\n"
                "  parallel — same grammatical move, not just same word in a\n"
                "  different role."
            )
            example_block = "\n".join(example_lines) + "\n"
        else:
            example_block = (
                "\nAdditional-example candidates: (none — V7 evidence had no\n"
                "resolvable lemma to cross-reference). Set additional_examples\n"
                "to an empty array [].\n"
            )
        cf_block = ""
        if cf.get("present") and cf.get("text"):
            cf_block = (
                f"\nCounterfactual present ({cf.get('type','')}):\n"
                f"  {cf['text']}\n"
                "  → BUILD THE SCRIPT AROUND THIS CONTRAST.\n"
            )
        else:
            cf_block = (
                "\nNo explicit counterfactual on this insight. Construct the\n"
                "natural alternative yourself (e.g. for a passive verb, the\n"
                "active form; for fronted phrases, the unmarked order; for\n"
                "perfective-of-future, the present-tense alternative). Frame\n"
                "it as 'a more typical way to say this would be ...' so the\n"
                "viewer knows the alternative is inferred, not quoted.\n"
            )

        note_block = ""
        if translation_note:
            note_block = (
                f"\nTranslation note (corroborating context only — do NOT make\n"
                f"this the spine of the script; the grammatical move is the\n"
                f"spine):\n  {translation_note}\n"
            )

        body = (
            "Series: Grammar Insights. Frame: every grammatical structure in\n"
            "the Quran is a deliberate choice. Your job is to illuminate ONE\n"
            "such choice. You are not teaching grammar rules. You are showing\n"
            "the reader a choice the author made and what that choice does.\n"
            "\n"
            "OUTPUT JSON beat keys (the structure is a contrast, not a lecture):\n"
            "  hook        (8 to 12s):   pose a small tension or question. Hint\n"
            "                             at the verse without quoting it yet.\n"
            "  verse_intro (25 to 35s):  the contrast. Quote the chosen Arabic\n"
            "                             form (1-2 words, with English gloss).\n"
            "                             State explicitly what the alternative\n"
            "                             would have been. Use phrasing like\n"
            "                             'The Quran could have used X. It\n"
            "                             chose Y instead. Why?' End the beat\n"
            "                             with the 'Why?' question to pull the\n"
            "                             listener into the next beat. THIS IS\n"
            "                             THE BEAT WHERE THE VERSE LANDS ON\n"
            "                             SCREEN.\n"
            "  insight     (35 to 50s, HARD CAP 65 WORDS, AT MOST 3\n"
            "                             SENTENCES): the payoff. State what the\n"
            "                             chosen form does that the alternative\n"
            "                             wouldn't — ONCE — then move to the\n"
            "                             concrete image and stop. Operator\n"
            "                             feedback from published Grammar Insights\n"
            "                             videos: the script consistently loses\n"
            "                             steam roughly 2/3 of the way through.\n"
            "                             That 2/3 point is exactly THIS beat.\n"
            "                             Viewers swipe when the script repeats\n"
            "                             the same point in different words\n"
            "                             instead of advancing.\n"
            "\n"
            "                             FORBIDDEN PATTERNS in this beat:\n"
            "                             • Enumeration: 'First, X. Second, Y.'\n"
            "                               Numbered points read as labored.\n"
            "                               State the moves prose-style.\n"
            "                             • Echo restatement: 'She is the sender.\n"
            "                               They are the sent. The queen commands;\n"
            "                               they obey. The grammar encodes her\n"
            "                               authority.' Pick ONE of these\n"
            "                               formulations. Cut the rest.\n"
            "                             • Negation-affirmation stacks: 'It is\n"
            "                               not X. It is Y. It does not Z. It does\n"
            "                               W.' One 'not X but Y' is fine; two in\n"
            "                               a row is filler.\n"
            "                             • Meta-commentary: 'The grammar quietly\n"
            "                               assigns roles', 'The verse stages the\n"
            "                               scene', 'The form carries weight.'\n"
            "                               These are filler verbs about the\n"
            "                               text. Show what the form DOES;\n"
            "                               don't editorialize that it does.\n"
            "                             • Summarising before the close: 'The\n"
            "                               verse doesn't just describe — it\n"
            "                               encodes.' The CLOSE beat lands the\n"
            "                               summary. Don't preempt it.\n"
            "\n"
            "                             VERBOSE (102 words, v38 published —\n"
            "                             operator: 'loses steam 2/3 in'):\n"
            "                               \"That choice does two things. First,\n"
            "                                it keeps the referent clear. When\n"
            "                                the text later describes what\n"
            "                                happens to this fire or who\n"
            "                                encounters it, the feminine pronouns\n"
            "                                and verb forms anchor back to an-nār\n"
            "                                without ambiguity. Second, it\n"
            "                                preserves a layer of role structure.\n"
            "                                Feminine marking in Semitic languages\n"
            "                                often tracks states, conditions, or\n"
            "                                encompassing realities, while\n"
            "                                masculine forms lean toward agents\n"
            "                                and discrete actors. By keeping\n"
            "                                an-nār feminine, the verse frames\n"
            "                                the fire not as an active punisher\n"
            "                                but as the encompassing condition,\n"
            "                                the state into which the oppressors\n"
            "                                are cast. The grammar quietly\n"
            "                                assigns roles before the narrative\n"
            "                                does.\"\n"
            "                             TIGHT REWRITE (~50 words, same payload):\n"
            "                               \"Feminine marking in Arabic doesn't\n"
            "                                just describe — it tracks. Pronouns\n"
            "                                anchor back to an-nār without\n"
            "                                ambiguity, and the form casts the\n"
            "                                fire as a STATE the oppressors fall\n"
            "                                into rather than an agent that\n"
            "                                attacks them.\"\n"
            "\n"
            "                             Land ONE concrete image at the end of\n"
            "                             this beat and STOP. Do not add 'and\n"
            "                             what this shows is...' after a strong\n"
            "                             line.\n"
            "  close       (8 to 15s):   the most distilled, quotable line in\n"
            "                             the entire script. Find the single\n"
            "                             sentence that crystallizes the\n"
            "                             insight and put it here. The close\n"
            "                             is reserved for that line; do not\n"
            "                             bury it earlier in the script.\n"
            "\n"
            "  additional_examples (DEFAULT 1 entry, ≤55 words each):\n"
            "                             Cross-reference verses where the same\n"
            "                             grammatical move appears elsewhere.\n"
            "                             Pick from the candidate list at the\n"
            "                             bottom of this prompt; do not invent\n"
            "                             references. Slot the example slides\n"
            "                             between verse_intro and insight:\n"
            "                               1. Hook on the main verse.\n"
            "                               2. Verse_intro on the main verse.\n"
            "                               3. Example #1 (\"In another verse,\n"
            "                                  ...\") — short and pointed.\n"
            "                               4. Insight + close zoom back to\n"
            "                                  the main verse.\n"
            "                             Pick 2 examples ONLY when the second\n"
            "                             demonstrates something the first\n"
            "                             didn't — different rhetorical\n"
            "                             register, different scope, surprising\n"
            "                             context. If the second would just\n"
            "                             re-prove the first, drop it. Two\n"
            "                             redundant examples make the video\n"
            "                             feel padded.\n"
            "\n"
            "                             KEEP EACH NARRATION TIGHT (≤55 words):\n"
            "                             Open with \"In another verse,\" or\n"
            "                             \"Elsewhere,\". Quote ≤8 words from\n"
            "                             the example translation. ONE sentence\n"
            "                             on how the pattern manifests here.\n"
            "                             STOP. Do NOT re-explain the\n"
            "                             grammatical concept — viewer just\n"
            "                             heard it.\n"
            "\n"
            "                             BAD example narration (verbose, 79w):\n"
            "                               \"In another verse, the same\n"
            "                                conditional structure appears\n"
            "                                twice in parallel. Chapter 6,\n"
            "                                verse 160, reads: 'Whoever\n"
            "                                comes with the good deed will\n"
            "                                have ten like it, and whoever\n"
            "                                comes with an evil deed will be\n"
            "                                recompensed only with the like\n"
            "                                of it...' Notice how each clause\n"
            "                                opens with the same particle,\n"
            "                                framing both the reward and the\n"
            "                                consequence as scenarios that\n"
            "                                respond to a person's choice.\"\n"
            "                             GOOD example narration (tight, 35w):\n"
            "                               \"Elsewhere, in 6:160: 'Whoever\n"
            "                                comes with a good deed.' Same\n"
            "                                particle, same scenario logic,\n"
            "                                this time framing reward as a\n"
            "                                response to a hypothetical\n"
            "                                person's choice.\"\n"
            "                             The good version trusts the listener\n"
            "                             to remember what was just said about\n"
            "                             the main verse and just shows the\n"
            "                             parallel.\n"
            "\n"
            "                             Set to [] when the main verse\n"
            "                             carries the point on its own (rare —\n"
            "                             usually 1 example is the right call).\n"
            "\n"
            "VOICE: write like a thoughtful human, not an essayist.\n"
            "  - DO NOT use em dashes (—). Anywhere. In any beat. Use\n"
            "    periods, commas, parentheses, or semicolons. Em dashes are\n"
            "    a well-known AI tell and they break the cadence we want.\n"
            "  - Short sentences. When a sentence is getting long, break it.\n"
            "    Periods are stronger than commas.\n"
            "  - Direct verbs. Say 'It describes X', not 'It is the form that\n"
            "    usually describes X'.\n"
            "  - Avoid AI-essayist tics: 'That choice changes everything',\n"
            "    'It's not just X, it's Y', 'In other words', 'What this\n"
            "    really means is'. These are filler.\n"
            "  - Rhetorical questions are good transitions. 'Why?' at the\n"
            "    end of a beat is a clean handoff to the next.\n"
            "  - Don't over-explain. If a line is doing the work, stop\n"
            "    talking. Trust the reader to feel the impact.\n"
            "\n"
            "STOP-LINE DISCIPLINE (the most common failure mode):\n"
            "  After you write a strong sentence — a vivid image, a\n"
            "  pointed contrast, a punchy demand — the next sentence\n"
            "  is almost always a mistake. The model trains on essay\n"
            "  prose, so it wants to keep going. Don't.\n"
            "\n"
            "  Concrete bans on the LAST sentence of insight and close:\n"
            "    - No 'And so we see that...' / 'This shows us...' /\n"
            "      'What this really means is...' / 'In other words...'\n"
            "    - No 'such is the beauty of the Quran' / 'this is\n"
            "      the depth of the divine text' / 'every word is\n"
            "      purposeful' (these are generic awe-statements; the\n"
            "      script just demonstrated the beauty — saying it\n"
            "      out loud weakens the demonstration).\n"
            "    - No restating the punchline in different words\n"
            "      ('The form is a challenge. It demands action. It\n"
            "      forces the reader to confront something.' — that's\n"
            "      one idea written three times.)\n"
            "\n"
            "  BAD insight ending (over-explaining):\n"
            "    \"...the perfective form turns the question into a\n"
            "    challenge. And so we see that grammar matters. The\n"
            "    Quran's choice is profound, showing how every word\n"
            "    is purposeful.\"\n"
            "  GOOD insight ending (lands and stops):\n"
            "    \"...the perfective form turns the question into a\n"
            "    challenge.\"   ← STOP. The image is doing the work.\n"
            "\n"
            "  BAD close (multi-sentence summary):\n"
            "    \"The Quran's choice of grammar is a window into its\n"
            "    depth, inviting the reader to see how every word is\n"
            "    intentional, and teaching us the importance of\n"
            "    paying attention to grammar.\"\n"
            "  GOOD close (one sentence, quotable):\n"
            "    \"Every grammatical choice in the Quran is a\n"
            "    deliberate move.\"\n"
            "\n"
            "  Validator enforces: close must be ONE sentence (max\n"
            "  two if absolutely necessary). If the close has 3+\n"
            "  sentences, the second and third are diluting the first\n"
            "  — drop them.\n"
            "\n"
            "EXAMPLE — for verse 107:1 (perfective tense for a rhetorical\n"
            "question), this is the TARGET voice:\n"
            "  hook: \"When the Quran asks a question, does it really expect\n"
            "    an answer or is something else going on?\"\n"
            "  verse_intro: \"Chapter 107 opens with a question: 'Have you\n"
            "    seen the one who denies the Judgment?' In Arabic, the verb\n"
            "    is ra'ayta. It is in the past-tense form. It describes\n"
            "    something already done. The Quran could have asked 'Do you\n"
            "    see?' using the present-tense form, tara. But it chose the\n"
            "    perfective instead. Why?\"\n"
            "  insight: \"That choice changes the sentence from a question\n"
            "    to a reflection. The present tense tara would frame the\n"
            "    question as open-ended, inviting you to look around and\n"
            "    discover. But ra'ayta, the past-tense form, treats the\n"
            "    seeing as already settled, as if the answer is obvious and\n"
            "    the question is rhetorical. It's not asking whether you've\n"
            "    noticed; it's assuming you already have, and now demanding:\n"
            "    what are you going to do about it?\"\n"
            "  close: \"The perfective form turns a question into a\n"
            "    challenge, framing the denial of Judgment not as a debatable\n"
            "    position but as a visible, undeniable reality you've already\n"
            "    witnessed.\"\n"
            "Notice: no em dashes. Short declarative sentences. The contrast\n"
            "is built explicitly through 'could have / chose instead'. The\n"
            "verse_intro ends on 'Why?' as a forward handoff. The insight\n"
            "ends on a punchy demand and STOPS. The close is the script's\n"
            "most quotable line, reserved for the end.\n"
            "\n"
            "AUDIENCE: someone who loves the Quran but is not familiar with\n"
            "Arabic grammar terminology. So:\n"
            "  - 'perfective tense' translate to 'the past-tense form'\n"
            "    and explain inline what it usually does\n"
            "  - 'passive voice' translate to 'leaving the doer out of\n"
            "    the picture'\n"
            "  - 'fronting' translate to 'putting the object first'\n"
            "  - 'iltifat' translate to 'the sudden switch from He to We'\n"
            "Translate AT FIRST USE. After that you can use the simple\n"
            "phrase. Never use the technical Arabic name without a gloss.\n"
            "\n"
            f"{header}"
            f"{note_block}"
            f"\nInsight title: {ins.get('title','')}"
            f"\nCategory: {ins.get('category','')}"
            f"\nClaim: {claim.get('observation','')}"
            f"\nScope: {claim.get('scope','')}, strength: {claim.get('strength','')}"
            f"{cf_block}"
            f"\nMeaning payoff (what the chosen form achieves):\n  {payoff.get('text','')}\n"
            "\nEvidence tokens. Refer to AT MOST 1 or 2 by Arabic form, with an\n"
            "immediate English gloss after each Arabic word:\n"
            + ("\n".join(ev_lines) if ev_lines else "(none)")
            + "\n"
            + example_block +
            "\nenglish_emphases (1-4 short phrases for the verse-card\n"
            "highlight pills):\n"
            "  Pick the English phrases from the translation above that\n"
            "  most clearly carry the grammatical move you're explaining.\n"
            "  These are highlighted on the verse card and every\n"
            "  occurrence is found, so a phrase that appears twice\n"
            "  (parallel structure, repeated pronoun) will light up\n"
            "  twice. Each phrase MUST be a CHARACTER-FOR-CHARACTER\n"
            "  substring of the translation — copy it from there\n"
            "  exactly, including capitalization and punctuation. The\n"
            "  validator rejects any phrase not present verbatim.\n"
            "\n"
            "  Examples of good choices:\n"
            "    - Person mixture (1:5): [\"You alone we serve\",\n"
            "      \"You alone we seek help from\"]\n"
            "    - Iltifat from third to first person: pick the two\n"
            "      pronouns or pronoun-bearing phrases that show the\n"
            "      shift, e.g. [\"He created you\", \"We taught you\"]\n"
            "    - Cognate accusative emphasis: pick the verb+object\n"
            "      pair where the doubling lives.\n"
            "  Empty array [] is allowed when the verse is so short\n"
            "  that emphases would just span the whole translation.\n"
            "\nGuardrails (the validator enforces these):\n"
            "  - NO em dashes. Anywhere. In any beat. The validator rejects\n"
            "    them outright.\n"
            "  - Don't introduce any grammatical claim that isn't in the\n"
            "    structured insight or counterfactual.\n"
            "  - Don't teach the rule. Show the choice.\n"
            "  - At most 2 Arabic words quoted by their surface form;\n"
            "    each must be followed by a brief English gloss.\n"
            "  - languages_referenced: [] (this series doesn't cite cognates).\n"
            "  - If you mention 'iltifat' / 'taqdim' / 'hazf' / 'tahqiq',\n"
            "    immediately translate it in plain English in the same\n"
            "    sentence. Or better: don't use the term at all.\n"
            "  - english_emphases: each phrase must appear verbatim\n"
            "    in the translation above. Copy from there; don't\n"
            "    paraphrase. Validator rejects non-matches.\n"
            "  - english_emphases: phrases must NOT overlap each\n"
            "    other in the translation. If you pick \"You alone\n"
            "    we serve\", the next emphasis cannot start with\n"
            "    \"You alone\" again (the second \"You alone\" must\n"
            "    be paired with the words after it, e.g. \"You alone\n"
            "    we seek help from\"). Validator rejects overlapping\n"
            "    spans because they render as duplicated text.\n"
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
    # Educational shorts have no copyright audio (only our ElevenLabs
    # narration), so the YouTube ≤60s Shorts rule doesn't bind us.
    # Cap is now ~90s of narration room (200 words at 150wpm) — still
    # tight enough that "short" stays punchy vs the 250-340w long form.
    if short_wc > 200:
        errors.append(f"voiceover_short word count {short_wc} exceeds 200")

    # Quran-only grounding. Reject scripts that lean on extra-Quranic
    # vocabulary (hadith, sunnah, ummah, sharia, classical commentators,
    # "Muslims believe", etc.). The prompt asks for this; the validator
    # makes it a hard constraint so the operator doesn't have to catch
    # leakage by eye in the preview pane. Whole-word matching (\b) so
    # "summarize" doesn't false-positive on "sunnah", and so on.
    quran_only_terms = [
        # Post-Quranic religious sources
        r"hadith", r"hadiths", r"sunnah", r"sunna", r"sira", r"seerah",
        r"tafsir", r"tafseer",
        # Concepts not framed in the Quran's own vocabulary
        r"ummah", r"sharia", r"shariah", r"halal", r"haram",
        r"ijma", r"fiqh", r"madhhab", r"madhab", r"sahaba",
        # Phrases that signal external interpretation
        r"the prophet said", r"prophet said",
        r"muslims believe", r"islamic tradition", r"in islam",
        r"according to islam", r"classical commentators?",
        r"classical scholars?", r"the four schools",
        r"the community of (?:believers?|followers?|the faithful)",
        # Religious-practice vocabulary framed by post-Quranic
        # tradition. The Quran describes establishing prayer,
        # standing in prayer, etc. — but not "congregational" or
        # "ritual" or "the five pillars". These are systematizations
        # from later tradition. Stick to what the verse text
        # actually says (e.g. "we serve", "we worship", "we stand
        # before God").
        r"congregational prayers?",
        r"congregational worship",
        r"ritual prayers?",
        r"ritual ablutions?",
        r"the five pillars?", r"pillars? of [Ii]slam",
        r"five daily prayers?", r"the daily prayers?",
    ]
    quran_only_re = re.compile(
        r"\b(?:" + "|".join(quran_only_terms) + r")\b",
        re.IGNORECASE,
    )
    quran_only_hits: dict[str, list[str]] = {}
    for fld in ("hook", "tidbit_about_root", "tidbit_about_quran_usage",
                "tidbit_about_semitic", "verse_intro", "insight", "close",
                "voiceover_long", "voiceover_short"):
        text = script.get(fld) or ""
        if not isinstance(text, str):
            continue
        matches = quran_only_re.findall(text)
        if matches:
            quran_only_hits[fld] = sorted(set(m.lower() for m in matches))
    if quran_only_hits:
        details = "; ".join(f"{f}: {ms}" for f, ms in quran_only_hits.items())
        errors.append(
            f"extra-Quranic vocabulary detected ({details}). This series "
            f"grounds every claim in the Quran's own text — no hadith, no "
            f"sunnah, no tafsir, no classical commentators, no Ummah/sharia/"
            f"halal vocabulary. Rewrite using Quran-only phrasing: 'the "
            f"verse says', 'elsewhere in the Quran', 'in this text', 'the "
            f"speaker'."
        )

    # Type-specific grounding checks.
    if payload["type"] == "word_origins":
        # Match the prompt's filtering — the LLM was only shown the
        # viewer-friendly subset, so the validator should only accept
        # from that same subset. (When the filter falls back to the
        # full list, the helper returns it unchanged.)
        derivs_visible, _ = _viewer_friendly_derivatives(
            payload.get("derivatives", []),
        )
        allowed_pool = [d["language"] for d in derivs_visible if d.get("language")]
        declared = script.get("languages_referenced") or []
        if not isinstance(declared, list):
            declared = []
        unknown = [d for d in declared if not _lang_matches(d, allowed_pool)]
        if unknown:
            errors.append(
                f"declared cognate languages not in payload: {unknown}. "
                f"Allowed pool: {allowed_pool}"
            )

    elif payload["type"] in ("grammar_insights", "translation_hides"):
        # Most of the structural / style guardrails are shared between
        # the two non-Word-Origins series — they both use the same
        # 4-beat structure (hook / verse_intro / insight / close), both
        # use english_emphases to highlight phrases on the verse card,
        # and both should resist the same essayist tics.
        # Stop-line discipline: the close beat must be ≤2 sentences.
        # The prompt asks for ONE sentence, but a real period-bearing
        # secondary clause (e.g. introductory phrase + main clause) is
        # acceptable. Three or more sentences = diluting the punchline,
        # which is exactly the operator-flagged failure mode.
        close_text = (script.get("close") or "").strip()
        if close_text:
            # Sentence boundary: . ! ? followed by whitespace or
            # end of string. Don't double-count "..." (ellipsis).
            ellipsis_neutralized = re.sub(r"\.{2,}", "", close_text)
            sentence_endings = re.findall(r"[.!?]+(?=\s|$)", ellipsis_neutralized)
            if len(sentence_endings) > 2:
                errors.append(
                    f"close has {len(sentence_endings)} sentences; "
                    f"keep it to 1 (max 2). The close is the script's "
                    f"single most quotable line — restating the same "
                    f"idea in different words dilutes it. Pick the "
                    f"strongest sentence and drop the rest. Current "
                    f"close: {close_text!r}"
                )

        # Essayist-tic detector. The prompt bans phrases like "in
        # other words" and "what this really means is" because they're
        # the LLM's signal that it's about to over-explain. Catch them
        # in the insight + close beats (the two most likely to slip).
        essayist_tics = [
            r"in other words",
            r"what this really means(?: is)?",
            r"and so we see (?:that|how)",
            r"this shows us(?: that)?",
            r"what this shows(?: is)?",
            r"such is the (?:beauty|depth|wisdom|profundity)",
            r"every word is (?:purposeful|intentional|deliberate)",
            r"the depth of the divine (?:text|word|message)",
            r"the beauty of the Quran",
        ]
        tic_re = re.compile(
            r"\b(?:" + "|".join(essayist_tics) + r")\b",
            re.IGNORECASE,
        )
        tic_hits: dict[str, list[str]] = {}
        for fld in ("insight", "close", "voiceover_long"):
            txt = script.get(fld) or ""
            if not isinstance(txt, str):
                continue
            ms = tic_re.findall(txt)
            if ms:
                tic_hits[fld] = sorted(set(m.lower() for m in ms))
        if tic_hits:
            details = "; ".join(f"{f}: {ms}" for f, ms in tic_hits.items())
            errors.append(
                f"essayist filler detected ({details}). Phrases like "
                f"'in other words', 'this shows us', 'such is the "
                f"beauty', 'the depth of the divine text' weaken the "
                f"line they follow — the demonstration just happened, "
                f"don't editorialize it. Trim them out and let the "
                f"strong sentence stand on its own."
            )

        # Em-dash check. Em dashes are a well-known AI-generated-text tell
        # and they break the cadence we want for these scripts. The prompt
        # forbids them; this validator enforces the rule on every beat.
        # Catches the actual em dash (U+2014) and the en dash (U+2013) used
        # similarly. We don't reject the regular hyphen-minus ("-") since
        # that's a legitimate punctuation mark.
        em_dash_fields = []
        for fld in ("hook", "verse_intro", "insight", "close",
                    "voiceover_long", "voiceover_short"):
            text = script.get(fld) or ""
            if "—" in text or "–" in text:
                em_dash_fields.append(fld)
        if em_dash_fields:
            errors.append(
                f"em or en dash detected in: {em_dash_fields}. "
                f"Replace every '—' or '–' with a period, comma, "
                f"parenthesis, or semicolon. Em dashes are an AI tell "
                f"and the prompt forbids them anywhere in any beat."
            )

        # No-jargon guardrail. The technical Arabic grammar terms below
        # are exactly what the script is meant to AVOID: the rubric is
        # "show the choice, don't teach the rule". If the LLM uses one,
        # it must be immediately followed by a plain-English gloss in
        # the same sentence; we approximate that with a "translate at
        # first use" check via the long voiceover (the short one is
        # tight enough that we don't expect jargon there).
        long_text = (script.get("voiceover_long") or "")
        for jargon in ("iltifat", "taqdim", "hazf", "tahqiq", "majhul",
                       "ma'ruf", "jumlah ismiyyah", "jumlah fi'liyyah",
                       "wazn", "rubāʿī", "rubaai"):
            if jargon.lower() in long_text.lower():
                # Search for an English translator phrase nearby (within
                # 80 chars after the jargon use). Heuristic: a hyphen, em
                # dash, or parenthetical typically introduces a gloss.
                import re as _re
                idx = long_text.lower().find(jargon.lower())
                window = long_text[idx: idx + len(jargon) + 80]
                gloss_present = bool(_re.search(r"[—–\-(]\s*[A-Za-z]", window))
                if not gloss_present:
                    errors.append(
                        f"voiceover_long uses Arabic grammar term '{jargon}' "
                        f"without an immediate English gloss. Either translate "
                        f"it inline (e.g. \"{jargon} — the sudden switch from\") "
                        f"or rewrite without the term."
                    )
        # Counterfactual must not be reported as truncated content. If
        # the LLM echoes a CF that ends mid-word, that's a sign it
        # propagated the upstream V7 truncation bug into the script.
        verse_intro_text = script.get("verse_intro") or ""
        if verse_intro_text.rstrip().endswith(("(e.", "(i.")):
            errors.append(
                "verse_intro looks like it copied a truncated upstream "
                "counterfactual ending in '(e.' or '(i.'. Rewrite the "
                "contrast in your own words."
            )

        # english_emphases must be substrings of the verse translation.
        # The renderer searches the translation for these phrases and
        # highlights every occurrence; if a phrase doesn't actually
        # appear in the translation, the renderer silently drops it
        # and the slide ships with no English highlights — bad UX.
        # Make this a hard check so the LLM is forced to either copy
        # exact substrings or drop the field.
        #
        # Quote/apostrophe normalization: ai_translations text often
        # uses curly quotes (’ U+2019, ‘ U+2018, “ U+201C, ” U+201D)
        # while Claude's JSON output uses straight ASCII (' " '). The
        # eye-level "Qur'an" in both is the same word, but a literal
        # substring match fails. Folding both sides to ASCII before
        # the check fixes the false-positive. Also fold the curly
        # apostrophe used in some Arabic transliterations.
        def _normalize_quotes(s: str) -> str:
            return (s
                .replace("’", "'")  # right single quotation
                .replace("‘", "'")  # left single quotation
                .replace("ʼ", "'")  # modifier letter apostrophe
                .replace("ʹ", "'")  # modifier letter prime
                .replace("“", '"')  # left double quotation
                .replace("”", '"')  # right double quotation
                .replace("–", "-")  # en dash (commonly substituted)
                .replace("—", "-")  # em dash
            )

        emphases = script.get("english_emphases")
        if emphases is not None:
            if not isinstance(emphases, list):
                errors.append(
                    "english_emphases must be a list of strings (got "
                    f"{type(emphases).__name__})."
                )
            else:
                translation = (payload.get("verse") or {}).get("translation") or ""
                t_lower = _normalize_quotes(translation.lower())
                # Track first-occurrence span of each valid phrase so
                # we can detect overlaps below.
                spans: list[tuple[int, int, str]] = []
                for i, phrase in enumerate(emphases):
                    if not isinstance(phrase, str):
                        errors.append(
                            f"english_emphases[{i}] must be a string."
                        )
                        continue
                    p = phrase.strip()
                    if not p:
                        continue
                    idx = t_lower.find(_normalize_quotes(p.lower()))
                    if idx < 0:
                        errors.append(
                            f"english_emphases[{i}] = {p!r} is not a "
                            f"verbatim substring of the verse translation. "
                            f"Copy phrases EXACTLY from the translation; "
                            f"don't paraphrase. Translation: {translation!r}"
                        )
                        continue
                    spans.append((idx, idx + len(p), p))

                # Overlap check. The renderer slices the translation
                # by match span; overlapping spans cause the
                # overlapping segment to render twice, producing
                # duplicated text on screen ("...and You alone You
                # alone we seek..."). Force the LLM to pick disjoint
                # spans.
                spans.sort()
                for i in range(len(spans) - 1):
                    a_start, a_end, a_phrase = spans[i]
                    b_start, b_end, b_phrase = spans[i + 1]
                    if b_start < a_end:
                        errors.append(
                            f"english_emphases overlap: {a_phrase!r} "
                            f"(positions {a_start}-{a_end}) and "
                            f"{b_phrase!r} (positions {b_start}-{b_end}) "
                            f"share text. Pick non-overlapping spans — "
                            f"e.g. for 1:5 use [\"You alone we serve\", "
                            f"\"You alone we seek help from\"], NOT "
                            f"[\"You alone we serve, and You alone\", "
                            f"\"You alone we seek help from\"]."
                        )

                if len(emphases) > 4:
                    errors.append(
                        f"english_emphases has {len(emphases)} entries; "
                        f"keep it to 1-4 short phrases."
                    )

        # additional_examples is grammar_insights-only. translation_hides
        # videos focus on a single verse — no on-screen cross-references.
        # Skip the cross-ref candidate-pool check entirely for the new
        # series; just enforce that the field is empty/absent.
        if payload["type"] == "translation_hides":
            ax = script.get("additional_examples")
            if ax is not None and isinstance(ax, list) and len(ax) > 0:
                errors.append(
                    "additional_examples must be [] for translation_hides "
                    "(this series doesn't cross-reference other verses on "
                    "screen). Got "
                    f"{len(ax)} entries."
                )

            # Reveal slide fields — both required, both short, must differ.
            # These drive the opening "Most translations say X / The Arabic
            # actually says Y" contrast slide.
            for fld, limit in (("reveal_conventional", 80), ("reveal_hidden", 80)):
                val = script.get(fld)
                if not isinstance(val, str) or not val.strip():
                    errors.append(
                        f"{fld} is required for translation_hides and must "
                        f"be a non-empty string."
                    )
                elif len(val.strip()) > limit:
                    errors.append(
                        f"{fld} is {len(val.strip())} chars; limit is "
                        f"{limit}. Tighten to a glance-readable phrase."
                    )
            rc = (script.get("reveal_conventional") or "").strip().lower()
            rh = (script.get("reveal_hidden") or "").strip().lower()
            if rc and rh and rc == rh:
                errors.append(
                    "reveal_conventional and reveal_hidden are identical — "
                    "the slide's whole purpose is to show a contrast. Make "
                    "them say different things."
                )

            # evidence_chip — optional, but if present must be short and
            # follow one of the named evidence-kind prefixes so the chip
            # reads as deliberate, not freeform.
            chip = script.get("evidence_chip")
            if chip is not None and isinstance(chip, str) and chip.strip():
                chip_s = chip.strip()
                if len(chip_s) > 60:
                    errors.append(
                        f"evidence_chip is {len(chip_s)} chars; limit is 60."
                    )
                # Soft check — the prompt asks for one of these prefixes;
                # the validator nudges the LLM but doesn't hard-fail other
                # phrasings (some legitimate chips might not fit any prefix).
                allowed_prefixes = ("morphology:", "lexical:", "context:", "cognate:", "grammar:")
                if not any(chip_s.lower().startswith(p) for p in allowed_prefixes):
                    # Demote to a warning by NOT appending to errors — the
                    # field is optional and the chip still renders. Print
                    # to stderr-equivalent so the operator sees it but the
                    # script still validates.
                    print(
                        f"[script-validate] evidence_chip {chip_s!r} doesn't start with "
                        f"one of {allowed_prefixes} — chip will render but may read "
                        f"as ad-hoc."
                    )

            # selected_word_pos — optional integer 1-based position of
            # the primary 'lens' word on the verse. The renderer uses it
            # to highlight that word in the verse-flow slide and to drive
            # the word-lens slide that shows conventional vs AI gloss.
            # Accept 0/null to mean "phrase-level or grammar-driven; no
            # single word is the focus." When set, must be a valid
            # 1-based index into the verse's whitespace-split Arabic.
            swp = script.get("selected_word_pos")
            if swp is not None and swp != 0:
                if not isinstance(swp, int) or swp < 1:
                    errors.append(
                        f"selected_word_pos must be a positive integer or "
                        f"null/0 (got {swp!r})."
                    )
                else:
                    arabic = (payload.get("verse") or {}).get("text_uthmani") or ""
                    word_count = len([w for w in arabic.split() if w.strip()])
                    if word_count and swp > word_count:
                        errors.append(
                            f"selected_word_pos={swp} exceeds the verse's "
                            f"word count {word_count}."
                        )

        # additional_examples must come from the candidate pool, with
        # narration text and (optional) english_emphases that match
        # the example verse's translation. Hard-validate so the LLM
        # can't invent references. Grammar-insights only.
        ax = script.get("additional_examples")
        if payload["type"] == "grammar_insights" and ax is not None:
            if not isinstance(ax, list):
                errors.append(
                    "additional_examples must be a list (got "
                    f"{type(ax).__name__})."
                )
            else:
                if len(ax) > 2:
                    errors.append(
                        f"additional_examples has {len(ax)} entries; "
                        f"keep it to 0-2 cross-references."
                    )
                allowed = {
                    (c["chapter"], c["verse"]): c
                    for c in (payload.get("additional_example_candidates") or [])
                }
                for i, item in enumerate(ax[:2]):
                    if not isinstance(item, dict):
                        errors.append(
                            f"additional_examples[{i}] must be an object."
                        )
                        continue
                    try:
                        c_ch = int(item.get("chapter"))
                        c_v = int(item.get("verse"))
                    except (TypeError, ValueError):
                        errors.append(
                            f"additional_examples[{i}] missing valid chapter/verse."
                        )
                        continue
                    cand = allowed.get((c_ch, c_v))
                    if cand is None:
                        errors.append(
                            f"additional_examples[{i}] {c_ch}:{c_v} is not in "
                            f"the candidate pool. Pick from the list at the "
                            f"bottom of the prompt; do not invent references."
                        )
                        continue
                    narration = item.get("narration") or ""
                    if not isinstance(narration, str) or len(narration.strip()) < 30:
                        errors.append(
                            f"additional_examples[{i}].narration must be a "
                            f"sentence (≥30 chars). Aim for ~15-25s of "
                            f"voiceover that opens with 'In another verse,' "
                            f"or 'Elsewhere,' and shows the parallel."
                        )
                    # Word-count cap — operator feedback flagged that
                    # 70-80 word example narrations make the video feel
                    # padded. 55 words is ~12-15s, plenty for "open
                    # with 'Elsewhere,' + quote + one sentence" without
                    # re-explaining the grammar.
                    nar_wc = _word_count(narration)
                    if nar_wc > 55:
                        errors.append(
                            f"additional_examples[{i}].narration is {nar_wc} "
                            f"words; keep to ≤55 (≈12-15s). Don't re-explain "
                            f"the grammatical concept — the viewer just "
                            f"heard it. Format: 'In another verse,' / "
                            f"'Elsewhere,' + ≤8-word quote from the "
                            f"translation + one sentence on how the pattern "
                            f"shows up here. STOP."
                        )
                    # Essayist-tic check on narrations too — same
                    # filler patterns that bloat the main beats also
                    # bloat examples.
                    nar_tics = tic_re.findall(narration)
                    if nar_tics:
                        errors.append(
                            f"additional_examples[{i}].narration contains "
                            f"essayist filler: {sorted(set(t.lower() for t in nar_tics))}. "
                            f"Trim them out — the example slide should "
                            f"land the parallel cleanly without re-stating "
                            f"the lecture."
                        )
                    # Optional english_emphases on this example. Same
                    # rules as the top-level field but matched against
                    # THIS verse's translation. Apply the same quote
                    # normalisation so curly-quoted "Qur'an" in the
                    # translation matches the LLM's straight-quote
                    # version (the actual cause of the 87:18 failure).
                    e_em = item.get("english_emphases")
                    if e_em is not None:
                        if not isinstance(e_em, list):
                            errors.append(
                                f"additional_examples[{i}].english_emphases "
                                f"must be a list."
                            )
                        else:
                            cand_t = _normalize_quotes((cand.get("translation") or "").lower())
                            for j, phrase in enumerate(e_em):
                                if not isinstance(phrase, str):
                                    continue
                                p = phrase.strip()
                                if not p:
                                    continue
                                if _normalize_quotes(p.lower()) not in cand_t:
                                    errors.append(
                                        f"additional_examples[{i}]."
                                        f"english_emphases[{j}] = {p!r} is "
                                        f"not in {c_ch}:{c_v}'s translation. "
                                        f"Copy verbatim or drop the field."
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
        "\n  - voiceover_short: ≤200 words. Keep it punchy."
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
        derivs_visible, _ = _viewer_friendly_derivatives(
            payload.get("derivatives", []),
        )
        langs = sorted({d["language"] for d in derivs_visible if d.get("language")})
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
