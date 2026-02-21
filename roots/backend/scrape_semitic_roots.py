#!/usr/bin/env python3
"""Scrape semiticroots.net and save Semitic root/derivative data.

Produces data/semitic_roots.json and imports into data/quran.db.

Usage:
    python scrape_semitic_roots.py          # scrape all roots
    python scrape_semitic_roots.py --force  # re-scrape even if cache exists
"""

import json
import os
import re
import sqlite3
import sys
import time
import urllib3

import requests
from bs4 import BeautifulSoup

# Suppress InsecureRequestWarning (site uses self-signed cert)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://www.semiticroots.net"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(DATA_DIR, "semitic_roots.json")
DB_PATH = os.path.join(DATA_DIR, "quran.db")
DELAY = 0.5  # seconds between requests


def fetch(url: str) -> str:
    """Fetch a URL with retries."""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30, verify=False)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt == 2:
                print(f"    FAILED after 3 attempts: {e}")
                raise
            print(f"    Retry {attempt + 1}: {e}")
            time.sleep(2)
    return ""


def scrape_root_index() -> list[dict]:
    """Scrape all root IDs, transliterations, and concepts from search pages."""
    roots = []
    page = 1
    total_pages = None

    while True:
        label = f"{page}/{total_pages}" if total_pages else str(page)
        print(f"  Fetching search page {label}...")
        html = fetch(f"{BASE_URL}/index.php/root/search?pageSize=100&Root_page={page}")
        soup = BeautifulSoup(html, "html.parser")

        # Determine total pages from pager on first request
        if total_pages is None:
            last_link = soup.select_one(".pager .last a")
            if last_link and last_link.get("href"):
                m = re.search(r"Root_page=(\d+)", last_link["href"])
                if m:
                    total_pages = int(m.group(1))

        # Parse table rows
        table = soup.select_one("table.items")
        if not table:
            break

        rows = table.select("tbody tr")
        if not rows or rows[0].select_one(".empty"):
            break

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            root_id = int(cells[0].get_text(strip=True))
            transliteration = cells[1].get_text(strip=True)
            concept = cells[6].get_text(strip=True)

            roots.append({
                "id": root_id,
                "transliteration": transliteration,
                "concept": concept,
            })

        # Check for next page
        if total_pages and page >= total_pages:
            break
        if f"Root_page={page + 1}" not in html:
            break

        page += 1
        time.sleep(DELAY)

    return roots


def scrape_root_detail(root_id: int) -> list[dict]:
    """Scrape derivatives for a single root from its detail page."""
    html = fetch(f"{BASE_URL}/index.php/root/{root_id}")
    soup = BeautifulSoup(html, "html.parser")

    derivatives = []

    detail_table = soup.select_one("table.detail-view")
    if not detail_table:
        return derivatives

    # Find the Derivatives row
    for row in detail_table.find_all("tr"):
        th = row.find("th")
        if not th or th.get_text(strip=True) != "Derivatives":
            continue

        td = row.find("td")
        if not td:
            break

        inner_table = td.find("table")
        if not inner_table:
            break

        for drow in inner_table.find_all("tr"):
            dcells = drow.find_all("td")
            if len(dcells) < 2:
                continue

            language = dcells[0].get_text(strip=True)
            link = dcells[1].find("a")
            if not link:
                continue

            title = link.get("title", "")
            displayed_text = link.get_text(strip=True)

            # Parse title: "Word: حمد\nConcept: praise\nMeaning: He praised, thanked."
            word = ""
            d_concept = ""
            meaning = ""
            for line in title.split("\n"):
                line = line.strip()
                if line.startswith("Word:"):
                    word = line[5:].strip()
                elif line.startswith("Concept:"):
                    d_concept = line[8:].strip()
                elif line.startswith("Meaning:"):
                    meaning = line[8:].strip()

            derivatives.append({
                "language": language,
                "word": word or displayed_text,
                "displayed_text": displayed_text,
                "concept": d_concept,
                "meaning": meaning,
            })
        break

    return derivatives


# --------------- Buckwalter ↔ SemiticRoots transliteration ---------------

