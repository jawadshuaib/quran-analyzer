"""Flask API for al-nuqta."""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
from collections import OrderedDict, defaultdict
from urllib.parse import quote

import arabic_reshaper
import secrets
from bidi.algorithm import get_display
from datetime import datetime, timezone
from functools import wraps

import bcrypt
import jwt
import numpy as np
import requests
from flask import Flask, Response, jsonify, redirect, request, send_from_directory
from flask_cors import CORS

# Bump this when mnemonic images are regenerated to bust browser caches
_MNEMONIC_VERSION = 12

# In Docker, static/ sits next to app.py; in local dev it doesn't exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SERVE_STATIC = os.path.isdir(STATIC_DIR)

app = Flask(
    __name__,
    static_folder=None,  # We handle static files in the catch-all route
)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit

# Secret key for JWT — persisted so tokens survive restarts
_SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), "data", ".admin_secret")
if os.path.isfile(_SECRET_KEY_FILE):
    with open(_SECRET_KEY_FILE) as f:
        app.config["SECRET_KEY"] = f.read().strip()
else:
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    fd = os.open(_SECRET_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(app.config["SECRET_KEY"])

# Return JSON for oversized uploads instead of HTML error page
@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "File too large (max 500MB)"}), 413

# Register public API v1 Blueprint
from api_v1 import v1_bp
app.register_blueprint(v1_bp)

# In Docker the DB lives on a volume at /app/data/quran.db;
# in local dev it's at roots/backend/data/quran.db — same relative path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")

# Surah names (English), index 0 is unused so SURAH_NAMES[1] == "Al-Fatihah"
SURAH_NAMES = [
    "", "Al-Fatihah", "Al-Baqarah", "Ali 'Imran", "An-Nisa", "Al-Ma'idah",
    "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
    "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
    "An-Nahl", "Al-Isra", "Al-Kahf", "Maryam", "Taha",
    "Al-Anbya", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan",
    "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum",
    "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir",
    "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
    "Fussilat", "Ash-Shuraa", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah",
    "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
    "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman",
    "Al-Waqi'ah", "Al-Hadid", "Al-Mujadila", "Al-Hashr", "Al-Mumtahanah",
    "As-Saf", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq",
    "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
    "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah",
    "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at", "'Abasa",
    "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj",
    "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Ash-Shams", "Al-Layl", "Ad-Duhaa", "Ash-Sharh", "At-Tin",
    "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat",
    "Al-Qari'ah", "At-Takathur", "Al-'Asr", "Al-Humazah", "Al-Fil",
    "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
]


