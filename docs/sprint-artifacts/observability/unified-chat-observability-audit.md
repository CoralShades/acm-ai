# Unified Chat Observability Audit

**Date**: 2026-03-22
**Auditor**: Observability Debugger (acm-observability-debugger)
**Scope**: open_notebook/graphs/unified_agent.py and its observability wiring

---

## 1. CopilotKit State Emission

**Status: PASS**

The import at lines 46-51 of unified_agent.py is correctly guarded with a try/except that sets a _HAS_COPILOTKIT flag. If the copilotkit package is not installed the flag is False and the entire emit block is skipped.

The emit inside call_unified_agent (lines 194-210) is non-fatal. The outer except Exception: pass catches any failure during the event loop creation or the copilotkit_emit_state coroutine. Both requirements are satisfied.

One observation: the pattern spins up a new asyncio event loop inside a sync function that may itself run inside _run_in_thread, which already runs in a thread pool with its own event loop. This is safe because _run_in_thread closes its event loop before returning and the emit loop is a separate object. No event loop conflict exists.

---

## 2. Langfuse Tracing Compatibility

**Status: GAP - No Langfuse tracing in the AG-UI path**

### What agui_chat.py does

api/routers/agui_chat.py registers /api/agui/chat by wrapping unified_graph in an ag_ui_langgraph.LangGraphAgent and streaming events via unified_agent.run(input_data). There is no call to langfuse_tracing(), get_langfuse_handler(), merge_langfuse_into_config(), or any Langfuse import anywhere in agui_chat.py.

### How the extraction pipeline traces (reference)

Other routers such as api/routers/chat.py and api/routers/source_chat.py use:

    with langfuse_tracing(chat, source_id=...) as (cb, meta):
        config = merge_langfuse_into_config(base_config, cb, meta)
        graph.invoke(input, config=config)

This injects a CallbackHandler into RunnableConfig.callbacks. Every LLM call during graph execution is reported to Langfuse.

### Why the AG-UI path cannot use the same pattern directly

LangGraphAgent.run(input_data) constructs its own internal RunnableConfig from input_data.config. The endpoint does set recursion_limit on input_data.config (lines 211-216), proving that this field is respected. However there is no mechanism in agui_chat.py to inject a Langfuse CallbackHandler into that config before the agent runs.

### Impact

Chat sessions routed through /api/agui/chat produce zero traces in Langfuse. All LLM calls (model provisioning, tool calls, multi-step reasoning chains) are invisible to Langfuse cost tracking and latency dashboards when LANGFUSE_ENABLED=true.

LangSmith auto-tracing via LANGCHAIN_TRACING_V2=true still works because it operates at the LangChain SDK environment level, independent of RunnableConfig.callbacks.

### Recommendation

Inside unified_chat_endpoint in agui_chat.py, before the async for event loop, inject the Langfuse callback via merge_langfuse_into_config and update input_data.config. The langfuse_tracing context manager from open_notebook/observability/langfuse_config.py handles flush and OTel context attachment automatically.

---

## 3. Logfire Pydantic Instrumentation

**Status: PASS - UnifiedAgentState is a TypedDict, not instrumented**

UnifiedAgentState (lines 62-68 of unified_agent.py) is declared as a typing_extensions.TypedDict. TypedDict classes are not Pydantic BaseModel subclasses. Logfire instrument_pydantic() only instruments BaseModel subclasses; TypedDict classes are ignored regardless of the include= filter.

logfire_config.py confirms that instrument_pydantic() is intentionally not called at init time (lines 59-81). The comment documents the rationale: blanket instrumentation causes approximately 48K traces per run because Docling creates one PdfTextCell per character in the PDF. The selective target list (ACMExtractionRecord, BuildingRoomContext, ACMItemRecord, ACMExtractionResult, ACMItemExtractionResult) covers only extraction-path models and does not include any unified agent types.

The unified agent state will generate no Logfire spans. This is correct and expected behavior.

---

## 4. LangGraph Studio Compatibility

**Status: GAP - unified_agent not registered in langgraph.json**

langgraph.json at the project root currently registers two graphs:

    acm_extraction -> ./open_notebook/graphs/studio_entry.py:graph
    supervisor     -> ./open_notebook/graphs/studio_entry_supervisor.py:graph

The unified_agent graph is not registered. Consequences:
- uv run langgraph dev does not expose the unified graph at 127.0.0.1:2024.
- Thread state for unified chat sessions cannot be inspected via GET /threads/{id}/state in the Swagger UI.
- The graph cannot be invoked or debugged via the LangGraph dev server.

### Missing studio entry file

studio_entry_supervisor.py follows the established pattern: it rebuilds the graph without a checkpointer (Studio provides its own persistence) and exports it as graph. A studio_entry_unified.py counterpart does not exist.

build_unified_graph() in unified_agent.py attaches a SqliteSaver checkpointer. For Studio registration, the graph must be rebuilt without the checkpointer, following the same pattern as studio_entry_supervisor.py.

### Recommendation

Create open_notebook/graphs/studio_entry_unified.py that rebuilds the unified graph topology without calling get_checkpointer() and exports it as graph. Then add to langgraph.json:

    unified_agent: ./open_notebook/graphs/studio_entry_unified.py:graph

---

## 5. Session Checkpointer Isolation

**Status: PASS**

open_notebook/graphs/checkpointer.py derives _UNIFIED_CHECKPOINT_FILE by calling replace on LANGGRAPH_CHECKPOINT_FILE from open_notebook/config.py:

    LANGGRAPH_CHECKPOINT_FILE  = ./data/sqlite-db/checkpoints.sqlite
    _UNIFIED_CHECKPOINT_FILE   = ./data/sqlite-db/unified_chat_checkpoints.sqlite

The two files are physically separate. A SqliteSaver instance on one file has no shared state or connection with the other.

The _checkpointer singleton initializes with sqlite3.connect(..., check_same_thread=False). The check_same_thread=False flag is required for async LangGraph and is correctly set.

### Hardening note (not a current bug)

The string-replace derivation is fragile. If LANGGRAPH_CHECKPOINT_FILE is ever changed to a path that does not contain the substring checkpoints.sqlite, _UNIFIED_CHECKPOINT_FILE would silently equal LANGGRAPH_CHECKPOINT_FILE and the two graphs would share a checkpointer. A safer derivation:

    from pathlib import Path
    _UNIFIED_CHECKPOINT_FILE = str(
        Path(LANGGRAPH_CHECKPOINT_FILE).with_name(unified_chat_checkpoints.sqlite)
    )

---

## Summary Table

| Area | Status | Severity |
|------|--------|----------|
| CopilotKit import guard (_HAS_COPILOTKIT) | PASS | - |
| CopilotKit emit non-fatal (except Exception: pass) | PASS | - |
| Langfuse tracing wired into agui_chat.py | GAP | Medium - chat LLM costs invisible in Langfuse |
| Logfire Pydantic spans from TypedDict state | PASS | - |
| LangGraph Studio registration of unified_agent | GAP | Low - dev debugging only, no production impact |
| Checkpointer isolation (separate SQLite file) | PASS | - |
| Checkpointer derivation robustness | NOTE | Low - fragile string replace, not a current bug |

---

## Files Examined

- open_notebook/graphs/unified_agent.py
- api/routers/agui_chat.py
- open_notebook/observability/langfuse_config.py
- open_notebook/observability/logfire_config.py
- langgraph.json
- open_notebook/graphs/studio_entry.py
- open_notebook/graphs/studio_entry_supervisor.py
- open_notebook/graphs/checkpointer.py
- open_notebook/config.py
