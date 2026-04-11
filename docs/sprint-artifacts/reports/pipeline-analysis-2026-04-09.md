# Pipeline Analysis Report — 2026-04-09

## Service Status

| Service | URL | Status | Notes |
|---------|-----|--------|-------|
| LangGraph Dev Server | http://127.0.0.1:2024 | **RUNNING** | Swagger UI + graph API live |
| Langfuse (self-hosted) | http://localhost:3000 | **RUNNING** | Loading UI confirmed, API returning traces |
| LangSmith (cloud) | smith.langchain.com | **CONFIGURED** | LANGCHAIN_TRACING_V2=true, API key set |
| Logfire | N/A | **DISABLED** | LOGFIRE_ENABLED=false (intentional) |

---

## LangGraph Analysis

### Graph Definitions

Two graphs registered with the LangGraph dev server:

| Graph | Assistant ID | Created | Status |
|-------|-------------|---------|--------|
| `unified_agent` | cbfb957b-5863-5f6b-88e6-791818fd4bd0 | 2026-04-09 (today) | Active |
| `acm_extraction` | a8416622-a8d4-58f4-bdd7-0236e1506d35 | 2026-04-05 | Active |

**ACM Extraction Graph Topology** (`open_notebook/graphs/acm_extraction.py:3033`):

```
START → metadata_and_structure (S4: 1 LLM call)
      → inventory (S17: 1 LLM call, synthesizes page_tags)
      → save_intelligence (E30-S9: persist pre-extraction data)
      → schema_inference (MCS2: multi-consultant format detection)
      → extract_building (E32-S1: Building__c phase 1)
      → extract_items (E32-S2: Item__c phase 2)
      → normalize_to_sf
      → validate
      → [conditional] should_correct → {correct → validate (loop) | deduplicate}
      → recover_no_access
      → save
      → END
```

**Unified Agent Graph** (`open_notebook/graphs/unified_agent.py:14`):
```
START → agent_node (all tools bound)
      ├─ tool_calls? → tools_node → check_pending → approval_node (interrupt) → agent_node
      ├─ tool_calls? → tools_node → check_pending → agent_node (no pending)
      └─ no tool_calls → END
```

### Thread State

- **Total threads found**: 1 (thread ID: `d7f0756d-92cf-44e1-852c-ffa67e954393`)
- **Thread status**: `idle`, created 2026-03-31, values: `{}` (empty — graph completed)
- **No pending runs or interrupts found**
- **Note**: LangGraph threads are created per-chat session; 1 thread is expected for dev usage

### Issues Found

1. **`unified_agent` created today** — fresh restart of LangGraph dev server wiped prior state (expected behavior for MemorySaver — sessions are ephemeral in dev mode)
2. **No production checkpointer**: The `unified_agent` uses `MemorySaver` (in-memory). Per `checkpointer.py`, upgrade to `SqliteSaver` is planned but not yet done. Sessions do NOT persist across restarts.
3. **Hardcoded fallback model IDs** (lines 994–998 in `acm_extraction.py`): When Ollama extraction fails, the code falls back to hardcoded model strings:
   - `"anthropic/claude-sonnet-4-20250514"` (direct Anthropic)
   - `"openrouter/anthropic/claude-sonnet-4"` (OpenRouter)
   - `"openai/gpt-4o-mini"` (direct OpenAI)
   
   **Risk**: This fallback chain includes direct Anthropic/OpenAI API keys which are NOT configured in `.env` (per MEMORY.md: system uses OpenRouter only). If Ollama fails during a large extraction, the cloud fallback will silently fail, causing the extraction to error out without a useful error message.

---

## Langfuse Analysis

### Trace Summary

- **Total traces in Langfuse**: 243,743 (large historical accumulation since system setup)
- **Most recent extraction traces**: 2026-04-05 (AlexanderHospital.pdf)
- **Today's traces**: 1 (empty trace from 11:43 AM — likely initialization artifact)
- **Date range confirmed active**: 2026-03-17 to 2026-04-09

### Trace Quality

