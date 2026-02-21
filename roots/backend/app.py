"""Flask API for the Quran Root Word Analyzer."""

import math
import os
import sqlite3
from collections import OrderedDict, defaultdict

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")


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

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "text_uthmani": _strip_bismillah(verse["text_uthmani"], surah, ayah),
            "translation": trans["text_en"] if trans else "",
            "words": words_list,
            "roots_summary": roots_list,
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

        # Surah names (English)
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

        surahs = []
        for row in rows:
            ch = row["chapter"]
            name = SURAH_NAMES[ch] if ch < len(SURAH_NAMES) else f"Surah {ch}"
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
            trans_row = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
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
                "translation": trans_row["text_en"] if trans_row else "",
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
            "SELECT v.chapter, v.verse, v.text_uthmani, t.text_en "
            "FROM verses v LEFT JOIN translations t "
            "ON v.chapter = t.chapter AND v.verse = t.verse "
            "WHERE v.chapter = ? AND v.verse BETWEEN ? AND ? AND v.verse != ? "
            "ORDER BY v.verse",
            (surah, start, end, ayah),
        ).fetchall()

        verses = [
            {
                "surah": r["chapter"],
                "ayah": r["verse"],
                "text_uthmani": _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
                "translation": r["text_en"] or "",
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
            trans_row = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
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
                "translation": trans_row["text_en"] if trans_row else "",
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
