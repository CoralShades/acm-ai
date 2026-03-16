#!/bin/bash
# Starts the Cloudflare tunnel in a tmux session
# Prerequisites: bash scripts/runpod/setup-tunnel.sh (one-time)
# Usage: bash /workspace/acm-ai/scripts/runpod/start-tunnel.sh
set -euo pipefail

REPO_DIR="${REPO_DIR:-/workspace/acm-ai}"
TUNNEL_NAME="acm-runpod"

# Kill existing tunnel session
tmux kill-session -t tunnel 2>/dev/null || true

mkdir -p "$REPO_DIR/logs"

tmux new-session -d -s tunnel \
    "cloudflared tunnel run $TUNNEL_NAME 2>&1 | tee $REPO_DIR/logs/tunnel.log"

sleep 2
if tmux has-session -t tunnel 2>/dev/null; then
    echo "Cloudflare tunnel started (tmux session: tunnel)"
    echo "  Frontend: https://acmv3.coralshades.ai"
    echo "  API:      https://api.acmv3.coralshades.ai"
    echo ""
    echo "  tmux attach -t tunnel   # View tunnel logs"
else
    echo "Tunnel failed to start — check: tmux attach -t tunnel"
    exit 1
fi
