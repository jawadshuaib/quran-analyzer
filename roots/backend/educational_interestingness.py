"""Interestingness gate for the educational pipeline.

After a script is generated for a candidate verse, this judge decides
whether the reveal is interesting enough to publish as a YouTube
Short. If not, the pipeline marks the row 'rejected_uninteresting'
and picks the next candidate.

Why this exists: operator feedback on the 33:5 render — "it rendered
but honestly it is a bit uninteresting." The verse + script combo
landed in the 'technically a translation hides moment, but viewers
will swipe' zone. Plenty of signals at score ≥ 7 are technical
nuances (passive→active, definite→indefinite) without a sensorial
payoff. The conventional gloss + AI gloss don't disagree in a way
that flips the picture; they just refine a corner of it. Bland
shorts hurt the channel's hit rate — better to skip and let the
pipeline land on a verse where the contrast SHOWS something
(sins→tails, chastity→architecture).

The judge runs ONLY after script generation, so it can score the
whole story arc (hook + verse_intro + insight + close), not just
the bare signal. A great signal with a fumbled script gets rejected;
a clean script around a quiet signal also gets rejected. Either way
the pipeline tries the next candidate.

Public surface:
    ensure_columns(conn)
        Idempotent ALTER for the new verdict columns + status value.
        Called once on app boot.

    judge_script(conn, payload, script) -> dict
        {verdict: 'interesting'|'skip'|'unknown',
         score:   1-10,
         reason:  '≤25 word phrase'}
        'unknown' on any Ollama failure — caller treats as 'interesting'
        (permissive default: we'd rather render one boring video than
        starve the pipeline because Ollama is flapping).

The Ollama call uses the same admin_preferences keys
('ollama_base_url', 'ollama_metadata_model' / 'ollama_model',
'ollama_api_key') as educational_safety.py so the operator only
configures one model.
"""

from __future__ import annotations

import json
import re
import sqlite3

import requests


# Threshold at which we accept. Tuned against the 33:5 reference
# ("uninteresting" per operator) and 66:12 / 25:58 ("interesting" per
# operator). 6 leaves enough margin that legitimate 5/10 scripts get
# through when the pool is thin, but cuts the dross.
INTERESTING_THRESHOLD = 6

# Cap on how many candidates we'll judge before giving up on a single
# pipeline run. The score≥7 pool is in the 1000s, so 8 won't drain it;
# 8 is also high enough that a transient run of bland verses can be
# burned through without a human poking the pipeline.
MAX_REJECTIONS_PER_RUN = 8


# ---------------------------------------------------------------------------
#  Schema
# ---------------------------------------------------------------------------

def ensure_columns(conn: sqlite3.Connection) -> None:
    """Add the verdict columns to educational_videos. Idempotent —
    safe to call on every app boot. We add columns (not a new table)
    so the verdict travels with the row through render/upload and
    shows up in the admin UI alongside the other status fields."""
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(educational_videos)").fetchall()}
        if "interestingness_score" not in cols:
            conn.execute("ALTER TABLE educational_videos ADD COLUMN interestingness_score INTEGER")
        if "interestingness_verdict" not in cols:
            conn.execute("ALTER TABLE educational_videos ADD COLUMN interestingness_verdict TEXT")
        if "interestingness_reason" not in cols:
            conn.execute("ALTER TABLE educational_videos ADD COLUMN interestingness_reason TEXT")
        if "interestingness_model" not in cols:
            conn.execute("ALTER TABLE educational_videos ADD COLUMN interestingness_model TEXT")
        conn.commit()
    except Exception as e:
        print(f"[interestingness] could not ensure columns: {e}")


