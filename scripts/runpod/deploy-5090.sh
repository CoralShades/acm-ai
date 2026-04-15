#!/bin/bash
# ACM-AI RunPod RTX 5090 — One-Command Deploy from Local WSL
# Creates network volume, creates pod, SCPs scripts, runs bootstrap remotely
#
# Usage:
#   bash scripts/runpod/deploy-5090.sh \
#     --cf-token "eyJ..."                           \
#     --deploy-key ~/.ssh/acm-ai-deploy             \
#     [--anthropic-key "sk-ant-..."]                \
#     [--datacenter US-IL-1]                        \
#     [--pod-id abc123]                             \
#     [--skip-create]
#
# Prerequisites:
#   1. runpodctl installed:  curl -sL https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64.tar.gz | tar xz -C ~/.local/bin
#   2. API key configured:  runpodctl config --apiKey <key>
#   3. SSH key registered:  runpodctl ssh add-key
#   4. Cloudflare tunnel created in Zero Trust dashboard
#   5. SSH deploy key added to github.com/CoralShades/acm-ai → Deploy keys
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ────────────────────────────────────────
# Defaults
# ────────────────────────────────────────
GPU_TYPE="RTX 5090"
VOLUME_NAME="acm-ai-data"
VOLUME_SIZE=150
POD_NAME="acm-ai-5090"
CONTAINER_DISK=50
DATACENTER="US-IL-1"
FALLBACK_DATACENTERS=("US-NC-1" "US-GA-1" "EU-RO-1")
SSH_TIMEOUT=300
SSH_KEY_PATH="${HOME}/.runpod/ssh/RunPod-Key-Go"

# Arguments
CF_TUNNEL_TOKEN=""
DEPLOY_KEY_PATH=""
ANTHROPIC_KEY=""
POD_ID=""
SKIP_CREATE=false

# ────────────────────────────────────────
# Helpers
# ────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
step() { echo -e "\n${CYAN}[$1/7]${NC} $2"; }

usage() {
    echo "ACM-AI RunPod RTX 5090 — One-Command Deploy"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Required (for full deploy):"
    echo "  --deploy-key PATH    Path to SSH deploy key for GitHub"
    echo ""
    echo "Optional:"
    echo "  --cf-token TOKEN     Cloudflare tunnel token (skips tunnel if omitted)"
    echo "  --anthropic-key KEY  Anthropic API key (last-resort fallback)"
    echo "  --datacenter ID      Preferred datacenter (default: $DATACENTER)"
    echo "  --pod-id ID          Target existing pod (skip creation)"
    echo "  --skip-create        Re-run setup on existing pod (requires --pod-id)"
    echo "  --ssh-key PATH       Path to RunPod SSH private key (default: $SSH_KEY_PATH)"
    echo "  --help               Show this help"
    exit 0
}

# ────────────────────────────────────────
# Parse Arguments
# ────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cf-token)      CF_TUNNEL_TOKEN="$2"; shift 2 ;;
        --deploy-key)    DEPLOY_KEY_PATH="$2"; shift 2 ;;
        --anthropic-key) ANTHROPIC_KEY="$2"; shift 2 ;;
        --datacenter)    DATACENTER="$2"; shift 2 ;;
        --pod-id)        POD_ID="$2"; shift 2 ;;
        --skip-create)   SKIP_CREATE=true; shift ;;
        --ssh-key)       SSH_KEY_PATH="$2"; shift 2 ;;
        --help|-h)       usage ;;
        *)               echo "Unknown option: $1"; usage ;;
    esac
done

echo "========================================"
echo "  ACM-AI RunPod RTX 5090 Deploy"
echo "========================================"
echo ""

# ────────────────────────────────────────
# Phase 0: Preflight Checks
# ────────────────────────────────────────
step 0 "Preflight checks..."

# runpodctl
if ! command -v runpodctl &>/dev/null; then
    echo "  runpodctl not found. Installing..."
    mkdir -p ~/.local/bin
    curl -sL https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-linux-amd64.tar.gz \
        | tar xz -C ~/.local/bin
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v runpodctl &>/dev/null; then
        fail "runpodctl installation failed. Install manually and add to PATH."
    fi
