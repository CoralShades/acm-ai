#!/usr/bin/env bash

# ACM-AI - Start All Services with tmux (WSL/Linux)
# Creates a tmux session with 4 service panes + optional health dashboard
# Usage: ./start-all-tmux.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="acm-ai"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "tmux is not installed."
    echo "Run: sudo apt-get update && sudo apt-get install -y tmux"
    echo ""
    echo "Or use ./start-all.sh for background processes with log files."
    exit 1
fi

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null || true

echo "========================================"
echo "  ACM-AI - Starting All Services"
echo "  (tmux session: $SESSION_NAME)"
echo "========================================"
echo ""

# Sync dependencies before tmux (so output is visible)
echo "Syncing Python dependencies..."
cd "$SCRIPT_DIR"
UV_LINK_MODE=copy uv sync --quiet
echo "Dependencies synced."
echo ""

# Kill any processes occupying our ports before starting
echo "Clearing ports..."
uv run python scripts/service_manager.py fix --auto-fix 2>/dev/null || true
echo ""

# Also stop any leftover docker services
docker compose down 2>/dev/null || true

# Create new tmux session - start with full-width bottom pane for health
# Layout strategy: split bottom first (full-width), then split top into 2x2
tmux new-session -d -s $SESSION_NAME -n "ACM-AI" -c "$SCRIPT_DIR"

# Split: top 80% / bottom 20% (health strip spans full width)
tmux split-window -v -l 20% -t $SESSION_NAME:0.0

# Split the top pane (0) horizontally: left | right
tmux split-window -h -t $SESSION_NAME:0.0

# Split top-left (0) vertically: SurrealDB (top) / Worker (bottom)
tmux split-window -v -t $SESSION_NAME:0.0

# Split top-right (1) vertically: API (top) / Frontend (bottom)
tmux split-window -v -t $SESSION_NAME:0.2

# After all splits, pane indices are:
#   0 = top-left-top (SurrealDB)
#   1 = bottom (health dashboard, full width)
#   2 = top-right-top (API)
#   3 = top-left-bottom (Worker)
#   4 = top-right-bottom (Frontend)

# Helper: inline wait-for-port function (used by pane commands)
WAIT_PORT='wait_port() { local p=$1 n=$2 i=0; echo "Waiting for $n on port $p..."; while ! python3 -c "import socket; s=socket.socket(); s.settimeout(1); exit(0) if s.connect_ex((\"127.0.0.1\",$p))==0 else exit(1)" 2>/dev/null; do sleep 2; i=$((i+1)); if [ $i -ge 30 ]; then echo "Timeout waiting for $n"; break; fi; done; echo "$n is ready!"; }'

# Helper: inline wait-for-health function (HTTP check)
WAIT_HEALTH='wait_health() { local url=$1 n=$2 i=0; echo "Waiting for $n health..."; while ! curl -sf "$url" >/dev/null 2>&1; do sleep 2; i=$((i+1)); if [ $i -ge 45 ]; then echo "Timeout waiting for $n health"; break; fi; done; echo "$n health check passed!"; }'

# Pane 0 (top-left-top): SurrealDB
tmux send-keys -t $SESSION_NAME:0.0 "echo '=== SurrealDB (Database) ==='; cd $SCRIPT_DIR && docker compose up surrealdb" C-m

# Pane 2 (top-right-top): API Server - waits for SurrealDB port
tmux send-keys -t $SESSION_NAME:0.2 "cd $SCRIPT_DIR && $WAIT_PORT && wait_port 8000 SurrealDB && echo '=== API Server (port 5055) ===' && uv run python run_api.py" C-m

# Pane 3 (top-left-bottom): Worker - waits for SurrealDB port
tmux send-keys -t $SESSION_NAME:0.3 "cd $SCRIPT_DIR && $WAIT_PORT && wait_port 8000 SurrealDB && echo '=== Background Worker ===' && uv run surreal-commands-worker --import-modules commands" C-m

# Pane 4 (top-right-bottom): Frontend - waits for API health
tmux send-keys -t $SESSION_NAME:0.4 "cd $SCRIPT_DIR/frontend && $WAIT_HEALTH && wait_health http://localhost:5055/health 'API Server' && echo '=== Frontend (port 8502) ===' && PORT=8502 npm run dev -- -p 8502" C-m

# Pane 1 (bottom full-width): Health Dashboard - waits for API
tmux send-keys -t $SESSION_NAME:0.1 "cd $SCRIPT_DIR && $WAIT_HEALTH && wait_health http://localhost:5055/health 'API Server' && uv run python scripts/service_manager.py health" C-m

echo "All services starting in tmux session!"
echo ""
echo "========================================"
echo "  Access your application:"
echo "========================================"
echo "  Frontend:  http://localhost:8502"
echo "  API:       http://localhost:5055"
echo "  API Docs:  http://localhost:5055/docs"
echo ""
echo "========================================"
echo "  tmux commands:"
echo "========================================"
echo "  Attach to session:    tmux attach -t $SESSION_NAME"
echo "  Detach (exit view):   Ctrl+B, then D"
echo "  Switch panes:         Ctrl+B, then arrow keys"
echo "  Kill session:         tmux kill-session -t $SESSION_NAME"
echo "  Stop all services:    ./stop-all.sh"
echo ""
echo "  Pane layout:"
echo "    +-------------+-------------+"
echo "    | SurrealDB   | API Server  |"
echo "    +-------------+-------------+"
echo "    | Worker      | Frontend    |"
echo "    +-------------+-------------+"
echo "    |    Health Dashboard (live) |"
echo "    +---------------------------+"
echo "========================================"
echo ""

# Attach to the session
tmux attach -t $SESSION_NAME
