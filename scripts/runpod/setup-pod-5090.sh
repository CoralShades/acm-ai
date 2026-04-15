#!/bin/bash
# ACM-AI RunPod RTX 5090 Bootstrap Script
# All-native services + Docker for Langfuse observability
#
# Usage:
#   bash setup-pod-5090.sh              # Full bootstrap (phases 1-10)
#   bash setup-pod-5090.sh --phase N    # Run single phase
#   bash setup-pod-5090.sh --from N     # Run from phase N onwards
#   bash setup-pod-5090.sh --help       # Show usage
#
# Phases:
#   1:  System deps (apt: tmux, htop, jq, curl)
#   2:  Install tools (uv, Node.js 22, SurrealDB v2.2.1, Ollama, cloudflared, Claude Code CLI)
#   3:  Clone/update repo (SSH deploy key, main branch)
#   4:  Environment setup (.env, data directories, env var injection)
#   5:  Python dependencies (uv sync + CUDA smoke test + Docling import)
#   6:  Frontend dependencies (npm install + npm run build)
#   7:  Start Langfuse Docker stack
#   8:  Start native services (SurrealDB, Ollama, API, Worker, Frontend, Tunnel)
#   9:  Pull Ollama models (sequential, graceful failures)
#   10: Health check + summary
set -euo pipefail

# ────────────────────────────────────────
# Configuration
# ────────────────────────────────────────
WORKSPACE="${WORKSPACE:-/workspace}"
REPO_DIR="$WORKSPACE/acm-ai"
DATA_DIR="$WORKSPACE/data"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SURREALDB_VERSION="v2.2.1"
NODE_MAJOR=22
GIT_BRANCH="main"
GIT_REPO="git@github.com:CoralShades/acm-ai.git"
DEPLOY_KEY="${DEPLOY_KEY:-/root/.ssh/acm-ai-deploy}"
TOTAL_PHASES=10

# Ollama models to pull (order: most critical first)
OLLAMA_MODELS=(
    "mxbai-embed-large"     # Embedding — small, needed first
    "gemma4:e4b"            # ACM per-row extraction — fast, small
    "gemma4:latest"         # Default chat
    "gemma4:26b"            # Default extraction + tools
    "gemma4:31b"            # Large context
    "phi4:14b"              # Fallback
    "llama3.1:8b"           # Legacy fallback
)

# ────────────────────────────────────────
# Helpers
# ────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$1/$TOTAL_PHASES]${NC} $2"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

wait_for_service() {
    local name="$1" url="$2" max_attempts="${3:-30}" interval="${4:-2}"
    echo -n "  Waiting for $name"
    for i in $(seq 1 "$max_attempts"); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC} (attempt $i)"
            return 0
        fi
        echo -n "."
        sleep "$interval"
    done
    echo -e " ${RED}TIMEOUT${NC}"
    fail "$name did not become ready after $((max_attempts * interval))s"
    return 1
}

usage() {
    echo "ACM-AI RunPod RTX 5090 Bootstrap"
    echo ""
    echo "Usage:"
    echo "  $0              Full bootstrap (phases 1-$TOTAL_PHASES)"
    echo "  $0 --phase N    Run only phase N"
    echo "  $0 --from N     Run from phase N onwards"
    echo "  $0 --help       Show this help"
    echo ""
    echo "Phases:"
    echo "  1   System dependencies (apt packages)"
    echo "  2   Install tools (uv, Node.js 22, SurrealDB v2.2.1, Ollama, cloudflared, Claude Code)"
    echo "  3   Clone/update repository (main branch)"
    echo "  4   Environment setup (.env + directories)"
    echo "  5   Python dependencies + CUDA verification"
    echo "  6   Frontend dependencies + production build"
    echo "  7   Langfuse Docker stack"
    echo "  8   Start native services"
    echo "  9   Pull Ollama models"
    echo "  10  Health check + summary"
    exit 0
}

# ────────────────────────────────────────
# Phase 1: System Dependencies
# ────────────────────────────────────────
phase_1() {
    log 1 "Installing system dependencies..."
    apt-get update -qq
    apt-get install -y -qq curl git tmux htop jq unzip wget lsof > /dev/null 2>&1
    ok "System deps installed"
}

