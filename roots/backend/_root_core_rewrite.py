#!/usr/bin/env python3
"""Pass 2 — rewrite the passages that need it, keeping what is already right.

TWO KINDS OF TARGET, and they need different instructions:

  ungrounded   the audit quoted a claim the evidence does not support. The fix
               is surgical: drop or correct that claim, leave everything else.
  formulaic    the passage is fine but wears a frame the corpus wears 300 times
               over. The owner's objection was exactly this ("sounds AI
               generated"). The fix is a new opening, same substance.

THE BANNED FRAMES ARE MEASURED, NOT GUESSED. A hand-written list only catches
the formulas I happen to notice; counting them across the corpus catches the
one the model actually settled into. At the time of writing:
    "... is where these letters begin/start"   308 passages (16%)
    "Arabs used these letters ..."             180 (9%)
    "The letters name/carry ..."                85 (4.5%)
A rewrite is told the current top frames and forbidden to use any of them, so
the ban list tightens itself each time this runs.

  python3 _root_core_rewrite.py --plan     # what would be rewritten, and why
  python3 _root_core_rewrite.py --limit 50
"""
import argparse
import collections
import json
import os
import queue
import re
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SHOW_EXISTING', '0')
import _root_core_bundle as B          # noqa: E402
import _root_core_prompt as P          # noqa: E402
import _root_core_gates as G           # noqa: E402
import _root_core_schema as S          # noqa: E402
import _root_core_calibrate as C       # noqa: E402  (shares the ask() client)

MODEL = os.environ.get('REWRITE_MODEL', 'kimi-k3')
WORKERS = int(os.environ.get('REWRITE_WORKERS', '2'))
PACE = float(os.environ.get('REWRITE_PACE', '2'))
TOP_FRAMES = 8


def measure_frames(c, top=TOP_FRAMES):
    """The opening frames the corpus over-uses, counted from the corpus."""
    pats = collections.Counter()
    for (p,) in c.execute("SELECT passage FROM root_core_meanings WHERE COALESCE(passage,'')!=''"):
        first = re.split(r'(?<=[.;:])\s', p.strip())[0]
        # normalise a frame to its shape: first four words, and the stock tail
        words = re.findall(r"[A-Za-z']+", first)[:4]
        if words:
            pats[' '.join(w.lower() for w in words)] += 1
        m = re.search(r'is where these letters (?:begin|start)', p, re.I)
        if m:
            pats['is where these letters begin'] += 1
    return [f for f, n in pats.most_common(top * 3) if n >= 15][:top]


def targets(c):
    """(root, sense_key, reason, detail) for everything worth rewriting."""
    out = []
    seen = set()
    for r in c.execute(
            "SELECT v.root_buckwalter bw, v.sense_key sk, v.unsupported_json u, v.why w, "
            "       v.grounded g, v.worth_showing ws "
            "FROM root_core_review v JOIN root_core_meanings m "
            "  ON m.root_buckwalter=v.root_buckwalter AND m.sense_key=v.sense_key "
            "     AND m.passage=v.judged_passage "
            "WHERE v.grounded=0 OR v.worth_showing=0"):
        why = []
        if not r['g']:
            claims = json.loads(r['u'] or '[]')
            why.append("The evidence does not support: %s" % '; '.join('"%s"' % x for x in claims[:3]))
        if not r['ws']:
            why.append("It says no more than the plain dictionary gloss already tells the reader.")
        out.append((r['bw'], r['sk'], 'audit', ' '.join(why) + ' ' + (r['w'] or '')))
        seen.add((r['bw'], r['sk']))
    frames = measure_frames(c)
    if frames:
        like = " OR ".join(["LOWER(passage) LIKE ?"] * len(frames))
        rows = c.execute(
            "SELECT root_buckwalter bw, sense_key sk FROM root_core_meanings "
            "WHERE COALESCE(passage,'')!='' AND (%s)" % like,
            ['%' + f + '%' for f in frames]).fetchall()
        for r in rows:
            if (r['bw'], r['sk']) not in seen:
                out.append((r['bw'], r['sk'], 'formulaic',
                            'It opens with a frame the corpus already uses many times over.'))
    return out, frames


