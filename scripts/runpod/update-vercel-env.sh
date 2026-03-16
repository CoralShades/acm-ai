#!/bin/bash
# Update Vercel env vars when RunPod pod ID changes
# Usage: bash scripts/runpod/update-vercel-env.sh <new-pod-id>
set -euo pipefail

POD_ID="${1:?Usage: $0 <pod-id>}"
RUNPOD_API_URL="https://${POD_ID}-5055.proxy.runpod.net"

echo "Updating Vercel INTERNAL_API_URL → $RUNPOD_API_URL"
cd "$(dirname "$0")/../../frontend"

vercel env rm INTERNAL_API_URL production --yes 2>/dev/null || true
echo "$RUNPOD_API_URL" | vercel env add INTERNAL_API_URL production

echo "Done. Changes take effect on next Vercel serverless invocation (no redeploy needed)."
echo ""
echo "API_URL and NEXT_PUBLIC_API_URL stay as https://demo.vaea.coralshades.ai (unchanged)."
