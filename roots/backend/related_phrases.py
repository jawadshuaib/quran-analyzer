"""Verses related to a selected phrase — the /related/<s>:<a>/<words> pages.

A reader selects (or has highlighted) some words of a verse; this ranks the
other verses of the Qur'an by how close they are in meaning to THOSE words,
not to the whole verse. A selection is one or more runs of Arabic word
positions, 1-indexed over the verse's `text_uthmani.split()` tokens (the same
positions the highlight store and the morphology table use), written in the
URL as "1-4" or "1-4,15-21".

Ranking (the prototype that chose it is summarised in the commit):
  1. Candidates: the Arabic phrase embedded with the Voyage model behind hybrid
     search, scored against every verse's Arabic vector (search_v2's matrix),
     unioned with the verses that share the phrase's lemmas/roots (IDF).
  2. Rerank: Voyage's reranker reads the phrase (Arabic + our word glosses)
     against each candidate (Arabic + our translation). Verse vectors embed
     the WHOLE verse, so a long verse holding the phrase's idea in one clause
     scores low on cosine alone; the reranker reads the clause.
  3. Final score = rerank relevance + a small bonus for shared lemmas/roots,
     so verses that reuse the phrase's own wording edge ahead of loose
     paraphrases.

Both Voyage calls cost money, so a reranked result is cached in
related_phrase_cache keyed by the canonical selection and is never computed
twice. When Voyage is unreachable, or the hourly spend caps are hit, it
degrades to cosine + lexical (or lexical alone) and that result is only held
in memory for a few minutes, so the page retries the full ranking later.

app.py provides (via a deferred `import app`): get_db, the IDF engine globals,
_strip_bismillah, _best_translation, _surah_name and search_v2.
"""

import json
import re
import threading
import time
from collections import OrderedDict

import numpy as np
import requests

ENGINE = "rerank-v1"            # bump to recompute every cached ranking
RERANK_URL = "https://api.voyageai.com/v1/rerank"
RERANK_MODEL = "rerank-2.5-lite"
CANDIDATES_PER_ARM = 60
RESULT_LIMIT = 20
RERANK_FLOOR = 0.35             # below this the reranker is saying "unrelated"
DENSE_FLOOR = 0.30
LEX_BONUS = 0.10                # weight of shared wording in the final score
LEX_BLEND = 0.25                # weight of shared wording in the candidate arm
MAX_RUNS = 8

# Spend guard on cache misses (each rerank reads ~100 verses, ~30k tokens).
RERANK_HOURLY_MAX = 240
RERANK_HOURLY_PER_IP = 30

# Words that carry no meaning of their own for this purpose.
_SKIP_LEMMAS = {"{ll~ah"}
_SKIP_ROOTS = {"Alh"}

_SEL_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")


# --------------------------------------------------------------------------
# Selections
# --------------------------------------------------------------------------
def parse_selection(sel):
    """'1-4,15-21' -> [(1, 4), (15, 21)] sorted, overlaps/neighbours merged.
    None when it isn't a selection at all."""
    if not sel or len(sel) > 120 or not _SEL_RE.match(sel):
        return None
    runs = []
    for part in sel.split(","):
        a, _, b = part.partition("-")
        a = int(a)
        b = int(b) if b else a
        if a < 1 or b < a:
            return None
        runs.append((a, b))
    runs.sort()
    merged = [list(runs[0])]
    for a, b in runs[1:]:
        if a <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    if len(merged) > MAX_RUNS:
        return None
    return [(a, b) for a, b in merged]


def format_selection(runs):
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in runs)


_tokens_cache = OrderedDict()
_tokens_lock = threading.Lock()


def verse_tokens(surah, ayah, conn=None):
    """The verse's Arabic words as every page renders them (basmala stripped
    from a surah's first verse), or None for a verse that doesn't exist."""
    key = (surah, ayah)
    with _tokens_lock:
        if key in _tokens_cache:
            _tokens_cache.move_to_end(key)
            return _tokens_cache[key]
    import app
    own = conn is None
    if own:
        conn = app.get_db()
    try:
        row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (surah, ayah),
        ).fetchone()
    finally:
        if own:
            conn.close()
    toks = app._strip_bismillah(row["text_uthmani"], surah, ayah).split() if row else None
    with _tokens_lock:
        _tokens_cache[key] = toks
        while len(_tokens_cache) > 2048:
            _tokens_cache.popitem(last=False)
    return toks