# ────────────────────────────────────────
# Phase 2: Install Tools
# ────────────────────────────────────────
phase_2() {
    log 2 "Installing tools..."

    # --- uv ---
    if ! command -v uv &> /dev/null; then
        echo "  Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        grep -q 'local/bin' ~/.bashrc 2>/dev/null || \
            echo 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    ok "uv $(uv --version 2>/dev/null || echo 'unknown')"

    # --- Node.js 22 LTS ---
    if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d v) -lt $NODE_MAJOR ]]; then
        echo "  Installing Node.js ${NODE_MAJOR} LTS..."
        curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - > /dev/null 2>&1
        apt-get install -y -qq nodejs > /dev/null 2>&1
    fi
    ok "Node.js $(node -v), npm $(npm -v)"

    # --- SurrealDB v2.2.1 (CRITICAL: pinned version) ---
    local current_surreal=""
    if command -v surreal &> /dev/null; then
        current_surreal=$(surreal version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "")
    fi
    local target_surreal="${SURREALDB_VERSION#v}"
    if [[ "$current_surreal" != "$target_surreal" ]]; then
        echo "  Installing SurrealDB ${SURREALDB_VERSION} (pinned — v2.6.3+ breaks SDK)..."
        curl -sSf https://install.surrealdb.com | sh -s -- --version "${SURREALDB_VERSION}" > /dev/null 2>&1
        # Verify
        local installed_ver
        installed_ver=$(surreal version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "")
        if [[ "$installed_ver" != "$target_surreal" ]]; then
            fail "SurrealDB version mismatch: got $installed_ver, expected $target_surreal"
            echo "  Attempting direct binary download..."
            local arch="linux-amd64"
            curl -sL "https://github.com/surrealdb/surrealdb/releases/download/${SURREALDB_VERSION}/surreal-${SURREALDB_VERSION}.${arch}.tgz" \
                | tar xz -C /usr/local/bin/
        fi
    fi
    ok "SurrealDB $(surreal version 2>/dev/null || echo 'unknown')"

    # --- Ollama ---
    if ! command -v ollama &> /dev/null; then
        echo "  Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
    fi
    ok "Ollama $(ollama --version 2>/dev/null || echo 'unknown')"

    # --- cloudflared ---
    if ! command -v cloudflared &> /dev/null; then
        echo "  Installing cloudflared..."
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
            -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
    fi
    ok "cloudflared $(cloudflared --version 2>/dev/null | head -1 || echo 'unknown')"

    # --- Docker daemon check ---
    if command -v docker &>/dev/null; then
        if ! docker info &>/dev/null 2>&1; then
            echo "  Starting Docker daemon..."
            dockerd &>/dev/null &
            sleep 3
        fi
        if docker info &>/dev/null 2>&1; then
            ok "Docker daemon running"
        else
            warn "Docker daemon failed to start — Langfuse will be unavailable"
        fi
    else
        warn "Docker not installed — Langfuse will be unavailable"
    fi

    # --- Claude Code CLI ---
    if ! command -v claude &> /dev/null; then
        echo "  Installing Claude Code CLI..."
        # Try npm global install (most reliable on RunPod)
        npm install -g @anthropic-ai/claude-code 2>/dev/null || \
            warn "Claude Code CLI install failed — install manually later"
    fi
    if command -v claude &> /dev/null; then
        ok "Claude Code CLI installed"
    fi
}

# ────────────────────────────────────────
# Phase 3: Clone/Update Repository
# ────────────────────────────────────────
phase_3() {
    log 3 "Setting up repository..."

    # Configure SSH deploy key
    if [[ -f "$DEPLOY_KEY" ]]; then
        chmod 600 "$DEPLOY_KEY"
        export GIT_SSH_COMMAND="ssh -i $DEPLOY_KEY -o StrictHostKeyChecking=no"
        ok "SSH deploy key configured at $DEPLOY_KEY"
    else
        warn "Deploy key not found at $DEPLOY_KEY — trying default SSH or HTTPS"
    fi

    if [ -d "$REPO_DIR/.git" ]; then
        echo "  Repo exists, pulling latest..."
        cd "$REPO_DIR"
        git fetch --all --prune
        git checkout "$GIT_BRANCH"
        git pull --ff-only origin "$GIT_BRANCH" || warn "Pull failed (maybe local changes?) — continuing"
    else
        echo "  Cloning repo..."
        if [[ -f "$DEPLOY_KEY" ]]; then
            git clone "$GIT_REPO" "$REPO_DIR"
        else
            # Fallback to HTTPS (requires PAT or public repo)
            git clone "https://github.com/CoralShades/acm-ai.git" "$REPO_DIR"
        fi
        cd "$REPO_DIR"
        git checkout "$GIT_BRANCH"
    fi
    ok "Repository at $REPO_DIR (branch: $(git rev-parse --abbrev-ref HEAD))"
}

