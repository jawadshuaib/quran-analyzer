#!/bin/sh
set -e

# Copy seed database to the volume only on first run
if [ ! -f /app/data/quran.db ]; then
    echo "First run: seeding database into volume..."
    cp /app/seed-quran.db /app/data/quran.db
fi

exec "$@"
