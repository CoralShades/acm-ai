# OpenRouter fallback chain non-functional — insufficient credits (HTTP 402)

> **GitHub Issue**: #101
> **Discovered**: 2026-03-05 (E36-S2 browser verification)
> **Findings**: F004, F009
> **Priority**: CONCERN
> **Status**: Open

## Problem

OpenRouter account has insufficient credits, causing HTTP 402 errors when the provider fallback chain reaches OpenRouter. The Ollama → Anthropic Direct → OpenRouter chain is correctly ordered (E35-S5), but the final node is non-functional. Extractions that exhaust Ollama and Anthropic fallbacks fail silently.

## Evidence

```
2026-03-05 00:03 | ERROR | HTTP 402 Payment Required — openrouter/anthropic/claude-sonnet-4
2026-03-05 00:05 | ERROR | HTTP 402 Payment Required — openrouter/anthropic/claude-sonnet-4
2026-03-05 07:05 | ERROR | HTTP 402 Payment Required — openrouter/anthropic/claude-sonnet-4
2026-03-05 07:18 | ERROR | HTTP 402 Payment Required — openrouter/anthropic/claude-sonnet-4
```

4 extraction attempts failed when the fallback chain reached OpenRouter as the final provider.

## Impact

- No working fallback after Ollama and Anthropic Direct both fail
- No automatic notification when credits are exhausted
- Benchmark/production runs can fail silently if they depend on the full fallback chain

## Fix

### 1. Immediate: Top up OpenRouter credits

### 2. Code: Add graceful HTTP 402 handling

```python
# In utils.py:provision_extraction_fallback_model()
try:
    response = await openrouter_call(...)
except OpenRouterError as e:
    if e.status_code == 402:
        logger.error(
            "OpenRouter: Insufficient credits. "
            "Top up at https://openrouter.ai/credits or remove ACM_OPENROUTER_API_KEY"
        )
        raise ProviderExhaustedError("OpenRouter credits exhausted")
```

### 3. Config: Document billing requirement

Add to `.env.example`:
```bash
# OpenRouter requires active billing — HTTP 402 if credits exhausted
ACM_OPENROUTER_API_KEY=sk-or-...
```

## Key Files

- [`open_notebook/graphs/utils.py`](../../open_notebook/graphs/utils.py) — `provision_extraction_fallback_model()` (~line 910)
- [`.env`](../../.env) — `ACM_OPENROUTER_API_KEY` configuration
- [`.env.example`](../../.env.example) — environment variable documentation

## Related

- GitHub Issue: [#101](https://github.com/CoralShades/acm-ai/issues/101)
- Findings: F004, F009 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Evidence: `logs/api-error.log` lines 9-17
