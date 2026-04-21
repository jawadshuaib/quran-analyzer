"""
Public API v1 for al-nuqta.com
================================
A clean, versioned REST API that exposes Quranic analysis data.

All endpoints are GET-based and return a consistent JSON envelope:
  { "ok": true, "data": {...}, "meta": {...} }

Register with:  app.register_blueprint(v1_bp)
"""

from __future__ import annotations

import time
from flask import Blueprint, request, jsonify

v1_bp = Blueprint("v1", __name__, url_prefix="/api/v1")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_FIELDS = {
    "morphology", "word-meanings", "roots", "related", "context",
    "ai-translation", "thematic-context", "surah-context", "grammar",
    "grammar-notes", "all",
}


def _envelope(data, meta=None, status=200):
    """Wrap data in a standard response envelope."""
    body = {"ok": True, "data": data, "meta": meta or {}}
    return jsonify(body), status


def _error(code: str, message: str, status: int):
    return jsonify({
        "ok": False,
        "error": {"code": code, "message": message, "status": status},
    }), status


def _verse_exists(conn, surah: int, ayah: int) -> bool:
    """Quick check if a verse exists in the database."""
    row = conn.execute(
        "SELECT 1 FROM verses WHERE chapter = ? AND verse = ? LIMIT 1",
        (surah, ayah),
    ).fetchone()
    return row is not None


def _parse_fields(raw: str | None) -> set[str]:
    if not raw:
        return set()
    fields = {f.strip().lower() for f in raw.split(",") if f.strip()}
    invalid = fields - VALID_FIELDS
    if invalid:
        return {"__invalid__": invalid}  # type: ignore[dict-items]
    if "all" in fields:
        return VALID_FIELDS - {"all"}
    return fields


# ---------------------------------------------------------------------------
# Lazy import from app module — avoids circular import at module level.
# We import at first request instead.
# ---------------------------------------------------------------------------
_app_mod = None


def _app():
    """Lazy-import the main app module so we can call its helpers."""
    global _app_mod
    if _app_mod is None:
        import app as _m
        _app_mod = _m
    return _app_mod


# ---------------------------------------------------------------------------
# 1. VERSES
# ---------------------------------------------------------------------------

@v1_bp.route("/verses/<int:surah>:<int:ayah>")
def get_verse(surah: int, ayah: int):
    """Composite verse endpoint with optional ?fields= parameter."""
    t0 = time.monotonic()
    mod = _app()

    raw_fields = request.args.get("fields")
    fields = _parse_fields(raw_fields)
    if isinstance(fields, dict):  # invalid fields
        inv = ", ".join(sorted(fields.get("__invalid__", set())))
        return _error("INVALID_PARAM", f"Unknown fields: {inv}. Valid: {', '.join(sorted(VALID_FIELDS))}", 400)

    conn = mod.get_db()
    try:
        # Base verse data
        verse = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
        if not verse:
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)

        # Build base response (always included)
        data = _build_verse_base(mod, conn, surah, ayah, verse, include_morphology="morphology" in fields)
        included = ["default"]

        # --- Optional fields ---

        if "morphology" in fields:
            included.append("morphology")
            # morphology is embedded in words already when requested

        if "word-meanings" in fields:
            included.append("word-meanings")
            data["word_meanings"] = _fetch_word_meanings(mod, conn, surah, ayah)

        if "roots" in fields:
            included.append("roots")
            # roots_summary is already in base; enrich with cognates
            # (already done in _build_verse_base)

        if "related" in fields:
            included.append("related")
            limit = request.args.get("related_limit", 10, type=int)
            limit = max(1, min(limit, 25))
            data["related_verses"] = _fetch_related(mod, conn, surah, ayah, limit)

        if "context" in fields:
            included.append("context")
            size = request.args.get("context_size", 3, type=int)
            size = max(1, min(size, 6))
            data["context_verses"] = _fetch_context(mod, conn, surah, ayah, size)

        if "ai-translation" in fields:
            included.append("ai-translation")
            data["ai_translation"] = _fetch_ai_translation(mod, conn, surah, ayah)

        if "thematic-context" in fields:
            included.append("thematic-context")
            data["thematic_context"] = _fetch_thematic_context(mod, conn, surah, ayah)

        if "surah-context" in fields:
            included.append("surah-context")
            data["surah_context"] = _fetch_surah_context(mod, conn, surah, ayah)

        if "grammar" in fields:
            included.append("grammar")
            data["grammar_insights"] = _fetch_grammar(mod, conn, surah, ayah)

        if "grammar-notes" in fields:
            included.append("grammar-notes")
            data["grammar_notes"] = _fetch_grammar_notes(mod, conn, surah, ayah)

        elapsed = round((time.monotonic() - t0) * 1000)
        return _envelope(data, meta={"fields_included": included, "response_time_ms": elapsed})
    finally:
        conn.close()


# --- Standalone sub-resource endpoints ---

