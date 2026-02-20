"""Download Quranic data and build the SQLite database."""

import os
import re
import json
import sqlite3
import requests

from buckwalter import buckwalter_to_arabic, space_root

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

MORPHOLOGY_URL = (
    "https://raw.githubusercontent.com/bnjasim/quranic-corpus/"
    "master/quranic-corpus-morphology-0.4.txt"
)
# Fallback mirror
MORPHOLOGY_URL_ALT = (
    "https://raw.githubusercontent.com/mustafa0x/quran-morphology/"
    "master/quran-morphology.txt"
)

TANZIL_URL = "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true"
TANZIL_URL_ALT = "https://tanzil.net/res/text/uthmani/quran-uthmani.txt"

TRANSLATION_URL = "https://api.alquran.cloud/v1/quran/en.sahih"


def download_file(url: str, dest: str, alt_url: str | None = None) -> str:
    """Download a URL to dest path, return content as string."""
    if os.path.exists(dest):
        print(f"  [cached] {dest}")
        with open(dest, "r", encoding="utf-8") as f:
            return f.read()

    print(f"  Downloading {url} ...")
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except Exception:
        if alt_url:
            print(f"  Primary failed, trying alt: {alt_url} ...")
            resp = requests.get(alt_url, timeout=120)
            resp.raise_for_status()
        else:
            raise

    with open(dest, "w", encoding="utf-8") as f:
        f.write(resp.text)
    return resp.text


def download_json(url: str, dest: str) -> dict:
    """Download a JSON API response."""
    if os.path.exists(dest):
        print(f"  [cached] {dest}")
        with open(dest, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"  Downloading {url} ...")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


# ---------- POS tag to human-readable name ----------

POS_MAP = {
    "N": "Noun",
    "PN": "Proper Noun",
    "ADJ": "Adjective",
    "V": "Verb",
    "IMPV": "Imperative Verb",
    "IMPN": "Verbal Noun",
    "PRON": "Pronoun",
    "DEM": "Demonstrative",
    "REL": "Relative Pronoun",
    "COND": "Conditional",
    "INT": "Interrogative",
    "T": "Time Adverb",
    "LOC": "Location Adverb",
    "P": "Preposition",
    "CONJ": "Conjunction",
    "SUB": "Subordinating Conjunction",
    "ACC": "Accusative Particle",
    "AMD": "Amendment Particle",
    "ANS": "Answer Particle",
    "AVR": "Aversion Particle",
    "CERT": "Certainty Particle",
    "CIRC": "Circumstantial Particle",
    "COM": "Comitative Particle",
    "CAUS": "Cause Particle",
    "NEG": "Negative Particle",
    "EXH": "Exhortation Particle",
    "EXL": "Explanation Particle",
    "EXP": "Exceptive Particle",
    "FUT": "Future Particle",
    "INC": "Inceptive Particle",
    "INT": "Interrogative Particle",
    "INTG": "Interrogative Particle",
    "PRO": "Prohibition Particle",
    "RES": "Restriction Particle",
    "RET": "Retraction Particle",
    "SUR": "Surprise Particle",
    "VOC": "Vocative Particle",
    "REM": "Resumption Particle",
    "EMPH": "Emphatic Particle",
    "INL": "Inceptive lam",
    "PREV": "Preventive Particle",
    "SP": "Supplemental Particle",
    "ATT": "Attention Particle",
    "RSLT": "Result Particle",
    "INF": "Interpretation Particle",
    "DET": "Determiner",
    "STEM": "Stem",
    "POS": "Possessive",
    "PREFIX": "Prefix",
    "SUFFIX": "Suffix",
}

GENDER_MAP = {"M": "Masculine", "F": "Feminine"}
NUMBER_MAP = {"S": "Singular", "D": "Dual", "P": "Plural"}
PERSON_MAP = {"1": "1st", "2": "2nd", "3": "3rd"}
CASE_MAP = {"NOM": "Nominative", "ACC": "Accusative", "GEN": "Genitive"}
VOICE_MAP = {"ACT": "Active", "PASS": "Passive"}
MOOD_MAP = {"IND": "Indicative", "SUBJ": "Subjunctive", "JUS": "Jussive", "ENERGETIC": "Energetic"}
STATE_MAP = {"DEF": "Definite", "INDEF": "Indefinite"}
FORM_MAP = {"(I)": "I", "(II)": "II", "(III)": "III", "(IV)": "IV",
            "(V)": "V", "(VI)": "VI", "(VII)": "VII", "(VIII)": "VIII",
            "(IX)": "IX", "(X)": "X", "(XI)": "XI", "(XII)": "XII"}


