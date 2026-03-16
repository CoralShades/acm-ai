# Troubleshooting

Common issues when running ACM-AI on RunPod and how to fix them.

## SSH Connection Issues

### "Permission denied (publickey,password)"

**Cause:** Pod was created before SSH key was registered with RunPod.

**Fix:**
```bash
# 1. Delete the pod
runpodctl pod delete <pod-id>

# 2. Ensure SSH key is registered
runpodctl ssh list-keys  # Should show your key

# 3. If no key, register one:
echo "y" | runpodctl ssh add-key

# 4. Create a new pod (key will be injected automatically)
```

### "Connection refused" or timeout

**Cause:** Pod is still starting, or IP/port changed after restart.

**Fix:**
```bash
# Get current SSH info
runpodctl pod get <pod-id>
# Use the new IP and port from ssh.ssh_command
```

### SSH works but drops frequently

**Cause:** Network instability or idle timeout.

**Fix:** Add keepalive to SSH config:
```bash
ssh -i ~/.runpod/ssh/RunPod-Key-Go \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=5 \
  -p <port> root@<ip>
```

Or add to `~/.ssh/config`:
```
Host runpod
    HostName <ip>
    Port <port>
    User root
    IdentityFile ~/.runpod/ssh/RunPod-Key-Go
    ServerAliveInterval 30
    ServerAliveCountMax 5
```

## API Startup Failures

### "Failed to run database migrations: FLEXIBLE must be specified after TYPE"

**Cause:** SurrealDB v3 nightly installed instead of v2.x.

**Fix:**
```bash
# Check version
surreal version  # If 3.x → wrong version

# Install v2
curl -sSf https://install.surrealdb.com | sh -s -- --version v2.2.1

# Clear incompatible data
rm -rf /workspace/data/surrealdb/*

# Restart SurrealDB and API
tmux kill-session -t surrealdb
tmux kill-session -t api
bash /workspace/acm-ai/scripts/runpod/start-services.sh
```

### "Connection refused" on port 5055

**Cause:** API crashed on startup (check logs) or SurrealDB isn't running.

**Fix:**
```bash
# Check API logs
tail -50 /workspace/acm-ai/logs/api.log

# Ensure SurrealDB is running first
curl -sf http://localhost:8000/health || echo "SurrealDB is down!"

# Restart API
tmux kill-session -t api
tmux new-session -d -s api -c /workspace/acm-ai \
  "API_HOST=0.0.0.0 API_RELOAD=false uv run python run_api.py 2>&1 | tee logs/api.log"
```

### API starts but health returns error

**Cause:** Missing `.env` variables or database connection issue.

**Fix:**
```bash
# Verify .env exists and has required vars
cat /workspace/acm-ai/.env | grep SURREAL
# Should show: SURREAL_URL=ws://localhost:8000/rpc

# Test SurrealDB connection
surreal sql --conn http://localhost:8000 --user root --pass root \
  --ns open_notebook --db development \
  "INFO FOR DB;"
```

## Ollama Issues

### "model not found" (404)

**Cause:** Model not pulled yet, or `OLLAMA_MODELS` env var not set.

**Fix:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.1:8b-instruct-q8_0

# Check OLLAMA_MODELS is set in tmux session
# Models should be at /workspace/data/ollama/
ls /workspace/data/ollama/
```

### Ollama slow or hanging

**Cause:** GPU memory full, model swapping.

**Fix:**
```bash
# Check VRAM usage
nvidia-smi

# Check loaded models
curl http://localhost:11434/api/ps

# Unload all models (frees VRAM)
curl -X DELETE http://localhost:11434/api/generate -d '{"model":"llama3.1:8b-instruct-q8_0","keep_alive":0}'

# Reduce concurrent models
export OLLAMA_MAX_LOADED_MODELS=1
# Restart Ollama session
```

### "could not connect to a running Ollama instance"

**Cause:** Ollama server not running.

**Fix:**
```bash
# Check if Ollama is running
tmux list-sessions | grep ollama