@v1_bp.route("/verses/<int:surah>:<int:ayah>/morphology")
def get_verse_morphology(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        verse = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
        if not verse:
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)

        data = _build_verse_base(mod, conn, surah, ayah, verse, include_morphology=True)
        return _envelope({"surah": surah, "ayah": ayah, "words": data["words"]})
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/ai-translation")
def get_verse_ai_translation(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_ai_translation(mod, conn, surah, ayah)
        if not result:
            return _error("NO_DATA", f"No AI translation for {surah}:{ayah}", 404)
        return _envelope(result)
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/word-meanings")
def get_verse_word_meanings(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_word_meanings(mod, conn, surah, ayah)
        return _envelope({"surah": surah, "ayah": ayah, "meanings": result})
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/related")
def get_verse_related(surah: int, ayah: int):
    mod = _app()
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 25))
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        related = _fetch_related(mod, conn, surah, ayah, limit)
        return _envelope({"surah": surah, "ayah": ayah, "related_verses": related})
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/context")
def get_verse_context(surah: int, ayah: int):
    mod = _app()
    size = request.args.get("size", 3, type=int)
    size = max(1, min(size, 6))
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        context = _fetch_context(mod, conn, surah, ayah, size)
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?", (surah,)
        ).fetchone()
        total = row["cnt"] if row else 0
        return _envelope({
            "surah": surah, "ayah": ayah,
            "context_verses": context, "surah_total": total,
        })
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/thematic-context")
def get_verse_thematic(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_thematic_context(mod, conn, surah, ayah)
        if not result:
            return _error("NO_DATA", f"No thematic context for {surah}:{ayah}", 404)
        return _envelope(result)
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/surah-context")
def get_verse_surah_context(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_surah_context(mod, conn, surah, ayah)
        if not result:
            return _error("NO_DATA", f"No surah context for {surah}:{ayah}", 404)
        return _envelope(result)
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/grammar")
def get_verse_grammar(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_grammar(mod, conn, surah, ayah)
        if not result:
            return _error("NO_DATA", f"No grammar insights for {surah}:{ayah}", 404)
        return _envelope(result)
    finally:
        conn.close()


@v1_bp.route("/verses/<int:surah>:<int:ayah>/grammar-notes")
def get_verse_grammar_notes(surah: int, ayah: int):
    mod = _app()
    conn = mod.get_db()
    try:
        if not _verse_exists(conn, surah, ayah):
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)
        result = _fetch_grammar_notes(mod, conn, surah, ayah)
        if not result:
            return _error("NO_DATA", f"No grammar notes for {surah}:{ayah}", 404)
        return _envelope(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. WORDS
# ---------------------------------------------------------------------------

@v1_bp.route("/words/<int:surah>:<int:ayah>/<int:position>")
def get_word(surah: int, ayah: int, position: int):
    mod = _app()
    conn = mod.get_db()
    try:
        # Get verse existence check
        verse_row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
        if not verse_row:
            return _error("VERSE_NOT_FOUND", f"Verse {surah}:{ayah} does not exist", 404)

        # Get morphology for this word
        morph_rows = conn.execute(
            "SELECT form_arabic, form_buckwalter, tag, pos, "
            "       root_buckwalter, root_arabic, lemma_buckwalter, lemma_arabic, "
            "       features_raw, gender, number, person, case_val, voice, mood, "
            "       verb_form, state "
            "FROM morphology WHERE chapter = ? AND verse = ? AND word_pos = ? "
            "ORDER BY segment",
            (surah, ayah, position),
        ).fetchall()
        if not morph_rows:
            return _error("WORD_NOT_FOUND", f"No word at position {position} in {surah}:{ayah}", 404)

        segments = []
        main_root_bw = main_root_ar = main_lemma_bw = main_lemma_ar = None
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
            })
            if row["root_buckwalter"] and not main_root_bw:
                main_root_bw = row["root_buckwalter"]
                main_root_ar = row["root_arabic"]
            if row["lemma_buckwalter"] and not main_lemma_bw:
                main_lemma_bw = row["lemma_buckwalter"]
                main_lemma_ar = row["lemma_arabic"]

        # Conventional gloss
        glosses = mod._fetch_word_glosses(conn, surah, ayah)
        conventional_gloss = glosses.get(position, "")

        # Cognate
        cognate = mod._get_cognate(conn, main_root_bw) if main_root_bw else None

        # AI meaning
        wm_row = conn.execute(
            "SELECT wm.*, c.config_name, c.model_name "
            "FROM ai_word_meanings wm "
            "JOIN ai_translation_configs c ON wm.config_id = c.id "
            "WHERE wm.chapter = ? AND wm.verse = ? AND wm.word_pos = ? "
            "ORDER BY wm.created_at DESC LIMIT 1",
            (surah, ayah, position),
        ).fetchone()

        ai_meaning = None
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

        # Other occurrences of the same lemma
        other_occurrences = []
        total_lemma = 0
        if main_lemma_bw:
            lemma_verses = sorted(mod._lemma_inv.get(main_lemma_bw, set()))
            total_lemma = len(lemma_verses)
            count = 0
            for ch, v in lemma_verses:
                if ch == surah and v == ayah:
                    continue
                if count >= 10:
                    break
                occ_morph = conn.execute(
                    "SELECT DISTINCT word_pos FROM morphology "
                    "WHERE chapter = ? AND verse = ? AND lemma_buckwalter = ?",
                    (ch, v, main_lemma_bw),
                ).fetchall()
                occ_positions = [r["word_pos"] for r in occ_morph]
                ov_row = conn.execute(
                    "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                    (ch, v),
                ).fetchone()
                occ_glosses = mod._fetch_word_glosses(conn, ch, v)
                occ_gloss = occ_glosses.get(occ_positions[0], "") if occ_positions else ""
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
                    "text_uthmani": mod._strip_bismillah(ov_row["text_uthmani"], ch, v) if ov_row else "",
                    "translation": mod._best_translation(conn, ch, v),
                    "conventional_gloss": occ_gloss,
                    "ai_meaning": occ_ai["meaning_short"] if occ_ai else None,
                })
                count += 1

        return _envelope({
            "surah": surah,
            "ayah": ayah,
            "word_pos": position,
            "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], surah, ayah),
            "translation": mod._best_translation(conn, surah, ayah),
            "segments": segments,
            "conventional_gloss": conventional_gloss,
            "root_arabic": main_root_ar,
            "root_buckwalter": main_root_bw,
            "lemma_arabic": main_lemma_ar,
            "lemma_buckwalter": main_lemma_bw,
            "cognate": cognate,
            "ai_meaning": ai_meaning,
            "other_occurrences": other_occurrences,
            "total_lemma_occurrences": total_lemma,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. ROOTS
# ---------------------------------------------------------------------------

@v1_bp.route("/roots/<root_bw>")
def get_root(root_bw: str):
    mod = _app()
    conn = mod.get_db()
    try:
        root_arabic = mod._root_arabic_map.get(root_bw)
        if not root_arabic:
            return _error("ROOT_NOT_FOUND", f"Root '{root_bw}' not found", 404)

        verse_keys = mod._root_inv.get(root_bw, set())
        total_occurrences = len(verse_keys)

        lemma_rows = conn.execute(
            "SELECT DISTINCT lemma_arabic, lemma_buckwalter "
            "FROM morphology "
            "WHERE root_buckwalter = ? AND lemma_arabic IS NOT NULL AND lemma_arabic != '' "
            "ORDER BY lemma_arabic",
            (root_bw,),
        ).fetchall()
        lemmas = [{"lemma_arabic": r["lemma_arabic"], "lemma_buckwalter": r["lemma_buckwalter"]} for r in lemma_rows]

        cognate = mod._get_cognate(conn, root_bw)

        sample_keys = sorted(verse_keys)[:10]
        sample_verses = []
        for ch, v in sample_keys:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            morph_rows = conn.execute(
                "SELECT DISTINCT word_pos FROM morphology "
                "WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                (ch, v, root_bw),
            ).fetchall()
            sample_verses.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": mod._best_translation(conn, ch, v),
                "matched_positions": sorted(r["word_pos"] for r in morph_rows),
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

        return _envelope(result)
    finally:
        conn.close()


@v1_bp.route("/roots/<root_bw>/cognates")
def get_root_cognates(root_bw: str):
    mod = _app()
    conn = mod.get_db()
    try:
        cognate = mod._get_cognate(conn, root_bw)
        if not cognate:
            return _error("NO_DATA", f"No cognate data for root '{root_bw}'", 404)
        return _envelope(cognate)
    finally:
        conn.close()


@v1_bp.route("/roots/<root_bw>/verses")
def get_root_verses(root_bw: str):
    mod = _app()
    conn = mod.get_db()
    try:
        root_arabic = mod._root_arabic_map.get(root_bw)
        if not root_arabic:
            return _error("ROOT_NOT_FOUND", f"Root '{root_bw}' not found", 404)

        verse_keys = sorted(mod._root_inv.get(root_bw, set()))
        total = len(verse_keys)
        limit = request.args.get("limit", 10, type=int)
        limit = max(1, min(limit, 50))
        offset = request.args.get("offset", 0, type=int)
        offset = max(0, offset)

        page = verse_keys[offset:offset + limit]
        verses = []
        for ch, v in page:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            morph_rows = conn.execute(
                "SELECT DISTINCT word_pos FROM morphology "
                "WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                (ch, v, root_bw),
            ).fetchall()
            verses.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": mod._best_translation(conn, ch, v),
                "matched_positions": sorted(r["word_pos"] for r in morph_rows),
            })

        return _envelope(
            {"root_buckwalter": root_bw, "root_arabic": root_arabic, "verses": verses},
            meta={"total": total, "offset": offset, "limit": limit},
        )
    finally:
        conn.close()


