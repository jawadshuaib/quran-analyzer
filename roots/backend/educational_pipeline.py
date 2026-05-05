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
import re
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
    # Idempotent ALTER for runtime-added columns. Each new column
    # ships a default so existing rows pass through cleanly.
    for col, coltype in (
        # Optional sound bite played during the al-nuqta outro card.
        # When set, the renderer overlays the audio after the narration
        # ends and extends the outro window so the audio can finish.
        ("outro_audio_filename", "TEXT"),
    ):
        try:
            conn.execute(f"ALTER TABLE educational_pipelines ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass

    # Schedule config — one row per pipeline. Mirrors pipeline_schedules
    # (recitation) so the scheduler-loop logic can stay structurally
    # identical across the two domains.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS educational_pipeline_schedules (
            pipeline_id INTEGER PRIMARY KEY REFERENCES educational_pipelines(id) ON DELETE CASCADE,
            times TEXT NOT NULL DEFAULT '[]',
            max_runs_per_day INTEGER NOT NULL DEFAULT 2,
            enabled INTEGER NOT NULL DEFAULT 0,
            grace_minutes INTEGER NOT NULL DEFAULT 30,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Audit log of scheduled fires. status:
    #   'fired'         — the scheduler started a video; video_id set
    #   'skipped_grace' — slot was past the grace window
    #   'skipped_cap'   — daily run cap reached
    #   'skipped_active'— another video already running for this pipeline
    #   'error'         — kick-off raised an exception
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS educational_pipeline_schedule_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL,
            scheduled_time TEXT NOT NULL,
            fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
            video_id INTEGER,
            status TEXT NOT NULL,
            note TEXT
        )
        """
    )
    # Same idempotency guard as the recitation scheduler — slot is
    # uniquely identified by (pipeline_id, scheduled_time) so a tick
    # firing twice for the same minute can't double-record.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_eps_runs_unique
        ON educational_pipeline_schedule_runs (pipeline_id, scheduled_time)
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


# Categories whose grammatical move is "video-shaped" — the contrast or
# rhetorical shift is concrete enough that a 90-second viewer can grok
# it without prior grammar exposure. These get a Tier A bump.
_GRAMMAR_TIER_A_CATEGORIES = frozenset({
    "time_perspective",     # Past-for-Future (Tahqiq)
    "perspective_shift",    # Iltifat
    "person_mixture",       # He / We / I shifts
    "royal_we_vs_i",        # Majestic plural intimacy contrast
    "cognate_accusative",   # Reduplicated root for emphasis
    "oath_structure",       # Wāw al-qasam framing
})

# Cooldowns — the pool excludes recently-shipped categories and surahs so
# the channel rotates through variety. Tunable; widen if the candidate
# pool gets sparse.
GRAMMAR_CATEGORY_COOLDOWN_DAYS = 7
GRAMMAR_SURAH_COOLDOWN_DAYS = 14


def _grammar_insights_candidates(conn, limit: int, exclude_queued: bool) -> list[dict]:
    """Pool: V7 insights at primary tier with confidence ≥ MIN_INSIGHT_CONFIDENCE.

    Tiering on top of the base score (overall_confidence):
      - Tier A (× 2.0) — counterfactual present AND category is one of
        the "video-shaped" categories above. These are the strongest
        hooks: a concrete "could-have-said-X / said-Y" frame.
      - Tier B (× 1.5) — counterfactual present (other categories), OR
        the verse also carries a translation_note (corroborating signal).
      - Tier C (× 1.0) — primary-tier insight without counterfactual or
        note. Eligible but ranked below.

    Cooldowns (only applied when exclude_queued=True; admin-side
    sample_candidates passes the same flag, so they apply by default):
      - Same `category` shipped to YouTube in the last 7 days → skip
      - Same `chapter` (surah) shipped in the last 14 days → skip
    Cooldowns measure against `educational_videos.created_at`, the
    moment the row was queued — not when it was uploaded — so manual
    queues count too. That keeps the operator from silently flooding
    one surah by hand.
    """
    rows = conn.execute(
        """
        SELECT chapter, verse, insights_v7_json
        FROM verse_grammar_insights
        WHERE insights_v7_json IS NOT NULL AND insights_v7_json != ''
        """
    ).fetchall()

    # Materialize already-queued anchors once for an O(1) check.
    queued: set[tuple[int, int, str]] = set()
    cooldown_categories: set[str] = set()
    cooldown_chapters: set[int] = set()
    if exclude_queued:
        for r in conn.execute(
            "SELECT chapter, verse, anchor_insight_id FROM educational_videos "
            "WHERE type = 'grammar_insights'"
        ):
            queued.add((r["chapter"], r["verse"], r["anchor_insight_id"] or ""))

        # Surah cooldown — 14 days. Direct from `educational_videos`.
        for rr in conn.execute(
            f"""
            SELECT DISTINCT chapter FROM educational_videos
            WHERE type = 'grammar_insights'
              AND created_at >= datetime('now', '-{GRAMMAR_SURAH_COOLDOWN_DAYS} days')
            """
        ).fetchall():
            cooldown_chapters.add(int(rr["chapter"]))

        # Category cooldown — 7 days. Categories aren't stored on
        # `educational_videos`; we resolve them by reading the V7
        # JSON for each recent (chapter, anchor_insight_id) pair.
        recent_anchors_7d: list[tuple[int, str]] = []
        for rr in conn.execute(
            f"""
            SELECT chapter, anchor_insight_id FROM educational_videos
            WHERE type = 'grammar_insights'
              AND anchor_insight_id IS NOT NULL
              AND created_at >= datetime('now', '-{GRAMMAR_CATEGORY_COOLDOWN_DAYS} days')
            """
        ).fetchall():
            recent_anchors_7d.append((int(rr["chapter"]), rr["anchor_insight_id"]))

        if recent_anchors_7d:
            chapters_filter = ",".join(str(c) for c, _ in recent_anchors_7d)
            anchor_set = set(recent_anchors_7d)
            for vr in conn.execute(
                f"""
                SELECT chapter, insights_v7_json
                FROM verse_grammar_insights
                WHERE chapter IN ({chapters_filter})
                """
            ).fetchall():
                try:
                    arr = json.loads(vr["insights_v7_json"]) or []
                except Exception:
                    continue
                for ins in arr:
                    iid = ins.get("id") or ""
                    if (int(vr["chapter"]), iid) in anchor_set:
                        cat = ins.get("category")
                        if cat:
                            cooldown_categories.add(cat)

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

            category = ins.get("category") or ""
            chapter = int(r["chapter"])
            if exclude_queued:
                if category in cooldown_categories:
                    continue
                if chapter in cooldown_chapters:
                    continue

            cf_present = bool((ins.get("counterfactual") or {}).get("present"))
            cf_text = (ins.get("counterfactual") or {}).get("text") or ""
            cf_truncated = cf_present and not cf_text.rstrip().endswith((".", "!", "?", ".”", "."))

            # Tier scoring
            if cf_present and not cf_truncated and category in _GRAMMAR_TIER_A_CATEGORIES:
                tier = "A"
                multiplier = 2.0
            elif cf_present and not cf_truncated:
                tier = "B"
                multiplier = 1.5
            else:
                tier = "C"
                multiplier = 1.0

            out.append({
                "chapter": chapter,
                "verse": int(r["verse"]),
                "word_pos": None,
                "insight_id": insight_id,
                "category": category,
                "title": ins.get("title"),
                "confidence": conf,
                "has_counterfactual": cf_present,
                "tier": tier,
                "score": conf * multiplier,
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
    recency_days: int = 0,
) -> list[dict]:
    """Pull a ranked list of candidates for the given series type.

    `recency_days` (default 0 = disabled) excludes candidates whose
    *content key* was used recently — so the same root (Word Origins)
    or verse (other types) doesn't dominate every run. Pipeline
    orchestrator passes 30; the candidate-browser UI passes 0 so the
    operator can still see the full pool.
    """
    if vtype not in _SAMPLERS:
        raise ValueError(f"unknown educational video type: {vtype}")
    out = _SAMPLERS[vtype](conn, limit, exclude_queued)
    if recency_days and recency_days > 0:
        out = _apply_recency_filter(conn, vtype, out, recency_days)
    return out


def _apply_recency_filter(
    conn: sqlite3.Connection,
    vtype: str,
    candidates: list[dict],
    recency_days: int,
) -> list[dict]:
    """Drop candidates whose content key (root for word_origins,
    (chapter, verse) for the others) was used by an
    educational_videos row within the last `recency_days`.

    Why per-type, not per-pipeline:
      The recitation pipeline scopes recency to a single pipeline so
      two pipelines on different languages never collide. For
      educational, all pipelines of one type (e.g. all Word Origins
      pipelines) share the same content universe — we don't want the
      'short' pipeline burning a-y-n today and the 'long' pipeline
      doing the same root tomorrow. Global per-type recency keeps
      content varied across both.
    """
    if not candidates:
        return candidates
    rows = conn.execute(
        "SELECT chapter, verse, anchor_word_pos, payload_json "
        "FROM educational_videos "
        "WHERE type = ? AND created_at >= datetime('now', ?)",
        (vtype, f"-{recency_days} days"),
    ).fetchall()
    if not rows:
        return candidates

    if vtype == "word_origins":
        # Deduplicate by root_buckwalter — that's the unit a viewer
        # would recognize as "the same video idea." Different verses
        # for the same root still talk about that root.
        #
        # Resolution order for the row's root:
        #   1. payload_json.root_bw            (manual-queue shape)
        #   2. payload_json.root.buckwalter    (enriched / script-gen shape)
        #   3. morphology lookup by (chapter, verse, word_pos)
        #
        # The morphology fallback is the source of truth — if the
        # payload format ever changes again, we still get the right
        # answer.
        used_roots: set[str] = set()
        for r in rows:
            rb: str | None = None
            try:
                p = json.loads(r["payload_json"] or "{}")
                rb = p.get("root_bw") or (p.get("root") or {}).get("buckwalter")
            except Exception:
                pass
            if not rb and r["anchor_word_pos"] is not None:
                m = conn.execute(
                    "SELECT root_buckwalter FROM morphology "
                    "WHERE chapter = ? AND verse = ? AND word_pos = ? "
                    "AND root_buckwalter IS NOT NULL AND root_buckwalter != '' "
                    "ORDER BY segment ASC LIMIT 1",
                    (r["chapter"], r["verse"], r["anchor_word_pos"]),
                ).fetchone()
                if m and m["root_buckwalter"]:
                    rb = m["root_buckwalter"]
            if rb:
                used_roots.add(rb)
        if not used_roots:
            return candidates
        return [c for c in candidates if c.get("root_bw") not in used_roots]

    # translation_hides + grammar_insights: per-anchor dedupe is
    # already covered by exclude_queued (the anchor IS the verse for
    # these types). Apply (chapter, verse) recency anyway so the
    # filter behaves consistently across types.
    used_pairs: set[tuple[int, int]] = {(r["chapter"], r["verse"]) for r in rows}
    return [
        c for c in candidates
        if (c.get("chapter"), c.get("verse")) not in used_pairs
    ]


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
               music_id, outro_audio_filename, enabled, created_at, updated_at
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


# --------------------------------------------------------------------------
#  Pipeline schedule CRUD
# --------------------------------------------------------------------------

# Defaults returned when no schedule row exists for a pipeline yet.
SCHEDULE_DEFAULTS: dict = {
    "times": [],
    "max_runs_per_day": 2,
    "enabled": False,
    "grace_minutes": 30,
}


def get_schedule(conn: sqlite3.Connection, pipeline_id: int) -> dict:
    """Return the schedule for a pipeline. Returns SCHEDULE_DEFAULTS
    (with `pipeline_id` filled in) if no row exists yet — no need to
    pre-create rows just to render the form."""
    row = conn.execute(
        "SELECT pipeline_id, times, max_runs_per_day, enabled, "
        "       grace_minutes, created_at, updated_at "
        "FROM educational_pipeline_schedules WHERE pipeline_id = ?",
        (pipeline_id,),
    ).fetchone()
    if not row:
        return {
            "pipeline_id": pipeline_id,
            **SCHEDULE_DEFAULTS,
            "created_at": None,
            "updated_at": None,
        }
    out = dict(row)
    try:
        out["times"] = json.loads(out["times"] or "[]")
    except Exception:
        out["times"] = []
    out["enabled"] = bool(out.get("enabled"))
    return out


def upsert_schedule(
    conn: sqlite3.Connection,
    pipeline_id: int,
    *,
    times: list[str],
    max_runs_per_day: int = 2,
    enabled: bool = False,
    grace_minutes: int = 30,
) -> dict:
    """Replace the schedule for a pipeline (creates the row on first
    save). Validates time strings as HH:MM and the integer caps as
    sane bounds before writing."""
    # Validate / normalize times. Accept "9:30" → "09:30"; reject anything
    # that doesn't match HH:MM with valid hours/minutes.
    cleaned: list[str] = []
    for t in times or []:
        if not isinstance(t, str):
            continue
        m = re.match(r"^(\d{1,2}):(\d{2})$", t.strip())
        if not m:
            raise ValueError(f"invalid time format: {t!r} (expected HH:MM)")
        hh = int(m.group(1)); mm = int(m.group(2))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError(f"time out of range: {t!r}")
        norm = f"{hh:02d}:{mm:02d}"
        if norm not in cleaned:
            cleaned.append(norm)
    cleaned.sort()

    if not (1 <= int(max_runs_per_day) <= 24):
        raise ValueError("max_runs_per_day must be 1..24")
    if not (0 <= int(grace_minutes) <= 240):
        raise ValueError("grace_minutes must be 0..240")

    conn.execute(
        """
        INSERT INTO educational_pipeline_schedules
            (pipeline_id, times, max_runs_per_day, enabled, grace_minutes, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(pipeline_id) DO UPDATE SET
            times = excluded.times,
            max_runs_per_day = excluded.max_runs_per_day,
            enabled = excluded.enabled,
            grace_minutes = excluded.grace_minutes,
            updated_at = datetime('now')
        """,
        (
            pipeline_id,
            json.dumps(cleaned, ensure_ascii=False),
            int(max_runs_per_day),
            1 if enabled else 0,
            int(grace_minutes),
        ),
    )
    conn.commit()
    return get_schedule(conn, pipeline_id)


def list_schedule_runs(
    conn: sqlite3.Connection, pipeline_id: int, limit: int = 50,
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, pipeline_id, scheduled_time, fired_at, video_id, status, note
        FROM educational_pipeline_schedule_runs
        WHERE pipeline_id = ?
        ORDER BY fired_at DESC
        LIMIT ?
        """,
        (pipeline_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def record_schedule_run(
    conn: sqlite3.Connection,
    pipeline_id: int,
    scheduled_time: str,
    status: str,
    *,
    video_id: int | None = None,
    note: str | None = None,
) -> None:
    """Idempotent insert — if the (pipeline_id, scheduled_time) slot
    already has a row, leave it alone. Lets the scheduler tick
    repeatedly within the grace window without double-recording."""
    try:
        conn.execute(
            """
            INSERT INTO educational_pipeline_schedule_runs
                (pipeline_id, scheduled_time, status, video_id, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pipeline_id, scheduled_time, status, video_id, (note or "")[:300]),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Slot already recorded — fine, idempotent by design.
        pass


# Cap on how many candidates we'll skip before giving up — if the top 20
# all fail safety, something's miscalibrated and we'd rather surface that
# than spin forever burning Ollama calls.
_MAX_SAFETY_SKIPS = 20

# Don't repeat the same root (Word Origins) or verse (other types)
# within this many days. Mirrors the recitation pipeline's 30-day
# rotation. Set 0 to disable.
PIPELINE_RECENCY_DAYS = 30


def pick_and_queue_for_pipeline(
    conn: sqlite3.Connection,
    pipeline_id: int,
    *,
    triggered_by: str = "pipeline",
) -> int:
    """Pick the highest-scoring unused candidate of the pipeline's type
    and insert an educational_videos row tagged with the pipeline. Does
    NOT generate a script or render — caller chains those steps after.
    Returns the new educational_videos.id.

    Walks the candidate list until we find one whose source verse
    passes content-safety screening. Permissive when the safety
    module is unavailable (returns the candidate as-is)."""
    pipe = get_pipeline(conn, pipeline_id)
    if not pipe:
        raise PipelineRunError(f"pipeline {pipeline_id} not found")
    if not pipe.get("enabled"):
        raise PipelineRunError(f"pipeline {pipeline_id} is disabled")

    # Pull plenty of candidates so the recency filter (drops recently-
    # used roots/verses) and the safety loop (drops controversial
    # source verses) both have room to work without starving us.
    # 100 is well over the worst-case combined drop rate; ranking by
    # score in the underlying sampler means the front of the list is
    # still our best content even after filtering.
    candidates = sample_candidates(
        conn, pipe["type"],
        limit=100,
        exclude_queued=True,
        recency_days=PIPELINE_RECENCY_DAYS,
    )
    if not candidates:
        raise PipelineRunError(
            f"no unused {pipe['type']} candidates remain — either the pool "
            f"is exhausted or every top candidate was used in the last "
            f"{PIPELINE_RECENCY_DAYS} days. Wait or widen the pool."
        )

    # Filter the source verse through content safety. If Ollama isn't
    # configured / reachable, the safety module is permissive (returns
    # True) so this loop just picks the first candidate.
    try:
        import educational_safety as _safety
        chosen = None
        skipped = 0
        for cand in candidates:
            if _safety.is_verse_safe(conn, cand["chapter"], cand["verse"]):
                chosen = cand
                break
            skipped += 1
            if skipped >= _MAX_SAFETY_SKIPS:
                break
        if chosen is None:
            raise PipelineRunError(
                f"all top-{skipped} candidates flagged as controversial — "
                f"either widen the candidate pool or relax safety prompt"
            )
        c = chosen
    except ImportError:
        # Safety module unimportable — skip the screening, just take
        # the top candidate. Module is supposed to be present in this
        # codebase; this except is defense-in-depth only.
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
