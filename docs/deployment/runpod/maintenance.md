# Maintenance

Pod lifecycle management, code updates, backups, model management, and routine operations.

## Pod Lifecycle

### Stop Pod (Saves Money)

```bash
# From local machine
runpodctl pod stop 9eusawy77gd1d0

# Billing stops immediately
# Volume data (/workspace) persists
# Container state is lost (tmux sessions, running processes)
```

### Start Pod (Resume)

```bash
# Resume the pod
runpodctl pod start 9eusawy77gd1d0

# Wait ~30 seconds for it to come up
# Then SSH in and restart services:
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<new-ip> -p <new-port>
bash /workspace/acm-ai/scripts/runpod/start-services.sh
```

> **Important:** IP and SSH port change on every restart. Always check:
> ```bash
> runpodctl pod get 9eusawy77gd1d0
> ```

### Delete Pod (Permanent)

```bash
runpodctl pod delete 9eusawy77gd1d0
# WARNING: All data including /workspace volume is destroyed
# Ollama models, SurrealDB data, and repo will be lost
```

### Create New Pod (After Delete)

Follow the [Setup Guide](setup.md). Remember to:
1. Update pod ID in all documentation and scripts
2. Re-run `setup-pod.sh` for dependency installation
3. Re-pull Ollama models
4. Restore any database backups

## Code Updates

### Pull Latest Code

```bash
# SSH into pod
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<ip> -p <port>

# Pull changes
cd /workspace/acm-ai
git pull --ff-only

# Restart affected services
tmux kill-session -t api
tmux kill-session -t worker

# Re-sync Python deps (if pyproject.toml changed)
uv sync

# Re-install frontend deps (if package.json changed)
cd frontend && npm install && cd ..

# Restart services
bash scripts/runpod/start-services.sh
```

### Push Local Changes → Pod

```bash
# Option 1: Git (recommended)
# On local machine:
git add . && git commit -m "feat: my changes"
git push

# On pod:
cd /workspace/acm-ai && git pull

# Option 2: SCP (for quick file transfers)
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  ./open_notebook/graphs/acm_extraction.py \
  root@174.94.157.109:/workspace/acm-ai/open_notebook/graphs/

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
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  root@174.94.157.109:/workspace/data/backups/*.surql ./
```

### Import SurrealDB Data

```bash
# Upload backup to pod
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  ./surreal-backup.surql root@174.94.157.109:/workspace/data/backups/

# On the pod
surreal import --conn http://localhost:8000 --user root --pass root \
  --ns open_notebook --db development \
  /workspace/data/backups/surreal-backup.surql
```

### Backup Volume Data

```bash
# Create a tarball of all persistent data
ssh -i ~/.runpod/ssh/RunPod-Key-Go -p 31130 root@174.94.157.109 \
  "cd /workspace && tar czf /tmp/acm-data-backup.tar.gz data/"

# Download to local machine
scp -i ~/.runpod/ssh/RunPod-Key-Go -P 31130 \
  root@174.94.157.109:/tmp/acm-data-backup.tar.gz ./
```

## Ollama Model Management

### List Models

```bash
ollama list
# NAME                         SIZE      MODIFIED
# llama3.1:8b-instruct-q8_0    8.5 GB    2 hours ago
# qwen2.5:7b                   4.7 GB    2 hours ago
# qwen3:latest                 5.2 GB    2 hours ago
# mxbai-embed-large            669 MB    2 hours ago
```

### Pull New Models

```bash
ollama pull <model-name>

# Useful models for ACM-AI:
ollama pull qwen2.5:32b       # 19GB — large context extraction
ollama pull qwen3:32b         # 19GB — advanced reasoning
ollama pull phi4:14b           # 8.8GB — good balance
```

### Remove Models (Free VRAM/Disk)

```bash
ollama rm qwen2.5:32b         # Remove from disk
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
bash /workspace/acm-ai/scripts/runpod/health-check.sh

# Individual checks
curl -sf http://localhost:8000/health && echo OK    # SurrealDB
curl -sf http://localhost:11434/api/tags && echo OK  # Ollama
curl -sf http://localhost:5055/health && echo OK      # API
curl -sf http://localhost:8502 && echo OK              # Frontend
tmux list-sessions                                     # All sessions
```

### Disk Usage

```bash
# Volume usage
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
- [ ] Stop the pod when not in use (`runpodctl pod stop`)
- [ ] Pull latest code (`git pull`)

### Monthly
- [ ] Update Ollama (`curl -fsSL https://ollama.com/install.sh | sh`)
- [ ] Update SurrealDB if new v2.x release available
- [ ] Export database backup
- [ ] Check disk usage (`df -h /workspace`)
- [ ] Remove unused Ollama models

### After Pod Recreation
- [ ] Update pod ID in documentation
- [ ] Update proxy URLs
- [ ] Re-run `setup-pod.sh`
- [ ] Re-pull Ollama models
- [ ] Import database backup
- [ ] Test all services with health check

---

**Next:** [Troubleshooting](troubleshooting.md) — Common issues and diagnostic commands.
