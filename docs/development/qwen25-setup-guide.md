# Qwen2.5:32b Setup Guide — ACM-AI

## Overview

Qwen2.5:32b-Instruct is the recommended local model for ACM extraction on hardware
with 24GB VRAM (RTX 4090, RTX 3090, A10). It provides:

- **128k context window** — fits entire SAMP document in one pass
- **8k output tokens** — sufficient for 31+ ACM records as JSON
- **Strong instruction following** for structured JSON generation
- **Excellent table/register comprehension**

> **How it works in ACM-AI:** Qwen2.5 is on the `TOOL_CALLING_BLOCKLIST` in
> `open_notebook/graphs/utils.py`, which means the extraction pipeline automatically
> bypasses LangChain's `with_structured_output()` and uses **direct JSON mode** with
> brace-depth parsing via `parse_json_response()`. No special configuration needed —
> the pipeline detects Qwen2.5 and adapts automatically.

---

## Option A: Ollama (Local, Recommended)

### Prerequisites

- **Ollama** installed: <https://ollama.ai/download>
- **24GB VRAM GPU** (Q4_K_M quantization) OR **20GB VRAM** (Q3_K_M)
- ~20GB disk space

### Installation

```bash
# Pull the model (Q4_K_M quantization — best quality/size tradeoff for 24GB)
ollama pull qwen2.5:32b

# Verify it runs
ollama run qwen2.5:32b "Extract the building name from: Building B00A - Admin Block"

# Check model info (confirm context window)
ollama show qwen2.5:32b --modelfile
```

### Configure ACM-AI

Add to your `.env`:

```env
DEFAULT_CHAT_MODEL=ollama/qwen3:14b
DEFAULT_TRANSFORMATION_MODEL=ollama/qwen3:32b
DEFAULT_TOOLS_MODEL=ollama/qwen3:32b
DEFAULT_LARGE_CONTEXT_MODEL=ollama/qwen2.5:32b
DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:32b
DEFAULT_EMBEDDING_MODEL=ollama/mxbai-embed-large
OLLAMA_API_BASE=http://localhost:11434
```

> **Note:** `DEFAULT_CHAT_MODEL` and `DEFAULT_TOOLS_MODEL` use Qwen3 (which supports
> tool calling). Only extraction and large-context use Qwen2.5.

### Docker-based Ollama (Alternative)

If you prefer running Ollama in Docker:

```bash
# GPU-enabled (requires NVIDIA Container Toolkit)
docker compose --profile ollama-gpu up -d

# CPU-only (slower, but works on any machine)
docker compose --profile ollama-cpu up -d

# Pull the model inside the container
docker exec acm-ai-ollama ollama pull qwen2.5:32b
```

Then set in `.env`:
```env
OLLAMA_API_BASE=http://ollama:11434
```

### Verify Extraction Quality

```bash
# Run the E2E extraction test with Qwen2.5
uv run pytest tests/test_broadmeadows_e2e.py -m integration -v -s

# Target: >= 27/31 records (87%)
```

---

## Option B: OpenRouter (Cloud, No GPU Required)

### Prerequisites

- **OpenRouter account**: <https://openrouter.ai>
- API key with credits

### Configure ACM-AI

Add to your `.env`:

```env
OPENROUTER_API_KEY=sk-or-...
DEFAULT_EXTRACTION_MODEL=openrouter/qwen/qwen2.5-32b-instruct
DEFAULT_LARGE_CONTEXT_MODEL=openrouter/qwen/qwen2.5-32b-instruct
```

> **Tip:** You can mix providers — use OpenRouter for extraction and Ollama for
> chat/embeddings to minimize cloud costs.

### OpenRouter Model Selection Guide

For ACM extraction, prefer models with confirmed JSON mode support:

| Model | OpenRouter ID | Context | Cost (in/out per M tokens) | Structured Output |
|-------|---------------|---------|---------------------------|-------------------|
| **Qwen2.5 32B Instruct** | `qwen/qwen2.5-32b-instruct` | 128k | ~$0.07 / $0.16 | JSON mode |
| Qwen2.5 72B Instruct | `qwen/qwen2.5-72b-instruct` | 128k | ~$0.14 / $0.30 | JSON mode |
| DeepSeek V3 | `deepseek/deepseek-chat` | 163k | ~$0.27 / $1.10 | JSON mode |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` | 128k | ~$0.12 / $0.30 | Function calling |
| Qwen3 235B A22B | `qwen/qwen3-235b-a22b` | 262k | ~$0.20 / $0.60 | Function calling |

> **Cost estimate:** A typical Broadmeadows SAMP PDF (~45k tokens input, ~4k output)
> costs approximately **$0.004** per extraction on Qwen2.5 32B via OpenRouter.

---

## How the Pipeline Handles Qwen2.5

Understanding the extraction path helps with debugging:

```
1. Model provisioned via Esperanto → LangChain wrapper
2. supports_tool_calling() checks TOOL_CALLING_BLOCKLIST
   → Qwen2.5 matched → returns False
3. Pipeline skips with_structured_output()
4. Uses direct ainvoke() with JSON-instructed prompt
5. parse_json_response() extracts JSON via brace-depth matching
6. ACMRecord Pydantic validation on each extracted record
```

Key files:
- `open_notebook/graphs/utils.py` — `supports_tool_calling()`, `parse_json_response()`
- `open_notebook/graphs/acm_extraction.py` — extraction pipeline with Qwen2.5 path
- `api/model_provisioning.py` — model catalog and fallback chain
- `open_notebook/domain/models.py` — `_PROVIDER_DEFAULTS` with Qwen2.5 specs

---

## Troubleshooting

### Model not reachable

```
Error: Could not connect to Ollama at http://localhost:11434
```

- Verify Ollama is running: `ollama list`
- Check the URL in `.env` matches your Ollama instance
- For Docker: ensure the container is up: `docker ps | grep ollama`

### Out of VRAM

```
Error: CUDA out of memory
```

- Try a smaller quantization: `ollama pull qwen2.5:32b-q3_K_M`
- Or use the 14B variant: `ollama pull qwen2.5:14b`
- Check VRAM usage: `nvidia-smi`

### Low extraction accuracy (< 25/31)

1. Verify the model is actually being used (check API logs for model name)
2. Ensure `DEFAULT_EXTRACTION_MODEL` is set correctly in `.env`
3. Restart the API after `.env` changes: models are provisioned at startup
4. Check if `_preprocess_samp_format()` normalizations are active (product vocabulary)

### OpenRouter rate limits

- OpenRouter may rate-limit free-tier models
- Add credits to your account for higher rate limits
- Check `OPENROUTER_API_KEY` is valid: `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models`

---

## Verification Checklist

Run the automated verification after setup:

```bash
uv run python scripts/verify_model_setup.py --model ollama/qwen2.5:32b

# Or for OpenRouter:
uv run python scripts/verify_model_setup.py --model openrouter/qwen/qwen2.5-32b-instruct
```

Expected output:
```
[PASS] Model reachable
[PASS] Context window: 131072 tokens
[PASS] JSON mode: supported
[PASS] Sample extraction: 5+ records from test chunk
[PASS] Token count estimate for Broadmeadows PDF: ~45,000 tokens (fits in one pass)
```

---

## Performance Benchmarks

| Setup | Extraction Time | Records | Accuracy |
|-------|----------------|---------|----------|
| Ollama Qwen2.5:32b (RTX 4090) | ~60-90s | 27-31/31 | 87-100% |
| OpenRouter Qwen2.5:32b | ~30-45s | 27-31/31 | 87-100% |
| Ollama Qwen2.5:14b (RTX 3060) | ~45-60s | 22-27/31 | 71-87% |
| OpenRouter DeepSeek V3 | ~20-30s | 25-29/31 | 81-94% |

> Benchmarks are approximate and depend on LLM non-determinism, network latency,
> and GPU thermal throttling.