**Observations per extraction trace** (from trace `71dbaddd`): 20 observations captured:
- `CHAIN` type: `save`, `recover_no_access`, `deduplicate`, `should_correct`, `validate`
- `GENERATION` type: 5+ `ChatOllama` LLM calls (model: `llama3.1:8b`)

The graph nodes are being traced correctly via LangChain callbacks.

### Cost Analysis

- **All traces show `totalCost: 0`** — This is **expected** because the system is running Ollama locally (`llama3.1:8b`). Ollama has no API cost, so Langfuse correctly reports $0.
- **Cost tracking would only activate** if OpenRouter or direct Anthropic/OpenAI models were used

### Metadata Issues Found

The `build_langfuse_metadata()` function in `langfuse_config.py` is called in `extract_acm_from_source()` (line 3110) **without** the `document_type` parameter:

```python
langfuse_metadata = build_langfuse_metadata(
    source_id=source_id_str,
    extraction_model=model_id,
    command_id=command_id,
    # Missing: document_type=...
)
```

**Result**: All extraction traces show:
- `document_type: "unknown"` (default value)
- `extraction_model: "default"` (model_id is None at call time; actual model resolved later in the graph)
- `service.name: "unknown_service"` (OTel attribute — Logfire service_name not applied when Logfire is disabled)

### Empty Trace from Today

Trace `97941b891d37eaed5761f20b37ddca41` (2026-04-09T11:43:05) has:
- No name, no input, no output
- Likely a Langfuse SDK initialization event or abandoned trace from a test

### Issues Found

1. **`document_type` always "unknown"** — metadata doesn't reflect the actual document type extracted during the pipeline run. Reduces Langfuse filter/search utility.
2. **`extraction_model` shows "default"** — model_id isn't resolved at trace creation time (it's resolved later inside graph nodes). Trace metadata doesn't show which model was actually used.
3. **243K trace count** — Large accumulation; Langfuse UI may become slow. Periodic cleanup recommended (`/trace-cleanup` command available).
4. **service.name = "unknown_service"** — OTel service identification not configured when Logfire is disabled.
5. **Empty/unnamed trace today** — Minor artifact, non-critical.

---

## LangSmith Configuration

### Status

| Setting | Value | Status |
|---------|-------|--------|
| `LANGCHAIN_TRACING_V2` | `true` | **ENABLED** |
| `LANGCHAIN_API_KEY` | `lsv2_pt_...` (set) | **CONFIGURED** |
| `LANGSMITH_PROJECT` | `ACM-AI` | **CONFIGURED** |
| `LANGCHAIN_ENDPOINT` | (not set — uses default) | Default cloud endpoint |

### Notes

- LangSmith is auto-tracing all LangChain/LangGraph calls via env vars (zero code changes needed)
- This means **both** Langfuse AND LangSmith receive all graph traces simultaneously
- LangSmith traces useful for prompt playground and side-by-side comparison
- No issues found with LangSmith configuration

---

## Code Review Findings

### Potential Issues

#### 1. Silent Fallback Failures — Cloud Model Fallback (HIGH)
**File**: `open_notebook/graphs/acm_extraction.py`, lines 987–998

When Ollama extraction fails, the code tries cloud models in this order:
```python
cloud_model_id = "anthropic/claude-sonnet-4-20250514"  # direct Anthropic
# or
cloud_model_id = "openrouter/anthropic/claude-sonnet-4"  # OpenRouter
# or  
cloud_model_id = "openai/gpt-4o-mini"  # direct OpenAI
```
The system uses OpenRouter only (no `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`). If Ollama fails, the cloud fallback will fail with an authentication error. The error is logged but may be confusing.

#### 2. Broad Exception Handling Masks Errors (MEDIUM)
**File**: `open_notebook/graphs/acm_extraction.py`, lines 426, 532, 1129

