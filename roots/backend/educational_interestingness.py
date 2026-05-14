"""Interestingness gate for ALL the channel's pipelines.

After a script (or, for recitations, a passage) is selected, this
judge decides whether the candidate is interesting enough to publish
as a YouTube Short. If not, the pipeline marks the row
'rejected_uninteresting' and picks the next candidate.

Why this exists: operator feedback after the 33:5 translation_hides
render ("uninteresting") and the 'Why Himar Means Red In The Quran'
word_origins upload ("not interesting at all, will likely lose
subscribers"). Both passed the upstream signal/safety filters but
landed flat with viewers. Publishing bland shorts actively hurts
the channel — better to skip and let the pipeline land on a verse
where the content stops the scroll.

Each pipeline type has its OWN "interesting" criteria:

  - translation_hides: does the conventional vs hidden reading flip
    the picture (chastity→architecture; sins→tails)? Or is it just
    a synonym swap?

  - word_origins: does the etymology change how you read a familiar
    verse or concept (religion←debt; heart←inside-out)? Or is it a
    linguistic curiosity (animal-named-for-its-color) with no payoff
    for understanding the Quran?

  - grammar_insights: does the grammatical move change the MEANING
    of a famous verse (passive→active reframing who's in control;
    perfect tense for future events)? Or is it a routine agreement
    detail that only specialists care about?

  - recitation: is this passage striking on its own as a 60-second
    standalone clip? Or is it a transitional/legalistic verse that
    only lands inside a longer reading? Judged at PASSAGE-SELECTION
    time, before we burn TTS + render on it.

Public surface:
    ensure_columns(conn)
        Idempotent ALTER for the verdict columns on educational_videos
        AND admin_pipeline_videos. Called once on app boot.

    judge_script(conn, payload, script, vtype) -> dict
        Educational pipelines (word_origins, translation_hides,
        grammar_insights).
        {verdict, score, reason, model, pass}

    judge_passage(conn, chapter, ayah_start, ayah_end, *, is_arabic) -> dict
        Recitation pipeline. Reads the verse text from the DB and
        scores the passage. Same return shape as judge_script.

'unknown' on any Ollama failure — callers treat as 'interesting'
(permissive default: rather publish one bland video than starve the
pipeline when Ollama is flapping).
"""

from __future__ import annotations

import html
import json
import re
import sqlite3

import requests


# Threshold at which we accept. Tuned against operator-flagged
# references — 33:5 ("uninteresting") and 2:259-himar ("not
# interesting at all") need to be cut; 66:12 and 25:58 need to be
# kept. The user's followup explicitly warned that bad uploads
# COST subscribers, so the bar is intentionally above the median.
INTERESTING_THRESHOLD = 6

# Cap on how many candidates we'll judge before giving up on a
# single pipeline run. With ~1000+ score≥7 signals in the pool, 8
# attempts is plenty without thrashing.
MAX_REJECTIONS_PER_RUN = 8


# ---------------------------------------------------------------------------
#  Schema
# ---------------------------------------------------------------------------

def ensure_columns(conn: sqlite3.Connection) -> None:
    """Add the verdict columns to BOTH video tables. Idempotent —
    safe to call on every app boot. The columns travel with the row
    through render/upload so the admin UI can show why a candidate
    was skipped, and an operator can manually re-queue if they
    disagree with the judge."""
    for table in ("educational_videos", "admin_pipeline_videos"):
        try:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if "interestingness_score" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN interestingness_score INTEGER")
            if "interestingness_verdict" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN interestingness_verdict TEXT")
            if "interestingness_reason" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN interestingness_reason TEXT")
            if "interestingness_model" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN interestingness_model TEXT")
            conn.commit()
        except Exception as e:
            print(f"[interestingness] could not ensure columns on {table}: {e}")


# ---------------------------------------------------------------------------
#  System prompts — one per pipeline type
# ---------------------------------------------------------------------------

