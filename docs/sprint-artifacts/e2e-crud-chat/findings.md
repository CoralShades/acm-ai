# E2E CRUD Chat — Findings Log

## Research & Discovery

### Services Required
- SurrealDB on port 8000 (Docker)
- API on port 5055 (uvicorn)
- Worker (background)
- Frontend on port 8503 (Next.js)

### Test Data Requirements
- Need at least one source with extracted ACM records
- Source must have building_record and acm_record entries
- crud_audit table must have migration 53 fields

### CopilotKit Integration Points
- CRUD chat uses CopilotKit at `/copilot-crud` runtime URL
- Tool renderers registered via `useRenderToolCall` hooks
- AG-UI endpoint at `/api/agui/crud-chat`

### Observability
- Langfuse traces via `langfuse_tracing()` context manager
- LangGraph checkpoints in SQLite at `data/checkpoints.sqlite`
- crud_audit in SurrealDB stores all write operations

## Bugs Found & Fixed

### BUG-1: SurrealDB `option<any>` type not supported
- **Symptom**: Migration 53 fails with `Parse error: Unexpected token ANY`
- **Root cause**: SurrealDB doesn't have `option<any>` type. `any` type already accepts NONE.
- **Fix**: Changed `TYPE option<any>` → `TYPE any` in migration 53

### BUG-2: SqliteSaver doesn't support async
- **Symptom**: `NotImplementedError: The SqliteSaver does not support async methods`
- **Root cause**: AG-UI adapter calls `aget_state()` which is async. SqliteSaver is sync-only.
- **Fix**: Reverted to `MemorySaver()` (in-memory, not persistent across restarts)
- **TODO**: For production, use `AsyncSqliteSaver` with proper `async with` context management

### BUG-3: EventEncoder missing in agui_chat.py custom endpoint
- **Symptom**: `AttributeError: 'RunStartedEvent' object has no attribute 'encode'`
- **Root cause**: StreamingResponse was passed raw AG-UI Pydantic objects instead of SSE-encoded strings
- **Fix**: Added `EventEncoder` to serialize events before streaming

### BUG-4: AG-UI adapter crashes on structural HITL write execution
- **Symptom**: `AttributeError: 'str' object has no attribute 'tool_call_id'` in ag_ui_langgraph agent.py:740
- **Root cause**: `execute_write_node` returns `AIMessage(content=result_str)` (plain text). AG-UI adapter expects tool_call output objects with `.tool_call_id` attribute
- **Impact**: Write executes in SurrealDB but SSE stream breaks — client sees incomplete response
- **Workaround**: The DB write succeeds despite the SSE error. User can verify by querying the record
- **Fix needed**: Return proper ToolMessage instead of AIMessage from execute_write_node, or wrap in AG-UI compatible format
