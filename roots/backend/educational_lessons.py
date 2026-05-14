"""Performance-driven lessons for the interestingness judge.

A cron task that:
  1. Reads YouTube stats per pipeline type (recitation, word_origins,
     translation_hides, grammar_insights).
  2. Ranks each pipeline's published videos by like-rate (likes/views)
     among videos with enough post-upload time + view volume to be
     past cold-start noise.
  3. Sends the top + bottom quartile, the judge's verdicts on
     rejected videos, and the verse/script content to Ollama Cloud,
     asking for 3-6 concrete lessons per pipeline type — each lesson
     must cite the specific video IDs that motivated it.
  4. Validates that every cited video ID exists in the DB (catches
     hallucinations) and stores the lessons as the new active
     generation. Operator can toggle individual lessons off or add
     manual ones via the admin UI.

The active lessons are appended to the judge's system prompt at
candidate-evaluation time, so the judge's editorial calls get tuned
by real YouTube performance over time.

Design choices (per operator preference 2026-05-14):
  * AUTO-APPROVE: lessons go live immediately on cron completion. No
    review queue. Worst case is the judge gets briefly off-tone; the
    operator can disable individual lessons via the UI.
  * Include past REJECTED videos in the analysis: their verdict +
    reason tell the LLM what the judge thought BORING; their (lack
    of) YouTube performance confirms or contradicts the rubric.
  * EXCLUDE comments from the engagement signal: Quran channel
    comments skew theological/contentious and don't track quality.
  * Per-pipeline cohorts, not cross-pipeline: a recitation's 6.1%
    avg like-rate vs an educational's 2.8% is a baseline difference,
    not a signal that recitations are "better."

Public surface:
    ensure_tables(conn)
        Idempotent ALTERs / CREATE TABLE for judge_lessons and the
        admin_preferences keys (auto-refresh toggle, interval, last
        run). Called from boot.

    current_lessons_for(conn, pipeline_type) -> list[dict]
        Active lessons for a pipeline (or 'all') — used by the judge.

    lesson_section_for_prompt(conn, pipeline_type) -> str
        Formatted markdown section to append to the judge's system
        prompt. Empty string when no active lessons exist.

    refresh_lessons(conn, *, only_type=None, force=False) -> dict
        Run the analyzer. Returns a summary dict
        {generation_id, per_type: {type: {kept: int, rejected: int}}}.

    should_refresh(conn) -> bool
        True when auto-refresh is enabled AND the next-run time has
        passed. Called from the scheduler tick.

The Ollama call uses the SAME admin_preferences keys as the
interestingness judge: ollama_base_url, ollama_api_key, and
ollama_metadata_model (or ollama_model fallback).
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import requests


# ---------------------------------------------------------------------------
# Tunables (deliberately broad — operator can change via admin_preferences
# without a code deploy; values here are just safe defaults).
# ---------------------------------------------------------------------------

# Minimum days since upload before a video can feed into the analyzer.
# YouTube's algorithm takes about a week to settle for shorts.
DEFAULT_MIN_AGE_DAYS = 7

# Minimum views needed for a video's like-rate to be a meaningful
# signal. Below this, like-rate is dominated by friends-of-the-channel
# noise. Raise to 50 if the channel is getting more traction; lower to
# 15 in the early days.
DEFAULT_MIN_VIEWS = 30

# Max lessons we'll keep per pipeline type. Keeps the judge prompt
# manageable AND makes it harder for one bad cron run to fully
# overwrite editorial values.
MAX_LESSONS_PER_TYPE = 6

# Cron interval. 3 days lines up with the operator's stated cadence.
DEFAULT_REFRESH_INTERVAL_DAYS = 3

# Which `educational_videos.type` values count as our educational
# pipelines.
EDUCATIONAL_TYPES = ("word_origins", "translation_hides", "grammar_insights")
PIPELINE_TYPES = ("recitation",) + EDUCATIONAL_TYPES


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def ensure_tables(conn: sqlite3.Connection) -> None:
    """Create judge_lessons and seed the admin_preferences keys that
    control the cron. Idempotent — safe on every boot."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS judge_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_type TEXT NOT NULL,         -- 'word_origins'|'translation_hides'|'grammar_insights'|'recitation'|'all'
            lesson TEXT NOT NULL,                -- one-sentence directive
            evidence_video_ids TEXT,             -- JSON array of source-table refs
            generation_id INTEGER,               -- groups lessons from one cron run
            source TEXT NOT NULL DEFAULT 'auto', -- 'auto' | 'manual'
            active INTEGER NOT NULL DEFAULT 1,   -- operator can toggle
            operator_note TEXT,                  -- free-text annotation
            generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lesson_type_active "
        "ON judge_lessons(pipeline_type, active)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lesson_generation "
        "ON judge_lessons(generation_id)"
    )

    # Seed admin_preferences keys with defaults if missing. Use
    # INSERT OR IGNORE so we don't clobber operator changes.
    defaults = {
        "lessons_auto_refresh_enabled": "1",
        "lessons_refresh_interval_days": str(DEFAULT_REFRESH_INTERVAL_DAYS),
        "lessons_min_age_days": str(DEFAULT_MIN_AGE_DAYS),
        "lessons_min_views": str(DEFAULT_MIN_VIEWS),
        # 'lessons_last_refresh_at' is set when the cron runs; absence
        # means "never run."
    }
    for k, v in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO admin_preferences (key, value) VALUES (?, ?)",
            (k, v),
        )
    conn.commit()