fi
ok "runpodctl $(runpodctl version 2>/dev/null || echo 'installed')"

# API key
if ! runpodctl user &>/dev/null; then
    fail "RunPod API key not configured. Run: runpodctl config --apiKey <your-key>"
fi
ok "RunPod account authenticated"

# SSH key
if [[ ! -f "$SSH_KEY_PATH" ]]; then
    # Try common alternatives
    for alt in "$HOME/.ssh/id_ed25519" "$HOME/.ssh/id_rsa" "$HOME/.runpod/ssh/id_ed25519"; do
        if [[ -f "$alt" ]]; then
            SSH_KEY_PATH="$alt"
            break
        fi
    done
fi
if [[ -f "$SSH_KEY_PATH" ]]; then
    ok "SSH key found at $SSH_KEY_PATH"
else
    warn "SSH key not found at $SSH_KEY_PATH — pod may not be accessible via SSH"
    echo "  Run: runpodctl ssh add-key"
fi

# Deploy key
if [[ -n "$DEPLOY_KEY_PATH" && -f "$DEPLOY_KEY_PATH" ]]; then
    ok "Deploy key found at $DEPLOY_KEY_PATH"
elif [[ -n "$DEPLOY_KEY_PATH" ]]; then
    fail "Deploy key not found at $DEPLOY_KEY_PATH"
else
    warn "No --deploy-key specified — repo clone will use HTTPS (may need PAT)"
fi

# Check balance
echo "  Account balance:"
runpodctl user 2>/dev/null | grep -i balance || true

if [[ "$SKIP_CREATE" == true ]]; then
    echo ""
    echo "  --skip-create: Skipping volume and pod creation"
fi

