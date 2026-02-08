#!/usr/bin/env bash

# ACM-AI - Kill all processes (works without pkill)
# Usage: ./kill-all.sh

echo "🛑 Killing all ACM-AI processes..."

# Kill npm/node processes
ps -ef | grep -E "npm run dev|next dev|node" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null

# Kill Python processes (API and Worker)
ps -ef | grep -E "run_api.py|surreal-commands-worker|uvicorn.*api.main" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null

# Stop Docker containers
docker compose down 2>/dev/null

# Clean up PID files
rm -f /tmp/acm-ai-*.pid 2>/dev/null

echo "✅ All processes killed!"
echo ""
echo "Run ./start-all-tmux.sh to restart services"
