#!/usr/bin/env bash
set -e

# ACM-AI - Start All Services (WSL/Linux)
# Usage: ./start-all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper: wait for a port to be listening
wait_port() {
    local port=$1 name=$2 i=0
    echo "  Waiting for $name on port $port..."
    while ! python3 -c "import socket; s=socket.socket(); s.settimeout(1); exit(0) if s.connect_ex(('127.0.0.1',$port))==0 else exit(1)" 2>/dev/null; do
        sleep 2
        i=$((i+1))
        if [ $i -ge 30 ]; then
            echo "  Timeout waiting for $name (port $port)"
            return 1
        fi
    done
    echo "  $name is ready!"
}

# Helper: wait for an HTTP health endpoint
wait_health() {
    local url=$1 name=$2 i=0
    echo "  Waiting for $name health ($url)..."
    while ! curl -sf "$url" >/dev/null 2>&1; do
        sleep 2
        i=$((i+1))
        if [ $i -ge 45 ]; then
            echo "  Timeout waiting for $name health"
            return 1
        fi
    done
    echo "  $name health check passed!"
}

echo "========================================"
echo "  ACM-AI - Starting All Services"
echo "========================================"
echo ""

# [0/5] Sync Python dependencies (must happen BEFORE service manager)
echo "[0/5] Syncing Python dependencies..."
UV_LINK_MODE=copy uv sync --quiet
echo "Dependencies synced."
echo ""

# [1/5] Clear ports - kill any processes on our ports
echo "[1/5] Clearing ports and fixing conflicts..."
uv run python scripts/service_manager.py fix --auto-fix 2>/dev/null || true
echo ""

# [2/5] Start SurrealDB
echo "[2/5] Starting SurrealDB..."
if docker compose ps surrealdb 2>/dev/null | grep -q "running"; then
    echo "SurrealDB is already running."
else
    docker compose up -d surrealdb
    wait_port 8000 "SurrealDB"
fi
echo ""

# [3/5] Start API Server
echo "[3/5] Starting API Server (port 5055)..."
cd "$SCRIPT_DIR"
# API_RELOAD=false: Uvicorn's StatReload blocks the event loop on WSL2's slow /mnt/* filesystem
API_RELOAD=false nohup uv run python run_api.py > /tmp/acm-ai-api.log 2>&1 &
echo $! > /tmp/acm-ai-api.pid
echo "API launched (PID: $(cat /tmp/acm-ai-api.pid))"
wait_health "http://localhost:5055/health" "API Server"
echo ""

# [4/5] Start Background Worker
echo "[4/5] Starting Background Worker..."
cd "$SCRIPT_DIR"
nohup uv run surreal-commands-worker --import-modules commands > /tmp/acm-ai-worker.log 2>&1 &
echo $! > /tmp/acm-ai-worker.pid
echo "Worker started (PID: $(cat /tmp/acm-ai-worker.pid))"
sleep 2
echo ""

# [5/5] Start Frontend (API is confirmed healthy before this point)
echo "[5/5] Starting Frontend (port 8502)..."
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
echo ""

# Post-startup health verification
echo "Verifying service health..."
cd "$SCRIPT_DIR"
uv run python scripts/service_manager.py status 2>/dev/null || true
