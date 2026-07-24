#!/usr/bin/env python3
"""Read index-judge workflow output and run `index-add` SERIALLY per root
(serial to avoid SQLite lock contention). Usage: _apply_index_verdicts.py <out.json>"""
import json, subprocess, sys, tempfile, os

raw = json.load(open(sys.argv[1]))
rows = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(rows, str):
    rows = json.loads(rows)

print(f"{'root':6} {'scanned':>8} {'matches':>8}   index-add result")
for r in rows:
    root = r["root"]
    payload = {"scanned": r.get("scanned", []), "matches": r.get("matches", [])}
    fd, path = tempfile.mkstemp(suffix=f"_{root}.json", prefix="idxv_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    out = subprocess.run(
        ["python3", "poetry_corpus.py", "index-add", "--file", path, root],
        capture_output=True, text=True)
    tail = (out.stdout.strip().splitlines() or ["(no output)"])[-1]
    if out.returncode != 0:
        tail = "ERR: " + (out.stderr.strip().splitlines() or [""])[-1]
    print(f"{root:6} {len(payload['scanned']):>8} {len(payload['matches']):>8}   {tail}")
    os.unlink(path)
