#!/usr/bin/env python3
"""Normalize cognate languages into a proper relational table.

Creates a `cognate_languages` table with id, name, and family, then replaces
the raw language string in `semitic_derivatives` with a foreign key.

Also deduplicates derivative entries where the same language appears multiple
times for the same root with redundant data (meaning = word, or near-identical).

Usage:
    python normalize_cognate_languages.py --dry-run   # Preview changes
    python normalize_cognate_languages.py              # Apply changes
"""

import argparse
import sqlite3
import sys

from app import DB_PATH

# Language → Family mapping
LANGUAGE_FAMILIES = {
    # Akkadian / East Semitic
    "Akkadian": "East Semitic",
    "Amarna": "East Semitic",
    "Eblaite": "East Semitic",

    # Aramaic
    "Aramaic": "Aramaic",
    "Biblical Aramaic": "Aramaic",
    "Hatran": "Aramaic",
    "Judaic Aramaic": "Aramaic",
    "Mandaic": "Aramaic",
    "Mandaic Aramaic": "Aramaic",
    "Maʕlula": "Aramaic",
    "Modern Aramaic": "Aramaic",
    "Nabataean": "Aramaic",
    "Old Aramaic": "Aramaic",
    "Palmyrene": "Aramaic",
    "Samalian": "Aramaic",
    "Syriac": "Aramaic",
    "Syrian Aramaic": "Aramaic",

    # Canaanite
    "Ammonite": "Canaanite",
    "Canaanite": "Canaanite",
    "Edomite": "Canaanite",
    "Hebrew": "Canaanite",
    "Moabite": "Canaanite",
    "Phoenician": "Canaanite",
    "Punic": "Canaanite",

    # Arabic
    "Arabic": "Arabic",
    "Maltese": "Arabic",
    "Modern Arabic": "Arabic",

    # Ancient North Arabian
    "Dadanitic": "Ancient North Arabian",
    "Hasaitic": "Ancient North Arabian",
    "Hismaic": "Ancient North Arabian",
    "Safaitic": "Ancient North Arabian",
    "Taymanitic": "Ancient North Arabian",
    "Thamudic B": "Ancient North Arabian",

    # Ancient South Arabian
    "Epigraphic South Arabian": "Ancient South Arabian",
    "Minaic": "Ancient South Arabian",
    "Qatabanic": "Ancient South Arabian",
    "Sabaic": "Ancient South Arabian",
    "Ḥaḍramitic": "Ancient South Arabian",

    # Ethiopic
    "Amharic": "Ethiopic",
    "Argobba": "Ethiopic",
    "East Ethiopic": "Ethiopic",
    "Gafat": "Ethiopic",
    "Ge'ez": "Ethiopic",
    "Gurage": "Ethiopic",
    "Harari": "Ethiopic",
    "Tigre": "Ethiopic",
    "Tigrinya": "Ethiopic",
    "Wolane": "Ethiopic",

    # Modern South Arabian
    "Harsusi": "Modern South Arabian",
    "Jibbali": "Modern South Arabian",
    "Mehri": "Modern South Arabian",
    "Shehri": "Modern South Arabian",
    "Soqotri": "Modern South Arabian",

    # Northwest Semitic (misc)
    "Amorite": "Northwest Semitic",
    "Deir Alla": "Northwest Semitic",
    "Ugaritic": "Northwest Semitic",
}


