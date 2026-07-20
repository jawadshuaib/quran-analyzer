"""Build multilingual verse embeddings (Phase B) via Voyage AI.

Produces a MULTI-VECTOR index: two documents per verse —
  * ar  = Uthmani Arabic text (Bismillah-stripped)
  * en  = best available English translation (+ themes)
— each embedded with a hosted Voyage multilingual model. This is what lets an
Arabic query ("آيات عن الصبر") and an English query ("verse involving satan and
adam") both retrieve the right verses; at query time we take the max similarity
across the two doc vectors per verse (same embedding space).

Run OFFLINE on a dev machine (indexing is free under the Voyage token grant),
then ship the table to prod with ./sync_tables_to_prod.sh verse_embeddings_v2.

The Voyage API key is read from (in order): env VOYAGE_API_KEY, a local
roots/backend/.env file (gitignored), or admin_preferences.voyage_api_key.
The key is NEVER printed.

Usage:
    python build_embeddings_v2.py                          # voyage-4-lite / 512, ar+en
    python build_embeddings_v2.py --model voyage-4 --dim 1024
    python build_embeddings_v2.py --doc-types ar           # only the Arabic side
    python build_embeddings_v2.py --limit 40 --dry-run     # smoke test, no API calls
    python build_embeddings_v2.py --force                  # re-embed everything
"""

import argparse
import hashlib
import os
import sys
import time

import numpy as np
import requests

from app import DB_PATH, get_db, _strip_bismillah  # noqa: E402

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = "voyage-4-lite"
DEFAULT_DIM = 512
DOC_TYPES = ("ar", "en")
HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# API key + config
# --------------------------------------------------------------------------

def _load_env_file():
    """Load KEY=VALUE lines from roots/backend/.env into os.environ (no dep on
    python-dotenv). Does not overwrite values already in the environment."""
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def get_voyage_key():
    _load_env_file()
    key = os.environ.get("VOYAGE_API_KEY", "").strip()
    if key:
        return key
    try:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'voyage_api_key'"
            ).fetchone()
            if row and row["value"]:
                return row["value"].strip()
        finally:
            conn.close()
    except Exception:
        pass
    return ""


# --------------------------------------------------------------------------
# Schema + doc building
# --------------------------------------------------------------------------

def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verse_embeddings_v2 (
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            doc_type TEXT NOT NULL,
            model_name TEXT NOT NULL,
            dim INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            text_used TEXT,
            text_hash TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (chapter, verse, doc_type, model_name)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_model ON verse_embeddings_v2(model_name, doc_type)"
    )
    conn.commit()


def fetch_docs(conn):
    """One row per verse with the Arabic text, best English translation, and
    themes. Latest-config ai_translation (revised_text preferred) else the
    conventional English translation — matching what the reader displays."""
    rows = conn.execute("""
        SELECT v.chapter, v.verse, v.text_uthmani,
               COALESCE(
                 (SELECT COALESCE(NULLIF(a.revised_text, ''), a.translation_text)
                  FROM ai_translations a
                  WHERE a.chapter = v.chapter AND a.verse = v.verse
                  ORDER BY a.config_id DESC, a.id DESC LIMIT 1),
                 t.text_en
               ) AS translation,
               GROUP_CONCAT(DISTINCT vt.theme) AS themes
        FROM verses v
        LEFT JOIN translations t
            ON t.chapter = v.chapter AND t.verse = v.verse
        LEFT JOIN verse_themes vt
            ON vt.chapter = v.chapter AND vt.verse = v.verse
        GROUP BY v.chapter, v.verse
        ORDER BY v.chapter, v.verse
    """).fetchall()
    return rows


def build_en_text(translation, themes):
    if not translation:
        return ""
    text = translation.strip()
    if themes:
        theme_list = [t.strip() for t in themes.split(",") if t.strip()]
        if theme_list:
            text += " | Themes: " + ", ".join(theme_list)
    return text


def build_ar_text(text_uthmani, chapter, verse):
    if not text_uthmani:
        return ""
    return _strip_bismillah(text_uthmani, chapter, verse).strip()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Voyage
# --------------------------------------------------------------------------

def voyage_embed(texts, model, input_type, output_dim, api_key, max_retries=6):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"input": texts, "model": model, "input_type": input_type, "output_dtype": "float"}
    if output_dim:
        body["output_dimension"] = output_dim
    last_err = None
    for attempt in range(max_retries):
        try:
            r = requests.post(VOYAGE_URL, headers=headers, json=body, timeout=(6.05, 120))
            if r.status_code == 429 or r.status_code >= 500:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(min(2 ** attempt, 30))
                continue
            r.raise_for_status()
            data = r.json()["data"]
            data.sort(key=lambda d: d["index"])
            return [d["embedding"] for d in data]
        except requests.RequestException as exc:
            last_err = str(exc)
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"Voyage embed failed after {max_retries} tries: {last_err}")