def _pref(conn, key: str, default: str | None = None) -> str | None:
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else default


def _pref_int(conn, key: str, default: int) -> int:
    try:
        return int(_pref(conn, key, str(default)) or default)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Reading lessons (called by the judge prompt builder)
# ---------------------------------------------------------------------------

def current_lessons_for(conn: sqlite3.Connection, pipeline_type: str) -> list[dict]:
    """Active lessons for a pipeline type, plus any 'all' lessons that
    apply to every type. Returns up to MAX_LESSONS_PER_TYPE rows."""
    rows = conn.execute(
        """
        SELECT id, pipeline_type, lesson, evidence_video_ids, source, generated_at
        FROM judge_lessons
        WHERE active = 1
          AND pipeline_type IN (?, 'all')
        ORDER BY
          -- manual lessons rank above auto so the operator's note
          -- always lands when the cap is tight
          CASE source WHEN 'manual' THEN 0 ELSE 1 END,
          generated_at DESC
        LIMIT ?
        """,
        (pipeline_type, MAX_LESSONS_PER_TYPE),
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "pipeline_type": r["pipeline_type"],
            "lesson": r["lesson"],
            "evidence_video_ids": json.loads(r["evidence_video_ids"] or "[]"),
            "source": r["source"],
            "generated_at": r["generated_at"],
        })
    return out


