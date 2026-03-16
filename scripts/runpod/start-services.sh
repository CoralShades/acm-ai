#!/bin/bash
# ACM-AI RunPod Service Starter (Native — no Docker)
# Starts SurrealDB, Ollama, API, Worker, and Frontend in named tmux sessions
# Usage: bash /workspace/acm-ai/scripts/runpod/start-services.sh
set -euo pipefail

REPO_DIR="/workspace/acm-ai"
DATA_DIR="/workspace/data"
export PATH="$HOME/.local/bin:$PATH"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

wait_for_service() {
    local name="$1" url="$2" max_attempts="${3:-30}" interval="${4:-2}"
    echo -n "  Waiting for $name"
    for i in $(seq 1 "$max_attempts"); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC} (${i}/${max_attempts})"
            return 0
        fi
        echo -n "."
        sleep "$interval"
    done
    echo -e " ${RED}TIMEOUT${NC}"
    return 1
}

echo "========================================"
echo "  ACM-AI — Starting All Services"
echo "========================================"

mkdir -p "$REPO_DIR/logs" "$DATA_DIR"/{surrealdb,ollama}

# Kill existing tmux sessions (clean slate)
tmux kill-server 2>/dev/null || true
sleep 1

# ── 1. SurrealDB ──────────────────────
echo -e "\n[1/5] Starting SurrealDB (port 8000)..."
tmux new-session -d -s surrealdb \
    "surreal start --log info --user root --pass root --bind 0.0.0.0:8000 surrealkv://$DATA_DIR/surrealdb/open_notebook.db 2>&1 | tee $REPO_DIR/logs/surrealdb.log"

if ! wait_for_service "SurrealDB" "http://localhost:8000/health" 15 2; then
    echo -e "${RED}SurrealDB failed to start. Check: tmux attach -t surrealdb${NC}"
    exit 1
fi

# ── 2. Ollama ─────────────────────────
echo "[2/5] Starting Ollama (port 11434)..."
tmux new-session -d -s ollama \
    "OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=$DATA_DIR/ollama ollama serve 2>&1 | tee $REPO_DIR/logs/ollama.log"

if ! wait_for_service "Ollama" "http://localhost:11434/api/tags" 15 2; then
    echo -e "${YELLOW}Ollama slow to start — continuing (models may not be ready yet)${NC}"
fi

# ── 3. API Server ─────────────────────
echo "[3/5] Starting API server (port 5055)..."
tmux new-session -d -s api -c "$REPO_DIR" \
    "export PATH=\"$HOME/.local/bin:\$PATH\"; cd $REPO_DIR && API_HOST=0.0.0.0 API_RELOAD=false uv run python run_api.py 2>&1 | tee logs/api.log"

if ! wait_for_service "API" "http://localhost:5055/health" 30 3; then
    echo -e "${RED}API failed to start. Check: tmux attach -t api${NC}"
    exit 1
fi

# ── 4. Background Worker ──────────────
echo "[4/5] Starting background worker..."
tmux new-session -d -s worker -c "$REPO_DIR" \
    "export PATH=\"$HOME/.local/bin:\$PATH\"; export CUDA_VISIBLE_DEVICES=''; cd $REPO_DIR && uv run python run_worker.py --import-modules commands 2>&1 | tee logs/worker.log"
# Worker has no HTTP endpoint — just verify the tmux session exists
sleep 2
if tmux has-session -t worker 2>/dev/null; then
    echo -e "  ${GREEN}Worker session started${NC}"
else
    echo -e "  ${YELLOW}Worker session may have exited — check logs${NC}"
fi

# ── 5. Frontend ───────────────────────
echo "[5/5] Starting frontend (port 8502)..."
tmux new-session -d -s frontend -c "$REPO_DIR/frontend" \
    "cd $REPO_DIR/frontend && PORT=8502 npm run dev -- -p 8502 2>&1 | tee $REPO_DIR/logs/frontend.log"

# Frontend takes a moment to compile — non-blocking check
echo -n "  Waiting for frontend"
for i in $(seq 1 10); do
    if curl -sf http://localhost:8502 > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    echo -n "."
    sleep 3
done
echo ""

# ── Summary ───────────────────────────
echo ""
echo "========================================"
echo "  All services started!"
echo "========================================"
echo ""
echo "  tmux sessions:"
tmux list-sessions 2>/dev/null | sed 's/^/    /' || echo "    (none)"
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
