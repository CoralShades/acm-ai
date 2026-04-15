# Optimization

GPU memory management, model selection strategies, performance tuning, and cost optimization for RunPod.

## GPU Memory Management

### RTX 5090 Memory Budget (32GB)

| Model | VRAM Usage | Disk Size | Use Case |
|-------|-----------|-----------|----------|
| gemma4:26b | ~18GB | 17GB | Extraction, tools, transformation |
| gemma4:e4b | ~10GB | 9.6GB | ACM per-row extraction |
| gemma4:latest | ~10GB | 9.6GB | Chat |
| mxbai-embed-large | ~1GB | 669MB | Embeddings |

> **Note:** PyTorch nightly (cu128) is required for Blackwell GPUs (RTX 5090). Standard
> PyTorch builds do not support the sm_120 compute capability. See
> [Troubleshooting](troubleshooting.md) for details.

### Multi-Model Loading

Ollama keeps recently used models in VRAM. On 32GB RTX 5090:
- **2 medium models** (gemma4:e4b + gemma4:latest + embedding) can coexist (~21GB total)
- **1 large model** (gemma4:26b) uses most VRAM (~18GB), can coexist with embedding (~19GB total)
- **Switching penalty**: Loading a new model takes 3-10 seconds (vs <1s if already loaded)

### Control VRAM Usage

```bash
# Limit concurrent models in VRAM (on the pod)
export OLLAMA_MAX_LOADED_MODELS=2    # Default: auto
export OLLAMA_NUM_PARALLEL=2          # Max concurrent inference requests

# Set in the tmux session:
tmux kill-session -t ollama
tmux new-session -d -s ollama \
  "OLLAMA_HOST=0.0.0.0:11434 \
   OLLAMA_MODELS=/workspace/data/ollama \
   OLLAMA_MAX_LOADED_MODELS=2 \
   OLLAMA_NUM_PARALLEL=2 \
   ollama serve"
```

### Monitor VRAM

```bash
# One-shot check
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader

# Continuous monitoring (updates every 2 seconds)
watch -n 2 nvidia-smi

# See which models are loaded
curl http://localhost:11434/api/ps
```

## Model Selection Strategy

### For ACM Extraction

| Priority | Model | Why |
|----------|-------|-----|
| 1st | `gemma4:26b` | Best quality for structured extraction, tools support |
| 2nd | `gemma4:e4b` | Lighter alternative for per-row extraction |

### For Chat

| Priority | Model | Why |
|----------|-------|-----|
| 1st | `gemma4:latest` | General-purpose chat |
| 2nd | `gemma4:26b` | Higher quality when VRAM budget allows |

### For Embeddings

| Priority | Model | Why |
|----------|-------|-----|
| 1st | `mxbai-embed-large` | Standard embedding model, small VRAM footprint |

### .env Model Configuration

```bash
# Per-row extraction
ACM_EXTRACTION_MODEL=gemma4:e4b
ACM_ROW_EXTRACTION_NUM_CTX=2048

# Default models (general purpose)
DEFAULT_CHAT_MODEL=ollama/gemma4:latest
DEFAULT_TRANSFORMATION_MODEL=ollama/gemma4:26b
DEFAULT_LARGE_CONTEXT_MODEL=ollama/gemma4:26b
DEFAULT_EXTRACTION_MODEL=ollama/gemma4:e4b
DEFAULT_EMBEDDING_MODEL=ollama/mxbai-embed-large
```

## Context Window Tuning

```bash
# Global default context window
OLLAMA_NUM_CTX=32768  # 32k tokens (fine for 32GB VRAM)

# Per-row extraction uses smaller context (faster)
ACM_ROW_EXTRACTION_NUM_CTX=2048

# For metadata extraction, needs at least 16k
# (8k produces "consultant=Unknown, buildings=0")
```

> **Rule of thumb:** Each 1k tokens of context ~ 50MB VRAM (varies by model and quantization).

## Cost Optimization

### Current Pricing (Community Cloud)

