#!/usr/bin/env python3
"""Apply translate-poems workflow output via `trans-add`, SERIALLY per poem.
Usage: python3 _apply_translations.py <workflow_output.json>"""
import json, subprocess, sys, tempfile, os

raw = json.load(open(sys.argv[1]))
rows = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(rows, str):
    rows = json.loads(rows)

poems = lines = 0
for r in rows or []:
    if not r:
        continue
    pid = r.get("poem_id")
    trans = [t for t in (r.get("translations") or []) if t.get("line_id") and (t.get("english") or "").strip()]
    if not pid or not trans:
        continue
    fd, path = tempfile.mkstemp(suffix=f"_p{pid}.json", prefix="trans_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"translations": trans}, f, ensure_ascii=False)
    out = subprocess.run(["python3", "poetry_corpus.py", "trans-add", "--file", path, str(pid)],
                         capture_output=True, text=True)
    os.unlink(path)
    tail = (out.stdout.strip().splitlines() or [out.stderr.strip()[:80]])[-1]
    print(f"  poem {pid}: {tail}")
    poems += 1
    lines += len(trans)
print(f"APPLIED {poems} poems, {lines} line translations")