# If not running, start it:
tmux new-session -d -s ollama \
  "OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=/workspace/data/ollama ollama serve"

# Wait a few seconds, then verify:
curl http://localhost:11434/api/tags
```

## Docker Issues

### "iptables failed: Permission denied" when starting Docker

**Cause:** RunPod community pods don't support Docker-in-Docker (missing kernel capabilities).

**This is expected.** ACM-AI on RunPod uses native services, not Docker. The `docker-compose.runpod.yml` file is for reference only.

**Workaround for Langfuse:** Use Langfuse cloud (free tier) instead of self-hosted.

## Frontend Issues

### Frontend shows 404 on root URL

**Cause:** The root route (`/`) may not have a page component. The app's main pages are at specific routes.

**Fix:** Navigate directly to:
- `/notebooks` — Notebook list
- `/jobs` — Jobs dashboard
- `/source/<id>` — Source detail / ACM register

### Frontend accessible locally but not via proxy

**Cause:** Frontend is listening on `127.0.0.1` instead of `0.0.0.0`.

**Fix:** Ensure the `PORT` and `HOST` are set:
```bash
tmux kill-session -t frontend
tmux new-session -d -s frontend -c /workspace/acm-ai/frontend \
  "HOST=0.0.0.0 PORT=8502 npm run dev -- -p 8502"
```

## GPU Issues

### "No GPU detected" or nvidia-smi shows no GPU

**Cause:** Pod started without GPU (rare) or driver issue.

**Fix:**
```bash
# Check GPU
nvidia-smi

# If no output, check pod details
runpodctl pod get <pod-id>
# Verify gpuCount > 0 and machine.gpuId is correct

# If GPU is missing, restart the pod:
runpodctl pod stop <pod-id>
runpodctl pod start <pod-id>
```

### CUDA out of memory

**Cause:** Too many models loaded or context window too large.

**Fix:**
```bash
# Check VRAM
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# Unload models
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:32b","keep_alive":0}'

# Reduce context window in .env
OLLAMA_NUM_CTX=16384  # Reduce from 32768

# Limit loaded models
OLLAMA_MAX_LOADED_MODELS=1
```

## Volume / Disk Issues

### "No space left on device"

**Cause:** Container disk (50GB) or volume (75GB) is full.

**Fix:**
```bash
# Check disk usage
df -h

# Find large files
du -sh /workspace/data/*
du -sh /workspace/acm-ai/.venv/
du -sh /workspace/acm-ai/node_modules/ 2>/dev/null

# Clean up
ollama rm <unused-model>                    # Remove unused models
rm -rf /workspace/acm-ai/logs/*.log        # Clear logs
rm -rf /tmp/*                               # Clear temp files
pip cache purge                             # Clear pip cache
npm cache clean --force                     # Clear npm cache
```

### Data lost after pod restart

**Cause:** Data was stored outside `/workspace` (which is the only persistent volume).

**Prevention:** Always store data under `/workspace/data/`:
- SurrealDB: `/workspace/data/surrealdb/`
- Ollama models: `/workspace/data/ollama/`
- Backups: `/workspace/data/backups/`

## Diagnostic Commands

```bash
# Full system overview
echo "=== GPU ===" && nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
echo "=== Disk ===" && df -h /workspace
echo "=== Memory ===" && free -h
echo "=== Services ===" && tmux list-sessions
echo "=== SurrealDB ===" && curl -sf http://localhost:8000/health && echo " OK" || echo " FAIL"
echo "=== Ollama ===" && curl -sf http://localhost:11434/api/tags > /dev/null && echo "OK" || echo "FAIL"
echo "=== API ===" && curl -sf http://localhost:5055/health && echo " OK" || echo " FAIL"
echo "=== Frontend ===" && curl -sf http://localhost:8502 > /dev/null && echo "OK" || echo "FAIL"
echo "=== Models ===" && ollama list 2>/dev/null
```

---

**Back to:** [RunPod Overview](index.md)
