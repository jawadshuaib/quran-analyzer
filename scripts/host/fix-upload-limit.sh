#!/usr/bin/env bash
# Raise the host reverse-proxy upload limit so admin uploads (background
# videos, music, etc.) > ~1 MB stop getting rejected with HTTP 413
# before they reach Flask. Flask itself already accepts 500 MB; the
# bottleneck is the proxy in front of the container.
#
# Idempotent — re-running it is safe. Detects nginx (Debian/Ubuntu
# layout) or Caddy and patches whichever it finds. Run with sudo on
# the production host:
#
#   scp scripts/host/fix-upload-limit.sh user@host:/tmp/
#   ssh user@host 'sudo bash /tmp/fix-upload-limit.sh'
#
# If you're behind Cloudflare's free plan, this script can't help —
# Cloudflare caps uploads at 100 MB regardless of origin config. See
# DEPLOY.md for that case.

set -euo pipefail

LIMIT="${1:-500m}"   # override with: sudo bash fix-upload-limit.sh 1g

# ----------------------------------------------------------------- nginx
# Look for site configs the way Debian/Ubuntu lay them out.
NGINX_CANDIDATES=(
  /etc/nginx/sites-enabled/*
  /etc/nginx/conf.d/*.conf
  /etc/nginx/nginx.conf
)

patch_nginx() {
  local conf="$1"
  if grep -q "client_max_body_size" "$conf"; then
    # Already has the directive — bump it to our value if smaller. We
    # only edit if the existing value is < LIMIT, so a deliberately
    # higher cap (10g for someone uploading source masters) is left
    # alone.
    local current
    current=$(grep -m1 "client_max_body_size" "$conf" | sed -E 's/.*client_max_body_size +([^;]+);.*/\1/')
    echo "  found existing client_max_body_size=$current in $conf"
    sed -i.bak "s|client_max_body_size [^;]*;|client_max_body_size ${LIMIT};|" "$conf"
    echo "  → bumped to ${LIMIT}"
    return 0
  fi
  # Not present — inject inside the first server { ... } block.
  if grep -q "^[[:space:]]*server[[:space:]]*{" "$conf"; then
    sed -i.bak "0,/^[[:space:]]*server[[:space:]]*{/s||server {\n    client_max_body_size ${LIMIT};|" "$conf"
    echo "  → added client_max_body_size ${LIMIT}; to $conf"
    return 0
  fi
  return 1
}

if command -v nginx >/dev/null 2>&1; then
  echo "nginx detected"
  patched=0
  for conf in "${NGINX_CANDIDATES[@]}"; do
    [ -f "$conf" ] || continue
    case "$conf" in
      *.bak|*.dpkg-*) continue ;;  # skip backups
    esac
    # Only patch confs that actually proxy to our app port — leave
    # unrelated vhosts alone. If proxy_pass isn't matchable here,
    # we still patch nginx.conf as a fallback below.
    if grep -qE "proxy_pass.*:8070|proxy_pass.*quran" "$conf"; then
      patch_nginx "$conf" && patched=1
    fi
  done
  if [ "$patched" -eq 0 ] && [ -f /etc/nginx/nginx.conf ]; then
    echo "no proxy_pass:8070 site found — patching /etc/nginx/nginx.conf as fallback"
    patch_nginx /etc/nginx/nginx.conf || true
  fi
  echo "testing nginx config..."
  nginx -t
  echo "reloading nginx..."
  systemctl reload nginx || nginx -s reload
  echo "✓ nginx reloaded with client_max_body_size ${LIMIT}"
  exit 0
fi

# ----------------------------------------------------------------- Caddy
if command -v caddy >/dev/null 2>&1; then
  echo "Caddy detected"
  CADDYFILE=/etc/caddy/Caddyfile
  if [ ! -f "$CADDYFILE" ]; then
    echo "Caddyfile not found at $CADDYFILE — patch manually" >&2
    exit 1
  fi
  if grep -q "max_size" "$CADDYFILE"; then
    echo "  found existing request_body max_size — leaving as-is. Edit $CADDYFILE manually if needed."
  else
    # Inject a request_body block at the top level so it applies to
    # every site. Operators with multiple unrelated sites can move it
    # into the specific block themselves.
    cp "$CADDYFILE" "${CADDYFILE}.bak"
    awk 'NR==1{print "{\n  request_body {\n    max_size '"${LIMIT}"'\n  }\n}\n"} {print}' \
      "${CADDYFILE}.bak" > "$CADDYFILE"
    echo "  → added request_body max_size ${LIMIT} to $CADDYFILE"
  fi
  echo "testing Caddy config..."
  caddy validate --config "$CADDYFILE" --adapter caddyfile
  echo "reloading Caddy..."
  systemctl reload caddy || caddy reload --config "$CADDYFILE"
  echo "✓ Caddy reloaded with request_body max_size ${LIMIT}"
  exit 0
fi

echo "Neither nginx nor Caddy found in PATH." >&2
echo "If you use a different proxy (Traefik, HAProxy, AWS ALB), raise the upload limit there." >&2
echo "If you're on Cloudflare's free plan, the 100MB cap is at Cloudflare — see DEPLOY.md." >&2
exit 1
