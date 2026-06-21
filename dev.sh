#!/usr/bin/env bash
#
# Dev runner — start the Flask backend (port 5000) and the Vite frontend
# (port 4000) together, and shut BOTH down cleanly on Ctrl+C.
#
#   ./dev.sh             start both and open the browser
#   ./dev.sh --no-open   start both without opening the browser
#
# Paths are resolved relative to this script, so it works no matter where
# the repo lives or which directory you run it from.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/roots/backend"
FRONTEND="$ROOT/roots/frontend"

OPEN_BROWSER=1
[ "${1:-}" = "--no-open" ] && OPEN_BROWSER=0

# --- pick a Python interpreter (prefer a project venv if one exists) -------
if   [ -x "$ROOT/.venv/bin/python" ];     then PY="$ROOT/.venv/bin/python"
elif [ -x "$BACKEND/.venv/bin/python" ];  then PY="$BACKEND/.venv/bin/python"
elif [ -x "$BACKEND/venv/bin/python" ];   then PY="$BACKEND/venv/bin/python"
elif command -v python3 >/dev/null 2>&1;  then PY="python3"
else                                            PY="python"; fi

# --- sanity checks ---------------------------------------------------------
[ -d "$BACKEND" ]  || { echo "✗ backend dir not found: $BACKEND";  exit 1; }
[ -d "$FRONTEND" ] || { echo "✗ frontend dir not found: $FRONTEND"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "✗ npm not found on PATH"; exit 1; }

# --- install frontend deps on first run ------------------------------------
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "[setup] frontend dependencies missing — running npm install…"
  ( cd "$FRONTEND" && npm install ) || { echo "✗ npm install failed"; exit 1; }
fi

# --- clean shutdown --------------------------------------------------------
# `kill 0` signals the whole process group, so it also reaps Flask's
# debug-reloader child and Vite's esbuild child — which a named-PID kill
# would leave orphaned holding ports 5000/4000.
cleanup() {
  echo
  echo "Shutting down backend + frontend…"
  trap - INT TERM EXIT
  kill 0 2>/dev/null
}
trap cleanup INT TERM EXIT

echo "▶ backend   → http://localhost:5000   ($PY app.py)"
( cd "$BACKEND"  && exec "$PY" app.py ) &

echo "▶ frontend  → http://localhost:4000   (npm run dev)"
( cd "$FRONTEND" && exec npm run dev ) &

if [ "$OPEN_BROWSER" = "1" ]; then
  ( sleep 4
    if   command -v open >/dev/null 2>&1;     then open "http://localhost:4000"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:4000"
    fi ) >/dev/null 2>&1 &
fi

echo
echo "Both running. Open http://localhost:4000 — press Ctrl+C to stop both."
wait
