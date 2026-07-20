"""Phase B search runtime: Voyage multilingual dense + lexical hybrid retrieval.

Imported by app.py. Design constraints:
  * NO network at import time (only at query time).
  * A missing v2 index or a down/absent Voyage key must NEVER 5xx — it degrades:
        Voyage ok + v2 index      -> dense(ar+en) ⊕ lexical  (RRF)
        Voyage down / no v2 index -> v1 MiniLM(en) ⊕ lexical  (RRF, degraded)
        MiniLM also unavailable   -> lexical only             (degraded)
  * Memory-lean: one float32 matrix of the v2 vectors (~26 MB at 512-dim) plus
    small python indices. No torch — the dense arm is a hosted API call.

app.py provides (accessed via a deferred `import app`, so there is no circular
import at load time): get_db, the lexical IDF globals (_root_inv/_root_idf/…),
_semantic_search (v1 fallback), and _strip_bismillah/_best_translation/_surah_name
(used by the /api/search/v2 handler, not here).
"""

import os
import re
import threading
import time
from collections import OrderedDict

import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "quran.db")

# --- tunables (eval_retrieval.py picks the final values) -------------------
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = os.environ.get("SEARCH_V2_MODEL", "voyage-4-lite")
DEFAULT_DIM = int(os.environ.get("SEARCH_V2_DIM", "512"))
RRF_K = 60
W_DENSE = 1.0
W_LEXICAL = 0.7
DENSE_FLOOR = 0.30          # cosine floor: below this a dense hit is noise
LEXICAL_CAP = 200           # max verses the lexical arm scores per query

_ARABIC_RE = re.compile(r"[؀-ۿ]")
_TASHKEEL_RE = re.compile(r"[ً-ْٰـ]")

# --- Voyage API key: admin_preferences → env → local .env, 60s cache ---------
def _load_env_file_once():
    """Load roots/backend/.env into os.environ (dev parity; no-op on prod, whose
    key comes from admin_preferences). Never overwrites a real env var."""
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


_load_env_file_once()
_VOYAGE_KEY_ENV = os.environ.get("VOYAGE_API_KEY", "")
_voyage_key_cache = {"key": None, "ts": 0.0}


def _get_voyage_api_key():
    now = time.time()
    if _voyage_key_cache["key"] is not None and now - _voyage_key_cache["ts"] < 60:
        return _voyage_key_cache["key"]
    result = _VOYAGE_KEY_ENV
    try:
        import app
        conn = app.get_db()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'voyage_api_key'"
            ).fetchone()
            if row and row["value"]:
                result = row["value"]
        finally:
            conn.close()
    except Exception:
        pass
    _voyage_key_cache["key"] = result
    _voyage_key_cache["ts"] = now
    return result


def invalidate_voyage_key_cache():
    _voyage_key_cache["key"] = None
    _voyage_key_cache["ts"] = 0.0


# --------------------------------------------------------------------------
# The v2 index (loaded once from the local DB; tolerant of a missing table)
# --------------------------------------------------------------------------
_v2_matrix = None            # (N, dim) float32, L2-normalized, all ar+en docs
_v2_doc_type = None          # (N,) object array of 'ar'/'en' aligned with rows
_v2_verse_rows = {}          # (ch, v) -> np.array of row indices for that verse
_v2_model = None
_v2_dim = None
_v2_ready = False


