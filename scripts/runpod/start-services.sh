#!/bin/bash
# ACM-AI RunPod Service Starter (Native — no Docker)
# Starts SurrealDB, Ollama, API, Worker, and Frontend in named tmux sessions
# Usage: bash /workspace/acm-ai/scripts/runpod/start-services.sh
set -euo pipefail

REPO_DIR="/workspace/acm-ai"
DATA_DIR="/workspace/data"
export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo "  ACM-AI — Starting All Services"
echo "========================================"

mkdir -p "$REPO_DIR/logs" "$DATA_DIR"/{surrealdb,ollama}

# Kill existing tmux sessions
tmux kill-server 2>/dev/null || true
sleep 1

# Start SurrealDB
echo "[1/5] Starting SurrealDB (port 8000)..."
tmux new-session -d -s surrealdb \
    "surreal start --log info --user root --pass root --bind 0.0.0.0:8000 surrealkv://$DATA_DIR/surrealdb/open_notebook.db 2>&1 | tee $REPO_DIR/logs/surrealdb.log"
sleep 3

# Start Ollama
echo "[2/5] Starting Ollama (port 11434)..."
tmux new-session -d -s ollama \
    "OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=$DATA_DIR/ollama ollama serve 2>&1 | tee $REPO_DIR/logs/ollama.log"
sleep 3

# Wait for SurrealDB
for i in $(seq 1 10); do
    curl -sf http://localhost:8000/health > /dev/null 2>&1 && break
    sleep 1
done

# Start API server
echo "[3/5] Starting API server (port 5055)..."
tmux new-session -d -s api -c "$REPO_DIR" \
    "export PATH=\"$HOME/.local/bin:\$PATH\"; cd $REPO_DIR && API_HOST=0.0.0.0 API_RELOAD=false uv run python run_api.py 2>&1 | tee logs/api.log"

# Wait for API to be ready
echo "Waiting for API..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:5055/health > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    sleep 3
done

# Start background worker
echo "[4/5] Starting background worker..."
tmux new-session -d -s worker -c "$REPO_DIR" \
    "export PATH=\"$HOME/.local/bin:\$PATH\"; cd $REPO_DIR && uv run python run_worker.py --import-modules commands 2>&1 | tee logs/worker.log"

# Start frontend
echo "[5/5] Starting frontend (port 8502)..."
tmux new-session -d -s frontend -c "$REPO_DIR/frontend" \
    "cd $REPO_DIR/frontend && PORT=8502 npm run dev -- -p 8502 2>&1 | tee $REPO_DIR/logs/frontend.log"

# Show status
sleep 3
echo ""
echo "========================================"
echo "  All services started!"
echo "========================================"
echo ""
echo "  tmux sessions:"
tmux list-sessions 2>/dev/null || echo "  (none)"
echo ""
echo "  Local access:"
echo "    API:       http://localhost:5055"
echo "    API Docs:  http://localhost:5055/docs"
echo "    Frontend:  http://localhost:8502"
echo "    SurrealDB: http://localhost:8000"
echo "    Ollama:    http://localhost:11434"
echo ""
echo "  Terminal access:"
echo "    tmux attach -t api        # API logs"
echo "    tmux attach -t worker     # Worker logs"
echo "    tmux attach -t frontend   # Frontend logs"
echo "    tmux attach -t ollama     # Ollama logs"
echo "    tmux attach -t surrealdb  # SurrealDB logs"
echo "    Ctrl+B then D to detach"
echo ""
echo "  Run health check:"
echo "    bash $REPO_DIR/scripts/runpod/health-check.sh"
