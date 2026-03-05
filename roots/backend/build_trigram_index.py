#!/usr/bin/env python3
"""Build a normalized trigram index of the Quran for the Chrome extension.

Outputs a JSON file mapping normalized 3-word sequences to their verse locations,
plus a per-verse normalized word list for extending matches beyond trigrams.

The normalization strips all diacritics and small marks, removes tatweel,
and normalizes alef/ya variants so the index matches any Arabic script convention.
"""

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "quran.db"
OUT_PATH = Path(__file__).parent.parent.parent / "extensions" / "quran-research-tool" / "public" / "quran-index.json"


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text to a canonical consonantal skeleton."""
    # Alef variants → bare alef
    text = text.replace("\u0671", "\u0627")  # alef wasla
    text = text.replace("\u0623", "\u0627")  # alef + hamza above
    text = text.replace("\u0625", "\u0627")  # alef + hamza below
    text = text.replace("\u0622", "\u0627")  # alef + madda
    # Alef maqsura → ya
    text = text.replace("\u0649", "\u064A")
    # Remove tatweel
    text = text.replace("\u0640", "")
    # Strip all combining marks (Mn category): diacritics, small signs, etc.
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def build_index():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT chapter, verse, text_uthmani FROM verses ORDER BY chapter, verse")

    trigrams: dict[str, list[list[int]]] = {}
    verse_words: dict[str, list[str]] = {}
    total_words = 0
    total_trigrams = 0

    for chapter, verse, text in cur:
        raw_words = text.split()
        norm_words = [normalize_arabic(w) for w in raw_words]
        # Filter out empty strings (shouldn't happen but be safe)
        norm_words = [w for w in norm_words if w]
        if not norm_words:
            continue

        key = f"{chapter}:{verse}"
        verse_words[key] = norm_words
        total_words += len(norm_words)

        # Build trigrams (sliding window of 3)
        for i in range(len(norm_words) - 2):
            tri = f"{norm_words[i]} {norm_words[i+1]} {norm_words[i+2]}"
            if tri not in trigrams:
                trigrams[tri] = []
            trigrams[tri].append([chapter, verse, i + 1])  # 1-indexed position
            total_trigrams += 1

    conn.close()

    index = {
        "trigrams": trigrams,
        "verses": verse_words,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    file_size = OUT_PATH.stat().st_size
    unique_trigrams = len(trigrams)

    print(f"Total words:     {total_words:,}")
    print(f"Total trigrams:  {total_trigrams:,}")
    print(f"Unique trigrams: {unique_trigrams:,}")
    print(f"Verses:          {len(verse_words):,}")
    print(f"Output size:     {file_size / 1024 / 1024:.2f} MB")
    print(f"Written to:      {OUT_PATH}")


if __name__ == "__main__":
    build_index()
