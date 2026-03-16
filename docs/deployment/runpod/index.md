# RunPod GPU Cloud Deployment

Deploy ACM-AI on a RunPod GPU pod for high-performance extraction with cloud GPUs (RTX 5090, A100, H100, etc.).

## Why RunPod?

- **GPU access on demand** — RTX 5090 (32GB), A100 (80GB), H100 (80GB) at community pricing
- **Pay per hour** — No long-term commitment; stop the pod when not in use
- **Direct GPU access** — Ollama runs natively with full CUDA, no Docker GPU passthrough overhead
- **Persistent storage** — `/workspace` volume survives pod restarts
- **External access** — Every port gets an HTTPS proxy URL automatically

## Current Deployment

| Detail | Value |
|--------|-------|
| Pod ID | `9eusawy77gd1d0` |
| GPU | NVIDIA RTX 5090 (32GB VRAM) |
| RAM | 83GB |
| vCPUs | 21 |
| Cost | $0.69/hr |
| Location | Canada (community cloud) |
| Volume | 75GB at `/workspace` |

## Documentation

| Guide | Description |
|-------|-------------|
| [Initial Setup](setup.md) | Create pod, install dependencies, clone repo |
| [Services](services.md) | SurrealDB, Ollama, API, Worker, Frontend configuration |
| [Access & Terminals](access.md) | SSH, proxy URLs, tmux sessions, remote commands |
| [Optimization](optimization.md) | GPU memory, model selection, cost management, performance |
| [Maintenance](maintenance.md) | Updates, backups, pod lifecycle, model management |
| [Troubleshooting](troubleshooting.md) | Common issues, fixes, diagnostic commands |

## Quick Reference

```bash
# SSH into the pod
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@174.94.157.109 -p 31130

# Start all services (after pod restart)
bash /workspace/acm-ai/scripts/runpod/start-services.sh

# Health check
bash /workspace/acm-ai/scripts/runpod/health-check.sh

# Service URLs (via RunPod proxy)
# Frontend:  https://9eusawy77gd1d0-8502.proxy.runpod.net
# API:       https://9eusawy77gd1d0-5055.proxy.runpod.net
# API Docs:  https://9eusawy77gd1d0-5055.proxy.runpod.net/docs

# Pod management (from local machine)
runpodctl pod list                    # List pods
runpodctl pod get 9eusawy77gd1d0     # Pod details
runpodctl pod stop 9eusawy77gd1d0    # Stop (saves money)
runpodctl pod start 9eusawy77gd1d0   # Resume
runpodctl pod delete 9eusawy77gd1d0  # Delete permanently
```

## Architecture

```
Local Machine                          RunPod Pod (RTX 5090)
┌──────────────┐                       ┌─────────────────────────────────┐
│ Claude Code  │───SSH (port 31130)───▶│ tmux sessions:                  │
│ runpodctl    │                       │   surrealdb  → port 8000        │
│ RunPod MCP   │                       │   ollama     → port 11434 (GPU) │
│ Browser      │───HTTPS proxy───────▶│   api        → port 5055        │
│              │                       │   worker     → (background)     │
│              │                       │   frontend   → port 8502        │
└──────────────┘                       │                                 │
                                       │ /workspace/data/                │
                                       │   surrealdb/  (DB files)        │
                                       │   ollama/     (model weights)   │
                                       └─────────────────────────────────┘
```

## Service Stack Comparison

| Component | Local (Windows) | RunPod (Linux) |
|-----------|----------------|----------------|
| SurrealDB | Docker container | Native binary (v2.2.1) |
| Ollama | Host binary (localhost) | Native binary (direct GPU) |
| API | `uv run python run_api.py` | Same (tmux session) |
| Worker | `uv run python run_worker.py` | Same (tmux session) |
| Frontend | `npm run dev` (port 8502/8503) | Same, port 8502 (tmux) |
| Langfuse | Docker Compose stack | Not available (no Docker-in-Docker) |
| GPU | RTX 4090 (24GB) | RTX 5090 (32GB) |

---

**Next:** [Initial Setup](setup.md) to create your first RunPod pod.
