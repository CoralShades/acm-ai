# Findings: CopilotKit Audit & Integration

Date: 2026-03-16
Status: IMPLEMENTATION COMPLETE (Phases A-C)

## Version Info

| Package | Installed | Latest Stable | Notes |
|---------|-----------|---------------|-------|
| @copilotkit/react-core | ^1.51.3 (resolved 1.51.4) | 1.51.x | v2 API available at `/v2` subpath |
| @copilotkit/react-ui | ^1.51.3 (resolved 1.51.4) | 1.51.x | v2 consolidates into react-core/v2 |
| @copilotkit/runtime | ^1.51.3 (resolved 1.51.4) | 1.51.x | Backend unchanged in v2 |
| ag-ui-langgraph (Python) | >=0.0.25 | 0.0.25 | Provides LangGraphAgent, endpoint helper |
| copilotkit (Python SDK) | NOT INSTALLED | 0.1.78 | Wraps ag-ui-langgraph + adds emit helpers |

## v1 → v2 Migration Path

v2 is **additive and non-breaking** on v1.51.4:
- v1 imports from `@copilotkit/react-core` still work
- v2 imports from `@copilotkit/react-core/v2` (same package, subpath export)
- `CopilotKit` → `CopilotKitProvider` (v2 rename)
- `useCoAgent` → `useAgent` (v2 superset: adds time-travel, multi-agent awareness)
- `useCoAgentStateRender` → available in both v1 and v2
- Styles: `@copilotkit/react-ui/styles.css` → `@copilotkit/react-core/v2/styles.css`
- **Backend `@copilotkit/runtime` unchanged** — no migration needed
- **Python backend unchanged** — `ag-ui-langgraph` or `copilotkit` SDK both work

**Decision: Stay on v1 API for now, fix bugs first, plan v2 migration as separate story.**

## Critical Bugs Found (5)

### BUG-1: CopilotRuntime instantiated per-request
**Files:** `frontend/src/app/api/copilotkit/route.ts`, `frontend/src/app/copilot-crud/route.ts`
**Issue:** Runtime and HttpAgent created inside the POST handler. SKILL.md anti-pattern: "Create a new CopilotRuntime per request."
**Impact:** Memory pressure, prevents thread persistence, degrades performance.
**Fix:** Move to module-level singletons.

### BUG-2: HttpAgent from @ag-ui/client with `as any` cast
**Files:** `frontend/src/app/api/copilotkit/route.ts`, `frontend/src/app/copilot-crud/route.ts`
**Issue:** Uses `HttpAgent` from `@ag-ui/client` (transitive dep) with `.clone() as any` workaround. Should use `CustomHttpAgent` from `@copilotkit/runtime`.
**Impact:** Type-unsafe, fragile across upgrades, `@ag-ui/client` not in package.json.

### BUG-3: No checkpointer on CRUD graph
**Files:** `open_notebook/graphs/crud_agent.py`
**Issue:** `_builder.compile()` without `checkpointer=MemorySaver()`. Supervisor has MemorySaver.
**Impact:** CRUD agent loses all conversation context between turns.

### BUG-4: `status === 'failed'` never handled in tool renders
**Files:** `frontend/src/components/chat/ToolResultRenderers.tsx`, `frontend/src/components/jobs/CrudToolRenderers.tsx`
**Issue:** All 11 render functions lack error state handling.
**Impact:** Agent errors silently render nothing — user sees blank space.

### BUG-5: No `onError` on CopilotKit provider
**Files:** `frontend/src/components/providers/CopilotProvider.tsx`
**Issue:** React error boundary catches render crashes but `onError` prop missing for runtime/network errors. `showDevConsole={false}` hardcoded.
**Impact:** Runtime errors go unhandled and invisible in development.

## High-Priority Gaps (6)

### GAP-1: Tool renderers use wrong hook
**Files:** `ToolResultRenderers.tsx`, `CrudToolRenderers.tsx`
**Issue:** `useCopilotAction({ available: 'disabled', parameters: [] })` used for backend tool rendering. Correct v1.51.x pattern is `useRenderToolCall` (for backend tools) or `useFrontendTool` (for frontend tools).
**Sub-issue:** Empty `parameters: []` means CopilotKit has no schema to match against inbound tool args.

### GAP-2: No useCopilotReadable anywhere
**Issue:** ACM data, source metadata, page context never exposed to LLM as structured context. All context manually composed in `makeSystemMessage` string.
**Impact:** LLM cannot access current page state, selected building, active filters, etc.

