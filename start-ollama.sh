#!/usr/bin/env bash

# ACM-AI - Ollama Local AI Setup (WSL/Linux)
# Usage: ./start-ollama.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  ACM-AI - Ollama Local AI Setup"
echo "========================================"
echo ""

echo "Choose your Ollama configuration:"
echo ""
echo "  [1] CPU-only    (office laptops, VMs, no GPU)"
echo "  [2] NVIDIA GPU  (developer machines with GPU)"
echo "  [3] Skip        (use cloud AI providers only)"
echo ""

read -p "Enter choice (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "Starting Ollama (CPU-only mode)..."
        docker compose --profile ollama-cpu up -d
        ;;
    2)
        echo ""
        echo "Starting Ollama (GPU mode)..."
        docker compose --profile ollama-gpu up -d
        ;;
    3)
        echo ""
        echo "Skipping Ollama setup."
        echo "You can use cloud AI providers (OpenAI, Anthropic, etc.)"
        echo ""
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Waiting for Ollama to start..."
sleep 10

echo ""
echo "Checking Ollama health..."
if ! docker exec acm-ai-ollama curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is still starting, waiting longer..."
    sleep 15
fi

echo ""
echo "========================================"
echo "  Pull AI Models (Optional)"
echo "========================================"
echo ""
echo "Do you want to pull recommended models now?"
echo "  - qwen3 (language model, ~4GB)"
echo "  - mxbai-embed-large (embeddings, ~670MB)"
echo ""

read -p "Pull models? (y/n): " pullmodels

if [[ "$pullmodels" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Pulling qwen3 (this may take a few minutes)..."
    docker exec acm-ai-ollama ollama pull qwen3
    echo ""
    echo "Pulling mxbai-embed-large..."
    docker exec acm-ai-ollama ollama pull mxbai-embed-large
    echo ""
    echo "Models pulled successfully!"
fi

echo ""
echo "========================================"
echo "  Ollama Setup Complete!"
echo "========================================"
echo ""
echo "  Ollama URL: http://localhost:11434"
echo ""
echo "  Add this to your .env file:"
echo "  OLLAMA_API_BASE=http://ollama:11434"
echo ""
echo "  Then configure models in the app:"
echo "  - Language Model: qwen3"
echo "  - Embedding Model: mxbai-embed-large"
echo ""
