"""Verse content moderation for the educational pipeline.

Filters out verses that would distract a general-audience viewer
from the linguistic / etymological point of an educational short —
houris in paradise, violent commands, gendered legal rules,
specific punishments, hellfire imagery, etc. The controversial
status is sticky per (chapter, verse), so every result is cached
in `verse_safety_cache` and reused for ~30 days.

Public surface:
    ensure_table(conn)
        Create the cache table on app boot.

    is_verse_safe(conn, chapter, verse) -> bool
        True for safe / unknown / Ollama-down (permissive default —
        we'd rather let one through than starve the pipeline).
        False only when Ollama positively flagged the verse.

    safety_status(conn, chapter, verse) -> dict | None
        For UI/debug. Returns the cache row as-is, or None on miss.

    bulk_filter_safe(conn, refs) -> list
        Filter a list of (chapter, verse) tuples down to safe ones.
        Calls Ollama on cache misses sequentially (typical hit rate
        is high after the first run through a root's pool).

The Ollama call uses the same `ollama_metadata_model` preference as
metadata generation so the operator only configures one model.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Iterable

import requests


# ---------------------------------------------------------------------------
#  Schema
# ---------------------------------------------------------------------------

CACHE_TTL_DAYS = 30


def ensure_table(conn: sqlite3.Connection) -> None:
    """Idempotent — safe to call on every app boot."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verse_safety_cache (
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('safe','controversial','unknown')),
            reason TEXT,
            model TEXT,
            checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chapter, verse)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_vsafety_status ON verse_safety_cache (status)"
    )
    conn.commit()


# ---------------------------------------------------------------------------
#  Ollama prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You screen Quran verses for use in a SHORT EDUCATIONAL VIDEO about an "
    "Arabic word's etymology. Your job: flag a verse as 'controversial' "
    "ONLY if quoting it in a general-audience video could realistically "
    "spark non-linguistic debate or backlash from viewers focused on the "
    "topic rather than the word.\n\n"
    "CONTROVERSIAL — flag these:\n"
    "  - Houris / wide-eyed companions / paradise sexual imagery\n"
    "  - Violence as positive command (kill, fight, slay)\n"
    "  - Gendered legal rules (polygyny, women's testimony, inheritance)\n"
    "  - Hijab / dress / modesty rules for women\n"
    "  - Specific corporal punishments (hand-cutting, lashing, stoning)\n"
    "  - Slavery, captives, 'what your right hands possess'\n"
    "  - Apostasy, cursing, vivid hellfire torture imagery\n"
    "  - Sect-specific polemics against Christians, Jews, polytheists\n\n"
    "SAFE — do NOT flag these:\n"
    "  - Nature, animals, weather, agriculture, geography\n"
    "  - General prophet stories (Moses, Joseph, Jesus narratives)\n"
    "  - Mercy, gratitude, patience, kindness, justice in general\n"
    "  - Creation, signs of God, day/night, water, mountains\n"
    "  - Generic moral teaching, prayer, charity\n"
    "  - Historical references, names of places\n\n"
    "Answer with a single JSON object:\n"
    '{\"status\": \"safe\" | \"controversial\", \"reason\": \"≤15 words\"}'
)


def _build_user_prompt(chapter: int, verse: int, arabic: str, translation: str) -> str:
    return (
        f"Quran {chapter}:{verse}\n\n"
        f"Arabic: {arabic}\n\n"
        f"English: {translation}\n\n"
        "Respond with ONLY the JSON object — no preamble, no code fence."
    )


def _strip_to_json(text: str) -> str:
    """Strip <think> blocks and code fences. Used by the same idiom as
    the metadata generator."""
    s = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    s = re.sub(r"^```(?:json)?\s*\n?", "", s.strip())
    s = re.sub(r"\n?```\s*$", "", s.strip())
    return s


# ---------------------------------------------------------------------------
#  Ollama call
# ---------------------------------------------------------------------------