def parse_features(features_str: str) -> dict:
    """Parse the features portion of a morphology tag.

    Example features_str: 'ROOT:mlk|LEM:m~`lik|N|GEN|M|S'
    Returns dict with root, lemma, pos, gender, number, etc.
    """
    result = {
        "root_bw": None,
        "lemma_bw": None,
        "pos": None,
        "tag": None,
        "gender": None,
        "number": None,
        "person": None,
        "case_val": None,
        "voice": None,
        "mood": None,
        "verb_form": None,
        "state": None,
    }

    parts = features_str.split("|")
    for part in parts:
        part = part.strip()
        if part.startswith("ROOT:"):
            result["root_bw"] = part[5:]
        elif part.startswith("LEM:"):
            result["lemma_bw"] = part[4:]
        elif part.startswith("POS:"):
            pos_code = part[4:]
            result["tag"] = pos_code
            result["pos"] = POS_MAP.get(pos_code, pos_code)
        elif part in POS_MAP:
            if result["pos"] is None:
                result["tag"] = part
                result["pos"] = POS_MAP[part]
        elif part in GENDER_MAP:
            result["gender"] = GENDER_MAP[part]
        elif part in NUMBER_MAP:
            result["number"] = NUMBER_MAP[part]
        elif part in PERSON_MAP:
            result["person"] = PERSON_MAP[part]
        elif part in CASE_MAP:
            result["case_val"] = CASE_MAP[part]
        elif part in VOICE_MAP:
            result["voice"] = VOICE_MAP[part]
        elif part in MOOD_MAP:
            result["mood"] = MOOD_MAP[part]
        elif part in FORM_MAP:
            result["verb_form"] = FORM_MAP[part]
        elif part in STATE_MAP:
            result["state"] = STATE_MAP[part]
        elif part in ("1", "2", "3"):
            result["person"] = PERSON_MAP[part]

    return result


def parse_morphology(text: str) -> list[dict]:
    """Parse the morphology corpus file into a list of row dicts."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Format: LOCATION\tFORM\tTAG\tFEATURES
        parts = line.split("\t")
        if len(parts) < 4:
            continue

        location = parts[0]  # e.g. (1:1:1:1)
        form_bw = parts[1]
        tag = parts[2]
        features_str = parts[3]

        # Parse location: (chapter:verse:word:segment)
        loc_match = re.match(r"\((\d+):(\d+):(\d+):(\d+)\)", location)
        if not loc_match:
            continue

        chapter = int(loc_match.group(1))
        verse = int(loc_match.group(2))
        word_pos = int(loc_match.group(3))
        segment = int(loc_match.group(4))

        feats = parse_features(features_str)

        form_arabic = buckwalter_to_arabic(form_bw)
        root_arabic = ""
        root_spaced = ""
        if feats["root_bw"]:
            root_arabic = buckwalter_to_arabic(feats["root_bw"])
            root_spaced = space_root(root_arabic)
        lemma_arabic = ""
        if feats["lemma_bw"]:
            lemma_arabic = buckwalter_to_arabic(feats["lemma_bw"])

        # Use the tag from the file or from features
        pos_tag = feats["tag"] or tag
        pos_name = feats["pos"] or POS_MAP.get(tag, tag)

        rows.append({
            "chapter": chapter,
            "verse": verse,
            "word_pos": word_pos,
            "segment": segment,
            "form_buckwalter": form_bw,
            "form_arabic": form_arabic,
            "tag": pos_tag,
            "pos": pos_name,
            "root_buckwalter": feats["root_bw"] or "",
            "root_arabic": root_spaced,
            "lemma_buckwalter": feats["lemma_bw"] or "",
            "lemma_arabic": lemma_arabic,
            "features_raw": features_str,
            "gender": feats["gender"] or "",
            "number": feats["number"] or "",
            "person": feats["person"] or "",
            "case_val": feats["case_val"] or "",
            "voice": feats["voice"] or "",
            "mood": feats["mood"] or "",
            "verb_form": feats["verb_form"] or "",
            "state": feats["state"] or "",
        })

    return rows


def parse_tanzil(text: str) -> list[dict]:
    """Parse Tanzil pipe-delimited text file."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        try:
            chapter = int(parts[0])
            verse = int(parts[1])
        except ValueError:
            continue
        rows.append({"chapter": chapter, "verse": verse, "text_uthmani": parts[2]})
    return rows