# ---------------------------------------------------------------------------
#  Ollama prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You decide whether a 60-second YouTube Short script about a Quranic verse "
    "is INTERESTING enough to publish. The channel is a general-audience "
    "etymology / translation-nuance show — viewers are curious laypeople who "
    "scroll past anything boring within 2 seconds.\n\n"
    "INTERESTING (score 7-10):\n"
    "  - The reveal FLIPS the picture: conventional reading and the hidden "
    "    reading paint genuinely different scenes, not just better-phrased "
    "    versions of the same scene (e.g. chastity→architecture; sins→tails; "
    "    'guarded'→'fortified like a fortress').\n"
    "  - The hidden reading has concrete sensorial imagery — physical, "
    "    visual, emotional, surprising.\n"
    "  - The stakes are clear: the difference MATTERS for how you understand "
    "    the verse, not just for academic accuracy.\n"
    "  - A casual scroller with zero Quran background would want to keep "
    "    watching after the hook lands.\n\n"
    "BORING (score 1-5):\n"
    "  - The two readings say essentially the same thing with different word "
    "    choices (e.g. 'their fathers'→'their real fathers'; 'guarded'→'kept "
    "    safe'). No reframing, just polish.\n"
    "  - The insight is purely grammatical with no meaning payoff a viewer "
    "    would feel (passive→active, definite→indefinite, perfect→imperfect "
    "    aspect on a routine verb).\n"
    "  - The reveal requires specialist vocabulary or grammar knowledge to "
    "    appreciate.\n"
    "  - The hook lands flat — no concrete image, no stakes, just 'here's a "
    "    subtle nuance'.\n"
    "  - The contrast is real but the script BURIES it in qualifications "
    "    instead of letting it land.\n\n"
    "Be a tough editor. Most signals at score≥7 in the dataset are "
    "legitimately translation-hides moments, but only ~half are 'scroll-"
    "stopping shorts'. Reject the bland ones — the pipeline will pick the "
    "next candidate.\n\n"
    "Return ONLY a JSON object:\n"
    '{\"score\": 1-10, \"verdict\": \"interesting\" | \"skip\", \"reason\": \"≤25 words\"}'
)


def _summarize_for_judge(payload: dict, script: dict) -> str:
    """Pack the script + the underlying signal into a single user
    message. We feed the JUDGE the same surfaces the VIEWER will see:
    the hook (audio open), the conventional + hidden glosses (the pill
    contrast), and the insight (the body of the explanation). We deny
    the judge the departure_notes (the model's own reasoning trace)
    because we want it judging the OUTPUT, not the inputs."""
    chapter = payload.get("chapter") or script.get("chapter") or "?"
    verse = payload.get("verse") or script.get("verse") or "?"
    # The judge needs the verse text so it can tell whether the
    # contrast is genuinely visible IN the Arabic vs an academic
    # over-reading.
    arabic = (payload.get("verse_arabic") or "").strip()
    translation = (payload.get("verse_translation_en") or "").strip()
    hook = (script.get("hook") or "").strip()
    verse_intro = (script.get("verse_intro") or "").strip()
    insight = (script.get("insight") or "").strip()
    close = (script.get("close") or "").strip()
    reveal_conv = (script.get("reveal_conventional") or "").strip()
    reveal_hidden = (script.get("reveal_hidden") or "").strip()
    emphases = script.get("english_emphases") or []
    return (
        f"Quran {chapter}:{verse}\n\n"
        f"Arabic: {arabic}\n"
        f"Conventional English: {translation}\n\n"
        f"--- Generated script (judge this) ---\n"
        f"HOOK (opener, ≤22 words):\n{hook}\n\n"
        f"VERSE_INTRO (sets baseline):\n{verse_intro}\n\n"
        f"INSIGHT (the reveal):\n{insight}\n\n"
        f"CLOSE (payoff line):\n{close}\n\n"
        f"REVEAL CONTRAST PILL — conventional: {reveal_conv!r}\n"
        f"REVEAL CONTRAST PILL — hidden:       {reveal_hidden!r}\n"
        f"Highlighted English phrases on the verse slide: {emphases}\n\n"
        "Score this script on the rubric above. Respond with ONLY the JSON."
    )


