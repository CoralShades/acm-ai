# Chat System Debug — Task Plan

**Created**: 2026-03-31
**Trace IDs**: 1249fde5-2ce2-4940-a7a3-95c62a7ddbcf, 82b131ac-05d6-4fa5-a6c1-e808cecef770, 53e7f1e5-147a-4362-91b3-b834a21cbc76
**Scope**: CopilotKit → AG-UI → LangGraph unified_agent → SurrealDB

## Architecture (Data Flow)

```
Frontend (CopilotKit)          → /api/copilotkit (Next.js route)
  useCoAgent(acm_agent)            → CopilotRuntime + HttpAgent
    state: {source_id,                → /api/agui/chat (FastAPI)
     notebook_id, session_id, ...}        → unified_agent graph (LangGraph)
                                              → context_aware_tools → SurrealDB
                                              → approval_node (interrupt/HITL)
```

## Issues to Debug

### 1. Source/Job Mapping (CRITICAL)
- [ ] source_id not propagating from frontend to backend correctly
- [ ] Verify: useCoAgent setState → AG-UI protocol → graph state
- [ ] Check _resolve_source_id fallback chain
- [ ] Verify chatSessionStore session → thread mapping

### 2. Query Failures
- [ ] surreal_query returns incorrect/no records
- [ ] SurrealQL generation issues for building tables
- [ ] Variable binding failures ($sid, unmatched params)
- [ ] Compare frontend-displayed data vs backend query results

### 3. Tool Rendering
- [ ] Tools not rendering in frontend chat
- [ ] Verify tool names match: backend @tool ↔ useRenderToolCall
- [ ] AG-UI TOOL_CALL_BEGIN/TOOL_CALL_END events not emitted

### 4. HITL Approval Flow
- [ ] preview_write → interrupt → approval dialog broken
- [ ] useLangGraphInterrupt not receiving payloads
- [ ] resolve() not resuming backend graph

### 5. Edit/Delete Errors
- [ ] execute_pending_write fails after approval
- [ ] _pending_writes in-memory dict: state lost across requests?
- [ ] Record validation (source_id mismatch, record not found)

### 6. Backend/Frontend Mismatch
- [ ] Pipeline changes not reflected after messages
- [ ] Session/thread lifecycle not aligned
- [ ] Checkpointer state issues

## Agent Team Assignments

| Agent | Focus Area | Key Files |
|-------|-----------|-----------|
| backend-investigator | Graph execution, tool context, SurrealDB | unified_agent.py, crud_tools.py, acm_tools.py, tool_context.py |
| frontend-investigator | CopilotKit state, renderers, HITL UI | UnifiedChatPanel.tsx, useUnifiedChat.ts, UnifiedToolRenderers.tsx |
| api-tracer | AG-UI bridge, session endpoints, HTTP flow | agui_chat.py, copilotkit/route.ts, chatSessionStore.ts |
| worker-logger | API logs, error analysis, trace correlation | Backend logs, trace IDs, SurrealDB queries |
| devils-advocate | Challenge findings, find edge cases | All files — adversarial review |
| browser-tester | Visual testing, screenshots | agent-browser automation |
| doc-updater | Track findings, save evidence | findings.md, progress.md, screenshots/ |

---

## Verification Phase — PASS

**Backend Verifier Results:**

| Check | Result | Notes |
|-------|--------|-------|
| AG-UI chat health | PASS | `LangGraphAGUIAgent` confirmed operational |
| All 4 code fixes deployed | PASS | Unified agent state, source_id resolution, per-request agents, context propagation |
| ACM records exist | PASS | 57 + 118 records found across test sources |
| `building_record.record_count` | NULL (Pre-existing) | All building records show NULL — pre-existing data issue, not chat bug |
| Session `thread_id` alignment | PASS | Newer sessions have `thread_id` populated from CopilotKit |

**Summary**: All 11 fixes deployed successfully. Session/thread alignment now bidirectional (useUnifiedChat + UnifiedChatPanel both sync thread_id). The `building_record.record_count` NULL values are a pre-existing data model issue, not caused by chat fixes.
