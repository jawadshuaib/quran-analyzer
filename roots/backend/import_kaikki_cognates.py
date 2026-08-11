#!/usr/bin/env python3
"""Import reviewed Kaikki/Wiktionary cognates into quran.db.

Only records explicitly accepted during the pilot are imported. Re-running the
command replaces the prior ``wiktionary`` source atomically and preserves all
SemiticRoots/Starling rows.

Usage:
    python import_kaikki_cognates.py --dry-run
    python import_kaikki_cognates.py
    python import_kaikki_cognates.py --db /path/to/quran.db
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from scrape_semitic_roots import bw_root_to_sr


HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "quran.db"
DEFAULT_REVIEW = HERE / "data" / "kaikki_cognate_review.csv"
DEFAULT_ACCEPTED = HERE / "kaikki_cognates_accepted.json"
SOURCE = "wiktionary"
SOURCE_LICENSE = "CC BY-SA 4.0"
SOURCE_ATTRIBUTION = "English Wiktionary contributors; extracted via Kaikki/Wiktextract"

LANGUAGE_METADATA = {
    "Proto-Semitic": ("Proto-Semitic", None, None),
    "Akkadian": ("East Semitic", -2500, 100),
    "Ugaritic": ("Northwest Semitic", -1400, -1180),
    "Phoenician": ("Canaanite", -1050, -150),
    "Hebrew": ("Canaanite", -1000, 2025),
    "Biblical Hebrew": ("Canaanite", -1000, 200),
    "Aramaic": ("Aramaic", -1000, 2025),
    "Classical Syriac": ("Aramaic", 200, 1300),
    "Classical Mandaic": ("Aramaic", 200, 700),
    "Ge'ez": ("Ethiopic", -500, 2025),
    "Amharic": ("Ethiopic", 1300, 2025),
    "Tigre": ("Ethiopic", 800, 2025),
    "Sabaic": ("Ancient South Arabian", -1000, 600),
}

PROVENANCE_COLUMNS = {
    "source": "TEXT",
    "source_url": "TEXT",
    "relation_type": "TEXT",
    "confidence": "TEXT",
    "source_license": "TEXT",
    "source_attribution": "TEXT",
    "imported_at": "TEXT",
}


def load_review(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            dict(row) for row in csv.DictReader(handle)
            if row.get("decision", "").strip().lower() == "accept"
        ]


def load_accepted(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return data


def validate_rows(rows: list[dict]) -> None:
    required = {
        "root_buckwalter", "arabic_headword", "headword_gloss", "relation",
        "language", "word", "source_url",
    }
    if not rows:
        raise ValueError("No accepted cognate rows were found")
    for number, row in enumerate(rows, 1):
        missing = sorted(key for key in required if not row.get(key))
        if missing:
            raise ValueError(f"Accepted row {number} lacks: {', '.join(missing)}")
        if row["relation"] not in {"cognate", "inherited"}:
            raise ValueError(f"Accepted row {number} has unsupported relation {row['relation']!r}")


def ensure_schema(conn: sqlite3.Connection) -> None:
    root_columns = {row[1] for row in conn.execute("PRAGMA table_info(semitic_roots)")}
    if "source" not in root_columns:
        conn.execute("ALTER TABLE semitic_roots ADD COLUMN source TEXT DEFAULT 'semiticroots'")

    derivative_columns = {row[1] for row in conn.execute("PRAGMA table_info(semitic_derivatives)")}
    if "language_id" not in derivative_columns:
        conn.execute("ALTER TABLE semitic_derivatives ADD COLUMN language_id INTEGER")
    for name, sql_type in PROVENANCE_COLUMNS.items():
        if name not in derivative_columns:
            conn.execute(f"ALTER TABLE semitic_derivatives ADD COLUMN {name} {sql_type}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derivatives_source ON semitic_derivatives(source)")


def ensure_language(conn: sqlite3.Connection, name: str) -> int | None:
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cognate_languages'"
    ).fetchone()
    if not table:
        return None
    columns = {row[1] for row in conn.execute("PRAGMA table_info(cognate_languages)")}
    row = conn.execute("SELECT id FROM cognate_languages WHERE name=?", (name,)).fetchone()
    if row:
        return row[0]
    family, date_from, date_to = LANGUAGE_METADATA.get(name, (None, None, None))
    fields = ["name"]
    values = [name]
    for field, value in (("family", family), ("date_from", date_from), ("date_to", date_to)):
        if field in columns:
            fields.append(field)
            values.append(value)
    placeholders = ",".join("?" for _ in fields)
    conn.execute(
        f"INSERT INTO cognate_languages ({','.join(fields)}) VALUES ({placeholders})",
        values,
    )
    return conn.execute("SELECT id FROM cognate_languages WHERE name=?", (name,)).fetchone()[0]


def concept_for(rows: list[dict]) -> str:
    # An explicit inherited-source gloss is the strongest etymological
    # concept available. Do not promote all senses of the Arabic headword to
    # meanings shared by the wider cognate family.
    inherited = [
        (row.get("meaning") or "").strip()
        for row in rows
        if row.get("relation") == "inherited" and (row.get("meaning") or "").strip()
    ]
    if inherited:
        return inherited[0]

    concepts = []
    for row in rows:
        value = (row.get("headword_gloss") or "").strip()
        # The pilot serializes separate Arabic senses with semicolons. In the
        # absence of an inherited gloss, retain only the primary Arabic sense
        # as a cautious heading rather than asserting every later/figurative
        # sense across the Semitic family.
        value = value.split(";", 1)[0].strip()
        if value and value not in concepts:
            concepts.append(value)
    return " / ".join(concepts[:1])


def import_rows(conn: sqlite3.Connection, rows: list[dict]) -> dict:
    validate_rows(rows)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["root_buckwalter"]].append(row)

    ensure_schema(conn)
    old_roots = conn.execute(
        "SELECT COUNT(*) FROM semitic_roots WHERE source=?", (SOURCE,)
    ).fetchone()[0]
    old_derivatives = conn.execute(
        """
        SELECT COUNT(*) FROM semitic_derivatives
        WHERE root_id IN (SELECT id FROM semitic_roots WHERE source=?)
        """,
        (SOURCE,),
    ).fetchone()[0]
    conn.execute(
        "DELETE FROM semitic_derivatives WHERE root_id IN "
        "(SELECT id FROM semitic_roots WHERE source=?)",
        (SOURCE,),
    )
    conn.execute("DELETE FROM semitic_roots WHERE source=?", (SOURCE,))

    inserted_derivatives = 0
    for root_bw, root_rows in sorted(grouped.items()):
        cursor = conn.execute(
            "INSERT INTO semitic_roots (transliteration, concept, source) VALUES (?, ?, ?)",
            (bw_root_to_sr(root_bw), concept_for(root_rows), SOURCE),
        )
        root_id = cursor.lastrowid
        for row in root_rows:
            language_id = ensure_language(conn, row["language"])
            # A blank template gloss means the source asserted the cognate
            # relation but did not define that individual form. Keep it NULL;
            # copying the Arabic headword's senses here falsely makes them
            # look independently attested in every language.
            meaning = (row.get("meaning") or "").strip() or None
            displayed = row["word"]
            if row.get("romanization"):
                displayed += f" ({row['romanization']})"
            conn.execute(
                """
                INSERT INTO semitic_derivatives
                    (root_id, language, word, displayed_text, concept, meaning,
                     language_id, source, source_url, relation_type, confidence,
                     source_license, source_attribution, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    root_id, row["language"], row["word"], displayed,
                    meaning, meaning, language_id, SOURCE, row["source_url"],
                    row["relation"], "reviewed", SOURCE_LICENSE,
                    SOURCE_ATTRIBUTION,
                ),
            )
            inserted_derivatives += 1

    return {
        "removed_roots": old_roots,
        "removed_derivatives": old_derivatives,
        "inserted_roots": len(grouped),
        "inserted_derivatives": inserted_derivatives,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--accepted-json", type=Path, default=DEFAULT_ACCEPTED)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # The tracked JSON makes production/deployment imports reproducible. A
    # local review CSV takes precedence so newly adjudicated pilots can be run
    # without first regenerating that artifact.
    rows = load_review(args.review_csv) or load_accepted(args.accepted_json)
    validate_rows(rows)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        result = import_rows(conn, rows)
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    mode = "Would import" if args.dry_run else "Imported"
    print(f"{mode} {result['inserted_derivatives']} reviewed relations for {result['inserted_roots']} roots")
    if result["removed_roots"]:
        print(f"Replaced {result['removed_derivatives']} prior Wiktionary relations for {result['removed_roots']} roots")


if __name__ == "__main__":
    main()
