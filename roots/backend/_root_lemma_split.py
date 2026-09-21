#!/usr/bin/env python3
"""Which roots need a SEPARATE explanation per lemma?

A reader hovers a word, not a root. For most roots one explanation serves every
word -- sabara, sabir and sabr are one idea in three grammatical shapes. But for
a minority the radicals carry genuinely different words: tarf is a glance and
taraf is an edge, dhahaba is to depart and dhahab is gold. One passage cannot
serve both, and the reader on 11:114 wants the edge while the reader on 55:56
wants the glance.

THE TEST. Compare the conventional per-word glosses of each substantial lemma.
Two lemmas are DIFFERENT WORDS when their gloss vocabulary is disjoint; they are
ONE WORD when it overlaps. Deterministic, no model, and it uses data we already
have for every root-bearing token.

Two corrections were needed before it worked, both found by validating against
roots whose answer was already known:

  * STEM, DON'T MATCH WHOLE WORDS. "patience" and "patient" are the same word to
    a reader and different strings to a computer. Comparing 5-char stems fixes
    s-b-r, which was being split into "patience" and "the patient ones".
  * BRIDGE ENGLISH SUPPLETION. h-s-n's outlier lemma is the elative ahsan,
    glossed "best"/"better" -- the same sense as "good" but with no letters in
    common, because English grades good/better/best irregularly. A small bridge
    table collapses these.
"""
import collections
import os
import re
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')
STOP = set("the a an of to and or in on for with is are be by from that this his her its their you "
           "they we he she it not no your our them us who whom which what when will would has have "
           "had was were been being do does did so then than there here into upon".split())
# English grades the same idea with unrelated words; Arabic does it with one root.
SUPPLETION = {'best': 'good', 'better': 'good', 'worse': 'bad', 'worst': 'bad',
              'more': 'many', 'most': 'many', 'less': 'few', 'least': 'few',
              'greater': 'great', 'greatest': 'great', 'elder': 'old', 'eldest': 'old'}
STEM_LEN = 5
MIN_VERSES = 3        # a lemma below this cannot carry its own explanation
MIN_SHARE = 0.03      # nor one that is a rounding error within its root

# WHY CLUSTERING, NOT PAIRWISE. The divergence is between SENSE GROUPS, not
# between individual lemmas. q-w-m splits into qawm ("a people", 56% of the
# root) and a SEVEN-lemma family about standing -- qiyama, aqama, mustaqim,
# qama, qa'im, maqam, muqim -- none of which individually clears a share
# threshold. Comparing lemmas two at a time cannot see that shape. So: build a
# graph where lemmas are joined when their gloss stems overlap, and take the
# connected components. Each component is one sense of the root.

def _stems(text):
    out = set()
    for w in re.findall(r"[a-z]+", (text or '').lower()):
        if w in STOP or len(w) < 3:
            continue
        w = SUPPLETION.get(w, w)
        out.add(w[:STEM_LEN])
    return out


def analyse(conn=None):
    c = conn or sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    stems = collections.defaultdict(lambda: collections.defaultdict(set))
    counts = collections.defaultdict(collections.Counter)
    for r in c.execute("""SELECT m.root_buckwalter bw, m.lemma_arabic lem, g.translation_en gl
                          FROM morphology m JOIN word_glosses g
                            ON g.chapter=m.chapter AND g.verse=m.verse AND g.word_pos=m.word_pos
                          WHERE m.root_buckwalter NOT IN ('','-') AND m.root_buckwalter IS NOT NULL
                            AND m.lemma_arabic IS NOT NULL AND m.lemma_arabic!=''
                            AND g.translation_en IS NOT NULL"""):
        stems[r['bw']][r['lem']] |= _stems(r['gl'])
        counts[r['bw']][r['lem']] += 1
    out = {}
    for bw, lemc in counts.items():
        tot = sum(lemc.values())
        lems = [l for l, n in lemc.items()
                if n >= MIN_VERSES and n / tot >= MIN_SHARE and stems[bw][l]]
        if len(lems) < 2:
            continue
        # Union-find over lemmas: joined when they share any gloss stem.
        parent = {l: l for l in lems}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i, a in enumerate(lems):
            for b in lems[i + 1:]:
                if stems[bw][a] & stems[bw][b]:
                    parent[find(a)] = find(b)
        comps = collections.defaultdict(list)
        for l in lems:
            comps[find(l)].append(l)
        # A component earns its own explanation when it carries real weight.
        groups = []
        for members in comps.values():
            n = sum(lemc[m] for m in members)
            if n >= MIN_VERSES and n / tot >= MIN_SHARE:
                groups.append({'lemmas': sorted(members, key=lambda m: -lemc[m]),
                               'verses': n, 'share': round(n / tot, 3)})
        if len(groups) >= 2:
            groups.sort(key=lambda g: -g['verses'])
            out[bw] = {'groups': groups, 'total': tot}
    return out


if __name__ == '__main__':
    import sys
    res = analyse()
    import sqlite3 as _s
    _c = _s.connect(DB)
    counts_total = {r[0] for r in _c.execute("SELECT DISTINCT root_buckwalter FROM morphology WHERE root_buckwalter NOT IN ('','-') AND root_buckwalter IS NOT NULL")}
    truth = {'Trf': 'split', '*hb': 'split', '*kr': 'split', 'qwm': 'split',
             'Sbr': 'one', 'Swm': 'one', 'Hsn': 'one', 'zlf': 'one', 'Slw': 'one'}
    print("VALIDATION:")
    ok = 0
    for bw, want in truth.items():
        got = 'split' if bw in res else 'one'
        ok += got == want
        detail = ''
        if bw in res:
            detail = ' | '.join('%s(%d)' % ('+'.join(g['lemmas'][:3]), g['verses'])
                                for g in res[bw]['groups'])
        print("   %-5s want=%-6s got=%-6s %-4s %s" % (bw, want, got, 'OK' if got == want else 'MISS', detail[:96]))
    print("   -> %d/%d\n" % (ok, len(truth)))
    print("roots needing a per-lemma split: %d of %d (%.0f%%)"
          % (len(res), len(counts_total), 100 * len(res) / len(counts_total)))
    print("total explanations if we split: %d (vs %d root-level)"
          % (sum(len(v['groups']) for v in res.values()) + (len(counts_total) - len(res)), len(counts_total)))
    if '--list' in sys.argv:
        print()
        for bw, v in sorted(res.items(), key=lambda x: -x[1]['total'])[:20]:
            print("   %-6s %s" % (bw, ' | '.join('%s(%d)' % ('+'.join(g['lemmas'][:2]), g['verses'])
                                                 for g in v['groups'])[:100]))
