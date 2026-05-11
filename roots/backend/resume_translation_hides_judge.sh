#!/usr/bin/env bash
# Resumable wrapper for translation_hides_ai.py.
#
# Why this exists: the underlying judge script is fully idempotent
# (already-judged verses are skipped on each run via a DB check), so
# the simplest way to handle Ollama cloud session expiry / quota
# exhaustion / transient network failure is to loop the python script
# itself, sleeping between attempts.
#
# Behaviour:
#   - Launches the python script.
#   - Exit code 0 → all done, break out of the loop.
#   - Exit code 2 → consecutive-error bail (the script itself decided
#     to stop because the cloud endpoint appears persistently dead).
#     Wait the long-delay, then retry.
#   - Any other non-zero → unexpected crash, wait the short-delay,
#     then retry (and let the operator inspect the log if it persists).
#
# Usage:
#   ./resume_translation_hides_judge.sh                    # run/resume full pool
#   ./resume_translation_hides_judge.sh --limit 1000       # cap to top-1000
#   ./resume_translation_hides_judge.sh --model qwen3:14b  # local override
#
# Logs land in logs/th_judge_<UTC-timestamp>.log. Each loop iteration
# appends to the same log file so a tail -f works across restarts.
#
# Ctrl+C: SIGINT is forwarded to the python child; it exits cleanly,
# the wrapper sees the exit and breaks the loop.

set -u
cd "$(dirname "$0")"

MAX_RETRIES="${MAX_RETRIES:-100}"   # outer-loop iteration cap
LONG_DELAY_S="${LONG_DELAY_S:-1800}"  # 30 min — for consecutive-error bail
SHORT_DELAY_S="${SHORT_DELAY_S:-60}"  # 1 min — for unexpected crashes
LOG_DIR="${LOG_DIR:-logs}"

mkdir -p "$LOG_DIR"
TS="$(date -u +%Y%m%d_%H%M%S)"
LOG="${LOG_DIR}/th_judge_${TS}.log"

# Track Ctrl+C so we stop the loop cleanly when the user interrupts.
INTERRUPTED=0
trap 'INTERRUPTED=1; echo ""; echo "[wrapper] SIGINT received; will exit after the current iteration."; ' INT

echo "[wrapper] Logging to $LOG" | tee -a "$LOG"
echo "[wrapper] Started at $(date)" | tee -a "$LOG"

# Quick progress query: how many rows already exist in the judge table?
preflight() {
  python3 - <<'PYEOF' 2>/dev/null
import sqlite3
try:
    conn = sqlite3.connect("data/quran.db")
    n = conn.execute("SELECT COUNT(*) FROM translation_hides_signals").fetchone()[0]
    print(f"existing rows: {n}")
except sqlite3.OperationalError as e:
    print(f"table missing (will be created on first run): {e}")
PYEOF
}
echo "[wrapper] $(preflight)" | tee -a "$LOG"

ATTEMPT=0
while [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; do
  ATTEMPT=$((ATTEMPT + 1))
  if [ "$INTERRUPTED" -eq 1 ]; then break; fi

  {
    echo ""
    echo "[wrapper] === Attempt $ATTEMPT/$MAX_RETRIES at $(date) ==="
  } | tee -a "$LOG"

  # Run the python script with whatever extra args the operator passed
  # in. `unbuffer` would give nicer line buffering but isn't installed
  # everywhere; `python3 -u` does the trick on stdout/stderr.
  python3 -u translation_hides_ai.py "$@" 2>&1 | tee -a "$LOG"
  rc=${PIPESTATUS[0]}

  case "$rc" in
    0)
      echo "[wrapper] Judge exited 0 (complete). Stopping." | tee -a "$LOG"
      break
      ;;
    2)
      echo "[wrapper] Judge exited 2 (consecutive-error bail)." | tee -a "$LOG"
      if [ "$INTERRUPTED" -eq 1 ]; then break; fi
      echo "[wrapper] Sleeping ${LONG_DELAY_S}s before retry to let the cloud session recover..." | tee -a "$LOG"
      sleep "$LONG_DELAY_S"
      ;;
    130)
      # SIGINT from python — operator hit Ctrl+C inside the script.
      echo "[wrapper] Judge exited 130 (interrupted). Stopping." | tee -a "$LOG"
      break
      ;;
    *)
      echo "[wrapper] Judge exited $rc (unexpected). Retrying after ${SHORT_DELAY_S}s." | tee -a "$LOG"
      if [ "$INTERRUPTED" -eq 1 ]; then break; fi
      sleep "$SHORT_DELAY_S"
      ;;
  esac
done

echo "[wrapper] Finished at $(date)" | tee -a "$LOG"
echo "[wrapper] $(preflight)" | tee -a "$LOG"
