"""Flask API for the Quran Root Word Analyzer."""

import os
import sqlite3
from collections import OrderedDict

import requests
from flask import Flask, jsonify
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

        return jsonify({
            "surah": surah,
            "ayah": ayah,
            "text_uthmani": verse["text_uthmani"],
            "translation": trans["text_en"] if trans else "",
            "words": words_list,
            "roots_summary": list(roots_seen.values()),
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
