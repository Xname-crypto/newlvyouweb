#!/bin/sh
set -eu

: "${PORT:=8080}"
sed "s/\${PORT}/${PORT}/g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

cat > /usr/share/nginx/html/env.js <<EOF
window.__APP_ENV__ = {
  VITE_SUPABASE_URL: "${VITE_SUPABASE_URL:-}",
  VITE_SUPABASE_ANON_KEY: "${VITE_SUPABASE_ANON_KEY:-}",
  VITE_API_BASE_URL: "${VITE_API_BASE_URL:-}"
}
EOF

exec nginx -g 'daemon off;'
