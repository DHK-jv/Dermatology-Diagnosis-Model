#!/bin/sh
set -eu

TEMPLATE="/app/frontend/js/runtime-env.template.js"
TARGET="/app/frontend/js/runtime-env.js"

if [ -f "$TEMPLATE" ]; then
  envsubst '${API_BASE_URL}' < "$TEMPLATE" > "$TARGET"
fi

exec "$@"
