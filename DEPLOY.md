# Deployment notes

The Flask app runs inside Docker, exposed on port `8070` per
`docker-compose.prod.yml`. A reverse proxy on the host (nginx, Caddy,
or Cloudflare) terminates TLS on `:443` and forwards to `:8070`.

## Reverse-proxy upload limit

Flask is configured to accept uploads up to **500 MB**
(`app.config["MAX_CONTENT_LENGTH"]` in `roots/backend/app.py`). The
host reverse proxy must be configured to allow at least the same, or
admin uploads (background videos, music tracks, etc.) get rejected
with **HTTP 413** before the request even reaches Flask.

Symptom: a small upload (e.g. 2 MB) returns "Upload rejected by
reverse proxy" in the admin UI, but the same upload works against
`localhost:5000` directly.

### One-step fix (nginx or Caddy)

`scripts/host/fix-upload-limit.sh` detects whichever proxy is
installed and patches it idempotently. From your local checkout:

```sh
scp scripts/host/fix-upload-limit.sh user@host:/tmp/
ssh user@host 'sudo bash /tmp/fix-upload-limit.sh'
```

It bumps the upload cap to 500 MB, validates the config, and
reloads. Override with a different size as the first arg:
`sudo bash /tmp/fix-upload-limit.sh 1g`.

If you'd rather edit by hand, the manual snippets are below.

### nginx fix

In the `server` (or `location`) block that proxies to the Docker
container, set:

```nginx
client_max_body_size 500m;
```

Then reload:

```sh
sudo nginx -t && sudo systemctl reload nginx
```

### Caddy fix

```caddy
your-host.example {
  request_body {
    max_size 500MB
  }
  reverse_proxy localhost:8070
}
```

### Cloudflare

Cloudflare's free plan caps client uploads at 100 MB regardless of
origin config. Pro is 200 MB; Business is 500 MB. If you're behind
Cloudflare on the free plan, large uploads (> 100 MB) need to bypass
the proxy — either upload directly to the origin's port `:8070`, or
use Cloudflare Tunnel which doesn't have the limit.

## Other deploy notes

- `docker-entrypoint.sh` runs `normalize_cognate_languages.py` on
  every container start to keep the cognate schema in sync with the
  seed DB. Failures are logged but don't block boot (commit `c982dbb`).
- `.github/workflows/deploy.yml` runs `set -e` and prunes Docker
  images before pulling so a near-full disk fails the workflow loudly
  instead of silently (commit `f8195d6`).
