# Findings: Multi-Provider Audit (2026-02-23)

## Files Read
- open_notebook/domain/models.py — Model class, _PROVIDER_DEFAULTS, get_context_window(), get_max_output_tokens(), AIFactory calls
- api/model_provisioning.py — MODEL_CATALOG, parse_model_env(), capability detection, FALLBACK_MODELS
- open_notebook/graphs/utils.py — provision_langchain_model, supports_tool_calling, parse_json_response, TOOL_CALLING_BLOCKLIST
- open_notebook/graphs/acm_extraction.py — extract_records, _is_qwen_model, _chunk_content, with_structured_output, fallback
- .env.example — all env vars documented
- esperanto providers: openrouter.py, ollama.py, base.py, timeout.py, openai.py
- migrations/12.surrealql — MTREE 1024-dimension index
- tests/test_broadmeadows_e2e.py — direct ChatOpenAI/ChatAnthropic usage

## Critical Gaps Found

### TK-1 FAIL: Chunk size ignores model context window
- _chunk_content(processed_content) at acm_extraction.py:1007 passes no model arg
- DEFAULT_CONTEXT_WINDOW = 128000 always used (line 79)
- Token threshold = 64000 regardless of actual model context window

### OR-7 PARTIAL: deepseek marked as supports_tool_calling=True
- api/model_provisioning.py:240 includes "deepseek" in tool_calling list
- utils.py TOOL_CALLING_BLOCKLIST (line 102) only has ["qwen2.5", "phi4", "gemma-3"]
- deepseek models go through with_structured_output() which may fail silently

### OR-5 PARTIAL: Multiple required OpenRouter models absent
Missing from MODEL_CATALOG:
- anthropic/claude-3-5-haiku-20241022
- anthropic/claude-sonnet-4-5 (only claude-sonnet-4.6 present)
- openai/gpt-4o
- openai/gpt-4o-mini
- deepseek/deepseek-chat
- qwen/qwen-2.5-72b-instruct

### EH-2 FAIL: No 429 rate-limit retry
- OpenRouter 429 caught as generic Exception (acm_extraction.py:1279)
- Retried 3x with 1,2,4s backoff — grossly inadequate for rate limits
- No exponential backoff with 60s+ waits specific to rate limiting

### EH-4 FAIL: No simpler prompt fallback
- After JSON fallback fails and MAX_RETRIES hit, pipeline returns error dict
- No prompt simplification or token reduction strategy

### OL-5 PARTIAL: MTREE index hardcoded to 1024 dims
- migrations/12.surrealql:15: DIMENSION 1024
- nomic-embed-text produces 768-dim vectors — silent index mismatch if used

### OL-2 PARTIAL: Ollama provider-available check uses wrong env var
- api/model_provisioning.py:61: checks OLLAMA_API_BASE only
- Esperanto ollama.py:46 also accepts OLLAMA_BASE_URL
- If user sets OLLAMA_BASE_URL but not OLLAMA_API_BASE, provider is skipped
