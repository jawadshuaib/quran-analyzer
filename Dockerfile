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

# Install system deps:
#   - curl, ffmpeg, fonts-liberation, fonts-dejavu-core: existing
#     ASS-overlay video generation (translation_hides + grammar_insights)
#   - fonts-amiri: Arabic font for the Remotion renderer's RTL slides;
#     headless Chromium can't render Quranic text without it
#   - Chromium runtime libs: libnss3 / libnspr4 / libgbm1 / etc. — headless
#     Chromium fails-to-launch without them. List sourced from the
#     puppeteer/playwright Debian recipes; covers the common dynamic
#     dependencies of chrome-headless-shell that Remotion bundles.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg \
    fonts-liberation fonts-dejavu-core fonts-amiri \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libxss1 libpangocairo-1.0-0 \
    ca-certificates gnupg && \
    # libasound was renamed to libasound2t64 in some Debian 12 update
    # tracks (time64 transition). Try the new name first, fall back
    # to the old; one of them will be present whichever bookworm
    # snapshot we're built against. Without `|| true` the apt-get
    # rolls back the whole transaction on a missing package.
    (apt-get install -y --no-install-recommends libasound2t64 || \
     apt-get install -y --no-install-recommends libasound2) && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS via NodeSource. Required by the Remotion
# video renderer (roots/video-renderer/) which is invoked as a
# subprocess from the Python backend for word_origins educational
# videos. Frontend stage uses Node too but lives in its own builder
# image; the runtime image needs Node baked in for live render calls.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
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

# ---------------------------------------------------------------------------
# Remotion video renderer — used by the word_origins educational pipeline.
#
# Layout: copied into /app/video-renderer/ (parallel to the Python code at
# /app/). The Python module educational_render_remotion.py reads the
# REMOTION_RENDERER_DIR env var to find this dir; we set it just below.
#
# We install npm deps + the headless-Chromium binary INSIDE the image so a
# fresh container can render immediately on first request. Both add ~400
# MB total — non-trivial but acceptable for the feature value (the renderer
# produces the karaoke-captioned word-detail videos the educational
# pipeline ships to YouTube Shorts).
# ---------------------------------------------------------------------------
COPY roots/video-renderer/ ./video-renderer/
WORKDIR /app/video-renderer
RUN npm ci --omit=dev && npx remotion browser ensure
WORKDIR /app

ENV REMOTION_RENDERER_DIR=/app/video-renderer

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