# ────────────────────────────────────────
# Phase 4: Environment Setup
# ────────────────────────────────────────
phase_4() {
    log 4 "Setting up environment..."

    # Create data directories
    mkdir -p "$DATA_DIR"/{surrealdb,ollama,uploads}
    mkdir -p "$DATA_DIR"/langfuse/{postgres,clickhouse,clickhouse-logs,redis,minio}
    mkdir -p "$REPO_DIR/logs"
    ok "Data directories created"

    # Copy .env template
    if [ ! -f "$REPO_DIR/.env" ]; then
        cp "$REPO_DIR/scripts/runpod/.env.runpod" "$REPO_DIR/.env"
        ok "Copied .env.runpod → .env"
    else
        ok ".env already exists"
    fi

    # Inject RunPod environment variables into .env
    local env_file="$REPO_DIR/.env"

    # CF_TUNNEL_TOKEN from pod env var
    if [[ -n "${CF_TUNNEL_TOKEN:-}" ]]; then
        if grep -q '^CF_TUNNEL_TOKEN=' "$env_file" 2>/dev/null; then
            sed -i "s|^CF_TUNNEL_TOKEN=.*|CF_TUNNEL_TOKEN=$CF_TUNNEL_TOKEN|" "$env_file"
        else
            echo "CF_TUNNEL_TOKEN=$CF_TUNNEL_TOKEN" >> "$env_file"
        fi
        ok "CF_TUNNEL_TOKEN injected into .env"
    fi

    # ACM_ANTHROPIC_API_KEY from pod env var (last-resort fallback)
    if [[ -n "${ACM_ANTHROPIC_API_KEY:-}" ]]; then
        if grep -q '^ACM_ANTHROPIC_API_KEY=' "$env_file" 2>/dev/null; then
            sed -i "s|^ACM_ANTHROPIC_API_KEY=.*|ACM_ANTHROPIC_API_KEY=$ACM_ANTHROPIC_API_KEY|" "$env_file"
        else
            echo "ACM_ANTHROPIC_API_KEY=$ACM_ANTHROPIC_API_KEY" >> "$env_file"
        fi
        ok "ACM_ANTHROPIC_API_KEY injected into .env"
    fi

    # Validate critical env vars
    local missing=()
    source "$env_file" 2>/dev/null || true
    [[ -z "${SURREAL_URL:-}" ]] && missing+=("SURREAL_URL")
    [[ -z "${OLLAMA_API_BASE:-}" ]] && missing+=("OLLAMA_API_BASE")
    [[ -z "${CORS_ALLOWED_ORIGINS:-}" ]] && missing+=("CORS_ALLOWED_ORIGINS")

    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Missing env vars: ${missing[*]}"
    else
        ok "Critical env vars present"
    fi
}

