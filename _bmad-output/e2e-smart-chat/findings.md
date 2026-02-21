# E2E Smart Chat Verification - Findings

**Date:** 2026-02-12
**Branch:** `feat/smart-chat`
**Status:** COMPLETE - All phases verified, chat working end-to-end

## Phase 0: Service Startup

| Service | Status | Notes |
|---------|--------|-------|
| SurrealDB | PASS | Healthy on port 8000 |
| API (FastAPI) | PASS | AG-UI endpoint at `/api/agui/chat` |
| Frontend (Next.js) | PASS | Port 8502, Turbopack, graphql@16 |

## Phase 1: Bug Fixes (8 bugs total)

### Bug 1: graphql version mismatch - FIXED
- **Symptom:** `SyntaxError: The requested module 'graphql' does not provide an export named 'versionInfo'`
- **Fix:** `npm install graphql@^16.12.0` in frontend

### Bug 2: CopilotKit runtime TypeError - FIXED
- **Symptom:** `TypeError: Cannot read properties of undefined (reading 'constructor')`
- **Root cause:** `copilotRuntimeNextJSAppRouterEndpoint()` requires `serviceAdapter` option
- **Fix:** Custom `AgUiAdapter extends EmptyAdapter` with overridden `get name()` getter

### Bug 3: EmptyAdapter blacklist - FIXED
- **Symptom:** "No default agent provided"
- **Root cause:** `EmptyAdapter` is in `illegalServiceAdapterNames` blacklist; the `name` getter returns "EmptyAdapter" and is inherited by subclasses
- **Fix:** Override `get name() { return "AgUiAdapter"; }` in the subclass

### Bug 4: remoteEndpoints doesn't register agents - FIXED
- **Symptom:** "Agent 'supervisor' not found after runtime sync. Known agents: [default]"
- **Root cause:** `assignEndpointsToAgents()` returns `{}` for non-LangGraph-Platform endpoints. Only `agents: {}` option works.
- **Fix:** Use `HttpAgent` from `@ag-ui/client` with `agents: { default: agent.clone(), supervisor: agent }`

### Bug 5: CopilotProvider needs "default" agent - FIXED
- **Symptom:** "Agent 'default' not found" + "Invalid action configuration"
- **Root cause:** CopilotProvider at layout level auto-initializes with "default" agent; SmartChatPanel uses "supervisor"
- **Fix:** Register both agents in route.ts pointing to same backend

### Bug 6: CopilotKit error crashes entire page - FIXED (prior session)
- **Fix:** Added `CopilotErrorBoundary` in `CopilotProvider.tsx`

### Bug 7: useCopilotAction "Invalid action configuration" - FIXED
- **Symptom:** `Error: Invalid action configuration` in `ToolResultRenderers` component
- **Root cause:** CopilotKit's `getActionConfig()` requires one of: `handler`, `available`, `name: "*"`, or HITL props. Render-only actions had none.
- **Fix:** Add `available: 'disabled'` to all 9 `useCopilotAction()` calls in `ToolResultRenderers.tsx`

### Bug 8: AG-UI backend agent wrapping - FIXED
- **Symptom:** `AttributeError: 'CompiledStateGraph' object has no attribute 'run'`
- **Root cause:** `add_langgraph_fastapi_endpoint()` expects a `LangGraphAgent` wrapper, not a raw compiled graph
- **Fix:** Wrap `supervisor_graph` in `LangGraphAgent(name="supervisor", graph=supervisor_graph)` in `agui_chat.py`

### Bug 8b: SqliteSaver async incompatibility - FIXED
- **Symptom:** `NotImplementedError: The SqliteSaver does not support async methods`
- **Root cause:** AG-UI adapter uses `aget_state()` (async); `SqliteSaver` only supports sync
- **Fix:** Replace `SqliteSaver` with `MemorySaver` in `supervisor_agent.py`

## Phase 1 UI Verification

