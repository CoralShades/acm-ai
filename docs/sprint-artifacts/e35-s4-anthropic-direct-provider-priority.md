# E35-S4: Anthropic Direct Provider Priority in Primary Path

## Story
**ID**: E35-S4 | **Epic**: E35 | **Sprint**: V3-8 | **Points**: 3 SP | **Risk**: MEDIUM | **Type**: backend

## Summary

Add Ollama->Anthropic Direct->OpenRouter priority chain to the **primary** extraction path (`provision_langchain_model()`), not just the fallback. Currently, the primary path reads a DB-stored default model and fails if that provider is unavailable. The priority chain should activate when `default_type="extraction"` and no explicit `model_id`.

## Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC1 | provision_langchain_model() follows Ollama-Anthropic-OpenRouter when model_type=extraction and no explicit model_id | NEW |
| AC2 | Uses ACM_ANTHROPIC_API_KEY (never bare ANTHROPIC_API_KEY) | Partially done in fallback |
| AC3 | When Ollama unavailable, Anthropic Direct tried next (not OpenRouter) | NEW |
| AC4 | Integration test: OLLAMA_API_BASE unset + ACM_ANTHROPIC_API_KEY set = Anthropic used | NEW |
| AC5 | Existing fallback function remains as secondary safety net | NO CHANGE |
| AC6 | DB-stored model preferences still override when explicitly set | NO CHANGE |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/graphs/utils.py` | MODIFY | Add `_provision_extraction_primary_model()` and call it from `provision_langchain_model()` |
| `tests/test_openrouter_provider_routing.py` | MODIFY | Add `TestExtractionPrimaryProviderPriority` test class |

## Implementation Details

### 1. New function: `_provision_extraction_primary_model()` in utils.py

Add this function near `provision_extraction_fallback_model()` (around line 850). It mirrors the fallback function's priority chain but operates as the **primary** path:

```python
async def _provision_extraction_primary_model(
    **kwargs,
) -> Optional[BaseChatModel]:
    """Primary extraction model provisioning with Ollama->Anthropic->OpenRouter priority.

    E35-S4: When default_type='extraction' and no explicit model_id, use this
    priority chain instead of only reading the DB-stored default. Uses ACM-namespaced
    API keys only (never bare ANTHROPIC_API_KEY).

    Returns None if no provider is available (caller falls through to DB default).
    """
    candidates: list[tuple[str, str, Optional[str]]] = []

    # 1) Ollama first
    if os.getenv("OLLAMA_API_BASE"):
        candidates.append(("ollama", "qwen2.5:7b", None))

    # 2) Anthropic Direct — ACM-namespaced key ONLY
    acm_anthropic_key = os.getenv("ACM_ANTHROPIC_API_KEY")
    if acm_anthropic_key:
        candidates.append(("anthropic", "claude-sonnet-4-20250514", acm_anthropic_key))

    # 3) OpenRouter — ACM-namespaced key ONLY
    acm_openrouter_key = os.getenv("ACM_OPENROUTER_API_KEY")
    if acm_openrouter_key:
        candidates.append(("openrouter", "anthropic/claude-sonnet-4", acm_openrouter_key))

    for provider, model_name, api_key in candidates:
        try:
            config: dict = {**kwargs}
            if api_key:
                config["api_key"] = api_key
            model = AIFactory.create_language(
                model_name=model_name,
                provider=provider,
                config=config,
            )
            assert isinstance(model, LanguageModel)
            lc_model = model.to_langchain()
            lc_model = _apply_openrouter_preferences(lc_model)
            lc_model = _apply_ollama_extraction_settings(lc_model)
            logger.info(f"Primary extraction model: {provider}/{model_name}")
            return lc_model
        except Exception as e:
            logger.warning(f"Primary extraction candidate {provider}/{model_name} failed: {e}")

    return None
```

### 2. Modify `provision_langchain_model()` (line 596-597)

Change the `else` branch:

**Before:**
```python
    else:
        model = await model_manager.get_default_model(default_type, **kwargs)
```

**After:**
```python
    elif default_type == "extraction":
        # E35-S4: Primary extraction priority chain (Ollama -> Anthropic -> OpenRouter)
        lc_model = await _provision_extraction_primary_model(**kwargs)
        if lc_model is not None:
            return lc_model
        # Fall through to DB default if no provider available
        model = await model_manager.get_default_model(default_type, **kwargs)
    else:
        model = await model_manager.get_default_model(default_type, **kwargs)
```

Note: `_provision_extraction_primary_model` returns a `BaseChatModel` (already converted), so we return early. The DB-stored default is only used if no provider in the priority chain is available.

**Important**: When `model_id` is explicitly passed (line 594-595), it still uses the DB-stored model directly — this preserves AC6 (DB overrides).

### 3. Tests: `TestExtractionPrimaryProviderPriority` in test_openrouter_provider_routing.py

Add a new test class at the end of the file. Tests should mock `AIFactory.create_language`, `os.getenv`, and `model_manager.get_default_model`:

1. **`test_ollama_first_when_available`** — OLLAMA_API_BASE set → Ollama model returned, Anthropic/OpenRouter not tried
2. **`test_anthropic_when_ollama_unavailable`** (AC4) — OLLAMA_API_BASE unset + ACM_ANTHROPIC_API_KEY set → Anthropic used
3. **`test_openrouter_when_ollama_and_anthropic_unavailable`** — Only ACM_OPENROUTER_API_KEY set → OpenRouter used
4. **`test_db_default_when_no_provider_available`** — No env vars set → falls through to DB default
5. **`test_uses_acm_key_not_bare`** (AC2) — Verify api_key in config is from ACM_ANTHROPIC_API_KEY, not bare ANTHROPIC_API_KEY
6. **`test_explicit_model_id_bypasses_priority`** (AC6) — When model_id is provided, priority chain is skipped

## Testing

```bash
uv run pytest tests/test_openrouter_provider_routing.py -v -k "TestExtractionPrimary"
uv run ruff check open_notebook/graphs/utils.py tests/test_openrouter_provider_routing.py
```