def resolve(surah, ayah, sel):
    """(runs, canonical selection string) for a valid selection of an existing
    verse, else None. The canonical form may differ from `sel` (sorted, merged,
    "5-5" -> "5"); callers redirect to it."""
    runs = parse_selection(sel)
    if runs is None:
        return None
    toks = verse_tokens(surah, ayah)
    if not toks or runs[-1][1] > len(toks):
        return None
    return runs, format_selection(runs)


def path_for(surah, ayah, selection):
    return f"/related/{surah}:{ayah}/{selection}"


# --------------------------------------------------------------------------
# The phrase: its words, glosses, lemmas and roots
# --------------------------------------------------------------------------
def _word_glosses(conn, surah, ayah):
    """pos -> the English label the word-by-word view shows for each word."""
    out = {}
    for r in conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ):
        if r["translation_en"]:
            out[r["word_pos"]] = r["translation_en"]
    for r in conn.execute(
        "SELECT wm.word_pos, wm.preferred_translation, wm.meaning_short "
        "FROM ai_word_meanings wm JOIN ("
        "  SELECT word_pos, MAX(created_at) AS mc FROM ai_word_meanings "
        "  WHERE chapter = ? AND verse = ? GROUP BY word_pos"
        ") l ON wm.word_pos = l.word_pos AND wm.created_at = l.mc "
        "WHERE wm.chapter = ? AND wm.verse = ?",
        (surah, ayah, surah, ayah),
    ):
        label = r["preferred_translation"] or r["meaning_short"]
        if label:
            out[r["word_pos"]] = label
    return out


def phrase_info(conn, surah, ayah, runs):
    """Arabic + gloss per run, and the content lemmas/roots the runs hold."""
    toks = verse_tokens(surah, ayah, conn) or []
    glosses = _word_glosses(conn, surah, ayah)
    out_runs = []
    for a, b in runs:
        out_runs.append({
            "start": a,
            "end": b,
            "arabic": " ".join(toks[a - 1:b]),
            "gloss": " ".join(glosses[p] for p in range(a, b + 1) if glosses.get(p)),
        })
    positions = [p for a, b in runs for p in range(a, b + 1)]
    lemmas, roots = set(), set()
    if positions:
        qmarks = ",".join("?" * len(positions))
        for r in conn.execute(
            "SELECT lemma_buckwalter, root_buckwalter FROM morphology "
            f"WHERE chapter = ? AND verse = ? AND word_pos IN ({qmarks}) "
            "AND root_buckwalter IS NOT NULL AND root_buckwalter != ''",
            (surah, ayah, *positions),
        ):
            if r["root_buckwalter"] not in _SKIP_ROOTS:
                roots.add(r["root_buckwalter"])
                if r["lemma_buckwalter"] and r["lemma_buckwalter"] not in _SKIP_LEMMAS:
                    lemmas.add(r["lemma_buckwalter"])
    return {"runs": out_runs, "lemmas": lemmas, "roots": roots}


# --------------------------------------------------------------------------
# Scoring arms
# --------------------------------------------------------------------------
def _lexical_scores(lemmas, roots):
    """(ch, v) -> share of the phrase's IDF-weighted wording the verse holds,
    0..1 (a lemma counts fully, its root again at half weight)."""
    import app
    lidf, ridf = app._lemma_idf, app._root_idf
    discount = getattr(app, "ROOT_DISCOUNT", 0.5)
    total = sum(lidf.get(l, 0.0) for l in lemmas) + discount * sum(ridf.get(r, 0.0) for r in roots)
    if total <= 0:
        return {}
    scores = {}
    for l in lemmas:
        w = lidf.get(l, 0.0)
        for key in app._lemma_inv.get(l, ()):
            scores[key] = scores.get(key, 0.0) + w
    for r in roots:
        w = discount * ridf.get(r, 0.0)
        for key in app._root_inv.get(r, ()):
            scores[key] = scores.get(key, 0.0) + w
    return {k: s / total for k, s in scores.items()}


_ar_index = {"model": None, "rows": None, "keys": None}


def _arabic_rows():
    """Row indices + (ch, v) keys of the Arabic doc vectors in search_v2's
    matrix, or (None, None) when the v2 index isn't loaded."""
    import app
    sv2 = getattr(app, "search_v2", None)
    if sv2 is None or not sv2._v2_ready or sv2._v2_matrix is None:
        return None, None
    if _ar_index["model"] != (sv2._v2_model, sv2._v2_matrix.shape):
        rows, keys = [], []
        for key, idx in sv2._v2_verse_rows.items():
            for i in idx:
                if sv2._v2_doc_type[i] == "ar":
                    rows.append(int(i))
                    keys.append(key)
        _ar_index.update(model=(sv2._v2_model, sv2._v2_matrix.shape),
                         rows=np.array(rows, dtype=np.int64), keys=keys)
    return _ar_index["rows"], _ar_index["keys"]


