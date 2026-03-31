#!/bin/sh
set -e

# Always deploy the latest database from the image
echo "Deploying latest database..."
cp /app/seed-quran.db /app/data/quran.db

# Deploy mnemonic images to the data volume
mkdir -p /app/data/mnemonic_images
if [ -d /app/seed-mnemonic-images ] && [ "$(ls -A /app/seed-mnemonic-images 2>/dev/null)" ]; then
  echo "Deploying mnemonic images..."
  cp /app/seed-mnemonic-images/* /app/data/mnemonic_images/
fi

exec "$@"