# Shared prelude — every prompt starts with these editorial values so
# the LLM optimizes for the same viewer regardless of pipeline.
_PRELUDE = (
    "You decide whether a 60-second YouTube Short about a Quranic verse "
    "is INTERESTING enough to publish. The channel is a general-audience "
    "etymology / Arabic-nuance show — viewers are curious laypeople with "
    "zero Quranic background who scroll past anything boring within 2 "
    "seconds. Publishing flat content actively LOSES subscribers, so be "
    "a tough editor: skip the bland ones and the pipeline will pick the "
    "next candidate.\n\n"
    "Return ONLY a JSON object:\n"
    '{"score": 1-10, "verdict": "interesting" | "skip", "reason": "≤25 words"}\n\n'
)


_PROMPT_TRANSLATION_HIDES = _PRELUDE + (
    "GENRE: Translation Hides — reveals that the conventional English "
    "translation of a Quranic word/phrase flattens a more vivid Arabic "
    "meaning.\n\n"
    "INTERESTING (score 7-10):\n"
    "  - The reveal FLIPS the picture: conventional reading and the "
    "    hidden reading paint genuinely different scenes (chastity→"
    "    architecture; sins→tails; 'take control'→'seize by the palate').\n"
    "  - The hidden reading has CONCRETE sensorial imagery — physical, "
    "    visual, emotional. Not abstract refinements.\n"
    "  - The stakes are clear: the difference MATTERS for how you "
    "    read the verse, not just for academic accuracy.\n"
    "  - A casual scroller would FEEL the contrast in the first 5s.\n\n"
    "BORING (score 1-5):\n"
    "  - The two readings say essentially the same thing with different "
    "    word choices ('their fathers'→'their real fathers'; 'guarded'"
    "    →'kept safe'). No reframing, just polish.\n"
    "  - The insight is grammatical with no meaning payoff (passive→"
    "    active, definite→indefinite, perfect aspect on a routine verb).\n"
    "  - The reveal requires specialist vocabulary to appreciate.\n"
    "  - The hook lands flat — no concrete image, no stakes.\n"
)


_PROMPT_WORD_ORIGINS = _PRELUDE + (
    "GENRE: Word Origins — short essays on an Arabic root's etymology, "
    "Semitic cognates, and how the Quran uses it. The 'tidbit_about_'* "
    "fields ARE the body of the video; hook is the opener.\n\n"
    "INTERESTING (score 7-10):\n"
    "  - The etymology REFRAMES a familiar Quranic concept the audience "
    "    cares about (deen←debt, qalb←inside-out, dhanb←tail, isim←raised).\n"
    "  - The root does THEMATIC work across the Quran — same root popping "
    "    up in surprising verses in a way that becomes a unifying image.\n"
    "  - The cognate evidence is striking, not just 'this also exists in "
    "    Akkadian.' E.g., the cognate chain tells a story about how human "
    "    cultures saw the concept.\n"
    "  - A casual scroller would walk away thinking 'I'll never read THAT "
    "    verse the same way again.'\n\n"
    "BORING (score 1-5):\n"
    "  - Animal-named-for-its-color etymologies (himar←red; raven←black) "
    "    UNLESS the reframe actually changes a famous verse. "
    "    Cute trivia ≠ scroll-stopping payoff. Operator example: 'Why "
    "    Himar Means Red In The Quran' — the etymology is real, but "
    "    donkey-color is not a topic anyone scrolls for.\n"
    "  - Pure linguistic curiosities ('this Akkadian word also exists') "
    "    with no payoff for understanding the Quran.\n"
    "  - Connections that only matter to comparative semiticists.\n"
    "  - The Quran-usage section is generic ('used many times in the "
    "    Quran to mean X') without a single vivid example.\n"
    "  - The hook ('Did you know X means Y?') lands flat because X "
    "    isn't a concept the audience cares about (animal names, "
    "    obscure objects).\n"
)


