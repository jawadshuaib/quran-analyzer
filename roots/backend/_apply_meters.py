#!/usr/bin/env python3
"""Apply the generate-meters workflow output via `meter-add`, SERIALLY per metre.
Usage: python3 _apply_meters.py <workflow_output.json>"""
import json, subprocess, sys, tempfile, os

raw = json.load(open(sys.argv[1]))
rows = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(rows, str):
    rows = json.loads(rows)

n = 0
for r in rows or []:
    if not r:
        continue
    key = r.get("key")
    if not key or not (r.get("article_markdown") or "").strip():
        print(f"  skip {key!r}: no article"); continue
    payload = {
        "meter_ar": r.get("meter_ar"),
        "name_en": r.get("name_en"),
        "name_meaning": r.get("name_meaning"),
        "tafil_ar": r.get("tafil_ar"),
        "tafil_latin": r.get("tafil_latin"),
        "syllable_pattern": r.get("syllable_pattern"),
        "mnemonic_en": r.get("mnemonic_en"),
        "article_markdown": r.get("article_markdown"),
        "showcase": r.get("showcase") or [],
        "confidence": r.get("confidence"),
        "qa_status": r.get("qa_status"),
        "qa_notes": r.get("qa_notes"),
        "raw_response": json.dumps(r, ensure_ascii=False),
    }
    fd, path = tempfile.mkstemp(suffix=f"_{key}.json", prefix="meter_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    out = subprocess.run(["python3", "poetry_corpus.py", "meter-add", key, "--file", path],
                         capture_output=True, text=True)
    os.unlink(path)
    tail = (out.stdout.strip().splitlines() or [out.stderr.strip()[:120]])[-1]
    print(f"  {key}: {tail}")
    n += 1
print(f"APPLIED {n} metre page(s)")
