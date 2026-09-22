#!/usr/bin/env python3
"""Run the root core-meaning generator over a list of roots via Ollama Cloud.

Pacing and quota handling follow the pattern already proven in
_exeg_review_ollama.py: never more than WORKERS requests in flight (the owner's
standing cap is 2), a small delay between launches, and a quota exhaustion that
REQUEUES the root rather than burning it -- an allowance that runs out must cost
us nothing but time.
"""
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _root_core_bundle as B          # noqa: E402
import _root_core_prompt as P          # noqa: E402

HOST = os.environ.get('OLLAMA_HOST', 'https://ollama.com')
KEY = os.environ.get('OLLAMA_API_KEY', '')
# PACING. The owner's cap is 2 in flight, but the binding constraint turned out
# to be Ollama's ROLLING 5-HOUR SESSION window, not the weekly budget (weekly sat
# at 18.6% when the session limit tripped). Two workers at 0.6s burned a session
# allowance in minutes. Default to ONE worker with a real gap between calls, so
# a long run spreads across the window instead of spiking and stalling.
WORKERS = int(os.environ.get('ROOT_CORE_WORKERS', '1'))
PACE = float(os.environ.get('ROOT_CORE_PACE', '5'))
TIMEOUT = 300
# Append-as-you-go log so a killed or quota-stalled run keeps what it finished.
JSONL = os.environ.get('ROOT_CORE_JSONL', '')
ASK_OVERRIDE = int(os.environ.get('ROOT_CORE_ASK', '0'))


class QuotaExhausted(Exception):
    """Subscription allowance spent -- wait, do not burn the root."""


def call(model, system, user):
    body = json.dumps({
        # think=False is the single biggest lever on this run. kimi-k3 otherwise
        # emits ~6,000 tokens of reasoning to produce a ~100-token passage, and
        # since the binding limit is a token allowance, that reasoning WAS the
        # schedule: 7.7 of the first 10.7 hours were spent asleep on quota.
        # Disabling it cuts output ~97% and the call from 72s to 3.5s.
        "model": model, "stream": False, "format": "json", "think": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(HOST + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer " + KEY} if KEY else {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        txt = e.read()[:300].decode('utf8', 'replace')
        if e.code in (429, 402) or 'limit' in txt.lower() or 'quota' in txt.lower():
            raise QuotaExhausted(txt)
        raise RuntimeError("HTTP %s %s" % (e.code, txt))
    raw = (d.get('message') or {}).get('content') or ''
    try:
        return json.loads(raw), raw, d
    except json.JSONDecodeError:
        i, j = raw.find('{'), raw.rfind('}')
        if i >= 0 and j > i:
            return json.loads(raw[i:j + 1]), raw, d
        raise RuntimeError("model did not return JSON: %r" % raw[:200])


def run(roots, model):
    q = queue.Queue()
    for r in roots:
        q.put(r)
    out, lock = {}, threading.Lock()

    def worker():
        backoff = 300
        while True:
            try:
                bw = q.get_nowait()
            except queue.Empty:
                return
            try:
                key = bw
                grp = None
                if '|' in bw:
                    bw, _, lems = bw.partition('|')
                    grp = lems.split('+')
                b = B.build(bw, lemma_group=grp)
                system, user = P.build(b['text'])
                # A unit that already failed the length gate is re-asked for
                # something shorter. Retrying at the same temperature and the
                # same asked-for length mostly reproduces the same overrun.
                if ASK_OVERRIDE and ASK_OVERRIDE != P.ASK_CHARS:
                    system = system.replace('At most %d characters' % P.ASK_CHARS,
                                            'At most %d characters' % ASK_OVERRIDE)
                    user = user.replace('<=%d chars' % P.ASK_CHARS, '<=%d chars' % ASK_OVERRIDE)
                    user = user.replace('at most %d characters' % P.ASK_CHARS,
                                        'at most %d characters' % ASK_OVERRIDE)
                t0 = time.time()
                obj, raw, meta = call(model, system, user)
                rec = {"ok": True, "key": key, "root_bw": bw, "lemma_group": grp,
                       "root_ar": b['root_ar'],
                       "has_maqayis": b['has_maqayis'], "bundle_chars": len(b['text']),
                       "secs": round(time.time() - t0, 1), "eval_tokens": meta.get('eval_count'),
                       "prompt_tokens": meta.get('prompt_eval_count'), **obj}
                with lock:
                    out[key] = rec
                    if JSONL:
                        with open(JSONL, 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except QuotaExhausted as e:
                q.put(bw)                      # requeue -- the root is not burned
                with lock:
                    # stderr, NOT stdout: stdout carries the JSON result and a
                    # progress line printed into it corrupts the whole file.
                    print("[quota] exhausted, sleeping %ds: %s" % (backoff, str(e)[:90]),
                          file=sys.stderr, flush=True)
                time.sleep(backoff)
                backoff = min(backoff * 2, 1800)
            except Exception as e:
                with lock:
                    out[key if 'key' in dir() else bw] = {"ok": False, "error": str(e)[:300]}
            finally:
                q.task_done()
            time.sleep(PACE)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    return out


if __name__ == '__main__':
    model = os.environ.get('MODEL', 'kimi-k3')
    roots = sys.argv[1:] or ['*hb']
    res = run(roots, model)
    print(json.dumps({"model": model, "prompt_version": P.PROMPT_VERSION, "results": res},
                     ensure_ascii=False, indent=1))