BW_TO_SR = {
    "'": "ʔ", ">": "ʔ", "<": "ʔ", "&": "ʔ", "}": "ʔ", "A": "ʔ",
    "b": "b", "t": "t", "v": "ṯ", "j": "g",
    "H": "ḥ", "x": "ḫ", "d": "d", "*": "ḏ",
    "r": "r", "z": "z", "s": "s¹", "$": "s²",
    "S": "ṣ", "D": "ḍ", "T": "ṭ", "Z": "ẓ",
    "E": "ʕ", "g": "ġ", "f": "f", "q": "q",
    "k": "k", "l": "l", "m": "m", "n": "n",
    "h": "h", "w": "w", "y": "y",
}


def bw_root_to_sr(bw_root: str) -> str:
    """Convert a Buckwalter root like 'Hmd' to semiticroots format 'ḥ-m-d'."""
    return "-".join(BW_TO_SR.get(c, c) for c in bw_root)


# --------------- Database ---------------

def import_to_db(roots: list[dict]):
    """Import scraped data into the SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"  Database not found at {DB_PATH}. Skipping DB import.")
        print("  Run seed_db.py first, then re-run this script.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

    # Delete existing semiticroots data only (preserves starling data)
    c.execute(
        "DELETE FROM semitic_derivatives WHERE root_id IN "
        "(SELECT id FROM semitic_roots WHERE source = 'semiticroots' OR source IS NULL)"
    )
    c.execute("DELETE FROM semitic_roots WHERE source = 'semiticroots' OR source IS NULL")

    for root in roots:
        c.execute(
            "INSERT INTO semitic_roots (id, transliteration, concept, source) VALUES (?, ?, ?, ?)",
            (root["id"], root["transliteration"], root["concept"], "semiticroots"),
        )
        for d in root.get("derivatives", []):
            c.execute(
                "INSERT INTO semitic_derivatives (root_id, language, word, displayed_text, concept, meaning) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (root["id"], d["language"], d["word"], d["displayed_text"], d["concept"], d["meaning"]),
            )

    conn.commit()
    conn.close()
    print(f"  Imported {len(roots)} roots into {DB_PATH}")


# --------------- Main ---------------

def main():
    force = "--force" in sys.argv
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check for cached data
    if os.path.exists(CACHE_FILE) and not force:
        print(f"Using cached data: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            roots = json.load(f)
        total_derivs = sum(len(r.get("derivatives", [])) for r in roots)
        print(f"  {len(roots)} roots, {total_derivs} derivatives")
        print("Importing into database...")
        import_to_db(roots)
        return

    # Step 1: Scrape root index
    print("Step 1/3: Scraping root index from search pages...")
    roots = scrape_root_index()
    print(f"  Found {len(roots)} roots")

    if not roots:
        print("ERROR: No roots found. The website may be down.")
        sys.exit(1)

    # Step 2: Scrape detail pages for derivatives
    print(f"Step 2/3: Scraping {len(roots)} root detail pages...")
    for i, root in enumerate(roots):
        print(f"  [{i + 1}/{len(roots)}] {root['transliteration']} ({root['concept']})")
        try:
            root["derivatives"] = scrape_root_detail(root["id"])
        except Exception as e:
            print(f"    ERROR: {e}")
            root["derivatives"] = []
        time.sleep(DELAY)

        # Save progress every 50 roots
        if (i + 1) % 50 == 0:
            with open(CACHE_FILE + ".partial", "w", encoding="utf-8") as f:
                json.dump(roots, f, ensure_ascii=False, indent=2)
            print(f"    (progress saved)")

    total_derivs = sum(len(r.get("derivatives", [])) for r in roots)
    print(f"  Total: {len(roots)} roots, {total_derivs} derivatives")

    # Step 3: Save and import
    print("Step 3/3: Saving and importing...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(roots, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {CACHE_FILE}")

    # Remove partial file if it exists
    partial = CACHE_FILE + ".partial"
    if os.path.exists(partial):
        os.remove(partial)

    import_to_db(roots)
    print("Done!")


if __name__ == "__main__":
    main()
