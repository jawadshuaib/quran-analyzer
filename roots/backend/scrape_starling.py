#!/usr/bin/env python3
"""Scrape the Starling/Tower of Babel Semitic Etymology database.

Produces data/starling_semitic.json and imports into data/quran.db.

Usage:
    python scrape_starling.py          # scrape all pages
    python scrape_starling.py --force  # re-scrape even if cache exists
"""

import json
import os
import re
import sqlite3
import sys
import time
import unicodedata

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://starlingdb.org/cgi-bin/response.cgi"
BASENAME = "/data/semham/semet"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(DATA_DIR, "starling_semitic.json")
DB_PATH = os.path.join(DATA_DIR, "quran.db")
DELAY = 1.0  # seconds between requests
RECORDS_PER_PAGE = 20
TOTAL_RECORDS = 2923
ID_OFFSET = 10001  # Starling IDs start here to avoid collisions with semiticroots

# Starling consonant notation → our transliteration system
# Key difference: Starling uses 's' for sin (our s¹), 'š' for shin (our s²), 'ḳ' for qaf (our q)
STARLING_CONSONANTS = {
    "\u0294": "\u0294",  # ʔ → ʔ (glottal stop)
    "b": "b",
    "t": "t",
    "\u1e6f": "\u1e6f",  # ṯ → ṯ
    "g": "g",            # jim
    "\u1e25": "\u1e25",  # ḥ → ḥ
    "\u1e2b": "\u1e2b",  # ḫ → ḫ
    "d": "d",
    "\u1e0f": "\u1e0f",  # ḏ → ḏ
    "r": "r",
    "z": "z",
    "s": "s\u00b9",      # s → s¹ (sin)
    "\u0161": "s\u00b2",  # š → s² (shin)
    "\u1e63": "\u1e63",  # ṣ → ṣ
    "\u1e0d": "\u1e0d",  # ḍ → ḍ
    "\u1e6d": "\u1e6d",  # ṭ → ṭ
    "\u1e93": "\u1e93",  # ẓ → ẓ
    "\u0295": "\u0295",  # ʕ → ʕ
    "\u0121": "\u0121",  # ġ → ġ
    "f": "f",
    "q": "q",
    "\u1e33": "q",       # ḳ → q
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "h": "h",
    "w": "w",
    "y": "y",
}

# Fields that are metadata, not language attestations
METADATA_FIELDS = {"Number", "Proto-Semitic", "Afroasiatic etymology", "Meaning", "Notes"}


def fetch(url, params=None):
    """Fetch a URL with retries."""
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt == 2:
                print(f"    FAILED after 3 attempts: {e}")
                raise
            print(f"    Retry {attempt + 1}: {e}")
            time.sleep(2)
    return ""


def extract_consonants(text, fallback_text=None):
    """Extract consonantal root from a Starling transliterated field.

    Tries the primary text (Arabic field) first; falls back to fallback_text
    (Proto-Semitic) if no consonants are found.

    Returns transliteration in our format (e.g. 'b-ʕ-l') or None.
    """
    for source in [text, fallback_text]:
        if not source:
            continue

        # Normalize Unicode to handle combining characters
        source = unicodedata.normalize("NFC", source.strip())

        # Remove parenthesized references: (BK 1, 6), (CAD...), etc.
        source = re.sub(r"\([^)]*\)", "", source)
        # Remove bracketed content: [-u-]
        source = re.sub(r"\[[^\]]*\]", "", source)
        # Remove quoted glosses (single and double quotes)
        source = re.sub(r"'[^']*'", "", source)
        source = re.sub(r'"[^"]*"', "", source)

        # Take first form: split on ';' then ','
        part = source.split(";")[0].strip()
        part = part.split(",")[0].strip()

        # Remove sense numbers, 'id.', 'cf.', reference abbreviations
        part = re.sub(r"\b(id|cf)\b\.?", "", part, flags=re.IGNORECASE)
        part = re.sub(r"\b\d+\b", "", part)

        # Take first whitespace-delimited token (the actual form)
        tokens = part.split()
        if not tokens:
            continue
        form = tokens[0].strip(" -*")

        # For Proto-Semitic forms, strip leading *
        form = form.lstrip("*")

        # Extract consonants using our mapping
        consonants = []
        for ch in form:
            mapped = STARLING_CONSONANTS.get(ch)
            if mapped is not None:
                consonants.append(mapped)

        if consonants:
            return "-".join(consonants)

    return None


def parse_record(record_div):
    """Parse a single results_record div into a {label: value} dict."""
    fields = {}
    for div in record_div.find_all("div", recursive=False):
        fld_span = div.find("span", class_="fld")
        val_span = div.find("span", class_="unicode")
        if not fld_span or not val_span:
            continue

        label = fld_span.get_text(strip=True).rstrip(":")
        value = val_span.get_text(strip=True)
        fields[label] = value

    return fields


def scrape_page(first):
    """Scrape a single page of results, returning a list of field dicts."""
    params = {
        "root": "config",
        "morphession": "0",
        "basename": BASENAME,
        "first": str(first),
    }
    html = fetch(BASE_URL, params=params)
    soup = BeautifulSoup(html, "html.parser")

    records = []
    for rec_div in soup.find_all("div", class_="results_record"):
        fields = parse_record(rec_div)
        if not fields.get("Number"):
            continue
        records.append(fields)

    return records


