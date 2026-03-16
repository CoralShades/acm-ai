#!/bin/bash
# ACM-AI RunPod Health Check
# Usage: bash /workspace/acm-ai/scripts/runpod/health-check.sh
set -uo pipefail

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local cmd="$2"
    local result
    if result=$(eval "$cmd" 2>&1); then
        echo "  [PASS] $name"
        ((PASS++))
    else
        echo "  [FAIL] $name"
        echo "         $result"
        ((FAIL++))
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"
    local result
    if result=$(eval "$cmd" 2>&1); then
        echo "  [PASS] $name"
        ((PASS++))
    else
        echo "  [WARN] $name (optional)"
        ((WARN++))
    fi
}

echo "========================================"
echo "  ACM-AI RunPod Health Check"
echo "========================================"
echo ""

echo "--- GPU ---"
check "NVIDIA GPU detected" "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | grep -i nvidia"

echo ""
echo "--- Docker Services ---"
check "SurrealDB container" "docker ps --format '{{.Names}}' | grep acm-ai-db"
check "Ollama container" "docker ps --format '{{.Names}}' | grep acm-ai-ollama"
warn_check "Langfuse container" "docker ps --format '{{.Names}}' | grep acm-ai-langfuse$"

echo ""
echo "--- Service Endpoints ---"
check "SurrealDB (port 8000)" "curl -sf http://localhost:8000/health -o /dev/null"
check "Ollama (port 11434)" "curl -sf http://localhost:11434/api/tags -o /dev/null"
check "API (port 5055)" "curl -sf http://localhost:5055/health -o /dev/null"
warn_check "Frontend (port 8502)" "curl -sf http://localhost:8502 -o /dev/null"
warn_check "Langfuse (port 3000)" "curl -sf http://localhost:3000/api/public/health -o /dev/null"

echo ""
echo "--- Ollama Models ---"
MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null || echo "")
if [ -n "$MODELS" ]; then
    echo "  Loaded models:"
    echo "$MODELS" | while read -r m; do echo "    - $m"; done
else
    echo "  [WARN] No models loaded (run: docker exec acm-ai-ollama ollama pull <model>)"
    ((WARN++))
fi

echo ""
echo "--- tmux Sessions ---"
SESSIONS=$(tmux list-sessions 2>/dev/null || echo "none")
if [ "$SESSIONS" != "none" ]; then
    echo "  Active sessions:"
    echo "$SESSIONS" | while read -r s; do echo "    - $s"; done
else
    echo "  [WARN] No tmux sessions running"
    ((WARN++))
fi

echo ""
echo "========================================"
echo "  Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "========================================"
[ $FAIL -eq 0 ] && echo "  Status: HEALTHY" || echo "  Status: UNHEALTHY"
exit $FAIL
