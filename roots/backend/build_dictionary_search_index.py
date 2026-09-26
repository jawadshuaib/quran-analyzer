#!/usr/bin/env python3
"""Build the derived tables behind /api/dictionary/search (dictionary_search.py).

Both are rebuilt from dictionary_entries / ai_root_meanings / root_core_meanings
on each host — never synced between hosts:

  dictionary_search_fts   FTS5 over each displayed entry's English, porter-
                          stemmed, so "millet" finds د خ ن through the
                          dictionaries' own wording.
  root_search_vectors     one vector per root "profile" (gloss, field, core
                          sense) and per displayed dictionary entry, for the
                          semantic arm. Per model: Voyage (the model the
                          verse search uses; needs a working key) and/or the
                          local MiniLM fallback.

  python3 build_dictionary_search_index.py --fts
  python3 build_dictionary_search_index.py --vectors minilm
  python3 build_dictionary_search_index.py --vectors voyage
  python3 build_dictionary_search_index.py --all          (fts + every model that works here)

Incremental: a vector is recomputed only when its text changed (text_hash).
"""
import argparse
import hashlib
import os
import re
import sqlite3
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
SHOWN = ("e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
         "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> ''")
ENTRY_CHARS = 1800      # enough for an entry's main senses; keeps vectors focused
MINILM = "all-MiniLM-L6-v2"