def process_record(fields):
    """Convert parsed fields into our storage format."""
    try:
        number = int(fields.get("Number", 0))
    except (ValueError, TypeError):
        return None

    if number == 0:
        return None

    proto_semitic = fields.get("Proto-Semitic", "")
    meaning = fields.get("Meaning", "").strip("'\"")
    arabic = fields.get("Arabic", "")

    # Extract transliteration: Arabic field first, Proto-Semitic fallback
    transliteration = extract_consonants(arabic, proto_semitic)

    # Build derivatives from all language fields
    derivatives = []
    for label, value in fields.items():
        if label in METADATA_FIELDS or not value:
            continue
        derivatives.append({
            "language": label,
            "word": value,
            "displayed_text": value,
            "concept": meaning,
            "meaning": value,
        })

    return {
        "id": ID_OFFSET + number,
        "starling_number": number,
        "transliteration": transliteration,
        "concept": meaning,
        "proto_semitic": proto_semitic,
        "source": "starling",
        "derivatives": derivatives,
    }


def scrape_all():
    """Scrape all pages from the Starling database."""
    records = []
    total_pages = (TOTAL_RECORDS + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE

    for page_num in range(total_pages):
        first = page_num * RECORDS_PER_PAGE + 1
        label = f"{page_num + 1}/{total_pages}"
        print(f"  [{label}] Fetching records starting at {first}...")

        try:
            page_records = scrape_page(first)
            for fields in page_records:
                processed = process_record(fields)
                if processed:
                    records.append(processed)
            print(f"    Got {len(page_records)} records (total: {len(records)})")
        except Exception as e:
            print(f"    ERROR on page {page_num + 1}: {e}")

        # Save progress every 10 pages
        if (page_num + 1) % 10 == 0:
            with open(CACHE_FILE + ".partial", "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"    (progress saved: {len(records)} records)")

        time.sleep(DELAY)

    return records


def import_to_db(records):
    """Import Starling data into the SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"  Database not found at {DB_PATH}. Skipping DB import.")
        print("  Run seed_db.py first, then re-run this script.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure tables exist with source column
    c.execute("""
        CREATE TABLE IF NOT EXISTS semitic_roots (
            id INTEGER PRIMARY KEY,
            transliteration TEXT NOT NULL,
            concept TEXT,
            source TEXT DEFAULT 'semiticroots'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS semitic_derivatives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_id INTEGER NOT NULL,
            language TEXT,
            word TEXT,
            displayed_text TEXT,
            concept TEXT,
            meaning TEXT,
            FOREIGN KEY (root_id) REFERENCES semitic_roots(id)
        )
    """)

    # Add source column if it doesn't exist (for existing databases)
    try:
        c.execute("ALTER TABLE semitic_roots ADD COLUMN source TEXT DEFAULT 'semiticroots'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    c.execute("CREATE INDEX IF NOT EXISTS idx_sr_trans ON semitic_roots(transliteration)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sd_root ON semitic_derivatives(root_id)")

    # Delete existing Starling data only (preserves semiticroots data)
    c.execute(
        "DELETE FROM semitic_derivatives WHERE root_id IN "
        "(SELECT id FROM semitic_roots WHERE source = 'starling')"
    )
    c.execute("DELETE FROM semitic_roots WHERE source = 'starling'")

    imported = 0
    skipped = 0
    for rec in records:
        if not rec.get("transliteration"):
            skipped += 1
            continue

        c.execute(
            "INSERT OR REPLACE INTO semitic_roots (id, transliteration, concept, source) "
            "VALUES (?, ?, ?, ?)",
            (rec["id"], rec["transliteration"], rec["concept"], "starling"),
        )
        for d in rec.get("derivatives", []):
            c.execute(
                "INSERT INTO semitic_derivatives "
                "(root_id, language, word, displayed_text, concept, meaning) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rec["id"], d["language"], d["word"], d["displayed_text"],
                 d["concept"], d["meaning"]),
            )
        imported += 1

    conn.commit()
    conn.close()
    print(f"  Imported {imported} roots ({skipped} skipped — no transliteration) into {DB_PATH}")


def main():
    force = "--force" in sys.argv
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check for cached data
    if os.path.exists(CACHE_FILE) and not force:
        print(f"Using cached data: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
        total_derivs = sum(len(r.get("derivatives", [])) for r in records)
        with_trans = sum(1 for r in records if r.get("transliteration"))
        print(f"  {len(records)} records, {total_derivs} derivatives")
        print(f"  {with_trans} records have extractable root transliterations")
        print("Importing into database...")
        import_to_db(records)
        return

    # Scrape all pages
    print("Scraping Starling Semitic Etymology database...")
    print(f"  URL: {BASE_URL}")
    total_pages = (TOTAL_RECORDS + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
    print(f"  Expected: ~{TOTAL_RECORDS} records across {total_pages} pages")
    print(f"  Delay: {DELAY}s between requests")
    print()
    records = scrape_all()

    if not records:
        print("ERROR: No records found. The website may be down.")
        sys.exit(1)

    total_derivs = sum(len(r.get("derivatives", [])) for r in records)
    with_trans = sum(1 for r in records if r.get("transliteration"))
    print(f"\nTotal: {len(records)} records, {total_derivs} derivatives")
    print(f"  Records with extractable root: {with_trans}/{len(records)}")

    # Save cache
    print("\nSaving to cache...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {CACHE_FILE}")

    # Remove partial file
    partial = CACHE_FILE + ".partial"
    if os.path.exists(partial):
        os.remove(partial)

    # Import to database
    print("\nImporting into database...")
    import_to_db(records)
    print("\nDone!")


if __name__ == "__main__":
    main()
