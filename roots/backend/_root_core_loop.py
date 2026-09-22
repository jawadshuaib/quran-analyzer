#!/usr/bin/env python3
"""Drive the root core-meaning generation to completion, unattended.

  nohup python3 _root_core_loop.py > data/_root_core_loop.log 2>&1 &
  touch data/_root_core.stop      # ask it to finish the current chunk and exit

Runs until the worklist is empty. Each cycle: take a chunk of work units from
the worklist (canonical sense keys, read from the DB -- never constructed), hand
them to the generator, then apply the results through the tick, which gates
every passage and stores it as pending.

PACING is the whole problem. Ollama's binding limit is a rolling 5-hour SESSION
window, not the weekly budget -- the weekly sat at 18.6% when the session
allowance tripped. So: one request in flight, a real gap between them, and on a
429 the generator requeues the unit and sleeps with a doubling backoff rather
than burning it. A stall costs time, never work.

SAFE TO KILL at any moment: results append to a JSONL as they land, the tick is
idempotent, and units whose passage fails a hard gate stay on the worklist to be
tried again (up to 3 attempts) instead of shipping with a known defect.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = int(os.environ.get('ROOT_CORE_CHUNK', '12'))
# ONE FILE PER CYCLE, not one growing file. A single appended JSONL is
# re-applied in full every cycle, so the work grows with the run: by the end
# each cycle re-gates ~1,900 stored rows. Worse than the wasted time, it
# re-judges settled rows against whatever the gates say NOW, so tightening a
# gate mid-run could flip an already-accepted unit back onto the worklist and
# send it round again. Each cycle writes and applies only its own results; the
# files stay on disk as the archive of what the model actually returned.
JSONL_DIR = os.path.join(HERE, 'data', 'root_core_batches')
STOP = os.path.join(HERE, 'data', '_root_core.stop')


def tick(*args):
    out = subprocess.run([sys.executable, '_root_core_tick.py', *args], cwd=HERE,
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception:
        print("tick failed: %s %s" % (out.stdout[-300:], out.stderr[-300:]), flush=True)
        return {}


def main():
    cycle = 0
    t0 = time.time()
    while True:
        if os.path.exists(STOP):
            print("[loop] stop file present — exiting", flush=True)
            break
        state = tick('--next', str(CHUNK))
        chunk, remaining = state.get('chunk') or [], state.get('remaining', 0)
        if not chunk:
            print("[loop] worklist empty — done", flush=True)
            break
        cycle += 1
        print("[loop] cycle %d: %d units, %d remaining (%.1f h elapsed)"
              % (cycle, len(chunk), remaining, (time.time() - t0) / 3600), flush=True)
        os.makedirs(JSONL_DIR, exist_ok=True)
        batch = os.path.join(JSONL_DIR, 'cycle-%05d.jsonl' % cycle)
        env = dict(os.environ, SHOW_EXISTING='0', MODEL=os.environ.get('MODEL', 'kimi-k3'),
                   ROOT_CORE_JSONL=batch)
        subprocess.run([sys.executable, '_root_core_run.py', *chunk], cwd=HERE, env=env,
                       stdout=subprocess.DEVNULL, stderr=sys.stderr)
        applied = tick('--apply', batch)
        rep = tick('--report')
        print("[loop]   applied=%s stored=%s worklist_todo=%s"
              % (applied.get('applied'), rep.get('stored'), rep.get('worklist_todo')), flush=True)
    print("[loop] final: %s" % json.dumps(tick('--report')), flush=True)


if __name__ == '__main__':
    main()