_PROMPT_GRAMMAR_INSIGHTS = _PRELUDE + (
    "GENRE: Grammar Insights — a specific grammatical move in a verse "
    "and what it does to the meaning.\n\n"
    "INTERESTING (score 7-10):\n"
    "  - The grammar move CHANGES the meaning of a verse a viewer might "
    "    quote (passive vs active reframing who's in control; perfect "
    "    tense used for a future event making prophecy a fait accompli; "
    "    definiteness contrast revealing hierarchy).\n"
    "  - The example verse is famous or rhetorically powerful.\n"
    "  - The audience can FEEL the difference without grammar training "
    "    — 'she is the sender, they are the sent' encodes power "
    "    dynamics in word form.\n"
    "  - The additional_examples (if any) extend the same move to "
    "    other powerful verses, not just repeat the point.\n\n"
    "BORING (score 1-5):\n"
    "  - Routine agreement, case endings, number-agreement details.\n"
    "  - Subtle morphology with no semantic payoff the viewer feels.\n"
    "  - Examples on obscure verses no one quotes.\n"
    "  - 'Did you know there's a perfect tense / dual / energetic here' "
    "    — the answer is no, the viewer doesn't care about the FORM "
    "    unless the form changes the MEANING.\n"
    "  - The insight is a re-statement of the verse with grammar "
    "    vocabulary sprinkled in.\n"
)


_PROMPT_RECITATION = _PRELUDE + (
    "GENRE: Quranic Passage Recitation — a 1-8 verse passage read with "
    "translation overlay. NO etymology, NO grammar — the content IS the "
    "verse itself. You're judging WHETHER THE PASSAGE LANDS ON ITS OWN.\n\n"
    "INTERESTING (score 7-10):\n"
    "  - A striking, vivid passage with a clear emotional or imagistic "
    "    arc (the parable of the gold pieces; the seven heavens; the "
    "    descent of the angels; the description of the heart's veil).\n"
    "  - The passage stands alone: a viewer with no Quran background "
    "    can follow it and feel something in 60 seconds.\n"
    "  - The translation reads as poetry / parable / striking imagery, "
    "    not as legal prose.\n\n"
    "BORING (score 1-5):\n"
    "  - Transitional verses, narrative middle-bits that need surrounding "
    "    context to make sense.\n"
    "  - Legal / procedural content (inheritance shares, divorce rules, "
    "    fasting exemptions) — even when uncontroversial, these don't "
    "    land as standalone 60s shorts.\n"
    "  - Repetition-heavy passages that read flat in translation.\n"
    "  - Polemic / refutation verses that require knowing what's being "
    "    refuted to make sense.\n"
    "  - Passages that are theologically routine without striking "
    "    imagery (generic 'God is forgiving and merciful' tags).\n"
)


def _prompt_for(vtype: str, conn: sqlite3.Connection | None = None) -> str:
    """Pick the right system prompt for the candidate's pipeline type
    and append the latest performance-driven lessons (when available)
    so the judge stays calibrated to what actually engages viewers on
    YouTube. The hand-written rubric stays on top — editorial values
    take precedence over data-derived trends."""
    base = {
        "translation_hides": _PROMPT_TRANSLATION_HIDES,
        "word_origins": _PROMPT_WORD_ORIGINS,
        "grammar_insights": _PROMPT_GRAMMAR_INSIGHTS,
        "recitation": _PROMPT_RECITATION,
    }.get(vtype, _PROMPT_TRANSLATION_HIDES)
    if conn is None:
        return base
    try:
        import educational_lessons as _lessons
        section = _lessons.lesson_section_for_prompt(conn, vtype)
        if section:
            return base + section
    except Exception as e:
        # Never let a lessons-module failure block the judge — the
        # base rubric is enough to operate; we just lose the data-
        # informed refinement until the module can be loaded again.
        print(f"[interestingness] lessons-section skipped: {e}")
    return base


