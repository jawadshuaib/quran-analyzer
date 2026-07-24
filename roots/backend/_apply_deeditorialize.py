#!/usr/bin/env python3
"""Apply de-editorialized lexicon entries with a marker-parity guard.

Reads the workflow output, and for each cleaned entry validates that the
[[q:ID|...]] markers in the new lexicon_markdown match the existing
quoted_lines line_root_id set EXACTLY before updating. Mismatches are skipped
(original kept) and reported.
"""
import json, re, sqlite3, datetime, sys

OUT = "/private/tmp/claude-501/-Users-jawadshuaib-Desktop-projects-quran-related/e303eb4a-2940-4e0a-9cd2-26418759b8cf/tasks/we2om94gx.output"
DB = "data/quran.db"
MARKER = re.compile(r"\[\[q:(\d+)\|")

raw = json.load(open(OUT))
# output may be {summary, result, ...} or a bare list
entries = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(entries, str):
    entries = json.loads(entries)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
now = datetime.datetime.now().isoformat(timespec="seconds")

applied, skipped = [], []
for e in entries:
    bw = e["root_buckwalter"]
    row = conn.execute(
        "SELECT quoted_lines_json FROM root_poetic_lexicon WHERE root_buckwalter=?", (bw,)
    ).fetchone()
    if row is None:
        skipped.append((bw, "no existing row")); continue
    existing_ids = set()
    if row["quoted_lines_json"]:
        try:
            existing_ids = {int(q["line_root_id"]) for q in json.loads(row["quoted_lines_json"])}
        except Exception as ex:
            skipped.append((bw, f"bad quoted_lines_json: {ex}")); continue
    new_ids = {int(m) for m in MARKER.findall(e["lexicon_markdown"])}
    if new_ids != existing_ids:
        skipped.append((bw, f"PARITY BREAK new={sorted(new_ids)} existing={sorted(existing_ids)}")); continue
    conn.execute(
        "UPDATE root_poetic_lexicon SET quran_internal_summary=?, lexicon_markdown=?, "
        "relation_to_quran=?, updated_at=? WHERE root_buckwalter=?",
        (e["quran_internal_summary"], e["lexicon_markdown"], e["relation_to_quran"], now, bw),
    )
    applied.append((bw, len(new_ids)))

conn.commit()
print(f"APPLIED {len(applied)}/{len(entries)}:")
for bw, n in applied:
    print(f"  {bw:5} ({n} markers)")
if skipped:
    print(f"SKIPPED {len(skipped)}:")
    for bw, why in skipped:
        print(f"  {bw:5} {why}")
conn.close()
