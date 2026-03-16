# Optimization

GPU memory management, model selection strategies, performance tuning, and cost optimization for RunPod.

## GPU Memory Management

### RTX 5090 Memory Budget (32GB)

| Model | VRAM Usage | Tokens/sec | Use Case |
|-------|-----------|------------|----------|
| llama3.1:8b-instruct-q8_0 | ~9GB | 207 tok/s | Extraction (primary) |
| qwen2.5:7b | ~5GB | ~180 tok/s | Extraction (alternative) |
| qwen3:latest (8b) | ~5GB | ~180 tok/s | Chat |
| mxbai-embed-large | ~1GB | N/A | Embeddings |
| qwen2.5:32b | ~19GB | ~45 tok/s | Large context |
| qwen3:32b | ~19GB | ~45 tok/s | Advanced chat |

### Multi-Model Loading

Ollama keeps recently used models in VRAM. On 32GB RTX 5090:
- **2-3 small models** (8b-class) can coexist (~15GB total)
- **1 large model** (32b-class) uses most VRAM (~19GB)
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
| 1st | `llama3.1:8b-instruct-q8_0` | Best JSON compliance, fastest (207 tok/s) |
| 2nd | `qwen2.5:7b` | Good alternative, slightly different extraction patterns |
| Avoid | `qwen2.5:32b` for per-row | Overkill for single-row extraction, wastes VRAM |

### For Metadata/Structure Extraction

| Priority | Model | Why |
|----------|-------|-----|
| 1st | `qwen2.5:32b` | Better at understanding document structure |
| 2nd | `llama3.1:8b-instruct-q8_0` | Acceptable with `num_ctx=16384+` |

### .env Model Configuration

```bash
# Per-row extraction (small, fast)
ACM_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0
ACM_ROW_EXTRACTION_NUM_CTX=2048

# Default models (general purpose)
DEFAULT_CHAT_MODEL=ollama/qwen3:latest
DEFAULT_TRANSFORMATION_MODEL=ollama/qwen3:32b
DEFAULT_LARGE_CONTEXT_MODEL=ollama/qwen2.5:32b
DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:7b
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

> **Rule of thumb:** Each 1k tokens of context ≈ 50MB VRAM (varies by model and quantization).

## Cost Optimization

### Current Pricing (Community Cloud)

| GPU | Cost/hr | VRAM | Best For |
|-----|---------|------|----------|
| RTX 4090 | $0.39 | 24GB | Development, small models |
| RTX 5090 | $0.69 | 32GB | **Recommended** — all models fit |
| A100 80GB | $1.64 | 80GB | Multiple large models simultaneously |
| H100 80GB | $3.89 | 80GB | Maximum throughput |

### Cost-Saving Tips

1. **Stop the pod when not using it**
   ```bash
   runpodctl pod stop 9eusawy77gd1d0   # Stops billing
   runpodctl pod start 9eusawy77gd1d0  # Resume later
   ```
   Volume data persists across stop/start. You only pay when the pod is running.

2. **Use spot/interruptible instances** for batch processing
   - Set `cloudType: COMMUNITY` for lower prices
   - `SECURE` cloud is ~2x more expensive

3. **Right-size your GPU**
   - If only running 8b models → RTX 4090 ($0.39/hr) is sufficient
   - If running 32b models → RTX 5090 ($0.69/hr) is the sweet spot
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

Measured on the current deployment:

| Model | Tokens/sec | First Token (ms) | VRAM Usage |
|-------|-----------|-------------------|------------|
| llama3.1:8b-instruct-q8_0 | 207.6 | ~200 | ~9GB |
| qwen2.5:7b | ~180 | ~250 | ~5GB |
| qwen3:latest (8b) | ~180 | ~250 | ~5GB |
| mxbai-embed-large | N/A | ~50 | ~1GB |

### Extraction Pipeline Performance

| Metric | RTX 4090 (local) | RTX 5090 (RunPod) | Improvement |
|--------|-------------------|-------------------|-------------|
| 8b tok/s | ~120 | ~207 | 1.7x |
| VRAM | 24GB | 32GB | +33% |
| Max concurrent models | 1-2 small | 2-3 small or 1 large + 1 small | Better multi-model |

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

## Quantization Guide

Higher quantization = better quality but more VRAM:

| Quantization | Quality | VRAM (8b model) | Speed |
|-------------|---------|-----------------|-------|
| q4_0 | Acceptable | ~4.5GB | Fastest |
| q4_K_M | Good | ~5GB | Fast |
| q8_0 | Excellent | ~8.5GB | Moderate |
| f16 | Maximum | ~16GB | Slowest |

For ACM extraction, `q8_0` is recommended — it provides near-lossless quality and the RTX 5090 has plenty of VRAM.

---

**Next:** [Maintenance](maintenance.md) — Updates, backups, and pod lifecycle management.
