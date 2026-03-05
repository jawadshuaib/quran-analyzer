# Hosting & Deployment

## Architecture

- **Single container**: Flask serves the API and the static frontend build (no separate nginx container)
- **Host-level nginx**: Reverse-proxies `yourdomain.com` → container port 8070
- **SSL**: Certbot on the host handles Let's Encrypt
- **Database**: `quran.db` baked into image, overwritten on the Docker volume on every deploy so AI translations, word meanings, and judge results propagate automatically
- **CI/CD**: Push to `main` → GitHub Actions builds image → pushes to GHCR → SSHs into server to pull & restart

## Server-Side Setup (one-time)

### 1. Prepare the directory

```bash
mkdir -p /opt/quran-root-analyzer
```

Copy `docker-compose.prod.yml` from the repo root to `/opt/quran-root-analyzer/` on your VPS.

### 2. Point your domain

Add an A record for your domain pointing to your server's IP address.

### 3. Create nginx site config

```bash
sudo nano /etc/nginx/sites-available/yourdomain.com
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8070;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. SSL with Certbot

```bash
sudo certbot --nginx -d yourdomain.com
```

### 5. GitHub Secrets

Add these three secrets in your repo settings (**Settings > Secrets and variables > Actions**):

| Secret | Value |
|--------|-------|
| `SERVER_HOST` | Your server's IP or hostname |
| `SERVER_USER` | SSH username (e.g. `root` or a deploy user) |
| `SERVER_SSH_KEY` | Private SSH key for that user |

## How It Works

On every push to `main`, the GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. Builds the Docker image (multi-stage: frontend build + Python runtime)
2. Pushes to `ghcr.io/<owner>/quran-root-analyzer:latest`
3. SSHs into the server, pulls the new image, recreates the container, prunes old images

The Docker entrypoint overwrites `quran.db` on the volume with the latest version from the image on every deploy. This ensures AI translations, word meanings, and judge results are always up to date. Make sure `assets/quran.db` is current before pushing.

## Local Docker Testing

```bash
docker build -t quran-test .
docker run -p 8070:8000 -v quran-test-data:/app/data quran-test
```

Verify:

- `http://localhost:8070` — SPA loads
- `http://localhost:8070/api/surahs` — JSON response
- `http://localhost:8070/root/Hmd` — SPA loads (not 404)

## Updating the docker-compose.prod.yml Image Name

The default image in `docker-compose.prod.yml` is `ghcr.io/jawadshuaib/quran-root-analyzer:latest`. If your GitHub username or repo differs, update the `image:` field accordingly.
