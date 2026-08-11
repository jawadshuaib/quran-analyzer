#!/usr/bin/env python3
"""Database regression test for the reviewed Kaikki importer."""

import sqlite3

from import_kaikki_cognates import import_rows


def schema(conn):
    conn.executescript("""
        CREATE TABLE semitic_roots (
            id INTEGER PRIMARY KEY, transliteration TEXT NOT NULL,
            concept TEXT, source TEXT DEFAULT 'semiticroots'
        );
        CREATE TABLE cognate_languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
            family TEXT, date_from INTEGER, date_to INTEGER
        );
        CREATE TABLE semitic_derivatives (
            id INTEGER PRIMARY KEY AUTOINCREMENT, root_id INTEGER NOT NULL,
            language TEXT, word TEXT, displayed_text TEXT, concept TEXT,
            meaning TEXT, language_id INTEGER
        );
    """)


def accepted(word="אָב", meaning=""):
    return [{
        "root_buckwalter": "Abw", "arabic_headword": "أب",
        "headword_gloss": "father", "relation": "cognate",
        "language": "Hebrew", "word": word, "romanization": "ʾāḇ",
        "meaning": meaning, "source_url": "https://en.wiktionary.org/wiki/أب#Arabic",
    }]


def main():
    conn = sqlite3.connect(":memory:")
    schema(conn)
    conn.execute("INSERT INTO semitic_roots VALUES (1, 'k-t-b', 'write', 'starling')")
    conn.execute("INSERT INTO semitic_derivatives (root_id,language,word) VALUES (1,'Hebrew','כתב')")

    first = import_rows(conn, accepted())
    assert first["inserted_roots"] == 1 and first["inserted_derivatives"] == 1
    row = conn.execute(
        "SELECT r.source,r.concept,d.source,d.relation_type,d.confidence,d.source_license,d.meaning,d.concept "
        "FROM semitic_derivatives d JOIN semitic_roots r ON r.id=d.root_id "
        "WHERE r.source='wiktionary'"
    ).fetchone()
    assert row == (
        "wiktionary", "father", "wiktionary", "cognate", "reviewed",
        "CC BY-SA 4.0", None, None,
    )

    second = import_rows(conn, accepted("אָבִי", "father"))
    assert second["removed_roots"] == 1 and second["removed_derivatives"] == 1
    assert conn.execute("SELECT COUNT(*) FROM semitic_roots WHERE source='starling'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM semitic_roots WHERE source='wiktionary'").fetchone()[0] == 1
    assert conn.execute("SELECT word FROM semitic_derivatives WHERE source='wiktionary'").fetchone()[0] == "אָבִי"
    assert conn.execute("SELECT meaning FROM semitic_derivatives WHERE source='wiktionary'").fetchone()[0] == "father"
    print("ok — atomic source replacement, provenance, and source preservation")


if __name__ == "__main__":
    main()
