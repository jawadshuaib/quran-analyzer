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
    qa_id INTEGER NOT NULL,
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
    UNIQUE(qa_id)
);
CREATE INDEX IF NOT EXISTS idx_qa_videos_status ON qa_videos(status);
CREATE INDEX IF NOT EXISTS idx_qa_videos_qa ON qa_videos(qa_id);
"""


def ensure_tables(conn) -> None:
    conn.executescript(SCHEMA)
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


def upsert_video(conn, qa_id: int, anchor_ref: str, **fields) -> int:
    ensure_tables(conn)
    row = conn.execute("SELECT id FROM qa_videos WHERE qa_id=?", (qa_id,)).fetchone()
    cols = {"anchor_ref": anchor_ref, **fields}
    if row:
        sets = ", ".join(f"{k}=?" for k in cols)
        conn.execute(f"UPDATE qa_videos SET {sets} WHERE qa_id=?",
                     (*cols.values(), qa_id))
        vid = row["id"]
    else:
        keys = ["qa_id"] + list(cols.keys())
        ph = ", ".join("?" for _ in keys)
        conn.execute(f"INSERT INTO qa_videos ({', '.join(keys)}) VALUES ({ph})",
                     (qa_id, *cols.values()))
        vid = conn.execute("SELECT id FROM qa_videos WHERE qa_id=?", (qa_id,)).fetchone()["id"]
    conn.commit()
    return vid


def set_status(conn, qa_id: int, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE qa_videos SET status=?, error_message=? WHERE qa_id=?",
        (status, error, qa_id),
    )
    conn.commit()
