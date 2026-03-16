#!/bin/bash
# Creates a Cloudflare tunnel and configures DNS for acmv3.coralshades.ai
# One-time setup — run this once per pod after `cloudflared tunnel login`.
#
# Prerequisites:
#   1. cloudflared installed (setup-pod.sh phase 2)
#   2. ~/.cloudflared/cert.pem exists (run: cloudflared tunnel login)
#
# Usage: bash /workspace/acm-ai/scripts/runpod/setup-tunnel.sh
set -euo pipefail

TUNNEL_NAME="acm-runpod"
FRONTEND_DOMAIN="acmv3.coralshades.ai"
API_DOMAIN="api.acmv3.coralshades.ai"
CONFIG_DIR="$HOME/.cloudflared"

# ── Prerequisites ────────────────────
if ! command -v cloudflared &> /dev/null; then
    echo "ERROR: cloudflared not installed."
    echo "Run: bash scripts/runpod/setup-pod.sh --phase 2"
    exit 1
fi

if [ ! -f "$CONFIG_DIR/cert.pem" ]; then
    echo "ERROR: No Cloudflare cert found at $CONFIG_DIR/cert.pem"
    echo "Run: cloudflared tunnel login"
    echo "Then re-run this script."
    exit 1
fi

# ── Create tunnel (idempotent) ───────
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "Tunnel '$TUNNEL_NAME' already exists"
else
    echo "Creating tunnel: $TUNNEL_NAME"
    cloudflared tunnel create "$TUNNEL_NAME"
fi

# Get tunnel UUID
TUNNEL_ID=$(cloudflared tunnel list -o json | python3 -c \
    "import sys,json; tunnels=json.load(sys.stdin); print([t['id'] for t in tunnels if t['name']=='$TUNNEL_NAME'][0])")

echo "Tunnel ID: $TUNNEL_ID"

# ── Create DNS routes (idempotent) ───
cloudflared tunnel route dns "$TUNNEL_NAME" "$FRONTEND_DOMAIN" 2>/dev/null || true
cloudflared tunnel route dns "$TUNNEL_NAME" "$API_DOMAIN" 2>/dev/null || true

# ── Write config file ───────────────
cat > "$CONFIG_DIR/config.yml" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/${TUNNEL_ID}.json

ingress:
  - hostname: $FRONTEND_DOMAIN
    service: http://localhost:8502
  - hostname: $API_DOMAIN
    service: http://localhost:5055
  - service: http_status:404
EOF

echo ""
echo "Tunnel '$TUNNEL_NAME' ($TUNNEL_ID) configured."
echo "DNS: $FRONTEND_DOMAIN → localhost:8502"
echo "DNS: $API_DOMAIN → localhost:5055"
echo "Config: $CONFIG_DIR/config.yml"
echo ""
echo "Start with: bash scripts/runpod/start-tunnel.sh"
