#!/usr/bin/env python3
"""Calibrate a JUDGE model on planted faults before trusting it on 1,911 rows.

The project's standing rule: never let a model grade real work until it has
been shown it can tell a known-bad from a known-good. Here the faults are
planted into REAL passages against their REAL evidence bundles, because the
judge's whole job is to check a claim against the bundle it came from.

  clean   : the passage as generated, every claim traceable
  cognate : a sister-language gloss swapped for one our rows do not record
  verse   : a verse reference swapped for one the root does not occur in
  invent  : a concrete detail added that appears nowhere in the bundle
  bland   : rewritten to restate the gloss and say nothing else
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SHOW_EXISTING', '0')
import _root_core_bundle as B          # noqa: E402
import _root_core_schema as S          # noqa: E402

HOST = os.environ.get('OLLAMA_HOST', 'https://ollama.com')
KEY = os.environ.get('OLLAMA_API_KEY', '')

JUDGE_SYSTEM = """You audit short explanations of Qur'anic root meanings against
the evidence they were written from. You are given the EVIDENCE and the
PASSAGE. Your only question: is every factual claim in the passage supported by
the evidence?

A claim is UNSUPPORTED if the evidence does not contain it -- a sister-language
word or gloss we do not record, a verse the root does not occur in, a concrete
detail (an animal, a tool, a practice) that appears nowhere in the evidence, or
a lexicographer's opinion not given.

Paraphrase is fine. Compression is fine. Saying "the old poetry" for a named
poet is fine. Inventing specifics is not.

Also judge whether the passage is WORTH SHOWING: it must tell a reader
something beyond the plain dictionary gloss of the word. A passage that only
restates the gloss in longer words is not worth showing.

Be strict about invention and lenient about style. Report the exact phrase you
believe is unsupported, quoted from the passage."""

JUDGE_USER = """EVIDENCE THE PASSAGE WAS WRITTEN FROM:
{bundle}

PASSAGE UNDER AUDIT:
{passage}

Return JSON only:
{{
  "grounded": true | false,
  "unsupported_claims": ["exact quoted phrase", ...],
  "worth_showing": true | false,
  "why": "one sentence"
}}"""


def ask(model, system, user, timeout=300):
    body = json.dumps({
        "model": model, "stream": False, "format": "json", "think": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(HOST + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer " + KEY} if KEY else {})})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    raw = (d.get('message') or {}).get('content') or ''
    try:
        o = json.loads(raw)
    except json.JSONDecodeError:
        i, j = raw.find('{'), raw.rfind('}')
        o = json.loads(raw[i:j + 1]) if i >= 0 else {}
    return o, round(time.time() - t, 1), (d.get('prompt_eval_count') or 0) + (d.get('eval_count') or 0)


def plant(kind, passage):
    """Return (mutated_passage, note) or None when this passage can't carry the fault."""
    if kind == 'clean':
        return passage, ''
    if kind == 'cognate':
        m = re.search(r'\b(Hebrew|Aramaic|Akkadian|Ugaritic|Syriac|Sabaic)\b', passage)
        if not m:
            return None
        return (passage[:m.start()] + 'Phoenician' + passage[m.end():],
                'language swapped to one with no row for this root')
    if kind == 'verse':
        m = re.search(r'\((\d{1,3}):(\d{1,3})\)', passage)
        if not m:
            return None
        return passage[:m.start()] + '(49:13)' + passage[m.end():], 'verse swapped to 49:13'
    if kind == 'invent':
        return (passage.rstrip() + ' The Arabs also used it of a blacksmith quenching '
                'a blade in snow-water before dawn.', 'invented concrete detail appended')
    if kind == 'bland':
        return ('This root carries the general notion of the meaning given in the '
                'translation, and the Qur\'an uses it in that ordinary sense throughout.',
                'replaced with a gloss restatement')
    return None


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else 'kimi-k3'
    n_each = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    c = S.connect()
    rows = c.execute(
        "SELECT root_buckwalter bw, sense_key, passage FROM root_core_meanings "
        "WHERE COALESCE(passage,'')!='' AND COALESCE(gates_json,'[]')='[]' "
        "ORDER BY root_buckwalter LIMIT 200").fetchall()
    cases = []
    for kind in ('clean', 'cognate', 'verse', 'invent', 'bland'):
        made = 0
        for r in rows:
            if made >= n_each:
                break
            p = plant(kind, r['passage'])
            if not p:
                continue
            cases.append((kind, r['bw'], r['sense_key'], p[0], p[1]))
            made += 1
    tp = fp = fn = tn = 0
    toks = 0
    print("model: %s   (%d cases)" % (model, len(cases)))
    for kind, bw, sk, passage, note in cases:
        bundle = B.build(bw, lemma_group=sk.split('+') if sk else None)['text']
        try:
            o, secs, t = ask(model, JUDGE_SYSTEM,
                             JUDGE_USER.format(bundle=bundle, passage=passage))
        except Exception as e:
            print("  %-8s %-6s ERROR %s" % (kind, bw, str(e)[:60]))
            continue
        toks += t
        flagged = not o.get('grounded', True) or (kind == 'bland' and not o.get('worth_showing', True))
        should = kind != 'clean'
        if should and flagged: tp += 1
        elif should and not flagged: fn += 1
        elif not should and flagged: fp += 1
        else: tn += 1
        mark = 'OK ' if flagged == should else '** MISS **'
        print("  %-8s %-6s flagged=%-5s %s  %s" % (kind, bw, flagged, mark,
              (o.get('unsupported_claims') or [''])[0][:58]))
    print("\n  caught %d/%d planted faults | false alarms on clean: %d/%d | %d tokens"
          % (tp, tp + fn, fp, fp + tn, toks))
    print("  VERDICT: %s" % ("USABLE" if tp >= 0.8 * (tp + fn) and fp == 0 else "NOT SAFE — do not run at scale"))


if __name__ == '__main__':
    main()