def parse_translation(data: dict) -> list[dict]:
    """Parse Al Quran Cloud API response."""
    rows = []
    for surah in data.get("data", {}).get("surahs", []):
        surah_num = surah["number"]
        for ayah in surah["ayahs"]:
            rows.append({
                "chapter": surah_num,
                "verse": ayah["numberInSurah"],
                "text_en": ayah["text"],
            })
    return rows


def create_db(morphology_rows, verse_rows, translation_rows):
    """Create and populate the SQLite database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE verses (
            chapter INTEGER,
            verse INTEGER,
            text_uthmani TEXT,
            PRIMARY KEY (chapter, verse)
        )
    """)

    c.execute("""
        CREATE TABLE translations (
            chapter INTEGER,
            verse INTEGER,
            text_en TEXT,
            PRIMARY KEY (chapter, verse)
        )
    """)

    c.execute("""
        CREATE TABLE morphology (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER,
            verse INTEGER,
            word_pos INTEGER,
            segment INTEGER,
            form_buckwalter TEXT,
            form_arabic TEXT,
            tag TEXT,
            pos TEXT,
            root_buckwalter TEXT,
            root_arabic TEXT,
            lemma_buckwalter TEXT,
            lemma_arabic TEXT,
            features_raw TEXT,
            gender TEXT,
            number TEXT,
            person TEXT,
            case_val TEXT,
            voice TEXT,
            mood TEXT,
            verb_form TEXT,
            state TEXT
        )
    """)

    c.execute("CREATE INDEX idx_morph_cv ON morphology(chapter, verse)")

    c.executemany(
        "INSERT INTO verses (chapter, verse, text_uthmani) VALUES (?, ?, ?)",
        [(r["chapter"], r["verse"], r["text_uthmani"]) for r in verse_rows],
    )

    c.executemany(
        "INSERT INTO translations (chapter, verse, text_en) VALUES (?, ?, ?)",
        [(r["chapter"], r["verse"], r["text_en"]) for r in translation_rows],
    )

    c.executemany(
        """INSERT INTO morphology
        (chapter, verse, word_pos, segment, form_buckwalter, form_arabic,
         tag, pos, root_buckwalter, root_arabic, lemma_buckwalter, lemma_arabic,
         features_raw, gender, number, person, case_val, voice, mood, verb_form, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["chapter"], r["verse"], r["word_pos"], r["segment"],
                r["form_buckwalter"], r["form_arabic"],
                r["tag"], r["pos"],
                r["root_buckwalter"], r["root_arabic"],
                r["lemma_buckwalter"], r["lemma_arabic"],
                r["features_raw"],
                r["gender"], r["number"], r["person"], r["case_val"],
                r["voice"], r["mood"], r["verb_form"], r["state"],
            )
            for r in morphology_rows
        ],
    )

    conn.commit()
    conn.close()


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Step 1/3: Downloading morphology corpus...")
    morph_text = download_file(
        MORPHOLOGY_URL,
        os.path.join(DATA_DIR, "morphology.txt"),
        alt_url=MORPHOLOGY_URL_ALT,
    )

    print("Step 2/3: Downloading Uthmani text...")
    tanzil_text = download_file(
        TANZIL_URL,
        os.path.join(DATA_DIR, "uthmani.txt"),
        alt_url=TANZIL_URL_ALT,
    )

    print("Step 3/3: Downloading English translation...")
    translation_data = download_json(
        TRANSLATION_URL,
        os.path.join(DATA_DIR, "translation.json"),
    )

    print("Parsing morphology...")
    morphology_rows = parse_morphology(morph_text)
    print(f"  {len(morphology_rows)} morphology segments")

    print("Parsing verses...")
    verse_rows = parse_tanzil(tanzil_text)
    print(f"  {len(verse_rows)} verses")

    print("Parsing translations...")
    translation_rows = parse_translation(translation_data)
    print(f"  {len(translation_rows)} translations")

    print("Creating database...")
    create_db(morphology_rows, verse_rows, translation_rows)
    print(f"Done! Database at: {DB_PATH}")


if __name__ == "__main__":
    main()