def _surah_name(ch: int) -> str:
    return SURAH_NAMES[ch] if ch < len(SURAH_NAMES) else f"Surah {ch}"


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_word_glosses_table():
    """Create the word_glosses cache table if it doesn't exist."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS word_glosses (
                chapter INTEGER,
                verse INTEGER,
                word_pos INTEGER,
                translation_en TEXT,
                PRIMARY KEY (chapter, verse, word_pos)
            )
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_word_glosses_table()


def _ensure_ai_translation_tables():
    """Create the AI translation tables if they don't exist."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_translation_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT NOT NULL UNIQUE,
                model_name TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                temperature REAL DEFAULT 0.3,
                context_verses_before INTEGER DEFAULT 3,
                context_verses_after INTEGER DEFAULT 3,
                related_verses_limit INTEGER DEFAULT 7,
                methodology_notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                translation_text TEXT NOT NULL,
                departure_notes TEXT,
                full_prompt TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES ai_translation_configs(id),
                UNIQUE (chapter, verse, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_translations_verse
            ON ai_translations (chapter, verse)
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_ai_translation_tables()


def _ensure_ai_word_meanings_table():
    """Create the ai_word_meanings table if it doesn't exist."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_word_meanings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                word_pos INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                meaning_short TEXT NOT NULL,
                meaning_detailed TEXT NOT NULL,
                semantic_field TEXT,
                cross_ref_notes TEXT,
                cognate_notes TEXT,
                morphology_notes TEXT,
                departure_notes TEXT,
                full_prompt TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES ai_translation_configs(id),
                UNIQUE (chapter, verse, word_pos, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_word_meanings_verse
            ON ai_word_meanings (chapter, verse)
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_ai_word_meanings_table()


def _ensure_judge_columns():
    """Add preferred_translation and preferred_source columns if missing."""
    conn = get_db()
    try:
        for col, coltype in [
            ("preferred_translation", "TEXT"),
            ("preferred_source", "TEXT"),
            ("judge_reasoning", "TEXT"),
        ]:
            try:
                conn.execute(
                    f"ALTER TABLE ai_word_meanings ADD COLUMN {col} {coltype}"
                )
                conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists
    finally:
        conn.close()


_ensure_judge_columns()


def _ensure_align_checked_column():
    """Add align_checked_at column to ai_word_meanings if missing."""
    conn = get_db()
    try:
        try:
            conn.execute(
                "ALTER TABLE ai_word_meanings ADD COLUMN align_checked_at TEXT"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
    finally:
        conn.close()


_ensure_align_checked_column()


def _ensure_ai_root_meanings_table():
    """Create the ai_root_meanings table if it doesn't exist."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_root_meanings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_buckwalter TEXT NOT NULL,
                config_id INTEGER NOT NULL,
                primary_meaning TEXT NOT NULL,
                detailed_meaning TEXT NOT NULL,
                semantic_field TEXT,
                evidence_summary TEXT,
                full_prompt TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES ai_translation_configs(id),
                UNIQUE (root_buckwalter, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_root_meanings_root
            ON ai_root_meanings (root_buckwalter)
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_ai_root_meanings_table()


def _ensure_thematic_context_tables():
    """Create versioned Qur'an-only thematic context tables if missing."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS thematic_context_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT NOT NULL UNIQUE,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                methodology_notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verse_thematic_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                passage_start_ayah INTEGER,
                passage_end_ayah INTEGER,
                passage_theme TEXT,
                passage_confidence REAL,
                surah_role_summary TEXT,
                surah_role_confidence REAL,
                neighbor_surah_summary TEXT,
                neighbor_surah_confidence REAL,
                quran_wide_links_json TEXT,
                evidence_json TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES thematic_context_configs(id),
                UNIQUE (chapter, verse, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_thematic_context_verse
            ON verse_thematic_contexts (chapter, verse, created_at DESC)
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_thematic_context_tables()


def _ensure_assistant_conversations_table():
    for _attempt in range(15):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=60)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assistant_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    page_type TEXT NOT NULL,
                    page_key TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    context_summary TEXT,
                    model_used TEXT,
                    response_time_ms INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_assistant_conv_page
                ON assistant_conversations (page_type, page_key, created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_assistant_conv_session
                ON assistant_conversations (session_id, created_at DESC)
            """)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError:
            import time as _t
            _t.sleep(3)
    # If all retries fail, print warning but don't crash — table will be created lazily
    print("WARNING: Could not create assistant_conversations table (DB locked). Will retry on first use.")


try:
    _ensure_assistant_conversations_table()
except Exception as e:
    print(f"WARNING: assistant table setup failed: {e}")


def _ensure_insight_evolution_table():
    """Create the insight_evolution_log table for tracking Q&A-driven translation improvements."""
    for _attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=60)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insight_evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse INTEGER NOT NULL,
                    word_pos INTEGER,
                    status TEXT NOT NULL,
                    target_table TEXT,
                    target_column TEXT,
                    target_row_id INTEGER,
                    old_value TEXT,
                    new_value TEXT,
                    evaluation_model TEXT NOT NULL,
                    evaluation_reasoning TEXT NOT NULL,
                    confidence_score REAL,
                    qa_question TEXT NOT NULL,
                    qa_answer TEXT NOT NULL,
                    reverted_at TEXT,
                    reverted_by TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_insight_evo_verse
                ON insight_evolution_log (chapter, verse, created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_insight_evo_status
                ON insight_evolution_log (status, created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_insight_evo_conversation
                ON insight_evolution_log (conversation_id)
            """)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError:
            time.sleep(3)
    print("WARNING: Could not create insight_evolution_log table (DB locked).")


try:
    _ensure_insight_evolution_table()
except Exception as e:
    print(f"WARNING: insight evolution table setup failed: {e}")


def _ensure_surah_context_tables():
    """Create versioned Surah-so-far context tables if missing."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS surah_context_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT NOT NULL UNIQUE,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                methodology_notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verse_surah_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                summary_so_far TEXT,
                current_verse_focus TEXT,
                key_verses_json TEXT,
                summary_points_json TEXT,
                lexical_continuity_json TEXT,
                signal_score REAL,
                verifier_report_json TEXT,
                evidence_json TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES surah_context_configs(id),
                UNIQUE (chapter, verse, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_surah_context_verse
            ON verse_surah_contexts (chapter, verse, created_at DESC)
        """)
        for col, coltype in [
            ("summary_points_json", "TEXT"),
            ("lexical_continuity_json", "TEXT"),
            ("signal_score", "REAL"),
            ("verifier_report_json", "TEXT"),
        ]:
            try:
                conn.execute(
                    f"ALTER TABLE verse_surah_contexts ADD COLUMN {col} {coltype}"
                )
            except sqlite3.OperationalError:
                pass
        conn.commit()
    finally:
        conn.close()


_ensure_surah_context_tables()


def _ensure_grammar_insight_tables():
    """Create versioned grammar insight tables if missing."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grammar_insight_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT NOT NULL UNIQUE,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                methodology_notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verse_grammar_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                overview_text TEXT,
                insights_json TEXT,
                signal_score REAL,
                verifier_report_json TEXT,
                evidence_json TEXT,
                raw_response TEXT,
                model_response_time_ms INTEGER,
                generation_version TEXT,
                insights_v7_json TEXT,
                quality_json TEXT,
                overall_confidence REAL,
                model_confidence_raw REAL,
                display_json TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (config_id) REFERENCES grammar_insight_configs(id),
                UNIQUE (chapter, verse, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_grammar_insights_verse
            ON verse_grammar_insights (chapter, verse, created_at DESC)
        """)
        for col, coltype in [
            ("signal_score", "REAL"),
            ("verifier_report_json", "TEXT"),
            ("generation_version", "TEXT"),
            ("insights_v7_json", "TEXT"),
            ("quality_json", "TEXT"),
            ("overall_confidence", "REAL"),
            ("model_confidence_raw", "REAL"),
            ("display_json", "TEXT"),
        ]:
            try:
                conn.execute(
                    f"ALTER TABLE verse_grammar_insights ADD COLUMN {col} {coltype}"
                )
            except sqlite3.OperationalError:
                pass
        conn.commit()
    finally:
        conn.close()


_ensure_grammar_insight_tables()


def _ensure_learning_tables():
    """Create learning curriculum tables if they don't exist."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_curriculum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_buckwalter TEXT NOT NULL UNIQUE,
                root_arabic TEXT NOT NULL,
                unit_number INTEGER NOT NULL,
                unit_theme TEXT NOT NULL,
                priority_score REAL NOT NULL,
                frequency_rank INTEGER NOT NULL,
                theological_importance REAL,
                derivative_richness INTEGER,
                anchor_verse_chapter INTEGER NOT NULL,
                anchor_verse_verse INTEGER NOT NULL,
                root_story TEXT NOT NULL,
                teaching_notes TEXT,
                related_roots TEXT,
                config_id INTEGER,
                mnemonic_image_path TEXT,
                mnemonic_caption TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_derivatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_buckwalter TEXT NOT NULL,
                lemma_buckwalter TEXT NOT NULL,
                lemma_arabic TEXT NOT NULL,
                pos TEXT,
                verb_form TEXT,
                frequency INTEGER NOT NULL,
                meaning_gloss TEXT NOT NULL,
                semantic_shift TEXT,
                display_order INTEGER NOT NULL,
                FOREIGN KEY (root_buckwalter) REFERENCES learning_curriculum(root_buckwalter)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_context_verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_buckwalter TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                target_lemma_buckwalter TEXT,
                verse_role TEXT NOT NULL,
                teaching_note TEXT,
                display_order INTEGER NOT NULL,
                FOREIGN KEY (root_buckwalter) REFERENCES learning_curriculum(root_buckwalter)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_learning_deriv_root
            ON learning_derivatives (root_buckwalter)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_learning_ctx_root
            ON learning_context_verses (root_buckwalter)
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_learning_tables()


def _ensure_mnemonic_columns():
    """Add mnemonic_image_path and mnemonic_caption columns if missing."""
    conn = get_db()
    try:
        for col, coltype in [
            ("mnemonic_image_path", "TEXT"),
            ("mnemonic_caption", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE learning_curriculum ADD COLUMN {col} {coltype}")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists
    finally:
        conn.close()


_ensure_mnemonic_columns()


def _ensure_verse_themes_table():
    """Create the verse_themes table for storing thematic tags per verse."""
    for _attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=60)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verse_themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter INTEGER NOT NULL,
                    verse INTEGER NOT NULL,
                    theme TEXT NOT NULL,
                    confidence REAL,
                    config_id INTEGER,
                    model_used TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(chapter, verse, theme)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_verse_themes_verse
                ON verse_themes (chapter, verse)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_verse_themes_theme
                ON verse_themes (theme)
            """)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError:
            time.sleep(3)
    print("WARNING: Could not create verse_themes table (DB locked).")


try:
    _ensure_verse_themes_table()
except Exception as e:
    print(f"WARNING: verse_themes table setup failed: {e}")


# --------------- Lemma-Based IDF-Weighted Containment Engine ---------------

ROOT_DISCOUNT = 0.5  # Root-only matches get half credit vs lemma matches

_lemma_idf = {}                # lemma_bw -> float
_root_idf = {}                 # root_bw -> float
_form_idf = {}                 # form_bw -> float
_verse_lemmas = {}             # (ch, v) -> set of lemma_bw
_verse_roots = {}              # (ch, v) -> set of root_bw
_lemma_inv = defaultdict(set)  # lemma_bw -> set of (ch, v)
_root_inv = defaultdict(set)   # root_bw -> set of (ch, v)
_form_inv = defaultdict(set)   # form_bw -> set of (ch, v)
_lemma_roots = defaultdict(set)  # lemma_bw -> set of root_bw
_root_arabic_map = {}          # root_bw -> root_arabic string

THEMATIC_MIN_LINK_CONFIDENCE = 0.62
THEMATIC_MIN_PASSAGE_CONFIDENCE = 0.68
THEMATIC_MIN_ROLE_CONFIDENCE = 0.68
THEMATIC_GENERIC_PHRASES = (
    "divine punishment",
    "divine judgment",
    "human schemes",
    "futility of opposing",
    "those who oppose",
    "human arrogance",
)
GRAMMAR_INSIGHT_MIN_SCORE = 0.68


def _is_grammar_insight_displayable(score: float, insights: list[dict]) -> bool:
    """Two-tier display gate for grammar insights.

    Tier A (full): score >= 0.70 and >=2 substantial insights.
    Tier B (single): score >= 0.50 and >=1 high-confidence grounded insight.
    """
    substantial = 0
    tier_b_hit = False
    for it in insights:
        if not isinstance(it, dict):
            continue
        txt = str(it.get("insight", "")).strip()
        if len(txt) >= 90:
            substantial += 1
        conf = float(it.get("confidence", 0.0) or 0.0)
        mev = it.get("morph_evidence", [])
        if (
            conf >= 0.80
            and isinstance(mev, list)
            and len(mev) >= 1
            and len(txt) >= 90
        ):
            tier_b_hit = True

    if score >= 0.70 and substantial >= 2:
        return True
    if score >= 0.50 and tier_b_hit:
        return True
    return False


def _thematic_text_is_generic(text: str) -> bool:
    low = (text or "").strip().lower()
    if len(low) < 28:
        return True
    return any(p in low for p in THEMATIC_GENERIC_PHRASES)


def _is_thematic_context_displayable(row, links: list[dict]) -> bool:
    high_links = 0
    for item in links:
        if not isinstance(item, dict):
            continue
        refs = item.get("related_verses", [])
        conf = float(item.get("confidence", 0) or 0)
        summary = str(item.get("summary", "") or "")
        theme = str(item.get("theme", "") or "")
        if len(refs) >= 2 and conf >= THEMATIC_MIN_LINK_CONFIDENCE:
            if not (_thematic_text_is_generic(summary) and _thematic_text_is_generic(theme)):
                high_links += 1

    p_conf = float(row["passage_confidence"] or 0)
    p_theme = str(row["passage_theme"] or "")
    p_start = int(row["passage_start_ayah"] or row["verse"] or 0)
    p_end = int(row["passage_end_ayah"] or row["verse"] or 0)
    has_passage = (
        p_conf >= THEMATIC_MIN_PASSAGE_CONFIDENCE
        and (p_end - p_start + 1) >= 2
        and not _thematic_text_is_generic(p_theme)
    )

    role_conf = float(row["surah_role_confidence"] or 0)
    role_txt = str(row["surah_role_summary"] or "")
    has_role = role_conf >= THEMATIC_MIN_ROLE_CONFIDENCE and not _thematic_text_is_generic(role_txt)

    neighbor_conf = float(row["neighbor_surah_confidence"] or 0)
    neighbor_txt = str(row["neighbor_surah_summary"] or "")
    has_neighbor = neighbor_conf >= 0.65 and not _thematic_text_is_generic(neighbor_txt)

    score = 0
    if high_links >= 2:
        score += 1
    if has_passage:
        score += 1
    if has_role:
        score += 1
    if has_neighbor:
        score += 1
    return high_links >= 2 and (has_passage or has_role) and score >= 3


def _build_similarity_engine():
    """Pre-compute lemma/root IDF values and inverted indexes for all verses."""
    conn = get_db()
    try:
        # Query 1: Lemma profiles per verse
        lemma_rows = conn.execute(
            "SELECT DISTINCT chapter, verse, lemma_buckwalter "
            "FROM morphology "
            "WHERE lemma_buckwalter IS NOT NULL AND lemma_buckwalter != ''"
        ).fetchall()

        # Query 2: Root profiles per verse + arabic mapping
        root_rows = conn.execute(
            "SELECT DISTINCT chapter, verse, root_buckwalter, root_arabic "
            "FROM morphology "
            "WHERE root_buckwalter IS NOT NULL AND root_buckwalter != ''"
        ).fetchall()

        # Query 3: Lemma-to-root mapping
        lr_rows = conn.execute(
            "SELECT DISTINCT lemma_buckwalter, root_buckwalter "
            "FROM morphology "
            "WHERE lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '' "
            "AND root_buckwalter IS NOT NULL AND root_buckwalter != ''"
        ).fetchall()

        # Query 4: Form profiles per verse (for particles with no lemma/root)
        form_rows = conn.execute(
            "SELECT DISTINCT chapter, verse, form_buckwalter "
            "FROM morphology "
            "WHERE form_buckwalter IS NOT NULL AND form_buckwalter != ''"
        ).fetchall()
    finally:
        conn.close()

    if not lemma_rows and not root_rows:
        print("Similarity engine: no morphology data found")
        return

    # Build lemma profiles and doc frequency
    lemma_doc_freq = defaultdict(int)  # lemma_bw -> number of verses containing it
    verse_lemma_sets = defaultdict(set)

    for row in lemma_rows:
        key = (row["chapter"], row["verse"])
        lbw = row["lemma_buckwalter"]
        verse_lemma_sets[key].add(lbw)

    for key, lemmas in verse_lemma_sets.items():
        _verse_lemmas[key] = lemmas
        for lbw in lemmas:
            lemma_doc_freq[lbw] += 1
            _lemma_inv[lbw].add(key)

    # Build root profiles and doc frequency
    root_doc_freq = defaultdict(int)
    verse_root_sets = defaultdict(set)

    for row in root_rows:
        key = (row["chapter"], row["verse"])
        rbw = row["root_buckwalter"]
        verse_root_sets[key].add(rbw)
        _root_arabic_map[rbw] = row["root_arabic"]

    for key, roots in verse_root_sets.items():
        _verse_roots[key] = roots
        for rbw in roots:
            root_doc_freq[rbw] += 1
            _root_inv[rbw].add(key)

    # Build lemma-to-root mapping
    for row in lr_rows:
        _lemma_roots[row["lemma_buckwalter"]].add(row["root_buckwalter"])

    # Build form inverted index and doc frequency
    form_doc_freq = defaultdict(int)
    for row in form_rows:
        key = (row["chapter"], row["verse"])
        fbw = row["form_buckwalter"]
        form_doc_freq[fbw] += 1
        _form_inv[fbw].add(key)

    # Compute IDF values
    total_verses = len(set(list(_verse_lemmas.keys()) + list(_verse_roots.keys())))

    for lbw, df in lemma_doc_freq.items():
        _lemma_idf[lbw] = math.log(total_verses / df)

    for rbw, df in root_doc_freq.items():
        _root_idf[rbw] = math.log(total_verses / df)

    for fbw, df in form_doc_freq.items():
        _form_idf[fbw] = math.log(total_verses / df)

    print(
        f"Similarity engine ready: {len(_lemma_idf)} lemmas, "
        f"{len(_root_idf)} roots, {len(_form_idf)} forms, "
        f"~{total_verses} verse profiles"
    )


def _find_related_verses(surah, ayah, limit=10):
    """Find verses most related to (surah, ayah) using IDF-weighted containment."""
    query_key = (surah, ayah)
    query_lemmas = _verse_lemmas.get(query_key)
    query_roots = _verse_roots.get(query_key, set())

    if not query_lemmas:
        return []

    # Gather candidates via both lemma and root inverted indexes
    candidates = set()
    for lbw in query_lemmas:
        candidates.update(_lemma_inv.get(lbw, set()))
    for rbw in query_roots:
        candidates.update(_root_inv.get(rbw, set()))
    candidates.discard(query_key)

    # Remove adjacent verses (same surah, ±2 ayahs)
    adjacent = {(surah, ayah + d) for d in range(-2, 3)}
    candidates -= adjacent

    # Score each candidate by containment
    scored = []
    for cand_key in candidates:
        cand_lemmas = _verse_lemmas.get(cand_key)
        if not cand_lemmas:
            continue
        cand_roots = _verse_roots.get(cand_key, set())

        # Shared lemmas
        shared_lemmas = cand_lemmas & query_lemmas

        # Roots already covered by shared lemmas
        covered_roots = set()
        for lbw in shared_lemmas:
            covered_roots.update(_lemma_roots.get(lbw, set()))

        # Extra shared roots (root matches not already covered by lemma matches)
        extra_shared_roots = (cand_roots & query_roots) - covered_roots

        # Shared weight = full credit for lemmas + discounted credit for root-only
        shared_weight = sum(_lemma_idf.get(lbw, 0) for lbw in shared_lemmas)
        shared_weight += ROOT_DISCOUNT * sum(_root_idf.get(rbw, 0) for rbw in extra_shared_roots)

        if shared_weight == 0:
            continue

        # Candidate total weight = sum of lemma IDF for all candidate lemmas
        cand_total = sum(_lemma_idf.get(lbw, 0) for lbw in cand_lemmas)
        if cand_total == 0:
            continue

        containment = min(shared_weight / cand_total, 1.0)

        # Collect all shared roots for display (from both lemma and root matches)
        all_shared_roots = set()
        for lbw in shared_lemmas:
            all_shared_roots.update(_lemma_roots.get(lbw, set()) & cand_roots)
        all_shared_roots.update(extra_shared_roots)

        scored.append((containment, shared_weight, cand_key, all_shared_roots))

    # Sort by containment DESC, then shared_weight DESC
    scored.sort(key=lambda x: (-x[0], -x[1]))

    return scored[:limit]


_build_similarity_engine()

# --------------- Semantic Embedding Search Engine ---------------

_embedding_model = None       # Lazy-loaded SentenceTransformer
_embedding_model_lock = threading.Lock()
_embedding_matrix = None      # np.ndarray shape (N, dim), pre-normalised
_embedding_keys = []          # list of (chapter, verse) in same order as matrix rows
_embedding_texts = {}         # (chapter, verse) -> text_used for snippets
_EMBEDDING_DIM = 384
_SEMANTIC_MODEL_NAME = "all-MiniLM-L6-v2"


def _load_embedding_matrix():
    """Load pre-computed verse embeddings from DB into a NumPy matrix."""
    global _embedding_matrix, _embedding_keys, _embedding_texts
    conn = get_db()
    try:
        # Check if table exists
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='verse_embeddings'"
        ).fetchone()
        if not tbl:
            print("  Semantic search: verse_embeddings table not found — skipping")
            return
        rows = conn.execute(
            "SELECT chapter, verse, embedding, text_used FROM verse_embeddings "
            "ORDER BY chapter, verse"
        ).fetchall()
        if not rows:
            print("  Semantic search: no embeddings found — skipping")
            return
        keys = []
        texts = {}
        vecs = []
        skipped = 0
        for r in rows:
            ch, v = r["chapter"], r["verse"]
            vec = np.frombuffer(r["embedding"], dtype=np.float32)
            if vec.shape[0] != _EMBEDDING_DIM:
                skipped += 1
                continue
            keys.append((ch, v))
            texts[(ch, v)] = r["text_used"] or ""
            vecs.append(vec)
        if skipped:
            print(f"  WARNING: Skipped {skipped} embeddings with wrong dimensions")
        try:
            _embedding_matrix = np.vstack(vecs)  # (N, 384)
        except ValueError as e:
            print(f"  ERROR: Failed to stack embeddings: {e}")
            _embedding_matrix = None
            return
        _embedding_keys = keys
        _embedding_texts = texts
        print(f"  Semantic search ready: {len(keys)} verse embeddings loaded")
    finally:
        conn.close()


_load_embedding_matrix()


def _get_embedding_model():
    """Lazy-load the sentence transformer model (thread-safe)."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    with _embedding_model_lock:
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(_SEMANTIC_MODEL_NAME)
    return _embedding_model


def _semantic_search(query: str, limit: int = 10, threshold: float = 0.25):
    """Search verses by semantic similarity to a natural-language query.

    Returns list of (chapter, verse, score, snippet) sorted by score DESC.
    """
    if _embedding_matrix is None or len(_embedding_keys) == 0:
        return []
    model = _get_embedding_model()
    q_vec = model.encode([query], normalize_embeddings=True)  # (1, 384)
    # Cosine similarity (vectors are pre-normalised, so dot product = cosine)
    scores = _embedding_matrix @ q_vec.T  # (N, 1)
    scores = scores.flatten()
    # Get top results above threshold
    top_idx = np.argsort(scores)[::-1][:limit * 2]  # grab extra, filter by threshold
    results = []
    for idx in top_idx:
        score = float(scores[idx])
        if score < threshold:
            break
        ch, v = _embedding_keys[idx]
        snippet = _embedding_texts.get((ch, v), "")
        results.append((ch, v, score, snippet))
        if len(results) >= limit:
            break
    return results


# Load exact Bismillah from DB to avoid Unicode diacritics-ordering mismatches
_conn = get_db()
_BISMILLAH = _conn.execute(
    "SELECT text_uthmani FROM verses WHERE chapter=1 AND verse=1"
).fetchone()["text_uthmani"]
_conn.close()


def _strip_bismillah(text, surah, ayah):
    """Strip the Bismillah prefix from verse 1 display text (except 1:1 where it IS the verse)."""
    if ayah == 1 and surah != 1 and text.startswith(_BISMILLAH):
        return text[len(_BISMILLAH):].strip()
    return text


def _best_translation(conn, surah, ayah):
    """Return AI translation if available, otherwise fall back to conventional."""
    ai = conn.execute(
        "SELECT translation_text FROM ai_translations "
        "WHERE chapter = ? AND verse = ? ORDER BY created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if ai:
        return ai["translation_text"]
    conv = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return conv["text_en"] if conv else ""


def _fetch_word_glosses(conn, surah, ayah):
    """Get word-by-word English translations, fetching from Quran.com API v4 if not cached."""
    rows = conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
        (surah, ayah),
    ).fetchall()

    if rows:
        return {row["word_pos"]: row["translation_en"] for row in rows}

    # Fetch from Quran.com API v4 and cache
    try:
        resp = requests.get(
            f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}",
            params={"language": "en", "words": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        glosses = {}
        for word in data.get("verse", {}).get("words", []):
            pos = word.get("position")
            trans = word.get("translation", {}).get("text", "")
            char_type = word.get("char_type_name", "")
            if pos and trans and char_type != "end":
                glosses[pos] = trans
                conn.execute(
                    "INSERT OR REPLACE INTO word_glosses "
                    "(chapter, verse, word_pos, translation_en) VALUES (?, ?, ?, ?)",
                    (surah, ayah, pos, trans),
                )

        conn.commit()
        return glosses
    except Exception:
        return {}


# --------------- Buckwalter → SemiticRoots transliteration ---------------

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


def _bw_to_sr(bw_root: str) -> str:
    """Convert Buckwalter root 'Hmd' to semiticroots format 'ḥ-m-d'."""
    return "-".join(_BW_TO_SR.get(c, c) for c in bw_root)


def _has_semitic_tables(conn) -> bool:
    """Check if semitic_roots table exists."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='semitic_roots'"
    ).fetchone()
    return row is not None


def _get_cognate(conn, bw_root: str) -> dict | None:
    """Look up Semitic cognate data for a Buckwalter root."""
    if not _has_semitic_tables(conn):
        return None

    sr_trans = _bw_to_sr(bw_root)
    # Multiple roots may share the same transliteration (homographic roots)
    root_rows = conn.execute(
        "SELECT id, transliteration, concept FROM semitic_roots WHERE transliteration = ?",
        (sr_trans,),
    ).fetchall()

    if not root_rows:
        return None

    # Check if cognate_languages table exists (may not on older DBs)
    has_lang_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cognate_languages'"
    ).fetchone() is not None

    # Collect concepts and derivatives from all matching roots
    concepts = []
    all_derivs = []
    for root_row in root_rows:
        concepts.append(root_row["concept"])
        if has_lang_table:
            derivs = conn.execute(
                "SELECT d.language, d.word, d.displayed_text, d.concept, d.meaning, "
                "       cl.family AS language_family, "
                "       cl.date_from, cl.date_to "
                "FROM semitic_derivatives d "
                "LEFT JOIN cognate_languages cl ON d.language_id = cl.id "
                "WHERE d.root_id = ? ORDER BY cl.date_from ASC, d.language",
                (root_row["id"],),
            ).fetchall()
        else:
            derivs = conn.execute(
                "SELECT language, word, displayed_text, concept, meaning "
                "FROM semitic_derivatives WHERE root_id = ? ORDER BY language",
                (root_row["id"],),
            ).fetchall()
        all_derivs.extend(derivs)

    # Sort across all root_ids: oldest language first, then by language name
    if has_lang_table:
        all_derivs.sort(key=lambda d: (d["date_from"] or 0, d["language"]))

    return {
        "semitic_root_id": root_rows[0]["id"],
        "transliteration": root_rows[0]["transliteration"],
        "concept": " / ".join(concepts),
        "derivatives": [
            {
                "language": d["language"],
                "language_family": d["language_family"] if has_lang_table else None,
                "date_from": d["date_from"] if has_lang_table else None,
                "date_to": d["date_to"] if has_lang_table else None,
                "word": d["word"],
                "displayed_text": d["displayed_text"],
                "concept": d["concept"],
                "meaning": d["meaning"],
            }
            for d in all_derivs
        ],
    }


# ---------------------------------------------------------------------------
# "Ask the Quran" — free-tier proxy (server-side Claude calls)
# ---------------------------------------------------------------------------

_FREE_QUESTION_LIMIT = 3
_PROXY_MODEL = "claude-sonnet-4-20250514"
_MODERATION_MODEL = "claude-haiku-4-20250414"
_CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")


def _moderate_question(question: str) -> dict:
    """Use a fast Claude model to check appropriateness and reword the question.

    Returns {"approved": bool, "reworded": str, "reason": str|None}.
    Falls back to approving the raw question if the API key is missing or the call fails.
    """
    if not _CLAUDE_API_KEY:
        return {"approved": True, "reworded": question, "reason": None}

    prompt = (
        "You are a content moderator for a Quran study application. "
        "A user submitted the following question to the assistant:\n\n"
        f'"{question}"\n\n'
        "Do TWO things:\n"
        "1. Decide if this question is APPROPRIATE. Reject if it is:\n"
        "   - Gibberish, random characters, or keyboard mashing\n"
        "   - Abusive, hateful, bullying, or vulgar language\n"
        "   - Spam or advertising\n"
        "   - Completely unrelated nonsense (not a real question)\n"
        "   Accept everything else — even simple, off-topic, or naive questions are fine.\n"
        "2. If approved, reword the question for clarity and proper grammar. "
        "Write it in third-person FAQ style — do NOT use 'you' or 'your'. "
        "For example, 'What does this verse mean?' not 'Can you explain this verse to me?'. "
        "Keep the original meaning and intent. If it's already clear and third-person, return it as-is. "
        "Do NOT add information the user didn't ask about.\n\n"
        'Respond with ONLY a JSON object: {"approved": true/false, "reworded": "...", "reason": "..."}\n'
        'If approved, "reason" should be null. If rejected, "reason" should be a short user-friendly explanation.'
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": _CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": _MODERATION_MODEL,
                "max_tokens": 300,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        if not resp.ok:
            return {"approved": True, "reworded": question, "reason": None}

        import json as _json
        body = resp.json()
        text = body.get("content", [{}])[0].get("text", "")
        # Extract JSON from the response (may be wrapped in markdown code block)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = _json.loads(text)
        return {
            "approved": bool(result.get("approved", True)),
            "reworded": str(result.get("reworded", question)).strip() or question,
            "reason": result.get("reason"),
        }
    except Exception:
        # On any failure, allow the question through unchanged
        return {"approved": True, "reworded": question, "reason": None}


def _synthesize_questions(questions: list) -> str:
    """Synthesize multiple follow-up questions into one clear, consolidated question.

    Uses Claude Haiku to merge a thread of questions into a single question
    that captures everything the user explored.
    Falls back to joining with semicolons if the API call fails.
    """
    if len(questions) <= 1:
        return questions[0] if questions else ""

    if not _CLAUDE_API_KEY:
        return "; ".join(questions)

    numbered = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    prompt = (
        "A user asked the following series of questions in a Quran study conversation:\n\n"
        f"{numbered}\n\n"
        "Synthesize these into ONE clear, concise question (1-2 sentences max) that captures "
        "the full scope of what the user was exploring. "
        "Write it in third-person FAQ style for general readers — do NOT use 'you' or 'your'. "
        "For example: 'What is the significance of...' not 'Can you explain...'. "
        "Keep the original intent. "
        "Respond with ONLY the synthesized question text, nothing else."
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": _CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": _MODERATION_MODEL,
                "max_tokens": 200,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        if not resp.ok:
            return "; ".join(questions)

        body = resp.json()
        text = body.get("content", [{}])[0].get("text", "").strip()
        return text if text else "; ".join(questions)
    except Exception:
        return "; ".join(questions)


# ---------------------------------------------------------------------------
# Insight Evolution — Q&A-driven translation improvement
# ---------------------------------------------------------------------------

INSIGHT_CONFIDENCE_THRESHOLD = 0.85
_INSIGHT_MODEL = _PROXY_MODEL  # Claude Sonnet for careful evaluation

ALLOWED_INSIGHT_TARGETS = {
    ("ai_translations", "departure_notes"),
    ("ai_word_meanings", "meaning_detailed"),
    ("ai_word_meanings", "departure_notes"),
}

_INSIGHT_SYSTEM_PROMPT = """You are a careful, honest academic reviewer evaluating whether a Q&A conversation about a Quranic verse has produced a genuinely novel insight that is MISSING from the current scholarly analysis.

Your goal is to identify observations that BROADEN understanding of the Quranic text. Accept insights that are textually grounded and add something genuinely new. But be EXTREMELY cautious about two failure modes:

1. HALLUCINATIONS — The AI assistant may have fabricated a cross-reference, root connection, or cognate claim that doesn't actually exist. Verify any specific claims (verse references, root meanings) against the provided data. If a claimed cross-reference or root meaning is not present in the data provided to you, it may be hallucinated — reject it.

2. SYCOPHANTIC AGREEMENT — The AI assistant may have agreed with a user's premise just to be agreeable, producing an "insight" that isn't actually supported by the text. If the Q&A reads like the AI simply validated whatever the user said without providing independent textual evidence, reject it.

ALL of these must be true for something to qualify as an insight:
1. It is a SPECIFIC linguistic, etymological, semantic, or structural observation about the Arabic text
2. It is NOT already captured in the existing translation notes, word meanings, or departure notes shown below
3. It is derived EXCLUSIVELY from: the Quran's own text, Arabic root word analysis, morphology, or Semitic cognate evidence. REJECT anything sourced from hadith, tafsir, Islamic jurisprudence, sectarian commentary, or any external religious texts.
4. The AI's response provides INDEPENDENT textual support — not just agreement with the user's premise

REJECT these categories outright:
- Spiritual reflections or devotional commentary
- Restatements of what the existing data already says
- Theological opinions or sectarian interpretations
- Anything sourced from hadith, tafsir, or Islamic tradition
- Vague claims about "deeper meaning" without specific textual evidence
- User assertions that the AI merely echoed back without independent verification
- Post-Quranic religious terminology (e.g. "Islamic", "halal", "haram", "sunnah")

You may only recommend updates to these fields:
- ai_translations.departure_notes: Add a note about a verse-level insight
- ai_word_meanings.meaning_detailed: Enrich the detailed explanation for a specific word (specify word_pos)
- ai_word_meanings.departure_notes: Add a word-level departure note (specify word_pos)

You MUST NOT recommend changes to: translation_text, meaning_short, preferred_translation.

Updates must be MINIMAL APPENDS — do not rewrite existing content, only add a brief note with new information.

Respond with ONLY a JSON object in this exact format:
{"verdict": "NO_INSIGHT" or "INSIGHT", "confidence": 0.0 to 1.0, "reasoning": "1-3 sentences explaining your decision", "update": null or {"target_table": "ai_translations" or "ai_word_meanings", "target_column": "departure_notes" or "meaning_detailed", "word_pos": null or integer, "append_text": "the text to append"}}

If verdict is NO_INSIGHT, set update to null. If verdict is INSIGHT, update must be non-null."""


def _evaluate_insight(conversation_id: int, chapter: int, verse: int,
                      question: str, answer: str) -> None:
    """Evaluate a Q&A conversation for novel insights worth incorporating.

    Runs in a background thread. All results (including rejections and errors)
    are logged to insight_evolution_log. Never raises exceptions to the caller.
    """
    if not _CLAUDE_API_KEY:
        return

    try:
        conn = get_db()
        try:
            # Dedup: skip if already evaluated
            existing = conn.execute(
                "SELECT id FROM insight_evolution_log WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if existing:
                return

            # Fetch current AI translation for this verse
            trans_row = conn.execute(
                "SELECT id, translation_text, departure_notes "
                "FROM ai_translations WHERE chapter = ? AND verse = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (chapter, verse),
            ).fetchone()

            # Fetch current word meanings for this verse
            word_rows = conn.execute(
                "SELECT id, word_pos, meaning_short, meaning_detailed, "
                "       departure_notes, preferred_translation "
                "FROM ai_word_meanings WHERE chapter = ? AND verse = ? "
                "ORDER BY word_pos",
                (chapter, verse),
            ).fetchall()

            # If no translation or word data exists, nothing to improve
            if not trans_row and not word_rows:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'skipped_no_data', ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     "No AI translation or word meanings exist for this verse yet.",
                     question[:500], answer[:5000]),
                )
                conn.commit()
                return

            # Build the user prompt
            translation_text = trans_row["translation_text"] if trans_row else "(none)"
            departure_notes = trans_row["departure_notes"] if trans_row and trans_row["departure_notes"] else "(none)"

            word_section = ""
            for wr in word_rows:
                detailed_trunc = (wr["meaning_detailed"] or "")[:300]
                dep = wr["departure_notes"] or "(none)"
                pref = wr["preferred_translation"] or "(none)"
                word_section += (
                    f"  Word {wr['word_pos']}: short=\"{wr['meaning_short']}\", "
                    f"detailed=\"{detailed_trunc}\", departure=\"{dep}\", "
                    f"preferred=\"{pref}\"\n"
                )

            user_prompt = (
                f"## Verse Under Review\n{chapter}:{verse}\n\n"
                f"## Current AI Translation\n{translation_text}\n\n"
                f"## Current Departure Notes (verse-level)\n{departure_notes}\n\n"
                f"## Current Word Meanings\n{word_section or '(no word meanings available)'}\n\n"
                f"## Q&A Conversation\nQuestion: {question}\n\nAnswer: {answer[:3000]}\n\n"
                "Does this Q&A contain a genuinely novel insight that is MISSING "
                "from the current data above?"
            )

            # Call Claude Sonnet
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": _CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": _INSIGHT_MODEL,
                    "max_tokens": 1500,
                    "temperature": 0,
                    "system": _INSIGHT_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=60,
            )

            if not resp.ok:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'error', ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     f"API error ({resp.status_code}): {resp.text[:200]}",
                     question[:500], answer[:5000]),
                )
                conn.commit()
                return

            # Parse the JSON response
            body = resp.json()
            text = body.get("content", [{}])[0].get("text", "").strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            result = json.loads(text)
            verdict = result.get("verdict", "NO_INSIGHT")
            confidence = float(result.get("confidence", 0.0))
            reasoning = str(result.get("reasoning", ""))
            update = result.get("update")

            # Gate: only proceed if INSIGHT with sufficient confidence
            if verdict != "INSIGHT" or confidence < INSIGHT_CONFIDENCE_THRESHOLD or not update:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, confidence_score, "
                    " qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'no_insight', ?, ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     reasoning, confidence, question[:500], answer[:5000]),
                )
                conn.commit()
                return

            # Validate the update target
            target_table = update.get("target_table", "")
            target_column = update.get("target_column", "")
            word_pos = update.get("word_pos")
            append_text = str(update.get("append_text", "")).strip()

            if (target_table, target_column) not in ALLOWED_INSIGHT_TARGETS:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, confidence_score, "
                    " qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'error', ?, ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     f"Invalid target: {target_table}.{target_column}",
                     confidence, question[:500], answer[:5000]),
                )
                conn.commit()
                return

            if not append_text:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, confidence_score, "
                    " qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'error', ?, ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     "Empty append_text in update", confidence,
                     question[:500], answer[:5000]),
                )
                conn.commit()
                return

            # Fetch the target row
            if target_table == "ai_translations":
                target_row = conn.execute(
                    "SELECT id, departure_notes FROM ai_translations "
                    "WHERE chapter = ? AND verse = ? ORDER BY created_at DESC LIMIT 1",
                    (chapter, verse),
                ).fetchone()
            else:  # ai_word_meanings
                if word_pos is None:
                    conn.execute(
                        "INSERT INTO insight_evolution_log "
                        "(conversation_id, chapter, verse, status, "
                        " evaluation_model, evaluation_reasoning, confidence_score, "
                        " qa_question, qa_answer) "
                        "VALUES (?, ?, ?, 'error', ?, ?, ?, ?, ?)",
                        (conversation_id, chapter, verse, _INSIGHT_MODEL,
                         "word_pos required for ai_word_meanings target",
                         confidence, question[:500], answer[:5000]),
                    )
                    conn.commit()
                    return
                target_row = conn.execute(
                    f"SELECT id, {target_column} FROM ai_word_meanings "
                    "WHERE chapter = ? AND verse = ? AND word_pos = ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (chapter, verse, word_pos),
                ).fetchone()

            if not target_row:
                conn.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, word_pos, status, "
                    " evaluation_model, evaluation_reasoning, confidence_score, "
                    " qa_question, qa_answer) "
                    "VALUES (?, ?, ?, ?, 'error', ?, ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, word_pos, _INSIGHT_MODEL,
                     f"Target row not found in {target_table}",
                     confidence, question[:500], answer[:5000]),
                )
                conn.commit()
                return

            # Apply the update: append, never replace
            target_row_id = target_row["id"]
            old_value = target_row[target_column] or ""
            if old_value:
                new_value = old_value + " | " + append_text
            else:
                new_value = append_text

            conn.execute(
                f"UPDATE {target_table} SET {target_column} = ? WHERE id = ?",
                (new_value, target_row_id),
            )

            # Log the successful update
            conn.execute(
                "INSERT INTO insight_evolution_log "
                "(conversation_id, chapter, verse, word_pos, status, "
                " target_table, target_column, target_row_id, "
                " old_value, new_value, "
                " evaluation_model, evaluation_reasoning, confidence_score, "
                " qa_question, qa_answer) "
                "VALUES (?, ?, ?, ?, 'updated', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (conversation_id, chapter, verse, word_pos,
                 target_table, target_column, target_row_id,
                 old_value, new_value,
                 _INSIGHT_MODEL, reasoning, confidence,
                 question[:500], answer[:5000]),
            )
            conn.commit()
            print(f"INSIGHT EVOLUTION: Updated {target_table}.{target_column} "
                  f"for {chapter}:{verse} (confidence={confidence:.2f})")

        finally:
            conn.close()
    except Exception as e:
        # Last resort: try to log the error
        try:
            conn2 = get_db()
            try:
                conn2.execute(
                    "INSERT INTO insight_evolution_log "
                    "(conversation_id, chapter, verse, status, "
                    " evaluation_model, evaluation_reasoning, qa_question, qa_answer) "
                    "VALUES (?, ?, ?, 'error', ?, ?, ?, ?)",
                    (conversation_id, chapter, verse, _INSIGHT_MODEL,
                     f"Exception: {str(e)[:300]}",
                     question[:500], answer[:5000]),
                )
                conn2.commit()
            finally:
                conn2.close()
        except Exception:
            pass  # absolutely never crash


def _trigger_insight_evaluation(conversation_id: int, chapter_verse: str,
                                question: str, answer: str) -> None:
    """Fire-and-forget background evaluation of a Q&A for novel insights."""
    if not _CLAUDE_API_KEY:
        return

    parts = chapter_verse.split(":")
    if len(parts) != 2:
        return
    try:
        chapter, verse = int(parts[0]), int(parts[1])
    except (ValueError, TypeError):
        return

    t = threading.Thread(
        target=_evaluate_insight,
        args=(conversation_id, chapter, verse, question, answer),
        daemon=True,
    )
    t.start()


@app.route("/api/assistant/usage")
def get_assistant_usage():
    """Return how many free questions the session has used."""
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"used": 0, "limit": _FREE_QUESTION_LIMIT})
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM assistant_conversations "
            "WHERE session_id = ? AND model_used = ?",
            (session_id, f"free:{_PROXY_MODEL}"),
        ).fetchone()
        used = row[0] if row else 0
        return jsonify({"used": used, "limit": _FREE_QUESTION_LIMIT})
    except Exception:
        return jsonify({"used": 0, "limit": _FREE_QUESTION_LIMIT})
    finally:
        conn.close()


@app.route("/api/assistant/ask", methods=["POST"])
def proxy_assistant_ask():
    """Stream a Claude response using the server's API key (free tier)."""
    if not _CLAUDE_API_KEY:
        return jsonify({"error": "Assistant not configured on this server"}), 503

    data = request.get_json(force=True)
    session_id = data.get("session_id", "")

    # Check usage limit
    if session_id:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM assistant_conversations "
                "WHERE session_id = ? AND model_used = ?",
                (session_id, f"free:{_PROXY_MODEL}"),
            ).fetchone()
            used = row[0] if row else 0
        except Exception:
            used = 0
        finally:
            conn.close()
        if used >= _FREE_QUESTION_LIMIT:
            return jsonify({
                "error": "free_limit_reached",
                "message": f"You've used all {_FREE_QUESTION_LIMIT} free questions. Add your own Claude API key to continue.",
                "used": used,
                "limit": _FREE_QUESTION_LIMIT,
            }), 429

    system_prompt = data.get("system", "")
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    # Sanitize and limit input size
    if len(system_prompt) > 30000:
        system_prompt = system_prompt[:30000]
    for msg in messages:
        if isinstance(msg.get("content"), str):
            # Strip HTML/JS from user messages and enforce length limits
            if msg.get("role") == "user":
                c = msg["content"]
                c = re.sub(r"<[^>]*>", "", c)
                c = re.sub(r"javascript\s*:", "", c, flags=re.IGNORECASE)
                c = re.sub(r"on\w+\s*=", "", c, flags=re.IGNORECASE)
                msg["content"] = c.strip()[:500]
            elif len(msg["content"]) > 5000:
                msg["content"] = msg["content"][:5000]

    def generate():
        import json as _json
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": _CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": _PROXY_MODEL,
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "system": system_prompt,
                    "messages": messages,
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            if not resp.ok:
                error_body = resp.text[:200]
                yield f"data: {_json.dumps({'type': 'error', 'error': {'message': f'API error ({resp.status_code}): {error_body}'}})}\n\n"
                return

            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    yield line + "\n\n"
        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'error': {'message': str(e)[:200]}})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/assistant/save", methods=["POST"])
def save_assistant_qa():
    """Save or update an Ask the Quran Q&A conversation thread.

    Uses a three-layer upsert strategy:
    1. Client sends thread_id from a previous save → direct UPDATE.
    2. No thread_id but a recent row exists for this (session, page) → UPDATE that row.
    3. No match at all → INSERT a new row.
    Synthesis runs on every UPDATE path, not just when the client provides all_questions.
    """
    data = request.get_json(force=True)
    required = ("session_id", "page_type", "page_key", "question", "answer")
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    thread_id = data.get("thread_id")          # int or None
    all_questions = data.get("all_questions")   # list[str] or None

    # Sanitize the current question
    q = data.get("question", "")
    q = re.sub(r"<[^>]*>", "", q)
    q = re.sub(r"javascript\s*:", "", q, flags=re.IGNORECASE)
    q = re.sub(r"on\w+\s*=", "", q, flags=re.IGNORECASE)
    data["question"] = q.strip()

    # Sanitize all_questions too
    if all_questions and isinstance(all_questions, list):
        sanitized = []
        for aq in all_questions:
            if isinstance(aq, str):
                aq = re.sub(r"<[^>]*>", "", aq)
                aq = re.sub(r"javascript\s*:", "", aq, flags=re.IGNORECASE)
                aq = re.sub(r"on\w+\s*=", "", aq, flags=re.IGNORECASE)
                sanitized.append(aq.strip()[:500])
        all_questions = [sq for sq in sanitized if sq]

    # Input length limits
    MAX_LEN = {"question": 500, "answer": 50000, "context_summary": 500}
    for field, limit in MAX_LEN.items():
        val = data.get(field, "")
        if isinstance(val, str) and len(val) > limit:
            data[field] = val[:limit]

    # Moderate the current question
    moderation = _moderate_question(data["question"])
    if not moderation["approved"]:
        return jsonify({
            "ok": False,
            "moderated": True,
            "reason": moderation.get("reason", "Question was not appropriate for saving."),
        })

    try:
        conn = get_db()
        try:
            # Use BEGIN IMMEDIATE for atomic lookup+write (Fix 7)
            conn.execute("BEGIN IMMEDIATE")

            # --- Resolve existing row: client thread_id OR session-based lookup (Fix 5) ---
            existing_row = None
            if thread_id:
                existing_row = conn.execute(
                    "SELECT id, question FROM assistant_conversations "
                    "WHERE id = ? AND session_id = ?",
                    (thread_id, data["session_id"]),
                ).fetchone()

            if not existing_row:
                # Defense-in-depth: look for a recent row from same session+page (Fix 5)
                existing_row = conn.execute(
                    "SELECT id, question FROM assistant_conversations "
                    "WHERE session_id = ? AND page_type = ? AND page_key = ? "
                    "  AND created_at > datetime('now', '-1 hour') "
                    "ORDER BY id DESC LIMIT 1",
                    (data["session_id"], data["page_type"], data["page_key"]),
                ).fetchone()

            if existing_row:
                # --- UPDATE path --- (Fix 6: always synthesize when updating)
                row_id = existing_row["id"]
                existing_question = existing_row["question"]

                # Build question list for synthesis
                if all_questions and len(all_questions) > 1:
                    questions_to_merge = all_questions
                else:
                    # Fallback: merge existing stored question + new question
                    questions_to_merge = [existing_question, data["question"]]

                # Synthesize + moderate
                synthesized = _synthesize_questions(questions_to_merge)
                synth_mod = _moderate_question(synthesized)
                saved_question = synth_mod["reworded"] if synth_mod["approved"] else synthesized

                conn.execute(
                    "UPDATE assistant_conversations "
                    "SET question = ?, answer = ?, model_used = ?, response_time_ms = ? "
                    "WHERE id = ?",
                    (
                        saved_question,
                        data["answer"],
                        data.get("model_used", ""),
                        data.get("response_time_ms"),
                        row_id,
                    ),
                )
                conn.commit()

                # Trigger async insight evaluation for verse Q&A
                if data.get("page_type") == "verse":
                    _trigger_insight_evaluation(
                        row_id, data["page_key"],
                        saved_question, data["answer"])

                return jsonify({
                    "ok": True,
                    "id": row_id,
                    "reworded_question": saved_question,
                    "answer": data["answer"],
                })
            else:
                # --- INSERT path (genuinely first question) ---
                saved_question = moderation["reworded"]

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS assistant_conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        page_type TEXT NOT NULL,
                        page_key TEXT NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        context_summary TEXT,
                        model_used TEXT,
                        response_time_ms INTEGER,
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                cur = conn.execute(
                    "INSERT INTO assistant_conversations "
                    "(session_id, page_type, page_key, question, answer, "
                    " context_summary, model_used, response_time_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["session_id"],
                        data["page_type"],
                        data["page_key"],
                        saved_question,
                        data["answer"],
                        data.get("context_summary", ""),
                        data.get("model_used", ""),
                        data.get("response_time_ms"),
                    ),
                )
                new_id = cur.lastrowid
                conn.commit()

                # Trigger async insight evaluation for verse Q&A
                if data.get("page_type") == "verse":
                    _trigger_insight_evaluation(
                        new_id, data["page_key"],
                        saved_question, data["answer"])

                return jsonify({
                    "ok": True,
                    "id": new_id,
                    "reworded_question": saved_question,
                    "answer": data["answer"],
                })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": f"Failed to save: {str(e)[:200]}"}), 500


@app.route("/api/assistant/history")
def get_assistant_history():
    """Get shared Q&A for a page (visible to all users)."""
    page_type = request.args.get("page_type", "")
    page_key = request.args.get("page_key", "")
    try:
        limit = min(int(request.args.get("limit", 50)), 100)
    except (ValueError, TypeError):
        limit = 50

    if not page_type or not page_key:
        return jsonify({"history": []})

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, question, answer, model_used, created_at "
            "FROM assistant_conversations "
            "WHERE page_type = ? AND page_key = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (page_type, page_key, limit),
        ).fetchall()
        return jsonify({
            "history": [
                {
                    "id": r["id"],
                    "question": r["question"],
                    "answer": r["answer"],
                    "model_used": r["model_used"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Insight Evolution — API endpoints
# ---------------------------------------------------------------------------


def _revert_insight(log_id: int, reverted_by: str = "admin") -> dict:
    """Revert a single insight evolution change. Returns status dict."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM insight_evolution_log WHERE id = ?", (log_id,)
        ).fetchone()

        if not row:
            return {"error": "Log entry not found"}
        if row["status"] != "updated":
            return {"error": "Only 'updated' entries can be reverted"}
        if row["reverted_at"]:
            return {"error": "Already reverted"}

        target = (row["target_table"], row["target_column"])
        if target not in ALLOWED_INSIGHT_TARGETS:
            return {"error": "Invalid target — cannot revert"}

        # Restore old value
        conn.execute(
            f"UPDATE {row['target_table']} SET {row['target_column']} = ? WHERE id = ?",
            (row["old_value"], row["target_row_id"]),
        )
        # Mark as reverted
        conn.execute(
            "UPDATE insight_evolution_log "
            "SET reverted_at = datetime('now'), reverted_by = ? WHERE id = ?",
            (reverted_by, log_id),
        )
        conn.commit()
        return {"ok": True, "reverted_log_id": log_id}
    finally:
        conn.close()


@app.route("/api/insight-evolution/log")
def get_insight_evolution_log():
    """View the insight evolution audit log."""
    chapter = request.args.get("chapter")
    verse = request.args.get("verse")
    status = request.args.get("status")
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except (ValueError, TypeError):
        limit = 50

    conn = get_db()
    try:
        conditions = []
        params = []
        if chapter:
            conditions.append("chapter = ?")
            params.append(int(chapter))
        if verse:
            conditions.append("verse = ?")
            params.append(int(verse))
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM insight_evolution_log {where} "
            "ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()

        return jsonify({
            "entries": [
                {k: row[k] for k in row.keys()}
                for row in rows
            ]
        })
    except Exception:
        return jsonify({"entries": []})
    finally:
        conn.close()


@app.route("/api/insight-evolution/revert", methods=["POST"])
def revert_insight_evolution():
    """Revert a single insight evolution change."""
    data = request.get_json(force=True)
    log_id = data.get("log_id")
    if not log_id:
        return jsonify({"error": "log_id is required"}), 400

    result = _revert_insight(int(log_id))
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/insight-evolution/stats")
def get_insight_evolution_stats():
    """Summary statistics for the insight evolution system."""
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM insight_evolution_log"
        ).fetchone()[0]

        by_status = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM insight_evolution_log GROUP BY status"
        ).fetchall()
        status_counts = {r["status"]: r["cnt"] for r in by_status}

        updated = status_counts.get("updated", 0)
        reverted = conn.execute(
            "SELECT COUNT(*) FROM insight_evolution_log "
            "WHERE status = 'updated' AND reverted_at IS NOT NULL"
        ).fetchone()[0]

        # Recent insights (last 10 updates)
        recent = conn.execute(
            "SELECT id, chapter, verse, word_pos, target_table, target_column, "
            "       confidence_score, evaluation_reasoning, created_at, reverted_at "
            "FROM insight_evolution_log WHERE status = 'updated' "
            "ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        return jsonify({
            "total_evaluations": total,
            "status_breakdown": status_counts,
            "total_insights": updated,
            "total_reverted": reverted,
            "active_insights": updated - reverted,
            "recent_insights": [
                {k: r[k] for k in r.keys()}
                for r in recent
            ],
        })
    except Exception:
        return jsonify({
            "total_evaluations": 0,
            "status_breakdown": {},
            "total_insights": 0,
            "total_reverted": 0,
            "active_insights": 0,
            "recent_insights": [],
        })
    finally:
        conn.close()


@app.route("/api/verse/<verse_ref>/themes")
def get_verse_themes(verse_ref: str):
    """Get themes assigned to a verse. verse_ref is 'surah:ayah'."""
    parts = verse_ref.split(":")
    if len(parts) != 2:
        return jsonify({"error": "Invalid verse reference"}), 400
    try:
        chapter, verse = int(parts[0]), int(parts[1])
    except ValueError:
        return jsonify({"error": "Invalid verse reference"}), 400

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT theme, confidence FROM verse_themes "
            "WHERE chapter = ? AND verse = ? ORDER BY confidence DESC",
            (chapter, verse),
        ).fetchall()
        return jsonify({
            "chapter": chapter,
            "verse": verse,
            "themes": [{"theme": r["theme"], "confidence": r["confidence"]} for r in rows],
        })
    finally:
        conn.close()


@app.route("/api/themes")
def get_all_themes():
    """Get all distinct themes and their verse counts."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT theme, COUNT(*) as verse_count FROM verse_themes "
            "GROUP BY theme ORDER BY verse_count DESC"
        ).fetchall()
        return jsonify({
            "themes": [{"theme": r["theme"], "verse_count": r["verse_count"]} for r in rows],
        })
    finally:
        conn.close()


@app.route("/api/themes/<theme>/verses")
def get_verses_by_theme(theme: str):
    """Get all verses for a given theme."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT vt.chapter, vt.verse, vt.confidence, v.text_uthmani, t.text_en "
            "FROM verse_themes vt "
            "JOIN verses v ON vt.chapter = v.chapter AND vt.verse = v.verse "
            "LEFT JOIN translations t ON vt.chapter = t.chapter AND vt.verse = t.verse "
            "WHERE vt.theme = ? ORDER BY vt.chapter, vt.verse",
            (theme,),
        ).fetchall()
        return jsonify({
            "theme": theme,
            "verses": [
                {
                    "chapter": r["chapter"],
                    "verse": r["verse"],
                    "confidence": r["confidence"],
                    "text_uthmani": r["text_uthmani"],
                    "text_en": r["text_en"],
                }
                for r in rows
            ],
        })
    finally:
        conn.close()


@app.route("/api/cognates/<root_bw>")
def get_cognates(root_bw: str):
    """Get Semitic cognate data for a Buckwalter root (e.g. 'Hmd')."""
    conn = get_db()
    try:
        cognate = _get_cognate(conn, root_bw)
        if not cognate:
            return jsonify({"error": f"No cognate data for root '{root_bw}'"}), 404
        return jsonify(cognate)
    finally:
        conn.close()


@app.route("/api/root/<root_bw>")
def get_root(root_bw: str):
    """Get comprehensive data for a Buckwalter root: Arabic form, lemmas, cognates, sample verses."""
    conn = get_db()
    try:
        root_arabic = _root_arabic_map.get(root_bw)
        if not root_arabic:
            return jsonify({"error": f"Root '{root_bw}' not found"}), 404

        # Total occurrences (number of verses containing this root)
        verse_keys = _root_inv.get(root_bw, set())
        total_occurrences = len(verse_keys)

        # Distinct lemmas associated with this root
        lemma_rows = conn.execute(
            "SELECT DISTINCT lemma_arabic, lemma_buckwalter "
            "FROM morphology "
            "WHERE root_buckwalter = ? AND lemma_arabic IS NOT NULL AND lemma_arabic != '' "
            "ORDER BY lemma_arabic",
            (root_bw,),
        ).fetchall()
        lemmas = [
            {"lemma_arabic": r["lemma_arabic"], "lemma_buckwalter": r["lemma_buckwalter"]}
            for r in lemma_rows
        ]

        # Cognate data
        cognate = _get_cognate(conn, root_bw)

        # Sample verses (up to 10, sorted by surah:ayah)
        sample_keys = sorted(verse_keys)[:10]
        sample_verses = []
        for ch, v in sample_keys:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            # Find word positions that contain this root
            morph_rows = conn.execute(
                "SELECT DISTINCT word_pos FROM morphology "
                "WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                (ch, v, root_bw),
            ).fetchall()
            matched_positions = sorted(r["word_pos"] for r in morph_rows)
            sample_verses.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": _strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": _best_translation(conn, ch, v),
                "matched_positions": matched_positions,
            })

        # AI-generated root meaning (latest config)
        ai_row = conn.execute(
            "SELECT primary_meaning, detailed_meaning, semantic_field "
            "FROM ai_root_meanings WHERE root_buckwalter = ? "
            "ORDER BY config_id DESC LIMIT 1",
            (root_bw,),
        ).fetchone()

        result = {
            "root_arabic": root_arabic,
            "root_buckwalter": root_bw,
            "total_occurrences": total_occurrences,
            "lemmas": lemmas,
            "cognate": cognate,
            "sample_verses": sample_verses,
        }
        if ai_row:
            result["primary_meaning"] = ai_row["primary_meaning"]
            result["detailed_meaning"] = ai_row["detailed_meaning"]
            result["semantic_field"] = ai_row["semantic_field"]

        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/preview")
def get_verse_preview(surah: int, ayah: int):
    """Lightweight verse preview — just text, translation, and surah name."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
        if not row:
            return jsonify({"error": f"Verse {surah}:{ayah} not found"}), 404
        text = _strip_bismillah(row["text_uthmani"], surah, ayah)
        translation = _best_translation(conn, surah, ayah)
        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "surah_name": _surah_name(surah),
            "text_uthmani": text,
            "translation": translation or "",
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>")
def get_verse(surah: int, ayah: int):
    conn = get_db()
    try:
        # Get Arabic text
        verse = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()

        if not verse:
            return jsonify({"error": f"Verse {surah}:{ayah} not found"}), 404

        # Get translation
        trans = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()

        # Get morphology
        morphology = conn.execute(
            """SELECT word_pos, segment, form_buckwalter, form_arabic,
                      tag, pos, root_buckwalter, root_arabic,
                      lemma_buckwalter, lemma_arabic, features_raw,
                      gender, number, person, case_val, voice, mood,
                      verb_form, state
               FROM morphology
               WHERE chapter = ? AND verse = ?
               ORDER BY word_pos, segment""",
            (surah, ayah),
        ).fetchall()

        # Group segments by word position
        words = OrderedDict()
        roots_seen = OrderedDict()

        for row in morphology:
            wp = row["word_pos"]
            if wp not in words:
                words[wp] = []

            features = {}
            for key in ("gender", "number", "person", "case_val", "voice", "mood", "verb_form", "state"):
                val = row[key]
                if val:
                    display_key = "case" if key == "case_val" else key.replace("_", " ")
                    features[display_key] = val

            words[wp].append({
                "form_arabic": row["form_arabic"],
                "form_buckwalter": row["form_buckwalter"],
                "tag": row["tag"],
                "pos": row["pos"],
                "root_arabic": row["root_arabic"],
                "root_buckwalter": row["root_buckwalter"],
                "lemma_arabic": row["lemma_arabic"],
                "lemma_buckwalter": row["lemma_buckwalter"],
                "features": features,
                "features_raw": row["features_raw"],
            })

            # Track unique roots
            rbw = row["root_buckwalter"]
            if rbw:
                if rbw not in roots_seen:
                    roots_seen[rbw] = {
                        "root_arabic": row["root_arabic"],
                        "root_buckwalter": rbw,
                        "occurrences": 0,
                    }
                roots_seen[rbw]["occurrences"] += 1

        # Get word-by-word translations
        glosses = _fetch_word_glosses(conn, surah, ayah)

        words_list = [
            {"position": pos, "segments": segs, "translation": glosses.get(pos, "")}
            for pos, segs in words.items()
        ]

        # Enrich roots with cognate data
        roots_list = list(roots_seen.values())
        for root_entry in roots_list:
            cognate = _get_cognate(conn, root_entry["root_buckwalter"])
            root_entry["cognate"] = cognate

        # Build previous/next verse links (across surah boundaries).
        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?",
            (surah,),
        ).fetchone()
        total_in_surah = int(total_row["cnt"]) if total_row and total_row["cnt"] else 0

        previous = None
        if ayah > 1:
            previous = {"surah": surah, "ayah": ayah - 1}
        elif surah > 1:
            prev_total_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?",
                (surah - 1,),
            ).fetchone()
            prev_total = int(prev_total_row["cnt"]) if prev_total_row and prev_total_row["cnt"] else 0
            if prev_total > 0:
                previous = {"surah": surah - 1, "ayah": prev_total}

        next_ref = None
        if total_in_surah > 0 and ayah < total_in_surah:
            next_ref = {"surah": surah, "ayah": ayah + 1}
        elif surah < 114:
            next_exists = conn.execute(
                "SELECT 1 FROM verses WHERE chapter = ? AND verse = 1",
                (surah + 1,),
            ).fetchone()
            if next_exists:
                next_ref = {"surah": surah + 1, "ayah": 1}

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "surah_name": _surah_name(surah),
            "text_uthmani": _strip_bismillah(verse["text_uthmani"], surah, ayah),
            "translation": _best_translation(conn, surah, ayah),
            "words": words_list,
            "roots_summary": roots_list,
            "previous": previous,
            "next": next_ref,
        })
    finally:
        conn.close()


@app.route("/api/surahs")
def get_surahs():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT chapter, COUNT(*) as verse_count FROM verses GROUP BY chapter ORDER BY chapter"
        ).fetchall()

        surahs = []
        for row in rows:
            ch = row["chapter"]
            name = _surah_name(ch)
            surahs.append({
                "number": ch,
                "name": name,
                "verse_count": row["verse_count"],
            })

        return jsonify(surahs)
    finally:
        conn.close()


