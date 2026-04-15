#!/bin/bash
# ACM-AI RunPod RTX 5090 Health Check
# Enhanced verification: GPU, CUDA, Docker/Langfuse, native services, tunnel, models
# Usage: bash /workspace/acm-ai/scripts/runpod/health-check-5090.sh
set -uo pipefail

REPO_DIR="${REPO_DIR:-/workspace/acm-ai}"
ENV_FILE="$REPO_DIR/.env"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH"

PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check() {
    local name="$1"
    local cmd="$2"
    local result
    if result=$(eval "$cmd" 2>&1); then
        echo -e "  ${GREEN}[PASS]${NC} $name"
        ((PASS++))
    else
        echo -e "  ${RED}[FAIL]${NC} $name"
        [[ -n "$result" ]] && echo "         $result"
        ((FAIL++))
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"
    local result
    if result=$(eval "$cmd" 2>&1); then
        echo -e "  ${GREEN}[PASS]${NC} $name"
        ((PASS++))
    else
        echo -e "  ${YELLOW}[WARN]${NC} $name (optional)"
        ((WARN++))
    fi
}

echo "========================================"
echo "  ACM-AI RTX 5090 Health Check"
echo "========================================"
echo ""

# ── GPU & CUDA ───────────────────────
echo "--- GPU & CUDA ---"
check "NVIDIA GPU detected" "nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>/dev/null | head -1"
if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    VRAM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
    VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    CUDA_DRV=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1)
    echo -e "  ${CYAN}GPU:${NC} $GPU_NAME | VRAM: ${VRAM_USED}/${VRAM_TOTAL} MiB | Driver: $CUDA_DRV"
fi

# PyTorch CUDA check
if [[ -d "$REPO_DIR" ]]; then
    check "PyTorch CUDA available" \
        "cd $REPO_DIR && uv run python -c \"import torch; assert torch.cuda.is_available(), 'CUDA not available'; print(f'PyTorch {torch.__version__}, CUDA {torch.version.cuda}, Device: {torch.cuda.get_device_name()}')\""
    warn_check "Docling import" \
        "cd $REPO_DIR && uv run python -c \"from docling.document_converter import DocumentConverter; print('Docling OK')\""
fi

