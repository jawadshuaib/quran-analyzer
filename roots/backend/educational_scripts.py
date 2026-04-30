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

Output schema (all keys required, all strings):
{
  "hook":          "1 sentence, ≤22 words, hooks attention",
  "verse_intro":   "1 sentence introducing the verse reference and what it says",
  "insight":       "2-4 sentences delivering the actual payload",
  "close":         "1 sentence reflective close. End on the meaning, not on a doctrinal claim.",
  "voiceover_long":  "Concatenated narration 220-340 words (target ~280; absolute minimum 180), smooth flow, suitable for ElevenLabs TTS. Include the verse reference said aloud once. DO NOT include the Arabic recitation — the reciter's audio plays separately.",
  "voiceover_short": "Concatenated narration ≤120 words, suitable for a sub-55-second Short. Skip the verse-intro recap; lead with the hook, deliver the insight, close. Same exclusion: do not include Arabic recitation in the narration.",
  "languages_referenced": ["list of language names actually mentioned in voiceover_long, copied exactly from the payload"],
  "notes": "any caveats; empty string if none"
}
"""


class ScriptGenError(Exception):
    """Raised when generation or validation fails."""


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
        body = (
            "Series: Word Origins. Trace this Arabic word's root across Semitic.\n\n"
            f"{header}\n"
            f"Word in this verse: {word['form_arabic']} ({word['form_buckwalter']})\n"
            f"Root: {root['arabic']} (Buckwalter: {root['buckwalter']}, "
            f"transliteration: {root['transliteration']})\n\n"
            "Cognate derivatives (oldest first — pick 2-4 most striking for the script):\n"
            + "\n".join(deriv_lines)
            + "\n\nGuidance for this script:\n"
            "- Hook on the cross-language link a viewer wouldn't expect.\n"
            "- Pick at most 4 cognates to name. Don't try to list all.\n"
            "- If two languages give different but related meanings, that's the payload — show how the meaning shifts across the family.\n"
            "- Languages_referenced must contain ONLY languages from the list above."
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
    required = (
        "hook", "verse_intro", "insight", "close",
        "voiceover_long", "voiceover_short",
    )
    for k in required:
        v = script.get(k)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"missing or empty: {k}")

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
    if payload.get("type") == "word_origins":
        langs = sorted({d["language"] for d in payload.get("derivatives", []) if d.get("language")})
        msg += (
            "\n\nThe ONLY languages you may name in voiceover_long, voiceover_short, "
            "or languages_referenced are these — copy the spelling exactly, "
            "including any apostrophes:\n"
            + ", ".join(langs)
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

    script["raw_response"] = raw
    script["model"] = model
    return script
