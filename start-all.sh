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

# [0/5] Pre-flight check
echo "[0/5] Running pre-flight checks..."
if uv run python scripts/service_manager.py check 2>/dev/null; then
    echo "Pre-flight checks passed."
else
    echo ""
    echo "WARNING: Some pre-flight checks failed."
    echo "Continuing anyway... (use Ctrl+C to abort)"
    sleep 2
fi
echo ""

# [1/5] Sync Python dependencies (must happen BEFORE launching services)
echo "[1/5] Syncing Python dependencies..."
cd "$SCRIPT_DIR"
UV_LINK_MODE=copy uv sync --quiet
echo "Dependencies synced."
echo ""

# [2/5] Start SurrealDB
echo "[2/5] Checking SurrealDB..."
if docker compose ps surrealdb 2>/dev/null | grep -q "running"; then
    echo "SurrealDB is already running."
else
    echo "Starting SurrealDB via Docker Compose..."
    docker compose up -d surrealdb
    sleep 5
fi
echo ""

# [3/5] Start API Server
echo "[3/5] Starting API Server (port 5055)..."
# Check for port conflict
if python3 -c "import socket; s=socket.socket(); s.settimeout(1); exit(0 if s.connect_ex(('127.0.0.1',5055)) else 1)" 2>/dev/null; then
    cd "$SCRIPT_DIR"
    nohup uv run python run_api.py > /tmp/acm-ai-api.log 2>&1 &
    echo $! > /tmp/acm-ai-api.pid
    echo "API started (PID: $(cat /tmp/acm-ai-api.pid))"
else
    echo "WARNING: Port 5055 is already in use. Skipping API start."
fi
sleep 3
echo ""

# [4/5] Start Background Worker
echo "[4/5] Starting Background Worker..."
cd "$SCRIPT_DIR"
nohup uv run surreal-commands-worker --import-modules commands > /tmp/acm-ai-worker.log 2>&1 &
echo $! > /tmp/acm-ai-worker.pid
echo "Worker started (PID: $(cat /tmp/acm-ai-worker.pid))"
sleep 2
echo ""

# [5/5] Start Frontend
echo "[5/5] Starting Frontend (port 8502)..."
# Check for port conflict
if python3 -c "import socket; s=socket.socket(); s.settimeout(1); exit(0 if s.connect_ex(('127.0.0.1',8502)) else 1)" 2>/dev/null; then
    cd "$SCRIPT_DIR/frontend"
    PORT=8502 nohup npm run dev -- -p 8502 > /tmp/acm-ai-frontend.log 2>&1 &
    echo $! > /tmp/acm-ai-frontend.pid
    echo "Frontend started (PID: $(cat /tmp/acm-ai-frontend.pid))"
else
    echo "WARNING: Port 8502 is already in use. Skipping Frontend start."
fi
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
