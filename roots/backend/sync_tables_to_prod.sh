#!/usr/bin/env bash
# Push specific TABLES from local quran.db up to prod — safely.
#
# Why this exists: the earlier full-DB rsync mode wiped prod-only
# state (pipeline #2, scheduled runs, YouTube playlists, rendered
# videos), because prod has rows that don't exist locally. A full
# DB replacement clobbers those. This script instead syncs *only*
# the tables you name, using INSERT OR REPLACE, so prod-only data
# in OTHER tables is untouched.
#
# Usage:
#   ./sync_tables_to_prod.sh translation_hides_signals translation_hides_configs
#   ./sync_tables_to_prod.sh ai_word_meanings
#
# Each table name MUST exist locally. The script:
#   1. Dumps each named table from local data/quran.db into a
#      single INSERT-OR-REPLACE SQL file under /tmp.
#   2. Takes a timestamped backup of the prod DB before touching it
#      (so if the operator ever needs to undo, the backup is right
#      there alongside the live file).
#   3. SCPs the SQL file to prod and applies it via python3 inside
#      the running container (sqlite3 binary is not in the image,
#      so we go through python).
#   4. Prints a row-count diff (BEFORE / AFTER) for each table so
#      the operator can sanity-check the result.
#
# Knobs:
#   PROD_HOST           ssh target (default: root@al-nuqta.com)
#   PROD_CONTAINER      docker container name (default: quran-root-analyzer)
#   PROD_DB_PATH        DB path inside the container (default: /app/data/quran.db)
#   LOCAL_DB_PATH       local DB path (default: data/quran.db)
#   DRY_RUN=1           build the SQL but don't push it
#
# Safety:
#   - Refuses to run if you pass zero table names (would be a no-op).
#   - Refuses if any named table is missing locally.
#   - Uses INSERT OR REPLACE, so prod-only rows in the SAME table
#     that don't exist locally are PRESERVED (sync is one-way:
#     local → prod, but it's additive, not destructive). Rows that
#     exist in both will be replaced by the local copy.

set -euo pipefail
cd "$(dirname "$0")"

PROD_HOST="${PROD_HOST:-root@al-nuqta.com}"
PROD_CONTAINER="${PROD_CONTAINER:-quran-root-analyzer}"
PROD_DB_PATH="${PROD_DB_PATH:-/app/data/quran.db}"
LOCAL_DB_PATH="${LOCAL_DB_PATH:-data/quran.db}"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <table1> [<table2> ...]" >&2
  echo "       Pass at least one table name. See top of script for examples." >&2
  exit 2
fi

if [ ! -f "$LOCAL_DB_PATH" ]; then
  echo "[sync] Local DB not found at $LOCAL_DB_PATH" >&2
  exit 1
fi

TABLES=("$@")
TS="$(date -u +%Y%m%d_%H%M%S)"
LOCAL_SQL="/tmp/db_sync_${TS}.sql"

echo "[sync] === Building $LOCAL_SQL from local DB for tables: ${TABLES[*]} ==="

python3 - "$LOCAL_DB_PATH" "$LOCAL_SQL" "${TABLES[@]}" <<'PYEOF'
import sqlite3, sys

db_path = sys.argv[1]
out_path = sys.argv[2]
tables = sys.argv[3:]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Validate every named table exists, fail loudly if any doesn't —
# we'd rather refuse than silently skip and leave the operator
# wondering why prod didn't get an update.
for t in tables:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,)
    ).fetchone()
    if row is None:
        print(f"[sync] Table {t!r} does not exist locally — aborting.", file=sys.stderr)
        sys.exit(1)

def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, bytes):
        return "X'" + v.hex() + "'"
    s = str(v).replace("'", "''")
    return f"'{s}'"

with open(out_path, "w") as f:
    f.write("-- Table-only sync produced by sync_tables_to_prod.sh\n")
    f.write(f"-- Tables: {', '.join(tables)}\n")
    f.write("BEGIN TRANSACTION;\n")
    total = 0
    for t in tables:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
        col_str = ",".join(cols)
        f.write(f"\n-- Table: {t}\n")
        rows = conn.execute(f"SELECT * FROM {t}").fetchall()
        for r in rows:
            vals = [r[c] for c in cols]
            val_str = ",".join(lit(v) for v in vals)
            f.write(f"INSERT OR REPLACE INTO {t} ({col_str}) VALUES ({val_str});\n")
        f.write(f"-- {t}: {len(rows)} rows\n")
        total += len(rows)
    f.write("\nCOMMIT;\n")

print(f"[sync] wrote {out_path} — {total} rows across {len(tables)} table(s)")
PYEOF

ls -lh "$LOCAL_SQL"
echo

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[sync] DRY_RUN=1 set — stopping before pushing to prod."
  echo "[sync] SQL file is at $LOCAL_SQL; inspect it and rerun without DRY_RUN to apply."
  exit 0
fi

echo "[sync] === Copying $LOCAL_SQL to $PROD_HOST:/tmp/ ==="
scp "$LOCAL_SQL" "$PROD_HOST:$LOCAL_SQL"
echo

echo "[sync] === Taking safety backup of prod DB ==="
# Use a per-run timestamped name so successive syncs don't overwrite
# each other's backups (cheap insurance: the operator can always
# `docker cp ... .` if they need to roll back).
ssh -o ConnectTimeout=10 "$PROD_HOST" "
  set -e
  docker exec $PROD_CONTAINER cp $PROD_DB_PATH ${PROD_DB_PATH}.before-tablesync-$TS
  docker exec $PROD_CONTAINER ls -lh $PROD_DB_PATH ${PROD_DB_PATH}.before-tablesync-$TS
"
echo

echo "[sync] === Reading prod BEFORE counts ==="
ssh -o ConnectTimeout=10 "$PROD_HOST" "docker exec $PROD_CONTAINER python3 -c \"
import sqlite3
conn = sqlite3.connect('$PROD_DB_PATH')
for t in $(printf '%s\n' "${TABLES[@]}" | python3 -c 'import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))'):
    try:
        n = conn.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]
        print('  ' + t + ': ' + str(n) + ' rows BEFORE')
    except Exception as e:
        print('  ' + t + ': table missing (' + str(e) + ')')
\""
echo

echo "[sync] === Copying SQL file into the container & applying ==="
ssh -o ConnectTimeout=10 "$PROD_HOST" "
  set -e
  docker cp $LOCAL_SQL $PROD_CONTAINER:$LOCAL_SQL
  docker exec $PROD_CONTAINER python3 -c \"
import sqlite3
conn = sqlite3.connect('$PROD_DB_PATH')
with open('$LOCAL_SQL') as f:
    conn.executescript(f.read())
conn.commit()
print('[sync] script applied OK')
\"
"
echo

echo "[sync] === Reading prod AFTER counts ==="
ssh -o ConnectTimeout=10 "$PROD_HOST" "docker exec $PROD_CONTAINER python3 -c \"
import sqlite3
conn = sqlite3.connect('$PROD_DB_PATH')
for t in $(printf '%s\n' "${TABLES[@]}" | python3 -c 'import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))'):
    try:
        n = conn.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]
        print('  ' + t + ': ' + str(n) + ' rows AFTER')
    except Exception as e:
        print('  ' + t + ': error (' + str(e) + ')')
\""

echo
echo "[sync] DONE. Backup on prod at ${PROD_DB_PATH}.before-tablesync-$TS"
echo "[sync] If something looks wrong, restore with:"
echo "       ssh $PROD_HOST 'docker exec $PROD_CONTAINER cp ${PROD_DB_PATH}.before-tablesync-$TS $PROD_DB_PATH'"
