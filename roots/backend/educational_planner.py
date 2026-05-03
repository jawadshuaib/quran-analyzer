"""Ollama-driven slide planner for word_origins videos.

The static slide-builder in educational_render_remotion.py maps script
beats onto fixed slide positions (root → source verse → cross-ref →
outro). That works but produces two problems:

1. The root slide lingers (hook + tidbit_about_root concatenated, ~15s
   on a static visual reads as boring).
2. When the narrator says "in 19:4", the slide on screen is whichever
   verse the static mapping picked — often NOT 19:4. Visual-audio
   mismatch.

This module asks Ollama (cloud-hosted) to:
  - Polish the narration text (remove em dashes, fix "?." typos,
    rewrite hard-to-pronounce transliterations like "ra's" → "raas").
  - Split the polished narration into slides such that each slide's
    visual matches what's being spoken: when narrator mentions 19:4,
    a verse-flow slide for 19:4 is active.
  - Constrain total length to ~60 seconds so the output fits the
    Shorts format the user is producing.

Falls back to the static mapping if Ollama is unavailable or its
output fails validation. The fallback is the same shape, so the
caller doesn't need to know which path produced the slides.
"""

from __future__ import annotations

import json
import re
import sqlite3

import requests


class PlannerError(Exception):
    """Raised when the planner can't produce a valid plan. Caller
    should fall back to a static mapping."""


# How many words per second of TTS at ElevenLabs eleven_multilingual_v2
# at default settings. Empirically ~2.5 words/sec for English. Used to
# convert word counts into expected playback duration in the prompt
# rules — Ollama gets a soft duration target rather than picking
# wildly-long-or-short narrations per slide.
_WORDS_PER_SEC = 2.5

# Target total duration in seconds. Shorts cap at 60s on YouTube
# without losing the Shorts label, so we aim for 50-58s of narration
# plus a 5s outro splash → 55-63s total.
_TARGET_NARRATION_SEC_MIN = 45
_TARGET_NARRATION_SEC_MAX = 58


def _ollama_prefs(conn: sqlite3.Connection) -> dict[str, str]:
    """Pull the same Ollama preferences app.py's _ollama_complete uses,
    via a passed-in connection so we can be called from a background
    thread that already has a Flask request context."""
    out: dict[str, str] = {}
    for r in conn.execute(
        "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
    ).fetchall():
        out[r["key"]] = r["value"]
    return out


def _build_prompt(
    *,
    root_letters: str,
    transliteration: str,
    root_meaning: str,
    available_verses: list[dict],
    raw_narration: str,
) -> str:
    """Assemble the planning prompt. Kept in one place so prompt
    changes are visible and the inputs can be unit-checked."""

    verses_block = json.dumps(available_verses, ensure_ascii=False, indent=2)

    return f"""You are editing a 60-second YouTube Short script about a Quranic root word.

ROOT: {root_letters} (transliteration: {transliteration})
Approximate meaning: {root_meaning}

VERSES AVAILABLE TO DISPLAY (you may ONLY pick from these — do not invent verses):
{verses_block}

RAW NARRATION (needs polishing AND segmenting):
{raw_narration}

YOUR TASK
=========
Output strict JSON describing how to slice this narration into slides,
where each slide shows a visual that matches what's being spoken.

OUTPUT SHAPE (no markdown, no commentary, JSON only):
{{
  "slides": [
    {{ "type": "root", "narration": "<polished text>" }},
    {{ "type": "verse", "surah": <int>, "ayah": <int>, "word_pos": <int>, "narration": "<polished text>" }},
    {{ "type": "verse", "surah": <int>, "ayah": <int>, "word_pos": <int>, "narration": "<polished text>" }},
    {{ "type": "outro", "narration": "<polished text>" }}
  ]
}}

RULES
=====
1. Total spoken narration must be roughly {_TARGET_NARRATION_SEC_MIN}-{_TARGET_NARRATION_SEC_MAX} seconds. At about {_WORDS_PER_SEC} words/second of TTS, that's roughly {int(_TARGET_NARRATION_SEC_MIN * _WORDS_PER_SEC)}-{int(_TARGET_NARRATION_SEC_MAX * _WORDS_PER_SEC)} words across all slides combined. Keep it tight — cut anything that doesn't earn its time.

2. Slide order is FIXED: exactly one "root" first, exactly one "outro" last, "verse" slides between them.

3. The root slide narration is just the HOOK — the most surprising or vivid sentence in the script. Should be 3-7 seconds (8-18 words). Do NOT pile the entire root tidbit onto the root slide; that makes the static letters linger and it reads as boring.

4. For each "verse" slide, copy the surah+ayah+word_pos EXACTLY from the AVAILABLE VERSES list. Do not change them. Do not invent.

5. The narration on each verse slide must talk about THAT verse (or about a phenomenon vividly illustrated by THAT verse). When the original script says "in 37:65", the slide showing 37:65 should be the active one during those words.

6. If the script doesn't explicitly tie a sentence to a specific verse, you can still use a verse slide — pick the verse from the pool that BEST illustrates the sentence's claim.

7. The outro narration is a brief reflective close — typically the script's last sentence, polished. Should be 3-7 seconds.

8. POLISHING the text — apply ALL of these:
   - Remove em dashes (—). Replace with a period (full pause) or comma (brief pause), whichever reads more naturally.
   - Fix punctuation errors: "?." → "?", "!." → "!", double spaces → single.
   - Rewrite Arabic transliterations to be PHONETIC for English TTS:
     * "ra's" → "raas" (no apostrophe; vowels readable)
     * "ra'iis" → "raees"
     * "rasiyat" stays as is (already readable)
     * "nazzala" stays as is
     * In general: drop apostrophes inside transliterated words, double a vowel where the apostrophe was hiding length.
   - Keep proper nouns: "Sūrah", "Quran", "Allah" (with macrons or without — pick what's already in the source).
   - Don't add new claims or remove substantive content. You are POLISHING and SEGMENTING, not rewriting.

9. Total slide count: aim for 4-6 slides. Anything fewer and the visual lingers; anything more and the slides feel choppy.

10. Output JSON only. Nothing before, nothing after. No ```json fences.
"""


