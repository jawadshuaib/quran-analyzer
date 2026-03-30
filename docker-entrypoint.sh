#!/bin/sh
set -e

# Always deploy the latest database from the image
echo "Deploying latest database..."
cp /app/seed-quran.db /app/data/quran.db

# Ensure mnemonic images directory exists on the data volume
mkdir -p /app/data/mnemonic_images

exec "$@"
