#!/usr/bin/env bash

# ACM-AI - Start All Services with tmux (WSL/Linux)
# This creates a tmux session with 5 panes (4 services + health dashboard)
# Usage: ./start-all-tmux.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="acm-ai"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "tmux is not installed. Installing..."
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

# Pre-flight check
echo "Running pre-flight checks..."
cd "$SCRIPT_DIR"
uv run python scripts/service_manager.py check 2>/dev/null || {
    echo ""
    echo "WARNING: Some pre-flight checks failed. Continuing anyway..."
    sleep 2
}
echo ""

# Sync dependencies before tmux (so output is visible)
echo "Syncing Python dependencies..."
cd "$SCRIPT_DIR"
UV_LINK_MODE=copy uv sync --quiet
echo "Dependencies synced."
echo ""

# Create new tmux session with first pane for SurrealDB
tmux new-session -d -s $SESSION_NAME -n "ACM-AI" -c "$SCRIPT_DIR"

# Set up pane layout: 2x2 grid + bottom health strip (5 panes)
# Start with the first pane (pane 0)
tmux split-window -h -t $SESSION_NAME:0       # Split horizontally: pane 0 | pane 1
tmux split-window -v -t $SESSION_NAME:0.0     # Split pane 0 vertically: top-left (0) / bottom-left (2)
tmux split-window -v -t $SESSION_NAME:0.1     # Split pane 1 vertically: top-right (1) / bottom-right (3)

# Create bottom health strip by splitting the full width
tmux select-pane -t $SESSION_NAME:0.3
tmux split-window -v -p 20 -t $SESSION_NAME:0  # Bottom pane for health dashboard

# Pane 0 (top-left): SurrealDB
tmux send-keys -t $SESSION_NAME:0.0 "echo '=== SurrealDB (Database) ==='; docker compose up surrealdb" C-m

# Wait for SurrealDB to start
sleep 3

# Pane 1 (top-right): API Server
tmux send-keys -t $SESSION_NAME:0.1 "echo '=== API Server (port 5055) ==='; sleep 2; cd $SCRIPT_DIR && uv run python run_api.py" C-m

# Wait for API to initialize
sleep 2

# Pane 2 (bottom-left): Background Worker
tmux send-keys -t $SESSION_NAME:0.2 "echo '=== Background Worker ==='; sleep 3; cd $SCRIPT_DIR && uv run surreal-commands-worker --import-modules commands" C-m

# Pane 3 (middle-right): Frontend
tmux send-keys -t $SESSION_NAME:0.3 "echo '=== Frontend (port 8502) ==='; sleep 4; cd $SCRIPT_DIR/frontend && PORT=8502 npm run dev -- -p 8502" C-m

# Pane 4 (bottom): Health Dashboard
tmux send-keys -t $SESSION_NAME:0.4 "sleep 8; cd $SCRIPT_DIR && uv run python scripts/service_manager.py health" C-m

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