### GAP-3: HITL uses toast+chat-message pattern
**Files:** `CrudToolRenderers.tsx`, `WriteConfirmationCard.tsx`, `crud_agent.py`
**Issue:** Preview-write confirmation relies on user typing "confirm X" in chat. No `interrupt()` on backend, no `useLangGraphInterrupt` on frontend.
**Impact:** Error-prone, non-idiomatic, bypasses CopilotKit HITL infrastructure.

### GAP-4: useCoAgent instead of useAgent (v2)
**Files:** `useSmartChat.ts`
**Issue:** v1 `useCoAgent` used; v2 `useAgent` recommended. Local React state and agent state can diverge.

### GAP-5: No useCopilotChatSuggestions
**Issue:** Users see empty chat with no guidance. Domain-aware suggestions ("Show high-risk records", "Summarize document") would improve UX significantly.

### GAP-6: No useCoAgentStateRender
**Issue:** When supervisor agent is reasoning (calling tools, searching), user sees generic loading. State render would show intermediate progress.

## Medium-Priority Gaps (4)

| Gap | Issue | Impact |
|-----|-------|--------|
| No `useDefaultTool` fallback | Unexpected agent tool calls render nothing | Silent UX failures |
| No `storageRunner` on CopilotRuntime | Thread state lost on Next.js restart | Conversation continuity broken |
| makeSystemMessage ignores contextString in CRUD panel | `() =>` signature instead of `(contextString) =>` | useCopilotReadable data would be ignored |
| @ag-ui/client not in package.json | Used in routes but transitive dep only | Fragile, can break silently |

## Low-Priority Items (deferred)

| Item | Notes |
|------|-------|
| CopilotPopup / CopilotSidebar | Current inline CopilotChat sufficient for now |
| CopilotTextarea | No AI text-area use case yet |
| CopilotTask | No programmatic task triggers needed |
| copilotkit Python SDK | ag-ui-langgraph works; SDK adds emit helpers but not critical |
| A2UI / declarative generative UI | Static AG-UI pattern sufficient |
| MCP Apps generative UI | Not needed |
| v2 CopilotKitProvider migration | Non-breaking; defer to separate story |
| v2 slot system for styling | Current CSS customization works |

## Decisions Made

1. **Stay on v1 API** — v2 is additive but migration is low-priority; fix bugs first
2. **Fix 5 critical bugs** before adding new features
3. **Add useCopilotReadable** as highest-impact UX improvement
4. **Replace tool render pattern** — `useRenderToolCall` for backend tools
5. **Add HITL for CRUD writes** — `useLangGraphInterrupt` + `interrupt()` is a larger change; implement after bug fixes
6. **Add chat suggestions** — quick UX win with `useCopilotChatSuggestions`
7. **Defer Python SDK migration** — `ag-ui-langgraph` works, SDK adds convenience but no functionality gap
8. **Add @ag-ui/client as explicit dependency** — defensive dependency management

## File-by-File Audit Summary

| File | Status | Key Issues |
|------|--------|------------|
| CopilotProvider.tsx | Needs fixes | No onError, showDevConsole hardcoded, redundant CSS import |
| api/copilotkit/route.ts | Needs rewrite | Per-request runtime, wrong HttpAgent, as any cast |
| copilot-crud/route.ts | Needs rewrite | Same issues as above |
| SmartChatPanel.tsx | Mostly OK | Missing useCopilotReadable, useCopilotChatSuggestions |
| ToolResultRenderers.tsx | Needs refactor | Wrong hook (useCopilotAction → useRenderToolCall), no failed status |
| ACMAssistantMessage.tsx | Good | Clean implementation |
| JobCrudChatPanel.tsx | Needs fixes | makeSystemMessage wrong signature, nested provider fragile |
| CrudToolRenderers.tsx | Needs rewrite | Wrong hook, no failed status, ad-hoc HITL pattern |
| useSmartChat.ts | Needs upgrade | useCoAgent → useAgent, state divergence bug |
| smart-chat.ts | Good | Types align with backend |
| globals.css | Good | CopilotKit styles imported correctly |
| agui_chat.py | Mostly OK | Agent name mismatch (crud_agent vs crud) |
| main.py | OK | AG-UI endpoints registered, auth exempted |
| supervisor_agent.py | OK | MemorySaver present, tools work, no emit_state (acceptable) |
| crud_agent.py | Needs fix | No checkpointer, no interrupt(), prompt-based HITL |
| agui_event_emitter.py | OK | Parallel AG-UI system for extraction, not CopilotKit |
| agent_cards.py | Stub | Cards defined but not served at .well-known |
| package.json | Needs fix | @ag-ui/client missing as direct dep |
| next.config.ts | Good | serverExternalPackages correct |