def _dense_scores(arabic_query):
    """(ch, v) -> cosine of the Arabic phrase to the verse's Arabic vector, or
    {} when the phrase can't be embedded (no key, Voyage down, no index)."""
    import app
    sv2 = getattr(app, "search_v2", None)
    rows, keys = _arabic_rows()
    if rows is None or not len(rows):
        return {}
    q = sv2.embed_query(arabic_query)
    if q is None:
        return {}
    sims = sv2._v2_matrix[rows] @ q
    return dict(zip(keys, sims.tolist()))


def _top(scores, n, exclude):
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return [k for k, _s in ranked if k != exclude][:n]


# --------------------------------------------------------------------------
# Rerank (Voyage) with a spend guard
# --------------------------------------------------------------------------
_rerank_sema = threading.BoundedSemaphore(2)
_spend_lock = threading.Lock()
_spend_global = []      # timestamps of reranks in the last hour
_spend_by_ip = {}       # ip -> [timestamps]


def _spend_allowed(ip):
    now = time.time()
    with _spend_lock:
        _spend_global[:] = [t for t in _spend_global if now - t < 3600]
        if len(_spend_by_ip) > 5000:
            _spend_by_ip.clear()
        mine = [t for t in _spend_by_ip.get(ip, []) if now - t < 3600]
        if len(_spend_global) >= RERANK_HOURLY_MAX or len(mine) >= RERANK_HOURLY_PER_IP:
            _spend_by_ip[ip] = mine
            return False
        _spend_global.append(now)
        mine.append(now)
        _spend_by_ip[ip] = mine
        return True


def _rerank(query, documents):
    """[relevance per document] in input order, or None on any problem."""
    import app
    sv2 = getattr(app, "search_v2", None)
    api_key = sv2._get_voyage_api_key() if sv2 is not None else ""
    if not api_key or not documents:
        return None
    if not _rerank_sema.acquire(timeout=2):
        return None
    try:
        r = requests.post(
            RERANK_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"query": query, "documents": documents, "model": RERANK_MODEL},
            timeout=(3.05, 20),
        )
        if r.status_code != 200:
            print(f"[related] rerank HTTP {r.status_code}: {r.text[:200]}", flush=True)
            return None
        out = [0.0] * len(documents)
        for d in r.json()["data"]:
            out[d["index"]] = float(d["relevance_score"])
        return out
    except Exception as exc:
        print(f"[related] rerank failed: {exc}", flush=True)
        return None
    finally:
        _rerank_sema.release()


# --------------------------------------------------------------------------
# Ranking + cache
# --------------------------------------------------------------------------
def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS related_phrase_cache (
            surah INTEGER NOT NULL,
            ayah INTEGER NOT NULL,
            selection TEXT NOT NULL,       -- canonical, e.g. "1-4,15-21"
            engine TEXT NOT NULL,          -- ENGINE that ranked it
            ranking_json TEXT NOT NULL,    -- [[surah, ayah, score], ...]
            created_at TEXT DEFAULT (datetime('now')),
            hits INTEGER NOT NULL DEFAULT 0,
            last_hit_at TEXT,
            PRIMARY KEY (surah, ayah, selection)
        )
    """)
    conn.commit()


def _rank(conn, surah, ayah, info, ip):
    """[(ch, v, score)], engine. Computes; doesn't touch the cache."""
    import app
    src = (surah, ayah)
    arabic_q = " … ".join(r["arabic"] for r in info["runs"])
    lex = _lexical_scores(info["lemmas"], info["roots"])
    dense = _dense_scores(arabic_q)

    if dense:
        blend = {k: s + LEX_BLEND * lex.get(k, 0.0) for k, s in dense.items()}
        cands = []
        for k in (_top(dense, CANDIDATES_PER_ARM, src) + _top(blend, CANDIDATES_PER_ARM, src)
                  + _top(lex, CANDIDATES_PER_ARM, src)):
            if k not in cands:
                cands.append(k)
    else:
        blend = {}
        cands = _top(lex, CANDIDATES_PER_ARM * 2, src)

    if cands and _spend_allowed(ip):
        gloss_q = " … ".join(r["gloss"] for r in info["runs"] if r["gloss"])
        query = arabic_q + (f"\n({gloss_q})" if gloss_q else "")
        docs = []
        for ch, v in cands:
            toks = verse_tokens(ch, v, conn) or []
            docs.append(" ".join(toks) + "\n" + (app._best_translation(conn, ch, v) or ""))
        rel = _rerank(query, docs)
        if rel is not None:
            scored = [(ch, v, r + LEX_BONUS * lex.get((ch, v), 0.0), r)
                      for (ch, v), r in zip(cands, rel)]
            scored = [s for s in scored if s[3] >= RERANK_FLOOR]
            scored.sort(key=lambda s: -s[2])
            return [(ch, v, round(s, 4)) for ch, v, s, _r in scored[:RESULT_LIMIT]], ENGINE

    if blend:
        ranked = [(k, s) for k, s in blend.items() if k != src and dense.get(k, 0.0) >= DENSE_FLOOR]
        ranked.sort(key=lambda kv: -kv[1])
        return [(ch, v, round(s, 4)) for (ch, v), s in ranked[:RESULT_LIMIT]], "dense+lexical"
    ranked = [(k, s) for k, s in sorted(lex.items(), key=lambda kv: -kv[1]) if k != src]
    return [(ch, v, round(s, 4)) for (ch, v), s in ranked[:RESULT_LIMIT]], "lexical"


