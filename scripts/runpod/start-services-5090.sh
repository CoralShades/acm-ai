#!/bin/bash
# ACM-AI RunPod RTX 5090 — Service Launcher
# Starts Docker/Langfuse + native services in named tmux sessions
# Usage: bash /workspace/acm-ai/scripts/runpod/start-services-5090.sh
set -euo pipefail

REPO_DIR="${REPO_DIR:-/workspace/acm-ai}"
DATA_DIR="${DATA_DIR:-/workspace/data}"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
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
echo "  ACM-AI RTX 5090 — Starting Services"
echo "========================================"

mkdir -p "$REPO_DIR/logs" "$DATA_DIR"/{surrealdb,ollama,uploads}
mkdir -p "$DATA_DIR"/langfuse/{postgres,clickhouse,clickhouse-logs,redis,minio}

# ── Pre-flight: PyTorch sm_120 guard ───
# RTX 5090 (Blackwell, sm_120) needs PyTorch nightly with cu128.
# Standard stable releases only support up to sm_90. If uv sync ran,
# it may have downgraded torch. Detect and auto-fix here.
echo -e "\n${CYAN}[pre]${NC} Checking PyTorch CUDA compatibility..."
TORCH_CUDA_OK=false
if command -v "$REPO_DIR/.venv/bin/python" &>/dev/null; then
    TORCH_ARCHS=$("$REPO_DIR/.venv/bin/python" -c "
import torch
archs = torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else []
print(' '.join(archs))
" 2>/dev/null || echo "")

    if echo "$TORCH_ARCHS" | grep -q "sm_120"; then
        TORCH_VER=$("$REPO_DIR/.venv/bin/python" -c "import torch; print(torch.__version__)" 2>/dev/null)
        echo -e "  ${GREEN}[OK]${NC} PyTorch $TORCH_VER supports sm_120 (RTX 5090)"
        TORCH_CUDA_OK=true
    else
        echo -e "  ${YELLOW}[FIX]${NC} PyTorch missing sm_120 support (archs: $TORCH_ARCHS)"
        echo "  Installing PyTorch stable cu128 — this takes 2-4 minutes..."
        "$REPO_DIR/.venv/bin/pip" install --force-reinstall \
            torch torchvision torchaudio \
            --index-url https://download.pytorch.org/whl/cu128 \
            2>&1 | tail -3

        # Verify the fix
        TORCH_ARCHS_NEW=$("$REPO_DIR/.venv/bin/python" -c "
import torch
archs = torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else []
print(' '.join(archs))
" 2>/dev/null || echo "")
        if echo "$TORCH_ARCHS_NEW" | grep -q "sm_120"; then
            TORCH_VER=$("$REPO_DIR/.venv/bin/python" -c "import torch; print(torch.__version__)" 2>/dev/null)
            echo -e "  ${GREEN}[OK]${NC} Fixed — PyTorch $TORCH_VER now supports sm_120"
            TORCH_CUDA_OK=true
        else
            echo -e "  ${RED}[FAIL]${NC} PyTorch still missing sm_120 after reinstall"
            echo "  Docling GPU inference will fail. Manual fix:"
            echo "    .venv/bin/pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"
        fi
    fi
else
    echo -e "  ${YELLOW}[SKIP]${NC} Python venv not found — skipping torch check"
fi

# Kill existing tmux sessions (clean slate)
tmux kill-server 2>/dev/null || true
sleep 1

# ── 0. Docker & Langfuse Stack ───────
echo -e "\n${CYAN}[0/7]${NC} Starting Docker & Langfuse stack..."
if command -v docker &>/dev/null; then
    # Ensure Docker daemon is running
    if ! docker info &>/dev/null 2>&1; then
        echo "  Starting Docker daemon..."
        dockerd &>/dev/null &
        sleep 3
        if ! docker info &>/dev/null 2>&1; then
            echo -e "  ${YELLOW}Docker daemon failed to start — Langfuse will be unavailable${NC}"
        fi
    fi

    if docker info &>/dev/null 2>&1; then
        # Fix ClickHouse volume permissions (user 101:101)
        chown -R 101:101 "$DATA_DIR/langfuse/clickhouse" "$DATA_DIR/langfuse/clickhouse-logs" 2>/dev/null || true

        cd "$REPO_DIR/scripts/runpod"
        docker compose -f docker-compose.runpod.yml up -d 2>&1 | tail -5
        cd "$REPO_DIR"

        echo -n "  Waiting for Langfuse"
        for i in $(seq 1 40); do
            if curl -sf http://localhost:3000/api/public/health > /dev/null 2>&1; then
                echo -e " ${GREEN}ready${NC} (${i}/40)"
                break
            fi
            echo -n "."
            sleep 3
        done
        echo ""
    fi
else
    echo -e "  ${YELLOW}Docker not available — skipping Langfuse${NC}"
fi

# ── 1. SurrealDB ─────────────────────
echo -e "\n${CYAN}[1/7]${NC} Starting SurrealDB (port 8000)..."
tmux new-session -d -s surrealdb \
    "surreal start --log info --user root --pass root --bind 0.0.0.0:8000 surrealkv://$DATA_DIR/surrealdb/open_notebook.db 2>&1 | tee $REPO_DIR/logs/surrealdb.log"

if ! wait_for_service "SurrealDB" "http://localhost:8000/health" 15 2; then
    echo -e "${RED}SurrealDB failed to start. Check: tmux attach -t surrealdb${NC}"
    exit 1
fi

# ── 2. Ollama ────────────────────────
echo -e "${CYAN}[2/7]${NC} Starting Ollama (port 11434)..."
# Load VRAM tuning from .env if available
MAX_MODELS="${OLLAMA_MAX_LOADED_MODELS:-2}"
NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-2}"

tmux new-session -d -s ollama \
    "OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=$DATA_DIR/ollama OLLAMA_MAX_LOADED_MODELS=$MAX_MODELS OLLAMA_NUM_PARALLEL=$NUM_PARALLEL ollama serve 2>&1 | tee $REPO_DIR/logs/ollama.log"

if ! wait_for_service "Ollama" "http://localhost:11434/api/tags" 15 2; then
    echo -e "${YELLOW}Ollama slow to start — continuing${NC}"
fi

# ── 3. API Server ────────────────────
echo -e "${CYAN}[3/7]${NC} Starting API server (port 5055)..."
tmux new-session -d -s api -c "$REPO_DIR" \
    "cd $REPO_DIR && API_HOST=0.0.0.0 API_RELOAD=false .venv/bin/python run_api.py 2>&1 | tee logs/api.log"

if ! wait_for_service "API" "http://localhost:5055/health" 30 3; then
    echo -e "${RED}API failed to start. Check: tmux attach -t api${NC}"
    exit 1
fi

# ── 4. Background Worker ─────────────
echo -e "${CYAN}[4/7]${NC} Starting background worker..."
tmux new-session -d -s worker -c "$REPO_DIR" \
    "cd $REPO_DIR && .venv/bin/python run_worker.py --import-modules commands 2>&1 | tee logs/worker.log"
sleep 2
if tmux has-session -t worker 2>/dev/null; then
    echo -e "  ${GREEN}Worker session started${NC}"
else
    echo -e "  ${YELLOW}Worker session may have exited — check logs${NC}"
fi

# ── 5. Frontend (production) ─────────
echo -e "${CYAN}[5/7]${NC} Starting frontend (port 8502, production)..."
# Load API_URL from .env so the /config route returns the correct URL to the browser
FE_API_URL=""
if [[ -f "$REPO_DIR/.env" ]]; then
    FE_API_URL=$(grep '^API_URL=' "$REPO_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || echo "")
fi
FE_ENV="PORT=8502 INTERNAL_API_URL=http://localhost:5055"
[[ -n "$FE_API_URL" ]] && FE_ENV="$FE_ENV API_URL=$FE_API_URL"

# Use production mode if build exists, fall back to dev mode
if [[ -d "$REPO_DIR/frontend/.next" ]]; then
    tmux new-session -d -s frontend -c "$REPO_DIR/frontend" \
        "cd $REPO_DIR/frontend && $FE_ENV npm run start 2>&1 | tee $REPO_DIR/logs/frontend.log"
else
    echo -e "  ${YELLOW}No .next build found — using dev mode${NC}"
    tmux new-session -d -s frontend -c "$REPO_DIR/frontend" \
        "cd $REPO_DIR/frontend && $FE_ENV npm run dev -- -p 8502 2>&1 | tee $REPO_DIR/logs/frontend.log"
fi

echo -n "  Waiting for frontend"
for i in $(seq 1 15); do
    if curl -sf http://localhost:8502 > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    echo -n "."
    sleep 3
done
echo ""

# ── 6. Cloudflare Tunnel ─────────────
echo -e "${CYAN}[6/7]${NC} Starting Cloudflare tunnel..."
# Source .env for CF_TUNNEL_TOKEN if not already in environment
if [[ -z "${CF_TUNNEL_TOKEN:-}" && -f "$REPO_DIR/.env" ]]; then
    CF_TUNNEL_TOKEN=$(grep '^CF_TUNNEL_TOKEN=' "$REPO_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || echo "")
fi

if [[ -n "${CF_TUNNEL_TOKEN:-}" ]]; then
    tmux new-session -d -s tunnel \
        "cloudflared tunnel run --token $CF_TUNNEL_TOKEN 2>&1 | tee $REPO_DIR/logs/tunnel.log"
    sleep 3
    if tmux has-session -t tunnel 2>/dev/null; then
        echo -e "  ${GREEN}Tunnel session started${NC}"
    else
        echo -e "  ${YELLOW}Tunnel session may have exited — check logs${NC}"
    fi
else
    echo -e "  ${YELLOW}CF_TUNNEL_TOKEN not set — tunnel skipped${NC}"
    echo "  Set CF_TUNNEL_TOKEN in .env or environment, then run:"
    echo "    bash $REPO_DIR/scripts/runpod/start-tunnel.sh"
fi

# ── Summary ──────────────────────────
echo ""
echo "========================================"
echo "  All services started!"
echo "========================================"
echo ""
echo "  tmux sessions:"
tmux list-sessions 2>/dev/null | sed 's/^/    /' || echo "    (none)"
echo ""
echo "  Local access:"
echo "    API:         http://localhost:5055"
echo "    API Docs:    http://localhost:5055/docs"
echo "    Frontend:    http://localhost:8502"
echo "    SurrealDB:   http://localhost:8000"
echo "    Ollama:      http://localhost:11434"
echo "    Langfuse:    http://localhost:3000"
echo ""
echo "  External access (via Cloudflare tunnel):"
echo "    API:         https://acmapi.silvatron.au"
echo "    Frontend:    https://acm.silvatron.au"
echo ""
echo "  Terminal access:"
echo "    tmux attach -t api        # API logs"
echo "    tmux attach -t worker     # Worker logs"
echo "    tmux attach -t frontend   # Frontend logs"
echo "    tmux attach -t ollama     # Ollama logs"
echo "    tmux attach -t surrealdb  # SurrealDB logs"
echo "    tmux attach -t tunnel     # Tunnel logs"
echo "    Ctrl+B then D to detach"
echo ""
echo "  Health check:"
echo "    bash $REPO_DIR/scripts/runpod/health-check-5090.sh"

# Langfuse key warning
if [[ -f "$REPO_DIR/.env" ]]; then
    LF_KEY=$(grep '^LANGFUSE_SECRET_KEY=' "$REPO_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"')
    if [[ "$LF_KEY" == "sk-lf-CHANGE-ME" ]]; then
        echo ""
        echo -e "  ${YELLOW}NOTE: Langfuse API keys are placeholder values.${NC}"
        echo "  Visit http://localhost:3000, create an account + project,"
        echo "  then update LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env"
    fi
fi
