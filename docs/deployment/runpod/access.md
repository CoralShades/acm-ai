# Access & Terminals

How to access the RunPod pod — SSH, proxy URLs, tmux sessions, and remote command execution.

## SSH Access

### Connect

```bash
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@174.94.157.109 -p 31130
```

> **Note:** The IP and port may change after pod restarts. Always check first:
> ```bash
> runpodctl pod get 9eusawy77gd1d0
> # Look for ssh.ssh_command field
> ```

### SSH Key Location

| Platform | Private Key Path |
|----------|-----------------|
| Windows | `C:\Users\User\.runpod\ssh\RunPod-Key-Go` |
| Linux/macOS | `~/.runpod/ssh/RunPod-Key-Go` |

### Run a Remote Command (without interactive shell)

```bash
ssh -i ~/.runpod/ssh/RunPod-Key-Go -p 31130 root@174.94.157.109 \
  "curl -sf http://localhost:5055/health"
```

### Transfer Files

```bash
# Local → Pod
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  ./my-file.pdf root@174.94.157.109:/workspace/acm-ai/docs/samplePDF/

# Pod → Local
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  root@174.94.157.109:/workspace/acm-ai/logs/api.log ./

# Or use runpodctl send/receive (uses transfer codes, no SSH needed)
# On local machine:
runpodctl send my-file.pdf    # prints a code like "9-example-words"
# On the pod:
runpodctl receive 9-example-words
```

## Proxy URLs (External Browser Access)

RunPod provides HTTPS proxy URLs for every exposed port. Format:
```
https://<pod-id>-<port>.proxy.runpod.net
```

### Current URLs

| Service | URL |
|---------|-----|
| Frontend | `https://9eusawy77gd1d0-8502.proxy.runpod.net` |
| API | `https://9eusawy77gd1d0-5055.proxy.runpod.net` |
| API Docs (Swagger) | `https://9eusawy77gd1d0-5055.proxy.runpod.net/docs` |
| SurrealDB | `https://9eusawy77gd1d0-8000.proxy.runpod.net` |
| Ollama | `https://9eusawy77gd1d0-11434.proxy.runpod.net` |

> **Pod ID changes when you delete and recreate a pod.** After creating a new pod, update all proxy URLs with the new pod ID.

### Proxy Authentication

RunPod proxy URLs are public by default. Anyone with the URL can access your services. For security:
- Use RunPod's "Secure Cloud" option (adds IP restrictions)
- Or set `OPEN_NOTEBOOK_PASSWORD` in `.env` for frontend password protection
- Or add API key authentication to the FastAPI backend

### Using Proxy URLs from Local Machine

```bash
# Test API health remotely
curl https://9eusawy77gd1d0-5055.proxy.runpod.net/health

# Use the remote API from local code
export API_URL=https://9eusawy77gd1d0-5055.proxy.runpod.net
```

## tmux Terminal Sessions

All services run in named tmux sessions. This provides persistent terminals that survive SSH disconnects.

### View All Sessions

```bash
tmux list-sessions
# Output:
# api: 1 windows (created Mon Mar 16 02:16:34 2026)
# frontend: 1 windows (created Mon Mar 16 02:13:19 2026)
# ollama: 1 windows (created Mon Mar 16 02:13:09 2026)
# surrealdb: 1 windows (created Mon Mar 16 02:16:30 2026)
# worker: 1 windows (created Mon Mar 16 02:17:10 2026)
```

### Attach to a Session

```bash
tmux attach -t api         # View API logs in real-time
tmux attach -t worker      # View worker logs
tmux attach -t frontend    # View frontend logs
tmux attach -t ollama      # View Ollama logs
tmux attach -t surrealdb   # View SurrealDB logs
```

### Detach from a Session

Press `Ctrl+B` then `D` (release Ctrl+B first, then press D).

### tmux Cheat Sheet

| Action | Keys |
|--------|------|
| Detach | `Ctrl+B`, then `D` |
| Scroll up | `Ctrl+B`, then `[`, then arrow keys or Page Up |
| Exit scroll | `q` |
| Create new window | `Ctrl+B`, then `C` |
| Switch windows | `Ctrl+B`, then `N` (next) or `P` (previous) |
| Split horizontal | `Ctrl+B`, then `"` |
| Split vertical | `Ctrl+B`, then `%` |
| Kill session | `tmux kill-session -t <name>` |

### Create a Custom tmux Session

```bash
# Run a one-off command in a persistent session
tmux new-session -d -s my-task "cd /workspace/acm-ai && uv run pytest tests/ -x"

# Attach to see output
tmux attach -t my-task
```

## RunPod Web Terminal

You can also access the pod via the RunPod web console:

1. Go to [runpod.io/console/pods](https://runpod.io/console/pods)
2. Find your pod (`acm-ai-dev`)
3. Click "Connect"
4. Select "Terminal" for a browser-based shell

This is useful when SSH isn't available (firewall restrictions, etc.).

## Claude Code Remote Execution

From Claude Code on your local machine, you can run commands on the pod:

```bash
# Run a health check from Claude Code
ssh -i "/c/Users/User/.runpod/ssh/RunPod-Key-Go" -o StrictHostKeyChecking=no -p 31130 root@174.94.157.109 "bash /workspace/acm-ai/scripts/runpod/health-check.sh"

# Check GPU status
ssh -i "/c/Users/User/.runpod/ssh/RunPod-Key-Go" -o StrictHostKeyChecking=no -p 31130 root@174.94.157.109 "nvidia-smi"

# Pull a new Ollama model
ssh -i "/c/Users/User/.runpod/ssh/RunPod-Key-Go" -o StrictHostKeyChecking=no -p 31130 root@174.94.157.109 "ollama pull qwen2.5:32b"
```

## Port Reference

| Port | Service | Protocol | Proxy URL Pattern |
|------|---------|----------|-------------------|
| 22 | SSH | TCP | N/A (direct IP:port) |
| 5055 | FastAPI | HTTP | `https://<id>-5055.proxy.runpod.net` |
| 8000 | SurrealDB | HTTP/WS | `https://<id>-8000.proxy.runpod.net` |
| 8502 | Frontend | HTTP | `https://<id>-8502.proxy.runpod.net` |
| 11434 | Ollama | HTTP | `https://<id>-11434.proxy.runpod.net` |
| 3000 | Langfuse | HTTP | `https://<id>-3000.proxy.runpod.net` (not active) |

---

**Next:** [Optimization](optimization.md) — GPU memory, model selection, and cost management.