REWRITE_USER = """{bundle}

=========================================================================
A passage explaining this root already exists. Rewrite it.

CURRENT PASSAGE:
{passage}

WHAT IS WRONG WITH IT:
{problem}

RULES FOR THE REWRITE:
 - Keep everything that is right. This is a repair, not a fresh start: the
   images, the evidence and the Qur'anic landing should survive unless they
   are the problem.
 - Fix ONLY what is named above, and change the opening sentence.
 - Do NOT begin with any of these frames, which the corpus already overuses:
{frames}
   The ban covers REWORDINGS of the same shape, not just these exact words:
   "is where this root lives", "is what these letters picture", "the letters
   begin in" and anything else that announces the letters before showing the
   thing. If your new opening still says something about "these letters" or
   "this root" as its subject, you have not changed the frame.

 - KEEP THE CONCRETE IMAGE. This is the trap. The frame usually wraps the best
   part of the passage, and deleting the wrapper together with the image makes
   the passage WORSE, not better. Recast the sentence so the image leads:
       BAD  (image deleted)  "A man who no longer fears for his life is where
                              these letters begin: amn is safety."
                          -> "Amn is safety, the heart gone still."
       GOOD (image kept)    "A mark cut into a thing so it can be told apart is
                              where these letters begin, and knowing is what
                              such marks leave in the mind."
                          -> "Knowing begins as a mark cut into a thing so it
                              can be told apart, and such marks are what
                              knowledge leaves in the mind."
   If the rewritten opening has no picture in it, you have gone backwards.

 - Do not let the passage grow. It must still fit the limit below; if the new
   opening is longer, tighten elsewhere.

 - Every claim must trace to the evidence above. If a claim cannot be
   supported, cut it rather than soften it.

Return JSON only:
{{
  "verdict": "ok" | "no_insight",
  "physical_origin": "the concrete thing the letters start from, <=70 chars",
  "passage": "the rewritten passage, <={max_chars} chars",
  "verses_relied_on": ["2:153"],
  "changed": "one line on what you changed and why",
  "confidence": "high" | "medium" | "low"
}}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    c = S.connect()
    tg, frames = targets(c)
    if a.plan:
        by = collections.Counter(t[2] for t in tg)
        print(json.dumps({"targets": len(tg), "by_reason": dict(by),
                          "measured_frames": frames}, ensure_ascii=False, indent=1))
        return
    if a.limit:
        tg = tg[:a.limit]
    frame_block = "\n".join("     - %s..." % f for f in frames)
    print("[rewrite] %d passages with %s" % (len(tg), MODEL), flush=True)
    q = queue.Queue()
    for t in tg:
        q.put(t)
    lock = threading.Lock()
    done = {"n": 0, "kept": 0, "toks": 0}

    def worker():
        conn = S.connect()
        backoff = 300
        while True:
            try:
                bw, sk, reason, problem = q.get_nowait()
            except queue.Empty:
                return
            try:
                row = conn.execute("SELECT passage FROM root_core_meanings WHERE "
                                   "root_buckwalter=? AND sense_key=?", (bw, sk)).fetchone()
                grp = sk.split('+') if sk else None
                bundle = B.build(bw, lemma_group=grp)['text']
                o, secs, toks = C.ask(MODEL, P.SYSTEM, REWRITE_USER.format(
                    bundle=bundle, passage=row['passage'], problem=problem,
                    frames=frame_block, max_chars=P.ASK_CHARS))
                new = (o.get('passage') or '').strip()
                # Only accept a rewrite that is at least as clean as what it replaces.
                old_flags = G.check({'root_bw': bw, 'verdict': 'ok', 'passage': row['passage'],
                                     'verses_relied_on': []}, conn)
                new_flags = G.check({'root_bw': bw, 'verdict': o.get('verdict', 'ok'),
                                     'passage': new,
                                     'verses_relied_on': o.get('verses_relied_on') or []}, conn)
                old_hard = sum(1 for f in old_flags if f[1] == 'hard')
                new_hard = sum(1 for f in new_flags if f[1] == 'hard')
                accept = new and new_hard <= old_hard
                with lock:
                    done['n'] += 1
                    done['toks'] += toks
                if accept:
                    conn.execute(
                        "UPDATE root_core_meanings SET passage=?, gates_json=?, "
                        "prompt_version=?, edited_at=NULL WHERE root_buckwalter=? AND sense_key=?",
                        (new, json.dumps([{"gate": f[0], "severity": f[1], "msg": f[2]}
                                          for f in new_flags], ensure_ascii=False),
                         P.PROMPT_VERSION + '+rw', bw, sk))
                    conn.commit()
                else:
                    with lock:
                        done['kept'] += 1
                if done['n'] % 50 == 0:
                    print("[rewrite] %d/%d (kept original %d) %.1fM tokens"
                          % (done['n'], len(tg), done['kept'], done['toks'] / 1e6), flush=True)
            except Exception as e:
                msg = str(e)
                if '429' in msg or 'limit' in msg.lower():
                    q.put((bw, sk, reason, problem))
                    print("[rewrite] quota — sleeping %ds" % backoff, file=sys.stderr, flush=True)
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 1800)
                else:
                    print("[rewrite] %s error: %s" % (bw, msg[:90]), file=sys.stderr, flush=True)
            finally:
                q.task_done()
            time.sleep(PACE)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    print("[rewrite] done: %d rewritten, %d kept original, %.1fM tokens"
          % (done['n'] - done['kept'], done['kept'], done['toks'] / 1e6), flush=True)


if __name__ == '__main__':
    main()