@app.route("/api/related/<int:surah>:<int:ayah>")
def get_related_verses(surah: int, ayah: int):
    """Find verses related to the given verse using lemma-based IDF-weighted containment."""
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 25))

    results = _find_related_verses(surah, ayah, limit=limit)

    if not results:
        query_lemmas = _verse_lemmas.get((surah, ayah), set())
        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "related": [],
            "meta": {"query_lemma_count": len(query_lemmas)},
        })

    # Fetch text/translation for each related verse
    conn = get_db()
    try:
        related = []
        for containment, shared_weight, (ch, v), shared_roots in results:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()

            # Build shared roots list sorted by IDF (rarest first)
            shared_info = sorted(
                [
                    {
                        "root_arabic": _root_arabic_map.get(rbw, ""),
                        "root_buckwalter": rbw,
                        "idf": round(_root_idf.get(rbw, 0), 2),
                    }
                    for rbw in shared_roots
                ],
                key=lambda x: -x["idf"],
            )

            related.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": _strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": _best_translation(conn, ch, v),
                "similarity_score": round(containment, 3),
                "shared_roots": shared_info,
            })

        query_lemmas = _verse_lemmas.get((surah, ayah), set())
        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "related": related,
            "meta": {"query_lemma_count": len(query_lemmas)},
        })
    finally:
        conn.close()


