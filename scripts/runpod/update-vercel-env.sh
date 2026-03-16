#!/bin/bash
# Set Vercel INTERNAL_API_URL to the stable local Docker API tunnel
# No pod-id needed — api.coralshades.ai is a stable Cloudflare tunnel URL.
# Usage: bash scripts/runpod/update-vercel-env.sh
set -euo pipefail

API_URL="https://api.coralshades.ai"

echo "Setting Vercel INTERNAL_API_URL → $API_URL"
cd "$(dirname "$0")/../../frontend"

vercel env rm INTERNAL_API_URL production --yes 2>/dev/null || true
echo "$API_URL" | vercel env add INTERNAL_API_URL production

echo "Done. Vercel frontend will proxy API calls to $API_URL"
echo "No pod-id needed — this is a stable Cloudflare tunnel URL."
