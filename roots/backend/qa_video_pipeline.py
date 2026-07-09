"""Q&A video pipeline — schema + candidate sourcing + status helpers.

Separate `qa_videos*` tables (NOT an extension of the educational
`type` CHECK constraint, which would force a SQLite table rebuild). The
table mirrors educational_videos so the existing YouTube uploader can
gain a third eligible-row branch later with minimal change.

Source pool: rated-5 AI Q&A — assistant_conversations.quality_score=5,
source='ai', page_type='verse' — not yet turned into a video.
"""

from __future__ import annotations

import json
import os

import qa_video_common as C

# Where gate-passed/draft script JSONs live (one per qa_id). A cloud
# Routine runs on a fresh checkout with an EMPTY qa_videos table, so
# cross-run dedup keys off these COMMITTED files, not the table.
DRAFTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_video_drafts")


def _drafted_qa_ids() -> set[int]:
    ids: set[int] = set()
    if not os.path.isdir(DRAFTS_DIR):
        return ids
    for fn in os.listdir(DRAFTS_DIR):
        if fn.endswith(".json"):
            stem = fn[:-5]
            if stem.isdigit():
                ids.add(int(stem))
    return ids

SCHEMA = """
CREATE TABLE IF NOT EXISTS qa_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Studio model (2026-07): the bank serves FOUR series, not just Q&A.
    -- qa_id is set only for source_type='qa'; source_key is the universal
    -- dedup handle ('qa:5768', 'exegesis:1234', 'root:Slw', 'poetry:rHm').
    qa_id INTEGER,
    source_type TEXT NOT NULL DEFAULT 'qa',
    source_key TEXT,
    angle TEXT,
    self_score REAL,
    anchor_ref TEXT NOT NULL,
    theme TEXT,
    title TEXT,
    script_json TEXT,
    payload_json TEXT,
    match_snapshot TEXT,
    format TEXT DEFAULT 'short',
    filename TEXT,
    file_size INTEGER,
    status TEXT DEFAULT 'candidate',
    -- Gate A (punchiness)
    punch_ok INTEGER,
    punch_report TEXT,
    -- Gate B (match)
    match_ok INTEGER,
    match_report TEXT,
    -- safety
    safety_ok INTEGER,
    -- youtube / lifecycle
    triggered_by TEXT,
    uploaded_to_youtube INTEGER DEFAULT 0,
    youtube_video_id TEXT,
    auto_upload_skipped INTEGER DEFAULT 0,
    youtube_title TEXT,
    youtube_description TEXT,
    youtube_tags TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    pipeline_id INTEGER,
    rendering INTEGER DEFAULT 0,
    edit_token_hash TEXT,
    edit_token_expires TEXT
);
CREATE INDEX IF NOT EXISTS idx_qa_videos_status ON qa_videos(status);
CREATE INDEX IF NOT EXISTS idx_qa_videos_qa ON qa_videos(qa_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_qa_videos_source_key ON qa_videos(source_key);

-- The idea layer: mined candidates with self-ratings. This is the
-- generation loop's MEMORY — rejected ideas stay recorded (with the
-- rationale) so they are never re-proposed.
CREATE TABLE IF NOT EXISTS video_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_key TEXT NOT NULL UNIQUE,
    anchor_ref TEXT,
    angle TEXT,
    hook_sketch TEXT,
    self_score REAL,
    rationale TEXT,
    status TEXT DEFAULT 'proposed',  -- proposed|drafted|rejected_score|rejected_gate|duplicate|starred
    video_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_video_candidates_status ON video_candidates(status);

-- The lessons ledger: editorial doctrine LEARNED from operator verdicts,
-- operator edits, and panel findings. Active lessons are injected into
-- every drafting context AND the calibration-judge's checklist, so each
-- verdict permanently improves future scripts. The operator can retire
-- or edit lessons on prod (prod is truth for text+status of existing
-- keys; the loop only creates new ones).
CREATE TABLE IF NOT EXISTS studio_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_key TEXT NOT NULL UNIQUE,
    lesson TEXT NOT NULL,
    source TEXT NOT NULL,        -- operator_reject|operator_edit|panel|seed|manual
    evidence TEXT,               -- the verdict/edit/finding that taught it, quoted
    status TEXT DEFAULT 'active',-- active|retired|flagged
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT
);
"""