@app.route("/api/context/<int:surah>:<int:ayah>")
def get_context(surah: int, ayah: int):
    """Return surrounding verses for context (up to 6 total, excluding the queried verse)."""
    conn = get_db()
    try:
        # Find total verses in this surah
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?", (surah,)
        ).fetchone()
        total = row["cnt"] if row else 0

        if total == 0:
            return jsonify({"error": f"Surah {surah} not found"}), 404

        # Determine range: 3 before + 3 after, sliding at boundaries
        context_size = 6
        before = 3
        after = 3

        if ayah <= before:
            # Near the start: take fewer before, more after
            before = ayah - 1
            after = context_size - before
        elif ayah + after > total:
            # Near the end: take fewer after, more before
            after = total - ayah
            before = context_size - after

        start = max(1, ayah - before)
        end = min(total, ayah + after)

        rows = conn.execute(
            "SELECT chapter, verse, text_uthmani "
            "FROM verses "
            "WHERE chapter = ? AND verse BETWEEN ? AND ? AND verse != ? "
            "ORDER BY verse",
            (surah, start, end, ayah),
        ).fetchall()

        verses = [
            {
                "surah": r["chapter"],
                "ayah": r["verse"],
                "text_uthmani": _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
                "translation": _best_translation(conn, r["chapter"], r["verse"]),
            }
            for r in rows
        ]

        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "context": verses,
            "surah_total": total,
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/thematic-context")
def get_thematic_context(surah: int, ayah: int):
    """Return precomputed Qur'an-only thematic context for a verse."""
    config_name = request.args.get("config", type=str)
    include_all = request.args.get("include_all", "0") == "1"
    conn = get_db()
    try:
        params = [surah, ayah]
        where_config = ""
        if config_name:
            where_config = "AND c.config_name = ?"
            params.append(config_name)

        row = conn.execute(
            "SELECT tc.chapter, tc.verse, tc.passage_start_ayah, tc.passage_end_ayah, "
            "       tc.passage_theme, tc.passage_confidence, "
            "       tc.surah_role_summary, tc.surah_role_confidence, "
            "       tc.neighbor_surah_summary, tc.neighbor_surah_confidence, "
            "       tc.quran_wide_links_json, tc.evidence_json, tc.created_at, "
            "       c.config_name, c.model_name, c.prompt_version "
            "FROM verse_thematic_contexts tc "
            "JOIN thematic_context_configs c ON tc.config_id = c.id "
            "WHERE tc.chapter = ? AND tc.verse = ? "
            f"{where_config} "
            "ORDER BY tc.created_at DESC LIMIT 1",
            tuple(params),
        ).fetchone()

        if not row:
            return jsonify({"error": "No thematic context available"}), 404

        links = []
        if row["quran_wide_links_json"]:
            try:
                links = json.loads(row["quran_wide_links_json"])
            except json.JSONDecodeError:
                links = []

        evidence = {}
        if row["evidence_json"]:
            try:
                evidence = json.loads(row["evidence_json"])
            except json.JSONDecodeError:
                evidence = {}

        def _hydrate_refs(refs: list[str]) -> list[dict]:
            out = []
            for ref in refs:
                try:
                    s, a = ref.split(":")
                    ch, v = int(s), int(a)
                except (ValueError, AttributeError):
                    continue
                vr = conn.execute(
                    "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                    (ch, v),
                ).fetchone()
                if not vr:
                    continue
                out.append({
                    "surah": ch,
                    "ayah": v,
                    "text_uthmani": _strip_bismillah(vr["text_uthmani"], ch, v),
                    "translation": _best_translation(conn, ch, v),
                })
            return out

        hydrated_links = []
        for item in links:
            refs = item.get("related_verses", []) if isinstance(item, dict) else []
            hydrated_links.append({
                "theme": item.get("theme", "") if isinstance(item, dict) else "",
                "summary": item.get("summary", "") if isinstance(item, dict) else "",
                "confidence": item.get("confidence", 0.0) if isinstance(item, dict) else 0.0,
                "verses": _hydrate_refs(refs if isinstance(refs, list) else []),
            })

        if not include_all and not _is_thematic_context_displayable(row, links):
            return jsonify({"error": "No high-signal thematic context available"}), 404

        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "thematic_context": {
                "passage": {
                    "start_ayah": row["passage_start_ayah"],
                    "end_ayah": row["passage_end_ayah"],
                    "theme": row["passage_theme"] or "",
                    "confidence": row["passage_confidence"] or 0.0,
                },
                "surah_role": {
                    "summary": row["surah_role_summary"] or "",
                    "confidence": row["surah_role_confidence"] or 0.0,
                },
                "neighbor_surahs": {
                    "summary": row["neighbor_surah_summary"] or "",
                    "confidence": row["neighbor_surah_confidence"] or 0.0,
                },
                "quran_wide_links": hydrated_links,
                "evidence": evidence,
                "model": {
                    "config_name": row["config_name"],
                    "model_name": row["model_name"],
                    "prompt_version": row["prompt_version"],
                    "created_at": row["created_at"],
                },
            },
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/surah-context")
def get_surah_context(surah: int, ayah: int):
    """Return precomputed 'what happened so far in this surah' context."""
    config_name = request.args.get("config", type=str)
    include_all = request.args.get("include_all", "0") == "1"
    conn = get_db()
    try:
        params = [surah, ayah]
        where_config = ""
        if config_name:
            where_config = "AND c.config_name = ?"
            params.append(config_name)

        row = conn.execute(
            "SELECT vc.chapter, vc.verse, vc.summary_so_far, vc.current_verse_focus, "
            "       vc.key_verses_json, vc.summary_points_json, vc.lexical_continuity_json, "
            "       vc.signal_score, vc.verifier_report_json, vc.evidence_json, vc.created_at, "
            "       c.config_name, c.model_name, c.prompt_version "
            "FROM verse_surah_contexts vc "
            "JOIN surah_context_configs c ON vc.config_id = c.id "
            "WHERE vc.chapter = ? AND vc.verse = ? "
            f"{where_config} "
            "ORDER BY vc.created_at DESC LIMIT 1",
            tuple(params),
        ).fetchone()

        if not row:
            return jsonify({"error": "No surah context available"}), 404

        key_items = []
        if row["key_verses_json"]:
            try:
                key_items = json.loads(row["key_verses_json"])
            except json.JSONDecodeError:
                key_items = []

        if not isinstance(key_items, list):
            key_items = []

        summary_points = []
        if row["summary_points_json"]:
            try:
                summary_points = json.loads(row["summary_points_json"])
            except json.JSONDecodeError:
                summary_points = []
        if not isinstance(summary_points, list):
            summary_points = []

        lexical = []
        if row["lexical_continuity_json"]:
            try:
                lexical = json.loads(row["lexical_continuity_json"])
            except json.JSONDecodeError:
                lexical = []
        if not isinstance(lexical, list):
            lexical = []

        verifier = {}
        if row["verifier_report_json"]:
            try:
                verifier = json.loads(row["verifier_report_json"])
            except json.JSONDecodeError:
                verifier = {}

        hydrated = []
        for item in key_items:
            if not isinstance(item, dict):
                continue
            ref = item.get("ref", "")
            try:
                s, a = ref.split(":")
                ch, v = int(s), int(a)
            except (ValueError, AttributeError):
                continue
            vr = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            if not vr:
                continue
            hydrated.append({
                "surah": ch,
                "ayah": v,
                "why": item.get("why", ""),
                "text_uthmani": _strip_bismillah(vr["text_uthmani"], ch, v),
                "translation": _best_translation(conn, ch, v),
            })

        summary = (row["summary_so_far"] or "").strip()
        focus = (row["current_verse_focus"] or "").strip()
        signal_score = float(row["signal_score"] or 0.0)

        if not include_all:
            if signal_score < 0.68:
                return jsonify({"error": "No high-signal surah context available"}), 404

        evidence = {}
        if row["evidence_json"]:
            try:
                evidence = json.loads(row["evidence_json"])
            except json.JSONDecodeError:
                evidence = {}

        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "surah_context": {
                "summary_so_far": summary,
                "current_verse_focus": focus,
                "key_verses": hydrated,
                "summary_points": summary_points,
                "lexical_continuity": lexical,
                "signal_score": signal_score,
                "verifier": verifier,
                "evidence": evidence,
                "model": {
                    "config_name": row["config_name"],
                    "model_name": row["model_name"],
                    "prompt_version": row["prompt_version"],
                    "created_at": row["created_at"],
                },
            },
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/ai-translation")
def get_ai_translation(surah: int, ayah: int):
    """Return the most recent AI translation for a verse, or 404 if none exists."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT t.translation_text, t.departure_notes, t.created_at, "
            "       c.config_name, c.model_name "
            "FROM ai_translations t "
            "JOIN ai_translation_configs c ON t.config_id = c.id "
            "WHERE t.chapter = ? AND t.verse = ? "
            "ORDER BY t.created_at DESC LIMIT 1",
            (surah, ayah),
        ).fetchone()

        if not row:
            return jsonify({"error": "No AI translation available"}), 404

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "translation": row["translation_text"],
            "departure_notes": row["departure_notes"],
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "created_at": row["created_at"],
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/grammar-insights")
def get_grammar_insights(surah: int, ayah: int):
    """Return precomputed grammar insights for a verse."""
    config_name = request.args.get("config", type=str)
    include_all = request.args.get("include_all", "0") == "1"
    conn = get_db()
    try:
        params = [surah, ayah]
        where_config = ""
        if config_name:
            where_config = "AND c.config_name = ?"
            params.append(config_name)

        row = conn.execute(
            "SELECT gi.overview_text, gi.insights_json, gi.signal_score, gi.verifier_report_json, "
            "       gi.evidence_json, gi.created_at, gi.generation_version, gi.insights_v7_json, "
            "       gi.quality_json, gi.overall_confidence, gi.model_confidence_raw, gi.display_json, "
            "       c.config_name, c.model_name, c.prompt_version "
            "FROM verse_grammar_insights gi "
            "JOIN grammar_insight_configs c ON gi.config_id = c.id "
            "WHERE gi.chapter = ? AND gi.verse = ? "
            f"{where_config} "
            "ORDER BY gi.created_at DESC LIMIT 1",
            tuple(params),
        ).fetchone()

        if not row:
            return jsonify({"error": "No grammar insights available"}), 404

        insights = []
        if row["insights_json"]:
            try:
                insights = json.loads(row["insights_json"])
            except json.JSONDecodeError:
                insights = []
        if not isinstance(insights, list):
            insights = []

        verifier = {}
        if row["verifier_report_json"]:
            try:
                verifier = json.loads(row["verifier_report_json"])
            except json.JSONDecodeError:
                verifier = {}

        evidence = {}
        if row["evidence_json"]:
            try:
                evidence = json.loads(row["evidence_json"])
            except json.JSONDecodeError:
                evidence = {}

        insights_v7 = []
        if row["insights_v7_json"]:
            try:
                insights_v7 = json.loads(row["insights_v7_json"])
            except json.JSONDecodeError:
                insights_v7 = []

        quality = {}
        if row["quality_json"]:
            try:
                quality = json.loads(row["quality_json"])
            except json.JSONDecodeError:
                quality = {}

        display = {}
        if row["display_json"]:
            try:
                display = json.loads(row["display_json"])
            except json.JSONDecodeError:
                display = {}

        score = float(row["signal_score"] or 0.0)
        if not include_all and not _is_grammar_insight_displayable(score, insights):
            return jsonify({"error": "No high-signal grammar insights available"}), 404

        return jsonify({
            "query": {"surah": surah, "ayah": ayah},
            "grammar_insights": {
                "overview": (row["overview_text"] or "").strip(),
                "insights": insights,
                "signal_score": score,
                "generation_version": (row["generation_version"] or "v6"),
                "insights_v7": insights_v7,
                "quality": quality,
                "overall_confidence": float(row["overall_confidence"] or score),
                "model_confidence_raw": float(row["model_confidence_raw"] or 0.0),
                "display": display,
                "verifier": verifier,
                "evidence": evidence,
                "model": {
                    "config_name": row["config_name"],
                    "model_name": row["model_name"],
                    "prompt_version": row["prompt_version"],
                    "created_at": row["created_at"],
                },
            },
        })
    finally:
        conn.close()


@app.route("/api/search-words", methods=["POST"])
def search_words():
    """Find verses containing ALL of the given search terms (intersection)."""
    body = request.get_json(force=True)
    terms = body.get("terms", [])
    limit = min(max(1, body.get("limit", 25)), 50)
    query_verse = body.get("query_verse")  # optional {surah, ayah} to exclude

    count_only = body.get("count_only", False)

    if not terms:
        return jsonify({"error": "No search terms provided"}), 400

    # Resolve each term to a search strategy and candidate verse set
    resolved = []
    candidate_sets = []

    for term in terms:
        lemma_bw = term.get("lemma_bw")
        root_bw = term.get("root_bw")
        form_bw = term.get("form_bw")
        display_arabic = term.get("display_arabic", "")

        if lemma_bw and lemma_bw in _lemma_inv:
            resolved.append({
                "display_arabic": display_arabic,
                "search_type": "lemma",
                "search_key": lemma_bw,
            })
            candidate_sets.append(_lemma_inv[lemma_bw])
        elif root_bw and root_bw in _root_inv:
            resolved.append({
                "display_arabic": display_arabic,
                "search_type": "root",
                "search_key": root_bw,
            })
            candidate_sets.append(_root_inv[root_bw])
        elif form_bw and form_bw in _form_inv:
            resolved.append({
                "display_arabic": display_arabic,
                "search_type": "form",
                "search_key": form_bw,
            })
            candidate_sets.append(_form_inv[form_bw])
        else:
            # Term not found in any index — intersection will be empty
            return jsonify({
                "terms_used": [],
                "results": [],
                "total_found": 0,
            })

    # Intersect all candidate sets
    result_set = candidate_sets[0]
    for cs in candidate_sets[1:]:
        result_set = result_set & cs

    # Remove query verse if provided
    if query_verse:
        result_set = result_set - {(query_verse["surah"], query_verse["ayah"])}

    total_found = len(result_set)

    if count_only:
        return jsonify({
            "terms_used": resolved,
            "total_found": total_found,
        })

    if not result_set:
        return jsonify({
            "terms_used": resolved,
            "results": [],
            "total_found": 0,
        })

    # Score each candidate: sum of idf_weight per resolved term
    scored = []
    for key in result_set:
        score = 0.0
        matched = []
        for r in resolved:
            if r["search_type"] == "lemma":
                score += _lemma_idf.get(r["search_key"], 0)
            elif r["search_type"] == "root":
                score += ROOT_DISCOUNT * _root_idf.get(r["search_key"], 0)
            else:  # form
                score += ROOT_DISCOUNT * _form_idf.get(r["search_key"], 0)
            matched.append(r)
        scored.append((score, key, matched))

    scored.sort(key=lambda x: -x[0])
    scored = scored[:limit]

    # Build lookup sets for matching word positions in result verses
    lemma_keys = {r["search_key"] for r in resolved if r["search_type"] == "lemma"}
    root_keys = {r["search_key"] for r in resolved if r["search_type"] == "root"}
    form_keys = {r["search_key"] for r in resolved if r["search_type"] == "form"}

    # Fetch text + translation for results
    conn = get_db()
    try:
        results = []
        for score, (ch, v), matched in scored:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()

            # Find word positions that match any of the search terms
            matched_positions = set()
            morph_rows = conn.execute(
                "SELECT word_pos, lemma_buckwalter, root_buckwalter, form_buckwalter "
                "FROM morphology WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchall()
            for mr in morph_rows:
                lbw = mr["lemma_buckwalter"] or ""
                rbw = mr["root_buckwalter"] or ""
                fbw = mr["form_buckwalter"] or ""
                if (lbw in lemma_keys) or (rbw in root_keys) or (fbw in form_keys):
                    matched_positions.add(mr["word_pos"])

            results.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": _strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": _best_translation(conn, ch, v),
                "score": round(score, 3),
                "matched_terms": matched,
                "matched_positions": sorted(matched_positions),
            })

        return jsonify({
            "terms_used": resolved,
            "results": results,
            "total_found": total_found,
        })
    finally:
        conn.close()


@app.route("/api/semantic-search")
def semantic_search_api():
    """Search verses by natural-language meaning using vector embeddings.

    GET /api/semantic-search?q=punishment+for+disbelievers&limit=10
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    if len(query) > 500:
        return jsonify({"error": "Query too long (max 500 characters)"}), 400
    try:
        limit = min(int(request.args.get("limit", "10")), 50)
    except (ValueError, TypeError):
        return jsonify({"error": "limit must be a positive integer"}), 400

    results = _semantic_search(query, limit=limit)
    if not results:
        return jsonify({"query": query, "results": [], "total": 0})

    # Fetch verse text + translation for each result
    conn = get_db()
    try:
        out = []
        for ch, v, score, snippet in results:
            row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            text = row["text_uthmani"] if row else ""
            if text:
                text = _strip_bismillah(text, ch, v)
            translation = _best_translation(conn, ch, v)
            # Clean snippet: strip pipe-delimited themes metadata
            display_text = translation if translation else snippet.split(" | ")[0] if snippet else ""
            surah_name = _surah_name(ch)
            out.append({
                "surah": ch,
                "ayah": v,
                "surah_name": surah_name,
                "text_uthmani": text,
                "translation": display_text,
                "score": round(score, 4),
            })
        return jsonify({
            "query": query,
            "results": out,
            "total": len(out),
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/word-meanings")
def get_word_meanings(surah: int, ayah: int):
    """Return AI word meanings for all words in a verse (for tooltips)."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT wm.word_pos, wm.meaning_short, wm.meaning_detailed, "
            "       wm.preferred_translation, wm.preferred_source "
            "FROM ai_word_meanings wm "
            "INNER JOIN ("
            "  SELECT word_pos, MAX(created_at) AS max_created "
            "  FROM ai_word_meanings "
            "  WHERE chapter = ? AND verse = ? "
            "  GROUP BY word_pos"
            ") latest ON wm.word_pos = latest.word_pos AND wm.created_at = latest.max_created "
            "WHERE wm.chapter = ? AND wm.verse = ?",
            (surah, ayah, surah, ayah),
        ).fetchall()

        meanings = {}
        for row in rows:
            entry = {
                "meaning_short": row["meaning_short"],
                "has_detail": bool(row["meaning_detailed"]),
            }
            if row["preferred_translation"]:
                entry["preferred_translation"] = row["preferred_translation"]
                entry["preferred_source"] = row["preferred_source"]
            meanings[str(row["word_pos"])] = entry

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "meanings": meanings,
        })
    finally:
        conn.close()


@app.route("/api/word/<int:surah>:<int:ayah>/<int:pos>")
def get_word_detail(surah: int, ayah: int, pos: int):
    """Return full word analysis data for the dedicated word page."""
    conn = get_db()
    try:
        # Get the AI meaning
        wm_row = conn.execute(
            "SELECT wm.*, c.config_name, c.model_name "
            "FROM ai_word_meanings wm "
            "JOIN ai_translation_configs c ON wm.config_id = c.id "
            "WHERE wm.chapter = ? AND wm.verse = ? AND wm.word_pos = ? "
            "ORDER BY wm.created_at DESC LIMIT 1",
            (surah, ayah, pos),
        ).fetchone()

        # Get verse text + translation
        verse_row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
        if not verse_row:
            return jsonify({"error": f"Verse {surah}:{ayah} not found"}), 404

        trans_row = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()

        # Get morphology for this word
        morph_rows = conn.execute(
            "SELECT form_arabic, form_buckwalter, tag, pos, "
            "       root_buckwalter, root_arabic, lemma_buckwalter, lemma_arabic, "
            "       features_raw, gender, number, person, case_val, voice, mood, "
            "       verb_form, state "
            "FROM morphology WHERE chapter = ? AND verse = ? AND word_pos = ? "
            "ORDER BY segment",
            (surah, ayah, pos),
        ).fetchall()

        if not morph_rows:
            return jsonify({"error": f"Word at position {pos} not found"}), 404

        # Build segments
        segments = []
        main_root_bw = None
        main_lemma_bw = None
        main_lemma_ar = None
        main_root_ar = None
        for row in morph_rows:
            features = {}
            for key in ("gender", "number", "person", "case_val", "voice", "mood", "verb_form", "state"):
                val = row[key]
                if val:
                    display_key = "case" if key == "case_val" else key.replace("_", " ")
                    features[display_key] = val

            segments.append({
                "form_arabic": row["form_arabic"],
                "form_buckwalter": row["form_buckwalter"],
                "tag": row["tag"],
                "pos": row["pos"],
                "root_arabic": row["root_arabic"],
                "root_buckwalter": row["root_buckwalter"],
                "lemma_arabic": row["lemma_arabic"],
                "lemma_buckwalter": row["lemma_buckwalter"],
                "features": features,
                "features_raw": row["features_raw"],
            })
            if row["root_buckwalter"] and not main_root_bw:
                main_root_bw = row["root_buckwalter"]
                main_root_ar = row["root_arabic"]
            if row["lemma_buckwalter"] and not main_lemma_bw:
                main_lemma_bw = row["lemma_buckwalter"]
                main_lemma_ar = row["lemma_arabic"]

        # Get conventional gloss
        glosses = _fetch_word_glosses(conn, surah, ayah)
        conventional_gloss = glosses.get(pos, "")

        # Get cognate data
        cognate = _get_cognate(conn, main_root_bw) if main_root_bw else None

        # Find other occurrences of the same lemma (up to 10)
        other_occurrences = []
        if main_lemma_bw:
            lemma_verses = sorted(_lemma_inv.get(main_lemma_bw, set()))
            count = 0
            for ch, v in lemma_verses:
                if ch == surah and v == ayah:
                    continue
                if count >= 10:
                    break

                # Find the word position(s) with this lemma in the other verse
                occ_morph = conn.execute(
                    "SELECT DISTINCT word_pos FROM morphology "
                    "WHERE chapter = ? AND verse = ? AND lemma_buckwalter = ?",
                    (ch, v, main_lemma_bw),
                ).fetchall()
                occ_positions = [r["word_pos"] for r in occ_morph]

                # Get verse text + translation
                ov_row = conn.execute(
                    "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                    (ch, v),
                ).fetchone()

                # Get conventional gloss for the word in that verse
                occ_glosses = _fetch_word_glosses(conn, ch, v)
                occ_gloss = occ_glosses.get(occ_positions[0], "") if occ_positions else ""

                # Check if AI meaning exists for this occurrence
                occ_ai = conn.execute(
                    "SELECT meaning_short FROM ai_word_meanings "
                    "WHERE chapter = ? AND verse = ? AND word_pos = ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (ch, v, occ_positions[0] if occ_positions else 0),
                ).fetchone()

                other_occurrences.append({
                    "surah": ch,
                    "ayah": v,
                    "word_positions": occ_positions,
                    "text_uthmani": _strip_bismillah(ov_row["text_uthmani"], ch, v) if ov_row else "",
                    "translation": _best_translation(conn, ch, v),
                    "conventional_gloss": occ_gloss,
                    "ai_meaning": occ_ai["meaning_short"] if occ_ai else None,
                })
                count += 1

        result = {
            "surah": surah,
            "ayah": ayah,
            "word_pos": pos,
            "text_uthmani": _strip_bismillah(verse_row["text_uthmani"], surah, ayah),
            "translation": _best_translation(conn, surah, ayah),
            "segments": segments,
            "conventional_gloss": conventional_gloss,
            "root_arabic": main_root_ar,
            "root_buckwalter": main_root_bw,
            "lemma_arabic": main_lemma_ar,
            "lemma_buckwalter": main_lemma_bw,
            "cognate": cognate,
            "other_occurrences": other_occurrences,
            "total_lemma_occurrences": len(_lemma_inv.get(main_lemma_bw, set())) if main_lemma_bw else 0,
        }

        # Add AI meaning fields if available
        if wm_row:
            ai_meaning = {
                "meaning_short": wm_row["meaning_short"],
                "meaning_detailed": wm_row["meaning_detailed"],
                "semantic_field": wm_row["semantic_field"],
                "cross_ref_notes": wm_row["cross_ref_notes"],
                "cognate_notes": wm_row["cognate_notes"],
                "morphology_notes": wm_row["morphology_notes"],
                "departure_notes": wm_row["departure_notes"],
                "config_name": wm_row["config_name"],
                "model_name": wm_row["model_name"],
                "created_at": wm_row["created_at"],
            }
            if wm_row["preferred_translation"]:
                ai_meaning["preferred_translation"] = wm_row["preferred_translation"]
                ai_meaning["preferred_source"] = wm_row["preferred_source"]
            result["ai_meaning"] = ai_meaning
        else:
            result["ai_meaning"] = None

        return jsonify(result)
    finally:
        conn.close()


# --------------- Learning Curriculum API ---------------


@app.route("/api/learning/curriculum")
def get_learning_curriculum():
    """Return all learning units with their roots (lightweight, no verse text)."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT root_buckwalter, root_arabic, unit_number, unit_theme, "
            "       priority_score, frequency_rank, theological_importance, "
            "       derivative_richness, anchor_verse_chapter, anchor_verse_verse, "
            "       related_roots, mnemonic_image_path, mnemonic_caption "
            "FROM learning_curriculum ORDER BY unit_number, priority_score DESC"
        ).fetchall()
        if not rows:
            return jsonify({"units": []})

        # Pre-fetch top 2 derivatives per root (by frequency) for the mnemonic sheet
        all_root_bws = [r["root_buckwalter"] for r in rows]
        top_derivs: dict[str, list] = {bw: [] for bw in all_root_bws}
        if all_root_bws:
            placeholders = ",".join("?" for _ in all_root_bws)
            deriv_rows = conn.execute(
                "SELECT root_buckwalter, lemma_arabic, meaning_gloss, frequency "
                f"FROM learning_derivatives WHERE root_buckwalter IN ({placeholders}) "
                "ORDER BY root_buckwalter, frequency DESC",
                all_root_bws,
            ).fetchall()
            for dr in deriv_rows:
                bw = dr["root_buckwalter"]
                if len(top_derivs[bw]) < 2:
                    top_derivs[bw].append({
                        "lemma_arabic": dr["lemma_arabic"],
                        "meaning_gloss": dr["meaning_gloss"],
                    })

        units: dict[int, dict] = {}
        for r in rows:
            un = r["unit_number"]
            if un not in units:
                units[un] = {
                    "unit_number": un,
                    "unit_theme": r["unit_theme"],
                    "roots": [],
                }
            units[un]["roots"].append({
                "root_buckwalter": r["root_buckwalter"],
                "root_arabic": r["root_arabic"],
                "frequency_rank": r["frequency_rank"],
                "theological_importance": r["theological_importance"],
                "derivative_richness": r["derivative_richness"],
                "anchor_verse": f"{r['anchor_verse_chapter']}:{r['anchor_verse_verse']}",
                "related_roots": json.loads(r["related_roots"]) if r["related_roots"] else [],
                "mnemonic_image_url": (
                    f"/api/learning/root/{r['root_buckwalter']}/mnemonic-image?v={_MNEMONIC_VERSION}"
                    if r["mnemonic_image_path"] else None
                ),
                "mnemonic_caption": r["mnemonic_caption"] or None,
                "top_derivatives": top_derivs.get(r["root_buckwalter"], []),
            })
        return jsonify({"units": list(units.values())})
    finally:
        conn.close()


@app.route("/api/learning/root/<root_bw>")
def get_learning_root(root_bw: str):
    """Return full teaching package for one root."""
    conn = get_db()
    try:
        # Curriculum entry
        cur = conn.execute(
            "SELECT * FROM learning_curriculum WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not cur:
            return jsonify({"error": "Root not in curriculum"}), 404

        # Derivatives
        derivs = conn.execute(
            "SELECT lemma_buckwalter, lemma_arabic, pos, verb_form, frequency, "
            "       meaning_gloss, semantic_shift, display_order "
            "FROM learning_derivatives WHERE root_buckwalter = ? "
            "ORDER BY display_order",
            (root_bw,),
        ).fetchall()

        # Context verses
        ctx_rows = conn.execute(
            "SELECT chapter, verse, target_lemma_buckwalter, verse_role, "
            "       teaching_note, display_order "
            "FROM learning_context_verses WHERE root_buckwalter = ? "
            "ORDER BY display_order",
            (root_bw,),
        ).fetchall()

        # Build verse data for anchor + context verses
        all_verse_refs = [(cur["anchor_verse_chapter"], cur["anchor_verse_verse"])]
        for cv in ctx_rows:
            all_verse_refs.append((cv["chapter"], cv["verse"]))

        verses_data = {}
        for ch, v in set(all_verse_refs):
            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            t_row = _best_translation(conn, ch, v)

            text = v_row["text_uthmani"] if v_row else ""
            if ch > 1 and v == 1:
                text = _strip_bismillah(text, ch, v)

            # Split clean Uthmani text into words for display
            uthmani_words = text.split() if text else []

            # Get morphology for the verse — aggregate segments per word_pos
            morph_rows = conn.execute(
                "SELECT word_pos, form_arabic, lemma_buckwalter, lemma_arabic, "
                "       root_buckwalter, tag, pos, features_raw "
                "FROM morphology WHERE chapter = ? AND verse = ? "
                "ORDER BY word_pos, segment",
                (ch, v),
            ).fetchall()

            # Aggregate: pick the most informative segment per word_pos
            # (the one with a root/lemma, or the first one as fallback)
            word_meta = {}
            for mr in morph_rows:
                wp = mr["word_pos"]
                if wp not in word_meta:
                    word_meta[wp] = mr
                elif mr["root_buckwalter"] and not word_meta[wp]["root_buckwalter"]:
                    word_meta[wp] = mr
                elif mr["lemma_buckwalter"] and not word_meta[wp]["lemma_buckwalter"]:
                    word_meta[wp] = mr

            # Get word glosses
            glosses = _fetch_word_glosses(conn, ch, v)

            # Get AI word meanings
            ai_meanings = {}
            wm_rows = conn.execute(
                "SELECT word_pos, meaning_short, preferred_translation, preferred_source "
                "FROM ai_word_meanings WHERE chapter = ? AND verse = ? "
                "ORDER BY created_at DESC",
                (ch, v),
            ).fetchall()
            seen_pos = set()
            for wmr in wm_rows:
                wp = wmr["word_pos"]
                if wp not in seen_pos:
                    seen_pos.add(wp)
                    ai_meanings[wp] = {
                        "meaning_short": wmr["meaning_short"],
                        "preferred_translation": wmr["preferred_translation"],
                        "preferred_source": wmr["preferred_source"],
                    }

            words = []
            for wp in sorted(word_meta.keys()):
                mr = word_meta[wp]
                # Use clean Uthmani text for display, fall back to form_arabic
                display_arabic = uthmani_words[wp - 1] if wp <= len(uthmani_words) else mr["form_arabic"]
                w = {
                    "pos": wp,
                    "arabic": display_arabic,
                    "lemma_bw": mr["lemma_buckwalter"],
                    "lemma_ar": mr["lemma_arabic"],
                    "root_bw": mr["root_buckwalter"],
                    "tag": mr["tag"],
                    "part_of_speech": mr["pos"],
                    "gloss": glosses.get(wp, ""),
                    "is_target": mr["root_buckwalter"] == root_bw,
                }
                if wp in ai_meanings:
                    w["ai_meaning"] = ai_meanings[wp]
                words.append(w)

            verses_data[f"{ch}:{v}"] = {
                "chapter": ch,
                "verse": v,
                "text_uthmani": text,
                "translation": t_row or "",
                "surah_name": _surah_name(ch),
                "words": words,
            }

        # Cognate data
        cognate = _get_cognate(conn, root_bw)

        # Related roots info
        related_roots_data = []
        related_bw_list = json.loads(cur["related_roots"]) if cur["related_roots"] else []
        for rbw in related_bw_list:
            rel_cur = conn.execute(
                "SELECT root_arabic, unit_number, unit_theme "
                "FROM learning_curriculum WHERE root_buckwalter = ?",
                (rbw,),
            ).fetchone()
            if rel_cur:
                related_roots_data.append({
                    "root_buckwalter": rbw,
                    "root_arabic": rel_cur["root_arabic"],
                    "unit_number": rel_cur["unit_number"],
                    "unit_theme": rel_cur["unit_theme"],
                })

        anchor_key = f"{cur['anchor_verse_chapter']}:{cur['anchor_verse_verse']}"

        context_verses = []
        for cv in ctx_rows:
            vkey = f"{cv['chapter']}:{cv['verse']}"
            context_verses.append({
                "verse_ref": vkey,
                "verse_data": verses_data.get(vkey),
                "target_lemma_buckwalter": cv["target_lemma_buckwalter"],
                "verse_role": cv["verse_role"],
                "teaching_note": cv["teaching_note"],
            })

        mnemonic_url = (
            f"/api/learning/root/{root_bw}/mnemonic-image?v={_MNEMONIC_VERSION}"
            if cur["mnemonic_image_path"] else None
        )

        return jsonify({
            "root_buckwalter": root_bw,
            "root_arabic": cur["root_arabic"],
            "unit_number": cur["unit_number"],
            "unit_theme": cur["unit_theme"],
            "theological_importance": cur["theological_importance"],
            "root_story": cur["root_story"],
            "teaching_notes": cur["teaching_notes"],
            "mnemonic_image_url": mnemonic_url,
            "mnemonic_caption": cur["mnemonic_caption"] if cur["mnemonic_caption"] else None,
            "anchor_verse": {
                "verse_ref": anchor_key,
                "verse_data": verses_data.get(anchor_key),
            },
            "derivatives": [dict(d) for d in derivs],
            "context_verses": context_verses,
            "cognate": cognate,
            "related_roots": related_roots_data,
        })
    finally:
        conn.close()


@app.route("/api/learning/root/<root_bw>/mnemonic-image")
def get_mnemonic_image(root_bw: str):
    """Serve the mnemonic image for a root word."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT mnemonic_image_path FROM learning_curriculum WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
    finally:
        conn.close()

    if not row or not row["mnemonic_image_path"]:
        return jsonify({"error": "No mnemonic image for this root"}), 404

    # mnemonic_image_path is stored relative to the backend dir
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    img_abs = os.path.join(backend_dir, row["mnemonic_image_path"])
    img_dir = os.path.dirname(img_abs)
    img_file = os.path.basename(img_abs)

    if not os.path.isfile(img_abs):
        return jsonify({"error": "Image file not found on disk"}), 404

    response = send_from_directory(img_dir, img_file, mimetype="image/webp")
    # Use file mtime as ETag so updated images are re-fetched
    mtime = int(os.path.getmtime(img_abs))
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["ETag"] = f'"{root_bw}-{mtime}"'
    return response


@app.route("/api/learning/root/<root_bw>/review-verses")
def get_learning_review_verses(root_bw: str):
    """Return fresh verses for spaced repetition review of a root.

    Query param: exclude=1:1,2:255 (comma-separated verse refs to skip)
    """
    exclude_str = request.args.get("exclude", "")
    exclude_set = set()
    for ref in exclude_str.split(","):
        ref = ref.strip()
        if ":" in ref:
            parts = ref.split(":")
            try:
                exclude_set.add((int(parts[0]), int(parts[1])))
            except ValueError:
                pass

    # Get all verses containing this root from the inverted index
    all_verses = _root_inv.get(root_bw, set())
    if not all_verses:
        return jsonify({"verses": []})

    # Filter out excluded verses and sort by IDF distinctiveness
    candidates = [v for v in all_verses if v not in exclude_set]
    if not candidates:
        return jsonify({"verses": []})

    # Rank by how "distinctive" this root is in each verse (fewer total roots = more focused)
    root_idf = _root_idf.get(root_bw, 1.0)

    def verse_score(key):
        """Prefer shorter verses where this root is prominent."""
        vr = _verse_roots.get(key, set())
        vl = _verse_lemmas.get(key, set())
        total_content = len(vr) + len(vl)
        return root_idf / max(total_content, 1)

    candidates.sort(key=verse_score, reverse=True)
    top = candidates[:5]

    conn = get_db()
    try:
        result = []
        for ch, v in top:
            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            t_row = _best_translation(conn, ch, v)

            text = v_row["text_uthmani"] if v_row else ""
            if ch > 1 and v == 1:
                text = _strip_bismillah(text, ch, v)
            uthmani_words = text.split() if text else []

            # Find which word positions have this root
            morph_rows = conn.execute(
                "SELECT word_pos, form_arabic, lemma_buckwalter, lemma_arabic "
                "FROM morphology WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                (ch, v, root_bw),
            ).fetchall()
            # Deduplicate by word_pos (multiple segments per word)
            seen_wp = set()
            unique_morph = []
            for mr in morph_rows:
                if mr["word_pos"] not in seen_wp:
                    seen_wp.add(mr["word_pos"])
                    unique_morph.append(mr)
            target_positions = [mr["word_pos"] for mr in unique_morph]

            glosses = _fetch_word_glosses(conn, ch, v)

            result.append({
                "chapter": ch,
                "verse": v,
                "surah_name": _surah_name(ch),
                "text_uthmani": text,
                "translation": t_row or "",
                "target_positions": target_positions,
                "target_words": [
                    {
                        "pos": mr["word_pos"],
                        "arabic": uthmani_words[mr["word_pos"] - 1]
                            if mr["word_pos"] <= len(uthmani_words)
                            else mr["form_arabic"],
                        "lemma_bw": mr["lemma_buckwalter"],
                        "lemma_ar": mr["lemma_arabic"],
                        "gloss": glosses.get(mr["word_pos"], ""),
                    }
                    for mr in unique_morph
                ],
            })
        return jsonify({"verses": result})
    finally:
        conn.close()


@app.route("/api/learning/ask", methods=["POST"])
def learning_ask():
    """On-demand LLM explanation for a root concept.

    Expects JSON: { root_bw, question, context? }
    Calls Ollama and returns the explanation.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("root_bw") or not data.get("question"):
        return jsonify({"error": "root_bw and question are required"}), 400

    root_bw = data["root_bw"]
    question = data["question"][:500]  # Limit question length

    conn = get_db()
    try:
        # Gather root context
        cur = conn.execute(
            "SELECT root_arabic, root_story, teaching_notes "
            "FROM learning_curriculum WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not cur:
            return jsonify({"error": "Root not in curriculum"}), 404

        # Get derivatives for context
        derivs = conn.execute(
            "SELECT lemma_arabic, meaning_gloss, verb_form, frequency "
            "FROM learning_derivatives WHERE root_buckwalter = ? ORDER BY frequency DESC",
            (root_bw,),
        ).fetchall()

        deriv_lines = []
        for d in derivs:
            vf = f" (Form {d['verb_form']})" if d["verb_form"] else ""
            deriv_lines.append(f"- {d['lemma_arabic']}{vf}: {d['meaning_gloss']} ({d['frequency']}x)")

        root_arabic = cur["root_arabic"]
        root_story = cur["root_story"] or ""

        system_prompt = (
            "You are a Quranic Arabic teacher explaining root concepts to a learner. "
            "Be clear, accurate, and engaging. Reference specific Quranic usage when helpful. "
            "Keep your answer concise (under 200 words)."
        )

        user_prompt = (
            f"Root: {root_arabic} ({root_bw})\n\n"
            f"Root story:\n{root_story[:500]}\n\n"
            f"Derivatives:\n" + "\n".join(deriv_lines[:10]) + "\n\n"
            f"Student's question: {question}"
        )

        # Try to call Ollama
        OLLAMA_URL = "http://localhost:11434/api/chat"
        model = "qwen3:14b"

        try:
            t0 = time.time()
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
                timeout=120,
            )
            resp.raise_for_status()
            answer = resp.json()["message"]["content"]
            elapsed = int((time.time() - t0) * 1000)
            return jsonify({"answer": answer, "model": model, "elapsed_ms": elapsed})
        except Exception as e:
            return jsonify({"error": f"LLM unavailable: {str(e)}"}), 503

    finally:
        conn.close()


# --------------- SEO helpers ---------------

SITE_URL = os.environ.get("SITE_URL", "https://al-nuqta.com")


def _is_known_spa_path(path: str) -> bool:
    if path == "/":
        return True
    if re.match(r"^/privacy/extension/?$", path):
        return True
    if re.match(r"^/verse/\d+:\d+$", path):
        return True
    if re.match(r"^/root/.+$", path):
        return True
    if re.match(r"^/word/\d+:\d+/\d+$", path):
        return True
    if re.match(r"^/learning(/root/.+|/mnemonic-sheet)?/?$", path):
        return True
    if re.match(r"^/settings/?$", path):
        return True
    if re.match(r"^/developers/?$", path):
        return True
    if re.match(r"^/methodology/?$", path):
        return True
    if re.match(r"^/admin(/settings|/media(/recitations|/resources|/generate)?)?/?$", path):
        return True
    return False


def _get_seo_meta(path: str) -> dict:
    """Return title, description, og_type for a given URL path."""
    # Extension privacy page: /privacy/extension
    if re.match(r"^/privacy/extension/?$", path):
        return {
            "title": "Quran Research Tool Privacy Policy | al-nuqta",
            "description": "Privacy policy for the Quran Research Tool Chrome extension, including data access, usage, and retention details.",
            "og_type": "article",
            "canonical": SITE_URL + "/privacy/extension",
            "robots": "index, follow",
        }

    # Verse page: /verse/2:255
    m = re.match(r"^/verse/(\d+):(\d+)$", path)
    if m:
        surah, ayah = int(m.group(1)), int(m.group(2))
        name = _surah_name(surah)
        snippet = ""
        arabic = ""
        try:
            conn = get_db()
            snippet = _best_translation(conn, surah, ayah)[:160]
            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (surah, ayah),
            ).fetchone()
            if v_row:
                arabic = v_row["text_uthmani"][:80]
            conn.close()
        except Exception:
            pass
        desc_parts = []
        if arabic:
            desc_parts.append(f"\u201c{arabic}\u201d")
        if snippet:
            desc_parts.append(snippet)
        else:
            desc_parts.append(f"Explore root words, morphology, and etymology of Quran verse {surah}:{ayah}.")
        return {
            "title": f"Surah {name} ({surah}:{ayah}) | al-nuqta",
            "description": " \u2014 ".join(desc_parts),
            "og_type": "article",
            "canonical": f"{SITE_URL}/verse/{surah}:{ayah}",
            "robots": "index, follow",
        }

    # Root page: /root/rHm
    m = re.match(r"^/root/(.+)$", path)
    if m:
        root_bw = m.group(1)
        root_arabic = _root_arabic_map.get(root_bw, "")
        count = len(_root_inv.get(root_bw, set()))
        label = f"Root {root_arabic} ({root_bw})" if root_arabic else f"Root {root_bw}"
        # Try to get lemmas for a richer description
        lemma_samples = ""
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT DISTINCT lemma_arabic FROM morphology "
                "WHERE root_buckwalter = ? AND lemma_arabic IS NOT NULL LIMIT 5",
                (root_bw,),
            ).fetchall()
            conn.close()
            if rows:
                lemma_samples = ", ".join(r["lemma_arabic"] for r in rows)
        except Exception:
            pass
        desc = f"Explore {count} Quran verses containing the root {root_arabic or root_bw}"
        if lemma_samples:
            desc += f" \u2014 derivatives include {lemma_samples}"
        desc += ". Morphological breakdowns, cross-references, and Semitic cognates."
        return {
            "title": f"{label} \u2014 {count} Verses | al-nuqta",
            "description": desc[:160],
            "og_type": "article",
            "canonical": f"{SITE_URL}/root/{quote(root_bw)}",
            "robots": "index, follow",
        }

    # Word page: /word/2:255/3
    m = re.match(r"^/word/(\d+):(\d+)/(\d+)$", path)
    if m:
        surah, ayah, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        name = _surah_name(surah)
        word_arabic = ""
        word_gloss = ""
        try:
            conn = get_db()
            w_row = conn.execute(
                "SELECT form_arabic, lemma_arabic FROM morphology "
                "WHERE chapter = ? AND verse = ? AND word_pos = ? LIMIT 1",
                (surah, ayah, pos),
            ).fetchone()
            if w_row:
                word_arabic = w_row["form_arabic"] or ""
            glosses = _fetch_word_glosses(conn, surah, ayah)
            word_gloss = glosses.get(pos, "")
            conn.close()
        except Exception:
            pass
        word_label = f"{word_arabic} " if word_arabic else ""
        gloss_part = f' \u2014 "{word_gloss}"' if word_gloss else ""
        return {
            "title": f"{word_label}Word {pos}, {name} {surah}:{ayah} | al-nuqta",
            "description": f"Morphology, etymology, and AI analysis of {word_label}(word {pos}) in Surah {name} {surah}:{ayah}{gloss_part}.",
            "og_type": "article",
            "canonical": f"{SITE_URL}/word/{surah}:{ayah}/{pos}",
            "robots": "index, follow",
        }

    # Methodology: /methodology
    if re.match(r"^/methodology/?$", path):
        return {
            "title": "Methodology \u2014 How We Translate the Quran | al-nuqta",
            "description": "Our translation uses three lenses: the Quran\u2019s own internal cross-references, Semitic cognate etymology across 59 languages, and morphological precision \u2014 ensuring every word is grounded in evidence.",
            "og_type": "article",
            "canonical": SITE_URL + "/methodology",
            "robots": "index, follow",
        }

    # Developers / API: /developers
    if re.match(r"^/developers/?$", path):
        return {
            "title": "Public API \u2014 Build with the Quran Corpus | al-nuqta",
            "description": "Free, open API for accessing Quranic text, morphology, root analysis, Semitic etymology, and translations. No API key required \u2014 just send a GET request.",
            "og_type": "website",
            "canonical": SITE_URL + "/developers",
            "robots": "index, follow",
        }

    # Home
    if path == "/":
        return {
            "title": "al-nuqta \u2014 A Root Based Translation of the Quran",
            "description": "Explore Quranic Arabic through its root words. Trace any word back to its Semitic origins, compare cross-references across 6,236 verses, and study morphology \u2014 all grounded in the Quran\u2019s own usage.",
            "og_type": "website",
            "canonical": SITE_URL + "/",
            "robots": "index, follow",
        }

    # Learning root detail: /learning/root/<root_bw>
    m = re.match(r"^/learning/root/(.+?)/?$", path)
    if m:
        root_bw = m.group(1)
        root_arabic = _root_arabic_map.get(root_bw, root_bw)
        # Get curriculum data for richer meta
        try:
            conn = get_db()
            cur = conn.execute(
                "SELECT root_story, unit_theme FROM learning_curriculum WHERE root_buckwalter = ?",
                (root_bw,),
            ).fetchone()
            conn.close()
            theme = cur["unit_theme"] if cur else ""
            snippet = cur["root_story"][:155] + "..." if cur and cur["root_story"] else ""
            desc = snippet or f"Learn the Quranic root {root_arabic} ({root_bw}) — its derivatives, usage across verses, and theological significance."
        except Exception:
            theme = ""
            desc = f"Learn the Quranic root {root_arabic} ({root_bw}) — its derivatives, usage across verses, and theological significance."
        title_theme = f" — {theme}" if theme else ""
        return {
            "title": f"Root {root_arabic} ({root_bw}){title_theme} | Learn Quranic Arabic",
            "description": desc,
            "og_type": "article",
            "canonical": f"{SITE_URL}/learning/root/{quote(root_bw)}",
            "robots": "index, follow",
        }

    # Mnemonic sheet: /learning/mnemonic-sheet
    if re.match(r"^/learning/mnemonic-sheet/?$", path):
        return {
            "title": "Mnemonic Sheet — 50 Quranic Root Words | Learn Quranic Arabic",
            "description": "Visual mnemonic cards for the 50 most important Quranic Arabic root words. Each card pairs an iconic image with the root's etymological meaning.",
            "og_type": "article",
            "canonical": SITE_URL + "/learning/mnemonic-sheet",
            "robots": "index, follow",
        }

    # Learning dashboard: /learning
    if re.match(r"^/learning/?$", path):
        return {
            "title": "Learn Quranic Arabic | Quranic Concept Web",
            "description": "Learn Arabic vocabulary through the Quran itself. Master 50 root word families across 8 thematic units with spaced repetition, connecting vocabulary to theological understanding.",
            "og_type": "website",
            "ld_type": "Course",
            "canonical": SITE_URL + "/learning",
            "robots": "index, follow",
        }

    # Unknown page
    return {
        "title": "Page Not Found | al-nuqta",
        "description": "The requested page does not exist.",
        "og_type": "website",
        "canonical": SITE_URL + path,
        "robots": "noindex, follow",
    }


