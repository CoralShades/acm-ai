#!/usr/bin/env bash
# Wait for a TCP port to be listening.
# Usage: scripts/_wait_for_port.sh PORT [NAME] [TIMEOUT_SECONDS]
#
# Examples:
#   scripts/_wait_for_port.sh 8000 "SurrealDB" 60
#   scripts/_wait_for_port.sh 5055 "API Server" 90

PORT="$1"
NAME="${2:-service}"
TIMEOUT="${3:-60}"

echo "Waiting for $NAME on port $PORT..."
elapsed=0
while ! python3 -c "import socket; s=socket.socket(); s.settimeout(1); exit(0) if s.connect_ex(('127.0.0.1',$PORT))==0 else exit(1)" 2>/dev/null; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ $elapsed -ge "$TIMEOUT" ]; then
        echo "Timeout waiting for $NAME (port $PORT) after ${TIMEOUT}s"
        exit 1
    fi
done
echo "$NAME (port $PORT) is ready!"
