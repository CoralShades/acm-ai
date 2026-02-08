#!/usr/bin/env bash

# ACM-AI - Start All Services with tmux (WSL/Linux)
# This creates a tmux session with 4 panes (one per service)
# Usage: ./start-all-tmux.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="acm-ai"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed. Installing..."
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

# Create new tmux session with first pane for SurrealDB
tmux new-session -d -s $SESSION_NAME -n "ACM-AI" -c "$SCRIPT_DIR"

# Set up pane layout: 4 panes in a grid (2x2)
tmux split-window -h -t $SESSION_NAME:0
tmux split-window -v -t $SESSION_NAME:0.0
tmux split-window -v -t $SESSION_NAME:0.1

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

# Pane 3 (bottom-right): Frontend
tmux send-keys -t $SESSION_NAME:0.3 "echo '=== Frontend (port 8502) ==='; sleep 4; cd $SCRIPT_DIR/frontend && PORT=8502 npm run dev -- -p 8502" C-m

echo "✅ All services starting in tmux session!"
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
echo "    ┌─────────────┬─────────────┐"
echo "    │ SurrealDB   │ API Server  │"
echo "    ├─────────────┼─────────────┤"
echo "    │ Worker      │ Frontend    │"
echo "    └─────────────┴─────────────┘"
echo "========================================"
echo ""

# Attach to the session
tmux attach -t $SESSION_NAME
