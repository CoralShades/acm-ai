#!/usr/bin/env bash
# Wait for an HTTP endpoint to respond.
# Usage: scripts/_wait_for.sh URL [NAME] [TIMEOUT_SECONDS]
#
# Examples:
#   scripts/_wait_for.sh http://localhost:5055/health "API Server" 90
#   scripts/_wait_for.sh http://localhost:8502 "Frontend" 60

URL="$1"
NAME="${2:-service}"
TIMEOUT="${3:-90}"

echo "Waiting for $NAME ($URL)..."
elapsed=0
while ! curl -sf "$URL" >/dev/null 2>&1; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ $elapsed -ge "$TIMEOUT" ]; then
        echo "Timeout waiting for $NAME after ${TIMEOUT}s"
        exit 1
    fi
done
echo "$NAME is ready!"
