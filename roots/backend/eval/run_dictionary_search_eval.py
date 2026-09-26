#!/usr/bin/env python3
"""Score /api/dictionary/search against eval/dictionary_search_eval.json.

  python3 eval/run_dictionary_search_eval.py                       # local backend
  python3 eval/run_dictionary_search_eval.py --api https://al-nuqta.com
  python3 eval/run_dictionary_search_eval.py --only english-word --show-pass

A query passes when any expected root is within its top k (k=0 with an
empty expectation: passes when nothing is returned or nothing crashes).
Prints pass rate and MRR per category, then every failure with what came back.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def fetch(api, q):
    url = f"{api}/api/dictionary/search?q={urllib.parse.quote(q)}&limit=20"
    t = time.time()
    with urllib.request.urlopen(url, timeout=60) as r:
        body = json.loads(r.read().decode("utf-8"))
    return body, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:5000")
    ap.add_argument("--file", default=os.path.join(HERE, "dictionary_search_eval.json"))
    ap.add_argument("--only")
    ap.add_argument("--show-pass", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.file))
    by_cat = defaultdict(lambda: [0, 0, 0.0])
    fails, times, engine = [], [], None
    for item in data["queries"]:
        if a.only and item["category"] != a.only:
            continue
        q, exp, k = item["q"], item.get("expect", []), item.get("k", 1)
        try:
            body, dt = fetch(a.api, q)
        except Exception as e:
            by_cat[item["category"]][1] += 1
            fails.append((item, [f"ERROR {e}"]))
            continue
        times.append(dt)
        engine = body.get("engine", engine)
        got = [r["buckwalter"] for r in body.get("results", [])]
        c = by_cat[item["category"]]
        c[1] += 1
        if not exp:
            ok = True  # robustness: answered without crashing
            rr = 1.0
        else:
            ranks = [got.index(e) + 1 for e in exp if e in got]
            best = min(ranks) if ranks else None
            ok = best is not None and best <= k
            rr = 1.0 / best if best else 0.0
        c[2] += rr
        if ok:
            c[0] += 1
            if a.show_pass:
                print(f"  ok   {q!r} -> {got[:5]}")
        else:
            fails.append((item, got[:8]))
    tot = sum(v[0] for v in by_cat.values()), sum(v[1] for v in by_cat.values())
    print(f"engine: {engine}")
    print(f"{'category':28} pass     MRR")
    for cat, (p, n, rr) in sorted(by_cat.items()):
        print(f"{cat:28} {p:3}/{n:<3}  {rr / max(n, 1):.2f}")
    print(f"{'TOTAL':28} {tot[0]}/{tot[1]}  ({100 * tot[0] / max(tot[1], 1):.1f}%)")
    if times:
        ts = sorted(times)
        print(f"latency: median {1000 * ts[len(ts) // 2]:.0f} ms, p95 {1000 * ts[int(len(ts) * 0.95)]:.0f} ms")
    if fails:
        print("\nFAILURES")
        for item, got in fails:
            print(f"  [{item['category']}] {item['q']!r} expect {item.get('expect')} in top {item.get('k')} — got {got}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