def lesson_section_for_prompt(conn: sqlite3.Connection, pipeline_type: str) -> str:
    """Markdown section to append to the judge's system prompt.
    Empty string when there are no active lessons (so the judge
    falls back to the hand-written rubric alone)."""
    lessons = current_lessons_for(conn, pipeline_type)
    if not lessons:
        return ""
    last_run = _pref(conn, "lessons_last_refresh_at")
    when = f" (last refreshed {last_run.split('T')[0]})" if last_run else ""
    lines = [
        "",
        f"RECENT PERFORMANCE INSIGHTS{when}:",
        "These were extracted from real YouTube engagement on past "
        "uploads. They REFINE the rubric above; the hand-written "
        "criteria still win on any conflict.",
    ]
    for lsn in lessons:
        marker = "★" if lsn["source"] == "manual" else "•"
        lines.append(f"  {marker} {lsn['lesson']}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Cron entry point
# ---------------------------------------------------------------------------

def should_refresh(conn: sqlite3.Connection) -> bool:
    """True when auto-refresh is enabled and the configured interval
    has elapsed since the last run (or there's never been one)."""
    enabled = _pref(conn, "lessons_auto_refresh_enabled", "1")
    if str(enabled).lower() not in ("1", "true", "yes", "on"):
        return False
    interval_days = _pref_int(conn, "lessons_refresh_interval_days", DEFAULT_REFRESH_INTERVAL_DAYS)
    last = _pref(conn, "lessons_last_refresh_at")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
    except Exception:
        return True
    return datetime.now(timezone.utc) - last_dt >= timedelta(days=interval_days)


def refresh_lessons(
    conn: sqlite3.Connection,
    *,
    only_type: str | None = None,
    force: bool = False,
) -> dict:
    """Run the analyzer. Returns a summary dict.

    Args:
      only_type: limit to a single pipeline type (debug / manual run)
      force:     ignore the should_refresh schedule check
    """
    if not force and not should_refresh(conn):
        return {"ok": False, "reason": "not yet due"}

    types_to_run = (only_type,) if only_type else PIPELINE_TYPES
    generation_id = _next_generation_id(conn)
    summary: dict = {"ok": True, "generation_id": generation_id, "per_type": {}}

    for ptype in types_to_run:
        try:
            res = _refresh_one_type(conn, ptype, generation_id)
            summary["per_type"][ptype] = res
        except Exception as e:
            print(f"[lessons] refresh failed for {ptype}: {e}")
            summary["per_type"][ptype] = {"error": str(e)[:300]}

    # Mark last-run timestamp regardless of per-type success — if Ollama
    # is broken across the board the operator will see no new lessons
    # and can investigate; we don't want a thrashing retry loop.
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
        "VALUES ('lessons_last_refresh_at', ?, CURRENT_TIMESTAMP)",
        (now,),
    )
    conn.commit()
    summary["last_refresh_at"] = now
    return summary


def _next_generation_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(generation_id), 0) + 1 FROM judge_lessons"
    ).fetchone()
    return int(row[0])


def _refresh_one_type(
    conn: sqlite3.Connection,
    ptype: str,
    generation_id: int,
) -> dict:
    """Build prompt for one pipeline type, call Ollama, validate, store."""
    cohort = _build_cohort(conn, ptype)
    if not cohort.get("top") and not cohort.get("rejected"):
        return {"kept": 0, "rejected": 0, "skipped": True,
                "reason": "no data — need more uploads"}

    prompt = _build_analyzer_prompt(ptype, cohort)
    raw = _call_ollama_analyzer(conn, prompt)
    if not raw:
        return {"kept": 0, "rejected": 0, "skipped": True,
                "reason": "ollama call failed"}

    proposed = _parse_lessons(raw, ptype)
    valid_ids = cohort.get("valid_video_ids") or set()
    accepted, dropped = _validate_lessons(proposed, valid_ids)

    # Retire previous auto lessons for this type. Manual lessons are
    # preserved (the operator's voice always carries forward).
    conn.execute(
        "UPDATE judge_lessons SET active = 0 "
        "WHERE pipeline_type = ? AND source = 'auto'",
        (ptype,),
    )
    for lsn in accepted[:MAX_LESSONS_PER_TYPE]:
        conn.execute(
            """
            INSERT INTO judge_lessons
              (pipeline_type, lesson, evidence_video_ids,
               generation_id, source, active)
            VALUES (?, ?, ?, ?, 'auto', 1)
            """,
            (
                ptype,
                lsn["lesson"],
                json.dumps(lsn["evidence_video_ids"]),
                generation_id,
            ),
        )
    conn.commit()
    return {
        "kept": min(len(accepted), MAX_LESSONS_PER_TYPE),
        "rejected": len(dropped),
        "rejected_reasons": dropped[:5],
    }


# ---------------------------------------------------------------------------
# Cohort building — what we feed the analyzer
# ---------------------------------------------------------------------------