# ────────────────────────────────────────
# Phase 5: Python Dependencies
# ────────────────────────────────────────
phase_5() {
    log 5 "Installing Python dependencies..."
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    cd "$REPO_DIR"

    echo "  Running uv sync..."
    uv sync --quiet
    ok "Python deps installed"

    # CRITICAL: uv sync pulls stable torch from PyPI (sm_50–sm_90 only).
    # This overwrites nightly cu128 which is required for RTX 5090 (sm_120).
    # All runtime commands MUST use .venv/bin/python (not uv run) to avoid
    # re-triggering uv sync. See start-services-5090.sh.
    #
    # RTX 5090 sm_120 guard: detect and auto-fix by installing stable cu128.
    echo "  Checking PyTorch sm_120 (Blackwell) support..."
    local torch_archs
    torch_archs=$("$REPO_DIR/.venv/bin/python" -c "
import torch
archs = torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else []
print(' '.join(archs))
" 2>/dev/null || echo "")

    if ! echo "$torch_archs" | grep -q "sm_120"; then
        warn "PyTorch missing sm_120 — reinstalling stable cu128..."
        "$REPO_DIR/.venv/bin/pip" install --force-reinstall \
            torch torchvision torchaudio \
            --index-url https://download.pytorch.org/whl/cu128 \
            2>&1 | tail -3
        ok "PyTorch stable cu128 installed"
    else
        ok "PyTorch already supports sm_120"
    fi

    # CUDA smoke test
    echo "  Verifying CUDA + PyTorch..."
    local cuda_result
    cuda_result=$("$REPO_DIR/.venv/bin/python" -c "
import torch
assert torch.cuda.is_available(), 'CUDA not available'
archs = torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else []
assert 'sm_120' in archs, f'sm_120 not in arch list: {archs}'
print(f'PyTorch {torch.__version__}, CUDA {torch.version.cuda}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Compute capability: {torch.cuda.get_device_capability(0)}')
print(f'Arch list includes sm_120: OK')
" 2>&1) || {
        fail "PyTorch CUDA check failed: $cuda_result"
        warn "RTX 5090 (Blackwell) needs PyTorch nightly with cu128"
        warn "Manual fix: .venv/bin/pip install --force-reinstall --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128"
        return 1
    }
    echo "  $cuda_result"
    ok "PyTorch CUDA verified (sm_120 OK)"

    # Docling import test
    echo "  Verifying Docling..."
    "$REPO_DIR/.venv/bin/python" -c "from docling.document_converter import DocumentConverter; print('Docling OK')" 2>&1 || {
        warn "Docling import failed — table extraction may not work"
    }
    ok "Docling verified"
}

# ────────────────────────────────────────
# Phase 6: Frontend Dependencies
# ────────────────────────────────────────
phase_6() {
    log 6 "Installing frontend dependencies + building..."

    cd "$REPO_DIR/frontend"
    echo "  Running npm install..."
    npm install --quiet 2>/dev/null
    ok "Frontend deps installed"

    echo "  Building frontend (production)..."
    if npm run build 2>&1 | tail -5; then
        ok "Frontend build complete"
    else
        warn "Frontend build failed — will use dev mode as fallback"
    fi
}

# ────────────────────────────────────────
# Phase 7: Start Langfuse Docker Stack
# ────────────────────────────────────────
phase_7() {
    log 7 "Starting Langfuse Docker stack..."

    if ! command -v docker &>/dev/null || ! docker info &>/dev/null 2>&1; then
        warn "Docker not available — skipping Langfuse"
        # Disable Langfuse in .env
        if [[ -f "$REPO_DIR/.env" ]]; then
            sed -i 's/^LANGFUSE_ENABLED=true/LANGFUSE_ENABLED=false/' "$REPO_DIR/.env"
        fi
        return 0
    fi

    # Fix ClickHouse volume permissions
    chown -R 101:101 "$DATA_DIR/langfuse/clickhouse" "$DATA_DIR/langfuse/clickhouse-logs" 2>/dev/null || true

    cd "$REPO_DIR/scripts/runpod"
    docker compose -f docker-compose.runpod.yml up -d 2>&1 | tail -5
    cd "$REPO_DIR"

    echo -n "  Waiting for Langfuse health"
    for i in $(seq 1 40); do
        if curl -sf http://localhost:3000/api/public/health > /dev/null 2>&1; then
            echo -e " ${GREEN}ready${NC} (${i}/40)"
            ok "Langfuse stack running"
            return 0
        fi
        echo -n "."
        sleep 3
    done
    echo ""
    warn "Langfuse slow to start — check: docker compose -f scripts/runpod/docker-compose.runpod.yml logs"
}

# ────────────────────────────────────────
# Phase 8: Start Native Services
# ────────────────────────────────────────
phase_8() {
    log 8 "Starting native services..."
    bash "$REPO_DIR/scripts/runpod/start-services-5090.sh"
    ok "Services started"
}

# ────────────────────────────────────────
# Phase 9: Pull Ollama Models
# ────────────────────────────────────────
phase_9() {
    log 9 "Pulling Ollama models..."

    if ! wait_for_service "Ollama" "http://localhost:11434/api/tags" 15 2; then
        fail "Ollama not ready — skipping model pulls"
        return 1
    fi

    # Check available disk
    local avail_gb
    avail_gb=$(df --output=avail -BG "$WORKSPACE" 2>/dev/null | tail -1 | tr -d 'G ' || echo "999")
    echo "  Available disk: ${avail_gb}GB"

    local pulled=0 skipped=0 failed=0

    for model in "${OLLAMA_MODELS[@]}"; do
        # Skip large optional models if disk is tight
        if [[ "$avail_gb" -lt 20 ]]; then
            case "$model" in
                gemma4:31b|gemma4:34b|phi4:14b)
                    warn "Skipping $model (< 20GB free)"
                    ((skipped++))
                    continue
                    ;;
            esac
        fi

        echo -e "  Pulling ${CYAN}$model${NC}..."
        if ollama pull "$model" 2>&1 | tail -2; then
            ok "$model pulled"
            ((pulled++))
        else
            warn "$model not found or pull failed — skipping"
            ((failed++))
        fi
    done

    echo "  Models: $pulled pulled, $skipped skipped, $failed failed"
    ok "Model pulls complete"
}

