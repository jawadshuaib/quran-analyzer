"""Educational video pipeline — Phase 1 (foundation).

Produces a sampling pool of verses for each of the three educational
video types. Phases 2 (script generation) and 3 (rendering) will
consume these candidates.

Public API:
    ensure_table(conn)              — idempotent schema bootstrap
    pool_size(conn, vtype) → int    — how many usable candidates exist
    sample_candidates(conn, vtype, limit, exclude_queued=True)
                                    — returns ranked candidate dicts
    queue_candidate(conn, vtype, anchor) → row_id

Three video types are handled:
    'word_origins'      — verse contains a content word whose root has
                          cognates in ≥2 distinct Semitic languages.
    'translation_hides' — verse has an `ai_translations.departure_notes`
                          worth surfacing (≥80 chars).
    'grammar_insights'  — verse has a V7 grammar insight with
                          tier='primary', eligible, confidence ≥0.7.

The candidate-pool queries derive from existing tables (no separate
candidates table). The educational_videos table records what's been
queued/generated; UNIQUE on (type, chapter, verse, anchor_*) prevents
the same anchor showing up twice.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

# Buckwalter → semiticroots transliteration. Mirrors _BW_TO_SR in app.py;
# we duplicate it here so this module is import-safe (no app.py side
# effects). Keep the two in sync if the app.py table is ever extended.
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


def _bw_to_sr(bw: str | None) -> str | None:
    if not bw:
        return None
    return "-".join(_BW_TO_SR.get(c, c) for c in bw)


def _register_udfs(conn: sqlite3.Connection) -> None:
    """Register bw_to_sr() as a user function so the cognate-pool join
    can run inside SQL. Idempotent — re-registering is a no-op."""
    conn.create_function("bw_to_sr", 1, _bw_to_sr, deterministic=True)

# Type → field requirements at the script-generation stage. Phase 1
# uses these only for filtering; Phase 2 will use them as the prompt
# input contract.
TYPES = ("word_origins", "translation_hides", "grammar_insights")

# Word-Origins: minimum cognate diversity to be worth a 45-second video.
MIN_COGNATE_LANGUAGES = 2

# Translation-Hides: a departure note shorter than this is usually a
# one-liner gloss that doesn't sustain a video.
MIN_DEPARTURE_NOTE_CHARS = 80

# Grammar-Insights: confidence floor — anything below this hasn't earned
# a script yet. Tunable as the V7 generator improves.
MIN_INSIGHT_CONFIDENCE = 0.70


# --------------------------------------------------------------------------
#  Schema
# --------------------------------------------------------------------------

def ensure_table(conn: sqlite3.Connection) -> None:
    """Idempotent — safe to call on every app boot."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS educational_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('word_origins','translation_hides','grammar_insights')),
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            -- Anchor: NULL when the type doesn't subdivide a verse.
            anchor_word_pos INTEGER,
            anchor_insight_id TEXT,
            -- The structured grounding for Phase 2 script generation.
            payload_json TEXT,
            -- Phase 2 outputs.
            script_json TEXT,
            voiceover_text TEXT,
            -- Phase 3 outputs.
            format TEXT,
            filename TEXT,
            file_size INTEGER,
            -- Distribution.
            youtube_video_id TEXT,
            tiktok_video_id TEXT,
            -- Lifecycle.
            status TEXT NOT NULL DEFAULT 'candidate',
            score REAL,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
        """
    )
    # Pipeline integration columns (idempotent ALTERs). When a row
    # comes from a configured pipeline run, pipeline_id points to
    # the pipeline definition; triggered_by records 'manual',
    # 'pipeline' (Run-now button), or 'scheduler' (cron) for audit.
    for col, coltype in (
        ("pipeline_id", "INTEGER"),
        ("triggered_by", "TEXT DEFAULT 'manual'"),
        # YouTube metadata generated from Ollama after render. Same
        # column shape as admin_pipeline_videos for consistency, so
        # the same upload helper can target both tables later.
        ("youtube_title", "TEXT"),
        ("youtube_description", "TEXT"),
        ("youtube_tags", "TEXT"),  # JSON array
    ):
        try:
            conn.execute(f"ALTER TABLE educational_videos ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass

    # Pipeline configuration table — one row per saved pipeline.
    # Mirrors admin_pipelines's shape so the frontend / scheduler can
    # reason about both with a similar mental model. The `format`
    # column is new (recitation pipelines don't have it because they
    # always produce 9:16 shorts); educational shorts vs long form
    # is a real authoring decision.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS educational_pipelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('word_origins','translation_hides','grammar_insights')),
            voice_id TEXT NOT NULL,
            format TEXT NOT NULL CHECK(format IN ('short','long')),
            show_dim_background INTEGER NOT NULL DEFAULT 1,
            music_id INTEGER,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # UNIQUE-coalesce: SQLite treats NULLs as distinct, which would let
    # the same Translation-Hides verse be queued twice. We collapse the
    # null anchor fields to '' for uniqueness purposes.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_educational_unique
        ON educational_videos (
            type, chapter, verse,
            COALESCE(anchor_word_pos, -1),
            COALESCE(anchor_insight_id, '')
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_educational_status ON educational_videos (status, type)"
    )
    conn.commit()

    # Reset stuck 'rendering' rows on app boot. A render that was
    # in-flight when the server died (deploy, OOM, restart) leaves
    # the row stranded — there's no daemon thread to finish it.
    # We move them to 'failed' with an explanation so the operator
    # can re-render with one click. Mirrors the recitation pipeline's
    # boot-time recovery (admin_pipeline_videos resets the same way).
    try:
        cur = conn.execute(
            "UPDATE educational_videos "
            "SET status = 'failed', "
            "    error_message = 'Server restarted mid-render — re-run to recover.' "
            "WHERE status = 'rendering'"
        )
        if cur.rowcount:
            print(f"[educational] reset {cur.rowcount} stuck rendering row(s) on boot")
        conn.commit()
    except sqlite3.OperationalError:
        # Educational tables not yet present on a fresh install — ALTER
        # path above creates them on this same call, so on the next
        # boot the recovery will run normally.
        pass


# --------------------------------------------------------------------------
#  Candidate-pool queries
# --------------------------------------------------------------------------

def _excluded_clause(vtype: str) -> tuple[str, dict]:
    """Build a NOT IN clause matching already-queued anchors so we never
    sample the same candidate twice."""
    return (
        """
        NOT EXISTS (
            SELECT 1 FROM educational_videos ev
            WHERE ev.type = :etype
              AND ev.chapter = c
              AND ev.verse = v
              AND COALESCE(ev.anchor_word_pos, -1) = COALESCE(awp, -1)
              AND COALESCE(ev.anchor_insight_id, '') = COALESCE(aid, '')
        )
        """,
        {"etype": vtype},
    )


def _translation_hides_candidates(conn, limit: int, exclude_queued: bool) -> list[dict]:
    """Pool: ai_translations rows with a substantive departure note."""
    excl_sql, excl_params = _excluded_clause("translation_hides")
    where_excl = f"AND {excl_sql}" if exclude_queued else ""
    rows = conn.execute(
        f"""
        SELECT chapter AS c, verse AS v, NULL AS awp, NULL AS aid,
               chapter, verse,
               departure_notes,
               LENGTH(departure_notes) AS score
        FROM ai_translations
        WHERE departure_notes IS NOT NULL
          AND LENGTH(TRIM(departure_notes)) >= :min_chars
          {where_excl}
        ORDER BY score DESC, RANDOM()
        LIMIT :limit
        """,
        {"min_chars": MIN_DEPARTURE_NOTE_CHARS, "limit": limit, **excl_params},
    ).fetchall()
    return [dict(r) for r in rows]


def _grammar_insights_candidates(conn, limit: int, exclude_queued: bool) -> list[dict]:
    """Pool: V7 insights at primary tier with confidence ≥ MIN_INSIGHT_CONFIDENCE.

    The insights are stored JSON-blobbed inside verse_grammar_insights —
    Python unpacks them so each insight becomes its own candidate. A
    counterfactual ("could have said X but said Y") boosts the score
    1.4× because those make the strongest video hooks.
    """
    rows = conn.execute(
        """
        SELECT chapter, verse, insights_v7_json
        FROM verse_grammar_insights
        WHERE insights_v7_json IS NOT NULL AND insights_v7_json != ''
        """
    ).fetchall()

    # Materialize already-queued anchors once for an O(1) check.
    queued = set()
    if exclude_queued:
        for r in conn.execute(
            "SELECT chapter, verse, anchor_insight_id FROM educational_videos "
            "WHERE type = 'grammar_insights'"
        ):
            queued.add((r["chapter"], r["verse"], r["anchor_insight_id"] or ""))

    out: list[dict] = []
    for r in rows:
        try:
            insights = json.loads(r["insights_v7_json"])
        except Exception:
            continue
        if not isinstance(insights, list):
            continue
        for ins in insights:
            display = ins.get("display") or {}
            quality = ins.get("quality") or {}
            if display.get("tier") != "primary" or not display.get("eligible"):
                continue
            conf = quality.get("overall_confidence") or 0.0
            if conf < MIN_INSIGHT_CONFIDENCE:
                continue
            insight_id = ins.get("id") or ""
            if (r["chapter"], r["verse"], insight_id) in queued:
                continue
            cf = (ins.get("counterfactual") or {}).get("present")
            score = conf * (1.4 if cf else 1.0)
            out.append({
                "chapter": r["chapter"],
                "verse": r["verse"],
                "word_pos": None,
                "insight_id": insight_id,
                "category": ins.get("category"),
                "title": ins.get("title"),
                "confidence": conf,
                "has_counterfactual": bool(cf),
                "score": score,
            })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:limit]


def _word_origins_candidates(conn, limit: int, exclude_queued: bool) -> list[dict]:
    """One sample per distinct root — common roots like ع ي ن occur in
    dozens of verses and would otherwise dominate the preview. The
    dedupe happens in SQL via a windowed row_number() so we don't
    over-fetch."""
    _register_udfs(conn)
    excl_sql, excl_params = _excluded_clause("word_origins")
    where_excl = f"AND {excl_sql}" if exclude_queued else ""
    rows = conn.execute(
        f"""
        WITH content_words AS (
            SELECT m.chapter AS c, m.verse AS v, m.word_pos AS awp,
                   NULL AS aid,
                   m.root_buckwalter AS root_bw, m.root_arabic AS root_ar,
                   m.lemma_buckwalter AS lemma_bw,
                   bw_to_sr(m.root_buckwalter) AS sr_trans
            FROM morphology m
            WHERE m.root_buckwalter IS NOT NULL
              AND m.root_buckwalter != ''
              AND m.pos NOT IN ('Prefix','Suffix','Pronoun')
        ),
        cognate_stats AS (
            SELECT sr.transliteration AS sr_trans,
                   COUNT(DISTINCT sd.language) AS lang_count,
                   COUNT(*) AS deriv_count
            FROM semitic_roots sr
            JOIN semitic_derivatives sd ON sd.root_id = sr.id
            WHERE sd.language IS NOT NULL AND sd.language != ''
            GROUP BY sr.transliteration
            HAVING COUNT(DISTINCT sd.language) >= :min_langs
        ),
        joined AS (
            SELECT cw.c AS chapter, cw.v AS verse, cw.awp AS word_pos,
                   cw.root_bw, cw.root_ar, cw.lemma_bw,
                   cs.lang_count, cs.deriv_count,
                   (cs.lang_count * 1.0 + cs.deriv_count * 0.2) AS score,
                   ROW_NUMBER() OVER (
                       PARTITION BY cw.root_bw
                       ORDER BY cs.lang_count DESC, RANDOM()
                   ) AS rn
            FROM content_words cw
            JOIN cognate_stats cs ON cs.sr_trans = cw.sr_trans
            WHERE 1=1 {where_excl}
        )
        SELECT chapter, verse, word_pos, root_bw, root_ar, lemma_bw,
               lang_count, deriv_count, score
        FROM joined
        WHERE rn = 1
        ORDER BY score DESC, RANDOM()
        LIMIT :limit
        """,
        {"min_langs": MIN_COGNATE_LANGUAGES, "limit": limit, **excl_params},
    ).fetchall()
    return [dict(r) for r in rows]


_SAMPLERS = {
    "word_origins": _word_origins_candidates,
    "translation_hides": _translation_hides_candidates,
    "grammar_insights": _grammar_insights_candidates,
}


def sample_candidates(
    conn: sqlite3.Connection,
    vtype: str,
    limit: int = 25,
    exclude_queued: bool = True,
) -> list[dict]:
    if vtype not in _SAMPLERS:
        raise ValueError(f"unknown educational video type: {vtype}")
    return _SAMPLERS[vtype](conn, limit, exclude_queued)


def pool_size(conn: sqlite3.Connection, vtype: str) -> int:
    """Cheap-ish count of available candidates per type. Uses the
    sampler with a generous cap; the UI only needs an order-of-
    magnitude reading, not a precise total."""
    # 10k cap so we don't materialize millions of rows; the dashboard
    # shows '10k+' if we hit it.
    rows = sample_candidates(conn, vtype, limit=10_000, exclude_queued=True)
    return len(rows)


# --------------------------------------------------------------------------
#  Queueing
# --------------------------------------------------------------------------

def queue_candidate(
    conn: sqlite3.Connection,
    vtype: str,
    *,
    chapter: int,
    verse: int,
    word_pos: int | None = None,
    insight_id: str | None = None,
    payload: dict[str, Any] | None = None,
    score: float | None = None,
) -> int:
    """Insert a candidate into educational_videos (status='candidate').
    Caller is expected to pass the structured payload that Phase 2 will
    feed to the LLM. Raises sqlite3.IntegrityError if already queued."""
    if vtype not in TYPES:
        raise ValueError(f"unknown type: {vtype}")
    cur = conn.execute(
        """
        INSERT INTO educational_videos
            (type, chapter, verse, anchor_word_pos, anchor_insight_id,
             payload_json, status, score)
        VALUES (?, ?, ?, ?, ?, ?, 'candidate', ?)
        """,
        (
            vtype, chapter, verse, word_pos, insight_id,
            json.dumps(payload, ensure_ascii=False) if payload else None,
            score,
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_videos(
    conn, vtype: str | None = None, pipeline_id: int | None = None, limit: int = 100,
) -> list[dict]:
    clauses: list[str] = []
    params: list = []
    if vtype:
        clauses.append("type = ?"); params.append(vtype)
    if pipeline_id is not None:
        clauses.append("pipeline_id = ?"); params.append(pipeline_id)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        f"""
        SELECT id, type, chapter, verse, anchor_word_pos, anchor_insight_id,
               status, format, filename, file_size,
               youtube_video_id, tiktok_video_id,
               youtube_title, youtube_description, youtube_tags,
               pipeline_id, triggered_by,
               score, error_message, created_at, completed_at
        FROM educational_videos
        {where}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