def _build_cohort(conn: sqlite3.Connection, ptype: str) -> dict:
    """Pull recent uploads of this pipeline type plus the judge's
    rejection notes for the same type. Returns:
      {
        top:       [video summaries, ranked by like-rate, top quartile],
        bottom:    [video summaries, bottom quartile],
        rejected:  [judge-rejected candidates with reason],
        valid_video_ids: set of ID strings that lessons may cite,
      }
    """
    min_age = _pref_int(conn, "lessons_min_age_days", DEFAULT_MIN_AGE_DAYS)
    min_views = _pref_int(conn, "lessons_min_views", DEFAULT_MIN_VIEWS)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=min_age)).strftime("%Y-%m-%d")

    if ptype == "recitation":
        rows = _published_recitations(conn, cutoff_date=cutoff, min_views=min_views)
        rejected = _rejected_recitations(conn)
        ref_prefix = "rec"
    else:
        rows = _published_educational(conn, ptype, cutoff_date=cutoff, min_views=min_views)
        rejected = _rejected_educational(conn, ptype)
        ref_prefix = "edu"

    valid_ids: set[str] = set()
    for r in rows:
        valid_ids.add(f"{ref_prefix}:{r['id']}")
    for r in rejected:
        valid_ids.add(f"{ref_prefix}:{r['id']}")

    # Rank by like-rate. Tie-break by views desc so a 10-views-10-likes
    # video doesn't beat a 200-views-200-likes one.
    def _like_rate(r):
        v = max(1, r["views"] or 0)
        return (r["likes"] or 0) / v
    rows = sorted(rows, key=lambda r: (-_like_rate(r), -(r["views"] or 0)))

    n = len(rows)
    if n == 0:
        top, bottom = [], []
    elif n <= 4:
        # Pool too small for quartiles — feed all as "top," nothing as bottom.
        top = rows[:]
        bottom = []
    else:
        q = max(1, n // 4)
        top = rows[:q]
        bottom = rows[-q:]
    return {
        "top": top,
        "bottom": bottom,
        "rejected": rejected[:12],  # cap so prompt stays small
        "valid_video_ids": valid_ids,
        "total_pool": n,
    }


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _published_educational(
    conn, vtype: str, *, cutoff_date: str, min_views: int,
) -> list[dict]:
    """Educational rows that have been published long enough + got
    enough views to feed into the analyzer."""
    cur = conn.execute(
        """
        SELECT
          ev.id AS id,
          ev.chapter AS chapter,
          ev.verse AS verse,
          ev.script_json AS script_json,
          ev.youtube_title AS internal_title,
          ev.interestingness_score AS judge_score,
          ev.interestingness_verdict AS judge_verdict,
          ev.interestingness_reason AS judge_reason,
          yv.title AS published_title,
          yv.views AS views,
          yv.likes AS likes,
          yv.published_at AS published_at
        FROM educational_videos ev
        JOIN youtube_video_stats yv
          ON yv.source_table = 'educational_videos' AND yv.source_id = ev.id
        WHERE ev.type = ?
          AND yv.snapshot_date = (
            SELECT MAX(snapshot_date) FROM youtube_video_stats yv2
            WHERE yv2.youtube_video_id = yv.youtube_video_id
          )
          AND yv.views >= ?
          AND (yv.published_at IS NULL OR yv.published_at < ?)
        """,
        (vtype, min_views, cutoff_date),
    ).fetchall()
    return [dict(r) for r in cur]


def _rejected_educational(conn, vtype: str) -> list[dict]:
    """Rows the judge rejected — their verdicts feed the analyzer so
    it can confirm or contradict the rubric. We don't have YouTube
    stats on these (never published), but the judge's reason itself
    is what the analyzer learns from."""
    cur = conn.execute(
        """
        SELECT id, chapter, verse, interestingness_score AS judge_score,
               interestingness_verdict AS judge_verdict,
               interestingness_reason AS judge_reason,
               script_json
        FROM educational_videos
        WHERE type = ? AND status = 'rejected_uninteresting'
        ORDER BY id DESC LIMIT 12
        """,
        (vtype,),
    ).fetchall()
    return [dict(r) for r in cur]


def _passage_ref_from_verse_data(verse_data_json: str | None) -> tuple[int | None, int | None, int | None, str]:
    """Recitations don't store chapter/ayah as columns — they live
    inside the verse_data JSON blob, one row per verse in the passage.
    Pull the first verse's chapter and the min/max ayah numbers, plus
    the polished_text concatenation (first 200 chars) so the analyzer
    sees what the viewer would actually see in the recitation.
    Returns (chapter, ayah_start, ayah_end, body_excerpt)."""
    if not verse_data_json:
        return (None, None, None, "")
    try:
        rows = json.loads(verse_data_json)
    except json.JSONDecodeError:
        return (None, None, None, "")
    if not isinstance(rows, list) or not rows:
        return (None, None, None, "")
    chap = rows[0].get("chapter")
    ayahs = [r.get("verse") for r in rows if isinstance(r, dict)]
    ayahs = [a for a in ayahs if isinstance(a, int)]
    start = min(ayahs) if ayahs else None
    end = max(ayahs) if ayahs else None
    # Concatenated polished_text — that's what the recitation subtitles
    # actually show on screen, so it's the right surface for the analyzer
    # to judge "did this passage land."
    body_parts = []
    for r in rows[:8]:
        if not isinstance(r, dict):
            continue
        t = (r.get("polished_text") or r.get("original_translation") or "").strip()
        if t:
            body_parts.append(t)
    body = " / ".join(body_parts)
    return (chap, start, end, body)


def _published_recitations(conn, *, cutoff_date: str, min_views: int) -> list[dict]:
    cur = conn.execute(
        """
        SELECT
          apv.id AS id,
          apv.verse_data AS verse_data,
          apv.youtube_title AS internal_title,
          apv.interestingness_score AS judge_score,
          apv.interestingness_verdict AS judge_verdict,
          apv.interestingness_reason AS judge_reason,
          yv.title AS published_title,
          yv.views AS views,
          yv.likes AS likes,
          yv.published_at AS published_at
        FROM admin_pipeline_videos apv
        JOIN youtube_video_stats yv
          ON yv.source_table = 'admin_pipeline_videos' AND yv.source_id = apv.id
        WHERE yv.snapshot_date = (
            SELECT MAX(snapshot_date) FROM youtube_video_stats yv2
            WHERE yv2.youtube_video_id = yv.youtube_video_id
          )
          AND yv.views >= ?
          AND (yv.published_at IS NULL OR yv.published_at < ?)
        """,
        (min_views, cutoff_date),
    ).fetchall()
    out = []
    for r in cur:
        d = dict(r)
        chap, start, end, body = _passage_ref_from_verse_data(d.pop("verse_data", None))
        d["chapter"] = chap
        d["ayah_start"] = start
        d["ayah_end"] = end
        d["passage_body"] = body
        out.append(d)
    return out


def _rejected_recitations(conn) -> list[dict]:
    """Recitation candidates the judge rejected. The interestingness
    columns may or may not exist on this table depending on deploy
    order — guard accordingly."""
    try:
        cur = conn.execute(
            """
            SELECT id, verse_data, youtube_title AS title,
                   interestingness_score AS judge_score,
                   interestingness_verdict AS judge_verdict,
                   interestingness_reason AS judge_reason
            FROM admin_pipeline_videos
            WHERE interestingness_verdict = 'skip'
               OR status = 'rejected_uninteresting'
            ORDER BY id DESC LIMIT 12
            """
        ).fetchall()
        out = []
        for r in cur:
            d = dict(r)
            chap, start, end, body = _passage_ref_from_verse_data(d.pop("verse_data", None))
            d["chapter"] = chap
            d["ayah_start"] = start
            d["ayah_end"] = end
            d["passage_body"] = body
            out.append(d)
        return out
    except sqlite3.OperationalError:
        return []


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

# Genre-specific framing — what the analyzer is looking AT and FOR.
_GENRE_FRAME = {
    "translation_hides": (
        "Translation Hides shorts: contrast a conventional English "
        "translation against a more vivid Arabic meaning. The reveal "
        "should FLIP a viewer's mental image of the verse."
    ),
    "word_origins": (
        "Word Origins shorts: etymology of an Arabic root + Semitic "
        "cognates + how the Quran uses it. The payoff should REFRAME "
        "a familiar concept (not catalogue trivia about animal names)."
    ),
    "grammar_insights": (
        "Grammar Insights shorts: a grammatical move that changes the "
        "MEANING of a verse a layperson would recognize. Not formal "
        "agreement details."
    ),
    "recitation": (
        "Quranic Recitation shorts: a striking 1-8 verse passage read "
        "with translation overlay. The passage itself should stand "
        "alone (no etymology / commentary)."
    ),
}


_ANALYZER_SYSTEM = (
    "You are an editorial analyst for a YouTube Shorts channel about "
    "Quranic Arabic. You will see RECENT VIDEOS this channel has "
    "uploaded along with their real YouTube performance — views, "
    "likes, like-rate — and ALSO candidates the channel's "
    "interestingness judge rejected before they ever shipped (with "
    "the judge's reasons).\n\n"
    "Your job: extract 3 to 6 CONCRETE, FALSIFIABLE lessons the "
    "judge can apply to FUTURE candidates of this genre. Lessons must:\n"
    "  - be SHORT (one sentence, <= 30 words)\n"
    "  - be SPECIFIC (point at a content pattern, not a vague vibe)\n"
    "  - cite the video IDs (e.g. 'edu:7,edu:49') that support them — "
    "    at LEAST one ID per lesson\n"
    "  - be ACTIONABLE at judge time — phrased as 'prefer X' or "
    "    'skip Y when Z' or 'X tends to outperform Y'\n\n"
    "Avoid:\n"
    "  - empty platitudes ('make it interesting')\n"
    "  - re-stating the rubric the judge already has\n"
    "  - quoting metrics in absolute numbers (the channel grows; "
    "    relative engagement is the signal)\n"
    "  - citing video IDs that don't appear in the data you were shown\n\n"
    "Return ONLY a JSON object:\n"
    '{"lessons": [{"lesson": "...", "evidence_video_ids": ["edu:7", "edu:49"]}, ...]}'
)


def _trim(s: str | None, n: int = 240) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")


def _chap_v_ref(r: dict, ptype: str) -> str:
    if ptype == "recitation":
        c, s, e = r.get("chapter"), r.get("ayah_start"), r.get("ayah_end")
        if c is None:
            return "?"
        if s == e or e is None:
            return f"{c}:{s}"
        return f"{c}:{s}-{e}"
    return f"{r.get('chapter')}:{r.get('verse')}"


def _summarize_published(rows: list[dict], ref_prefix: str, ptype: str) -> str:
    out = []
    for r in rows:
        title = _strip_html(r.get("published_title") or r.get("internal_title") or "")
        views = r.get("views") or 0
        likes = r.get("likes") or 0
        lr = (likes / max(1, views)) * 100
        body = ""
        if ptype == "recitation":
            body = f" passage: {_trim(r.get('passage_body'), 240)}"
        else:
            try:
                s = json.loads(r.get("script_json") or "{}")
                body = (
                    f" hook: {_trim(s.get('hook'), 160)} | "
                    f"insight: {_trim(s.get('insight') or s.get('tidbit_about_root'), 200)}"
                )
            except json.JSONDecodeError:
                pass
        out.append(
            f"  {ref_prefix}:{r['id']}  Q{_chap_v_ref(r, ptype)}  views={views} likes={likes} "
            f"like_rate={lr:.2f}%  title='{title}'{body}"
        )
    return "\n".join(out) if out else "  (none yet)"


def _summarize_rejected(rows: list[dict], ref_prefix: str, ptype: str) -> str:
    out = []
    for r in rows:
        body = ""
        if ptype == "recitation":
            body = f"  passage: {_trim(r.get('passage_body'), 200)}"
        else:
            try:
                s = json.loads(r.get("script_json") or "{}")
                body = f"  hook: {_trim(s.get('hook'), 160)}"
            except json.JSONDecodeError:
                pass
        out.append(
            f"  {ref_prefix}:{r['id']}  Q{_chap_v_ref(r, ptype)}  "
            f"judge={r.get('judge_verdict')!r} score={r.get('judge_score')}  "
            f"reason: {_trim(r.get('judge_reason'), 200)}{body}"
        )
    return "\n".join(out) if out else "  (none)"


def _build_analyzer_prompt(ptype: str, cohort: dict) -> str:
    ref_prefix = "rec" if ptype == "recitation" else "edu"
    return (
        f"GENRE: {_GENRE_FRAME.get(ptype, ptype)}\n\n"
        f"TOP performers (ranked by like-rate among videos with enough "
        f"post-upload time and view volume to be meaningful — {len(cohort['top'])} of "
        f"{cohort['total_pool']} pool):\n"
        f"{_summarize_published(cohort['top'], ref_prefix, ptype)}\n\n"
        f"BOTTOM performers (same metric, low like-rate):\n"
        f"{_summarize_published(cohort['bottom'], ref_prefix, ptype)}\n\n"
        f"JUDGE-REJECTED candidates (never shipped — the judge's own "
        f"calls and reasons):\n"
        f"{_summarize_rejected(cohort['rejected'], ref_prefix, ptype)}\n\n"
        f"Extract 3-6 concrete lessons specific to this genre. The video "
        f"IDs you cite MUST appear in the data above — do not invent IDs. "
        f"Respond with ONLY the JSON."
    )


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

def _ollama_prefs(conn) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in conn.execute(
        "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
    ).fetchall():
        out[r["key"]] = r["value"]
    return out


def _strip_to_json(text: str) -> str:
    s = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    s = re.sub(r"^```(?:json)?\s*\n?", "", s.strip())
    s = re.sub(r"\n?```\s*$", "", s.strip())
    return s


def _call_ollama_analyzer(conn, user_message: str) -> str | None:
    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (
        prefs.get("ollama_metadata_model")
        or prefs.get("ollama_model")
        or ""
    ).strip()
    api_key = prefs.get("ollama_api_key") or ""
    if not model:
        print("[lessons] no ollama model configured; skipping")
        return None
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
                    {"role": "system", "content": _ANALYZER_SYSTEM},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0.3},
                "think": False,
            },
            timeout=180,  # the analyzer reads ~6KB of context; needs runway
        )
    except requests.RequestException as e:
        print(f"[lessons] transport error: {e}")
        return None
    if resp.status_code != 200:
        print(f"[lessons] http {resp.status_code}: {resp.text[:200]}")
        return None
    content = (resp.json().get("message") or {}).get("content", "")
    return content


