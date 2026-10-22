"""Mine candidate Qur'anic expressions from the morphology table, for free.

Six kinds, each a deterministic pattern an LLM later judges and explains
(expressions_ai.py):

  mirror    one verb root used twice in a verse, the action passing between
            parties: "remember Me, I will remember you" (2:152)
  family    two content lemmas that keep appearing together across contexts:
            faḍḍala ... baʿḍ (2:253, 4:32, 4:34, 13:4, 16:71, 17:21, 17:55)
  twin      near-identical verses that differ by a word or two (22:62 / 31:30)
  closing   the pair of divine names that ends a verse, incl. order flips
            (ʿalīm ḥakīm / ḥakīm ʿalīm)
  contrast  two roots that keep being set against each other in one verse
  frame     a fixed formula with a changing slot ("what will make you know
            what ___ is")

    python expressions_mine.py --db .../quran.db --out candidates.json
"""
import argparse
import collections
import difflib
import json
import math
import os
import re
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")
CONTENT = {"N", "V", "ADJ"}
ALLAH = "{ll~ah"


def load_words(conn):
    """(ch, v) -> [word dicts in order], one per word_pos (its stem segment).

    `form` is the word as printed in the Uthmani text when the token count
    lines up (all but a handful of verses); the morphology forms carry
    annotation marks (@ ^ #) that must not reach readers."""
    verses = collections.defaultdict(dict)
    for ch, v, wp, seg, form, tag, root, lemma, feats in conn.execute(
            "SELECT chapter, verse, word_pos, segment, form_arabic, tag, root_buckwalter, "
            "lemma_buckwalter, features_raw FROM morphology ORDER BY chapter, verse, word_pos, segment"):
        w = verses[(ch, v)].setdefault(wp, {"pos": wp, "form": "", "tag": None, "root": None,
                                             "lemma": None, "feats": ""})
        w["form"] += form or ""
        if tag not in ("PREFIX", "SUFFIX") and w["tag"] is None:
            w.update(tag=tag, root=root, lemma=lemma, feats=feats or "")
    from alt_translations_ai import strip_basmala
    out = {k: [d[p] for p in sorted(d)] for k, d in verses.items()}
    for ch, v, text in conn.execute("SELECT chapter, verse, text_uthmani FROM verses"):
        toks = strip_basmala(conn, text, ch, v).split()
        ws = out.get((ch, v), [])
        if len(toks) == len(ws):
            for w, t in zip(ws, toks):
                w["form"] = t
        else:
            for w in ws:
                w["form"] = re.sub(r"[@^#.]", "", w["form"])
    return out


def person(feats):
    m = re.search(r"\|([123][MF]?[SDP])(?:\||$)", "|" + feats)
    return m.group(1) if m else None


def span(words, a, b, cap=10):
    a, b = min(a, b), max(a, b)
    b = min(b, a + cap - 1)
    return " ".join(w["form"] for w in words[a:b + 1])


def mine_mirror(V):
    out = []
    for (ch, v), ws in V.items():
        by_root = collections.defaultdict(list)
        for i, w in enumerate(ws):
            if w["tag"] == "V" and w["root"]:
                by_root[w["root"]].append(i)
        has_allah = any(w["lemma"] == ALLAH for w in ws)
        for root, idx in by_root.items():
            if len(idx) < 2:
                continue
            persons = {person(ws[i]["feats"]) for i in idx}
            score = 1.0
            score += 2 if len({p[0] for p in persons if p}) >= 2 else 0   # I/you/they swap
            score += 1.5 if has_allah or any(p and p[0] == "1" for p in persons) else 0
            score += 1 if idx[-1] - idx[0] <= 6 else 0                      # tight, quotable
            out.append({"kind": "mirror", "key": f"{ch}:{v}:{root}", "root": root,
                        "phrase": span(ws, idx[0], idx[-1]), "refs": [f"{ch}:{v}"],
                        "score": score})
    return out


def mine_family(V, idf):
    pairs = collections.defaultdict(set)
    first = {}
    for (ch, v), ws in V.items():
        for i, a in enumerate(ws):
            if a["tag"] not in CONTENT or not a["lemma"] or a["lemma"] == ALLAH:
                continue
            for j in range(i + 1, min(i + 5, len(ws))):
                b = ws[j]
                if b["tag"] not in CONTENT or not b["lemma"] or b["lemma"] == ALLAH:
                    continue
                k = (a["lemma"], b["lemma"])
                pairs[k].add((ch, v))
                first.setdefault(k, ((ch, v), i, j))
    out = []
    for k, refs in pairs.items():
        n, surahs = len(refs), len({r[0] for r in refs})
        if not (3 <= n <= 15) or surahs < 2:
            continue
        (ch, v), i, j = first[k]
        score = (idf.get(k[0], 0) + idf.get(k[1], 0)) * math.log(1 + surahs)
        out.append({"kind": "family", "key": "|".join(k), "lemmas": list(k),
                    "phrase": span(V[(ch, v)], i, j), "refs": [f"{a}:{b}" for a, b in sorted(refs)],
                    "score": round(score, 3)})
    # Collapse pairs that are really one family (same verses, e.g. the two
    # halves of a fixed phrase): keep the best-scoring pair per verse set.
    out.sort(key=lambda c: -c["score"])
    kept, seen = [], []
    for c in out:
        s = set(c["refs"])
        if any(len(s & t) / len(s | t) >= 0.6 for t in seen):
            continue
        seen.append(s)
        kept.append(c)
    return kept