# ---------------------------------------------------------------------------
#  User-message builders — one per pipeline type
# ---------------------------------------------------------------------------

def _summarize_translation_hides(payload: dict, script: dict) -> str:
    chapter = payload.get("chapter") or script.get("chapter") or "?"
    verse = payload.get("verse") or script.get("verse") or "?"
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
        f"--- Generated script ---\n"
        f"HOOK: {hook}\n\n"
        f"VERSE_INTRO: {verse_intro}\n\n"
        f"INSIGHT (the reveal): {insight}\n\n"
        f"CLOSE: {close}\n\n"
        f"Reveal pill — conventional: {reveal_conv!r}\n"
        f"Reveal pill — hidden:       {reveal_hidden!r}\n"
        f"Highlighted phrases: {emphases}\n\n"
        "Score this script. Respond with ONLY the JSON."
    )


def _summarize_word_origins(payload: dict, script: dict) -> str:
    chapter = payload.get("chapter") or script.get("chapter") or "?"
    verse = payload.get("verse") or script.get("verse") or "?"
    root_ar = (payload.get("root_ar") or "").strip()
    root_bw = (payload.get("root_bw") or "").strip()
    hook = (script.get("hook") or "").strip()
    tidbit_root = (script.get("tidbit_about_root") or "").strip()
    tidbit_quran = (script.get("tidbit_about_quran_usage") or "").strip()
    tidbit_semitic = (script.get("tidbit_about_semitic") or "").strip()
    close = (script.get("close") or "").strip()
    languages = script.get("languages_referenced") or []
    verses_referenced = script.get("selected_verse_refs") or []
    return (
        f"Anchor verse: Quran {chapter}:{verse}\n"
        f"Arabic root: {root_ar!r} (Buckwalter: {root_bw!r})\n"
        f"Cognate languages referenced: {languages}\n"
        f"Other verses cited on-screen: {verses_referenced}\n\n"
        f"--- Generated script ---\n"
        f"HOOK (opener): {hook}\n\n"
        f"ROOT ETYMOLOGY: {tidbit_root}\n\n"
        f"QURAN USAGE: {tidbit_quran}\n\n"
        f"SEMITIC COGNATES: {tidbit_semitic}\n\n"
        f"CLOSE: {close}\n\n"
        "Score this Word Origins script. The body of the video is the "
        "three tidbit sections — focus on whether THOSE land. Respond "
        "with ONLY the JSON."
    )


def _summarize_grammar_insights(payload: dict, script: dict) -> str:
    chapter = payload.get("chapter") or script.get("chapter") or "?"
    verse = payload.get("verse") or script.get("verse") or "?"
    arabic = (payload.get("verse_arabic") or "").strip()
    translation = (payload.get("verse_translation_en") or "").strip()
    hook = (script.get("hook") or "").strip()
    verse_intro = (script.get("verse_intro") or "").strip()
    insight = (script.get("insight") or "").strip()
    close = (script.get("close") or "").strip()
    emphases = script.get("english_emphases") or []
    examples = script.get("additional_examples") or []
    ex_lines = []
    for e in examples[:3]:
        if isinstance(e, dict):
            ex_lines.append(
                f"  - Quran {e.get('chapter')}:{e.get('verse')}: "
                f"{(e.get('narration') or '')[:200]}"
            )
    examples_str = "\n".join(ex_lines) if ex_lines else "(none)"
    return (
        f"Quran {chapter}:{verse}\n\n"
        f"Arabic: {arabic}\n"
        f"English: {translation}\n\n"
        f"--- Generated script ---\n"
        f"HOOK: {hook}\n\n"
        f"VERSE_INTRO: {verse_intro}\n\n"
        f"INSIGHT (the grammar move + its meaning payoff): {insight}\n\n"
        f"CLOSE: {close}\n\n"
        f"Highlighted phrases: {emphases}\n"
        f"Additional example verses:\n{examples_str}\n\n"
        "Score this Grammar Insights script. The key question: does the "
        "grammar move change the MEANING in a way a layperson can feel? "
        "Or is it a form-level subtlety? Respond with ONLY the JSON."
    )