_degraded = OrderedDict()       # (s, a, sel) -> (ts, ranking, engine)
_DEGRADED_TTL = 600


def cached_ranking(conn, surah, ayah, selection):
    """The stored full ranking for this selection, or None."""
    try:
        row = conn.execute(
            "SELECT ranking_json, engine FROM related_phrase_cache "
            "WHERE surah = ? AND ayah = ? AND selection = ?",
            (surah, ayah, selection),
        ).fetchone()
    except Exception:
        return None
    if not row or row["engine"] != ENGINE:
        return None
    return [tuple(x) for x in json.loads(row["ranking_json"])]


def get_ranking(conn, surah, ayah, runs, selection, info, ip):
    """(ranking, engine, cached) — from the cache when it can be."""
    ranking = cached_ranking(conn, surah, ayah, selection)
    if ranking is not None:
        try:
            conn.execute(
                "UPDATE related_phrase_cache SET hits = hits + 1, last_hit_at = datetime('now') "
                "WHERE surah = ? AND ayah = ? AND selection = ?",
                (surah, ayah, selection),
            )
            conn.commit()
        except Exception:
            pass
        return ranking, ENGINE, True

    key = (surah, ayah, selection)
    hit = _degraded.get(key)
    if hit and time.time() - hit[0] < _DEGRADED_TTL:
        return hit[1], hit[2], True

    ranking, engine = _rank(conn, surah, ayah, info, ip)
    if engine == ENGINE:
        conn.execute(
            "INSERT OR REPLACE INTO related_phrase_cache "
            "(surah, ayah, selection, engine, ranking_json, hits, last_hit_at) "
            "VALUES (?, ?, ?, ?, ?, 1, datetime('now'))",
            (surah, ayah, selection, engine, json.dumps(ranking)),
        )
        conn.commit()
        _degraded.pop(key, None)
    else:
        _degraded[key] = (time.time(), ranking, engine)
        while len(_degraded) > 500:
            _degraded.popitem(last=False)
    return ranking, engine, False


def shape_results(conn, ranking, roots):
    """Each ranked verse with its text, our translation, and which of its
    words share a root with the phrase (so the page can mark them)."""
    import app
    out = []
    for ch, v, score in ranking:
        matched, shared = [], []
        if roots:
            qmarks = ",".join("?" * len(roots))
            for r in conn.execute(
                "SELECT DISTINCT word_pos, root_buckwalter FROM morphology "
                f"WHERE chapter = ? AND verse = ? AND root_buckwalter IN ({qmarks}) "
                "ORDER BY word_pos",
                (ch, v, *sorted(roots)),
            ):
                if r["word_pos"] not in matched:
                    matched.append(r["word_pos"])
                if r["root_buckwalter"] not in shared:
                    shared.append(r["root_buckwalter"])
        out.append({
            "surah": ch,
            "ayah": v,
            "surah_name": app._surah_name(ch),
            "text_uthmani": " ".join(verse_tokens(ch, v, conn) or []),
            "translation": app._best_translation(conn, ch, v),
            "score": score,
            "matched_positions": matched,
            "shared_roots": [
                {"root_buckwalter": r, "root_arabic": app._root_arabic_map.get(r, "")}
                for r in shared
            ],
        })
    return out


def sitemap_paths(conn, limit=5000):
    """Paths of the selections readers have opened, most visited first."""
    try:
        rows = conn.execute(
            "SELECT surah, ayah, selection FROM related_phrase_cache WHERE engine = ? "
            "ORDER BY hits DESC, created_at LIMIT ?",
            (ENGINE, limit),
        ).fetchall()
    except Exception:
        return []
    return [path_for(r["surah"], r["ayah"], r["selection"]) for r in rows]