Nodes like `metadata_and_structure_node` and `compile_inventory` catch all exceptions and return empty dicts:
```python
except Exception as e:
    logger.warning(f"Combined metadata+structure extraction failed: {e}")
    return {"document_metadata": None, "document_structure": None}
```
While intentionally non-fatal, these silent returns mean downstream nodes operate without critical pre-extraction context. The pipeline continues but extraction quality degrades silently.

#### 3. No Persistent Checkpointer for Chat Sessions (MEDIUM)
**File**: `open_notebook/graphs/unified_agent.py`

`unified_agent` uses `MemorySaver` (in-memory). Chat sessions are lost on every LangGraph dev server restart. The comment "upgrade to SqliteSaver planned" suggests this is a known gap.

#### 4. Langfuse Trace Metadata Not Updated Post-Extraction (LOW)
**File**: `open_notebook/graphs/acm_extraction.py`, line 3108–3114

`document_type` and the actual model ID are known after the pipeline runs but are never written back to the Langfuse trace. The `update_trace=True` flag on the `CallbackHandler` should allow this, but no code performs the update.

#### 5. Empty State Thread in LangGraph (INFO)
Thread `d7f0756d` from 2026-03-31 has `values: {}`. This is normal for a completed graph run but indicates the checkpoint data was lost (MemorySaver cleared on restart). Not an error.

### Configuration Gaps

| Gap | Impact | Recommendation |
|-----|--------|---------------|
| `document_type` not passed to `build_langfuse_metadata()` | Trace metadata always shows "unknown" | Pass `document_type` after structure extraction |
| `model_id` not resolved before trace creation | Trace metadata shows "default" | Use model ID from DB lookup before starting graph |
| LOGFIRE_ENABLED=false | Pydantic validation spans not captured | Enable selectively if debugging validation failures |
| MemorySaver for unified_agent | Chat sessions ephemeral in dev | Upgrade to SqliteSaver for dev persistence |
| 243K+ trace accumulation | Langfuse UI performance | Schedule periodic trace cleanup |

---

## Recommendations

### Priority 1 — HIGH
1. **Document the cloud fallback gap**: The Ollama-to-cloud fallback uses hardcoded model IDs that won't work in the current config (OpenRouter-only). Add a clear log message noting which provider/key is missing when fallback fails, rather than letting it fail silently with an auth error.

### Priority 2 — MEDIUM  
2. **Upgrade unified_agent to SqliteSaver**: Replace `MemorySaver` with `SqliteSaver` for persistent chat sessions across server restarts. This is already noted as planned.
3. **Improve Langfuse trace metadata**: Pass `document_type` from the extracted structure back into the trace. Use `pipeline_version` field to distinguish Ollama vs cloud runs.

### Priority 3 — LOW
4. **Langfuse trace cleanup**: Run `/trace-cleanup` to remove old traces and keep Langfuse UI responsive. The 243K total is a large accumulation from development history.
5. **Enable Logfire selectively**: When debugging specific Pydantic validation failures, enable `LOGFIRE_ENABLED=true` + selective `instrument_pydantic(include={...})` per the observability rules — do NOT use blanket instrumentation.
6. **Set service name in OTel**: Add `OTEL_SERVICE_NAME=acm-ai` to `.env` so OTel traces identify the service correctly even when Logfire is disabled.

---

## Summary

| Component | Health | Key Finding |
|-----------|--------|-------------|
| LangGraph Dev Server | ✅ Healthy | Two graphs registered, no failed threads |
| acm_extraction graph | ✅ Healthy | Complete 11-node pipeline with corrective RAG loop |
| unified_agent graph | ✅ Healthy | Chat agent with HITL interrupt support |
| Langfuse | ✅ Healthy | LLM calls captured, cost $0 (expected for Ollama) |
| LangSmith | ✅ Configured | Auto-tracing all graph invocations |
| Logfire | ℹ️ Disabled | Intentionally off; enable only for debugging |
| Cloud fallback | ⚠️ Risk | Fallback model IDs hardcoded for APIs not configured |
| Trace metadata | ⚠️ Gap | document_type/model not populated in Langfuse traces |
| Chat persistence | ⚠️ Gap | MemorySaver loses sessions on restart |
