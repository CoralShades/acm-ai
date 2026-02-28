# Findings — E27-S3: Hard-Lock OpenRouter Provider Routing

## Root Cause Analysis

### Problem
OpenRouter activity logs show extraction requests being served by BOTH Anthropic and Google Vertex providers during the same extraction run. After E27-S1 eliminated `with_structured_output()`, Vertex no longer errors on `anthropic-beta` headers, so it silently succeeds as fallback — with different extraction behavior.

### Current Code (utils.py:22-100)
- `OPENROUTER_IGNORED_PROVIDERS = ["Amazon Bedrock", "Azure"]` — Vertex NOT blocked
- `OPENROUTER_PROVIDER_ORDER = ["Anthropic", "Google", "OpenAI"]` — **soft preference**, not a hard lock
- `_apply_openrouter_preferences()` uses `provider.ignore` + `provider.order` (both soft routing)
- For Anthropic models, adds Google to ignore list — but this is conditional on model name detection

### Why Soft Routing Fails
Per OpenRouter docs: `provider.order` is a PREFERENCE list. When the preferred provider is rate-limited, slow, or temporarily unavailable, OpenRouter CAN and DOES fall back to unlisted providers. `provider.ignore` only blocks listed providers — any unlisted provider is fair game.

## Call Sites Analysis

`_apply_openrouter_preferences()` is called from exactly 2 locations:
1. `utils.py:134` — inside `provision_langchain_model()` (main path for ALL extraction stages)
2. `utils.py:413` — inside `provision_extraction_fallback_model()` (fallback path)

All extraction stages go through `provision_langchain_model()`:
- `document_structure.py:136` → `provision_langchain_model()` (line 136)
- `building_inventory.py:470` → `provision_langchain_model()` (line 470)
- `page_tagger.py:348` → `provision_langchain_model()` (line 348)
- `orchestrator.py:501` → via `_llm_extract_building()` → `provision_langchain_model()`
- `acm_extraction.py:1209` → `provision_langchain_model()` (main extract_records)
- `acm_extraction.py:2003` → `provision_langchain_model()` (correction path)

**Good news**: ALL extraction paths flow through a single chokepoint (`provision_langchain_model` → `_apply_openrouter_preferences`). We only need to change `_apply_openrouter_preferences()` and the constants.

## OpenRouter Feature Analysis

| Feature | Status | Effort | Impact |
|---------|--------|--------|--------|
| `provider.only` + `allow_fallbacks=false` | **CRITICAL** | Low | Eliminates Vertex fallback |
| Response Healing plugin | SHOULD-HAVE | Low | Auto-fix malformed JSON, free, <1ms |
| ZDR (Zero Data Retention) | SHOULD-HAVE | Low | Government data compliance |
| `data_collection: "deny"` | SHOULD-HAVE | Low | Don't train on government data |
| `require_parameters: true` | Already present | None | Keep existing |
| Request metadata | NICE-TO-HAVE | Medium | Production observability |
| Generation API verification | NICE-TO-HAVE | Medium | Definitive provider logging |
| App Attribution headers | NICE-TO-HAVE | Low | Dashboard visibility |
| Prompt caching (`cache_control`) | EXPERIMENTAL | Medium | Cost savings, may not pass through LangChain |

## Deep Merge Concern

Current code (utils.py:83-94) does a SHALLOW merge:
```python
prev_extra = existing.get("extra_body", {})
object.__setattr__(lc_model, "model_kwargs", {**existing, "extra_body": {**prev_extra, **openrouter_body}})
```

This overwrites `provider` dict entirely if one already exists. Need proper deep merge for `provider` dict and `plugins` array (append, don't replace).

## Esperanto/LangChain Header Injection

Models are constructed by Esperanto (`AIFactory.create_language()`) then converted to LangChain (`model.to_langchain()`). The LangChain `ChatOpenAI` class supports `default_headers` in the constructor, but since Esperanto creates the model, we can't easily inject headers at construction time.

**Alternative**: App Attribution headers (`HTTP-Referer`, `X-OpenRouter-Title`) can go in `extra_body` — BUT OpenRouter docs say these should be HTTP headers, not body fields. If `model_kwargs` can include `default_headers`, that works. Otherwise, skip app attribution headers for now (metadata covers observability).

**Decision**: Include app attribution via `default_headers` injection through `model_kwargs` if LangChain supports it. Otherwise, the `metadata` field in `extra_body` handles observability.

## LLM Call Sites for Provider Verification

Each extraction stage calls `model.ainvoke(messages)`:
- `document_structure.py:152` — single call
- `building_inventory.py:486` — single call
- `page_tagger.py:363` — per-batch call (multiple per document)
- `orchestrator.py:534` (inside `_invoke()`) — per-building call
- `acm_extraction.py:1287` — main extraction call
- `acm_extraction.py:2025` — correction call

Provider verification after ainvoke() would be ideal but requires the function to be importable and the response to contain gen_id. This is NON-CRITICAL — if it fails, extraction continues.

## Prompt Caching Compatibility

LangChain `SystemMessage` accepts `content` as either a string or a list of content blocks. To use Anthropic prompt caching, the content must be a list with `cache_control` on each block:
```python
SystemMessage(content=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}])
```

**Risk**: LangChain/Esperanto may strip unknown fields like `cache_control`. This is a SHOULD-HAVE — log TODO if it doesn't work.