def _summarize_recitation(arabic: str, translation: str,
                          chapter: int, ayah_start: int, ayah_end: int) -> str:
    span = f"{chapter}:{ayah_start}" if ayah_start == ayah_end else f"{chapter}:{ayah_start}-{ayah_end}"
    return (
        f"Passage: Quran {span}\n\n"
        f"Arabic:\n{arabic}\n\n"
        f"English translation:\n{translation}\n\n"
        "Judge: as a standalone 60s short with no surrounding context, "
        "would this passage stop the scroll? Or does it need explanation "
        "/ before/after verses / specialist context to land? Respond "
        "with ONLY the JSON."
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
    key→value store, NOT a single row with named columns."""
    out: dict[str, str] = {}
    for r in conn.execute(
        "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
    ).fetchall():
        out[r["key"]] = r["value"]
    return out


def _call_ollama(
    *,
    system_prompt: str,
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
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
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


def _resolve(conn, system_prompt: str, user_message: str) -> dict:
    """Shared dispatcher: read prefs, call Ollama, package result."""
    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (
        prefs.get("ollama_metadata_model")
        or prefs.get("ollama_model")
        or ""
    ).strip()
    api_key = prefs.get("ollama_api_key") or ""
    verdict, score, reason, model_used = _call_ollama(
        system_prompt=system_prompt, user_message=user_message,
        base_url=base_url, model=model, api_key=api_key,
    )
    if verdict == "unknown":
        # Permissive: judge unreachable / malformed → let it through.
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


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def judge_script(
    conn: sqlite3.Connection,
    payload: dict,
    script: dict,
    vtype: str,
) -> dict:
    """Judge a generated educational script. vtype is one of
    'word_origins' / 'translation_hides' / 'grammar_insights' — each
    routes to its own prompt + summary builder."""
    system_prompt = _prompt_for(vtype, conn)
    if vtype == "word_origins":
        user_msg = _summarize_word_origins(payload, script)
    elif vtype == "grammar_insights":
        user_msg = _summarize_grammar_insights(payload, script)
    else:
        user_msg = _summarize_translation_hides(payload, script)
    return _resolve(conn, system_prompt, user_msg)


def judge_passage(
    conn: sqlite3.Connection,
    chapter: int,
    ayah_start: int,
    ayah_end: int,
) -> dict:
    """Judge a recitation passage by fetching the verse text directly
    from the DB. Returns the same shape as judge_script."""
    rows = conn.execute(
        "SELECT verse, text_uthmani FROM verses WHERE chapter = ? "
        "AND verse BETWEEN ? AND ? ORDER BY verse",
        (chapter, ayah_start, ayah_end),
    ).fetchall()
    arabic_lines = []
    for r in rows:
        arabic_lines.append(f"  {chapter}:{r['verse']}  {r['text_uthmani']}")
    arabic = "\n".join(arabic_lines)
    trans_rows = conn.execute(
        "SELECT verse, text_en FROM translations WHERE chapter = ? "
        "AND verse BETWEEN ? AND ? ORDER BY verse",
        (chapter, ayah_start, ayah_end),
    ).fetchall()
    trans_lines = []
    for r in trans_rows:
        clean = html.unescape(re.sub(r"<[^>]+>", "", r["text_en"] or ""))
        trans_lines.append(f"  {chapter}:{r['verse']}  {clean}")
    translation = "\n".join(trans_lines)
    if not arabic and not translation:
        return {"verdict": "unknown", "score": 0,
                "reason": "no verse data", "model": "", "pass": True}
    user_msg = _summarize_recitation(arabic, translation, chapter, ayah_start, ayah_end)
    return _resolve(conn, _prompt_for("recitation", conn), user_msg)
