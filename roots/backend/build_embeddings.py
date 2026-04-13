"""Build verse embeddings for semantic search.

Pre-computes sentence embeddings for all verses with AI translations
and stores them in the quran.db SQLite database. Run this offline on
a dev machine, then ship the updated DB to production.

Usage:
    python build_embeddings.py                # Build all embeddings
    python build_embeddings.py --force        # Rebuild even if exists
    python build_embeddings.py --model NAME   # Use different model
"""

import argparse
import sqlite3
import struct
import sys
import time

import numpy as np
from sentence_transformers import SentenceTransformer

from app import DB_PATH, get_db

DEFAULT_MODEL = "all-MiniLM-L6-v2"  # 22MB, 384-dim, fast on CPU


def ensure_embeddings_table(conn):
    """Create verse_embeddings table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verse_embeddings (
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            text_used TEXT,
            model_name TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (chapter, verse)
        )
    """)
    conn.commit()


def fetch_verses_for_embedding(conn):
    """Fetch all verses with AI translations for embedding."""
    rows = conn.execute("""
        SELECT v.chapter, v.verse,
               COALESCE(at_.translation_text, t.text_en) AS translation,
               GROUP_CONCAT(DISTINCT vt.theme) AS themes
        FROM verses v
        LEFT JOIN ai_translations at_
            ON at_.chapter = v.chapter AND at_.verse = v.verse
        LEFT JOIN translations t
            ON t.chapter = v.chapter AND t.verse = v.verse
        LEFT JOIN verse_themes vt
            ON vt.chapter = v.chapter AND vt.verse = v.verse
        WHERE COALESCE(at_.translation_text, t.text_en) IS NOT NULL
        GROUP BY v.chapter, v.verse
        ORDER BY v.chapter, v.verse
    """).fetchall()
    return rows


def build_text_for_embedding(translation: str, themes: str | None) -> str:
    """Combine translation + themes into embedding input text."""
    text = translation.strip()
    if themes:
        # Clean up theme list
        theme_list = [t.strip() for t in themes.split(",") if t.strip()]
        if theme_list:
            text += f" | Themes: {', '.join(theme_list)}"
    return text


def embedding_to_blob(embedding: np.ndarray) -> bytes:
    """Convert numpy array to bytes for SQLite storage."""
    return embedding.astype(np.float32).tobytes()


def blob_to_embedding(blob: bytes, dim: int = 384) -> np.ndarray:
    """Convert SQLite blob back to numpy array."""
    return np.frombuffer(blob, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser(description="Build verse embeddings")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Sentence transformer model (default: {DEFAULT_MODEL})")
    parser.add_argument("--force", action="store_true",
                        help="Rebuild all embeddings even if they exist")
    parser.add_argument("--batch-size", type=int, default=128,
                        help="Batch size for encoding (default: 128)")
    args = parser.parse_args()

    print(f"Loading model: {args.model}...")
    start = time.time()
    model = SentenceTransformer(args.model)
    dim = model.get_sentence_embedding_dimension()
    print(f"  Model loaded in {time.time() - start:.1f}s (dimension: {dim})")

    conn = get_db()
    ensure_embeddings_table(conn)

    # Check existing embeddings
    existing = set()
    if not args.force:
        rows = conn.execute(
            "SELECT chapter, verse FROM verse_embeddings"
        ).fetchall()
        existing = {(r["chapter"], r["verse"]) for r in rows}
        if existing:
            print(f"  {len(existing)} existing embeddings found (use --force to rebuild)")

    # Fetch verses
    verses = fetch_verses_for_embedding(conn)
    print(f"  {len(verses)} verses with translations")

    # Filter out already-embedded verses
    to_embed = []
    texts = []
    for row in verses:
        key = (row["chapter"], row["verse"])
        if key in existing:
            continue
        text = build_text_for_embedding(row["translation"], row["themes"])
        to_embed.append(row)
        texts.append(text)

    if not texts:
        print("  All verses already embedded. Nothing to do.")
        conn.close()
        return

    print(f"  Embedding {len(texts)} verses...")
    start = time.time()

    # Encode in batches
    all_embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # Pre-normalize for cosine similarity
    )

    elapsed = time.time() - start
    print(f"  Encoded in {elapsed:.1f}s ({len(texts) / elapsed:.0f} verses/sec)")

    # Write to database
    print("  Writing to database...")
    for i, row in enumerate(to_embed):
        blob = embedding_to_blob(all_embeddings[i])
        text = texts[i]
        if args.force:
            conn.execute(
                "INSERT OR REPLACE INTO verse_embeddings "
                "(chapter, verse, embedding, text_used, model_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["chapter"], row["verse"], blob, text, args.model),
            )
        else:
            conn.execute(
                "INSERT INTO verse_embeddings "
                "(chapter, verse, embedding, text_used, model_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["chapter"], row["verse"], blob, text, args.model),
            )

    conn.commit()
    conn.close()

    # Verify
    conn2 = get_db()
    total = conn2.execute("SELECT COUNT(*) FROM verse_embeddings").fetchone()[0]
    conn2.close()

    print(f"\nDone! {len(texts)} embeddings written.")
    print(f"Total embeddings in DB: {total}")
    size_mb = (len(texts) * dim * 4) / (1024 * 1024)
    print(f"Embedding data size: ~{size_mb:.1f} MB")


if __name__ == "__main__":
    main()
