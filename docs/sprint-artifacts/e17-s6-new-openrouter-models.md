# E17-S6: New OpenRouter Model Additions

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: ready-for-dev
- **Priority**: P1
- **Size**: S (Small)
- **Created**: 2026-02-22
- **Dependencies**: None
- **Blocks**: None

## Description

Add 6 new frontier models to the model catalog: MiniMax M2.1, Kimi K2.5, DeepSeek V3.2, Claude Sonnet 4.6, GPT 5.2, and Gemini 2.5 Pro.

## Acceptance Criteria

- [ ] 6 new models in `MODEL_CATALOG`
- [ ] `_PROVIDER_DEFAULTS` entries for each with correct context_window/max_output
- [ ] `supports_structured_output` and `supports_tool_calling` detection updated
- [ ] `seed_model_catalog()` creates them on startup when `OPENROUTER_API_KEY` set

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `api/model_provisioning.py` | MODIFY | Add 6 entries to MODEL_CATALOG; update capability detection |
| `open_notebook/domain/models.py` | MODIFY | Add 6 entries to _PROVIDER_DEFAULTS |

## Models to Add

| Model | OpenRouter ID | Context | Price (in/out $/M) |
|-------|--------------|---------|-------------------|
| MiniMax M2.1 | minimax/minimax-m2.1 | 196K | $0.27/$0.95 |
| Kimi K2.5 | moonshotai/kimi-k2.5 | 262K | $0.23/$3.00 |
| DeepSeek V3.2 | deepseek/deepseek-v3.2 | 163K | $0.26/$0.38 |
| Claude Sonnet 4.6 | anthropic/claude-sonnet-4.6 | 1M | $3/$15 |
| GPT 5.2 | openai/gpt-5.2 | 400K | $1.75/$14 |
| Gemini 2.5 Pro | google/gemini-2.5-pro | 1M | $1.25/$10 |
