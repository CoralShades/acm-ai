#!/usr/bin/env bash

# ACM-AI - Start All Services with tmux (WSL/Linux)
# Creates a tmux session with 4 service panes + health dashboard
# Usage: ./start-all-tmux.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="acm-ai"

# Detect WSL running against Windows filesystem (9P mount) — extremely slow and crash-prone
if [[ "$SCRIPT_DIR" == /mnt/* ]]; then
    echo "WARNING: Running from Windows filesystem (/mnt/...) via WSL2."
    echo "The 9P bridge causes severe I/O overhead and can crash WSL2 + Docker."
    echo ""
    echo "Options:"
    echo "  1. Use start-all.bat from Windows CMD/PowerShell (recommended)"
    echo "  2. Clone the repo inside WSL: git clone ... ~/acm-ai && cd ~/acm-ai"
    echo ""
    read -p "Continue anyway? (y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

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

# Preflight checks
echo "Running preflight checks..."
if ! uv run python scripts/preflight_checks.py; then
    echo "PREFLIGHT FAILED — fix issues above before starting."
    exit 1
fi
echo ""

# Kill any processes occupying our ports before starting
echo "Clearing ports..."
uv run python scripts/service_manager.py fix --auto-fix 2>/dev/null || true
echo ""

# Also stop any leftover docker services
docker compose down 2>/dev/null || true

# Create new tmux session
# Layout strategy: split bottom first (full-width health strip), then split top into 2x2
tmux new-session -d -s $SESSION_NAME -n "ACM-AI" -c "$SCRIPT_DIR"

# Split: top 80% / bottom 20% (health strip spans full width)
tmux split-window -v -l 20% -t $SESSION_NAME:0.0

# Split the top pane (0) horizontally: left | right
tmux split-window -h -t $SESSION_NAME:0.0

# Split top-left (0) vertically: SurrealDB (top) / Worker (bottom)
tmux split-window -v -t $SESSION_NAME:0.0

# Split top-right (2) vertically: API (top) / Frontend (bottom)
tmux split-window -v -t $SESSION_NAME:0.2

# After all splits, pane indices are:
#   0 = top-left-top     (SurrealDB)
#   1 = bottom full-width (Health Dashboard)
#   2 = top-right-top    (API Server)
#   3 = top-left-bottom  (Worker)
#   4 = top-right-bottom (Frontend)

SD="$SCRIPT_DIR"

# Pane 0: SurrealDB (starts immediately)
tmux send-keys -t $SESSION_NAME:0.0 "echo '=== SurrealDB (Database) ==='; cd $SD && docker compose up surrealdb" C-m

# Pane 2: API Server (waits for SurrealDB port 8000)
# API_RELOAD=false: Uvicorn's StatReload blocks the event loop on WSL2's slow /mnt/* filesystem
tmux send-keys -t $SESSION_NAME:0.2 "cd $SD && $SD/scripts/_wait_for_port.sh 8000 SurrealDB 60 && echo '=== API Server (port 5055) ===' && API_RELOAD=false uv run python run_api.py" C-m

# Pane 3: Worker (waits for SurrealDB port 8000)
tmux send-keys -t $SESSION_NAME:0.3 "cd $SD && $SD/scripts/_wait_for_port.sh 8000 SurrealDB 60 && echo '=== Background Worker ===' && uv run python run_worker.py --import-modules commands" C-m

# Pane 4: Frontend (waits for API health - ensures API is fully initialized)
tmux send-keys -t $SESSION_NAME:0.4 "cd $SD && $SD/scripts/_wait_for.sh http://localhost:5055/health 'API Server' 120 && echo '=== Frontend (port 8502) ===' && cd $SD/frontend && PORT=8502 npm run dev -- -p 8502" C-m

# Pane 1: Health Dashboard (waits for API, then shows live status)
tmux send-keys -t $SESSION_NAME:0.1 "cd $SD && $SD/scripts/_wait_for.sh http://localhost:5055/health 'API Server' 120 && uv run python scripts/service_manager.py health" C-m

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
