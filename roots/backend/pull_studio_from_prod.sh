#!/bin/bash
# Pull OPERATOR-OWNED Studio state from prod into the local DB. The loop
# runs this at the START of every tick so it never reasons from stale
# verdicts or stale doctrine.
#
# Prod is truth for:
#   - qa_videos: status, review outcome, and the operator-edited script
#     of any non-gate_passed row (approved/rejected/uploaded)
#   - studio_lessons: text + status of every existing lesson_key
# Local remains truth for rows prod doesn't have (new drafts push via
# sync_studio_to_prod.sh, which is insert-only the other way).
set -euo pipefail
cd "$(dirname "$0")"

HOST=root@al-nuqta.com
CONTAINER=quran-root-analyzer

cat > /tmp/studio_pull_dump.py <<'PYEOF'
import json, sqlite3
conn = sqlite3.connect('/app/data/quran.db'); conn.row_factory = sqlite3.Row
def rows(sql):
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []
out = {
    "qa_videos": rows(
        "SELECT source_key, status, title, script_json, error_message "
        "FROM qa_videos WHERE source_key IS NOT NULL"),
    "studio_lessons": rows(
        "SELECT lesson_key, lesson, status, evidence FROM studio_lessons"),
    "video_candidates": rows(
        "SELECT source_key, status, rationale FROM video_candidates "
        "WHERE status IN ('starred','rejected_score')"),
}
print(json.dumps(out, ensure_ascii=False))
PYEOF
scp -o BatchMode=yes /tmp/studio_pull_dump.py $HOST:/tmp/studio_pull_dump.py >/dev/null
ssh -o BatchMode=yes $HOST \
  "docker cp /tmp/studio_pull_dump.py $CONTAINER:/tmp/studio_pull_dump.py && \
   docker exec $CONTAINER python3 /tmp/studio_pull_dump.py" > /tmp/studio_pull.json

python3 - <<'PYEOF'
import json, sqlite3
data = json.load(open('/tmp/studio_pull.json'))
conn = sqlite3.connect('data/quran.db')
applied = {"verdicts": 0, "lessons": 0, "candidates": 0}

for row in data["qa_videos"]:
    cur = conn.execute(
        "SELECT status FROM qa_videos WHERE source_key=?",
        (row["source_key"],)).fetchone()
    if not cur:
        continue
    if row["status"] != "gate_passed":
        # Operator decided (or the scheduler uploaded): mirror status AND
        # the operator-edited script.
        conn.execute(
            "UPDATE qa_videos SET status=?, title=?, script_json=?, "
            "error_message=? WHERE source_key=?",
            (row["status"], row["title"], row["script_json"],
             row["error_message"], row["source_key"]))
        if (cur[0] or "") != row["status"]:
            applied["verdicts"] += 1

for row in data["studio_lessons"]:
    cur = conn.execute(
        "SELECT lesson, status FROM studio_lessons WHERE lesson_key=?",
        (row["lesson_key"],)).fetchone()
    if cur and (cur[0] != row["lesson"] or cur[1] != row["status"]):
        conn.execute(
            "UPDATE studio_lessons SET lesson=?, status=?, evidence=?, "
            "updated_at=datetime('now') WHERE lesson_key=?",
            (row["lesson"], row["status"], row["evidence"], row["lesson_key"]))
        applied["lessons"] += 1

for row in data["video_candidates"]:
    cur = conn.execute(
        "SELECT status FROM video_candidates WHERE source_key=?",
        (row["source_key"],)).fetchone()
    if cur and cur[0] not in ("drafted", "rejected_gate", "rejected_quality") \
            and cur[0] != row["status"]:
        conn.execute(
            "UPDATE video_candidates SET status=?, rationale=?, "
            "updated_at=datetime('now') WHERE source_key=?",
            (row["status"], row["rationale"], row["source_key"]))
        applied["candidates"] += 1

conn.commit()
print(json.dumps(applied))
PYEOF
