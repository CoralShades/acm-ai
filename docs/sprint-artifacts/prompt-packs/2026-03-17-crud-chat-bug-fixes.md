# Prompt Pack: CRUD Chat Pipeline — Bug Fix (BUG-2 + BUG-4)

**Generated**: 2026-03-17
**Type**: Bug Fix
**Complexity**: 5/10
**Plan Mode**: Yes
**Agent Strategy**: Solo

---

## Prompt

Fix the 2 remaining bugs from E2E testing of the CRUD Chat Pipeline Enhancement. Findings are documented in `docs/sprint-artifacts/e2e-crud-chat/findings.md`.

### BUG-2: AsyncSqliteSaver for Session Persistence

**Symptom**: `NotImplementedError: The SqliteSaver does not support async methods`
**Current workaround**: `MemorySaver()` (in-memory, no persistence across API restarts)
**Root cause**: AG-UI adapter calls `aget_state()` which requires async checkpointer. `SqliteSaver` is sync-only.

**Fix approach**:
1. Read `open_notebook/graphs/crud_agent.py` — currently uses `MemorySaver()`
2. Use `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio` with `aiosqlite`
3. **Key**: `AsyncSqliteSaver.from_conn_string()` returns an async context manager, NOT a saver directly
4. Pattern: Create the saver at module level using a lazy initialization approach:

```python
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE

# Lazy async saver — initialized on first use
_async_saver = None

async def get_async_saver():
    global _async_saver
    if _async_saver is None:
        conn = await aiosqlite.connect(LANGGRAPH_CHECKPOINT_FILE)
        _async_saver = AsyncSqliteSaver(conn)
        await _async_saver.setup()  # Create tables if needed
    return _async_saver
```

5. The graph compile needs a checkpointer at build time — use `MemorySaver` as default, then swap in `agui_chat.py` by calling the graph with `config={"checkpointer": async_saver}`
6. **Alternative simpler approach**: Use `AsyncSqliteSaver(aiosqlite.connect(...))` directly if the constructor accepts a connection factory
7. Verify with Context7: fetch LangGraph docs for `AsyncSqliteSaver` usage patterns
8. Test: restart API, send chat message, verify `thread_id` persists, restart API again, verify conversation restored

### BUG-4: AG-UI Adapter Crashes on execute_write_node Response

**Symptom**: `AttributeError: 'str' object has no attribute 'tool_call_id'` in `ag_ui_langgraph/agent.py:740`
**Root cause**: `execute_write_node` in `crud_agent.py:266` returns `AIMessage(content=result_str)`. The AG-UI LangGraph adapter expects the last message in a step to be either:
- An `AIMessage` with `.tool_calls` (which it then maps to AG-UI tool call events)
- A `ToolMessage` with `.tool_call_id` (which it maps to tool call results)

When `execute_write_node` returns a plain `AIMessage(content=str)` without tool_calls, the adapter tries to treat it as a tool output and crashes.

**Fix approach**:
1. Read `open_notebook/graphs/crud_agent.py` — find `execute_write_node` function
2. The issue is at line 266: `return {"messages": [AIMessage(content=result)]}`
3. **Option A** (preferred): Route the write result back through the `agent` node instead of going directly to END. Change graph:
   - `execute_write` → `agent` → END (instead of `execute_write` → END)
   - The agent node will produce a proper AIMessage with or without tool_calls
   - This also lets the LLM provide a natural language confirmation
4. **Option B**: Keep the current topology but ensure the message format is AG-UI compatible:
   - Parse the JSON result and create an AIMessage with the confirmation text
   - The adapter should handle a plain AIMessage without tool_calls as a text message
   - The bug might be that the adapter sees a `ToolMessage` in the message history from a previous step and tries to correlate it
5. **Debug first**: Add logging in `execute_write_node` to see exactly what messages are in state when the error occurs
6. Check `ag_ui_langgraph` source at `.venv/Lib/site-packages/ag_ui_langgraph/agent.py:740` to understand what triggers the `tool_call_id` access
7. Test: send write request → approve → verify green success card appears in chat

### Key Files

| File | Role |
|------|------|
| `open_notebook/graphs/crud_agent.py` | Graph definition, execute_write_node, checkpointer |
| `api/routers/agui_chat.py` | AG-UI endpoint, thread_id injection |
| `open_notebook/config.py` | LANGGRAPH_CHECKPOINT_FILE path |
| `.venv/Lib/site-packages/ag_ui_langgraph/agent.py` | AG-UI adapter (read-only, understand the error) |
| `docs/sprint-artifacts/e2e-crud-chat/findings.md` | Bug details and symptoms |

### Glossary

| Term | Definition |
|------|-----------|
| AG-UI | Agent-UI protocol — SSE event stream between LangGraph and CopilotKit |
| HITL | Human-in-the-loop — structural barrier requiring user approval for writes |
| AsyncSqliteSaver | Async-compatible LangGraph checkpointer using aiosqlite |
| MemorySaver | In-memory LangGraph checkpointer (no persistence) |
| execute_write_node | Graph node that executes approved writes (bypasses LLM) |
| ToolMessage | LangChain message type for tool call results with tool_call_id |
| EventEncoder | AG-UI encoder that serializes Pydantic events to SSE format |

### Skills to Load
- `/copilotkit` — CopilotKit AG-UI integration patterns
- Context7: `langgraph` — AsyncSqliteSaver, checkpointer patterns
- Context7: `copilotkit` — AG-UI protocol, tool call rendering

### Verification Checklist

**BUG-2 (AsyncSqliteSaver)**:
- [ ] `uv run python -c "from open_notebook.graphs.crud_agent import crud_graph; print(type(crud_graph.checkpointer))"` — shows AsyncSqliteSaver
- [ ] API starts without errors
- [ ] Send chat message → response streams correctly
- [ ] Restart API → same thread_id → conversation history restored
- [ ] `uv run pytest tests/test_crud_tools_v2.py tests/test_crud_tools_enhanced.py -x` — all pass

**BUG-4 (AG-UI write response)**:
- [ ] Send write request ("change risk_status to High on record X")
- [ ] HITL dialog renders with Approve/Reject
- [ ] Click Approve → no SSE stream error
- [ ] Green success card appears: "Updated risk_status on record X to 'High'"
- [ ] `tail /tmp/api-e2e.log | grep ERROR` — no errors
- [ ] `cd frontend && npm run build` — 0 TypeScript errors

---

*Generated by /generate-prompt for CRUD Chat Pipeline Bug Fix session*