_SCHEMA_REQUIRED = {"slides"}


def _validate_plan(plan: dict, available_verses: list[dict]) -> list[dict]:
    """Apply hard validation on Ollama's output. Returns the slides
    list if valid; raises PlannerError otherwise. Caller falls back
    to the static mapping on raise."""

    if not isinstance(plan, dict):
        raise PlannerError("plan is not an object")
    if "slides" not in plan or not isinstance(plan["slides"], list):
        raise PlannerError("plan.slides missing or not a list")
    slides = plan["slides"]
    if len(slides) < 3:
        raise PlannerError(f"too few slides: {len(slides)}")
    if len(slides) > 8:
        raise PlannerError(f"too many slides: {len(slides)}")

    # Order constraint: first must be root, last must be outro.
    if slides[0].get("type") != "root":
        raise PlannerError("first slide must be type=root")
    if slides[-1].get("type") != "outro":
        raise PlannerError("last slide must be type=outro")

    # Verses in the middle must reference real entries from
    # available_verses. Build a lookup of (surah, ayah) → word_pos
    # so we can validate AND fill in word_pos if Ollama got it
    # slightly wrong.
    pool = {(int(v["surah"]), int(v["ayah"])): int(v["word_pos"]) for v in available_verses}

    for idx, slide in enumerate(slides[1:-1], start=1):
        if slide.get("type") != "verse":
            raise PlannerError(f"slide {idx} type must be 'verse', got {slide.get('type')!r}")
        try:
            s = int(slide["surah"])
            a = int(slide["ayah"])
        except (KeyError, TypeError, ValueError):
            raise PlannerError(f"slide {idx} missing surah/ayah")
        if (s, a) not in pool:
            raise PlannerError(f"slide {idx} references {s}:{a} which isn't in the available pool")
        # Trust the pool's word_pos over whatever Ollama wrote — the
        # pool comes from morphology data and is canonical.
        slide["word_pos"] = pool[(s, a)]

    # Every slide must have non-empty narration text.
    for idx, slide in enumerate(slides):
        narration = (slide.get("narration") or "").strip()
        if not narration:
            raise PlannerError(f"slide {idx} has empty narration")
        slide["narration"] = narration

    # Final sanity: total word count should land near the target band.
    # Allow ±50% on the soft target since Ollama's word counting is
    # approximate. If wildly off (10s or 120s), something's wrong.
    total_words = sum(
        len(re.findall(r"\b\w+\b", s["narration"])) for s in slides
    )
    expected_words_low = int(_TARGET_NARRATION_SEC_MIN * _WORDS_PER_SEC * 0.5)
    expected_words_high = int(_TARGET_NARRATION_SEC_MAX * _WORDS_PER_SEC * 1.5)
    if not (expected_words_low <= total_words <= expected_words_high):
        raise PlannerError(
            f"total word count {total_words} outside acceptable band "
            f"[{expected_words_low}, {expected_words_high}]"
        )

    return slides


