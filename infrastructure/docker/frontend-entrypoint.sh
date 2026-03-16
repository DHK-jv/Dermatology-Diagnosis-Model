#!/bin/sh
set -eu

TEMPLATE="/usr/share/nginx/html/js/runtime-env.template.js"
TARGET="/usr/share/nginx/html/js/runtime-env.js"

if [ -f "$TEMPLATE" ]; then
  envsubst '${API_BASE_URL}' < "$TEMPLATE" > "$TARGET"
fi

exec "$@"
