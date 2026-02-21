# E1-S31: Expand AI Model Catalog & Update Default Assignments

## Story Info
- **Epic**: E1 — ACM Data Extraction Pipeline
- **Status**: done
- **Priority**: P1
- **Size**: S (Small)
- **Created**: 2026-02-22
- **Completed**: 2026-02-22

## Description

Expand the model catalog to support 40+ models across multiple providers (Anthropic, OpenAI, Ollama, OpenRouter) and update default assignments to use free-tier OpenRouter models and local Ollama models optimized for RTX 4090 24GB.

## Acceptance Criteria

- [x] `.env` updated with free-tier OpenRouter defaults and Ollama embedding model
- [x] `_PROVIDER_DEFAULTS` expanded to cover Qwen3 variants, DeepSeek, Gemma, Phi, Kimi K2, MiniMax M2, GLM-5, and more
- [x] `_EMBEDDING_DEFAULTS` expanded to cover Qwen3 Embedding, Gemini, Mistral, BGE models
- [x] `FALLBACK_MODELS` updated with free-tier OpenRouter fallbacks and Ollama local models
- [x] Capability detection (`supports_structured_output`, `supports_tool_calling`) expanded for all new model families
- [x] `MODEL_CATALOG` seeds 40+ models on startup for available providers
- [x] `update_defaults_if_needed()` respects env var changes on restart
- [x] Route ordering fixed (static before parametric) in `api/routers/models.py`
- [x] `GET /models/{model_id}` endpoint added

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/domain/models.py` | MODIFIED | Expanded `_PROVIDER_DEFAULTS` (11→45 entries) and `_EMBEDDING_DEFAULTS` (5→15 entries) |
| `api/model_provisioning.py` | MODIFIED | Added `MODEL_CATALOG` + `seed_model_catalog()`, fixed `update_defaults_if_needed()`, restructured `run_model_provisioning()` |
| `api/routers/models.py` | MODIFIED | Route reorder (static before parametric) + added `GET /models/{model_id}` |
| `.env` | MODIFIED | Updated `DEFAULT_*_MODEL` vars to free-tier OpenRouter + Ollama models |

## Technical Notes

- No database migrations needed — capability fields exist from E1-S28 (migration 20)
- `parse_model_env()` splits on first `/` only, so `openrouter/qwen/qwen3-next-80b-a3b-instruct:free` correctly gives `provider="openrouter"`, `name="qwen/qwen3-next-80b-a3b-instruct:free"`
- Default embedding model stays `ollama/mxbai-embed-large` (1024-dim) matching SurrealDB MTREE vector index
- `update_defaults_if_needed()` now compares current default against provisioned model_id — env var changes take effect on restart
- `seed_model_catalog()` runs before default assignment, ensuring all provider models exist in DB regardless of `DEFAULT_*_MODEL` env vars
- Tool calling excludes `gemma-3` and `phi4` (unreliable at the OpenRouter routing layer)
