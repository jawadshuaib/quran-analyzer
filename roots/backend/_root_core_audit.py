#!/usr/bin/env python3
"""Pass 1 — audit every passage against the evidence it was written from.

The one defect no deterministic gate can catch is a claim the bundle does not
support: an invented cognate gloss, a verse the root never occurs in, a
concrete detail from the model's own memory. I found one by hand (an invented
"Hebrew zakar" for dh-k-r, in a passage whose bundle contained no cognate data
at all). Reading 1,911 passages against 1,911 bundles is exactly the work a
model can do and a regex cannot.

THE JUDGE IS kimi-k3, and that is a measured choice, not a default. Calibrated
on planted faults (a swapped cognate language, a swapped verse, an invented
detail, a bland gloss-restatement) against five clean controls:

    kimi-k3               19/20 caught, 0/5 false alarms   <- chosen
    deepseek-v4-pro:0813  19/20 caught, 1/5 false alarms
    mistral-large-3:675b  19/20 caught, 1/5 false alarms
    glm-5.3                8/8  caught, 1/2 false alarms
    qwen3.5:397b          19/20 caught, 4/5 false alarms

Every larger model over-flags. On 1,911 rows a 1-in-5 false-alarm rate is ~380
spurious reviews, and qwen3.5 would have flagged most of the corpus. Re-run
_root_core_calibrate.py before ever swapping the judge.

  python3 _root_core_audit.py            # audit everything not yet audited
  python3 _root_core_audit.py --report
"""
import argparse
import json
import os
import queue
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SHOW_EXISTING', '0')
import _root_core_bundle as B          # noqa: E402
import _root_core_schema as S          # noqa: E402
import _root_core_calibrate as C       # noqa: E402  (judge prompt + ask live there)

MODEL = os.environ.get('AUDIT_MODEL', 'kimi-k3')
WORKERS = int(os.environ.get('AUDIT_WORKERS', '2'))
PACE = float(os.environ.get('AUDIT_PACE', '2'))

SCHEMA = """
CREATE TABLE IF NOT EXISTS root_core_review (
    root_buckwalter TEXT NOT NULL,
    sense_key TEXT NOT NULL DEFAULT '',
    grounded INTEGER,                  -- 0 = a claim the bundle does not support
    unsupported_json TEXT,             -- the exact phrases the judge quoted
    worth_showing INTEGER,             -- 0 = says no more than the plain gloss
    why TEXT,
    judged_passage TEXT,               -- WHICH text was judged: a later rewrite
                                       -- invalidates the verdict, so store it
    model TEXT,
    at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (root_buckwalter, sense_key)
);
"""


class Quota(Exception):
    pass


def audit_one(c, row):
    grp = row['sense_key'].split('+') if row['sense_key'] else None
    bundle = B.build(row['root_buckwalter'], lemma_group=grp)['text']
    o, secs, toks = C.ask(MODEL, C.JUDGE_SYSTEM,
                          C.JUDGE_USER.format(bundle=bundle, passage=row['passage']))
    return {
        "grounded": 0 if o.get('grounded') is False else 1,
        "unsupported": o.get('unsupported_claims') or [],
        "worth": 0 if o.get('worth_showing') is False else 1,
        "why": (o.get('why') or '')[:500],
        "toks": toks,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    c = S.connect()
    c.executescript(SCHEMA)
    c.commit()

    if a.report:
        n = c.execute("SELECT COUNT(*) FROM root_core_review").fetchone()[0]
        ug = c.execute("SELECT COUNT(*) FROM root_core_review WHERE grounded=0").fetchone()[0]
        nw = c.execute("SELECT COUNT(*) FROM root_core_review WHERE worth_showing=0").fetchone()[0]
        tot = c.execute("SELECT COUNT(*) FROM root_core_meanings WHERE COALESCE(passage,'')!=''").fetchone()[0]
        print(json.dumps({"audited": n, "of": tot, "ungrounded": ug, "not_worth_showing": nw}))
        return

    # Only rows whose CURRENT text has not been judged: a rewrite must be re-audited.
    rows = c.execute(
        "SELECT m.root_buckwalter, m.sense_key, m.passage FROM root_core_meanings m "
        "LEFT JOIN root_core_review r ON r.root_buckwalter=m.root_buckwalter "
        "  AND r.sense_key=m.sense_key AND r.judged_passage=m.passage "
        "WHERE COALESCE(m.passage,'')!='' AND r.root_buckwalter IS NULL "
        "ORDER BY (SELECT COUNT(*) FROM morphology WHERE root_buckwalter=m.root_buckwalter) DESC"
    ).fetchall()
    if a.limit:
        rows = rows[:a.limit]
    print("[audit] %d passages to judge with %s" % (len(rows), MODEL), flush=True)
    q = queue.Queue()
    for r in rows:
        q.put(dict(r))
    lock = threading.Lock()
    done = {"n": 0, "ug": 0, "nw": 0, "toks": 0}

    def worker():
        conn = S.connect()
        backoff = 300
        while True:
            try:
                row = q.get_nowait()
            except queue.Empty:
                return
            try:
                res = audit_one(conn, row)
                conn.execute(
                    "INSERT OR REPLACE INTO root_core_review (root_buckwalter, sense_key, "
                    "grounded, unsupported_json, worth_showing, why, judged_passage, model, at) "
                    "VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
                    (row['root_buckwalter'], row['sense_key'], res['grounded'],
                     json.dumps(res['unsupported'], ensure_ascii=False), res['worth'],
                     res['why'], row['passage'], MODEL))
                conn.commit()
                with lock:
                    done['n'] += 1
                    done['ug'] += (res['grounded'] == 0)
                    done['nw'] += (res['worth'] == 0)
                    done['toks'] += res['toks']
                    if done['n'] % 50 == 0:
                        print("[audit] %d/%d  ungrounded=%d not-worth=%d  %.1fM tokens"
                              % (done['n'], len(rows), done['ug'], done['nw'],
                                 done['toks'] / 1e6), flush=True)
            except Exception as e:
                msg = str(e)
                if '429' in msg or 'limit' in msg.lower():
                    q.put(row)
                    print("[audit] quota — sleeping %ds" % backoff, file=sys.stderr, flush=True)
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 1800)
                else:
                    print("[audit] %s error: %s" % (row['root_buckwalter'], msg[:90]),
                          file=sys.stderr, flush=True)
            finally:
                q.task_done()
            time.sleep(PACE)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    print("[audit] done: %d judged, %d ungrounded, %d not worth showing, %.1fM tokens"
          % (done['n'], done['ug'], done['nw'], done['toks'] / 1e6), flush=True)


if __name__ == '__main__':
    main()