def mine_twin(V):
    seqs = {k: [w["lemma"] for w in ws if w["lemma"]] for k, ws in V.items()}
    idx = collections.defaultdict(set)
    for k, s in seqs.items():
        if len(s) >= 6:
            for i in range(len(s) - 3):
                idx[tuple(s[i:i + 4])].add(k)
    pairs = set()
    for ks in idx.values():
        if 2 <= len(ks) <= 12:
            ks = sorted(ks)
            pairs.update((ks[i], ks[j]) for i in range(len(ks)) for j in range(i + 1, len(ks)))
    out = []
    for a, b in pairs:
        r = difflib.SequenceMatcher(None, seqs[a], seqs[b]).ratio()
        if 0.7 <= r < 1.0 and max(len(seqs[a]), len(seqs[b])) >= 8:
            out.append({"kind": "twin", "key": f"{a[0]}:{a[1]}~{b[0]}:{b[1]}",
                        "phrase": span(V[a], 0, len(V[a]) - 1, cap=12),
                        "refs": [f"{a[0]}:{a[1]}", f"{b[0]}:{b[1]}"],
                        # most instructive: nearly the same, but a real difference
                        "score": round(1 - abs(r - 0.88), 3), "ratio": round(r, 3)})
    return out


def mine_closing(V):
    pairs = collections.defaultdict(list)
    forms = {}
    for (ch, v), ws in V.items():
        stems = [w for w in ws if w["tag"]]
        if len(stems) >= 2 and stems[-1]["tag"] == "ADJ" and stems[-2]["tag"] == "ADJ":
            k = (stems[-2]["lemma"], stems[-1]["lemma"])
            pairs[k].append(f"{ch}:{v}")
            forms.setdefault(k, f"{stems[-2]['form']} {stems[-1]['form']}")
    out = []
    for k, refs in pairs.items():
        flip = pairs.get((k[1], k[0]), [])
        if len(refs) < 2 or (flip and k > (k[1], k[0])):
            continue  # one candidate per unordered pair
        score = math.log(1 + len(refs) + len(flip)) + (3 if flip else 0)
        out.append({"kind": "closing", "key": "|".join(k), "phrase": forms[k],
                    "flip_phrase": forms.get((k[1], k[0])), "refs": refs, "flip_refs": flip,
                    "score": round(score, 3)})
    return out


def mine_contrast(V, root_ar):
    roots_in = collections.defaultdict(set)
    co = collections.Counter()
    for k, ws in V.items():
        rs = sorted({w["root"] for w in ws if w["root"] and w["tag"] in CONTENT})
        for r in rs:
            roots_in[r].add(k)
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                co[(rs[i], rs[j])] += 1
    N = len(V)
    out = []
    for (a, b), n in co.items():
        if n < 4:
            continue
        pmi = math.log(n * N / (len(roots_in[a]) * len(roots_in[b])))
        if pmi < 0.8:  # opposites like light/darkness co-occur less than collocations
            continue
        refs = sorted(roots_in[a] & roots_in[b])
        out.append({"kind": "contrast", "key": f"{a}|{b}", "roots": [a, b],
                    "phrase": f"{root_ar.get(a, a)} × {root_ar.get(b, b)}",
                    "refs": [f"{x}:{y}" for x, y in refs], "score": round(pmi * math.log(1 + n), 3)})
    return out


def mine_frame(V):
    grams = collections.defaultdict(list)
    for (ch, v), ws in V.items():
        for i in range(len(ws) - 3):
            g = ws[i:i + 3]
            if not all(w["lemma"] for w in g) or not any(w["tag"] in CONTENT for w in g):
                continue
            slot = next((w for w in ws[i + 3:i + 5] if w["tag"] in CONTENT and w["lemma"]), None)
            if slot:
                grams[tuple(w["lemma"] for w in g)].append((ch, v, i, slot["lemma"], slot["form"]))
    out = []
    for g, occ in grams.items():
        fills = {o[3] for o in occ}
        if not (4 <= len(occ) <= 40) or not (3 <= len(fills) <= 25):
            continue
        ch, v, i, _, _ = occ[0]
        out.append({"kind": "frame", "key": "|".join(g), "phrase": span(V[(ch, v)], i, i + 2),
                    "refs": sorted({f"{o[0]}:{o[1]}" for o in occ}),
                    "fills": sorted({o[4] for o in occ})[:25],
                    "score": round(len(fills) / len(occ) * math.log(1 + len(occ)), 3)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=400, help="candidates kept per kind")
    a = ap.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    V = load_words(conn)
    df = collections.Counter(l for ws in V.values() for l in {w["lemma"] for w in ws if w["lemma"]})
    idf = {l: math.log(len(V) / n) for l, n in df.items()}
    root_ar = dict(conn.execute(
        "SELECT DISTINCT root_buckwalter, root_arabic FROM morphology WHERE root_buckwalter IS NOT NULL"))
    result = {}
    for kind, cands in [("mirror", mine_mirror(V)), ("family", mine_family(V, idf)),
                        ("twin", mine_twin(V)), ("closing", mine_closing(V)),
                        ("contrast", mine_contrast(V, root_ar)), ("frame", mine_frame(V))]:
        cands.sort(key=lambda c: -c["score"])
        print(f"{kind:9} {len(cands):6} candidates")
        result[kind] = cands[:a.top]
    with open(a.out, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
