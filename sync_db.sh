#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ -z "$MODE" ]]; then
  echo "Usage: $0 <full|judge-only> --server user@host [options]"
  exit 1
fi
shift || true

SERVER=""
CONTAINER="quran-root-analyzer"
LOCAL_DB="roots/backend/data/quran.db"
SEED_DB="assets/quran.db"
HEALTH_URL="http://127.0.0.1:8070/api/surahs"
HEALTH_TIMEOUT_SEC=120
HEALTH_POLL_SEC=3
PERSIST_SEED=0
COMMIT_PUSH=0
COMMIT_MESSAGE="Update quran.db from local generation"
RESTART_AFTER_APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server)
      SERVER="${2:-}"
      shift 2
      ;;
    --container)
      CONTAINER="${2:-}"
      shift 2
      ;;
    --local-db)
      LOCAL_DB="${2:-}"
      shift 2
      ;;
    --seed-db)
      SEED_DB="${2:-}"
      shift 2
      ;;
    --persist-seed)
      PERSIST_SEED=1
      shift
      ;;
    --commit-push)
      COMMIT_PUSH=1
      shift
      ;;
    --commit-message)
      COMMIT_MESSAGE="${2:-}"
      shift 2
      ;;
    --restart)
      RESTART_AFTER_APPLY=1
      shift
      ;;
    --health-url)
      HEALTH_URL="${2:-}"
      shift 2
      ;;
    --health-timeout)
      HEALTH_TIMEOUT_SEC="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$SERVER" ]]; then
  echo "Error: --server user@host is required."
  exit 1
fi

if [[ ! -f "$LOCAL_DB" ]]; then
  echo "Error: local DB not found at '$LOCAL_DB'"
  exit 1
fi

TS="$(date +%Y%m%d-%H%M%S)"
REMOTE_BACKUP="/tmp/quran-backup-${TS}.db"
REMOTE_NEW_DB="/tmp/quran-sync-${TS}.db"
REMOTE_JSON="/tmp/judge-updates-${TS}.json"
CONTAINER_TEMP_DB="/tmp/quran-sync.db"

wait_for_healthy_container() {
  local waited=0
  echo "Waiting for container health (timeout: ${HEALTH_TIMEOUT_SEC}s) ..."
  while (( waited < HEALTH_TIMEOUT_SEC )); do
    local state health
    state="$(ssh "$SERVER" "docker inspect ${CONTAINER} --format '{{.State.Status}}' 2>/dev/null || true")"
    health="$(ssh "$SERVER" "docker inspect ${CONTAINER} --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || true")"

    if [[ "$state" == "running" ]] && [[ "$health" == "healthy" || "$health" == "none" ]]; then
      echo "Container state is healthy enough: state=${state}, health=${health}"
      return 0
    fi

    sleep "$HEALTH_POLL_SEC"
    waited=$((waited + HEALTH_POLL_SEC))
  done

  echo "Timed out waiting for healthy container."
  return 1
}

verify_endpoint() {
  echo "Verifying endpoint: ${HEALTH_URL}"
  ssh "$SERVER" "curl -fsS --max-time 10 '${HEALTH_URL}' >/dev/null"
}

rollback_remote_db() {
  echo "Rolling back remote DB from backup ${REMOTE_BACKUP} ..."
  ssh "$SERVER" "docker cp ${REMOTE_BACKUP} ${CONTAINER}:/app/data/quran.db"
  ssh "$SERVER" "docker cp ${REMOTE_BACKUP} ${CONTAINER}:/app/seed-quran.db"
  ssh "$SERVER" "docker restart ${CONTAINER} >/dev/null"
  wait_for_healthy_container
  verify_endpoint
  echo "Rollback completed and endpoint is healthy."
}

backup_remote_db() {
  echo "Backing up remote DB to ${REMOTE_BACKUP} ..."
  ssh "$SERVER" "docker cp ${CONTAINER}:/app/data/quran.db ${REMOTE_BACKUP}"
  echo "Remote backup created at ${SERVER}:${REMOTE_BACKUP}"
}

persist_seed_and_maybe_push() {
  if [[ "$PERSIST_SEED" -ne 1 ]]; then
    return 0
  fi
  echo "Copying local DB to seed DB: ${SEED_DB}"
  cp "$LOCAL_DB" "$SEED_DB"

  if [[ "$COMMIT_PUSH" -eq 1 ]]; then
    echo "Committing and pushing seed DB update ..."
    git add "$SEED_DB"
    if git diff --cached --quiet; then
      echo "No changes in ${SEED_DB}; skipping commit/push."
    else
      git commit -m "$COMMIT_MESSAGE"
      git push origin main
    fi
  fi
}