def connect():
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _plain(text):
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text or "")
    t = re.sub(r"[*_#>`]", "", t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- FTS
def build_fts(conn):
    t0 = time.time()
    conn.execute("DROP TABLE IF EXISTS dictionary_search_fts")
    conn.execute(
        "CREATE VIRTUAL TABLE dictionary_search_fts USING fts5("
        "root_bw UNINDEXED, dictionary_slug UNINDEXED, body, "
        "tokenize = 'porter unicode61 remove_diacritics 2')")
    rows = conn.execute(
        "SELECT e.root_buckwalter, e.dictionary_slug, e.harmonized_en FROM dictionary_entries e WHERE "
        + SHOWN).fetchall()
    conn.executemany(
        "INSERT INTO dictionary_search_fts (root_bw, dictionary_slug, body) VALUES (?,?,?)",
        [(r[0], r[1], _plain(r[2])) for r in rows])
    conn.execute("INSERT INTO dictionary_search_fts(dictionary_search_fts) VALUES('optimize')")
    conn.commit()
    print(f"fts: {len(rows)} entries indexed in {time.time() - t0:.1f}s")


# ---------------------------------------------------------------- documents
_BW2LAT = {"A": "ʾ", "b": "b", "t": "t", "v": "th", "j": "j", "H": "ḥ", "x": "kh", "d": "d", "*": "dh",
           "r": "r", "z": "z", "s": "s", "$": "sh", "S": "ṣ", "D": "ḍ", "T": "ṭ", "Z": "ẓ", "E": "ʿ",
           "g": "gh", "f": "f", "q": "q", "k": "k", "l": "l", "m": "m", "n": "n", "h": "h", "w": "w", "y": "y"}


def documents(conn):
    """[(doc_id, root_bw, doc_type, dictionary_slug, text)]"""
    names = {r[0]: r[1] for r in conn.execute("SELECT slug, name_en FROM dictionaries")}
    roots = {}
    for r in conn.execute("SELECT e.root_buckwalter, MAX(e.root_arabic) FROM dictionary_entries e WHERE "
                          + SHOWN + " GROUP BY e.root_buckwalter"):
        roots[r[0]] = (r[1] or "").replace(" ", "")
    gloss = {}
    try:
        for r in conn.execute("SELECT root_buckwalter, primary_meaning, semantic_field FROM ai_root_meanings ORDER BY id"):
            gloss.setdefault(r[0], (r[1] or "", r[2] or ""))
    except sqlite3.OperationalError:
        pass
    core = {}
    try:
        for r in conn.execute("SELECT root_buckwalter, passage FROM root_core_meanings "
                              "WHERE review_status = 'approved' AND COALESCE(hidden,0) = 0 ORDER BY id"):
            core.setdefault(r[0], []).append(r[1] or "")
    except sqlite3.OperationalError:
        pass
    docs = []
    for bw, ar in roots.items():
        g, f = gloss.get(bw, ("", ""))
        lat = "-".join(_BW2LAT.get(ch, ch) for ch in bw)
        parts = [f"Arabic root {' '.join(ar)} ({lat})."]
        if g:
            parts.append(_plain(g) + ".")
        if f:
            parts.append("Semantic field: " + _plain(f) + ".")
        for p in core.get(bw, [])[:2]:
            parts.append(_plain(p))
        docs.append((f"p:{bw}", bw, "profile", None, " ".join(parts)[:2400]))
    for r in conn.execute("SELECT e.id, e.root_buckwalter, e.dictionary_slug, e.harmonized_en FROM dictionary_entries e WHERE "
                          + SHOWN):
        text = f"{names.get(r[2], r[2])}, root {' '.join(roots.get(r[1], ''))}: " + _plain(r[3])[:ENTRY_CHARS]
        docs.append((f"e:{r[0]}", r[1], "entry", r[2], text))
    return docs


def ensure_vec_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS root_search_vectors (
            doc_id TEXT NOT NULL, root_bw TEXT NOT NULL, doc_type TEXT NOT NULL,
            dictionary_slug TEXT, model_name TEXT NOT NULL, dim INTEGER NOT NULL,
            embedding BLOB NOT NULL, text_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (doc_id, model_name)
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rsv_model ON root_search_vectors(model_name)")
    conn.commit()


def _hash(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]


def _pending(conn, docs, model):
    have = {r[0]: r[1] for r in conn.execute(
        "SELECT doc_id, text_hash FROM root_search_vectors WHERE model_name = ?", (model,))}
    want = {d[0] for d in docs}
    stale = [d for d in docs if have.get(d[0]) != _hash(d[4])]
    gone = [k for k in have if k not in want]
    return stale, gone


def _store(conn, model, batch, vecs):
    conn.executemany(
        "INSERT OR REPLACE INTO root_search_vectors (doc_id, root_bw, doc_type, dictionary_slug, model_name, dim, "
        "embedding, text_hash) VALUES (?,?,?,?,?,?,?,?)",
        [(d[0], d[1], d[2], d[3], model, int(v.shape[0]), v.astype(np.float32).tobytes(), _hash(d[4]))
         for d, v in zip(batch, vecs)])
    conn.commit()


def build_minilm(conn, docs):
    from sentence_transformers import SentenceTransformer
    ensure_vec_table(conn)
    stale, gone = _pending(conn, docs, MINILM)
    print(f"minilm: {len(stale)} to embed, {len(gone)} to drop")
    if gone:
        conn.executemany("DELETE FROM root_search_vectors WHERE doc_id = ? AND model_name = ?",
                         [(g, MINILM) for g in gone])
        conn.commit()
    if not stale:
        return
    model = SentenceTransformer(MINILM)
    t0 = time.time()
    for i in range(0, len(stale), 256):
        batch = stale[i:i + 256]
        vecs = model.encode([d[4] for d in batch], normalize_embeddings=True, batch_size=64)
        _store(conn, MINILM, batch, np.asarray(vecs))
        print(f"  minilm {i + len(batch)}/{len(stale)} ({time.time() - t0:.0f}s)", flush=True)


def build_voyage(conn, docs):
    import requests
    import search_v2
    key = search_v2._get_voyage_api_key()
    model, dim = search_v2.DEFAULT_MODEL, search_v2.DEFAULT_DIM
    if not key:
        print("voyage: no API key — skipped")
        return False
    probe = requests.post(search_v2.VOYAGE_URL, headers={"Authorization": f"Bearer {key}"},
                          json={"input": ["test"], "model": model, "input_type": "document",
                                "output_dimension": dim}, timeout=20)
    if probe.status_code != 200:
        print(f"voyage: key rejected (HTTP {probe.status_code}) — skipped")
        return False
    ensure_vec_table(conn)
    stale, gone = _pending(conn, docs, model)
    print(f"voyage ({model}, {dim}d): {len(stale)} to embed, {len(gone)} to drop")
    if gone:
        conn.executemany("DELETE FROM root_search_vectors WHERE doc_id = ? AND model_name = ?",
                         [(g, model) for g in gone])
        conn.commit()
    t0 = time.time()
    B = 96
    for i in range(0, len(stale), B):
        batch = stale[i:i + B]
        for attempt in range(6):
            r = requests.post(search_v2.VOYAGE_URL, headers={"Authorization": f"Bearer {key}"},
                              json={"input": [d[4] for d in batch], "model": model, "input_type": "document",
                                    "output_dimension": dim, "output_dtype": "float"}, timeout=120)
            if r.status_code == 200:
                break
            wait = 5 * (2 ** attempt)
            print(f"  voyage HTTP {r.status_code}; retry in {wait}s", flush=True)
            time.sleep(wait)
        else:
            print("  voyage: giving up on this run (progress is saved; re-run to resume)")
            return False
        data = sorted(r.json()["data"], key=lambda x: x["index"])
        vecs = [np.asarray(x["embedding"], dtype=np.float32) for x in data]
        vecs = [v / (np.linalg.norm(v) or 1.0) for v in vecs]
        _store(conn, model, batch, vecs)
        print(f"  voyage {i + len(batch)}/{len(stale)} ({time.time() - t0:.0f}s)", flush=True)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fts", action="store_true")
    ap.add_argument("--vectors", choices=["minilm", "voyage"])
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if not (a.fts or a.vectors or a.all):
        ap.print_help()
        sys.exit(2)
    conn = connect()
    try:
        if a.fts or a.all:
            build_fts(conn)
        if a.vectors or a.all:
            docs = documents(conn)
            print(f"{len(docs)} documents")
            if a.vectors == "minilm" or a.all:
                build_minilm(conn, docs)
            if a.vectors == "voyage" or a.all:
                build_voyage(conn, docs)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