def _root_meaning_summary(payload: dict, script: dict) -> str:
    """Best one-line gloss of the root for the prompt. Prefers a
    cognate concept (Hebrew/Aramaic), falls back to the first
    sentence of tidbit_about_root."""
    derivs = payload.get("derivatives") or []
    for d in derivs:
        if d.get("language") in ("Hebrew", "Biblical Aramaic", "Aramaic") and d.get("concept"):
            return d["concept"]
    if derivs and derivs[0].get("concept"):
        return derivs[0]["concept"]
    tidbit = (script.get("tidbit_about_root") or "").strip()
    if tidbit:
        return tidbit.split(".")[0].strip()[:120]
    return "(no gloss available)"


def _build_available_verses(payload: dict, anchor_word_pos: int) -> list[dict]:
    """Assemble the pool of verses Ollama can pick from. Includes the
    source verse itself plus any other_verses populated by enrich_payload."""
    out: list[dict] = []
    src = payload.get("verse") or {}
    if src and src.get("chapter") and src.get("verse"):
        out.append({
            "surah": int(src["chapter"]),
            "ayah": int(src["verse"]),
            "word_pos": int(anchor_word_pos or 1),
            "arabic": src.get("text_uthmani", "")[:400],
            "translation": src.get("translation", "")[:400],
            "is_source": True,
        })
    for ov in (payload.get("other_verses") or []):
        try:
            s = int(ov["chapter"]); a = int(ov["verse"])
        except (KeyError, TypeError, ValueError):
            continue
        if any(v["surah"] == s and v["ayah"] == a for v in out):
            continue
        out.append({
            "surah": s,
            "ayah": a,
            "word_pos": int(ov.get("word_pos") or 1),
            "arabic": (ov.get("text_uthmani") or "")[:400],
            "translation": (ov.get("translation") or "")[:400],
            "is_source": False,
        })
    # Cap the pool at 6 — too many options confuses the planner and
    # bloats the prompt. The 6 most relevant come from the existing
    # candidate-selection logic upstream.
    return out[:6]


def _build_raw_narration(script: dict) -> str:
    """Concatenate the script's beats into one block for Ollama to
    polish + segment. We send beat fields rather than voiceover_long
    so Ollama can see the natural structure (hook → root → usage →
    semitic → close), which helps it match narration to slides."""
    parts: list[str] = []
    for k in (
        "hook",
        "tidbit_about_root",
        "tidbit_about_quran_usage",
        "tidbit_about_semitic",
        "close",
    ):
        v = (script.get(k) or "").strip()
        if v:
            parts.append(v)
    return "\n\n".join(parts)


def plan_word_origins_slides(
    conn: sqlite3.Connection,
    payload: dict,
    script: dict,
    anchor_word_pos: int,
) -> list[dict]:
    """Public entry point. Returns a list of slide dicts ready for the
    Remotion payload (each having 'type' and 'narration', plus per-
    type extras). Raises PlannerError if Ollama is misconfigured /
    unreachable / produces unusable output — caller falls back."""

    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (prefs.get("ollama_metadata_model") or prefs.get("ollama_model") or "").strip()
    api_key = prefs.get("ollama_api_key") or ""
    if not model:
        raise PlannerError("Ollama model not configured")

    root = payload.get("root") or {}
    root_letters = " ".join(list((root.get("arabic") or "").strip())) or "(root letters missing)"
    transliteration = (root.get("transliteration") or root.get("buckwalter") or "?").strip()
    root_meaning = _root_meaning_summary(payload, script)

    available_verses = _build_available_verses(payload, anchor_word_pos)
    if not available_verses:
        raise PlannerError("no available verses to plan against")

    raw_narration = _build_raw_narration(script)
    if not raw_narration:
        raise PlannerError("script has no narration content")

    user_prompt = _build_prompt(
        root_letters=root_letters,
        transliteration=transliteration,
        root_meaning=root_meaning,
        available_verses=available_verses,
        raw_narration=raw_narration,
    )

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an experienced video editor for a Quranic etymology channel. "
                            "You output strict JSON. You never invent verses. You do not add commentary."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.3},
                "think": True,
            },
            timeout=180,
        )
    except requests.RequestException as e:
        raise PlannerError(f"Ollama transport error: {e}")

    if resp.status_code != 200:
        raise PlannerError(f"Ollama HTTP {resp.status_code}: {resp.text[:300]}")

    content = resp.json().get("message", {}).get("content", "") or ""
    # Strip thinking blocks + markdown fences (pattern lifted from
    # app.py's _ollama_complete).
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
    content = re.sub(r"\n?```\s*$", "", content.strip())

    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise PlannerError("Ollama response had no JSON object")
    try:
        plan = json.loads(m.group())
    except json.JSONDecodeError as e:
        raise PlannerError(f"Ollama JSON parse failed: {e}")

    slides = _validate_plan(plan, available_verses)
    return slides
