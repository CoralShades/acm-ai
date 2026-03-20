# BUG-4: CRUD HITL AG-UI Adapter AIMessage Crash Fix
# Date: 2026-03-20 | SP: 3 | Priority: P0
# Blocks: Full CRUD write flow in JobCrudChatPanel

## Context

BUG-4 was identified during CRUD chat E2E testing (2026-03-17). The AG-UI adapter
crashes when `execute_write_node` emits an `AIMessage` during the HITL approval flow.

**Symptom**: User approves a write operation in the HITLApprovalDialog → backend
sends AIMessage from execute_write_node → AG-UI adapter throws exception →
SSE stream dies → user sees no confirmation, write may or may not have completed.

**Known state (from sprint-status.yaml):**
- T01 PASS: /jobs/{id}/chat page loads
- T03 PASS: surreal_query count queries work
- T04 PASS: buildings query returns data
- T10 PARTIAL: backend interrupt PASS, frontend HITL dialog blocked by BUG-4
- T15-T16 PASS: SSE streaming works

---

## Skills to Load

/systematic-debugging — root-cause before touching code
/langgraph-human-in-the-loop — interrupt() patterns, resume flow
/sse-streaming — AG-UI SSE event encoding
/acm-observability — Langfuse trace to see where crash occurs
/verification-before-completion — re-run T10 after fix

---

## Root Cause Investigation

### Step 1: Find the crash site

The AG-UI adapter in this project converts LangGraph events to AG-UI protocol events.
When `execute_write_node` finishes, it returns an `AIMessage`. The adapter must handle this.

Read these files to understand the current state:
- `api/routers/agui_chat.py` — AG-UI endpoint, event streaming loop
- `open_notebook/graphs/crud_agent.py` — `execute_write_node`, what it returns
- `api/models.py` — `EventEncoder` or similar SSE encoder

Look for:
```python
# The crash is likely here — AIMessage not handled in the event loop
async for event in graph.astream_events(...):
    if isinstance(event, AIMessage):  # <-- missing branch?
        ...
```

### Step 2: Understand what execute_write_node emits

```python
# In crud_agent.py — find execute_write_node
# What does it add to state? AIMessage? ToolMessage?
# Does it use copilotkit_emit_state() before returning?
```

### Step 3: Check the AG-UI event encoder

```python
# In agui_chat.py — find the event streaming loop
# What event types are handled?
# Is AIMessage from execute_write_node serialized correctly?
# Does EventEncoder handle all LangChain message types?
```

---

## Key Files

**Read and understand:**
- `api/routers/agui_chat.py` — CRUD chat SSE endpoint (lines with `astream_events`)
- `open_notebook/graphs/crud_agent.py` — `execute_write_node`, `check_write_approval_node`
- `open_notebook/graphs/supervisor_agent.py` — how AG-UI events are dispatched

**Likely modify:**
- `api/routers/agui_chat.py` — add AIMessage handling in event loop
- OR `open_notebook/graphs/crud_agent.py` — change what execute_write_node emits

**Do not modify:**
- `open_notebook/graphs/guardrails.py` — HITL barrier (security-critical)
- Migration 53 — crud_audit table (stable)

---

## Fix Strategies

### Strategy A: Handle AIMessage in event encoder (most likely fix)

If `EventEncoder` or the streaming loop doesn't handle `AIMessage`:
```python
# In agui_chat.py event loop, add:
elif isinstance(msg, AIMessage):
    # Convert to AG-UI TextMessageChunk or custom event
    yield encode_sse({
        "type": "text_message_chunk",
        "message_id": str(uuid4()),
        "delta": msg.content if isinstance(msg.content, str) else str(msg.content),
        "role": "assistant"
    })
```

### Strategy B: Change execute_write_node to not emit AIMessage

If execute_write_node can return a `ToolMessage` or update state without AIMessage:
```python
# Instead of returning AIMessage, update state directly:
return {"messages": [ToolMessage(content="Write confirmed", tool_call_id=...)]}
```

### Strategy C: Wrap in try/except with graceful degradation

If the crash is swallowed and the write DID succeed but the stream died:
```python
try:
    async for event in graph.astream_events(...):
        yield process_event(event)
except Exception as e:
    logger.error(f"AG-UI stream error: {e}")
    yield encode_sse({"type": "error", "message": str(e)})
    # Still close cleanly
```

---

## Test Procedure (T10)

After fix, re-run the HITL write test:

```bash
agent-browser open http://localhost:8502/jobs/{sourceId}/chat
agent-browser snapshot -i
# Type: "Update record {id} friability to Non-friable"
# Wait for HITLApprovalDialog to appear
agent-browser screenshot bug4-hitl-dialog.png
# Click "Approve"
agent-browser wait --text "confirmed" --timeout 15000
agent-browser screenshot bug4-write-confirmed.png
# Verify record was actually updated
agent-browser open http://localhost:8502/jobs/{sourceId}
agent-browser click @acm-records-tab
# Find the record — check friability field
```

**Pass criteria:**
- [ ] HITLApprovalDialog appears on write intent
- [ ] User clicks Approve
- [ ] Write confirmation appears in chat (no crash)
- [ ] SSE stream stays open and closes cleanly
- [ ] Record is actually updated in ACMGrid
- [ ] No console errors during the flow

---

## Backend Unit Test

Add a test for the fixed path:
```python
# tests/test_crud_agent.py or tests/test_agui_chat.py
async def test_execute_write_node_message_handled():
    """AG-UI encoder handles AIMessage from execute_write_node without crash."""
    ...
```

---

## Verification

```bash
uv run pytest tests/ -x -k "crud" -q    # existing CRUD tests pass
uv run pytest tests/ -x -k "agui" -q   # agui tests pass
cd frontend && npm run build             # no TS errors
```

---

## Update sprint-status after fix

```yaml
crud-chat-pipeline-enhancement-2026-03-17: done  # BUG-4 fixed 2026-03-20. All 11 T-tests pass including T10 HITL write flow.
```

---

## Commit Template

```
fix(agui): resolve BUG-4 AIMessage crash in CRUD HITL execute_write_node

Root cause: [describe what you found]
Fix: [describe the approach taken]
Result: T10 HITL approval flow now completes without AG-UI adapter crash.
All 11 CRUD chat E2E tests pass.

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