def _build_meta_tags(meta: dict) -> str:
    """Build HTML meta tag block from SEO meta dict."""
    title = meta["title"]
    desc = meta["description"]
    canonical = meta["canonical"]
    og_type = meta["og_type"]
    robots = meta.get("robots", "index, follow")

    title_e = html.escape(title, quote=True)
    desc_e = html.escape(desc, quote=True)
    canonical_e = html.escape(canonical, quote=True)
    robots_e = html.escape(robots, quote=True)

    og_image = html.escape(meta.get("og_image", f"{SITE_URL}/og-default.png"), quote=True)

    tags = [
        f'<meta name="description" content="{desc_e}" />',
        f'<meta name="robots" content="{robots_e}" />',
        f'<link rel="canonical" href="{canonical_e}" />',
        # Open Graph
        f'<meta property="og:title" content="{title_e}" />',
        f'<meta property="og:description" content="{desc_e}" />',
        f'<meta property="og:type" content="{og_type}" />',
        f'<meta property="og:url" content="{canonical_e}" />',
        f'<meta property="og:site_name" content="al-nuqta" />',
        f'<meta property="og:image" content="{og_image}" />',
        f'<meta property="og:locale" content="en_US" />',
        # Twitter Card
        f'<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{title_e}" />',
        f'<meta name="twitter:description" content="{desc_e}" />',
        f'<meta name="twitter:image" content="{og_image}" />',
    ]

    # JSON-LD structured data
    ld_type = meta.get("ld_type")
    if ld_type == "Course":
        ld = {
            "@context": "https://schema.org",
            "@type": "Course",
            "name": title,
            "description": desc,
            "url": canonical,
            "provider": {
                "@type": "Organization",
                "name": "al-nuqta",
                "url": SITE_URL,
            },
            "educationalLevel": "Beginner",
            "inLanguage": ["ar", "en"],
            "isAccessibleForFree": True,
            "hasCourseInstance": {
                "@type": "CourseInstance",
                "courseMode": "online",
                "courseWorkload": "PT1H",
            },
        }
    elif og_type == "website":
        ld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "al-nuqta",
            "url": SITE_URL,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{SITE_URL}/verse/{{surah}}:{{ayah}}",
                "query-input": "required name=surah,ayah",
            },
        }
    else:
        ld = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": desc,
            "url": canonical,
            "publisher": {
                "@type": "Organization",
                "name": "al-nuqta",
                "url": SITE_URL,
            },
        }
    ld_json = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    tags.append(f'<script type="application/ld+json">{ld_json}</script>')

    return "\n    ".join(tags)


