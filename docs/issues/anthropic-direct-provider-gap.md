# Anthropic Direct Provider — Primary Path Routing Gap

> **GitHub Issue**: #94
> **Discovered**: 2026-03-05 (E30-S8 verification)
> **Story**: E35-S4 (Sprint V3-8)
> **Priority**: P0
> **Status**: Open

## Problem

The Anthropic Direct provider path was never tested end-to-end during V3 implementation. When Ollama is unavailable, the system falls through to OpenRouter (which returned 402 — no credits) instead of trying Anthropic Direct.

## Root Cause

`provision_extraction_fallback_model()` (utils.py:~851) implements the Ollama→Anthropic→OpenRouter chain, but it's a **fallback function** — only called when the primary model fails with specific schema/auth errors.

The primary extraction path uses `provision_langchain_model()` with `default_extraction_model` from in-memory settings. When Ollama was disabled:

1. System used DB-stored default (an OpenRouter model)
2. OpenRouter returned 402 (no credits)
3. 402 is not a schema/auth error → fallback chain not triggered
4. Anthropic Direct was never reached

## Architecture Gap

```
Current flow:
  provision_langchain_model(default_extraction_model)
    → OpenRouter model (from DB) → 402 → FAIL (no fallback triggered)

Expected flow:
  provision_langchain_model(model_type="extraction")
    → Try Ollama (if available) → Try Anthropic Direct → Try OpenRouter
```

## Fix (E35-S4)

`provision_langchain_model()` itself should implement the Ollama→Anthropic→OpenRouter priority chain for `model_type="extraction"` when no explicit model_id is provided. The existing `provision_extraction_fallback_model()` remains as a secondary safety net.

## Key Requirements

1. Uses `ACM_ANTHROPIC_API_KEY` (never bare `ANTHROPIC_API_KEY`)
2. When Ollama unavailable, Anthropic Direct tried next (not OpenRouter)
3. DB-stored model preferences still override when explicitly set
4. Integration test: `OLLAMA_API_BASE` unset + `ACM_ANTHROPIC_API_KEY` set → Anthropic used

## Key Files

| File | Change |
|------|--------|
| `open_notebook/graphs/utils.py` | `provision_langchain_model()` — add extraction priority chain |
| `api/model_provisioning.py` | May need updates for provider priority |
| `tests/test_openrouter_provider_routing.py` | Integration tests |

## Related

- E30-S8 (Ollama + Anthropic Direct + OpenRouter Provider Priority) — implemented fallback function
- E35-S3 (Ollama Extraction Hardening) — dependency, must complete first
