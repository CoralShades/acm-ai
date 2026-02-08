#!/usr/bin/env bash

# ACM-AI - Stop Ollama (WSL/Linux)
# Usage: ./stop-ollama.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  ACM-AI - Stopping Ollama"
echo "========================================"
echo ""

echo "Stopping Ollama container..."
docker stop acm-ai-ollama 2>/dev/null || true
docker rm acm-ai-ollama 2>/dev/null || true

echo ""
echo "Ollama stopped."
echo ""
echo "Note: Model data is preserved in Docker volume 'acm-ai-ollama-data'"
echo "To remove models: docker volume rm acm-ai-ollama-data"
echo ""