def create_languages_table(conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Create cognate_languages table and populate it. Returns name→id map."""
    languages = conn.execute(
        "SELECT DISTINCT language FROM semitic_derivatives ORDER BY language"
    ).fetchall()
    lang_names = [r["language"] for r in languages]

    if dry_run:
        print(f"Would create cognate_languages table with {len(lang_names)} languages:")
        for name in lang_names:
            family = LANGUAGE_FAMILIES.get(name, "Unknown")
            print(f"  {name} → {family}")
            if family == "Unknown":
                print(f"    ⚠ No family mapping found!")
        return {}

    conn.execute("DROP TABLE IF EXISTS cognate_languages")
    conn.execute("""
        CREATE TABLE cognate_languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            family TEXT
        )
    """)

    name_to_id = {}
    for name in lang_names:
        family = LANGUAGE_FAMILIES.get(name)
        conn.execute(
            "INSERT INTO cognate_languages (name, family) VALUES (?, ?)",
            (name, family),
        )
        row = conn.execute(
            "SELECT id FROM cognate_languages WHERE name = ?", (name,)
        ).fetchone()
        name_to_id[name] = row["id"]

    conn.commit()
    print(f"Created cognate_languages table with {len(name_to_id)} languages")
    return name_to_id


def add_language_id_column(conn: sqlite3.Connection, name_to_id: dict, dry_run: bool):
    """Add language_id FK column to semitic_derivatives and populate it."""
    if dry_run:
        print(f"\nWould add language_id column to semitic_derivatives")
        print(f"Would update {conn.execute('SELECT COUNT(*) FROM semitic_derivatives').fetchone()[0]} rows")
        return

    # Check if column already exists
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(semitic_derivatives)").fetchall()]
    if "language_id" not in cols:
        conn.execute("ALTER TABLE semitic_derivatives ADD COLUMN language_id INTEGER REFERENCES cognate_languages(id)")

    # Populate
    for name, lang_id in name_to_id.items():
        conn.execute(
            "UPDATE semitic_derivatives SET language_id = ? WHERE language = ?",
            (lang_id, name),
        )

    conn.commit()

    # Verify
    null_count = conn.execute(
        "SELECT COUNT(*) FROM semitic_derivatives WHERE language_id IS NULL"
    ).fetchone()[0]
    if null_count:
        print(f"⚠ {null_count} rows still have NULL language_id")
    else:
        print(f"All rows populated with language_id")

    # Create index
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derivatives_language_id ON semitic_derivatives(language_id)")
    conn.commit()
    print("Created index on language_id")


def dedup_entries(conn: sqlite3.Connection, dry_run: bool) -> tuple[int, int]:
    """Remove redundant derivative entries programmatically.

    Targets entries where:
    1. meaning == word (no real gloss, just echoing the word)
       AND another entry for the same root+language exists with a real meaning
    2. Exact duplicate (same root_id, language, word, meaning)
    """
    # Pass 1: Remove exact duplicates (keep lowest id)
    exact_dupes = conn.execute("""
        SELECT MIN(id) as keep_id, root_id, language, word, meaning, COUNT(*) as cnt
        FROM semitic_derivatives
        GROUP BY root_id, language, word, meaning
        HAVING COUNT(*) > 1
    """).fetchall()

    exact_deleted = 0
    for row in exact_dupes:
        if dry_run:
            print(f"  Exact dupe: root_id={row['root_id']}, lang={row['language']}, "
                  f"word={row['word'][:40]}, count={row['cnt']} → keep ID {row['keep_id']}")
        else:
            conn.execute(
                "DELETE FROM semitic_derivatives WHERE root_id=? AND language=? AND word=? AND meaning=? AND id != ?",
                (row["root_id"], row["language"], row["word"], row["meaning"], row["keep_id"]),
            )
        exact_deleted += row["cnt"] - 1

    # Pass 2: For each (transliteration, language) group with >1 entry,
    # remove entries where meaning == word IF a better entry exists
    groups = conn.execute("""
        SELECT r.transliteration, d.root_id, d.language, COUNT(*) as cnt
        FROM semitic_derivatives d
        JOIN semitic_roots r ON d.root_id = r.id
        GROUP BY r.transliteration, d.language
        HAVING COUNT(*) > 1
    """).fetchall()

    junk_deleted = 0
    for g in groups:
        entries = conn.execute(
            "SELECT id, word, meaning FROM semitic_derivatives WHERE root_id=? AND language=?",
            (g["root_id"], g["language"]),
        ).fetchall()

        has_real_meaning = any(e["meaning"] and e["meaning"] != e["word"] for e in entries)
        if not has_real_meaning:
            continue

        for e in entries:
            if e["meaning"] and e["meaning"] != e["word"]:
                continue  # This one has a real meaning, keep it
            # This entry's meaning just echoes the word — junk if better exists
            if dry_run:
                print(f"  Junk entry: root={g['transliteration']}, lang={g['language']}, "
                      f"id={e['id']}, word={e['word'][:40]} (meaning echoes word)")
            else:
                conn.execute("DELETE FROM semitic_derivatives WHERE id=?", (e["id"],))
            junk_deleted += 1

    if not dry_run:
        conn.commit()

    return exact_deleted, junk_deleted


def main():
    parser = argparse.ArgumentParser(description="Normalize cognate languages into relational table")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying DB")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Step 1: Dedup entries first
    print("=== Step 1: Deduplicating entries ===")
    exact, junk = dedup_entries(conn, args.dry_run)
    print(f"  Exact duplicates removed: {exact}")
    print(f"  Junk entries removed (meaning=word, better exists): {junk}")
    if args.dry_run:
        print("  (dry-run — no changes)")

    # Step 2: Create languages table
    print("\n=== Step 2: Creating cognate_languages table ===")
    name_to_id = create_languages_table(conn, args.dry_run)

    # Step 3: Add FK column
    if not args.dry_run:
        print("\n=== Step 3: Adding language_id to semitic_derivatives ===")
        add_language_id_column(conn, name_to_id, args.dry_run)
    else:
        print("\n=== Step 3: Would add language_id column ===")
        add_language_id_column(conn, {}, args.dry_run)

    # Summary
    if not args.dry_run:
        total = conn.execute("SELECT COUNT(*) FROM semitic_derivatives").fetchone()[0]
        langs = conn.execute("SELECT COUNT(*) FROM cognate_languages").fetchone()[0]
        print(f"\n✓ Done. {total} derivatives, {langs} languages")

    conn.close()


if __name__ == "__main__":
    main()