def to_blob(vec):
    return np.asarray(vec, dtype=np.float32).tobytes()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Build Voyage multilingual verse index")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dim", type=int, default=DEFAULT_DIM)
    ap.add_argument("--doc-types", default="ar,en",
                    help="comma list subset of ar,en")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--limit", type=int, default=0,
                    help="only process the first N verses (smoke test)")
    ap.add_argument("--force", action="store_true",
                    help="re-embed even if an unchanged embedding exists")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the doc texts and report counts; no API calls")
    args = ap.parse_args()

    doc_types = [d.strip() for d in args.doc_types.split(",") if d.strip() in DOC_TYPES]
    if not doc_types:
        raise SystemExit("--doc-types must be a subset of: ar,en")

    conn = get_db()
    ensure_table(conn)

    verses = fetch_docs(conn)
    if args.limit:
        verses = verses[: args.limit]
    print(f"{len(verses)} verses; doc types={doc_types}; model={args.model} dim={args.dim}")

    # Build the (chapter, verse, doc_type, text, hash) work list.
    work = []
    for r in verses:
        ch, v = r["chapter"], r["verse"]
        if "ar" in doc_types:
            t = build_ar_text(r["text_uthmani"], ch, v)
            if t:
                work.append((ch, v, "ar", t, text_hash(t)))
        if "en" in doc_types:
            t = build_en_text(r["translation"], r["themes"])
            if t:
                work.append((ch, v, "en", t, text_hash(t)))

    # Skip already-embedded, unchanged docs (resumable) unless --force. The key
    # includes dim: `dim` is NOT part of the table PK, so a --dim change on the
    # same model must re-embed everything (else the index mixes dimensions and
    # load_matrices_v2 silently drops the odd rows).
    existing = {}
    if not args.force:
        for row in conn.execute(
            "SELECT chapter, verse, doc_type, text_hash, dim FROM verse_embeddings_v2 "
            "WHERE model_name = ?", (args.model,)
        ):
            existing[(row["chapter"], row["verse"], row["doc_type"])] = (row["text_hash"], row["dim"])

    todo = [w for w in work
            if args.force or existing.get((w[0], w[1], w[2])) != (w[4], args.dim)]
    print(f"{len(work)} docs total; {len(todo)} to embed "
          f"({len(work) - len(todo)} already current)")

    if args.dry_run:
        for w in todo[:3]:
            print(f"  sample {w[2]} {w[0]}:{w[1]} -> {w[3][:80]!r}")
        est_tokens = sum(len(w[3]) for w in todo) // 4
        print(f"[dry-run] ~{est_tokens:,} tokens across {len(todo)} docs; no API calls made.")
        conn.close()
        return

    if not todo:
        print("Nothing to embed. Done.")
        conn.close()
        return

    api_key = get_voyage_key()
    if not api_key:
        raise SystemExit(
            "No Voyage API key. Set VOYAGE_API_KEY in the environment or in "
            "roots/backend/.env (gitignored), or admin_preferences.voyage_api_key."
        )

    written = 0
    start = time.time()
    for i in range(0, len(todo), args.batch_size):
        batch = todo[i:i + args.batch_size]
        vecs = voyage_embed([w[3] for w in batch], args.model, "document",
                            args.dim, api_key)
        if len(vecs) != len(batch):
            raise RuntimeError(f"Voyage returned {len(vecs)} vecs for {len(batch)} inputs")
        for (ch, v, dt, text, h), vec in zip(batch, vecs):
            conn.execute(
                "INSERT OR REPLACE INTO verse_embeddings_v2 "
                "(chapter, verse, doc_type, model_name, dim, embedding, text_used, text_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ch, v, dt, args.model, args.dim, to_blob(vec), text, h),
            )
        conn.commit()  # per-batch, so a crash resumes cleanly
        written += len(batch)
        rate = written / max(time.time() - start, 0.1)
        print(f"  {written}/{len(todo)} embedded ({rate:.0f}/s)", end="\r")

    conn.close()
    elapsed = time.time() - start
    print(f"\nDone. {written} docs embedded in {elapsed:.0f}s.")

    conn2 = get_db()
    total = conn2.execute(
        "SELECT COUNT(*) FROM verse_embeddings_v2 WHERE model_name=?", (args.model,)
    ).fetchone()[0]
    conn2.close()
    size_mb = total * args.dim * 4 / (1024 * 1024)
    print(f"Total {args.model} vectors in DB: {total} (~{size_mb:.0f} MB of float32 blobs)")
    print("Next: python eval_retrieval.py --engine v1 --engine2 v2  "
          "then ./sync_tables_to_prod.sh verse_embeddings_v2")


if __name__ == "__main__":
    main()
