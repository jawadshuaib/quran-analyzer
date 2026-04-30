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


def list_videos(conn, vtype: str | None = None, limit: int = 100) -> list[dict]:
    where = "WHERE type = ?" if vtype else ""
    params = (vtype,) if vtype else ()
    rows = conn.execute(
        f"""
        SELECT id, type, chapter, verse, anchor_word_pos, anchor_insight_id,
               status, format, filename, file_size,
               youtube_video_id, tiktok_video_id,
               score, error_message, created_at, completed_at
        FROM educational_videos
        {where}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        params + (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
