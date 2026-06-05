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
    fonts-liberation fonts-dejavu-core \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libxss1 libpangocairo-1.0-0 \
    ca-certificates gnupg && \
    # libasound was renamed to libasound2t64 in the Debian time64
    # transition (bookworm-updates → trixie). Try the new name
    # first, fall back to the old. One will be present in whatever
    # snapshot we're building against.
    (apt-get install -y --no-install-recommends libasound2t64 || \
     apt-get install -y --no-install-recommends libasound2) && \
    # fonts-amiri was renamed to fonts-hosny-amiri in trixie (Debian
    # 13). Same try-fallback. The Remotion renderer ALSO loads Amiri
    # via @remotion/google-fonts at bundle time so the system font
    # is mostly belt-and-braces — if neither apt name resolves
    # (some future trixie update), don't fail the build; emit a
    # warning so it shows up in CI logs and we can revisit.
    (apt-get install -y --no-install-recommends fonts-hosny-amiri || \
     apt-get install -y --no-install-recommends fonts-amiri || \
     echo "WARNING: no system Amiri font installed; Remotion's @remotion/google-fonts is the only source") && \
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

# Pre-download sentence-transformer model so first search is fast. HuggingFace
# is intermittently unreachable mid-build (this exact step has failed a deploy
# with a transient "couldn't connect to huggingface.co"), so retry with backoff
# instead of letting one network blip kill the whole build.
RUN for i in 1 2 3 4 5; do \
        python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && exit 0; \
        echo "[build] HF model download attempt $i failed; retrying in $((i*15))s"; \
        sleep $((i*15)); \
    done; \
    echo "[build] sentence-transformer model download failed after 5 attempts" >&2; exit 1

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

# ---------------------------------------------------------------------------
# Defense-in-depth: fail the build if app.py can't import.
#
# Why this exists: a forward-reference bug (e.g. @admin_required used on a
# route defined ABOVE the decorator's own definition) doesn't manifest
# until gunicorn's worker tries to load app.py at runtime. Without this
# step, GitHub Actions happily builds + pushes a broken image to GHCR, the
# server pulls it, the worker fails to boot, the container restart-loops,
# and each restart writes a fresh ~600MB DB snapshot until the disk fills.
#
# This `python3 -c "import app"` runs the same import gunicorn would —
# decorator evaluation, schema migrations, similarity-engine load,
# scheduler-thread init — but here, BEFORE the image gets tagged. If any
# of that fails, the docker build fails, the GHCR push never happens, and
# prod stays on the previous (working) image.
#
# The import needs DB_PATH (/app/data/quran.db) to exist because app.py
# loads the corpus into the similarity engine at import time. Stage the
# seed DB into the runtime path before the check; it'll be either
# overwritten or shadowed by the persistent volume mount at runtime, so
# leaving it in place has no side effects.
# ---------------------------------------------------------------------------
RUN mkdir -p /app/data && \
    cp /app/seed-quran.db /app/data/quran.db && \
    python3 -c "import app" && \
    rm /app/data/quran.db && \
    echo "[Dockerfile] app.py import check passed (image's /app/data/quran.db removed)"

# IMPORTANT: do NOT leave /app/data/quran.db in the image after the
# import check. Docker named-volume initialization copies the
# image's content at the mount point INTO an empty volume on first
# mount. If a fresh server creates a new volume (or someone runs
# `docker compose down -v`), Docker would then propagate the seed
# DB into the volume — masquerading as "existing data" and
# bypassing the entrypoint's data-preservation logic. The `rm`
# above ensures the image's /app/data/ is empty so volume init
# is a no-op.

# Copy mnemonic images as seed (entrypoint deploys to data volume)
COPY assets/mnemonic_images ./seed-mnemonic-images

# Copy built frontend into static/
COPY --from=frontend-build /build/dist ./static

# Copy entrypoint
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Create data directory for volume mount
RUN mkdir -p /app/data

# Build metadata — captured by GitHub Actions and passed as build
# args. The backend exposes these via /api/build-info so the admin
# dashboard can display "Last updated on X via commit Y" without
# any GitHub API call. Setting them at the END of the Dockerfile
# means the heavier earlier layers (npm ci, remotion browser ensure,
# pip install) stay cache-hot across deploys; only this trivial
# layer rebuilds when the SHA changes.
ARG BUILD_GIT_SHA=
ARG BUILD_GIT_SHA_SHORT=
ARG BUILD_GIT_DATE=
ARG BUILD_GIT_MESSAGE=
ENV BUILD_GIT_SHA=$BUILD_GIT_SHA \
    BUILD_GIT_SHA_SHORT=$BUILD_GIT_SHA_SHORT \
    BUILD_GIT_DATE=$BUILD_GIT_DATE \
    BUILD_GIT_MESSAGE=$BUILD_GIT_MESSAGE

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "300"]
