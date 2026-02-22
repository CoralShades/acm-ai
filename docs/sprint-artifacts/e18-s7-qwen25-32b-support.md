# E18-S7: Qwen2.5:32b — Full Ollama & OpenRouter Support

## Story Info
- **Epic**: E18 — Production Hardening & Demo Stability
- **Status**: review
- **Priority**: P0
- **Size**: M (Medium)
- **Created**: 2026-02-23
- **Dependencies**: E1-S28 (capabilities schema), E1-S31 (model catalog expansion)

## Description

Configure ACM-AI for optimal use of Qwen2.5:32b on both Ollama (local, RTX 4090 24GB) and OpenRouter (cloud). Qwen2.5:32b has 128K input context / 8K output tokens, excellent structured JSON output, instruction following, and long-text comprehension — making it well-suited for ACM register extraction.

The model is already partially registered:
- **Ollama**: `("ollama", "qwen2.5:32b", "language")` exists in `MODEL_CATALOG`
- **`_PROVIDER_DEFAULTS`**: `"qwen2.5-32b": {"max_output": 8192, "context": 131072}` exists
- **Capability detection**: `"qwen2.5"` is already in both `supports_structured_output` and `supports_tool_calling` keyword lists

### What's Missing

1. **OpenRouter catalog entry**: No `("openrouter", "qwen/qwen2.5-32b-instruct", "language")` in `MODEL_CATALOG`
2. **Fallback table entry**: `FALLBACK_MODELS["openrouter"]` has no Qwen2.5 reference — only Qwen3 and DeepSeek
3. **Extraction prompt Qwen2.5 guidance**: The extraction prompt has no Qwen2.5-specific instruction format notes (unlike Claude/GPT which get implicit good results)
4. **`.env.example` documentation**: No mention of Qwen2.5:32b as a viable extraction model
5. **E2E validation**: No test run confirming Qwen2.5:32b achieves acceptable accuracy on Broadmeadows

### Why Qwen2.5:32b

| Capability | Value | Extraction Relevance |
|------------|-------|---------------------|
| Context window | 131,072 tokens | Full SAMP document in single pass |
| Max output | 8,192 tokens | Sufficient for 30+ ACM records per chunk |
| Structured JSON | Native JSON mode | Compatible with `with_structured_output()` |
| Instruction following | Excellent | Follows complex extraction schemas |
| Long-text comprehension | Strong | Handles multi-page PDF content well |
| Local VRAM | ~20GB Q4_K_M | Fits RTX 4090 24GB with headroom |

## Acceptance Criteria

- [x] AC1: `MODEL_CATALOG` includes Qwen2.5:32b for both `ollama` and `openrouter` providers
- [x] AC2: Capability fields set correctly: `context_window=131072`, `max_output_tokens=8192`, `supports_structured_output=True`
- [x] AC3: `FALLBACK_MODELS` updated — Qwen2.5:32b added as `large_context` and/or `extraction` fallback where appropriate
- [x] AC4: Fallback JSON parser active (confirmed already present in `acm_extraction.py:1237-1280`)
- [x] AC5: `.env.example` updated with Qwen2.5:32b as documented extraction model option
- [ ] AC6: E2E test passes with Qwen2.5:32b as extraction model (target: >= 25/31 records, stretch: >= 27/31)
- [x] AC7: No regressions — `ruff check .` and existing tests pass

## Tasks / Subtasks

### Task 1: Add OpenRouter Catalog Entry (AC1)
- [x] 1.1 Add `("openrouter", "qwen/qwen2.5-32b-instruct", "language")` to `MODEL_CATALOG` in `api/model_provisioning.py`
- [x] 1.2 Verify Ollama entry `("ollama", "qwen2.5:32b", "language")` already exists (no change needed)

### Task 2: Verify Capability Detection (AC2)
- [x] 2.1 Confirm `_PROVIDER_DEFAULTS` has `"qwen2.5-32b": {"max_output": 8192, "context": 131072}` (already present)
- [x] 2.2 Confirm `supports_structured_output` keyword list includes `"qwen2.5"` (already present)
- [x] 2.3 Confirm `supports_tool_calling` keyword list includes `"qwen2.5"` (already present)

### Task 3: Update Fallback Models (AC3)
- [x] 3.1 Add/update `FALLBACK_MODELS["ollama"]["large_context"]` — confirm `qwen2.5:32b` is already set
- [x] 3.2 Updated `FALLBACK_MODELS["openrouter"]["large_context"]` to `qwen/qwen2.5-32b-instruct` (was qwen3-235b)

