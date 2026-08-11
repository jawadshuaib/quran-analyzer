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

### Production topology (al-nuqta.com)

⚠️ **The nginx in front of this app lives in a sibling repo,
`the-intrinsic-value-project` (IV)**, at `docker/nginx/al-nuqta.conf`
inside that repo. The al-nuqta-com container only exposes port
`8070` on the host; IV's `iv-nginx` container terminates TLS and
proxies through to it.

That has a sharp edge: **any server-side `nginx.conf` patch is wiped
on the next IV deploy** (its workflow runs `git reset --hard
origin/main` before rebuild). The persistent fix has to land in the
IV repo's `docker/nginx/al-nuqta.conf`. The block to add inside the
canonical al-nuqta.com HTTPS server (the one with
`server_name al-nuqta.com;`):

```nginx
# Right after the security headers, before `location / { ... }`:
client_max_body_size 500M;

# Inside `location / { ... }`, after the proxy_set_header lines:
proxy_request_buffering off;
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
```

`proxy_request_buffering off` matters as much as the size cap —
without it, nginx buffers the whole upload to disk before forwarding,
which both stalls the client and can run nginx's tmp dir out of
space on big uploads. The 5-minute timeouts keep slow uploads from
getting killed mid-stream.

After committing and pushing to IV's `main`, the next IV deploy
rebuilds `iv-nginx` with the patched config and the fix sticks.

### One-step fix (only for hosts where you control nginx in-repo)

`scripts/host/fix-upload-limit.sh` detects whichever proxy is
installed and patches it idempotently. From your local checkout:

```sh
scp scripts/host/fix-upload-limit.sh user@host:/tmp/
ssh user@host 'sudo bash /tmp/fix-upload-limit.sh'
```

⚠️ This is a **one-off** patch — if your reverse proxy is managed by
another repo's CI (like the IV repo for al-nuqta.com), the next
deploy of that other repo will overwrite the change. In that case,
make the edit in the proxy-owning repo instead.

The script bumps the upload cap to 500 MB, validates the config, and
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
- It then runs `import_kaikki_cognates.py` transactionally, replacing only the
  reviewed `wiktionary` source rows from the versioned accepted-data artifact.
  This updates fresh databases and existing persistent volumes without
  disturbing SemiticRoots or Starling records.
- `.github/workflows/deploy.yml` runs `set -e` and prunes Docker
  images before pulling so a near-full disk fails the workflow loudly
  instead of silently (commit `f8195d6`).
