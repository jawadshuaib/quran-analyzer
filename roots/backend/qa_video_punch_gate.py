"""Q&A video — Gate A: editorial / punchiness ("would someone subscribe?").

Two stages:
  precheck()    deterministic, free, runs first. Word/duration budget,
                no post-Quranic terminology, a question in the hook, the
                <=2-verses rule, refs exist.
  judge_panel() OPTIONAL multi-lens LLM panel. FAILS CLOSED (timeout /
                malformed / refuse => reject), the opposite of the
                educational interestingness judge's fail-open default,
                because here the mandate is quality over quantity. OFF by
                default in Phase 0 (no spend); enable via run(..., llm=True).

Both return {ok, issues|verdict}. The orchestrator gates on ok.
"""

from __future__ import annotations

import json
import os
import re

import qa_video_common as C

# Post-Quranic terminology that must never appear in narration (the
# label-scan from the Q&A doctrine). Transliterated Quranic terms WITH a
# gloss are fine; these Latin identity/era labels are not.
_POST_QURANIC = re.compile(
    r"\b(Muslims?|Islamic|Islam|halal|haram|hadith|sunnah|caliph|"
    r"sharia|mosque|imam|madhhab|fiqh)\b",
    re.IGNORECASE,
)
# "pre-Islamic" is a period label, not post-Quranic vocabulary — the site's
# own public feature is titled "Pre-Islamic Poetry" and the bayt slide's
# on-screen eyebrow says the same. Strip it before the banned-term scan so
# "Islamic" inside it doesn't false-positive.
_PRE_ISLAMIC = re.compile(r"\bpre-?islamic\b", re.IGNORECASE)

# Budget. Length is the real lever since total video length is
# narration-driven (renderer bumps each slide to audio+0.4s).
MIN_WORDS = 60
# Raised from 95s (2026-07-08): at 3 curated videos/week a script may run
# to ~2 minutes when the insight earns the room (YouTube Shorts allows up
# to 3 min vertical). Punchy still wins — the brief keeps 45-75s as the
# default aim; this is a ceiling, not a target.
MAX_DURATION_SEC = 125.0
# Verses SHOWN (a contrast slide shows two at once). Raised 2 -> 3 with
# the ~2-minute budget: a long script may add one extra cross-reference.
MAX_VERSE_SLIDES = 3

# Distinctive phrases from the 39:42 exemplar in the script-gen prompt.
# If they show up on a verse that ISN'T 39:42, the model leaked the
# example into its output (the narration won't describe the real verse).
# A cheap backstop for narration<->verse incoherence; the LLM panel's
# "student" lens is the fuller semantic check.
_EXEMPLAR_FINGERPRINTS = (
    "sleep resembles death",
    "one verb performs both",
    "runs the same scene with a bolder verb",
    "yatawaffā", "yatawaffa",
    "the resurrection word",
)


def _all_narration(payload: dict) -> str:
    parts = []
    for s in payload.get("slides") or []:
        t = ((s.get("narration") or {}).get("text") or "").strip()
        if t:
            parts.append(t)
    return " ".join(parts)


def precheck(conn, script: dict, payload: dict, *, cited_refs: list[str] | None = None) -> dict:
    issues: list[str] = []
    narration = _all_narration(payload)
    wc = C.word_count(narration)
    dur = C.estimate_duration_sec(narration)

    if wc < MIN_WORDS:
        issues.append(f"too thin: {wc} spoken words (< {MIN_WORDS})")
    if dur > MAX_DURATION_SEC:
        issues.append(f"too long: ~{dur:.0f}s estimated (> {MAX_DURATION_SEC:.0f}s); trim the script")

    m = _POST_QURANIC.search(_PRE_ISLAMIC.sub(" ", narration + " " + (script.get("title") or "")))
    if m:
        issues.append(f"post-Quranic terminology: {m.group(0)!r} (render Arabic terms transliterated + glossed)")

    # Spoken-style check (operator rule, 2026-07-09): the narration is
    # SPEECH — it is read aloud and shown as captions. Em/en dashes and
    # colon/semicolon constructions are written-register tics (and read
    # as AI prose); a voice can't say them. Titles are exempt (not spoken).
    for ch, name in (("\u2014", "em-dash"), ("\u2013", "en-dash"),
                     (":", "colon"), (";", "semicolon")):
        n = narration.count(ch)
        if n:
            issues.append(
                f"written-register punctuation in narration: {n}x {name} — "
                f"rewrite as speech (short sentences, no {name}s)")

    if (script.get("anchor_ref") or "") != "39:42":
        low = narration.lower()
        leaked = next((fp for fp in _EXEMPLAR_FINGERPRINTS if fp.lower() in low), None)
        if leaked:
            issues.append(f"exemplar leakage: narration reuses the 39:42 example phrase {leaked!r} "
                          f"— it doesn't describe this verse")

    # A question must open the loop: the title or the first/hook beat.
    beats = script.get("beats") or []
    hook = next((b for b in beats if b.get("kind") == "hook"), beats[0] if beats else {})
    hook_text = (hook.get("narration") or "")
    title = script.get("title") or ""
    if "?" not in hook_text and "?" not in title:
        issues.append("no question in the hook/title — the video must open in a question")

    n_verse = sum(
        2 if s.get("type") == "verse-contrast" else 1
        for s in payload.get("slides") or []
        if s.get("type") in ("verse-flow", "verse-contrast")
    )
    if n_verse == 0:
        issues.append("no verse on screen")
    if n_verse > MAX_VERSE_SLIDES:
        issues.append(f"{n_verse} verses shown (> {MAX_VERSE_SLIDES}) — keep it punchy")

    for ref in [script.get("anchor_ref")] + list(cited_refs or []):
        if not ref:
            continue
        try:
            c, v = C.parse_ref(ref)
        except ValueError:
            issues.append(f"ref {ref!r} malformed")
            continue
        if not C.verse_exists(conn, c, v):
            issues.append(f"ref {ref} does not exist")

    return {"ok": not issues, "issues": issues,
            "word_count": wc, "est_duration_sec": round(dur, 1), "verse_slides": n_verse}


