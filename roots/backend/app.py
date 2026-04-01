"""Flask API for The Quran Explorer."""

import html
import json
import math
import os
import re
import sqlite3
import time
from collections import OrderedDict, defaultdict
from urllib.parse import quote

import requests
from flask import Flask, Response, jsonify, redirect, request, send_from_directory
from flask_cors import CORS

# Bump this when mnemonic images are regenerated to bust browser caches
_MNEMONIC_VERSION = 7

# In Docker, static/ sits next to app.py; in local dev it doesn't exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SERVE_STATIC = os.path.isdir(STATIC_DIR)

app = Flask(
    __name__,
    static_folder=None,  # We handle static files in the catch-all route
)
CORS(app)

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
    conn = sqlite3.connect(DB_PATH)
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

    # Collect concepts and derivatives from all matching roots
    concepts = []
    all_derivs = []
    for root_row in root_rows:
        concepts.append(root_row["concept"])
        derivs = conn.execute(
            "SELECT language, word, displayed_text, concept, meaning "
            "FROM semitic_derivatives WHERE root_id = ? ORDER BY language",
            (root_row["id"],),
        ).fetchall()
        all_derivs.extend(derivs)

    return {
        "semitic_root_id": root_rows[0]["id"],
        "transliteration": root_rows[0]["transliteration"],
        "concept": " / ".join(concepts),
        "derivatives": [
            {
                "language": d["language"],
                "word": d["word"],
                "displayed_text": d["displayed_text"],
                "concept": d["concept"],
                "meaning": d["meaning"],
            }
            for d in all_derivs
        ],
    }


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

        return jsonify({
            "root_arabic": root_arabic,
            "root_buckwalter": root_bw,
            "total_occurrences": total_occurrences,
            "lemmas": lemmas,
            "cognate": cognate,
            "sample_verses": sample_verses,
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
    return False


def _get_seo_meta(path: str) -> dict:
    """Return title, description, og_type for a given URL path."""
    # Extension privacy page: /privacy/extension
    if re.match(r"^/privacy/extension/?$", path):
        return {
            "title": "Quran Research Tool Privacy Policy | The Quran Explorer",
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
            "title": f"Surah {name} ({surah}:{ayah}) | The Quran Explorer",
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
            "title": f"{label} \u2014 {count} Verses | The Quran Explorer",
            "description": desc[:200],
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
            "title": f"{word_label}Word {pos}, {name} {surah}:{ayah} | The Quran Explorer",
            "description": f"Morphology, etymology, and AI analysis of {word_label}(word {pos}) in Surah {name} {surah}:{ayah}{gloss_part}.",
            "og_type": "article",
            "canonical": f"{SITE_URL}/word/{surah}:{ayah}/{pos}",
            "robots": "index, follow",
        }

    # Home
    if path == "/":
        return {
            "title": "The Quran Explorer",
            "description": "Explore the Quran verse by verse \u2014 root words, morphology, Semitic etymology, cross-references, and AI-powered meanings.",
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
        "title": "Page Not Found | The Quran Explorer",
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
        f'<meta property="og:site_name" content="The Quran Explorer" />',
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
                "name": "The Quran Explorer",
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
            "name": "The Quran Explorer",
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
                "name": "The Quran Explorer",
                "url": SITE_URL,
            },
        }
    ld_json = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    tags.append(f'<script type="application/ld+json">{ld_json}</script>')

    return "\n    ".join(tags)


# --------------- robots.txt & sitemap.xml ---------------

@app.route("/robots.txt")
def robots_txt():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /tools/\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
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


# --------------- Legacy redirect ---------------

@app.before_request
def _redirect_legacy_query_params():
    """301 redirect /?s=X&a=Y to /verse/X:Y in production."""
    if request.path == "/" and request.args.get("s") and request.args.get("a"):
        s = request.args.get("s")
        a = request.args.get("a")
        return redirect(f"/verse/{s}:{a}", code=301)


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
                '<title>Page Not Found | The Quran Explorer</title>'
                '</head><body>'
                '<h1>404 — Page Not Found</h1>'
                f'<p>Go to <a href="/">The Quran Explorer</a></p>'
                '</body></html>'
            )
            return Response(not_found_html, mimetype="text/html", status=404)

        meta = _get_seo_meta(req_path)
        meta_tags = _build_meta_tags(meta)

        html_doc = _index_html_cache
        html_doc = html_doc.replace("<!-- SEO_META_PLACEHOLDER -->", meta_tags)
        html_doc = html_doc.replace(
            "<title>The Quran Explorer</title>",
            f"<title>{html.escape(meta['title'])}</title>",
        )

        return Response(html_doc, mimetype="text/html", status=200)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