def _parse_lessons(raw: str, ptype: str) -> list[dict]:
    """Extract the lessons list from the LLM response. Permissive on
    casing and key naming; strict on shape (must have lesson + ids)."""
    s = _strip_to_json(raw)
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        print(f"[lessons] no JSON found in response: {s[:200]}")
        return []
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError as e:
        print(f"[lessons] bad JSON: {e} -- {m.group()[:200]}")
        return []
    lessons = obj.get("lessons") if isinstance(obj, dict) else None
    if not isinstance(lessons, list):
        # The LLM sometimes returns a top-level array.
        lessons = obj if isinstance(obj, list) else []
    out = []
    for lsn in lessons:
        if not isinstance(lsn, dict):
            continue
        text = (lsn.get("lesson") or lsn.get("text") or "").strip()
        ids = lsn.get("evidence_video_ids") or lsn.get("evidence") or []
        if isinstance(ids, str):
            ids = [s.strip() for s in re.split(r"[,\s]+", ids) if s.strip()]
        if not text or not isinstance(ids, list):
            continue
        ids = [str(i).strip() for i in ids if str(i).strip()]
        if not ids:
            continue
        out.append({"lesson": text[:400], "evidence_video_ids": ids[:6]})
    return out


def _validate_lessons(
    proposed: list[dict],
    valid_ids: set[str],
) -> tuple[list[dict], list[str]]:
    """Accept only lessons whose cited IDs all exist in our cohort.
    Catches hallucinations — the LLM occasionally invents IDs the
    way it invents URLs."""
    accepted = []
    dropped = []
    for lsn in proposed:
        bad = [i for i in lsn["evidence_video_ids"] if i not in valid_ids]
        if bad:
            dropped.append(
                f"hallucinated IDs {bad} in lesson: {lsn['lesson'][:80]}"
            )
            continue
        accepted.append(lsn)
    return accepted, dropped