# ---------------------------------------------------------------------------
#  Optional LLM panel (fail-closed). Import-safe: requests is lazy-imported,
#  and we never import app/translate_ai (which would boot Flask).
# ---------------------------------------------------------------------------

_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
_PANEL_MODEL = os.environ.get("QA_VIDEO_JUDGE_MODEL", "qwen3:14b")

_LENSES = {
    "scroller": (
        "You are a YouTube viewer with your thumb on the screen. In the first 3 "
        "seconds, is there a concrete reason NOT to scroll past? Reject synonym-"
        "swaps and statements with no real question."
    ),
    "student": (
        "You are a careful student. Does the script actually TRIANGULATE — converge "
        "on meaning by naming verse evidence — and does the payoff genuinely answer "
        "the opening question? Is the voice a teacher speaking WITH the viewer (not "
        "preaching AT them), with confidence proportioned to the evidence?"
    ),
    "doctrine": (
        "You check doctrine. Is it strictly Qur'an-internal (no hadith, tafsir, "
        "biography, chronology)? No post-Qur'anic terminology? Arabic rendered "
        "transliterated + glossed, never as a bare Latin identity label? No "
        "fabricated or off-point cross-references?"
    ),
}


def _ollama_judge(lens_name: str, lens_desc: str, script_text: str, model: str) -> dict:
    import requests  # lazy

    sys = (
        f"{lens_desc}\n\nYou are judging a 60-90s Qur'an video script. Be strict and "
        "FAIL CLOSED: if anything is borderline, mark pass=false. Reply with STRICT "
        'JSON only: {"pass": true|false, "score": 0-10, "reason": "<one line>"}.'
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": script_text},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }
    resp = requests.post(_OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"no JSON in {lens_name} reply: {content[:160]}")
    return json.loads(content[start:end + 1])


def judge_panel(script: dict, payload: dict, *, model: str | None = None) -> dict:
    """Three-lens fail-closed panel. Reject unless ALL lenses pass.
    Any per-lens error counts as that lens failing (fail closed)."""
    model = model or _PANEL_MODEL
    script_text = (
        f"TITLE: {script.get('title','')}\n\n"
        + _all_narration(payload)
    )
    verdicts = {}
    all_pass = True
    for name, desc in _LENSES.items():
        try:
            v = _ollama_judge(name, desc, script_text, model)
            v["pass"] = bool(v.get("pass"))
        except Exception as e:  # fail closed
            v = {"pass": False, "score": 0, "reason": f"judge error: {e}"}
        verdicts[name] = v
        all_pass = all_pass and v["pass"]
    return {"ok": all_pass, "verdicts": verdicts, "model": model}


def run(conn, script: dict, payload: dict, *, cited_refs: list[str] | None = None,
        llm: bool = False, model: str | None = None) -> dict:
    pre = precheck(conn, script, payload, cited_refs=cited_refs)
    out = {"ok": pre["ok"], "precheck": pre, "panel": None}
    if not pre["ok"]:
        return out  # don't pay for the LLM panel on a script that already fails
    if llm:
        panel = judge_panel(script, payload, model=model)
        out["panel"] = panel
        out["ok"] = panel["ok"]
    return out
