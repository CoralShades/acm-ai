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
| Pod ID | `qpzht3hvrbg95w` |
| GPU | NVIDIA GeForce RTX 5090 (32GB VRAM), Driver 570.195.03 |
| RAM | 46GB (reported as 377GB by `free -h`) |
| vCPUs | 24 |
| Cost | $0.69/hr |
| Location | CA (Canada, Community Cloud) |
| Image | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (`runpod-torch-v280`) |
| Container Disk | 100GB (64% used) |
| Network Volume | `acm-ai-data` 150GB in US-IL-1 (exists but NOT attached — different datacenter) |

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
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@142.127.93.36 -p 11392

# Start all services (after pod restart)
bash /workspace/acm-ai/scripts/runpod/start-services-5090.sh

# Health check
bash /workspace/acm-ai/scripts/runpod/health-check-5090.sh

# Deploy from WSL (one-command)
bash /mnt/d/ailocal/acm-ai/scripts/runpod/deploy-5090.sh

# Service URLs (via RunPod proxy)
# Frontend:  https://qpzht3hvrbg95w-8502.proxy.runpod.net
# API:       https://qpzht3hvrbg95w-5055.proxy.runpod.net
# API Docs:  https://qpzht3hvrbg95w-5055.proxy.runpod.net/docs

# Service URLs (via Cloudflare Tunnel — DNS/TLS issue, currently not resolving)
# Frontend:  https://app.acmv3.coralshades.ai
# API:       https://api.acmv3.coralshades.ai

# Pod management (from local machine)
runpodctl pod list                    # List pods
runpodctl pod get qpzht3hvrbg95w     # Pod details
runpodctl pod stop qpzht3hvrbg95w    # Stop (saves money)
runpodctl pod start qpzht3hvrbg95w   # Resume
runpodctl pod delete qpzht3hvrbg95w  # Delete permanently
```

## Architecture

```
Local Machine                          RunPod Pod (RTX 5090)
┌──────────────┐                       ┌─────────────────────────────────┐
│ Claude Code  │───SSH (port 11392)───▶│ tmux sessions (6):              │
│ runpodctl    │                       │   surrealdb  → port 8000        │
│ RunPod MCP   │                       │   ollama     → port 11434 (GPU) │
│ Browser      │───HTTPS proxy───────▶│   api        → port 5055        │
│              │───CF Tunnel──────────▶│   worker     → (background)     │
│              │                       │   frontend   → port 8502 (prod) │
└──────────────┘                       │   tunnel     → Cloudflare       │
                                       │                                 │
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
| Frontend | `npm run dev` (port 8502/8503) | `npm run start` production build, port 8502 (tmux) |
| Langfuse | Docker Compose stack | Not available (community cloud has no Docker-in-Docker) |
| Cloudflare Tunnel | N/A | `cloudflared tunnel run` (tmux session) |
| GPU | RTX 4090 (24GB) | RTX 5090 (32GB) |

---

**Next:** [Initial Setup](setup.md) to create your first RunPod pod.