def _call_ollama(
    *,
    chapter: int,
    verse: int,
    arabic: str,
    translation: str,
    base_url: str,
    model: str,
    api_key: str,
    timeout: int = 90,
) -> tuple[str, str, str]:
    """Returns (status, reason, model). status in
    {'safe','controversial','unknown'}. 'unknown' on any failure."""
    if not (model and arabic and translation):
        return "unknown", "missing input", model or ""
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
                    {"role": "user", "content": _build_user_prompt(chapter, verse, arabic, translation)},
                ],
                "stream": False,
                # Low temperature — this is a yes/no decision, not creative.
                "options": {"temperature": 0.1},
                "think": False,
            },
            timeout=timeout,
        )
    except requests.RequestException as e:
        return "unknown", f"transport: {e}"[:200], model
    if resp.status_code != 200:
        return "unknown", f"http {resp.status_code}", model
    content = (resp.json().get("message") or {}).get("content", "")
    s = _strip_to_json(content)
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        return "unknown", "no json in response", model
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return "unknown", "bad json", model
    status = (obj.get("status") or "").strip().lower()
    if status not in ("safe", "controversial"):
        return "unknown", f"unexpected status: {status!r}", model
    reason = (obj.get("reason") or "").strip()[:200]
    return status, reason, model


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def safety_status(conn: sqlite3.Connection, chapter: int, verse: int) -> dict | None:
    row = conn.execute(
        "SELECT chapter, verse, status, reason, model, checked_at "
        "FROM verse_safety_cache WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    return dict(row) if row else None


def _is_cache_fresh(checked_at: str | None) -> bool:
    if not checked_at:
        return False
    try:
        # SQLite CURRENT_TIMESTAMP is "YYYY-MM-DD HH:MM:SS"
        dt = datetime.fromisoformat(checked_at.replace(" ", "T"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return datetime.now(timezone.utc) - dt < timedelta(days=CACHE_TTL_DAYS)


def _fetch_verse(conn, chapter: int, verse: int) -> tuple[str, str]:
    v = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    t = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    return (
        (v["text_uthmani"] if v else ""),
        (t["text_en"] if t else ""),
    )


def _ollama_prefs(conn) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in conn.execute(
        "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
    ).fetchall():
        out[r["key"]] = r["value"]
    return out


def is_verse_safe(
    conn: sqlite3.Connection,
    chapter: int,
    verse: int,
    *,
    allow_ollama_call: bool = True,
) -> bool:
    """Return True if the verse is safe to feature in an educational
    video, False if Ollama positively flagged it as controversial.

    Permissive by default: cache miss + Ollama unavailable returns
    True so the pipeline doesn't get starved when the metadata
    server is down. The trade-off is that the FIRST pass over a
    pool may include a controversial verse; subsequent passes
    benefit from the cache.

    Set `allow_ollama_call=False` to skip the Ollama call entirely
    and return based purely on the cache (used by bulk callers
    that want to surface only known-safe verses)."""
    cached = safety_status(conn, chapter, verse)
    if cached and _is_cache_fresh(cached.get("checked_at")):
        # 'unknown' is treated as safe by the permissive default —
        # we couldn't decide, don't block.
        return cached["status"] != "controversial"

    if not allow_ollama_call:
        # No cache hit and caller explicitly opted out of Ollama —
        # treat as safe (permissive).
        return True

    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (prefs.get("ollama_metadata_model") or prefs.get("ollama_model") or "").strip()
    api_key = prefs.get("ollama_api_key") or ""
    arabic, translation = _fetch_verse(conn, chapter, verse)
    if not arabic or not translation:
        # Don't have data to assess — accept and don't pollute cache.
        return True

    status, reason, model_used = _call_ollama(
        chapter=chapter, verse=verse,
        arabic=arabic, translation=translation,
        base_url=base_url, model=model, api_key=api_key,
    )
    # Cache the result (including 'unknown' so the same verse doesn't
    # retry Ollama on every render — TTL covers re-checks).
    try:
        conn.execute(
            "INSERT OR REPLACE INTO verse_safety_cache "
            "(chapter, verse, status, reason, model, checked_at) "
            "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (chapter, verse, status, reason, model_used),
        )
        conn.commit()
    except Exception as e:
        print(f"[verse-safety] cache write failed for {chapter}:{verse}: {e}")
    if status == "controversial":
        print(f"[verse-safety] flagged {chapter}:{verse} controversial: {reason}")
    return status != "controversial"


def bulk_filter_safe(
    conn: sqlite3.Connection,
    refs: Iterable[tuple[int, int]],
    *,
    allow_ollama_call: bool = True,
) -> list[tuple[int, int]]:
    """Convenience: filter a list of (chapter, verse) tuples down to
    those known/believed-safe. Sequential Ollama calls on misses —
    parallelize later if it becomes a bottleneck."""
    out: list[tuple[int, int]] = []
    for c, v in refs:
        if is_verse_safe(conn, int(c), int(v), allow_ollama_call=allow_ollama_call):
            out.append((int(c), int(v)))
    return out


