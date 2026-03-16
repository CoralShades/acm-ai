#!/bin/bash
# ACM-AI RunPod Pod Bootstrap Script
# Comprehensive setup: from fresh pod to running services in one command.
#
# Usage:
#   bash /workspace/acm-ai/scripts/runpod/setup-pod.sh          # Full bootstrap
#   bash /workspace/acm-ai/scripts/runpod/setup-pod.sh --phase N # Run single phase
#   bash /workspace/acm-ai/scripts/runpod/setup-pod.sh --help    # Show usage
#
# Phases:
#   1: System deps (apt: tmux, htop, jq, curl)
#   2: Install tools (uv, Node.js 20, SurrealDB v2.2.1, Ollama)
#   3: Clone/update repo + checkout ACMV3
#   4: Copy .env template
#   5: Install dependencies (uv sync + npm install)
#   6: Start services (SurrealDB, Ollama, API, Worker, Frontend)
#   7: Pull Ollama models (parallel, config-driven)
#   8: Health check + print next steps
#
# IMPORTANT: Docker-in-Docker is NOT supported on RunPod community pods.
#            All services run natively in tmux sessions.
set -euo pipefail

# ────────────────────────────────────────
# Configuration
# ────────────────────────────────────────
WORKSPACE="/workspace"
REPO_DIR="$WORKSPACE/acm-ai"
DATA_DIR="$WORKSPACE/data"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SURREALDB_VERSION="v2.2.1"
NODE_MAJOR=20

# ────────────────────────────────────────
# Helpers
# ────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$1/8]${NC} $2"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

wait_for_service() {
    local name="$1" url="$2" max_attempts="${3:-30}" interval="${4:-2}"
    for i in $(seq 1 "$max_attempts"); do
        if curl -sf "$url" > /dev/null 2>&1; then
            ok "$name is ready (attempt $i)"
            return 0
        fi
        sleep "$interval"
    done
    fail "$name did not become ready after $((max_attempts * interval))s"
    return 1
}

usage() {
    echo "ACM-AI RunPod Pod Bootstrap"
    echo ""
    echo "Usage:"
    echo "  $0              Full bootstrap (phases 1-8)"
    echo "  $0 --phase N    Run only phase N (1-8)"
    echo "  $0 --from N     Run from phase N onwards"
    echo "  $0 --help       Show this help"
    echo ""
    echo "Phases:"
    echo "  1  System dependencies (apt packages)"
    echo "  2  Install tools (uv, Node.js, SurrealDB, Ollama)"
    echo "  3  Clone/update repository"
    echo "  4  Copy .env template"
    echo "  5  Install Python + frontend dependencies"
    echo "  6  Start all services"
    echo "  7  Pull Ollama models"
    echo "  8  Health check + next steps"
    exit 0
}

# ────────────────────────────────────────
# Phase 1: System Dependencies
# ────────────────────────────────────────
phase_1() {
    log 1 "Installing system dependencies..."
    apt-get update -qq
    apt-get install -y -qq curl git tmux htop jq unzip wget > /dev/null 2>&1
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
        export PATH="$HOME/.local/bin:$PATH"
        # Persist in .bashrc if not already there
        grep -q 'local/bin' ~/.bashrc 2>/dev/null || \
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
    ok "uv $(uv --version 2>/dev/null || echo 'unknown')"

    # --- Node.js ---
    if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d v) -lt $NODE_MAJOR ]]; then
        echo "  Installing Node.js ${NODE_MAJOR}..."
        curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - > /dev/null 2>&1
        apt-get install -y -qq nodejs > /dev/null 2>&1
    fi
    ok "Node.js $(node -v), npm $(npm -v)"

    # --- SurrealDB (pinned version, native binary) ---
    local current_surreal=""
    if command -v surreal &> /dev/null; then
        current_surreal=$(surreal version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "")
    fi
    local target_surreal="${SURREALDB_VERSION#v}"
    if [[ "$current_surreal" != "$target_surreal" ]]; then
        echo "  Installing SurrealDB ${SURREALDB_VERSION}..."
        curl -sSf https://install.surrealdb.com | sh -s -- --version "${SURREALDB_VERSION}" > /dev/null 2>&1
    fi
    ok "SurrealDB $(surreal version 2>/dev/null || echo 'unknown')"

    # --- Ollama (native binary, GPU passthrough) ---
    if ! command -v ollama &> /dev/null; then
        echo "  Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
    fi
    ok "Ollama $(ollama --version 2>/dev/null || echo 'unknown')"

    # --- cloudflared (Cloudflare Tunnel) ---
    if ! command -v cloudflared &> /dev/null; then
        echo "  Installing cloudflared..."
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
            -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
    fi
    ok "cloudflared $(cloudflared --version 2>/dev/null || echo 'unknown')"
}

