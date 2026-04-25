# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY roots/frontend/package.json roots/frontend/package-lock.json* ./
RUN npm ci
COPY roots/frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.12-slim
WORKDIR /app

# Install system deps: curl, ffmpeg (video generation), fonts (text overlays)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg fonts-liberation fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps (CPU-only torch to keep image small)
COPY roots/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# Pre-download sentence-transformer model so first search is fast
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code — all backend Python modules.
# app.py is the entry point; the rest are CLI scripts and helpers that
# various API endpoints lazy-import (vocab studio, bias pipeline, etc.).
# Bringing them all in keeps the Dockerfile from drifting whenever a new
# lazy import is added; the source files are kilobytes each so image
# size impact is negligible.
COPY roots/backend/*.py ./

# Copy bundled fonts for video text overlays
COPY roots/backend/data/fonts ./data/fonts

# Copy database as seed (entrypoint copies to volume on first run)
COPY assets/quran.db ./seed-quran.db

# Copy mnemonic images as seed (entrypoint deploys to data volume)
COPY assets/mnemonic_images ./seed-mnemonic-images

# Copy built frontend into static/
COPY --from=frontend-build /build/dist ./static

# Copy entrypoint
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Create data directory for volume mount
RUN mkdir -p /app/data

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "300"]