# ────────────────────────────────────────
# Phase 10: Health Check + Summary
# ────────────────────────────────────────
phase_10() {
    log 10 "Running health check..."
    echo ""
    bash "$REPO_DIR/scripts/runpod/health-check-5090.sh" || true

    echo ""
    echo -e "${GREEN}========================================"
    echo "  RTX 5090 Bootstrap Complete!"
    echo -e "========================================${NC}"
    echo ""
    echo "  External access:"
    echo "    API:       https://acmapi.silvatron.au"
    echo "    Frontend:  https://acm.silvatron.au"
    echo ""

    # RunPod proxy URLs
    if [[ -n "${RUNPOD_POD_ID:-}" ]]; then
        echo "  RunPod proxy URLs (fallback):"
        echo "    API:       https://${RUNPOD_POD_ID}-5055.proxy.runpod.net"
        echo "    Frontend:  https://${RUNPOD_POD_ID}-8502.proxy.runpod.net"
        echo "    Ollama:    https://${RUNPOD_POD_ID}-11434.proxy.runpod.net"
        echo "    Langfuse:  https://${RUNPOD_POD_ID}-3000.proxy.runpod.net"
        echo ""
    fi

    echo "  Quick commands:"
    echo "    tmux attach -t api         # API logs"
    echo "    tmux attach -t ollama      # Ollama logs"
    echo "    bash scripts/runpod/health-check-5090.sh  # Re-run health check"
    echo ""

    # Langfuse key warning
    if [[ -f "$REPO_DIR/.env" ]]; then
        local lf_key
        lf_key=$(grep '^LANGFUSE_SECRET_KEY=' "$REPO_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"')
        if [[ "$lf_key" == "sk-lf-CHANGE-ME" ]]; then
            echo -e "  ${YELLOW}ACTION REQUIRED: Langfuse API keys are placeholder values.${NC}"
            echo "  1. Visit http://localhost:3000 (or RunPod proxy)"
            echo "  2. Create an account and project"
            echo "  3. Copy the API keys"
            echo "  4. Update LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env"
            echo "  5. Restart the API: tmux send-keys -t api C-c && sleep 1 && tmux send-keys -t api 'cd $REPO_DIR && API_HOST=0.0.0.0 .venv/bin/python run_api.py' Enter"
            echo ""
        fi
    fi
}

# ────────────────────────────────────────
# Main
# ────────────────────────────────────────
main() {
    local single_phase="" from_phase=1

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --phase)
                single_phase="$2"; shift 2 ;;
            --from)
                from_phase="$2"; shift 2 ;;
            --help|-h)
                usage ;;
            *)
                echo "Unknown option: $1"; usage ;;
        esac
    done

    echo "========================================"
    echo "  ACM-AI RunPod RTX 5090 Bootstrap"
    echo "========================================"
    echo ""
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'detecting...')"
    echo "  VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null || echo 'detecting...')"
    echo "  Workspace: $WORKSPACE"
    echo ""

    if [[ -n "$single_phase" ]]; then
        echo "Running phase $single_phase only..."
        "phase_$single_phase"
    else
        for phase in $(seq "$from_phase" "$TOTAL_PHASES"); do
            "phase_$phase"
            echo ""
        done
    fi
}

main "$@"