| GPU | Cost/hr | VRAM | Best For |
|-----|---------|------|----------|
| RTX 4090 | $0.39 | 24GB | Development, small models |
| RTX 5090 | $0.69 | 32GB | **Current deployment** — gemma4 family fits |
| A100 80GB | $1.64 | 80GB | Multiple large models simultaneously |
| H100 80GB | $3.89 | 80GB | Maximum throughput |

### Cost-Saving Tips

1. **Stop the pod when not using it**
   ```bash
   runpodctl pod stop qpzht3hvrbg95w   # Stops billing
   runpodctl pod start qpzht3hvrbg95w  # Resume later
   ```
   Container disk data persists across stop/start. You only pay when the pod is running.

2. **Use spot/interruptible instances** for batch processing
   - Set `cloudType: COMMUNITY` for lower prices
   - `SECURE` cloud is ~2x more expensive

3. **Right-size your GPU**
   - If only running gemma4:e4b/latest -> RTX 4090 ($0.39/hr) may suffice
   - If running gemma4:26b -> RTX 5090 ($0.69/hr) is the sweet spot
   - Only use A100/H100 if you need multi-model concurrency

4. **Use `OLLAMA_MAX_LOADED_MODELS=1`** if running one model at a time
   - Reduces idle VRAM consumption
   - Model loads take 3-10 seconds on first request

5. **Monitor spending**
   ```bash
   runpodctl user                      # Current balance + spend rate
   runpodctl billing pods              # Historical pod billing
   ```

## Performance Benchmarks (RTX 5090)

> **TBD:** No benchmarks have been run yet for the gemma4 model family on the RTX 5090.
> Previous benchmarks were for phi4/qwen/llama models on the old deployment and are not
> comparable. Benchmarks will be added once extraction pipeline testing is complete.

| Model | Tokens/sec | First Token (ms) | VRAM Usage |
|-------|-----------|-------------------|------------|
| gemma4:26b | TBD | TBD | ~18GB |
| gemma4:e4b | TBD | TBD | ~10GB |
| gemma4:latest | TBD | TBD | ~10GB |
| mxbai-embed-large | N/A | TBD | ~1GB |

### Extraction Pipeline Performance

| Metric | RTX 4090 (local) | RTX 5090 (RunPod) | Improvement |
|--------|-------------------|-------------------|-------------|
| gemma4 tok/s | TBD | TBD | TBD |
| VRAM | 24GB | 32GB | +33% |
| Max concurrent models | 1-2 small | 2 medium or 1 large + embedding | Better multi-model |

## Network Performance

The current pod has:
- Download: 925 Mbps
- Upload: 863 Mbps
- Disk throughput: 11,401 MB/s

This means:
- Model downloads (ollama pull) are fast (~1 min for 8GB model)
- Git clone/pull is near-instant
- PDF uploads via the API are fast

## Ollama Inference Optimization

```bash
# For maximum throughput on a single model:
OLLAMA_NUM_PARALLEL=4          # Process 4 requests simultaneously
OLLAMA_MAX_LOADED_MODELS=1     # Keep only 1 model in VRAM
OLLAMA_FLASH_ATTENTION=1       # Enable flash attention (if supported)

# For multi-model workflows:
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=3     # Keep embedding + extraction + chat loaded
```

## Disk Budget

Container disk is 100GB with no network volume. Current usage is ~64%:

| Item | Approximate Size | Notes |
|------|-----------------|-------|
| gemma4:e4b + gemma4:latest | 9.6GB | Shared blob (same model ID) |
| gemma4:26b | 17GB | Default extraction + tools |
| gemma4:31b | 19GB | Large context |
| mxbai-embed-large | 669MB | Embeddings |
| Python venv + deps | ~3GB | |
| Node modules + frontend | ~1GB | |
| SurrealDB data | ~500MB | |
| System + repo + misc | ~12GB | |
| **Total** | **~63GB / 100GB** | **37GB free** |

> Optional fallback models can still fit: `phi4:14b` (8GB) and `llama3.1:8b` (5GB).
> Monitor with `df -h /`.

---

**Next:** [Maintenance](maintenance.md) — Updates, backups, and pod lifecycle management.