replace_remote_db_full() {
  echo "Uploading local DB to ${SERVER}:${REMOTE_NEW_DB} ..."
  scp "$LOCAL_DB" "${SERVER}:${REMOTE_NEW_DB}"

  echo "Copying uploaded DB into container temp path ..."
  ssh "$SERVER" "docker cp ${REMOTE_NEW_DB} ${CONTAINER}:${CONTAINER_TEMP_DB} && rm -f ${REMOTE_NEW_DB}"

  echo "Validating temp DB integrity and required tables ..."
  ssh "$SERVER" "docker exec ${CONTAINER} python - <<'PY'
import sqlite3
import sys

db_path = '/tmp/quran-sync.db'
conn = sqlite3.connect(db_path)

integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
if integrity != 'ok':
    print(f'integrity_check failed: {integrity}')
    sys.exit(1)

required = ['verses', 'morphology', 'translations', 'ai_word_meanings']
for name in required:
    row = conn.execute(
        \"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?\",
        (name,),
    ).fetchone()
    if not row:
        print(f'missing required table: {name}')
        sys.exit(1)

print('Temp DB validation passed.')
PY"

  backup_remote_db

  echo "Replacing live DB and seed DB with validated temp DB ..."
  ssh "$SERVER" "docker exec ${CONTAINER} sh -lc 'cp ${CONTAINER_TEMP_DB} /app/data/quran.db && cp ${CONTAINER_TEMP_DB} /app/seed-quran.db && rm -f ${CONTAINER_TEMP_DB}'"

  if [[ "$RESTART_AFTER_APPLY" -eq 1 ]]; then
    echo "Restarting container ${CONTAINER} ..."
    ssh "$SERVER" "docker restart ${CONTAINER} >/dev/null"
  fi

  echo "Running health verification ..."
  if ! wait_for_healthy_container || ! verify_endpoint; then
    echo "Health verification failed after full DB sync."
    rollback_remote_db
  fi

  echo "Full DB sync completed."
  persist_seed_and_maybe_push
}

apply_judge_only_updates() {
  local tmp_json
  tmp_json="$(mktemp /tmp/judge-updates-XXXXXX.json)"

  echo "Exporting judged rows from local DB ..."
  python3 - <<'PY' "$LOCAL_DB" "$tmp_json"
import json
import sqlite3
import sys

db_path = sys.argv[1]
out_path = sys.argv[2]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    """
    SELECT chapter, verse, word_pos, preferred_translation, preferred_source, judge_reasoning
    FROM ai_word_meanings
    WHERE preferred_translation IS NOT NULL
    """
).fetchall()
with open(out_path, "w", encoding="utf-8") as f:
    json.dump([dict(r) for r in rows], f, ensure_ascii=False)
print(len(rows))
PY

  backup_remote_db

  echo "Uploading judge updates JSON to ${SERVER}:${REMOTE_JSON} ..."
  scp "$tmp_json" "${SERVER}:${REMOTE_JSON}"
  rm -f "$tmp_json"

  echo "Applying judge-only updates on remote DB ..."
  ssh "$SERVER" "docker cp ${REMOTE_JSON} ${CONTAINER}:/tmp/judge-updates.json && rm -f ${REMOTE_JSON}"
  ssh "$SERVER" "docker exec ${CONTAINER} python - <<'PY'
import json
import sqlite3

with open('/tmp/judge-updates.json', 'r', encoding='utf-8') as f:
    rows = json.load(f)

conn = sqlite3.connect('/app/data/quran.db')
cur = conn.cursor()
updated = 0
for r in rows:
    cur.execute(
        '''
        UPDATE ai_word_meanings
        SET preferred_translation = ?, preferred_source = ?, judge_reasoning = ?
        WHERE id = (
            SELECT id
            FROM ai_word_meanings
            WHERE chapter = ? AND verse = ? AND word_pos = ?
            ORDER BY created_at DESC
            LIMIT 1
        )
        ''',
        (
            r.get('preferred_translation'),
            r.get('preferred_source'),
            r.get('judge_reasoning'),
            r.get('chapter'),
            r.get('verse'),
            r.get('word_pos'),
        ),
    )
    updated += cur.rowcount
conn.commit()
print(f'Updated rows: {updated}')
PY"
  ssh "$SERVER" "docker exec ${CONTAINER} rm -f /tmp/judge-updates.json"

  if [[ "$RESTART_AFTER_APPLY" -eq 1 ]]; then
    echo "Restarting container ${CONTAINER} ..."
    ssh "$SERVER" "docker restart ${CONTAINER} >/dev/null"
  fi

  echo "Running health verification ..."
  if ! wait_for_healthy_container || ! verify_endpoint; then
    echo "Health verification failed after judge-only sync."
    rollback_remote_db
  fi

  echo "Judge-only sync completed."
  persist_seed_and_maybe_push
}

case "$MODE" in
  full)
    replace_remote_db_full
    ;;
  judge-only)
    apply_judge_only_updates
    ;;
  *)
    echo "Unknown mode '$MODE'. Use: full | judge-only"
    exit 1
    ;;
esac