# --------------- robots.txt & sitemap.xml ---------------

@app.route("/llms.txt")
def llms_txt():
    """Serve llms.txt for AI/LLM crawler discovery."""
    # In production, serve from static/; in dev, from frontend public/
    llms_path = os.path.join(STATIC_DIR, "llms.txt") if SERVE_STATIC else None
    if llms_path and os.path.isfile(llms_path):
        return send_from_directory(STATIC_DIR, "llms.txt", mimetype="text/plain")
    # Fallback: serve from frontend public dir in dev
    frontend_public = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
    llms_dev = os.path.join(frontend_public, "llms.txt")
    if os.path.isfile(llms_dev):
        return send_from_directory(os.path.abspath(frontend_public), "llms.txt", mimetype="text/plain")
    return Response("# llms.txt not found", mimetype="text/plain", status=404)


@app.route("/robots.txt")
def robots_txt():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /tools/\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
        "\n"
        "# Allow AI/LLM crawlers to access the public API\n"
        "User-agent: GPTBot\n"
        "Allow: /api/v1/\n"
        "Disallow: /api/learning/\n"
        "\n"
        "User-agent: ChatGPT-User\n"
        "Allow: /api/v1/\n"
        "Disallow: /api/learning/\n"
        "\n"
        "User-agent: Claude-Web\n"
        "Allow: /api/v1/\n"
        "Disallow: /api/learning/\n"
        "\n"
        "User-agent: PerplexityBot\n"
        "Allow: /api/v1/\n"
        "Disallow: /api/learning/\n"
        "\n"
        "User-agent: CCBot\n"
        "Allow: /api/v1/\n"
        "Disallow: /api/learning/\n"
    )
    return Response(body, mimetype="text/plain")


_sitemap_cache: dict = {"xml": None}


@app.route("/sitemap.xml")
def sitemap_xml():
    if _sitemap_cache["xml"]:
        resp = Response(_sitemap_cache["xml"], mimetype="application/xml")
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp

    urls = []

    def _add(loc: str, priority: str):
        urls.append(f"  <url><loc>{loc}</loc><priority>{priority}</priority></url>")

    # Home
    _add(SITE_URL + "/", "1.0")
    _add(SITE_URL + "/privacy/extension", "0.3")

    # All verse pages
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT chapter, verse FROM verses ORDER BY chapter, verse"
        ).fetchall()
        for row in rows:
            _add(f"{SITE_URL}/verse/{row['chapter']}:{row['verse']}", "0.7")

        # All root pages (from in-memory IDF engine)
        for root_bw in sorted(_root_arabic_map.keys()):
            _add(f"{SITE_URL}/root/{quote(root_bw)}", "0.6")

        # Learning pages
        _add(SITE_URL + "/learning", "0.8")
        _add(SITE_URL + "/learning/mnemonic-sheet", "0.7")
        cur_roots = conn.execute(
            "SELECT root_buckwalter FROM learning_curriculum ORDER BY unit_number, priority_score DESC"
        ).fetchall()
        for cr in cur_roots:
            _add(f"{SITE_URL}/learning/root/{quote(cr['root_buckwalter'])}", "0.7")
    finally:
        conn.close()

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>\n"

    _sitemap_cache["xml"] = xml
    resp = Response(xml, mimetype="application/xml")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


# --------------- Root Search ---------------

