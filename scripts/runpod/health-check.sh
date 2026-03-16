#!/bin/bash
# ACM-AI RunPod Health Check
# Usage: bash /workspace/acm-ai/scripts/runpod/health-check.sh
set -uo pipefail

REPO_DIR="${REPO_DIR:-/workspace/acm-ai}"
ENV_FILE="$REPO_DIR/.env"

PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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
echo "  ACM-AI RunPod Health Check"
echo "========================================"
echo ""

# ── GPU ───────────────────────────────
echo "--- GPU ---"
check "NVIDIA GPU detected" "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | grep -i nvidia"

# ── Service Processes ─────────────────
echo ""
echo "--- Service Processes ---"
check "SurrealDB process" "pgrep -f 'surreal start' > /dev/null"
check "Ollama process" "pgrep -f 'ollama serve' > /dev/null"
check "API process (uvicorn)" "pgrep -f 'run_api.py' > /dev/null"
check "Worker process" "pgrep -f 'run_worker.py' > /dev/null"

# ── Service Endpoints ─────────────────
echo ""
echo "--- Service Endpoints ---"
check "SurrealDB (port 8000)" "curl -sf http://localhost:8000/health -o /dev/null"
check "Ollama (port 11434)" "curl -sf http://localhost:11434/api/tags -o /dev/null"
check "API (port 5055)" "curl -sf http://localhost:5055/health -o /dev/null"
warn_check "Frontend (port 8502)" "curl -sf http://localhost:8502 -o /dev/null"

# ── SurrealDB Version ────────────────
echo ""
echo "--- SurrealDB Version ---"
SURREAL_VER=$(surreal version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
if [[ "$SURREAL_VER" == 2.* ]]; then
    echo -e "  ${GREEN}[PASS]${NC} SurrealDB v${SURREAL_VER} (v2.x required)"
    ((PASS++))
else
    echo -e "  ${RED}[FAIL]${NC} SurrealDB v${SURREAL_VER} — v2.x required (v3 has incompatible migrations)"
    ((FAIL++))
fi

# ── API → SurrealDB Connectivity ─────
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
        # Check for Vercel domain
        if echo "$CORS" | grep -q "demo.vaea.coralshades.ai"; then
            echo -e "  ${GREEN}[PASS]${NC} Vercel domain in CORS origins"
            ((PASS++))
        else
            echo -e "  ${YELLOW}[WARN]${NC} demo.vaea.coralshades.ai not in CORS origins"
            ((WARN++))
        fi
        ((PASS++))
    else
        echo -e "  ${RED}[FAIL]${NC} CORS_ALLOWED_ORIGINS not set in .env"
        ((FAIL++))
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} .env file not found"
    ((WARN++))
fi

# ── Ollama Models ─────────────────────
echo ""
echo "--- Ollama Models ---"
LOADED_MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null \
    | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null \
    || echo "")

if [ -n "$LOADED_MODELS" ]; then
    echo "  Loaded models:"
    echo "$LOADED_MODELS" | while read -r m; do echo "    - $m"; done

    # Check that .env-referenced models are present
    if [[ -f "$ENV_FILE" ]]; then
        MISSING_MODELS=()
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
            if [[ "$key" =~ ^DEFAULT_.*_MODEL$ && "$value" =~ ^ollama/ ]]; then
                model="${value#ollama/}"
                if ! echo "$LOADED_MODELS" | grep -qF "$model"; then
                    MISSING_MODELS+=("$model")
                fi
            fi
            if [[ "$key" == "ACM_EXTRACTION_MODEL" && -n "$value" ]]; then
                if ! echo "$LOADED_MODELS" | grep -qF "$value"; then
                    MISSING_MODELS+=("$value")
                fi
            fi
        done < "$ENV_FILE"

        if [[ ${#MISSING_MODELS[@]} -gt 0 ]]; then
            echo -e "  ${YELLOW}[WARN]${NC} Missing models referenced in .env:"
            for m in "${MISSING_MODELS[@]}"; do
                echo -e "    ${YELLOW}⚠${NC} $m"
            done
            ((WARN++))
        else
            echo -e "  ${GREEN}[PASS]${NC} All .env-referenced models are loaded"
            ((PASS++))
        fi
    fi
else
    echo -e "  ${YELLOW}[WARN]${NC} No models loaded (run: bash scripts/runpod/pull-models.sh)"
    ((WARN++))
fi

# ── tmux Sessions ─────────────────────
echo ""
echo "--- tmux Sessions ---"
SESSIONS=$(tmux list-sessions 2>/dev/null || echo "")
if [ -n "$SESSIONS" ]; then
    echo "  Active sessions:"
    echo "$SESSIONS" | while read -r s; do echo "    - $s"; done
else
    echo -e "  ${YELLOW}[WARN]${NC} No tmux sessions running"
    ((WARN++))
fi

# ── Disk Usage ────────────────────────
echo ""
echo "--- Disk Usage ---"
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

# ── Summary ───────────────────────────
echo ""
echo "========================================"
echo -e "  Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$WARN warnings${NC}"
echo "========================================"
if [ $FAIL -eq 0 ]; then
    echo -e "  Status: ${GREEN}HEALTHY${NC}"
else
    echo -e "  Status: ${RED}UNHEALTHY${NC}"
fi
exit $FAIL