@v1_bp.route("/roots/search")
def search_roots():
    """Search roots by Buckwalter, phonetic alias, Arabic text, or English meaning.

    Query params:
        q      — search query (required)
        limit  — max results (default 10, max 30)

    Returns matching roots with Arabic form, meaning, frequency, and a sample verse.
    """
    import sqlite3 as _sqlite3

    mod = _app()
    q = request.args.get("q", "").strip().lower()
    if not q:
        return _error("INVALID_PARAM", "Provide a 'q' query parameter", 400)

    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 30))

    conn = mod.get_db()
    try:
        matched_roots = {}  # root_bw -> score

        # 1. Direct Buckwalter match
        for root_bw in mod._root_arabic_map:
            if root_bw.lower() == q:
                matched_roots[root_bw] = 100
            elif root_bw.lower().startswith(q):
                matched_roots[root_bw] = 80

        # 2. Arabic text -> resolve to root via morphology
        if any('\u0600' <= c <= '\u06FF' for c in q):
            rows = conn.execute(
                "SELECT DISTINCT root_buckwalter FROM morphology "
                "WHERE (arabic_word LIKE ? OR lemma_arabic LIKE ?) "
                "AND root_buckwalter IS NOT NULL AND root_buckwalter != '' LIMIT 20",
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
        except _sqlite3.OperationalError:
            pass

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
            except _sqlite3.OperationalError:
                pass

        # 5. English meaning search
        if len(q) >= 2 and not any('\u0600' <= c <= '\u06FF' for c in q):
            try:
                rows = conn.execute(
                    "SELECT DISTINCT root_buckwalter FROM learning_derivatives "
                    "WHERE LOWER(meaning_gloss) LIKE ? LIMIT 20",
                    (f"%{q}%",),
                ).fetchall()
                for r in rows:
                    rbw = r["root_buckwalter"]
                    if rbw not in matched_roots:
                        matched_roots[rbw] = 50
            except _sqlite3.OperationalError:
                pass

            try:
                rows = conn.execute(
                    "SELECT DISTINCT m.root_buckwalter FROM morphology m "
                    "JOIN word_glosses wg ON m.chapter = wg.chapter AND m.verse = wg.verse AND m.word_pos = wg.word_pos "
                    "WHERE LOWER(wg.translation_en) LIKE ? "
                    "AND m.root_buckwalter IS NOT NULL AND m.root_buckwalter != '' LIMIT 20",
                    (f"%{q}%",),
                ).fetchall()
                for r in rows:
                    rbw = r["root_buckwalter"]
                    if rbw not in matched_roots:
                        matched_roots[rbw] = 45
            except _sqlite3.OperationalError:
                pass

        if not matched_roots:
            return _envelope([], meta={"query": q, "total": 0})

        # Sort by score desc, then frequency desc
        scored = []
        for root_bw, score in matched_roots.items():
            freq = len(mod._root_inv.get(root_bw, set()))
            scored.append((root_bw, score, freq))
        scored.sort(key=lambda x: (-x[1], -x[2]))
        scored = scored[:limit]

        results = []
        for root_bw, _score, freq in scored:
            root_arabic = mod._root_arabic_map.get(root_bw, "")
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
            except _sqlite3.OperationalError:
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
                except _sqlite3.OperationalError:
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
                except _sqlite3.OperationalError:
                    pass

            # Sample verse with Arabic words and matched positions
            sample = None
            verse_keys = sorted(mod._root_inv.get(root_bw, set()))[:1]
            if verse_keys:
                ch, v = verse_keys[0]
                vrow = conn.execute(
                    "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                    (ch, v),
                ).fetchone()
                if vrow:
                    arabic_text = mod._strip_bismillah(vrow["text_uthmani"], ch, v)
                    arabic_words = arabic_text.split()
                    morph_rows = conn.execute(
                        "SELECT DISTINCT word_pos FROM morphology "
                        "WHERE chapter = ? AND verse = ? AND root_buckwalter = ?",
                        (ch, v, root_bw),
                    ).fetchall()
                    matched_positions = [r["word_pos"] for r in morph_rows]
                    max_words = 10
                    if arabic_words and matched_positions:
                        first_match = min(matched_positions) - 1
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
                    adjusted_positions = [p - start for p in matched_positions if start < p <= start + max_words]
                    sample = {
                        "ref": f"{ch}:{v}",
                        "words": windowed_words,
                        "matched_positions": adjusted_positions,
                        "starts_truncated": start > 0,
                        "ends_truncated": end < len(arabic_words),
                        "translation": mod._best_translation(conn, ch, v)[:150],
                    }

            in_curriculum = False
            try:
                c_row = conn.execute(
                    "SELECT 1 FROM learning_curriculum WHERE root_buckwalter = ?",
                    (root_bw,),
                ).fetchone()
                in_curriculum = c_row is not None
            except _sqlite3.OperationalError:
                pass

            results.append({
                "root_buckwalter": root_bw,
                "root_arabic": root_arabic,
                "meaning": meaning,
                "frequency": freq,
                "in_curriculum": in_curriculum,
                "sample_verse": sample,
            })

        return _envelope(results, meta={"query": q, "total": len(results)})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. SURAHS
# ---------------------------------------------------------------------------

@v1_bp.route("/surahs")
def get_surahs():
    mod = _app()
    conn = mod.get_db()
    try:
        rows = conn.execute(
            "SELECT chapter, COUNT(*) as verse_count FROM verses GROUP BY chapter ORDER BY chapter"
        ).fetchall()
        surahs = [
            {"number": r["chapter"], "name": mod._surah_name(r["chapter"]), "verse_count": r["verse_count"]}
            for r in rows
        ]
        return _envelope(surahs, meta={"total": len(surahs)})
    finally:
        conn.close()


@v1_bp.route("/surahs/<int:number>")
def get_surah(number: int):
    mod = _app()
    conn = mod.get_db()
    try:
        rows = conn.execute(
            "SELECT verse FROM verses WHERE chapter = ? ORDER BY verse",
            (number,),
        ).fetchall()
        if not rows:
            return _error("SURAH_NOT_FOUND", f"Surah {number} does not exist", 404)
        return _envelope({
            "number": number,
            "name": mod._surah_name(number),
            "verse_count": len(rows),
            "verses": [r["verse"] for r in rows],
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. SEARCH
# ---------------------------------------------------------------------------

@v1_bp.route("/search")
def search():
    """GET-based search for verses by root/lemma intersection."""
    mod = _app()

    roots = request.args.getlist("root")
    lemmas = request.args.getlist("lemma")
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))
    offset = request.args.get("offset", 0, type=int)
    offset = max(0, offset)

    if not roots and not lemmas:
        return _error("INVALID_PARAM", "Provide at least one 'root' or 'lemma' query parameter", 400)

    resolved = []
    candidate_sets = []

    for root_bw in roots:
        resolved.append({"search_type": "root", "search_key": root_bw})
        if root_bw in mod._root_inv:
            candidate_sets.append(mod._root_inv[root_bw])
        else:
            candidate_sets.append(set())  # unknown term → empty set → empty intersection

    for lemma_bw in lemmas:
        resolved.append({"search_type": "lemma", "search_key": lemma_bw})
        if lemma_bw in mod._lemma_inv:
            candidate_sets.append(mod._lemma_inv[lemma_bw])
        else:
            candidate_sets.append(set())  # unknown term → empty set → empty intersection

    # Intersect
    result_set = candidate_sets[0]
    for cs in candidate_sets[1:]:
        result_set = result_set & cs

    total_found = len(result_set)

    # Score
    scored = []
    for key in result_set:
        score = 0.0
        for r in resolved:
            if r["search_type"] == "lemma":
                score += mod._lemma_idf.get(r["search_key"], 0)
            else:
                score += mod.ROOT_DISCOUNT * mod._root_idf.get(r["search_key"], 0)
        scored.append((score, key))

    scored.sort(key=lambda x: -x[0])
    page = scored[offset:offset + limit]

    conn = mod.get_db()
    try:
        lemma_keys = {r["search_key"] for r in resolved if r["search_type"] == "lemma"}
        root_keys = {r["search_key"] for r in resolved if r["search_type"] == "root"}

        results = []
        for score, (ch, v) in page:
            verse_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            morph_rows = conn.execute(
                "SELECT word_pos, lemma_buckwalter, root_buckwalter "
                "FROM morphology WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchall()
            matched_positions = set()
            for mr in morph_rows:
                if (mr["lemma_buckwalter"] or "") in lemma_keys or (mr["root_buckwalter"] or "") in root_keys:
                    matched_positions.add(mr["word_pos"])

            results.append({
                "surah": ch,
                "ayah": v,
                "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
                "translation": mod._best_translation(conn, ch, v),
                "score": round(score, 3),
                "matched_positions": sorted(matched_positions),
            })

        return _envelope(
            {"terms_used": resolved, "results": results},
            meta={"total_found": total_found, "offset": offset, "limit": limit},
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5b. SEMANTIC SEARCH
# ---------------------------------------------------------------------------

@v1_bp.route("/search/semantic")
def search_semantic():
    """GET /api/v1/search/semantic?q=mercy+and+forgiveness&limit=10

    Find verses by natural-language meaning using pre-computed vector embeddings.
    """
    mod = _app()
    query = request.args.get("q", "").strip()
    if not query:
        return _error("INVALID_PARAM", "Missing required query parameter 'q'", 400)
    if len(query) > 500:
        return _error("INVALID_PARAM", "Query too long (max 500 characters)", 400)
    try:
        limit = min(int(request.args.get("limit", "10")), 50)
    except (ValueError, TypeError):
        return _error("INVALID_PARAM", "limit must be a positive integer", 400)

    results = mod._semantic_search(query, limit=limit)
    if not results:
        return _envelope(
            {"query": query, "results": []},
            meta={"total": 0},
        )

    conn = mod.get_db()
    try:
        out = []
        for ch, v, score, snippet in results:
            row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            text = row["text_uthmani"] if row else ""
            if text:
                text = mod._strip_bismillah(text, ch, v)
            translation = mod._best_translation(conn, ch, v)
            display_text = translation if translation else snippet.split(" | ")[0] if snippet else ""
            out.append({
                "surah": ch,
                "ayah": v,
                "surah_name": mod._surah_name(ch),
                "text_uthmani": text,
                "translation": display_text,
                "score": round(score, 4),
            })
        return _envelope(
            {"query": query, "results": out},
            meta={"total": len(out)},
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. LEARNING
# ---------------------------------------------------------------------------

@v1_bp.route("/learning/curriculum")
def get_learning_curriculum():
    mod = _app()
    conn = mod.get_db()
    try:
        rows = conn.execute(
            "SELECT root_buckwalter, root_arabic, unit_number, unit_theme, "
            "       frequency_rank, theological_importance, derivative_richness, "
            "       anchor_verse_chapter, anchor_verse_verse, related_roots, "
            "       mnemonic_image_path, mnemonic_caption "
            "FROM learning_curriculum ORDER BY unit_number, priority_score DESC"
        ).fetchall()
        if not rows:
            return _envelope({"units": []})

        import json as _json

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
                units[un] = {"unit_number": un, "unit_theme": r["unit_theme"], "roots": []}
            units[un]["roots"].append({
                "root_buckwalter": r["root_buckwalter"],
                "root_arabic": r["root_arabic"],
                "frequency_rank": r["frequency_rank"],
                "theological_importance": r["theological_importance"],
                "derivative_richness": r["derivative_richness"],
                "anchor_verse": f"{r['anchor_verse_chapter']}:{r['anchor_verse_verse']}",
                "related_roots": _json.loads(r["related_roots"]) if r["related_roots"] else [],
                "mnemonic_image_url": (
                    f"/api/v1/learning/roots/{r['root_buckwalter']}/mnemonic?v={_app()._MNEMONIC_VERSION}"
                    if r["mnemonic_image_path"] else None
                ),
                "mnemonic_caption": r["mnemonic_caption"] or None,
                "top_derivatives": top_derivs.get(r["root_buckwalter"], []),
            })

        return _envelope({"units": list(units.values())})
    finally:
        conn.close()


@v1_bp.route("/learning/roots/<root_bw>")
def get_learning_root(root_bw: str):
    """Full teaching package for one root — delegates to main app handler logic."""
    mod = _app()
    conn = mod.get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM learning_curriculum WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        if not cur:
            return _error("ROOT_NOT_FOUND", f"Root '{root_bw}' not in learning curriculum", 404)

        # Re-use the existing handler's response by calling the internal route
        # This is a large, complex handler — we call it via the existing function
        # and wrap the result in our envelope.
        import json as _json

        # Build the same response as the internal endpoint
        derivs = conn.execute(
            "SELECT lemma_buckwalter, lemma_arabic, pos, verb_form, frequency, "
            "       meaning_gloss, semantic_shift, display_order "
            "FROM learning_derivatives WHERE root_buckwalter = ? ORDER BY display_order",
            (root_bw,),
        ).fetchall()

        ctx_rows = conn.execute(
            "SELECT chapter, verse, target_lemma_buckwalter, verse_role, "
            "       teaching_note, display_order "
            "FROM learning_context_verses WHERE root_buckwalter = ? ORDER BY display_order",
            (root_bw,),
        ).fetchall()

        cognate = mod._get_cognate(conn, root_bw)

        related_roots_data = []
        related_bw_list = _json.loads(cur["related_roots"]) if cur["related_roots"] else []
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

        mnemonic_url = (
            f"/api/v1/learning/roots/{root_bw}/mnemonic?v={_app()._MNEMONIC_VERSION}"
            if cur["mnemonic_image_path"] else None
        )

        return _envelope({
            "root_buckwalter": root_bw,
            "root_arabic": cur["root_arabic"],
            "unit_number": cur["unit_number"],
            "unit_theme": cur["unit_theme"],
            "theological_importance": cur["theological_importance"],
            "root_story": cur["root_story"],
            "teaching_notes": cur["teaching_notes"],
            "mnemonic_image_url": mnemonic_url,
            "mnemonic_caption": cur["mnemonic_caption"] if cur["mnemonic_caption"] else None,
            "derivatives": [dict(d) for d in derivs],
            "cognate": cognate,
            "related_roots": related_roots_data,
        })
    finally:
        conn.close()


@v1_bp.route("/learning/roots/<root_bw>/mnemonic")
def get_learning_mnemonic(root_bw: str):
    """Serve the mnemonic image for a root word."""
    import os
    from flask import send_from_directory
    mod = _app()
    conn = mod.get_db()
    try:
        row = conn.execute(
            "SELECT mnemonic_image_path FROM learning_curriculum WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
    finally:
        conn.close()

    if not row or not row["mnemonic_image_path"]:
        return _error("NO_DATA", "No mnemonic image for this root", 404)

    backend_dir = os.path.dirname(os.path.abspath(mod.__file__))
    img_abs = os.path.join(backend_dir, row["mnemonic_image_path"])
    img_dir = os.path.dirname(img_abs)
    img_file = os.path.basename(img_abs)

    if not os.path.isfile(img_abs):
        return _error("NO_DATA", "Image file not found on disk", 404)

    response = send_from_directory(img_dir, img_file, mimetype="image/webp")
    mtime = int(os.path.getmtime(img_abs))
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["ETag"] = f'"{root_bw}-{mtime}"'
    return response


# ---------------------------------------------------------------------------
# Internal data-fetching helpers (used by composite verse endpoint)
# ---------------------------------------------------------------------------

from collections import OrderedDict


def _build_verse_base(mod, conn, surah, ayah, verse_row, include_morphology=False):
    """Build the base verse data dict."""
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

        seg = {
            "form_arabic": row["form_arabic"],
            "form_buckwalter": row["form_buckwalter"],
            "tag": row["tag"],
            "pos": row["pos"],
            "root_arabic": row["root_arabic"],
            "root_buckwalter": row["root_buckwalter"],
            "lemma_arabic": row["lemma_arabic"],
            "lemma_buckwalter": row["lemma_buckwalter"],
            "features": features,
        }
        if include_morphology:
            seg["features_raw"] = row["features_raw"]
        words[wp].append(seg)

        rbw = row["root_buckwalter"]
        if rbw and rbw not in roots_seen:
            roots_seen[rbw] = {
                "root_arabic": row["root_arabic"],
                "root_buckwalter": rbw,
                "occurrences": 0,
            }
        if rbw:
            roots_seen[rbw]["occurrences"] += 1

    glosses = mod._fetch_word_glosses(conn, surah, ayah)
    words_list = [
        {"position": pos, "segments": segs, "translation": glosses.get(pos, "")}
        for pos, segs in words.items()
    ]

    # Enrich roots with cognate data
    roots_list = list(roots_seen.values())
    for root_entry in roots_list:
        root_entry["cognate"] = mod._get_cognate(conn, root_entry["root_buckwalter"])

    # Navigation
    total_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?", (surah,)
    ).fetchone()
    total_in_surah = int(total_row["cnt"]) if total_row and total_row["cnt"] else 0

    previous = None
    if ayah > 1:
        previous = {"surah": surah, "ayah": ayah - 1}
    elif surah > 1:
        prev_total = conn.execute(
            "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?", (surah - 1,)
        ).fetchone()
        prev_cnt = int(prev_total["cnt"]) if prev_total and prev_total["cnt"] else 0
        if prev_cnt > 0:
            previous = {"surah": surah - 1, "ayah": prev_cnt}

    next_ref = None
    if total_in_surah > 0 and ayah < total_in_surah:
        next_ref = {"surah": surah, "ayah": ayah + 1}
    elif surah < 114:
        nxt = conn.execute(
            "SELECT 1 FROM verses WHERE chapter = ? AND verse = 1", (surah + 1,)
        ).fetchone()
        if nxt:
            next_ref = {"surah": surah + 1, "ayah": 1}

    return {
        "surah": surah,
        "ayah": ayah,
        "surah_name": mod._surah_name(surah),
        "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], surah, ayah),
        "translation": mod._best_translation(conn, surah, ayah),
        "words": words_list,
        "roots_summary": roots_list,
        "previous": previous,
        "next": next_ref,
    }


def _fetch_word_meanings(mod, conn, surah, ayah):
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
        entry = {"meaning_short": row["meaning_short"], "has_detail": bool(row["meaning_detailed"])}
        if row["preferred_translation"]:
            entry["preferred_translation"] = row["preferred_translation"]
            entry["preferred_source"] = row["preferred_source"]
        meanings[str(row["word_pos"])] = entry
    return meanings


def _fetch_ai_translation(mod, conn, surah, ayah):
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
        return None
    return {
        "surah": surah,
        "ayah": ayah,
        "translation": row["translation_text"],
        "departure_notes": row["departure_notes"],
        "config_name": row["config_name"],
        "model_name": row["model_name"],
        "created_at": row["created_at"],
    }


def _fetch_related(mod, conn, surah, ayah, limit):
    results = mod._find_related_verses(surah, ayah, limit=limit)
    if not results:
        return []
    related = []
    for containment, _shared_weight, (ch, v), shared_roots in results:
        verse_row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (ch, v),
        ).fetchone()
        shared_info = sorted(
            [
                {
                    "root_arabic": mod._root_arabic_map.get(rbw, ""),
                    "root_buckwalter": rbw,
                    "idf": round(mod._root_idf.get(rbw, 0), 2),
                }
                for rbw in shared_roots
            ],
            key=lambda x: -x["idf"],
        )
        related.append({
            "surah": ch,
            "ayah": v,
            "text_uthmani": mod._strip_bismillah(verse_row["text_uthmani"], ch, v) if verse_row else "",
            "translation": mod._best_translation(conn, ch, v),
            "similarity_score": round(containment, 3),
            "shared_roots": shared_info,
        })
    return related


def _fetch_context(mod, conn, surah, ayah, half_size):
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM verses WHERE chapter = ?", (surah,)
    ).fetchone()
    total = row["cnt"] if row else 0
    if total == 0:
        return []

    before = half_size
    after = half_size
    if ayah <= before:
        before = ayah - 1
        after = (half_size * 2) - before
    elif ayah + after > total:
        after = total - ayah
        before = (half_size * 2) - after

    start = max(1, ayah - before)
    end = min(total, ayah + after)

    rows = conn.execute(
        "SELECT chapter, verse, text_uthmani FROM verses "
        "WHERE chapter = ? AND verse BETWEEN ? AND ? AND verse != ? ORDER BY verse",
        (surah, start, end, ayah),
    ).fetchall()
    return [
        {
            "surah": r["chapter"],
            "ayah": r["verse"],
            "text_uthmani": mod._strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
            "translation": mod._best_translation(conn, r["chapter"], r["verse"]),
        }
        for r in rows
    ]


def _fetch_thematic_context(mod, conn, surah, ayah):
    import json as _json
    row = conn.execute(
        "SELECT tc.passage_start_ayah, tc.passage_end_ayah, "
        "       tc.passage_theme, tc.passage_confidence, "
        "       tc.surah_role_summary, tc.surah_role_confidence, "
        "       tc.neighbor_surah_summary, tc.neighbor_surah_confidence, "
        "       tc.quran_wide_links_json, tc.evidence_json, tc.created_at, "
        "       c.config_name, c.model_name, c.prompt_version "
        "FROM verse_thematic_contexts tc "
        "JOIN thematic_context_configs c ON tc.config_id = c.id "
        "WHERE tc.chapter = ? AND tc.verse = ? "
        "ORDER BY tc.created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if not row:
        return None

    links = _safe_json(row["quran_wide_links_json"], [])
    evidence = _safe_json(row["evidence_json"], {})

    hydrated_links = []
    for item in links:
        if not isinstance(item, dict):
            continue
        refs = item.get("related_verses", [])
        if not isinstance(refs, list):
            refs = []
        hydrated = []
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
            if vr:
                hydrated.append({
                    "surah": ch, "ayah": v,
                    "text_uthmani": mod._strip_bismillah(vr["text_uthmani"], ch, v),
                    "translation": mod._best_translation(conn, ch, v),
                })
        hydrated_links.append({
            "theme": item.get("theme", ""),
            "summary": item.get("summary", ""),
            "confidence": item.get("confidence", 0.0),
            "verses": hydrated,
        })

    return {
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
    }


def _fetch_surah_context(mod, conn, surah, ayah):
    import json as _json
    row = conn.execute(
        "SELECT vc.summary_so_far, vc.current_verse_focus, "
        "       vc.key_verses_json, vc.summary_points_json, vc.lexical_continuity_json, "
        "       vc.signal_score, vc.verifier_report_json, vc.evidence_json, vc.created_at, "
        "       c.config_name, c.model_name, c.prompt_version "
        "FROM verse_surah_contexts vc "
        "JOIN surah_context_configs c ON vc.config_id = c.id "
        "WHERE vc.chapter = ? AND vc.verse = ? "
        "ORDER BY vc.created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if not row:
        return None

    key_items = _safe_json(row["key_verses_json"], [])
    if not isinstance(key_items, list):
        key_items = []
    summary_points = _safe_json(row["summary_points_json"], [])
    if not isinstance(summary_points, list):
        summary_points = []
    lexical = _safe_json(row["lexical_continuity_json"], [])
    if not isinstance(lexical, list):
        lexical = []
    verifier = _safe_json(row["verifier_report_json"], {})
    evidence = _safe_json(row["evidence_json"], {})

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
        if vr:
            hydrated.append({
                "surah": ch, "ayah": v, "why": item.get("why", ""),
                "text_uthmani": mod._strip_bismillah(vr["text_uthmani"], ch, v),
                "translation": mod._best_translation(conn, ch, v),
            })

    return {
        "summary_so_far": (row["summary_so_far"] or "").strip(),
        "current_verse_focus": (row["current_verse_focus"] or "").strip(),
        "key_verses": hydrated,
        "summary_points": summary_points,
        "lexical_continuity": lexical,
        "signal_score": float(row["signal_score"] or 0.0),
        "verifier": verifier,
        "evidence": evidence,
        "model": {
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "prompt_version": row["prompt_version"],
            "created_at": row["created_at"],
        },
    }


def _fetch_grammar(mod, conn, surah, ayah):
    import json as _json
    row = conn.execute(
        "SELECT gi.overview_text, gi.insights_json, gi.signal_score, gi.verifier_report_json, "
        "       gi.evidence_json, gi.created_at, gi.generation_version, gi.insights_v7_json, "
        "       gi.quality_json, gi.overall_confidence, gi.model_confidence_raw, gi.display_json, "
        "       c.config_name, c.model_name, c.prompt_version "
        "FROM verse_grammar_insights gi "
        "JOIN grammar_insight_configs c ON gi.config_id = c.id "
        "WHERE gi.chapter = ? AND gi.verse = ? "
        "ORDER BY gi.created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if not row:
        return None

    return {
        "overview": (row["overview_text"] or "").strip(),
        "insights": _safe_json(row["insights_json"], []),
        "signal_score": float(row["signal_score"] or 0.0),
        "generation_version": row["generation_version"] or "v6",
        "insights_v7": _safe_json(row["insights_v7_json"], []),
        "quality": _safe_json(row["quality_json"], {}),
        "overall_confidence": float(row["overall_confidence"] or 0.0),
        "model_confidence_raw": float(row["model_confidence_raw"] or 0.0),
        "display": _safe_json(row["display_json"], {}),
        "verifier": _safe_json(row["verifier_report_json"], {}),
        "evidence": _safe_json(row["evidence_json"], {}),
        "model": {
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "prompt_version": row["prompt_version"],
            "created_at": row["created_at"],
        },
    }


def _fetch_grammar_notes(mod, conn, surah, ayah):
    """Return the prose grammar commentary for a verse plus its term glossary.

    The response contains:
      - notes_markdown: plain prose with [[term]] markers wrapping technical
        grammar terms (consumers that don't want the markers can strip them
        with a simple regex /\\[\\[([^\\]]+)\\]\\]/ → $1)
      - terms: a dict keyed by lowercased term_english, each value carrying
        term_english, term_arabic (may be null), plain_explanation,
        example_sentence (may be null), example_translation (may be null)

    Returns None if no notes exist for this verse.
    """
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
        return None

    term_names = _safe_json(row["referenced_terms"], [])
    terms_map: dict = {}
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
            terms_map[tr["term_english"].lower()] = {
                "term_english": tr["term_english"],
                "term_arabic": tr["term_arabic"],
                "plain_explanation": tr["plain_explanation"],
                "example_sentence": tr["example_sentence"],
                "example_translation": tr["example_translation"],
            }

    return {
        "notes_markdown": row["notes_markdown"],
        "terms": terms_map,
        "model": {
            "config_name": row["config_name"],
            "model_name": row["model_name"],
            "prompt_version": row["prompt_version"],
            "created_at": row["created_at"],
        },
    }


def _safe_json(text, default):
    """Parse JSON text, returning default on failure."""
    if not text:
        return default
    try:
        import json
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