@app.route("/api/roots/search")
def search_roots():
    """Search roots by Buckwalter, phonetic alias, Arabic text, or English meaning.

    Query params:
        q: search query (required, min 1 char)
        limit: max results (default 10, max 30)

    Returns list of matching roots with Arabic form, meaning, frequency, and sample verse.
    """
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])

    limit = min(int(request.args.get("limit", 10)), 30)

    conn = get_db()
    try:
        matched_roots = {}  # root_bw -> match_score

        # 1. Direct Buckwalter match (exact or prefix)
        for root_bw in _root_arabic_map:
            if root_bw.lower() == q:
                matched_roots[root_bw] = 100  # exact match
            elif root_bw.lower().startswith(q):
                matched_roots[root_bw] = 80   # prefix match

        # 2. Arabic text -> resolve to root via morphology
        # Check if query contains Arabic characters
        if any('\u0600' <= c <= '\u06FF' for c in q):
            # Look up the Arabic word in morphology to find its root
            rows = conn.execute(
                "SELECT DISTINCT root_buckwalter, root_arabic FROM morphology "
                "WHERE (arabic_word LIKE ? OR lemma_arabic LIKE ?) "
                "AND root_buckwalter IS NOT NULL AND root_buckwalter != '' "
                "LIMIT 20",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
            for r in rows:
                rbw = r["root_buckwalter"]
                if rbw not in matched_roots:
                    matched_roots[rbw] = 70

        # 3. Alias table lookup
        try:
            alias_rows = conn.execute(
                "SELECT root_buckwalter, source FROM root_search_aliases "
                "WHERE alias = ? OR alias LIKE ?",
                (q, f"{q}%"),
            ).fetchall()
            for r in alias_rows:
                rbw = r["root_buckwalter"]
                score = 75 if r["source"] == "ai" else 60
                if rbw not in matched_roots or matched_roots[rbw] < score:
                    matched_roots[rbw] = score
        except sqlite3.OperationalError:
            pass  # table may not exist yet

        # 4. AI root meanings search
        if len(q) >= 2 and not any('\u0600' <= c <= '\u06FF' for c in q):
            try:
                ai_rows = conn.execute(
                    "SELECT DISTINCT root_buckwalter FROM ai_root_meanings "
                    "WHERE LOWER(primary_meaning) LIKE ? OR LOWER(semantic_field) LIKE ? "
                    "LIMIT 20",
                    (f"%{q}%", f"%{q}%"),
                ).fetchall()
                for r in ai_rows:
                    rbw = r["root_buckwalter"]
                    if rbw not in matched_roots or matched_roots[rbw] < 55:
                        matched_roots[rbw] = 55
            except sqlite3.OperationalError:
                pass

        # 5. English meaning search in learning_derivatives
        if len(q) >= 2 and not any('\u0600' <= c <= '\u06FF' for c in q):
            try:
                meaning_rows = conn.execute(
                    "SELECT DISTINCT root_buckwalter FROM learning_derivatives "
                    "WHERE LOWER(meaning_gloss) LIKE ? LIMIT 20",
                    (f"%{q}%",),
                ).fetchall()
                for r in meaning_rows:
                    rbw = r["root_buckwalter"]
                    if rbw not in matched_roots:
                        matched_roots[rbw] = 50
            except sqlite3.OperationalError:
                pass

            # Also search word_glosses for English meanings
            try:
                gloss_rows = conn.execute(
                    "SELECT DISTINCT m.root_buckwalter FROM morphology m "
                    "JOIN word_glosses wg ON m.chapter = wg.chapter AND m.verse = wg.verse AND m.word_pos = wg.word_pos "
                    "WHERE LOWER(wg.translation_en) LIKE ? "
                    "AND m.root_buckwalter IS NOT NULL AND m.root_buckwalter != '' "
                    "LIMIT 20",
                    (f"%{q}%",),
                ).fetchall()
                for r in gloss_rows:
                    rbw = r["root_buckwalter"]
                    if rbw not in matched_roots:
                        matched_roots[rbw] = 45
            except sqlite3.OperationalError:
                pass

        if not matched_roots:
            return jsonify([])

        # Sort by score desc, then by frequency desc
        scored = []
        for root_bw, score in matched_roots.items():
            freq = len(_root_inv.get(root_bw, set()))
            scored.append((root_bw, score, freq))
        scored.sort(key=lambda x: (-x[1], -x[2]))
        scored = scored[:limit]

        # Build rich results
        results = []
        for root_bw, score, freq in scored:
            root_arabic = _root_arabic_map.get(root_bw, "")

            # Get top meaning: AI root meaning > learning_derivatives > word_glosses
            meaning = ""
            try:
                ai_row = conn.execute(
                    "SELECT primary_meaning FROM ai_root_meanings "
                    "WHERE root_buckwalter = ? ORDER BY config_id DESC LIMIT 1",
                    (root_bw,),
                ).fetchone()
                if ai_row:
                    meaning = ai_row["primary_meaning"]
            except sqlite3.OperationalError:
                pass

            if not meaning:
                try:
                    m_row = conn.execute(
                        "SELECT meaning_gloss FROM learning_derivatives "
                        "WHERE root_buckwalter = ? ORDER BY frequency DESC LIMIT 1",
                        (root_bw,),
                    ).fetchone()
                    if m_row:
                        meaning = m_row["meaning_gloss"]
                except sqlite3.OperationalError:
                    pass

            if not meaning:
                try:
                    g_row = conn.execute(
                        "SELECT wg.translation_en, COUNT(*) AS cnt FROM morphology m "
                        "JOIN word_glosses wg ON m.chapter = wg.chapter AND m.verse = wg.verse AND m.word_pos = wg.word_pos "
                        "WHERE m.root_buckwalter = ? AND wg.translation_en IS NOT NULL AND wg.translation_en != '' "
                        "GROUP BY wg.translation_en ORDER BY cnt DESC, LENGTH(wg.translation_en) ASC LIMIT 1",
                        (root_bw,),
                    ).fetchone()
                    if g_row:
                        meaning = g_row["translation_en"]
                except sqlite3.OperationalError:
                    pass

            # Get one sample verse with Arabic words and matched positions
            sample = None
            verse_keys = sorted(_root_inv.get(root_bw, set()))[:1]
            if verse_keys:
                ch, v = verse_keys[0]
                vrow = conn.execute(
                    "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                    (ch, v),
                ).fetchone()
                if vrow:
                    arabic_text = _strip_bismillah(vrow["text_uthmani"], ch, v)
                    arabic_words = arabic_text.split()
                    # Find which word positions contain this root
                    morph_rows = conn.execute(
                        "SELECT DISTINCT word_pos FROM morphology "
                        "WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                        (ch, v, root_bw),
                    ).fetchall()
                    matched_positions = [r["word_pos"] for r in morph_rows]
                    # Window around matched word so it's always visible
                    max_words = 10
                    if arabic_words and matched_positions:
                        first_match = min(matched_positions) - 1  # 0-based
                        if len(arabic_words) <= max_words:
                            start = 0
                        elif first_match <= max_words // 2:
                            start = 0
                        else:
                            start = min(first_match - max_words // 2, len(arabic_words) - max_words)
                    else:
                        start = 0
                    end = start + max_words
                    windowed_words = arabic_words[start:end]
                    # Adjust positions to be relative to the window
                    adjusted_positions = [p - start for p in matched_positions if start < p <= start + max_words]
                    sample = {
                        "ref": f"{ch}:{v}",
                        "words": windowed_words,
                        "matched_positions": adjusted_positions,
                        "starts_truncated": start > 0,
                        "ends_truncated": end < len(arabic_words),
                        "translation": _best_translation(conn, ch, v)[:150],
                    }

            # Check if it's in the learning curriculum
            in_curriculum = False
            try:
                c_row = conn.execute(
                    "SELECT 1 FROM learning_curriculum WHERE root_buckwalter = ?",
                    (root_bw,),
                ).fetchone()
                in_curriculum = c_row is not None
            except sqlite3.OperationalError:
                pass

            results.append({
                "root_buckwalter": root_bw,
                "root_arabic": root_arabic,
                "meaning": meaning,
                "frequency": freq,
                "in_curriculum": in_curriculum,
                "sample_verse": sample,
            })

        return jsonify(results)
    finally:
        conn.close()


# --------------- Admin auth ---------------

_ADMIN_JWT_EXP_HOURS = 24

# Simple in-memory rate limiter for login attempts
_login_attempts: dict[str, list[float]] = {}
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 300  # 5 minutes


def _check_rate_limit(ip: str) -> bool:
    """Return True if the IP is rate-limited."""
    now = time.time()
    # Periodically purge stale IPs to prevent unbounded growth
    if len(_login_attempts) > 1000:
        stale = [k for k, v in _login_attempts.items() if not v or now - v[-1] > _LOGIN_WINDOW_SECONDS]
        for k in stale:
            del _login_attempts[k]
    attempts = _login_attempts.get(ip, [])
    # Prune old attempts
    attempts = [t for t in attempts if now - t < _LOGIN_WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= _LOGIN_MAX_ATTEMPTS


def _record_attempt(ip: str):
    _login_attempts.setdefault(ip, []).append(time.time())


def _ensure_admin_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                pw_changed_at INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration: add pw_changed_at if missing
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(admin_users)").fetchall()]
        if "pw_changed_at" not in cols:
            conn.execute("ALTER TABLE admin_users ADD COLUMN pw_changed_at INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        conn.commit()
        # Seed default admin if none exists
        row = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()
        if row[0] == 0:
            default_pw = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                ("admin", default_pw),
            )
            conn.commit()
    finally:
        conn.close()

_ensure_admin_table()


def _ensure_admin_media_tables():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_voices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                voice_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

_ensure_admin_media_tables()


def _create_admin_token(user_id: int, username: str, pw_changed_at: int = 0) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": now + _ADMIN_JWT_EXP_HOURS * 3600,
        "iat": now,
        "pwc": pw_changed_at,  # invalidated when password changes
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        # Check token wasn't issued before a password change
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT pw_changed_at FROM admin_users WHERE id = ?",
                (int(payload["sub"]),),
            ).fetchone()
            if not row:
                return jsonify({"error": "User not found"}), 401
            if payload.get("pwc", 0) < row["pw_changed_at"]:
                return jsonify({"error": "Token invalidated by password change"}), 401
        finally:
            conn.close()

        request.admin_user = payload
        return f(*args, **kwargs)
    return decorated


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    ip = request.remote_addr or "unknown"
    if _check_rate_limit(ip):
        return jsonify({"error": "Too many attempts. Try again in a few minutes."}), 429

    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, pw_changed_at FROM admin_users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row or not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            _record_attempt(ip)
            return jsonify({"error": "Invalid credentials"}), 401

        token = _create_admin_token(row["id"], row["username"], row["pw_changed_at"])
        return jsonify({"token": token, "username": row["username"]})
    finally:
        conn.close()


@app.route("/api/admin/me", methods=["GET"])
@admin_required
def admin_me():
    return jsonify({"username": request.admin_user["username"]})


@app.route("/api/admin/change-password", methods=["POST"])
@admin_required
def admin_change_password():
    body = request.get_json(silent=True) or {}
    current_pw = body.get("current_password", "")
    new_pw = body.get("new_password", "")

    if not current_pw or not new_pw:
        return jsonify({"error": "Both current and new password required"}), 400
    if len(new_pw) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    conn = get_db()
    try:
        user_id = int(request.admin_user["sub"])
        row = conn.execute(
            "SELECT password_hash FROM admin_users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row or not bcrypt.checkpw(current_pw.encode(), row["password_hash"].encode()):
            return jsonify({"error": "Current password is incorrect"}), 401

        new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        pw_changed_at = int(datetime.now(timezone.utc).timestamp())
        conn.execute(
            "UPDATE admin_users SET password_hash = ?, pw_changed_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_hash, pw_changed_at, user_id),
        )
        conn.commit()
        # Return a fresh token so the user stays logged in
        new_token = _create_admin_token(user_id, request.admin_user["username"], pw_changed_at)
        return jsonify({"message": "Password changed successfully", "token": new_token})
    finally:
        conn.close()


# --------------- Admin: Voices CRUD ---------------

@app.route("/api/admin/voices", methods=["GET"])
@admin_required
def admin_list_voices():
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, name, voice_id, created_at FROM admin_voices ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/voices", methods=["POST"])
@admin_required
def admin_add_voice():
    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()[:100]
    voice_id = body.get("voice_id", "").strip()[:100]
    if not name or not voice_id:
        return jsonify({"error": "name and voice_id required"}), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO admin_voices (name, voice_id) VALUES (?, ?)", (name, voice_id))
        conn.commit()
        row = conn.execute("SELECT id, name, voice_id, created_at FROM admin_voices WHERE rowid = last_insert_rowid()").fetchone()
        return jsonify(dict(row)), 201
    finally:
        conn.close()


@app.route("/api/admin/voices/<int:voice_id>", methods=["DELETE"])
@admin_required
def admin_delete_voice(voice_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM admin_voices WHERE id = ?", (voice_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Voice not found"}), 404
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


# --------------- Admin: Preferences ---------------

@app.route("/api/admin/preferences", methods=["GET"])
@admin_required
def admin_get_preferences():
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM admin_preferences").fetchall()
        prefs = {r["key"]: r["value"] for r in rows}
        return jsonify(prefs)
    finally:
        conn.close()


@app.route("/api/admin/preferences", methods=["PUT"])
@admin_required
def admin_save_preferences():
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        for k, v in body.items():
            conn.execute(
                "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (str(k), str(v)),
            )
        conn.commit()
        return jsonify({"message": "Saved"})
    finally:
        conn.close()


# --------------- Admin: Reciters proxy (Quran.com) ---------------

_reciters_cache: dict | None = None
_reciters_cache_time: float = 0


@app.route("/api/admin/reciters", methods=["GET"])
@admin_required
def admin_reciters():
    global _reciters_cache, _reciters_cache_time
    now = time.time()
    if _reciters_cache and now - _reciters_cache_time < 3600:
        return jsonify(_reciters_cache)
    try:
        resp = requests.get("https://api.quran.com/api/v4/resources/recitations", timeout=10)
        resp.raise_for_status()
        _reciters_cache = resp.json().get("recitations", [])
        _reciters_cache_time = now
        return jsonify(_reciters_cache)
    except Exception as e:
        if _reciters_cache:
            return jsonify(_reciters_cache)
        return jsonify({"error": f"Failed to fetch reciters: {e}"}), 502


# --------------- Admin: Recitation preview ---------------

# Map reciter_id → audio URL folder (from Quran.com)
_RECITER_FOLDERS: dict[int, str] = {}


def _get_reciter_folder(reciter_id: int) -> str:
    """Get the audio folder for a reciter. Fetch from Quran.com API if not cached."""
    if reciter_id in _RECITER_FOLDERS:
        return _RECITER_FOLDERS[reciter_id]
    try:
        resp = requests.get(
            f"https://api.quran.com/api/v4/recitations/{reciter_id}/by_ayah/1:1",
            timeout=10,
        )
        resp.raise_for_status()
        audio_files = resp.json().get("audio_files", [])
        if audio_files:
            url = audio_files[0]["url"]  # e.g. "Alafasy/mp3/001001.mp3"
            # Extract folder: everything before the last "/"
            folder = url.rsplit("/", 1)[0]
            _RECITER_FOLDERS[reciter_id] = folder
            return folder
    except Exception:
        pass
    # Fallback for Mishari (id=7)
    return "Alafasy/mp3"


@app.route("/api/admin/recitation-preview", methods=["POST"])
@admin_required
def admin_recitation_preview():
    body = request.get_json(silent=True) or {}
    reciter_id = body.get("reciter_id", 7)
    from_s = body.get("from_surah", 1)
    from_a = body.get("from_ayah", 1)
    to_s = body.get("to_surah", from_s)
    to_a = body.get("to_ayah", from_a)

    # Validate
    if not (1 <= from_s <= 114 and 1 <= to_s <= 114):
        return jsonify({"error": "Invalid surah"}), 400

    folder = _get_reciter_folder(reciter_id)
    audio_base = "https://verses.quran.com"

    conn = get_db()
    try:
        verses = []
        # Build list of (surah, ayah) in range
        if from_s == to_s:
            surah_ayahs = [(from_s, a) for a in range(from_a, to_a + 1)]
        else:
            # Get verse counts for surahs in range
            surah_ayahs = []
            for s in range(from_s, to_s + 1):
                row = conn.execute(
                    "SELECT MAX(verse) as max_a FROM verses WHERE chapter = ?", (s,)
                ).fetchone()
                max_a = row["max_a"] if row else 0
                start = from_a if s == from_s else 1
                end = to_a if s == to_s else max_a
                for a in range(start, end + 1):
                    surah_ayahs.append((s, a))

        # Limit to 30 verses
        if len(surah_ayahs) > 30:
            return jsonify({"error": "Maximum 30 verses per preview"}), 400

        for s, a in surah_ayahs:
            row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (s, a)
            ).fetchone()
            arabic = _strip_bismillah(row["text_uthmani"], s, a) if row else ""

            # Get translation (AI preferred, conventional fallback with HTML stripped)
            trans_row = conn.execute(
                "SELECT translation_text FROM ai_translations WHERE chapter = ? AND verse = ?", (s, a)
            ).fetchone()
            if trans_row:
                translation = trans_row["translation_text"]
            else:
                conv_row = conn.execute(
                    "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?", (s, a)
                ).fetchone()
                raw = conv_row["text_en"] if conv_row else ""
                # Strip HTML tags and decode entities from conventional translations
                translation = html.unescape(re.sub(r"<[^>]+>", "", raw))

            audio_url = f"{audio_base}/{folder}/{s:03d}{a:03d}.mp3"

            verses.append({
                "surah": s,
                "ayah": a,
                "surah_name": _surah_name(s),
                "arabic_text": arabic,
                "translation": translation,
                "audio_url": audio_url,
            })

        return jsonify({"verses": verses})
    finally:
        conn.close()


# --------------- Admin: TTS via ElevenLabs (with caching) ---------------

_TTS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "tts_cache")
os.makedirs(_TTS_CACHE_DIR, exist_ok=True)

_RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "data", "resources")
os.makedirs(_RESOURCES_DIR, exist_ok=True)

_GENERATED_VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "data", "generated_videos")
os.makedirs(_GENERATED_VIDEOS_DIR, exist_ok=True)

_FFMPEG = "ffmpeg"
_FFPROBE = "ffprobe"

# Arabic font for video text overlays (Scheherazade New renders hamzat al-wasl correctly)
_ARABIC_FONT = os.path.join(os.path.dirname(__file__), "data", "fonts", "ScheherazadeNew-Regular.ttf")
if not os.path.isfile(_ARABIC_FONT):
    # Fallback chain: Amiri -> macOS GeezaPro
    _alt = os.path.join(os.path.dirname(__file__), "data", "fonts", "Amiri-Regular.ttf")
    _ARABIC_FONT = _alt if os.path.isfile(_alt) else "/System/Library/Fonts/GeezaPro.ttc"
_LATIN_FONT = "/System/Library/Fonts/Helvetica.ttc"
if not os.path.isfile(_LATIN_FONT):
    # Linux / Docker fallback
    for _lf in [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]:
        if os.path.isfile(_lf):
            _LATIN_FONT = _lf
            break


def _ensure_tts_cache_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_tts_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                voice_id TEXT NOT NULL,
                voice_name TEXT NOT NULL DEFAULT '',
                text_hash TEXT NOT NULL,
                translation_text TEXT NOT NULL,
                filename TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chapter, verse, voice_id)
            )
        """)
        conn.commit()
    finally:
        conn.close()

_ensure_tts_cache_table()


def _tts_hash(text: str, voice_id: str) -> str:
    return hashlib.sha256(f"{voice_id}:{text}".encode()).hexdigest()[:16]


@app.route("/api/admin/tts", methods=["POST"])
@admin_required
def admin_tts():
    """Generate speech from text using ElevenLabs, cache the result, return MP3."""
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    voice_id = body.get("voice_id", "").strip()
    chapter = body.get("chapter", 0)
    verse_num = body.get("verse", 0)

    if not text or not voice_id:
        return jsonify({"error": "text and voice_id required"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text too long (max 2000 chars)"}), 400
    if not isinstance(chapter, int) or not isinstance(verse_num, int) or chapter < 1 or verse_num < 1:
        return jsonify({"error": "Valid chapter and verse required"}), 400

    text_hash = _tts_hash(text, voice_id)

    # Check cache first
    old_filename = None
    conn = get_db()
    try:
        cached = conn.execute(
            "SELECT filename, text_hash FROM admin_tts_cache WHERE chapter = ? AND verse = ? AND voice_id = ?",
            (chapter, verse_num, voice_id),
        ).fetchone()
        if cached:
            if cached["text_hash"] == text_hash:
                cached_path = os.path.join(_TTS_CACHE_DIR, cached["filename"])
                if os.path.isfile(cached_path):
                    return send_from_directory(_TTS_CACHE_DIR, cached["filename"], mimetype="audio/mpeg")
            else:
                # Text changed — remember old file for cleanup
                old_filename = cached["filename"]
    finally:
        conn.close()

    # Get ElevenLabs API key from preferences
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'"
        ).fetchone()
        if not row or not row["value"]:
            return jsonify({"error": "ElevenLabs API key not configured. Add it in Settings."}), 400
        api_key = row["value"]
    finally:
        conn.close()

    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
            timeout=30,
        )
        if resp.status_code != 200:
            error_msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            return jsonify({"error": f"ElevenLabs error: {error_msg}"}), 502

        # Save to disk
        filename = f"{chapter:03d}{verse_num:03d}_{text_hash}.mp3"
        filepath = os.path.join(_TTS_CACHE_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)

        # Delete old cached file if text changed
        if old_filename and old_filename != filename:
            old_path = os.path.join(_TTS_CACHE_DIR, old_filename)
            if os.path.isfile(old_path):
                os.remove(old_path)

        # Look up the voice name for display
        voice_name = ""
        conn = get_db()
        try:
            vrow = conn.execute(
                "SELECT name FROM admin_voices WHERE voice_id = ?", (voice_id,)
            ).fetchone()
            if vrow:
                voice_name = vrow["name"]
        finally:
            conn.close()

        # Upsert cache record
        conn = get_db()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO admin_tts_cache
                   (chapter, verse, voice_id, voice_name, text_hash, translation_text, filename, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (chapter, verse_num, voice_id, voice_name, text_hash, text, filename),
            )
            conn.commit()
        finally:
            conn.close()

        return Response(
            resp.content,
            mimetype="audio/mpeg",
            headers={"Content-Disposition": "inline"},
        )
    except requests.Timeout:
        return jsonify({"error": "ElevenLabs request timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"TTS failed: {e}"}), 500


@app.route("/api/admin/tts-cache", methods=["GET"])
@admin_required
def admin_tts_cache_list():
    """List all cached TTS audio entries."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT id, chapter, verse, voice_id, voice_name, translation_text, filename, created_at
               FROM admin_tts_cache ORDER BY chapter, verse"""
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["surah_name"] = _surah_name(r["chapter"])
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/tts-cache/<int:cache_id>", methods=["DELETE"])
@admin_required
def admin_tts_cache_delete(cache_id):
    """Delete a cached TTS entry and its file."""
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_tts_cache WHERE id = ?", (cache_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        # Delete file
        filepath = os.path.join(_TTS_CACHE_DIR, row["filename"])
        if os.path.isfile(filepath):
            os.remove(filepath)
        conn.execute("DELETE FROM admin_tts_cache WHERE id = ?", (cache_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/tts-cache/<int:cache_id>/audio", methods=["GET"])
@admin_required
def admin_tts_cache_audio(cache_id):
    """Serve a cached TTS audio file."""
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_tts_cache WHERE id = ?", (cache_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        filepath = os.path.join(_TTS_CACHE_DIR, row["filename"])
        if not os.path.isfile(filepath):
            return jsonify({"error": "Audio file missing"}), 404
        return send_from_directory(_TTS_CACHE_DIR, row["filename"], mimetype="audio/mpeg")
    finally:
        conn.close()


# --------------- Admin: Resources (background videos) ---------------

def _ensure_resource_tables():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_generated_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                format TEXT NOT NULL,
                resource_id INTEGER REFERENCES admin_resources(id),
                reciter_id INTEGER NOT NULL,
                verse_data TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress TEXT DEFAULT '',
                filename TEXT,
                file_size INTEGER,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        conn.commit()
        # On startup: reset stuck jobs
        conn.execute(
            "UPDATE admin_generated_videos SET status='failed', error_message='Server restarted' "
            "WHERE status IN ('pending','processing')"
        )
        conn.commit()
    finally:
        conn.close()

_ensure_resource_tables()


def _probe_video(filepath):
    """Extract duration, width, height from a video file using ffprobe."""
    result = subprocess.run(
        [_FFPROBE, "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", filepath],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None, None, None
    try:
        info = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None, None, None
    video_stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), None
    )
    duration = float(info.get("format", {}).get("duration", 0)) or None
    width = int(video_stream.get("width")) if video_stream and video_stream.get("width") else None
    height = int(video_stream.get("height")) if video_stream and video_stream.get("height") else None
    return duration, width, height


_ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".webm"}


@app.route("/api/admin/resources", methods=["POST"])
@admin_required
def admin_upload_resource():
    """Upload a background video file."""
    file = request.files.get("video")
    if not file or not file.filename:
        return jsonify({"error": "No video file provided"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in _ALLOWED_VIDEO_EXTS:
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(_ALLOWED_VIDEO_EXTS)}"}), 400

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(_RESOURCES_DIR, filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)
    try:
        duration, width, height = _probe_video(filepath)
    except Exception:
        duration, width, height = None, None, None

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO admin_resources (original_name, filename, file_size, duration_seconds, width, height)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file.filename, filename, file_size, duration, width, height),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM admin_resources WHERE rowid = last_insert_rowid()"
        ).fetchone()
        return jsonify(dict(row)), 201
    finally:
        conn.close()


@app.route("/api/admin/resources", methods=["GET"])
@admin_required
def admin_list_resources():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM admin_resources ORDER BY created_at DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/resources/<int:resource_id>", methods=["DELETE"])
@admin_required
def admin_delete_resource(resource_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        # Delete file and thumbnail
        filepath = os.path.join(_RESOURCES_DIR, row["filename"])
        if os.path.isfile(filepath):
            os.remove(filepath)
        thumb = filepath + ".thumb.jpg"
        if os.path.isfile(thumb):
            os.remove(thumb)
        conn.execute("DELETE FROM admin_resources WHERE id = ?", (resource_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/resources/<int:resource_id>/thumbnail", methods=["GET"])
@admin_required
def admin_resource_thumbnail(resource_id):
    """Generate and serve a thumbnail for a resource video."""
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        filepath = os.path.join(_RESOURCES_DIR, row["filename"])
        if not os.path.isfile(filepath):
            return jsonify({"error": "Resource video file not found on disk"}), 404
        thumb_path = filepath + ".thumb.jpg"
        if not os.path.isfile(thumb_path):
            try:
                result = subprocess.run(
                    [_FFMPEG, "-y", "-i", filepath, "-ss", "1", "-vframes", "1",
                     "-vf", "scale=320:-1", thumb_path],
                    capture_output=True, timeout=15,
                )
                if result.returncode != 0 or not os.path.isfile(thumb_path):
                    return jsonify({"error": "Failed to generate thumbnail"}), 500
            except Exception:
                if os.path.isfile(thumb_path):
                    os.remove(thumb_path)
                return jsonify({"error": "Failed to generate thumbnail"}), 500
        return send_from_directory(_RESOURCES_DIR, row["filename"] + ".thumb.jpg", mimetype="image/jpeg")
    finally:
        conn.close()


# --------------- Admin: Video Generation ---------------

def _get_audio_duration(filepath):
    """Get duration of an audio file in seconds using ffprobe."""
    result = subprocess.run(
        [_FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        capture_output=True, text=True, timeout=15
    )
    return float(result.stdout.strip())


def _escape_drawtext(text):
    """Escape text for ffmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")  # replace with smart quote to avoid escaping issues
    text = text.replace(":", "\\:")
    text = text.replace("%", "%%")
    text = text.replace("\n", "")
    return text


