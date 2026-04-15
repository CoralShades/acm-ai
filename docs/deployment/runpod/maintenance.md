# Maintenance

Pod lifecycle management, code updates, backups, model management, and routine operations.

## Pod Lifecycle

### Stop Pod (Saves Money)

```bash
# From local machine
runpodctl pod stop qpzht3hvrbg95w

# Billing stops immediately
# Container state is lost (tmux sessions, running processes)
# NOTE: No network volume attached — container disk (100GB) persists across stop/start
#       but is destroyed on pod deletion
```

### Start Pod (Resume)

```bash
# Resume the pod
runpodctl pod start qpzht3hvrbg95w

# Wait ~30 seconds for it to come up
# Then SSH in and restart services:
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<new-ip> -p <new-port>
bash /workspace/acm-ai/scripts/runpod/start-services-5090.sh
```

> **Important:** IP and SSH port change on every restart. Always check:
> ```bash
> runpodctl pod get qpzht3hvrbg95w
> ```

### Delete Pod (Permanent)

```bash
runpodctl pod delete qpzht3hvrbg95w
# WARNING: No network volume attached — ALL data is destroyed on deletion
# Ollama models, SurrealDB data, and repo will be lost
# Back up everything before deleting (see Database Backups below)
```

### Create New Pod (After Delete)

Follow the [Setup Guide](setup.md). Remember to:
1. Update pod ID in all documentation and scripts
2. Re-run `setup-pod-5090.sh` for dependency installation
3. Re-pull Ollama models
4. Restore any database backups

## Code Updates

### Pull Latest Code

```bash
# SSH into pod
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<ip> -p <port>

# Pull changes (deploy key is configured for git operations)
cd /workspace/acm-ai
git checkout main
git pull --ff-only

# Restart affected services
tmux kill-session -t api
tmux kill-session -t worker

# Re-sync Python deps (if pyproject.toml changed)
uv sync

# Re-install frontend deps (if package.json changed)
cd frontend && npm install && cd ..

# Restart services
bash scripts/runpod/start-services-5090.sh
```

### Push Local Changes -> Pod

```bash
# Option 1: Git (recommended — deploy key configured on pod)
# On local machine:
git add . && git commit -m "feat: my changes"
git push

# On pod:
cd /workspace/acm-ai && git pull

# Option 2: SCP (for quick file transfers)
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 11392 \
  ./open_notebook/graphs/acm_extraction.py \
  root@142.127.93.36:/workspace/acm-ai/open_notebook/graphs/

# Option 3: runpodctl send/receive
runpodctl send ./my-changes.tar.gz
# On pod: runpodctl receive <code>
```

## Database Backups

### Export SurrealDB Data

```bash
# On the pod
surreal export --conn http://localhost:8000 --user root --pass root \
  --ns open_notebook --db development \
  /workspace/data/backups/surreal-$(date +%Y%m%d).surql

# Transfer to local machine
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 11392 \
  root@142.127.93.36:/workspace/data/backups/*.surql ./
```

### Import SurrealDB Data

```bash
# Upload backup to pod
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 11392 \
  ./surreal-backup.surql root@142.127.93.36:/workspace/data/backups/

# On the pod
surreal import --conn http://localhost:8000 --user root --pass root \
  --ns open_notebook --db development \
  /workspace/data/backups/surreal-backup.surql
```

### Backup Volume Data

```bash
# Create a tarball of all persistent data
ssh -i ~/.runpod/ssh/RunPod-Key-Go -p 11392 root@142.127.93.36 \
  "cd /workspace && tar czf /tmp/acm-data-backup.tar.gz data/"

# Download to local machine
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 11392 \
  root@142.127.93.36:/tmp/acm-data-backup.tar.gz ./
```

> **Important:** No network volume is attached. All data lives on the 100GB container disk.
> Back up regularly — data is lost if the pod is deleted.

## Ollama Model Management

### List Models

```bash
ollama list
# NAME                         SIZE      MODIFIED
# gemma4:26b                   17 GB     ...
# gemma4:e4b                   9.6 GB    ...
# gemma4:latest                9.6 GB    ...
# mxbai-embed-large            669 MB    ...
```

### Pull New Models

```bash
ollama pull <model-name>

# Current gemma4 family models:
ollama pull gemma4:26b        # 17GB — extraction, tools, transformation
ollama pull gemma4:e4b        # 9.6GB — ACM per-row extraction
ollama pull gemma4:latest     # 9.6GB — chat (shared blob with e4b)
ollama pull gemma4:31b        # 19GB — large context
ollama pull mxbai-embed-large # 669MB — embeddings

# Optional fallbacks (100GB disk has ~37GB free):
# ollama pull phi4:14b        # 8GB
# ollama pull llama3.1:8b     # 5GB
```

### Remove Models (Free VRAM/Disk)

```bash
ollama rm <model-name>         # Remove from disk
```

### Check Loaded Models (in VRAM)

```bash
curl http://localhost:11434/api/ps
# Shows which models are currently loaded in GPU memory
```

### Update Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
# Then restart the Ollama tmux session
tmux kill-session -t ollama
tmux new-session -d -s ollama \
  "OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=/workspace/data/ollama ollama serve"
```

## Monitoring

### Real-Time GPU Monitoring

```bash
# Continuous GPU status (updates every 2s)
watch -n 2 nvidia-smi

# One-shot check
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu,power.draw --format=csv,noheader
```

### Service Status

```bash
# All services at once
bash /workspace/acm-ai/scripts/runpod/health-check-5090.sh

# Individual checks
curl -sf http://localhost:8000/health && echo OK    # SurrealDB
curl -sf http://localhost:11434/api/tags && echo OK  # Ollama
curl -sf http://localhost:5055/health && echo OK      # API
curl -sf http://localhost:8502 && echo OK              # Frontend
tmux list-sessions                                     # All sessions
```

### Disk Usage

```bash
# Container disk usage (no network volume)
df -h /workspace

# Ollama models size
du -sh /workspace/data/ollama/

# SurrealDB data size
du -sh /workspace/data/surrealdb/

# Repo size
du -sh /workspace/acm-ai/
```

### Cost Monitoring

```bash
# From local machine
runpodctl user                   # Current balance + spend rate
runpodctl billing pods           # Pod billing history
runpodctl billing serverless     # Serverless billing (if used)
```

## Routine Maintenance Checklist

### Weekly
- [ ] Check `runpodctl user` balance — top up if needed
- [ ] Stop the pod when not in use (`runpodctl pod stop qpzht3hvrbg95w`)
- [ ] Pull latest code (`git checkout main && git pull`)
- [ ] Check disk usage (`df -h /`) — 100GB disk, monitor if above 80%

### Monthly
- [ ] Update Ollama (`curl -fsSL https://ollama.com/install.sh | sh`)
- [ ] Update SurrealDB if new v2.x release available
- [ ] Export database backup
- [ ] Check disk usage — remove unused models if needed
- [ ] Remove old logs (`rm -rf /workspace/acm-ai/logs/*.log`)

### After Pod Recreation
- [ ] Update pod ID in documentation
- [ ] Configure deploy key for git operations
- [ ] Update proxy URLs
- [ ] Re-run `setup-pod-5090.sh`
- [ ] Re-pull Ollama models (gemma4 family + mxbai-embed-large)
- [ ] Import database backup
- [ ] Test all services with `health-check-5090.sh`

---

**Next:** [Troubleshooting](troubleshooting.md) — Common issues and diagnostic commands.
