#!/bin/bash
# ACM-AI Ollama Model Puller
# Reads model names from .env and pulls them via Ollama API.
# Usage: bash /workspace/acm-ai/scripts/runpod/pull-models.sh
set -uo pipefail

REPO_DIR="${REPO_DIR:-/workspace/acm-ai}"
ENV_FILE="$REPO_DIR/.env"
OLLAMA_URL="${OLLAMA_API_BASE:-http://localhost:11434}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ────────────────────────────────────────
# Gather model list from .env
# ────────────────────────────────────────
declare -A MODELS_MAP  # associative array for dedup

if [[ -f "$ENV_FILE" ]]; then
    # Extract model names from DEFAULT_*_MODEL=ollama/<model> entries
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        # Match DEFAULT_*_MODEL=ollama/<model>
        if [[ "$key" =~ ^DEFAULT_.*_MODEL$ && "$value" =~ ^ollama/ ]]; then
            model="${value#ollama/}"
            MODELS_MAP["$model"]=1
        fi
        # Match ACM_EXTRACTION_MODEL=<model> (no ollama/ prefix)
        if [[ "$key" == "ACM_EXTRACTION_MODEL" && -n "$value" ]]; then
            MODELS_MAP["$value"]=1
        fi
    done < "$ENV_FILE"
else
    echo -e "${YELLOW}Warning: $ENV_FILE not found. Using hardcoded defaults.${NC}"
fi

# Always include extraction model as a fallback
MODELS_MAP["llama3.1:8b-instruct-q8_0"]=1

# Convert to array
MODELS=("${!MODELS_MAP[@]}")

echo "========================================"
echo "  ACM-AI Ollama Model Puller"
echo "========================================"
echo ""
echo "  Models to pull (${#MODELS[@]}):"
for m in "${MODELS[@]}"; do
    echo "    - $m"
done
echo ""

# ────────────────────────────────────────
# Check which models are already available
# ────────────────────────────────────────
EXISTING=$(curl -sf "$OLLAMA_URL/api/tags" 2>/dev/null \
    | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null \
    || echo "")

NEEDED=()
for m in "${MODELS[@]}"; do
    # Check if model name matches (with or without :latest tag)
    if echo "$EXISTING" | grep -qF "$m"; then
        echo -e "  ${GREEN}✓${NC} $m (already pulled)"
    else
        NEEDED+=("$m")
    fi
done

if [[ ${#NEEDED[@]} -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}All models already available!${NC}"
    exit 0
fi

echo ""
echo "  Pulling ${#NEEDED[@]} model(s)..."
echo ""

# ────────────────────────────────────────
# Pull models in parallel (background jobs)
# ────────────────────────────────────────
PIDS=()
for m in "${NEEDED[@]}"; do
    echo -e "  ${YELLOW}⏳${NC} Pulling $m ..."
    ollama pull "$m" > /dev/null 2>&1 &
    PIDS+=("$!:$m")
done

# Wait for all pulls and report results
FAILED=0
for entry in "${PIDS[@]}"; do
    pid="${entry%%:*}"
    model="${entry#*:}"
    if wait "$pid"; then
        echo -e "  ${GREEN}✓${NC} $model pulled successfully"
    else
        echo -e "  ${RED}✗${NC} $model pull FAILED"
        ((FAILED++))
    fi
done

echo ""
if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}All models pulled successfully!${NC}"
else
    echo -e "${RED}$FAILED model(s) failed to pull.${NC}"
    exit 1
fi
