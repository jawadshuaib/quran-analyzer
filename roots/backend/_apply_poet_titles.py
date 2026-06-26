#!/usr/bin/env python3
"""Apply the poet-titles workflow output via poets-add + titles-add.
Usage: python3 _apply_poet_titles.py <workflow_output.json>"""
import json, subprocess, sys, tempfile, os

raw = json.load(open(sys.argv[1]))
data = raw.get("result") if isinstance(raw, dict) and "result" in raw else raw
if isinstance(data, str):
    data = json.loads(data)

poets = data.get("poets") or []
titles = data.get("titles") or []


def run(cmd_args, payload):
    fd, path = tempfile.mkstemp(suffix=".json", prefix="pt_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    out = subprocess.run(["python3", "poetry_corpus.py", *cmd_args, "--file", path],
                         capture_output=True, text=True)
    os.unlink(path)
    print("  " + (out.stdout.strip().splitlines() or [out.stderr.strip()[:120]])[-1])


if poets:
    run(["poets-add"], {"poets": poets})
if titles:
    run(["titles-add"], {"titles": titles})
print(f"APPLIED {len(poets)} poet romanisation group(s), {len(titles)} title(s)")
