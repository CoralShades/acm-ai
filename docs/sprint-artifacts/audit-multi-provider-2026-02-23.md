# Multi-Provider Audit Report — ACM-AI

*Winston, System Architect · 2026-02-23 · No code changed, report only*

---

## OPENROUTER PROVIDER

**OR-1** ✅ PASS — Esperanto's `openrouter.py:24–26` reads `OPENROUTER_BASE_URL` or defaults to `"https://openrouter.ai/api/v1"`. The base_url is passed directly to `ChatOpenAI(base_url=...)` in `to_langchain()` at line 231.

**OR-2** ✅ PASS — Esperanto's `openai.py:56` sets `"Authorization": f"Bearer {self.api_key}"`. `api_key` is read from `OPENROUTER_API_KEY` at `openrouter.py:27`. The key is also passed to `ChatOpenAI(api_key=...)` at `to_langchain():230`.

**OR-3** ✅ PASS — Two places set this header:
- Direct HTTP calls: `openrouter.py:41–44` — `_get_headers()` adds `"HTTP-Referer"` and `"X-Title"`
- LangChain path: `to_langchain():235–238` — `default_headers={"HTTP-Referer": ..., "X-Title": ...}`

**OR-4** ✅ PASS — `api/model_provisioning.py:38`:
```python
parts = env_value.split("/", 1)   # maxsplit=1 — correct
```
`"openrouter/anthropic/claude-3-5-haiku"` → `provider="openrouter"`, `name="anthropic/claude-3-5-haiku"`.

**OR-5** ⚠️ PARTIAL — The following required models are **absent** from `MODEL_CATALOG` (disregarding `:free` models as instructed):

| Required | Present? |
|---|---|
| `openrouter` + `anthropic/claude-3-5-haiku-20241022` | ❌ Missing |
| `openrouter` + `anthropic/claude-sonnet-4-5` / `claude-3-5-sonnet` | ❌ Missing (`claude-sonnet-4.6` is there but different) |
| `openrouter` + `openai/gpt-4o` | ❌ Missing |
| `openrouter` + `openai/gpt-4o-mini` | ❌ Missing |
| `openrouter` + `deepseek/deepseek-chat` | ❌ Missing (only `deepseek-r1`, `deepseek-v3`, `deepseek-v3.2`) |
| `openrouter` + `deepseek/deepseek-r1` | ✅ Present |
| `openrouter` + `qwen/qwen2.5-32b-instruct` | ✅ Present |
| `openrouter` + `qwen/qwen2.5-72b-instruct` | ❌ Missing |
| `openrouter` + `meta-llama/llama-3.3-70b-instruct` | ✅ Present |

Also: `.env.example:156` documents `openrouter/anthropic/claude-3.5-sonnet` but that name does not exist in the catalog; and line 180 shows wrong Anthropic model ID format (`claude-haiku-3-5-20241022` instead of `claude-3-5-haiku-20241022`).