# ────────────────────────────────────────
# Phase 1: Network Volume
# ────────────────────────────────────────
VOLUME_ID=""
if [[ "$SKIP_CREATE" != true && -z "$POD_ID" ]]; then
    step 1 "Creating network volume ($VOLUME_NAME, ${VOLUME_SIZE}GB)..."

    # Check if volume already exists
    VOLUME_ID=$(runpodctl network-volume list 2>/dev/null \
        | python3 -c "import sys,json; vols=json.load(sys.stdin); [print(v['id']) for v in vols if v['name']=='$VOLUME_NAME']" 2>/dev/null | head -1 || echo "")
    if [[ -n "$VOLUME_ID" ]]; then
        ok "Volume '$VOLUME_NAME' already exists (ID: $VOLUME_ID)"
    else
        echo "  Creating ${VOLUME_SIZE}GB volume in ${DATACENTER}..."
        VOL_OUTPUT=$(runpodctl network-volume create \
            --name "$VOLUME_NAME" \
            --size "$VOLUME_SIZE" \
            --data-center-id "$DATACENTER" 2>&1) || {
                warn "Volume creation failed in $DATACENTER — trying fallbacks"
                for dc in "${FALLBACK_DATACENTERS[@]}"; do
                    echo "  Trying $dc..."
                    if VOL_OUTPUT=$(runpodctl network-volume create \
                        --name "$VOLUME_NAME" \
                        --size "$VOLUME_SIZE" \
                        --data-center-id "$dc" 2>&1); then
                        DATACENTER="$dc"
                        ok "Volume created in $dc"
                        break
                    fi
                done
            }
        echo "  $VOL_OUTPUT"
        VOLUME_ID=$(echo "$VOL_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    fi
    if [[ -n "$VOLUME_ID" ]]; then
        ok "Network volume ID: $VOLUME_ID"
    else
        warn "Could not determine volume ID — pod will not have network volume"
    fi
else
    step 1 "Skipping volume creation (--skip-create or --pod-id provided)"
fi

# ────────────────────────────────────────
# Phase 2: Create Pod
# ────────────────────────────────────────
if [[ "$SKIP_CREATE" != true && -z "$POD_ID" ]]; then
    step 2 "Creating RTX 5090 pod..."

    # Build env vars as JSON object for --env flag
    ENV_JSON="{"
    ENV_PARTS=()
    [[ -n "$CF_TUNNEL_TOKEN" ]] && ENV_PARTS+=("\"CF_TUNNEL_TOKEN\":\"$CF_TUNNEL_TOKEN\"")
    [[ -n "$ANTHROPIC_KEY" ]] && ENV_PARTS+=("\"ACM_ANTHROPIC_API_KEY\":\"$ANTHROPIC_KEY\"")
    ENV_JSON+=$(IFS=,; echo "${ENV_PARTS[*]}")
    ENV_JSON+="}"

    # Build volume args
    VOL_ARGS=""
    if [[ -n "$VOLUME_ID" ]]; then
        VOL_ARGS="--network-volume-id $VOLUME_ID"
    else
        VOL_ARGS="--volume-in-gb 0"
    fi

    # Check GPU availability
    echo "  Checking RTX 5090 availability..."
    runpodctl gpu list 2>/dev/null | grep -i "5090" || warn "RTX 5090 may not be listed yet"

    echo "  Using RunPod PyTorch template..."

    # Helper function to create pod in a given datacenter
    create_pod_in_dc() {
        local dc="$1"
        runpodctl pod create \
            --name "$POD_NAME" \
            --gpu-id "NVIDIA GeForce RTX 5090" \
            --image "runpod/pytorch:2.8.0-py3.12-cuda12.8.0-devel-ubuntu24.04" \
            --container-disk-in-gb "$CONTAINER_DISK" \
            $VOL_ARGS \
            --ssh \
            --ports "5055/http,8000/http,8502/http,11434/http,3000/http,22/tcp" \
            --data-center-ids "$dc" \
            ${ENV_PARTS:+--env "$ENV_JSON"} 2>&1
    }

    # Create pod
    echo "  Creating pod in $DATACENTER..."
    CREATE_OUTPUT=$(create_pod_in_dc "$DATACENTER") || {
            echo "  Create failed in $DATACENTER. Trying fallback datacenters..."
            for dc in "${FALLBACK_DATACENTERS[@]}"; do
                echo "  Trying $dc..."
                CREATE_OUTPUT=$(create_pod_in_dc "$dc") && break
            done
        }

    echo "  $CREATE_OUTPUT"

    # Extract pod ID from JSON output
    POD_ID=$(echo "$CREATE_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    # Fallback: try regex if JSON parsing fails
    [[ -z "$POD_ID" ]] && POD_ID=$(echo "$CREATE_OUTPUT" | grep -oP '"id"\s*:\s*"([a-z0-9]+)"' | head -1 | grep -oP '[a-z0-9]{8,}' || echo "")
    if [[ -z "$POD_ID" ]]; then
        echo ""
        echo "  Could not auto-detect pod ID from output."
        echo "  Run: runpodctl pod list"
        echo "  Then re-run with: $0 --pod-id <id> --skip-create ..."
        exit 1
    fi
    ok "Pod created: $POD_ID"
else
    step 2 "Using existing pod: $POD_ID"
fi

# ────────────────────────────────────────
# Phase 3: Wait for SSH
# ────────────────────────────────────────
step 3 "Waiting for pod SSH to become reachable..."

# Get SSH info
SSH_INFO=""
for attempt in $(seq 1 30); do
    SSH_INFO=$(runpodctl ssh info "$POD_ID" 2>/dev/null || echo "")
    if [[ -n "$SSH_INFO" ]]; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

if [[ -z "$SSH_INFO" ]]; then
    fail "Could not get SSH info for pod $POD_ID"
fi

echo "  SSH info:"
echo "$SSH_INFO" | sed 's/^/    /'

# Parse SSH host and port from info
SSH_HOST=$(echo "$SSH_INFO" | grep -oP '[\w.-]+\.runpod\.io' | head -1 || echo "")
SSH_PORT=$(echo "$SSH_INFO" | grep -oP '(?<=-p\s)\d+' | head -1 || echo "22")

if [[ -z "$SSH_HOST" ]]; then
    echo ""
    echo "  Could not parse SSH host from pod info."
    echo "  SSH info: $SSH_INFO"
    echo "  You can manually SSH and run setup:"
    echo "    ssh -i $SSH_KEY_PATH root@<host> -p <port>"
    echo "    bash /tmp/runpod-setup/setup-pod-5090.sh"
    exit 1
fi

# Wait for SSH to be reachable
echo -n "  Waiting for SSH ($SSH_HOST:$SSH_PORT)"
ELAPSED=0
while [[ $ELAPSED -lt $SSH_TIMEOUT ]]; do
    if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        -p "$SSH_PORT" "root@$SSH_HOST" "echo ok" &>/dev/null; then
        echo -e " ${GREEN}connected${NC}"
        break
    fi
    echo -n "."
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [[ $ELAPSED -ge $SSH_TIMEOUT ]]; then
    fail "SSH timed out after ${SSH_TIMEOUT}s"
fi
ok "SSH connection established"

# SSH command shortcut
SSH_CMD="ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no -p $SSH_PORT root@$SSH_HOST"
SCP_CMD="scp -i $SSH_KEY_PATH -o StrictHostKeyChecking=no -P $SSH_PORT"

# ────────────────────────────────────────
# Phase 4: Copy Scripts to Pod
# ────────────────────────────────────────
step 4 "Copying setup scripts to pod..."

# Create temp directory on pod
$SSH_CMD "mkdir -p /tmp/runpod-setup"

# Copy the entire scripts/runpod directory
$SCP_CMD -r "$SCRIPT_DIR"/* "root@$SSH_HOST:/tmp/runpod-setup/" 2>&1 | tail -3
ok "Scripts copied to /tmp/runpod-setup/"

# Copy deploy key if provided
if [[ -n "$DEPLOY_KEY_PATH" && -f "$DEPLOY_KEY_PATH" ]]; then
    $SSH_CMD "mkdir -p /root/.ssh"
    $SCP_CMD "$DEPLOY_KEY_PATH" "root@$SSH_HOST:/root/.ssh/acm-ai-deploy"
    $SSH_CMD "chmod 600 /root/.ssh/acm-ai-deploy"
    ok "Deploy key copied to pod"
fi

# ────────────────────────────────────────
# Phase 5: Run Bootstrap on Pod
# ────────────────────────────────────────
step 5 "Running bootstrap on pod (this takes 15-25 minutes)..."
echo "  The setup script will stream output below."
echo "  If disconnected, SSH in and check: tmux list-sessions"
echo ""
echo "  ────────────────────────────────────────"

# Run setup script remotely (streaming output)
$SSH_CMD "bash /tmp/runpod-setup/setup-pod-5090.sh" 2>&1 || {
    echo ""
    warn "Bootstrap script exited with non-zero status"
    echo "  SSH into the pod to debug:"
    echo "    $SSH_CMD"
    echo "  Check logs:"
    echo "    tail -50 /workspace/acm-ai/logs/*.log"
}

echo "  ────────────────────────────────────────"

# ────────────────────────────────────────
# Phase 6: Print Summary
# ────────────────────────────────────────
step 6 "Deploy complete!"
echo ""
echo "  Pod ID:    $POD_ID"
echo "  SSH:       $SSH_CMD"
echo ""
echo "  External access:"
echo "    API:       https://acmapi.silvatron.au"
echo "    Frontend:  https://acm.silvatron.au"
echo ""
echo "  RunPod proxy URLs:"
echo "    API:       https://${POD_ID}-5055.proxy.runpod.net"
echo "    Frontend:  https://${POD_ID}-8502.proxy.runpod.net"
echo "    Ollama:    https://${POD_ID}-11434.proxy.runpod.net"
echo "    Langfuse:  https://${POD_ID}-3000.proxy.runpod.net"
echo ""
echo "  Manage pod:"
echo "    runpodctl pod stop $POD_ID     # Stop (saves $)"
echo "    runpodctl pod start $POD_ID    # Restart"
echo "    runpodctl pod delete $POD_ID   # Delete permanently"
echo ""
echo "  After restart, SSH in and run:"
echo "    bash /workspace/acm-ai/scripts/runpod/setup-pod-5090.sh --from 2"
echo ""