# ---------------------------------------------------------------------------
#  Ollama call
# ---------------------------------------------------------------------------

def _strip_to_json(text: str) -> str:
    s = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    s = re.sub(r"^```(?:json)?\s*\n?", "", s.strip())
    s = re.sub(r"\n?```\s*$", "", s.strip())
    return s


def _ollama_prefs(conn) -> dict[str, str]:
    """Pull all ollama_* prefs in one query — the table is a flat
    key→value store, NOT a single row with named columns. (This is
    the same idiom educational_safety.py uses; the artifact resolver
    in educational_render_remotion.py originally got this wrong and
    silently fell through to the localhost fallback on prod.)"""
    out: dict[str, str] = {}
    for r in conn.execute(
        "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
    ).fetchall():
        out[r["key"]] = r["value"]
    return out


def _call_ollama(
    *,
    user_message: str,
    base_url: str,
    model: str,
    api_key: str,
    timeout: int = 90,
) -> tuple[str, int, str, str]:
    """Returns (verdict, score, reason, model_used). verdict is
    'interesting' / 'skip' / 'unknown'. 'unknown' on any failure —
    caller decides whether to treat it as pass or fail (we recommend
    pass: be permissive when the judge is flapping)."""
    if not model:
        return "unknown", 0, "no ollama model configured", model or ""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
                # qwen3 thinks by default; we don't need the chain-of-
                # thought, and "think": False is much faster.
                "think": False,
            },
            timeout=timeout,
        )
    except requests.RequestException as e:
        return "unknown", 0, f"transport: {e}"[:200], model
    if resp.status_code != 200:
        return "unknown", 0, f"http {resp.status_code}: {resp.text[:160]}", model
    content = (resp.json().get("message") or {}).get("content", "")
    s = _strip_to_json(content)
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        return "unknown", 0, f"no json in response: {s[:160]}", model
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return "unknown", 0, f"bad json: {m.group()[:160]}", model
    verdict = (obj.get("verdict") or "").strip().lower()
    if verdict not in ("interesting", "skip"):
        return "unknown", 0, f"unexpected verdict: {verdict!r}", model
    score = obj.get("score")
    try:
        score_i = int(score)
    except (TypeError, ValueError):
        score_i = 0
    reason = (obj.get("reason") or "").strip()[:300]
    return verdict, score_i, reason, model


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def judge_script(
    conn: sqlite3.Connection,
    payload: dict,
    script: dict,
) -> dict:
    """Score a generated script. Returns:
        {
            'verdict':  'interesting' | 'skip' | 'unknown',
            'score':    int 0-10  (0 when unknown),
            'reason':   str,
            'model':    str,
            'pass':     bool   — caller-facing convenience: True if
                                 verdict == 'interesting' AND
                                 score >= INTERESTING_THRESHOLD, OR
                                 verdict == 'unknown' (permissive).
        }
    """
    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    # Same model resolution as safety: prefer the dedicated metadata
    # model, fall back to the general ollama_model.
    model = (
        prefs.get("ollama_metadata_model")
        or prefs.get("ollama_model")
        or ""
    ).strip()
    api_key = prefs.get("ollama_api_key") or ""

    user_msg = _summarize_for_judge(payload, script)
    verdict, score, reason, model_used = _call_ollama(
        user_message=user_msg,
        base_url=base_url, model=model, api_key=api_key,
    )

    if verdict == "unknown":
        # Permissive: judge was unreachable / malformed → let it through.
        # We'd rather publish one bland video than block the pipeline
        # because Ollama Cloud rate-limited or the model produced bad
        # JSON. The operator still sees the row in the admin UI.
        pass_ = True
    else:
        pass_ = (verdict == "interesting") and (score >= INTERESTING_THRESHOLD)

    return {
        "verdict": verdict,
        "score": score,
        "reason": reason,
        "model": model_used,
        "pass": pass_,
    }