**OR-6** ✅ PASS — `api/model_provisioning.py:236–246`. `"claude"` matches anthropic/*, `"gpt-4"` / `"gpt-5"` matches openai/*, `"llama-3"` matches `meta-llama/llama-3.3-70b-instruct` — all correctly set `supports_tool_calling=True`.

**OR-7** ⚠️ PARTIAL
- qwen/* (qwen2.5 variants): ✅ Correctly False — `"qwen2.5"` not in the tool-calling allowlist; also blocked by `utils.py:102` `TOOL_CALLING_BLOCKLIST`
- qwen3 models: Marked `True` (via `"qwen3"` in allowlist) — acceptable since Qwen3 does support function calling
- deepseek/* models: ❌ **Incorrectly True** — `"deepseek"` appears at `api/model_provisioning.py:240` in the `supports_tool_calling` allowlist. The audit requires these to be `False`. Additionally, `TOOL_CALLING_BLOCKLIST` in `utils.py:102` does NOT include `"deepseek"`, so at inference time deepseek models will attempt `with_structured_output()` instead of JSON mode. This is a silent correctness risk.

**OR-8** ✅ PASS — `acm_extraction.py:1283–1351`: when `with_structured_output()` fails, the pipeline falls back to `model.ainvoke(messages)` + `parse_json_response()`.

**OR-9** ✅ PASS — `open_notebook/graphs/utils.py:117–124`:
```python
json_match = re.search(r"```(?:json)?\s*
?(\{.*?\})\s*
?```", ...)
```
Handles fenced ```json blocks, then falls back to brace-depth matching.

**OR-10** ✅ PASS — `_PROVIDER_DEFAULTS` in `models.py:32–96` has correct per-family values (e.g. claude-3-5-haiku=8192, gpt-4o=16384, deepseek-r1=32768). One gap: `"deepseek-chat"` is not a key in `_PROVIDER_DEFAULTS` so if deepseek-chat were added to the catalog it would fall through to the `128000` `get_context_window()` fallback.

---

## OLLAMA PROVIDER

**OL-1** ✅ PASS — `esperanto/providers/llm/ollama.py:46`:
```python
self.base_url = self.base_url or os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_API_BASE") or "http://localhost:11434"
```
Both env var names accepted; passed through to `ChatOllama(base_url=...)` in `to_langchain():290`.

**OL-2** ⚠️ PARTIAL — Esperanto accepts both `OLLAMA_BASE_URL` and `OLLAMA_API_BASE`. However, `api/model_provisioning.py:61` checks **only** `OLLAMA_API_BASE` to determine whether Ollama is available:
```python
"ollama": lambda: os.getenv("OLLAMA_API_BASE") is not None,
```
A user who sets `OLLAMA_BASE_URL` (Esperanto-native) would have models instantiated correctly but **Ollama would not be seeded in the catalog** and would not appear in the UI. Same discrepancy in `api/routers/models.py:220`.

**OL-3** ✅ PASS — `MODEL_CATALOG:122` has `("ollama", "qwen2.5:32b", "language")`. `_PROVIDER_DEFAULTS` key `"qwen2.5:32b"` maps to `context=131072, max_output=8192`. These are correct for the Ollama quantised variant.

**OL-4** ✅ PASS — `"qwen2.5:32b"` does not match any key in the `supports_tool_calling` allowlist (`models.py:236–246`). It is also explicitly in `TOOL_CALLING_BLOCKLIST` (`utils.py:102`). Double protection: provisioned as `False` AND blocked at inference time.

**OL-5** ⚠️ PARTIAL — Four Ollama embedding models are in the catalog:

| Model | Dimensions |
|---|---|
| `mxbai-embed-large` | 1024 |
| `nomic-embed-text` | 768 |
| `bge-m3` | 1024 |
| `bge-large` | 1024 |

`migrations/12.surrealql:15` defines the ACM record MTREE index as **`DIMENSION 1024` hardcoded**. If a user switches the default embedding model to `nomic-embed-text` (768d), the SurrealDB MTREE index will silently produce wrong similarity scores or error on insertion. No dimension validation exists at embedding time.

---

## PROVIDER ISOLATION

**ISO-1** ✅ PASS — Each provider reads its own env vars within Esperanto dataclass instances. `ModelManager.get_model()` calls `AIFactory.create_language(provider=..., model_name=..., config=kwargs)`. Setting `DEFAULT_CHAT_MODEL=ollama/qwen2.5:32b` and `DEFAULT_EXTRACTION_MODEL=openrouter/anthropic/claude-sonnet-4.6` would create two separate Esperanto instances with no shared state.

**ISO-2** ✅ PASS — OpenRouter's `FALLBACK_MODELS` has `"embedding": None` (`model_provisioning.py:109`). Embedding is always routed to Ollama (or OpenAI if configured). No code path sends embeddings through OpenRouter.

**ISO-3** ✅ PASS — No module-level singleton holds API keys. `model_manager` (`models.py:327`) is a stateless `ModelManager` instance with no cached key material. Each `AIFactory.create_*()` call constructs a fresh Esperanto dataclass that reads env vars at construction time.

---

## CHUNKING & TOKEN MANAGEMENT

**TK-1** ❌ FAIL — `acm_extraction.py:1007`:
```python
chunks = _chunk_content(processed_content)  # no model arg passed
```
`_chunk_content()` signature at line 522: `def _chunk_content(content, context_window=DEFAULT_CONTEXT_WINDOW)`. `DEFAULT_CONTEXT_WINDOW = 128000` (line 79). The model's actual context window (`Model.get_context_window()`) is **never consulted for chunking**.

Consequence: a model with a smaller context window (e.g. 32K) would receive oversized chunks. For Claude with 200K context, documents are chunked more than necessary, adding unnecessary round-trips.

**TK-2** ⚠️ PARTIAL — Hardcoded literal token values found:
- `acm_extraction.py:79` — `DEFAULT_CONTEXT_WINDOW = 128000` (never overridden with model's real window)
- `acm_extraction.py:1087` — `_max_tokens = 16384` (safe fallback; only used if model lookup fails — acceptable)
- `acm_extraction.py:1839` — `max_tokens=1024` (correction node — likely intentional small output)
- `acm_extraction.py:2434` — `context_window=DEFAULT_CONTEXT_WINDOW` in `TokenLimitValidator` (same hardcoding issue)
- `open_notebook/graphs/utils.py:25` — `if tokens > 105_000:` (hardcoded large-context switch threshold)

**TK-3** ⚠️ PARTIAL — `acm_extraction.py:1092` does call `_domain_model.get_max_output_tokens(fallback=16384)` dynamically for `max_tokens`. But `get_context_window()` is never called for chunk sizing. Max output tokens is dynamic; chunk threshold is not.

---

## ERROR HANDLING

**EH-1** ⚠️ PARTIAL — OpenRouter 401 propagates as `RuntimeError("OpenAI API error: ...")` from `openrouter.py:55`. In `acm_extraction.py:1279`, it is caught by `except (ValidationError, Exception) as e:` and logged only as `logger.warning(f"Structured output {error_type} failed: {e}")`. After all retries the user sees `"Extraction extraction failed after 3 retries"` — **the 401 is buried, not clearly surfaced as a credentials problem.**

**EH-2** ❌ FAIL — No 429-specific handling exists anywhere in the stack. OpenRouter 429 would:
1. Raise `RuntimeError` in Esperanto
2. Be caught as a generic extraction exception at `acm_extraction.py:1279`
3. Trigger the JSON fallback path (which also 429s)
4. Trigger up to MAX_RETRIES=3 retries with delays of [1, 2, 4] seconds

Rate limit recovery typically requires 30–120 second waits. The current 1/2/4s backoff is useless for 429s. No `Retry-After` header is read.

**EH-3** ⚠️ PARTIAL — Esperanto's default `ESPERANTO_LLM_TIMEOUT=60s` (`timeout.py:9`). An unreachable Ollama would hang for 60 seconds per attempt, then retry 3 times = up to ~3 minutes of silent hanging. The error when it finally surfaces is an `httpx.ConnectError` or `RuntimeError("Ollama API error: ...")` — not a clear "Ollama unreachable, check OLLAMA_API_BASE". The `.env.example` documents `ESPERANTO_LLM_TIMEOUT` for tuning.

**EH-4** ❌ FAIL — `acm_extraction.py:1355–1371`: after the JSON fallback fails, the pipeline increments `retry_count` and retries the **same prompt with the same model** up to `MAX_RETRIES=3`. There is no:
- Reduced-complexity prompt retry
- Token limit reduction strategy
- Model family detection that adjusts the prompt template on retry

---

## PRIORITISED GAP LIST

### P0 — Blocks extraction or causes silent data loss

| ID | Issue | Location |
|---|---|---|
| **TK-1** | Chunk size ignores model context window — oversized chunks sent to small-context models | `acm_extraction.py:1007`, `_chunk_content():522` |
| **OR-7** | `deepseek/*` provisioned as `supports_tool_calling=True` + not in BLOCKLIST → `with_structured_output()` fails silently, JSON mode not used | `model_provisioning.py:240`, `utils.py:102` |
| **EH-2** | No 429 / rate-limit retry — extraction aborts after 7 seconds total backoff | Nowhere in stack |

### P1 — Wrong results silently / wrong behaviour at runtime

| ID | Issue | Location |
|---|---|---|
| **OL-5** | MTREE index hardcoded to 1024 dims — `nomic-embed-text` (768d) corrupts semantic search | `migrations/12.surrealql:15` |
| **EH-1** | 401 bad-API-key errors buried in generic extraction failure message | `acm_extraction.py:1279` |
| **OL-2** | `OLLAMA_BASE_URL` accepted by Esperanto but ignored by provisioning — Ollama invisible in catalog | `model_provisioning.py:61`, `routers/models.py:220` |
| **TK-2** | `TokenLimitValidator` and large-context switch threshold also hardcode `128000` | `acm_extraction.py:2434`, `utils.py:25` |

### P2 — Missing models / config gaps

| ID | Issue | Location |
|---|---|---|
| **OR-5a** | 6 models absent from `MODEL_CATALOG` for OpenRouter: `anthropic/claude-3-5-haiku-20241022`, `claude-sonnet-4-5`, `openai/gpt-4o`, `gpt-4o-mini`, `deepseek/deepseek-chat`, `qwen/qwen2.5-72b-instruct` | `model_provisioning.py:115–173` |
| **OR-5b** | `.env.example:156` documents `claude-3.5-sonnet` (wrong name); line 180 has wrong ID order `claude-haiku-3-5-20241022` | `.env.example:156,180` |
| **EH-4** | No simpler-prompt retry on structured output failure — same prompt repeated 3× | `acm_extraction.py:1355–1371` |

### P3 — Nice-to-have / observability

| ID | Issue | Location |
|---|---|---|
| **EH-3** | Ollama unreachable hangs 60s × 3 retries; raw `httpx` error text shown, not user-friendly | Esperanto timeout defaults |
| **TK-3** | `get_context_window()` exists and is populated — not wired to `_chunk_content()` | `acm_extraction.py:1007` |
| **OR-10** | `deepseek-chat` absent from `_PROVIDER_DEFAULTS` — falls through to 128K fallback if added | `models.py:_PROVIDER_DEFAULTS` |
| **E2E test** | `test_broadmeadows_e2e.py` bypasses Esperanto entirely, uses raw `ChatOpenAI`/`ChatAnthropic` — does not exercise production provisioning path | `tests/test_broadmeadows_e2e.py:233–248` |