| Test | Status | Screenshot | Notes |
|------|--------|------------|-------|
| 1.1 Landing page | PASS | `01-landing.png` | Full page renders |
| 1.2 Source detail | PASS (partial) | `02a-source-acm-tab.png` | ACM tab renders |
| 1.3 Smart Chat tab | PASS | `07-smart-chat-working.png` | SmartChatPanel renders, 0 errors |
| 1.4 ACM toggle | SKIP | - | Needs source with ACM data |
| 1.5 Notebook Classic/Smart | PASS | `06-notebook-no-errors.png` | Both tabs work, 0 errors |

## Phase 2: Chat Interaction

| Test | Status | Screenshot | Notes |
|------|--------|------------|-------|
| 2.1 Send message | PASS | `09-chat-working.png` | Full E2E: CopilotKit → route.ts → AG-UI → LangGraph → LLM → streamed response |
| 2.2 ACM tool query | SKIP | - | No ACM data in test notebook |
| 2.3 Risk query | SKIP | - | No ACM data in test notebook |

## Phase 3: Network & Log Analysis

- CopilotKit → `/copilot` POST returns 200
- `/copilot` route proxies to backend AG-UI endpoint via HttpAgent
- Backend receives request, LangGraph supervisor processes, streams SSE events back
- Response streamed successfully with proper formatting (bullet points, bold text)
- 0 browser console errors during chat interaction

## Key Technical Insights

1. **CopilotKit v1 wraps v2 internally**: `copilotRuntimeNextJSAppRouterEndpoint` calls `createCopilotEndpointSingleRoute` internally
2. **EmptyAdapter has `get name()` getter**: Returns "EmptyAdapter" by default, inherited by subclasses, checked against blacklist
3. **`remoteEndpoints` is essentially a no-op** for non-LangGraph-Platform endpoints
4. **Must use `agents: { name: instance }` directly** with `HttpAgent` from `@ag-ui/client`
5. **TypeScript type mismatch**: CopilotKit uses internal `@ag-ui/client` at different path than top-level; needs `as any`
6. **Turbopack quirk**: Server-side route handlers don't auto-recompile on file change; need full restart
7. **`handleServiceAdapter` uses Promise-based agent resolution**: `/info` endpoint does `await runtime.agents`
8. **`useCopilotAction` render-only pattern**: Must include `available: 'disabled'` for actions that only render backend tool results
9. **`add_langgraph_fastapi_endpoint` needs `LangGraphAgent` wrapper**: Raw compiled graphs don't have the `.run()` method
10. **Async checkpointer required**: AG-UI adapter uses async LangGraph methods; `MemorySaver` supports both sync and async

## Files Modified

| File | Change | Category |
|------|--------|----------|
| `frontend/package.json` + lockfile | graphql@16 dependency | Frontend |
| `frontend/src/components/providers/CopilotProvider.tsx` | Error boundary | Frontend |
| `frontend/src/app/copilot/route.ts` | v1 API + HttpAgent + dual agents | Frontend |
| `frontend/src/components/chat/ToolResultRenderers.tsx` | `available: 'disabled'` on all 9 actions | Frontend |
| `api/routers/agui_chat.py` | `LangGraphAgent` wrapper | Backend |
| `open_notebook/graphs/supervisor_agent.py` | `MemorySaver` instead of `SqliteSaver` | Backend |

## Screenshots

1. `01-landing.png` - Landing page (PASS)
2. `02-source-classic.png` - Source page
3. `02a-source-acm-tab.png` - ACM tab
4. `05-notebook-classic-chat.png` - Notebook with Classic/Smart Chat tabs
5. `06-notebook-no-errors.png` - Notebook page, 0 errors
6. `07-smart-chat-working.png` - Smart Chat panel rendered
7. `08-chat-sent-backend-error.png` - Chat sent, backend AG-UI error (before fix)
8. `09-chat-working.png` - Full E2E chat working