def load_matrices_v2(model_name=None, dim=None):
    """Read verse_embeddings_v2 for one model into an in-memory matrix. Safe to
    call before the table exists (prod before first sync): leaves _v2_ready
    False. Idempotent-ish: re-loads if called with a different model."""
    global _v2_matrix, _v2_doc_type, _v2_verse_rows, _v2_model, _v2_dim, _v2_ready
    import sqlite3

    want_model = model_name or DEFAULT_MODEL
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        # Self-heal: ensure the table exists (empty is fine — stays in fallback
        # until a sync populates it). This makes a table-only prod sync work
        # without a manual CREATE, and survives a DB reset.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verse_embeddings_v2 (
                chapter INTEGER NOT NULL, verse INTEGER NOT NULL, doc_type TEXT NOT NULL,
                model_name TEXT NOT NULL, dim INTEGER NOT NULL, embedding BLOB NOT NULL,
                text_used TEXT, text_hash TEXT, created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (chapter, verse, doc_type, model_name)
            )
        """)
        conn.commit()
        # If a dim wasn't given, discover it from the stored rows.
        rows = conn.execute(
            "SELECT chapter, verse, doc_type, dim, embedding FROM verse_embeddings_v2 "
            "WHERE model_name = ? ORDER BY chapter, verse, doc_type",
            (want_model,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print(f"[search_v2] no rows for model={want_model} — dense v2 disabled (fallback active)")
        _v2_ready = False
        return

    want_dim = dim or rows[0]["dim"]
    vecs, doc_types, verse_of_row = [], [], []
    for r in rows:
        if r["dim"] != want_dim:
            continue
        vec = np.frombuffer(r["embedding"], dtype=np.float32)
        if vec.shape[0] != want_dim:
            continue
        vecs.append(vec)
        doc_types.append(r["doc_type"])
        verse_of_row.append((r["chapter"], r["verse"]))

    if not vecs:
        _v2_ready = False
        return

    mat = np.vstack(vecs)
    # Ensure L2-normalized (defensive; the builder already normalizes via cosine).
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat = mat / norms

    verse_rows = {}
    for i, key in enumerate(verse_of_row):
        verse_rows.setdefault(key, []).append(i)
    verse_rows = {k: np.array(v, dtype=np.int64) for k, v in verse_rows.items()}

    _v2_matrix = mat
    _v2_doc_type = np.array(doc_types, dtype=object)
    _v2_verse_rows = verse_rows
    _v2_model = want_model
    _v2_dim = want_dim
    _v2_ready = True
    print(f"[search_v2] loaded {len(vecs)} vectors "
          f"({len(verse_rows)} verses) model={want_model} dim={want_dim}")


def active_model_name():
    return _v2_model


# --------------------------------------------------------------------------
# Query embedding (never blocks the request path for long)
# --------------------------------------------------------------------------
_embed_sema = threading.BoundedSemaphore(4)
_query_cache = OrderedDict()
_QCACHE_MAX = 512
_qcache_lock = threading.Lock()


def embed_query(q):
    """Return an L2-normalized (dim,) query vector, or None on ANY problem
    (no key, timeout, throttle, error). Cached; capped concurrency so a slow
    Voyage never wedges workers (the 2026-07-02 outage lesson)."""
    if not _v2_ready:
        return None
    key = (_v2_model, _v2_dim, q)
    with _qcache_lock:
        if key in _query_cache:
            _query_cache.move_to_end(key)
            return _query_cache[key]

    api_key = _get_voyage_api_key()
    if not api_key:
        return None

    if not _embed_sema.acquire(timeout=0.5):
        return None  # upstream saturated — degrade rather than queue
    try:
        body = {"input": [q], "model": _v2_model, "input_type": "query",
                "output_dtype": "float"}
        if _v2_dim:
            body["output_dimension"] = _v2_dim
        r = requests.post(
            VOYAGE_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=(3.05, 6),
        )
        if r.status_code != 200:
            return None
        vec = np.asarray(r.json()["data"][0]["embedding"], dtype=np.float32)
        n = np.linalg.norm(vec)
        if n == 0:
            return None
        vec = vec / n
    except Exception:
        return None
    finally:
        _embed_sema.release()

    with _qcache_lock:
        _query_cache[key] = vec
        _query_cache.move_to_end(key)
        while len(_query_cache) > _QCACHE_MAX:
            _query_cache.popitem(last=False)
    return vec


# --------------------------------------------------------------------------
# Dense arm — per-verse MAX across its ar/en doc vectors (same space)
# --------------------------------------------------------------------------
def _dense_search(q_vec, limit):
    """Returns [(ch, v, score, doc_type)] ranked by cosine, above DENSE_FLOOR."""
    if not _v2_ready or _v2_matrix is None:
        return []
    doc_scores = _v2_matrix @ q_vec  # (N,)
    out = []
    for (ch, v), rows in _v2_verse_rows.items():
        idx = rows[np.argmax(doc_scores[rows])]
        s = float(doc_scores[idx])
        if s >= DENSE_FLOOR:
            out.append((ch, v, s, _v2_doc_type[idx]))
    out.sort(key=lambda x: -x[2])
    return out[:limit]


# --------------------------------------------------------------------------
# Lexical arm — query terms -> roots -> IDF-weighted verses
# --------------------------------------------------------------------------
def _normalize_ar(tok):
    tok = _TASHKEEL_RE.sub("", tok)
    tok = tok.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    tok = tok.replace("ى", "ي").replace("ة", "ه")
    # Strip the definite article "ال" (and "وال"/"فال"/"بال"/"كال"/"لل") so a
    # word like "الصبر" resolves to the root ص-ب-ر, not a literal "الصبر".
    for pre in ("وال", "فال", "بال", "كال", "لل", "ال"):
        if tok.startswith(pre) and len(tok) - len(pre) >= 3:
            tok = tok[len(pre):]
            break
    return tok


# Normalized root skeletons ["رحم", …] paired with their Buckwalter key. The
# root map is immutable after the IDF engine builds, so normalize once and
# reuse — not per query token (that was O(roots × tokens) regex on hot path).
_root_skeletons = None


def _get_root_skeletons(app):
    global _root_skeletons
    if _root_skeletons is None:
        rmap = getattr(app, "_root_arabic_map", {}) or {}
        out = []
        for rbw, rar in rmap.items():
            skel = _normalize_ar((rar or "").replace(" ", ""))
            if len(skel) >= 3:
                out.append((rbw, skel))
        _root_skeletons = out
    return _root_skeletons


def _term_to_roots(tok, conn, app):
    """Best-effort map ONE query token to a set of root_buckwalter, reusing the
    same signals as /api/roots/search (Buckwalter, Arabic morphology, English
    glosses). Returns a set of root_bw."""
    roots = set()
    low = tok.lower()
    if _ARABIC_RE.search(tok):
        norm = _normalize_ar(tok)
        if len(norm) < 3:
            return roots
        # A word contains its root's consonantal skeleton (e.g. "الرحمة"→"رحمه"
        # contains "رحم"; "مغفرة"→"مغفره" contains "غفر"). Match against the
        # precomputed, normalized root skeletons — reliable across inflections
        # and prefix-free (skeletons are cached once, not rebuilt per token).
        for root_bw, skel in _get_root_skeletons(app):
            if skel in norm:
                roots.add(root_bw)
    else:
        if len(low) < 3:
            return roots
        # Buckwalter direct / prefix against known roots.
        for root_bw in getattr(app, "_root_arabic_map", {}):
            rl = root_bw.lower()
            if rl == low or rl.startswith(low):
                roots.add(root_bw)
        # English gloss / meaning signals (best-effort; tables may not exist).
        for sql, params in (
            ("SELECT DISTINCT root_buckwalter FROM ai_root_meanings "
             "WHERE LOWER(primary_meaning) LIKE ? OR LOWER(semantic_field) LIKE ? LIMIT 8",
             (f"%{low}%", f"%{low}%")),
        ):
            try:
                for r in conn.execute(sql, params):
                    if r["root_buckwalter"]:
                        roots.add(r["root_buckwalter"])
            except Exception:
                pass
    return roots


_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "is",
    "are", "verse", "verses", "surah", "ayah", "about", "story", "quran",
    "prophet", "god", "allah", "his", "her", "their", "who", "that", "this",
    "في", "من", "عن", "على", "الله", "آيات", "آية", "سورة", "قصة", "و",
}


def lexical_search(q, limit):
    """Returns [(ch, v, score)] ranked by summed root IDF over matched roots."""
    import app
    tokens = [t for t in re.split(r"[\s،,.:؛;]+", q.strip()) if t]
    tokens = [t for t in tokens if t.lower() not in _STOPWORDS and _normalize_ar(t) not in _STOPWORDS]
    if not tokens:
        return []
    root_idf = getattr(app, "_root_idf", {})
    root_inv = getattr(app, "_root_inv", {})
    discount = getattr(app, "ROOT_DISCOUNT", 0.5)
    conn = app.get_db()
    try:
        matched = set()
        for tok in tokens[:8]:
            matched |= _term_to_roots(tok, conn, app)
    finally:
        conn.close()
    if not matched:
        return []
    scores = {}
    for root_bw in matched:
        idf = root_idf.get(root_bw, 0.0)
        if idf <= 0:
            continue
        for key in root_inv.get(root_bw, ()):  # key is (ch, v)
            scores[key] = scores.get(key, 0.0) + discount * idf
        if len(scores) > LEXICAL_CAP * 4:
            break
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:limit]
    return [(c, v, s) for (c, v), s in ranked]


# --------------------------------------------------------------------------
# Fusion + the public entry point with the degradation ladder
# --------------------------------------------------------------------------
def _rrf(dense_keys, lexical_keys, limit):
    """Reciprocal-rank fusion. dense_keys/lexical_keys are ranked lists of
    (ch, v). Returns [(ch, v, fused_score)] top `limit`."""
    fused = {}
    for rank, key in enumerate(dense_keys):
        fused[key] = fused.get(key, 0.0) + W_DENSE / (RRF_K + rank)
    for rank, key in enumerate(lexical_keys):
        fused[key] = fused.get(key, 0.0) + W_LEXICAL / (RRF_K + rank)
    return sorted(fused.items(), key=lambda kv: -kv[1])[:limit]


def hybrid_search(q, limit=15):
    """Public entry. Returns:
        {"results": [{"surah","ayah","score","matched_because":{...}}...],
         "degraded": bool, "engine": str}
    Never raises for a normal query; always returns something searchable."""
    q = (q or "").strip()
    if not q:
        return {"results": [], "degraded": False, "engine": "none"}

    pool = max(limit * 3, 30)
    lexical = lexical_search(q, pool)
    lexical_keys = [(c, v) for c, v, _ in lexical]
    lex_score = {(c, v): s for c, v, s in lexical}

    q_vec = embed_query(q)  # None if Voyage down / no key / v2 not ready
    if q_vec is not None:
        dense = _dense_search(q_vec, pool)
        dense_keys = [(c, v) for c, v, _, _ in dense]
        dense_meta = {(c, v): (s, dt) for c, v, s, dt in dense}
        fused = _rrf(dense_keys, lexical_keys, limit)
        engine, degraded = "v2-hybrid", False
    else:
        # Degrade: v1 MiniLM (English) dense arm + lexical. But v1 is an
        # English-only encoder — feeding it an Arabic query yields noise, so for
        # Arabic we drop the v1 arm and lean on lexical (root) matching instead.
        import app
        if _ARABIC_RE.search(q):
            v1 = []
        else:
            try:
                v1 = app._semantic_search(q, pool)  # [(ch, v, score, snippet)]
            except Exception:
                v1 = []
        dense_keys = [(c, v) for c, v, _s, _snip in v1]
        dense_meta = {(c, v): (float(s), "en") for c, v, s, _snip in v1}
        if dense_keys or lexical_keys:
            fused = _rrf(dense_keys, lexical_keys, limit)
        else:
            fused = [(k, s) for k, s in [((c, v), s) for c, v, s in lexical]][:limit]
        engine = "v1+lexical" if dense_keys else "lexical"
        degraded = True

    results = []
    for (ch, v), score in fused:
        mb = {}
        if (ch, v) in dense_meta:
            ds, dt = dense_meta[(ch, v)]
            mb["dense"] = {"score": round(ds, 4), "doc_type": dt}
        if (ch, v) in lex_score:
            mb["lexical"] = {"score": round(lex_score[(ch, v)], 4)}
        results.append({"surah": ch, "ayah": v, "score": round(score, 6),
                        "matched_because": mb})
    return {"results": results, "degraded": degraded, "engine": engine}
