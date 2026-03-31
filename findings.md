# Chat Debug Findings — 2026-03-31

## Trace IDs Under Investigation
- `1249fde5-2ce2-4940-a7a3-95c62a7ddbcf`
- `82b131ac-05d6-4fa5-a6c1-e808cecef770`
- `53e7f1e5-147a-4362-91b3-b834a21cbc76`

---

## ROOT CAUSE ANALYSIS

### RC-1: call_unified_agent didn't persist resolved source_id back to state — ✅ FIXED (Fixes 1, 3, 4)

**Previously titled**: CopilotKit sends agent state as AgentStateMessage, NOT input.state (CONFIRMED)

**Evidence from `@copilotkit/runtime/dist/index.js`:**
- Line 3088: `function aguiToGQL(messages, actions, coAgentStateRenders)` — converts AG-UI messages, recognizes `AgentStateMessage` as a special message type
- Line 3095-3110: Agent state is embedded as a message with `agentName` and `state` properties within the messages array
- `AgentStateMessageInput` (line 1582) has fields: `threadId`, `agentName`, `role`, `state`, `running`, `nodeName`, `runId`, `active`

**Evidence from `ag_ui_langgraph/agent.py`:**
- Line 271: `state_input = input.state or {}` — uses `RunAgentInput.state` which CopilotKit may NOT populate
- Line 279: `state = self.langgraph_default_merge_state(state_input, langchain_messages, input)`
- Line 476: `{**state, "messages": new_messages, ...}` — if state_input is `{}`, source_id/notebook_id are missing
- **BUT**: The `prepare_stream` at line 271 takes `input.state or {}`, and CopilotKit runtime likely passes agent state in `input.state` for AG-UI protocol (not just as a message)

**Verification**: Graph schema IS correct — `get_input_jsonschema()` returns `['messages', 'source_id', 'notebook_id', 'model_id', 'include_acm_context', 'pending_operation']`. So schema-based filtering at `get_stream_payload_input` would NOT strip source_id.

**STATUS**: Partially confirmed. The CopilotKit runtime constructs RunAgentInput with `state` from `useCoAgent`, which should include source_id. However, the actual propagation needs instrumentation to confirm.

### RC-2: _resolve_source_id message regex only matches lowercase hex — ✅ FIXED (Fix 2)

**Evidence from `unified_agent.py` line 78:**
```python
match = re.search(r"(source:[a-z0-9]+)", content)
```
This ONLY matches lowercase hex characters. SurrealDB record IDs can contain any alphanumeric characters. If the source_id is `source:ABC123` or `source:some-uuid`, the regex fails silently.

**Fix applied**: Changed to `[a-zA-Z0-9_]` pattern in `_extract_source_id_from_messages`.

### RC-3: CopilotKit useCopilotReadable sends context as system messages

**Evidence from `UnifiedChatPanel.tsx` line 130-134:**
```tsx
useCopilotReadable({
  description: 'Current page context: source ID, notebook ID...',
  value: readableValue,  // includes sourceId
})
```
This injects a system message with the context. However, `_extract_source_id_from_messages` only regex-searches for `source:xxx` — it doesn't parse JSON or structured context. If CopilotKit formats it as JSON like `{"sourceId": "source:abc"}`, the regex won't match because JavaScript uses camelCase (`sourceId`) not the `source:xxx` pattern.

### RC-4: Session/Thread ID disconnect

**Evidence from `unified_sessions.py` line 89:**
```python
thread_id = str(_uuid.uuid4())  # Creates a NEW UUID
```
**Evidence from `ag_ui_langgraph/agent.py` line 118:**
```python
thread_id = input.thread_id or str(uuid.uuid4())  # Uses CopilotKit's thread_id or generates new
```

The frontend `chatSessionStore` creates sessions with `thread_id` (line 89 of unified_sessions.py), but CopilotKit manages its own `thread_id`. These are DIFFERENT values. The checkpointer stores state under CopilotKit's thread_id, not the session's thread_id.

**Impact**: Session switching doesn't actually change the LangGraph thread — conversations may bleed across sessions.

### RC-5: _pending_writes in-memory dict (CONFIRMED) — ✅ PARTIALLY FIXED (Fix 8)

**Evidence from `crud_tools.py` line 48:**
```python
_pending_writes: dict = {}
```
This is module-level in-memory storage. Issues:
1. Lost on server restart
2. No TTL — stale pending writes accumulate forever ← **Fixed: 10-minute TTL, cleaned on each new preview**
3. No locking for concurrent access
4. The HITL interrupt/resume flow goes: preview_write → stores in dict → interrupt() → frontend gets payload → user approves → Command(resume=...) → approval_node reads from dict

The `approval_node` calls `execute_pending_write.ainvoke()` — but this is a @tool function. Since `execute_pending_write` is NOT in the LLM-facing tools list (line 106-107), it can only be called internally. The dict access SHOULD work within the same process, but timing and restart issues remain.

**Fix applied**: TTL cleanup added — entries older than 10 minutes purged on each new `preview_write` call. Restart persistence still unresolved (would require Redis or DB storage).

### RC-6: parseResult silently swallowed error results — ✅ FIXED (Fix 6)

**Evidence**: `UnifiedToolRenderers.tsx` `parseResult` helper returned `null`/empty on error-shaped payloads — failed tool calls showed no UI feedback.

**Fix applied**: `parseResult` now propagates error results through to the renderer.

**Also fixed (S-1)**: `search_documents` and `text_search_documents` used f-string SQL interpolation instead of parameterized bindings — replaced with `$source_id`/`$notebook_id` parameters (Fix 7).

---

## Secondary Issues

### S-1: useCoAgent setState race condition
`useUnifiedChat.ts` uses `didSyncRef` guard but only syncs once per scope change. If CopilotKit sends a request before the setState propagates, the first message may lack source_id.

### S-2: Session endpoint query may fail
`unified_sessions.py` line 48 uses SurrealQL graph traversal: `SELECT <-refers_to<-chat_session.* as sessions FROM $sid`. If the `refers_to` edge or `chat_session` table doesn't exist, this silently returns empty.

### S-3: Frontend tool name alignment
All 18 frontend renderer names need to match the backend @tool function names exactly. Previous fix (PR #114-#116) corrected some mismatches, but new issues may have been introduced.

---

## Recommended Fix Order — STATUS

| Priority | Fix | Status |
|----------|-----|--------|
| P0 | Persist source_id/notebook_id to state output (Fix 1) | ✅ DONE |
| P0 | Fix regex for mixed-case source IDs (Fix 2) | ✅ DONE |
| P0 | Add resolution logging (Fix 3) | ✅ DONE |
| P1 | Add session_id to UnifiedAgentState (Fix 4) | ✅ DONE |
| P1 | Per-request agent creation — fix concurrent corruption (Fix 5) | ✅ DONE |
| P2 | parseResult error propagation (Fix 6) | ✅ DONE |
| P2 | Parameterized queries in search_tools.py (Fix 7) | ✅ DONE |
| P2 | TTL cleanup for _pending_writes (Fix 8) | ✅ DONE |
| OPEN | RC-4: thread_id alignment (session ↔ CopilotKit) | ⏳ Partial — session_id in state added; full wiring pending |
| OPEN | RC-5: _pending_writes restart persistence | ⏳ TTL added; Redis/DB storage still needed for production |
