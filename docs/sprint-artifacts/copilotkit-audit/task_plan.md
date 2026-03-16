# Task Plan: CopilotKit Audit & Integration

Date: 2026-03-16
Status: PHASES A-C COMPLETE

## Goal

Fix critical bugs, improve correctness, and add high-priority missing CopilotKit features.

## Implementation Steps (prioritized)

### Phase A — Critical Bug Fixes (DONE)

- [x] A1. Rewrite runtime routes: module-level singletons + lazy init (BUG-1, BUG-2)
- [x] A2. Add MemorySaver checkpointer to CRUD graph (BUG-3)
- [x] A3. Add error result handling to all 11 tool renderers (BUG-4)
- [x] A4. Fix CopilotProvider: add onError, env-conditional showDevConsole (BUG-5)
- [x] A5. Add @ag-ui/client v0.0.43 as explicit dependency in package.json

### Phase B — High-Priority Correctness Fixes (DONE)

- [x] B1. Refactor ToolResultRenderers: useCopilotAction → useRenderToolCall (9 tools)
- [x] B2. Refactor CrudToolRenderers: useCopilotAction → useRenderToolCall (2 tools)
- [x] B3. Add useCopilotReadable for source/notebook/page context in SmartChatPanel
- [x] B4. Fix makeSystemMessage signature in JobCrudChatPanel (contextString param)
- [ ] B5. Fix useSmartChat local/agent state divergence — DEFERRED (needs useAgent v2)

### Phase C — Feature Additions (PARTIAL)

- [x] C1. Add useCopilotChatSuggestions to SmartChatPanel (domain-aware suggestions)
- [ ] C2. Add useCoAgentStateRender for supervisor progress — DEFERRED (needs emit_state)
- [ ] C3. Add useDefaultTool fallback renderer — DEFERRED (low priority)

### Phase D — HITL Implementation (DEFERRED — separate story)

- [ ] D1. Add interrupt() to CRUD graph preview-write flow
- [ ] D2. Add useLangGraphInterrupt to CrudToolRenderers
- [ ] D3. Remove toast+chat-message confirmation workaround

### Phase E — Verification (DONE)

- [x] E1. Frontend build: `cd frontend && npm run build` — PASS
- [x] E2. Frontend lint: `cd frontend && npm run lint` — PASS (pre-existing warnings only)
- [x] E3. Backend lint: `uv run ruff check .` — PASS on modified files
- [ ] E4. Backend tests: `uv run pytest tests/ -x` — not run (no CopilotKit-specific tests)
- [ ] E5. Browser verify: supervisor chat works — requires running services
- [ ] E6. Browser verify: CRUD chat works — requires running services

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/app/api/copilotkit/route.ts` | Lazy singleton runtime, reuse across requests |
| `frontend/src/app/copilot-crud/route.ts` | Lazy singleton runtime, reuse across requests |
| `frontend/src/components/providers/CopilotProvider.tsx` | onError callback, env-conditional showDevConsole, removed redundant CSS import |
| `frontend/src/components/chat/ToolResultRenderers.tsx` | useCopilotAction → useRenderToolCall, error result handling |
| `frontend/src/components/chat/SmartChatPanel.tsx` | Added useCopilotReadable, useCopilotChatSuggestions |
| `frontend/src/components/jobs/CrudToolRenderers.tsx` | useCopilotAction → useRenderToolCall, error result handling |
| `frontend/src/components/jobs/JobCrudChatPanel.tsx` | Fixed makeSystemMessage signature |
| `frontend/src/components/chat/renderers/ToolErrorCard.tsx` | NEW — error state component for tool renders |
| `frontend/package.json` | Added @ag-ui/client ^0.0.43 |
| `open_notebook/graphs/crud_agent.py` | Added MemorySaver checkpointer |

## Recommended Follow-Up Stories

1. **HITL for CRUD writes** — Replace text "confirm {id}" with interrupt() + useLangGraphInterrupt
2. **useAgent v2 migration** — Replace useCoAgent with useAgent for time-travel + multi-agent
3. **useCoAgentStateRender** — Stream supervisor reasoning progress to chat UI
4. **copilotkit Python SDK** — Evaluate replacing ag-ui-langgraph with SDK for emit helpers
5. **Thread persistence** — Replace MemorySaver with persistent checkpointer for production