# ────────────────────────────────────────
# Phase 3: Clone/Update Repository
# ────────────────────────────────────────
phase_3() {
    log 3 "Setting up repository..."
    if [ -d "$REPO_DIR/.git" ]; then
        echo "  Repo exists, pulling latest..."
        cd "$REPO_DIR"
        git fetch --all --prune
        git checkout ACMV3
        git pull --ff-only origin ACMV3 || warn "Pull failed (maybe local changes?) — continuing"
    else
        echo "  Cloning repo..."
        git clone https://github.com/CoralShades/acm-ai.git "$REPO_DIR"
        cd "$REPO_DIR"
        git checkout ACMV3
    fi
    ok "Repository at $REPO_DIR (branch: $(git rev-parse --abbrev-ref HEAD))"
}

# ────────────────────────────────────────
# Phase 4: Environment Setup
# ────────────────────────────────────────
phase_4() {
    log 4 "Setting up environment..."
    mkdir -p "$DATA_DIR"/{surrealdb,ollama}

    if [ ! -f "$REPO_DIR/.env" ]; then
        cp "$REPO_DIR/scripts/runpod/.env.runpod" "$REPO_DIR/.env"
        ok "Copied .env.runpod → .env"
        warn "Edit $REPO_DIR/.env to add your API keys!"
    else
        ok ".env already exists"
    fi

    # Validate critical env vars
    local missing=()
    source "$REPO_DIR/.env" 2>/dev/null || true
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
# Phase 5: Install Dependencies
# ────────────────────────────────────────
phase_5() {
    log 5 "Installing dependencies..."
    export PATH="$HOME/.local/bin:$PATH"

    # Python
    cd "$REPO_DIR"
    echo "  Installing Python dependencies..."
    uv sync --quiet
    ok "Python deps installed"

    # Frontend
    echo "  Installing frontend dependencies..."
    cd "$REPO_DIR/frontend"
    npm install --quiet 2>/dev/null
    ok "Frontend deps installed"
}

# ────────────────────────────────────────
# Phase 6: Start Services
# ────────────────────────────────────────
phase_6() {
    log 6 "Starting services..."
    bash "$REPO_DIR/scripts/runpod/start-services.sh"
    ok "Services started"
}

# ────────────────────────────────────────
# Phase 7: Pull Ollama Models
# ────────────────────────────────────────
phase_7() {
    log 7 "Pulling Ollama models..."

    # Wait for Ollama to be ready
    if ! wait_for_service "Ollama" "http://localhost:11434/api/tags" 15 2; then
        fail "Ollama not ready — skipping model pulls"
        return 1
    fi

    bash "$REPO_DIR/scripts/runpod/pull-models.sh"
    ok "Model pulls complete"
}

# ────────────────────────────────────────
# Phase 8: Health Check + Next Steps
# ────────────────────────────────────────
phase_8() {
    log 8 "Running health check..."
    echo ""
    bash "$REPO_DIR/scripts/runpod/health-check.sh" || true

    echo ""
    echo -e "${GREEN}========================================"
    echo "  Bootstrap Complete!"
    echo -e "========================================${NC}"
    echo ""
    echo "  Pod services are running. Next steps:"
    echo ""
    echo "  1. Set up Cloudflare tunnel (one-time):"
    echo "     cloudflared tunnel login"
    echo "     bash $REPO_DIR/scripts/runpod/setup-tunnel.sh"
    echo ""
    echo "  2. Start the tunnel:"
    echo "     bash $REPO_DIR/scripts/runpod/start-tunnel.sh"
    echo ""
    echo "  3. Verify the app:"
    echo "     curl https://api.acmv3.coralshades.ai/health"
    echo "     curl https://acmv3.coralshades.ai/"
    echo ""
    echo "  4. Edit .env if needed:"
    echo "     nano $REPO_DIR/.env"
    echo ""
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
    echo "  ACM-AI RunPod Pod Bootstrap"
    echo "========================================"
    echo ""

    if [[ -n "$single_phase" ]]; then
        echo "Running phase $single_phase only..."
        "phase_$single_phase"
    else
        for phase in $(seq "$from_phase" 8); do
            "phase_$phase"
            echo ""
        done
    fi
}

main "$@"
