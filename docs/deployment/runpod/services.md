# RunPod Services Configuration

All services run natively (no Docker) in tmux sessions. This gives Ollama direct GPU access without container overhead.

## Quick Start

```bash
# Start everything with one command:
bash /workspace/acm-ai/scripts/runpod/start-services.sh
```

This starts 5 tmux sessions: `surrealdb`, `ollama`, `api`, `worker`, `frontend`.

## Individual Service Configuration

### SurrealDB (Port 8000)

```bash
# Start
tmux new-session -d -s surrealdb \
  "surreal start --log info --user root --pass root --bind 0.0.0.0:8000 \
   surrealkv:///workspace/data/surrealdb/open_notebook.db \
   2>&1 | tee /workspace/acm-ai/logs/surrealdb.log"

# Verify
curl -sf http://localhost:8000/health  # → 200 OK

# Connect via CLI
surreal sql --conn http://localhost:8000 --user root --pass root --ns open_notebook --db development
```

**Data location:** `/workspace/data/surrealdb/` (persists across pod restarts)

**Version requirement:** v2.x only. v3 nightly uses incompatible `FLEXIBLE TYPE` syntax that breaks migrations.

### Ollama (Port 11434)

```bash
# Start with GPU and persistent model storage
tmux new-session -d -s ollama \
  "OLLAMA_HOST=0.0.0.0:11434 \
   OLLAMA_MODELS=/workspace/data/ollama \
   ollama serve \
   2>&1 | tee /workspace/acm-ai/logs/ollama.log"

# Verify
curl -sf http://localhost:11434/api/tags  # → lists models

# Pull models (run after Ollama is serving)
ollama pull llama3.1:8b-instruct-q8_0    # 8.5GB — primary extraction
ollama pull qwen2.5:7b                    # 4.7GB — extraction alternative
ollama pull qwen3:latest                  # 5.2GB — chat
ollama pull mxbai-embed-large             # 669MB — embeddings

# Optional larger models (RTX 5090 32GB can fit these)
ollama pull qwen2.5:32b                   # 19GB — large context
ollama pull qwen3:32b                     # 19GB — advanced chat
```

**Model storage:** `/workspace/data/ollama/` (persists across pod restarts)

**Environment variables:**
| Variable | Value | Purpose |
|----------|-------|---------|
| `OLLAMA_HOST` | `0.0.0.0:11434` | Listen on all interfaces (required for proxy access) |
| `OLLAMA_MODELS` | `/workspace/data/ollama` | Store models on persistent volume |
| `OLLAMA_NUM_PARALLEL` | `2` | Max concurrent requests (optional) |
| `OLLAMA_MAX_LOADED_MODELS` | `2` | Max models in VRAM simultaneously (optional) |

### FastAPI Backend (Port 5055)

```bash
# Start (wait for SurrealDB first!)
tmux new-session -d -s api -c /workspace/acm-ai \
  "export PATH=\"\$HOME/.local/bin:\$PATH\"; \
   API_HOST=0.0.0.0 API_RELOAD=false \
   uv run python run_api.py \
   2>&1 | tee logs/api.log"

# Verify
curl -sf http://localhost:5055/health  # → {"status":"healthy"}
```

**Key environment variables:**
| Variable | Value | Purpose |
|----------|-------|---------|
| `API_HOST` | `0.0.0.0` | Listen on all interfaces (required for proxy) |
| `API_RELOAD` | `false` | Disable hot reload (saves CPU) |
| `SURREAL_URL` | `ws://localhost:8000/rpc` | SurrealDB connection |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama connection |

**Startup order matters:** SurrealDB must be running before the API starts, because the API runs database migrations on startup.

### Background Worker

```bash
# Start (after API is ready)
tmux new-session -d -s worker -c /workspace/acm-ai \
  "export PATH=\"\$HOME/.local/bin:\$PATH\"; \
   uv run python run_worker.py --import-modules commands \
   2>&1 | tee logs/worker.log"
```

The worker has no HTTP port — it polls SurrealDB for pending commands and processes them.

**Important:** The worker must be restarted separately from the API to pick up code changes in `open_notebook/graphs/`.

### Next.js Frontend (Port 8502)

```bash
# Start
tmux new-session -d -s frontend -c /workspace/acm-ai/frontend \
  "PORT=8502 npm run dev -- -p 8502 \
   2>&1 | tee /workspace/acm-ai/logs/frontend.log"

# Verify
curl -sf http://localhost:8502  # → HTML response
```

## Service Startup Order

Services must start in this order (each depends on the previous):

```
1. SurrealDB (port 8000)     ← no dependencies
2. Ollama (port 11434)        ← no dependencies (can parallel with #1)
3. API (port 5055)            ← requires SurrealDB
4. Worker                     ← requires SurrealDB + API
5. Frontend (port 8502)       ← requires API (for /api/* proxy)
```

The `start-services.sh` script handles this order automatically with health-check waits between steps.

## Health Check

```bash
# Run the full health check script
bash /workspace/acm-ai/scripts/runpod/health-check.sh

# Or check individually
curl -sf http://localhost:8000/health      # SurrealDB
curl -sf http://localhost:11434/api/tags   # Ollama
curl -sf http://localhost:5055/health      # API
curl -sf http://localhost:8502             # Frontend
nvidia-smi                                 # GPU status
tmux list-sessions                         # All tmux sessions
```

## Logs

All services log to both the tmux pane and files:

| Service | Log File | tmux Session |
|---------|----------|-------------|
| SurrealDB | `/workspace/acm-ai/logs/surrealdb.log` | `tmux attach -t surrealdb` |
| Ollama | `/workspace/acm-ai/logs/ollama.log` | `tmux attach -t ollama` |
| API | `/workspace/acm-ai/logs/api.log` | `tmux attach -t api` |
| Worker | `/workspace/acm-ai/logs/worker.log` | `tmux attach -t worker` |
| Frontend | `/workspace/acm-ai/logs/frontend.log` | `tmux attach -t frontend` |

```bash
# View live logs
tmux attach -t api       # then Ctrl+B, D to detach

# View log files
tail -f /workspace/acm-ai/logs/api.log
tail -100 /workspace/acm-ai/logs/worker.log
```

## Stopping Services

```bash
# Stop individual service
tmux kill-session -t api

# Stop all services
tmux kill-server

# Restart a service (example: API)
tmux kill-session -t api
tmux new-session -d -s api -c /workspace/acm-ai \
  "API_HOST=0.0.0.0 API_RELOAD=false uv run python run_api.py 2>&1 | tee logs/api.log"
```

---

**Next:** [Access & Terminals](access.md) — SSH, proxy URLs, and remote access methods.
