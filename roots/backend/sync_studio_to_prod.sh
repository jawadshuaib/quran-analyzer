#!/bin/bash
# Studio-safe sync: push NEW bank rows + candidates to prod, INSERT-ONLY.
#
# Unlike sync_tables_to_prod.sh (INSERT OR REPLACE by id), this script
# NEVER touches a row that already exists on prod — because prod carries
# operator state (approved/rejected, edited scripts) that a stale local
# copy must never clobber. Lesson learned 2026-07-09: a full REPLACE sync
# overwrote an operator-edited script and un-rejected a rejected one
# (recovered from the pre-sync backup).
#
# Rows are matched by source_key (globally unique). Prod ids may differ
# from local ids — the id column is EXCLUDED and prod assigns its own.
set -euo pipefail
cd "$(dirname "$0")"

HOST=root@al-nuqta.com
CONTAINER=quran-root-analyzer

python3 - <<'PYEOF' > /tmp/studio_sync_payload.json
import json, sqlite3
conn = sqlite3.connect('data/quran.db'); conn.row_factory = sqlite3.Row
def dump(table, key):
    rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
    for r in rows:
        r.pop('id', None)                 # prod assigns its own ids
        r.pop('edit_token_hash', None)    # tokens are per-environment
        r.pop('edit_token_expires', None)
    return rows
print(json.dumps({
    "qa_videos": dump("qa_videos", "source_key"),
    "video_candidates": dump("video_candidates", "source_key"),
}, ensure_ascii=False))
PYEOF

scp -o BatchMode=yes /tmp/studio_sync_payload.json $HOST:/tmp/studio_sync_payload.json >/dev/null

cat > /tmp/studio_sync_apply.py <<'PYEOF'
import json, sqlite3
data = json.load(open('/tmp/studio_sync_payload.json'))
conn = sqlite3.connect('/app/data/quran.db')
inserted = {"qa_videos": 0, "video_candidates": 0}
for table in ("qa_videos", "video_candidates"):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    existing = {r[0] for r in conn.execute(
        f"SELECT source_key FROM {table} WHERE source_key IS NOT NULL").fetchall()}
    for row in data[table]:
        key = row.get("source_key")
        if not key or key in existing:
            continue                      # INSERT-ONLY: never touch prod rows
        common = [c for c in row if c in cols]
        conn.execute(
            f"INSERT INTO {table} ({', '.join(common)}) "
            f"VALUES ({', '.join('?' * len(common))})",
            [row[c] for c in common])
        inserted[table] += 1
conn.commit()
print(json.dumps(inserted))
PYEOF
scp -o BatchMode=yes /tmp/studio_sync_apply.py $HOST:/tmp/studio_sync_apply.py >/dev/null

ssh -o BatchMode=yes $HOST \
  "docker cp /tmp/studio_sync_payload.json $CONTAINER:/tmp/studio_sync_payload.json && \
   docker cp /tmp/studio_sync_apply.py $CONTAINER:/tmp/studio_sync_apply.py && \
   docker exec $CONTAINER python3 /tmp/studio_sync_apply.py"
