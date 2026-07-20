"""Retrieval evaluation harness for Qur'an search (Phase B).

Standalone (opens data/quran.db directly — does NOT need the Flask app running).
Scores a retriever against the hand-labeled gold set in eval_gold.json using
recall@k and MRR, broken down by language. Use it to compare the current
English-only MiniLM engine (v1) against the Voyage multilingual hybrid (v2)
BEFORE any production cutover, and to pick the model / dims / threshold /
fusion weights.

Usage:
    python eval_retrieval.py --engine v1                 # MiniLM baseline
    python eval_retrieval.py --engine lexical            # IDF root/lemma arm only
    python eval_retrieval.py --engine v2                 # Voyage hybrid (needs v2 index + key)
    python eval_retrieval.py --engine v2 --model voyage-3-large --dim 1024
    python eval_retrieval.py --engine v1 --engine2 v2    # side-by-side comparison
    python eval_retrieval.py --engine v1 --lang en       # English queries only

Metrics:
    recall@k  — fraction of a query's relevant verses found in the top-k (averaged)
    hit@k     — fraction of queries with >= 1 relevant verse in the top-k
    MRR       — mean reciprocal rank of the first relevant verse
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "quran.db")
GOLD_PATH = os.path.join(HERE, "eval_gold.json")
KS = (5, 10, 20)


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def load_gold(lang=None):
    with open(GOLD_PATH, encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    if lang:
        items = [it for it in items if it["lang"] == lang]
    # Normalize qrels to sets of (ch, v) tuples.
    for it in items:
        it["rel_set"] = {(int(c), int(v)) for c, v in it["relevant"]}
    return items


# --------------------------------------------------------------------------
# Retrievers. Each exposes .name and .retrieve(query, k) -> ranked [(ch, v)].
# --------------------------------------------------------------------------

class V1Retriever:
    """The current production engine: all-MiniLM-L6-v2 over the English
    translation index (verse_embeddings). English-only encoder — expect it to
    do poorly on Arabic queries; that is exactly the gap v2 closes."""

    name = "v1-minilm-en"

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        conn = get_conn()
        try:
            rows = conn.execute(
                "SELECT chapter, verse, embedding FROM verse_embeddings "
                "ORDER BY chapter, verse"
            ).fetchall()
        finally:
            conn.close()
        if not rows:
            raise SystemExit("verse_embeddings is empty — build it first.")
        self.keys = [(r["chapter"], r["verse"]) for r in rows]
        self.matrix = np.vstack(
            [np.frombuffer(r["embedding"], dtype=np.float32) for r in rows]
        )

    def retrieve(self, query, k):
        q = self.model.encode([query], normalize_embeddings=True)
        scores = (self.matrix @ q.T).ravel()
        top = np.argsort(-scores)[:k]
        return [self.keys[i] for i in top]


class V2Retriever:
    """The Voyage multilingual hybrid (dense ar+en + lexical), via search_v2.
    Imports lazily so this harness still runs for v1 before search_v2 exists or
    before the v2 index / API key are in place."""

    def __init__(self, model=None, dim=None):
        try:
            import search_v2
        except Exception as exc:  # pragma: no cover - depends on build state
            raise SystemExit(
                f"Cannot load search_v2 ({exc}). Build the v2 index and set "
                "VOYAGE_API_KEY first (see build_embeddings_v2.py)."
            )
        self._sv2 = search_v2
        self._sv2.load_matrices_v2(model_name=model, dim=dim)
        self.name = f"v2-{self._sv2.active_model_name() or 'voyage'}"

    def retrieve(self, query, k):
        res = self._sv2.hybrid_search(query, limit=k)
        return [(r["surah"], r["ayah"]) for r in res.get("results", [])]


class LexicalRetriever:
    """Lexical arm only (root/lemma IDF), via search_v2's lexical helper.
    A baseline to measure how much the dense arm adds."""

    name = "lexical-idf"

    def __init__(self):
        try:
            import search_v2
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"Cannot load search_v2 ({exc}).")
        self._sv2 = search_v2
        self._sv2.load_matrices_v2()

    def retrieve(self, query, k):
        return [(c, v) for c, v in self._sv2.lexical_search(query, limit=k)]


def build_retriever(engine, model=None, dim=None):
    if engine == "v1":
        return V1Retriever()
    if engine == "v2":
        return V2Retriever(model=model, dim=dim)
    if engine == "lexical":
        return LexicalRetriever()
    raise SystemExit(f"Unknown engine: {engine}")


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def evaluate(retriever, items, ks=KS):
    """Returns {'overall': {...}, 'en': {...}, 'ar': {...}} of metric dicts."""
    maxk = max(ks)
    per_lang = {}
    for it in items:
        ranked = retriever.retrieve(it["query"], maxk)
        rel = it["rel_set"]
        # First-hit rank for MRR.
        rr = 0.0
        for rank, key in enumerate(ranked, start=1):
            if key in rel:
                rr = 1.0 / rank
                break
        row = {"rr": rr}
        for k in ks:
            topk = set(ranked[:k])
            hits = len(topk & rel)
            row[f"recall@{k}"] = hits / len(rel) if rel else 0.0
            row[f"hit@{k}"] = 1.0 if hits > 0 else 0.0
        per_lang.setdefault(it["lang"], []).append(row)
        per_lang.setdefault("overall", []).append(row)

    def agg(rows):
        n = len(rows)
        out = {"n": n, "MRR": sum(r["rr"] for r in rows) / n}
        for k in ks:
            out[f"recall@{k}"] = sum(r[f"recall@{k}"] for r in rows) / n
            out[f"hit@{k}"] = sum(r[f"hit@{k}"] for r in rows) / n
        return out

    return {lang: agg(rows) for lang, rows in per_lang.items()}


def print_report(name, report, ks=KS):
    order = [g for g in ("overall", "en", "ar") if g in report]
    print(f"\n=== {name} ===")
    header = f"{'group':<9}{'n':>4}  {'MRR':>6}"
    for k in ks:
        header += f"  {'R@' + str(k):>7}{'H@' + str(k):>7}"
    print(header)
    for g in order:
        m = report[g]
        line = f"{g:<9}{m['n']:>4}  {m['MRR']:>6.3f}"
        for k in ks:
            line += f"  {m['recall@' + str(k)]:>7.3f}{m['hit@' + str(k)]:>7.3f}"
        print(line)


def main():
    ap = argparse.ArgumentParser(description="Qur'an retrieval eval")
    ap.add_argument("--engine", default="v1", choices=["v1", "v2", "lexical"])
    ap.add_argument("--engine2", default=None, choices=["v1", "v2", "lexical"],
                    help="Second engine to compare side by side")
    ap.add_argument("--lang", default=None, choices=["en", "ar"],
                    help="Restrict to one language")
    ap.add_argument("--model", default=None, help="v2 model name override")
    ap.add_argument("--dim", type=int, default=None, help="v2 dim override")
    args = ap.parse_args()

    items = load_gold(args.lang)
    if not items:
        raise SystemExit("No gold items (check --lang / eval_gold.json).")
    print(f"Loaded {len(items)} gold queries"
          f"{' (' + args.lang + ')' if args.lang else ''}.")

    for eng in [args.engine] + ([args.engine2] if args.engine2 else []):
        t0 = time.time()
        r = build_retriever(eng, model=args.model, dim=args.dim)
        report = evaluate(r, items)
        print_report(r.name, report)
        print(f"({eng} evaluated in {time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
