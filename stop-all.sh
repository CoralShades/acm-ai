#!/usr/bin/env bash

# ACM-AI - Stop All Services (WSL/Linux)
# Usage: ./stop-all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  ACM-AI - Stopping All Services"
echo "========================================"
echo ""

# Stop Frontend
echo "Stopping Frontend..."
if [ -f /tmp/acm-ai-frontend.pid ]; then
    PID=$(cat /tmp/acm-ai-frontend.pid)
    kill $PID 2>/dev/null || true
    rm -f /tmp/acm-ai-frontend.pid
fi
ps -ef | grep -E "npm run dev.*8502|next dev" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null || true

# Stop Background Worker
echo "Stopping Background Worker..."
if [ -f /tmp/acm-ai-worker.pid ]; then
    PID=$(cat /tmp/acm-ai-worker.pid)
    kill $PID 2>/dev/null || true
    rm -f /tmp/acm-ai-worker.pid
fi
ps -ef | grep "surreal-commands-worker" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null || true

# Stop API Server
echo "Stopping API Server..."
if [ -f /tmp/acm-ai-api.pid ]; then
    PID=$(cat /tmp/acm-ai-api.pid)
    kill $PID 2>/dev/null || true
    rm -f /tmp/acm-ai-api.pid
fi
ps -ef | grep "run_api.py" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null || true

# Stop SurrealDB
echo "Stopping SurrealDB..."
docker compose down 2>/dev/null || true

echo ""
echo "========================================"
echo "  All services stopped!"
echo "========================================"