#  Pipeline configuration CRUD
# --------------------------------------------------------------------------

PIPELINE_FORMATS = ("short", "long")


def list_pipelines(conn: sqlite3.Connection, vtype: str | None = None) -> list[dict]:
    where = "WHERE type = ?" if vtype else ""
    params = (vtype,) if vtype else ()
    rows = conn.execute(
        f"""
        SELECT id, name, type, voice_id, format, show_dim_background,
               music_id, enabled, created_at, updated_at
        FROM educational_pipelines
        {where}
        ORDER BY created_at DESC
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def get_pipeline(conn: sqlite3.Connection, pipeline_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM educational_pipelines WHERE id = ?", (pipeline_id,),
    ).fetchone()
    return dict(row) if row else None


def create_pipeline(
    conn: sqlite3.Connection,
    *,
    name: str,
    vtype: str,
    voice_id: str,
    format: str,
    show_dim_background: bool = True,
    music_id: int | None = None,
    enabled: bool = True,
) -> int:
    if vtype not in TYPES:
        raise ValueError(f"unknown type: {vtype}")
    if format not in PIPELINE_FORMATS:
        raise ValueError(f"unknown format: {format}")
    if not name.strip():
        raise ValueError("name required")
    if not voice_id.strip():
        raise ValueError("voice_id required")
    cur = conn.execute(
        """
        INSERT INTO educational_pipelines
            (name, type, voice_id, format, show_dim_background, music_id, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), vtype, voice_id.strip(), format,
         1 if show_dim_background else 0, music_id, 1 if enabled else 0),
    )
    conn.commit()
    return cur.lastrowid


