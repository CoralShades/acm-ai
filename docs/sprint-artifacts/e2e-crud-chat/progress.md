# E2E CRUD Chat — Progress Journal

## Session 1: 2026-03-17

### Status: E2E TESTING COMPLETE (Phase 1)

### Test Results Summary
| Test | Status | Notes |
|------|--------|-------|
| P0.1 Services | PASS | SurrealDB, API, Worker, Frontend all running |
| P0.2 Migration 53 | PASS | Applied: record_id, field_name, old_value, new_value on crud_audit |
| P0.3 Test data | PASS | source:7ltfu81qzc06yuae1h0s — 90 records, 6 buildings |
| P0.4 Chat panel | PASS | CopilotKit CRUD chat loads, model selector works |
| T1.1 Schema info | PASS | LLM used surreal_query + listed all 25 editable fields with enums |
| T1.2 Analytics query | PASS | QueryResultsTable with GROUP BY risk_status, SQL disclosure |
| T1.6 HITL preview | PASS | HITLApprovalDialog rendered: UPDATE, field, value, Approve/Reject |
| T1.7 Write execute | PASS | Approval sent, DB write executed, SSE stream stays open (BUG-4 fixed 2026-03-20) |
| T1.11 Guardrail | PASS | "drop table" refused by LLM without attempting any tool call |

### Bugs Found & Fixed (3 fixed, 1 known)
1. **FIXED** Migration 53 `option<any>` → `TYPE any` (SurrealDB parse error)
2. **FIXED** SqliteSaver → MemorySaver (AG-UI needs async checkpointer)
3. **FIXED** EventEncoder missing in agui_chat.py (Pydantic events not SSE-serializable)
4. **FIXED** AG-UI adapter crashes on execute_write_node AIMessage response (BUG-4) — fixed 2026-03-20

### Evidence Screenshots
- P0-chat-panel-loaded.png
- T1.1-schema-info.png
- T1.2-analytics-query.png
- T1.6-record-ids.png
- T1.6-hitl-dialog.png
- T1.7-write-result.png
- T1.7-write-complete.png
- T1.11-guardrail-block.png

### Files Modified During E2E (bug fixes)
- `migrations/53.surrealql` — TYPE any instead of option<any>
- `migrations/53_down.surrealql` — matching down migration
- `open_notebook/graphs/crud_agent.py` — MemorySaver + removed sqlite3 import
- `api/routers/agui_chat.py` — EventEncoder for SSE serialization

### Key Architectural Findings
- Thread persistence works: `thread_id=crud_source_7ltfu81qzc06yuae1h0s` confirmed in SSE stream
- Intent classification works: route_entry correctly routes to agent vs execute_write
- All 7 tools registered in system prompt and available to LLM
- Claude Sonnet 4 reliably selects correct tools based on user intent
- CopilotKit tool renderers (QueryResultsTable, HITLApprovalDialog) render correctly

### Next Steps for Full Coverage
- ~~Fix BUG-4: execute_write_node needs to return ToolMessage for AG-UI compatibility~~ DONE 2026-03-20
- Test ChatMiniGrid with larger result sets (>5 rows)
- Test ChatChoiceCard with ask_user_choice
- Test undo_last_write flow
- Test preview_bulk_write flow
- Implement AsyncSqliteSaver for true session persistence

## Session 2: 2026-03-20 — BUG-4 Fix

### Status: BUG-4 RESOLVED

### Root Cause
`execute_write_node` returns `AIMessage(content=result)` into LangGraph state. The AG-UI
adapter emits `StateSnapshotEvent` with raw `BaseMessage` objects in its `snapshot: Any` field.
`EventEncoder.encode()` calls `model_dump_json()` which fails with `PydanticSerializationError`
on the non-serializable `BaseMessage` objects, killing the SSE stream.

A secondary crash vector: `langchain_messages_to_agui()` inside the adapter's
`_handle_stream_events` raising during `MessagesSnapshotEvent` construction — this crashes
the async generator before the custom endpoint can intercept it.

### Fix: 3-Layer Defense in `api/routers/agui_chat.py`
1. **Event-level**: `_sanitize_state_snapshot` (existing, strengthened) + `_sanitize_messages_snapshot` (new) — converts raw `BaseMessage` objects to AGUI dicts before encoding
2. **Encode-level**: `_safe_encode` (new) — wraps `encoder.encode()` with try/except, falls back to `make_json_safe` → `json.dumps` if Pydantic serialization fails
3. **Generator-level**: `try/except` around `crud_agent.run()` (new) — catches exceptions from inside the adapter, emits `RunErrorEvent` instead of killing SSE stream

### Test Results
| Test | Status | Notes |
|------|--------|-------|
| T1.7 Write execute | PASS | 3-layer defense prevents SSE crash |
| 14 new unit tests | PASS | `tests/test_agui_chat_sanitize.py` |
| 70 existing CRUD tests | PASS | No regressions |
| Frontend build | PASS | No TS errors |
| Ruff lint | PASS | Clean |

### Files Modified
- `api/routers/agui_chat.py` — Added `_sanitize_messages_snapshot`, `_safe_encode`, generator-level error handler
- `tests/test_agui_chat_sanitize.py` — NEW: 14 regression tests for BUG-4
