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
import sys
import tempfile
import threading
import time
import unicodedata
import uuid
from collections import OrderedDict, defaultdict
from urllib.parse import quote

import arabic_reshaper
import secrets
from bidi.algorithm import get_display
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
import numpy as np
import requests
from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

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
# Trust the X-Forwarded-* headers from our nginx reverse proxy so
# `request.remote_addr` is the real client IP, not nginx's. Critical for
# the analytics tables (admin_ips, page_views) to dedupe correctly.
# x_for=1 means "trust exactly one hop"; if we ever sit behind multiple
# proxies bump it. x_proto/x_host let url_for() generate https URLs in
# prod. Local dev (no proxy) is a no-op — the headers won't be present.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
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


# Verse counts per surah (index 0 unused). Static table — the canonical
# Quran has fixed verse counts so we don't need a DB hit per redirect.
SURAH_VERSE_COUNTS = [
    0, 7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6,
]


def _surah_max_ayah(ch: int) -> int:
    """Highest ayah number in surah `ch`. Returns 0 for invalid surahs."""
    return SURAH_VERSE_COUNTS[ch] if 1 <= ch < len(SURAH_VERSE_COUNTS) else 0


# Arabic surah names — index 0 unused so SURAH_NAMES_ARABIC[1] = الفاتحة
SURAH_NAMES_ARABIC = [
    "", "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة",
    "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان",
    "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر",
    "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية",
    "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن",
    "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق",
    "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة",
    "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج",
    "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين",
    "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل",
    "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس",
]

# Short English meaning of each surah's name. Used by the homepage
# Surah list and reader header. Index 0 unused.
SURAH_MEANINGS = [
    "", "The Opening", "The Cow", "Family of Imran", "The Women", "The Table Spread",
    "The Cattle", "The Heights", "The Spoils of War", "The Repentance", "Jonah",
    "Hud", "Joseph", "The Thunder", "Abraham", "The Rocky Tract",
    "The Bee", "The Night Journey", "The Cave", "Mary", "Ta-Ha",
    "The Prophets", "The Pilgrimage", "The Believers", "The Light", "The Criterion",
    "The Poets", "The Ant", "The Stories", "The Spider", "The Romans",
    "Luqman", "The Prostration", "The Confederates", "Sheba", "The Originator",
    "Ya-Sin", "Those Who Set the Ranks", "Sad", "The Troops", "The Forgiver",
    "Explained in Detail", "The Consultation", "The Gold Adornments", "The Smoke", "The Crouching",
    "The Curved Sandhills", "Muhammad", "The Victory", "The Chambers", "Qaf",
    "The Wind That Scatter", "The Mount", "The Star", "The Moon", "The Most Merciful",
    "The Inevitable", "The Iron", "The Pleading Woman", "The Gathering", "The Examined One",
    "The Ranks", "Friday", "The Hypocrites", "Mutual Disillusion", "The Divorce",
    "The Prohibition", "The Sovereignty", "The Pen", "The Inevitable Reality", "The Ascending Stairways",
    "Noah", "The Jinn", "The Enshrouded One", "The Cloaked One", "The Resurrection",
    "Man", "Those Sent Forth", "The Tidings", "Those Who Pull Out", "He Frowned",
    "The Folding Up", "The Cleaving", "The Defrauding", "The Splitting", "The Constellations",
    "The Night Visitor", "The Most High", "The Overwhelming Calamity", "The Dawn", "The City",
    "The Sun", "The Night", "The Forenoon", "The Relief", "The Fig",
    "The Clinging Substance", "The Power", "The Clear Proof", "The Earthquake", "The Coursers",
    "The Striking Calamity", "Rivalry in Increase", "The Time", "The Slanderer", "The Elephant",
    "Quraysh", "Small Kindnesses", "The Abundance", "The Disbelievers", "The Help",
    "The Palm Fiber", "The Sincerity", "The Daybreak", "Mankind",
]


def _surah_arabic(ch: int) -> str:
    return SURAH_NAMES_ARABIC[ch] if ch < len(SURAH_NAMES_ARABIC) else ""


def _surah_meaning(ch: int) -> str:
    return SURAH_MEANINGS[ch] if ch < len(SURAH_MEANINGS) else ""


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


def _ensure_grammar_notes_tables():
    """Create the grammar notes + centralized glossary tables."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grammar_notes_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_grammar_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                config_id INTEGER NOT NULL REFERENCES grammar_notes_configs(id),
                notes_markdown TEXT NOT NULL,
                referenced_terms TEXT NOT NULL DEFAULT '[]',
                raw_response TEXT,
                full_prompt TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (chapter, verse, config_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_grammar_notes_verse
            ON ai_grammar_notes (chapter, verse)
        """)
        # Centralized glossary of grammar terms. term_english is the canonical
        # form emitted by the LLM inside [[...]] markers in notes_markdown.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grammar_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_english TEXT UNIQUE NOT NULL COLLATE NOCASE,
                term_arabic TEXT,
                plain_explanation TEXT NOT NULL,
                example_sentence TEXT,
                example_translation TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_grammar_notes_tables()


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


def _ensure_translation_bias_reviews_table():
    """Stage-1/Stage-2 translation bias review pipeline storage.

    Rows are created by bias_detect.py (Stage 1). Stage 2 (Claude
    adjudicator) fills in adjudicator_model / decision / etc. Nothing
    touches ai_translations directly — revisions are staged here and
    only applied explicitly from admin UI or a separate apply script.
    """
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS translation_bias_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                ai_translation_config_id INTEGER NOT NULL,
                original_text TEXT NOT NULL,

                -- Stage 1 (detector)
                detector_model TEXT NOT NULL,
                detector_prompt_version TEXT NOT NULL,
                detector_run_at TEXT DEFAULT CURRENT_TIMESTAMP,
                detector_flagged INTEGER NOT NULL DEFAULT 0,
                flags_json TEXT,          -- [{type, span, reason}, ...]
                detector_raw_response TEXT,

                -- Stage 2 (adjudicator, nullable until run)
                adjudicator_model TEXT,
                adjudicator_run_at TEXT,
                decision TEXT,            -- 'revise' | 'keep' | 'defer'
                revised_text TEXT,
                reasoning TEXT,
                confidence REAL,
                adjudicator_raw_response TEXT,

                -- Application lifecycle
                applied INTEGER NOT NULL DEFAULT 0,
                applied_at TEXT,
                reverted_at TEXT,
                reverted_reason TEXT,

                UNIQUE (chapter, verse, detector_model, detector_prompt_version,
                        ai_translation_config_id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tbr_flagged_unadjudicated "
            "ON translation_bias_reviews (detector_flagged, decision) "
            "WHERE detector_flagged = 1 AND decision IS NULL"
        )
        conn.commit()
    finally:
        conn.close()


_ensure_translation_bias_reviews_table()


def _ensure_term_surveys_table():
    """Per-root semantic survey results — the 'ground truth' used by the
    bias detector and adjudicator to decide what the Quran-only canonical
    rendering of a term is. One row per root (keyed by Buckwalter form).
    Populated by term_survey.py (Stage 0)."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS term_surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_buckwalter TEXT NOT NULL UNIQUE,
                root_arabic TEXT,
                occurrence_count INTEGER,
                -- JSON array of {chapter, verse, arabic_word, lemma, translation}
                occurrence_samples TEXT,

                surveyor_model TEXT NOT NULL,
                surveyor_prompt_version TEXT NOT NULL DEFAULT 'v1',
                surveyor_run_at TEXT DEFAULT CURRENT_TIMESTAMP,

                canonical_english TEXT,       -- semantic anchor for the glossary
                reasoning TEXT,               -- semantic thread through all usages
                counter_examples_json TEXT,   -- JSON: [{ref, how_canonical_fits}, ...]
                translation_note TEXT,        -- reader-facing note for public display
                leave_untranslated INTEGER NOT NULL DEFAULT 0,
                -- Verses where conventional English would have to invent (e.g.
                -- "send blessings upon" for 33:56). Translation should use
                -- pure transliteration on these, with the glossary tooltip
                -- carrying the explanation. JSON list:
                --   [{ref, arabic_word, transliteration, reason}, ...]
                hard_cases_json TEXT,
                confidence REAL,
                raw_response TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_term_surveys_table()


def _ensure_proper_noun_candidates_table():
    """Per-occurrence candidates flagged as potentially-mistranslated proper
    nouns (e.g. 'Abu Lahab' kept verbatim when literal Arabic is descriptive).
    Populated by proper_noun_detect.py (Stage 0 + Stage 1) and
    proper_noun_adjudicate.py (Stage 2). Reviewed via the admin UI."""
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proper_noun_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                word_pos INTEGER NOT NULL,

                arabic_word TEXT,
                root_buckwalter TEXT,
                lemma_buckwalter TEXT,
                surface_translation TEXT,
                -- 'compound' (Abu/Ibn/Dhu + X), 'single' (lone capitalized
                -- transliteration), 'phrase' (multi-token name spans)
                candidate_type TEXT,

                -- Stage 0: cheap mechanical evidence
                is_indefinite INTEGER DEFAULT 0,
                root_quran_frequency INTEGER,
                has_compound_marker TEXT,

                -- Stage 1: Ollama cloud (qwen + gptoss)
                qwen_verdict TEXT,
                qwen_confidence REAL,
                qwen_reasoning TEXT,
                gptoss_verdict TEXT,
                gptoss_confidence REAL,
                gptoss_reasoning TEXT,
                stage1_run_at TEXT,

                -- Stage 2: Sonnet adjudication
                sonnet_verdict TEXT,
                sonnet_alternatives_json TEXT,
                sonnet_reasoning TEXT,
                sonnet_supporting_refs_json TEXT,
                stage2_run_at TEXT,

                -- Operator review
                operator_action TEXT,
                operator_translation TEXT,
                operator_notes TEXT,
                reviewed_at TEXT,

                -- Application
                applied_at TEXT,
                applied_to_verses_json TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chapter, verse, word_pos)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pnc_status "
            "ON proper_noun_candidates(operator_action, sonnet_verdict)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pnc_root "
            "ON proper_noun_candidates(root_buckwalter)"
        )
        conn.commit()
    finally:
        conn.close()


_ensure_proper_noun_candidates_table()


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
            # Reader-range Q&A: when the user asks a question while
            # reading a multi-verse window (e.g. /read/3 scrolled to
            # 20–26), the row is anchored to the most-visible verse via
            # (page_type='verse', page_key='3:23'), but `context_range`
            # records the window the LLM saw (e.g. "3:20-26"). NULL on
            # all pre-existing rows and on single-verse asks.
            cols = [r[1] for r in conn.execute("PRAGMA table_info(assistant_conversations)")]
            if "context_range" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN context_range TEXT"
                )
            # Admin moderation columns. `hidden`=1 removes a Q&A from the
            # public per-verse history without deleting it (reversible from
            # the admin "Ask the Quran" section). `edited_at` is stamped
            # when an admin corrects the stored question/answer.
            if "hidden" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN hidden INTEGER DEFAULT 0"
                )
            if "edited_at" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN edited_at TEXT"
                )
            # AI-pre-generated Q&A (pre-populating "Ask the Quran" with
            # insightful, Quran-internal questions). `source` distinguishes
            # user-asked from AI-drafted rows; `review_status` gates AI drafts
            # (pending -> approved/rejected) so nothing AI-authored reaches the
            # public verse until an admin approves it. category = question
            # archetype (grammar/root/cross-ref/...), quality_score and
            # generation_meta (JSON) aid the admin review queue.
            if "source" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN source TEXT DEFAULT 'user'"
                )
            if "review_status" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN review_status TEXT"
                )
            if "category" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN category TEXT"
                )
            if "quality_score" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN quality_score REAL"
                )
            if "generation_meta" not in cols:
                conn.execute(
                    "ALTER TABLE assistant_conversations ADD COLUMN generation_meta TEXT"
                )
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


def _ensure_moving_verse_groups_table():
    """Create the moving_verse_groups table for caching AI-suggested verse groups."""
    for _attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=60)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS moving_verse_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter INTEGER NOT NULL,
                    verse_start INTEGER NOT NULL,
                    verse_end INTEGER NOT NULL,
                    emotional_score REAL NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    translation_snippet TEXT,
                    used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE (chapter, verse_start, verse_end)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mvg_score
                ON moving_verse_groups (emotional_score DESC)
            """)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError:
            time.sleep(3)
    print("WARNING: Could not create moving_verse_groups table (DB locked).")


try:
    _ensure_moving_verse_groups_table()
except Exception as e:
    print(f"WARNING: moving_verse_groups table setup failed: {e}")


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

# Phase B: Voyage multilingual hybrid retrieval. Loads the v2 vector index from
# the local DB (tolerant of a missing table — degrades to v1+lexical). No
# network at import; the dense arm only calls Voyage at query time.
try:
    import search_v2
    search_v2.load_matrices_v2()
except Exception as _sv2_exc:  # never let search v2 break app startup
    print(f"[search_v2] init skipped: {_sv2_exc}")
    search_v2 = None


def _get_embedding_model():
    """Lazy-load the sentence transformer model (thread-safe).

    Returns None instead of blocking when the model is still loading in
    another thread. This lock used to be a plain blocking `with`, and the
    load inside it could touch the network (HuggingFace revision check) with
    no timeout — one stalled load poisoned the lock and every subsequent
    semantic-search request thread blocked on it forever. That is the prime
    suspect for the 2026-07-02 outage where all gunicorn request threads
    wedged. Now: callers time out after 10s and degrade (route returns 503);
    the image also sets HF_HUB_OFFLINE=1 so the load can never phone home.
    """
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    if not _embedding_model_lock.acquire(timeout=10):
        return None  # another thread is mid-load and slow — fail fast
    try:
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(_SEMANTIC_MODEL_NAME)
        return _embedding_model
    finally:
        _embedding_model_lock.release()


def _semantic_search(query: str, limit: int = 10, threshold: float = 0.25):
    """Search verses by semantic similarity to a natural-language query.

    Returns list of (chapter, verse, score, snippet) sorted by score DESC.
    """
    if _embedding_matrix is None or len(_embedding_keys) == 0:
        return []
    model = _get_embedding_model()
    if model is None:
        # Model still loading in another thread — degrade rather than block.
        return []
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


_BISMILLAH_SKELETON = [c for c in _BISMILLAH if not unicodedata.combining(c) and not c.isspace()]


def _strip_bismillah(text, surah, ayah):
    """Strip the Bismillah prefix from verse 1 display text (except 1:1 where it IS the verse).

    Matches by letter skeleton (diacritics ignored) because some surahs carry
    variant pointing on the basmala — e.g. 95:1 and 97:1 write its ba' with a
    shadda — which an exact prefix match misses."""
    if ayah != 1 or surah == 1:
        return text
    if text.startswith(_BISMILLAH):
        return text[len(_BISMILLAH):].strip()
    ti = 0
    for i, ch in enumerate(text):
        if unicodedata.combining(ch) or ch.isspace():
            continue
        if ti < len(_BISMILLAH_SKELETON) and ch == _BISMILLAH_SKELETON[ti]:
            ti += 1
            if ti == len(_BISMILLAH_SKELETON):
                j = i + 1
                while j < len(text) and unicodedata.combining(text[j]):
                    j += 1
                return text[j:].strip()
        else:
            return text
    return text


def _best_translation(conn, surah, ayah):
    """Return AI translation if available (preferring the revised text
    when present), otherwise fall back to the conventional translation."""
    ai = conn.execute(
        "SELECT translation_text, revised_text FROM ai_translations "
        "WHERE chapter = ? AND verse = ? ORDER BY created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if ai:
        return ai["revised_text"] or ai["translation_text"]
    conv = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return conv["text_en"] if conv else ""


def _fetch_word_glosses(conn, surah, ayah, allow_fetch=True):
    """Get word-by-word English translations, fetching from Quran.com API v4 if not cached.

    allow_fetch=False makes this cache-only: callers that loop over many
    verses in one request (e.g. the v1 word detail's other-occurrences list)
    must not fire a chain of sequential external fetches on a request thread.
    """
    rows = conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
        (surah, ayah),
    ).fetchall()

    if rows:
        return {row["word_pos"]: row["translation_en"] for row in rows}

    if not allow_fetch:
        return {}

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
_PROXY_MODEL = "claude-sonnet-4-6"
_MODERATION_MODEL = "claude-haiku-4-5"
_CLAUDE_API_KEY_ENV = os.environ.get("CLAUDE_API_KEY", "")
_CLAUDE_API_KEY = _CLAUDE_API_KEY_ENV  # backward-compat alias for CLI scripts


_claude_key_cache: dict = {"key": None, "ts": 0.0}
_ga_id_cache: dict = {"id": None, "ts": 0.0}


def _get_google_analytics_id() -> str:
    """Read the GA4 Measurement ID from admin_preferences. Cached for 60s
    so we don't hit the DB on every page render. Returns '' if unset."""
    now = time.time()
    if _ga_id_cache["id"] is not None and now - _ga_id_cache["ts"] < 60:
        return _ga_id_cache["id"]
    val = ""
    try:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'google_analytics_id'"
            ).fetchone()
            if row and row["value"]:
                val = (row["value"] or "").strip()
        finally:
            conn.close()
    except Exception:
        pass
    _ga_id_cache["id"] = val
    _ga_id_cache["ts"] = now
    return val


def _build_ga_snippet(ga_id: str) -> str:
    """Standard gtag.js bootstrap. Only emit if ga_id looks like a GA4
    Measurement ID (G-XXXXX) — anything else is silently dropped so a
    typo'd value can't inject random script tags."""
    import re as _re
    if not _re.match(r"^G-[A-Z0-9]{4,20}$", ga_id):
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>'
        '<script>'
        'window.dataLayer = window.dataLayer || [];'
        'function gtag(){dataLayer.push(arguments);}'
        'gtag(\'js\', new Date());'
        f'gtag(\'config\', \'{ga_id}\');'
        '</script>'
    )


def _get_claude_api_key() -> str:
    """Get Claude API key: prefer admin_preferences, fall back to env var.

    Caches the DB lookup for 60 seconds to avoid per-request queries.
    """
    now = time.time()
    if _claude_key_cache["key"] is not None and now - _claude_key_cache["ts"] < 60:
        return _claude_key_cache["key"]
    try:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'claude_api_key'"
            ).fetchone()
            if row and row["value"]:
                _claude_key_cache["key"] = row["value"]
                _claude_key_cache["ts"] = now
                return row["value"]
        finally:
            conn.close()
    except Exception:
        pass
    result = _CLAUDE_API_KEY_ENV
    _claude_key_cache["key"] = result
    _claude_key_cache["ts"] = now
    return result


def _invalidate_claude_key_cache():
    """Clear the cached Claude API key (call after saving preferences)."""
    _claude_key_cache["key"] = None
    _claude_key_cache["ts"] = 0.0


def _moderate_question(question: str) -> dict:
    """Use a fast Claude model to check appropriateness and reword the question.

    Returns {"approved": bool, "reworded": str, "reason": str|None}.
    Falls back to approving the raw question if the API key is missing or the call fails.
    """
    if not _get_claude_api_key():
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
                "x-api-key": _get_claude_api_key(),
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

    if not _get_claude_api_key():
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
                "x-api-key": _get_claude_api_key(),
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
    if not _get_claude_api_key():
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
                    "x-api-key": _get_claude_api_key(),
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
    if not _get_claude_api_key():
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


# At most 2 of the (few) gunicorn request threads may proxy an upstream
# Claude stream at once. Streaming holds a thread for the whole response;
# without a cap, a handful of concurrent (or malicious — session_id is
# client-supplied) asks could occupy every request thread and take the
# site down for everyone.
_assistant_ask_slots = threading.BoundedSemaphore(2)


@app.route("/api/assistant/ask", methods=["POST"])
def proxy_assistant_ask():
    """Stream a Claude response using the server's API key (free tier)."""
    if not _get_claude_api_key():
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
        # Acquire the streaming slot INSIDE the generator so acquire/release
        # are tied to actual execution: a generator that is never iterated
        # (client vanished before the first byte) never acquires, and one
        # that is closed mid-stream still runs the finally. Reject rather
        # than queue when all slots are busy — a queued request would hold a
        # scarce gunicorn thread anyway.
        if not _assistant_ask_slots.acquire(blocking=False):
            yield f"data: {_json.dumps({'type': 'error', 'error': {'message': 'The assistant is answering other questions right now — please retry in a moment.'}})}\n\n"
            return
        resp = None
        # Hard wall-clock budget for the WHOLE stream. requests' timeout is
        # per-socket-read, so a slowly-dripping upstream could otherwise hold
        # this thread indefinitely.
        deadline = time.monotonic() + 180
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": _get_claude_api_key(),
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
                timeout=(10, 30),  # 10s connect, 30s max silence between chunks
            )
            if not resp.ok:
                error_body = resp.text[:200]
                yield f"data: {_json.dumps({'type': 'error', 'error': {'message': f'API error ({resp.status_code}): {error_body}'}})}\n\n"
                return

            for line in resp.iter_lines(decode_unicode=True):
                if time.monotonic() > deadline:
                    yield f"data: {_json.dumps({'type': 'error', 'error': {'message': 'Response took too long and was cut off.'}})}\n\n"
                    return
                if line and line.startswith("data: "):
                    yield line + "\n\n"
        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'error': {'message': str(e)[:200]}})}\n\n"
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass
            _assistant_ask_slots.release()

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

    # context_range: optional "S:V1-V2" string from reader-range asks.
    # Strict validation — anything that doesn't match the expected
    # pattern is silently dropped (NULL persists), since this field
    # only ever feeds a UI pill and never gates behavior.
    cr_raw = data.get("context_range")
    context_range = None
    if isinstance(cr_raw, str) and cr_raw:
        m = re.match(r"^(\d{1,3}):(\d{1,3})-(\d{1,3})$", cr_raw.strip())
        if m:
            s, v1, v2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= s <= 114 and 1 <= v1 <= v2 <= 286:
                context_range = f"{s}:{v1}-{v2}"

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
            # --- Resolve existing row OUTSIDE any transaction (Fix 5) ---
            # The synthesis/moderation Claude calls below take up to 15s
            # each; they used to run INSIDE a BEGIN IMMEDIATE transaction,
            # holding SQLite's write lock across the network for up to 30s
            # per save (a thread-starvation contributor found in the
            # 2026-07-02 outage audit). Now: resolve → network calls with no
            # lock → short write transaction with a re-resolve for atomicity.
            def _resolve_existing(c):
                row = None
                if thread_id:
                    row = c.execute(
                        "SELECT id, question FROM assistant_conversations "
                        "WHERE id = ? AND session_id = ?",
                        (thread_id, data["session_id"]),
                    ).fetchone()
                if not row:
                    # Defense-in-depth: recent row from same session+page (Fix 5)
                    row = c.execute(
                        "SELECT id, question FROM assistant_conversations "
                        "WHERE session_id = ? AND page_type = ? AND page_key = ? "
                        "  AND created_at > datetime('now', '-1 hour') "
                        "ORDER BY id DESC LIMIT 1",
                        (data["session_id"], data["page_type"], data["page_key"]),
                    ).fetchone()
                return row

            existing_row = _resolve_existing(conn)

            saved_question_update = None
            if existing_row:
                # (Fix 6: always synthesize when updating) — network calls
                # happen here, with NO database lock held.
                existing_question = existing_row["question"]
                if all_questions and len(all_questions) > 1:
                    questions_to_merge = all_questions
                else:
                    questions_to_merge = [existing_question, data["question"]]
                synthesized = _synthesize_questions(questions_to_merge)
                synth_mod = _moderate_question(synthesized)
                saved_question_update = (
                    synth_mod["reworded"] if synth_mod["approved"] else synthesized
                )

            # Use BEGIN IMMEDIATE for atomic lookup+write (Fix 7). Re-resolve
            # inside the transaction: if a concurrent save inserted a row in
            # the window above, we update it instead of double-inserting.
            conn.execute("BEGIN IMMEDIATE")
            existing_row = _resolve_existing(conn)

            if existing_row:
                row_id = existing_row["id"]
                # Rare race: the row appeared between the pre-resolve and the
                # transaction, so no synthesis ran. Save the moderated new
                # question rather than making a network call under the lock.
                saved_question = (
                    saved_question_update
                    if saved_question_update is not None
                    else moderation["reworded"]
                )

                # context_range: only overwrite when the new ask provided
                # one. Empty/None on a follow-up question means "carry the
                # original range forward" rather than blanking it.
                if context_range is not None:
                    conn.execute(
                        "UPDATE assistant_conversations "
                        "SET question = ?, answer = ?, model_used = ?, "
                        "    response_time_ms = ?, context_range = ? "
                        "WHERE id = ?",
                        (
                            saved_question,
                            data["answer"],
                            data.get("model_used", ""),
                            data.get("response_time_ms"),
                            context_range,
                            row_id,
                        ),
                    )
                else:
                    conn.execute(
                        "UPDATE assistant_conversations "
                        "SET question = ?, answer = ?, model_used = ?, "
                        "    response_time_ms = ? "
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
                    " context_summary, model_used, response_time_ms, "
                    " context_range) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["session_id"],
                        data["page_type"],
                        data["page_key"],
                        saved_question,
                        data["answer"],
                        data.get("context_summary", ""),
                        data.get("model_used", ""),
                        data.get("response_time_ms"),
                        context_range,
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


@app.route("/api/assistant/session-qa")
def get_assistant_session_qa():
    """All of ONE browser session's own Q&A (verse/word/root), for the /saved page.

    The session_id is the per-browser UUID the assistant already uses — it
    acts as the bearer here (same trust model as /api/assistant/save), so a
    user only ever sees the questions they themselves asked. Anchored to the
    three saveable page types; admin-hidden rows are withheld. page_type is
    returned so the client can match each row to its saved verse/word/root.
    """
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"qa": []})
    try:
        limit = min(int(request.args.get("limit", 300)), 500)
    except (ValueError, TypeError):
        limit = 300

    conn = get_db()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(assistant_conversations)")]
        has_hidden = "hidden" in cols
        sql = (
            "SELECT id, page_type, page_key, question, answer, created_at "
            "FROM assistant_conversations "
            "WHERE session_id = ? AND page_type IN ('verse', 'word', 'root') "
            + ("  AND COALESCE(hidden, 0) = 0 " if has_hidden else "")
            + "ORDER BY created_at DESC LIMIT ?"
        )
        rows = conn.execute(sql, (session_id, limit)).fetchall()
        return jsonify({
            "qa": [
                {
                    "id": r["id"],
                    "page_type": r["page_type"],
                    "page_key": r["page_key"],
                    "question": r["question"],
                    "answer": r["answer"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        })
    finally:
        conn.close()


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
        # context_range may not exist on legacy DBs that pre-date the
        # reader-range feature; selecting it through `*` would crash.
        # The migration runs at startup, but we degrade cleanly anyway.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(assistant_conversations)")]
        has_range = "context_range" in cols
        has_hidden = "hidden" in cols
        has_review = "review_status" in cols
        sql = (
            "SELECT id, question, answer, model_used, created_at"
            + (", context_range" if has_range else "")
            + " FROM assistant_conversations "
            "WHERE page_type = ? AND page_key = ? "
            # Admin-hidden Q&A are withheld from the public per-verse list
            # (degrade cleanly on legacy DBs that pre-date the column).
            + ("  AND COALESCE(hidden, 0) = 0 " if has_hidden else "")
            # AI-drafted rows are public only once approved; user-asked rows
            # (source NULL/'user') are unaffected.
            + ("  AND (COALESCE(source, 'user') = 'user' OR review_status = 'approved') " if has_review else "")
            + "ORDER BY created_at DESC LIMIT ?"
        )
        rows = conn.execute(sql, (page_type, page_key, limit)).fetchall()
        return jsonify({
            "history": [
                {
                    "id": r["id"],
                    "question": r["question"],
                    "answer": r["answer"],
                    "model_used": r["model_used"],
                    "created_at": r["created_at"],
                    "context_range": (r["context_range"] if has_range else None),
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


# A few AI-generated root meanings came back as the prompt's own heading
# ("## Root Analysis: ا ب د") with no meaning behind them at all, and the rest
# vary between sentence case, all-lowercase and (rarely) ALL CAPS. Normalized
# at READ time so the stored text stays untouched — regenerating a meaning
# later isn't then fighting a one-off rewrite of the column. Used by every
# surface that shows ai_root_meanings.primary_meaning: the root page heading,
# root search, the /dictionary index, and the crawler HTML.
_GLOSS_HEADING_RE = re.compile(
    r"^\s*(?:root\s+analysis|analysis\s+of\s+(?:the\s+)?root)\b", re.I
)
_GLOSS_WRAPPED_RE = re.compile(r"^(\*\*|\*|__|_)(.+?)\1$", re.S)


def _clean_root_gloss(gloss):
    """Display-ready root meaning: markdown stripped, uniform sentence case.
    Returns None when the stored text is a failed generation carrying only a
    heading, so callers can show nothing rather than junk."""
    if not gloss:
        return None
    for raw in str(gloss).splitlines():
        s = re.sub(r"^#{1,6}\s*", "", raw.strip()).strip()
        if not s or _GLOSS_HEADING_RE.match(s):
            continue
        m = _GLOSS_WRAPPED_RE.match(s)   # "**glad tidings**" -> "glad tidings"
        if m:
            s = m.group(2).strip()
        if not s:
            continue
        # Shouty entries ("OPPONENT, ADVERSARY") get folded down, but only when
        # there's no lowercase at all — mixed case may hold proper nouns.
        if any(c.isupper() for c in s) and not any(c.islower() for c in s):
            s = s.lower()
        # Capitalize the first letter that HAS a capital, so a leading quote or
        # a caseless transliteration mark is stepped over ("ʿibāda" -> "ʿIbāda")
        # while an all-Arabic or digit-led gloss is left exactly as it is.
        for i, ch in enumerate(s):
            if ch.isalpha() and ch.upper() != ch.lower():   # a letter that HAS case
                return s[:i] + ch.upper() + s[i + 1:]
            if ch.isalnum() and not ch.isalpha():
                break                    # "3rd person" — don't reach into the word
        return s
    return None


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
            # Cleaned for display — the page uses this as its heading, so a
            # failed generation would otherwise title the root "## Root
            # Analysis:". None here simply hides the meaning panel.
            result["primary_meaning"] = _clean_root_gloss(ai_row["primary_meaning"])
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

        # Enrich roots with cognate data, then layer the surveyed canonical
        # English on top when one exists. The chip box on /verse/<ref> shows
        # `r.cognate.concept`; for surveyed roots we want that to be the
        # admin-curated canonical (e.g. "endure" for ص-ب-ر) rather than the
        # raw Semitic-cognate concept ("restrain / ice / pointed tool"),
        # because the survey reflects deliberate Quran-only methodology.
        # The original concept is preserved on `cognate.concept_cognate` for
        # any UI that wants to surface it explicitly.
        roots_list = list(roots_seen.values())
        for root_entry in roots_list:
            cognate = _get_cognate(conn, root_entry["root_buckwalter"])
            survey_row = conn.execute(
                "SELECT canonical_english FROM term_surveys "
                "WHERE root_buckwalter = ? AND canonical_english IS NOT NULL "
                "AND TRIM(canonical_english) != ''",
                (root_entry["root_buckwalter"],),
            ).fetchone()
            if survey_row and survey_row["canonical_english"]:
                if cognate is None:
                    cognate = {"concept": survey_row["canonical_english"]}
                else:
                    cognate = dict(cognate)
                    cognate["concept_cognate"] = cognate.get("concept")
                    cognate["concept"] = survey_row["canonical_english"]
                    cognate["from_survey"] = True
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


@app.route("/api/build-info")
def build_info():
    """Deploy metadata baked into the image at build time by the
    GitHub Actions workflow + Dockerfile ARGs. Used by the admin
    dashboard to show "Website last updated on X via commit Y"
    without an external GitHub API call. Returns empty strings on
    local dev (no build args set) so the dashboard can render a
    "running locally" hint.

    Public endpoint — the data is harmless deployment metadata
    (commit SHA + message + date) and a future public footer might
    want to surface it too."""
    return jsonify({
        "sha": os.environ.get("BUILD_GIT_SHA", ""),
        "sha_short": os.environ.get("BUILD_GIT_SHA_SHORT", ""),
        "date": os.environ.get("BUILD_GIT_DATE", ""),
        "message": os.environ.get("BUILD_GIT_MESSAGE", ""),
        # Hard-coded so the dashboard can build a commit URL
        # without parsing the git remote at runtime. If we ever
        # rename the repo, update here.
        "repo": "jawadshuaib/quran-analyzer",
    })


@app.route("/api/surahs")
def get_surahs():
    """List all 114 surahs with English + Arabic names + verse counts.
    Used by the search bar surah picker and the homepage reader index."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT chapter, COUNT(*) as verse_count FROM verses GROUP BY chapter ORDER BY chapter"
        ).fetchall()

        surahs = []
        for row in rows:
            ch = row["chapter"]
            surahs.append({
                "number": ch,
                "name": _surah_name(ch),
                "name_arabic": _surah_arabic(ch),
                "meaning": _surah_meaning(ch),
                "verse_count": row["verse_count"],
            })

        return jsonify(surahs)
    finally:
        conn.close()


@app.route("/api/surah/<int:surah>")
def get_surah(surah: int):
    """Bulk-fetch every verse of one surah for the reader page.

    Default response includes Arabic text + English translation + flags
    for translation-notes / grammar-notes presence (used by the reader
    gutter icons).

    Optional ?include=words,surveyed_roots query param:
      - words: per-verse `words: [{position, form_arabic, translation}]`
        for the word-by-word reader view
      - surveyed_roots: per-verse `surveyed_roots: [<root_buckwalter>]`
        — the subset of roots in the verse that have a term_surveys row,
        used by the chip-tooltip layer in the reader translation
    """
    if not 1 <= surah <= 114:
        return jsonify({"error": "surah must be 1-114"}), 400
    include = set(
        i.strip() for i in (request.args.get("include") or "").split(",") if i.strip()
    )
    include_words = "words" in include
    include_surveyed = "surveyed_roots" in include

    conn = get_db()
    try:
        verse_rows = conn.execute(
            "SELECT verse, text_uthmani FROM verses "
            "WHERE chapter = ? ORDER BY verse",
            (surah,),
        ).fetchall()
        if not verse_rows:
            return jsonify({"error": f"surah {surah} not found"}), 404

        # Pull translations + departure-note flags in bulk
        trans_rows = conn.execute(
            "SELECT verse, translation_text, revised_text, departure_notes "
            "FROM ai_translations WHERE chapter = ?",
            (surah,),
        ).fetchall()
        trans_by_verse = {
            r["verse"]: {
                "translation": (r["revised_text"] or r["translation_text"] or ""),
                "has_translation_note": bool(r["departure_notes"]),
            }
            for r in trans_rows
        }

        # Grammar-note presence (just a flag, not the full markdown)
        gn_rows = conn.execute(
            "SELECT verse FROM ai_grammar_notes "
            "WHERE chapter = ? AND notes_markdown IS NOT NULL "
            "  AND TRIM(notes_markdown) != ''",
            (surah,),
        ).fetchall()
        has_grammar = {r["verse"] for r in gn_rows}

        # Exegesis-note presence (approved + non-hidden only — same gate as
        # the public /api/verse/<>/exegesis endpoint), so the reader's Notes
        # icon appears whenever a publicly-visible exegesis note exists.
        _ensure_exegesis_table(conn)
        exeg_rows = conn.execute(
            "SELECT verse FROM verse_exegesis "
            "WHERE chapter = ? AND review_status = 'approved' "
            "  AND COALESCE(hidden, 0) = 0",
            (surah,),
        ).fetchall()
        has_exegesis = {r["verse"] for r in exeg_rows}

        # Pre-Islamic poetry-note presence (same approved + non-hidden gate as
        # the public /api/verse/<>/poetry endpoint), so the reader's Notes icon
        # also lights up when a verse has a poetry note.
        _ensure_poetry_serve_tables(conn)
        poetry_rows = conn.execute(
            "SELECT verse FROM verse_poetry_notes "
            "WHERE chapter = ? AND review_status = 'approved' "
            "  AND COALESCE(hidden, 0) = 0",
            (surah,),
        ).fetchall()
        has_poetry = {r["verse"] for r in poetry_rows}

        # Optional: per-word data (full segments + translation). Grouped
        # by word_pos so prefixes/suffixes/content all live under one
        # word entry — earlier we only kept ONE segment per word_pos
        # (arbitrary which one) which made compound words like فَصَلِّ
        # show up as just the prefix فَ in the reader's word-by-word view.
        #
        # When ai_word_meanings has no row for a position (~800 such
        # gaps in the corpus), we fall back to the root's primary
        # meaning from ai_root_meanings (which covers all 1642 roots).
        # The frontend renders fallback glosses with a different style
        # so the reader knows it's a root-level hint, not a verb-form
        # gloss.
        words_by_verse: dict[int, list[dict]] = {}
        if include_words:
            morph_rows = conn.execute(
                "SELECT verse, word_pos, segment, "
                "       form_arabic, form_buckwalter, tag, pos, "
                "       root_arabic, root_buckwalter, "
                "       lemma_arabic, lemma_buckwalter "
                "FROM morphology "
                "WHERE chapter = ? "
                "ORDER BY verse, word_pos, segment",
                (surah,),
            ).fetchall()
            wm_rows = conn.execute(
                "SELECT verse, word_pos, preferred_translation, meaning_short "
                "FROM ai_word_meanings WHERE chapter = ?",
                (surah,),
            ).fetchall()
            wm_by_key: dict[tuple[int, int], dict] = {
                (r["verse"], r["word_pos"]): r for r in wm_rows
            }

            # word_glosses is the conventional Quran.com-style per-word
            # English source. It covers ~4100 positions where the AI-
            # generated ai_word_meanings has gaps (the dataset the
            # /verse/<ref> research view uses for its word-by-word
            # column). Pre-load for this surah.
            wg_rows = conn.execute(
                "SELECT verse, word_pos, translation_en "
                "FROM word_glosses WHERE chapter = ?",
                (surah,),
            ).fetchall()
            wg_by_key: dict[tuple[int, int], str] = {
                (r["verse"], r["word_pos"]): (r["translation_en"] or "").strip()
                for r in wg_rows
            }

            # Pre-load ai_root_meanings for the LAST-RESORT fallback
            # (when neither AI nor conventional has a per-word entry —
            # only ~16 such positions in the entire corpus). Tiny
            # table; one query covers the full corpus.
            root_meaning_rows = conn.execute(
                "SELECT root_buckwalter, primary_meaning FROM ai_root_meanings"
            ).fetchall()
            root_meaning_map: dict[str, str] = {
                r["root_buckwalter"]: (_clean_root_gloss(r["primary_meaning"]) or "")
                for r in root_meaning_rows
            }

            def _content_root(segs: list[dict]) -> str | None:
                """Pick the content-word segment's root for fallback
                gloss. Skips prefixes / suffixes / pronouns / particles.
                Returns the buckwalter string or None."""
                content_pos = ("Proper Noun", "Noun", "Verb", "Adjective")
                for s in segs:
                    if s.get("pos") in content_pos and s.get("root_buckwalter"):
                        return s["root_buckwalter"]
                # Fallback: any segment with a root
                for s in segs:
                    if s.get("root_buckwalter"):
                        return s["root_buckwalter"]
                return None

            def _emit_word(verse_n: int, word_pos: int, segs: list[dict]):
                # Resolve gloss with a clear priority chain:
                #   1. AI-judged preferred_translation (best per-word)
                #   2. AI meaning_short
                #   3. Conventional word_glosses.translation_en
                #   4. Root-level ai_root_meanings.primary_meaning
                #   5. Empty string
                # Source is "word" for 1-3 (real per-word data), "root"
                # for 4 (root-level hint). The frontend styles "root"
                # entries distinctly so users know the gloss is the
                # root's primary meaning, not a per-form translation.
                key = (verse_n, word_pos)
                wm = wm_by_key.get(key)
                preferred = (wm["preferred_translation"] if wm else None) or ""
                short = (wm["meaning_short"] if wm else None) or ""
                translation = (preferred or short).strip()
                source = ""
                if translation:
                    source = "word"
                else:
                    wg = wg_by_key.get(key, "")
                    if wg:
                        translation = wg
                        source = "word"
                    else:
                        rbw = _content_root(segs)
                        if rbw:
                            primary = root_meaning_map.get(rbw, "").strip()
                            if primary:
                                translation = primary
                                source = "root"
                words_by_verse.setdefault(verse_n, []).append({
                    "position": word_pos,
                    "segments": segs,
                    "translation": translation,
                    "translation_source": source,
                })

            # Walk morphology in order, building (verse → list of words),
            # each word being { position, segments[], translation, source }.
            # Multiple segments at the same (verse, word_pos) are
            # accumulated under that word's segments list.
            cur_key: tuple[int, int] | None = None
            cur_segs: list[dict] = []
            for r in morph_rows:
                key = (r["verse"], r["word_pos"])
                if key != cur_key:
                    if cur_key is not None:
                        _emit_word(cur_key[0], cur_key[1], cur_segs)
                    cur_key = key
                    cur_segs = []
                cur_segs.append({
                    "form_arabic": r["form_arabic"],
                    "form_buckwalter": r["form_buckwalter"],
                    "tag": r["tag"],
                    "pos": r["pos"],
                    "root_arabic": r["root_arabic"],
                    "root_buckwalter": r["root_buckwalter"],
                    "lemma_arabic": r["lemma_arabic"],
                    "lemma_buckwalter": r["lemma_buckwalter"],
                })
            if cur_key is not None:
                _emit_word(cur_key[0], cur_key[1], cur_segs)

        # Optional: surveyed_roots per verse — root_buckwalters that
        # both appear in the verse AND have a term_surveys row. Lets
        # the reader's chip layer know which words to make tooltipped.
        surveyed_by_verse: dict[int, list[str]] = {}
        if include_surveyed:
            sr_rows = conn.execute(
                "SELECT m.verse, m.root_buckwalter "
                "FROM morphology m "
                "JOIN term_surveys t ON t.root_buckwalter = m.root_buckwalter "
                "WHERE m.chapter = ? AND m.root_buckwalter IS NOT NULL "
                "GROUP BY m.verse, m.root_buckwalter "
                "ORDER BY m.verse",
                (surah,),
            ).fetchall()
            for r in sr_rows:
                surveyed_by_verse.setdefault(r["verse"], []).append(r["root_buckwalter"])

        verses = []
        for r in verse_rows:
            v = r["verse"]
            tr = trans_by_verse.get(v, {})
            entry: dict = {
                "verse": v,
                "text_uthmani": _strip_bismillah(r["text_uthmani"], surah, v),
                "translation": tr.get("translation", ""),
                "has_translation_note": bool(tr.get("has_translation_note")),
                "has_grammar_note": v in has_grammar,
                "has_exegesis": v in has_exegesis,
                "has_poetry_note": v in has_poetry,
            }
            if include_words:
                entry["words"] = words_by_verse.get(v, [])
            if include_surveyed:
                entry["surveyed_roots"] = surveyed_by_verse.get(v, [])
            verses.append(entry)

        return jsonify({
            "surah": surah,
            "name": _surah_name(surah),
            "name_arabic": _surah_arabic(surah),
            "meaning": _surah_meaning(surah),
            "verse_count": len(verses),
            "verses": verses,
        })
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
            "SELECT t.translation_text, t.revised_text, t.departure_notes, "
            "       t.created_at, c.config_name, c.model_name "
            "FROM ai_translations t "
            "JOIN ai_translation_configs c ON t.config_id = c.id "
            "WHERE t.chapter = ? AND t.verse = ? "
            "ORDER BY t.created_at DESC LIMIT 1",
            (surah, ayah),
        ).fetchone()

        if not row:
            return jsonify({"error": "No AI translation available"}), 404

        # Prefer revised_text when present (transliteration applied for
        # hard-case verses); fall back to the original translation_text.
        active = row["revised_text"] if row["revised_text"] else row["translation_text"]
        was_revised = bool(row["revised_text"])

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "translation": active,
            "translation_original": row["translation_text"] if was_revised else None,
            "is_revised": was_revised,
            "departure_notes": row["departure_notes"],
            "word_anchors": _fetch_word_anchors(conn, surah, ayah, 'translation_notes'),
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "created_at": row["created_at"],
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/grammar-notes")
def get_grammar_notes(surah: int, ayah: int):
    """Return the most recent grammar notes for a verse with all referenced terms.

    Notes are stored as markdown-like prose with [[term]] markers that wrap
    technical grammar terms. This endpoint joins each referenced term with the
    centralized `grammar_terms` glossary so the frontend can render tooltips
    without a second fetch.

    Response: 404 if no notes exist for the verse.
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT n.notes_markdown, n.referenced_terms, n.created_at, "
            "       c.config_name, c.model_name, c.prompt_version "
            "FROM ai_grammar_notes n "
            "JOIN grammar_notes_configs c ON n.config_id = c.id "
            "WHERE n.chapter = ? AND n.verse = ? "
            "ORDER BY n.created_at DESC LIMIT 1",
            (surah, ayah),
        ).fetchone()

        if not row:
            return jsonify({"error": "No grammar notes available"}), 404

        try:
            term_names = json.loads(row["referenced_terms"] or "[]")
        except (json.JSONDecodeError, TypeError):
            term_names = []

        terms_map = {}
        if term_names:
            placeholders = ",".join(["?"] * len(term_names))
            term_rows = conn.execute(
                f"SELECT term_english, term_arabic, plain_explanation, "
                f"       example_sentence, example_translation "
                f"FROM grammar_terms "
                f"WHERE term_english IN ({placeholders})",
                tuple(term_names),
            ).fetchall()
            for tr in term_rows:
                # Key by lowercased term so frontend lookup is case-insensitive
                terms_map[tr["term_english"].lower()] = {
                    "term_english": tr["term_english"],
                    "term_arabic": tr["term_arabic"],
                    "plain_explanation": tr["plain_explanation"],
                    "example_sentence": tr["example_sentence"],
                    "example_translation": tr["example_translation"],
                }

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "notes_markdown": row["notes_markdown"],
            "terms": terms_map,
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "created_at": row["created_at"],
        })
    finally:
        conn.close()


# =========================================================================
# Grammar term categorization
# -------------------------------------------------------------------------
# The glossary is organized pedagogically rather than alphabetically: terms
# related by grammatical function sit next to each other. The category is
# stored on the row so the frontend/noscript/sitemap logic can all read it
# cheaply, and the categorize() function is the single source of truth —
# it's invoked on startup to backfill NULL categories (after new terms are
# inserted by the grammar_notes_ai.py pipeline, the next backend restart
# will categorize them).
# =========================================================================

GRAMMAR_CATEGORIES = [
    "Sentence Structures",
    "Case & Mood",
    "Subjects, Objects & Complements",
    "Verb Morphology & Forms",
    "Tense & Aspect",
    "Participles & Verbal Nouns",
    "Nouns",
    "Pronouns",
    "Prepositions",
    "Particles",
    "Negation",
    "Emphasis & Restriction",
    "Conditionals & Oaths",
    "Interrogatives",
    "Relatives",
    "Vocatives & Address",
    "Adverbial & Circumstantial",
    "Inna / Kāna Families",
    "Rhetorical Devices",
    "Agreement & Number",
    "Morphology & Phonology",
    "Other",
]

# Rule table: ordered — first match wins. Each rule is
# (category, regex_pattern). Patterns are matched case-insensitively
# against the English term first, then the explanation as a fallback.
_GRAMMAR_CAT_RULES = [
    ("Inna / Kāna Families",
     r"\b(inna and its sisters|kana and its sisters|sisters of|and its sisters)\b|\b(kāna|kana|laysa|layta|la.alla|ka.anna|lakinna|lākinna|ṣāra|aṣbaḥa|amsā|ẓalla|bāta|ʾanna|ʾinna|dhanna|ḥasiba|khāla|predicate of kana)\b|\binna\b|\binnamā\b|\bPredicate of 'Kana'\b"),
    ("Conditionals & Oaths",
     r"\b(conditional|counterfactual|hypothetical|apodosis|protasis|consequence particle|oath|qasam)\b|^law\b|^lawla\b|^lawlā\b|^idha\b|^idhā\b|\bwāw of oath\b|\bwaw of oath\b"),
    ("Adverbial & Circumstantial",
     r"^(hal|ḥāl|halah|circumstantial|adverbial|adverb|locative adverb)\b|\baccusative of (time|place|reason|purpose|specification|exaltation)\b|\b(adverb of|zarf|ẓarf)\b"),
    ("Rhetorical Devices",
     r"\b(iltifāt|iltifat|rhetorical|fronting|taqdīm|taqdim|topicalization|ellipsis|omission|ḥadhf|metaphor|metonymy|parallelism|antithesis|chiasmus|merism|hasr|ḥaṣr|restriction|exclusive|fasl|faṣl|direct speech|badal|apposit|tamyiz|tamyīz|specification|exception|exceptive|istithnāʾ|istithna|concessive|iqtiṣāṣ|contrastive topic)\b"),
    ("Pronouns",
     r"\bpronoun\b|\bpronominal\b|\bdemonstrative\b|^(1st|2nd|3rd|first|second|third) person\b|^damir|^ḍamīr|\bgrammatical person\b"),
    ("Negation",
     r"\b(negation|negative|negator|negating|absolute negat)\b|^(lā|la) (of|al-)|\b(lam|lan|laysa|lā nāfiya|lā nafiya|lā naf|mā al-)\b|\bno verb\b|\bno noun\b"),
    ("Emphasis & Restriction",
     r"\b(emphatic|emphasis|emphasising|emphasizing|tawkīd|tawkid|assertive|corroborative|corroborat|intensif|confirmatory|confirm|accentuating)\b"),
    ("Prepositions",
     r"\bpreposition\b|\bprepositional\b|\bharf jar\b"),
    ("Case & Mood",
     r"^(nominative|accusative|genitive|jussive|subjunctive|indicative|mansub|majzum|marfu|majrūr|majrur|mabni|muʿrab|apocopate|indeclinable)\b|^(case|mood|aspect|tense|voice|active|passive)$|^grammatical (case|mood)$|\b(active|passive) (voice|verb|participle)\b"),
    ("Verb Morphology & Forms",
     r"^form [ivx]+\b|^verb form|\b(triliteral|biliteral|quadriliteral|quintuple)\b|\broot letters?\b|^(transitive|intransitive|ditransitive|copular|defective|sound|weak|hollow|assimilated|doubled|denominal)\b|^(causative|reflexive|reciprocal|iterative|intensive|factitive)\b|\b(double accusative|double object|doubly transitive|approach verb|auxiliary verb|derived form|reciprocity|inceptive verb)\b"),
    ("Tense & Aspect",
     r"^(perfect|imperfect|past|present|future|imperative|continuous past)\b|\b(continuous past|past tense|perfect tense|perfect verb|imperfect verb|imperfect aspect|jussive mood)\b"),
    ("Participles & Verbal Nouns",
     r"\b(participle|gerund|masdar|verbal noun|infinitive|active participle|passive participle)\b"),
    ("Nouns",
     r"\b(idāfa|idafa|idaafa|possessive construct|construct phrase|annexation|genitive construction|possessive noun|possessive)\b|^(noun|proper noun|common noun|definite|indefinite|nakira|ma.rifa|definiteness|indefiniteness|collective|broken plural|sound plural|diminutive|elative|elicitive|superlative|comparative|partitive|ism tafdil|ism tafdeel|ism fāʿil|ism mafʿūl|attribute|attributive noun|adjective|adjective agreement)\b|^ism\b"),
    ("Interrogatives",
     r"^(interrogative|question particle)\b|\b(question particle|interrogative particle|hamza of interrogation|hal particle)\b|\bexclamation\b"),
    ("Relatives",
     r"\brelative (pronoun|clause)\b|^alladh[īyū]\b|\bism mawṣūl\b"),
    ("Vocatives & Address",
     r"\b(vocative|nidā|nidāʾ|nida|ya of |calling|address|interjection)\b"),
    ("Sentence Structures",
     r"\b(nominal|verbal) (sentence|clause|phrase|jumla)\b|\bjumla\b|^(sentence|clause|phrase|main clause|subordinate|dependent clause|embedded clause|result clause|apposition|appositive|apposite)\b"),
    ("Agreement & Number",
     r"\b(agreement|concord|number|gender|plural agreement|feminine|masculine|singular|dual|plural|agreement by meaning|agreement shift|agreement mismatch)\b"),
    ("Subjects, Objects & Complements",
     r"^(subject|agent|object|objects|complement|predicate|mubtada|khabar|mafʿūl|mafʿūl bi|maf.ul|fāʿil|nāʾib|delayed subject|postponed subject|grammatical object)\b|\b(mafʿūl|mafʿūl bi|fāʿil|nāʾib al-fāʿil)\b"),
    ("Morphology & Phonology",
     r"\b(wazn|pattern|morpholog|affix|prefix|suffix|infix|nunation|tanwīn|tanwin|iʿrāb|irab|sukūn|sukun|ḥaraka|haraka|vowel|hamza|sun letter|moon letter|assimilat|shadda|dagger alif|disconnected letters|disjointed letters|gemin|elision|root)\b"),
    # Broad fallback — anything still "X particle" or generic conjunction
    ("Particles",
     r"\bparticle\b|\bparticles\b|\bconjunction\b|\bconjunctive\b|\bdiscourse marker\b|\bfa-?\b|\bwāw\b|\bwaw\b|\bmarker\b"),
    # --- Final cleanup rules for terms the more specific patterns miss ---
    ("Subjects, Objects & Complements",
     r"^(second object|substitute|vicarious subject|vice-subject)$"),
    ("Adverbial & Circumstantial",
     r"^(temporal adverb|temporal clause|time adverb)$"),
    ("Sentence Structures",
     r"^(VSO word order|SVO word order|word order)$"),
    ("Rhetorical Devices",
     r"^(topical structure)$"),
    ("Verb Morphology & Forms",
     r"^(verb|transformative verb|verb of becoming|verb of censure|verbs of becoming|verbs of nearness|verb taking two objects|verb \"to be\"|verb to be)$"),
    ("Tense & Aspect",
     r"^(verb aspect|verb voice)$"),
    ("Nouns",
     r"^(sifa|ṣifa)$"),
    ("Morphology & Phonology",
     r"^(morphology|syntax)$"),
]


def _categorize_grammar_term(term: str, explanation: str = "") -> str:
    """Return the best-fit category for a grammar term.

    Tries the term name first; falls back to explanation if the term is
    ambiguous. Unknown terms fall into 'Other' — these can be fixed by
    adding more patterns above or by manually updating the row.
    """
    for cat, pat in _GRAMMAR_CAT_RULES:
        if re.search(pat, term or "", re.IGNORECASE):
            return cat
    for cat, pat in _GRAMMAR_CAT_RULES:
        if re.search(pat, explanation or "", re.IGNORECASE):
            return cat
    return "Other"


def _ensure_grammar_term_category():
    """Add the category column if missing, then backfill any NULL rows.

    Idempotent — safe to run on every startup. New rows inserted by the
    grammar_notes_ai.py pipeline get categorized on the next restart.
    """
    conn = get_db()
    try:
        try:
            conn.execute("ALTER TABLE grammar_terms ADD COLUMN category TEXT")
            conn.commit()
        except Exception:
            pass  # column already exists

        rows = conn.execute(
            "SELECT term_english, plain_explanation FROM grammar_terms "
            "WHERE category IS NULL OR category = ''"
        ).fetchall()
        if not rows:
            return
        updates = [
            (_categorize_grammar_term(r["term_english"], r["plain_explanation"]),
             r["term_english"])
            for r in rows
        ]
        conn.executemany(
            "UPDATE grammar_terms SET category = ? WHERE term_english = ?",
            updates,
        )
        conn.commit()
        print(f"[grammar_terms] categorized {len(updates)} rows")
    finally:
        conn.close()


try:
    _ensure_grammar_term_category()
except Exception as e:
    print(f"WARNING: grammar_terms category backfill failed: {e}")


@app.route("/api/grammar-terms")
def get_grammar_terms_all():
    """Return the full grammar terms glossary grouped by category.

    Response shape:
      {
        "categories": ["Sentence Structures", "Case & Mood", ...],  // display order
        "terms": [ { term_english, term_arabic, plain_explanation,
                     example_sentence, example_translation, category } ]
      }
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT term_english, term_arabic, plain_explanation, "
            "       example_sentence, example_translation, category, updated_at "
            "FROM grammar_terms ORDER BY term_english COLLATE NOCASE"
        ).fetchall()
        return jsonify({
            "categories": GRAMMAR_CATEGORIES,
            "terms": [dict(r) for r in rows],
        })
    finally:
        conn.close()


# English word families that should trigger a glossary chip when seen in
# a verse translation, IF the verse's morphology contains the matching
# root. Combines (a) the canonical's inflections (so "connect/connection"
# lights up where Slw is used) with (b) the conventional ritualistic
# English (so "prayer" also lights up — same root, broader meaning).
# Words like bare "stand" / "fast" / "bow" are excluded because they're
# too ambiguous to chip on word-match alone — the verse-page chips for
# those roots only fire on transliteration markers.
_CHIP_WORD_FAMILIES: dict[str, list[str]] = {
    # Slw → connect (canonical) ∪ prayer (conventional)
    "Slw":  ["connect", "connects", "connected", "connecting",
             "connection", "connections",
             "prayer", "prayers", "praying", "prayed", "prays"],
    # zkw → grow (canonical) ∪ alms / zakah / purifying-due (conventional)
    "zkw":  ["grow", "grows", "grew", "grown", "growing", "growth",
             "alms", "almsgiving", "zakah", "zakāh", "zakat"],
    # Swm → abstain (canonical) ∪ fasting (conventional)
    "Swm":  ["abstain", "abstains", "abstained", "abstaining",
             "abstention", "abstinence",
             "fasting", "fasted", "fasts"],
    # Hjj → argue (canonical) ∪ pilgrimage (conventional)
    "Hjj":  ["argue", "argues", "argued", "arguing", "argument", "arguments",
             "pilgrimage", "pilgrim", "pilgrims"],
    # sjd → submit (canonical) ∪ prostrate/prostration (conventional)
    "sjd":  ["submit", "submits", "submitted", "submitting", "submission",
             "submissions", "submissive",
             "prostrate", "prostrates", "prostrated", "prostrating",
             "prostration", "prostrations"],
    # rkE → humble (canonical) ∪ bowing (conventional, narrow)
    "rkE":  ["humble", "humbles", "humbled", "humbling", "humbly",
             "humility",
             "bowing", "bowed"],
    # snn → pattern (canonical) ∪ sunnah (conventional)
    "snn":  ["pattern", "patterns", "patterned",
             "sunnah", "sunna"],
    # nsk → devotion (canonical)
    "nsk":  ["devote", "devotes", "devoted", "devoting", "devotion",
             "devotions", "devotional"],
    # qwm → stand (canonical, broad) — only chip the conventional ritual word
    # "establish" since bare "stand" is too ambiguous
    "qwm":  ["establish", "establishes", "established", "establishing"],
    # $Er → perceive (canonical) ∪ rites (conventional)
    "$Er":  ["perceive", "perceives", "perceived", "perceiving",
             "perception", "perceptible",
             "rite", "rites", "ritual"],
    # Emr → cultivate (canonical) ∪ umrah (conventional)
    "Emr":  ["cultivate", "cultivates", "cultivated", "cultivating",
             "cultivation",
             "umrah", "ʿumrah"],
    # *kr → remember (canonical, also conventional)
    "*kr":  ["remember", "remembers", "remembered", "remembering",
             "remembrance", "reminder", "reminders", "remind", "reminds",
             "reminded", "reminding",
             "mention", "mentions", "mentioned", "mentioning"],
    # Thr → purify (canonical, also conventional)
    "Thr":  ["purify", "purifies", "purified", "purifying", "purification",
             "pure", "purity",
             "ablution", "ablutions"],
}


@app.route("/api/quran-vocabulary")
def get_quran_vocabulary():
    """Return the 13 surveyed ritualistic-vocabulary terms with their
    canonical Qur'an-only renderings, translation notes, and hard-case
    verse lists. Public, no auth — used by /quran-vocabulary frontend
    page. Each term row:
      {
        root_buckwalter, root_arabic, canonical_english,
        translation_note, occurrence_count, confidence,
        hard_cases: [{ref, arabic_word, transliteration, reason}, ...]
      }
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT root_buckwalter, root_arabic, canonical_english, "
            "       translation_note, occurrence_count, confidence, "
            "       leave_untranslated, hard_cases_json "
            "FROM term_surveys "
            "ORDER BY occurrence_count DESC"
        ).fetchall()
        terms = []
        for r in rows:
            hard_cases = []
            if r["hard_cases_json"]:
                try:
                    hard_cases = json.loads(r["hard_cases_json"])
                except Exception:
                    hard_cases = []
            terms.append({
                "root_buckwalter": r["root_buckwalter"],
                "root_arabic": r["root_arabic"],
                "canonical_english": r["canonical_english"],
                "translation_note": r["translation_note"],
                "occurrence_count": r["occurrence_count"],
                "confidence": r["confidence"],
                "leave_untranslated": bool(r["leave_untranslated"]),
                "hard_cases": hard_cases,
                "chip_word_family": _CHIP_WORD_FAMILIES.get(r["root_buckwalter"], []),
            })
        return jsonify({"terms": terms})
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


# --- Phase B: multilingual hybrid search -----------------------------------
_search_v2_hits: dict = {}          # ip -> [timestamps]
_SEARCH_V2_MAX = 30                 # per IP
_SEARCH_V2_WINDOW = 60              # seconds


def _search_v2_rate_limited(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _search_v2_hits.get(ip, []) if now - t < _SEARCH_V2_WINDOW]
    if len(_search_v2_hits) > 2000:  # bound memory
        _search_v2_hits.clear()
    hits.append(now)
    _search_v2_hits[ip] = hits
    return len(hits) > _SEARCH_V2_MAX


@app.route("/api/search/v2")
def search_v2_api():
    """Multilingual hybrid search (dense ar+en Voyage ⊕ lexical roots, RRF).

    GET /api/search/v2?q=verse+involving+satan+and+adam&limit=15
    Works for Arabic and English. Never 5xx: if Voyage is unreachable or the v2
    index isn't present, it degrades to the v1 English encoder + lexical arm and
    sets "degraded": true. Response mirrors /api/semantic-search plus per-result
    "matched_because" diagnostics and an "engine"/"degraded" flag.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    if len(query) > 500:
        return jsonify({"error": "Query too long (max 500 characters)"}), 400
    try:
        limit = min(int(request.args.get("limit", "15")), 50)
    except (ValueError, TypeError):
        return jsonify({"error": "limit must be a positive integer"}), 400

    if _search_v2_rate_limited(_get_client_ip()):
        return jsonify({"error": "Too many searches, slow down a moment."}), 429

    if search_v2 is None:
        # Module failed to import — fall back to v1 so search still works.
        results = _semantic_search(query, limit=limit)
        conn = get_db()
        try:
            out = []
            for ch, v, score, snippet in results:
                out.append(_shape_v2_result(conn, ch, v, round(score, 6), {}))
            return jsonify({"query": query, "results": out, "total": len(out),
                            "degraded": True, "engine": "v1-only"})
        finally:
            conn.close()

    res = search_v2.hybrid_search(query, limit=limit)
    conn = get_db()
    try:
        out = []
        for r in res["results"]:
            out.append(_shape_v2_result(conn, r["surah"], r["ayah"], r["score"],
                                        r.get("matched_because", {})))
        return jsonify({
            "query": query,
            "results": out,
            "total": len(out),
            "degraded": res.get("degraded", False),
            "engine": res.get("engine", "v2-hybrid"),
        })
    finally:
        conn.close()


def _shape_v2_result(conn, ch, v, score, matched_because):
    """Enrich a (chapter, verse) retrieval hit with display text, reusing the
    same helpers as /api/semantic-search so the two endpoints agree."""
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, v),
    ).fetchone()
    text = row["text_uthmani"] if row else ""
    if text:
        text = _strip_bismillah(text, ch, v)
    return {
        "surah": ch,
        "ayah": v,
        "surah_name": _surah_name(ch),
        "text_uthmani": text,
        "translation": _best_translation(conn, ch, v) or "",
        "score": score,
        "matched_because": matched_because,
    }


def _detail_excerpt(detailed: str | None, max_chars: int = 240) -> str | None:
    """Trim meaning_detailed to a short excerpt for tooltip use.
    Cuts at the nearest sentence boundary <= max_chars when possible,
    falling back to a clean word-boundary cut otherwise."""
    if not detailed:
        return None
    text = detailed.strip()
    if len(text) <= max_chars:
        return text
    # Sentence boundary: prefer ". " or "! " or "? " up to max_chars
    cutoff = max_chars
    best = -1
    for sep in (". ", "! ", "? ", "; "):
        idx = text.rfind(sep, 0, cutoff)
        if idx > best:
            best = idx + 1  # include the punctuation
    if best > max_chars * 0.5:
        return text[: best].rstrip() + " …"
    # Fall back to word boundary
    space = text.rfind(" ", 0, cutoff)
    if space < 0:
        return text[: cutoff].rstrip() + "…"
    return text[: space].rstrip() + " …"


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
                "meaning_excerpt": _detail_excerpt(row["meaning_detailed"]),
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

        # All distinct roots in the parent verse — used by the frontend
        # TermChip layer to scope word-family chip matches.
        verse_roots_rows = conn.execute(
            "SELECT DISTINCT root_buckwalter FROM morphology "
            "WHERE chapter = ? AND verse = ? AND root_buckwalter IS NOT NULL",
            (surah, ayah),
        ).fetchall()
        verse_root_buckwalters = [r["root_buckwalter"] for r in verse_roots_rows]

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

                # All distinct roots in this other verse — for chip scoping.
                occ_roots_rows = conn.execute(
                    "SELECT DISTINCT root_buckwalter FROM morphology "
                    "WHERE chapter = ? AND verse = ? AND root_buckwalter IS NOT NULL",
                    (ch, v),
                ).fetchall()
                occ_verse_roots = [r["root_buckwalter"] for r in occ_roots_rows]

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
                    "verse_root_buckwalters": occ_verse_roots,
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
            "verse_root_buckwalters": verse_root_buckwalters,
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
                # (3s connect, 45s read) — was a flat 120s, which let this
                # public endpoint pin a scarce request thread for 2 minutes.
                timeout=(3, 45),
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
    if re.match(r"^/privacy/?$", path):
        return True
    if re.match(r"^/terms/?$", path):
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
    if re.match(r"^/saved/?$", path):
        return True
    if re.match(r"^/search/?$", path):
        return True
    if re.match(r"^/developers/?$", path):
        return True
    if re.match(r"^/methodology/?$", path):
        return True
    if re.match(r"^/grammar-glossary/?$", path):
        return True
    if re.match(r"^/quran-vocabulary/?$", path):
        return True
    if re.match(r"^/dictionary/?$", path):
        return True
    if re.match(r"^/502/?$", path):
        return True
    if re.match(r"^/read/\d+(:\d+(-\d+)?)?/?$", path):
        return True
    if re.match(r"^/admin(/settings|/scheduler|/revisions|/verse-settings|/verse-of-the-day|/stats|/judge-lessons|/qa|/qa-videos|/exegesis|/poetry|/dictionaries|/vocabulary(/[^/]+)?|/proper-nouns(/\d+)?|/pipelines(/recitation|/educational(/candidates)?)?|/media(/recitations|/resources|/music|/generate|/explanations|/generate-explanation|/pipelines|/educational(/word-origins|/translation-hides|/grammar-insights|/pipelines(/\d+)?)?)?)?/?$", path):
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

    # Site privacy policy: /privacy
    if re.match(r"^/privacy/?$", path):
        return {
            "title": "Privacy Policy | al-nuqta",
            "description": "Privacy policy for al-nuqta.com — what data we collect, what we don't, and how we handle it.",
            "og_type": "article",
            "canonical": SITE_URL + "/privacy",
            "robots": "index, follow",
        }

    # 502 server-error landing page: /502 (mirrors the SPA-side 404 for
    # noindex-friendly handling of upstream errors. Cloudflare or any
    # reverse proxy can be configured to redirect upstream 502s here so
    # users get a styled in-app message instead of the proxy default.)
    if re.match(r"^/502/?$", path):
        return {
            "title": "Server Unavailable | al-nuqta",
            "description": "The al-nuqta server is temporarily unavailable. Please try again in a moment.",
            "og_type": "website",
            "canonical": SITE_URL + "/502",
            "robots": "noindex, follow",
        }

    # Site terms of service: /terms
    if re.match(r"^/terms/?$", path):
        return {
            "title": "Terms of Service | al-nuqta",
            "description": "Terms of service for al-nuqta.com — permitted use, disclaimers, and scholarly caveats.",
            "og_type": "article",
            "canonical": SITE_URL + "/terms",
            "robots": "index, follow",
        }

    # Reader page: /read/2 or /read/2:255
    m = re.match(r"^/read/(\d+)(?::(\d+))?/?$", path)
    if m:
        surah = int(m.group(1))
        name = _surah_name(surah)
        arabic = _surah_arabic(surah)
        meaning = _surah_meaning(surah)
        # Canonical always points at /read/<n> — the verse-anchor URL
        # (/read/<n>:<v>) loads identical content; the verse number is
        # just a deep-link fragment that the React reader uses to
        # scroll into view. Telling Google "/read/<n>" is the canonical
        # version prevents duplicate-content indexing of the same page
        # 286× for Surah Al-Baqarah.
        canonical = f"{SITE_URL}/read/{surah}"
        return {
            "title": f"Read Surah {name} ({arabic}) | al-nuqta",
            "description": (
                f"Read Surah {name} — {meaning} — verse by verse "
                f"with English translation. Quranic Arabic with optional "
                f"word-by-word, in-line notes, and bookmarks."
            ),
            "og_type": "article",
            "canonical": canonical,
            "robots": "index, follow",
            # Custom hint that _build_meta_tags uses to emit a richer
            # JSON-LD block (Article + isPartOf Qur'an Book) plus a
            # BreadcrumbList for SERP rich-snippet support.
            "ld_type": "Surah",
            "surah_number": surah,
            "surah_name_english": name,
            "surah_name_arabic": arabic,
            "surah_meaning": meaning,
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

    # Grammar glossary: /grammar-glossary
    if re.match(r"^/grammar-glossary/?$", path):
        return {
            "title": "Grammar Glossary \u2014 Arabic Grammar Terms in Quranic Analysis | al-nuqta",
            "description": "Definitions and examples for every Arabic grammar term used in al-nuqta's verse-level grammar notes \u2014 \u1e25\u0101l, i\u1e0d\u0101fa, jussive, mubtada, subjunctive, and 600+ more. Each entry links back to the verses that reference it.",
            "og_type": "article",
            "canonical": SITE_URL + "/grammar-glossary",
            "robots": "index, follow",
        }

    # Quran vocabulary: /quran-vocabulary
    if re.match(r"^/quran-vocabulary/?$", path):
        return {
            "title": "Qur'an Vocabulary \u2014 Abstract Meanings of \u1e63al\u0101h, zak\u0101h, \u1e25ajj | al-nuqta",
            "description": "Some Qur'anic roots whose meaning is often narrowed when translated are explored in greater detail. For these roots, we trace every occurrence in the corpus and find the broader meaning that survives every usage.",
            "og_type": "article",
            "canonical": SITE_URL + "/quran-vocabulary",
            "robots": "index, follow",
        }

    # Qur'anic Dictionary: /dictionary
    if re.match(r"^/dictionary/?$", path):
        return {
            "title": "Qur'anic Dictionary \u2014 Classical Arabic Root Definitions | al-nuqta",
            "description": "Browse the classical Arabic lexicon for every Qur'anic root \u2014 Lis\u0101n al-\u02bfArab, al-Mufrad\u0101t and other classical works \u2014 harmonized into readable English with the original Arabic one click away, ordered alphabetically by root.",
            "og_type": "article",
            "canonical": SITE_URL + "/dictionary",
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

    # JSON-LD structured data — list of dicts. Most pages emit a single
    # block; some pages (e.g. surah readers) emit multiple, like an
    # Article + a BreadcrumbList, which is supported by all major
    # search engines.
    ld_type = meta.get("ld_type")
    ld_blocks: list[dict] = []
    if ld_type == "Course":
        ld_blocks.append({
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
        })
    elif og_type == "website":
        ld_blocks.append({
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "al-nuqta",
            "url": SITE_URL,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{SITE_URL}/verse/{{surah}}:{{ayah}}",
                "query-input": "required name=surah,ayah",
            },
        })
    elif ld_type == "Surah":
        # Surah reader: emit Article (enriched with articleSection +
        # isPartOf Qur'an Book) and a BreadcrumbList. Both feed Google
        # rich-snippet rendering — the Article gives a headline +
        # publisher summary, the BreadcrumbList replaces the URL slug
        # in SERPs with "al-nuqta › Read › Surah Name".
        surah_num = meta.get("surah_number")
        surah_en = meta.get("surah_name_english", "")
        surah_ar = meta.get("surah_name_arabic", "")
        ld_blocks.append({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": desc,
            "url": canonical,
            "articleSection": "Qur'an",
            "isPartOf": {
                "@type": "Book",
                "name": "The Qur'an",
                "alternateName": "Holy Qur'an",
                "inLanguage": "ar",
                "numberOfPages": 114,
            },
            "publisher": {
                "@type": "Organization",
                "name": "al-nuqta",
                "url": SITE_URL,
            },
        })
        crumb_label = f"Surah {surah_en}" + (f" ({surah_ar})" if surah_ar else "")
        # Two-level breadcrumb: Home → Surah X. We deliberately don't
        # add an intermediate "Read the Qur'an" level because there's
        # no dedicated /read landing page — the homepage hosts the
        # 114-surah list directly. Two ListItems with the same URL is
        # a Schema.org smell that some search engines warn about.
        ld_blocks.append({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "al-nuqta", "item": SITE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": crumb_label, "item": canonical},
            ],
        })
        # Mention the surah number explicitly via aria-style data —
        # Article doesn't have a built-in "chapter number" field, so we
        # tuck it into the description if missing. (Already in title.)
        if surah_num:
            ld_blocks[0]["position"] = surah_num
    else:
        ld_blocks.append({
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
        })
    for block in ld_blocks:
        ld_json = json.dumps(block, ensure_ascii=False).replace("<", "\\u003c")
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
    _add(SITE_URL + "/privacy", "0.3")
    _add(SITE_URL + "/terms", "0.3")
    _add(SITE_URL + "/privacy/extension", "0.3")
    _add(SITE_URL + "/grammar-glossary", "0.6")
    _add(SITE_URL + "/quran-vocabulary", "0.6")
    _add(SITE_URL + "/dictionary", "0.7")

    # All 114 surah reader pages — high priority because they're the
    # main entry points users land on for "read Surah X" searches.
    # /read/<n> only — verse-anchor variants (/read/<n>:<v>) share
    # the same canonical and shouldn't be re-listed.
    for surah_num in range(1, 115):
        _add(f"{SITE_URL}/read/{surah_num}", "0.8")

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
            # Match the space-stripped root letters ("ص ب ر" -> "صبر") first —
            # that's what a user typing root letters on a root explorer wants —
            # then fall back to exact (diacritized) surface/lemma substrings.
            rows = conn.execute(
                "SELECT DISTINCT root_buckwalter, root_arabic FROM morphology "
                "WHERE (REPLACE(root_arabic, ' ', '') LIKE ? "
                "       OR form_arabic LIKE ? OR lemma_arabic LIKE ?) "
                "AND root_buckwalter IS NOT NULL AND root_buckwalter != '' "
                "LIMIT 20",
                (f"%{q}%", f"%{q}%", f"%{q}%"),
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
                    meaning = _clean_root_gloss(ai_row["primary_meaning"]) or ""
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

# "Remember me" token lifetime. When the operator ticks the box on the
# login form, we issue a long-lived token instead of the 24h default so
# the session survives browser restarts and isn't dropped after a day.
_ADMIN_JWT_REMEMBER_DAYS = 30

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


# admin_required must be defined BEFORE any @admin_required-decorated
# route, because Python evaluates decorators at module-import time.
# Adding a route between this point and the original definition (which
# used to live further down the file) was a recurring source of
# import-time crashes — fixed by moving the definition up here, right
# after admin_users is created (which is what the decorator reads
# from). Don't move it back down, and don't add new helpers here that
# admin_required depends on without checking import order.
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Bearer header is the primary path. Fall back to a `?token=`
        # query-string for cases where the browser can't set headers
        # — chiefly, <video> / <audio> / <a target="_blank"> tags
        # that need to authenticate a binary GET. Same JWT, same
        # validation downstream, so the security model is unchanged.
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif request.args.get("token"):
            token = request.args["token"]
        else:
            return jsonify({"error": "Missing token"}), 401
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


# ---------------------------------------------------------------------------
# Ask the Quran — admin moderation of the shared Q&A
#
# Every answer the assistant gives is saved to assistant_conversations and
# then shown to all later visitors of that verse/word/root. These endpoints
# let an admin review what's been asked and answered across the whole site,
# correct or hide low-quality answers, and purge spam. Defined right after
# admin_required so the decorator exists at import time.
# ---------------------------------------------------------------------------

# Whitelisted sort modes -> ORDER BY fragment. User input is mapped through
# this dict, never interpolated into SQL. "slowest" pushes NULL response
# times last without relying on the (newer) NULLS LAST syntax.
_QA_SORT_SQL = {
    "recent": "created_at DESC, id DESC",
    "oldest": "created_at ASC, id ASC",
    "slowest": "(response_time_ms IS NULL) ASC, response_time_ms DESC, created_at DESC",
    "longest": "LENGTH(answer) DESC, created_at DESC",
}


def _qa_row_to_dict(row):
    """Shape a DB row for the admin client: drop the raw session id (only a
    short prefix is surfaced as a rough 'same person' hint), coerce hidden
    to a real bool."""
    d = dict(row)
    sid = d.pop("session_id", "") or ""
    d["session_short"] = sid[:8]
    d["hidden"] = bool(d.get("hidden"))
    # generation_meta is stored as a JSON string on AI drafts; hand the client
    # a parsed object (source_notes, cited_refs, flags) when present.
    gm = d.get("generation_meta")
    if gm:
        try:
            import json as _json
            d["generation_meta"] = _json.loads(gm)
        except Exception:
            pass
    return d


_QA_ADMIN_COLUMNS = (
    "id, session_id, page_type, page_key, question, answer, "
    "context_summary, model_used, response_time_ms, created_at, "
    "context_range, COALESCE(hidden, 0) AS hidden, edited_at, "
    "COALESCE(source, 'user') AS source, review_status, category, "
    "quality_score, generation_meta"
)


@app.route("/api/admin/assistant/qa", methods=["GET"])
@admin_required
def admin_list_assistant_qa():
    """Paginated, searchable, filterable list of saved Q&A threads."""
    q = (request.args.get("q") or "").strip()
    page_type = (request.args.get("page_type") or "").strip()
    model = (request.args.get("model") or "").strip()
    source = (request.args.get("source") or "").strip()           # 'user' | 'ai'
    review_status = (request.args.get("review_status") or "").strip()  # pending|approved|rejected
    score = (request.args.get("score") or "").strip()             # 1-5 quality grade
    status = (request.args.get("status") or "all").strip()
    sort = (request.args.get("sort") or "recent").strip()
    order_by = _QA_SORT_SQL.get(sort, _QA_SORT_SQL["recent"])

    try:
        limit = min(max(int(request.args.get("limit", 25)), 1), 100)
    except (ValueError, TypeError):
        limit = 25
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    where, params = [], []
    if q:
        where.append("(question LIKE ? OR answer LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like])
    if page_type:
        where.append("page_type = ?")
        params.append(page_type)
    if model:
        where.append("model_used = ?")
        params.append(model)
    if source:
        where.append("COALESCE(source, 'user') = ?")
        params.append(source)
    if review_status:
        where.append("review_status = ?")
        params.append(review_status)
    if score:
        try:
            where.append("CAST(quality_score AS INT) = ?")
            params.append(int(score))
        except (ValueError, TypeError):
            pass
    if status == "visible":
        where.append("COALESCE(hidden, 0) = 0")
    elif status == "hidden":
        where.append("COALESCE(hidden, 0) = 1")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM assistant_conversations {where_sql}",
            params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT {_QA_ADMIN_COLUMNS} FROM assistant_conversations "
            f"{where_sql} ORDER BY {order_by} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return jsonify({
            "items": [_qa_row_to_dict(r) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    finally:
        conn.close()


@app.route("/api/admin/assistant/qa/stats", methods=["GET"])
@admin_required
def admin_assistant_qa_stats():
    """At-a-glance totals for the Ask-the-Quran admin section."""
    conn = get_db()
    try:
        def scalar(sql):
            return conn.execute(sql).fetchone()["c"]

        total = scalar("SELECT COUNT(*) AS c FROM assistant_conversations")
        hidden = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE COALESCE(hidden, 0) = 1"
        )
        pages = scalar(
            "SELECT COUNT(DISTINCT page_type || '|' || page_key) AS c "
            "FROM assistant_conversations"
        )
        sessions = scalar(
            "SELECT COUNT(DISTINCT session_id) AS c FROM assistant_conversations"
        )
        last7 = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE created_at > datetime('now', '-7 days')"
        )
        last24 = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE created_at > datetime('now', '-1 day')"
        )
        edited = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE edited_at IS NOT NULL"
        )
        ai_total = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE COALESCE(source, 'user') = 'ai'"
        )
        ai_pending = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE source = 'ai' AND review_status = 'pending'"
        )
        ai_approved = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE source = 'ai' AND review_status = 'approved'"
        )
        ai_rejected = scalar(
            "SELECT COUNT(*) AS c FROM assistant_conversations "
            "WHERE source = 'ai' AND review_status = 'rejected'"
        )
        by_type = [dict(r) for r in conn.execute(
            "SELECT page_type, COUNT(*) AS count FROM assistant_conversations "
            "GROUP BY page_type ORDER BY count DESC"
        ).fetchall()]
        by_model = [dict(r) for r in conn.execute(
            "SELECT COALESCE(NULLIF(model_used, ''), 'unknown') AS model, "
            "       COUNT(*) AS count FROM assistant_conversations "
            "GROUP BY model ORDER BY count DESC"
        ).fetchall()]
        # Quality-score distribution across the AI-drafted Q&A (the only rows
        # that carry a 1–5 grade). Bucketed by integer score.
        by_score = [dict(r) for r in conn.execute(
            "SELECT CAST(quality_score AS INT) AS score, COUNT(*) AS count "
            "FROM assistant_conversations "
            "WHERE source = 'ai' AND quality_score IS NOT NULL "
            "GROUP BY score ORDER BY score"
        ).fetchall()]
        top_pages = [dict(r) for r in conn.execute(
            "SELECT page_type, page_key, COUNT(*) AS count "
            "FROM assistant_conversations "
            "GROUP BY page_type, page_key "
            "ORDER BY count DESC, MAX(created_at) DESC LIMIT 10"
        ).fetchall()]
        return jsonify({
            "total": total,
            "hidden": hidden,
            "visible": total - hidden,
            "edited": edited,
            "ai_total": ai_total,
            "ai_pending": ai_pending,
            "ai_approved": ai_approved,
            "ai_rejected": ai_rejected,
            "pages": pages,
            "sessions": sessions,
            "last_7_days": last7,
            "last_24_hours": last24,
            "by_type": by_type,
            "by_model": by_model,
            "by_score": by_score,
            "top_pages": top_pages,
        })
    finally:
        conn.close()


@app.route("/api/admin/assistant/qa/<int:qa_id>", methods=["PATCH"])
@admin_required
def admin_update_assistant_qa(qa_id):
    """Hide/unhide, or correct the stored question/answer of one Q&A."""
    data = request.get_json(force=True) or {}
    sets, params, edited = [], [], False

    if "hidden" in data:
        sets.append("hidden = ?")
        params.append(1 if data.get("hidden") else 0)

    if "review_status" in data:
        rs = data.get("review_status")
        if rs not in ("pending", "approved", "rejected", None):
            return jsonify({"error": "review_status must be pending/approved/rejected"}), 400
        sets.append("review_status = ?")
        params.append(rs)

    if "answer" in data:
        answer = data.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            return jsonify({"error": "answer must be a non-empty string"}), 400
        sets.append("answer = ?")
        params.append(answer.strip()[:50000])
        edited = True

    if "question" in data:
        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "question must be a non-empty string"}), 400
        # Same injection scrub the public save path applies.
        question = re.sub(r"<[^>]*>", "", question)
        question = re.sub(r"javascript\s*:", "", question, flags=re.IGNORECASE)
        question = re.sub(r"on\w+\s*=", "", question, flags=re.IGNORECASE)
        sets.append("question = ?")
        params.append(question.strip()[:500])
        edited = True

    if not sets:
        return jsonify({"error": "No updatable fields provided"}), 400
    if edited:
        sets.append("edited_at = datetime('now')")

    conn = get_db()
    try:
        cur = conn.execute(
            f"UPDATE assistant_conversations SET {', '.join(sets)} WHERE id = ?",
            params + [qa_id],
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Q&A not found"}), 404
        row = conn.execute(
            f"SELECT {_QA_ADMIN_COLUMNS} FROM assistant_conversations WHERE id = ?",
            (qa_id,),
        ).fetchone()
        return jsonify({"ok": True, "item": _qa_row_to_dict(row)})
    finally:
        conn.close()


@app.route("/api/admin/assistant/qa/<int:qa_id>", methods=["DELETE"])
@admin_required
def admin_delete_assistant_qa(qa_id):
    """Permanently remove one saved Q&A (use hide for reversible removal)."""
    conn = get_db()
    try:
        cur = conn.execute(
            "DELETE FROM assistant_conversations WHERE id = ?", (qa_id,)
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Q&A not found"}), 404
        return jsonify({"ok": True, "deleted": qa_id})
    finally:
        conn.close()


@app.route("/api/admin/assistant/qa/bulk", methods=["POST"])
@admin_required
def admin_bulk_assistant_qa():
    """Bulk moderation for the review queue: approve / reject / pending /
    hide / unhide / delete many rows in one call."""
    data = request.get_json(force=True) or {}
    raw_ids = data.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return jsonify({"error": "ids must be a non-empty list"}), 400
    ids = [int(i) for i in raw_ids if str(i).isdigit()][:500]
    if not ids:
        return jsonify({"error": "no valid ids"}), 400
    op = (data.get("op") or "").strip()
    placeholders = ",".join("?" * len(ids))

    conn = get_db()
    try:
        if op == "delete":
            cur = conn.execute(
                f"DELETE FROM assistant_conversations WHERE id IN ({placeholders})", ids)
        elif op in ("approve", "reject", "pending"):
            rs = {"approve": "approved", "reject": "rejected", "pending": "pending"}[op]
            cur = conn.execute(
                f"UPDATE assistant_conversations SET review_status = ? "
                f"WHERE id IN ({placeholders})", [rs] + ids)
        elif op in ("hide", "unhide"):
            cur = conn.execute(
                f"UPDATE assistant_conversations SET hidden = ? "
                f"WHERE id IN ({placeholders})", [1 if op == "hide" else 0] + ids)
        else:
            return jsonify({"error": "op must be approve/reject/pending/hide/unhide/delete"}), 400
        conn.commit()
        return jsonify({"ok": True, "op": op, "affected": cur.rowcount})
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Verse exegesis — teacher-voice commentary distilled from grade-3/4 Q&A,
# shown at the bottom of a verse's translation notes. Admin-reviewed
# (pending -> approved/rejected) before anything reaches the public verse.
# ----------------------------------------------------------------------------

def _ensure_exegesis_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verse_exegesis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            page_key TEXT NOT NULL,
            exegesis_markdown TEXT NOT NULL,
            source_gem_ids TEXT,
            source_scores TEXT,
            model_used TEXT,
            review_status TEXT DEFAULT 'pending',
            hidden INTEGER DEFAULT 0,
            template_version TEXT,
            generation_meta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            edited_at TEXT,
            UNIQUE(chapter, verse)
        )
    """)
    conn.commit()


_EXEG_SORT_SQL = {
    "recent": "created_at DESC, id DESC",
    "oldest": "created_at ASC, id ASC",
    "verse": "chapter ASC, verse ASC",
    "longest": "LENGTH(exegesis_markdown) DESC, created_at DESC",
}

_EXEG_COLUMNS = (
    "id, chapter, verse, page_key, exegesis_markdown, source_gem_ids, "
    "source_scores, model_used, review_status, COALESCE(hidden, 0) AS hidden, "
    "template_version, generation_meta, created_at, edited_at"
)


def _exeg_row_to_dict(row):
    d = dict(row)
    d["hidden"] = bool(d.get("hidden"))
    for k in ("source_gem_ids", "source_scores", "generation_meta"):
        v = d.get(k)
        if v:
            try:
                d[k] = json.loads(v)
            except Exception:
                pass
    return d


@app.route("/api/verse/<int:surah>:<int:ayah>/exegesis")
def get_verse_exegesis(surah: int, ayah: int):
    """Public: the approved, non-hidden exegesis note for a verse, or 404.

    Only review_status='approved' rows that aren't hidden reach the public
    verse page; everything else stays gated in /admin/exegesis. The body is
    raw markdown — the client linkifies verse refs / roots / Arabic exactly
    as it does for the Ask-the-Quran answers (FormattedText / VerseRefText).
    """
    conn = get_db()
    try:
        _ensure_exegesis_table(conn)
        row = conn.execute(
            "SELECT exegesis_markdown, source_scores, created_at, edited_at "
            "FROM verse_exegesis "
            "WHERE chapter = ? AND verse = ? "
            "  AND review_status = 'approved' AND COALESCE(hidden, 0) = 0 "
            "LIMIT 1",
            (surah, ayah),
        ).fetchone()
        if not row:
            return jsonify({"error": "No exegesis available"}), 404
        scores = row["source_scores"]
        if scores:
            try:
                scores = json.loads(scores)
            except Exception:
                scores = None
        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "exegesis_markdown": row["exegesis_markdown"],
            "source_scores": scores,
            "word_anchors": _fetch_word_anchors(conn, surah, ayah),
            "created_at": row["created_at"],
            "edited_at": row["edited_at"],
        })
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# Pre-Islamic poetry comparison — root-level "In Pre-Islamic Poetry" section
# and the verse-level note shown below the exegesis. Generated by
# poetry_gen.py, admin-reviewed (pending -> approved) before public display.
# Tables live in the same DB (synced to prod like verse_exegesis).
# ----------------------------------------------------------------------------

# ---- Meter (baḥr) registry --------------------------------------------------
# The corpus stores meter as a raw Arabic string (poetry_poems.meter). Most
# values are truncated variants (مجزوء = halved, أحذ/مخلع/مشطور = clipped) of a
# small set of base meters. We surface ONE page per base meter, keyed by a Latin
# slug; every variant string folds into its base. Order = teaching priority
# (most frequent first). name_en/meaning here are sensible defaults; an approved
# meter_articles row overrides them for display.
METER_REGISTRY = [
    {"key": "tawil", "ar": "الطويل", "en": "Ṭawīl", "meaning": "the long",
     "variants": ["مجزوء الطويل"]},
    {"key": "wafir", "ar": "الوافر", "en": "Wāfir", "meaning": "the abundant",
     "variants": ["مجزوء الوافر"]},
    {"key": "basit", "ar": "البسيط", "en": "Basīṭ", "meaning": "the outspread",
     "variants": ["مجزوء البسيط", "مخلع البسيط"]},
    {"key": "kamil", "ar": "الكامل", "en": "Kāmil", "meaning": "the complete",
     "variants": ["مجزوء الكامل", "أحذ الكامل"]},
    {"key": "mutaqarib", "ar": "المتقارب", "en": "Mutaqārib", "meaning": "the nearing",
     "variants": []},
    {"key": "khafif", "ar": "الخفيف", "en": "Khafīf", "meaning": "the light",
     "variants": ["مجزوء الخفيف"]},
    {"key": "rajaz", "ar": "الرجز", "en": "Rajaz", "meaning": "the quivering",
     "variants": ["مجزوء الرجز", "مشطور الرجز"]},
    {"key": "ramal", "ar": "الرمل", "en": "Ramal", "meaning": "the trotting",
     "variants": ["مجزوء الرمل"]},
    {"key": "sari", "ar": "السريع", "en": "Sarīʿ", "meaning": "the swift",
     "variants": []},
    {"key": "munsarih", "ar": "المنسرح", "en": "Munsariḥ", "meaning": "the flowing",
     "variants": []},
    {"key": "madid", "ar": "المديد", "en": "Madīd", "meaning": "the outstretched",
     "variants": []},
    {"key": "hazaj", "ar": "الهزج", "en": "Hazaj", "meaning": "the lilting",
     "variants": []},
    {"key": "mujtathth", "ar": "المجتث", "en": "Mujtathth", "meaning": "the uprooted",
     "variants": []},
]
_METER_BY_KEY = {m["key"]: m for m in METER_REGISTRY}
# Every raw meter string (base + variants) -> base entry.
_METER_VALUE_TO_BASE = {}
for _m in METER_REGISTRY:
    _METER_VALUE_TO_BASE[_m["ar"]] = _m
    for _v in _m["variants"]:
        _METER_VALUE_TO_BASE[_v] = _m


def _meter_base_for(meter_value):
    """Map a raw poetry_poems.meter string to its base registry entry, or None."""
    if not meter_value:
        return None
    return _METER_VALUE_TO_BASE.get(meter_value.strip())


def _meter_all_values(entry):
    """Every raw meter string that folds into this base (base name + variants)."""
    return [entry["ar"], *entry["variants"]]


def _ensure_meter_articles_table(conn):
    """Idempotent: the read table for per-meter teaching pages. One row per base
    meter (keyed by Latin slug). article_markdown holds the prose; the machine
    fields (tafil/syllable_pattern/mnemonic) drive the rhythm player; showcase_json
    holds chosen example lines with transliteration + scansion."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meter_articles (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_key        TEXT UNIQUE NOT NULL,
            meter_ar         TEXT,
            name_en          TEXT,
            name_meaning     TEXT,
            tafil_ar         TEXT,
            tafil_latin      TEXT,
            syllable_pattern TEXT,
            mnemonic_en      TEXT,
            article_markdown TEXT,
            showcase_json    TEXT,
            variants_json    TEXT,
            confidence       REAL,
            qa_status        TEXT,
            qa_notes         TEXT,
            review_status    TEXT DEFAULT 'pending',
            hidden           INTEGER DEFAULT 0,
            raw_response     TEXT,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
            edited_at        TEXT
        );
    """)
    conn.commit()


def _ensure_poetry_serve_tables(conn):
    """Idempotent: the read tables for the poetry comparison feature. No-op
    when poetry_gen.py / a prod sync already created them with their full
    column set (CREATE IF NOT EXISTS never alters an existing table)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS root_poetry_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_buckwalter TEXT NOT NULL UNIQUE,
            root_arabic TEXT, shift_type TEXT, comparison_markdown TEXT,
            quran_usage_summary TEXT, poetry_usage_summary TEXT,
            quoted_lines_json TEXT, collocations_json TEXT,
            continuity INTEGER DEFAULT 0, confidence REAL, auth_tier_max TEXT,
            review_status TEXT DEFAULT 'pending', hidden INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, edited_at TEXT
        );
        CREATE TABLE IF NOT EXISTS verse_poetry_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL, verse INTEGER NOT NULL, page_key TEXT,
            focus_root_buckwalter TEXT, note_markdown TEXT,
            quoted_lines_json TEXT, continuity INTEGER DEFAULT 0,
            confidence REAL, auth_tier_max TEXT,
            review_status TEXT DEFAULT 'pending', hidden INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, edited_at TEXT,
            UNIQUE(chapter, verse)
        );
    """)
    conn.commit()
    _ensure_lexicon_table(conn)
    _ensure_meter_articles_table(conn)
    _ensure_qa_videos_table(conn)


def _ensure_qa_videos_table(conn):
    """Idempotent: the Q&A video script-bank table. The schema is owned by
    qa_video_pipeline.py (import-safe module, no app import); reusing it
    here means prod gets the table on deploy and the two never drift."""
    import qa_video_pipeline as _qa_pipe
    _qa_pipe.ensure_tables(conn)


def _poetry_quoted(conn, raw):
    """Parse a quoted_lines_json blob and enrich each entry with poem_id +
    line_no (so the client can deep-link to /poem/<id>). Tier labels are
    intentionally NOT surfaced to readers."""
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except Exception:
        return []
    for q in items:
        q.pop("auth_tier", None)  # never expose tier to readers
        # Prefer an embedded poem_id/line_no (self-contained data, like the
        # lexicon's) so the deep-link never depends on poetry_line_roots being
        # complete in this environment. Only fall back to a live lookup when
        # the embedded values are missing.
        if q.get("poem_id") is None:
            lrid = q.get("line_root_id")
            if lrid:
                loc = conn.execute(
                    "SELECT pl.poem_id, pl.line_no FROM poetry_line_roots plr "
                    "JOIN poetry_lines pl ON pl.id = plr.line_id WHERE plr.id = ?",
                    (lrid,)).fetchone()
                if loc:
                    q["poem_id"] = loc["poem_id"]
                    q["line_no"] = loc["line_no"]
    return items


def _approved_quoted_lrids(conn) -> set:
    """line_root_ids quoted by any APPROVED comparison, verse note, or lexicon
    entry (used to flag which lines to highlight on a poem page)."""
    lrids = set()
    for tbl in ("root_poetry_comparisons", "verse_poetry_notes", "root_poetic_lexicon"):
        try:
            for r in conn.execute(
                    f"SELECT quoted_lines_json FROM {tbl} "
                    "WHERE review_status='approved' AND quoted_lines_json IS NOT NULL"):
                try:
                    for q in json.loads(r["quoted_lines_json"]):
                        if q.get("line_root_id"):
                            lrids.add(q["line_root_id"])
                except Exception:
                    pass
        except Exception:
            pass
    return lrids


def _quoted_poem_ids(conn) -> set:
    """Poem ids referenced by any approved comparison, verse note, or lexicon
    quote. Prefers the embedded poem_id (self-contained) and falls back to a
    poetry_line_roots lookup for any quote that lacks one."""
    pids = set()
    need_lrids = set()
    for tbl in ("root_poetry_comparisons", "verse_poetry_notes", "root_poetic_lexicon"):
        try:
            for r in conn.execute(
                    f"SELECT quoted_lines_json FROM {tbl} "
                    "WHERE review_status='approved' AND quoted_lines_json IS NOT NULL"):
                try:
                    for q in json.loads(r["quoted_lines_json"]):
                        if q.get("poem_id") is not None:
                            pids.add(int(q["poem_id"]))
                        elif q.get("line_root_id"):
                            need_lrids.add(q["line_root_id"])
                except Exception:
                    pass
        except Exception:
            pass
    if need_lrids:
        qmarks = ",".join("?" * len(need_lrids))
        for r in conn.execute(
                f"""SELECT DISTINCT pl.poem_id FROM poetry_line_roots plr
                    JOIN poetry_lines pl ON pl.id = plr.line_id
                    WHERE plr.id IN ({qmarks})""", list(need_lrids)).fetchall():
            pids.add(r["poem_id"])
    return pids


@app.route("/api/poems")
def list_poems():
    """The browsable library: every poem our approved comparisons draw on."""
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        pids = _quoted_poem_ids(conn)
        if not pids:
            return jsonify({"poems": []})
        qmarks = ",".join("?" * len(pids))
        rows = conn.execute(
            f"""SELECT pp.id, pp.poet, pp.poet_latin, pp.title, pp.title_en, pp.meter, pp.era,
                   (SELECT COUNT(*) FROM poetry_lines WHERE poem_id = pp.id) AS line_count,
                   (SELECT COUNT(*) FROM poetry_lines WHERE poem_id = pp.id
                      AND translation_en IS NOT NULL AND translation_en != '') AS translated_count
                FROM poetry_poems pp WHERE pp.id IN ({qmarks})
                ORDER BY pp.poet, pp.id""", list(pids)).fetchall()
        return jsonify({"poems": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route("/api/poem/<int:poem_id>")
def get_poem(poem_id: int):
    """A single poem: metadata + every line (Arabic + English as available),
    with the lines our notes quote flagged for highlighting."""
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        p = conn.execute(
            "SELECT id, poet, poet_latin, title, title_en, meter, rhyme, era "
            "FROM poetry_poems WHERE id = ?", (poem_id,)).fetchone()
        if not p:
            return jsonify({"error": "Poem not found"}), 404
        lines = conn.execute(
            "SELECT line_no, hemistich1, hemistich2, text_plain, translation_en "
            "FROM poetry_lines WHERE poem_id = ? ORDER BY line_no", (poem_id,)).fetchall()
        quoted_line_nos = set()
        lrids = _approved_quoted_lrids(conn)
        if lrids:
            qmarks = ",".join("?" * len(lrids))
            for r in conn.execute(
                    f"SELECT pl.line_no FROM poetry_line_roots plr "
                    "JOIN poetry_lines pl ON pl.id = plr.line_id "
                    f"WHERE plr.id IN ({qmarks}) AND pl.poem_id = ?", (*lrids, poem_id)):
                quoted_line_nos.add(r["line_no"])
        # link the metre to its teaching page + a hover beat-preview, if approved
        meter_key, meter_beat = None, None
        base = _meter_base_for(p["meter"])
        if base:
            meter_key = base["key"]
            _ensure_meter_articles_table(conn)
            ma = conn.execute(
                "SELECT name_en, name_meaning, tafil_latin, syllable_pattern, mnemonic_en "
                "FROM meter_articles WHERE meter_key = ? AND review_status = 'approved' "
                "AND COALESCE(hidden,0) = 0 LIMIT 1", (base["key"],)).fetchone()
            if ma and (ma["syllable_pattern"] or "").strip():
                meter_beat = {
                    "name_en": ma["name_en"] or base["en"],
                    "name_meaning": ma["name_meaning"] or base.get("meaning"),
                    "tafil_latin": ma["tafil_latin"],
                    "syllable_pattern": ma["syllable_pattern"],
                    "mnemonic_en": ma["mnemonic_en"],
                }
        return jsonify({
            "id": p["id"], "poet": p["poet"], "poet_latin": p["poet_latin"],
            "title": p["title"], "title_en": p["title_en"],
            "meter": p["meter"], "rhyme": p["rhyme"], "era": p["era"],
            "meter_key": meter_key, "meter_beat": meter_beat,
            "line_count": len(lines),
            "translated_count": sum(1 for ln in lines if (ln["translation_en"] or "").strip()),
            "lines": [{
                "line_no": ln["line_no"],
                "arabic": ln["text_plain"] or " ".join(
                    x for x in [ln["hemistich1"], ln["hemistich2"]] if x),
                "english": ln["translation_en"],
                "quoted": ln["line_no"] in quoted_line_nos,
            } for ln in lines],
        })
    finally:
        conn.close()


@app.route("/api/root/<root_bw>/poetry")
def get_root_poetry(root_bw: str):
    """Public: the approved, non-hidden root-level poetry comparison, or 404."""
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        row = conn.execute(
            "SELECT root_arabic, shift_type, comparison_markdown, quran_usage_summary, "
            "poetry_usage_summary, quoted_lines_json, collocations_json, "
            "COALESCE(continuity,0) AS continuity, confidence, auth_tier_max, created_at "
            "FROM root_poetry_comparisons "
            "WHERE root_buckwalter = ? AND review_status = 'approved' "
            "  AND COALESCE(hidden,0) = 0 LIMIT 1",
            (root_bw,)).fetchone()
        if not row:
            return jsonify({"error": "No poetry comparison available"}), 404
        collocations = None
        if row["collocations_json"]:
            try:
                collocations = json.loads(row["collocations_json"])
            except Exception:
                collocations = None
        return jsonify({
            "root_buckwalter": root_bw,
            "root_arabic": row["root_arabic"],
            "shift_type": row["shift_type"],
            "comparison_markdown": row["comparison_markdown"],
            "quran_usage_summary": row["quran_usage_summary"],
            "poetry_usage_summary": row["poetry_usage_summary"],
            "quoted_lines": _poetry_quoted(conn, row["quoted_lines_json"]),
            "collocations": collocations,
            "continuity": bool(row["continuity"]),
            "confidence": row["confidence"],
            "auth_tier_max": row["auth_tier_max"],
            "created_at": row["created_at"],
        })
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/poetry")
def get_verse_poetry(surah: int, ayah: int):
    """Public: the approved, non-hidden verse-level poetry note, or 404."""
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        row = conn.execute(
            "SELECT focus_root_buckwalter, note_markdown, quoted_lines_json, "
            "COALESCE(continuity,0) AS continuity, confidence, auth_tier_max, created_at "
            "FROM verse_poetry_notes "
            "WHERE chapter = ? AND verse = ? AND review_status = 'approved' "
            "  AND COALESCE(hidden,0) = 0 LIMIT 1",
            (surah, ayah)).fetchone()
        if not row:
            return jsonify({"error": "No poetry note available"}), 404
        return jsonify({
            "surah": surah, "ayah": ayah,
            "focus_root_buckwalter": row["focus_root_buckwalter"],
            "note_markdown": row["note_markdown"],
            "quoted_lines": _poetry_quoted(conn, row["quoted_lines_json"]),
            "continuity": bool(row["continuity"]),
            "confidence": row["confidence"],
            "auth_tier_max": row["auth_tier_max"],
            "created_at": row["created_at"],
        })
    finally:
        conn.close()


def _ensure_lexicon_table(conn):
    """Idempotent: the read table for the per-root contemporaneous-attestation
    lexicon (what a Qur'anic root is attested to mean in authenticated 6th-c.
    poetry). Quran-only meaning: shows the evidence, never imports a codified
    definition."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS root_poetic_lexicon (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            root_buckwalter      TEXT UNIQUE NOT NULL,
            root_arabic          TEXT,
            attested_senses_json TEXT,
            poetry_occurrences   INTEGER DEFAULT 0,
            poetry_tier_max      TEXT,
            attestation_strength TEXT,
            quran_internal_summary TEXT,
            quran_occurrences    INTEGER DEFAULT 0,
            lexicon_markdown     TEXT,
            relation_to_quran    TEXT,
            quoted_lines_json    TEXT,
            lexical_basis        TEXT,
            counter_search       TEXT,
            adversarial_report   TEXT,
            confidence           REAL,
            review_status        TEXT DEFAULT 'pending',
            hidden               INTEGER DEFAULT 0,
            raw_response         TEXT,
            created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at           TEXT,
            edited_at            TEXT
        );
    """)
    conn.commit()


def _lexicon_public(conn, row):
    """Reader-facing shape of a lexicon entry. Tier labels stay internal."""
    try:
        senses = json.loads(row["attested_senses_json"] or "[]")
    except Exception:
        senses = []
    for s in senses:
        s.pop("tier_max", None)  # evidence strength is summarised, not tiered to readers
    return {
        "root_arabic": row["root_arabic"],
        "attested_senses": senses,
        "attestation_strength": row["attestation_strength"],
        "poetry_occurrences": row["poetry_occurrences"],
        "quran_internal_summary": row["quran_internal_summary"],
        "lexicon_markdown": row["lexicon_markdown"],
        "relation_to_quran": row["relation_to_quran"],
        "quoted_lines": _poetry_quoted(conn, row["quoted_lines_json"]),
        "confidence": row["confidence"],
    }


@app.route("/api/root/<root_bw>/lexicon")
def get_root_lexicon(root_bw: str):
    """Public: the approved contemporaneous-attestation lexicon entry, or 404."""
    conn = get_db()
    try:
        _ensure_lexicon_table(conn)
        row = conn.execute(
            "SELECT * FROM root_poetic_lexicon WHERE root_buckwalter = ? "
            "AND review_status = 'approved' AND COALESCE(hidden,0) = 0 LIMIT 1",
            (root_bw,)).fetchone()
        if not row:
            return jsonify({"error": "No lexicon entry"}), 404
        out = _lexicon_public(conn, row)
        out["root_buckwalter"] = root_bw
        return jsonify(out)
    finally:
        conn.close()


@app.route("/api/verse/<int:surah>:<int:ayah>/root-lexicon")
def get_verse_root_lexicon(surah: int, ayah: int):
    """Public: for each content word of the verse, its root and (if approved)
    the contemporaneous-attestation lexicon entry — so a Qur'an-only reader can
    see, word by word, what each root is attested to mean in 6th-century usage."""
    conn = get_db()
    try:
        _ensure_lexicon_table(conn)
        words = conn.execute(
            "SELECT word_pos, MAX(form_arabic) AS form_arabic, "
            "root_buckwalter, root_arabic "
            "FROM morphology WHERE chapter = ? AND verse = ? "
            "AND root_buckwalter IS NOT NULL AND root_buckwalter <> '' "
            "GROUP BY word_pos, root_buckwalter ORDER BY word_pos",
            (surah, ayah)).fetchall()
        out = []
        for w in words:
            rb = w["root_buckwalter"]
            lex = conn.execute(
                "SELECT * FROM root_poetic_lexicon WHERE root_buckwalter = ? "
                "AND review_status = 'approved' AND COALESCE(hidden,0) = 0 LIMIT 1",
                (rb,)).fetchone()
            out.append({
                "word_pos": w["word_pos"],
                "word_arabic": w["form_arabic"],
                "root_buckwalter": rb,
                "root_arabic": w["root_arabic"],
                "lexicon": _lexicon_public(conn, lex) if lex else None,
            })
        return jsonify({"surah": surah, "ayah": ayah, "words": out})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# The Lexicon Library — harmonized classical-dictionary root definitions.
# One page per root aggregating each dictionary's entry (date-ordered), sourced
# respectfully from arabiclexicon.hawramani.com, harmonized to readable English
# with the original Arabic + a faithful translation one click away. Buckwalter-
# keyed; review_status/hidden gate public reads (approved AND NOT hidden).
# ---------------------------------------------------------------------------
def _fetch_word_anchors(conn, surah: int, ayah: int, source: str = 'exegesis'):
    """Citations inside this verse's note that quote the verse itself, mapped to
    the word range they quote, so the client can highlight those words on hover.

    `source` selects which note body the anchors were resolved against —
    'exegesis' or 'translation_notes'. They are kept apart because a span is
    matched by its literal text, and the same phrase can be cited in one note
    and not the other.

    Built offline by align_note_anchors.py. Returns [] when the table has not
    been synced yet — the note then renders as ordinary prose.
    """
    try:
        rows = conn.execute(
            "SELECT span_text, script, word_start, word_end FROM note_word_anchors "
            "WHERE chapter = ? AND verse = ? AND source = ?",
            (surah, ayah, source),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        {"span": r["span_text"], "script": r["script"],
         "start": r["word_start"], "end": r["word_end"]}
        for r in rows
    ]


def _ensure_word_translit_table(conn):
    """Self-heal `word_translit` (prod before its first sync).

    Per-word romanization + normalised match keys, derived deterministically
    from `morphology` by build_word_translit.py. Used to resolve a
    transliterated or Arabic citation inside a note back to the exact word
    range of the verse, so hovering the citation can highlight those words.
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS word_translit (
        chapter INTEGER NOT NULL, verse INTEGER NOT NULL, word_pos INTEGER NOT NULL,
        translit TEXT NOT NULL, translit_key TEXT NOT NULL,
        arabic_plain TEXT NOT NULL, arabic_key TEXT NOT NULL,
        PRIMARY KEY (chapter, verse, word_pos)
    );
    CREATE INDEX IF NOT EXISTS idx_word_translit_key ON word_translit(translit_key);
    CREATE INDEX IF NOT EXISTS idx_word_translit_arkey ON word_translit(arabic_key);
    """)


# --- Citations inside prose written at request time ------------------------
# An Ask-the-Quran answer quotes the verse the reader is on exactly as the
# notes do ("ٱللَّهُ وَلِىُّ ٱلَّذِينَ ءَامَنُوا۟", *inna maʿa l-ʿusri yusran*), and the reader
# wants the same thing from it: hover the citation, see which words of the
# verse it means. The notes get that from align_note_anchors.py, which runs
# offline over the stored corpus — an answer doesn't exist yet when that runs,
# so the same rules are applied here on demand. Deterministic string alignment
# over `word_translit`; no model, no network, a few hundred microseconds.
_ALIGN_MOD = None
# Generous next to the ~7KB of answers a busy verse actually carries; a
# ceiling exists so an arbitrary POST body can't turn into arbitrary work.
_ALIGN_MAX_TEXT = 60000


def _align_module():
    """align_note_anchors, imported on first use (nothing else needs it)."""
    global _ALIGN_MOD
    if _ALIGN_MOD is None:
        import align_note_anchors
        _ALIGN_MOD = align_note_anchors
    return _ALIGN_MOD


@app.route("/api/verse/<int:surah>:<int:ayah>/align-quotes", methods=["POST"])
def align_quotes(surah: int, ayah: int):
    """Resolve the citations in the posted prose to word ranges of this verse.

    Body: {"text": "..."}. Returns the same shape the notes' stored anchors
    use, so the client can hand it straight to the renderer. Citations that
    quote some *other* verse, bare root forms and ordinary emphasis simply
    don't resolve and come back absent — they render as plain prose.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"anchors": []})

    align = _align_module()
    # The four verses where the corpus' word count and the rendered token
    # count disagree by one: an anchor there could light the wrong word.
    if (surah, ayah) in align.MISALIGNED:
        return jsonify({"anchors": []})

    conn = get_db()
    try:
        words = [
            (r["word_pos"], r["translit_key"], r["arabic_key"])
            for r in conn.execute(
                "SELECT word_pos, translit_key, arabic_key FROM word_translit "
                "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
                (surah, ayah),
            )
        ]
    except sqlite3.OperationalError:
        # Table not synced yet — citations stay ordinary prose, as with notes.
        return jsonify({"anchors": []})
    finally:
        conn.close()
    if not words:
        return jsonify({"anchors": []})

    anchors = []
    seen = set()
    for span, script in align.spans_in(text[:_ALIGN_MAX_TEXT]):
        if span in seen:          # the same phrase quoted more than once
            continue
        seen.add(span)
        rng = align.resolve(span, script, words)
        if rng:
            anchors.append(
                {"span": span, "script": script, "start": rng[0], "end": rng[1]}
            )
    return jsonify({"anchors": anchors})


def _ensure_dict_tables(conn):
    """Self-heal the Lexicon Library tables (prod before its first sync)."""
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS dictionaries (
        id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL,
        hawramani_category_id INTEGER, name_en TEXT, name_ar TEXT,
        author TEXT, author_death_year INTEGER, language TEXT,
        is_quran_specific INTEGER DEFAULT 0, phase INTEGER DEFAULT 1,
        sort_order INTEGER, description_en TEXT
    );
    CREATE TABLE IF NOT EXISTS dictionary_entries (
        id INTEGER PRIMARY KEY,
        root_buckwalter TEXT NOT NULL, root_arabic TEXT,
        dictionary_slug TEXT NOT NULL,
        original_text_ar TEXT, translation_en TEXT, harmonized_en TEXT,
        source_url TEXT, source_anchor TEXT, scrape_hash TEXT,
        review_status TEXT DEFAULT 'pending', hidden INTEGER DEFAULT 0,
        confidence REAL, gen_meta TEXT, raw_response TEXT,
        created_at TEXT DEFAULT (datetime('now')), edited_at TEXT,
        UNIQUE(root_buckwalter, dictionary_slug)
    );
    CREATE INDEX IF NOT EXISTS idx_dictentry_root ON dictionary_entries(root_buckwalter);
    """)
    conn.commit()


def _ejtaal_url(root_bw):
    """ejtaal.net keeps its external-reference link (Buckwalter root key)."""
    return "https://ejtaal.net/aa/#bwq=%s" % (root_bw or "")


def _dict_meta(r):
    return {
        "dictionary_slug": r["dictionary_slug"], "name_en": r["name_en"],
        "name_ar": r["name_ar"], "author": r["author"],
        "author_death_year": r["author_death_year"], "language": r["language"],
        "is_quran_specific": bool(r["is_quran_specific"]),
    }


# --- Which dictionary opens first ----------------------------------------
# The panel still LISTS the works chronologically (chronology is the method —
# see get_root_dictionaries), but the one expanded by default is whichever is
# most likely to answer "what does this root actually mean?" straight away.
# Ranked by how well each serves this site's method: meaning derived from the
# Qur'an's own usage and contemporaneous attestation, not later codification.
# Lower number opens first; anything unlisted falls to the end and is chosen
# chronologically among its peers.
_DICTIONARY_PRIORITY = {
    # Gives each root's single core principle (aṣl) rather than a list of
    # senses — usually the fastest route to what a root is really about.
    "ibn-faris-maqayis-al-lugha": 1,
    # The standard Qur'an-specific lexicon: defines words as the Qur'an uses them.
    "al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran": 2,
    # Earliest of all (d. 687) and grounds Qur'anic words in pre-Islamic
    # poetry — exactly the contemporaneous evidence this site leans on.
    "abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab": 3,
    # The first Arabic dictionary; the closest witness to 6th-century usage.
    "al-khalil-b-ahmad-al-farahidi-kitab-al-ain": 4,
    # Qur'an-specific gharīb work.
    "abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib": 5,
    # Separates literal from figurative usage, which the others often blur.
    "al-zamakhshari-asas-al-balagha": 6,
    # The great compendium — thorough, but long to read through.
    "ibn-manzur-lisan-al-arab": 7,
    # The most thorough English work, translated from the classical sources.
    "william-edward-lane-arabic-english-lexicon": 8,
    "ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya": 9,
    "ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam": 10,
    "firuzabadi-al-qamus-al-muhit": 11,
    "murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus": 12,
    "al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir": 13,
    "al-sahib-bin-abbad-al-muhit-fi-l-lugha": 14,
    "zayn-al-din-al-razi-mukhtar-al-sihah": 15,
    "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary": 16,
}
_DICTIONARY_PRIORITY_FALLBACK = 999


@app.route("/api/root/<root_bw>/dictionaries")
def get_root_dictionaries(root_bw: str):
    """Public View 1: the approved, harmonized dictionary definitions for a root,
    ordered by author death-year (chronology is the method). Empty list if none."""
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        rows = conn.execute(
            "SELECT e.id, e.root_arabic, e.dictionary_slug, e.harmonized_en, e.confidence, "
            "d.name_en, d.name_ar, d.author, d.author_death_year, d.language, d.is_quran_specific "
            "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
            "WHERE e.root_buckwalter = ? AND e.review_status = 'approved' "
            "AND COALESCE(e.hidden,0) = 0 AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> '' "
            "ORDER BY d.author_death_year ASC, d.sort_order ASC",
            (root_bw,)).fetchall()
        items = [{**_dict_meta(r), "entry_id": r["id"], "harmonized_en": r["harmonized_en"]}
                 for r in rows]
        # The list stays chronological; this only picks which entry starts
        # expanded — the highest-priority work this root actually has, with
        # ties falling to the oldest (rows are already in that order).
        default_entry_id = min(
            items,
            key=lambda it: _DICTIONARY_PRIORITY.get(
                it["dictionary_slug"], _DICTIONARY_PRIORITY_FALLBACK),
        )["entry_id"] if items else None
        return jsonify({
            "root_buckwalter": root_bw,
            "root_arabic": rows[0]["root_arabic"] if rows else None,
            "count": len(items), "dictionaries": items,
            "default_entry_id": default_entry_id,
            "ejtaal_url": _ejtaal_url(root_bw),
        })
    finally:
        conn.close()


@app.route("/api/dictionary-entry/<int:entry_id>")
def get_dictionary_entry(entry_id: int):
    """Public View 2: one entry's original Arabic + faithful translation + the
    harmonized text, with provenance links (hawramani + ejtaal)."""
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        r = conn.execute(
            "SELECT e.*, d.name_en, d.name_ar, d.author, d.author_death_year, "
            "d.language, d.is_quran_specific "
            "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
            "WHERE e.id = ? AND e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0",
            (entry_id,)).fetchone()
        if not r:
            return jsonify({"error": "Not found"}), 404
        return jsonify({
            **_dict_meta(r), "entry_id": r["id"],
            "root_buckwalter": r["root_buckwalter"], "root_arabic": r["root_arabic"],
            "original_text_ar": r["original_text_ar"], "translation_en": r["translation_en"],
            "harmonized_en": r["harmonized_en"], "source_url": r["source_url"],
            "ejtaal_url": _ejtaal_url(r["root_buckwalter"]),
        })
    finally:
        conn.close()


@app.route("/api/dictionary-roots")
def get_dictionary_roots():
    """Public index for the Qur'anic Dictionary page (/dictionary): every root
    that has at least one approved, visible harmonized entry, with a concise
    gloss (from ai_root_meanings) and its entry count. Ordered by the Arabic
    root so the frontend can group alphabetically by first radical."""
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        rows = conn.execute(
            "SELECT e.root_buckwalter, e.root_arabic, COUNT(*) AS entries, "
            "(SELECT m.primary_meaning FROM ai_root_meanings m "
            " WHERE m.root_buckwalter = e.root_buckwalter "
            "   AND m.primary_meaning IS NOT NULL AND m.primary_meaning <> '' "
            " ORDER BY m.id LIMIT 1) AS gloss "
            "FROM dictionary_entries e "
            "WHERE e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
            "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> '' "
            "GROUP BY e.root_buckwalter, e.root_arabic "
            "ORDER BY e.root_arabic"
        ).fetchall()
        roots = [{
            "buckwalter": r["root_buckwalter"],
            "arabic": r["root_arabic"],
            "entries": r["entries"],
            "gloss": _clean_root_gloss(r["gloss"]),
        } for r in rows]
        return jsonify({
            "root_count": len(roots),
            "entry_count": sum(r["entries"] for r in roots),
            "roots": roots,
        })
    finally:
        conn.close()


# --- Admin review surface for the Lexicon Library -------------------------
_DICT_EDITABLE = {"harmonized_en", "translation_en"}


def _dict_admin_row(r):
    d = dict(r)
    d["hidden"] = bool(d.get("hidden"))
    d["is_quran_specific"] = bool(d.get("is_quran_specific"))
    d["harm_len"] = len(d.get("harmonized_en") or "")
    d["orig_len"] = len(d.get("original_text_ar") or "")
    # verify verdict from gen_meta, surfaced for the reviewer
    try:
        v = (json.loads(d.get("gen_meta") or "{}") or {}).get("verify") or {}
        d["verify_ok"] = v.get("ok")
        d["verify_reason"] = v.get("reason")
    except Exception:
        d["verify_ok"], d["verify_reason"] = None, None
    d.pop("gen_meta", None); d.pop("raw_response", None); d.pop("scrape_hash", None)
    d["label"] = d.get("root_arabic") or d.get("root_buckwalter")
    d["link"] = "/root/%s" % d.get("root_buckwalter")
    return d


@app.route("/api/admin/dictionaries", methods=["GET"])
@admin_required
def admin_list_dictionaries():
    q = (request.args.get("q") or "").strip()
    root = (request.args.get("root") or "").strip()
    slug = (request.args.get("dictionary_slug") or "").strip()
    review_status = (request.args.get("review_status") or "").strip()
    status = (request.args.get("status") or "all").strip()
    sort = (request.args.get("sort") or "recent").strip()
    only = (request.args.get("only") or "").strip()  # harmonized|unharmonized
    sort_sql = {
        "recent": "e.edited_at DESC, e.id DESC",
        "root": "e.root_buckwalter ASC, d.author_death_year ASC",
        "confidence": "e.confidence ASC, e.id DESC",
        "longest": "LENGTH(e.harmonized_en) DESC",
    }.get(sort, "e.edited_at DESC, e.id DESC")
    try:
        limit = min(max(int(request.args.get("limit", 25)), 1), 100)
    except (ValueError, TypeError):
        limit = 25
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    where, params = [], []
    if q:
        where.append("(e.harmonized_en LIKE ? OR e.translation_en LIKE ? OR e.root_buckwalter LIKE ?)")
        params += ["%%%s%%" % q] * 3
    if root:
        where.append("e.root_buckwalter = ?"); params.append(root)
    if slug:
        where.append("e.dictionary_slug = ?"); params.append(slug)
    if review_status:
        where.append("e.review_status = ?"); params.append(review_status)
    if status == "visible":
        where.append("COALESCE(e.hidden,0) = 0")
    elif status == "hidden":
        where.append("COALESCE(e.hidden,0) = 1")
    if only == "harmonized":
        where.append("e.harmonized_en IS NOT NULL AND e.harmonized_en <> ''")
    elif only == "unharmonized":
        where.append("(e.harmonized_en IS NULL OR e.harmonized_en = '')")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        base = ("FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug %s"
                % where_sql)
        total = conn.execute("SELECT COUNT(*) AS c " + base, params).fetchone()["c"]
        rows = conn.execute(
            "SELECT e.*, d.name_en, d.name_ar, d.author, d.author_death_year, "
            "d.language, d.is_quran_specific " + base
            + " ORDER BY %s LIMIT ? OFFSET ?" % sort_sql, params + [limit, offset]).fetchall()
        return jsonify({"items": [_dict_admin_row(r) for r in rows],
                        "total": total, "limit": limit, "offset": offset})
    finally:
        conn.close()


@app.route("/api/admin/dictionaries/stats", methods=["GET"])
@admin_required
def admin_dictionaries_stats():
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        s = lambda w, p=(): conn.execute(  # noqa: E731
            "SELECT COUNT(*) AS c FROM dictionary_entries " + w, p).fetchone()["c"]
        harm = "harmonized_en IS NOT NULL AND harmonized_en <> ''"
        stats = {
            "total": s(""),
            "harmonized": s("WHERE " + harm),
            "pending": s("WHERE review_status='pending'"),
            "approved": s("WHERE review_status='approved'"),
            "rejected": s("WHERE review_status='rejected'"),
            "hidden": s("WHERE COALESCE(hidden,0)=1"),
            "roots": conn.execute(
                "SELECT COUNT(DISTINCT root_buckwalter) AS c FROM dictionary_entries").fetchone()["c"],
        }
        by_dict = conn.execute(
            "SELECT d.slug, d.name_en, d.author_death_year, COUNT(e.id) AS n, "
            "SUM(CASE WHEN e.review_status='approved' THEN 1 ELSE 0 END) AS approved "
            "FROM dictionaries d LEFT JOIN dictionary_entries e ON e.dictionary_slug=d.slug "
            "GROUP BY d.slug ORDER BY d.author_death_year").fetchall()
        stats["by_dictionary"] = [dict(r) for r in by_dict]
        return jsonify(stats)
    finally:
        conn.close()


@app.route("/api/admin/dictionary/<int:entry_id>", methods=["PATCH"])
@admin_required
def admin_update_dictionary(entry_id: int):
    data = request.get_json(silent=True) or {}
    sets, params = [], []
    if "review_status" in data:
        rs = data.get("review_status")
        if rs not in ("pending", "approved", "rejected"):
            return jsonify({"error": "review_status must be pending/approved/rejected"}), 400
        sets.append("review_status = ?"); params.append(rs)
    if "hidden" in data:
        sets.append("hidden = ?"); params.append(1 if data.get("hidden") else 0)
    for f in _DICT_EDITABLE:
        if f in data:
            sets.append("%s = ?" % f); params.append((data.get(f) or "").strip())
    if not sets:
        return jsonify({"error": "nothing to update"}), 400
    sets.append("edited_at = datetime('now')")
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        cur = conn.execute("UPDATE dictionary_entries SET %s WHERE id = ?" % ", ".join(sets),
                           params + [entry_id])
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        r = conn.execute(
            "SELECT e.*, d.name_en, d.name_ar, d.author, d.author_death_year, "
            "d.language, d.is_quran_specific FROM dictionary_entries e "
            "JOIN dictionaries d ON d.slug=e.dictionary_slug WHERE e.id = ?", (entry_id,)).fetchone()
        return jsonify(_dict_admin_row(r))
    finally:
        conn.close()


@app.route("/api/admin/dictionaries/bulk", methods=["POST"])
@admin_required
def admin_bulk_dictionaries():
    """Bulk review action over a filter (approve/reject/hide/unhide). Handy for
    ~3.5k entries: e.g. approve all harmonized entries for one dictionary, or all
    verify-clean pending. Never touches un-harmonized rows on approve."""
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip()
    setmap = {
        "approve": "review_status='approved'", "reject": "review_status='rejected'",
        "pending": "review_status='pending'", "hide": "hidden=1", "unhide": "hidden=0",
    }
    if action not in setmap:
        return jsonify({"error": "action must be approve/reject/pending/hide/unhide"}), 400
    where, params = [], []
    if data.get("root"):
        where.append("root_buckwalter = ?"); params.append(data["root"])
    if data.get("dictionary_slug"):
        where.append("dictionary_slug = ?"); params.append(data["dictionary_slug"])
    if data.get("review_status"):
        where.append("review_status = ?"); params.append(data["review_status"])
    if action == "approve":  # only ever approve harmonized rows
        where.append("harmonized_en IS NOT NULL AND harmonized_en <> ''")
    if not where:
        return jsonify({"error": "refusing an unfiltered bulk action"}), 400
    conn = get_db()
    try:
        _ensure_dict_tables(conn)
        cur = conn.execute(
            "UPDATE dictionary_entries SET %s, edited_at=datetime('now') WHERE %s"
            % (setmap[action], " AND ".join(where)), params)
        conn.commit()
        return jsonify({"action": action, "updated": cur.rowcount})
    finally:
        conn.close()


def _meter_poem_counts(conn):
    """Raw meter string -> poem count, across the whole corpus."""
    counts = {}
    for r in conn.execute(
            "SELECT meter, COUNT(*) AS c FROM poetry_poems "
            "WHERE meter IS NOT NULL AND meter <> '' GROUP BY meter"):
        counts[r["meter"]] = r["c"]
    return counts


@app.route("/api/meters")
def list_meters():
    """Public: the base meters of the corpus, most-used first, each with its
    poem count (base + variants folded in) and whether an approved teaching
    article exists. Always lists every registry meter so the index is stable."""
    conn = get_db()
    try:
        _ensure_meter_articles_table(conn)
        counts = _meter_poem_counts(conn)
        have = {
            r["meter_key"] for r in conn.execute(
                "SELECT meter_key FROM meter_articles "
                "WHERE review_status = 'approved' AND COALESCE(hidden,0) = 0")
        }
        meters = []
        for m in METER_REGISTRY:
            poem_count = sum(counts.get(v, 0) for v in _meter_all_values(m))
            meters.append({
                "key": m["key"], "meter_ar": m["ar"], "name_en": m["en"],
                "name_meaning": m["meaning"], "poem_count": poem_count,
                "has_article": m["key"] in have,
            })
        meters.sort(key=lambda x: x["poem_count"], reverse=True)
        return jsonify({"meters": meters})
    finally:
        conn.close()


@app.route("/api/meter/<key>")
def get_meter(key: str):
    """Public: one meter's teaching page — the approved article + rhythm data,
    chosen showcase lines (with transliteration + scansion), the corpus variants
    that fold into it, and a sample of poems written in it. 404 if no approved
    article yet (the meter still exists, but has nothing to teach with)."""
    entry = _METER_BY_KEY.get((key or "").strip())
    if not entry:
        return jsonify({"error": "Unknown meter"}), 404
    conn = get_db()
    try:
        _ensure_meter_articles_table(conn)
        row = conn.execute(
            "SELECT * FROM meter_articles WHERE meter_key = ? "
            "AND review_status = 'approved' AND COALESCE(hidden,0) = 0 LIMIT 1",
            (entry["key"],)).fetchone()
        if not row:
            return jsonify({"error": "No meter article"}), 404
        try:
            showcase = json.loads(row["showcase_json"] or "[]")
        except Exception:
            showcase = []
        counts = _meter_poem_counts(conn)
        values = _meter_all_values(entry)
        # variants present in the corpus, with their counts
        variants = [{"meter_ar": v, "poem_count": counts.get(v, 0)}
                    for v in entry["variants"] if counts.get(v, 0)]
        poem_count = sum(counts.get(v, 0) for v in values)
        # a browsable sample of poems in this meter — translated/quoted first
        qmarks = ",".join("?" * len(values))
        poems = conn.execute(
            f"""SELECT pp.id, pp.poet, pp.poet_latin, pp.title, pp.title_en, pp.meter, pp.era,
                   (SELECT COUNT(*) FROM poetry_lines WHERE poem_id = pp.id) AS line_count,
                   (SELECT COUNT(*) FROM poetry_lines WHERE poem_id = pp.id
                      AND translation_en IS NOT NULL AND translation_en != '') AS translated_count
                FROM poetry_poems pp WHERE pp.meter IN ({qmarks})
                ORDER BY translated_count DESC, pp.id LIMIT 24""",
            list(values)).fetchall()
        return jsonify({
            "key": entry["key"],
            "meter_ar": row["meter_ar"] or entry["ar"],
            "name_en": row["name_en"] or entry["en"],
            "name_meaning": row["name_meaning"] or entry["meaning"],
            "tafil_ar": row["tafil_ar"],
            "tafil_latin": row["tafil_latin"],
            "syllable_pattern": row["syllable_pattern"],
            "mnemonic_en": row["mnemonic_en"],
            "article_markdown": row["article_markdown"],
            "showcase": showcase,
            "variants": variants,
            "poem_count": poem_count,
            "poems": [dict(p) for p in poems],
        })
    finally:
        conn.close()


# ---- Admin: pre-Islamic poetry review (root comparisons + verse notes) -----
# Two tables share one review surface, switched by a `kind` param. Mirrors the
# exegesis admin endpoints below.
_POETRY_ADMIN = {
    "root": {"table": "root_poetry_comparisons", "md": "comparison_markdown",
             "search": ("comparison_markdown", "root_buckwalter", "root_arabic")},
    "verse": {"table": "verse_poetry_notes", "md": "note_markdown",
              "search": ("note_markdown", "page_key")},
    "lexicon": {"table": "root_poetic_lexicon", "md": "lexicon_markdown",
                "search": ("lexicon_markdown", "root_buckwalter", "root_arabic",
                           "quran_internal_summary")},
    "meter": {"table": "meter_articles", "md": "article_markdown",
              "search": ("article_markdown", "meter_key", "meter_ar", "name_en")},
}


def _poetry_admin_row(kind, row):
    """Unify a root/verse row into the shape the admin queue renders."""
    d = dict(row)
    cfg = _POETRY_ADMIN[kind]
    d["kind"] = kind
    d["hidden"] = bool(d.get("hidden"))
    d["continuity"] = bool(d.get("continuity"))
    d["markdown"] = d.pop(cfg["md"], None)
    ql = d.pop("quoted_lines_json", None)
    try:
        d["quoted_count"] = len(json.loads(ql)) if ql else 0
    except Exception:
        d["quoted_count"] = 0
    # lexicon-specific fields (surfaced before the heavy columns are dropped)
    if kind == "lexicon":
        try:
            d["sense_count"] = len(json.loads(d.get("attested_senses_json") or "[]"))
        except Exception:
            d["sense_count"] = 0
    if kind == "meter":
        try:
            d["showcase_count"] = len(json.loads(d.get("showcase_json") or "[]"))
        except Exception:
            d["showcase_count"] = 0
    # drop heavy / internal columns from the payload
    for k in ("raw_response", "adversarial_report", "counter_search_json",
              "counter_search", "collocations_json", "config_id", "quran_usage_summary",
              "poetry_usage_summary", "attested_senses_json", "quran_internal_summary",
              "lexical_basis", "showcase_json", "variants_json"):
        d.pop(k, None)
    if kind == "root":
        d["label"] = d.get("root_arabic") or d.get("root_buckwalter")
        d["link"] = "/root/%s" % d.get("root_buckwalter")
        d["verdict"] = "continuity" if d["continuity"] else d.get("shift_type")
    elif kind == "lexicon":
        d["label"] = d.get("root_arabic") or d.get("root_buckwalter")
        d["link"] = "/root/%s" % d.get("root_buckwalter")
        d["verdict"] = d.get("relation_to_quran")
    elif kind == "meter":
        d["label"] = d.get("name_en") or d.get("meter_ar") or d.get("meter_key")
        d["link"] = "/meter/%s" % d.get("meter_key")
        d["verdict"] = d.get("qa_status") or d.get("name_meaning")
    else:
        key = d.get("page_key") or ("%s:%s" % (d.get("chapter"), d.get("verse")))
        d["label"] = key
        d["link"] = "/verse/%s" % key
        d["verdict"] = "continuity" if d["continuity"] else "contrast"
    return d


@app.route("/api/admin/poetry", methods=["GET"])
@admin_required
def admin_list_poetry():
    kind = (request.args.get("kind") or "root").strip()
    if kind not in _POETRY_ADMIN:
        return jsonify({"error": "kind must be root|verse|lexicon|meter"}), 400
    cfg = _POETRY_ADMIN[kind]
    md, table = cfg["md"], cfg["table"]
    q = (request.args.get("q") or "").strip()
    review_status = (request.args.get("review_status") or "").strip()
    status = (request.args.get("status") or "all").strip()
    sort = (request.args.get("sort") or "recent").strip()
    sort_sql = {
        "recent": "created_at DESC, id DESC",
        "oldest": "created_at ASC, id ASC",
        "longest": "LENGTH(%s) DESC, created_at DESC" % md,
    }.get(sort, "created_at DESC, id DESC")
    try:
        limit = min(max(int(request.args.get("limit", 25)), 1), 100)
    except (ValueError, TypeError):
        limit = 25
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    where, params = [], []
    if q:
        where.append("(" + " OR ".join("%s LIKE ?" % c for c in cfg["search"]) + ")")
        params.extend(["%%%s%%" % q] * len(cfg["search"]))
    if review_status:
        where.append("review_status = ?")
        params.append(review_status)
    if status == "visible":
        where.append("COALESCE(hidden, 0) = 0")
    elif status == "hidden":
        where.append("COALESCE(hidden, 0) = 1")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM %s %s" % (table, where_sql), params
        ).fetchone()["c"]
        rows = conn.execute(
            "SELECT * FROM %s %s ORDER BY %s LIMIT ? OFFSET ?" % (table, where_sql, sort_sql),
            params + [limit, offset],
        ).fetchall()
        return jsonify({
            "items": [_poetry_admin_row(kind, r) for r in rows],
            "total": total, "limit": limit, "offset": offset, "kind": kind,
        })
    finally:
        conn.close()


@app.route("/api/admin/poetry/stats", methods=["GET"])
@admin_required
def admin_poetry_stats():
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)

        def per(table):
            s = lambda w: conn.execute(  # noqa: E731
                "SELECT COUNT(*) AS c FROM %s %s" % (table, w)).fetchone()["c"]
            return {
                "total": s(""),
                "pending": s("WHERE review_status='pending'"),
                "approved": s("WHERE review_status='approved'"),
                "rejected": s("WHERE review_status='rejected'"),
                "hidden": s("WHERE COALESCE(hidden,0)=1"),
            }
        root = per("root_poetry_comparisons")
        verse = per("verse_poetry_notes")
        lexicon = per("root_poetic_lexicon")
        meter = per("meter_articles")
        comb = {k: root[k] + verse[k] + lexicon[k] + meter[k] for k in root}
        comb["roots"] = root["total"]
        comb["verses"] = verse["total"]
        comb["lexicons"] = lexicon["total"]
        comb["meters"] = meter["total"]
        return jsonify({"root": root, "verse": verse, "lexicon": lexicon,
                        "meter": meter, **comb})
    finally:
        conn.close()


@app.route("/api/admin/poetry/<kind>/<int:pid>", methods=["PATCH"])
@admin_required
def admin_update_poetry(kind, pid):
    if kind not in _POETRY_ADMIN:
        return jsonify({"error": "kind must be root|verse|lexicon|meter"}), 400
    cfg = _POETRY_ADMIN[kind]
    md, table = cfg["md"], cfg["table"]
    data = request.get_json(force=True) or {}
    sets, params, edited = [], [], False
    if "hidden" in data:
        sets.append("hidden = ?")
        params.append(1 if data.get("hidden") else 0)
    if "review_status" in data:
        rs = data.get("review_status")
        if rs not in ("pending", "approved", "rejected", None):
            return jsonify({"error": "review_status must be pending/approved/rejected"}), 400
        sets.append("review_status = ?")
        params.append(rs)
    if "markdown" in data:
        m = data.get("markdown")
        if not isinstance(m, str) or not m.strip():
            return jsonify({"error": "markdown must be a non-empty string"}), 400
        sets.append("%s = ?" % md)
        params.append(m.strip()[:50000])
        edited = True
    if not sets:
        return jsonify({"error": "No updatable fields provided"}), 400
    if edited:
        sets.append("edited_at = datetime('now')")

    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        cur = conn.execute(
            "UPDATE %s SET %s WHERE id = ?" % (table, ", ".join(sets)), params + [pid])
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        row = conn.execute("SELECT * FROM %s WHERE id = ?" % table, (pid,)).fetchone()
        return jsonify({"ok": True, "item": _poetry_admin_row(kind, row)})
    finally:
        conn.close()


@app.route("/api/admin/poetry/<kind>/<int:pid>", methods=["DELETE"])
@admin_required
def admin_delete_poetry(kind, pid):
    if kind not in _POETRY_ADMIN:
        return jsonify({"error": "kind must be root|verse|lexicon|meter"}), 400
    table = _POETRY_ADMIN[kind]["table"]
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        cur = conn.execute("DELETE FROM %s WHERE id = ?" % table, (pid,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"ok": True, "deleted": pid})
    finally:
        conn.close()


@app.route("/api/admin/poetry/bulk", methods=["POST"])
@admin_required
def admin_bulk_poetry():
    data = request.get_json(force=True) or {}
    kind = (data.get("kind") or "root").strip()
    if kind not in _POETRY_ADMIN:
        return jsonify({"error": "kind must be root|verse|lexicon|meter"}), 400
    table = _POETRY_ADMIN[kind]["table"]
    raw_ids = data.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return jsonify({"error": "ids must be a non-empty list"}), 400
    ids = [int(i) for i in raw_ids if str(i).isdigit()][:500]
    if not ids:
        return jsonify({"error": "no valid ids"}), 400
    op = (data.get("op") or "").strip()
    placeholders = ",".join("?" * len(ids))
    conn = get_db()
    try:
        _ensure_poetry_serve_tables(conn)
        if op == "delete":
            cur = conn.execute(
                "DELETE FROM %s WHERE id IN (%s)" % (table, placeholders), ids)
        elif op in ("approve", "reject", "pending"):
            rs = {"approve": "approved", "reject": "rejected", "pending": "pending"}[op]
            cur = conn.execute(
                "UPDATE %s SET review_status = ? WHERE id IN (%s)" % (table, placeholders),
                [rs] + ids)
        elif op in ("hide", "unhide"):
            cur = conn.execute(
                "UPDATE %s SET hidden = ? WHERE id IN (%s)" % (table, placeholders),
                [1 if op == "hide" else 0] + ids)
        else:
            return jsonify({"error": "op must be approve/reject/pending/hide/unhide/delete"}), 400
        conn.commit()
        return jsonify({"ok": True, "op": op, "affected": cur.rowcount})
    finally:
        conn.close()


@app.route("/api/admin/exegesis", methods=["GET"])
@admin_required
def admin_list_exegesis():
    """Paginated, filterable list of verse exegesis notes."""
    q = (request.args.get("q") or "").strip()
    review_status = (request.args.get("review_status") or "").strip()
    status = (request.args.get("status") or "all").strip()
    sort = (request.args.get("sort") or "recent").strip()
    order_by = _EXEG_SORT_SQL.get(sort, _EXEG_SORT_SQL["recent"])
    try:
        limit = min(max(int(request.args.get("limit", 25)), 1), 100)
    except (ValueError, TypeError):
        limit = 25
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    where, params = [], []
    if q:
        where.append("(exegesis_markdown LIKE ? OR page_key LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like])
    if review_status:
        where.append("review_status = ?")
        params.append(review_status)
    if status == "visible":
        where.append("COALESCE(hidden, 0) = 0")
    elif status == "hidden":
        where.append("COALESCE(hidden, 0) = 1")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_db()
    try:
        _ensure_exegesis_table(conn)
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM verse_exegesis {where_sql}", params
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT {_EXEG_COLUMNS} FROM verse_exegesis "
            f"{where_sql} ORDER BY {order_by} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return jsonify({
            "items": [_exeg_row_to_dict(r) for r in rows],
            "total": total, "limit": limit, "offset": offset,
        })
    finally:
        conn.close()


@app.route("/api/admin/exegesis/stats", methods=["GET"])
@admin_required
def admin_exegesis_stats():
    conn = get_db()
    try:
        _ensure_exegesis_table(conn)

        def scalar(sql):
            return conn.execute(sql).fetchone()["c"]

        total = scalar("SELECT COUNT(*) AS c FROM verse_exegesis")
        return jsonify({
            "total": total,
            "visible": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE COALESCE(hidden,0)=0"),
            "hidden": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE COALESCE(hidden,0)=1"),
            "pending": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE review_status='pending'"),
            "approved": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE review_status='approved'"),
            "rejected": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE review_status='rejected'"),
            "verses": scalar("SELECT COUNT(DISTINCT chapter || ':' || verse) AS c FROM verse_exegesis"),
            "edited": scalar("SELECT COUNT(*) AS c FROM verse_exegesis WHERE edited_at IS NOT NULL"),
        })
    finally:
        conn.close()


@app.route("/api/admin/exegesis/<int:exeg_id>", methods=["PATCH"])
@admin_required
def admin_update_exegesis(exeg_id):
    """Hide/unhide, approve/reject, or correct the exegesis text."""
    data = request.get_json(force=True) or {}
    sets, params, edited = [], [], False
    if "hidden" in data:
        sets.append("hidden = ?")
        params.append(1 if data.get("hidden") else 0)
    if "review_status" in data:
        rs = data.get("review_status")
        if rs not in ("pending", "approved", "rejected", None):
            return jsonify({"error": "review_status must be pending/approved/rejected"}), 400
        sets.append("review_status = ?")
        params.append(rs)
    if "exegesis_markdown" in data:
        md = data.get("exegesis_markdown")
        if not isinstance(md, str) or not md.strip():
            return jsonify({"error": "exegesis_markdown must be a non-empty string"}), 400
        sets.append("exegesis_markdown = ?")
        params.append(md.strip()[:50000])
        edited = True
    if not sets:
        return jsonify({"error": "No updatable fields provided"}), 400
    if edited:
        sets.append("edited_at = datetime('now')")

    conn = get_db()
    try:
        _ensure_exegesis_table(conn)
        cur = conn.execute(
            f"UPDATE verse_exegesis SET {', '.join(sets)} WHERE id = ?",
            params + [exeg_id],
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Exegesis not found"}), 404
        row = conn.execute(
            f"SELECT {_EXEG_COLUMNS} FROM verse_exegesis WHERE id = ?", (exeg_id,)
        ).fetchone()
        return jsonify({"ok": True, "item": _exeg_row_to_dict(row)})
    finally:
        conn.close()


@app.route("/api/admin/exegesis/<int:exeg_id>", methods=["DELETE"])
@admin_required
def admin_delete_exegesis(exeg_id):
    conn = get_db()
    try:
        _ensure_exegesis_table(conn)
        cur = conn.execute("DELETE FROM verse_exegesis WHERE id = ?", (exeg_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Exegesis not found"}), 404
        return jsonify({"ok": True, "deleted": exeg_id})
    finally:
        conn.close()


@app.route("/api/admin/exegesis/bulk", methods=["POST"])
@admin_required
def admin_bulk_exegesis():
    data = request.get_json(force=True) or {}
    raw_ids = data.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return jsonify({"error": "ids must be a non-empty list"}), 400
    ids = [int(i) for i in raw_ids if str(i).isdigit()][:500]
    if not ids:
        return jsonify({"error": "no valid ids"}), 400
    op = (data.get("op") or "").strip()
    placeholders = ",".join("?" * len(ids))
    conn = get_db()
    try:
        _ensure_exegesis_table(conn)
        if op == "delete":
            cur = conn.execute(
                f"DELETE FROM verse_exegesis WHERE id IN ({placeholders})", ids)
        elif op in ("approve", "reject", "pending"):
            rs = {"approve": "approved", "reject": "rejected", "pending": "pending"}[op]
            cur = conn.execute(
                f"UPDATE verse_exegesis SET review_status = ? WHERE id IN ({placeholders})",
                [rs] + ids)
        elif op in ("hide", "unhide"):
            cur = conn.execute(
                f"UPDATE verse_exegesis SET hidden = ? WHERE id IN ({placeholders})",
                [1 if op == "hide" else 0] + ids)
        else:
            return jsonify({"error": "op must be approve/reject/pending/hide/unhide/delete"}), 400
        conn.commit()
        return jsonify({"ok": True, "op": op, "affected": cur.rowcount})
    finally:
        conn.close()


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


# ---------------------------------------------------------------------------
# Verse of the Day pool
#
# The home page shows one verse from this pool, picked deterministically by
# day-of-year. Used to live as a hard-coded array in
# VerseOfTheDay.tsx; promoting to a DB table so admins can curate the
# rotation without a deploy.
#
# Seeded on first run with the original 20 verses so behavior is unchanged
# until an admin starts editing. position is unused for ordering today
# (day-of-year picks by id ASC) but reserved so a future "drag to reorder"
# UI doesn't need a schema change.
# ---------------------------------------------------------------------------
_VERSE_OF_THE_DAY_SEED: list[tuple[int, int]] = [
    (1, 1), (2, 255), (24, 35), (36, 1), (55, 13),
    (59, 22), (67, 1), (96, 1), (112, 1), (13, 28),
    (94, 5), (49, 13), (21, 107), (3, 139), (56, 77),
    (39, 53), (31, 18), (17, 1), (18, 10), (2, 152),
]


def _ensure_verse_of_the_day_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verse_of_the_day_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chapter, verse)
            )
        """)
        # Seed if empty. Idempotent: a deploy that adds the table for the
        # first time gets the 20 originals; subsequent boots see existing
        # rows and skip. Admin edits are preserved across redeploys.
        existing = conn.execute(
            "SELECT COUNT(*) FROM verse_of_the_day_pool"
        ).fetchone()[0]
        if existing == 0:
            for pos, (c, v) in enumerate(_VERSE_OF_THE_DAY_SEED):
                conn.execute(
                    "INSERT INTO verse_of_the_day_pool (chapter, verse, position) "
                    "VALUES (?, ?, ?)",
                    (c, v, pos),
                )
            print(f"  Seeded verse_of_the_day_pool with {len(_VERSE_OF_THE_DAY_SEED)} entries")
        conn.commit()
    finally:
        conn.close()


_ensure_verse_of_the_day_table()


def _list_verse_of_the_day_pool(conn) -> list[dict]:
    """Return the full pool ordered by id ASC (insertion order). Each row
    is enriched with the FULL Arabic + English text so the admin UI can
    show the verse content inline (operator review pass 2026-05-15 —
    the previous version returned 60-char Arabic / 140-char English
    previews, and the surah_name lookup raised silently because there's
    no `surahs` table in this DB, which also wiped the Arabic + English
    fields via the catch-all except block).
    """
    rows = conn.execute(
        "SELECT id, chapter, verse, position, created_at "
        "FROM verse_of_the_day_pool ORDER BY id ASC"
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        c = r["chapter"]; v = r["verse"]
        # Per-query try/except so one missing table doesn't take down
        # the others. Older code wrapped all three lookups in a single
        # try block — when `surahs` 404'd, arabic + translation both
        # got skipped silently.
        arabic = ""
        translation = ""
        try:
            arow = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (c, v),
            ).fetchone()
            if arow and arow["text_uthmani"]:
                arabic = arow["text_uthmani"].strip()
        except Exception as e:
            print(f"[votd] arabic lookup failed for {c}:{v}: {e}")
        try:
            trow = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
                (c, v),
            ).fetchone()
            if trow and trow["text_en"]:
                translation = trow["text_en"].strip()
        except Exception as e:
            print(f"[votd] translation lookup failed for {c}:{v}: {e}")
        out.append({
            "id": r["id"],
            "chapter": c,
            "verse": v,
            "position": r["position"],
            "created_at": r["created_at"],
            # Keep the legacy `*_preview` field names for backwards
            # compatibility with any callers that haven't redeployed.
            # They now carry the FULL strings, not truncated previews.
            "arabic_preview": arabic,
            "translation_preview": translation,
            # Canonical full-text fields. Use these going forward.
            "arabic": arabic,
            "translation_en": translation,
        })
    return out


def _todays_verse_of_the_day(conn) -> tuple[int, int] | None:
    """Pick today's verse deterministically: day-of-year mod pool size.
    Matches the old VerseOfTheDay.tsx behavior exactly so a deploy that
    flips frontend to API-driven doesn't change which verse shows on a
    given day. Returns None if the pool is empty."""
    rows = conn.execute(
        "SELECT chapter, verse FROM verse_of_the_day_pool ORDER BY id ASC"
    ).fetchall()
    if not rows:
        return None
    now = datetime.now()
    start_of_year = datetime(now.year, 1, 1)
    day_of_year = (now - start_of_year).days
    pick = rows[day_of_year % len(rows)]
    return int(pick["chapter"]), int(pick["verse"])


@app.route("/api/verse-of-the-day", methods=["GET"])
def public_verse_of_the_day():
    """Public endpoint — homepage / NotFound / BadGateway pages call
    this to know which verse to surface today. Returns just the
    chapter:verse reference; the consumer fetches the full verse data
    via the existing /api/verse/<surah>:<ayah> endpoint. Splitting
    those keeps this endpoint cheap and cacheable."""
    conn = get_db()
    try:
        pick = _todays_verse_of_the_day(conn)
    finally:
        conn.close()
    if not pick:
        # Empty pool — fall back to a safe canonical default rather
        # than 404'ing, so the homepage's verse-of-the-day section
        # never renders blank just because an admin emptied the pool.
        return jsonify({"chapter": 2, "verse": 255})
    return jsonify({"chapter": pick[0], "verse": pick[1]})


@app.route("/api/admin/verse-of-the-day-pool", methods=["GET"])
@admin_required
def admin_verse_of_the_day_list():
    """List all verses in the rotation, with surah name + previews so
    the admin UI can render rich rows in one fetch."""
    conn = get_db()
    try:
        items = _list_verse_of_the_day_pool(conn)
        today = _todays_verse_of_the_day(conn)
    finally:
        conn.close()
    return jsonify({
        "items": items,
        "today": ({"chapter": today[0], "verse": today[1]} if today else None),
    })


@app.route("/api/admin/verse-of-the-day-pool", methods=["POST"])
@admin_required
def admin_verse_of_the_day_add():
    """Add a verse to the rotation. Validates that the verse actually
    exists in the corpus before inserting — prevents typo'd refs from
    silently producing a blank verse-of-the-day display."""
    body = request.get_json(force=True, silent=True) or {}
    try:
        chapter = int(body.get("chapter"))
        verse = int(body.get("verse"))
    except (TypeError, ValueError):
        return jsonify({"error": "chapter and verse must be integers"}), 400
    if not (1 <= chapter <= 114 and verse >= 1):
        return jsonify({"error": "chapter must be 1-114, verse >= 1"}), 400

    conn = get_db()
    try:
        # Validate the reference exists.
        vrow = conn.execute(
            "SELECT 1 FROM verses WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        ).fetchone()
        if not vrow:
            return jsonify({"error": f"Quran {chapter}:{verse} doesn't exist"}), 404
        # Reject duplicate. The UNIQUE constraint would catch this anyway
        # but we want a clean 409 rather than a 500 from an integrity error.
        existing = conn.execute(
            "SELECT id FROM verse_of_the_day_pool WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        ).fetchone()
        if existing:
            return jsonify({"error": f"Quran {chapter}:{verse} is already in the rotation"}), 409
        cur = conn.execute(
            "INSERT INTO verse_of_the_day_pool (chapter, verse, position) "
            "VALUES (?, ?, COALESCE((SELECT MAX(position) + 1 FROM verse_of_the_day_pool), 0))",
            (chapter, verse),
        )
        conn.commit()
        new_id = cur.lastrowid
        items = _list_verse_of_the_day_pool(conn)
    finally:
        conn.close()
    # Return the freshly-inserted row (looked up from the enriched list)
    # so the frontend gets the surah name + previews without a follow-up.
    new_row = next((i for i in items if i["id"] == new_id), None)
    return jsonify(new_row or {"id": new_id, "chapter": chapter, "verse": verse}), 201


@app.route("/api/admin/verse-of-the-day-pool/<int:pool_id>", methods=["DELETE"])
@admin_required
def admin_verse_of_the_day_delete(pool_id: int):
    """Remove a verse from the rotation. The home page falls back to
    2:255 if the pool ends up empty."""
    conn = get_db()
    try:
        cur = conn.execute(
            "DELETE FROM verse_of_the_day_pool WHERE id = ?", (pool_id,),
        )
        conn.commit()
        deleted = cur.rowcount
    finally:
        conn.close()
    if not deleted:
        return jsonify({"error": "Pool entry not found"}), 404
    return jsonify({"id": pool_id, "deleted": True})


def _create_admin_token(
    user_id: int, username: str, pw_changed_at: int = 0, remember: bool = False
) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    ttl_seconds = (
        _ADMIN_JWT_REMEMBER_DAYS * 24 * 3600 if remember else _ADMIN_JWT_EXP_HOURS * 3600
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": now + ttl_seconds,
        "iat": now,
        "pwc": pw_changed_at,  # invalidated when password changes
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


# ---------------------------------------------------------------------------
# Analytics: admin_ips, page_views, youtube_video_stats
#
# admin_ips     — every IP that has ever successfully logged into the admin
#                 CMS. Used to *exclude* admins from public-site visitor
#                 counts so the operator's own browsing doesn't pollute the
#                 metrics.
# page_views    — one row per public-site page load. ip_hash = sha256(salt
#                 + ip). The salt is per-deployment and stored in
#                 admin_preferences; an attacker with read-only DB access
#                 can't reverse-engineer raw IPs.
# youtube_video_stats — daily snapshots so we can compute "views gained in
#                 the last 7d" without continuously hammering the YouTube
#                 Data API. Refreshed by a daily background thread (and on
#                 demand from the Stats page).
# ---------------------------------------------------------------------------
def _ensure_analytics_tables():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL UNIQUE,
                username TEXT,
                user_agent TEXT,
                first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_hash TEXT NOT NULL,
                path TEXT NOT NULL,
                referrer TEXT,
                user_agent TEXT,
                viewed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pv_viewed_at ON page_views(viewed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pv_path_viewed ON page_views(path, viewed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pv_ip_viewed ON page_views(ip_hash, viewed_at)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youtube_video_stats (
                youtube_video_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                title TEXT,
                published_at TEXT,
                views INTEGER NOT NULL DEFAULT 0,
                likes INTEGER NOT NULL DEFAULT 0,
                comments INTEGER NOT NULL DEFAULT 0,
                snapshot_date TEXT NOT NULL,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (youtube_video_id, snapshot_date)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_yvs_video_date "
            "ON youtube_video_stats(youtube_video_id, snapshot_date DESC)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youtube_channel_stats (
                channel_id TEXT NOT NULL,
                title TEXT,
                subscriber_count INTEGER NOT NULL DEFAULT 0,
                view_count INTEGER NOT NULL DEFAULT 0,
                video_count INTEGER NOT NULL DEFAULT 0,
                snapshot_date TEXT NOT NULL,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (channel_id, snapshot_date)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ycs_date "
            "ON youtube_channel_stats(snapshot_date DESC)"
        )
        conn.commit()
    finally:
        conn.close()


_ensure_analytics_tables()


def _get_client_ip() -> str:
    """Best-effort real client IP. ProxyFix handled X-Forwarded-For above."""
    return (request.remote_addr or "unknown").strip()


# Module-level cache so we don't hit the DB on every pageview request.
_pageview_salt_cache: dict = {"value": None}


def _get_pageview_salt() -> str:
    """Return a per-deployment secret salt used to hash visitor IPs.

    Generated lazily on first use and persisted in admin_preferences so it
    survives restarts. Caching matters: pageviews are write-heavy and
    fetching the salt fresh every time would double the DB hits.
    """
    if _pageview_salt_cache["value"]:
        return _pageview_salt_cache["value"]
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'pageview_ip_salt'"
        ).fetchone()
        if row and row["value"]:
            _pageview_salt_cache["value"] = row["value"]
            return row["value"]
        salt = secrets.token_hex(16)
        conn.execute(
            "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
            "VALUES ('pageview_ip_salt', ?, CURRENT_TIMESTAMP)",
            (salt,),
        )
        conn.commit()
        _pageview_salt_cache["value"] = salt
        return salt
    finally:
        conn.close()


def _hash_ip(ip: str) -> str:
    salt = _get_pageview_salt()
    return hashlib.sha256((salt + ip).encode("utf-8")).hexdigest()


def _record_admin_ip(ip: str, username: str, user_agent: str) -> None:
    """Idempotent: first seen -> INSERT, subsequent -> bump last_seen."""
    if not ip:
        return
    user_agent = (user_agent or "")[:500]
    username = (username or "")[:120]
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO admin_ips (ip, username, user_agent) VALUES (?, ?, ?)",
            (ip, username, user_agent),
        )
        conn.execute(
            "UPDATE admin_ips SET last_seen_at = CURRENT_TIMESTAMP, "
            "username = ?, user_agent = ? WHERE ip = ?",
            (username, user_agent, ip),
        )
        conn.commit()
    finally:
        conn.close()


def _is_admin_ip(ip: str) -> bool:
    if not ip:
        return False
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM admin_ips WHERE ip = ? LIMIT 1", (ip,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    ip = request.remote_addr or "unknown"
    if _check_rate_limit(ip):
        return jsonify({"error": "Too many attempts. Try again in a few minutes."}), 429

    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")
    remember = bool(body.get("remember"))

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

        # Track this IP so the analytics page can exclude admin browsing
        # from public-site visitor counts. Failures here must NOT break
        # login — the user shouldn't get locked out because of an
        # analytics-table issue.
        try:
            _record_admin_ip(ip, row["username"], request.headers.get("User-Agent", ""))
        except Exception as e:
            print(f"WARNING: _record_admin_ip failed: {e}")

        token = _create_admin_token(
            row["id"], row["username"], row["pw_changed_at"], remember=remember
        )
        return jsonify({"token": token, "username": row["username"]})
    finally:
        conn.close()


@app.route("/api/admin/me", methods=["GET"])
@admin_required
def admin_me():
    return jsonify({"username": request.admin_user["username"]})


# ---------------------------------------------------------------------------
# Analytics endpoints: pageview ingest + stats summaries
# ---------------------------------------------------------------------------
@app.route("/api/track/pageview", methods=["POST"])
def track_pageview():
    """Public endpoint hit by the frontend on every route change.

    Quietly drops admin-IP visits, /admin paths, and /api paths so the
    metrics reflect actual public-site usage. Always returns 204 on
    well-formed requests so a malicious client can't probe whether their
    IP is admin via timing or response body."""
    body = request.get_json(silent=True) or {}
    path = (body.get("path") or "").strip()
    referrer = (body.get("referrer") or "").strip()
    if not path or len(path) > 500:
        return ("", 400)
    if path.startswith("/admin") or path.startswith("/api/"):
        return ("", 204)
    ip = _get_client_ip()
    if _is_admin_ip(ip):
        return ("", 204)
    referrer = referrer[:500]
    user_agent = (request.headers.get("User-Agent") or "")[:500]
    try:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO page_views (ip_hash, path, referrer, user_agent) "
                "VALUES (?, ?, ?, ?)",
                (_hash_ip(ip), path, referrer, user_agent),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"WARNING: pageview insert failed: {e}")
    return ("", 204)


def _parse_stats_range(arg: str | None) -> int:
    """Returns the range in days. Defaults to 7. Allowed: 7, 30."""
    if arg == "30d":
        return 30
    if arg == "7d":
        return 7
    return 7


@app.route("/api/admin/stats/website", methods=["GET"])
@admin_required
def admin_stats_website():
    days = _parse_stats_range(request.args.get("range"))
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    prior_since = since - timedelta(days=days)
    five_min_ago = now - timedelta(minutes=5)

    since_iso = since.strftime("%Y-%m-%d %H:%M:%S")
    until_iso = now.strftime("%Y-%m-%d %H:%M:%S")
    prior_since_iso = prior_since.strftime("%Y-%m-%d %H:%M:%S")
    five_min_ago_iso = five_min_ago.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    try:
        # Current period totals
        row = conn.execute(
            "SELECT COUNT(*) AS pv, COUNT(DISTINCT ip_hash) AS uv "
            "FROM page_views WHERE viewed_at >= ?",
            (since_iso,),
        ).fetchone()
        pv = int(row["pv"] or 0)
        uv = int(row["uv"] or 0)

        # Prior period totals (same length, immediately preceding)
        prior_row = conn.execute(
            "SELECT COUNT(*) AS pv, COUNT(DISTINCT ip_hash) AS uv "
            "FROM page_views WHERE viewed_at >= ? AND viewed_at < ?",
            (prior_since_iso, since_iso),
        ).fetchone()
        pv_prior = int(prior_row["pv"] or 0)
        uv_prior = int(prior_row["uv"] or 0)

        # Daily breakdown — fill in zeros so the chart is dense
        daily_rows = conn.execute(
            "SELECT date(viewed_at) AS d, COUNT(*) AS pv, "
            "COUNT(DISTINCT ip_hash) AS uv "
            "FROM page_views WHERE viewed_at >= ? "
            "GROUP BY date(viewed_at) ORDER BY d ASC",
            (since_iso,),
        ).fetchall()
        daily_map = {r["d"]: (int(r["pv"]), int(r["uv"])) for r in daily_rows}
        daily = []
        # Buckets are calendar days ending TODAY. Earlier off-by-one
        # produced [now-7d .. now-1d] which silently dropped every
        # event landing on the current calendar day — the dashboard's
        # "page_views" total said 25 while the chart showed nothing.
        today_date = now.date()
        for i in range(days):
            d = (today_date - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            pvi, uvi = daily_map.get(d, (0, 0))
            daily.append({"date": d, "page_views": pvi, "unique_visitors": uvi})

        # Top pages
        top_pages_rows = conn.execute(
            "SELECT path, COUNT(*) AS pv, COUNT(DISTINCT ip_hash) AS uv "
            "FROM page_views WHERE viewed_at >= ? "
            "GROUP BY path ORDER BY pv DESC LIMIT 10",
            (since_iso,),
        ).fetchall()
        top_pages = [
            {"path": r["path"], "page_views": int(r["pv"]), "unique_visitors": int(r["uv"])}
            for r in top_pages_rows
        ]

        # Top referrers — bucket NULL/empty as "(direct)"
        top_ref_rows = conn.execute(
            "SELECT COALESCE(NULLIF(referrer, ''), '(direct)') AS ref, COUNT(*) AS pv "
            "FROM page_views WHERE viewed_at >= ? "
            "GROUP BY ref ORDER BY pv DESC LIMIT 10",
            (since_iso,),
        ).fetchall()
        top_referrers = [{"referrer": r["ref"], "page_views": int(r["pv"])} for r in top_ref_rows]

        # Live: distinct visitors in the last 5 minutes
        live_row = conn.execute(
            "SELECT COUNT(DISTINCT ip_hash) AS active FROM page_views "
            "WHERE viewed_at >= ?",
            (five_min_ago_iso,),
        ).fetchone()
        active = int(live_row["active"] or 0)
    finally:
        conn.close()

    return jsonify({
        "range": f"{days}d",
        "since": since_iso,
        "until": until_iso,
        "totals": {
            "page_views": pv,
            "unique_visitors": uv,
            "page_views_prior": pv_prior,
            "unique_visitors_prior": uv_prior,
        },
        "daily": daily,
        "top_pages": top_pages,
        "top_referrers": top_referrers,
        "live": {"active_last_5min": active},
    })


# ---------------------------------------------------------------------------
# YouTube stats: daily snapshots + on-demand refresh + summary endpoint.
# ---------------------------------------------------------------------------
def _refresh_youtube_stats() -> dict:
    """Fetch current view/like/comment counts for every uploaded video and
    write a snapshot row dated today. Idempotent — running twice in the
    same UTC day just overwrites that day's row (PK is video_id+date)."""
    conn = get_db()
    id_to_source: dict[str, tuple[str, int]] = {}
    try:
        # Prefer educational_videos when an id appears in both (more
        # reliable schema; admin_pipeline_videos.youtube_video_id is
        # populated less consistently).
        try:
            for r in conn.execute(
                "SELECT id, youtube_video_id FROM educational_videos "
                "WHERE youtube_video_id IS NOT NULL AND youtube_video_id != ''"
            ).fetchall():
                id_to_source[r["youtube_video_id"]] = ("educational_videos", int(r["id"]))
        except sqlite3.OperationalError:
            # Educational tables may not exist on a fresh install
            pass
        for r in conn.execute(
            "SELECT id, youtube_video_id FROM admin_pipeline_videos "
            "WHERE youtube_video_id IS NOT NULL AND youtube_video_id != ''"
        ).fetchall():
            yid = r["youtube_video_id"]
            if yid not in id_to_source:
                id_to_source[yid] = ("admin_pipeline_videos", int(r["id"]))
        # Shorts published by the Q&A/Studio scheduler — the live
        # pipeline. Collected last with unconditional assignment so a
        # qa_videos row wins any id collision with the legacy tables.
        try:
            for r in conn.execute(
                "SELECT id, youtube_video_id FROM qa_videos "
                "WHERE youtube_video_id IS NOT NULL AND youtube_video_id != ''"
            ).fetchall():
                id_to_source[r["youtube_video_id"]] = ("qa_videos", int(r["id"]))
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()

    if not id_to_source:
        return {"ok": True, "videos_refreshed": 0, "fetched_at": datetime.now(timezone.utc).isoformat()}

    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return {"ok": False, "error": str(e), "videos_refreshed": 0}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    refreshed = 0
    ids = list(id_to_source.keys())
    for batch_start in range(0, len(ids), 50):
        batch = ids[batch_start:batch_start + 50]
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "statistics,snippet", "id": ",".join(batch)},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
            )
        except requests.RequestException as e:
            return {"ok": False, "error": f"YouTube request failed: {e}", "videos_refreshed": refreshed}
        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {}).get("message") or resp.text[:300]
            except Exception:
                err = resp.text[:300]
            return {"ok": False, "error": f"YouTube {resp.status_code}: {err}", "videos_refreshed": refreshed}

        items = resp.json().get("items") or []
        conn = get_db()
        try:
            for item in items:
                yid = item.get("id")
                if not yid or yid not in id_to_source:
                    continue
                stats = item.get("statistics") or {}
                snippet = item.get("snippet") or {}

                def _i(k: str) -> int:
                    v = stats.get(k)
                    try:
                        return int(v) if v is not None else 0
                    except (TypeError, ValueError):
                        return 0

                source_table, source_id = id_to_source[yid]
                conn.execute(
                    "INSERT OR REPLACE INTO youtube_video_stats "
                    "(youtube_video_id, source_table, source_id, title, published_at, "
                    " views, likes, comments, snapshot_date, fetched_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    (
                        yid, source_table, source_id,
                        snippet.get("title"), snippet.get("publishedAt"),
                        _i("viewCount"), _i("likeCount"), _i("commentCount"),
                        today,
                    ),
                )
                refreshed += 1
            conn.commit()
        finally:
            conn.close()

    # Channel-level snapshot — subscriber/view/video counts for the
    # authenticated channel. Single API call, separate from the per-
    # video loop. `mine=true` resolves the channel from the OAuth
    # token, so we don't need to know the channel ID upfront. Failure
    # here is non-fatal — we already have the per-video data; just
    # log and move on.
    channel_ok = False
    try:
        ch_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics,snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        if ch_resp.status_code == 200:
            ch_items = ch_resp.json().get("items") or []
            if ch_items:
                ch = ch_items[0]
                ch_id = ch.get("id")
                ch_stats = ch.get("statistics") or {}
                ch_snippet = ch.get("snippet") or {}

                def _ci(k: str) -> int:
                    v = ch_stats.get(k)
                    try:
                        return int(v) if v is not None else 0
                    except (TypeError, ValueError):
                        return 0

                if ch_id:
                    # Channel-identity guard. Operator hit this on
                    # 2026-05-25: after re-OAuthing from a different
                    # Google account, channels.mine returned a
                    # DIFFERENT channel — the personal one rather
                    # than the brand-account one — and the dashboard
                    # silently flipped to showing those stats
                    # (subscribers 42 → 161 overnight). Refuse to
                    # write the snapshot when the channel_id has
                    # changed from the pinned one; surface the
                    # mismatch so the operator can re-auth correctly.
                    conn = get_db()
                    try:
                        # The "pinned" channel is whatever the
                        # operator first connected — stored in
                        # admin_preferences. If it's not set yet,
                        # auto-pin to whatever we see today (first-
                        # run case).
                        pinned_row = conn.execute(
                            "SELECT value FROM admin_preferences "
                            "WHERE key='youtube_channel_id_pinned'"
                        ).fetchone()
                        pinned = pinned_row["value"] if pinned_row else None
                        if pinned and pinned != ch_id:
                            err_msg = (
                                f"OAuth channel mismatch — pinned "
                                f"channel is {pinned} but the connected "
                                f"OAuth token resolves to {ch_id} "
                                f"({ch_snippet.get('title') or '?'}). "
                                f"Refusing to overwrite stats. "
                                f"Either re-OAuth from the original "
                                f"account, or visit Admin → Stats → "
                                f"YouTube and click 'Repin to current "
                                f"channel' to switch."
                            )
                            print(f"[youtube-stats] {err_msg}")
                            # Persist the mismatch for the dashboard to
                            # surface as a banner.
                            conn.execute(
                                "INSERT OR REPLACE INTO admin_preferences "
                                "(key, value, updated_at) VALUES "
                                "('youtube_channel_mismatch', ?, "
                                "CURRENT_TIMESTAMP)",
                                (f"{ch_id}|{ch_snippet.get('title') or ''}",),
                            )
                            conn.commit()
                        else:
                            if not pinned:
                                # First-run pin
                                conn.execute(
                                    "INSERT OR REPLACE INTO admin_preferences "
                                    "(key, value, updated_at) VALUES "
                                    "('youtube_channel_id_pinned', ?, "
                                    "CURRENT_TIMESTAMP)",
                                    (ch_id,),
                                )
                            # Clear any stale mismatch marker.
                            conn.execute(
                                "DELETE FROM admin_preferences "
                                "WHERE key='youtube_channel_mismatch'"
                            )
                            conn.execute(
                                "INSERT OR REPLACE INTO youtube_channel_stats "
                                "(channel_id, title, subscriber_count, view_count, "
                                " video_count, snapshot_date, fetched_at) "
                                "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                                (
                                    ch_id,
                                    ch_snippet.get("title"),
                                    _ci("subscriberCount"),
                                    _ci("viewCount"),
                                    _ci("videoCount"),
                                    today,
                                ),
                            )
                            channel_ok = True
                        conn.commit()
                    finally:
                        conn.close()
        else:
            print(f"[youtube-stats] channels.list returned {ch_resp.status_code}: {ch_resp.text[:200]}")
    except Exception as e:
        print(f"[youtube-stats] channel snapshot failed: {e}")

    return {
        "ok": True,
        "videos_refreshed": refreshed,
        "channel_refreshed": channel_ok,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@app.route("/api/admin/stats/youtube/refresh", methods=["POST"])
@admin_required
def admin_stats_youtube_refresh():
    return jsonify(_refresh_youtube_stats())


@app.route("/api/admin/stats/youtube", methods=["GET"])
@admin_required
def admin_stats_youtube():
    days = _parse_stats_range(request.args.get("range"))
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")

    conn = get_db()
    try:
        # Most-recent snapshot per video
        current_rows = conn.execute(
            "SELECT s.* FROM youtube_video_stats s "
            "JOIN ( "
            "  SELECT youtube_video_id, MAX(snapshot_date) AS d "
            "  FROM youtube_video_stats GROUP BY youtube_video_id "
            ") m ON m.youtube_video_id = s.youtube_video_id AND m.d = s.snapshot_date"
        ).fetchall()

        # Prior snapshot per video — most recent strictly before cutoff
        prior_rows = conn.execute(
            "SELECT s.* FROM youtube_video_stats s "
            "JOIN ( "
            "  SELECT youtube_video_id, MAX(snapshot_date) AS d "
            "  FROM youtube_video_stats "
            "  WHERE snapshot_date <= ? "
            "  GROUP BY youtube_video_id "
            ") m ON m.youtube_video_id = s.youtube_video_id AND m.d = s.snapshot_date",
            (cutoff,),
        ).fetchall()

        snapshot_count = int(conn.execute(
            "SELECT COUNT(*) FROM youtube_video_stats"
        ).fetchone()[0])
        last_refresh_row = conn.execute(
            "SELECT MAX(fetched_at) FROM youtube_video_stats"
        ).fetchone()
        last_refresh = last_refresh_row[0] if last_refresh_row else None

        # Channel: most-recent snapshot for the PINNED channel id (if
        # one is set). Falls back to "latest snapshot regardless of
        # channel" for first-run / pre-pin case. The pinning
        # mechanism stops a mid-history channel switch from
        # silently flipping the dashboard to the wrong channel's
        # numbers — operator hit this 2026-05-25 when re-OAuthing
        # pulled in a personal channel and 162 subs overlaid the
        # real al-nuqta numbers (42 at the time).
        pinned_row_q = conn.execute(
            "SELECT value FROM admin_preferences "
            "WHERE key='youtube_channel_id_pinned'"
        ).fetchone()
        pinned_for_query = pinned_row_q["value"] if pinned_row_q else None

        if pinned_for_query:
            channel_current = conn.execute(
                "SELECT * FROM youtube_channel_stats "
                "WHERE channel_id = ? "
                "ORDER BY snapshot_date DESC LIMIT 1",
                (pinned_for_query,),
            ).fetchone()
        else:
            channel_current = conn.execute(
                "SELECT * FROM youtube_channel_stats "
                "WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM youtube_channel_stats) "
                "ORDER BY channel_id LIMIT 1"
            ).fetchone()

        channel_prior = None
        channel_daily_rows: list = []
        if channel_current:
            channel_prior = conn.execute(
                "SELECT * FROM youtube_channel_stats "
                "WHERE channel_id = ? AND snapshot_date <= ? "
                "ORDER BY snapshot_date DESC LIMIT 1",
                (channel_current["channel_id"], cutoff),
            ).fetchone()
            channel_daily_rows = conn.execute(
                "SELECT snapshot_date AS d, subscriber_count, view_count, video_count "
                "FROM youtube_channel_stats "
                "WHERE channel_id = ? AND snapshot_date >= ? "
                "ORDER BY snapshot_date ASC",
                (channel_current["channel_id"],
                 (now - timedelta(days=days)).strftime("%Y-%m-%d")),
            ).fetchall()
    finally:
        conn.close()

    prior_map = {r["youtube_video_id"]: r for r in prior_rows}

    videos = []
    total_views = 0
    total_likes = 0
    views_gain = 0
    likes_gain = 0
    for r in current_rows:
        yid = r["youtube_video_id"]
        cur_views = int(r["views"] or 0)
        cur_likes = int(r["likes"] or 0)
        cur_comments = int(r["comments"] or 0)
        prior = prior_map.get(yid)
        gain_v = cur_views - int(prior["views"] or 0) if prior else 0
        gain_l = cur_likes - int(prior["likes"] or 0) if prior else 0
        videos.append({
            "youtube_video_id": yid,
            "url": f"https://youtube.com/watch?v={yid}",
            "title": r["title"],
            "published_at": r["published_at"],
            "current_views": cur_views,
            "current_likes": cur_likes,
            "current_comments": cur_comments,
            "views_gain": gain_v,
            "likes_gain": gain_l,
            "source_table": r["source_table"],
            "source_id": int(r["source_id"]),
        })
        total_views += cur_views
        total_likes += cur_likes
        views_gain += gain_v
        likes_gain += gain_l

    # Default sort: most recently uploaded first. Videos with no
    # published_at (older edge cases) sort to the bottom. The frontend
    # offers alternative sorts (most views, most growth) without a
    # round-trip — it reorders the list client-side.
    videos.sort(key=lambda v: v["published_at"] or "", reverse=True)

    # Shape the channel block for the response — None if no snapshot
    # exists yet (post-deploy / OAuth not configured).
    channel_block = None
    if channel_current:
        cur_subs = int(channel_current["subscriber_count"] or 0)
        prior_subs = int(channel_prior["subscriber_count"] or 0) if channel_prior else cur_subs
        channel_block = {
            "channel_id": channel_current["channel_id"],
            "title": channel_current["title"],
            "current_subscribers": cur_subs,
            "current_view_count": int(channel_current["view_count"] or 0),
            "current_video_count": int(channel_current["video_count"] or 0),
            "subscribers_gain": cur_subs - prior_subs,
            "subscribers_daily": [
                {
                    "date": r["d"],
                    "subscribers": int(r["subscriber_count"] or 0),
                }
                for r in channel_daily_rows
            ],
        }

    # Channel-identity sanity block — surface the pinned channel ID
    # and any mismatch detected during the most recent refresh. The
    # frontend uses this to render a red banner when stats are coming
    # from the wrong account (the 2026-05-25 incident).
    conn2 = get_db()
    try:
        pin_row = conn2.execute(
            "SELECT value FROM admin_preferences "
            "WHERE key='youtube_channel_id_pinned'"
        ).fetchone()
        mismatch_row = conn2.execute(
            "SELECT value, updated_at FROM admin_preferences "
            "WHERE key='youtube_channel_mismatch'"
        ).fetchone()
    finally:
        conn2.close()
    pinned_channel_id = pin_row["value"] if pin_row else None
    mismatch = None
    if mismatch_row and mismatch_row["value"]:
        raw = mismatch_row["value"]
        # Format is "<connected_channel_id>|<title>"
        connected_id, _, connected_title = raw.partition("|")
        mismatch = {
            "pinned_channel_id": pinned_channel_id,
            "connected_channel_id": connected_id,
            "connected_title": connected_title or None,
            "detected_at": mismatch_row["updated_at"],
        }

    return jsonify({
        "range": f"{days}d",
        "totals": {
            "videos": len(videos),
            "total_views": total_views,
            "total_likes": total_likes,
            "views_gain_period": views_gain,
            "likes_gain_period": likes_gain,
        },
        "videos": videos,
        "channel": channel_block,
        "pinned_channel_id": pinned_channel_id,
        "channel_mismatch": mismatch,
        "last_refresh": last_refresh,
        "snapshot_count": snapshot_count,
    })


@app.route("/api/admin/stats/youtube/repin", methods=["POST"])
@admin_required
def admin_stats_youtube_repin():
    """Operator action — accept the currently-connected OAuth channel
    as the pinned one. Use after intentionally switching channels.
    Calls the YouTube API now to read the channel_id from `mine=true`,
    overwrites the pinned id, clears the mismatch marker, and runs a
    fresh refresh."""
    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "snippet,statistics", "mine": "true"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if resp.status_code != 200:
        return jsonify({
            "ok": False,
            "error": f"YouTube channels.list returned {resp.status_code}",
        }), 502
    items = resp.json().get("items") or []
    if not items:
        return jsonify({"ok": False, "error": "No channel returned by mine=true"}), 502
    ch = items[0]
    ch_id = ch.get("id")
    title = (ch.get("snippet") or {}).get("title") or ""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
            "VALUES ('youtube_channel_id_pinned', ?, CURRENT_TIMESTAMP)",
            (ch_id,),
        )
        conn.execute(
            "DELETE FROM admin_preferences WHERE key='youtube_channel_mismatch'"
        )
        conn.commit()
    finally:
        conn.close()
    # Fire a fresh refresh so the dashboard reflects the new pin
    # immediately.
    try:
        _refresh_youtube_stats()
    except Exception as e:
        print(f"[youtube-stats] post-repin refresh failed: {e}")
    return jsonify({"ok": True, "channel_id": ch_id, "title": title})


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
        # Detect youtube_refresh_token CHANGING (not just being saved with the
        # same value). When it changes, stamp the save time so the dashboard
        # can warn the admin before the 7-day testing-mode expiry.
        if "youtube_refresh_token" in body:
            new_val = str(body.get("youtube_refresh_token") or "").strip()
            existing = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'youtube_refresh_token'"
            ).fetchone()
            old_val = (existing["value"] if existing else "") or ""
            if new_val and new_val != old_val.strip():
                body["youtube_refresh_token_saved_at"] = datetime.now(timezone.utc).isoformat()

        for k, v in body.items():
            conn.execute(
                "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (str(k), str(v)),
            )
        conn.commit()
        if "claude_api_key" in body:
            _invalidate_claude_key_cache()
        if "voyage_api_key" in body and search_v2 is not None:
            search_v2.invalidate_voyage_key_cache()
        if "google_analytics_id" in body:
            _ga_id_cache["id"] = None
            _ga_id_cache["ts"] = 0.0
        return jsonify({"message": "Saved"})
    finally:
        conn.close()


# =========================================================================
# Admin: Vocabulary Studio
# -------------------------------------------------------------------------
# Admin-driven version of the bias-revision pipeline. Lets the admin
# search a root, run a Stage-0 semantic survey via Claude Opus, edit
# the result, then bulk-apply revisions across the three reader-facing
# surfaces (verse translations, grammar notes, word meanings) with
# per-row revert. Reuses the same logic the CLI scripts use.
# =========================================================================

VOCAB_OPUS_MODEL = "claude-opus-4-8"
VOCAB_SONNET_MODEL = "claude-sonnet-4-6"


def _vocab_get_state(conn, root_bw: str) -> dict | None:
    """Return current term_surveys row for a root + occurrence summary."""
    row = conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, reasoning, "
        "       counter_examples_json, translation_note, leave_untranslated, "
        "       confidence, hard_cases_json, occurrence_count, surveyor_model, "
        "       surveyor_run_at "
        "FROM term_surveys WHERE root_buckwalter = ?",
        (root_bw,),
    ).fetchone()
    if not row:
        return None
    out = dict(row)
    for key in ("counter_examples_json", "hard_cases_json"):
        try:
            out[key.replace("_json", "")] = json.loads(out[key]) if out[key] else []
        except Exception:
            out[key.replace("_json", "")] = []
    return out


def _vocab_count_revisions(conn, root_bw: str) -> dict:
    """How many DB rows for this root would be / are revised across each
    reader surface. Used by the Apply panel to show pending counts."""
    # Verses with hard cases (transliteration applied)
    survey = conn.execute(
        "SELECT hard_cases_json FROM term_surveys WHERE root_buckwalter = ?",
        (root_bw,),
    ).fetchone()
    hard_cases: list[dict] = []
    if survey and survey["hard_cases_json"]:
        try:
            hard_cases = json.loads(survey["hard_cases_json"])
        except Exception:
            hard_cases = []
    hard_refs = [hc.get("ref") for hc in hard_cases if hc.get("ref")]

    # Translations with revised_text from the hard-case pipeline
    # (apply_hard_case_transliterations). Counted separately from the
    # broader Phase-2 verse-translation pipeline below.
    translations_revised = 0
    if hard_refs:
        for ref in hard_refs:
            try:
                ch, vs = ref.split(":")
                ch, vs = int(ch), int(vs)
            except Exception:
                continue
            r = conn.execute(
                "SELECT 1 FROM ai_translations WHERE chapter = ? AND verse = ? "
                "AND revised_text IS NOT NULL LIMIT 1",
                (ch, vs),
            ).fetchone()
            if r:
                translations_revised += 1

    # Verse-translation revisions from revise_verse_translations.
    # Indicator = departure_notes_original IS NOT NULL (set on first
    # revision). Total = verses containing this root that have an
    # ai_translations row, EXCLUDING hard-case verses.
    has_dno_col = any(
        r[1] == "departure_notes_original"
        for r in conn.execute("PRAGMA table_info(ai_translations)")
    )
    verse_translations_revised = 0
    verse_translations_total = 0
    if has_dno_col:
        verse_translations_revised = conn.execute(
            "SELECT COUNT(DISTINCT t.chapter || ':' || t.verse) "
            "FROM ai_translations t "
            "JOIN morphology m ON m.chapter = t.chapter AND m.verse = t.verse "
            "WHERE m.root_buckwalter = ? "
            "  AND t.departure_notes_original IS NOT NULL "
            "  AND t.departure_notes_original != ''",
            (root_bw,),
        ).fetchone()[0]
        # Total: verses with this root + ai_translations row, minus hard cases.
        total_with_translation = conn.execute(
            "SELECT COUNT(DISTINCT t.chapter || ':' || t.verse) "
            "FROM ai_translations t "
            "JOIN morphology m ON m.chapter = t.chapter AND m.verse = t.verse "
            "WHERE m.root_buckwalter = ? AND t.translation_text IS NOT NULL",
            (root_bw,),
        ).fetchone()[0]
        verse_translations_total = total_with_translation - len(hard_refs)
        if verse_translations_total < 0:
            verse_translations_total = 0

    # Grammar notes touched (any verse where notes_markdown_original is set
    # AND verse contains this root in morphology)
    grammar_revised = conn.execute(
        "SELECT COUNT(DISTINCT g.chapter || ':' || g.verse) "
        "FROM ai_grammar_notes g "
        "JOIN morphology m ON m.chapter = g.chapter AND m.verse = g.verse "
        "WHERE g.notes_markdown_original IS NOT NULL AND m.root_buckwalter = ?",
        (root_bw,),
    ).fetchone()[0]

    # Word meanings touched
    word_meanings_revised = conn.execute(
        "SELECT COUNT(*) FROM ai_word_meanings w "
        "JOIN morphology m ON m.chapter = w.chapter AND m.verse = w.verse "
        "                  AND m.word_pos = w.word_pos "
        "WHERE w.meaning_short_original IS NOT NULL AND m.root_buckwalter = ?",
        (root_bw,),
    ).fetchone()[0]

    # Pending: occurrences in the corpus NOT yet revised
    total_word_occurrences = conn.execute(
        "SELECT COUNT(DISTINCT chapter || ':' || verse || '/' || word_pos) "
        "FROM morphology WHERE root_buckwalter = ?",
        (root_bw,),
    ).fetchone()[0]

    # Total candidates the Phase-2 revisers can touch (joins narrow the
    # set vs. raw morphology counts: ai_word_meanings might be missing a
    # row; ai_grammar_notes is per-verse, not per-word).
    word_meanings_total = conn.execute(
        "SELECT COUNT(*) FROM ai_word_meanings w "
        "JOIN morphology m ON m.chapter = w.chapter AND m.verse = w.verse "
        "                  AND m.word_pos = w.word_pos "
        "WHERE m.root_buckwalter = ?",
        (root_bw,),
    ).fetchone()[0]

    grammar_notes_total = conn.execute(
        "SELECT COUNT(DISTINCT g.chapter || ':' || g.verse) "
        "FROM ai_grammar_notes g "
        "JOIN morphology m ON m.chapter = g.chapter AND m.verse = g.verse "
        "WHERE m.root_buckwalter = ? AND g.notes_markdown IS NOT NULL",
        (root_bw,),
    ).fetchone()[0]

    return {
        "hard_cases_total": len(hard_refs),
        "translations_revised": translations_revised,
        "verse_translations_revised": verse_translations_revised,
        "verse_translations_total": verse_translations_total,
        "grammar_notes_revised": grammar_revised,
        "grammar_notes_total": grammar_notes_total,
        "word_meanings_revised": word_meanings_revised,
        "word_meanings_total": word_meanings_total,
        "total_word_occurrences": total_word_occurrences,
    }


@app.route("/api/admin/vocab/<root_bw>", methods=["GET"])
@admin_required
def admin_vocab_state(root_bw: str):
    """Return everything the studio needs for one root."""
    conn = get_db()
    try:
        state = _vocab_get_state(conn, root_bw)
        # Occurrences (for the survey panel)
        occ_rows = conn.execute(
            "SELECT m.chapter, m.verse, m.word_pos, m.form_arabic, m.pos, "
            "       v.text_uthmani, t.translation_text, t.revised_text "
            "FROM morphology m "
            "JOIN verses v ON v.chapter = m.chapter AND v.verse = m.verse "
            "LEFT JOIN ai_translations t ON t.chapter = m.chapter "
            "                            AND t.verse = m.verse "
            "WHERE m.root_buckwalter = ? "
            "GROUP BY m.chapter, m.verse, m.word_pos "
            "ORDER BY m.chapter, m.verse, m.word_pos",
            (root_bw,),
        ).fetchall()
        occurrences = [{
            "chapter": r["chapter"],
            "verse": r["verse"],
            "word_pos": r["word_pos"],
            "arabic_word": r["form_arabic"],
            "pos": r["pos"],
            "translation": (r["revised_text"] or r["translation_text"] or "")[:240],
        } for r in occ_rows]

        root_arabic = (state and state["root_arabic"]) or _root_arabic_map.get(root_bw, "")
        revisions = _vocab_count_revisions(conn, root_bw)

        return jsonify({
            "root_buckwalter": root_bw,
            "root_arabic": root_arabic,
            "occurrences": occurrences,
            "occurrence_count": len(occurrences),
            "survey": state,
            "revisions": revisions,
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/survey", methods=["POST"])
@admin_required
def admin_vocab_run_survey(root_bw: str):
    """Run a Claude Opus Stage-0 survey for this root. Body may include:
        { "model": "claude-opus-4-8", "extra_constraint": "...", "force": false }
    Writes the result to term_surveys (creates or overwrites)."""
    body = request.get_json(silent=True) or {}
    model = body.get("model") or VOCAB_OPUS_MODEL
    extra = body.get("extra_constraint") or ""
    force = bool(body.get("force"))

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    # Lazy import to avoid circular issues at startup
    import term_survey

    conn = get_db()
    try:
        # If already surveyed and not forcing, return existing
        existing = conn.execute(
            "SELECT id FROM term_surveys WHERE root_buckwalter = ?", (root_bw,)
        ).fetchone()
        if existing and not force:
            return jsonify({"error": "Already surveyed; pass force=true to overwrite",
                            "existing_id": existing["id"]}), 409

        occurrences = term_survey.pull_occurrences(
            conn, root_bw, term_survey.DEFAULT_TRANSLATION_CONFIG,
        )
        if not occurrences:
            return jsonify({"error": "No occurrences in morphology for this root"}), 404

        root_arabic = _root_arabic_map.get(root_bw, root_bw)
        prompt = term_survey.build_user_prompt(
            root_bw, root_arabic, "", occurrences, extra,
        )
        try:
            raw, ms = term_survey.call_claude(
                model, term_survey.SYSTEM_PROMPT, prompt, api_key,
            )
            parsed = term_survey.parse_response(raw)
        except Exception as e:
            return jsonify({"error": f"Survey call failed: {e}"}), 502

        wrote = term_survey.save_survey(
            conn, root_bw, root_arabic, occurrences,
            model, "v1", parsed, raw, force=True,
        )
        if not wrote:
            return jsonify({"error": "save_survey returned False unexpectedly"}), 500

        return jsonify({
            "ok": True,
            "elapsed_ms": ms,
            "model": model,
            "state": _vocab_get_state(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>", methods=["PUT"])
@admin_required
def admin_vocab_save_edits(root_bw: str):
    """Admin edits to canonical_english / reasoning / translation_note /
    leave_untranslated / confidence after the survey ran. Body:
        { canonical_english, reasoning, translation_note,
          leave_untranslated, confidence, counter_examples,
          hard_cases }"""
    body = request.get_json(silent=True) or {}
    fields: list[tuple[str, object]] = []

    def _set(col: str, val):
        fields.append((col, val))

    if "canonical_english" in body:
        _set("canonical_english", str(body["canonical_english"]).strip())
    if "reasoning" in body:
        _set("reasoning", str(body["reasoning"]).strip())
    if "translation_note" in body:
        _set("translation_note", str(body["translation_note"]).strip())
    if "leave_untranslated" in body:
        _set("leave_untranslated", 1 if body["leave_untranslated"] else 0)
    if "confidence" in body:
        try:
            _set("confidence", float(body["confidence"]))
        except Exception:
            pass
    if "counter_examples" in body and isinstance(body["counter_examples"], list):
        _set("counter_examples_json",
             json.dumps(body["counter_examples"], ensure_ascii=False))
    if "hard_cases" in body and isinstance(body["hard_cases"], list):
        _set("hard_cases_json",
             json.dumps(body["hard_cases"], ensure_ascii=False))

    if not fields:
        return jsonify({"error": "No editable fields in body"}), 400

    conn = get_db()
    try:
        sql = ("UPDATE term_surveys SET " +
               ", ".join(f"{c} = ?" for c, _ in fields) +
               " WHERE root_buckwalter = ?")
        conn.execute(sql, [v for _, v in fields] + [root_bw])
        conn.commit()
        return jsonify({"ok": True, "state": _vocab_get_state(conn, root_bw)})
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/apply-transliteration", methods=["POST"])
@admin_required
def admin_vocab_apply_transliteration(root_bw: str):
    """Apply transliteration to all hard-case verses for this root. Uses
    Claude Sonnet (as the existing apply_hard_case_transliterations.py
    script). Returns per-verse results."""
    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    import apply_hard_case_transliterations as ahct

    conn = get_db()
    try:
        survey_row = conn.execute(
            "SELECT hard_cases_json, root_arabic, canonical_english "
            "FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not survey_row or not survey_row["hard_cases_json"]:
            return jsonify({"error": "No hard cases for this root"}), 404

        try:
            cases = json.loads(survey_row["hard_cases_json"])
        except Exception:
            cases = []
        results = []
        for hc in cases:
            ref = hc.get("ref", "")
            m = re.match(r"^(\d+):(\d+)$", ref)
            if not m:
                continue
            ch, vs = int(m.group(1)), int(m.group(2))
            case = {
                "chapter": ch, "verse": vs,
                "root_bw": root_bw,
                "root_arabic": survey_row["root_arabic"],
                "canonical_english": survey_row["canonical_english"],
                "arabic_word": hc.get("arabic_word"),
                "transliteration": hc.get("transliteration"),
                "reason": hc.get("reason"),
            }
            outcome = ahct.apply_one(
                conn, case, VOCAB_SONNET_MODEL, api_key,
                ahct.DEFAULT_TRANSLATION_CONFIG,
                dry_run=False, force=True,
            )
            results.append({"ref": ref, "outcome": outcome})

        return jsonify({"ok": True, "results": results,
                        "revisions": _vocab_count_revisions(conn, root_bw)})
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revert-transliteration/<int:chapter>/<int:verse>",
           methods=["POST"])
@admin_required
def admin_vocab_revert_transliteration(root_bw: str, chapter: int, verse: int):
    """Clear ai_translations.revised_text for one (chapter, verse).
    The original translation_text remains intact."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE ai_translations SET revised_text = NULL "
            "WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        )
        conn.commit()
        return jsonify({"ok": True,
                        "revisions": _vocab_count_revisions(conn, root_bw)})
    finally:
        conn.close()


# ---- Phase 2: bulk-apply revisions across reader surfaces ----------------
# Three reader-facing surfaces use the surveyed canonical:
#   1. term_surveys.translation_note      (single-row regeneration)
#   2. ai_word_meanings rows for this root (per-word revision, chunked)
#   3. ai_grammar_notes rows for verses that contain this root (chunked)
#
# Each chunked endpoint takes optional { limit, force } and returns
# { processed, revised, errors, remaining, samples }. The frontend keeps
# calling until remaining == 0.
#
# Both word-meanings and grammar-notes have *_original backup columns
# (created by the underlying CLI scripts on first run). The revert
# endpoints copy *_original back into the active column for every row
# under this root, then clear *_original.


def _vocab_collect_word_meanings_targets(conn, root_bw: str, force: bool) -> list[dict]:
    """ai_word_meanings rows joined to morphology where root = root_bw.
    If not force, excludes rows already revised (meaning_short_original set)."""
    rows = conn.execute(
        "SELECT w.id, w.chapter, w.verse, w.word_pos, "
        "       w.meaning_short, w.meaning_detailed, w.preferred_translation, "
        "       w.meaning_short_original, w.preferred_source, "
        "       m.root_buckwalter, m.root_arabic, m.form_arabic, m.pos, m.tag "
        "FROM ai_word_meanings w "
        "JOIN morphology m ON m.chapter = w.chapter AND m.verse = w.verse "
        "                  AND m.word_pos = w.word_pos "
        "WHERE m.root_buckwalter = ? "
        "GROUP BY w.id "
        "ORDER BY w.chapter, w.verse, w.word_pos",
        (root_bw,),
    ).fetchall()
    out = [dict(r) for r in rows]
    if not force:
        out = [r for r in out if not r.get("meaning_short_original")]
    return out


def _vocab_collect_grammar_targets(
    conn, root_bw: str, force: bool,
) -> list[tuple[int, int]]:
    """Distinct (chapter, verse) pairs where the verse contains this root
    AND has a grammar note. If not force, excludes already-revised."""
    sql = (
        "SELECT DISTINCT g.chapter, g.verse "
        "FROM ai_grammar_notes g "
        "JOIN morphology m ON m.chapter = g.chapter AND m.verse = g.verse "
        "WHERE m.root_buckwalter = ? AND g.notes_markdown IS NOT NULL "
    )
    if not force:
        sql += "AND (g.notes_markdown_original IS NULL OR g.notes_markdown_original = '') "
    sql += "ORDER BY g.chapter, g.verse"
    rows = conn.execute(sql, (root_bw,)).fetchall()
    return [(r["chapter"], r["verse"]) for r in rows]


@app.route("/api/admin/vocab/<root_bw>/regenerate-translation-note", methods=["POST"])
@admin_required
def admin_vocab_regenerate_translation_note(root_bw: str):
    """Re-generate the reader-facing translation_note for this survey using
    the canonical_english + reasoning + counter_examples already on file.
    Single Claude Sonnet call, ~5 sec, ~$0.01.
    Body (optional): { model }"""
    body = request.get_json(silent=True) or {}
    model = body.get("model") or VOCAB_SONNET_MODEL

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    import regenerate_translation_notes as rtn

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not row:
            return jsonify({"error": "No survey for this root yet"}), 404
        try:
            t0 = time.time()
            rtn.regenerate_for_row(conn, dict(row), model, api_key, dry_run=False)
            elapsed_ms = int((time.time() - t0) * 1000)
        except Exception as e:
            return jsonify({"error": f"Regeneration failed: {e}"}), 502

        # Re-read to get the new note
        new_note = conn.execute(
            "SELECT translation_note FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        return jsonify({
            "ok": True,
            "elapsed_ms": elapsed_ms,
            "model": model,
            "translation_note": new_note["translation_note"] if new_note else None,
            "state": _vocab_get_state(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revise-word-meanings", methods=["POST"])
@admin_required
def admin_vocab_revise_word_meanings(root_bw: str):
    """Run revise_word_meanings.revise_one on up to <limit> ai_word_meanings
    rows for this root. Idempotent: skips rows already revised unless
    force=true. Returns progress so the UI can keep calling.
    Body: { limit?: 20, force?: false }"""
    body = request.get_json(silent=True) or {}
    limit = max(1, min(50, int(body.get("limit") or 20)))
    force = bool(body.get("force"))

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    import revise_word_meanings as rwm

    conn = get_db()
    try:
        canon_row = conn.execute(
            "SELECT root_buckwalter, root_arabic, canonical_english, "
            "       translation_note, hard_cases_json "
            "FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not canon_row:
            return jsonify({"error": "No survey for this root yet"}), 404
        if not canon_row["canonical_english"]:
            return jsonify({"error": "Survey has no canonical_english yet"}), 400

        canon = dict(canon_row)
        # hard-case index for THIS root only
        try:
            cases = json.loads(canon_row["hard_cases_json"] or "[]")
        except Exception:
            cases = []
        hc_index: dict[tuple[str, int, int], dict] = {}
        for hc in cases:
            ref = hc.get("ref", "")
            m = re.match(r"^(\d+):(\d+)$", ref)
            if not m:
                continue
            hc_index[(root_bw, int(m.group(1)), int(m.group(2)))] = {
                "root_buckwalter": root_bw,
                "root_arabic": canon_row["root_arabic"],
                "canonical_english": canon_row["canonical_english"],
                "arabic_word": hc.get("arabic_word"),
                "transliteration": hc.get("transliteration"),
                "reason": hc.get("reason"),
            }

        all_targets = _vocab_collect_word_meanings_targets(conn, root_bw, force)
        total_pending_before = len(all_targets)
        batch = all_targets[:limit]

        revised, errors = 0, 0
        samples: list[dict] = []
        # errors_detail: per-row failure reasons. Surfaces what would
        # otherwise only land in stderr, so the UI can show the operator
        # exactly which rows failed and why (HTTP 5xx, malformed JSON, etc.).
        errors_detail: list[dict] = []
        t0 = time.time()
        for row in batch:
            hc = hc_index.get((root_bw, row["chapter"], row["verse"]))
            before_short = row.get("meaning_short", "")
            ref = f"{row['chapter']}:{row['verse']}/p{row['word_pos']}"
            err_msg: str | None = None
            outcome = "error"
            try:
                outcome = rwm.revise_one(
                    conn, row, hc, canon, VOCAB_SONNET_MODEL, api_key, dry_run=False,
                )
                if outcome == "error":
                    # revise_one swallowed the exception and returned "error".
                    # Best we can do is a generic note.
                    err_msg = "revise_one returned 'error' — see container stderr for details"
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                print(f"[vocab/word-meanings] {ref} {err_msg}", file=sys.stderr)
            if outcome == "revised":
                revised += 1
                # Re-read to capture what got written
                new_short = conn.execute(
                    "SELECT meaning_short FROM ai_word_meanings WHERE id = ?",
                    (row["id"],),
                ).fetchone()
                samples.append({
                    "ref": ref,
                    "before": before_short,
                    "after": new_short["meaning_short"] if new_short else "",
                    "hard_case": hc is not None,
                })
            else:
                errors += 1
                errors_detail.append({
                    "ref": ref,
                    "hard_case": hc is not None,
                    "message": (err_msg or outcome)[:300],
                })

        elapsed_ms = int((time.time() - t0) * 1000)
        remaining = max(0, total_pending_before - len(batch))
        return jsonify({
            "ok": True,
            "processed": len(batch),
            "revised": revised,
            "errors": errors,
            "remaining": remaining,
            "elapsed_ms": elapsed_ms,
            "samples": samples[:5],
            "errors_detail": errors_detail[:10],
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revert-word-meanings", methods=["POST"])
@admin_required
def admin_vocab_revert_word_meanings(root_bw: str):
    """Restore meaning_short / meaning_detailed / preferred_translation
    from their *_original backups for every ai_word_meanings row joined to
    morphology with this root. Clears the *_original columns so a future
    revise call sees the row as unrevised."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT w.id "
            "FROM ai_word_meanings w "
            "JOIN morphology m ON m.chapter = w.chapter AND m.verse = w.verse "
            "                  AND m.word_pos = w.word_pos "
            "WHERE m.root_buckwalter = ? "
            "  AND w.meaning_short_original IS NOT NULL",
            (root_bw,),
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(
                f"UPDATE ai_word_meanings SET "
                f"  meaning_short = meaning_short_original, "
                f"  meaning_detailed = meaning_detailed_original, "
                f"  preferred_translation = preferred_translation_original, "
                f"  meaning_short_original = NULL, "
                f"  meaning_detailed_original = NULL, "
                f"  preferred_translation_original = NULL "
                f"WHERE id IN ({placeholders})",
                ids,
            )
            conn.commit()
        return jsonify({
            "ok": True,
            "reverted": len(ids),
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revise-grammar-notes", methods=["POST"])
@admin_required
def admin_vocab_revise_grammar_notes(root_bw: str):
    """Run revise_grammar_notes.revise_one on up to <limit> verses where
    this root appears AND a grammar note exists. Body: { limit?: 20, force?: false }"""
    body = request.get_json(silent=True) or {}
    limit = max(1, min(50, int(body.get("limit") or 20)))
    force = bool(body.get("force"))

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    import revise_grammar_notes as rgn

    conn = get_db()
    try:
        # Make sure backup column exists (idempotent)
        rgn.ensure_backup_column(conn)

        canon_row = conn.execute(
            "SELECT canonical_english FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not canon_row or not canon_row["canonical_english"]:
            return jsonify({"error": "No surveyed canonical for this root yet"}), 404

        all_targets = _vocab_collect_grammar_targets(conn, root_bw, force)
        total_pending_before = len(all_targets)
        batch = all_targets[:limit]

        revised, errors = 0, 0
        samples: list[dict] = []
        errors_detail: list[dict] = []
        t0 = time.time()
        for ch, vs in batch:
            before_row = conn.execute(
                "SELECT notes_markdown FROM ai_grammar_notes WHERE chapter=? AND verse=?",
                (ch, vs),
            ).fetchone()
            before_md = before_row["notes_markdown"] if before_row else ""
            ref = f"{ch}:{vs}"
            err_msg: str | None = None
            outcome = "error"
            try:
                outcome = rgn.revise_one(
                    conn, ch, vs, [root_bw],
                    VOCAB_SONNET_MODEL, api_key,
                    dry_run=False, force=force,
                )
                if outcome == "error":
                    err_msg = "revise_one returned 'error' — see container stderr for details"
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                print(f"[vocab/grammar-notes] {ref} {err_msg}", file=sys.stderr)
            if outcome == "revised":
                revised += 1
                after_row = conn.execute(
                    "SELECT notes_markdown FROM ai_grammar_notes WHERE chapter=? AND verse=?",
                    (ch, vs),
                ).fetchone()
                samples.append({
                    "ref": ref,
                    "before": (before_md or "")[:200],
                    "after": (after_row["notes_markdown"] if after_row else "")[:200],
                })
            elif isinstance(outcome, str) and outcome.startswith("skip"):
                pass  # already revised or no canon — not an error
            else:
                errors += 1
                errors_detail.append({
                    "ref": ref,
                    "message": (err_msg or str(outcome))[:300],
                })

        elapsed_ms = int((time.time() - t0) * 1000)
        remaining = max(0, total_pending_before - len(batch))
        return jsonify({
            "ok": True,
            "processed": len(batch),
            "revised": revised,
            "errors": errors,
            "remaining": remaining,
            "elapsed_ms": elapsed_ms,
            "samples": samples[:5],
            "errors_detail": errors_detail[:10],
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revert-grammar-notes", methods=["POST"])
@admin_required
def admin_vocab_revert_grammar_notes(root_bw: str):
    """Restore notes_markdown from notes_markdown_original for every
    ai_grammar_notes row whose verse contains this root."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT g.chapter, g.verse "
            "FROM ai_grammar_notes g "
            "JOIN morphology m ON m.chapter = g.chapter AND m.verse = g.verse "
            "WHERE m.root_buckwalter = ? "
            "  AND g.notes_markdown_original IS NOT NULL "
            "  AND g.notes_markdown_original != ''",
            (root_bw,),
        ).fetchall()
        reverted = 0
        for r in rows:
            conn.execute(
                "UPDATE ai_grammar_notes SET "
                "  notes_markdown = notes_markdown_original, "
                "  notes_markdown_original = NULL "
                "WHERE chapter = ? AND verse = ?",
                (r["chapter"], r["verse"]),
            )
            reverted += 1
        conn.commit()
        return jsonify({
            "ok": True,
            "reverted": reverted,
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revise-verse-translations", methods=["POST"])
@admin_required
def admin_vocab_revise_verse_translations(root_bw: str):
    """Run revise_verse_translations.revise_one on up to <limit> verses
    where this root appears (excluding hard-case verses, which are
    handled by apply_hard_case_transliterations).
    Body: { limit?: 20, force?: false }"""
    body = request.get_json(silent=True) or {}
    limit = max(1, min(50, int(body.get("limit") or 20)))
    force = bool(body.get("force"))

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    import revise_verse_translations as rvt

    conn = get_db()
    try:
        rvt.ensure_backup_columns(conn)

        survey = conn.execute(
            "SELECT root_buckwalter, root_arabic, canonical_english, translation_note "
            "FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not survey or not survey["canonical_english"]:
            return jsonify({"error": "No surveyed canonical for this root yet"}), 404

        all_targets = rvt.collect_targets(conn, root_bw, force)
        total_pending_before = len(all_targets)
        batch = all_targets[:limit]

        revised, errors = 0, 0
        samples: list[dict] = []
        errors_detail: list[dict] = []
        t0 = time.time()
        for ch, vs in batch:
            ref = f"{ch}:{vs}"
            before_row = conn.execute(
                "SELECT translation_text, revised_text FROM ai_translations "
                "WHERE chapter = ? AND verse = ?",
                (ch, vs),
            ).fetchone()
            before_trans = ((before_row["revised_text"] if before_row else None)
                            or (before_row["translation_text"] if before_row else "")
                            or "")
            err_msg: str | None = None
            outcome = "error"
            try:
                outcome = rvt.revise_one(
                    conn, ch, vs,
                    survey["root_buckwalter"], survey["root_arabic"],
                    survey["canonical_english"], survey["translation_note"] or "",
                    VOCAB_SONNET_MODEL, api_key,
                    dry_run=False, force=force,
                )
                if outcome == "error":
                    err_msg = "revise_one returned 'error' — see container stderr for details"
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                print(f"[vocab/verse-translations] {ref} {err_msg}", file=sys.stderr)
            if outcome == "revised":
                revised += 1
                after_row = conn.execute(
                    "SELECT revised_text FROM ai_translations "
                    "WHERE chapter = ? AND verse = ?",
                    (ch, vs),
                ).fetchone()
                samples.append({
                    "ref": ref,
                    "before": (before_trans or "")[:200],
                    "after": ((after_row["revised_text"] if after_row else "") or "")[:200],
                })
            elif isinstance(outcome, str) and outcome.startswith("skip"):
                pass
            else:
                errors += 1
                errors_detail.append({
                    "ref": ref,
                    "message": (err_msg or str(outcome))[:300],
                })

        elapsed_ms = int((time.time() - t0) * 1000)
        remaining = max(0, total_pending_before - len(batch))
        return jsonify({
            "ok": True,
            "processed": len(batch),
            "revised": revised,
            "errors": errors,
            "remaining": remaining,
            "elapsed_ms": elapsed_ms,
            "samples": samples[:5],
            "errors_detail": errors_detail[:10],
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


@app.route("/api/admin/vocab/<root_bw>/revert-verse-translations", methods=["POST"])
@admin_required
def admin_vocab_revert_verse_translations(root_bw: str):
    """Restore departure_notes from departure_notes_original and clear
    revised_text for every ai_translations row whose verse contains this
    root. translation_text was never touched, so revised_text=NULL puts
    the original back via _best_translation's COALESCE."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT t.chapter, t.verse "
            "FROM ai_translations t "
            "JOIN morphology m ON m.chapter = t.chapter AND m.verse = t.verse "
            "WHERE m.root_buckwalter = ? "
            "  AND t.departure_notes_original IS NOT NULL "
            "  AND t.departure_notes_original != ''",
            (root_bw,),
        ).fetchall()
        reverted = 0
        for r in rows:
            conn.execute(
                "UPDATE ai_translations SET "
                "  departure_notes = departure_notes_original, "
                "  departure_notes_original = NULL, "
                "  revised_text = NULL "
                "WHERE chapter = ? AND verse = ?",
                (r["chapter"], r["verse"]),
            )
            reverted += 1
        conn.commit()
        return jsonify({
            "ok": True,
            "reverted": reverted,
            "revisions": _vocab_count_revisions(conn, root_bw),
        })
    finally:
        conn.close()


# =========================================================================
# Admin: Proper Nouns review queue
# -------------------------------------------------------------------------
# Two-stage detection pipeline. Stage 0 (mechanical) and Stage 1 (Ollama
# cloud) live in proper_noun_detect.py; Stage 2 (Sonnet adjudication) in
# proper_noun_adjudicate.py. The endpoints here drive them from the admin
# UI and host the operator review + apply/revert flow.
#
# Apply pattern: on approve, we capture the row's CURRENT preferred_
# translation in applied_to_verses_json so revert is self-contained — no
# need for a parallel *_original_pn column collision with the vocab
# studio's backups.
# =========================================================================


def _pn_get_stats(conn) -> dict:
    """Counts that drive the dashboard at the top of the review queue."""
    row = conn.execute(
        "SELECT "
        "  COUNT(*) AS total, "
        "  SUM(CASE WHEN stage1_run_at IS NOT NULL THEN 1 ELSE 0 END) AS stage1_done, "
        "  SUM(CASE WHEN stage2_run_at IS NOT NULL THEN 1 ELSE 0 END) AS stage2_done, "
        "  SUM(CASE WHEN sonnet_verdict = 'literal' THEN 1 ELSE 0 END) AS literal, "
        "  SUM(CASE WHEN sonnet_verdict = 'name' THEN 1 ELSE 0 END) AS name, "
        "  SUM(CASE WHEN sonnet_verdict = 'ambiguous' THEN 1 ELSE 0 END) AS ambiguous, "
        "  SUM(CASE WHEN operator_action = 'approved' THEN 1 ELSE 0 END) AS approved, "
        "  SUM(CASE WHEN operator_action = 'rejected' THEN 1 ELSE 0 END) AS rejected, "
        "  SUM(CASE WHEN applied_at IS NOT NULL THEN 1 ELSE 0 END) AS applied "
        "FROM proper_noun_candidates"
    ).fetchone()
    return {k: int(row[k] or 0) for k in row.keys()}


def _pn_serialize(c) -> dict:
    """Turn a sqlite3.Row into a JSON-safe dict, parsing JSON columns."""
    out = dict(c)
    for k in ("sonnet_alternatives_json", "sonnet_supporting_refs_json", "applied_to_verses_json"):
        try:
            out[k.replace("_json", "")] = json.loads(out[k]) if out.get(k) else []
        except Exception:
            out[k.replace("_json", "")] = []
    return out


@app.route("/api/admin/proper-nouns", methods=["GET"])
@admin_required
def admin_pn_list():
    """List candidates with optional filters.
    Query params:
      status        = pending | adjudicated | approved | rejected | applied
      verdict       = literal | name | ambiguous (Sonnet's verdict)
      type          = compound | single
      root          = Buckwalter root
      limit         = (default 200; max 1000)
      offset        = (default 0)
      order         = recent | rooted | random (default: rooted = root, ref)
    """
    status = (request.args.get("status") or "").strip().lower()
    verdict = (request.args.get("verdict") or "").strip().lower()
    ctype = (request.args.get("type") or "").strip().lower()
    root = (request.args.get("root") or "").strip()
    limit = max(1, min(1000, int(request.args.get("limit") or 200)))
    offset = max(0, int(request.args.get("offset") or 0))
    order = (request.args.get("order") or "rooted").strip().lower()

    where, params = ["1=1"], []
    if status == "pending":
        where.append("stage2_run_at IS NULL")
    elif status == "adjudicated":
        where.append("stage2_run_at IS NOT NULL AND operator_action IS NULL")
    elif status == "approved":
        where.append("operator_action = 'approved' AND applied_at IS NULL")
    elif status == "rejected":
        where.append("operator_action = 'rejected'")
    elif status == "applied":
        where.append("applied_at IS NOT NULL")
    if verdict in ("literal", "name", "ambiguous"):
        where.append("sonnet_verdict = ?")
        params.append(verdict)
    if ctype in ("compound", "single", "phrase"):
        where.append("candidate_type = ?")
        params.append(ctype)
    if root:
        where.append("root_buckwalter = ?")
        params.append(root)

    order_sql = {
        "recent": "ORDER BY id DESC",
        "rooted": "ORDER BY root_buckwalter, chapter, verse, word_pos",
        "random": "ORDER BY RANDOM()",
    }.get(order, "ORDER BY root_buckwalter, chapter, verse, word_pos")

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE "
            + " AND ".join(where) + f" {order_sql} LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM proper_noun_candidates WHERE "
            + " AND ".join(where), params
        ).fetchone()["n"]
        return jsonify({
            "candidates": [_pn_serialize(r) for r in rows],
            "total_matched": int(total),
            "limit": limit, "offset": offset,
            "stats": _pn_get_stats(conn),
        })
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/detect", methods=["POST"])
@admin_required
def admin_pn_detect():
    """Stage 0 mechanical pre-filter. Sync — runs in ~10-30s; inserts
    new rows where missing (idempotent). Returns counts."""
    import proper_noun_detect as pnd
    conn = get_db()
    try:
        stats = pnd.stage0_detect(conn)
        return jsonify({"ok": True, **stats, "summary": _pn_get_stats(conn)})
    except Exception as e:
        return jsonify({"error": f"Stage 0 failed: {e}"}), 500
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/run-ollama", methods=["POST"])
@admin_required
def admin_pn_run_ollama():
    """Stage 1: run Ollama cloud (Qwen and/or gpt-oss) on a chunk of
    candidates without stage1_run_at.
    Body: { limit?: 5, models?: 'qwen' | 'qwen,gptoss', refresh?: false }"""
    body = request.get_json(silent=True) or {}
    limit = max(1, min(20, int(body.get("limit") or 5)))
    models = body.get("models") or "qwen"
    if isinstance(models, str):
        models = [m.strip() for m in models.split(",") if m.strip()]
    refresh = bool(body.get("refresh"))

    conn = get_db()
    try:
        api_key_row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key='ollama_api_key'"
        ).fetchone()
        api_key = (api_key_row["value"] if api_key_row else "") or ""
        if not api_key:
            return jsonify({"error": "No ollama_api_key in admin_preferences."}), 400

        import proper_noun_detect as pnd
        # Find pending count BEFORE running so the UI knows remaining
        pending_before = conn.execute(
            "SELECT COUNT(*) AS n FROM proper_noun_candidates "
            + ("" if refresh else "WHERE stage1_run_at IS NULL")
        ).fetchone()["n"]

        t0 = time.time()
        stats = pnd.stage1_run(conn, api_key, models, limit, refresh)
        elapsed_ms = int((time.time() - t0) * 1000)

        remaining = max(0, int(pending_before) - int(stats.get("total", 0)))
        return jsonify({
            "ok": True,
            "processed": int(stats.get("total", 0)),
            "qwen_ok": stats.get("qwen_ok", 0),
            "qwen_err": stats.get("qwen_err", 0),
            "gptoss_ok": stats.get("gptoss_ok", 0),
            "gptoss_err": stats.get("gptoss_err", 0),
            "remaining": remaining,
            "elapsed_ms": elapsed_ms,
            "summary": _pn_get_stats(conn),
        })
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/run-sonnet", methods=["POST"])
@admin_required
def admin_pn_run_sonnet():
    """Stage 2: Claude Sonnet adjudication on a chunk of candidates that
    have stage1 done but not stage2. Body: { limit?: 5, only_disagreement?: false, refresh?: false }"""
    body = request.get_json(silent=True) or {}
    limit = max(1, min(20, int(body.get("limit") or 5)))
    refresh = bool(body.get("refresh"))
    only_disagreement = bool(body.get("only_disagreement"))

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "No CLAUDE_API_KEY in admin_preferences."}), 400

    conn = get_db()
    try:
        import proper_noun_adjudicate as pna
        targets = pna.collect_targets(conn, refresh, only_disagreement)
        total_pending_before = len(targets)
        batch = targets[:limit]

        t0 = time.time()
        adjudicated, errors = 0, 0
        errors_detail: list[dict] = []
        for c in batch:
            ref = f"{c['chapter']}:{c['verse']}/p{c['word_pos']}"
            try:
                outcome = pna.adjudicate_one(conn, c, pna.DEFAULT_MODEL, api_key, dry_run=False)
                if outcome == "adjudicated":
                    adjudicated += 1
                else:
                    errors += 1
                    errors_detail.append({"ref": ref, "message": outcome})
            except Exception as e:
                errors += 1
                msg = f"{type(e).__name__}: {e}"
                errors_detail.append({"ref": ref, "message": msg[:300]})
                print(f"[pn/sonnet] {ref} {msg}", file=sys.stderr)

        elapsed_ms = int((time.time() - t0) * 1000)
        remaining = max(0, total_pending_before - len(batch))
        return jsonify({
            "ok": True,
            "processed": len(batch),
            "adjudicated": adjudicated,
            "errors": errors,
            "errors_detail": errors_detail[:10],
            "remaining": remaining,
            "elapsed_ms": elapsed_ms,
            "summary": _pn_get_stats(conn),
        })
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/<int:cid>", methods=["POST"])
@admin_required
def admin_pn_review(cid: int):
    """Operator review action.
    Body: { action: 'approved'|'rejected'|'edited', translation?: str, notes?: str }"""
    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip().lower()
    if action not in ("approved", "rejected", "edited"):
        return jsonify({"error": "action must be approved/rejected/edited"}), 400
    translation = (body.get("translation") or "").strip() or None
    notes = (body.get("notes") or "").strip() or None
    if action in ("approved", "edited") and not translation:
        return jsonify({"error": "approved/edited actions require a translation"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        if not row:
            return jsonify({"error": "candidate not found"}), 404
        conn.execute(
            "UPDATE proper_noun_candidates SET "
            "  operator_action = ?, operator_translation = ?, operator_notes = ?, "
            "  reviewed_at = datetime('now') "
            "WHERE id = ?",
            (action, translation, notes, cid),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        return jsonify({"ok": True, "candidate": _pn_serialize(updated)})
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/<int:cid>/apply", methods=["POST"])
@admin_required
def admin_pn_apply(cid: int):
    """Apply an approved/edited candidate's translation to ai_word_meanings.
    Captures the prior preferred_translation so revert is self-contained.
    Returns the updated candidate row."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        if not row:
            return jsonify({"error": "candidate not found"}), 404
        if row["operator_action"] not in ("approved", "edited"):
            return jsonify({"error": "candidate is not approved/edited"}), 400
        translation = row["operator_translation"]
        if not translation:
            return jsonify({"error": "no operator_translation set"}), 400
        if row["applied_at"]:
            return jsonify({"error": "already applied"}), 409

        # Capture the original BEFORE updating.
        wm = conn.execute(
            "SELECT id, preferred_translation, preferred_source "
            "FROM ai_word_meanings "
            "WHERE chapter = ? AND verse = ? AND word_pos = ?",
            (row["chapter"], row["verse"], row["word_pos"]),
        ).fetchone()
        if not wm:
            return jsonify({
                "error": (
                    f"no ai_word_meanings row at "
                    f"{row['chapter']}:{row['verse']}/p{row['word_pos']} — "
                    "cannot apply"
                )
            }), 404

        applied_to: list[dict] = [{
            "chapter": row["chapter"],
            "verse": row["verse"],
            "word_pos": row["word_pos"],
            "original_translation": wm["preferred_translation"],
            "original_source": wm["preferred_source"],
        }]
        conn.execute(
            "UPDATE ai_word_meanings SET "
            "  preferred_translation = ?, "
            "  preferred_source = 'proper_noun_pipeline' "
            "WHERE id = ?",
            (translation, wm["id"]),
        )
        conn.execute(
            "UPDATE proper_noun_candidates SET "
            "  applied_at = datetime('now'), applied_to_verses_json = ? "
            "WHERE id = ?",
            (json.dumps(applied_to), cid),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        return jsonify({"ok": True, "candidate": _pn_serialize(updated),
                        "summary": _pn_get_stats(conn)})
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/clear", methods=["POST"])
@admin_required
def admin_pn_clear():
    """Wipe the entire proper_noun_candidates table. Useful when
    re-running Stage 0 after a heuristic update. By default refuses if
    any candidate has reviewed/adjudicated/applied state — operator must
    pass {force: true} to override (and any applied translations should
    be reverted first via the per-row revert)."""
    body = request.get_json(silent=True) or {}
    force = bool(body.get("force"))
    conn = get_db()
    try:
        protected = conn.execute(
            "SELECT COUNT(*) AS n FROM proper_noun_candidates "
            "WHERE applied_at IS NOT NULL "
            "   OR operator_action IS NOT NULL "
            "   OR stage2_run_at IS NOT NULL"
        ).fetchone()["n"]
        if protected > 0 and not force:
            return jsonify({
                "error": (
                    f"{protected} candidates have adjudication / review / "
                    "applied state. Revert applied rows first, then pass "
                    "force=true."
                ),
                "protected": int(protected),
            }), 409
        before = conn.execute("SELECT COUNT(*) AS n FROM proper_noun_candidates").fetchone()["n"]
        conn.execute("DELETE FROM proper_noun_candidates")
        conn.commit()
        return jsonify({
            "ok": True,
            "cleared": int(before),
            "summary": _pn_get_stats(conn),
        })
    finally:
        conn.close()


@app.route("/api/admin/proper-nouns/<int:cid>/revert", methods=["POST"])
@admin_required
def admin_pn_revert(cid: int):
    """Undo a previously-applied candidate. Reads applied_to_verses_json
    and restores the saved preferred_translation/preferred_source on each
    ai_word_meanings row, then clears applied_at."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        if not row:
            return jsonify({"error": "candidate not found"}), 404
        if not row["applied_at"]:
            return jsonify({"error": "candidate is not applied"}), 400
        try:
            applied = json.loads(row["applied_to_verses_json"] or "[]")
        except Exception:
            applied = []
        for entry in applied:
            conn.execute(
                "UPDATE ai_word_meanings SET "
                "  preferred_translation = ?, preferred_source = ? "
                "WHERE chapter = ? AND verse = ? AND word_pos = ?",
                (
                    entry.get("original_translation"),
                    entry.get("original_source"),
                    entry["chapter"], entry["verse"], entry["word_pos"],
                ),
            )
        conn.execute(
            "UPDATE proper_noun_candidates SET "
            "  applied_at = NULL, applied_to_verses_json = NULL "
            "WHERE id = ?",
            (cid,),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM proper_noun_candidates WHERE id = ?", (cid,)
        ).fetchone()
        return jsonify({"ok": True, "reverted": len(applied),
                        "candidate": _pn_serialize(updated),
                        "summary": _pn_get_stats(conn)})
    finally:
        conn.close()


# --------------- Public: Chrome extension info ---------------

# Fallback values used when admin hasn't set them yet. Matches what was
# previously hardcoded in the frontend. Updating the extension ID after
# a Chrome Web Store resubmission is now a one-field edit in Admin
# Settings rather than a code deploy.
_CHROME_EXTENSION_DEFAULTS = {
    "id": "jbalbedmilokgefgknhieckdidnlikdm",
    "store_url": (
        "https://chromewebstore.google.com/detail/quran-research-tool/"
        "jbalbedmilokgefgknhieckdidnlikdm"
    ),
}


@app.route("/api/public/chrome-extension-info", methods=["GET"])
def public_chrome_extension_info():
    """Return the current Chrome extension ID + store URL for the site to
    use when detecting whether the extension is installed and linking to
    the store. Public, no auth — this info isn't sensitive and is also
    visible in the extension listing itself."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT key, value FROM admin_preferences "
            "WHERE key IN ('chrome_extension_id', 'chrome_extension_store_url')"
        ).fetchall()
        prefs = {r["key"]: (r["value"] or "").strip() for r in rows}
    finally:
        conn.close()

    ext_id = prefs.get("chrome_extension_id") or _CHROME_EXTENSION_DEFAULTS["id"]
    store_url = (
        prefs.get("chrome_extension_store_url")
        or _CHROME_EXTENSION_DEFAULTS["store_url"]
    )
    return jsonify({"id": ext_id, "store_url": store_url})


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


# --------------- Public: Default reciter ---------------
#
# The reader's per-verse play button needs to know which reciter to
# play. Admin sets a `default_reciter_id` in admin_preferences via the
# Verse Settings page; this endpoint exposes that selection (and the
# audio folder for URL construction) to the public reader. Falls back
# to Mishari Alafasy (id=7) if no preference is saved.

_DEFAULT_RECITER_ID = 7
_DEFAULT_RECITER_NAME = "Mishary Rashid Alafasy"


@app.route("/api/reciter/default", methods=["GET"])
def public_default_reciter():
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'default_reciter_id'"
        ).fetchone()
        try:
            reciter_id = int(row["value"]) if row and row["value"] else _DEFAULT_RECITER_ID
        except (TypeError, ValueError):
            reciter_id = _DEFAULT_RECITER_ID
    finally:
        conn.close()

    folder = _get_reciter_folder(reciter_id)
    name = _DEFAULT_RECITER_NAME
    # Try to enrich with the friendly name from the cached reciter list.
    if _reciters_cache:
        for r in _reciters_cache:
            if r.get("id") == reciter_id:
                name = (r.get("reciter_name") or name)
                style = r.get("style")
                if style:
                    name = f"{name} ({style})"
                break
    return jsonify({
        "id": reciter_id,
        "name": name,
        "folder": folder,
        "audio_base": "https://verses.quran.com",
    })


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

            # Get translation (latest AI preferred, conventional fallback with HTML stripped)
            trans_row = conn.execute(
                "SELECT translation_text FROM ai_translations WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1", (s, a)
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

_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "data", "music")
os.makedirs(_MUSIC_DIR, exist_ok=True)


# --------------- Default video metadata (Ollama-down fallback) ---------------
# When the metadata-generation Ollama call fails (service down, timeout,
# parse error), we still want the upload to publish with reasonable
# title/description/tags rather than "Pipeline video 47" or an empty
# blob. These are deliberately generic so they fit any verse selection.
_DEFAULT_YT_TITLE = "Verses of the Quran"
_DEFAULT_YT_DESCRIPTION = (
    "A passage from the Quran with English translation and recitation. "
    "Brought to you by al-nuqta.com — A Root Based Translation of the Quran. "
    "Explore the morphology, etymology, and Semitic cognates behind every "
    "word of the Qur'an at https://al-nuqta.com.\n\n"
    "#Quran #QuranTranslation #QuranArabic"
)
# Kept under YouTube's 500-char total tag limit by design.
# Note: "Islamic" (the post-Quranic adjective) is deliberately
# excluded from every default + filtered out via _strip_islamic_terms
# below. The Quran refers to "Islam" (the noun) but never to
# anything as "Islamic" — the channel keeps that distinction.
_DEFAULT_YT_TAGS: tuple[str, ...] = (
    "Quran", "Quran recitation", "Quran translation",
    "Islam", "Quran in English",
    "Holy Quran", "Quranic verses", "al-nuqta",
)
# TikTok caption — same idea, single string with hashtags inline.
_DEFAULT_TIKTOK_CAPTION = (
    "A passage from the Quran with English translation. "
    "Explore root-by-root analysis at al-nuqta.com "
    "#Quran #QuranTranslation #QuranArabic"
)


# --- Quran-only-vocabulary guard for video metadata ---
# The Quran uses "Islam" (the submission/peace concept) but never the
# adjective "Islamic" (a much later linguistic construction). Operator
# wants the channel's metadata to mirror that — any hashtag, tag, or
# description sentence containing "Islamic" gets stripped before
# upload regardless of where it came from (default, Ollama, manual
# edit). Whole-substring match is enough since "Islam" alone never
# contains the "ic" suffix.
_ISLAMIC_RE = re.compile(r"islamic", re.IGNORECASE)


def _strip_islamic_terms(text: str) -> str:
    """Remove any hashtag containing 'Islamic' from a description, and
    soften standalone 'Islamic' phrases. Conservative: only touches
    hashtags + bare-word adjective uses, never the noun 'Islam'."""
    if not text or not isinstance(text, str):
        return text
    # Drop full hashtag tokens (e.g. "#IslamicVideos", "#islamicQuran")
    text = re.sub(r"#\S*[Ii]slamic\S*", "", text)
    # Drop standalone "Islamic" word in prose (rare in defaults but
    # could leak from Ollama). Replace with empty so the surrounding
    # punctuation/space cleanup below handles the gap.
    text = re.sub(r"\b[Ii]slamic\b", "", text)
    # Tidy up double spaces and orphaned hashtag separators left
    # behind by the strips.
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"(?:\n\s*){3,}", "\n\n", text)
    return text.strip()


def _filter_islamic_tags(tags: list[str]) -> list[str]:
    """Drop any tag whose text contains 'Islamic' (any casing)."""
    return [t for t in tags if isinstance(t, str) and not _ISLAMIC_RE.search(t)]

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


# --------------- Educational pipeline (Phase 1: foundation) ---------------
# Wrap import + bootstrap in try/except so a bug in the new pipeline
# module can never block app startup or the login endpoint. If this
# fails, the educational endpoints will 503 but the rest of the app
# stays healthy.
try:
    import educational_pipeline as _edu
    import educational_safety as _safety
    import educational_interestingness as _interest
    import educational_lessons as _lessons

    def _ensure_educational_table():
        conn = get_db()
        try:
            _edu.ensure_table(conn)
            _safety.ensure_table(conn)
            # Adds interestingness_* columns to educational_videos so
            # the judge verdict can be persisted alongside the row.
            _interest.ensure_columns(conn)
            # judge_lessons table + admin_preferences keys that drive
            # the every-N-days "learn from YouTube performance" cron.
            _lessons.ensure_tables(conn)
        finally:
            conn.close()

    _ensure_educational_table()
    _EDU_OK = True
    # Separate flag for the recitation pipeline — it has its own
    # admin_pipeline_videos table and lives outside the educational
    # bootstrap path, but it consumes the same _interest module to
    # judge passages before render. If the module loaded above, the
    # recitation path can use it too.
    _INTEREST_OK = True
    _LESSONS_OK = True
except Exception as _edu_exc:
    print(f"[educational] failed to initialize: {_edu_exc}")
    _EDU_OK = False
    _INTEREST_OK = False
    _LESSONS_OK = False
    _edu = None  # type: ignore
    _safety = None  # type: ignore
    _interest = None  # type: ignore
    _lessons = None  # type: ignore


def _edu_unavailable():
    return jsonify({"error": "Educational pipeline failed to initialize — see server logs."}), 503


@app.route("/api/admin/educational/pool", methods=["GET"])
@admin_required
def admin_educational_pool():
    """Pool sizes for the dashboard — one query per type."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        return jsonify({t: _edu.pool_size(conn, t) for t in _edu.TYPES})
    finally:
        conn.close()


@app.route("/api/admin/educational/candidates", methods=["GET"])
@admin_required
def admin_educational_candidates():
    if not _EDU_OK:
        return _edu_unavailable()
    vtype = request.args.get("type", "")
    limit = int(request.args.get("limit", "25"))
    if vtype not in _edu.TYPES:
        return jsonify({"error": "unknown type"}), 400
    conn = get_db()
    try:
        candidates = _edu.sample_candidates(conn, vtype, limit=limit)
        # Hydrate verse text/translation so the admin can scan the pool
        # without a second roundtrip per row. Arabic lives in `verses`,
        # English in the separate `translations` table.
        for c in candidates:
            v = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (c["chapter"], c["verse"]),
            ).fetchone()
            if v:
                c["text_uthmani"] = v["text_uthmani"]
            t = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
                (c["chapter"], c["verse"]),
            ).fetchone()
            if t:
                c["translation"] = t["text_en"]
            # Attach cached safety status (no Ollama call here — that
            # would slow the list endpoint to seconds-per-row). When
            # the cache has an entry, the frontend renders a badge.
            # When the verse hasn't been screened yet, safety_status
            # is null and the frontend can omit the badge or render a
            # neutral "unscreened" indicator. The Ollama screen runs
            # at queue-time (see admin_educational_queue) or when the
            # automated pipeline picks the verse.
            if _safety is not None:
                try:
                    st = _safety.safety_status(conn, c["chapter"], c["verse"])
                    if st:
                        c["safety_status"] = {
                            "status": st.get("status"),
                            "reason": st.get("reason"),
                            "model": st.get("model"),
                            "checked_at": st.get("checked_at"),
                        }
                except Exception:
                    pass
        # Grammar Insights — also hydrate the preview fields the
        # candidate-row drawer renders (claim observation, the full
        # counterfactual text, the meaning payoff). The candidate dict
        # already carries category/title/confidence/tier/has_cf; we
        # additionally surface the prose so the operator can read the
        # actual content before queuing.
        if vtype == "grammar_insights":
            for c in candidates:
                row = conn.execute(
                    "SELECT insights_v7_json FROM verse_grammar_insights "
                    "WHERE chapter = ? AND verse = ? "
                    "  AND insights_v7_json IS NOT NULL AND insights_v7_json != '' "
                    "ORDER BY id DESC LIMIT 1",
                    (c["chapter"], c["verse"]),
                ).fetchone()
                if not row:
                    continue
                try:
                    insights = json.loads(row["insights_v7_json"]) or []
                except Exception:
                    continue
                target = next(
                    (ins for ins in insights if ins.get("id") == c.get("insight_id")),
                    None,
                )
                if not target:
                    continue
                claim = target.get("claim") or {}
                cf = target.get("counterfactual") or {}
                payoff = target.get("meaning_payoff") or {}
                c["claim_observation"] = claim.get("observation") or ""
                c["counterfactual_text"] = cf.get("text") if cf.get("present") else ""
                c["payoff_text"] = payoff.get("text") or ""
        return jsonify({"type": vtype, "candidates": candidates})
    finally:
        conn.close()


@app.route("/api/admin/educational/queue", methods=["POST"])
@admin_required
def admin_educational_queue():
    """Move a candidate from the live pool into educational_videos for
    Phase 2 to pick up. Returns 409 if it's already queued.

    Safety gate: by default, refuses to queue any verse flagged
    controversial by educational_safety. The operator can override
    with `force: true` in the body when they've reviewed the flagged
    reason and want to proceed anyway. The override is captured in
    the row's payload so the audit trail records who deliberately
    bypassed the screen. The automated pipeline path
    (educational_pipeline.pick_and_queue_for_pipeline) also calls
    is_verse_safe, so this gate matches that behaviour at the
    manual-queue layer."""
    if not _EDU_OK:
        return _edu_unavailable()
    body = request.get_json(silent=True) or {}
    vtype = body.get("type", "")
    if vtype not in _edu.TYPES:
        return jsonify({"error": "unknown type"}), 400
    try:
        chapter = int(body["chapter"])
        verse = int(body["verse"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "chapter and verse required"}), 400
    word_pos = body.get("word_pos")
    insight_id = body.get("insight_id")
    payload = body.get("payload")
    score = body.get("score")
    force = bool(body.get("force", False))
    conn = get_db()
    try:
        # Content-safety gate. is_verse_safe() uses the
        # verse_safety_cache when fresh and otherwise calls Ollama
        # (with permissive defaults if Ollama is unreachable). A
        # cache miss can therefore take 5-30s on the first manual
        # queue of an unscreened verse — that's intentional, we'd
        # rather block briefly than ship a controversial verse.
        # `force: true` skips the check and stamps a marker on the
        # payload so the audit trail records the deliberate override.
        if _safety is not None and not force:
            try:
                if not _safety.is_verse_safe(conn, chapter, verse):
                    status = _safety.safety_status(conn, chapter, verse) or {}
                    return jsonify({
                        "error": "verse flagged as controversial",
                        "safety_status": {
                            "status": status.get("status") or "controversial",
                            "reason": status.get("reason") or "",
                            "model": status.get("model"),
                            "checked_at": status.get("checked_at"),
                        },
                        "hint": "pass force=true to override after reviewing the flag",
                    }), 409
            except Exception as e:
                # Safety module hard-failed (e.g. DB schema mismatch
                # mid-deploy). Log and fall through permissively —
                # the automated path uses the same fallback.
                print(f"[educational/queue] safety check error for {chapter}:{verse}: {e}")
        if force:
            # Stamp the override on the payload for the audit trail.
            try:
                pl = payload if isinstance(payload, dict) else (
                    json.loads(payload) if isinstance(payload, str) else {}
                )
            except Exception:
                pl = {}
            pl["safety_override"] = True
            payload = pl
        try:
            row_id = _edu.queue_candidate(
                conn, vtype,
                chapter=chapter, verse=verse,
                word_pos=int(word_pos) if word_pos is not None else None,
                insight_id=insight_id,
                payload=payload,
                score=float(score) if score is not None else None,
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "already queued"}), 409
        return jsonify({"id": row_id, "status": "candidate", "safety_override": force}), 201
    finally:
        conn.close()


@app.route("/api/admin/educational/<int:video_id>/generate-script", methods=["POST"])
@admin_required
def admin_educational_generate_script(video_id: int):
    """Phase 2: generate a 4-beat script + long/short voiceovers for a
    candidate row. On success the row moves to status='script_ready'.
    On validation/LLM failure it moves to status='failed' with the
    error captured in error_message — operator can fix the upstream
    data and Regenerate."""
    if not _EDU_OK:
        return _edu_unavailable()
    import educational_scripts as _scripts

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "video not found"}), 404
        rd = dict(row)
        # Allow regen from any state except 'uploaded' — once a video
        # is on YouTube/TikTok, regenerating the script would orphan
        # the upload's metadata. From any other state (including
        # 'rendered'), regen is fine: the script becomes script_ready
        # and the operator re-renders to apply the new script. Old
        # mp4 file stays on disk until the next render overwrites it.
        if rd["status"] == "uploaded":
            return jsonify({
                "error": "cannot regenerate script after upload — would orphan the published video"
            }), 409

        try:
            payload = _scripts.enrich_payload(conn, rd)
        except _scripts.ScriptGenError as e:
            conn.execute(
                "UPDATE educational_videos SET status='failed', error_message=? WHERE id=?",
                (f"payload: {e}", video_id),
            )
            conn.commit()
            return jsonify({"error": f"payload: {e}"}), 422

        api_key = _get_claude_api_key()
        try:
            script = _scripts.generate_script(payload, api_key=api_key)
        except _scripts.ScriptGenError as e:
            conn.execute(
                "UPDATE educational_videos SET status='failed', error_message=? WHERE id=?",
                (str(e), video_id),
            )
            conn.commit()
            return jsonify({"error": str(e)}), 502

        # Persist the script + the structured payload that grounded it
        # so Phase 3 (rendering) doesn't have to re-fetch.
        conn.execute(
            "UPDATE educational_videos SET "
            "  payload_json = ?, "
            "  script_json = ?, "
            "  voiceover_text = ?, "
            "  status = 'script_ready', "
            "  error_message = NULL "
            "WHERE id = ?",
            (
                json.dumps(payload, ensure_ascii=False),
                json.dumps({
                    "hook": script.get("hook"),
                    "verse_intro": script.get("verse_intro"),
                    "insight": script.get("insight"),
                    "close": script.get("close"),
                    # Word Origins template fields (empty for other types)
                    "tidbit_about_root": script.get("tidbit_about_root", ""),
                    "tidbit_about_quran_usage": script.get("tidbit_about_quran_usage", ""),
                    "tidbit_about_semitic": script.get("tidbit_about_semitic", ""),
                    "selected_verse_refs": script.get("selected_verse_refs", []),
                    # Grammar Insights template fields (empty for others). The
                    # renderer reads these at compose time to drive English
                    # phrase highlights and cross-reference example slides;
                    # leaving them out of this whitelist silently strips them
                    # before persistence even when Claude returns them.
                    "english_emphases": script.get("english_emphases", []),
                    "additional_examples": script.get("additional_examples", []),
                    "voiceover_short": script.get("voiceover_short"),
                    "voiceover_short_raw": script.get("voiceover_short_raw"),
                    "voiceover_long_raw": script.get("voiceover_long_raw"),
                    "languages_referenced": script.get("languages_referenced", []),
                    "notes": script.get("notes", ""),
                    "model": script.get("model"),
                }, ensure_ascii=False),
                script.get("voiceover_long"),
                video_id,
            ),
        )
        conn.commit()
        return jsonify({
            "id": video_id,
            "status": "script_ready",
            "script": {
                "hook": script.get("hook"),
                "verse_intro": script.get("verse_intro"),
                "insight": script.get("insight"),
                "close": script.get("close"),
                "voiceover_long": script.get("voiceover_long"),
                "voiceover_short": script.get("voiceover_short"),
                "languages_referenced": script.get("languages_referenced", []),
                "notes": script.get("notes", ""),
            },
        })
    finally:
        conn.close()


@app.route("/api/admin/educational/<int:video_id>/script", methods=["PATCH"])
@admin_required
def admin_educational_edit_script(video_id: int):
    """Operator edits to a generated script. Re-validates the result
    against the same payload that originally grounded the script
    (length budgets, TTS-friendliness, language grounding for Word
    Origins). On success the row stays in status='script_ready' with
    the operator's text. On validation failure the existing script is
    preserved and we return 422 with the list of issues."""
    if not _EDU_OK:
        return _edu_unavailable()
    import educational_scripts as _scripts

    body = request.get_json(silent=True) or {}
    # String fields the operator can hand-edit. Anything missing or
    # not-a-string is left untouched in the merge below.
    _STRING_FIELDS = (
        "hook", "verse_intro", "insight", "close",
        "voiceover_long", "voiceover_short",
        # Word Origins tidbits — letting the operator tweak the
        # narration over each verse without having to regenerate.
        "tidbit_about_root",
        "tidbit_about_quran_usage",
        "tidbit_about_semitic",
    )
    edits: dict[str, object] = {
        k: (body.get(k) if isinstance(body.get(k), str) else None)
        for k in _STRING_FIELDS
    }
    # Non-string fields go through their own type-checked branches so
    # we don't coerce a list into a stringified mess. Word Origins'
    # selected_verse_refs is the canonical example: a list of
    # {chapter, verse, why?} objects. Validator re-checks shape.
    if "selected_verse_refs" in body:
        refs = body.get("selected_verse_refs")
        if isinstance(refs, list):
            edits["selected_verse_refs"] = refs
    if "languages_referenced" in body:
        langs = body.get("languages_referenced")
        if isinstance(langs, list):
            edits["languages_referenced"] = langs

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "video not found"}), 404
        rd = dict(row)
        # Same gate as regenerate: allow edits up until 'uploaded'.
        # Editing a 'rendered' row's script just sends it back to
        # 'script_ready' for re-render; the old mp4 stays on disk.
        if rd["status"] == "uploaded":
            return jsonify({
                "error": "cannot edit script after upload — would orphan the published video"
            }), 409
        if rd["status"] not in ("script_ready", "failed", "rendered"):
            return jsonify({
                "error": f"cannot edit script while status={rd['status']}"
            }), 409

        # Start from the existing script, overlay the edits. This means
        # the operator can submit just the field they changed.
        existing_script = {}
        if rd.get("script_json"):
            try:
                existing_script = json.loads(rd["script_json"])
            except Exception:
                existing_script = {}
        merged = dict(existing_script)
        # Old rows stored only voiceover_short under script_json; long
        # lives in voiceover_text. Bring it in so the merge sees both.
        if rd.get("voiceover_text"):
            merged["voiceover_long"] = rd["voiceover_text"]
        # Apply edits, dropping any None values so untouched fields stay.
        for k, v in edits.items():
            if v is not None:
                merged[k] = v

        # Re-fetch the structured payload — language grounding for Word
        # Origins re-validates against the same allowed pool.
        try:
            payload = _scripts.enrich_payload(conn, rd)
        except _scripts.ScriptGenError as e:
            return jsonify({"error": f"payload: {e}"}), 422

        # Sanitize the voiceovers BEFORE validating, mirroring what the
        # generator does: the operator may paste IPA marks they got
        # from somewhere; we want them stripped, not bounce.
        if isinstance(merged.get("voiceover_long"), str):
            merged["voiceover_long_raw"] = merged["voiceover_long"]
            merged["voiceover_long"] = _scripts.sanitize_for_tts(merged["voiceover_long"])
        if isinstance(merged.get("voiceover_short"), str):
            merged["voiceover_short_raw"] = merged["voiceover_short"]
            merged["voiceover_short"] = _scripts.sanitize_for_tts(merged["voiceover_short"])

        errs = _scripts._validate(merged, payload)
        if errs:
            return jsonify({"error": "validation failed", "issues": errs}), 422

        conn.execute(
            "UPDATE educational_videos SET "
            "  script_json = ?, voiceover_text = ?, "
            "  status = 'script_ready', error_message = NULL "
            "WHERE id = ?",
            (
                json.dumps({
                    "hook": merged.get("hook"),
                    "verse_intro": merged.get("verse_intro"),
                    "insight": merged.get("insight"),
                    "close": merged.get("close"),
                    # Word Origins-specific fields — preserve so the
                    # renderer (which reads them at compose time)
                    # picks up the edited values.
                    "tidbit_about_root": merged.get("tidbit_about_root", ""),
                    "tidbit_about_quran_usage": merged.get("tidbit_about_quran_usage", ""),
                    "tidbit_about_semitic": merged.get("tidbit_about_semitic", ""),
                    "selected_verse_refs": merged.get("selected_verse_refs", []),
                    # Grammar Insights template fields — same reason.
                    "english_emphases": merged.get("english_emphases", []),
                    "additional_examples": merged.get("additional_examples", []),
                    "voiceover_short": merged.get("voiceover_short"),
                    "voiceover_short_raw": merged.get("voiceover_short_raw"),
                    "voiceover_long_raw": merged.get("voiceover_long_raw"),
                    "languages_referenced": merged.get("languages_referenced", []),
                    "notes": merged.get("notes", ""),
                    "model": merged.get("model"),
                    "edited_at": datetime.now(timezone.utc).isoformat(),
                }, ensure_ascii=False),
                merged.get("voiceover_long"),
                video_id,
            ),
        )
        conn.commit()
        return jsonify({
            "id": video_id,
            "status": "script_ready",
            "script": {k: merged.get(k) for k in (
                "hook", "verse_intro", "insight", "close",
                "voiceover_long", "voiceover_short",
                "voiceover_long_raw", "voiceover_short_raw",
                "languages_referenced", "notes",
            )},
        })
    finally:
        conn.close()


@app.route("/api/admin/educational/<int:video_id>/override-judge", methods=["POST"])
@admin_required
def admin_educational_override_judge(video_id: int):
    """Operator override: flip a rejected_uninteresting row back to
    script_ready so it can be rendered. The judge's verdict + score
    + reason stay on the row for auditing — we just clear the
    error_message and lift the status gate. The operator can then
    hit Render normally.

    This is the manual escape hatch when the judge's call disagrees
    with the operator's editorial taste. The judge's verdict + reason
    remain visible in the admin UI so the operator can revisit later
    or use the override as a signal that the rubric needs tuning."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, script_json FROM educational_videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "video not found"}), 404
        if row["status"] != "rejected_uninteresting":
            return jsonify({
                "error": (
                    f"override only valid for rejected_uninteresting rows "
                    f"(current status: {row['status']})"
                ),
            }), 400
        if not row["script_json"]:
            return jsonify({
                "error": "row has no script_json — cannot flip to script_ready",
            }), 400
        # Lift the status gate; preserve the judge's verdict so the
        # admin UI still shows why the auto-pipeline skipped this row.
        conn.execute(
            "UPDATE educational_videos SET "
            "  status = 'script_ready', "
            "  error_message = NULL "
            "WHERE id = ?",
            (video_id,),
        )
        conn.commit()
        return jsonify({"ok": True, "id": video_id, "status": "script_ready"})
    finally:
        conn.close()


@app.route("/api/admin/educational/<int:video_id>/render", methods=["POST"])
@admin_required
def admin_educational_render(video_id: int):
    """Phase 3: composite the script into an MP4. Spawns a daemon
    thread so the request returns immediately; the operator polls
    GET /api/admin/educational/<id> for status transitions
    rendering → rendered (or failed).

    Body: {"format": "long" | "short"}
    """
    if not _EDU_OK:
        return _edu_unavailable()
    body = request.get_json(silent=True) or {}
    fmt = body.get("format", "long")
    if fmt not in ("long", "short"):
        return jsonify({"error": "format must be 'long' or 'short'"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "video not found"}), 404
        rd = dict(row)
        # Allow re-render from any state that has a script on it
        # (script_ready, rendered, rendering, failed). The 'rendering'
        # case covers stuck rows where a previous attempt died mid-
        # flight (server restart, ffmpeg OOM, etc.) — the only
        # alternative is editing the DB by hand. Worst case, two
        # parallel renders write to the same filename and the second
        # to commit wins. Block only when we're past render — once
        # something's been uploaded, regenerating media under it
        # would orphan the upload.
        if rd["status"] not in ("script_ready", "rendered", "failed", "rendering"):
            return jsonify({
                "error": f"cannot render while status={rd['status']}"
            }), 409

        # Pull required credentials NOW so the background thread doesn't
        # have to handle "key missing" — fail fast if the admin hasn't
        # configured ElevenLabs.
        prefs_row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'"
        ).fetchone()
        elevenlabs_key = prefs_row["value"] if prefs_row and prefs_row["value"] else None
        if not elevenlabs_key:
            return jsonify({
                "error": "ElevenLabs API key not set (Admin → Settings → ElevenLabs)"
            }), 400

        # Pick a voice. Resolution order:
        #   1. Explicit voice_id in the request body (lets the operator
        #      override per-render — e.g. "what does this sound like
        #      with a different voice?").
        #   2. The owning pipeline's voice_id, when the row has a
        #      pipeline_id (auto-queued by the orchestrator).
        #   3. The voice of any pipeline matching the row's type. This
        #      handles candidates manually queued from the candidates
        #      page (no pipeline_id is set there) — the operator
        #      almost always has a word_origins / translation_hides /
        #      grammar_insights pipeline already configured with the
        #      voice they want, and falling back to it picks up the
        #      right one.
        #   4. As a last resort, the first row in admin_voices.
        #      Reached only when no pipeline of the matching type
        #      exists yet (early setup).
        voice_id = body.get("voice_id")
        if not voice_id and rd.get("pipeline_id"):
            prow = conn.execute(
                "SELECT voice_id FROM educational_pipelines WHERE id = ?",
                (rd["pipeline_id"],),
            ).fetchone()
            if prow and prow["voice_id"]:
                voice_id = prow["voice_id"]
        if not voice_id:
            # Find any pipeline of the same type and use its voice. We
            # take the most-recently-updated one so an operator who
            # tweaks voice on a pipeline gets that voice on subsequent
            # candidate renders without changing the candidate.
            prow = conn.execute(
                "SELECT voice_id FROM educational_pipelines "
                "WHERE type = ? AND voice_id IS NOT NULL AND voice_id != '' "
                "ORDER BY updated_at DESC LIMIT 1",
                (rd["type"],),
            ).fetchone()
            if prow and prow["voice_id"]:
                voice_id = prow["voice_id"]
        if not voice_id:
            v = conn.execute(
                "SELECT voice_id FROM admin_voices ORDER BY id LIMIT 1"
            ).fetchone()
            if not v:
                return jsonify({
                    "error": "No voices configured (Admin → Settings → ElevenLabs → Voices)"
                }), 400
            voice_id = v["voice_id"]

        # Mark as rendering BEFORE spawning the thread so a fast poll
        # doesn't catch it still in script_ready.
        conn.execute(
            "UPDATE educational_videos SET status='rendering', "
            "       error_message=NULL, format=?, completed_at=NULL "
            "WHERE id = ?",
            (fmt, video_id),
        )
        conn.commit()
    finally:
        conn.close()

    def _do_render():
        import educational_render as _r
        # Each thread gets its own connection.
        c = get_db()
        try:
            try:
                filename, size = _r.render_video(
                    c, video_id,
                    format=fmt,
                    elevenlabs_api_key=elevenlabs_key,
                    voice_id=voice_id,
                )
            except Exception as exc:  # noqa: BLE001 — we want any error captured
                c.execute(
                    "UPDATE educational_videos SET status='failed', "
                    "       error_message=? WHERE id=?",
                    (f"render: {exc}"[:1000], video_id),
                )
                c.commit()
                return
            c.execute(
                "UPDATE educational_videos SET status='rendered', "
                "       filename=?, file_size=?, completed_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (filename, size, video_id),
            )
            c.commit()
        finally:
            c.close()

    threading.Thread(target=_do_render, daemon=True).start()
    return jsonify({"id": video_id, "status": "rendering", "format": fmt}), 202


@app.route("/api/admin/educational/<int:video_id>/video", methods=["GET"])
@admin_required
def admin_educational_video_file(video_id: int):
    """Stream the rendered MP4 for a video row. Used by the preview
    player and the download link."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT filename FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row or not row["filename"]:
            return jsonify({"error": "no rendered file"}), 404
        import educational_render as _r
        return send_from_directory(_r.OUTPUT_DIR, row["filename"], mimetype="video/mp4")
    finally:
        conn.close()


@app.route("/api/admin/educational/<int:video_id>", methods=["GET"])
@admin_required
def admin_educational_video_detail(video_id: int):
    """Full row including script_json + voiceover_text — used by the UI
    to render the script preview after generation."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        d = dict(row)
        # Surface the parsed script JSON for UI ergonomics.
        if d.get("script_json"):
            try:
                d["script"] = json.loads(d["script_json"])
            except Exception:
                d["script"] = None
        return jsonify(d)
    finally:
        conn.close()


def _perform_educational_youtube_upload(
    video_id: int,
    privacy: str = "public",
) -> dict:
    """Upload an educational_videos row's mp4 to YouTube.

    Mirrors _perform_youtube_upload (the recitation-pipeline helper)
    but reads metadata from the educational_videos columns and adds
    to the per-series playlist (youtube_playlist_<vtype>) instead of
    the recitation default.

    Returns a dict shaped like:
      {ok: True,  video_id, youtube_video_id, youtube_url, privacy, playlist_note}
      {ok: False, error, status}
    """
    if not _EDU_OK:
        return {"ok": False, "error": "Educational pipeline disabled", "status": 503}
    import educational_render as _r

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM educational_videos WHERE id = ?", (video_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "Video not found", "status": 404}
        rd = dict(row)
        if rd.get("youtube_video_id"):
            return {
                "ok": False,
                "error": f"Already uploaded to YouTube ({rd['youtube_video_id']})",
                "status": 409,
            }
        if rd["status"] != "rendered":
            return {
                "ok": False,
                "error": f"Video must be in 'rendered' state to upload "
                         f"(current: {rd['status']}).",
                "status": 409,
            }
        if not rd.get("filename"):
            return {"ok": False, "error": "Video has no rendered file", "status": 404}
        filepath = os.path.join(_r.OUTPUT_DIR, rd["filename"])
        if not os.path.isfile(filepath):
            return {"ok": False, "error": "Video file missing on disk", "status": 404}

        # Defense-in-depth: ffprobe the file and refuse to upload if it
        # has no audio stream. Operator hit this when ElevenLabs credits
        # ran out — the renderer silently produced a soundless mp4 and
        # the scheduler pushed it to YouTube. The narration helper now
        # fails the render outright on TTS errors, but this last guard
        # also catches manual / pre-existing rows that slipped through
        # before that fix landed.
        try:
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0",
                    filepath,
                ],
                capture_output=True, text=True, timeout=30,
            )
            audio_streams = [
                line for line in (probe.stdout or "").splitlines()
                if line.strip() == "audio"
            ]
            if not audio_streams:
                return {
                    "ok": False,
                    "error": (
                        f"Refusing to upload {rd['filename']} — the mp4 has "
                        f"no audio stream. This usually means TTS failed "
                        f"during render (e.g. ElevenLabs credits exhausted). "
                        f"Re-render the row first."
                    ),
                    "status": 409,
                }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            # ffprobe missing or slow — log and proceed. We don't want
            # an ffprobe issue to block a legitimate upload, but we DO
            # want to know.
            print(f"[edu-upload] audio-stream check skipped: {e}")

        # Resolve metadata: educational_videos columns > generic Quran
        # fallback. Same fallback constants the recitation pipeline
        # uses so a metadata-less upload still publishes sensibly.
        final_title = (rd.get("youtube_title") or _DEFAULT_YT_TITLE).strip()[:100]
        final_description = (
            rd.get("youtube_description") or _DEFAULT_YT_DESCRIPTION
        ).strip()[:5000]
        try:
            tags_in = json.loads(rd.get("youtube_tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            tags_in = []
        if not tags_in:
            tags_in = list(_DEFAULT_YT_TAGS)
        final_tags: list[str] = []
        for t in tags_in:
            if not isinstance(t, str):
                continue
            cleaned = t.strip().lstrip("#")[:100]
            if cleaned and cleaned not in final_tags:
                final_tags.append(cleaned)
            if len(final_tags) >= 15:
                break
        while final_tags and len(",".join(final_tags)) > 500:
            final_tags.pop()

        # Quran-only vocabulary guard — final pass right before
        # upload so even pre-existing rows that have "Islamic" stored
        # in their columns get cleaned. Channel uses "Islam" but
        # never "Islamic" as an adjective.
        final_title = _ISLAMIC_RE.sub("", final_title).strip() or _DEFAULT_YT_TITLE
        final_description = _strip_islamic_terms(final_description) or _DEFAULT_YT_DESCRIPTION
        final_tags = _filter_islamic_tags(final_tags) or list(_DEFAULT_YT_TAGS)

        final_privacy = (privacy or "public").lower()
        if final_privacy not in ("public", "unlisted", "private"):
            final_privacy = "public"

        # Per-series playlist preference. youtube_playlist_word_origins
        # / _translation_hides / _grammar_insights — same key shape
        # the Settings UI exposes.
        playlist_key = f"youtube_playlist_{rd['type']}"
        plrow = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = ?",
            (playlist_key,),
        ).fetchone()
        playlist_id = (plrow["value"] if plrow and plrow["value"] else "").strip()
    finally:
        conn.close()

    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return {"ok": False, "error": str(e), "status": 400}

    metadata = {
        "snippet": {
            "title": final_title,
            "description": final_description,
            "tags": final_tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": final_privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Multipart resumable upload — same shape as the recitation
    # uploader. Educational videos are smaller (~5-30 MB each), so a
    # single-shot multipart works fine.
    boundary = f"boundary_{uuid.uuid4().hex}"
    body_parts: list[bytes] = []
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b"Content-Type: application/json; charset=UTF-8\r\n\r\n")
    body_parts.append(json.dumps(metadata).encode("utf-8"))
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b"Content-Type: video/mp4\r\n\r\n")
    with open(filepath, "rb") as f:
        body_parts.append(f.read())
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode())
    upload_body = b"".join(body_parts)

    try:
        up_resp = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos",
            params={"uploadType": "multipart", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            data=upload_body,
            # (connect, per-socket-op) — a flat 600 let a stalled Google
            # endpoint pin the calling thread ~10 min; 120s per op still
            # accommodates large multipart bodies making progress.
            timeout=(10, 120),
        )
    except requests.RequestException as e:
        return {"ok": False, "error": f"Upload request failed: {e}", "status": 502}

    if up_resp.status_code not in (200, 201):
        try:
            err_body = up_resp.json()
            err = err_body.get("error", {}).get("message") or str(err_body)[:500]
        except Exception:
            err = up_resp.text[:500]
        return {
            "ok": False,
            "error": f"YouTube upload failed ({up_resp.status_code}): {err}",
            "status": 502,
        }

    yt_video_id = up_resp.json().get("id")

    conn = get_db()
    try:
        conn.execute(
            "UPDATE educational_videos SET "
            "  youtube_video_id = ?, status = 'uploaded' "
            "WHERE id = ?",
            (yt_video_id, video_id),
        )
        conn.commit()
    finally:
        conn.close()

    # Per-series playlist add. Failure here doesn't fail the upload —
    # the video is already public on YouTube; placement is a nice-
    # to-have we can re-attempt manually if needed.
    playlist_note: str | None = None
    if playlist_id and yt_video_id:
        try:
            ok, msg = _youtube_add_to_playlist(access_token, yt_video_id, playlist_id)
            playlist_note = (
                f"Added to playlist {playlist_id}" if ok
                else f"Playlist add failed: {msg}"
            )
        except Exception as e:
            playlist_note = f"Playlist add error: {e}"

    return {
        "ok": True,
        "video_id": video_id,
        "youtube_video_id": yt_video_id,
        "youtube_url": f"https://youtube.com/watch?v={yt_video_id}",
        "privacy": final_privacy,
        "playlist_note": playlist_note,
    }


@app.route("/api/admin/educational/<int:video_id>/add-to-playlist", methods=["POST"])
@admin_required
def admin_educational_add_to_playlist(video_id: int):
    """Retry the per-series playlist add for an already-uploaded
    video. Useful when the original upload's playlist add failed
    (wrong channel selected for OAuth, transient API error, etc.)
    or when the operator updated the playlist preference after
    upload. Returns {ok, message, playlist_id} so the UI can show
    the actual outcome."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT type, youtube_video_id FROM educational_videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        if not row["youtube_video_id"]:
            return jsonify({"error": "Video hasn't been uploaded yet"}), 409
        playlist_key = f"youtube_playlist_{row['type']}"
        plrow = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = ?",
            (playlist_key,),
        ).fetchone()
        playlist_id = (plrow["value"] if plrow and plrow["value"] else "").strip()
    finally:
        conn.close()

    if not playlist_id:
        return jsonify({
            "ok": False,
            "error": f"No playlist configured for this series. Set "
                     f"'{playlist_key}' in Admin → Settings → YouTube Playlists.",
        }), 400

    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    ok, msg = _youtube_add_to_playlist(
        access_token, row["youtube_video_id"], playlist_id,
    )
    return jsonify({
        "ok": ok,
        "playlist_id": playlist_id,
        "message": msg or ("Added to playlist" if ok else "Playlist add failed"),
    }), (200 if ok else 502)


@app.route("/api/admin/educational/<int:video_id>/youtube-stats", methods=["GET"])
@admin_required
def admin_educational_youtube_stats(video_id: int):
    """Fetch view/like/comment counts for an uploaded video via
    YouTube Data API v3 videos.list?part=statistics.

    Stats come back live; we don't cache them. If the operator
    wants to track-over-time, that's a future feature.

    Requires the broad 'youtube' (or 'youtube.readonly') OAuth
    scope. With only 'youtube.upload', this returns 403 'insufficient
    authentication scopes' — the same condition the playlist add
    surfaces."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT youtube_video_id FROM educational_videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        if not row["youtube_video_id"]:
            return jsonify({"error": "Video hasn't been uploaded yet"}), 409
        yt_id = row["youtube_video_id"]
    finally:
        conn.close()

    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400

    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "statistics,snippet", "id": yt_id},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
    except requests.RequestException as e:
        return jsonify({"error": f"YouTube request failed: {e}"}), 502

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {}).get("message") or resp.text[:300]
        except Exception:
            err = resp.text[:300]
        return jsonify({
            "error": f"YouTube stats fetch failed ({resp.status_code}): {err}",
        }), 502

    items = resp.json().get("items") or []
    if not items:
        return jsonify({"error": "Video not found on YouTube — may have been removed"}), 404

    stats = items[0].get("statistics") or {}
    snippet = items[0].get("snippet") or {}
    # YouTube returns counts as strings — coerce to int for the UI.
    def _i(k: str) -> int:
        v = stats.get(k)
        try:
            return int(v) if v is not None else 0
        except (TypeError, ValueError):
            return 0
    return jsonify({
        "youtube_video_id": yt_id,
        "title": snippet.get("title"),
        "published_at": snippet.get("publishedAt"),
        "views": _i("viewCount"),
        "likes": _i("likeCount"),
        "comments": _i("commentCount"),
        # favoriteCount is deprecated on YouTube but still returned;
        # skip exposing it.
    })


@app.route("/api/admin/educational/<int:video_id>/upload-youtube", methods=["POST"])
@admin_required
def admin_educational_upload_youtube(video_id: int):
    """Upload a rendered educational video to YouTube. Synchronous —
    body is uploaded inside this request, so a 30 MB clip ties the
    request up for ~10–30 s. Frontend shows a loading state. Returns
    the YouTube URL on success."""
    body = request.get_json(silent=True) or {}
    privacy = (body.get("privacy") or "public").lower()
    result = _perform_educational_youtube_upload(video_id, privacy=privacy)
    if result.get("ok"):
        return jsonify(result)
    status = result.pop("status", 500)
    return jsonify(result), status


@app.route("/api/admin/educational/<int:video_id>", methods=["DELETE"])
@admin_required
def admin_educational_video_delete(video_id: int):
    """Remove an educational video — both the DB row and the rendered
    mp4 on disk. The shared TTS audio cache is intentionally NOT
    pruned (it's hashed by voice_id+text, so deleting it would
    invalidate cache hits for unrelated rows that happen to share
    the same voiceover string).

    Refuses to delete rows that are 'rendering' so we can't yank a
    file out from under an in-flight ffmpeg process."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, filename FROM educational_videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        if row["status"] == "rendering":
            return jsonify({
                "error": "cannot delete a row that's currently rendering — "
                "wait for it to finish or fail first."
            }), 409
        # Best-effort file removal: log a warning but still drop the
        # row if the mp4 is missing or already gone.
        if row["filename"]:
            import educational_render as _r
            fp = os.path.join(_r.OUTPUT_DIR, row["filename"])
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except Exception as e:
                    print(f"[educational delete] could not remove {fp}: {e}")
        conn.execute("DELETE FROM educational_videos WHERE id = ?", (video_id,))
        conn.commit()
        return jsonify({"ok": True, "id": video_id})
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines", methods=["GET"])
@admin_required
def admin_educational_pipelines_list():
    if not _EDU_OK:
        return _edu_unavailable()
    vtype = request.args.get("type") or None
    if vtype and vtype not in _edu.TYPES:
        return jsonify({"error": "unknown type"}), 400
    conn = get_db()
    try:
        return jsonify({"pipelines": _edu.list_pipelines(conn, vtype=vtype)})
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines", methods=["POST"])
@admin_required
def admin_educational_pipelines_create():
    if not _EDU_OK:
        return _edu_unavailable()
    body = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        try:
            pid = _edu.create_pipeline(
                conn,
                name=str(body.get("name", "")),
                vtype=str(body.get("type", "")),
                voice_id=str(body.get("voice_id", "")),
                format=str(body.get("format", "short")),
                show_dim_background=bool(body.get("show_dim_background", True)),
                music_id=(int(body["music_id"]) if body.get("music_id") else None),
                enabled=bool(body.get("enabled", True)),
            )
            row = _edu.get_pipeline(conn, pid)
        finally:
            conn.close()
        return jsonify(row), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>", methods=["GET"])
@admin_required
def admin_educational_pipeline_detail(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        p = _edu.get_pipeline(conn, pipeline_id)
        if not p:
            return jsonify({"error": "not found"}), 404
        # Hydrate with the videos this pipeline has produced.
        p["videos"] = _edu.list_videos(conn, pipeline_id=pipeline_id, limit=200)
        return jsonify(p)
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>", methods=["PUT"])
@admin_required
def admin_educational_pipeline_update(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    body = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        try:
            ok = _edu.update_pipeline(
                conn, pipeline_id,
                name=body.get("name"),
                voice_id=body.get("voice_id"),
                format=body.get("format"),
                show_dim_background=body.get("show_dim_background"),
                music_id=(int(body["music_id"]) if body.get("music_id") not in (None, "") else None) if "music_id" in body else None,
                enabled=body.get("enabled"),
            )
            if not ok:
                return jsonify({"error": "no fields to update or not found"}), 400
            row = _edu.get_pipeline(conn, pipeline_id)
            return jsonify(row)
        finally:
            conn.close()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>", methods=["DELETE"])
@admin_required
def admin_educational_pipeline_delete(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        ok = _edu.delete_pipeline(conn, pipeline_id)
        if not ok:
            return jsonify({"error": "not found"}), 404
        return jsonify({"ok": True})
    finally:
        conn.close()


def _educational_pipeline_run_thread(
    pipeline_id: int, video_id: int, voice_id: str,
    fmt: str, elevenlabs_key: str, claude_key: str,
) -> None:
    """The script→judge→render→metadata chain run inside a daemon thread.
    Used by both the manual /run endpoint and the scheduler. Caller
    is responsible for queueing the FIRST candidate row; this
    function takes that video_id, generates a script, judges it, and
    if the judge rejects it, picks the next candidate and tries
    again — up to MAX_REJECTIONS_PER_RUN attempts — before giving
    up.

    Status flow per attempt:
      candidate → script_ready → judged-interesting → rendering → rendered
                                ↘ judged-skip → rejected_uninteresting (final for THIS row)

    Errors are captured on the relevant row's error_message; the
    function never raises to its caller.

    Only the LAST surviving row (the one that passes the judge)
    proceeds to render + YouTube metadata. Rejected rows stay in the
    DB with status='rejected_uninteresting' so the admin UI can show
    why they were skipped and the operator can manually override if
    they disagree with the judge.
    """
    c = get_db()
    try:
        import educational_scripts as _scripts
        approved_video_id: int | None = None
        rejected_run: list[tuple[int, int, str]] = []  # (video_id, score, reason)
        attempts = 0
        # First iteration uses the video_id the caller queued. Later
        # iterations queue their own.
        current_video_id = video_id
        while approved_video_id is None and attempts < _interest.MAX_REJECTIONS_PER_RUN:
            attempts += 1
            try:
                row = c.execute(
                    "SELECT * FROM educational_videos WHERE id = ?", (current_video_id,),
                ).fetchone()
                if row is None:
                    print(
                        f"[interestingness] candidate {current_video_id} vanished — aborting run"
                    )
                    return
                rd = dict(row)
                payload = _scripts.enrich_payload(c, rd)
                script = _scripts.generate_script(payload, api_key=claude_key)
                c.execute(
                    "UPDATE educational_videos SET "
                    "  payload_json = ?, script_json = ?, voiceover_text = ?, "
                    "  status = 'script_ready', error_message = NULL "
                    "WHERE id = ?",
                    (
                        json.dumps(payload, ensure_ascii=False),
                        json.dumps({
                            k: script.get(k) for k in (
                                "hook", "verse_intro", "insight", "close",
                                "tidbit_about_root", "tidbit_about_quran_usage",
                                "tidbit_about_semitic", "selected_verse_refs",
                                "english_emphases", "additional_examples",
                                "voiceover_short", "voiceover_short_raw",
                                "voiceover_long_raw",
                                "languages_referenced", "notes", "model",
                            )
                        }, ensure_ascii=False),
                        script.get("voiceover_long"),
                        current_video_id,
                    ),
                )
                c.commit()
            except Exception as e:
                # Script generation failed on this candidate. Mark
                # the row and try the next one — script-gen failures
                # are typically transient or model-specific.
                c.execute(
                    "UPDATE educational_videos SET status='failed', error_message=? WHERE id=?",
                    (f"script: {e}"[:1000], current_video_id),
                )
                c.commit()
                # Try another candidate.
                try:
                    current_video_id = _edu.pick_and_queue_for_pipeline(
                        c, pipeline_id, triggered_by="interestingness-retry",
                    )
                    continue
                except _edu.PipelineRunError as pe:
                    print(f"[interestingness] no more candidates after script-fail: {pe}")
                    return

            # Interestingness gate. Ollama-based judge on the
            # generated script — uses a TYPE-SPECIFIC rubric, since
            # what makes a translation_hides short stop the scroll
            # is different from what makes a word_origins one
            # ("chastity→architecture" picture-flip vs. "etymology
            # reframes a familiar verse"). FAIL CLOSED: 'unknown'
            # (Ollama down or malformed JSON) and judge crashes now
            # REJECT — a dead judge should pause the pipeline, not
            # wave everything through (2026-07 audit).
            vtype = (rd.get("type") or "translation_hides").strip()
            try:
                verdict = _interest.judge_script(c, payload, script, vtype)
            except Exception as e:
                print(f"[interestingness] judge raised, rejecting: {e}")
                verdict = {"verdict": "unknown", "score": 0,
                           "reason": f"judge crashed: {e}", "model": "",
                           "pass": False}

            try:
                c.execute(
                    "UPDATE educational_videos SET "
                    "  interestingness_score = ?, "
                    "  interestingness_verdict = ?, "
                    "  interestingness_reason = ?, "
                    "  interestingness_model = ? "
                    "WHERE id = ?",
                    (
                        verdict.get("score") or None,
                        verdict.get("verdict"),
                        verdict.get("reason"),
                        verdict.get("model"),
                        current_video_id,
                    ),
                )
                c.commit()
            except Exception as e:
                print(f"[interestingness] could not persist verdict: {e}")

            if verdict.get("pass"):
                approved_video_id = current_video_id
                print(
                    f"[interestingness] {current_video_id} APPROVED "
                    f"(score={verdict.get('score')}, "
                    f"verdict={verdict.get('verdict')}): {verdict.get('reason')}"
                )
                break

            # Rejected — mark row and pick the next candidate.
            rejected_run.append(
                (current_video_id, verdict.get("score") or 0, verdict.get("reason") or "")
            )
            c.execute(
                "UPDATE educational_videos SET "
                "  status = 'rejected_uninteresting', "
                "  error_message = ? "
                "WHERE id = ?",
                (
                    f"interestingness skip (score={verdict.get('score')}): "
                    f"{verdict.get('reason')}"[:1000],
                    current_video_id,
                ),
            )
            c.commit()
            print(
                f"[interestingness] {current_video_id} REJECTED "
                f"(score={verdict.get('score')}): {verdict.get('reason')} "
                f"— attempt {attempts}/{_interest.MAX_REJECTIONS_PER_RUN}"
            )
            try:
                current_video_id = _edu.pick_and_queue_for_pipeline(
                    c, pipeline_id, triggered_by="interestingness-retry",
                )
            except _edu.PipelineRunError as pe:
                # No more candidates to try. Log + abort.
                print(
                    f"[interestingness] candidate pool exhausted after "
                    f"{attempts} attempts ({len(rejected_run)} rejected): {pe}"
                )
                return

        if approved_video_id is None:
            print(
                f"[interestingness] gave up after {attempts} attempts — "
                f"all judged 'skip'. Rejected: "
                + ", ".join(
                    f"#{vid}(score={s})" for vid, s, _r in rejected_run
                )
            )
            return

        # From here on we use approved_video_id, not the original.
        video_id = approved_video_id

        # Step 2: render
        try:
            c.execute(
                "UPDATE educational_videos SET status='rendering', "
                "       error_message=NULL, format=?, completed_at=NULL "
                "WHERE id = ?",
                (fmt, video_id),
            )
            c.commit()
            import educational_render as _r
            filename, size = _r.render_video(
                c, video_id,
                format=fmt,
                elevenlabs_api_key=elevenlabs_key,
                voice_id=voice_id,
            )
            c.execute(
                "UPDATE educational_videos SET status='rendered', "
                "       filename=?, file_size=?, completed_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (filename, size, video_id),
            )
            c.commit()
        except Exception as e:
            c.execute(
                "UPDATE educational_videos SET status='failed', error_message=? WHERE id=?",
                (f"render: {e}"[:1000], video_id),
            )
            c.commit()
            return

        # Step 3: YouTube metadata via Ollama. Failure here doesn't
        # fail the run — the video is rendered and watchable.
        try:
            row = c.execute(
                "SELECT * FROM educational_videos WHERE id = ?", (video_id,),
            ).fetchone()
            rd = dict(row)
            payload = json.loads(rd.get("payload_json") or "{}")
            script_obj = json.loads(rd.get("script_json") or "{}")
            yt_title, yt_desc, yt_tags = _generate_educational_metadata(
                c, rd, payload, script_obj,
            )
            c.execute(
                "UPDATE educational_videos SET "
                "  youtube_title = ?, youtube_description = ?, youtube_tags = ? "
                "WHERE id = ?",
                (yt_title or None, yt_desc or None,
                 json.dumps(yt_tags) if yt_tags else None, video_id),
            )
            c.commit()
        except Exception as e:
            print(f"[educational metadata] failed for video {video_id}: {e}")
    finally:
        c.close()


def _start_educational_pipeline_run(
    pipeline_id: int, *, triggered_by: str = "pipeline",
) -> tuple[int, str | None]:
    """Queue a candidate + spawn the chain thread. Used by both the
    manual /run endpoint (triggered_by='pipeline') and the scheduler
    (triggered_by='scheduler'). Returns (video_id, error_message).

    Raises nothing — caller checks the second tuple element. error
    is None on success; a string when validation fails (no candidates
    left, ElevenLabs key missing, pipeline disabled, etc.)."""
    conn = get_db()
    try:
        pipe = _edu.get_pipeline(conn, pipeline_id)
        if not pipe:
            return 0, "pipeline not found"
        if not pipe.get("enabled"):
            return 0, "pipeline is disabled"
        eleven_row = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'"
        ).fetchone()
        elevenlabs_key = eleven_row["value"] if eleven_row and eleven_row["value"] else None
        if not elevenlabs_key:
            return 0, "ElevenLabs API key missing"
        try:
            video_id = _edu.pick_and_queue_for_pipeline(
                conn, pipeline_id, triggered_by=triggered_by,
            )
        except _edu.PipelineRunError as e:
            return 0, str(e)
    finally:
        conn.close()

    voice_id = pipe["voice_id"]
    fmt = pipe["format"]
    claude_key = _get_claude_api_key()
    threading.Thread(
        target=_educational_pipeline_run_thread,
        args=(pipeline_id, video_id, voice_id, fmt, elevenlabs_key, claude_key),
        daemon=True,
    ).start()
    return video_id, None


# ----------------------------------------------------------------------------
# Judge-tuning lessons — performance-driven refinements to the
# interestingness judge's rubric. Lessons get auto-refreshed by the
# scheduler tick every N days; operator can read / edit / disable
# individual lessons or trigger a manual refresh here.
# ----------------------------------------------------------------------------

@app.route("/api/admin/judge-lessons", methods=["GET"])
@admin_required
def admin_judge_lessons_list():
    """All lessons grouped by pipeline_type, plus the cron settings.
    Lets the operator audit what the judge is currently weighting."""
    if not _LESSONS_OK or _lessons is None:
        return jsonify({"error": "lessons module not available"}), 503
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, pipeline_type, lesson, evidence_video_ids,
                   generation_id, source, active, operator_note,
                   generated_at
            FROM judge_lessons
            ORDER BY pipeline_type, source,
                     active DESC, generated_at DESC, id DESC
            """
        ).fetchall()
        lessons = []
        for r in rows:
            lessons.append({
                "id": r["id"],
                "pipeline_type": r["pipeline_type"],
                "lesson": r["lesson"],
                "evidence_video_ids": json.loads(r["evidence_video_ids"] or "[]"),
                "generation_id": r["generation_id"],
                "source": r["source"],
                "active": bool(r["active"]),
                "operator_note": r["operator_note"],
                "generated_at": r["generated_at"],
            })
        # Pipe settings out too — keeps the UI single-fetch.
        prefs = {}
        for k in (
            "lessons_auto_refresh_enabled",
            "lessons_refresh_interval_days",
            "lessons_min_age_days",
            "lessons_min_views",
            "lessons_last_refresh_at",
        ):
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = ?", (k,)
            ).fetchone()
            prefs[k] = row["value"] if row else None
        return jsonify({"lessons": lessons, "settings": prefs,
                        "pipeline_types": list(_lessons.PIPELINE_TYPES)})
    finally:
        conn.close()


@app.route("/api/admin/judge-lessons/<int:lesson_id>", methods=["PATCH"])
@admin_required
def admin_judge_lessons_update(lesson_id: int):
    """Edit a lesson — toggle `active`, edit `lesson` text, set an
    `operator_note`. Promote an auto lesson to source='manual' so a
    future cron run doesn't retire it.

    Body keys (all optional):
      active (bool), lesson (str), operator_note (str), source (str)
    """
    if not _LESSONS_OK:
        return jsonify({"error": "lessons module not available"}), 503
    body = request.get_json(silent=True) or {}
    sets = []
    args: list = []
    if "active" in body:
        sets.append("active = ?")
        args.append(1 if body["active"] else 0)
    if "lesson" in body:
        text = (body.get("lesson") or "").strip()
        if not text:
            return jsonify({"error": "lesson cannot be empty"}), 400
        sets.append("lesson = ?")
        args.append(text[:500])
    if "operator_note" in body:
        sets.append("operator_note = ?")
        args.append((body.get("operator_note") or "").strip()[:500] or None)
    if "source" in body:
        src = body.get("source")
        if src not in ("auto", "manual"):
            return jsonify({"error": "source must be 'auto' or 'manual'"}), 400
        sets.append("source = ?")
        args.append(src)
    if not sets:
        return jsonify({"error": "no editable fields supplied"}), 400
    args.append(lesson_id)
    conn = get_db()
    try:
        cur = conn.execute(
            f"UPDATE judge_lessons SET {', '.join(sets)} WHERE id = ?",
            args,
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "not found"}), 404
        return jsonify({"ok": True, "id": lesson_id})
    finally:
        conn.close()


@app.route("/api/admin/judge-lessons", methods=["POST"])
@admin_required
def admin_judge_lessons_create():
    """Add a manual lesson. The operator's own editorial nuggets live
    alongside the auto-generated ones and survive cron retirements."""
    if not _LESSONS_OK:
        return jsonify({"error": "lessons module not available"}), 503
    body = request.get_json(silent=True) or {}
    ptype = (body.get("pipeline_type") or "").strip()
    text = (body.get("lesson") or "").strip()
    if ptype not in (set(_lessons.PIPELINE_TYPES) | {"all"}):
        return jsonify({"error": "pipeline_type must be one of "
                        + ", ".join(_lessons.PIPELINE_TYPES) + ", all"}), 400
    if not text:
        return jsonify({"error": "lesson is required"}), 400
    evidence = body.get("evidence_video_ids") or []
    if not isinstance(evidence, list):
        return jsonify({"error": "evidence_video_ids must be a list"}), 400
    note = (body.get("operator_note") or "").strip()[:500] or None
    conn = get_db()
    try:
        cur = conn.execute(
            """
            INSERT INTO judge_lessons
              (pipeline_type, lesson, evidence_video_ids,
               source, active, operator_note)
            VALUES (?, ?, ?, 'manual', 1, ?)
            """,
            (ptype, text[:500], json.dumps([str(i) for i in evidence]), note),
        )
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    finally:
        conn.close()


@app.route("/api/admin/judge-lessons/<int:lesson_id>", methods=["DELETE"])
@admin_required
def admin_judge_lessons_delete(lesson_id: int):
    if not _LESSONS_OK:
        return jsonify({"error": "lessons module not available"}), 503
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM judge_lessons WHERE id = ?", (lesson_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "not found"}), 404
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route("/api/admin/judge-lessons/refresh", methods=["POST"])
@admin_required
def admin_judge_lessons_refresh():
    """Force a cron run NOW, regardless of the last-refresh schedule.
    Useful when the operator just changed thresholds in settings or
    wants a fresh sample after a batch upload."""
    if not _LESSONS_OK or _lessons is None:
        return jsonify({"error": "lessons module not available"}), 503
    body = request.get_json(silent=True) or {}
    only_type = body.get("pipeline_type")  # optional — limit to one type
    if only_type and only_type not in _lessons.PIPELINE_TYPES:
        return jsonify({"error": "invalid pipeline_type"}), 400

    # Run in a background thread — the analyzer hits Ollama Cloud
    # 4× (once per pipeline type) and can take 30-90s total, so we
    # don't want to block the request.
    def _bg():
        c = get_db()
        try:
            summary = _lessons.refresh_lessons(c, only_type=only_type, force=True)
            print(f"[lessons] manual refresh done: {summary}")
        except Exception as e:
            print(f"[lessons] manual refresh error: {e}")
        finally:
            c.close()

    threading.Thread(target=_bg, daemon=True).start()
    return jsonify({"ok": True, "status": "started",
                    "note": "Refresh running in background; poll GET /api/admin/judge-lessons in ~60-120s."})


@app.route("/api/admin/judge-lessons/settings", methods=["PUT"])
@admin_required
def admin_judge_lessons_settings():
    """Update the cron's tunables: enabled, interval, min_age, min_views."""
    if not _LESSONS_OK:
        return jsonify({"error": "lessons module not available"}), 503
    body = request.get_json(silent=True) or {}
    updates: list[tuple[str, str]] = []
    if "enabled" in body:
        updates.append(("lessons_auto_refresh_enabled",
                        "1" if body["enabled"] else "0"))
    if "interval_days" in body:
        try:
            n = int(body["interval_days"])
            if n < 1 or n > 60:
                raise ValueError("range")
            updates.append(("lessons_refresh_interval_days", str(n)))
        except (TypeError, ValueError):
            return jsonify({"error": "interval_days must be 1-60"}), 400
    if "min_age_days" in body:
        try:
            n = int(body["min_age_days"])
            if n < 0 or n > 90:
                raise ValueError("range")
            updates.append(("lessons_min_age_days", str(n)))
        except (TypeError, ValueError):
            return jsonify({"error": "min_age_days must be 0-90"}), 400
    if "min_views" in body:
        try:
            n = int(body["min_views"])
            if n < 0:
                raise ValueError("range")
            updates.append(("lessons_min_views", str(n)))
        except (TypeError, ValueError):
            return jsonify({"error": "min_views must be a non-negative integer"}), 400
    if not updates:
        return jsonify({"error": "no settings supplied"}), 400
    conn = get_db()
    try:
        for k, v in updates:
            conn.execute(
                "INSERT INTO admin_preferences (key, value, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                (k, v),
            )
        conn.commit()
        return jsonify({"ok": True, "updated": [k for k, _ in updates]})
    finally:
        conn.close()


@app.route("/api/admin/educational/schedules", methods=["GET"])
@admin_required
def admin_educational_schedules_list():
    """All educational pipeline schedules in one shot — mirrors the
    recitation /api/admin/pipeline-schedules endpoint so the Scheduler
    page can render both pipeline families with the same shape."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        pipelines = _edu.list_pipelines(conn)
        out = []
        for p in pipelines:
            sched = _edu.get_schedule(conn, p["id"])
            out.append({
                "pipeline_id": p["id"],
                "pipeline_name": p["name"],
                "pipeline_type": p["type"],
                "pipeline_enabled": bool(p.get("enabled", 1)),
                "times": sched.get("times", []),
                "max_runs_per_day": sched.get("max_runs_per_day", 2),
                "enabled": sched.get("enabled", False),
                "grace_minutes": sched.get("grace_minutes", 30),
                "updated_at": sched.get("updated_at"),
            })
        return jsonify(out)
    finally:
        conn.close()


@app.route("/api/admin/educational/schedule-runs", methods=["GET"])
@admin_required
def admin_educational_schedule_runs_all():
    """Combined audit log across all educational pipelines — mirrors the
    recitation /api/admin/pipeline-schedule-runs endpoint. Joined with
    pipelines so the UI can show the pipeline name + type per row."""
    if not _EDU_OK:
        return _edu_unavailable()
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    conn = get_db()
    try:
        # Surface the downstream video's state alongside the title.
        # Without this, an operator looking at the audit log sees
        # "fired" with a NULL title and assumes the title pipeline
        # is broken. In reality the schedule run fired but the video
        # itself failed (or is still mid-pipeline). video_status +
        # video_error give the UI enough to render a clear failure
        # chip with the actual error in a tooltip.
        rows = conn.execute(
            """
            SELECT r.id, r.pipeline_id, p.name AS pipeline_name, p.type AS pipeline_type,
                   r.scheduled_time, r.fired_at, r.video_id, r.status, r.note,
                   ev.youtube_title AS video_title,
                   ev.status AS video_status,
                   ev.error_message AS video_error
            FROM educational_pipeline_schedule_runs r
            LEFT JOIN educational_pipelines p ON p.id = r.pipeline_id
            LEFT JOIN educational_videos ev ON ev.id = r.video_id
            ORDER BY r.fired_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/schedule", methods=["GET"])
@admin_required
def admin_educational_schedule_get(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        if not _edu.get_pipeline(conn, pipeline_id):
            return jsonify({"error": "pipeline not found"}), 404
        return jsonify(_edu.get_schedule(conn, pipeline_id))
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/schedule", methods=["PUT"])
@admin_required
def admin_educational_schedule_upsert(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        if not _edu.get_pipeline(conn, pipeline_id):
            return jsonify({"error": "pipeline not found"}), 404
        try:
            schedule = _edu.upsert_schedule(
                conn, pipeline_id,
                times=list(body.get("times") or []),
                max_runs_per_day=int(body.get("max_runs_per_day", 2)),
                enabled=bool(body.get("enabled", False)),
                grace_minutes=int(body.get("grace_minutes", 30)),
            )
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(schedule)
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/schedule/runs", methods=["GET"])
@admin_required
def admin_educational_schedule_runs(pipeline_id: int):
    if not _EDU_OK:
        return _edu_unavailable()
    limit = max(1, min(int(request.args.get("limit", 50)), 200))
    conn = get_db()
    try:
        if not _edu.get_pipeline(conn, pipeline_id):
            return jsonify({"error": "pipeline not found"}), 404
        return jsonify({"runs": _edu.list_schedule_runs(conn, pipeline_id, limit)})
    finally:
        conn.close()


_OUTRO_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".aac"}
_OUTRO_AUDIO_MAX_BYTES = 10 * 1024 * 1024  # 10 MB — generous for ~5s clips


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/outro-audio", methods=["POST"])
@admin_required
def admin_educational_outro_audio_upload(pipeline_id: int):
    """Upload a sound bite to play during the al-nuqta outro splash.
    Replaces any existing audio for this pipeline. Stored at
    data/educational_outro_audio/<filename>; renderer ffprobes it
    and extends the outro window so the splash card holds long
    enough for the audio to finish."""
    if not _EDU_OK:
        return _edu_unavailable()
    import educational_render as _r

    f = request.files.get("audio")
    if not f or not f.filename:
        return jsonify({"error": "No audio file uploaded (form field 'audio')"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in _OUTRO_AUDIO_EXTS:
        return jsonify({
            "error": f"Unsupported format {ext or '(none)'}. "
                     f"Use {', '.join(sorted(_OUTRO_AUDIO_EXTS))}."
        }), 400
    # Cheap size check before saving — Flask's MAX_CONTENT_LENGTH is
    # the upper bound but we want a tighter cap for outro bites.
    f.stream.seek(0, os.SEEK_END)
    size = f.stream.tell()
    f.stream.seek(0)
    if size > _OUTRO_AUDIO_MAX_BYTES:
        return jsonify({
            "error": f"File too large ({size//1024} KB). "
                     f"Max {_OUTRO_AUDIO_MAX_BYTES//1024//1024} MB."
        }), 400

    conn = get_db()
    try:
        pipe = _edu.get_pipeline(conn, pipeline_id)
        if not pipe:
            return jsonify({"error": "pipeline not found"}), 404

        # Stable filename per pipeline. Replace any existing file (the
        # extension may differ across uploads, so the old file is
        # explicitly removed first to avoid stale stragglers).
        old = pipe.get("outro_audio_filename")
        if old:
            old_path = os.path.join(_r.OUTRO_AUDIO_DIR, old)
            if os.path.isfile(old_path):
                try: os.remove(old_path)
                except Exception: pass

        new_filename = f"pipeline_{pipeline_id}{ext}"
        target = os.path.join(_r.OUTRO_AUDIO_DIR, new_filename)
        f.save(target)

        # Sanity-check: probe the saved file. If ffprobe can't read
        # it, reject the upload before storing the column.
        try:
            duration = _r._probe_duration(target)
        except Exception as e:
            try: os.remove(target)
            except Exception: pass
            return jsonify({"error": f"Could not read audio duration: {e}"}), 400
        if duration > 30.0:
            try: os.remove(target)
            except Exception: pass
            return jsonify({
                "error": f"Audio is {duration:.1f}s — outro bites should be ≤30s. "
                         "Trim before uploading."
            }), 400

        conn.execute(
            "UPDATE educational_pipelines SET outro_audio_filename = ?, "
            "       updated_at = datetime('now') WHERE id = ?",
            (new_filename, pipeline_id),
        )
        conn.commit()
        return jsonify({
            "filename": new_filename,
            "size_bytes": size,
            "duration_seconds": duration,
        }), 201
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/outro-audio", methods=["GET"])
@admin_required
def admin_educational_outro_audio_get(pipeline_id: int):
    """Stream the outro audio for preview. Mimetype is set generically
    since the file extension dictates the actual codec."""
    if not _EDU_OK:
        return _edu_unavailable()
    import educational_render as _r
    conn = get_db()
    try:
        pipe = _edu.get_pipeline(conn, pipeline_id)
        if not pipe:
            return jsonify({"error": "pipeline not found"}), 404
        fname = pipe.get("outro_audio_filename")
        if not fname:
            return jsonify({"error": "no outro audio set"}), 404
        return send_from_directory(_r.OUTRO_AUDIO_DIR, fname)
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/outro-audio", methods=["DELETE"])
@admin_required
def admin_educational_outro_audio_delete(pipeline_id: int):
    """Remove the outro audio for a pipeline. Future renders fall back
    to the silent 5-second outro."""
    if not _EDU_OK:
        return _edu_unavailable()
    import educational_render as _r
    conn = get_db()
    try:
        pipe = _edu.get_pipeline(conn, pipeline_id)
        if not pipe:
            return jsonify({"error": "pipeline not found"}), 404
        fname = pipe.get("outro_audio_filename")
        if fname:
            path = os.path.join(_r.OUTRO_AUDIO_DIR, fname)
            if os.path.isfile(path):
                try: os.remove(path)
                except Exception as e:
                    print(f"[educational outro] could not remove {path}: {e}")
        conn.execute(
            "UPDATE educational_pipelines SET outro_audio_filename = NULL, "
            "       updated_at = datetime('now') WHERE id = ?",
            (pipeline_id,),
        )
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route("/api/admin/educational/pipelines/<int:pipeline_id>/run", methods=["POST"])
@admin_required
def admin_educational_pipeline_run(pipeline_id: int):
    """Manual "Run now" — picks a candidate, generates script, renders.
    Returns 202 immediately; operator polls GET /pipelines/<id> for
    the new video to appear in the videos list and watches the row's
    status flip candidate → script_ready → rendering → rendered (or
    failed)."""
    if not _EDU_OK:
        return _edu_unavailable()
    video_id, err = _start_educational_pipeline_run(
        pipeline_id, triggered_by="pipeline",
    )
    if err:
        # 'not found' → 404, 'disabled' → 400, pool exhausted → 409,
        # missing key → 400. The shared helper returns a flat string;
        # we map the most useful HTTP codes here for parity with the
        # earlier behavior.
        status = 404 if "not found" in err else (
            409 if "exhausted" in err or "no unused" in err else 400
        )
        return jsonify({"error": err}), status
    return jsonify({
        "pipeline_id": pipeline_id,
        "video_id": video_id,
        "status": "candidate",
    }), 202


@app.route("/api/admin/educational/videos", methods=["GET"])
@admin_required
def admin_educational_videos_list():
    if not _EDU_OK:
        return _edu_unavailable()
    vtype = request.args.get("type") or None
    if vtype and vtype not in _edu.TYPES:
        return jsonify({"error": "unknown type"}), 400
    conn = get_db()
    try:
        return jsonify({"videos": _edu.list_videos(conn, vtype=vtype)})
    finally:
        conn.close()


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
               FROM admin_tts_cache ORDER BY created_at DESC"""
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["surah_name"] = _surah_name(r["chapter"])
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/tts-cache/stale", methods=["GET"])
@admin_required
def admin_tts_cache_stale():
    """Check which TTS cache entries have outdated translations.

    Compares cached translation_text against the latest AI translation
    for each verse. Returns entries where they differ.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, chapter, verse, translation_text FROM admin_tts_cache"
        ).fetchall()
        stale = []
        for r in rows:
            latest = conn.execute(
                "SELECT translation_text FROM ai_translations WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1",
                (r["chapter"], r["verse"]),
            ).fetchone()
            if not latest:
                continue
            if latest["translation_text"].strip() != r["translation_text"].strip():
                stale.append({
                    "id": r["id"],
                    "chapter": r["chapter"],
                    "verse": r["verse"],
                    "surah_name": _surah_name(r["chapter"]),
                    "cached_text": r["translation_text"],
                    "latest_text": latest["translation_text"],
                })
        return jsonify(stale)
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
        # Idempotent column adds for admin_resources.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(admin_resources)").fetchall()]
        if "description" not in cols:
            conn.execute("ALTER TABLE admin_resources ADD COLUMN description TEXT DEFAULT ''")
            conn.commit()
        if "tags" not in cols:
            # Comma-separated list. The educational pipeline filters by
            # tag (e.g. videos tagged 'word-origins' for that series),
            # picking randomly from the matching pool.
            conn.execute("ALTER TABLE admin_resources ADD COLUMN tags TEXT DEFAULT ''")
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


def _ensure_music_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        # Add description column if missing
        cols = [r[1] for r in conn.execute("PRAGMA table_info(admin_music)").fetchall()]
        if "description" not in cols:
            conn.execute("ALTER TABLE admin_music ADD COLUMN description TEXT DEFAULT ''")
            conn.commit()
    finally:
        conn.close()

_ensure_music_table()


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


def _normalize_tags(raw: str) -> str:
    """Lowercase, deduplicate, comma-separate. 'Word-Origins, NATURE'
    → 'nature,word-origins'. Stored canonical so case/whitespace
    differences don't fragment the pool."""
    if not raw:
        return ""
    parts = [t.strip().lower() for t in raw.split(",") if t.strip()]
    seen: dict[str, None] = {}
    for p in parts:
        seen[p] = None
    return ",".join(sorted(seen))


@app.route("/api/admin/resources/<int:resource_id>", methods=["PUT"])
@admin_required
def admin_update_resource(resource_id):
    body = request.get_json(silent=True) or {}
    description = body.get("description", "").strip()[:500]
    tags = _normalize_tags(body.get("tags", ""))
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        # Only update fields explicitly present in the body so a PUT
        # that only changes tags doesn't blow away the description.
        sets: list[str] = []
        params: list = []
        if "description" in body:
            sets.append("description = ?"); params.append(description)
        if "tags" in body:
            sets.append("tags = ?"); params.append(tags)
        if sets:
            params.append(resource_id)
            conn.execute(f"UPDATE admin_resources SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
        updated = conn.execute("SELECT * FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        return jsonify(dict(updated))
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


# --------------- Admin: Background Music ---------------

_ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}


@app.route("/api/admin/music", methods=["POST"])
@admin_required
def admin_upload_music():
    """Upload a background music track."""
    file = request.files.get("audio")
    if not file or not file.filename:
        return jsonify({"error": "No audio file provided"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in _ALLOWED_AUDIO_EXTS:
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(_ALLOWED_AUDIO_EXTS)}"}), 400

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(_MUSIC_DIR, filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)
    try:
        duration = _get_audio_duration(filepath)
    except Exception:
        duration = None

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO admin_music (original_name, filename, file_size, duration_seconds)
               VALUES (?, ?, ?, ?)""",
            (file.filename, filename, file_size, duration),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM admin_music WHERE rowid = last_insert_rowid()"
        ).fetchone()
        return jsonify(dict(row)), 201
    finally:
        conn.close()


@app.route("/api/admin/music", methods=["GET"])
@admin_required
def admin_list_music():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM admin_music ORDER BY created_at DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/music/<int:music_id>", methods=["DELETE"])
@admin_required
def admin_delete_music(music_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_music WHERE id = ?", (music_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        filepath = os.path.join(_MUSIC_DIR, row["filename"])
        if os.path.isfile(filepath):
            os.remove(filepath)
        conn.execute("DELETE FROM admin_music WHERE id = ?", (music_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/music/<int:music_id>", methods=["PUT"])
@admin_required
def admin_update_music(music_id):
    body = request.get_json(silent=True) or {}
    description = body.get("description", "").strip()[:500]
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM admin_music WHERE id = ?", (music_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        conn.execute("UPDATE admin_music SET description = ? WHERE id = ?", (description, music_id))
        conn.commit()
        updated = conn.execute("SELECT * FROM admin_music WHERE id = ?", (music_id,)).fetchone()
        return jsonify(dict(updated))
    finally:
        conn.close()


@app.route("/api/admin/music/<int:music_id>/audio", methods=["GET"])
@admin_required
def admin_music_audio(music_id):
    """Stream a music file for preview playback."""
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM admin_music WHERE id = ?", (music_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        filepath = os.path.join(_MUSIC_DIR, row["filename"])
        if not os.path.isfile(filepath):
            return jsonify({"error": "File missing"}), 404
        return send_file(filepath)
    finally:
        conn.close()


# --------------- Admin: Verse Explanations ---------------

_OPENING_PHRASE = "The Quran says"
_TRANSITION_PHRASES = [
    "Elsewhere the Quran says",
    "And in another place",
    "It also says",
    "And again it tells us",
    "Further it says",
]


def _ensure_explanation_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                segments TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

_ensure_explanation_table()


def _fetch_translation_for_range(conn, chapter, ayah_start, ayah_end):
    """Fetch and concatenate English translations for a verse range."""
    parts = []
    for ayah in range(ayah_start, ayah_end + 1):
        row = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
            (chapter, ayah),
        ).fetchone()
        if row:
            text = html.unescape(re.sub(r"<[^>]+>", "", row["text_en"]))
            parts.append(text.strip())
    return " ".join(parts)


def _build_explanation_segments(conn, verse_groups):
    """Build the segments JSON array from a list of verse groups."""
    segments = []
    for i, vg in enumerate(verse_groups):
        ch = vg["chapter"]
        a_start = vg["ayah_start"]
        a_end = vg["ayah_end"]
        surah = _surah_name(ch)

        # Transition phrase
        if i == 0:
            phrase = _OPENING_PHRASE
        else:
            phrase = _TRANSITION_PHRASES[(i - 1) % len(_TRANSITION_PHRASES)]
        segments.append({"type": "transition", "text": phrase, "tts_filename": None})

        # Verse group
        if a_start == a_end:
            ref = f"{surah} {ch}:{a_start}"
        else:
            ref = f"{surah} {ch}:{a_start}-{a_end}"
        translation = _fetch_translation_for_range(conn, ch, a_start, a_end)
        segments.append({
            "type": "verses",
            "chapter": ch,
            "ayah_start": a_start,
            "ayah_end": a_end,
            "ref": ref,
            "translation": translation,
            "tts_filename": None,
        })

    # Closing placeholder
    segments.append({"type": "closing", "text": "", "tts_filename": None})
    return segments


@app.route("/api/admin/explanations", methods=["POST"])
@admin_required
def admin_create_explanation():
    """Create a new verse explanation."""
    body = request.get_json(silent=True) or {}
    title = body.get("title", "").strip()[:200]
    verse_groups = body.get("verse_groups", [])

    if not title:
        return jsonify({"error": "Title required"}), 400
    if not verse_groups or not isinstance(verse_groups, list):
        return jsonify({"error": "At least one verse group required"}), 400

    # Validate verse groups
    for vg in verse_groups:
        ch = vg.get("chapter")
        a_start = vg.get("ayah_start")
        a_end = vg.get("ayah_end")
        if not all(isinstance(x, int) and x > 0 for x in [ch, a_start, a_end]):
            return jsonify({"error": "Invalid verse group"}), 400
        if a_end < a_start:
            return jsonify({"error": "ayah_end must be >= ayah_start"}), 400

    conn = get_db()
    try:
        segments = _build_explanation_segments(conn, verse_groups)
        conn.execute(
            "INSERT INTO admin_explanations (title, segments) VALUES (?, ?)",
            (title, json.dumps(segments)),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM admin_explanations WHERE rowid = last_insert_rowid()"
        ).fetchone()
        result = dict(row)
        result["segments"] = json.loads(result["segments"])
        return jsonify(result), 201
    finally:
        conn.close()


@app.route("/api/admin/explanations", methods=["GET"])
@admin_required
def admin_list_explanations():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, title, status, segments, created_at, updated_at "
            "FROM admin_explanations ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            segs = json.loads(d.pop("segments"))
            d["segment_count"] = len(segs)
            d["verse_count"] = sum(1 for s in segs if s["type"] == "verses")
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/explanations/<int:expl_id>", methods=["GET"])
@admin_required
def admin_get_explanation(expl_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        result = dict(row)
        result["segments"] = json.loads(result["segments"])
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/explanations/<int:expl_id>", methods=["PUT"])
@admin_required
def admin_update_explanation(expl_id):
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404

        title = body.get("title", row["title"]).strip()[:200]
        segments = body.get("segments", json.loads(row["segments"]))

        # Determine status: ready if all segments have tts_filename
        all_have_tts = all(s.get("tts_filename") for s in segments)
        # But closing with empty text doesn't need TTS
        has_empty_closing = any(
            s["type"] == "closing" and not s.get("text", "").strip() for s in segments
        )
        status = "ready" if all_have_tts and not has_empty_closing else "draft"

        conn.execute(
            "UPDATE admin_explanations SET title=?, segments=?, status=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, json.dumps(segments), status, expl_id),
        )
        conn.commit()
        result = {"id": expl_id, "title": title, "segments": segments, "status": status}
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/explanations/<int:expl_id>", methods=["DELETE"])
@admin_required
def admin_delete_explanation(expl_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT segments FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        # Delete TTS files
        segments = json.loads(row["segments"])
        for s in segments:
            fn = s.get("tts_filename")
            if fn:
                fpath = os.path.join(_TTS_CACHE_DIR, fn)
                if os.path.isfile(fpath):
                    os.remove(fpath)
        conn.execute("DELETE FROM admin_explanations WHERE id = ?", (expl_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/explanation-suggest", methods=["POST"])
@admin_required
def admin_explanation_suggest():
    """Suggest related verses using the IDF engine."""
    body = request.get_json(silent=True) or {}
    chapter = body.get("chapter")
    ayah = body.get("ayah")
    if not chapter or not ayah:
        return jsonify({"error": "chapter and ayah required"}), 400

    scored = _find_related_verses(chapter, ayah, limit=8)
    conn = get_db()
    try:
        results = []
        for containment, shared_weight, (s, a), shared_roots in scored:
            row = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
                (s, a),
            ).fetchone()
            translation = ""
            if row:
                translation = html.unescape(re.sub(r"<[^>]+>", "", row["text_en"]))

            root_details = []
            for rbw in shared_roots:
                arabic = _root_arabic_map.get(rbw, rbw)
                root_details.append({"root_buckwalter": rbw, "root_arabic": arabic})

            results.append({
                "chapter": s,
                "ayah": a,
                "ref": f"{_surah_name(s)} {s}:{a}",
                "translation": translation.strip(),
                "similarity_score": round(containment, 3),
                "shared_roots": root_details,
            })
        return jsonify(results)
    finally:
        conn.close()


@app.route("/api/admin/explanation-closing", methods=["POST"])
@admin_required
def admin_explanation_closing():
    """Generate a closing reflection using Claude API."""
    body = request.get_json(silent=True) or {}
    segments = body.get("segments", [])

    verse_segments = [s for s in segments if s.get("type") == "verses"]
    if not verse_segments:
        return jsonify({"error": "No verse segments provided"}), 400

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "Claude API key not configured"}), 500

    # Build verse context for the prompt
    verse_lines = []
    for vs in verse_segments:
        verse_lines.append(f"{vs.get('ref', '')}: {vs.get('translation', '')}")

    # Fetch additional context (AI translations, departure notes) if available
    conn = get_db()
    try:
        context_blocks = []
        for vs in verse_segments:
            ch = vs.get("chapter")
            for ayah in range(vs.get("ayah_start", 1), vs.get("ayah_end", 1) + 1):
                ai = conn.execute(
                    "SELECT departure_notes FROM ai_translations "
                    "WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1",
                    (ch, ayah),
                ).fetchone()
                if ai and ai["departure_notes"]:
                    context_blocks.append(
                        f"  {ch}:{ayah} notes: {ai['departure_notes']}"
                    )
                # Word-level insights
                words = conn.execute(
                    "SELECT word_pos, meaning_short, departure_notes "
                    "FROM ai_word_meanings WHERE chapter = ? AND verse = ? "
                    "AND departure_notes IS NOT NULL AND departure_notes != '' "
                    "ORDER BY word_pos",
                    (ch, ayah),
                ).fetchall()
                for w in words:
                    context_blocks.append(
                        f"  {ch}:{ayah} word {w['word_pos']} \"{w['meaning_short']}\": "
                        f"{w['departure_notes']}"
                    )
    finally:
        conn.close()

    context_section = ""
    if context_blocks:
        context_section = (
            "\n\nTranslation and linguistic notes (use if they add depth):\n"
            + "\n".join(context_blocks)
        )

    prompt = (
        "You are writing a closing reflection for a short video that presents "
        "thematically connected Quranic verses. The video has just quoted these "
        "verses in English:\n\n"
        + "\n".join(verse_lines)
        + context_section
        + "\n\nWrite 1-2 sentences that tie these verses together into a single "
        "insight. The reflection should be profound, almost philosophical, "
        "revealing what these verses collectively show about the Quran's message. "
        "If a root word or cognate connection between the verses adds genuine "
        "depth, include it naturally.\n\n"
        "Style: Write with conviction, as someone who has sat with these verses. "
        "Avoid negation patterns ('not X but Y'), avoid 'merely', 'simply put'. "
        "Avoid spiritual clichés ('timeless wisdom', 'profound reminder'). "
        "Let the weight come from the ideas, not from announcing profundity. "
        "No em dashes. STRICT LIMIT: the entire response must be under 165 "
        "characters including spaces. Keep it to 1-2 short sentences."
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": _PROXY_MODEL,
                "max_tokens": 256,
                "temperature": 0.8,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not resp.ok:
            return jsonify({"error": f"Claude API error: {resp.status_code}"}), 502
        result = resp.json()
        text = result.get("content", [{}])[0].get("text", "")
        return jsonify({"closing_text": text.strip()})
    except requests.Timeout:
        return jsonify({"error": "Claude API timed out"}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/admin/explanation-tts", methods=["POST"])
@admin_required
def admin_explanation_tts():
    """Generate TTS for a single explanation segment."""
    body = request.get_json(silent=True) or {}
    expl_id = body.get("explanation_id")
    seg_idx = body.get("segment_index")
    text = (body.get("text") or "").strip()
    voice_id = (body.get("voice_id") or "").strip()

    if not all([expl_id, isinstance(seg_idx, int), text, voice_id]):
        return jsonify({"error": "explanation_id, segment_index, text, voice_id required"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT segments FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Explanation not found"}), 404
        segments = json.loads(row["segments"])
        if seg_idx < 0 or seg_idx >= len(segments):
            return jsonify({"error": "Invalid segment index"}), 400
    finally:
        conn.close()

    # Check for existing file with same hash
    text_hash = _tts_hash(text, voice_id)
    filename = f"expl_{expl_id}_{seg_idx}_{text_hash}.mp3"
    filepath = os.path.join(_TTS_CACHE_DIR, filename)

    if os.path.isfile(filepath):
        # Already exists, just update the segment reference
        conn = get_db()
        try:
            segments[seg_idx]["tts_filename"] = filename
            all_have_tts = all(s.get("tts_filename") for s in segments)
            has_empty_closing = any(
                s["type"] == "closing" and not s.get("text", "").strip() for s in segments
            )
            status = "ready" if all_have_tts and not has_empty_closing else "draft"
            conn.execute(
                "UPDATE admin_explanations SET segments=?, status=?, "
                "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (json.dumps(segments), status, expl_id),
            )
            conn.commit()
        finally:
            conn.close()
        return send_from_directory(_TTS_CACHE_DIR, filename, mimetype="audio/mpeg")

    # Get ElevenLabs API key
    conn = get_db()
    try:
        pref = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'"
        ).fetchone()
        if not pref or not pref["value"]:
            return jsonify({"error": "ElevenLabs API key not configured"}), 400
        api_key = pref["value"]
    finally:
        conn.close()

    # Call ElevenLabs
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
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
        if resp.status_code != 200:
            error_msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            return jsonify({"error": f"ElevenLabs error: {error_msg}"}), 502

        with open(filepath, "wb") as f:
            f.write(resp.content)

    except requests.Timeout:
        return jsonify({"error": "ElevenLabs API timed out"}), 504

    # Update segment with filename
    conn = get_db()
    try:
        # Re-read in case of concurrent modification
        row = conn.execute(
            "SELECT segments FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        segments = json.loads(row["segments"])
        segments[seg_idx]["tts_filename"] = filename
        all_have_tts = all(s.get("tts_filename") for s in segments)
        has_empty_closing = any(
            s["type"] == "closing" and not s.get("text", "").strip() for s in segments
        )
        status = "ready" if all_have_tts and not has_empty_closing else "draft"
        conn.execute(
            "UPDATE admin_explanations SET segments=?, status=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(segments), status, expl_id),
        )
        conn.commit()
    finally:
        conn.close()

    return send_from_directory(_TTS_CACHE_DIR, filename, mimetype="audio/mpeg")


@app.route("/api/admin/explanation-generate-all-tts", methods=["POST"])
@admin_required
def admin_explanation_generate_all_tts():
    """Batch-generate TTS for all segments of an explanation."""
    body = request.get_json(silent=True) or {}
    expl_id = body.get("explanation_id")
    voice_id = (body.get("voice_id") or "").strip()

    if not expl_id or not voice_id:
        return jsonify({"error": "explanation_id and voice_id required"}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT segments FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Explanation not found"}), 404
        segments = json.loads(row["segments"])
    finally:
        conn.close()

    # Get ElevenLabs API key
    conn = get_db()
    try:
        pref = conn.execute(
            "SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'"
        ).fetchone()
        if not pref or not pref["value"]:
            return jsonify({"error": "ElevenLabs API key not configured"}), 400
        api_key = pref["value"]
    finally:
        conn.close()

    generated = 0
    total = len(segments)

    for idx, seg in enumerate(segments):
        text = seg.get("text") or seg.get("translation") or ""
        text = text.strip()
        if not text:
            continue  # Skip empty segments (e.g. empty closing)
        if seg.get("tts_filename"):
            # Check if file still exists
            if os.path.isfile(os.path.join(_TTS_CACHE_DIR, seg["tts_filename"])):
                continue

        text_hash = _tts_hash(text, voice_id)
        filename = f"expl_{expl_id}_{idx}_{text_hash}.mp3"
        filepath = os.path.join(_TTS_CACHE_DIR, filename)

        if not os.path.isfile(filepath):
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
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    },
                    timeout=30,
                )
                if resp.status_code != 200:
                    return jsonify({
                        "error": f"ElevenLabs error on segment {idx}: {resp.text[:200]}",
                        "generated": generated,
                    }), 502

                with open(filepath, "wb") as f:
                    f.write(resp.content)
            except requests.Timeout:
                return jsonify({
                    "error": f"ElevenLabs timed out on segment {idx}",
                    "generated": generated,
                }), 504

        segments[idx]["tts_filename"] = filename
        generated += 1

    # Update explanation
    all_have_tts = all(s.get("tts_filename") for s in segments)
    has_empty_closing = any(
        s["type"] == "closing" and not s.get("text", "").strip() for s in segments
    )
    status = "ready" if all_have_tts and not has_empty_closing else "draft"

    conn = get_db()
    try:
        conn.execute(
            "UPDATE admin_explanations SET segments=?, status=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(segments), status, expl_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"generated": generated, "total": total, "status": status})


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

    english_only = verse_data[0].get("english_only", False) if verse_data else False
    arabic_only = verse_data[0].get("arabic_only", False) if verse_data else False
    music_filename = verse_data[0].get("_music_filename") if verse_data else None
    music_path = os.path.join(_MUSIC_DIR, music_filename) if music_filename else None
    if music_path and not os.path.isfile(music_path):
        music_path = None  # silently skip if file was deleted

    tmpdir = tempfile.mkdtemp(prefix="vidgen_")
    try:
        # Step 1: Download recitation audio (if not english_only) and collect TTS files
        recit_files = []
        tts_files = []
        for i, v in enumerate(verse_data):
            _update_video_status(video_id, "processing",
                f"{'Preparing' if english_only else 'Downloading'} audio {i + 1}/{len(verse_data)}...")

            if not english_only:
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
                recit_files.append(recit_path)

            # Copy TTS from cache (not needed for arabic_only)
            if not arabic_only:
                tts_src = os.path.join(_TTS_CACHE_DIR, v["tts_filename"])
                tts_path = os.path.join(tmpdir, f"tts_{i:03d}.mp3")
                if os.path.isfile(tts_src):
                    shutil.copy2(tts_src, tts_path)
                else:
                    _update_video_status(video_id, "failed",
                        error=f"TTS cache file missing for {v['verse_ref']}")
                    return
                tts_files.append(tts_path)

        # Step 2: Get durations and build timeline
        _update_video_status(video_id, "processing", "Analyzing audio durations...")

        tts_durs = [_get_audio_duration(f) for f in tts_files] if tts_files else []

        timeline = []
        current_time = 0.0

        if english_only:
            # English-only: just TTS phases, no recitation
            for i in range(len(verse_data)):
                timeline.append({
                    "phase": "tts",
                    "start": current_time,
                    "dur": tts_durs[i],
                    "arabic": verse_data[i]["arabic_text"],
                    "translation": verse_data[i]["translation"],
                    "ref": verse_data[i]["verse_ref"],
                })
                current_time += tts_durs[i]
        elif arabic_only:
            # Arabic-only: recitation only, show translation as subtitles
            recit_durs = [_get_audio_duration(f) for f in recit_files]
            for i in range(len(verse_data)):
                timeline.append({
                    "phase": "recitation",
                    "start": current_time,
                    "dur": recit_durs[i],
                    "arabic": verse_data[i]["arabic_text"],
                    "translation": verse_data[i]["translation"],
                    "ref": verse_data[i]["verse_ref"],
                })
                current_time += recit_durs[i]
        else:
            # Interleaved: recite verse → TTS voice → next verse → TTS voice
            recit_durs = [_get_audio_duration(f) for f in recit_files]
            for i in range(len(verse_data)):
                timeline.append({
                    "phase": "recitation",
                    "start": current_time,
                    "dur": recit_durs[i],
                    "arabic": verse_data[i]["arabic_text"],
                    "translation": verse_data[i]["translation"],
                    "ref": verse_data[i]["verse_ref"],
                })
                current_time += recit_durs[i]
                timeline.append({
                    "phase": "tts",
                    "start": current_time,
                    "dur": tts_durs[i],
                    "arabic": verse_data[i]["arabic_text"],
                    "translation": verse_data[i]["translation"],
                    "ref": verse_data[i]["verse_ref"],
                })
                current_time += tts_durs[i]

        # Outro slide: 5 seconds of branding after all verses
        outro_dur = 5.0
        outro_start = current_time
        total_duration = current_time + outro_dur

        # Step 3: Concatenate audio — interleaved: recite, tts, recite, tts
        # Plus silent outro (generated as silent audio segment)
        _update_video_status(video_id, "processing", "Building audio track...")

        # Generate silent audio for outro
        silence_path = os.path.join(tmpdir, "silence.mp3")
        subprocess.run(
            [_FFMPEG, "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=44100:cl=stereo", "-t", f"{outro_dur:.3f}",
             "-c:a", "libmp3lame", "-q:a", "9", silence_path],
            capture_output=True, timeout=30,
        )

        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for i in range(len(verse_data)):
                if not english_only:
                    f.write(f"file '{recit_files[i]}'\n")
                if not arabic_only:
                    f.write(f"file '{tts_files[i]}'\n")
            f.write(f"file '{silence_path}'\n")

        combined_audio = os.path.join(tmpdir, "combined.mp3")
        subprocess.run(
            [_FFMPEG, "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", combined_audio],
            capture_output=True, timeout=120,
        )

        # Step 4: Build ASS subtitle file for text overlays
        # White text with dark outline on dark semi-transparent bands (drawbox).
        # libass handles Arabic RTL/ligatures/diacritics natively.
        _update_video_status(video_id, "processing", "Rendering video...")

        # Font sizes
        arabic_fontsize = 96 if fmt == "short" else 78
        trans_fontsize = 64 if fmt == "short" else 52
        ref_fontsize = 62 if fmt == "short" else 52

        # ASS colours: white text, semi-transparent dark outline for readability
        # BorderStyle=1 (outline), no box background — drawbox provides the band
        text_colour = "&H00FFFFFF"
        outline_colour = "&H50000000"
        fonts_dir = os.path.join(os.path.dirname(__file__), "data", "fonts")
        ass_path = os.path.join(tmpdir, "subs.ass")

        # Band positions for drawbox filters
        # Ref band: top of frame
        ref_band_y = 15 if fmt == "short" else 10
        ref_band_h = 110 if fmt == "short" else 90
        ref_margin_v = 38 if fmt == "short" else 28
        # Content band: vertically centered
        # Taller band when showing Arabic + Translation together
        if arabic_only:
            content_band_h = 520 if fmt == "short" else 420
        else:
            content_band_h = 380 if fmt == "short" else 310
        content_band_y = (target_h - content_band_h) // 2

        with open(ass_path, "w", encoding="utf-8") as af:
            af.write("[Script Info]\n")
            af.write("ScriptType: v4.00+\n")
            af.write(f"PlayResX: {target_w}\n")
            af.write(f"PlayResY: {target_h}\n\n")

            af.write("[V4+ Styles]\n")
            af.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # Ref: top-center (Alignment=8), bold, white text
            af.write(f"Style: Ref,Liberation Sans,{ref_fontsize},{text_colour},&H000000FF,{outline_colour},&H00000000,1,0,0,0,100,100,0,0,1,3,0,8,40,40,{ref_margin_v},0\n")
            # Arabic: center (Alignment=5), Scheherazade New, white text
            af.write(f"Style: Arabic,Scheherazade New,{arabic_fontsize},{text_colour},&H000000FF,{outline_colour},&H00000000,0,0,0,0,100,100,0,0,1,3,0,5,60,60,0,0\n")
            # Translation: center (Alignment=5), same position as Arabic
            af.write(f"Style: Trans,Liberation Sans,{trans_fontsize},{text_colour},&H000000FF,{outline_colour},&H00000000,0,0,0,0,100,100,0,0,1,3,0,5,60,60,0,0\n")
            # Outro styles: positioned with \pos in events
            outro_site_fs = 90 if fmt == "short" else 72
            outro_tag_fs = 54 if fmt == "short" else 44
            # Alignment=5 (center), no outline — clean white text on dark overlay
            af.write(f"Style: OutroSite,Liberation Sans,{outro_site_fs},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,5,40,40,0,0\n")
            af.write(f"Style: OutroTag,Liberation Sans,{outro_tag_fs},&H80FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,0\n")

            af.write("\n[Events]\n")
            af.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            def _ass_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = seconds % 60
                return f"{h}:{m:02d}:{s:05.2f}"

            def _ass_escape(text):
                return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            def _fix_arabic_for_ass(text):
                """Fix Arabic text for libass rendering.

                - Replace U+0671 (alef wasla) with U+0627 (plain alef)
                - Strip Uthmani-specific marks that libass renders as squares:
                  U+0653 maddah above, U+0654 hamza above,
                  U+0670 superscript alef,
                  U+06D6-U+06ED (small high/low marks, Quranic annotations)
                """
                text = text.replace("\u0671", "\u0627")
                text = re.sub(r"[\u0653\u0654\u0670\u06d6-\u06ed]", "", text)
                return text

            # Interleaved: recitation shows ref + Arabic, TTS shows translation
            for t in timeline:
                start = _ass_time(t["start"])
                end = _ass_time(t["start"] + t["dur"])
                ref = _ass_escape(t["ref"])
                translation = _ass_escape(t["translation"])

                cx = target_w // 2
                band_cy = content_band_y + content_band_h // 2

                if english_only:
                    # English-only: always show ref + translation (no Arabic)
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,{translation}\n")
                elif arabic_only:
                    # Arabic-only: Arabic in upper third, translation in lower third
                    arabic = _ass_escape(_fix_arabic_for_ass(t["arabic"]))
                    ar_y = band_cy - (content_band_h // 4)
                    tr_y = band_cy + (content_band_h // 4)
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Arabic,,0,0,0,,"
                             f"{{\\pos({cx},{ar_y})}}{arabic}\n")
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,"
                             f"{{\\pos({cx},{tr_y})}}{translation}\n")
                elif t["phase"] == "recitation":
                    arabic = _ass_escape(_fix_arabic_for_ass(t["arabic"]))
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Arabic,,0,0,0,,{arabic}\n")
                else:
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,{translation}\n")

            # Outro slide: site name + tagline with fade-in
            outro_s = _ass_time(outro_start)
            outro_e = _ass_time(outro_start + outro_dur)
            cx = target_w // 2
            cy = target_h // 2
            # Site name slightly above center, tagline below
            site_y = cy - 40
            tag_y = cy + 70
            af.write(f"Dialogue: 0,{outro_s},{outro_e},OutroSite,,0,0,0,,{{\\fad(800,0)\\pos({cx},{site_y})}}al-nuqta.com\n")
            af.write(f"Dialogue: 0,{outro_s},{outro_e},OutroTag,,0,0,0,,{{\\fad(1200,0)\\pos({cx},{tag_y})}}A Root Based Translation of the Quran\n")

        # Step 5: Build drawbox filter chain for background bands
        drawbox_parts = []
        for t in timeline:
            s, e = t["start"], t["start"] + t["dur"]
            enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
            # Ref band (top)
            drawbox_parts.append(
                f"drawbox=x=0:y={ref_band_y}:w=iw:h={ref_band_h}"
                f":color=black@0.5:t=fill:enable='{enable}'"
            )
            # Content band (center)
            drawbox_parts.append(
                f"drawbox=x=0:y={content_band_y}:w=iw:h={content_band_h}"
                f":color=black@0.5:t=fill:enable='{enable}'"
            )

        # Outro: fade-in dark overlay over 1.5s (stepped opacity 0 → 0.75)
        fade_dur = 1.5
        fade_steps = 10
        step_dur = fade_dur / fade_steps
        for s in range(fade_steps):
            t_s = outro_start + s * step_dur
            t_e = outro_start + (s + 1) * step_dur
            alpha = 0.75 * (s + 1) / fade_steps
            drawbox_parts.append(
                f"drawbox=x=0:y=0:w=iw:h=ih"
                f":color=black@{alpha:.3f}:t=fill"
                f":enable='between(t\\,{t_s:.3f}\\,{t_e:.3f})'"
            )
        drawbox_parts.append(
            f"drawbox=x=0:y=0:w=iw:h=ih"
            f":color=black@0.75:t=fill"
            f":enable='gte(t\\,{outro_start + fade_dur:.3f})'"
        )

        # Step 6: Final render — scale/crop, drawbox bands, then ASS text overlay
        output_filename = f"video_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(_GENERATED_VIDEOS_DIR, output_filename)

        vf_parts = [
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase",
            f"crop={target_w}:{target_h}",
        ] + drawbox_parts + [
            f"ass={ass_path}:fontsdir={fonts_dir}",
        ]
        vf = ",".join(vf_parts)

        render_timeout = max(600, int(total_duration * 10))

        if music_path:
            # Mix voice audio (input 1) with background music (input 2, low volume)
            # Voice at full volume, music at ~4% so narrator is clearly heard
            af_mix = (
                f"[1:a]volume=1.0[voice];"
                f"[2:a]volume=0.01,afade=t=out:st={max(0, total_duration - 5):.3f}:d=5[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=3:normalize=0[aout]"
            )
            cmd = [
                _FFMPEG, "-y",
                "-stream_loop", "-1",
                "-i", bg_path,
                "-i", combined_audio,
                "-i", music_path,
                "-vf", vf,
                "-filter_complex", af_mix,
                "-t", f"{total_duration:.3f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0", "-map", "[aout]",
                "-movflags", "+faststart",
                output_path,
            ]
        else:
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
    english_only = bool(body.get("english_only", False))
    arabic_only = bool(body.get("arabic_only", False))
    music_id = body.get("music_id")  # optional

    if not title:
        return jsonify({"error": "Title required"}), 400
    if fmt not in ("short", "regular"):
        return jsonify({"error": "Format must be 'short' or 'regular'"}), 400
    if not isinstance(resource_id, int) or resource_id <= 0:
        return jsonify({"error": "Valid resource_id required"}), 400
    if not english_only and (not isinstance(reciter_id, int) or reciter_id <= 0):
        return jsonify({"error": "Valid reciter_id required"}), 400
    if english_only and arabic_only:
        return jsonify({"error": "Cannot set both english_only and arabic_only"}), 400
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

        # Validate music if provided
        music_filename = None
        if music_id:
            music_row = conn.execute("SELECT filename FROM admin_music WHERE id = ?", (music_id,)).fetchone()
            if not music_row:
                return jsonify({"error": "Music track not found"}), 404
            music_filename = music_row["filename"]

        # Build verse_data from TTS cache entries
        folder = _get_reciter_folder(reciter_id) if not english_only else None
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
            # Get Arabic text (still needed for reference even in english_only)
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, vs)
            ).fetchone()
            arabic = _strip_bismillah(verse_row["text_uthmani"], ch, vs) if verse_row else ""

            entry = {
                "chapter": ch,
                "verse": vs,
                "verse_ref": f"{_surah_name(ch)} {ch}:{vs}",
                "arabic_text": arabic,
                "translation": cache_row["translation_text"],
                "tts_filename": cache_row["filename"],
                "english_only": english_only,
                "arabic_only": arabic_only,
            }
            if not english_only:
                entry["audio_url"] = f"{audio_base}/{folder}/{ch:03d}{vs:03d}.mp3"
            verse_data.append(entry)

        # Store music filename as metadata in the first entry
        if music_filename and verse_data:
            verse_data[0]["_music_filename"] = music_filename

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


# --------------- Admin: Explanation Video Generation ---------------

def _generate_explanation_video_task(video_id):
    """Background task: generate explanation video from segments."""
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
    segments = verse_data.get("segments", [])
    fmt = row["format"]
    target_w, target_h = (1080, 1920) if fmt == "short" else (1920, 1080)

    music_filename = verse_data.get("_music_filename")
    music_path = os.path.join(_MUSIC_DIR, music_filename) if music_filename else None
    if music_path and not os.path.isfile(music_path):
        music_path = None

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

    tmpdir = tempfile.mkdtemp(prefix="explvid_")
    try:
        # Step 1: Copy TTS files for each segment
        _update_video_status(video_id, "processing", "Preparing audio files...")
        seg_files = []
        for i, seg in enumerate(segments):
            fn = seg.get("tts_filename")
            if not fn:
                _update_video_status(video_id, "failed",
                    error=f"Segment {i} missing TTS audio")
                return
            src = os.path.join(_TTS_CACHE_DIR, fn)
            dst = os.path.join(tmpdir, f"seg_{i:03d}.mp3")
            if not os.path.isfile(src):
                _update_video_status(video_id, "failed",
                    error=f"TTS file missing for segment {i}: {fn}")
                return
            shutil.copy2(src, dst)
            seg_files.append(dst)

        # Step 2: Build timeline with pauses between segments
        _update_video_status(video_id, "processing", "Building timeline...")
        seg_durs = [_get_audio_duration(f) for f in seg_files]

        timeline = []
        closing_seg_index = None  # track closing segment to overlay on outro
        current_time = 0.0
        for i, seg in enumerate(segments):
            if seg["type"] == "closing":
                closing_seg_index = i
                continue  # closing audio plays during outro, not here
            text = seg.get("text") or seg.get("translation") or ""
            entry = {
                "phase": seg["type"],  # transition, verses
                "start": current_time,
                "dur": seg_durs[i],
                "text": text,
            }
            if seg["type"] == "verses":
                entry["ref"] = seg.get("ref", "")
            timeline.append(entry)
            current_time += seg_durs[i]

            # Add pause after segments
            if seg["type"] == "transition":
                current_time += 0.3  # short pause after transition
            elif seg["type"] == "verses":
                current_time += 0.8  # longer pause after verses

        # Outro — duration is the longer of 5s or the closing audio
        closing_dur = seg_durs[closing_seg_index] if closing_seg_index is not None else 0
        outro_dur = max(5.0, closing_dur + 1.0)  # +1s padding after closing speech
        outro_start = current_time
        total_duration = current_time + outro_dur

        # Step 3: Concatenate audio with pauses
        _update_video_status(video_id, "processing", "Building audio track...")

        # Generate silence segments for pauses between segments
        silence_03 = os.path.join(tmpdir, "silence_03.mp3")
        silence_08 = os.path.join(tmpdir, "silence_08.mp3")
        for dur, path in [(0.3, silence_03), (0.8, silence_08)]:
            subprocess.run(
                [_FFMPEG, "-y", "-f", "lavfi", "-i",
                 f"anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}",
                 "-c:a", "libmp3lame", "-q:a", "9", path],
                capture_output=True, timeout=30,
            )

        # Generate outro silence (length of full outro)
        silence_outro = os.path.join(tmpdir, "silence_outro.mp3")
        subprocess.run(
            [_FFMPEG, "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=44100:cl=stereo", "-t", f"{outro_dur:.3f}",
             "-c:a", "libmp3lame", "-q:a", "9", silence_outro],
            capture_output=True, timeout=30,
        )

        # If we have closing audio, overlay it onto the outro silence
        if closing_seg_index is not None:
            outro_audio = os.path.join(tmpdir, "outro_with_closing.mp3")
            subprocess.run(
                [_FFMPEG, "-y",
                 "-i", silence_outro,
                 "-i", seg_files[closing_seg_index],
                 "-filter_complex",
                 "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
                 "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2",
                 outro_audio],
                capture_output=True, timeout=60,
            )
        else:
            outro_audio = silence_outro

        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for i, seg in enumerate(segments):
                if seg["type"] == "closing":
                    continue  # closing audio is in the outro
                f.write(f"file '{seg_files[i]}'\n")
                if seg["type"] == "transition":
                    f.write(f"file '{silence_03}'\n")
                elif seg["type"] == "verses":
                    f.write(f"file '{silence_08}'\n")
            f.write(f"file '{outro_audio}'\n")

        combined_audio = os.path.join(tmpdir, "combined.mp3")
        subprocess.run(
            [_FFMPEG, "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", combined_audio],
            capture_output=True, timeout=120,
        )

        # Step 4: Build ASS subtitle file
        _update_video_status(video_id, "processing", "Rendering video...")

        trans_fontsize = 64 if fmt == "short" else 52
        ref_fontsize = 62 if fmt == "short" else 52
        text_colour = "&H00FFFFFF"
        outline_colour = "&H50000000"
        fonts_dir = os.path.join(os.path.dirname(__file__), "data", "fonts")
        ass_path = os.path.join(tmpdir, "subs.ass")

        content_band_h = 380 if fmt == "short" else 310
        content_band_y = (target_h - content_band_h) // 2
        # Ref band sits directly below the content band
        ref_band_h = 110 if fmt == "short" else 90
        ref_band_y = content_band_y + content_band_h
        # MarginV from bottom = distance from screen bottom to ref band area
        ref_margin_v = target_h - ref_band_y - ref_band_h + 20

        with open(ass_path, "w", encoding="utf-8") as af:
            af.write("[Script Info]\n")
            af.write("ScriptType: v4.00+\n")
            af.write(f"PlayResX: {target_w}\n")
            af.write(f"PlayResY: {target_h}\n\n")

            af.write("[V4+ Styles]\n")
            af.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                     "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                     "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                     "Alignment, MarginL, MarginR, MarginV, Encoding\n")
            af.write(f"Style: Ref,Liberation Sans,{ref_fontsize},{text_colour},"
                     f"&H000000FF,{outline_colour},&H00000000,1,0,0,0,100,100,0,0,"
                     f"1,3,0,2,40,40,{ref_margin_v},0\n")
            af.write(f"Style: Trans,Liberation Sans,{trans_fontsize},{text_colour},"
                     f"&H000000FF,{outline_colour},&H00000000,0,0,0,0,100,100,0,0,"
                     f"1,3,0,5,60,60,0,0\n")
            outro_site_fs = 90 if fmt == "short" else 72
            outro_tag_fs = 54 if fmt == "short" else 44
            af.write(f"Style: OutroSite,Liberation Sans,{outro_site_fs},&H00FFFFFF,"
                     f"&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,"
                     f"1,0,0,5,40,40,0,0\n")
            af.write(f"Style: OutroTag,Liberation Sans,{outro_tag_fs},&H80FFFFFF,"
                     f"&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,"
                     f"1,0,0,5,40,40,0,0\n")

            af.write("\n[Events]\n")
            af.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
                     "MarginV, Effect, Text\n")

            def _ass_time_local(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = seconds % 60
                return f"{h}:{m:02d}:{s:05.2f}"

            def _ass_escape_local(text):
                return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            for t in timeline:
                start = _ass_time_local(t["start"])
                end = _ass_time_local(t["start"] + t["dur"])
                text = _ass_escape_local(t["text"])

                if t["phase"] == "verses":
                    ref = _ass_escape_local(t.get("ref", ""))
                    af.write(f"Dialogue: 0,{start},{end},Ref,,0,0,0,,{{\\fad(600,0)}}{ref}\n")
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,{{\\fad(600,0)}}{text}\n")
                # transitions and closing are spoken only — no subtitle text

            # Outro
            outro_s = _ass_time_local(outro_start)
            outro_e = _ass_time_local(outro_start + outro_dur)
            cx = target_w // 2
            cy = target_h // 2
            site_y = cy - 40
            tag_y = cy + 70
            af.write(f"Dialogue: 0,{outro_s},{outro_e},OutroSite,,0,0,0,,"
                     f"{{\\fad(800,0)\\pos({cx},{site_y})}}al-nuqta.com\n")
            af.write(f"Dialogue: 0,{outro_s},{outro_e},OutroTag,,0,0,0,,"
                     f"{{\\fad(1200,0)\\pos({cx},{tag_y})}}A Root Based Translation of the Quran\n")

        # Step 5: Drawbox filters — only show bands during verse segments
        # Fade-in bands over 0.6s to match subtitle fade
        band_fade_dur = 0.6
        band_fade_steps = 6
        band_step_dur = band_fade_dur / band_fade_steps
        drawbox_parts = []
        for t in timeline:
            if t["phase"] != "verses":
                continue  # transitions are spoken only, no visual overlay
            s, e = t["start"], t["start"] + t["dur"]
            # Stepped fade-in for bands
            for step in range(band_fade_steps):
                t_s = s + step * band_step_dur
                t_e = s + (step + 1) * band_step_dur
                alpha = 0.5 * (step + 1) / band_fade_steps
                step_en = f"between(t\\,{t_s:.3f}\\,{t_e:.3f})"
                drawbox_parts.append(
                    f"drawbox=x=0:y={content_band_y}:w=iw:h={content_band_h}"
                    f":color=black@{alpha:.3f}:t=fill:enable='{step_en}'"
                )
                drawbox_parts.append(
                    f"drawbox=x=0:y={ref_band_y}:w=iw:h={ref_band_h}"
                    f":color=black@{alpha:.3f}:t=fill:enable='{step_en}'"
                )
            # Hold at full opacity after fade
            hold_en = f"between(t\\,{s + band_fade_dur:.3f}\\,{e:.3f})"
            drawbox_parts.append(
                f"drawbox=x=0:y={content_band_y}:w=iw:h={content_band_h}"
                f":color=black@0.5:t=fill:enable='{hold_en}'"
            )
            drawbox_parts.append(
                f"drawbox=x=0:y={ref_band_y}:w=iw:h={ref_band_h}"
                f":color=black@0.5:t=fill:enable='{hold_en}'"
            )

        # Outro: fade-in dark overlay over 1.5s (stepped opacity 0 → 0.75)
        fade_dur = 1.5
        fade_steps = 10
        step_dur = fade_dur / fade_steps
        for s in range(fade_steps):
            t_s = outro_start + s * step_dur
            t_e = outro_start + (s + 1) * step_dur
            alpha = 0.75 * (s + 1) / fade_steps
            drawbox_parts.append(
                f"drawbox=x=0:y=0:w=iw:h=ih"
                f":color=black@{alpha:.3f}:t=fill"
                f":enable='between(t\\,{t_s:.3f}\\,{t_e:.3f})'"
            )
        drawbox_parts.append(
            f"drawbox=x=0:y=0:w=iw:h=ih"
            f":color=black@0.75:t=fill"
            f":enable='gte(t\\,{outro_start + fade_dur:.3f})'"
        )

        # Step 6: Final render
        output_filename = f"expl_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(_GENERATED_VIDEOS_DIR, output_filename)

        vf_parts = [
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase",
            f"crop={target_w}:{target_h}",
        ] + drawbox_parts + [
            f"ass={ass_path}:fontsdir={fonts_dir}",
        ]
        vf = ",".join(vf_parts)

        render_timeout = max(600, int(total_duration * 10))

        if music_path:
            # Voice at full volume, music at ~4% so narrator is clearly heard
            af_mix = (
                f"[1:a]volume=1.0[voice];"
                f"[2:a]volume=0.01,afade=t=out:st={max(0, total_duration - 5):.3f}:d=5[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=3:normalize=0[aout]"
            )
            cmd = [
                _FFMPEG, "-y",
                "-stream_loop", "-1", "-i", bg_path,
                "-i", combined_audio,
                "-i", music_path,
                "-vf", vf,
                "-filter_complex", af_mix,
                "-t", f"{total_duration:.3f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0", "-map", "[aout]",
                "-movflags", "+faststart",
                output_path,
            ]
        else:
            cmd = [
                _FFMPEG, "-y",
                "-stream_loop", "-1", "-i", bg_path,
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


@app.route("/api/admin/generate-explanation-video", methods=["POST"])
@admin_required
def admin_generate_explanation_video():
    """Start explanation video generation in a background thread."""
    body = request.get_json(silent=True) or {}
    expl_id = body.get("explanation_id")
    fmt = body.get("format", "")
    resource_id = body.get("resource_id")
    music_id = body.get("music_id")

    if not isinstance(expl_id, int) or expl_id <= 0:
        return jsonify({"error": "Valid explanation_id required"}), 400
    if fmt not in ("short", "regular"):
        return jsonify({"error": "Format must be 'short' or 'regular'"}), 400
    if not isinstance(resource_id, int) or resource_id <= 0:
        return jsonify({"error": "Valid resource_id required"}), 400

    conn = get_db()
    try:
        # Check concurrent limit
        active = conn.execute(
            "SELECT COUNT(*) FROM admin_generated_videos WHERE status IN ('pending','processing')"
        ).fetchone()[0]
        if active >= 2:
            return jsonify({"error": "Too many videos generating. Please wait."}), 429

        # Validate explanation
        expl = conn.execute(
            "SELECT * FROM admin_explanations WHERE id = ?", (expl_id,)
        ).fetchone()
        if not expl:
            return jsonify({"error": "Explanation not found"}), 404
        if expl["status"] != "ready":
            return jsonify({"error": "Explanation TTS not complete. Generate all TTS first."}), 400

        # Validate resource
        res_row = conn.execute("SELECT id FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not res_row:
            return jsonify({"error": "Resource not found"}), 404

        # Validate music if provided
        music_filename = None
        if music_id:
            music_row = conn.execute("SELECT filename FROM admin_music WHERE id = ?", (music_id,)).fetchone()
            if not music_row:
                return jsonify({"error": "Music track not found"}), 404
            music_filename = music_row["filename"]

        segments = json.loads(expl["segments"])
        verse_data = {"segments": segments}
        if music_filename:
            verse_data["_music_filename"] = music_filename

        title = expl["title"]
        conn.execute(
            """INSERT INTO admin_generated_videos (title, format, resource_id, reciter_id, verse_data, status)
               VALUES (?, ?, ?, 0, ?, 'pending')""",
            (title, fmt, resource_id, json.dumps(verse_data)),
        )
        conn.commit()
        video_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

    threading.Thread(target=_generate_explanation_video_task, args=(video_id,), daemon=True).start()
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


# --------------- Video Description Generation ---------------

@app.route("/api/admin/generate-description", methods=["POST"])
@admin_required
def admin_generate_description():
    """Generate a YouTube description for selected verses using Claude."""
    body = request.get_json(silent=True) or {}
    verses = body.get("verses", [])  # [{chapter, verse}, ...]
    if not verses:
        return jsonify({"error": "No verses provided"}), 400

    api_key = _get_claude_api_key()
    if not api_key:
        return jsonify({"error": "Claude API key not configured"}), 500

    conn = get_db()
    try:
        verse_blocks = []
        first_ch, first_v = verses[0]["chapter"], verses[0]["verse"]
        last_ch, last_v = verses[-1]["chapter"], verses[-1]["verse"]

        for v in verses:
            ch, vs = v["chapter"], v["verse"]

            # Arabic text
            row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, vs),
            ).fetchone()
            arabic = row["text_uthmani"] if row else ""

            # AI translation + departure notes (latest config)
            ai = conn.execute(
                "SELECT translation_text, departure_notes FROM ai_translations "
                "WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1",
                (ch, vs),
            ).fetchone()
            translation = ai["translation_text"] if ai else ""
            departure_notes = ai["departure_notes"] if ai and ai["departure_notes"] else ""

            # Conventional translation for comparison
            conv = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
                (ch, vs),
            ).fetchone()
            conventional = html.unescape(re.sub(r"<[^>]+>", "", conv["text_en"])) if conv else ""

            # Word meanings with departure notes
            words = conn.execute(
                "SELECT word_pos, meaning_short, meaning_detailed, departure_notes, "
                "preferred_translation, preferred_source "
                "FROM ai_word_meanings WHERE chapter = ? AND verse = ? "
                "ORDER BY word_pos",
                (ch, vs),
            ).fetchall()
            word_insights = []
            for w in words:
                if w["departure_notes"]:
                    word_insights.append(
                        f"  Word {w['word_pos']}: \"{w['meaning_short']}\" — {w['departure_notes']}"
                    )

            block = f"Verse {ch}:{vs}\n"
            block += f"  Arabic: {arabic}\n"
            block += f"  Translation: {translation}\n"
            if conventional and conventional != translation:
                block += f"  Conventional: {conventional}\n"
            if departure_notes:
                block += f"  Translation notes: {departure_notes}\n"
            if word_insights:
                block += "  Word-level insights:\n" + "\n".join(word_insights) + "\n"

            verse_blocks.append(block)

        # Build link
        link = f"https://al-nuqta.com/verse/{first_ch}:{first_v}"
        surah_name = _surah_name(first_ch)
        if first_ch == last_ch:
            if first_v == last_v:
                ref = f"{surah_name} {first_ch}:{first_v}"
            else:
                ref = f"{surah_name} {first_ch}:{first_v}-{last_v}"
        else:
            ref = f"{surah_name} {first_ch}:{first_v} - {_surah_name(last_ch)} {last_ch}:{last_v}"

        prompt = (
            f"Write a YouTube video description for a Quran recitation of {ref}.\n\n"
            "The description should have this structure:\n"
            f"1. Start with the verse reference link on its own line: {link}\n"
            "2. Leave a blank line, then write a sustained, contemplative reflection "
            "on these verses. Walk the reader through the movement of the text, "
            "unpacking what each verse establishes and how it builds toward "
            "the whole. Draw on translation notes and word-level insights to surface "
            "what most readers would miss, but weave them in naturally as discoveries "
            "within the reflection, not as separate linguistic commentary.\n"
            "3. Aim for 3-5 paragraphs. No hashtags, no emojis, no calls to action.\n\n"
            "Style guidelines:\n"
            "- Write with affirmative, forward-moving prose. State what something IS, "
            "not what it is not. Avoid negation-then-correction patterns "
            "(\"not X but Y\", \"not merely\", \"it is not... rather\").\n"
            "- Never use: \"merely\", \"simply put\", \"in other words\", \"it is worth noting\"\n"
            "- Avoid em dashes. Use commas, periods, or colons instead.\n"
            "- Avoid watered-down spiritual clichés (\"journey of faith\", \"timeless wisdom\", "
            "\"profound reminder\", \"beautifully captures\", \"speaks to the heart\")\n"
            "- Let the weight come from the ideas themselves, not from telling the reader "
            "something is profound or striking. Show, do not announce.\n"
            "- When the Arabic carries nuance (intensification, an unusual root meaning, "
            "a departure from conventional translation), explain the actual semantic content "
            "so the reader feels they have learned something concrete.\n"
            "- Write as someone who has sat with these verses. The tone should feel like "
            "a person thinking out loud with real conviction, tracing the logic of the text "
            "step by step.\n\n"
            "Here are the verses with all available context:\n\n"
            + "\n".join(verse_blocks)
        )

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": _PROXY_MODEL,
                "max_tokens": 1024,
                "temperature": 0.8,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not resp.ok:
            return jsonify({"error": f"Claude API error: {resp.status_code}"}), 502

        result = resp.json()
        text = result.get("content", [{}])[0].get("text", "")
        return jsonify({"description": text.strip()})

    except requests.Timeout:
        return jsonify({"error": "Claude API timed out"}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        conn.close()


# --------------- Moving Verse Suggestions ---------------

_MOVING_VERSES_SYSTEM_PROMPT = """\
You are a Quranic content curator for YouTube Shorts. Identify groups of 2-5 \
consecutive verses that are emotionally moving and meaningful as standalone clips.

Selection criteria:
- Emotional resonance: verses that evoke awe, hope, mercy, grief, humility, \
gratitude, or spiritual awakening
- Narrative completeness: the group conveys a complete thought or mini-story
- Universal appeal: resonates with a broad audience, not just scholars
- Poetic beauty: rhetorical power, imagery, parallelism
- Standalone clarity: a viewer seeing only these verses understands the message

AVOID selecting:
- Legal or jurisprudence verses (inheritance, dietary laws, etc.)
- Verses that require extensive context to understand
- Groups where emotional impact comes from only one verse (padding)
- Purely repetitive sections with no buildup

Categories (assign exactly one per group):
- "awe" — Divine majesty, creation, cosmic scale
- "mercy" — Divine compassion, forgiveness, tenderness
- "hope" — Promise, comfort, reassurance
- "grief" — Loss, regret, the human condition
- "warning" — Accountability, consequences, urgency
- "gratitude" — Blessings, reflection, thankfulness
- "devotion" — Love of God, worship, spiritual longing
- "justice" — Fairness, standing for truth, protecting the weak

Return ONLY a JSON array. Each element must have:
- "chapter": integer (surah number)
- "verse_start": integer (first verse)
- "verse_end": integer (last verse)
- "score": float 0.0-1.0 (emotional impact — use 0.8+ sparingly)
- "category": one of the categories above
- "title": a short evocative English title (3-8 words)
- "reasoning": 1-2 sentences explaining the emotional power

Return an empty array [] if no group in the given surahs qualifies.
Aim for quality over quantity — typically 1-3 groups per surah.\
"""

# Surahs often known for emotional/spiritual content (used for weighting)
_PRIORITY_SURAHS = [
    1, 2, 3, 12, 14, 17, 18, 19, 20, 21, 23, 25, 26, 29, 31, 33, 35, 36,
    37, 39, 40, 41, 42, 43, 44, 50, 51, 53, 54, 55, 56, 57, 59, 67, 73,
    74, 75, 76, 77, 78, 79, 81, 82, 84, 86, 87, 89, 90, 91, 93, 94, 95,
    99, 100, 101, 102, 103, 112, 113, 114,
]


def _fetch_surah_text_for_suggestion(conn, surah: int) -> str:
    """Build verse text block for a surah (Arabic + best English translation)."""
    rows = conn.execute(
        "SELECT v.verse, v.text_uthmani, t.text_en "
        "FROM verses v "
        "LEFT JOIN translations t ON v.chapter = t.chapter AND v.verse = t.verse "
        "WHERE v.chapter = ? ORDER BY v.verse",
        (surah,),
    ).fetchall()

    lines = []
    for r in rows:
        arabic = _strip_bismillah(r["text_uthmani"], surah, r["verse"])
        # Prefer AI translation (latest config), fall back to conventional
        ai_row = conn.execute(
            "SELECT translation_text FROM ai_translations "
            "WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1",
            (surah, r["verse"]),
        ).fetchone()
        if ai_row:
            english = ai_row["translation_text"]
        else:
            raw = r["text_en"] or ""
            english = html.unescape(re.sub(r"<[^>]+>", "", raw))
        lines.append(f"Verse {r['verse']}:\n  Arabic: {arabic}\n  English: {english}")

    name = _surah_name(surah)
    return f"## Surah {surah}: {name}\nTotal verses: {len(rows)}\n\n" + "\n\n".join(lines)


def _build_translation_snippet(conn, chapter: int, vs: int, ve: int) -> str:
    """Concatenate English translations for a verse range."""
    parts = []
    for v in range(vs, ve + 1):
        ai_row = conn.execute(
            "SELECT translation_text FROM ai_translations "
            "WHERE chapter = ? AND verse = ? ORDER BY config_id DESC LIMIT 1",
            (chapter, v),
        ).fetchone()
        if ai_row:
            parts.append(ai_row["translation_text"])
        else:
            conv = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
                (chapter, v),
            ).fetchone()
            raw = conv["text_en"] if conv else ""
            parts.append(html.unescape(re.sub(r"<[^>]+>", "", raw)))
    return " ".join(parts)


def _parse_moving_groups_response(raw: str) -> list:
    """Parse JSON array from Claude response."""
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {cleaned[:200]}")
    return json.loads(cleaned[start:end + 1])


@app.route("/api/admin/moving-verse-suggestions", methods=["POST"])
@admin_required
def admin_moving_verse_suggestion():
    """Return an emotionally moving verse group suggestion.

    Tries cached unused suggestions first; calls Claude API if cache is empty.
    """
    data = request.get_json(silent=True) or {}
    category = data.get("category")
    exclude_ids = data.get("exclude_ids", [])

    conn = get_db()
    try:
        # --- Try serving from cache ---
        where_parts = ["used = 0"]
        params: list = []
        if category:
            where_parts.append("category = ?")
            params.append(category)
        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            where_parts.append(f"id NOT IN ({placeholders})")
            params.extend(exclude_ids)

        where_sql = " AND ".join(where_parts)
        cached = conn.execute(
            f"SELECT * FROM moving_verse_groups WHERE {where_sql} ORDER BY RANDOM() LIMIT 1",
            params,
        ).fetchone()

        if cached:
            remaining = conn.execute(
                f"SELECT COUNT(*) as cnt FROM moving_verse_groups WHERE {where_sql}",
                params,
            ).fetchone()["cnt"] - 1
            return jsonify({
                "id": cached["id"],
                "chapter": cached["chapter"],
                "verse_start": cached["verse_start"],
                "verse_end": cached["verse_end"],
                "surah_name": _surah_name(cached["chapter"]),
                "emotional_score": cached["emotional_score"],
                "category": cached["category"],
                "title": cached["title"],
                "reasoning": cached["reasoning"],
                "translation_snippet": cached["translation_snippet"],
                "remaining_count": max(0, remaining),
            })

        # --- No cached suggestions — call Claude API ---
        if not _get_claude_api_key():
            return jsonify({"error": "Claude API key not configured"}), 500

        # Pick surahs to analyze — prefer ones not yet covered
        covered = {
            r["chapter"]
            for r in conn.execute("SELECT DISTINCT chapter FROM moving_verse_groups").fetchall()
        }
        uncovered_priority = [s for s in _PRIORITY_SURAHS if s not in covered]
        uncovered_other = [s for s in range(1, 115) if s not in covered and s not in _PRIORITY_SURAHS]

        import random as _rand
        if uncovered_priority:
            sample_pool = uncovered_priority
        elif uncovered_other:
            sample_pool = uncovered_other
        else:
            # All surahs covered — pick random ones for fresh suggestions
            sample_pool = list(range(1, 115))

        chosen = _rand.sample(sample_pool, min(5, len(sample_pool)))

        # Build prompt with verse text from chosen surahs
        surah_blocks = []
        for s in chosen:
            surah_blocks.append(_fetch_surah_text_for_suggestion(conn, s))

        user_prompt = (
            "Identify the most emotionally moving groups of consecutive verses "
            "from the following surahs. Return 1-3 groups per surah.\n\n"
            + "\n\n---\n\n".join(surah_blocks)
        )

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": _get_claude_api_key(),
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 4096,
                "temperature": 0.7,
                "system": _MOVING_VERSES_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=60,
        )
        if not resp.ok:
            return jsonify({"error": f"Claude API error: {resp.status_code}"}), 502

        body = resp.json()
        text = body.get("content", [{}])[0].get("text", "")
        groups = _parse_moving_groups_response(text)

        if not isinstance(groups, list):
            return jsonify({"error": "Invalid response from Claude"}), 502

        # Validate and insert
        inserted_ids = []
        for g in groups:
            ch = g.get("chapter")
            vs = g.get("verse_start")
            ve = g.get("verse_end")
            if not all(isinstance(x, int) for x in [ch, vs, ve]):
                continue
            if ch < 1 or ch > 114 or vs < 1 or ve < vs:
                continue
            if ve - vs + 1 > 5 or ve - vs + 1 < 2:
                continue
            score = max(0.0, min(1.0, float(g.get("score", 0.5))))
            cat = g.get("category", "awe")
            title = g.get("title", "Untitled")[:200]
            reasoning = g.get("reasoning", "")[:1000]
            snippet = _build_translation_snippet(conn, ch, vs, ve)

            try:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO moving_verse_groups "
                    "(chapter, verse_start, verse_end, emotional_score, category, "
                    "title, reasoning, translation_snippet) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (ch, vs, ve, score, cat, title, reasoning, snippet),
                )
                if cur.lastrowid:
                    inserted_ids.append(cur.lastrowid)
            except Exception:
                pass

        conn.commit()

        if not inserted_ids:
            return jsonify({"error": "No valid suggestions found. Try again."}), 404

        # Return the first newly inserted suggestion
        row = conn.execute(
            "SELECT * FROM moving_verse_groups WHERE id = ?", (inserted_ids[0],)
        ).fetchone()
        remaining = len(inserted_ids) - 1
        return jsonify({
            "id": row["id"],
            "chapter": row["chapter"],
            "verse_start": row["verse_start"],
            "verse_end": row["verse_end"],
            "surah_name": _surah_name(row["chapter"]),
            "emotional_score": row["emotional_score"],
            "category": row["category"],
            "title": row["title"],
            "reasoning": row["reasoning"],
            "translation_snippet": row["translation_snippet"],
            "remaining_count": remaining,
        })

    except requests.Timeout:
        return jsonify({"error": "Claude API timed out — try again"}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        conn.close()


# --------------- Admin: Pipelines ---------------

def _ensure_pipeline_tables():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_pipelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'english',
                resource_id INTEGER NOT NULL,
                voice_id TEXT NOT NULL,
                show_bands INTEGER NOT NULL DEFAULT 1,
                music_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # reciter_id is required for Arabic pipelines (NULL for English)
        try:
            conn.execute("ALTER TABLE admin_pipelines ADD COLUMN reciter_id INTEGER")
            conn.commit()
        except Exception:
            pass
        # random_resource flag: when 1, pick a random resource per run
        try:
            conn.execute("ALTER TABLE admin_pipelines ADD COLUMN random_resource INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_pipeline_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL REFERENCES admin_pipelines(id),
                verse_data TEXT NOT NULL DEFAULT '[]',
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
        # Add youtube metadata + manual override columns (idempotent migration)
        for col, coltype in (
            ("youtube_title", "TEXT"),
            ("youtube_description", "TEXT"),
            ("youtube_tags", "TEXT"),              # JSON array of strings
            ("youtube_video_id", "TEXT"),          # ID returned by YouTube after upload
            ("manual_chapter", "INTEGER"),
            ("manual_ayah_start", "INTEGER"),
            ("manual_ayah_end", "INTEGER"),
            # Scheduler integration
            ("triggered_by", "TEXT DEFAULT 'manual'"),  # 'manual' | 'scheduler'
            ("uploaded_to_youtube", "INTEGER NOT NULL DEFAULT 0"),
        ):
            try:
                conn.execute(f"ALTER TABLE admin_pipeline_videos ADD COLUMN {col} {coltype}")
                conn.commit()
            except Exception:
                pass

        # Pipeline scheduler — one config row per pipeline, audit log per fire
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_schedules (
                pipeline_id INTEGER PRIMARY KEY REFERENCES admin_pipelines(id) ON DELETE CASCADE,
                times TEXT NOT NULL DEFAULT '[]',
                max_runs_per_day INTEGER NOT NULL DEFAULT 2,
                enabled INTEGER NOT NULL DEFAULT 0,
                grace_minutes INTEGER NOT NULL DEFAULT 30,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_schedule_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL,
                scheduled_time TEXT NOT NULL,
                fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                video_id INTEGER,
                status TEXT NOT NULL,
                note TEXT
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_psr_pipeline_time
            ON pipeline_schedule_runs (pipeline_id, scheduled_time)
        """)
        conn.commit()
        # Reset stuck jobs on startup
        conn.execute(
            "UPDATE admin_pipeline_videos SET status='failed', error_message='Server restarted' "
            "WHERE status IN ('pending','selecting_verses','polishing','generating_tts','rendering','generating_metadata')"
        )
        conn.commit()
    finally:
        conn.close()


try:
    _ensure_pipeline_tables()
except Exception as e:
    print(f"WARNING: pipeline tables setup failed: {e}")


def _update_pipeline_video_status(video_id, status, progress="", error=""):
    conn = get_db()
    try:
        if error:
            conn.execute(
                "UPDATE admin_pipeline_videos SET status=?, progress=?, error_message=? WHERE id=?",
                (status, progress, error, video_id),
            )
        else:
            conn.execute(
                "UPDATE admin_pipeline_videos SET status=?, progress=? WHERE id=?",
                (status, progress, video_id),
            )
        conn.commit()
    finally:
        conn.close()


@app.route("/api/admin/pipelines", methods=["POST"])
@admin_required
def admin_create_pipeline():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()[:200]
    language = (body.get("language") or "english").strip().lower()
    resource_id = body.get("resource_id")
    voice_id = (body.get("voice_id") or "").strip()
    reciter_id = body.get("reciter_id")
    show_bands = bool(body.get("show_bands", True))
    random_resource = bool(body.get("random_resource", False))
    music_id = body.get("music_id")

    if language not in ("english", "arabic"):
        return jsonify({"error": "language must be 'english' or 'arabic'"}), 400
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not resource_id:
        return jsonify({"error": "Background video is required"}), 400

    if language == "english":
        if not voice_id:
            return jsonify({"error": "Voice is required for English pipelines"}), 400
        reciter_id = None
    else:  # arabic
        try:
            reciter_id = int(reciter_id) if reciter_id is not None else 0
        except (TypeError, ValueError):
            reciter_id = 0
        if not reciter_id:
            return jsonify({"error": "Reciter is required for Arabic pipelines"}), 400
        # voice_id column is NOT NULL — store empty string
        voice_id = voice_id or ""

    conn = get_db()
    try:
        res = conn.execute("SELECT id FROM admin_resources WHERE id = ?", (resource_id,)).fetchone()
        if not res:
            return jsonify({"error": "Background video not found"}), 404
        if music_id:
            mus = conn.execute("SELECT id FROM admin_music WHERE id = ?", (music_id,)).fetchone()
            if not mus:
                return jsonify({"error": "Music track not found"}), 404

        cur = conn.execute(
            "INSERT INTO admin_pipelines (name, language, resource_id, voice_id, reciter_id, show_bands, random_resource, music_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, language, resource_id, voice_id, reciter_id, 1 if show_bands else 0, 1 if random_resource else 0, music_id),
        )
        conn.commit()
        pipeline = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(pipeline)), 201
    finally:
        conn.close()


@app.route("/api/admin/pipelines", methods=["GET"])
@admin_required
def admin_list_pipelines():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM admin_pipelines ORDER BY created_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            count = conn.execute(
                "SELECT COUNT(*) as c FROM admin_pipeline_videos WHERE pipeline_id = ?", (r["id"],)
            ).fetchone()["c"]
            d["video_count"] = count
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@app.route("/api/admin/pipelines/<int:pipeline_id>", methods=["GET"])
@admin_required
def admin_get_pipeline(pipeline_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        d = dict(row)
        d["video_count"] = conn.execute(
            "SELECT COUNT(*) as c FROM admin_pipeline_videos WHERE pipeline_id = ?", (pipeline_id,)
        ).fetchone()["c"]
        return jsonify(d)
    finally:
        conn.close()


@app.route("/api/admin/pipelines/<int:pipeline_id>", methods=["PUT"])
@admin_required
def admin_update_pipeline(pipeline_id):
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404

        name = (body.get("name") or row["name"]).strip()[:200]
        resource_id = body.get("resource_id", row["resource_id"])
        voice_id = (body.get("voice_id") or row["voice_id"] or "").strip()
        show_bands = body.get("show_bands", bool(row["show_bands"]))
        music_id = body.get("music_id", row["music_id"])
        # Get reciter_id — try current row first, fall back safely
        try:
            existing_reciter_id = row["reciter_id"]
        except (IndexError, KeyError):
            existing_reciter_id = None
        reciter_id = body.get("reciter_id", existing_reciter_id)
        # Get random_resource flag
        try:
            existing_random = bool(row["random_resource"])
        except (IndexError, KeyError):
            existing_random = False
        random_resource = body.get("random_resource", existing_random)

        conn.execute(
            "UPDATE admin_pipelines SET name=?, resource_id=?, voice_id=?, reciter_id=?, show_bands=?, random_resource=?, music_id=?, updated_at=datetime('now') WHERE id=?",
            (name, resource_id, voice_id, reciter_id, 1 if show_bands else 0, 1 if random_resource else 0, music_id, pipeline_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
        return jsonify(dict(updated))
    finally:
        conn.close()


@app.route("/api/admin/pipelines/<int:pipeline_id>", methods=["DELETE"])
@admin_required
def admin_delete_pipeline(pipeline_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM admin_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        videos = conn.execute("SELECT * FROM admin_pipeline_videos WHERE pipeline_id = ?", (pipeline_id,)).fetchall()
        for v in videos:
            _cleanup_pipeline_video_files(v)
        conn.execute("DELETE FROM admin_pipeline_videos WHERE pipeline_id = ?", (pipeline_id,))
        # Scheduler rows: FK-CASCADE is declared but SQLite only honors it when
        # foreign_keys=ON is set per-connection, which we don't do globally.
        # Explicit deletes guarantee no orphans regardless of pragma state.
        conn.execute("DELETE FROM pipeline_schedules WHERE pipeline_id = ?", (pipeline_id,))
        conn.execute("DELETE FROM pipeline_schedule_runs WHERE pipeline_id = ?", (pipeline_id,))
        conn.execute("DELETE FROM admin_pipelines WHERE id = ?", (pipeline_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/pipelines/<int:pipeline_id>/generate", methods=["POST"])
@admin_required
def admin_pipeline_generate(pipeline_id):
    body = request.get_json(silent=True) or {}

    # Optional manual overrides
    manual_chapter = body.get("chapter")
    manual_ayah_start = body.get("ayah_start")
    manual_ayah_end = body.get("ayah_end")
    manual_title = (body.get("youtube_title") or "").strip() or None
    manual_description = (body.get("youtube_description") or "").strip() or None

    # Validate verse range if any manual verse field is provided
    if any(x is not None for x in (manual_chapter, manual_ayah_start, manual_ayah_end)):
        try:
            manual_chapter = int(manual_chapter)
            manual_ayah_start = int(manual_ayah_start)
            manual_ayah_end = int(manual_ayah_end)
        except (TypeError, ValueError):
            return jsonify({"error": "chapter, ayah_start, ayah_end must all be integers"}), 400
        if not (1 <= manual_chapter <= 114):
            return jsonify({"error": "chapter must be between 1 and 114"}), 400
        if manual_ayah_start < 1 or manual_ayah_end < manual_ayah_start:
            return jsonify({"error": "invalid ayah range"}), 400
        if manual_ayah_end - manual_ayah_start + 1 > 20:
            return jsonify({"error": "range too large (max 20 verses)"}), 400

    conn = get_db()
    try:
        pipeline = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
        if not pipeline:
            return jsonify({"error": "Pipeline not found"}), 404

        active = conn.execute(
            "SELECT COUNT(*) as c FROM admin_pipeline_videos "
            "WHERE status IN ('pending','selecting_verses','polishing','generating_tts','rendering','generating_metadata')"
        ).fetchone()["c"]
        if active >= 2:
            return jsonify({"error": "Too many videos generating. Please wait."}), 429

        cur = conn.execute(
            "INSERT INTO admin_pipeline_videos "
            "(pipeline_id, status, manual_chapter, manual_ayah_start, manual_ayah_end, "
            " youtube_title, youtube_description) "
            "VALUES (?, 'pending', ?, ?, ?, ?, ?)",
            (pipeline_id, manual_chapter, manual_ayah_start, manual_ayah_end,
             manual_title, manual_description),
        )
        conn.commit()
        video_id = cur.lastrowid

        t = threading.Thread(target=_pipeline_generate_task, args=(video_id,), daemon=True)
        t.start()

        return jsonify({"id": video_id, "status": "pending"}), 201
    finally:
        conn.close()


@app.route("/api/admin/pipeline-videos", methods=["GET"])
@admin_required
def admin_list_pipeline_videos():
    pipeline_id = request.args.get("pipeline_id", type=int)
    conn = get_db()
    try:
        if pipeline_id:
            rows = conn.execute(
                "SELECT * FROM admin_pipeline_videos WHERE pipeline_id = ? ORDER BY created_at DESC",
                (pipeline_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM admin_pipeline_videos ORDER BY created_at DESC"
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


def _cleanup_pipeline_video_files(row):
    """Remove the rendered video and TTS files for a pipeline video row."""
    if row["filename"]:
        fp = os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])
        if os.path.isfile(fp):
            os.remove(fp)
    # Clean up TTS files stored in verse_data
    try:
        for v in json.loads(row["verse_data"] or "[]"):
            for key in ("tts_filename", "intro_tts_filename"):
                tts = v.get(key)
                if tts:
                    tp = os.path.join(_TTS_CACHE_DIR, tts)
                    if os.path.isfile(tp):
                        os.remove(tp)
    except (json.JSONDecodeError, TypeError):
        pass


@app.route("/api/admin/pipeline-videos/<int:video_id>", methods=["DELETE"])
@admin_required
def admin_delete_pipeline_video(video_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM admin_pipeline_videos WHERE id = ?", (video_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        _cleanup_pipeline_video_files(row)
        conn.execute("DELETE FROM admin_pipeline_videos WHERE id = ?", (video_id,))
        conn.commit()
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.route("/api/admin/pipeline-videos/<int:video_id>/download", methods=["GET"])
@admin_required
def admin_download_pipeline_video(video_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM admin_pipeline_videos WHERE id = ? AND status = 'complete'", (video_id,)
        ).fetchone()
        if not row or not row["filename"]:
            return jsonify({"error": "Video not available"}), 404
        filepath = os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])
        if not os.path.isfile(filepath):
            return jsonify({"error": "File missing"}), 404
        return send_from_directory(
            _GENERATED_VIDEOS_DIR, row["filename"],
            mimetype="video/mp4", as_attachment=True,
            download_name=f"pipeline_{video_id}.mp4",
        )
    finally:
        conn.close()


def _gather_verse_root_insights(conn, verse_data):
    """Gather root word connections and cognate data for a set of verses."""
    if not verse_data or len(verse_data) < 2:
        return ""

    # Get roots for each verse from the IDF engine
    verse_root_map = {}
    for v in verse_data:
        key = (v["chapter"], v["verse"])
        roots = _verse_roots.get(key, set())
        if roots:
            verse_root_map[key] = roots

    if len(verse_root_map) < 2:
        return ""

    # Find roots shared across any two verses
    all_keys = list(verse_root_map.keys())
    shared_roots = set()
    for i in range(len(all_keys)):
        for j in range(i + 1, len(all_keys)):
            common = verse_root_map[all_keys[i]] & verse_root_map[all_keys[j]]
            shared_roots.update(common)

    if not shared_roots:
        return ""

    # Rank by IDF (rarer roots = more interesting connections)
    ranked = sorted(shared_roots, key=lambda r: _root_idf.get(r, 0), reverse=True)
    top_roots = ranked[:5]

    insights = []
    for root_bw in top_roots:
        arabic = _root_arabic_map.get(root_bw, "")
        containing = [k for k in all_keys if root_bw in verse_root_map.get(k, set())]
        refs = [f"{ch}:{vs}" for ch, vs in containing]

        # Root meaning from AI table
        meaning = None
        try:
            row = conn.execute(
                "SELECT primary_meaning FROM ai_root_meanings WHERE root_buckwalter = ? "
                "ORDER BY config_id DESC LIMIT 1",
                (root_bw,),
            ).fetchone()
            if row:
                meaning = _clean_root_gloss(row["primary_meaning"])
        except Exception:
            pass

        # Cognate data
        cognate_note = ""
        try:
            cognate = _get_cognate(conn, root_bw)
            if cognate and cognate.get("concepts"):
                concepts = cognate["concepts"]
                if concepts:
                    cognate_note = f" (Semitic root concept: {concepts[0]})"
        except Exception:
            pass

        line = f"Root '{arabic}' ({root_bw})"
        if meaning:
            line += f" meaning '{meaning}'"
        line += f" appears in verses {', '.join(refs)}"
        if cognate_note:
            line += cognate_note
        insights.append(line)

    return "\n".join(insights)


def _normalize_recitation_title(
    title: str, ref_string: str, ref_with_name: str,
) -> str:
    """Coerce the LLM-generated title into the operator-specified
    "<hook> (<surah verse:range>)" format.

    Catches three failure modes the prompt can't fully prevent:

      1. Old filing-label format → "Surah Al-Layl 92:12-19"
         Rebuild as "<hook>" + "(Al-Layl 92:12-19)" using the
         remainder after stripping the leading reference.

      2. Pipe-separator legacy format → "92:12-19 | The two paths…"
         Strip the "<ref> | " prefix, append "(<ref_with_name>)".

      3. Hook-only output (no parenthetical) → append the
         "(<ref_with_name>)" tail. Only when the title doesn't
         already contain a closing-paren-bracketed reference.

    Idempotent: if the title is already in the target shape it
    passes through unchanged. The check is permissive — anything
    ending with "(...verse:range)" or "(... <numeric ref>)" is
    treated as already-canonical.
    """
    t = title.strip()
    target_tail = f"({ref_with_name})"

    # Already canonical? Look for the parenthesised numeric ref at
    # the end. Use a permissive pattern — accept any "( ... 92:12-19 )"
    # tail even if the surah name varies.
    tail_pat = re.compile(
        r"\(\s*[^()]*?\d+:\d+(?:-\d+)?\s*\)\s*$"
    )
    if tail_pat.search(t):
        return t

    # 2. Pipe-separator legacy: strip "<ref> | " prefix.
    pipe_pat = re.compile(
        r"^\s*\d+:\d+(?:-\d+)?\s*[|—–-]\s*",
    )
    pipe_match = pipe_pat.match(t)
    if pipe_match:
        hook = t[pipe_match.end():].strip().rstrip(".")
        return f"{hook} {target_tail}".strip()

    # 1. Filing-label format: starts with "Surah ..." or just the
    # surah name + numeric ref, possibly followed by a colon /
    # dash and a hook.
    label_pat = re.compile(
        r"^\s*(?:Surah\s+)?[A-Za-z'\-' ]+\s+\d+:\d+(?:-\d+)?",
        re.IGNORECASE,
    )
    label_match = label_pat.match(t)
    if label_match:
        rest = t[label_match.end():].lstrip(" :|—–-").strip().rstrip(".")
        if rest:
            return f"{rest} {target_tail}".strip()
        # No hook content beyond the label — best we can do is
        # reformat as "<surah name> <ref> (<ref_with_name>)" which
        # is still better than the bare label, but really the LLM
        # didn't follow the prompt; let the next render retry.
        return f"{ref_with_name} {target_tail}".strip()

    # 3. Hook-only output without any reference. Append the tail.
    # Strip any trailing punctuation so we don't get "Hook. (ref)".
    return f"{t.rstrip('.')} {target_tail}".strip()


def _generate_youtube_metadata(verse_data):
    """Generate YouTube title, description, and tags via Ollama, enriched with
    root-word insights. Returns (title, description, tags_list).

    Uses `ollama_metadata_model` if set (recommended: qwen3.5:397b-cloud for
    depth), otherwise falls back to the main `ollama_model`.
    """
    conn = get_db()
    try:
        # Load Ollama settings from preferences
        prefs = {}
        for row in conn.execute(
            "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
        ).fetchall():
            prefs[row["key"]] = row["value"]

        base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
        # Metadata model override takes precedence; falls back to the main model
        model = (prefs.get("ollama_metadata_model") or prefs.get("ollama_model") or "").strip()
        api_key = prefs.get("ollama_api_key") or ""

        if not model:
            raise RuntimeError(
                "Ollama model not configured — open Admin Settings → Ollama "
                "and fill in Base URL, Model, and (for cloud) API Key."
            )

        # Gather root word insights
        root_insights = _gather_verse_root_insights(conn, verse_data)
    finally:
        conn.close()

    # Build verse refs string — prefer compact range format for consecutive passages
    if not verse_data:
        ref_string = ""
        ref_with_name = ""
    else:
        chapters = {v["chapter"] for v in verse_data}
        verses_sorted = sorted(v["verse"] for v in verse_data)
        is_consecutive = (
            len(chapters) == 1
            and verses_sorted == list(range(verses_sorted[0], verses_sorted[-1] + 1))
        )
        if is_consecutive:
            ch = verse_data[0]["chapter"]
            if verses_sorted[0] == verses_sorted[-1]:
                ref_string = f"{ch}:{verses_sorted[0]}"
            else:
                ref_string = f"{ch}:{verses_sorted[0]}-{verses_sorted[-1]}"
        else:
            ref_string = ", ".join(f"{v['chapter']}:{v['verse']}" for v in verse_data)

    # Surah-name reference for the title's parenthetical (e.g.
    # "Al-Layl 92:12-19"). For non-contiguous picks across multiple
    # chapters we fall back to the bare numeric ref_string in
    # parentheses — uncommon enough that we don't need the surah
    # name there.
    if verse_data and len(chapters) == 1:
        ref_with_name = f"{_surah_name(verse_data[0]['chapter'])} {ref_string}"
    else:
        ref_with_name = ref_string

    # Build verse block for prompt — show each verse individually so the LLM sees the full text
    verse_lines = []
    for v in verse_data:
        verse_lines.append(f"- {v['chapter']}:{v['verse']}: \"{v['polished_text']}\"")
    verse_block = "\n".join(verse_lines)

    system_prompt = (
        "You write YouTube Shorts titles and descriptions for Qur'anic recitation "
        "passages. Your job is to lead with MEANING, not metadata.\n\n"
        "The default auto-generated title for these videos used to be a bare verse "
        "reference (\"Surah Al-Layl 92:12-19\"). A YouTube marketing review found that "
        "format was the single biggest reason the channel got views but no subscribers: "
        "a reference number is a filing label, not a hook. Scrolling viewers process "
        "the first three or four words of a title and decide whether to stop. \"Surah "
        "Al-Layl\" is a name. \"The two paths Allah lays before every soul\" is an idea. "
        "Ideas stop the scroll; names don't.\n\n"
        "The voice is reverent and curious, not sensational. No clickbait, no all caps, "
        "no emoji, no exclamation marks. Faithfulness to the passage matters more than "
        "cleverness."
    )

    prompt = (
        f"## Passage ({ref_with_name})\n\n"
        f"{verse_block}\n\n"
    )

    if root_insights:
        prompt += f"## Root-word connections between these verses\n{root_insights}\n\n"

    prompt += (
        "## Output format\n\n"
        "Return ONLY valid JSON, nothing else:\n"
        f'{{"title": "...", "description": "...", "tags": ["tag1", "tag2", ...]}}\n\n'
        "## Title rules — HOOK-FIRST FORMAT\n\n"
        f'Required template: "<plain-English hook> ({ref_with_name})"\n\n'
        "The hook comes first; the verse reference is a parenthetical at the END. \n"
        "DO NOT lead with \"Surah ...\". DO NOT lead with the numeric reference. \n"
        "DO NOT use \"X | Y\" pipe-separator format.\n\n"
        "Hook rules:\n"
        "- 4-9 words.\n"
        "- Plain English. Conveys the THEME, IMAGE, or EMOTIONAL CORE of the verses,\n"
        "  not a literal translation. If a translation phrase IS the most striking\n"
        "  line, you can use it directly (e.g. \"Allah has not abandoned you\" for\n"
        "  Ad-Duha 93:1-9).\n"
        "- No clickbait, no hyperbole, no all caps, no emoji, no exclamation marks.\n"
        "- No invented content. If the verses are an oath sequence (\"By the sky...\"),\n"
        "  the hook can be the oath. If they're a warning, the hook reflects that.\n"
        "- BANNED filler words in the hook: powerful, profound, beautiful, majestic,\n"
        "  timeless, transformative, divine promises, deep reflection.\n\n"
        f'Reference rules: the parenthetical must be exactly "({ref_with_name})". \n'
        "Use the short surah name without the \"Surah\" prefix (e.g. \"Al-Layl\", not\n"
        "\"Surah Al-Layl\") to keep it compact.\n\n"
        "Total title length: under 100 characters.\n\n"
        "## Title examples (study these — they show the target voice)\n\n"
        "BAD (filing-label format the channel is moving away from):\n"
        '  "Surah Al-Layl 92:12-19"\n'
        '  "Surah Al-Balad 90:10-16"\n'
        '  "Surah Ad-Duha 93:1-9"\n'
        "  → All three describe what the video IS without giving anyone a reason to\n"
        "    stop. They serve only viewers who already know the passage.\n\n"
        "GOOD (hook-first, reference parenthesised):\n"
        '  "The two paths Allah lays before every soul (Al-Layl 92:12-19)"\n'
        '  "The steep climb most people never take (Al-Balad 90:10-16)"\n'
        '  "Allah has not abandoned you (Ad-Duha 93:1-9)"\n'
        '  "The night worth more than a thousand months (Al-Qadr 97:1-5)"\n'
        '  "When the trumpet sounds, wealth won\'t help (Al-Muddaththir 74:8-13)"\n'
        '  "By time — humanity is at a loss (Al-Asr 103:1-3)"\n'
        '  "Did We not expand your chest for you? (Ash-Sharh 94:1-8)"\n'
        '  "The day a man flees from his own brother (\'Abasa 80:33-37)"\n'
        '  "When the sun is wrapped up in darkness (At-Takwir 81:1-9)"\n'
        '  "The day the earth will tell its story (Az-Zalzalah 99:1-8)"\n'
        '  "I swear by the Day of Resurrection (Al-Qiyamah 75:1-9)"\n'
        '  "By the night-visitor — the piercing star (At-Tariq 86:1-7)"\n'
        "  → Each leads with an image or theme that earns a beat of attention before\n"
        "    the viewer reads the reference. Reverent, specific, not sensational.\n\n"
        "## Description rules\n"
        "- 2-3 short sentences. Roughly 200-400 characters total.\n"
        "- Must deliver a SPECIFIC OBSERVATION the reader wouldn't get just from\n"
        "  reading the translation. Something that reframes how they read the\n"
        "  passage after seeing the video.\n"
        "- Name the concrete thing — a word choice, a grammatical move, a reversal\n"
        "  of expectation, a structural echo. Do NOT wave vaguely at 'powerful\n"
        "  oaths' or 'deep reflection.'\n"
        "- If a root-word connection genuinely illuminates the passage, name the\n"
        "  English meaning and what shifts when you notice it — don't just drop\n"
        "  the Arabic letters.\n"
        "- Sound like a thoughtful human with something to say, not a content bot.\n"
        "- BANNED opening phrases: 'This passage...', 'These verses...', 'In this...',\n"
        "  'A reminder that...', 'Reflect on...', 'Explore...'\n"
        "- BANNED filler words: powerful, profound, beautiful, majestic, timeless,\n"
        "  deep reflection, divine promises, transformative.\n"
        "- No hashtags. No calls to action. No 'watch this video'.\n\n"
        "## Description — BAD vs GOOD for 89:1-5 (Al-Fajr opening oaths)\n\n"
        'BAD: "Surah Al-Fajr opens with powerful oaths—by the dawn, ten nights,\n'
        'and the night as it passes—connecting to the Arabic root ل ي ل meaning\n'
        '\'night\' to emphasize that these Divine promises deserve deep reflection."\n'
        '  — Generic ("powerful oaths", "deep reflection"), restates what the\n'
        '    verses say, the root mention is decorative, tells me nothing new.\n\n'
        'GOOD: "God swears five times in a row before making His point — and then\n'
        'the point is delivered as a question, not a statement. Verse 6 opens\n'
        'with \'Have you not seen...\', forcing the listener to arrive at the\n'
        'conclusion themselves. The oaths are a setup, not the argument."\n'
        '  — Names a specific structural move, notices what would surprise a\n'
        '    careful reader, respects the reader\'s intelligence.\n\n'
        "## Tags rules\n"
        "- 8-12 YouTube tags as an array of short strings.\n"
        f'- Mix: generic ("Quran", "Islam"), passage-specific ("{ref_string}"),\n'
        "  and thematic tags drawn from the actual content (e.g. 'patience',\n"
        "  'resurrection', 'gratitude' — pick what fits THIS passage).\n"
        "- Each 1-3 words, lowercase unless a proper noun.\n"
        "- Must include 'YouTube Shorts' and 'Quran Shorts'.\n"
        "- No hashtags, no special characters.\n"
    )

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Qwen3.5 and similar thinking-capable models accept a "think" flag to
    # enable chain-of-thought reasoning before answering. Crucial for catching
    # the subtle structural/grammatical hooks that separate insightful
    # descriptions from generic ones. Non-thinking models ignore the flag.
    resp = requests.post(
        f"{base_url}/api/chat",
        headers=headers,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.7},
            "think": True,
        },
        timeout=300,  # Thinking models run longer; metadata isn't a bottleneck
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama API error: {resp.status_code}")

    content = resp.json().get("message", {}).get("content", "")

    # Strip markdown code blocks and think blocks
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
    content = re.sub(r"\n?```\s*$", "", content.strip())

    # Parse JSON
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise RuntimeError("Could not parse metadata JSON from Ollama response")

    try:
        meta = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from Ollama: {e}")

    title = (meta.get("title") or "").strip()
    description = (meta.get("description") or "").strip()

    # Title normalisation — defence-in-depth against the LLM
    # falling back to old habits despite the prompt. Three failure
    # modes seen in practice:
    #   1. Leads with "Surah X 92:12-19" instead of a hook.
    #   2. Uses old "92:12-19 | hook" pipe format.
    #   3. Drops the parenthesised reference entirely and just
    #      writes a hook.
    # We rebuild the canonical "<hook> (<ref_with_name>)" shape
    # whenever any of these are detected.
    if title and ref_with_name:
        title = _normalize_recitation_title(title, ref_string, ref_with_name)

    # Append the standard al-nuqta.com links block — homepage + one
    # link per unique verse in the passage. Mirrors the educational
    # pipeline's footer so viewers always have a click path back to
    # the verse on the site, and the LLM doesn't have to be coaxed
    # into producing reliable URLs.
    description = _append_alnuqta_links_to_description(description, verse_data)

    # Tags: accept list; filter to non-empty strings; cap at 15 and 500 chars each
    raw_tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    tags: list[str] = []
    for t in raw_tags:
        if not isinstance(t, str):
            continue
        cleaned = t.strip().lstrip("#")[:500]
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
        if len(tags) >= 15:
            break

    return (title, description, tags)


def _format_verse_runs(verses_in_chapter: list[int]) -> list[str]:
    """Collapse sorted, unique verses within one chapter into ref
    fragments: consecutive runs become "3-5", singletons stay "3".
    Used to build cleaner range URLs like al-nuqta.com/2:3-5 instead
    of three separate per-verse links."""
    if not verses_in_chapter:
        return []
    sorted_v = sorted(set(verses_in_chapter))
    runs: list[str] = []
    start = prev = sorted_v[0]
    for v in sorted_v[1:]:
        if v == prev + 1:
            prev = v
            continue
        runs.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = v
    runs.append(f"{start}" if start == prev else f"{start}-{prev}")
    return runs


def _append_alnuqta_links_to_description(
    description: str,
    verse_data: list,
) -> str:
    """Append a programmatic links block to the recitation pipeline's
    YouTube description.

    Adds:
      - One link per consecutive run of verses (e.g. 2:3-5 collapses
        into a single al-nuqta.com/2:3-5 link; non-consecutive picks
        produce one link per run).
      - A homepage link.
      - The standard al-nuqta footer (mirrors the educational pipeline).

    Uses the site's shorthand URL (al-nuqta.com/<ref>) which redirects
    to /read/<ref> — single verses and ranges both work.

    The LLM-generated description stays at the top — that's what stops
    the scroll. Links live below as a footer block. If verse_data is
    empty the description is returned unchanged.
    """
    if not verse_data:
        return description

    # Group by chapter, preserving the order chapters first appear in
    # the source list. Within each chapter, _format_verse_runs handles
    # the consecutive-vs-disjoint logic.
    by_chapter: dict[int, list[int]] = {}
    chapter_order: list[int] = []
    for v in verse_data:
        try:
            c = int(v.get("chapter"))
            a = int(v.get("verse"))
        except (TypeError, ValueError, AttributeError):
            continue
        if c not in by_chapter:
            by_chapter[c] = []
            chapter_order.append(c)
        if a not in by_chapter[c]:
            by_chapter[c].append(a)

    if not by_chapter:
        return description

    parts: list[str] = []
    if description:
        parts.append(description.rstrip())
        parts.append("")

    parts.append("📖 Read on al-nuqta.com:")
    for c in chapter_order:
        for run in _format_verse_runs(by_chapter[c]):
            ref = f"{c}:{run}"
            parts.append(f"• Quran {ref} — https://al-nuqta.com/{ref}")
    parts.append("")
    parts.append(
        "Explore the Quran root-by-root, with morphology, etymology, "
        "and Semitic cognates behind every word: https://al-nuqta.com"
    )
    parts.append("")
    parts.append(
        "Brought to you by al-nuqta.com — A Root Based Translation of the Quran."
    )

    return "\n".join(parts)


# --------------------------------------------------------------------------
#  Educational pipeline: YouTube metadata
# --------------------------------------------------------------------------

def _fetch_word_label(conn, chapter: int, verse: int, word_pos: int) -> str:
    """Best label for a word in the description's link list. Tries the
    per-word English gloss first (preferred_translation → meaning_short
    → word_glosses.translation_en); falls back to the surface Arabic
    form. Used to label entries like
    "<label>: https://al-nuqta.com/word/X:Y/Z"."""
    try:
        wm = conn.execute(
            "SELECT COALESCE(preferred_translation, meaning_short) AS t "
            "FROM ai_word_meanings WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (chapter, verse, word_pos),
        ).fetchone()
        if wm and wm["t"]:
            return wm["t"].strip()
    except Exception:
        pass
    try:
        wg = conn.execute(
            "SELECT translation_en FROM word_glosses "
            "WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (chapter, verse, word_pos),
        ).fetchone()
        if wg and wg["translation_en"]:
            return wg["translation_en"].strip()
    except Exception:
        pass
    # Fall back to the Arabic word at that position
    try:
        v = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?",
            (chapter, verse),
        ).fetchone()
        if v and v["text_uthmani"]:
            words = v["text_uthmani"].split()
            if 1 <= word_pos <= len(words):
                return words[word_pos - 1]
    except Exception:
        pass
    return f"{chapter}:{verse}"


def _fetch_word_context_blurb(conn, chapter: int, verse: int, word_pos: int) -> str:
    """Pull the per-word "context-derived meaning" — what the word
    means in *this* verse's context, plus how it ranges across the
    Quran. Used as the body paragraph in the description's "various
    contexts" section.

    Order of preference:
      1. ai_word_meanings.cross_ref_notes (cross-Quran usage commentary)
      2. ai_word_meanings.meaning_detailed (longer per-word semantics)
    Both can be multi-paragraph; we trim to ~500 chars for the
    description.
    """
    try:
        row = conn.execute(
            "SELECT cross_ref_notes, meaning_detailed FROM ai_word_meanings "
            "WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (chapter, verse, word_pos),
        ).fetchone()
    except Exception:
        return ""
    if not row:
        return ""
    text = (row["cross_ref_notes"] or row["meaning_detailed"] or "").strip()
    if not text:
        return ""
    # Trim to a reasonable description chunk; YouTube descriptions
    # have a 5000-char limit total, but readability wants tight prose.
    if len(text) > 600:
        # Cut at the nearest paragraph or sentence boundary.
        snip = text[:600]
        boundary = max(snip.rfind("\n\n"), snip.rfind(". "))
        if boundary > 200:
            text = snip[:boundary + 1]
        else:
            text = snip + "…"
    return text


def _ollama_complete(prompt: str, system_prompt: str = "") -> dict:
    """Single Ollama call returning parsed JSON. Reuses the same
    preferences (base_url, model, api_key) the recitation pipeline
    uses. Raises RuntimeError on transport / parse failure."""
    conn = get_db()
    try:
        prefs: dict[str, str] = {}
        for r in conn.execute(
            "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
        ).fetchall():
            prefs[r["key"]] = r["value"]
    finally:
        conn.close()
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (prefs.get("ollama_metadata_model") or prefs.get("ollama_model") or "").strip()
    api_key = prefs.get("ollama_api_key") or ""
    if not model:
        raise RuntimeError(
            "Ollama model not configured (Admin → Settings → Ollama)"
        )
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = requests.post(
        f"{base_url}/api/chat",
        headers=headers,
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7},
            "think": True,
        },
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama API error: {resp.status_code}")
    content = resp.json().get("message", {}).get("content", "")
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
    content = re.sub(r"\n?```\s*$", "", content.strip())
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise RuntimeError("Ollama response did not contain JSON")
    try:
        return json.loads(m.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from Ollama: {e}")


def _generate_grammar_insights_metadata(
    conn, row: dict, payload: dict, script: dict,
) -> tuple[str, str, list[str]]:
    """Title/description/tags for a grammar_insights video.

    The original word-origins metadata generator was being applied to
    grammar_insights rows too, which produced wrong titles ("Why the
    Quran Uses Rahman Not Merciful" on a 84:8 grammar video) because
    the Ollama prompt's lemma examples leaked through when the actual
    lemma/root fields were empty. Same path also pulled a word-context
    blurb for word_pos=1, which for 84:8 was سَوْفَ — completely
    unrelated to the grammatical move the script discussed.

    Grammar-specific approach:
      - Title is generated from the SCRIPT's hook + insight + close
        plus the V7 category. No lemma fallbacks; Ollama is told the
        title must reference the grammatical move and the verse, not
        invent a "word".
      - Description is programmatic: hook → close → verse link →
        cross-reference example links → brand line. No "word context"
        blurb; that field is irrelevant when there's no anchor word.
    """
    chapter = int(row["chapter"])
    verse = int(row["verse"])
    insight = payload.get("insight") or {}
    category = (insight.get("category") or "").strip() or "other_grammar"
    title_text = (insight.get("title") or "").strip()

    # ---- Title via Ollama ----
    sys_p = (
        "You name short videos about ONE grammatical choice the Quran "
        "makes in a specific verse. Titles are catchy, verse-anchored, "
        "and avoid 'powerful', 'profound', 'beautiful', 'fascinating'."
    )
    user_p = (
        f"## Verse\nQuran {chapter}:{verse}\n\n"
        f"## Grammatical category\n{category}\n"
        f"## Insight title (from analyser)\n{title_text}\n\n"
        "## Script\n"
        f"Hook: {(script.get('hook') or '').strip()}\n"
        f"Insight: {(script.get('insight') or '').strip()}\n"
        f"Close: {(script.get('close') or '').strip()}\n\n"
        "## Output\n"
        'Return ONLY JSON: {"title": "...", "tags": ["tag1", ...]}\n\n'
        "Title rules:\n"
        f"- MUST reference Quran {chapter}:{verse} in the title (e.g. "
        f"'Quran {chapter}:{verse}', 'in {chapter}:{verse}', "
        f"'Surah ... {chapter}:{verse}').\n"
        "- Capture the GRAMMATICAL move (tense / pronoun / fronting / "
        "  exception / conditional / cognate-accusative / etc.), NOT "
        "  the topic of the verse.\n"
        '- Patterns that work: "When the Quran ___ in [X:Y]", '
        '"Why ___ in Quran [X:Y]", "The ___ Move in Quran [X:Y]", '
        '"[Grammatical thing] in Quran [X:Y]".\n'
        "- Under 80 characters. No emojis. No quotation marks.\n"
        "- DO NOT invent a single 'word' the video is about — this is "
        "  a video about a grammatical choice in a verse, not a "
        "  word-of-the-day video. Names of words ('Rahman', 'Salam', "
        "  etc.) DO NOT belong in this title unless the script "
        "  explicitly centres on that word.\n"
        "- DO NOT use the word 'Islamic' anywhere in the title. The "
        "  Quran uses 'Islam' (the noun) but never 'Islamic' as an "
        "  adjective. Say 'Quran' or 'Quranic' instead.\n"
        "\nTags rules:\n"
        "- 8-12 short tags, lowercase except proper nouns.\n"
        "- Mix: generic ('quran', 'quran arabic', 'quran grammar'), "
        "  category-specific ('quranic style', 'arabic grammar', "
        "  'quran linguistics'), verse-specific (the surah name).\n"
        "- Always include 'Quran' and 'Quran Shorts'.\n"
        "- DO NOT include any tag containing the word 'Islamic' "
        "  (e.g. 'islamic videos'). Use 'quran' variants instead."
    )
    try:
        meta = _ollama_complete(user_p, system_prompt=sys_p)
    except Exception as e:
        print(f"[grammar metadata] Ollama failed: {e}")
        meta = {}

    title = (meta.get("title") or "").strip()[:100]
    if not title:
        title = f"Grammar in Quran {chapter}:{verse}"[:100]

    raw_tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    tags: list[str] = []
    for t in raw_tags:
        if not isinstance(t, str):
            continue
        cleaned = t.strip().lstrip("#")[:100]
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
        if len(tags) >= 12:
            break
    if not tags:
        tags = list(_DEFAULT_YT_TAGS)

    # ---- Description (programmatic) ----
    parts: list[str] = []

    hook = (script.get("hook") or "").strip()
    if hook:
        parts.append(hook)
        parts.append("")

    close = (script.get("close") or "").strip()
    if close:
        parts.append(close)
        parts.append("")

    parts.append(f"Read this verse: https://al-nuqta.com/verse/{chapter}:{verse}")
    parts.append("")

    # Cross-reference examples — link to /verse/X:Y for each.
    ax = script.get("additional_examples") or []
    if isinstance(ax, list) and ax:
        parts.append("Same pattern elsewhere in the Quran:")
        for ex in ax[:2]:
            if not isinstance(ex, dict):
                continue
            try:
                c = int(ex.get("chapter"))
                v = int(ex.get("verse"))
            except (TypeError, ValueError):
                continue
            parts.append(f"- Quran {c}:{v} — https://al-nuqta.com/verse/{c}:{v}")
        parts.append("")

    parts.append("Brought to you by al-nuqta.com — A Root Based Translation of the Quran.")
    parts.append("")
    parts.append("#Quran #QuranArabic #QuranGrammar")

    description = "\n".join(parts)[:5000]
    # Quran-only vocabulary guard — strip any "Islamic" leakage that
    # might come back from Ollama in title/tags.
    title = _ISLAMIC_RE.sub("", title).strip() or f"Grammar in Quran {chapter}:{verse}"
    description = _strip_islamic_terms(description)
    tags = _filter_islamic_tags(tags) or list(_DEFAULT_YT_TAGS)
    return title, description, tags


def _generate_educational_metadata(conn, row: dict, payload: dict, script: dict) -> tuple[str, str, list[str]]:
    """Build YouTube title/description/tags for an educational video.

    Branches on row['type']:
      - grammar_insights → script-driven title (no lemma fallback)
        + programmatic description that links the verse + examples.
      - everything else (word_origins, translation_hides) → original
        word-anchored generator below.

    - Title + tags: Ollama call (catchy title from the script + word
      context). The title is constrained to ≤80 chars, no emojis.
    - Description: structured, programmatically built. Carries the
      hook, a link to the root, a "various contexts" paragraph drawn
      from the word's cross_ref_notes / meaning_detailed, and a list
      of word-page links for the source verse + the LLM-selected
      verses.
    """
    # Grammar Insights videos use a different metadata path — the
    # word-anchored Ollama prompt below produces wrong titles when
    # the row has no lemma/root (the Ollama lemma examples leak in,
    # producing artefacts like "Why the Quran Uses Rahman Not
    # Merciful" on a 84:8 grammar video about cognate-accusative).
    if (row.get("type") or "").lower() == "grammar_insights":
        return _generate_grammar_insights_metadata(conn, row, payload, script)

    word = payload.get("word") or {}
    root = payload.get("root") or {}
    root_bw = root.get("buckwalter") or ""
    root_ar = root.get("arabic") or ""
    chapter = row["chapter"]
    verse = row["verse"]
    word_pos = row.get("anchor_word_pos") or 1

    # ----------------------------------------------------------------
    # Step 1 — Ollama for catchy title + tags
    # ----------------------------------------------------------------
    sys_p = (
        "You name short educational videos about a single Arabic word "
        "from the Quran. Your titles are catchy, specific, and avoid "
        "religious-AI cliches like 'powerful', 'profound', 'beautiful'."
    )
    user_p = (
        "## Word\n"
        f"Arabic: {word.get('form_arabic','')}\n"
        f"Buckwalter: {word.get('form_buckwalter','')}\n"
        f"Lemma: {word.get('lemma_arabic','')}\n"
        f"Root: {root_ar} ({root_bw})\n\n"
        "## Script\n"
        f"Hook: {script.get('hook','')}\n"
        f"Root tidbit: {script.get('tidbit_about_root','')}\n"
        f"Quran-usage tidbit: {script.get('tidbit_about_quran_usage','')}\n"
        f"Semitic tidbit: {script.get('tidbit_about_semitic','')}\n\n"
        "## Output\n"
        'Return ONLY JSON: {"title": "...", "tags": ["tag1","tag2",...]}\n\n'
        "Title rules:\n"
        '- Pattern: "The Word [English transliteration of the lemma] in the Quran" '
        'OR a catchier variation (e.g. "What [Word] really means", '
        '"[Word]: older than the pyramids", "Why the Quran says [Word]").\n'
        "- Under 80 characters. No emojis. No quotation marks. No colons in "
        "  the title unless they're part of the framing.\n"
        "- Use a clean English transliteration of the lemma — 'Rahman', "
        "  'Rahim', 'Salam', 'Yawm', 'Ayn'. NOT IPA marks or hyphens.\n"
        "- DO NOT use the word 'Islamic' anywhere in the title. The "
        "  Quran uses 'Islam' (the noun) but never 'Islamic' as an "
        "  adjective. Say 'Quran' or 'Quranic' instead.\n\n"
        "Tags rules:\n"
        "- 8-12 short tags. Lowercase except proper nouns.\n"
        "- Mix: generic ('quran', 'islam', 'quran arabic'), word-specific "
        "  ('rahman', 'mercy in the quran'), and topical ('semitic languages', "
        "  'cognates', 'arabic etymology').\n"
        "- Always include 'Quran' and 'Quran Shorts'.\n"
        "- DO NOT include any tag containing the word 'Islamic' "
        "  (e.g. 'islamic videos', 'islamic content'). Use 'quran' "
        "  variants instead.\n"
    )
    try:
        meta = _ollama_complete(user_p, system_prompt=sys_p)
    except Exception as e:
        # Fall back gracefully so render isn't held hostage to Ollama.
        print(f"[educational metadata] Ollama failed: {e}")
        meta = {}

    title = (meta.get("title") or "").strip()[:100]
    if not title:
        # Sensible fallback constructed from the lemma if Ollama is down.
        lemma_ar = (word.get("lemma_arabic") or word.get("form_arabic") or "").strip()
        title = (
            f"The Quran on {lemma_ar}"[:100]
            if lemma_ar else _DEFAULT_YT_TITLE
        )

    raw_tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    tags: list[str] = []
    for t in raw_tags:
        if not isinstance(t, str):
            continue
        cleaned = t.strip().lstrip("#")[:100]
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
        if len(tags) >= 12:
            break
    if not tags:
        tags = list(_DEFAULT_YT_TAGS)

    # ----------------------------------------------------------------
    # Step 2 — Programmatic description
    # ----------------------------------------------------------------
    parts: list[str] = []

    # Lead with the script's hook (it's already attention-grabbing).
    hook = (script.get("hook") or "").strip()
    if hook:
        parts.append(hook)
        parts.append("")

    # Root link
    if root_bw:
        parts.append(f"See more detail on this root: https://al-nuqta.com/root/{root_bw}")
        parts.append("")

    # "Various contexts" paragraph + word links
    parts.append("See how the Quran uses this word in various contexts:")
    blurb = _fetch_word_context_blurb(conn, chapter, verse, word_pos)
    if blurb:
        parts.append("")
        parts.append(blurb)
    parts.append("")

    # Word links: source verse + the two LLM-selected refs
    seen: set[tuple[int, int, int]] = set()

    def _append_word_link(c: int, v: int, p: int) -> None:
        if (c, v, p) in seen:
            return
        seen.add((c, v, p))
        label = _fetch_word_label(conn, c, v, p)
        parts.append(f"{label}: https://al-nuqta.com/word/{c}:{v}/{p}")

    _append_word_link(chapter, verse, word_pos)
    # Selected refs from the script — pull word_pos from the payload's
    # other_verses pool (which is what enrich_payload populates).
    other_pool: dict[tuple[int, int], int] = {}
    for ov in (payload.get("other_verses") or []):
        try:
            other_pool[(int(ov["chapter"]), int(ov["verse"]))] = int(ov.get("word_pos") or 1)
        except (KeyError, TypeError, ValueError):
            continue
    for ref in (script.get("selected_verse_refs") or [])[:2]:
        try:
            c = int(ref.get("chapter")); v = int(ref.get("verse"))
        except (TypeError, ValueError):
            continue
        wp = other_pool.get((c, v))
        if wp:
            _append_word_link(c, v, wp)

    parts.append("")
    parts.append("Brought to you by al-nuqta.com — A Root Based Translation of the Quran.")
    parts.append("")
    parts.append("#Quran #QuranTranslation #QuranArabic")

    description = "\n".join(parts)[:5000]
    # Final guard: drop any "Islamic" leakage from Ollama-generated
    # title/tags or anywhere else upstream (the Quran uses "Islam",
    # never "Islamic" as an adjective).
    title = _ISLAMIC_RE.sub("", title).strip() or _DEFAULT_YT_TITLE
    description = _strip_islamic_terms(description)
    tags = _filter_islamic_tags(tags) or list(_DEFAULT_YT_TAGS)
    return title, description, tags


def _pipeline_generate_task(video_id):
    """Background task: AI-select verses, polish, TTS, render video."""

    try:
        # ---- 1. Load pipeline config ----
        conn = get_db()
        try:
            vid_row = conn.execute("SELECT * FROM admin_pipeline_videos WHERE id = ?", (video_id,)).fetchone()
            if not vid_row:
                return
            pipeline = conn.execute("SELECT * FROM admin_pipelines WHERE id = ?", (vid_row["pipeline_id"],)).fetchone()
            if not pipeline:
                _update_pipeline_video_status(video_id, "failed", error="Pipeline not found")
                return

            # Language determines audio source (ElevenLabs TTS vs reciter audio)
            language = (pipeline["language"] or "english").lower()
            is_arabic = language == "arabic"
            try:
                reciter_id_for_pipeline = pipeline["reciter_id"]
            except (IndexError, KeyError):
                reciter_id_for_pipeline = None
            if is_arabic and not reciter_id_for_pipeline:
                _update_pipeline_video_status(video_id, "failed", error="Arabic pipeline has no reciter configured")
                return

            # Gather used passage ranges from the last 30 days of completed
            # runs PLUS any runs the interestingness judge skipped. Anything
            # older than 30 days (or in other failure modes) is eligible
            # to be picked again. We include 'rejected_uninteresting' so
            # Claude won't keep proposing the same boring passage that
            # the judge just turned down — without this, every scheduled
            # run would burn a Claude API call on the same reject.
            used_rows = conn.execute(
                "SELECT verse_data FROM admin_pipeline_videos "
                "WHERE pipeline_id = ? "
                "  AND status IN ('complete', 'rejected_uninteresting') "
                "  AND created_at >= datetime('now', '-30 days')",
                (pipeline["id"],),
            ).fetchall()
            used_ranges = []
            for ur in used_rows:
                try:
                    vs_list = json.loads(ur["verse_data"] or "[]")
                except (json.JSONDecodeError, TypeError):
                    continue
                if not vs_list:
                    continue
                # Group verses by chapter to handle legacy multi-surah videos
                by_ch = {}
                for v in vs_list:
                    ch = v.get("chapter")
                    vs = v.get("verse")
                    if ch and vs:
                        by_ch.setdefault(ch, []).append(vs)
                for ch, verses in by_ch.items():
                    vs_min, vs_max = min(verses), max(verses)
                    if vs_min == vs_max:
                        used_ranges.append(f"{ch}:{vs_min}")
                    else:
                        used_ranges.append(f"{ch}:{vs_min}-{vs_max}")

            # Resource: either the pipeline's fixed choice, or a random one
            # per run (if random_resource flag is set).
            try:
                use_random_resource = bool(pipeline["random_resource"])
            except (IndexError, KeyError):
                use_random_resource = False
            if use_random_resource:
                resource = conn.execute(
                    "SELECT * FROM admin_resources ORDER BY RANDOM() LIMIT 1"
                ).fetchone()
            else:
                resource = conn.execute(
                    "SELECT * FROM admin_resources WHERE id = ?", (pipeline["resource_id"],)
                ).fetchone()
            music_filename = None
            if pipeline["music_id"]:
                music_row = conn.execute("SELECT filename FROM admin_music WHERE id = ?", (pipeline["music_id"],)).fetchone()
                if music_row:
                    music_filename = music_row["filename"]
        finally:
            conn.close()

        if not resource:
            _update_pipeline_video_status(video_id, "failed", error="Background video not found")
            return

        bg_path = os.path.join(_RESOURCES_DIR, resource["filename"])
        if not os.path.isfile(bg_path):
            _update_pipeline_video_status(video_id, "failed", error="Background video file missing")
            return

        music_path = os.path.join(_MUSIC_DIR, music_filename) if music_filename else None
        if music_path and not os.path.isfile(music_path):
            music_path = None

        # ---- 2. Select verses (Claude, unless manually overridden) ----
        manual_ch = vid_row["manual_chapter"] if "manual_chapter" in vid_row.keys() else None
        manual_start = vid_row["manual_ayah_start"] if "manual_ayah_start" in vid_row.keys() else None
        manual_end = vid_row["manual_ayah_end"] if "manual_ayah_end" in vid_row.keys() else None
        is_manual_selection = manual_ch is not None and manual_start is not None and manual_end is not None

        # Claude API key only needed for auto-select / polish steps
        api_key = _get_claude_api_key()

        if is_manual_selection:
            chapter = int(manual_ch)
            ayah_start = int(manual_start)
            ayah_end = int(manual_end)
            _update_pipeline_video_status(
                video_id, "selecting_verses",
                f"Using manual selection {chapter}:{ayah_start}-{ayah_end}",
            )
        else:
            _update_pipeline_video_status(video_id, "selecting_verses", "AI is selecting verses...")

            if not api_key:
                _update_pipeline_video_status(video_id, "failed", error="Claude API key not configured")
                return

        if not is_manual_selection:
            used_list = ", ".join(sorted(set(used_ranges))) if used_ranges else "None yet"

            if is_arabic:
                select_prompt = (
                    "You are selecting a Quranic passage for an ARABIC-RECITATION YouTube Short. The audio\n"
                    "will be a reciter chanting these verses in Arabic; on-screen the viewer sees the\n"
                    "English translation. Pick ONE continuous passage of 2 to 6 consecutive verses from\n"
                    "a SINGLE surah.\n\n"
                    "HIGHEST PRIORITY — the passage must be BOTH:\n"
                    "  (a) Emotionally resonant: when recited, the listener feels it — awe, grief, wonder,\n"
                    "      dread, hope. Not neutral narration or dry legal text.\n"
                    "  (b) Meaningful: carries a self-contained truth, image, or argument that lands even\n"
                    "      without extensive commentary.\n\n"
                    "════════════════════════════════════════════════════════════════════\n"
                    "CRITICAL — COMPLETENESS OF THOUGHT\n"
                    "════════════════════════════════════════════════════════════════════\n"
                    "The #1 failure mode of this selector is ending on a verse that LEAVES\n"
                    "A THOUGHT HANGING. Before you finalize ayah_end, read your last verse\n"
                    "and ask:\n"
                    "\n"
                    "    \"Does this verse complete the thought, or does it set something\n"
                    "     up that the NEXT verse would resolve?\"\n"
                    "\n"
                    "If the next verse is the payoff, EITHER include it (prefer this when\n"
                    "budget allows) OR stop one verse earlier so the current ending is\n"
                    "itself self-contained. Never ship a passage that ends mid-setup.\n"
                    "\n"
                    "Concrete examples of BAD endings that leave a thought open:\n"
                    "- Ends on a contrast \"as for those whose scales are light...\" with no\n"
                    "  consequence (Al-Qari'ah 101:8 needs 101:9 to land)\n"
                    "- Ends on a conditional \"if/when X...\" with no consequent\n"
                    "- Ends on a rhetorical question that the next verse answers\n"
                    "- Ends on a list that trails off mid-item\n"
                    "- Ends on a premise whose reversal or resolution is in the next ayah\n"
                    "\n"
                    "Strong endings stand on their own: a declaration, a verdict, a\n"
                    "complete scene, a closed question-and-answer, or a clean couplet.\n"
                    "\n"
                    "Good trimming examples for the 101:1-? case (choose based on length):\n"
                    "  - 101:1-7  ends on \"he will be in a pleasant life\" — full statement\n"
                    "  - 101:1-9  resolves BOTH sides of the contrast — best if budget fits\n"
                    "  - 101:1-11 answers \"what is Hawiyah?\" — ideal completion\n"
                    "  - 101:1-8  BAD: leaves the light-scales outcome hanging\n"
                    "════════════════════════════════════════════════════════════════════\n\n"
                    "HARD CONSTRAINT — the TOTAL RECITED LENGTH MUST FIT UNDER 55 SECONDS to avoid\n"
                    "copyright issues. Arabic recitation is slow and deliberate. Budget roughly:\n"
                    "  - Short verse (<15 Arabic words): ~5-10 seconds recited\n"
                    "  - Medium verse (15-30 words): ~10-20 seconds recited\n"
                    "  - Long verse (>30 words): often 25+ seconds — usually too long\n"
                    "STRONGLY prefer SHORT verses. Short surahs (Juz Amma: 78-114, and parts of 55, 56, 67)\n"
                    "usually work best. If you pick from a long surah, confirm each verse is short.\n\n"
                    "REJECT passages that are:\n"
                    "- Long verses or long passages that risk exceeding 55 seconds\n"
                    "- Purely legal/procedural, genealogical, or merely descriptive\n"
                    "- Ayat al-Kursi (2:255), last 3 surahs, Al-Fatiha — too overused\n"
                    "- One famous line padded with filler verses\n\n"
                    "Good targets include (but aren't limited to):\n"
                    "- The openings of Juz Amma (e.g. passages from An-Naba, An-Nazi'at, 'Abasa, At-Takwir,\n"
                    "  Al-Infitar, Al-Inshiqaq, Al-Ghashiyah, Al-Fajr, Al-Balad, Al-Layl, Al-Qari'ah)\n"
                    "- Rhythmic oath passages, vivid eschatological imagery, direct address\n"
                    "- Passages about human fragility, reckoning, wonder at creation\n\n"
                    "Other constraints:\n"
                    "- Must form a cohesive unit — a complete image, argument, or narrative beat\n"
                    "- Verses should build on each other rhythmically\n\n"
                    f"Previously used passages (DO NOT repeat or overlap with these): {used_list}\n\n"
                    "Return ONLY a valid JSON object, nothing else:\n"
                    '{"chapter": <int>, "ayah_start": <int>, "ayah_end": <int>}'
                )
            else:
                select_prompt = (
                    "You are selecting a Quranic passage for a YouTube Shorts video (under 60 seconds of spoken content).\n"
                    "Pick ONE continuous passage of 3 to 8 consecutive verses from a SINGLE surah.\n\n"
                    "HIGHEST PRIORITY — the passage must be BOTH:\n"
                    "  (a) Intellectually thought-provoking: contains paradox, a challenging question, a reversal of\n"
                    "      expectation, or a profound argument that makes the listener reconsider something\n"
                    "  (b) Emotionally striking: provokes awe, dread, grief, wonder, shame, or shock — not\n"
                    "      merely peaceful or comforting\n\n"
                    "CRITICAL — DO NOT END MID-THOUGHT. Before finalizing ayah_end, read your last verse and\n"
                    "ask: does this complete the thought, or does the NEXT verse contain the payoff? If the\n"
                    "next verse is the resolution, EITHER include it (preferred) OR stop one verse earlier\n"
                    "so the current ending is itself self-contained. Bad endings: trailing contrasts without\n"
                    "the counter side, conditionals without their consequence, rhetorical questions whose\n"
                    "answer is the next verse, setups whose reversal comes next. Strong endings: declarations,\n"
                    "verdicts, complete scenes, closed Q&A couplets.\n\n"
                    "REJECT passages that are:\n"
                    "- Merely descriptive of Paradise or rewards without tension\n"
                    "- Calmly reassuring (e.g. 89:27-30 — too gentle, no bite)\n"
                    "- Purely legal/procedural without emotional force\n"
                    "- One famous line padded with filler verses\n\n"
                    "Good targets include (but aren't limited to):\n"
                    "- Human ingratitude, the absurdity of idolatry, the shock of resurrection\n"
                    "- The silence before Judgment, the weight of an atom of good or evil\n"
                    "- The blindness of the arrogant, the fragility of life, the deception of wealth\n"
                    "- Direct challenges to the listener ('Have you seen...', 'What will make you know...')\n\n"
                    "Other constraints:\n"
                    "- Must form a cohesive unit — a complete thought, argument, or narrative arc\n"
                    "- Will be spoken in English only — Arabic poetic qualities don't matter\n"
                    "- Avoid the most overused passages (Ayat al-Kursi, last 3 surahs, Al-Fatiha)\n"
                    "- Prefer shorter verses — total spoken length roughly 30-45 seconds\n"
                    "- Verses should build on each other, not just pad one famous line\n\n"
                    f"Previously used passages (DO NOT repeat or overlap with these): {used_list}\n\n"
                    "Return ONLY a valid JSON object, nothing else:\n"
                    '{"chapter": <int>, "ayah_start": <int>, "ayah_end": <int>}'
                )

            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": select_prompt}],
                },
                timeout=30,
            )

            if resp.status_code != 200:
                _update_pipeline_video_status(video_id, "failed", error=f"Claude API error: {resp.status_code}")
                return

            resp_text = resp.json()["content"][0]["text"].strip()
            match = re.search(r"\{.*\}", resp_text, re.DOTALL)
            if not match:
                _update_pipeline_video_status(video_id, "failed", error="Could not parse passage selection from AI")
                return

            try:
                selection = json.loads(match.group())
            except json.JSONDecodeError as je:
                _update_pipeline_video_status(video_id, "failed", error=f"AI returned invalid JSON for passage selection: {je}")
                return

            try:
                chapter = int(selection["chapter"])
                ayah_start = int(selection["ayah_start"])
                ayah_end = int(selection["ayah_end"])
            except (KeyError, TypeError, ValueError):
                _update_pipeline_video_status(video_id, "failed", error="Missing chapter/ayah_start/ayah_end in AI response")
                return

            if ayah_end < ayah_start:
                ayah_start, ayah_end = ayah_end, ayah_start
            # Safety cap: keep short under copyright-safe time budget.
            # Arabic recitation is slower than English TTS, so Arabic cap is tighter.
            max_verses = 6 if is_arabic else 8
            if ayah_end - ayah_start + 1 > max_verses:
                ayah_end = ayah_start + max_verses - 1

        # ---- 2.5. Interestingness gate ----
        # For AI-selected passages, run an Ollama-based judge on the
        # passage BEFORE we spend money on Claude polish + ElevenLabs
        # TTS + render. Operator feedback: a himar-etymology word
        # origins video "will lead to losing subscribers" — bad
        # uploads actively hurt the channel. Recitations have the
        # same risk: a transitional / legalistic / repetitive
        # passage published as a standalone short reads as boring
        # and trains the YouTube algorithm against us.
        #
        # On rejection we mark the row 'rejected_uninteresting' and
        # return. The pipeline's used_rows query has been widened to
        # include this status, so the NEXT scheduled run won't pick
        # the same passage. Manual selections skip the gate (the
        # operator opted in).
        if not is_manual_selection and _INTEREST_OK:
            try:
                _update_pipeline_video_status(
                    video_id, "judging",
                    f"Checking if {chapter}:{ayah_start}-{ayah_end} is interesting enough...",
                )
                _judge_conn = get_db()
                try:
                    verdict = _interest.judge_passage(
                        _judge_conn, chapter, ayah_start, ayah_end,
                    )
                finally:
                    _judge_conn.close()
                # Persist the verdict regardless of pass/fail so the
                # admin UI can show why a candidate was skipped.
                _persist_conn = get_db()
                try:
                    _persist_conn.execute(
                        "UPDATE admin_pipeline_videos SET "
                        "  interestingness_score = ?, "
                        "  interestingness_verdict = ?, "
                        "  interestingness_reason = ?, "
                        "  interestingness_model = ? "
                        "WHERE id = ?",
                        (
                            verdict.get("score") or None,
                            verdict.get("verdict"),
                            verdict.get("reason"),
                            verdict.get("model"),
                            video_id,
                        ),
                    )
                    _persist_conn.commit()
                finally:
                    _persist_conn.close()
                if not verdict.get("pass"):
                    msg = (
                        f"interestingness skip "
                        f"(score={verdict.get('score')}): "
                        f"{verdict.get('reason')}"
                    )
                    print(
                        f"[interestingness] recitation {video_id} "
                        f"{chapter}:{ayah_start}-{ayah_end} REJECTED — {msg}"
                    )
                    _set_conn = get_db()
                    try:
                        _set_conn.execute(
                            "UPDATE admin_pipeline_videos SET "
                            "  status='rejected_uninteresting', "
                            "  error_message=?, "
                            "  verse_data=? "
                            "WHERE id=?",
                            (
                                msg[:1000],
                                # Persist the rejected verse range so the
                                # next run's used_rows query picks it up
                                # and forces Claude to avoid it.
                                json.dumps(
                                    [
                                        {"chapter": chapter, "verse": vs}
                                        for vs in range(ayah_start, ayah_end + 1)
                                    ]
                                ),
                                video_id,
                            ),
                        )
                        _set_conn.commit()
                    finally:
                        _set_conn.close()
                    return
                print(
                    f"[interestingness] recitation {video_id} "
                    f"{chapter}:{ayah_start}-{ayah_end} APPROVED "
                    f"(score={verdict.get('score')}): {verdict.get('reason')}"
                )
            except Exception as e:
                # Judge crashed — FAIL CLOSED (2026-07 audit): a dead
                # judge pauses the pipeline instead of waving passages
                # through unjudged. The row is marked failed so the
                # admin UI shows why nothing was produced.
                print(
                    f"[interestingness] recitation judge crashed, "
                    f"rejecting: {e}"
                )
                _set_conn = get_db()
                try:
                    _set_conn.execute(
                        "UPDATE admin_pipeline_videos SET "
                        "  status='failed', error_message=? WHERE id=?",
                        (f"interestingness judge unavailable: {e}"[:1000], video_id),
                    )
                    _set_conn.commit()
                finally:
                    _set_conn.close()
                return

        # ---- 3. Fetch translations ----
        surah_name = _surah_name(chapter)
        passage_ref = (
            f"{surah_name} {chapter}:{ayah_start}"
            if ayah_start == ayah_end
            else f"{surah_name} {chapter}:{ayah_start}-{ayah_end}"
        )

        conn = get_db()
        try:
            verse_data = []
            for vs in range(ayah_start, ayah_end + 1):
                translation = _best_translation(conn, chapter, vs)
                if not translation:
                    continue
                translation = html.unescape(re.sub(r"<[^>]+>", "", translation))
                verse_data.append({
                    "chapter": chapter,
                    "verse": vs,
                    "ref": passage_ref,
                    "passage_ref": passage_ref,
                    "original_translation": translation,
                    "polished_text": "",
                    "tts_filename": None,
                })
        finally:
            conn.close()

        if not verse_data:
            _update_pipeline_video_status(video_id, "failed", error=f"No translations found for {passage_ref}")
            return

        # ---- 4. Polish translations via Claude ----
        polish_status_msg = (
            "Polishing translations for on-screen display..." if is_arabic
            else "Polishing translations for spoken delivery..."
        )
        _update_pipeline_video_status(video_id, "polishing", polish_status_msg)

        verses_for_polish = [
            {"chapter": v["chapter"], "verse": v["verse"], "ref": v["ref"], "translation": v["original_translation"]}
            for v in verse_data
        ]

        if is_arabic:
            polish_intro = (
                "You are preparing a Quranic passage for ON-SCREEN DISPLAY in a YouTube Short.\n"
                f"This is a continuous passage from {passage_ref}. The Arabic recitation plays aloud;\n"
                "the translation appears as subtitles, one verse at a time, synced to the recitation.\n"
                "Polish each verse for clear, emotionally resonant silent reading.\n\n"
                "Rules:\n"
                "- Remove brackets, parentheses, footnote markers, editorial additions like [O Prophet], and superscript numbers\n"
                "- Make the English read cleanly on screen, and flow naturally from one verse to the next\n"
                "- Do NOT substantially change the meaning — polish for readability, not reinterpretation\n"
                "- Make it impactful — the viewer has only a few seconds to absorb each verse\n"
                "- Keep it concise — every word should earn its place (short lines read best on small screens)\n"
                "- Preserve the word 'Allah' if present in the original\n\n"
            )
        else:
            polish_intro = (
                "You are preparing a Quranic passage for spoken delivery in a YouTube Short.\n"
                f"This is a continuous passage from {passage_ref}. Polish each verse for natural spoken delivery.\n"
                "They'll be read as one flowing passage with brief pauses between verses.\n\n"
                "Rules:\n"
                "- Remove brackets, parentheses, footnote markers, editorial additions like [O Prophet], and superscript numbers\n"
                "- Make the text flow naturally for spoken English, and flow naturally from one verse to the next\n"
                "- Do NOT substantially change the meaning — polish for delivery, not reinterpretation\n"
                "- Make it smooth and impactful — imagine someone speaking to an audience with gravitas\n"
                "- Keep it concise — every word should earn its place\n"
                "- Preserve the word 'Allah' if present in the original\n\n"
            )

        polish_prompt = (
            polish_intro +
            f"Verses to polish:\n{json.dumps(verses_for_polish, indent=2)}\n\n"
            "Return ONLY a valid JSON array with the polished text, nothing else:\n"
            '[{"chapter": <int>, "verse": <int>, "polished": "<polished text>"}, ...]'
        )

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": polish_prompt}],
            },
            timeout=30,
        )

        if resp.status_code != 200:
            _update_pipeline_video_status(video_id, "failed", error=f"Claude polishing error: {resp.status_code}")
            return

        resp_text = resp.json()["content"][0]["text"].strip()
        match = re.search(r"\[.*\]", resp_text, re.DOTALL)
        if not match:
            _update_pipeline_video_status(video_id, "failed", error="Could not parse polished text from AI")
            return

        try:
            polished = json.loads(match.group())
        except json.JSONDecodeError as je:
            _update_pipeline_video_status(video_id, "failed", error=f"AI returned invalid JSON for polishing: {je}")
            return
        polished_map = {(p["chapter"], p["verse"]): p["polished"] for p in polished}

        for v in verse_data:
            key = (v["chapter"], v["verse"])
            v["polished_text"] = polished_map.get(key, v["original_translation"])

        # Save verse_data progress
        conn = get_db()
        try:
            conn.execute("UPDATE admin_pipeline_videos SET verse_data = ? WHERE id = ?", (json.dumps(verse_data), video_id))
            conn.commit()
        finally:
            conn.close()

        # ---- 5. Acquire audio: ElevenLabs TTS (English) or reciter mp3s (Arabic) ----
        # For Arabic pipelines: NO ElevenLabs call, NO "The Koraan says" intro.
        # The audio is purely the reciter's recitation — the English translation
        # is shown as subtitles on screen but never spoken aloud.
        if is_arabic:
            _update_pipeline_video_status(video_id, "generating_tts", "Downloading recitation audio...")

            folder = _get_reciter_folder(int(reciter_id_for_pipeline))
            audio_base = "https://verses.quran.com"

            total_dur = 0.0
            for i, v in enumerate(verse_data):
                audio_url = f"{audio_base}/{folder}/{v['chapter']:03d}{v['verse']:03d}.mp3"
                url_hash = hashlib.sha256(audio_url.encode()).hexdigest()[:16]
                filename = f"pipe_{video_id}_{i}_arabic_{url_hash}.mp3"
                filepath = os.path.join(_TTS_CACHE_DIR, filename)

                try:
                    resp = requests.get(audio_url, timeout=30)
                    resp.raise_for_status()
                except Exception as e:
                    _update_pipeline_video_status(video_id, "failed", error=f"Failed to download {audio_url}: {e}")
                    return

                with open(filepath, "wb") as f:
                    f.write(resp.content)

                v["tts_filename"] = filename
                v["audio_url"] = audio_url

                try:
                    total_dur += _get_audio_duration(filepath)
                except Exception:
                    pass

                _update_pipeline_video_status(
                    video_id, "generating_tts", f"Downloaded audio {i + 1}/{len(verse_data)}",
                )

            # Enforce 55s budget BEFORE rendering so we don't waste ffmpeg cycles
            if total_dur > 55.0:
                _update_pipeline_video_status(
                    video_id, "failed",
                    error=f"Passage too long: {total_dur:.1f}s of recitation (limit 55s). Try a shorter range.",
                )
                return

            # 5b. Smart extension: if Claude's auto-picked passage comes in
            # noticeably short (average has been ~33s with a 55s budget),
            # probe the next verses one at a time and ask Claude whether
            # adding each one would meaningfully improve the video. Skipped
            # for manual selection (user picked exact verses on purpose) and
            # for passages already close to the budget.
            # Trigger on anything under 48s — leaves room for one more short
            # verse before the 55s cap, and catches mid-argument endings that
            # would otherwise ship with 7–15s of unused budget.
            EXTENSION_TRIGGER_SECONDS = 48.0
            EXTENSION_MAX_COUNT = 3
            EXTENSION_HARD_CAP_SECONDS = 55.0

            if (
                not is_manual_selection
                and api_key
                and total_dur < EXTENSION_TRIGGER_SECONDS
            ):
                _update_pipeline_video_status(
                    video_id, "generating_tts",
                    f"Passage is {total_dur:.0f}s — considering extension...",
                )
                current_end_ayah = ayah_end

                for ext_i in range(EXTENSION_MAX_COUNT):
                    candidate_ayah = current_end_ayah + 1

                    # Does the next verse exist in the same surah?
                    conn_ext = get_db()
                    try:
                        cand_row = conn_ext.execute(
                            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                            (chapter, candidate_ayah),
                        ).fetchone()
                        if not cand_row:
                            break  # end of surah
                        candidate_arabic = _strip_bismillah(
                            cand_row["text_uthmani"], chapter, candidate_ayah
                        )
                        candidate_translation = _best_translation(conn_ext, chapter, candidate_ayah)
                    finally:
                        conn_ext.close()
                    if not candidate_translation:
                        break
                    candidate_translation = html.unescape(re.sub(r"<[^>]+>", "", candidate_translation))

                    # Ask Claude whether this extension would enhance the video
                    passage_so_far = "\n".join(
                        f"- {v['chapter']}:{v['verse']}: {v.get('polished_text') or v['original_translation']}"
                        for v in verse_data
                    )
                    budget_remaining = EXTENSION_HARD_CAP_SECONDS - total_dur
                    decide_prompt = (
                        f"You are deciding whether to extend a short Arabic-recitation Quran Short by one more verse.\n\n"
                        f"CURRENT PASSAGE ({chapter}:{ayah_start}-{current_end_ayah}, ~{total_dur:.0f}s of recitation, "
                        f"~{budget_remaining:.0f}s of budget remaining before the 55s cap):\n"
                        f"{passage_so_far}\n\n"
                        f"CANDIDATE NEXT VERSE ({chapter}:{candidate_ayah}):\n"
                        f"Arabic: {candidate_arabic}\n"
                        f"Translation: {candidate_translation}\n\n"
                        f"GUIDANCE — the #1 failure mode is ending a Short mid-thought. If the current\n"
                        f"passage trails off in a way that viewers feel was cut short, that is much worse\n"
                        f"than a slightly-too-long video. Read the last verse of the current passage and ask:\n\n"
                        f"  Does it end on a COMPLETE thought, or does it leave something hanging?\n\n"
                        f"Signs the current ending is INCOMPLETE (→ strongly prefer adding):\n"
                        f"- Ends on a rhetorical question that the next verse answers\n"
                        f"- Ends on a setup/premise that the next verse resolves or subverts\n"
                        f"- Ends on a conditional (\"if/when...\") whose consequence is in the next verse\n"
                        f"- Ends on a list or parallel structure that the next verse completes\n"
                        f"- Ends on a contrast (\"some... but others...\") missing its counterpart\n"
                        f"- Ends describing a scene/state whose resolution or reversal is in the next verse\n"
                        f"- The next verse contains the emotional, theological, or rhetorical PAYOFF\n\n"
                        f"Signs the current ending stands on its own (→ decline adding):\n"
                        f"- Ends on a definitive declaration, verdict, or summary statement\n"
                        f"- Next verse shifts to an unrelated topic or audience\n"
                        f"- Next verse dilutes rather than completes (e.g. restarts a new theme)\n\n"
                        f"When genuinely uncertain AND budget permits, add the verse. A finished thought\n"
                        f"is more valuable than a tighter runtime.\n\n"
                        f"Answer with JSON only:\n"
                        f'{{"add": true or false, "reason": "<one short sentence naming the completeness signal>"}}'
                    )
                    try:
                        dec_resp = requests.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "Content-Type": "application/json",
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                            },
                            json={
                                "model": "claude-sonnet-4-6",
                                "max_tokens": 200,
                                "messages": [{"role": "user", "content": decide_prompt}],
                            },
                            timeout=30,
                        )
                        if dec_resp.status_code != 200:
                            print(f"[extension] decision HTTP {dec_resp.status_code}; stopping")
                            break
                        decide_text = dec_resp.json()["content"][0]["text"].strip()
                        m = re.search(r"\{.*\}", decide_text, re.DOTALL)
                        if not m:
                            break
                        decision = json.loads(m.group())
                    except Exception as e:
                        print(f"[extension] decision error: {e}")
                        break

                    if not decision.get("add"):
                        print(
                            f"[extension] Claude declined {chapter}:{candidate_ayah}: "
                            f"{decision.get('reason', '(no reason)')}"
                        )
                        break

                    # Claude says yes — download the audio, measure, budget-check
                    ext_audio_url = f"{audio_base}/{folder}/{chapter:03d}{candidate_ayah:03d}.mp3"
                    ext_hash = hashlib.sha256(ext_audio_url.encode()).hexdigest()[:16]
                    ext_filename = f"pipe_{video_id}_ext{ext_i}_arabic_{ext_hash}.mp3"
                    ext_filepath = os.path.join(_TTS_CACHE_DIR, ext_filename)
                    try:
                        ext_resp = requests.get(ext_audio_url, timeout=30)
                        ext_resp.raise_for_status()
                    except Exception as e:
                        print(f"[extension] audio download failed: {e}")
                        break
                    with open(ext_filepath, "wb") as f:
                        f.write(ext_resp.content)
                    try:
                        ext_dur = _get_audio_duration(ext_filepath)
                    except Exception:
                        ext_dur = 0.0

                    if total_dur + ext_dur > EXTENSION_HARD_CAP_SECONDS:
                        print(
                            f"[extension] {chapter}:{candidate_ayah} would push total to "
                            f"{total_dur + ext_dur:.1f}s (cap {EXTENSION_HARD_CAP_SECONDS}s); stopping"
                        )
                        try:
                            os.remove(ext_filepath)
                        except OSError:
                            pass
                        break

                    # Polish this single added verse with a small Claude call
                    polish_ext_prompt = (
                        f"Polish this Quranic verse translation for clear on-screen display in a YouTube Short. "
                        f"The Arabic recitation plays aloud; this text appears as subtitles.\n\n"
                        f'Original: "{candidate_translation}"\n\n'
                        f"Rules:\n"
                        f"- Remove brackets, parentheses, footnote markers, editorial additions, superscript numbers\n"
                        f"- Read cleanly and impactfully for a viewer with a few seconds to absorb it\n"
                        f"- Keep concise; do NOT substantially change meaning\n"
                        f"- Preserve 'Allah' if present\n\n"
                        f"Return ONLY the polished text, no preamble."
                    )
                    try:
                        p_resp = requests.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "Content-Type": "application/json",
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                            },
                            json={
                                "model": "claude-sonnet-4-6",
                                "max_tokens": 500,
                                "messages": [{"role": "user", "content": polish_ext_prompt}],
                            },
                            timeout=30,
                        )
                        polished_ext = (
                            p_resp.json()["content"][0]["text"].strip()
                            if p_resp.status_code == 200 else candidate_translation
                        )
                    except Exception:
                        polished_ext = candidate_translation

                    # Commit
                    verse_data.append({
                        "chapter": chapter,
                        "verse": candidate_ayah,
                        "ref": passage_ref,  # rewritten below once loop ends
                        "passage_ref": passage_ref,
                        "original_translation": candidate_translation,
                        "polished_text": polished_ext,
                        "tts_filename": ext_filename,
                        "audio_url": ext_audio_url,
                    })
                    total_dur += ext_dur
                    current_end_ayah = candidate_ayah
                    print(
                        f"[extension] added {chapter}:{candidate_ayah} "
                        f"({ext_dur:.1f}s, total {total_dur:.1f}s): "
                        f"{decision.get('reason', '')}"
                    )
                    _update_pipeline_video_status(
                        video_id, "generating_tts",
                        f"Extended to {chapter}:{candidate_ayah} ({total_dur:.0f}s total)",
                    )

                # If we actually extended, update the passage_ref that the
                # renderer uses for the subtitle band and that the frontend
                # displays above video cards.
                if current_end_ayah != ayah_end:
                    ayah_end = current_end_ayah
                    new_passage_ref = (
                        f"{surah_name} {chapter}:{ayah_start}"
                        if ayah_start == ayah_end
                        else f"{surah_name} {chapter}:{ayah_start}-{ayah_end}"
                    )
                    for v in verse_data:
                        v["ref"] = new_passage_ref
                        v["passage_ref"] = new_passage_ref
                    passage_ref = new_passage_ref
        else:
            _update_pipeline_video_status(video_id, "generating_tts", "Generating voice audio...")

            conn = get_db()
            try:
                pref = conn.execute("SELECT value FROM admin_preferences WHERE key = 'elevenlabs_api_key'").fetchone()
                eleven_key = pref["value"] if pref else os.environ.get("ELEVENLABS_API_KEY", "")
            finally:
                conn.close()

            if not eleven_key:
                _update_pipeline_video_status(video_id, "failed", error="ElevenLabs API key not configured")
                return

            voice_id = pipeline["voice_id"]

            def _call_elevenlabs(text_to_speak):
                return requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": eleven_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg",
                    },
                    json={
                        "text": text_to_speak,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    },
                    timeout=60,
                )

            # Intro: spoken "The Quran says" before any verse text appears.
            # Phonetic spelling ("Koraan") because ElevenLabs mispronounces "Quran"
            # (often as "KWOR-an"). The text is never shown on screen — only spoken —
            # so the spelling only needs to produce the right sound ("kor-AAN").
            intro_text = "The Koraan says"
            intro_hash = hashlib.sha256(f"{voice_id}:intro:{intro_text}".encode()).hexdigest()[:16]
            intro_filename = f"pipe_{video_id}_intro_{intro_hash}.mp3"
            intro_filepath = os.path.join(_TTS_CACHE_DIR, intro_filename)

            intro_resp = _call_elevenlabs(intro_text)
            if intro_resp.status_code != 200:
                _update_pipeline_video_status(video_id, "failed", error=f"Intro TTS failed: {intro_resp.status_code}")
                return
            with open(intro_filepath, "wb") as f:
                f.write(intro_resp.content)

            # Stash intro filename on the first verse for cleanup tracking
            if verse_data:
                verse_data[0]["intro_tts_filename"] = intro_filename

            for i, v in enumerate(verse_data):
                text = v["polished_text"]
                text_hash = hashlib.sha256(f"{voice_id}:{text}".encode()).hexdigest()[:16]
                filename = f"pipe_{video_id}_{i}_{text_hash}.mp3"
                filepath = os.path.join(_TTS_CACHE_DIR, filename)

                tts_resp = _call_elevenlabs(text)

                if tts_resp.status_code != 200:
                    _update_pipeline_video_status(video_id, "failed", error=f"TTS failed for {v['ref']}: {tts_resp.status_code}")
                    return

                with open(filepath, "wb") as f:
                    f.write(tts_resp.content)

                v["tts_filename"] = filename
                _update_pipeline_video_status(video_id, "generating_tts", f"Generated audio {i + 1}/{len(verse_data)}")

        # Save verse_data with TTS filenames
        conn = get_db()
        try:
            conn.execute("UPDATE admin_pipeline_videos SET verse_data = ? WHERE id = ?", (json.dumps(verse_data), video_id))
            conn.commit()
        finally:
            conn.close()

        # ---- 6. Render video ----
        _update_pipeline_video_status(video_id, "rendering", "Rendering video...")

        tmpdir = tempfile.mkdtemp(prefix="pipeline_")
        try:
            target_w, target_h = 1080, 1920  # Always short (vertical) for YouTube Shorts
            show_bands = bool(pipeline["show_bands"])

            # -- Audio assembly --
            audio_segments = []
            timeline = []
            t = 0.0

            # Intro: spoken "The Quran says" + brief pause, no subtitles
            intro_fname = verse_data[0].get("intro_tts_filename") if verse_data else None
            if intro_fname:
                intro_src = os.path.join(_TTS_CACHE_DIR, intro_fname)
                if os.path.isfile(intro_src):
                    intro_local = os.path.join(tmpdir, "intro.mp3")
                    shutil.copy2(intro_src, intro_local)
                    intro_dur = _get_audio_duration(intro_local)
                    audio_segments.append(intro_local)
                    t += intro_dur

                    intro_pause = os.path.join(tmpdir, "intro_pause.mp3")
                    subprocess.run(
                        [_FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                         "-t", "0.7", "-c:a", "libmp3lame", "-q:a", "9", intro_pause],
                        capture_output=True, timeout=10,
                    )
                    audio_segments.append(intro_pause)
                    t += 0.7

            for i, v in enumerate(verse_data):
                tts_src = os.path.join(_TTS_CACHE_DIR, v["tts_filename"])
                tts_local = os.path.join(tmpdir, f"tts_{i}.mp3")
                shutil.copy2(tts_src, tts_local)
                dur = _get_audio_duration(tts_local)

                audio_segments.append(tts_local)
                timeline.append({
                    "start": t,
                    "dur": dur,
                    "ref": v["ref"],
                    "text": v["polished_text"],
                })
                t += dur

                # Add 0.5s silence between verses
                if i < len(verse_data) - 1:
                    sil = os.path.join(tmpdir, f"silence_{i}.mp3")
                    subprocess.run(
                        [_FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                         "-t", "0.5", "-c:a", "libmp3lame", "-q:a", "9", sil],
                        capture_output=True, timeout=10,
                    )
                    audio_segments.append(sil)
                    t += 0.5

            # Outro
            outro_dur = 5.0
            outro_start = t
            total_duration = t + outro_dur

            outro_sil = os.path.join(tmpdir, "outro_silence.mp3")
            subprocess.run(
                [_FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-t", str(outro_dur), "-c:a", "libmp3lame", "-q:a", "9", outro_sil],
                capture_output=True, timeout=10,
            )
            audio_segments.append(outro_sil)

            # Concatenate all audio
            concat_list = os.path.join(tmpdir, "concat.txt")
            with open(concat_list, "w") as f:
                for af in audio_segments:
                    f.write(f"file '{af}'\n")

            combined_audio = os.path.join(tmpdir, "combined.mp3")
            subprocess.run(
                [_FFMPEG, "-y", "-f", "concat", "-safe", "0",
                 "-i", concat_list, "-c", "copy", combined_audio],
                capture_output=True, timeout=120,
            )

            # -- ASS subtitle file --
            ref_fontsize = 82
            trans_fontsize = 64
            text_colour = "&H00FFFFFF"
            outline_colour = "&H50000000"
            fonts_dir = os.path.join(os.path.dirname(__file__), "data", "fonts")
            ass_path = os.path.join(tmpdir, "subs.ass")

            # Ref band at bottom of frame
            ref_band_h = 170
            ref_band_y = 1650
            # Alignment 2 (bottom center): MarginV = pixels from bottom to bottom of text
            # Band occupies y=1650..1820; center band at y=1735, so MarginV ≈ 1920-1735 = 185
            ref_margin_v = 180
            content_band_h = 380
            content_band_y = (target_h - content_band_h) // 2

            # Outline weight: heavier when no bands for readability
            ref_outline = 5 if not show_bands else 3
            trans_outline = 5 if not show_bands else 3

            with open(ass_path, "w", encoding="utf-8") as af:
                af.write("[Script Info]\n")
                af.write("ScriptType: v4.00+\n")
                af.write(f"PlayResX: {target_w}\n")
                af.write(f"PlayResY: {target_h}\n")
                af.write("ScaledBorderAndShadow: yes\n\n")

                af.write("[V4+ Styles]\n")
                af.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                af.write(f"Style: Ref,Liberation Sans,{ref_fontsize},{text_colour},&H000000FF,{outline_colour},&H00000000,1,0,0,0,100,100,0,0,1,{ref_outline},0,2,40,40,{ref_margin_v},0\n")
                af.write(f"Style: Trans,Liberation Sans,{trans_fontsize},{text_colour},&H000000FF,{outline_colour},&H00000000,0,0,0,0,100,100,0,0,1,{trans_outline},0,5,60,60,0,0\n")
                outro_site_fs = 90
                outro_tag_fs = 54
                af.write(f"Style: OutroSite,Liberation Sans,{outro_site_fs},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,5,40,40,0,0\n")
                af.write(f"Style: OutroTag,Liberation Sans,{outro_tag_fs},&H80FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,0\n")

                af.write("\n[Events]\n")
                af.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

                def _at(seconds):
                    h = int(seconds // 3600)
                    m = int((seconds % 3600) // 60)
                    s = seconds % 60
                    return f"{h}:{m:02d}:{s:05.2f}"

                def _esc(text):
                    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

                # One ref line spans the whole passage; text changes per verse
                if timeline:
                    passage_start = _at(timeline[0]["start"])
                    passage_end = _at(timeline[-1]["start"] + timeline[-1]["dur"])
                    ref_str = _esc(verse_data[0]["ref"])
                    af.write(f"Dialogue: 0,{passage_start},{passage_end},Ref,,0,0,0,,{{\\fad(600,600)}}{ref_str}\n")

                for entry in timeline:
                    start = _at(entry["start"])
                    end = _at(entry["start"] + entry["dur"])
                    text = _esc(entry["text"])
                    af.write(f"Dialogue: 0,{start},{end},Trans,,0,0,0,,{{\\fad(300,0)}}{text}\n")

                # Outro
                os_str = _at(outro_start)
                oe_str = _at(outro_start + outro_dur)
                cx = target_w // 2
                cy = target_h // 2
                site_y = cy - 40
                tag_y = cy + 70
                af.write(f"Dialogue: 0,{os_str},{oe_str},OutroSite,,0,0,0,,{{\\fad(800,0)\\pos({cx},{site_y})}}al-nuqta.com\n")
                af.write(f"Dialogue: 0,{os_str},{oe_str},OutroTag,,0,0,0,,{{\\fad(1200,0)\\pos({cx},{tag_y})}}A Root Based Translation of the Quran\n")

            # -- Drawbox filter chain --
            drawbox_parts = []

            if show_bands:
                # Ref band: one box spanning the whole passage
                if timeline:
                    ref_s = timeline[0]["start"]
                    ref_e = timeline[-1]["start"] + timeline[-1]["dur"]
                    ref_enable = f"between(t\\,{ref_s:.3f}\\,{ref_e:.3f})"
                    drawbox_parts.append(
                        f"drawbox=x=0:y={ref_band_y}:w=iw:h={ref_band_h}"
                        f":color=black@0.5:t=fill:enable='{ref_enable}'"
                    )
                # Content band: one box per verse (matches text changes)
                for entry in timeline:
                    s, e = entry["start"], entry["start"] + entry["dur"]
                    enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
                    drawbox_parts.append(
                        f"drawbox=x=0:y={content_band_y}:w=iw:h={content_band_h}"
                        f":color=black@0.5:t=fill:enable='{enable}'"
                    )

            # Outro: fade-in dark overlay over 1.5s (stepped opacity 0 -> 0.75)
            fade_dur = 1.5
            fade_steps = 10
            step_dur = fade_dur / fade_steps
            for s in range(fade_steps):
                t_s = outro_start + s * step_dur
                t_e = outro_start + (s + 1) * step_dur
                alpha = 0.75 * (s + 1) / fade_steps
                drawbox_parts.append(
                    f"drawbox=x=0:y=0:w=iw:h=ih"
                    f":color=black@{alpha:.3f}:t=fill"
                    f":enable='between(t\\,{t_s:.3f}\\,{t_e:.3f})'"
                )
            drawbox_parts.append(
                f"drawbox=x=0:y=0:w=iw:h=ih"
                f":color=black@0.75:t=fill"
                f":enable='gte(t\\,{outro_start + fade_dur:.3f})'"
            )

            # -- FFmpeg render --
            output_filename = f"pipeline_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(_GENERATED_VIDEOS_DIR, output_filename)

            vf_parts = [
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase",
                f"crop={target_w}:{target_h}",
            ] + drawbox_parts + [
                f"ass={ass_path}:fontsdir={fonts_dir}",
            ]
            vf = ",".join(vf_parts)

            render_timeout = max(600, int(total_duration * 10))

            if music_path:
                af_mix = (
                    f"[1:a]volume=1.0[voice];"
                    f"[2:a]volume=0.01,afade=t=out:st={max(0, total_duration - 5):.3f}:d=5[music];"
                    f"[voice][music]amix=inputs=2:duration=first:dropout_transition=3:normalize=0[aout]"
                )
                cmd = [
                    _FFMPEG, "-y",
                    "-stream_loop", "-1", "-i", bg_path,
                    "-i", combined_audio,
                    "-i", music_path,
                    "-vf", vf,
                    "-filter_complex", af_mix,
                    "-t", f"{total_duration:.3f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "aac", "-b:a", "192k",
                    "-map", "0:v:0", "-map", "[aout]",
                    "-movflags", "+faststart",
                    output_path,
                ]
            else:
                cmd = [
                    _FFMPEG, "-y",
                    "-stream_loop", "-1", "-i", bg_path,
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
                _update_pipeline_video_status(video_id, "failed", error=f"ffmpeg error: {stderr}")
                return

            file_size = os.path.getsize(output_path)

            # ---- 7. Generate YouTube title & description via Ollama (unless preseeded) ----
            # If the row already has a title/description (manual mode), keep them.
            preseed_title = vid_row["youtube_title"] if "youtube_title" in vid_row.keys() else None
            preseed_desc = vid_row["youtube_description"] if "youtube_description" in vid_row.keys() else None
            has_manual_metadata = bool(preseed_title) or bool(preseed_desc)

            yt_title, yt_desc = preseed_title or "", preseed_desc or ""
            yt_tags: list[str] = []
            if not has_manual_metadata:
                try:
                    _update_pipeline_video_status(video_id, "generating_metadata", "Generating YouTube metadata...")
                    yt_title, yt_desc, yt_tags = _generate_youtube_metadata(verse_data)
                except Exception as e:
                    print(f"WARNING: YouTube metadata generation failed for video {video_id}: {e}")

            conn2 = get_db()
            try:
                conn2.execute(
                    """UPDATE admin_pipeline_videos
                       SET status='complete', filename=?, file_size=?,
                           youtube_title=?, youtube_description=?, youtube_tags=?,
                           completed_at=CURRENT_TIMESTAMP, progress='Done'
                       WHERE id = ?""",
                    (output_filename, file_size, yt_title or None, yt_desc or None,
                     json.dumps(yt_tags) if yt_tags else None, video_id),
                )
                conn2.commit()
            finally:
                conn2.close()

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except subprocess.TimeoutExpired:
        _update_pipeline_video_status(video_id, "failed", error="Video generation timed out")
    except Exception as e:
        _update_pipeline_video_status(video_id, "failed", error=str(e)[:500])


# ---------------------------------------------------------------------------
# Pipeline Scheduler
#
# One background daemon thread polls pipeline_schedules every 30s. For each
# enabled schedule, for each scheduled time TODAY, if we're past the time but
# within grace_minutes AND no pipeline_schedule_runs row already exists for
# (pipeline_id, scheduled_time) — fire it, with appropriate guards.
#
# Guards:
#   - Daily cap: count today's scheduler-triggered runs for this pipeline
#     (manual runs don't count against the cap).
#   - Active video: if the pipeline has a video in a non-terminal state,
#     skip this fire (don't stack).
#
# Every fire — whether it produces a video or is skipped — writes an audit
# row so the UI can show what happened and why.
# ---------------------------------------------------------------------------

def _start_scheduled_pipeline_run(pipeline_id: int) -> int:
    """Launch a scheduler-triggered pipeline run. Returns the video_id.

    Mirrors admin_pipeline_generate's INSERT + thread start, but marks the
    row as triggered_by='scheduler' and skips the HTTP layer.
    """
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO admin_pipeline_videos (pipeline_id, status, triggered_by) "
            "VALUES (?, 'pending', 'scheduler')",
            (pipeline_id,),
        )
        conn.commit()
        video_id = cur.lastrowid
    finally:
        conn.close()
    t = threading.Thread(target=_pipeline_generate_task, args=(video_id,), daemon=True)
    t.start()
    return video_id


def _scheduler_record_run(pipeline_id: int, scheduled_time: str, status: str,
                          video_id: int | None = None, note: str | None = None):
    """Insert (or ignore if duplicate) an audit row for a scheduled fire."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO pipeline_schedule_runs "
            "(pipeline_id, scheduled_time, video_id, status, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (pipeline_id, scheduled_time, video_id, status, note),
        )
        conn.commit()
    finally:
        conn.close()


def _scheduler_tick():
    """One pass of the scheduler loop. Safe to call repeatedly."""
    from datetime import datetime, timedelta
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    conn = get_db()
    try:
        schedules = conn.execute(
            "SELECT s.pipeline_id, s.times, s.max_runs_per_day, s.enabled, s.grace_minutes, "
            "       p.name AS pipeline_name "
            "FROM pipeline_schedules s "
            "JOIN admin_pipelines p ON p.id = s.pipeline_id "
            "WHERE s.enabled = 1"
        ).fetchall()
    finally:
        conn.close()

    for sched in schedules:
        pid = sched["pipeline_id"]
        try:
            times = json.loads(sched["times"] or "[]")
        except (json.JSONDecodeError, TypeError):
            times = []
        if not isinstance(times, list) or not times:
            continue

        grace = int(sched["grace_minutes"] or 30)
        cap = int(sched["max_runs_per_day"] or 2)

        for t_str in times:
            if not isinstance(t_str, str) or not re.match(r"^\d{1,2}:\d{2}$", t_str):
                continue
            hh, mm = map(int, t_str.split(":"))
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                continue

            sched_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            scheduled_time_str = sched_dt.strftime("%Y-%m-%d %H:%M")

            # Only consider times that have already passed today.
            if now < sched_dt:
                continue

            # Past the grace window — won't backfill stale slots.
            if now > sched_dt + timedelta(minutes=grace):
                # Record a miss so the UI can show why nothing fired.
                _scheduler_record_run(
                    pid, scheduled_time_str, "skipped_grace",
                    note=f"Past {grace}-minute grace window"
                )
                continue

            # Already fired (or already recorded as a miss) — idempotent.
            conn = get_db()
            try:
                existing = conn.execute(
                    "SELECT id FROM pipeline_schedule_runs "
                    "WHERE pipeline_id = ? AND scheduled_time = ?",
                    (pid, scheduled_time_str),
                ).fetchone()
            finally:
                conn.close()
            if existing:
                continue

            # Daily cap — count only today's scheduler-triggered fires that
            # actually started a video (status='fired'). Skipped runs don't
            # count against the cap.
            conn = get_db()
            try:
                today_count = conn.execute(
                    "SELECT COUNT(*) AS c FROM pipeline_schedule_runs "
                    "WHERE pipeline_id = ? AND status = 'fired' "
                    "AND substr(scheduled_time, 1, 10) = ?",
                    (pid, today_str),
                ).fetchone()["c"]
            finally:
                conn.close()
            if today_count >= cap:
                _scheduler_record_run(
                    pid, scheduled_time_str, "skipped_cap",
                    note=f"Daily cap reached ({today_count}/{cap})"
                )
                continue

            # Don't stack on top of an already-running video for this pipeline.
            conn = get_db()
            try:
                active = conn.execute(
                    "SELECT id FROM admin_pipeline_videos "
                    "WHERE pipeline_id = ? AND status IN "
                    "('pending','selecting_verses','polishing','generating_tts','rendering','generating_metadata') "
                    "LIMIT 1",
                    (pid,),
                ).fetchone()
            finally:
                conn.close()
            if active:
                _scheduler_record_run(
                    pid, scheduled_time_str, "skipped_active",
                    note=f"Another video already running (#{active['id']})"
                )
                continue

            # All guards clear — fire.
            try:
                video_id = _start_scheduled_pipeline_run(pid)
                _scheduler_record_run(pid, scheduled_time_str, "fired", video_id=video_id)
                print(f"[scheduler] Fired pipeline {pid} ({sched['pipeline_name']}) "
                      f"for {scheduled_time_str} → video {video_id}")
            except Exception as e:
                _scheduler_record_run(
                    pid, scheduled_time_str, "error",
                    note=str(e)[:300]
                )
                print(f"[scheduler] ERROR firing pipeline {pid}: {e}")


# ---------------------------------------------------------------------------
# YouTube Upload Scheduler
#
# Runs inside the same daemon loop as the pipeline scheduler. For each
# configured time slot today, if we're past it + within the grace window and
# haven't already fired that slot, try to upload the oldest eligible pipeline
# video. Eligible = status 'complete' + uploaded_to_youtube = 0 +
# auto_upload_skipped = 0 + triggered_by = 'scheduler' (only auto-generated
# videos auto-upload; manual picks stay manual).
#
# Before uploading, runs an Ollama sanity check asking "is this video worth
# uploading?" — if the model says no, the video is marked auto_upload_skipped
# and the slot records skipped_sanity. If Ollama isn't configured or the check
# errors, we default to uploading (errors on the side of shipping, since the
# admin already blessed the video when it was generated).
# ---------------------------------------------------------------------------


def _ensure_youtube_upload_tables():
    conn = get_db()
    try:
        # Per-video skip flag for sanity-rejected videos (idempotent migration).
        # Recitation pipeline first.
        try:
            conn.execute(
                "ALTER TABLE admin_pipeline_videos "
                "ADD COLUMN auto_upload_skipped INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()
        except Exception:
            pass
        # Same flag on educational_videos so the global YouTube upload
        # scheduler can sanity-reject educational rows without re-picking
        # them every slot. Idempotent: ALTER fails harmlessly if already
        # present, and the docker entrypoint's schema-align step preserves
        # it across deploys.
        try:
            conn.execute(
                "ALTER TABLE educational_videos "
                "ADD COLUMN auto_upload_skipped INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()
        except Exception:
            pass
        # Singleton schedule config: single row with id=1
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youtube_upload_schedule (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0,
                times TEXT NOT NULL DEFAULT '["09:00","12:00","15:00","18:00","21:00"]',
                grace_minutes INTEGER NOT NULL DEFAULT 30,
                sanity_check_enabled INTEGER NOT NULL DEFAULT 1,
                privacy TEXT NOT NULL DEFAULT 'public',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT OR IGNORE INTO youtube_upload_schedule (id) VALUES (1)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youtube_upload_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_time TEXT NOT NULL,
                fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                video_id INTEGER,
                youtube_video_id TEXT,
                status TEXT NOT NULL,
                note TEXT
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_yur_scheduled_time
            ON youtube_upload_runs (scheduled_time)
        """)
        conn.commit()
    finally:
        conn.close()


try:
    _ensure_youtube_upload_tables()
except Exception as e:
    print(f"WARNING: youtube upload tables setup failed: {e}")


def _youtube_sanity_check(video_row) -> tuple[bool, str]:
    """Ask Ollama whether this video is worth uploading.

    Returns (should_upload, reason). If Ollama isn't configured or errors,
    defaults to True (with a note) — admin already blessed the video by
    having the pipeline produce it; we don't want the sanity check to become
    a hard dependency that blocks all uploads if Ollama is down.
    """
    title = (video_row["youtube_title"] or "").strip()
    description = (video_row["youtube_description"] or "").strip()
    try:
        tag_list = json.loads(video_row["youtube_tags"] or "[]")
    except (json.JSONDecodeError, TypeError):
        tag_list = []
    try:
        verses = json.loads(video_row["verse_data"] or "[]")
    except (json.JSONDecodeError, TypeError):
        verses = []

    # Summarise verses for the prompt
    verse_lines = []
    passage_ref = ""
    for v in verses:
        passage_ref = v.get("passage_ref") or v.get("ref") or passage_ref
        polished = v.get("polished_text") or v.get("original_translation") or ""
        verse_lines.append(f"  {v.get('chapter')}:{v.get('verse')}: {polished}")
    verse_block = "\n".join(verse_lines) or "(no verse data)"

    conn = get_db()
    try:
        prefs: dict[str, str] = {}
        for row in conn.execute(
            "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
        ).fetchall():
            prefs[row["key"]] = row["value"]
    finally:
        conn.close()

    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    model = (prefs.get("ollama_metadata_model") or prefs.get("ollama_model") or "").strip()
    api_key = prefs.get("ollama_api_key") or ""

    if not model:
        return (True, "Ollama not configured — sanity check skipped")

    prompt = (
        "You are doing a final quality check before a Quran Shorts video is uploaded "
        "to YouTube. Reject ONLY if there's a clear problem — default to approving.\n\n"
        f"Passage: {passage_ref or '(unknown)'}\n"
        f"Title: {title or '(none)'}\n"
        f"Description: {description or '(none)'}\n"
        f"Tags: {', '.join(tag_list) if tag_list else '(none)'}\n\n"
        f"Polished verses shown in the video:\n{verse_block}\n\n"
        "Reject if any of these are clearly wrong:\n"
        "- Title is broken, empty, or generic spiritual filler (e.g. 'Reflect on divine promises')\n"
        "- Description restates the translation without adding a specific insight\n"
        "- Tags are empty or nonsensical\n"
        "- Polished verse text looks garbled, truncated, or contains raw markup/brackets\n"
        "- The passage selection feels incoherent — verses don't form a meaningful unit\n\n"
        "Approve if the content is thoughtful and specific, even if you personally would\n"
        "phrase it differently. Err toward approving.\n\n"
        "Answer with JSON only:\n"
        '{"upload": true or false, "reason": "<one short sentence>"}'
    )

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            # 90s is plenty for a yes/no decision. If a model takes longer,
            # we'd rather abort and approve (since sanity is the safety net,
            # not the gate).
            timeout=90,
        )
        if resp.status_code != 200:
            return (True, f"Sanity check API error {resp.status_code}; proceeding")
        content = resp.json().get("message", {}).get("content", "")
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
        content = re.sub(r"\n?```\s*$", "", content.strip())
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return (True, "Sanity check response unparseable; proceeding")
        obj = json.loads(match.group())
        upload = bool(obj.get("upload", True))
        reason = (obj.get("reason") or "").strip()[:300]
        return (upload, reason or ("Approved" if upload else "Rejected"))
    except Exception as e:
        return (True, f"Sanity check error: {str(e)[:200]} — proceeding")


def _youtube_sanity_check_educational(edu_row, conn) -> tuple[bool, str]:
    """Sanity check for an educational_videos row.

    Adapts the educational schema (chapter/verse columns, no `verse_data`
    blob) to a minimal shim the recitation `_youtube_sanity_check` can
    consume, then delegates. Pulls the verse translation so the prompt
    sees the actual content the operator approved at script-gen time.
    Defaults to approve on any lookup error — same posture as the
    recitation check (sanity is the safety net, not the gate).
    """
    chapter = edu_row["chapter"]
    verse = edu_row["verse"]
    polished = ""
    try:
        tr = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        ).fetchone()
        if tr and tr["text_en"]:
            polished = tr["text_en"]
    except Exception:
        pass

    fake_row = {
        "youtube_title": edu_row["youtube_title"] or "",
        "youtube_description": edu_row["youtube_description"] or "",
        "youtube_tags": edu_row["youtube_tags"] or "[]",
        "verse_data": json.dumps([{
            "chapter": chapter,
            "verse": verse,
            "passage_ref": f"{chapter}:{verse}",
            "polished_text": polished,
            "original_translation": polished,
        }]),
    }
    return _youtube_sanity_check(fake_row)


def _youtube_upload_record_run(
    scheduled_time: str,
    status: str,
    video_id: int | None = None,
    youtube_video_id: str | None = None,
    note: str | None = None,
):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO youtube_upload_runs "
            "(scheduled_time, video_id, youtube_video_id, status, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (scheduled_time, video_id, youtube_video_id, status, note),
        )
        conn.commit()
    finally:
        conn.close()


def _youtube_update_run_status(
    scheduled_time: str,
    status: str,
    youtube_video_id: str | None = None,
    note: str | None = None,
):
    """Update an existing run row (keyed by scheduled_time) with a new status.

    Used by the async upload worker to transition from 'running' → final
    outcome without creating a duplicate audit row.
    """
    conn = get_db()
    try:
        if youtube_video_id is not None:
            conn.execute(
                "UPDATE youtube_upload_runs "
                "SET status = ?, youtube_video_id = ?, note = ?, fired_at = CURRENT_TIMESTAMP "
                "WHERE scheduled_time = ?",
                (status, youtube_video_id, note, scheduled_time),
            )
        else:
            conn.execute(
                "UPDATE youtube_upload_runs "
                "SET status = ?, note = ?, fired_at = CURRENT_TIMESTAMP "
                "WHERE scheduled_time = ?",
                (status, note, scheduled_time),
            )
        conn.commit()
    finally:
        conn.close()


# OAuth circuit-breaker tunables. After N consecutive OAuth failures
# across upload attempts, skip ALL upcoming slots until the operator
# fixes the credentials. Without this, every slot retried the same
# broken upload, accumulating ~5 failed-run rows per day until the
# Google API put us on a quota probation.
OAUTH_CIRCUIT_BREAKER_THRESHOLD = 3


def _youtube_oauth_failure_count(conn) -> int:
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key='youtube_oauth_failure_count'"
    ).fetchone()
    try:
        return int(row["value"]) if row and row["value"] else 0
    except (TypeError, ValueError):
        return 0


def _youtube_oauth_record_failure(conn, error_message: str) -> int:
    """Bump the consecutive-OAuth-failure counter. Returns the new count.
    Called from any upload helper when OAuth fails."""
    new_count = _youtube_oauth_failure_count(conn) + 1
    conn.execute(
        "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
        "VALUES ('youtube_oauth_failure_count', ?, CURRENT_TIMESTAMP)",
        (str(new_count),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
        "VALUES ('youtube_oauth_last_failure_message', ?, CURRENT_TIMESTAMP)",
        ((error_message or "")[:1000],),
    )
    conn.commit()
    return new_count


def _youtube_oauth_record_success(conn) -> None:
    """Reset the consecutive-OAuth-failure counter on any successful
    token fetch. Called from _get_youtube_access_token below."""
    conn.execute(
        "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
        "VALUES ('youtube_oauth_failure_count', '0', CURRENT_TIMESTAMP)",
    )
    conn.execute("DELETE FROM admin_preferences WHERE key='youtube_oauth_last_failure_message'")
    conn.commit()


def _youtube_upload_tick():
    """One pass of the YouTube upload scheduler. Idempotent per slot."""
    from datetime import datetime, timedelta
    now = datetime.now()

    # Circuit-breaker check FIRST — if OAuth is broken, every upload
    # attempt this tick would fail identically. Skip all slots until
    # the operator resets the breaker (which happens automatically
    # the next time _get_youtube_access_token succeeds).
    conn_cb = get_db()
    try:
        failures = _youtube_oauth_failure_count(conn_cb)
        last_msg_row = conn_cb.execute(
            "SELECT value FROM admin_preferences "
            "WHERE key='youtube_oauth_last_failure_message'"
        ).fetchone()
        last_msg = last_msg_row["value"] if last_msg_row else ""
    finally:
        conn_cb.close()
    if failures >= OAUTH_CIRCUIT_BREAKER_THRESHOLD:
        # Don't even attempt — just record one breaker-tripped row at
        # the earliest pending slot so the operator sees it on the UI
        # and stops getting one error per slot per day.
        # We log every ~hour, not every 30s tick.
        if not hasattr(_youtube_upload_tick, "_last_breaker_log") or \
           (now - _youtube_upload_tick._last_breaker_log).total_seconds() > 3600:
            print(
                f"[youtube-scheduler] OAuth circuit breaker open "
                f"({failures} consecutive failures). Last: "
                f"{last_msg[:200]}. Reset by fixing credentials at "
                f"Admin → Settings → YouTube."
            )
            _youtube_upload_tick._last_breaker_log = now
        return

    conn = get_db()
    try:
        sched = conn.execute(
            "SELECT enabled, times, grace_minutes, sanity_check_enabled, privacy "
            "FROM youtube_upload_schedule WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()
    if not sched or not sched["enabled"]:
        return

    try:
        times = json.loads(sched["times"] or "[]")
    except (json.JSONDecodeError, TypeError):
        times = []
    if not isinstance(times, list) or not times:
        return

    grace = int(sched["grace_minutes"] or 30)
    sanity_enabled = bool(sched["sanity_check_enabled"])
    privacy = (sched["privacy"] or "public").lower()
    if privacy not in ("public", "unlisted", "private"):
        privacy = "public"

    for t_str in times:
        if not isinstance(t_str, str) or not re.match(r"^\d{1,2}:\d{2}$", t_str):
            continue
        hh, mm = map(int, t_str.split(":"))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            continue
        sched_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        scheduled_time_str = sched_dt.strftime("%Y-%m-%d %H:%M")

        if now < sched_dt:
            continue
        if now > sched_dt + timedelta(minutes=grace):
            _youtube_upload_record_run(
                scheduled_time_str, "skipped_grace",
                note=f"Past {grace}-minute grace window",
            )
            continue

        # Idempotence
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM youtube_upload_runs WHERE scheduled_time = ?",
                (scheduled_time_str,),
            ).fetchone()
        finally:
            conn.close()
        if existing:
            continue

        # Find oldest eligible video across BOTH pipelines (recitation +
        # educational). One slot drains one video, picking whichever
        # has been waiting longest by created_at. Educational rows
        # become eligible at status='rendered' (no separate 'complete'
        # state) and use youtube_video_id IS NULL as the
        # not-uploaded-yet check.
        conn = get_db()
        try:
            rec_row = conn.execute(
                "SELECT id, created_at FROM admin_pipeline_videos "
                "WHERE status = 'complete' "
                "  AND uploaded_to_youtube = 0 "
                "  AND auto_upload_skipped = 0 "
                "  AND triggered_by = 'scheduler' "
                "ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            edu_row = None
            if _EDU_OK:
                edu_row = conn.execute(
                    "SELECT id, created_at FROM educational_videos "
                    "WHERE status = 'rendered' "
                    "  AND youtube_video_id IS NULL "
                    "  AND auto_upload_skipped = 0 "
                    "  AND triggered_by = 'scheduler' "
                    "ORDER BY created_at ASC LIMIT 1"
                ).fetchone()
        finally:
            conn.close()

        candidates: list[tuple[str, int, str]] = []
        if rec_row:
            candidates.append(("recitation", rec_row["id"], rec_row["created_at"] or ""))
        if edu_row:
            candidates.append(("educational", edu_row["id"], edu_row["created_at"] or ""))
        if not candidates:
            _youtube_upload_record_run(
                scheduled_time_str, "skipped_no_videos",
                note="No eligible scheduler-generated videos to upload",
            )
            continue

        # Oldest first. Ties (extremely rare — same created_at to the
        # second across two tables) deterministically pick recitation
        # first via the original list order.
        candidates.sort(key=lambda c: c[2])
        vrow_kind, vrow_id, _ = candidates[0]

        # Claim the slot IMMEDIATELY with a placeholder row. This serves two
        # purposes: (1) the UNIQUE index on scheduled_time prevents any other
        # tick from double-firing this slot while we're running, and (2) the
        # rest of the work (sanity + upload) can run in a background thread
        # without blocking the daemon loop for minutes at a time.
        _youtube_upload_record_run(
            scheduled_time_str, "running",
            video_id=vrow_id,
            note=f"[{vrow_kind}] Sanity check + upload in progress",
        )

        def _do_sanity_and_upload(
            scheduled_time_str: str = scheduled_time_str,
            video_row_id: int = vrow_id,
            kind: str = vrow_kind,
            sanity_enabled: bool = sanity_enabled,
            privacy: str = privacy,
        ):
            table = "educational_videos" if kind == "educational" else "admin_pipeline_videos"

            # Re-fetch the row inside the thread — the one from the outer
            # scope is a Row object from a connection that's been closed.
            conn_inner = get_db()
            try:
                vrow_inner = conn_inner.execute(
                    f"SELECT * FROM {table} WHERE id = ?",
                    (video_row_id,),
                ).fetchone()
            finally:
                conn_inner.close()
            if not vrow_inner:
                _youtube_update_run_status(
                    scheduled_time_str, "error",
                    note=f"[{kind}] Video disappeared mid-run",
                )
                return

            # Sanity check — branch on kind to use the right adapter.
            if sanity_enabled:
                if kind == "educational":
                    conn_san = get_db()
                    try:
                        should_upload, reason = _youtube_sanity_check_educational(
                            vrow_inner, conn_san,
                        )
                    finally:
                        conn_san.close()
                else:
                    should_upload, reason = _youtube_sanity_check(vrow_inner)
                if not should_upload:
                    conn2 = get_db()
                    try:
                        conn2.execute(
                            f"UPDATE {table} SET auto_upload_skipped = 1 WHERE id = ?",
                            (video_row_id,),
                        )
                        conn2.commit()
                    finally:
                        conn2.close()
                    _youtube_update_run_status(
                        scheduled_time_str, "skipped_sanity",
                        note=f"[{kind}] {reason}",
                    )
                    print(
                        f"[youtube-scheduler] {kind} video {video_row_id} "
                        f"rejected by sanity: {reason}"
                    )
                    return

            # Upload — branch on kind to call the right helper. Both
            # return the same result shape: {ok, youtube_video_id,
            # error?, playlist_note?}.
            try:
                if kind == "educational":
                    result = _perform_educational_youtube_upload(
                        video_row_id, privacy=privacy,
                    )
                else:
                    result = _perform_youtube_upload(video_row_id, privacy=privacy)
            except Exception as e:
                _youtube_update_run_status(
                    scheduled_time_str, "error",
                    note=f"[{kind}] Exception: {str(e)[:300]}",
                )
                return

            if not result.get("ok"):
                _youtube_update_run_status(
                    scheduled_time_str, "error",
                    note=f"[{kind}] {result.get('error', 'unknown')[:500]}",
                )
                return

            note_parts = [f"Uploaded {privacy} ({kind})"]
            pl_note = result.get("playlist_note")
            if pl_note:
                note_parts.append(f"Playlist: {pl_note}")
            _youtube_update_run_status(
                scheduled_time_str, "uploaded",
                youtube_video_id=result.get("youtube_video_id"),
                note=" — ".join(note_parts)[:500],
            )
            print(
                f"[youtube-scheduler] uploaded {kind} video {video_row_id} → "
                f"YT {result.get('youtube_video_id')} at {scheduled_time_str}"
            )

        threading.Thread(target=_do_sanity_and_upload, daemon=True).start()


_scheduler_stop = threading.Event()


def _educational_scheduler_tick():
    """Educational-pipeline equivalent of _scheduler_tick. For each
    enabled schedule + each time slot today within the grace window,
    fire the orchestrator unless the slot is already recorded, the
    daily cap is reached, or another video for this pipeline is in
    flight. Mirrors the recitation scheduler's logic so the operator
    mental model is identical across the two."""
    if not _EDU_OK:
        return
    from datetime import datetime, timedelta
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    conn = get_db()
    try:
        schedules = conn.execute(
            "SELECT s.pipeline_id, s.times, s.max_runs_per_day, s.enabled, "
            "       s.grace_minutes, p.name AS pipeline_name, p.enabled AS pipeline_enabled "
            "FROM educational_pipeline_schedules s "
            "JOIN educational_pipelines p ON p.id = s.pipeline_id "
            "WHERE s.enabled = 1"
        ).fetchall()
    finally:
        conn.close()

    for sched in schedules:
        pid = sched["pipeline_id"]
        # Pipeline itself disabled? Schedule sticks but doesn't fire.
        if not sched["pipeline_enabled"]:
            continue
        try:
            times = json.loads(sched["times"] or "[]")
        except (json.JSONDecodeError, TypeError):
            times = []
        if not isinstance(times, list) or not times:
            continue

        grace = int(sched["grace_minutes"] or 30)
        cap = int(sched["max_runs_per_day"] or 2)

        for t_str in times:
            if not isinstance(t_str, str) or not re.match(r"^\d{1,2}:\d{2}$", t_str):
                continue
            hh, mm = map(int, t_str.split(":"))
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                continue
            sched_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            scheduled_time_str = sched_dt.strftime("%Y-%m-%d %H:%M")

            # Only consider slots whose time has arrived today.
            if now < sched_dt:
                continue
            # Past the grace window — record a miss so the UI can
            # explain why nothing fired.
            if now > sched_dt + timedelta(minutes=grace):
                c = get_db()
                try:
                    _edu.record_schedule_run(
                        c, pid, scheduled_time_str, "skipped_grace",
                        note=f"Past {grace}-minute grace window",
                    )
                finally:
                    c.close()
                continue

            # Idempotency: if this slot already has a row, skip.
            c = get_db()
            try:
                existing = c.execute(
                    "SELECT id FROM educational_pipeline_schedule_runs "
                    "WHERE pipeline_id = ? AND scheduled_time = ?",
                    (pid, scheduled_time_str),
                ).fetchone()
            finally:
                c.close()
            if existing:
                continue

            # Daily cap — count only 'fired' rows. Skipped slots
            # don't burn cap.
            c = get_db()
            try:
                today_count = c.execute(
                    "SELECT COUNT(*) AS n FROM educational_pipeline_schedule_runs "
                    "WHERE pipeline_id = ? AND status = 'fired' "
                    "AND substr(scheduled_time, 1, 10) = ?",
                    (pid, today_str),
                ).fetchone()["n"]
            finally:
                c.close()
            if today_count >= cap:
                c = get_db()
                try:
                    _edu.record_schedule_run(
                        c, pid, scheduled_time_str, "skipped_cap",
                        note=f"Daily cap reached ({today_count}/{cap})",
                    )
                finally:
                    c.close()
                continue

            # Don't pile on top of an already-running educational video
            # for this pipeline. Educational has fewer in-flight statuses
            # than recitation — the candidate-through-rendering arc.
            c = get_db()
            try:
                active = c.execute(
                    "SELECT id FROM educational_videos "
                    "WHERE pipeline_id = ? AND status IN ('candidate','script_ready','rendering') "
                    "LIMIT 1",
                    (pid,),
                ).fetchone()
            finally:
                c.close()
            if active:
                c = get_db()
                try:
                    _edu.record_schedule_run(
                        c, pid, scheduled_time_str, "skipped_active",
                        note=f"Another video already running (#{active['id']})",
                    )
                finally:
                    c.close()
                continue

            # All guards clear — fire.
            video_id, err = _start_educational_pipeline_run(
                pid, triggered_by="scheduler",
            )
            c = get_db()
            try:
                if err:
                    _edu.record_schedule_run(
                        c, pid, scheduled_time_str, "error", note=err,
                    )
                    print(f"[edu-scheduler] ERROR firing pipeline {pid}: {err}")
                else:
                    _edu.record_schedule_run(
                        c, pid, scheduled_time_str, "fired", video_id=video_id,
                    )
                    print(
                        f"[edu-scheduler] Fired pipeline {pid} "
                        f"({sched['pipeline_name']}) for {scheduled_time_str} "
                        f"→ video {video_id}"
                    )
            finally:
                c.close()


def _lessons_refresh_tick():
    """Every-30-seconds tick that fires the lessons-refresh cron when
    the configured interval (default 3 days) has elapsed. The actual
    work is a single Ollama call per pipeline type — cheap enough to
    just gate on `should_refresh` rather than maintaining a separate
    daemon clock."""
    if not _LESSONS_OK or _lessons is None:
        return
    conn = get_db()
    try:
        if not _lessons.should_refresh(conn):
            return
        print("[lessons] scheduled refresh starting")
        summary = _lessons.refresh_lessons(conn)
        print(f"[lessons] scheduled refresh done: {summary}")
    finally:
        conn.close()


def _scheduler_loop():
    """Main scheduler daemon — ticks every 30 seconds."""
    print("[scheduler] daemon started")
    while not _scheduler_stop.is_set():
        try:
            _scheduler_tick()
        except Exception as e:
            print(f"[scheduler] tick error: {e}")
        try:
            _youtube_upload_tick()
        except Exception as e:
            print(f"[youtube-scheduler] tick error: {e}")
        try:
            _educational_scheduler_tick()
        except Exception as e:
            print(f"[edu-scheduler] tick error: {e}")
        try:
            _lessons_refresh_tick()
        except Exception as e:
            print(f"[lessons-scheduler] tick error: {e}")
        try:
            _qa_publish_tick()
        except Exception as e:
            print(f"[qa-publish] tick error: {e}")
        # Sleep in 5s chunks so shutdown can interrupt quickly.
        for _ in range(6):
            if _scheduler_stop.is_set():
                return
            time.sleep(5)


def _start_scheduler_once():
    """Spawn the scheduler daemon thread (idempotent per process)."""
    if getattr(_start_scheduler_once, "_started", False):
        return
    try:
        threading.Thread(target=_scheduler_loop, daemon=True).start()
        _start_scheduler_once._started = True
    except Exception as e:
        print(f"WARNING: could not start scheduler daemon: {e}")


def _youtube_stats_refresh_loop():
    """Daily YouTube stats refresh. Runs at 03:15 UTC; on startup fires
    once if today's snapshot is missing so the dashboard isn't stale
    after a deploy."""
    # Initial check: if no snapshot exists for today AND we have OAuth
    # credentials, populate one immediately. Useful after a deploy or
    # cold start.
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM youtube_video_stats WHERE snapshot_date = ?",
                (today,),
            ).fetchone()
        finally:
            conn.close()
        if int(row[0]) == 0:
            # Tiny delay so the app finishes booting before we hit YouTube
            time.sleep(30)
            try:
                _refresh_youtube_stats()
            except Exception as e:
                print(f"[youtube-stats] initial refresh failed: {e}")
    except Exception as e:
        print(f"[youtube-stats] initial-check failed: {e}")

    while True:
        # Sleep until next 03:15 UTC
        now = datetime.now(timezone.utc)
        target = now.replace(hour=3, minute=15, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)
        wait_seconds = max(60, (target - now).total_seconds())
        time.sleep(wait_seconds)
        try:
            result = _refresh_youtube_stats()
            print(f"[youtube-stats] daily refresh: {result}")
        except Exception as e:
            print(f"[youtube-stats] daily refresh error: {e}")


def _start_youtube_stats_thread_once():
    if getattr(_start_youtube_stats_thread_once, "_started", False):
        return
    try:
        threading.Thread(target=_youtube_stats_refresh_loop, daemon=True).start()
        _start_youtube_stats_thread_once._started = True
    except Exception as e:
        print(f"WARNING: could not start YouTube stats thread: {e}")


# When imported by a WSGI server (gunicorn, uwsgi) the module is loaded
# exactly once per worker and __name__ is the module name — safe to start.
# When `python app.py` is run directly the __main__ block below handles it
# with a reloader-aware guard; the module here is imported as __main__, so
# this branch is skipped.
if __name__ != "__main__":
    _start_scheduler_once()
    _start_youtube_stats_thread_once()


# --------------- Admin: Pipeline Scheduler endpoints ---------------

@app.route("/api/admin/pipeline-schedules", methods=["GET"])
@admin_required
def admin_list_pipeline_schedules():
    """Return every pipeline with its schedule row (creating an empty default
    if none exists yet)."""
    conn = get_db()
    try:
        pipelines = conn.execute(
            "SELECT id, name, language FROM admin_pipelines ORDER BY id"
        ).fetchall()
        out = []
        for p in pipelines:
            row = conn.execute(
                "SELECT times, max_runs_per_day, enabled, grace_minutes, updated_at "
                "FROM pipeline_schedules WHERE pipeline_id = ?",
                (p["id"],),
            ).fetchone()
            if row:
                try:
                    times = json.loads(row["times"] or "[]")
                except (json.JSONDecodeError, TypeError):
                    times = []
                out.append({
                    "pipeline_id": p["id"],
                    "pipeline_name": p["name"],
                    "pipeline_language": p["language"],
                    "times": times,
                    "max_runs_per_day": row["max_runs_per_day"],
                    "enabled": bool(row["enabled"]),
                    "grace_minutes": row["grace_minutes"],
                    "updated_at": row["updated_at"],
                })
            else:
                out.append({
                    "pipeline_id": p["id"],
                    "pipeline_name": p["name"],
                    "pipeline_language": p["language"],
                    "times": [],
                    "max_runs_per_day": 2,
                    "enabled": False,
                    "grace_minutes": 30,
                    "updated_at": None,
                })
        return jsonify(out)
    finally:
        conn.close()


@app.route("/api/admin/pipeline-schedules/<int:pipeline_id>", methods=["PUT"])
@admin_required
def admin_upsert_pipeline_schedule(pipeline_id):
    """Create or replace the schedule row for a pipeline."""
    body = request.get_json(silent=True) or {}
    times = body.get("times")
    max_runs = body.get("max_runs_per_day", 2)
    enabled = bool(body.get("enabled", False))
    grace = int(body.get("grace_minutes", 30))

    if not isinstance(times, list):
        return jsonify({"error": "times must be a JSON array of 'HH:MM' strings"}), 400
    cleaned: list[str] = []
    for t in times:
        if not isinstance(t, str):
            continue
        s = t.strip()
        m = re.match(r"^(\d{1,2}):(\d{2})$", s)
        if not m:
            return jsonify({"error": f"invalid time format: {t!r} (expected HH:MM)"}), 400
        h, mn = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mn <= 59):
            return jsonify({"error": f"invalid time value: {t}"}), 400
        cleaned.append(f"{h:02d}:{mn:02d}")
    # De-duplicate while preserving order
    seen: set[str] = set()
    deduped = [t for t in cleaned if not (t in seen or seen.add(t))]

    try:
        max_runs = int(max_runs)
    except (TypeError, ValueError):
        return jsonify({"error": "max_runs_per_day must be an integer"}), 400
    if not (1 <= max_runs <= 20):
        return jsonify({"error": "max_runs_per_day must be between 1 and 20"}), 400
    if not (1 <= grace <= 240):
        return jsonify({"error": "grace_minutes must be between 1 and 240"}), 400

    conn = get_db()
    try:
        pipe = conn.execute(
            "SELECT id FROM admin_pipelines WHERE id = ?", (pipeline_id,)
        ).fetchone()
        if not pipe:
            return jsonify({"error": "Pipeline not found"}), 404
        conn.execute(
            "INSERT INTO pipeline_schedules "
            "(pipeline_id, times, max_runs_per_day, enabled, grace_minutes, updated_at) "
            "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(pipeline_id) DO UPDATE SET "
            "  times=excluded.times, "
            "  max_runs_per_day=excluded.max_runs_per_day, "
            "  enabled=excluded.enabled, "
            "  grace_minutes=excluded.grace_minutes, "
            "  updated_at=CURRENT_TIMESTAMP",
            (pipeline_id, json.dumps(deduped), max_runs, 1 if enabled else 0, grace),
        )
        conn.commit()
        return jsonify({
            "pipeline_id": pipeline_id,
            "times": deduped,
            "max_runs_per_day": max_runs,
            "enabled": enabled,
            "grace_minutes": grace,
        })
    finally:
        conn.close()


@app.route("/api/admin/pipeline-schedule-runs", methods=["GET"])
@admin_required
def admin_list_schedule_runs():
    """Recent scheduler fires (or misses). Newest first."""
    limit = min(max(request.args.get("limit", 50, type=int), 1), 500)
    pipeline_id = request.args.get("pipeline_id", type=int)
    conn = get_db()
    try:
        # Include the produced video's youtube_title so the audit log
        # can show "what got generated" instead of just "video #47".
        # admin_pipeline_videos is the recitation pipeline's output
        # table — pipeline_schedule_runs only references this one.
        if pipeline_id:
            rows = conn.execute(
                "SELECT r.*, p.name AS pipeline_name, p.language AS pipeline_language, "
                "       av.youtube_title AS video_title, "
                "       av.status AS video_status "
                "FROM pipeline_schedule_runs r "
                "JOIN admin_pipelines p ON p.id = r.pipeline_id "
                "LEFT JOIN admin_pipeline_videos av ON av.id = r.video_id "
                "WHERE r.pipeline_id = ? ORDER BY r.fired_at DESC LIMIT ?",
                (pipeline_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT r.*, p.name AS pipeline_name, p.language AS pipeline_language, "
                "       av.youtube_title AS video_title, "
                "       av.status AS video_status "
                "FROM pipeline_schedule_runs r "
                "JOIN admin_pipelines p ON p.id = r.pipeline_id "
                "LEFT JOIN admin_pipeline_videos av ON av.id = r.video_id "
                "ORDER BY r.fired_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# --------------- Admin: YouTube Upload Scheduler endpoints ---------------

@app.route("/api/admin/youtube-upload-schedule", methods=["GET"])
@admin_required
def admin_get_youtube_upload_schedule():
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT enabled, times, grace_minutes, sanity_check_enabled, "
            "       privacy, updated_at "
            "FROM youtube_upload_schedule WHERE id = 1"
        ).fetchone()
        # OAuth circuit-breaker status — surfaced so the UI can warn
        # the operator that the schedule is currently paused (the tick
        # auto-pauses after N consecutive OAuth failures to stop
        # hammering broken credentials).
        oauth_failures = _youtube_oauth_failure_count(conn)
        oauth_msg_row = conn.execute(
            "SELECT value FROM admin_preferences "
            "WHERE key='youtube_oauth_last_failure_message'"
        ).fetchone()
        oauth_msg = oauth_msg_row["value"] if oauth_msg_row else None
    finally:
        conn.close()
    breaker_open = oauth_failures >= OAUTH_CIRCUIT_BREAKER_THRESHOLD
    if not row:
        return jsonify({
            "enabled": False,
            "times": ["09:00", "12:00", "15:00", "18:00", "21:00"],
            "grace_minutes": 30,
            "sanity_check_enabled": True,
            "privacy": "public",
            "updated_at": None,
            "oauth_circuit_breaker": {
                "open": breaker_open,
                "consecutive_failures": oauth_failures,
                "last_failure": oauth_msg,
            },
        })
    try:
        times = json.loads(row["times"] or "[]")
    except (json.JSONDecodeError, TypeError):
        times = []
    return jsonify({
        "enabled": bool(row["enabled"]),
        "times": times,
        "grace_minutes": row["grace_minutes"],
        "sanity_check_enabled": bool(row["sanity_check_enabled"]),
        "privacy": row["privacy"],
        "updated_at": row["updated_at"],
        "oauth_circuit_breaker": {
            "open": breaker_open,
            "consecutive_failures": oauth_failures,
            "last_failure": oauth_msg,
        },
    })


@app.route("/api/admin/youtube-upload-schedule/test-oauth", methods=["POST"])
@admin_required
def admin_test_youtube_oauth():
    """Operator action: try a token exchange right now to validate
    the configured credentials. On success, the circuit-breaker
    counter resets automatically (the helper records success). On
    failure, the helper records the failure with a concrete
    remediation message. Returns the result so the UI can show it."""
    try:
        # (was _get_youtube_access_token — an undefined name; the endpoint
        # 500'd with NameError on every use)
        token = _youtube_get_access_token()
        return jsonify({
            "ok": True,
            "message": "OAuth refresh succeeded. Upload schedule will resume on the next slot.",
            "access_token_prefix": (token or "")[:8] + "…",
        })
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/admin/youtube-upload-schedule/reset-circuit-breaker", methods=["POST"])
@admin_required
def admin_reset_youtube_circuit_breaker():
    """Operator escape hatch — clear the OAuth failure counter without
    actually testing creds. Use after manually fixing credentials when
    test-oauth would burn API quota you'd rather save."""
    conn = get_db()
    try:
        _youtube_oauth_record_success(conn)
    finally:
        conn.close()
    return jsonify({"ok": True})


# ============================================================================
# Q&A video script bank (admin) — Stage 1 of the pre-generated shorts plan.
#
# Scripts are drafted by Claude (subscription) via the /qa-video-draft skill,
# validated by the fail-closed compile/punch/match gates (qa_video_gen.py),
# and land in qa_videos as status='gate_passed'. From here the admin flow is:
#   gate_passed --render(202+thread)--> rendered --human approve--> approved
#   --publish tick (Mon/Wed/Fri)--> uploaded
# The publish scheduler ONLY uploads human-approved videos; it never
# generates anything.
# ============================================================================

_QA_PUBLISH_PREF_KEY = "qa_publish_schedule"
_QA_PUBLISH_DEFAULTS = {
    "enabled": True,
    # Python weekday(): Monday=0, Wednesday=2, Friday=4
    "days": [0, 2, 4],
    "time": "16:00",       # UTC
    "grace_minutes": 120,
    "privacy": "public",
    # ElevenLabs voice for bank renders; None → first admin_voices row.
    "voice_id": None,
    "last_fired_date": None,
}


def _qa_resolve_voice(conn) -> str | None:
    """Voice for bank renders: the schedule pref when set (and still
    existing), else the first configured voice."""
    prefs = _qa_publish_prefs(conn)
    want = (prefs.get("voice_id") or "").strip()
    if want:
        row = conn.execute(
            "SELECT voice_id FROM admin_voices WHERE voice_id=?", (want,)
        ).fetchone()
        if row:
            return row["voice_id"]
    row = conn.execute(
        "SELECT voice_id FROM admin_voices ORDER BY id LIMIT 1"
    ).fetchone()
    return row["voice_id"] if row else None


def _qa_videos_dir() -> str:
    import qa_video_render as _qr
    return _qr.OUTPUT_DIR


def _qa_publish_prefs(conn) -> dict:
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key=?",
        (_QA_PUBLISH_PREF_KEY,),
    ).fetchone()
    prefs = dict(_QA_PUBLISH_DEFAULTS)
    if row and row["value"]:
        try:
            prefs.update(json.loads(row["value"]))
        except Exception:
            pass
    return prefs


def _qa_publish_prefs_save(conn, prefs: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO admin_preferences (key, value) VALUES (?, ?)",
        (_QA_PUBLISH_PREF_KEY, json.dumps(prefs)),
    )
    conn.commit()


@app.route("/api/admin/qa-videos", methods=["GET"])
@admin_required
def admin_qa_videos_list():
    conn = get_db()
    try:
        _ensure_qa_videos_table(conn)
        rows = [dict(r) for r in conn.execute(
            "SELECT id, qa_id, anchor_ref, title, theme, status, filename, "
            "       file_size, punch_ok, match_ok, error_message, rendering, "
            "       source_type, source_key, angle, self_score, quality_report, "
            "       youtube_video_id, uploaded_to_youtube, created_at, "
            "       completed_at, script_json "
            "FROM qa_videos ORDER BY id DESC"
        ).fetchall()]
        for r in rows:
            # Ship the beats for the review UI's script panel, not the
            # whole raw JSON blob.
            try:
                r["beats"] = json.loads(r.pop("script_json") or "{}").get("beats", [])
            except Exception:
                r["beats"] = []
        prefs = _qa_publish_prefs(conn)
        try:
            voices = [dict(r) for r in conn.execute(
                "SELECT id, name, voice_id FROM admin_voices ORDER BY id"
            ).fetchall()]
        except Exception:
            voices = []
        try:
            candidates = [dict(r) for r in conn.execute(
                "SELECT id, source_type, source_key, anchor_ref, angle, "
                "       hook_sketch, self_score, status "
                "FROM video_candidates "
                "WHERE status IN ('proposed', 'starred') "
                "ORDER BY (status='starred') DESC, self_score DESC, id DESC "
                "LIMIT 20"
            ).fetchall()]
        except Exception:
            candidates = []
        try:
            lessons = [dict(r) for r in conn.execute(
                "SELECT id, lesson_key, lesson, source, evidence, status "
                "FROM studio_lessons "
                "ORDER BY (status='flagged') DESC, (status='active') DESC, id"
            ).fetchall()]
        except Exception:
            lessons = []
        return jsonify({"videos": rows, "publish_schedule": prefs,
                        "voices": voices, "candidates": candidates,
                        "lessons": lessons})
    finally:
        conn.close()


@app.route("/api/admin/qa-videos/<int:row_id>/render", methods=["POST"])
@admin_required
def admin_qa_video_render(row_id: int):
    """202 + daemon thread — rendering takes minutes (TTS + Chromium) and
    must never hold a request thread (2026-07 outage lesson)."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status, rendering FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        if row["status"] not in ("gate_passed", "approved"):
            return jsonify({"error": f"not renderable from status={row['status']}"}), 409
        if row["rendering"]:
            return jsonify({"error": "already rendering"}), 409
        pref = conn.execute(
            "SELECT value FROM admin_preferences WHERE key='elevenlabs_api_key'"
        ).fetchone()
        elevenlabs_key = pref["value"] if pref and pref["value"] else None
        if not elevenlabs_key:
            return jsonify({"error": "ElevenLabs API key not set"}), 400
        voice_id = _qa_resolve_voice(conn)
        if not voice_id:
            return jsonify({"error": "no voice configured (admin_voices empty)"}), 400
    finally:
        conn.close()

    def _do_render():
        import qa_video_render as _qr
        c = get_db()
        try:
            _qr.render_qa_video(
                c, row_id,
                elevenlabs_api_key=elevenlabs_key, voice_id=voice_id,
            )
        except Exception as exc:  # error already recorded on the row
            print(f"[qa-videos] render {row_id} failed: {exc}")
        finally:
            c.close()

    threading.Thread(target=_do_render, daemon=True).start()
    return jsonify({"id": row_id, "status": "rendering"}), 202


@app.route("/api/admin/qa-videos/<int:row_id>/video", methods=["GET"])
@admin_required
def admin_qa_video_file(row_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT filename FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["filename"]:
        return jsonify({"error": "no rendered file"}), 404
    # conditional=True → Range support, so the <video> player can seek.
    return send_from_directory(
        _qa_videos_dir(), row["filename"],
        mimetype="video/mp4", conditional=True,
    )


@app.route("/api/admin/qa-videos/<int:row_id>/approve", methods=["POST"])
@admin_required
def admin_qa_video_approve(row_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        if row["status"] != "gate_passed":
            return jsonify({"error": f"only gate_passed scripts can be approved (status={row['status']})"}), 409
        conn.execute(
            "UPDATE qa_videos SET status='approved', error_message=NULL WHERE id=?",
            (row_id,),
        )
        conn.commit()
        return jsonify({"id": row_id, "status": "approved"})
    finally:
        conn.close()


@app.route("/api/admin/qa-videos/<int:row_id>/reject", methods=["POST"])
@admin_required
def admin_qa_video_reject(row_id: int):
    body = request.get_json(silent=True) or {}
    reason = (body.get("reason") or "").strip()[:500]
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        conn.execute(
            "UPDATE qa_videos SET status='rejected', error_message=? WHERE id=?",
            (reason or "rejected by reviewer", row_id),
        )
        conn.commit()
        return jsonify({"id": row_id, "status": "rejected"})
    finally:
        conn.close()


@app.route("/api/admin/qa-videos/<int:row_id>/script", methods=["PUT"])
@admin_required
def admin_qa_video_edit_script(row_id: int):
    """Inline script edit. The edited script is re-validated through the
    SAME fail-closed gates the original draft passed (compile + punchiness
    + highlight-match) BEFORE anything is saved — a human edit can never
    ship an unverified highlight or a bloated narration. On success the
    stored script/payload are replaced and any previously rendered file is
    marked stale (cleared) so the publish tick re-renders the new text."""
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        result, code = _qa_apply_script_edit(conn, row_id, body)
        return jsonify(result), code
    finally:
        conn.close()


def _qa_apply_script_edit(conn, row_id: int, body: dict) -> tuple[dict, int]:
    """Shared gate-checked script edit — used by the admin inline editor AND
    the tokened agent endpoint. Merges title/theme/beats onto the stored
    script, re-runs ALL gates, and only persists on a clean pass."""
    row = conn.execute(
        "SELECT * FROM qa_videos WHERE id=?", (row_id,)
    ).fetchone()
    if not row:
        return {"error": "not found"}, 404
    rd = dict(row)
    if rd["status"] not in ("gate_passed", "approved", "rejected"):
        return {"error": f"not editable in status={rd['status']}"}, 409
    if rd.get("rendering"):
        return {"error": "rendering in progress — try again shortly"}, 409

    try:
        script = json.loads(rd["script_json"] or "{}")
    except Exception:
        return {"error": "stored script is unreadable"}, 500

    # Merge the editable surface: title + beats. Identity fields
    # (qa_id, anchor_ref) are immutable; theme may ride along.
    old_narrations = {(b.get("narration") or "").strip()
                      for b in script.get("beats", []) if isinstance(b, dict)}
    before = json.dumps(script, ensure_ascii=False, sort_keys=True)
    if isinstance(body.get("title"), str) and body["title"].strip():
        script["title"] = body["title"].strip()
    if isinstance(body.get("theme"), str) and body["theme"].strip():
        script["theme"] = body["theme"].strip()
    if isinstance(body.get("beats"), list) and body["beats"]:
        script["beats"] = body["beats"]
    after = json.dumps(script, ensure_ascii=False, sort_keys=True)
    if before == after:
        return {"ok": True, "unchanged": True, "status": rd["status"]}, 200

    import qa_video_gen as _qg
    result = _qg.gate_script(conn, script)
    if not result["ok"]:
        # Grandfather clause: scripts written before the spoken-style rule
        # may carry em-dashes/colons in narrations the operator did NOT
        # touch. Style issues only block the edit when a CHANGED narration
        # is dirty; everything else (compile, highlights, terminology,
        # budgets) still fails closed.
        style_issues = [i for i in result["issues"]
                        if "written-register punctuation" in i]
        other_issues = [i for i in result["issues"]
                        if "written-register punctuation" not in i]
        changed_narrations = [
            (b.get("narration") or "").strip()
            for b in script.get("beats", []) if isinstance(b, dict)
        ]
        changed_narrations = [n for n in changed_narrations
                              if n not in old_narrations]
        marks = ("\u2014", "\u2013", ":", ";")
        dirty_change = any(any(m in n for m in marks)
                           for n in changed_narrations)
        if other_issues or dirty_change or not style_issues:
            return {
                "error": "edit rejected by gates",
                "issues": result["issues"],
            }, 422
        # Legacy style forgiven: the edit itself is clean and every other
        # gate passed — proceed as a pass.

    # Saved: replace script + regenerated payload; clear any stale
    # render. A rejected script that now passes returns to the queue.
    new_status = "gate_passed" if rd["status"] == "rejected" else rd["status"]
    conn.execute(
        "UPDATE qa_videos SET "
        "  title=?, theme=?, script_json=?, payload_json=?, "
        "  match_snapshot=?, punch_ok=1, match_ok=1, "
        "  filename=NULL, file_size=NULL, error_message=NULL, status=? "
        "WHERE id=?",
        (
            script.get("title"), script.get("theme"),
            json.dumps(script, ensure_ascii=False),
            json.dumps(result["payload"], ensure_ascii=False),
            json.dumps(result["match_snapshot"], ensure_ascii=False),
            new_status, row_id,
        ),
    )
    conn.commit()
    return {"ok": True, "status": new_status}, 200


def _qa_edit_token_hash(token: str) -> str:
    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _qa_verify_edit_token(conn, row_id: int, token: str):
    """Return the row dict if the token is valid + unexpired, else None."""
    if not token:
        return None
    row = conn.execute(
        "SELECT * FROM qa_videos WHERE id=?", (row_id,)
    ).fetchone()
    if not row:
        return None
    rd = dict(row)
    if not rd.get("edit_token_hash") or not rd.get("edit_token_expires"):
        return None
    if _qa_edit_token_hash(token) != rd["edit_token_hash"]:
        return None
    from datetime import datetime, timezone
    try:
        exp = datetime.fromisoformat(rd["edit_token_expires"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    if datetime.now(timezone.utc) > exp:
        return None
    return rd


@app.route("/api/admin/qa-videos/<int:row_id>/edit-token", methods=["POST"])
@admin_required
def admin_qa_video_mint_edit_token(row_id: int):
    """Mint a 24h single-script edit token for the "Ask AI to Edit" flow.
    The plaintext token is returned ONCE (only its hash is stored); it
    authorizes the agent GET/PUT endpoints for THIS row only, and every
    edit still goes through the fail-closed gates. Re-minting replaces
    any previous token."""
    from datetime import datetime, timedelta, timezone
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        if row["status"] not in ("gate_passed", "approved", "rejected"):
            return jsonify({"error": f"not editable in status={row['status']}"}), 409
        token = secrets.token_urlsafe(24)
        expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        conn.execute(
            "UPDATE qa_videos SET edit_token_hash=?, edit_token_expires=? WHERE id=?",
            (_qa_edit_token_hash(token), expires, row_id),
        )
        conn.commit()
        return jsonify({"token": token, "expires": expires, "id": row_id})
    finally:
        conn.close()


@app.route("/api/qa-videos/agent/<int:row_id>", methods=["GET"])
def qa_video_agent_get(row_id: int):
    """Tokened read for an external editing agent (Claude Code): the current
    script plus numbered verse tokens + translations for every referenced
    verse — everything needed to rewrite highlights against the EXACT
    strings the renderer ships, with no local database."""
    token = request.args.get("token", "")
    conn = get_db()
    try:
        rd = _qa_verify_edit_token(conn, row_id, token)
        if not rd:
            return jsonify({"error": "invalid or expired token"}), 403
        try:
            script = json.loads(rd["script_json"] or "{}")
        except Exception:
            return jsonify({"error": "stored script unreadable"}), 500
        # Verse context: anchor + every ref in beats (plus cited refs the
        # original Q&A carried, so the agent may swap cross-references).
        import qa_video_script as _qs
        refs = []
        for b in script.get("beats", []):
            ref = (b.get("verse") or {}).get("ref")
            if ref:
                refs.append(ref)
        qa_row = conn.execute(
            "SELECT generation_meta FROM assistant_conversations WHERE id=?",
            (rd["qa_id"],),
        ).fetchone()
        if qa_row and qa_row["generation_meta"]:
            try:
                refs += list(json.loads(qa_row["generation_meta"]).get("cited_refs") or [])
            except Exception:
                pass
        ctx = _qs.build_context(conn, rd["anchor_ref"], refs)
        return jsonify({
            "id": rd["id"],
            "qa_id": rd["qa_id"],
            "anchor_ref": rd["anchor_ref"],
            "status": rd["status"],
            "title": rd["title"],
            "script": script,
            "verses": ctx["verses"],
            # The consolidator: exegesis, pre-Islamic poetry comparisons,
            # root lexicon, cognates, departure notes — so the editing agent
            # can draw on the most powerful material without any local DB.
            "enrichment": _qs.build_enrichment(conn, rd["anchor_ref"]),
            "rules": {
                "max_duration_sec": 125,
                "highlight_words_ar": "EXACT tokens from verses[].tokens, verbatim",
                "highlight_phrase_en": "verbatim substring of that verse's translation",
                "no_post_quranic_terms": True,
                "dynamic_beats": {
                    "root": "root on its own slide; root.arabic must be a root of a shown verse",
                    "poetry": "pre-Islamic bayt slide; poetry.arabic must be verbatim from enrichment (corpus-verified)",
                    "contrast": "verses: [two entries like verse beats] shown on screen together",
                },
            },
        })
    finally:
        conn.close()


@app.route("/api/qa-videos/agent/<int:row_id>", methods=["PUT"])
def qa_video_agent_put(row_id: int):
    """Tokened edit for an external agent. Identical gate-checked path as
    the admin inline editor — the token changes WHO may submit, never what
    is allowed through."""
    body = request.get_json(silent=True) or {}
    token = body.pop("token", "") or request.args.get("token", "")
    conn = get_db()
    try:
        rd = _qa_verify_edit_token(conn, row_id, token)
        if not rd:
            return jsonify({"error": "invalid or expired token"}), 403
        result, code = _qa_apply_script_edit(conn, row_id, body)
        return jsonify(result), code
    finally:
        conn.close()


@app.route("/api/admin/video-candidates/<int:cand_id>", methods=["PATCH"])
@admin_required
def admin_video_candidate_patch(cand_id: int):
    """Backlog panel actions: star an idea (loop drafts it next) or kill it
    (recorded so the loop never re-proposes it)."""
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in ("starred", "rejected_score", "proposed"):
        return jsonify({"error": "bad status"}), 400
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM video_candidates WHERE id=?", (cand_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        note = (body.get("reason") or "").strip()[:300]
        conn.execute(
            "UPDATE video_candidates SET status=?, "
            "rationale=COALESCE(NULLIF(?, ''), rationale), "
            "updated_at=datetime('now') WHERE id=?",
            (status, (f"operator: {note}" if note else ""), cand_id))
        conn.commit()
        return jsonify({"ok": True, "id": cand_id, "status": status})
    finally:
        conn.close()


@app.route("/api/admin/studio-lessons/<int:lesson_id>", methods=["PATCH"])
@admin_required
def admin_studio_lesson_patch(lesson_id: int):
    """Operator sovereignty over the learned doctrine: retire a lesson
    that over-generalized, edit one that is half-right, reactivate a
    retired one. Prod is truth for existing lessons' text and status."""
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM studio_lessons WHERE id=?", (lesson_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        sets, vals = [], []
        if body.get("status") in ("active", "retired", "flagged"):
            sets.append("status=?"); vals.append(body["status"])
        if isinstance(body.get("lesson"), str) and body["lesson"].strip():
            sets.append("lesson=?"); vals.append(body["lesson"].strip())
        if not sets:
            return jsonify({"error": "nothing to update"}), 400
        sets.append("updated_at=datetime('now')")
        conn.execute(f"UPDATE studio_lessons SET {', '.join(sets)} WHERE id=?",
                     (*vals, lesson_id))
        conn.commit()
        return jsonify({"ok": True, "id": lesson_id})
    finally:
        conn.close()


@app.route("/api/admin/qa-videos/publish-schedule", methods=["PUT"])
@admin_required
def admin_qa_publish_schedule_save():
    body = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        prefs = _qa_publish_prefs(conn)
        if "enabled" in body:
            prefs["enabled"] = bool(body["enabled"])
        if "days" in body:
            days = body["days"]
            if (not isinstance(days, list)
                    or any(not isinstance(d, int) or d < 0 or d > 6 for d in days)):
                return jsonify({"error": "days must be a list of weekday ints 0-6"}), 400
            prefs["days"] = sorted(set(days))
        if "time" in body:
            if not re.match(r"^\d{2}:\d{2}$", str(body["time"])):
                return jsonify({"error": "time must be 'HH:MM' (UTC)"}), 400
            prefs["time"] = body["time"]
        if "privacy" in body:
            if body["privacy"] not in ("public", "unlisted", "private"):
                return jsonify({"error": "bad privacy"}), 400
            prefs["privacy"] = body["privacy"]
        if "voice_id" in body:
            vid = (body["voice_id"] or "").strip() or None
            if vid:
                row = conn.execute(
                    "SELECT 1 FROM admin_voices WHERE voice_id=?", (vid,)
                ).fetchone()
                if not row:
                    return jsonify({"error": "unknown voice_id"}), 400
            prefs["voice_id"] = vid
        _qa_publish_prefs_save(conn, prefs)
        return jsonify(prefs)
    finally:
        conn.close()


def _qa_upload_to_youtube(conn, row: dict, privacy: str) -> dict:
    """Upload one approved qa_videos row. Returns {ok, video_id|error}.
    Mirrors the educational multipart upload (bounded tuple timeout)."""
    filepath = os.path.join(_qa_videos_dir(), row["filename"])
    if not os.path.isfile(filepath):
        return {"ok": False, "error": f"file missing: {row['filename']}"}

    access_token = _youtube_get_access_token()  # raises RuntimeError on bad creds

    script = {}
    try:
        script = json.loads(row.get("script_json") or "{}")
    except Exception:
        pass
    refs = [row.get("anchor_ref") or ""]
    for b in script.get("beats", []):
        ref = (b.get("verse") or {}).get("ref")
        if ref and ref not in refs:
            refs.append(ref)
    description = (
        f"{row['title']}\n\n"
        f"One verse, one question — read closely with us: {', '.join(r for r in refs if r)}.\n\n"
        "Brought to you by al-nuqta.com — A Root Based Translation of the "
        "Quran. Explore the morphology, etymology, and Semitic cognates "
        "behind every word of the Qur'an at https://al-nuqta.com.\n\n"
        "#Quran #QuranicArabic #Shorts"
    )
    metadata = {
        "snippet": {
            "title": (row["title"] or "One verse, one question")[:95],
            "description": description[:4900],
            "tags": ["Quran", "Quranic Arabic", "Quran translation", "Shorts"],
            "categoryId": "27",  # Education
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    boundary = f"boundary_{uuid.uuid4().hex}"
    parts: list[bytes] = [
        f"--{boundary}\r\n".encode(),
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
        json.dumps(metadata).encode("utf-8"),
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b"Content-Type: video/mp4\r\n\r\n",
    ]
    with open(filepath, "rb") as f:
        parts.append(f.read())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    up_resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos",
        params={"uploadType": "multipart", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        data=b"".join(parts),
        timeout=(10, 120),
    )
    if up_resp.status_code not in (200, 201):
        return {"ok": False, "error": f"upload http {up_resp.status_code}: {up_resp.text[:300]}"}
    vid = (up_resp.json() or {}).get("id")
    if not vid:
        return {"ok": False, "error": "upload ok but no video id in response"}
    return {"ok": True, "video_id": vid}


def _qa_publish_pick(conn):
    """The publish scheduler's video picker, shared with the status
    endpoint so the admin UI shows exactly what the next slot will do.
    Round-robin across series so subscribers get variety: pick the
    series whose last upload is oldest (never-uploaded series first,
    in cycle order), then the oldest approved script within it."""
    _CYCLE = ["poetry", "root", "exegesis", "qa"]
    last_up = {r["source_type"]: r["m"] for r in conn.execute(
        "SELECT source_type, MAX(completed_at) AS m FROM qa_videos "
        "WHERE status='uploaded' GROUP BY source_type").fetchall()}
    stocked = [r["source_type"] for r in conn.execute(
        "SELECT DISTINCT source_type FROM qa_videos WHERE status='approved'"
    ).fetchall()]
    stocked.sort(key=lambda t: (last_up.get(t) or "", _CYCLE.index(t)
                                if t in _CYCLE else 9))
    if not stocked:
        return None
    return conn.execute(
        "SELECT * FROM qa_videos WHERE status='approved' "
        "AND source_type=? ORDER BY id ASC LIMIT 1", (stocked[0],)
    ).fetchone()


def _qa_publish_next_slot(prefs, now):
    """Next datetime (UTC) the publish scheduler will fire, or None when
    disabled / no days configured. Mirrors _qa_publish_tick's gating:
    a day whose slot already fired (last_fired_date) or whose grace
    window has passed no longer counts."""
    from datetime import datetime, timedelta, timezone
    if not prefs.get("enabled"):
        return None
    days = [d for d in (prefs.get("days") or []) if isinstance(d, int) and 0 <= d <= 6]
    if not days:
        return None
    try:
        hh, mm = map(int, str(prefs.get("time") or "16:00").split(":"))
    except Exception:
        hh, mm = 16, 0
    grace = int(prefs.get("grace_minutes") or 120)
    for offset in range(0, 8):
        day = now + timedelta(days=offset)
        if day.weekday() not in days:
            continue
        slot = day.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if offset == 0:
            if prefs.get("last_fired_date") == now.strftime("%Y-%m-%d"):
                continue  # today's slot already consumed
            if now > slot + timedelta(minutes=grace):
                continue  # today's window missed
        return slot
    return None


@app.route("/api/admin/qa-videos/publish-status", methods=["GET"])
@admin_required
def admin_qa_publish_status():
    """Light status payload for the scheduler Overview: what the Shorts
    publish scheduler will do next, queue depth, last upload, health.
    Server-computed via the same picker the scheduler itself uses."""
    from datetime import datetime, timezone
    conn = get_db()
    try:
        _ensure_qa_videos_table(conn)
        prefs = _qa_publish_prefs(conn)
        now = datetime.now(timezone.utc)
        next_slot = _qa_publish_next_slot(prefs, now)
        pick = _qa_publish_pick(conn)
        counts = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM qa_videos GROUP BY status"
        ).fetchall()}
        last = conn.execute(
            "SELECT id, title, source_type, anchor_ref, youtube_video_id, completed_at "
            "FROM qa_videos WHERE status='uploaded' "
            "ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        el = conn.execute(
            "SELECT value FROM admin_preferences WHERE key='elevenlabs_api_key'"
        ).fetchone()
        oauth_failures = _youtube_oauth_failure_count(conn)
        voice_id = _qa_resolve_voice(conn)
        voice_name = None
        if voice_id:
            vrow = conn.execute(
                "SELECT name FROM admin_voices WHERE voice_id=?", (voice_id,)
            ).fetchone()
            voice_name = vrow["name"] if vrow else voice_id
        return jsonify({
            "prefs": {k: prefs.get(k) for k in
                      ("enabled", "days", "time", "grace_minutes", "privacy",
                       "last_fired_date")},
            "server_now": now.isoformat(),
            "next_slot": next_slot.isoformat() if next_slot else None,
            "next_up": ({
                "id": pick["id"], "title": pick["title"],
                "source_type": pick["source_type"],
                "anchor_ref": pick["anchor_ref"],
            } if pick else None),
            "counts": {
                "approved": counts.get("approved", 0),
                "awaiting_review": counts.get("gate_passed", 0),
                "uploaded": counts.get("uploaded", 0),
            },
            "last_upload": ({
                "id": last["id"], "title": last["title"],
                "source_type": last["source_type"],
                "youtube_video_id": last["youtube_video_id"],
                "completed_at": last["completed_at"],
            } if last else None),
            "health": {
                "oauth_failures": oauth_failures,
                "breaker_open": oauth_failures >= OAUTH_CIRCUIT_BREAKER_THRESHOLD,
                "elevenlabs_ok": bool(el and el["value"]),
                "voice_ok": bool(voice_id),
                "voice_name": voice_name,
            },
        })
    finally:
        conn.close()


def _tiktok_asset_sig(video_id: int, exp: int) -> str:
    """Keyed MAC over (video_id, expiry) so a short-lived, unauthenticated
    download link can be handed to the Claude Chrome agent without exposing
    the admin token. blake2b keyed hashing avoids an extra hmac import."""
    msg = f"{video_id}:{exp}".encode()
    return hashlib.blake2b(
        msg, key=app.config["SECRET_KEY"].encode(), digest_size=16
    ).hexdigest()


def _tiktok_asset_path(video_id: int, ttl_hours: int = 8) -> str:
    exp = int(time.time()) + ttl_hours * 3600
    return f"/api/tiktok-asset/{video_id}?exp={exp}&sig={_tiktok_asset_sig(video_id, exp)}"


@app.route("/api/tiktok-asset/<int:video_id>", methods=["GET"])
def tiktok_asset(video_id: int):
    """Short-lived signed .mp4 download for the manual TikTok flow. Public
    but tokened: the signature and expiry are minted only inside the
    admin-authed tiktok-queue response, and only YouTube-published videos
    are ever served (they are public content already)."""
    exp = request.args.get("exp", type=int)
    sig = request.args.get("sig", "")
    if not exp or time.time() > exp:
        return jsonify({"error": "link expired"}), 403
    if not secrets.compare_digest(sig, _tiktok_asset_sig(video_id, exp)):
        return jsonify({"error": "bad signature"}), 403
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT filename, status FROM qa_videos WHERE id=?", (video_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["filename"] or row["status"] != "uploaded":
        return jsonify({"error": "not available"}), 404
    return send_from_directory(
        _qa_videos_dir(), row["filename"], mimetype="video/mp4",
        as_attachment=True, download_name=f"al-nuqta-{video_id}.mp4",
        conditional=True,
    )


def _qa_tiktok_caption(row: dict) -> str:
    """Ready-to-paste TikTok caption for a Studio video. TikTok has no
    approved API integration here, so the operator posts by hand; this
    gives them a consistent caption to copy. Runs through the same
    'no Islamic-adjective' guard the YouTube metadata uses."""
    title = (row.get("title") or "").strip()
    ref = (row.get("anchor_ref") or "").strip()
    head = f"{title} ({ref})" if ref else title
    caption = (
        f"{head}\n\n"
        "Root-by-root Quran analysis at al-nuqta.com\n"
        "#Quran #QuranTranslation #QuranArabic #alnuqta"
    )
    return _strip_islamic_terms(caption).strip()


# TikTok account we mirror to (public profile — no API, manual upload).
_TIKTOK_ACCOUNT_URL = "https://www.tiktok.com/@al_nuqta_com"
_TIKTOK_UPLOAD_URL = "https://www.tiktok.com/upload"


@app.route("/api/admin/qa-videos/tiktok-queue", methods=["GET"])
@admin_required
def admin_qa_tiktok_queue():
    """Manual TikTok mirror queue. A video becomes TikTok-ready once it
    has been published to YouTube (status='uploaded'); the operator posts
    it to TikTok by hand and marks it done. Oldest-first so the mirror
    tracks the same Mon/Wed/Fri cadence as the YouTube publisher."""
    conn = get_db()
    try:
        _ensure_qa_videos_table(conn)
        pending = [dict(r) for r in conn.execute(
            "SELECT id, title, anchor_ref, source_type, youtube_video_id, "
            "       completed_at, (filename IS NOT NULL AND filename != '') AS has_file "
            "FROM qa_videos "
            "WHERE status='uploaded' AND COALESCE(posted_to_tiktok,0)=0 "
            "ORDER BY completed_at ASC, id ASC"
        ).fetchall()]
        for p in pending:
            p["has_file"] = bool(p["has_file"])
            p["caption"] = _qa_tiktok_caption(p)
            # Short-lived signed link so the paste-into-Claude prompt can
            # hand the Chrome agent a fetchable .mp4 without the admin token.
            p["download_url"] = _tiktok_asset_path(p["id"]) if p["has_file"] else None
        posted_count = conn.execute(
            "SELECT COUNT(*) FROM qa_videos WHERE COALESCE(posted_to_tiktok,0)=1"
        ).fetchone()[0]
        last = conn.execute(
            "SELECT title, tiktok_posted_at FROM qa_videos "
            "WHERE COALESCE(posted_to_tiktok,0)=1 AND tiktok_posted_at IS NOT NULL "
            "ORDER BY tiktok_posted_at DESC LIMIT 1"
        ).fetchone()
        return jsonify({
            "pending": pending,
            "counts": {"pending": len(pending), "posted": posted_count},
            "last_posted": (dict(last) if last else None),
            "account_url": _TIKTOK_ACCOUNT_URL,
            "upload_url": _TIKTOK_UPLOAD_URL,
        })
    finally:
        conn.close()


@app.route("/api/admin/qa-videos/<int:row_id>/tiktok-posted", methods=["POST"])
@admin_required
def admin_qa_tiktok_mark(row_id: int):
    """Mark (or unmark, for a mis-click) a video as manually posted to
    TikTok. Only videos already on YouTube are eligible, so the mirror
    can never run ahead of what the operator approved and published."""
    body = request.get_json(silent=True) or {}
    posted = body.get("posted", True)
    conn = get_db()
    try:
        _ensure_qa_videos_table(conn)
        row = conn.execute(
            "SELECT status FROM qa_videos WHERE id=?", (row_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        if posted and row["status"] != "uploaded":
            return jsonify({"error": f"only YouTube-published videos can be mirrored to TikTok (status={row['status']})"}), 409
        if posted:
            conn.execute(
                "UPDATE qa_videos SET posted_to_tiktok=1, "
                "  tiktok_posted_at=datetime('now') WHERE id=?",
                (row_id,),
            )
        else:
            conn.execute(
                "UPDATE qa_videos SET posted_to_tiktok=0, tiktok_posted_at=NULL WHERE id=?",
                (row_id,),
            )
        conn.commit()
        return jsonify({"id": row_id, "posted_to_tiktok": bool(posted)})
    finally:
        conn.close()


def _qa_publish_tick():
    """Publish-only scheduler: on configured days (default Mon/Wed/Fri
    16:00 UTC) upload the OLDEST human-approved video. Never generates,
    never uploads anything not explicitly approved. Skips quietly when
    the OAuth circuit breaker is open."""
    from datetime import datetime, timezone

    conn = get_db()
    try:
        _ensure_qa_videos_table(conn)
        prefs = _qa_publish_prefs(conn)
        if not prefs.get("enabled"):
            return
        now = datetime.now(timezone.utc)
        if now.weekday() not in (prefs.get("days") or []):
            return
        today = now.strftime("%Y-%m-%d")
        if prefs.get("last_fired_date") == today:
            return
        try:
            hh, mm = str(prefs.get("time") or "16:00").split(":")
            slot_min = int(hh) * 60 + int(mm)
        except Exception:
            slot_min = 16 * 60
        now_min = now.hour * 60 + now.minute
        grace = int(prefs.get("grace_minutes") or 120)
        if not (slot_min <= now_min <= slot_min + grace):
            return
        # Respect the OAuth circuit breaker — don't hammer broken creds.
        if _youtube_oauth_failure_count(conn) >= OAUTH_CIRCUIT_BREAKER_THRESHOLD:
            print("[qa-publish] OAuth circuit breaker open — skipping slot")
            return
        row = _qa_publish_pick(conn)
        if not row:
            return
        rd = dict(row)

        # Script-first flow: the human approved the SCRIPT; rendering
        # happens automatically here at publish time (unless the operator
        # already rendered a preview manually). The render runs in its own
        # daemon thread so this 30s scheduler tick never blocks; a later
        # tick inside the same grace window finds the file and uploads.
        if rd.get("rendering"):
            return  # render in flight — check again next tick
        if not rd.get("filename"):
            pref = conn.execute(
                "SELECT value FROM admin_preferences WHERE key='elevenlabs_api_key'"
            ).fetchone()
            elevenlabs_key = pref["value"] if pref and pref["value"] else None
            voice_id = _qa_resolve_voice(conn)
            if not (elevenlabs_key and voice_id):
                print("[qa-publish] cannot auto-render: ElevenLabs key/voice missing")
                return

            def _auto_render(video_row_id=rd["id"], key=elevenlabs_key, voice=voice_id):
                import qa_video_render as _qr
                c = get_db()
                try:
                    print(f"[qa-publish] auto-rendering qa_video {video_row_id} for today's slot")
                    _qr.render_qa_video(c, video_row_id,
                                        elevenlabs_api_key=key, voice_id=voice)
                    print(f"[qa-publish] auto-render {video_row_id} done")
                except Exception as exc:  # error recorded on the row
                    print(f"[qa-publish] auto-render {video_row_id} failed: {exc}")
                finally:
                    c.close()

            threading.Thread(target=_auto_render, daemon=True).start()
            return  # upload happens on a later tick once the file exists

        # Mark the slot consumed BEFORE the upload so a crash can't
        # double-post the same day; a failed upload just waits for the
        # next slot (the row stays approved).
        prefs["last_fired_date"] = today
        _qa_publish_prefs_save(conn, prefs)

        print(f"[qa-publish] uploading qa_video {rd['id']} — {rd['title']!r}")
        try:
            result = _qa_upload_to_youtube(conn, rd, prefs.get("privacy") or "public")
        except RuntimeError as e:  # credential problems
            _youtube_oauth_record_failure(conn, str(e))
            print(f"[qa-publish] upload failed (oauth): {e}")
            return
        if result.get("ok"):
            _youtube_oauth_record_success(conn)
            conn.execute(
                "UPDATE qa_videos SET status='uploaded', uploaded_to_youtube=1, "
                "  youtube_video_id=?, completed_at=datetime('now') WHERE id=?",
                (result["video_id"], rd["id"]),
            )
            conn.commit()
            print(f"[qa-publish] uploaded qa_video {rd['id']} → https://youtu.be/{result['video_id']}")
        else:
            conn.execute(
                "UPDATE qa_videos SET error_message=? WHERE id=?",
                (f"publish: {result.get('error')}"[:1000], rd["id"]),
            )
            conn.commit()
            print(f"[qa-publish] upload failed: {result.get('error')}")
    finally:
        conn.close()


@app.route("/api/admin/youtube-upload-schedule", methods=["PUT"])
@admin_required
def admin_save_youtube_upload_schedule():
    body = request.get_json(silent=True) or {}
    times = body.get("times")
    grace = int(body.get("grace_minutes", 30))
    sanity = bool(body.get("sanity_check_enabled", True))
    enabled = bool(body.get("enabled", False))
    privacy = (body.get("privacy") or "public").lower()

    if not isinstance(times, list):
        return jsonify({"error": "times must be a JSON array of 'HH:MM' strings"}), 400
    if privacy not in ("public", "unlisted", "private"):
        return jsonify({"error": "privacy must be public, unlisted, or private"}), 400
    if not (1 <= grace <= 240):
        return jsonify({"error": "grace_minutes must be between 1 and 240"}), 400

    cleaned: list[str] = []
    for t in times:
        if not isinstance(t, str):
            continue
        s = t.strip()
        m = re.match(r"^(\d{1,2}):(\d{2})$", s)
        if not m:
            return jsonify({"error": f"invalid time format: {t!r} (expected HH:MM)"}), 400
        h, mn = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mn <= 59):
            return jsonify({"error": f"invalid time value: {t}"}), 400
        cleaned.append(f"{h:02d}:{mn:02d}")
    # De-duplicate, sorted
    cleaned = sorted(set(cleaned))

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO youtube_upload_schedule "
            "(id, enabled, times, grace_minutes, sanity_check_enabled, privacy, updated_at) "
            "VALUES (1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(id) DO UPDATE SET "
            "  enabled=excluded.enabled, "
            "  times=excluded.times, "
            "  grace_minutes=excluded.grace_minutes, "
            "  sanity_check_enabled=excluded.sanity_check_enabled, "
            "  privacy=excluded.privacy, "
            "  updated_at=CURRENT_TIMESTAMP",
            (1 if enabled else 0, json.dumps(cleaned), grace,
             1 if sanity else 0, privacy),
        )
        conn.commit()
        return jsonify({
            "enabled": enabled,
            "times": cleaned,
            "grace_minutes": grace,
            "sanity_check_enabled": sanity,
            "privacy": privacy,
        })
    finally:
        conn.close()


@app.route("/api/admin/youtube-upload-runs", methods=["GET"])
@admin_required
def admin_list_youtube_upload_runs():
    """Recent YouTube upload fires. Newest first.

    Also returns the published video's title (when the run successfully
    uploaded) by joining on youtube_video_id against both the
    recitation and educational video tables. youtube_video_id is the
    YouTube-side identifier and is unique across both tables, so the
    COALESCE picks whichever side actually owns the row. Skipped /
    errored runs have a NULL youtube_video_id and therefore no title
    — UI shows the note in that case."""
    limit = min(max(request.args.get("limit", 50, type=int), 1), 500)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT r.*, "
            "       COALESCE(av.youtube_title, ev.youtube_title) AS video_title "
            "FROM youtube_upload_runs r "
            "LEFT JOIN admin_pipeline_videos av ON av.youtube_video_id = r.youtube_video_id "
            "LEFT JOIN educational_videos ev ON ev.youtube_video_id = r.youtube_video_id "
            "ORDER BY r.fired_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/admin/server-time", methods=["GET"])
@admin_required
def admin_server_time():
    """Current server local time, ISO-8601 with offset.

    Used by the Scheduler page so the operator's countdown clock
    reflects what the scheduler is actually using to decide when to
    fire — server local, not browser local. Browser-side ticking
    extrapolates from this anchor, with the offset between server
    epoch and browser epoch captured at fetch time."""
    from datetime import datetime, timezone
    now = datetime.now().astimezone()
    return jsonify({
        "now_iso": now.isoformat(timespec="seconds"),
        "now_epoch_ms": int(now.timestamp() * 1000),
        "tz_offset_minutes": int(now.utcoffset().total_seconds() / 60) if now.utcoffset() else 0,
        "tz_name": now.tzinfo.tzname(now) if now.tzinfo else "UTC",
    })


@app.route("/api/admin/pipeline-videos/<int:video_id>/clear-upload-skip", methods=["POST"])
@admin_required
def admin_clear_upload_skip(video_id):
    """Clear the auto_upload_skipped flag so the YouTube scheduler will
    reconsider this video on its next eligible slot. Useful after prompt
    tuning or if a video was rejected by sanity check you think was wrong.
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM admin_pipeline_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        conn.execute(
            "UPDATE admin_pipeline_videos SET auto_upload_skipped = 0 WHERE id = ?",
            (video_id,),
        )
        conn.commit()
        return jsonify({"id": video_id, "auto_upload_skipped": False})
    finally:
        conn.close()


@app.route(
    "/api/admin/educational/<int:video_id>/clear-upload-skip",
    methods=["POST"],
)
@admin_required
def admin_educational_clear_upload_skip(video_id: int):
    """Clear the auto_upload_skipped flag on an educational_videos row so
    the global YouTube upload scheduler will reconsider it. Mirrors the
    recitation endpoint above; used to re-arm a sanity-rejected
    educational video after prompt tuning or a manual review."""
    if not _EDU_OK:
        return _edu_unavailable()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM educational_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        conn.execute(
            "UPDATE educational_videos SET auto_upload_skipped = 0 WHERE id = ?",
            (video_id,),
        )
        conn.commit()
        return jsonify({"id": video_id, "auto_upload_skipped": False})
    finally:
        conn.close()


@app.route("/api/admin/pipeline-videos/<int:video_id>/uploaded", methods=["PUT"])
@admin_required
def admin_set_video_uploaded(video_id):
    """Toggle the uploaded_to_youtube flag on a pipeline video."""
    body = request.get_json(silent=True) or {}
    flag = 1 if bool(body.get("uploaded", False)) else 0
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM admin_pipeline_videos WHERE id = ?", (video_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        conn.execute(
            "UPDATE admin_pipeline_videos SET uploaded_to_youtube = ? WHERE id = ?",
            (flag, video_id),
        )
        conn.commit()
        return jsonify({"id": video_id, "uploaded_to_youtube": bool(flag)})
    finally:
        conn.close()


# --------------- Admin: YouTube upload ---------------

def _youtube_get_access_token() -> str:
    """Exchange the stored refresh_token for a short-lived access_token.

    Reads client_id, client_secret, and refresh_token from admin_preferences.
    Raises RuntimeError with a user-friendly message if any credential is
    missing or the exchange fails.
    """
    conn = get_db()
    try:
        prefs: dict[str, str] = {}
        for row in conn.execute(
            "SELECT key, value FROM admin_preferences "
            "WHERE key IN ('youtube_client_id','youtube_client_secret','youtube_refresh_token')"
        ).fetchall():
            prefs[row["key"]] = row["value"]
    finally:
        conn.close()

    client_id = (prefs.get("youtube_client_id") or "").strip()
    client_secret = (prefs.get("youtube_client_secret") or "").strip()
    refresh_token = (prefs.get("youtube_refresh_token") or "").strip()
    if not (client_id and client_secret and refresh_token):
        raise RuntimeError(
            "YouTube credentials not configured. "
            "Set Client ID, Client Secret, and Refresh Token in Admin Settings."
        )

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    if resp.status_code != 200:
        # Build a useful error. Google's `error_description` is often
        # the unhelpful literal string "Bad Request" for invalid_grant —
        # the `error` field carries the actual diagnostic code. Prefer
        # the code, and turn known codes into concrete remediation
        # instructions for the operator (the prior message was
        # 'OAuth token exchange failed: Bad Request', which gave the
        # operator no idea what to fix).
        try:
            body = resp.json()
            err_code = (body.get("error") or "").strip()
            err_desc = (body.get("error_description") or "").strip()
        except Exception:
            err_code = ""
            err_desc = (resp.text or "")[:300]

        # Bump the consecutive-failure counter so the upload-tick
        # circuit breaker can stop hammering the same broken creds.
        try:
            _conn_cb = get_db()
            _youtube_oauth_record_failure(
                _conn_cb,
                f"{err_code or 'HTTP ' + str(resp.status_code)}: {err_desc[:200]}",
            )
        finally:
            try: _conn_cb.close()
            except Exception: pass

        REMEDIATIONS = {
            "invalid_grant": (
                "Google rejected the refresh token (invalid_grant). The "
                "stored token is no longer valid. Common causes: (1) the "
                "OAuth consent screen is still in 'Testing' status in "
                "Google Cloud Console — refresh tokens expire after 7 "
                "days in that mode; publish the app to fix permanently. "
                "(2) The client secret was regenerated, which invalidates "
                "all refresh tokens. (3) The Google account revoked access "
                "at myaccount.google.com/permissions. "
                "FIX: re-run the OAuth flow and paste the new refresh "
                "token at Admin → Settings → YouTube."
            ),
            "invalid_client": (
                "Google rejected the client credentials (invalid_client). "
                "The Client ID or Client Secret is wrong. Re-copy both "
                "from Google Cloud Console → Credentials → OAuth 2.0 "
                "Client IDs at Admin → Settings → YouTube."
            ),
            "unauthorized_client": (
                "OAuth client is not authorized for this grant type "
                "(unauthorized_client). Likely the OAuth client was "
                "created as the wrong type (e.g. 'Desktop' vs 'Web "
                "application'). Recreate the OAuth client and reconnect."
            ),
        }
        if err_code in REMEDIATIONS:
            raise RuntimeError(
                f"OAuth token exchange failed ({err_code}): {REMEDIATIONS[err_code]}"
            )
        # Unknown error code — surface as much detail as we have.
        detail = err_desc or err_code or resp.text[:200] or f"HTTP {resp.status_code}"
        raise RuntimeError(
            f"OAuth token exchange failed ({err_code or 'HTTP ' + str(resp.status_code)}): {detail}"
        )
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("OAuth response missing access_token")
    # Successful token fetch — clear the circuit breaker so the
    # upload tick resumes on the next slot.
    try:
        _conn_ok = get_db()
        _youtube_oauth_record_success(_conn_ok)
    finally:
        try: _conn_ok.close()
        except Exception: pass
    return token


def _perform_youtube_upload(
    video_id: int,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    privacy: str = "public",
) -> dict:
    """Core upload logic shared by the HTTP endpoint and the YouTube upload
    scheduler. Reads the video row, uploads via YouTube Data API v3, persists
    the outcome.

    Returns a dict with one of:
      {"ok": True, "video_id": ..., "youtube_video_id": "...", "youtube_url": "...", "privacy": "..."}
      {"ok": False, "error": "...", "status": 400|404|502}
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM admin_pipeline_videos WHERE id = ? AND status = 'complete'",
            (video_id,),
        ).fetchone()
        if not row or not row["filename"]:
            return {"ok": False, "error": "Video not found or not complete", "status": 404}
        filepath = os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])
        if not os.path.isfile(filepath):
            return {"ok": False, "error": "Video file missing on disk", "status": 404}

        # Audio-stream guard — same defense as the educational upload
        # helper. Refuse to publish a silent video (ElevenLabs credits
        # exhausted is the most common cause).
        try:
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0",
                    filepath,
                ],
                capture_output=True, text=True, timeout=30,
            )
            audio_streams = [
                line for line in (probe.stdout or "").splitlines()
                if line.strip() == "audio"
            ]
            if not audio_streams:
                return {
                    "ok": False,
                    "error": (
                        f"Refusing to upload {row['filename']} — the mp4 has "
                        f"no audio stream. This usually means TTS failed "
                        f"during render (e.g. ElevenLabs credits exhausted). "
                        f"Re-render the row first."
                    ),
                    "status": 409,
                }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"[recitation-upload] audio-stream check skipped: {e}")

        # Resolve metadata: caller overrides > stored columns > generic
        # Quran-themed fallback. When Ollama is down (or hasn't run yet)
        # the stored youtube_* columns are empty; we still want the
        # video to publish with a sensible title/description rather
        # than "Pipeline video 47" or a blank field.
        final_title = (title or row["youtube_title"] or _DEFAULT_YT_TITLE).strip()[:100]
        final_description = (
            description or row["youtube_description"] or _DEFAULT_YT_DESCRIPTION
        ).strip()[:5000]

        if tags is None:
            try:
                tags_in = json.loads(row["youtube_tags"] or "[]")
            except (json.JSONDecodeError, TypeError):
                tags_in = []
        else:
            tags_in = tags
        if not tags_in:
            tags_in = list(_DEFAULT_YT_TAGS)

        final_tags: list[str] = []
        for t in tags_in or []:
            if not isinstance(t, str):
                continue
            cleaned = t.strip().lstrip("#")[:100]
            if cleaned and cleaned not in final_tags:
                final_tags.append(cleaned)
            if len(final_tags) >= 15:
                break
        while final_tags and len(",".join(final_tags)) > 500:
            final_tags.pop()

        # Quran-only vocabulary guard — strip "Islamic" anywhere it
        # might have leaked through, regardless of source. The Quran
        # uses "Islam" but never the post-Quranic adjective.
        final_title = _ISLAMIC_RE.sub("", final_title).strip() or _DEFAULT_YT_TITLE
        final_description = _strip_islamic_terms(final_description) or _DEFAULT_YT_DESCRIPTION
        final_tags = _filter_islamic_tags(final_tags) or list(_DEFAULT_YT_TAGS)

        final_privacy = (privacy or "public").lower()
        if final_privacy not in ("public", "unlisted", "private"):
            final_privacy = "public"
    finally:
        conn.close()

    try:
        access_token = _youtube_get_access_token()
    except RuntimeError as e:
        return {"ok": False, "error": str(e), "status": 400}

    metadata = {
        "snippet": {
            "title": final_title,
            "description": final_description,
            "tags": final_tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": final_privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    boundary = f"boundary_{uuid.uuid4().hex}"
    body_parts: list[bytes] = []
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b"Content-Type: application/json; charset=UTF-8\r\n\r\n")
    body_parts.append(json.dumps(metadata).encode("utf-8"))
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b"Content-Type: video/mp4\r\n\r\n")
    with open(filepath, "rb") as f:
        body_parts.append(f.read())
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode())
    upload_body = b"".join(body_parts)

    try:
        up_resp = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos",
            params={"uploadType": "multipart", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            data=upload_body,
            # (connect, per-socket-op) — a flat 600 let a stalled Google
            # endpoint pin the calling thread ~10 min; 120s per op still
            # accommodates large multipart bodies making progress.
            timeout=(10, 120),
        )
    except requests.RequestException as e:
        return {"ok": False, "error": f"Upload request failed: {e}", "status": 502}

    if up_resp.status_code not in (200, 201):
        try:
            err_body = up_resp.json()
            err = err_body.get("error", {}).get("message") or str(err_body)[:500]
        except Exception:
            err = up_resp.text[:500]
        return {
            "ok": False,
            "error": f"YouTube upload failed ({up_resp.status_code}): {err}",
            "status": 502,
        }

    yt_video_id = up_resp.json().get("id")

    conn = get_db()
    try:
        conn.execute(
            "UPDATE admin_pipeline_videos SET "
            "  uploaded_to_youtube = 1, "
            "  youtube_video_id = ?, "
            "  youtube_title = ?, "
            "  youtube_description = ?, "
            "  youtube_tags = ? "
            "WHERE id = ?",
            (yt_video_id, final_title, final_description,
             json.dumps(final_tags) if final_tags else None, video_id),
        )
        conn.commit()
    finally:
        conn.close()

    # Add to a YouTube playlist if the admin has configured a default
    # one in admin preferences. Failure is logged but doesn't fail the
    # upload — the video is already public on YouTube; playlist
    # placement is a nice-to-have we can retry later.
    playlist_note = None
    try:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = ?",
                ("youtube_playlist_default",),
            ).fetchone()
            playlist_id = (row["value"] if row and row["value"] else "").strip()
        finally:
            conn.close()
        if playlist_id and yt_video_id:
            ok, msg = _youtube_add_to_playlist(access_token, yt_video_id, playlist_id)
            playlist_note = (
                f"Added to playlist {playlist_id}" if ok
                else f"Playlist add failed: {msg}"
            )
    except Exception as e:
        playlist_note = f"Playlist add error: {e}"

    return {
        "ok": True,
        "video_id": video_id,
        "youtube_video_id": yt_video_id,
        "youtube_url": f"https://youtube.com/watch?v={yt_video_id}" if yt_video_id else None,
        "privacy": final_privacy,
        "playlist_note": playlist_note,
    }


def _youtube_add_to_playlist(
    access_token: str, video_id: str, playlist_id: str,
) -> tuple[bool, str]:
    """POST playlistItems.insert. Returns (ok, message).
    On 200/201 returns (True, ""); on 409 (already in playlist)
    returns (True, "already in playlist") since the desired end
    state is satisfied. All other errors return False."""
    if not video_id or not playlist_id:
        return False, "missing video_id or playlist_id"
    try:
        resp = requests.post(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            params={"part": "snippet"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
            timeout=20,
        )
    except requests.RequestException as e:
        return False, f"request failed: {e}"
    if resp.status_code in (200, 201):
        return True, ""
    # 409 conflict happens when the video is already in the playlist —
    # treat as success since the post-condition holds.
    if resp.status_code == 409:
        return True, "already in playlist"
    try:
        msg = resp.json().get("error", {}).get("message") or resp.text[:200]
    except Exception:
        msg = resp.text[:200]
    return False, f"HTTP {resp.status_code}: {msg}"


@app.route("/api/admin/pipeline-videos/<int:video_id>/upload", methods=["POST"])
@admin_required
def admin_upload_pipeline_video_to_youtube(video_id):
    """Upload a completed pipeline video to YouTube via the Data API v3.

    Body (all optional — falls back to stored values on the video row):
      { "title": "...", "description": "...", "tags": [...],
        "privacy": "public" | "unlisted" | "private" }
    """
    body = request.get_json(silent=True) or {}
    result = _perform_youtube_upload(
        video_id,
        title=body.get("title"),
        description=body.get("description"),
        tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
        privacy=body.get("privacy") or "public",
    )
    if not result["ok"]:
        return jsonify({"error": result["error"]}), result.get("status", 500)
    return jsonify({
        "video_id": result["video_id"],
        "youtube_video_id": result["youtube_video_id"],
        "youtube_url": result["youtube_url"],
        "privacy": result["privacy"],
    })


# =========================================================================
# TikTok Content Posting API integration (minimal, sandbox-ready)
# -------------------------------------------------------------------------
# Scope for this build: manual upload only. No scheduler, no auto-captions,
# no audit log — those come after the TikTok app is approved by reviewers.
#
# Flow:
#   1. Admin clicks "Connect TikTok" → backend generates PKCE verifier +
#      CSRF state, persists them in admin_preferences, redirects to the
#      TikTok OAuth authorize endpoint.
#   2. TikTok redirects back to /admin/tiktok/callback?code=...&state=...
#   3. Backend validates state, swaps code for access_token + refresh_token
#      (30-day refresh, 24-hour access), persists to admin_preferences.
#   4. Admin picks a completed pipeline video, adds a caption, clicks
#      "Post to TikTok". Backend uses the Content Posting FILE_UPLOAD flow:
#      init → PUT bytes → poll status.
#   5. Video uploads to the admin's TikTok as SELF_ONLY (sandbox/unapproved
#      apps cannot publish publicly — this is a TikTok platform limit).
# =========================================================================

TIKTOK_OAUTH_AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_OAUTH_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
TIKTOK_UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_UPLOAD_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
TIKTOK_REDIRECT_URI = "https://al-nuqta.com/admin/tiktok/callback"
TIKTOK_SCOPES = "user.info.basic,video.upload,video.publish"


def _ensure_tiktok_tables():
    """Add TikTok-related columns to admin_pipeline_videos (idempotent)."""
    conn = get_db()
    try:
        for alter in (
            "ALTER TABLE admin_pipeline_videos ADD COLUMN uploaded_to_tiktok INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE admin_pipeline_videos ADD COLUMN tiktok_video_id TEXT",
            "ALTER TABLE admin_pipeline_videos ADD COLUMN tiktok_caption TEXT",
        ):
            try:
                conn.execute(alter)
                conn.commit()
            except Exception:
                pass
    finally:
        conn.close()


try:
    _ensure_tiktok_tables()
except Exception as e:
    print(f"WARNING: tiktok tables setup failed: {e}")


def _tiktok_pkce_pair() -> tuple[str, str]:
    """Generate (code_verifier, code_challenge) for PKCE S256."""
    import base64
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _tiktok_read_prefs(keys: list[str]) -> dict[str, str]:
    conn = get_db()
    try:
        placeholders = ",".join(["?"] * len(keys))
        rows = conn.execute(
            f"SELECT key, value FROM admin_preferences WHERE key IN ({placeholders})",
            keys,
        ).fetchall()
        return {r["key"]: (r["value"] or "") for r in rows}
    finally:
        conn.close()


def _tiktok_write_prefs(updates: dict[str, str | None]):
    conn = get_db()
    try:
        for k, v in updates.items():
            if v is None:
                conn.execute("DELETE FROM admin_preferences WHERE key = ?", (k,))
            else:
                conn.execute(
                    "INSERT OR REPLACE INTO admin_preferences (key, value, updated_at) "
                    "VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (k, str(v)),
                )
        conn.commit()
    finally:
        conn.close()


def _tiktok_get_access_token() -> str:
    """Return a valid access_token, refreshing via refresh_token if expired.

    Raises RuntimeError with a user-friendly message if credentials are
    missing or the refresh call fails.
    """
    prefs = _tiktok_read_prefs([
        "tiktok_client_key",
        "tiktok_client_secret",
        "tiktok_access_token",
        "tiktok_refresh_token",
        "tiktok_access_token_expires_at",
    ])
    client_key = prefs.get("tiktok_client_key", "").strip()
    client_secret = prefs.get("tiktok_client_secret", "").strip()
    access_token = prefs.get("tiktok_access_token", "").strip()
    refresh_token = prefs.get("tiktok_refresh_token", "").strip()
    expires_at_s = prefs.get("tiktok_access_token_expires_at", "").strip()

    if not (client_key and client_secret and refresh_token):
        raise RuntimeError(
            "TikTok not connected. Click Connect TikTok in Admin Settings to authorize."
        )

    # If access_token still valid for >60s, use it.
    if access_token and expires_at_s:
        try:
            from datetime import datetime as _dt
            exp = _dt.fromisoformat(expires_at_s.replace("Z", "+00:00"))
            if (exp - datetime.now(timezone.utc)).total_seconds() > 60:
                return access_token
        except Exception:
            pass

    # Refresh
    resp = requests.post(
        TIKTOK_OAUTH_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"TikTok token refresh failed ({resp.status_code}): {resp.text[:300]}"
        )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok refresh returned no access_token: {str(data)[:300]}")

    new_access = data["access_token"]
    new_refresh = data.get("refresh_token", refresh_token)
    expires_in = int(data.get("expires_in", 86400))  # default 24h
    new_expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    _tiktok_write_prefs({
        "tiktok_access_token": new_access,
        "tiktok_refresh_token": new_refresh,
        "tiktok_access_token_expires_at": new_expires_at,
    })
    return new_access


@app.route("/api/admin/tiktok/status", methods=["GET"])
@admin_required
def admin_tiktok_status():
    """Summary of TikTok connection state for the admin UI."""
    prefs = _tiktok_read_prefs([
        "tiktok_client_key",
        "tiktok_client_secret",
        "tiktok_refresh_token",
        "tiktok_refresh_token_saved_at",
        "tiktok_open_id",
    ])
    return jsonify({
        "has_client_key": bool(prefs.get("tiktok_client_key")),
        "has_client_secret": bool(prefs.get("tiktok_client_secret")),
        "connected": bool(prefs.get("tiktok_refresh_token")),
        "open_id": prefs.get("tiktok_open_id") or None,
        "connected_at": prefs.get("tiktok_refresh_token_saved_at") or None,
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "scopes": TIKTOK_SCOPES,
    })


@app.route("/api/admin/tiktok/auth-start", methods=["POST"])
@admin_required
def admin_tiktok_auth_start():
    """Return the TikTok authorize URL the admin should open in a new tab.

    Generates and persists a PKCE verifier + CSRF state; the callback route
    validates the returned state before exchanging the code.
    """
    prefs = _tiktok_read_prefs(["tiktok_client_key"])
    client_key = (prefs.get("tiktok_client_key") or "").strip()
    if not client_key:
        return jsonify({"error": "Set tiktok_client_key in Admin Settings first."}), 400

    verifier, challenge = _tiktok_pkce_pair()
    state = secrets.token_urlsafe(32)
    _tiktok_write_prefs({
        "tiktok_oauth_state": state,
        "tiktok_oauth_verifier": verifier,
        "tiktok_oauth_started_at": datetime.now(timezone.utc).isoformat(),
    })

    from urllib.parse import urlencode
    authorize_url = TIKTOK_OAUTH_AUTHORIZE_URL + "?" + urlencode({
        "client_key": client_key,
        "response_type": "code",
        "scope": TIKTOK_SCOPES,
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    return jsonify({"authorize_url": authorize_url})


@app.route("/admin/tiktok/callback", methods=["GET"])
def tiktok_oauth_callback():
    """Public endpoint — TikTok redirects here with ?code=...&state=... after
    the user authorizes. We validate state, swap code for tokens, persist,
    then redirect back to /admin/settings."""
    code = request.args.get("code", "").strip()
    state = request.args.get("state", "").strip()
    error = request.args.get("error", "").strip()
    error_description = request.args.get("error_description", "").strip()

    def _redirect_with(msg_key: str, msg_val: str):
        from urllib.parse import quote as _q
        return Response(
            "",
            status=302,
            headers={"Location": f"/admin/settings?tiktok_{msg_key}={_q(msg_val)}"},
        )

    if error:
        return _redirect_with("error", error_description or error)
    if not code or not state:
        return _redirect_with("error", "missing code or state parameter")

    prefs = _tiktok_read_prefs([
        "tiktok_client_key",
        "tiktok_client_secret",
        "tiktok_oauth_state",
        "tiktok_oauth_verifier",
    ])
    client_key = (prefs.get("tiktok_client_key") or "").strip()
    client_secret = (prefs.get("tiktok_client_secret") or "").strip()
    saved_state = (prefs.get("tiktok_oauth_state") or "").strip()
    verifier = (prefs.get("tiktok_oauth_verifier") or "").strip()

    if not (client_key and client_secret and saved_state and verifier):
        return _redirect_with("error", "oauth session expired — retry")
    if not secrets.compare_digest(state, saved_state):
        return _redirect_with("error", "state mismatch — possible CSRF; retry")

    try:
        resp = requests.post(
            TIKTOK_OAUTH_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": TIKTOK_REDIRECT_URI,
                "code_verifier": verifier,
            },
            timeout=20,
        )
    except requests.RequestException as e:
        return _redirect_with("error", f"token exchange network error: {e}")

    if resp.status_code != 200:
        return _redirect_with("error", f"token exchange failed ({resp.status_code}): {resp.text[:200]}")

    data = resp.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    open_id = data.get("open_id") or ""
    expires_in = int(data.get("expires_in", 86400))
    if not (access_token and refresh_token):
        return _redirect_with("error", f"token exchange missing tokens: {str(data)[:200]}")

    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()
    _tiktok_write_prefs({
        "tiktok_access_token": access_token,
        "tiktok_refresh_token": refresh_token,
        "tiktok_access_token_expires_at": expires_at,
        "tiktok_open_id": open_id,
        "tiktok_refresh_token_saved_at": now_iso,
        # Clear ephemeral OAuth state
        "tiktok_oauth_state": None,
        "tiktok_oauth_verifier": None,
    })
    return _redirect_with("connected", "1")


@app.route("/api/admin/tiktok/disconnect", methods=["POST"])
@admin_required
def admin_tiktok_disconnect():
    """Revoke tokens at TikTok (best-effort) and clear local credentials."""
    prefs = _tiktok_read_prefs([
        "tiktok_client_key", "tiktok_client_secret", "tiktok_access_token"
    ])
    ck = prefs.get("tiktok_client_key", "").strip()
    cs = prefs.get("tiktok_client_secret", "").strip()
    at = prefs.get("tiktok_access_token", "").strip()
    if ck and cs and at:
        try:
            requests.post(
                TIKTOK_REVOKE_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"client_key": ck, "client_secret": cs, "token": at},
                timeout=10,
            )
        except requests.RequestException:
            pass
    _tiktok_write_prefs({
        "tiktok_access_token": None,
        "tiktok_refresh_token": None,
        "tiktok_access_token_expires_at": None,
        "tiktok_open_id": None,
        "tiktok_refresh_token_saved_at": None,
    })
    return jsonify({"ok": True})


@app.route("/api/admin/pipeline-videos/<int:video_id>/upload-to-tiktok", methods=["POST"])
@admin_required
def admin_upload_pipeline_video_to_tiktok(video_id: int):
    """Upload a completed pipeline video to TikTok via the Content Posting API.

    Body: { "caption": "...", "privacy_level": "SELF_ONLY" }  (privacy optional)

    Sandbox / unapproved apps MUST use SELF_ONLY — the TikTok platform will
    reject PUBLIC_TO_EVERYONE until the Content Posting scope is approved.
    """
    body = request.get_json(silent=True) or {}
    caption = (body.get("caption") or "").strip()[:2200]
    privacy_level = (body.get("privacy_level") or "SELF_ONLY").upper()
    if privacy_level not in ("SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"):
        privacy_level = "SELF_ONLY"

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, filename, youtube_title, youtube_description "
            "FROM admin_pipeline_videos WHERE id = ? AND status = 'complete'",
            (video_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["filename"]:
        return jsonify({"error": "Video not found or not complete"}), 404
    filepath = os.path.join(_GENERATED_VIDEOS_DIR, row["filename"])
    if not os.path.isfile(filepath):
        return jsonify({"error": "Video file missing on disk"}), 404

    # Fall back to YouTube-style metadata if no caption provided.
    # When Ollama is down both youtube_title and youtube_description
    # are empty; the result is a blank TikTok caption. Use the same
    # generic Quran-themed fallback as the YouTube uploader does.
    if not caption:
        caption = (
            (row["youtube_title"] or "").strip()
            + "\n\n"
            + (row["youtube_description"] or "").strip()
        ).strip()[:2200]
    if not caption:
        caption = _DEFAULT_TIKTOK_CAPTION

    try:
        access_token = _tiktok_get_access_token()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400

    video_size = os.path.getsize(filepath)
    # Single-chunk upload (simplest; TikTok allows up to ~50 MB single-chunk).
    init_resp = requests.post(
        TIKTOK_UPLOAD_INIT_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    if init_resp.status_code != 200:
        return jsonify({
            "error": f"TikTok init failed ({init_resp.status_code}): {init_resp.text[:500]}"
        }), 502
    init_data = init_resp.json().get("data", {})
    publish_id = init_data.get("publish_id")
    upload_url = init_data.get("upload_url")
    if not (publish_id and upload_url):
        return jsonify({
            "error": f"TikTok init returned no publish_id/upload_url: {str(init_resp.json())[:500]}"
        }), 502

    # PUT the file bytes to the upload_url.
    with open(filepath, "rb") as f:
        video_bytes = f.read()
    put_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        data=video_bytes,
        # (connect, per-socket-op) — bounds each op instead of letting a
        # stalled TikTok endpoint pin the request thread for 10 minutes.
        timeout=(10, 120),
    )
    if put_resp.status_code not in (200, 201):
        return jsonify({
            "error": f"TikTok upload PUT failed ({put_resp.status_code}): {put_resp.text[:500]}"
        }), 502

    # Poll status until PUBLISH_COMPLETE or FAILED (60s cap).
    final_status = None
    final_note = ""
    tiktok_video_id = None
    for _ in range(30):  # 30 * 2s = 60s
        time.sleep(2)
        try:
            st_resp = requests.post(
                TIKTOK_UPLOAD_STATUS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
                json={"publish_id": publish_id},
                timeout=15,
            )
        except requests.RequestException:
            continue
        if st_resp.status_code != 200:
            continue
        st_data = st_resp.json().get("data", {})
        status = st_data.get("status", "")
        if status == "PUBLISH_COMPLETE":
            final_status = "PUBLISH_COMPLETE"
            pids = st_data.get("publicaly_available_post_id") or st_data.get("publicly_available_post_id")
            if isinstance(pids, list) and pids:
                tiktok_video_id = str(pids[0])
            final_note = "published"
            break
        if status in ("FAILED", "PROCESSING_FAILED", "PUBLISH_FAILED"):
            final_status = status
            final_note = st_data.get("fail_reason", "unknown failure")
            break

    if final_status != "PUBLISH_COMPLETE":
        return jsonify({
            "error": f"TikTok publish did not complete: {final_status or 'timeout'} — {final_note}",
            "publish_id": publish_id,
        }), 502

    conn = get_db()
    try:
        conn.execute(
            "UPDATE admin_pipeline_videos SET "
            "  uploaded_to_tiktok = 1, tiktok_video_id = ?, tiktok_caption = ? "
            "WHERE id = ?",
            (tiktok_video_id, caption, video_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "ok": True,
        "video_id": video_id,
        "tiktok_video_id": tiktok_video_id,
        "publish_id": publish_id,
        "privacy_level": privacy_level,
        "note": "Uploaded. Sandbox apps can only post SELF_ONLY — visible to you only.",
    })


# Metadata-regeneration state (process-local; single-admin use — no locking needed).
# Keyed by video_id. One of:
#   {"status": "running", "started_at": <epoch>}
#   {"status": "done",    "title": "...", "description": "...", "tags": [...]}
#   {"status": "error",   "error": "..."}
_metadata_regen_state: dict[int, dict] = {}


def _regenerate_metadata_task(video_id: int, verse_data: list):
    """Background worker: regenerate metadata and persist, updating
    _metadata_regen_state so the frontend can poll for completion."""
    try:
        title, description, tags = _generate_youtube_metadata(verse_data)
        if not title and not description:
            _metadata_regen_state[video_id] = {
                "status": "error",
                "error": "Metadata generator returned empty result",
            }
            return

        conn = get_db()
        try:
            conn.execute(
                "UPDATE admin_pipeline_videos SET "
                "  youtube_title = ?, youtube_description = ?, youtube_tags = ? "
                "WHERE id = ?",
                (title or None, description or None, json.dumps(tags) if tags else None, video_id),
            )
            conn.commit()
        finally:
            conn.close()

        _metadata_regen_state[video_id] = {
            "status": "done",
            "title": title,
            "description": description,
            "tags": tags,
        }
    except Exception as e:
        _metadata_regen_state[video_id] = {"status": "error", "error": str(e)[:500]}


@app.route("/api/admin/pipeline-videos/<int:video_id>/regenerate-metadata", methods=["POST"])
@admin_required
def admin_regenerate_pipeline_video_metadata(video_id):
    """Start a background regenerate; return immediately with 202.

    The Ollama metadata call can run 1-3 minutes with a thinking-capable
    cloud model, which is longer than a typical proxy's read timeout.
    Running synchronously would return HTML error pages from the proxy
    before the endpoint finishes. Async + polling avoids that entirely.

    Clients should poll GET /regenerate-metadata-status every 2-3s until
    status is 'done' or 'error'.
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT verse_data, status FROM admin_pipeline_videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "Video not found"}), 404
        if row["status"] != "complete":
            return jsonify({"error": "Video must be complete before regenerating metadata"}), 400
        try:
            verse_data = json.loads(row["verse_data"] or "[]")
        except (json.JSONDecodeError, TypeError):
            verse_data = []
    finally:
        conn.close()

    if not verse_data:
        return jsonify({"error": "Video has no verse data to work from"}), 400

    # Already running for this video? Let the existing task finish rather
    # than spawn a duplicate.
    existing = _metadata_regen_state.get(video_id)
    if existing and existing.get("status") == "running":
        return jsonify({"status": "running", "video_id": video_id}), 202

    _metadata_regen_state[video_id] = {"status": "running", "started_at": time.time()}
    t = threading.Thread(
        target=_regenerate_metadata_task,
        args=(video_id, verse_data),
        daemon=True,
    )
    t.start()
    return jsonify({"status": "running", "video_id": video_id}), 202


@app.route("/api/admin/pipeline-videos/<int:video_id>/regenerate-metadata-status", methods=["GET"])
@admin_required
def admin_regenerate_pipeline_video_metadata_status(video_id):
    """Poll the current state of a regenerate-metadata run."""
    state = _metadata_regen_state.get(video_id)
    if not state:
        return jsonify({"status": "idle"})
    resp = dict(state)
    resp["video_id"] = video_id
    # Clean up terminal states once the client has observed them,
    # to avoid the dict growing unbounded.
    if state.get("status") in ("done", "error"):
        _metadata_regen_state.pop(video_id, None)
    return jsonify(resp)


# --------------- Legacy redirect ---------------

@app.before_request
def _redirect_legacy_query_params():
    """301 redirect /?s=X&a=Y to /verse/X:Y in production."""
    if request.path == "/" and request.args.get("s") and request.args.get("a"):
        s = request.args.get("s")
        a = request.args.get("a")
        return redirect(f"/verse/{s}:{a}", code=301)


# --------------- Noscript content for LLM crawlers ---------------

def _grammar_term_slug(term: str) -> str:
    """Convert a grammar term (e.g. 'emphatic lām') to a URL-safe anchor
    slug. Must stay in sync with grammarTermSlug() in frontend/api/quran.ts
    so tooltip deep links resolve correctly against both the client-rendered
    DOM and the server-rendered noscript HTML.
    """
    import unicodedata as _ucd
    s = _ucd.normalize('NFD', term or '')
    s = ''.join(c for c in s if not _ucd.combining(c))
    s = s.lower()
    s = re.sub(r"[^\w\s-]", '', s)
    s = s.strip()
    s = re.sub(r'\s+', '-', s)
    return s


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

    # Reader page: /read/<n> or /read/<n>:<v>
    # The reader's main draw is "the entire surah on one page" — so
    # we render every verse here as static HTML so Googlebot, GPTBot,
    # Claude-Web, and any other crawler that doesn't execute JS sees
    # the full surah text + English translation, with the surah
    # header as the H1. The verse-deep-link variant (/read/2:255)
    # produces the same content; the canonical points at /read/2 so
    # Google indexes a single page per surah.
    m = re.match(r'^/read/(\d+)(?::\d+)?/?$', path)
    if m:
        surah = int(m.group(1))
        if 1 <= surah <= 114:
            conn = get_db()
            try:
                verse_rows = conn.execute(
                    "SELECT verse, text_uthmani FROM verses "
                    "WHERE chapter = ? ORDER BY verse",
                    (surah,),
                ).fetchall()
                if verse_rows:
                    trans_rows = conn.execute(
                        "SELECT verse, translation_text, revised_text "
                        "FROM ai_translations WHERE chapter = ?",
                        (surah,),
                    ).fetchall()
                    trans_by_verse = {
                        r["verse"]: (r["revised_text"] or r["translation_text"] or "")
                        for r in trans_rows
                    }

                    name = _surah_name(surah)
                    arabic_name = _surah_arabic(surah)
                    meaning = _surah_meaning(surah)
                    parts.append(
                        f'<h1>Surah {html.escape(name)}'
                        + (f' &mdash; {html.escape(arabic_name)}' if arabic_name else '')
                        + '</h1>'
                    )
                    header_bits = [f'Surah {surah} of 114']
                    if meaning:
                        header_bits.append(html.escape(meaning))
                    header_bits.append(f'{len(verse_rows)} verses')
                    parts.append(f'<p>{" &middot; ".join(header_bits)}</p>')
                    parts.append(
                        '<p>Read this surah verse by verse with English '
                        'translation. The al-nuqta reader supports optional '
                        'word-by-word display, hover tooltips for surveyed '
                        'roots, personal notes, and saved bookmarks &mdash; '
                        'all stored locally in your browser. For deeper '
                        f'research on any verse, see '
                        f'<a href="/verse/{surah}:1">/verse/{surah}:1</a>.</p>'
                    )

                    # Prev / next surah crumbs
                    nav_bits = []
                    if surah > 1:
                        nav_bits.append(
                            f'<a href="/read/{surah - 1}">&larr; Surah '
                            f'{html.escape(_surah_name(surah - 1))}</a>'
                        )
                    nav_bits.append('<a href="/">All surahs</a>')
                    if surah < 114:
                        nav_bits.append(
                            f'<a href="/read/{surah + 1}">Surah '
                            f'{html.escape(_surah_name(surah + 1))} &rarr;</a>'
                        )
                    parts.append(f'<p>{" &middot; ".join(nav_bits)}</p>')

                    parts.append('<ol>')
                    for r in verse_rows:
                        v = r["verse"]
                        ar = _strip_bismillah(r["text_uthmani"], surah, v)
                        tr = trans_by_verse.get(v, "")
                        parts.append(
                            f'<li id="v{v}" value="{v}">'
                            + (
                                f'<p dir="rtl" lang="ar">{html.escape(ar)}</p>'
                                if ar else ''
                            )
                            + (f'<p>{html.escape(tr)}</p>' if tr else '')
                            + f'<p><a href="/verse/{surah}:{v}">'
                            + f'Research verse {surah}:{v} &rarr;</a></p>'
                            + '</li>'
                        )
                    parts.append('</ol>')
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

    # Grammar glossary: /grammar-glossary — render the full term list as
    # static HTML so crawlers (and LLM bots) can index every definition
    # without running JavaScript. Terms are grouped pedagogically by
    # category (matching the frontend's default view), and each term gets
    # a stable anchor that matches the frontend's slug scheme.
    if re.match(r'^/grammar-glossary/?$', path):
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT term_english, term_arabic, plain_explanation, "
                "       example_sentence, example_translation, category "
                "FROM grammar_terms ORDER BY term_english COLLATE NOCASE"
            ).fetchall()
        finally:
            conn.close()
        parts.append('<h1>Grammar Glossary</h1>')
        parts.append('<p>Arabic grammar terms used across al-nuqta\'s verse-level '
                     'grammar notes, grouped by grammatical function. Each entry '
                     'has a plain-English definition and an Arabic example.</p>')
        # Group by category in display order
        by_cat: dict[str, list] = {c: [] for c in GRAMMAR_CATEGORIES}
        for r in rows:
            by_cat.setdefault(r["category"] or "Other", []).append(r)
        for cat in GRAMMAR_CATEGORIES:
            items = by_cat.get(cat) or []
            if not items:
                continue
            cat_slug = _grammar_term_slug(cat)
            parts.append(f'<h2 id="cat-{cat_slug}">{html.escape(cat)}</h2>')
            parts.append('<dl>')
            for r in items:
                slug = _grammar_term_slug(r["term_english"])
                term_html = html.escape(r["term_english"])
                ar = r["term_arabic"] or ""
                ar_html = (f' <span lang="ar">({html.escape(ar)})</span>' if ar else "")
                parts.append(
                    f'<dt id="{slug}"><a href="#{slug}"><strong>{term_html}</strong></a>{ar_html}</dt>'
                )
                parts.append(f'<dd>{html.escape(r["plain_explanation"] or "")}')
                if r["example_sentence"] or r["example_translation"]:
                    parts.append('<br/>')
                    if r["example_sentence"]:
                        parts.append(
                            f'<em lang="ar">{html.escape(r["example_sentence"])}</em> '
                        )
                    if r["example_translation"]:
                        parts.append(
                            f'&mdash; <em>{html.escape(r["example_translation"])}</em>'
                        )
                parts.append('</dd>')
            parts.append('</dl>')

    # Qur'anic Dictionary: /dictionary — static list of every root that has an
    # approved lexicon entry, grouped alphabetically and linking to its root
    # page (where the definitions render). Lets crawlers/LLM bots discover the
    # whole lexicon without running JavaScript.
    if re.match(r'^/dictionary/?$', path):
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT e.root_buckwalter, e.root_arabic, COUNT(*) AS entries, "
                "(SELECT m.primary_meaning FROM ai_root_meanings m "
                " WHERE m.root_buckwalter = e.root_buckwalter "
                "   AND m.primary_meaning IS NOT NULL AND m.primary_meaning <> '' "
                " ORDER BY m.id LIMIT 1) AS gloss "
                "FROM dictionary_entries e "
                "WHERE e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
                "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> '' "
                "GROUP BY e.root_buckwalter, e.root_arabic ORDER BY e.root_arabic"
            ).fetchall()
        finally:
            conn.close()
        parts.append('<h1>Qur’anic Dictionary</h1>')
        parts.append('<p>Classical Arabic dictionary definitions for every Qur’anic '
                     'root, harmonized into readable English. Select a root to read its '
                     'entries from Lisān al-ʿArab, al-Mufradāt and other '
                     'classical works.</p>')
        cur_letter = None
        for r in rows:
            ar = r["root_arabic"] or ""
            letter = (ar or r["root_buckwalter"] or "?")[0]
            if letter != cur_letter:
                if cur_letter is not None:
                    parts.append('</ul>')
                parts.append(f'<h2 lang="ar">{html.escape(letter)}</h2>')
                parts.append('<ul>')
                cur_letter = letter
            href = "/root/" + quote(r["root_buckwalter"])
            label = html.escape(ar or r["root_buckwalter"])
            gloss = _clean_root_gloss(r["gloss"]) or ""
            suffix = f' &mdash; {html.escape(gloss)}' if gloss else ''
            parts.append(
                f'<li><a href="{href}"><span lang="ar">{label}</span></a>{suffix}</li>'
            )
        if cur_letter is not None:
            parts.append('</ul>')

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


# --------------- External redirects (m4th.com sibling) ---------------
# m4th.com is hosted on the same server; Google indexed several of its
# /report/<TICKER> URLs against al-nuqta.com (probably from a stale
# vhost mapping or a misconfigured canonical at some point). Permanent-
# redirect those paths to m4th.com so:
#   1. SEO consolidates on the right domain.
#   2. Visitors who landed via Google search land on the actual page.
#   3. al-nuqta's crawl budget isn't wasted on 404s for content that
#      lives elsewhere.
#
# Strategy:
#   - Always 301 (permanent), so search engines update their index.
#   - Strip everything after the first path segment after /report/.
#     Operator's examples explicitly say /report/LULU/- → /report/LULU.
#     Trailing junk like /-/growth observed in the Search Console
#     drilldown is treated the same way — collapse to the ticker.
#   - Bare /report and /report/ redirect to m4th.com root.
@app.route("/report")
@app.route("/report/")
def redirect_report_root():
    return redirect("https://m4th.com/", code=301)


@app.route("/report/<path:rest>")
def redirect_report_to_m4th(rest):
    # rest comes in path-decoded by Flask; split on the first slash to
    # isolate the ticker. Defensive: when a request comes in as just
    # "/report//something", rest may start with empty segments.
    parts = [p for p in rest.split("/") if p]
    if not parts:
        return redirect("https://m4th.com/", code=301)
    ticker = parts[0]
    return redirect(f"https://m4th.com/report/{ticker}", code=301)


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

        # Shortcut URLs the user might type by hand. The user doesn't
        # know the canonical separator, so accept any of :, /, . between
        # surah and ayah, and any of -, :, /, . between range endpoints.
        # All of these resolve correctly:
        #   /36          → /read/36
        #   /36:3        → /verse/36:3
        #   /36/3        → /verse/36:3
        #   /36.3        → /verse/36:3
        #   /36:3-6      → /read/36:3-6     (canonical range)
        #   /36/3-6      → /read/36:3-6
        #   /36/3:6      → /read/36:3-6
        #   /36:3/6      → /read/36:3-6
        #   /36/3/6      → /read/36:3-6
        # Validation still applies — invalid surah or ayah falls through
        # to the friendly 404, never an unconditional redirect.
        m = re.match(r"^(\d+)(?:[/:.](\d+)(?:[-/:.](\d+))?)?/?$", path)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 114:
                a = int(m.group(2)) if m.group(2) else None
                b = int(m.group(3)) if m.group(3) else None
                max_a = _surah_max_ayah(n)
                if a is None:
                    return redirect(f"/read/{n}", code=301)
                if 1 <= a <= max_a:
                    if b is None:
                        return redirect(f"/verse/{n}:{a}", code=301)
                    # Clamp the upper bound: /36:32-100 → /read/36:32-83
                    # since the surah ends at 83. Better UX than 404 —
                    # the user clearly meant "from a to the end".
                    end = min(b, max_a)
                    if end > a:
                        return redirect(f"/read/{n}:{a}-{end}", code=301)

        # /verse/<n>:<a>-<b> — a verse page shows exactly one verse, so a
        # range has nowhere to go there. The reader does show ranges, so
        # send it to /read/<n>:<a>-<b> instead of 404'ing. Non-canonical
        # separators are accepted here too, matching the shorthand above.
        # The canonical /verse/<n>:<a> falls through untouched.
        m_verse = re.match(r"^verse/(\d+)[:/.](\d+)(?:[-:/.](\d+))?/?$", path)
        if m_verse:
            n = int(m_verse.group(1))
            a = int(m_verse.group(2))
            b = int(m_verse.group(3)) if m_verse.group(3) else None
            if 1 <= n <= 114 and 1 <= a <= _surah_max_ayah(n):
                end = min(b, _surah_max_ayah(n)) if b is not None else None
                target = f"/read/{n}:{a}-{end}" if end and end > a else f"/verse/{n}:{a}"
                if target.lstrip("/") != path.rstrip("/"):
                    return redirect(target, code=301)

        # /word/<n>:<a> with the word-position segment stripped off (e.g.
        # the user edited it out of the address bar) — a word page needs
        # a position, so send them to the verse it came from instead of 404.
        m_word = re.match(r"^word/(\d+):(\d+)/?$", path)
        if m_word:
            return redirect(f"/verse/{m_word.group(1)}:{m_word.group(2)}", code=301)

        # Read and cache index.html template
        if _index_html_cache is None:
            with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
                _index_html_cache = f.read()

        # Inject SEO meta tags
        req_path = "/" + path if path else "/"

        # Unknown paths: still serve the SPA shell so React can render
        # the friendly NotFound page (verse of the day, recovery links).
        # We return HTTP 404 and tag the page noindex,nofollow so search
        # engines don't index unknown URLs as if they were real pages.
        is_unknown = not _is_known_spa_path(req_path)

        if is_unknown:
            meta_tags = (
                '<meta name="robots" content="noindex, nofollow">'
                '<meta property="og:title" content="Page Not Found | al-nuqta">'
            )
            page_title = "404 — Page Not Found | al-nuqta"
            noscript_html = (
                '<noscript><h1>404 — Page Not Found</h1>'
                '<p>Go to <a href="/">al-nuqta</a></p></noscript>'
            )
        else:
            meta = _get_seo_meta(req_path)
            meta_tags = _build_meta_tags(meta)
            page_title = meta["title"]
            noscript_html = _build_noscript_content(req_path)

        html_doc = _index_html_cache
        html_doc = html_doc.replace("<!-- SEO_META_PLACEHOLDER -->", meta_tags)
        html_doc = html_doc.replace(
            "<title>al-nuqta</title>",
            f"<title>{html.escape(page_title)}</title>",
        )
        # Inject Google Analytics if the admin has set a Measurement ID.
        # Skipped on /admin paths so admin activity isn't counted as user
        # traffic.
        ga_id = _get_google_analytics_id()
        if ga_id and not req_path.startswith("/admin"):
            ga_snippet = _build_ga_snippet(ga_id)
            if ga_snippet:
                html_doc = html_doc.replace("</head>", f"{ga_snippet}</head>", 1)
        if noscript_html:
            html_doc = html_doc.replace(
                '<div id="root"></div>',
                f'<div id="root"></div>\n{noscript_html}',
            )

        return Response(html_doc, mimetype="text/html", status=404 if is_unknown else 200)


if __name__ == "__main__":
    # Only the reloader-spawned child (WERKZEUG_RUN_MAIN=true) runs the
    # scheduler. The parent watcher process stays passive — that keeps one
    # and only one scheduler daemon alive, even across code reloads.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        _start_scheduler_once()
        _start_youtube_stats_thread_once()
    else:
        print("[scheduler] parent watcher — deferring start to reloader child")
    app.run(debug=True, port=5000)
