# RunPod Initial Setup

Step-by-step guide to create a RunPod GPU pod and install all ACM-AI dependencies.

## Prerequisites (Local Machine)

Before creating a pod, install these tools locally:

### 1. RunPod Account
- Sign up at [runpod.io](https://runpod.io)
- Add credits ($5+ recommended for testing)
- Get your API key from [Settings](https://runpod.io/console/user/settings)

### 2. RunPod CLI (`runpodctl`)

```bash
# Windows (PowerShell)
Invoke-WebRequest -Uri https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-windows-amd64.zip -OutFile runpodctl.zip
Expand-Archive runpodctl.zip -DestinationPath $env:LOCALAPPDATA\runpodctl
[Environment]::SetEnvironmentVariable('Path', $env:Path + ";$env:LOCALAPPDATA\runpodctl", 'User')

# Linux/macOS
mkdir -p ~/.local/bin && curl -sL https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64.tar.gz | tar xz -C ~/.local/bin

# macOS (Homebrew)
brew install runpod/runpodctl/runpodctl
```

Verify: `runpodctl version` → `2.1.6+`

### 3. Configure API Key

```bash
# Interactive setup (recommended for first time)
runpodctl doctor

# Or set via environment variable
export RUNPOD_API_KEY=rpa_your_key_here
```

### 4. Set Up SSH Keys

```bash
# Generate and register SSH key (interactive)
echo "y" | runpodctl ssh add-key
```

This creates `~/.runpod/ssh/RunPod-Key-Go` (private) and registers the public key with RunPod.

> **Important:** SSH keys must be registered BEFORE creating the pod. Pods created before key registration won't have SSH access — you'll need to delete and recreate the pod.

### 5. RunPod MCP Server (for Claude Code)

```bash
claude mcp add runpod --scope local --env RUNPOD_API_KEY=rpa_your_key -- npx -y @runpod/mcp-server@latest
```

### 6. Add RUNPOD_API_KEY to `.env`

```bash
# In your project .env (already gitignored)
RUNPOD_API_KEY=rpa_your_key_here
```

## Creating the Pod

### Check GPU Availability

```bash
# List all GPUs with stock status
runpodctl gpu list

# List datacenters with RTX 5090 availability
runpodctl datacenter list
```

RTX 5090 is typically available in: EU-CZ-1, EU-RO-1, EUR-IS-1, EUR-IS-2, EUR-NO-1, US-IL-1, US-NC-1.

### Create Pod via GraphQL API

The RunPod MCP and CLI don't support all creation options. Use the GraphQL API for full control:

```bash
curl -s https://api.runpod.io/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { podFindAndDeployOnDemand(input: {
      name: \"acm-ai-dev\",
      templateId: \"runpod-torch-v280\",
      gpuTypeId: \"NVIDIA GeForce RTX 5090\",
      gpuCount: 1,
      cloudType: COMMUNITY,
      containerDiskInGb: 50,
      volumeInGb: 75,
      volumeMountPath: \"/workspace\",
      ports: \"5055/http,8000/http,8502/http,11434/http,3000/http,22/tcp\",
      startSsh: true
    }) { id name desiredStatus machine { gpuDisplayName } } }"
  }'
```

### Or use runpodctl CLI (simpler, fewer options)

```bash
runpodctl pod create \
  --name "acm-ai-dev" \
  --template-id runpod-torch-v280 \
  --gpu-id "NVIDIA GeForce RTX 5090" \
  --container-disk-in-gb 50 \
  --volume-in-gb 75 \
  --volume-mount-path /workspace \
  --ports "5055/http,8000/http,8502/http,11434/http,3000/http,22/tcp" \
  --ssh
```

### Or use RunPod MCP (from Claude Code)

```
mcp__runpod__create-pod with:
  name: "acm-ai-dev"
  imageName: "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
  gpuTypeIds: ["NVIDIA GeForce RTX 5090"]
  containerDiskInGb: 50
  volumeInGb: 75
  volumeMountPath: "/workspace"
  ports: ["5055/http", "8000/http", "8502/http", "11434/http", "3000/http", "22/tcp"]
```

### GPU Type IDs (for `gpuTypeId` parameter)

| Display Name | GPU ID | VRAM | Approx Cost/hr |
|-------------|--------|------|-----------------|
| RTX 4090 | `NVIDIA GeForce RTX 4090` | 24GB | $0.39 |
| RTX 5090 | `NVIDIA GeForce RTX 5090` | 32GB | $0.69 |
| A100 PCIe | `NVIDIA A100 80GB PCIe` | 80GB | $1.64 |
| H100 SXM | `NVIDIA H100 80GB HBM3` | 80GB | $3.89 |
| H200 SXM | `NVIDIA H200` | 141GB | $4.49 |

### Template IDs

| Template | ID | Image | Notes |
|----------|-----|-------|-------|
| PyTorch 2.8.0 | `runpod-torch-v280` | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` | Recommended |
| PyTorch 2.4.0 | `runpod-torch-v240` | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` | Stable fallback |
| PyTorch 2.1.0 | `runpod-torch-v21` | `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04` | Legacy |

## Pod Initialization

After the pod is created and running (~30s), SSH in and run the 5090 setup script:

```bash
# Get SSH info
runpodctl pod get <pod-id>
# Look for ssh.ssh_command field

# SSH in
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<ip> -p <port>

# On the pod — run one-time setup (10-phase bootstrap):
bash /workspace/acm-ai/scripts/runpod/setup-pod-5090.sh
```

The `setup-pod-5090.sh` script runs 10 phases (compared to 8 in the old `setup-pod.sh`) and includes deploy key configuration, PyTorch nightly installation, and Cloudflare tunnel setup.

### Deploy Key (GitHub read-only access)

The pod uses a deploy key (`~/.ssh/acm-ai-deploy`) for read-only git clone access instead of a personal access token. The local copy of the key is at `~/.ssh/acm-ai-deploy`.

### Or deploy from WSL (one-command)

```bash
# From your local WSL machine — handles SSH + setup in one shot:
bash /mnt/d/ailocal/acm-ai/scripts/runpod/deploy-5090.sh
```

### Or run setup manually

```bash
# Install SurrealDB v2 (NOT v3 nightly!)
curl -sSf https://install.surrealdb.com | sh -s -- --version v2.2.1

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install Node.js 22 (was 20 on old pod)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# Clone repo (using deploy key)
cd /workspace
GIT_SSH_COMMAND="ssh -i ~/.ssh/acm-ai-deploy -o StrictHostKeyChecking=no" \
  git clone --branch main https://github.com/CoralShades/acm-ai.git
cd acm-ai

# Copy env template
cp scripts/runpod/.env.runpod .env
# Edit .env with your API keys:
nano .env

# Install dependencies
uv sync
cd frontend && npm install && npm run build
```

> **Critical:** Install SurrealDB v2.x specifically (`--version v2.2.1`). The default `curl | sh` installs v3 nightly which has incompatible migration syntax (`FLEXIBLE TYPE` parse error).

### PyTorch Nightly (Required for RTX 5090)

Standard PyTorch releases do not yet support the RTX 5090 (Blackwell / sm_120 architecture). You must install the nightly build with CUDA 12.8:

```bash
pip install --force-reinstall torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/nightly/cu128
```

The current pod runs PyTorch 2.12.0.dev (nightly) with CUDA 12.8.

## Verify Setup

```bash
surreal version    # → 2.2.1
ollama --version   # → 0.18.0+
uv --version       # → 0.9.0+
node -v            # → v22.x
nvidia-smi         # → Shows RTX 5090, 32607 MiB, Driver 570.195.03
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
                   # → 2.12.0.dev... True
```

---

**Next:** [Services](services.md) — Configure and start all services.
