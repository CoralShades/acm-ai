# E30-S8: Ollama + Anthropic Direct + OpenRouter Provider Priority

**Sprint:** V3-4
**Story Points:** 3
**Risk Level:** MEDIUM
**Type:** backend

## Summary

Implement ACM-namespaced API key isolation and provider priority ordering for the ACM extraction pipeline. The extraction code path must read keys ONLY from `ACM_ANTHROPIC_API_KEY` and `ACM_OPENROUTER_API_KEY` (or DB `model.api_key`), never from bare `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`.

## Acceptance Criteria

- AC0: ACM pipeline reads API keys ONLY from ACM_ANTHROPIC_API_KEY and ACM_OPENROUTER_API_KEY (or DB model.api_key). Bare ANTHROPIC_API_KEY/OPENAI_API_KEY never read by extraction code.
- AC1: Provider priority: 1) Ollama → 2) Anthropic direct → 3) OpenRouter. First available wins.
- AC2: Ollama primary when OLLAMA_API_BASE configured.
- AC3: ChatAnthropic instantiated with api_key from ACM_ANTHROPIC_API_KEY or model.api_key — never bare ANTHROPIC_API_KEY.
- AC4: OpenRouter fallback uses ACM_OPENROUTER_API_KEY or DB key.
- AC5: Model table supports optional api_key field. PATCH /api/models/{id} endpoint for setting/updating key.
- AC6: Tests confirm no bare ANTHROPIC_API_KEY/OPENAI_API_KEY reads in extraction code path.
- AC7: `provision_extraction_fallback_model()` uses new priority order and ACM-namespaced env vars.
- AC8: Broadmeadows 31/31 accuracy maintained (manual verification).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/graphs/utils.py` | MODIFY | Update `provision_extraction_fallback_model()` priority + ACM env vars; update `_verify_provider_routing()` env var |
| `open_notebook/domain/models.py` | MODIFY | Add `api_key: Optional[str]` to Model class; pass api_key in `ModelManager.get_model()` |
| `api/routers/models.py` | MODIFY | Add `PATCH /api/models/{id}` endpoint for api_key update |
| `api/models.py` | MODIFY | Add ModelUpdate Pydantic schema |
| `api/model_provisioning.py` | MODIFY | Update `is_provider_available()` to also check ACM-namespaced env vars |
| `migrations/XX.surrealql` | CREATE | Add api_key column to model table |
| `tests/test_openrouter_provider_routing.py` | MODIFY | Add tests for ACM-namespaced env var isolation and priority ordering |

## Implementation Details

### 1. Model api_key Field

Add `api_key: Optional[str] = None` to Model class. In `ModelManager.get_model()`, pass api_key into AIFactory config:

```python
config = {**kwargs}
if model.api_key:
    config["api_key"] = model.api_key
result = AIFactory.create_language(model_name=routed_name, provider=routed_provider, config=config)
```

### 2. Provider Priority in provision_extraction_fallback_model()

Reorder candidates to: Ollama first → Anthropic (ACM_ANTHROPIC_API_KEY) → OpenRouter (ACM_OPENROUTER_API_KEY). Remove bare ANTHROPIC_API_KEY and OPENAI_API_KEY checks.

### 3. _verify_provider_routing() Update

Change `OPENROUTER_API_KEY` → `ACM_OPENROUTER_API_KEY` for Generation API lookup.

### 4. PATCH /api/models/{id} Endpoint

New endpoint accepting `{ "api_key": "sk-..." }` body, updates model record.

### 5. is_provider_available() ACM Extension

Add ACM-namespaced env var checks alongside bare ones:
- `anthropic`: check `ACM_ANTHROPIC_API_KEY` OR `ANTHROPIC_API_KEY`
- `openrouter`: check `ACM_OPENROUTER_API_KEY` OR `OPENROUTER_API_KEY`

### 6. Migration

```sql
DEFINE FIELD api_key ON TABLE model TYPE option<string>;
```

## Test Plan

1. Unit test: `provision_extraction_fallback_model()` with only ACM_ANTHROPIC_API_KEY set → uses Anthropic
2. Unit test: priority order Ollama → Anthropic → OpenRouter
3. Unit test: bare ANTHROPIC_API_KEY alone → NOT used by extraction fallback
4. Unit test: PATCH /api/models/{id} updates api_key
5. Static analysis test: grep extraction code paths for bare env var reads
