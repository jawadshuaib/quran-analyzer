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

# Install system deps for potential native packages
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY roots/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY roots/backend/app.py ./app.py

# Copy database as seed (entrypoint copies to volume on first run)
COPY assets/quran.db ./seed-quran.db

# Copy built frontend into static/
COPY --from=frontend-build /build/dist ./static

# Copy entrypoint
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Create data directory for volume mount
RUN mkdir -p /app/data

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120"]
