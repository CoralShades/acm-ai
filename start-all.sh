#!/usr/bin/env bash
set -e

# ACM-AI - Start All Services (WSL/Linux)
# Usage: ./start-all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  ACM-AI - Starting All Services"
echo "========================================"
echo ""

# [1/4] Start SurrealDB
echo "[1/4] Checking SurrealDB..."
if docker compose ps surrealdb 2>/dev/null | grep -q "running"; then
    echo "SurrealDB is already running."
else
    echo "Starting SurrealDB via Docker Compose..."
    docker compose up -d surrealdb
    sleep 5
fi
echo ""

# [2/4] Start API Server
echo "[2/4] Starting API Server (port 5055)..."
cd "$SCRIPT_DIR"
nohup uv run python run_api.py > /tmp/acm-ai-api.log 2>&1 &
echo $! > /tmp/acm-ai-api.pid
echo "API started (PID: $(cat /tmp/acm-ai-api.pid))"
sleep 3
echo ""

# [3/4] Start Background Worker
echo "[3/4] Starting Background Worker..."
cd "$SCRIPT_DIR"
nohup uv run surreal-commands-worker --import-modules commands > /tmp/acm-ai-worker.log 2>&1 &
echo $! > /tmp/acm-ai-worker.pid
echo "Worker started (PID: $(cat /tmp/acm-ai-worker.pid))"
sleep 2
echo ""

# [4/4] Start Frontend
echo "[4/4] Starting Frontend (port 8502)..."
cd "$SCRIPT_DIR/frontend"
PORT=8502 nohup npm run dev -- -p 8502 > /tmp/acm-ai-frontend.log 2>&1 &
echo $! > /tmp/acm-ai-frontend.pid
echo "Frontend started (PID: $(cat /tmp/acm-ai-frontend.pid))"
echo ""

echo "========================================"
echo "  All services started!"
echo "========================================"
echo ""
echo "  Frontend:  http://localhost:8502"
echo "  API:       http://localhost:5055"
echo "  API Docs:  http://localhost:5055/docs"
echo ""
echo "  Logs:"
echo "    API:      tail -f /tmp/acm-ai-api.log"
echo "    Worker:   tail -f /tmp/acm-ai-worker.log"
echo "    Frontend: tail -f /tmp/acm-ai-frontend.log"
echo ""
echo "  To stop: ./stop-all.sh"
echo "========================================"