def _prepare_arabic(text):
    """Reshape and reorder Arabic text for ffmpeg drawtext (RTL → visual order)."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _wrap_text(text, max_chars):
    """Wrap text to max_chars per line, splitting on word boundaries."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return lines


def _update_video_status(video_id, status, progress="", error=""):
    conn = get_db()
    try:
        if error:
            conn.execute(
                "UPDATE admin_generated_videos SET status=?, progress=?, error_message=? WHERE id=?",
                (status, progress, error, video_id),
            )
        else:
            conn.execute(
                "UPDATE admin_generated_videos SET status=?, progress=? WHERE id=?",
                (status, progress, video_id),
            )
        conn.commit()
    finally:
        conn.close()


def _generate_video_task(video_id):
    """Background task: combine background video + recitation + TTS into final video."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM admin_generated_videos WHERE id = ?", (video_id,)).fetchone()
        if not row:
            return
        row = dict(row)
    finally:
        conn.close()

    _update_video_status(video_id, "processing", "Preparing...")

    verse_data = json.loads(row["verse_data"])
    fmt = row["format"]
    target_w, target_h = (1080, 1920) if fmt == "short" else (1920, 1080)

    conn = get_db()
    try:
        resource_row = conn.execute(
            "SELECT * FROM admin_resources WHERE id = ?", (row["resource_id"],)
        ).fetchone()
    finally:
        conn.close()

    if not resource_row:
        _update_video_status(video_id, "failed", error="Background video not found")
        return

    bg_path = os.path.join(_RESOURCES_DIR, resource_row["filename"])
    if not os.path.isfile(bg_path):
        _update_video_status(video_id, "failed", error="Background video file missing")
        return

    tmpdir = tempfile.mkdtemp(prefix="vidgen_")
    try:
        # Step 1: Download recitation audio and collect TTS files
        recit_files = []
        tts_files = []
        for i, v in enumerate(verse_data):
            _update_video_status(video_id, "processing",
                f"Downloading audio {i + 1}/{len(verse_data)}...")

            # Download recitation from Quran.com
            recit_path = os.path.join(tmpdir, f"recit_{i:03d}.mp3")
            try:
                resp = requests.get(v["audio_url"], timeout=30)
                resp.raise_for_status()
                with open(recit_path, "wb") as f:
                    f.write(resp.content)
            except Exception as e:
                _update_video_status(video_id, "failed",
                    error=f"Failed to download recitation for {v['verse_ref']}: {e}")
                return

            # Copy TTS from cache
            tts_src = os.path.join(_TTS_CACHE_DIR, v["tts_filename"])
            tts_path = os.path.join(tmpdir, f"tts_{i:03d}.mp3")
            if os.path.isfile(tts_src):
                shutil.copy2(tts_src, tts_path)
            else:
                _update_video_status(video_id, "failed",
                    error=f"TTS cache file missing for {v['verse_ref']}")
                return

            recit_files.append(recit_path)
            tts_files.append(tts_path)

        # Step 2: Get durations and build timeline
        # Layout: INTERLEAVED — recite verse → TTS voice → next verse → TTS voice
        _update_video_status(video_id, "processing", "Analyzing audio durations...")

        recit_durs = [_get_audio_duration(f) for f in recit_files]
        tts_durs = [_get_audio_duration(f) for f in tts_files]

        # Build interleaved timeline
        timeline = []
        current_time = 0.0
        for i in range(len(verse_data)):
            # Recitation phase: show Arabic text + verse ref
            timeline.append({
                "phase": "recitation",
                "start": current_time,
                "dur": recit_durs[i],
                "arabic": verse_data[i]["arabic_text"],
                "translation": verse_data[i]["translation"],
                "ref": verse_data[i]["verse_ref"],
            })
            current_time += recit_durs[i]
            # TTS phase: show translation text
            timeline.append({
                "phase": "tts",
                "start": current_time,
                "dur": tts_durs[i],
                "arabic": verse_data[i]["arabic_text"],
                "translation": verse_data[i]["translation"],
                "ref": verse_data[i]["verse_ref"],
            })
            current_time += tts_durs[i]

        total_duration = current_time

        # Step 3: Concatenate audio — interleaved: recite, tts, recite, tts
        _update_video_status(video_id, "processing", "Building audio track...")
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for i in range(len(verse_data)):
                f.write(f"file '{recit_files[i]}'\n")
                f.write(f"file '{tts_files[i]}'\n")

        combined_audio = os.path.join(tmpdir, "combined.mp3")
        subprocess.run(
            [_FFMPEG, "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", combined_audio],
            capture_output=True, timeout=120,
        )

        # Step 4: Build ASS subtitle file for text overlays
        # Using libass for proper Arabic rendering (RTL, ligatures, diacritics)
        _update_video_status(video_id, "processing", "Rendering video...")

        # Font sizes
        arabic_fontsize = 80 if fmt == "short" else 68
        trans_fontsize = 44 if fmt == "short" else 40
        ref_fontsize = 40 if fmt == "short" else 36

        # ASS colour format: &HAABBGGRR
        # Black text: &H00000000
        # Box background: semi-transparent white &H30FFFFFF
        # OutlineColour matches BackColour so outline = invisible padding around text
        box_colour = "&H30FFFFFF"
        text_colour = "&H00000000"
        fonts_dir = os.path.join(os.path.dirname(__file__), "data", "fonts")
        ass_path = os.path.join(tmpdir, "subs.ass")
        with open(ass_path, "w", encoding="utf-8") as af:
            af.write("[Script Info]\n")
            af.write("ScriptType: v4.00+\n")
            af.write(f"PlayResX: {target_w}\n")
            af.write(f"PlayResY: {target_h}\n\n")

            af.write("[V4+ Styles]\n")
            af.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # BorderStyle=3: Outline becomes box padding, OutlineColour=box colour so padding is invisible
            # Ref: top-center (Alignment=8), bold
            ref_margin_v = 100 if fmt == "short" else 60
            af.write(f"Style: Ref,Liberation Sans,{ref_fontsize},{text_colour},&H000000FF,{box_colour},{box_colour},1,0,0,0,100,100,0,0,3,14,0,8,40,40,{ref_margin_v},0\n")
            # Arabic: center (Alignment=5) — Scheherazade New for proper hamzat al-wasl
            af.write(f"Style: Arabic,Scheherazade New,{arabic_fontsize},{text_colour},&H000000FF,{box_colour},{box_colour},0,0,0,0,100,100,0,0,3,16,0,5,60,60,40,0\n")
            # Translation: below center (Alignment=2, bottom area)
            trans_margin_v = 120 if fmt == "short" else 80
            af.write(f"Style: Trans,Liberation Sans,{trans_fontsize},{text_colour},&H000000FF,{box_colour},{box_colour},0,0,0,0,100,100,0,0,3,14,0,2,60,60,{trans_margin_v},0\n")

            af.write("\n[Events]\n")
            af.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            def _ass_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = seconds % 60
                return f"{h}:{m:02d}:{s:05.2f}"

            def _ass_escape(text):
                return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            # Interleaved: recitation shows ref + Arabic, TTS shows translation
            for t in timeline:
                start = _ass_time(t["start"])
                end = _ass_time(t["start"] + t["dur"])
                ref = _ass_escape(t["ref"])
                arabic = _ass_escape(t["arabic"])
                translation = _ass_escape(t["translation"])

                if t["phase"] == "recitation":
                    # During recitation: show verse ref + Arabic text
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Arabic,,0,0,0,,{arabic}\n")
                else:
                    # During TTS: show verse ref + translation text
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,{translation}\n")

        # Step 5: Final render using ASS subtitles
        output_filename = f"video_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(_GENERATED_VIDEOS_DIR, output_filename)

        # Video filter: scale/crop background, then overlay ASS subtitles
        vf = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},"
            f"ass={ass_path}:fontsdir={fonts_dir}"
        )

        render_timeout = max(600, int(total_duration * 10))
        cmd = [
            _FFMPEG, "-y",
            "-stream_loop", "-1",
            "-i", bg_path,
            "-i", combined_audio,
            "-vf", vf,
            "-t", f"{total_duration:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-movflags", "+faststart",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=render_timeout)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")[:500] if result.stderr else "Unknown error"
            _update_video_status(video_id, "failed", error=f"ffmpeg error: {stderr}")
            return

        file_size = os.path.getsize(output_path)
        conn2 = get_db()
        try:
            conn2.execute(
                """UPDATE admin_generated_videos
                   SET status='complete', filename=?, file_size=?,
                       completed_at=CURRENT_TIMESTAMP, progress='Done'
                   WHERE id = ?""",
                (output_filename, file_size, video_id),
            )
            conn2.commit()
        finally:
            conn2.close()

    except subprocess.TimeoutExpired:
        _update_video_status(video_id, "failed", error="Video generation timed out")
    except Exception as e:
        _update_video_status(video_id, "failed", error=str(e)[:500])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.route("/api/admin/generate-video", methods=["POST"])
@admin_required
def admin_generate_video():
    """Start video generation in a background thread."""
    body = request.get_json(silent=True) or {}
    title = body.get("title", "").strip()[:200]
    fmt = body.get("format", "")
    resource_id = body.get("resource_id")
    reciter_id = body.get("reciter_id")
    verses = body.get("verses", [])

    if not title:
        return jsonify({"error": "Title required"}), 400
    if fmt not in ("short", "regular"):
        return jsonify({"error": "Format must be 'short' or 'regular'"}), 400
    if not isinstance(resource_id, int) or resource_id <= 0:
        return jsonify({"error": "Valid resource_id required"}), 400
    if not isinstance(reciter_id, int) or reciter_id <= 0:
        return jsonify({"error": "Valid reciter_id required"}), 400
    if not verses or not isinstance(verses, list):
        return jsonify({"error": "At least one verse required"}), 400
    if not all(isinstance(v, dict) for v in verses):
        return jsonify({"error": "Each verse must be an object"}), 400

    # Check concurrent generation limit
    conn = get_db()
    try:
        active = conn.execute(
            "SELECT COUNT(*) FROM admin_generated_videos WHERE status IN ('pending','processing')"
        ).fetchone()[0]
        if active >= 2:
            return jsonify({"error": "Too many videos generating. Please wait."}), 429

        # Validate resource exists
        res_row = conn.execute("SELECT id FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not res_row:
            return jsonify({"error": "Resource not found"}), 404

        # Build verse_data from TTS cache entries
        folder = _get_reciter_folder(reciter_id)
        audio_base = "https://verses.quran.com"
        verse_data = []
        for v in verses:
            cache_id = v.get("tts_cache_id")
            cache_row = conn.execute(
                "SELECT * FROM admin_tts_cache WHERE id = ?", (cache_id,)
            ).fetchone()
            if not cache_row:
                return jsonify({"error": f"TTS cache entry {cache_id} not found"}), 404

            ch, vs = cache_row["chapter"], cache_row["verse"]
            # Get Arabic text
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, vs)
            ).fetchone()
            arabic = _strip_bismillah(verse_row["text_uthmani"], ch, vs) if verse_row else ""

            verse_data.append({
                "chapter": ch,
                "verse": vs,
                "verse_ref": f"{_surah_name(ch)} {ch}:{vs}",
                "arabic_text": arabic,
                "translation": cache_row["translation_text"],
                "tts_filename": cache_row["filename"],
                "audio_url": f"{audio_base}/{folder}/{ch:03d}{vs:03d}.mp3",
            })

        conn.execute(
            """INSERT INTO admin_generated_videos (title, format, resource_id, reciter_id, verse_data, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (title, fmt, resource_id, reciter_id, json.dumps(verse_data)),
        )
        conn.commit()
        video_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

    # Start background thread
    threading.Thread(target=_generate_video_task, args=(video_id,), daemon=True).start()
    return jsonify({"id": video_id, "status": "pending"}), 201


@app.route("/api/admin/generated-videos", methods=["GET"])
@admin_required
def admin_list_generated_videos():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM admin_generated_videos ORDER BY created_at DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/generated-videos/<int:vid_id>", methods=["DELETE"])
@admin_required
def admin_delete_generated_video(vid_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_generated_videos WHERE id = ?", (vid_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        if row["filename"]:
            filepath = os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])
            if os.path.isfile(filepath):
                os.remove(filepath)
        conn.execute("DELETE FROM admin_generated_videos WHERE id = ?", (vid_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/generated-videos/<int:vid_id>/download", methods=["GET"])
@admin_required
def admin_download_generated_video(vid_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT filename, title FROM admin_generated_videos WHERE id = ? AND status = 'complete'",
            (vid_id,),
        ).fetchone()
        if not row or not row["filename"]:
            return jsonify({"error": "Video not found or not ready"}), 404
        if not os.path.isfile(os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])):
            return jsonify({"error": "Video file missing from disk"}), 404
        return send_from_directory(
            _GENERATED_VIDEOS_DIR, row["filename"],
            mimetype="video/mp4", as_attachment=True,
            download_name=f"{row['title']}.mp4",
        )
    finally:
        conn.close()


# --------------- Legacy redirect ---------------

@app.before_request
def _redirect_legacy_query_params():
    """301 redirect /?s=X&a=Y to /verse/X:Y in production."""
    if request.path == "/" and request.args.get("s") and request.args.get("a"):
        s = request.args.get("s")
        a = request.args.get("a")
        return redirect(f"/verse/{s}:{a}", code=301)


# --------------- Noscript content for LLM crawlers ---------------

def _build_noscript_content(path: str) -> str:
    """Generate static HTML content for crawlers that don't execute JavaScript.

    This ensures LLM crawlers (GPTBot, Claude-Web, etc.) see meaningful
    content in the page body, not just an empty <div id="root"></div>.
    """
    parts = []

    # Verse page: /verse/X:Y
    m = re.match(r'^/verse/(\d+):(\d+)$', path)
    if m:
        surah, ayah = int(m.group(1)), int(m.group(2))
        conn = get_db()
        try:
            vrow = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (surah, ayah),
            ).fetchone()
            if vrow:
                text = _strip_bismillah(vrow["text_uthmani"], surah, ayah)
                trans = _best_translation(conn, surah, ayah)
                name = _surah_name(surah)
                parts.append(f'<h1>Surah {html.escape(name)} ({surah}:{ayah})</h1>')
                parts.append(f'<p dir="rtl" lang="ar">{html.escape(text)}</p>')
                parts.append(f'<p>{html.escape(trans)}</p>')

                # Root summary
                morph = conn.execute(
                    "SELECT DISTINCT root_buckwalter FROM morphology "
                    "WHERE chapter = ? AND verse = ? AND root_buckwalter IS NOT NULL AND root_buckwalter != ''",
                    (surah, ayah),
                ).fetchall()
                if morph:
                    root_links = []
                    for r in morph:
                        rbw = r["root_buckwalter"]
                        ra = _root_arabic_map.get(rbw, "")
                        root_links.append(f'<a href="/root/{quote(rbw)}">{html.escape(ra)} ({html.escape(rbw)})</a>')
                    parts.append(f'<p>Roots in this verse: {", ".join(root_links)}</p>')
        finally:
            conn.close()

    # Root page: /root/X
    m = re.match(r'^/root/(.+)$', path)
    if m:
        root_bw = m.group(1)
        root_arabic = _root_arabic_map.get(root_bw, "")
        if root_arabic:
            freq = len(_root_inv.get(root_bw, set()))
            parts.append(f'<h1>Root {html.escape(root_arabic)} ({html.escape(root_bw)})</h1>')
            parts.append(f'<p>This root appears in {freq} verses across the Quran.</p>')
            conn = get_db()
            try:
                lemmas = conn.execute(
                    "SELECT DISTINCT lemma_arabic FROM morphology "
                    "WHERE root_buckwalter = ? AND lemma_arabic IS NOT NULL AND lemma_arabic != '' LIMIT 10",
                    (root_bw,),
                ).fetchall()
                if lemmas:
                    lemma_list = ", ".join(html.escape(r["lemma_arabic"]) for r in lemmas)
                    parts.append(f'<p>Derived forms: {lemma_list}</p>')
            finally:
                conn.close()

    # Learning hub: /learning
    if path == '/learning' or path == '/learning/':
        parts.append('<h1>Learn Quranic Arabic Through Root Words</h1>')
        parts.append('<p>Master 118 essential root words across 18 thematic units. '
                     'Each root unlocks a family of words used throughout the Quran, '
                     'building both vocabulary and deeper understanding.</p>')
        parts.append('<p>Features: visual mnemonics, spaced repetition, verse-by-verse discovery, '
                     'and fill-in-the-blank vocabulary testing.</p>')

    # Learning root page: /learning/root/X
    m = re.match(r'^/learning/root/(.+?)/?$', path)
    if m:
        root_bw = m.group(1)
        root_arabic = _root_arabic_map.get(root_bw, "")
        if root_arabic:
            parts.append(f'<h1>Learn Root {html.escape(root_arabic)} ({html.escape(root_bw)})</h1>')
            conn = get_db()
            try:
                cur = conn.execute(
                    "SELECT root_story, unit_theme FROM learning_curriculum WHERE root_buckwalter = ?",
                    (root_bw,),
                ).fetchone()
                if cur:
                    parts.append(f'<p>Theme: {html.escape(cur["unit_theme"])}</p>')
                    parts.append(f'<p>{html.escape(cur["root_story"][:300])}</p>')
            finally:
                conn.close()

    # Home page
    if path in ('', '/'):
        parts.append('<h1>al-nuqta</h1>')
        parts.append('<p>Explore the Quran verse by verse with root word analysis, '
                     'morphology, Semitic etymology, cross-references, and AI-powered translations.</p>')
        parts.append('<p>Search by verse reference (e.g., 2:255) or explore root words '
                     '(e.g., xlq, khalaq, create).</p>')
        parts.append(f'<p><a href="/learning">Learn Quranic Arabic</a> through 118 root words '
                     'across 18 thematic units.</p>')
        parts.append(f'<p>Free public API available at <a href="{SITE_URL}/api/v1/">{SITE_URL}/api/v1/</a>.</p>')

    if not parts:
        return ""

    content = "\n".join(parts)
    return f'<noscript><div style="max-width:800px;margin:0 auto;padding:20px">{content}</div></noscript>'


# --------------- SPA catch-all (production only) ---------------

_index_html_cache: str | None = None

if SERVE_STATIC:
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        """Serve static files or fall back to index.html with injected SEO meta."""
        global _index_html_cache

        # If the file exists in static/, serve it directly
        file_path = os.path.join(STATIC_DIR, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(STATIC_DIR, path)

        # Read and cache index.html template
        if _index_html_cache is None:
            with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
                _index_html_cache = f.read()

        # Inject SEO meta tags
        req_path = "/" + path if path else "/"

        # Unknown paths: return a minimal 404 with noindex — do NOT serve
        # the full SPA, which search engines may treat as a soft 404.
        if not _is_known_spa_path(req_path):
            not_found_html = (
                '<!DOCTYPE html><html><head>'
                '<meta charset="utf-8">'
                '<meta name="robots" content="noindex, nofollow">'
                '<title>Page Not Found | al-nuqta</title>'
                '</head><body>'
                '<h1>404 — Page Not Found</h1>'
                f'<p>Go to <a href="/">al-nuqta</a></p>'
                '</body></html>'
            )
            return Response(not_found_html, mimetype="text/html", status=404)

        meta = _get_seo_meta(req_path)
        meta_tags = _build_meta_tags(meta)

        # Generate noscript content for LLM/bot crawlers that don't execute JS
        noscript_html = _build_noscript_content(req_path)

        html_doc = _index_html_cache
        html_doc = html_doc.replace("<!-- SEO_META_PLACEHOLDER -->", meta_tags)
        html_doc = html_doc.replace(
            "<title>al-nuqta</title>",
            f"<title>{html.escape(meta['title'])}</title>",
        )
        if noscript_html:
            html_doc = html_doc.replace(
                '<div id="root"></div>',
                f'<div id="root"></div>\n{noscript_html}',
            )

        return Response(html_doc, mimetype="text/html", status=200)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
