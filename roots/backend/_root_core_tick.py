#!/usr/bin/env python3
"""One paced tick of the root core-meaning loop.

Mirrors the shape already proven in this repo: print ONE json line with what
was applied and what is left, so a /loop or a detached process can drive it
without holding state.

  python3 _root_core_tick.py --apply data/_root_core.jsonl   # store results
  python3 _root_core_tick.py --next 20                       # next work units
  python3 _root_core_tick.py --report

Every row lands review_status='pending', hidden=1. Nothing reaches a reader
until a human approves it.
"""
import argparse
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _root_core_schema as S      # noqa: E402
import _root_core_gates as G       # noqa: E402
import _root_core_prompt as P      # noqa: E402

MIN_LEN = 80


def apply_file(c, path):
    applied = skipped = rejected = 0
    if not os.path.exists(path):
        return {"applied": 0, "skipped": 0, "rejected": 0, "note": "no file"}
    for line in open(path, encoding='utf-8'):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get('ok'):
            continue
        bw = r.get('root_bw')
        key = '+'.join(r.get('lemma_group') or [])
        # The Arabic in this database is NOT NFC-normalised, but any string that
        # reaches here through a shell argument or a hand-typed literal usually
        # IS. The two compare unequal while looking identical, so the row stores
        # fine and then silently never joins to the lemma map. Resolve the key
        # back to the worklist's own bytes whenever it matches under NFC.
        if key:
            want = unicodedata.normalize('NFC', key)
            for row in c.execute("SELECT sense_key FROM root_core_worklist WHERE root_buckwalter=?", (bw,)):
                if unicodedata.normalize('NFC', row['sense_key']) == want:
                    key = row['sense_key']
                    break
        passage = (r.get('passage') or '').strip()
        verdict = r.get('verdict') or 'ok'
        if verdict != 'no_insight' and len(passage) < MIN_LEN:
            rejected += 1
            continue
        flags = G.check({**r, 'root_bw': bw}, c)
        hard = [f for f in flags if f[1] == 'hard']
        cur = c.execute(
            "INSERT OR REPLACE INTO root_core_meanings "
            "(root_buckwalter, sense_key, lemmas_json, passage, physical_origin, "
            " stations_json, verses_json, confidence, verdict, model_used, "
            " prompt_version, gates_json, review_status, hidden, edited_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'pending',1,datetime('now'))",
            (bw, key, json.dumps(r.get('lemma_group') or [], ensure_ascii=False),
             passage, r.get('physical_origin'),
             json.dumps(r.get('stations_used') or [], ensure_ascii=False),
             json.dumps(r.get('verses_relied_on') or [], ensure_ascii=False),
             r.get('confidence'), verdict, r.get('model') or 'kimi-k3',
             P.PROMPT_VERSION,
             json.dumps([{"gate": f[0], "severity": f[1], "msg": f[2]} for f in flags],
                        ensure_ascii=False)))
        applied += cur.rowcount
        # A unit with a HARD gate failure stays on the worklist: it must be
        # regenerated, not quietly shipped with a known defect.
        c.execute("UPDATE root_core_worklist SET status=?, attempts=attempts+1, "
                  "last_error=?, at=datetime('now') WHERE root_buckwalter=? AND sense_key=?",
                  ('todo' if hard else 'done',
                   '; '.join('%s:%s' % (f[0], f[2][:60]) for f in hard) or None, bw, key))
        if hard:
            skipped += 1
    c.commit()
    return {"applied": applied, "held_for_hard_gate": skipped, "rejected": rejected}


def next_units(c, n, retries=False):
    """Units to work next. retries=True returns only ones that have failed
    before, so the caller can ask them for a shorter passage."""
    op = '>=' if retries else '='
    rows = c.execute(
        "SELECT root_buckwalter bw, sense_key FROM root_core_worklist "
        "WHERE status='todo' AND attempts < 3 AND attempts %s ? "
        "ORDER BY n_verses DESC LIMIT ?" % op, (1 if retries else 0, n)).fetchall()
    return [r['bw'] + ('|' + r['sense_key'] if r['sense_key'] else '') for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply')
    ap.add_argument('--next', type=int, default=0)
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--retries', action='store_true')
    a = ap.parse_args()
    c = S.connect()
    out = {}
    if a.apply:
        out['applied'] = apply_file(c, a.apply)
    if a.report or not (a.apply or a.next):
        out['stored'] = c.execute("SELECT COUNT(*) FROM root_core_meanings").fetchone()[0]
        out['approved'] = c.execute("SELECT COUNT(*) FROM root_core_meanings "
                                    "WHERE review_status='approved'").fetchone()[0]
        for r in c.execute("SELECT status, COUNT(*) n FROM root_core_worklist GROUP BY 1"):
            out['worklist_' + r['status']] = r['n']
    if a.next:
        out['chunk'] = next_units(c, a.next, retries=a.retries)
        out['remaining'] = c.execute("SELECT COUNT(*) FROM root_core_worklist "
                                     "WHERE status='todo' AND attempts < 3").fetchone()[0]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