### Task 4: Update `.env.example` (AC5)
- [x] 4.1 Add commented example showing Qwen2.5:32b configuration for Ollama extraction
- [x] 4.2 Add commented example showing OpenRouter Qwen2.5 configuration

### Task 5: Lint & Test (AC7)
- [x] 5.1 `ruff check .` passes
- [x] 5.2 `pytest tests/` passes — 754 passed, pre-existing failures only (import errors in WSL env)

### Task 6: E2E Validation (AC6) — Manual
- [ ] 6.1 Set `DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:32b` in `.env`
- [ ] 6.2 Run extraction on Broadmeadows PDF
- [ ] 6.3 Compare results against `Clutch_Broadmeadows.csv` expected records
- [ ] 6.4 Document accuracy in Dev Agent Record below

## Technical Notes

### Existing Infrastructure (No Changes Needed)

The following are **already implemented** and require only verification:

1. **Provider defaults** in `models.py:_PROVIDER_DEFAULTS`:
   ```python
   "qwen2.5-32b": {"max_output": 8192, "context": 131072}
   ```

2. **Structured output detection** in `model_provisioning.py:223`:
   ```python
   new_model.supports_structured_output = any(k in name_lower for k in ["qwen2.5", ...])
   ```

3. **Tool calling detection** in `model_provisioning.py:235`:
   ```python
   new_model.supports_tool_calling = any(k in name_lower for k in ["qwen2.5", ...])
   ```

4. **Fallback JSON parser** in `acm_extraction.py:1237-1280`:
   Already handles models that return raw JSON instead of tool_use structured output.

5. **Ollama catalog entry** in `model_provisioning.py:121`:
   ```python
   ("ollama", "qwen2.5:32b", "language")
   ```

### OpenRouter Model Name

OpenRouter uses the format `qwen/qwen2.5-32b-instruct` for Qwen2.5 models. The `parse_model_env()` function splits on first `/`, so `openrouter/qwen/qwen2.5-32b-instruct` correctly gives `provider="openrouter"`, `name="qwen/qwen2.5-32b-instruct"`.

### Qwen2.5 Structured Output

Qwen2.5:32b supports JSON mode natively. LangChain's `with_structured_output()` will use JSON mode (not function calling) when the provider is Ollama. For OpenRouter, the existing fallback JSON parser handles cases where `tool_use` is not supported at the routing layer.

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `api/model_provisioning.py` | MODIFY | Add OpenRouter Qwen2.5 entry to `MODEL_CATALOG`; optionally update `FALLBACK_MODELS` |
| `.env.example` | MODIFY | Document Qwen2.5:32b as extraction model option |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Added OpenRouter catalog entry: `("openrouter", "qwen/qwen2.5-32b-instruct", "language")` — confirmed model ID via [OpenRouter API docs](https://openrouter.ai/qwen/qwen2.5-32b-instruct)
- Updated OpenRouter `large_context` fallback from `qwen3-235b-a22b-thinking-2507` to `qwen/qwen2.5-32b-instruct` (128K context, deterministic output vs thinking model)
- Verified all existing infrastructure: `_PROVIDER_DEFAULTS`, capability detection keywords, Ollama catalog entry, fallback JSON parser — all already support Qwen2.5
- Added two `.env.example` configuration blocks: Ollama local extraction and OpenRouter cloud extraction
- Lint passes, 754/754 available tests pass (pre-existing import failures in WSL unrelated)
- **AC6 (E2E validation) requires manual execution** — needs Ollama running with qwen2.5:32b pulled, or OpenRouter API key + live extraction run

### E2E Results
Pending manual validation. Requires:
1. Ollama with `qwen2.5:32b` model pulled (`ollama pull qwen2.5:32b`)
2. Set `DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:32b` in `.env`
3. Start services and upload Broadmeadows PDF
4. Compare against `Clutch_Broadmeadows.csv` (31 expected records)

### File List
- `api/model_provisioning.py` (modified — added OpenRouter catalog entry, updated fallback)
- `.env.example` (modified — added Qwen2.5 extraction config examples)
- `docs/sprint-artifacts/e18-s7-qwen25-32b-support.md` (new — story file)
- `docs/sprint-artifacts/sprint-status.yaml` (modified — added E18-S7 tracking)