# ── SurrealDB Version Gate ───────────
echo ""
echo "--- SurrealDB Version ---"
if command -v surreal &>/dev/null; then
    SURREAL_VER=$(surreal version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
    if [[ "$SURREAL_VER" == "2.2.1" ]]; then
        echo -e "  ${GREEN}[PASS]${NC} SurrealDB v${SURREAL_VER} (exact pinned version)"
        ((PASS++))
    elif [[ "$SURREAL_VER" == 2.2.* ]]; then
        echo -e "  ${YELLOW}[WARN]${NC} SurrealDB v${SURREAL_VER} — expected v2.2.1 exactly"
        ((WARN++))
    elif [[ "$SURREAL_VER" == 2.[3-9].* || "$SURREAL_VER" == 2.[0-9][0-9].* || "$SURREAL_VER" == 3.* ]]; then
        echo -e "  ${RED}[FAIL]${NC} SurrealDB v${SURREAL_VER} — v2.6.3+ breaks Python SDK 1.0.8 CBOR compat"
        ((FAIL++))
    else
        echo -e "  ${RED}[FAIL]${NC} SurrealDB version unknown: $SURREAL_VER"
        ((FAIL++))
    fi
else
    echo -e "  ${RED}[FAIL]${NC} SurrealDB binary not found"
    ((FAIL++))
fi

# ── Service Processes ─────────────────
echo ""
echo "--- Native Service Processes ---"
check "SurrealDB process" "pgrep -f 'surreal start' > /dev/null"
check "Ollama process" "pgrep -f 'ollama serve' > /dev/null"
check "API process (uvicorn)" "pgrep -f 'run_api.py' > /dev/null"
check "Worker process" "pgrep -f 'run_worker.py' > /dev/null"
warn_check "Frontend process (node)" "pgrep -f 'next.*start' > /dev/null || pgrep -f 'next.*dev' > /dev/null"

# ── Service Endpoints ─────────────────
echo ""
echo "--- Service Endpoints ---"
check "SurrealDB (port 8000)" "curl -sf http://localhost:8000/health -o /dev/null"
check "Ollama (port 11434)" "curl -sf http://localhost:11434/api/tags -o /dev/null"
check "API (port 5055)" "curl -sf http://localhost:5055/health -o /dev/null"
warn_check "Frontend (port 8502)" "curl -sf http://localhost:8502 -o /dev/null"

# ── Docker & Langfuse ─────────────────
echo ""
echo "--- Docker & Langfuse ---"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    echo -e "  ${GREEN}[PASS]${NC} Docker daemon running"
    ((PASS++))

    # Check Langfuse containers
    LF_CONTAINERS=("acm-ai-langfuse-postgres" "acm-ai-langfuse-clickhouse" "acm-ai-langfuse-redis" "acm-ai-langfuse-minio" "acm-ai-langfuse-worker" "acm-ai-langfuse")
    LF_RUNNING=0
    LF_TOTAL=${#LF_CONTAINERS[@]}

    for cname in "${LF_CONTAINERS[@]}"; do
        status=$(docker inspect -f '{{.State.Status}}' "$cname" 2>/dev/null || echo "missing")
        if [[ "$status" == "running" ]]; then
            ((LF_RUNNING++))
        fi
    done

    if [[ "$LF_RUNNING" -eq "$LF_TOTAL" ]]; then
        echo -e "  ${GREEN}[PASS]${NC} All $LF_TOTAL Langfuse containers running"
        ((PASS++))
    elif [[ "$LF_RUNNING" -gt 0 ]]; then
        echo -e "  ${YELLOW}[WARN]${NC} $LF_RUNNING/$LF_TOTAL Langfuse containers running"
        ((WARN++))
    else
        echo -e "  ${RED}[FAIL]${NC} No Langfuse containers running"
        ((FAIL++))
    fi

    # Langfuse health endpoint
    warn_check "Langfuse health (port 3000)" \
        "curl -sf http://localhost:3000/api/public/health -o /dev/null"
else
    echo -e "  ${YELLOW}[WARN]${NC} Docker not available — Langfuse disabled"
    ((WARN++))
fi

# ── API Connectivity ─────────────────
echo ""
echo "--- API Connectivity ---"
check "API can reach SurrealDB" "curl -sf http://localhost:5055/health -o /dev/null"
warn_check "API /health/ready" "curl -sf http://localhost:5055/health/ready -o /dev/null"

# ── CORS Configuration ───────────────
echo ""
echo "--- CORS Configuration ---"
if [[ -f "$ENV_FILE" ]]; then
    CORS=$(grep '^CORS_ALLOWED_ORIGINS=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
    if [[ -n "$CORS" ]]; then
        echo -e "  ${GREEN}[PASS]${NC} CORS_ALLOWED_ORIGINS is set"
        ((PASS++))
        for domain in "acm.silvatron.au" "acmapi.silvatron.au"; do
            if echo "$CORS" | grep -q "$domain"; then
                echo -e "  ${GREEN}[PASS]${NC} $domain in CORS"
                ((PASS++))
            else
                echo -e "  ${YELLOW}[WARN]${NC} $domain not in CORS"
                ((WARN++))
            fi
        done
    else
        echo -e "  ${RED}[FAIL]${NC} CORS_ALLOWED_ORIGINS not set"
        ((FAIL++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} .env file not found"
    ((WARN++))
fi

# ── Cloudflare Tunnel ────────────────
echo ""
echo "--- Cloudflare Tunnel ---"
if tmux has-session -t tunnel 2>/dev/null; then
    echo -e "  ${GREEN}[PASS]${NC} Tunnel tmux session running"
    ((PASS++))
    warn_check "API via tunnel (acmapi.silvatron.au)" \
        "curl -sf --max-time 10 https://acmapi.silvatron.au/health -o /dev/null"
    warn_check "Frontend via tunnel (acm.silvatron.au)" \
        "curl -sf --max-time 10 -o /dev/null -w '%{http_code}' https://acm.silvatron.au/ | grep -q 200"
elif pgrep -f 'cloudflared tunnel' > /dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} cloudflared process running (not via tmux)"
    ((PASS++))
else
    echo -e "  ${YELLOW}[WARN]${NC} Tunnel not running"
    ((WARN++))
fi

# ── Ollama Models ─────────────────────
echo ""
echo "--- Ollama Models ---"
LOADED_MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null \
    | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null \
    || echo "")

EXPECTED_MODELS=("gemma4:e4b" "mxbai-embed-large" "gemma4:26b" "gemma4:latest" "gemma4:31b" "phi4:14b" "llama3.1:8b")

if [ -n "$LOADED_MODELS" ]; then
    MODEL_COUNT=$(echo "$LOADED_MODELS" | wc -l)
    echo "  Loaded models ($MODEL_COUNT):"
    echo "$LOADED_MODELS" | while read -r m; do echo "    - $m"; done

    MISSING=()
    for expected in "${EXPECTED_MODELS[@]}"; do
        if ! echo "$LOADED_MODELS" | grep -qF "$expected"; then
            MISSING+=("$expected")
        fi
    done

    if [[ ${#MISSING[@]} -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} All expected models present"
        ((PASS++))
    else
        echo -e "  ${YELLOW}[WARN]${NC} Missing models (${#MISSING[@]}):"
        for m in "${MISSING[@]}"; do
            echo -e "    ${YELLOW}-${NC} $m"
        done
        ((WARN++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} No models loaded (run: bash scripts/runpod/pull-models.sh)"
    ((WARN++))
fi

# ── tmux Sessions ─────────────────────
echo ""
echo "--- tmux Sessions ---"
EXPECTED_SESSIONS=("surrealdb" "ollama" "api" "worker" "frontend" "tunnel")
SESSIONS=$(tmux list-sessions -F '#{session_name}' 2>/dev/null || echo "")
if [ -n "$SESSIONS" ]; then
    echo "  Active sessions:"
    tmux list-sessions 2>/dev/null | while read -r s; do echo "    $s"; done
    for es in "${EXPECTED_SESSIONS[@]}"; do
        if echo "$SESSIONS" | grep -q "^${es}$"; then
            ((PASS++))
        else
            echo -e "  ${YELLOW}[WARN]${NC} Missing session: $es"
            ((WARN++))
        fi
    done
else
    echo -e "  ${RED}[FAIL]${NC} No tmux sessions running"
    ((FAIL++))
fi

# ── Disk & Memory ─────────────────────
echo ""
echo "--- Resources ---"
if df -h /workspace > /dev/null 2>&1; then
    USAGE=$(df -h /workspace | tail -1 | awk '{print $5}')
    AVAIL=$(df -h /workspace | tail -1 | awk '{print $4}')
    USAGE_PCT=${USAGE/\%/}
    if [[ "$USAGE_PCT" -gt 85 ]]; then
        echo -e "  ${RED}[FAIL]${NC} /workspace at ${USAGE} (${AVAIL} free) — consider cleanup"
        ((FAIL++))
    elif [[ "$USAGE_PCT" -gt 70 ]]; then
        echo -e "  ${YELLOW}[WARN]${NC} /workspace at ${USAGE} (${AVAIL} free)"
        ((WARN++))
    else
        echo -e "  ${GREEN}[PASS]${NC} /workspace at ${USAGE} (${AVAIL} free)"
        ((PASS++))
    fi
fi
# RAM
RAM_TOTAL=$(free -h | awk '/Mem:/{print $2}')
RAM_USED=$(free -h | awk '/Mem:/{print $3}')
RAM_AVAIL=$(free -h | awk '/Mem:/{print $7}')
echo -e "  ${CYAN}RAM:${NC} ${RAM_USED} used / ${RAM_TOTAL} total (${RAM_AVAIL} available)"

# ── Summary ───────────────────────────
echo ""
echo "========================================"
echo -e "  Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$WARN warnings${NC}"
echo "========================================"
if [ $FAIL -eq 0 ]; then
    echo -e "  Status: ${GREEN}HEALTHY${NC}"
else
    echo -e "  Status: ${RED}UNHEALTHY${NC} — check failures above"
fi
exit $FAIL
