#!/bin/bash
# ACM-AI RunPod Pod Setup Script
# Run this ONCE after creating the pod to install all dependencies
# Usage: bash /workspace/acm-ai/scripts/runpod/setup-pod.sh
set -euo pipefail

echo "========================================"
echo "  ACM-AI RunPod Pod Setup"
echo "========================================"

WORKSPACE="/workspace"
REPO_DIR="$WORKSPACE/acm-ai"
DATA_DIR="$WORKSPACE/data"

# Create persistent data directories on network volume
echo "[1/8] Creating data directories..."
mkdir -p "$DATA_DIR"/{surrealdb,ollama,langfuse/{postgres,clickhouse,clickhouse-logs,redis,minio}}
echo "Done."

# Install system dependencies
echo "[2/8] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq curl git tmux htop jq unzip > /dev/null 2>&1
echo "Done."

# Install uv (Python package manager)
echo "[3/8] Installing uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi
echo "uv version: $(uv --version)"

# Install Node.js 20+ (if not present)
echo "[4/8] Installing Node.js..."
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d v) -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt-get install -y -qq nodejs > /dev/null 2>&1
fi
echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Install Docker Compose plugin (if not present)
echo "[5/8] Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
        -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
fi
echo "Docker Compose version: $(docker compose version --short)"

# Clone or update repo
echo "[6/8] Setting up repository..."
if [ -d "$REPO_DIR/.git" ]; then
    echo "Repo exists, pulling latest..."
    cd "$REPO_DIR" && git pull --ff-only
else
    echo "Cloning repo..."
    git clone https://github.com/CoralShades/acm-ai.git "$REPO_DIR"
    cd "$REPO_DIR"
    git checkout ACMV3
fi

# Copy RunPod env template if .env doesn't exist
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "Copying .env.runpod template to .env..."
    cp "$REPO_DIR/scripts/runpod/.env.runpod" "$REPO_DIR/.env"
    echo "IMPORTANT: Edit $REPO_DIR/.env to add your API keys!"
fi

# Install Python dependencies
echo "[7/8] Installing Python dependencies..."
cd "$REPO_DIR"
uv sync --quiet
echo "Python deps installed."

# Install frontend dependencies
echo "[8/8] Installing frontend dependencies..."
cd "$REPO_DIR/frontend"
npm install --quiet
echo "Frontend deps installed."

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env: nano $REPO_DIR/.env"
echo "  2. Start Docker services:"
echo "     cd $REPO_DIR/scripts/runpod"
echo "     docker compose -f docker-compose.runpod.yml up -d"
echo "  3. Pull Ollama models:"
echo "     docker exec acm-ai-ollama ollama pull llama3.1:8b-instruct-q8_0"
echo "     docker exec acm-ai-ollama ollama pull qwen2.5:7b"
echo "     docker exec acm-ai-ollama ollama pull qwen3:latest"
echo "     docker exec acm-ai-ollama ollama pull mxbai-embed-large"
echo "  4. Start app services:"
echo "     bash $REPO_DIR/scripts/runpod/start-services.sh"
echo "  5. Run health checks:"
echo "     bash $REPO_DIR/scripts/runpod/health-check.sh"