def update_pipeline(
    conn: sqlite3.Connection,
    pipeline_id: int,
    *,
    name: str | None = None,
    voice_id: str | None = None,
    format: str | None = None,
    show_dim_background: bool | None = None,
    music_id: int | None = None,
    enabled: bool | None = None,
) -> bool:
    """Patch-style update — only fields explicitly passed are changed.
    type is intentionally immutable: changing the type would orphan
    any existing videos that were generated under the old type."""
    if format is not None and format not in PIPELINE_FORMATS:
        raise ValueError(f"unknown format: {format}")
    sets: list[str] = []
    params: list = []
    if name is not None:
        sets.append("name = ?"); params.append(name.strip())
    if voice_id is not None:
        sets.append("voice_id = ?"); params.append(voice_id.strip())
    if format is not None:
        sets.append("format = ?"); params.append(format)
    if show_dim_background is not None:
        sets.append("show_dim_background = ?"); params.append(1 if show_dim_background else 0)
    if music_id is not None:  # intentionally accept None=clear via separate field
        sets.append("music_id = ?"); params.append(music_id)
    if enabled is not None:
        sets.append("enabled = ?"); params.append(1 if enabled else 0)
    if not sets:
        return False
    sets.append("updated_at = datetime('now')")
    params.append(pipeline_id)
    cur = conn.execute(
        f"UPDATE educational_pipelines SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return cur.rowcount > 0


def delete_pipeline(conn: sqlite3.Connection, pipeline_id: int) -> bool:
    cur = conn.execute(
        "DELETE FROM educational_pipelines WHERE id = ?", (pipeline_id,),
    )
    conn.commit()
    return cur.rowcount > 0


# --------------------------------------------------------------------------
#  Pipeline orchestration — pick a candidate and queue it under the pipeline
# --------------------------------------------------------------------------

class PipelineRunError(Exception):
    """Raised when picking + queueing fails. Caller decides whether to
    surface the error or move on."""


def pick_and_queue_for_pipeline(
    conn: sqlite3.Connection,
    pipeline_id: int,
    *,
    triggered_by: str = "pipeline",
) -> int:
    """Pick the highest-scoring unused candidate of the pipeline's type
    and insert an educational_videos row tagged with the pipeline. Does
    NOT generate a script or render — caller chains those steps after.
    Returns the new educational_videos.id."""
    pipe = get_pipeline(conn, pipeline_id)
    if not pipe:
        raise PipelineRunError(f"pipeline {pipeline_id} not found")
    if not pipe.get("enabled"):
        raise PipelineRunError(f"pipeline {pipeline_id} is disabled")

    candidates = sample_candidates(conn, pipe["type"], limit=1, exclude_queued=True)
    if not candidates:
        raise PipelineRunError(
            f"no unused {pipe['type']} candidates remain — pool exhausted"
        )
    c = candidates[0]
    payload = {
        # Per-type extras the script generator wants in the payload —
        # mirrors what the queue endpoint stores on a manual queue.
        "root_bw": c.get("root_bw"),
        "root_ar": c.get("root_ar"),
        "lemma_bw": c.get("lemma_bw"),
        "lang_count": c.get("lang_count"),
        "deriv_count": c.get("deriv_count"),
        "departure_notes": c.get("departure_notes"),
        "category": c.get("category"),
        "title": c.get("title"),
        "confidence": c.get("confidence"),
        "has_counterfactual": c.get("has_counterfactual"),
    }
    cur = conn.execute(
        """
        INSERT INTO educational_videos
            (type, chapter, verse, anchor_word_pos, anchor_insight_id,
             payload_json, status, score, pipeline_id, triggered_by)
        VALUES (?, ?, ?, ?, ?, ?, 'candidate', ?, ?, ?)
        """,
        (
            pipe["type"], c["chapter"], c["verse"],
            c.get("word_pos"), c.get("insight_id"),
            json.dumps(payload, ensure_ascii=False),
            c.get("score"),
            pipeline_id, triggered_by,
        ),
    )
    conn.commit()
    return cur.lastrowid