def ensure_tables(conn) -> None:
    # One-time rebuild from the legacy Q&A-only shape (qa_id NOT NULL +
    # UNIQUE(qa_id)) to the studio shape (qa_id nullable, source_key is
    # the universal dedup handle). SQLite can't ALTER constraints, so:
    # create the new table, copy the intersection of columns, swap.
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='qa_videos' AND type='table'"
    ).fetchone()
    if row and ("UNIQUE(qa_id)" in row[0] or "qa_id INTEGER NOT NULL" in row[0]):
        old_cols = [r[1] for r in conn.execute("PRAGMA table_info(qa_videos)").fetchall()]
        conn.execute("ALTER TABLE qa_videos RENAME TO qa_videos_legacy")
        conn.executescript(SCHEMA)
        new_cols = [r[1] for r in conn.execute("PRAGMA table_info(qa_videos)").fetchall()]
        common = [c for c in old_cols if c in new_cols]
        collist = ", ".join(common)
        conn.execute(
            f"INSERT INTO qa_videos ({collist}) SELECT {collist} FROM qa_videos_legacy"
        )
        conn.execute("DROP TABLE qa_videos_legacy")
        conn.commit()

    conn.executescript(SCHEMA)
    # Migrations for columns added after the first deploy (CREATE IF NOT
    # EXISTS never alters an existing table).
    cols = {r[1] for r in conn.execute("PRAGMA table_info(qa_videos)").fetchall()}
    if "rendering" not in cols:
        conn.execute("ALTER TABLE qa_videos ADD COLUMN rendering INTEGER DEFAULT 0")
    # "Ask AI to Edit" handoff: a per-row token (hash + expiry) lets a
    # local Claude Code session edit THIS script through the gate-checked
    # agent endpoint without an admin login.
    if "edit_token_hash" not in cols:
        conn.execute("ALTER TABLE qa_videos ADD COLUMN edit_token_hash TEXT")
    if "edit_token_expires" not in cols:
        conn.execute("ALTER TABLE qa_videos ADD COLUMN edit_token_expires TEXT")
    for col, ddl in (("source_type", "TEXT NOT NULL DEFAULT 'qa'"),
                     ("source_key", "TEXT"), ("angle", "TEXT"), ("self_score", "REAL"),
                     ("quality_report", "TEXT")):
        if col not in cols:
            conn.execute(f"ALTER TABLE qa_videos ADD COLUMN {col} {ddl}")
    # Backfill the universal dedup handle for legacy Q&A rows, then
    # enforce it going forward.
    conn.execute(
        "UPDATE qa_videos SET source_key='qa:'||qa_id "
        "WHERE source_key IS NULL AND qa_id IS NOT NULL"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_qa_videos_source_key ON qa_videos(source_key)"
    )
    # Script-first review model (2026-07): humans review SCRIPTS, not
    # renders — the legacy 'rendered' status folds into gate_passed (the
    # rendered file, when present, is just an optional preview).
    conn.execute("UPDATE qa_videos SET status='gate_passed' WHERE status='rendered'")
    conn.commit()


def sample_candidates(conn, limit: int = 20, exclude_built: bool = True) -> list[dict]:
    """Rated-5 verse Q&A not yet built into a video, newest first."""
    ensure_tables(conn)
    exclude = "AND ac.id NOT IN (SELECT qa_id FROM qa_videos)" if exclude_built else ""
    # Fetch the whole (small) pool, then exclude already-drafted ids and
    # cap to `limit` AFTER exclusion, so committed drafts don't shrink the
    # batch below the requested size.
    rows = conn.execute(
        f"""
        SELECT ac.id, ac.page_key, ac.category, ac.quality_score,
               ac.question, ac.answer, ac.generation_meta
        FROM assistant_conversations ac
        WHERE ac.source='ai' AND ac.quality_score=5.0 AND ac.page_type='verse'
          AND COALESCE(ac.hidden,0)=0
          {exclude}
        ORDER BY ac.id DESC
        """
    ).fetchall()
    drafted = _drafted_qa_ids()
    out = []
    for r in rows:
        if len(out) >= limit:
            break
        if r["id"] in drafted:
            continue  # already has a committed draft (cross-run dedup)
        meta = {}
        try:
            meta = json.loads(r["generation_meta"] or "{}")
        except Exception:
            meta = {}
        out.append({
            "qa_id": r["id"],
            "anchor_ref": r["page_key"],
            "category": r["category"],
            "question": r["question"],
            "answer": r["answer"],
            "cited_refs": meta.get("cited_refs") or [],
            "needs_voice_revision": bool(meta.get("needs_voice_revision")),
        })
    return out


def upsert_by_source(conn, source_type: str, source_key: str,
                     anchor_ref: str, **fields) -> int:
    """Universal bank upsert — one row per source_key across all series."""
    ensure_tables(conn)
    row = conn.execute(
        "SELECT id FROM qa_videos WHERE source_key=?", (source_key,)
    ).fetchone()
    cols = {"source_type": source_type, "anchor_ref": anchor_ref, **fields}
    if row:
        sets = ", ".join(f"{k}=?" for k in cols)
        conn.execute(f"UPDATE qa_videos SET {sets} WHERE source_key=?",
                     (*cols.values(), source_key))
        vid = row["id"]
    else:
        keys = ["source_key"] + list(cols.keys())
        ph = ", ".join("?" for _ in keys)
        conn.execute(f"INSERT INTO qa_videos ({', '.join(keys)}) VALUES ({ph})",
                     (source_key, *cols.values()))
        vid = conn.execute(
            "SELECT id FROM qa_videos WHERE source_key=?", (source_key,)
        ).fetchone()["id"]
    conn.commit()
    return vid


def upsert_video(conn, qa_id: int, anchor_ref: str, **fields) -> int:
    """Legacy Q&A-series wrapper around upsert_by_source."""
    return upsert_by_source(conn, "qa", f"qa:{qa_id}", anchor_ref,
                            qa_id=qa_id, **fields)


def set_status(conn, qa_id: int, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE qa_videos SET status=?, error_message=? WHERE qa_id=?",
        (status, error, qa_id),
    )
    conn.commit()
