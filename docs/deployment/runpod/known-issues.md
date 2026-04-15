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

## KI-3: Cloudflare Tunnel — Migrated to silvatron.au

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Status** | Resolved |

Previously: `acmv3.coralshades.ai` tunnel had DNS/TLS issues. Migrated to new Cloudflare account with `silvatron.au` domain.

**Current state:**
- Tunnel `acm-ai-runpod` (ID `157a5fd8-4eee-458c-83b7-f9055b45b20b`) running with 4 connections
- `https://acmapi.silvatron.au` → API (port 5055) — working
- `https://acm.silvatron.au` → Frontend (port 8502) — working
- Old `coralshades.ai` tunnel (ID `01582008-...`) is deprecated

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

The RTX 5090 deployment scripts exist on the `deploy/runpod-5090` branch (pushed 2026-04-15). The pod is now tracking this branch.

**Impact:** Changes merged to `main` won't appear on the pod until `deploy/runpod-5090` is rebased or merged.

**Fix:** Merge `deploy/runpod-5090` to `main` when ready for production.

---

## KI-7: CORS Configuration Tied to Pod Identity

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Status** | Open |

RunPod proxy URLs contain the pod ID (e.g., `qpzht3hvrbg95w`). CORS configuration in `.env` (`CORS_ALLOWED_ORIGINS`) references these URLs. When a pod is deleted and recreated, it gets a new ID, and the proxy URLs change.

**Impact:** After pod recreation, the frontend may fail CORS preflight checks until `.env` is updated with the new proxy URLs.

**Workaround:** After creating a new pod, update `CORS_ALLOWED_ORIGINS` in `.env` with the new pod ID in the proxy URLs.

**Fix:** Use wildcard CORS for `*.proxy.runpod.net` in development, or rely solely on the Cloudflare tunnel custom domain (`acm.silvatron.au` / `acmapi.silvatron.au`) which provides stable URLs.

---

## Summary

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| KI-1 | Disk space manageable (64% used, resized to 100GB) | Low | Mitigated |
| KI-2 | Network volume not attached (150GB wasted) | High | Open |
| KI-3 | Cloudflare Tunnel — migrated to silvatron.au | Low | Resolved |
| KI-4 | PyTorch nightly required for RTX 5090 | Medium | Mitigated |
| KI-5 | Docker not available (no Langfuse) | Medium | Open |
| KI-6 | 5090 scripts on deploy branch (not main) | Medium | Open |
| KI-7 | CORS config tied to pod identity | Low | Open |
