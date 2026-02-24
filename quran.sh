#!/bin/bash

PROJECT_DIR="$HOME/Desktop/projects/quran-related/roots"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "Done."
  exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
cd "$PROJECT_DIR/backend"
python app.py &
BACKEND_PID=$!

# Start frontend
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait a moment then open browser
sleep 3
open "http://localhost:4000"

echo "Backend PID: $BACKEND_PID (port 5000)"
echo "Frontend PID: $FRONTEND_PID (port 4000)"
echo "Press Ctrl+C to stop both servers."

wait
