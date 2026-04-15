# Known Issues -- RTX 5090 RunPod Deployment

**Last updated:** 2026-04-15
**Pod ID:** `qpzht3hvrbg95w`
**Back to:** [RunPod Deployment Index](index.md)

This document tracks active, unresolved issues specific to the current RTX 5090 RunPod deployment. For general troubleshooting and fixes, see [Troubleshooting](troubleshooting.md).

---

## KI-1: Disk Space Manageable (64% Used)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Status** | Mitigated |

Container disk was resized from 50GB to 100GB. Currently 64% used (37GB free).

**Breakdown:**
- 5 Ollama models consume ~46GB (deduplicated): `gemma4:26b` (17GB), `gemma4:31b` (19GB), `gemma4:e4b` + `gemma4:latest` (9.6GB shared blob), `mxbai-embed-large` (0.7GB)
- System, Python venv, frontend production build, and repo consume ~18GB

**Can still fit:**
- `phi4:14b` (~8GB) — optional fallback
- `llama3.1:8b` (~5GB) — optional legacy fallback

**Impact:** Comfortable headroom for data growth, logs, and temporary files.

**Workaround:** Monitor with `df -h /`. Clean logs and caches periodically.

**Note:** Disk resize wipes the container — all tools and data must be re-bootstrapped. Data persists across stop/start but NOT across resize or delete.

---

## KI-2: Network Volume Not Attached (150GB Wasted)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Status** | Open |

Network volume `acm-ai-data` (ID: `pevpptyb5x`, 150GB) exists in **US-IL-1** (Illinois). The pod runs in **CA** (Canada, Community Cloud). RunPod network volumes can only attach to pods in the same datacenter.

**Impact:** $4.50/month wasted on an unused volume. Pod data is ephemeral -- it persists across stop/start cycles but is permanently lost on pod delete.

**Workaround:** Pod data survives stop/start. Avoid deleting the pod. Back up critical data (SurrealDB exports, `.env`) to local machine before any destructive operation.

**Fix:** Either:
1. Delete the US-IL-1 volume and create a new one in CA, or
2. Wait for RTX 5090 availability in US-IL-1 and recreate the pod there

---

## KI-3: Cloudflare Tunnel DNS/TLS Failure

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Status** | Open |

The Cloudflare tunnel is running on the pod with 4 connections registered, but external custom domain URLs fail with TLS handshake errors:
- `https://api.acmv3.coralshades.ai` -- SSL alert handshake failure
- `https://app.acmv3.coralshades.ai` -- SSL alert handshake failure

**Impact:** Cannot access services via custom domain names. Must use RunPod proxy URLs instead.

**Workaround:** Use RunPod proxy URLs:
- Frontend: `https://qpzht3hvrbg95w-8502.proxy.runpod.net`
- API: `https://qpzht3hvrbg95w-5055.proxy.runpod.net`
- API Docs: `https://qpzht3hvrbg95w-5055.proxy.runpod.net/docs`

**Fix:** Check Cloudflare dashboard:
1. Verify CNAME records exist for `api.acmv3` and `app.acmv3` pointing to `01582008-a8d2-400f-a342-cc56a632e381.cfargotunnel.com` (proxied, orange cloud)
2. Verify SSL/TLS encryption mode is set to "Full" or "Flexible" (not "Full (strict)" unless a valid origin cert is installed)
3. Ensure the tunnel ingress rules in `config.yml` on the pod match the expected hostnames

---

## KI-4: PyTorch Nightly Required (No Stable Release for RTX 5090)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Status** | Mitigated |

The RTX 5090 uses NVIDIA Blackwell architecture with compute capability `sm_120`. Standard PyTorch stable releases only support up to `sm_90` (Ada Lovelace / RTX 4090). The pod must run PyTorch nightly with CUDA 12.8 support: `torch-2.12.0.dev20260407+cu128`.

**Impact:** Potential instability from dev builds. Running `uv sync` may overwrite the nightly torch with an incompatible stable version if `pyproject.toml` pins a torch version.

**Workaround:** After any `uv sync`, force-reinstall PyTorch nightly:
```bash
source .venv/bin/activate
pip install --force-reinstall torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/nightly/cu128
```

**Fix:** Wait for a PyTorch stable release with CUDA 12.8+ and `sm_120` support (expected in PyTorch 2.12 or later).

---

## KI-5: Docker Not Available (No Langfuse)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Status** | Open |

RunPod Community Cloud pods do not support Docker-in-Docker. The Langfuse observability stack (PostgreSQL, ClickHouse, Redis, MinIO, Langfuse Web/Worker) requires Docker Compose and therefore cannot run on this pod.

**Impact:** No LLM tracing, cost tracking, or prompt debugging on the RunPod deployment.

**Workaround:** Use Langfuse Cloud (free tier available). Update `LANGFUSE_HOST` in `.env` to point to the cloud instance:
```bash
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

**Fix:** Either:
1. Switch to Secure Cloud ($0.99/hr for RTX 5090) which supports Docker, or
2. Use an external Langfuse Cloud instance (recommended for production regardless)

---

## KI-6: New 5090 Scripts Not in Git (Main Branch)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Status** | Open |

The RTX 5090 deployment scripts (`deploy-5090.sh`, `setup-pod-5090.sh`, `start-services-5090.sh`, `health-check-5090.sh`) exist on the `feat/sf-reconciliation-20260411` branch but have not been merged to `main`. The pod was cloned from `main`, so the scripts were manually copied from `/tmp/runpod-setup/` during initial setup.

**Impact:** Running `git pull` on the pod (tracking `main`) will not include the 5090 scripts, or may overwrite manually placed copies if they were added to the working tree.

**Workaround:** Do not rely on `git pull` to update the scripts. If the pod is recreated, manually copy the scripts from the feature branch or from local.

**Fix:** Merge the `feat/sf-reconciliation-20260411` branch (or at minimum the 5090 scripts) to `main`, then `git pull` on the pod.

---

## KI-7: CORS Configuration Tied to Pod Identity

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Status** | Open |

RunPod proxy URLs contain the pod ID (e.g., `qpzht3hvrbg95w`). CORS configuration in `.env` (`CORS_ALLOWED_ORIGINS`) references these URLs. When a pod is deleted and recreated, it gets a new ID, and the proxy URLs change.

**Impact:** After pod recreation, the frontend may fail CORS preflight checks until `.env` is updated with the new proxy URLs.

**Workaround:** After creating a new pod, update `CORS_ALLOWED_ORIGINS` in `.env` with the new pod ID in the proxy URLs.

**Fix:** Use wildcard CORS for `*.proxy.runpod.net` in development, or rely solely on the Cloudflare tunnel custom domain (once KI-3 is resolved) which provides stable URLs.

---

## Summary

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| KI-1 | Disk space manageable (64% used, resized to 100GB) | Low | Mitigated |
| KI-2 | Network volume not attached (150GB wasted) | High | Open |
| KI-3 | Cloudflare Tunnel DNS/TLS failure | High | Open |
| KI-4 | PyTorch nightly required for RTX 5090 | Medium | Mitigated |
| KI-5 | Docker not available (no Langfuse) | Medium | Open |
| KI-6 | 5090 scripts not merged to main | Medium | Open |
| KI-7 | CORS config tied to pod identity | Low | Open |
