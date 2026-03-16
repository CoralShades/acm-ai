# Progress: HITL, Generative UI, and CopilotKit Enhancements

Date: 2026-03-16

## Completed

### Phase 1 — Backend Foundation
- [x] Install copilotkit>=0.1.78 Python SDK
- [x] Verify copilotkit imports: `copilotkit_emit_state` from `copilotkit.langgraph`
- [x] Verify LangGraph `interrupt` and `Command` from `langgraph.types`
- [x] Redesign CRUD graph: add `check_write_approval` node with `interrupt()`
- [x] Extract `execute_pending_write()` from `confirm_write` tool
- [x] Update CRUD system prompt: remove "type confirm" instructions
- [x] Graph flow: agent → tools → check_approval → agent (with interrupt for previews)
- [x] Keep `confirm_write` as legacy fallback (delegates to execute_pending_write)
- [x] Add `copilotkit_emit_state` to supervisor graph (non-fatal, guarded import)
- [x] Handle both dict and JSON string from CopilotKit resolve()
- [x] Backend lint passes (`ruff check` on all files)
- [x] Both graphs compile OK (CRUD: 5 nodes, Supervisor: 4 nodes)

### Phase 2 — Frontend HITL + Agent Hooks
- [x] Create HITLApprovalDialog component (approve/reject/edit value)
- [x] Replace toast confirmation with useLangGraphInterrupt in CrudToolRenderers
- [x] Removed WriteConfirmationCard import (replaced by HITLApprovalDialog)
- [x] Add useDefaultTool fallback renderer to ToolResultRenderers
- [x] Add useCoAgentStateRender to SmartChatPanel (supervisor progress)
- [x] Fix render return types (ReactElement, not null) for useRenderToolCall hooks

### Phase 3 — Generative UI Components
- [x] HITLApprovalDialog — HITL approval/reject/edit UI
- [x] WriteDiffView — old→new field diff display
- [x] BuildingSummaryCard — building data card for chat
- [x] ItemDetailCard — expandable ACM item card with all fields
- [x] ExtractionProgress — extraction stage progress indicator
- [x] DefaultToolFallback — fallback renderer component

### Verification
- [x] copilotkit SDK installed: `from copilotkit import LangGraphAgent` OK
- [x] Backend lint: `uv run ruff check open_notebook/ api/` — All checks passed
- [x] Frontend build: `npm run build` — Compiled successfully (0 errors)
- [x] Frontend lint: `npm run lint` — Pass (pre-existing warnings only)
- [x] CRUD graph has interrupt(): 3 references in crud_agent.py
- [x] useLangGraphInterrupt in CrudToolRenderers: 4 references
- [x] useCoAgentStateRender in SmartChatPanel: 2 references
- [x] useDefaultTool in ToolResultRenderers: 2 references

### Phase 4 — P2/P3 UI Polish + Chat Model Selector
- [x] P2-3: Removed redundant ACM banner from SmartChatPanel (toggle button suffices)
- [x] P2-4: Extracted BuildingListResult component from ACMStatsResult; replaced text-[10px] with text-xs; moved icons from metric numbers to labels
- [x] P2-7: Removed duplicate Wrench icon from DefaultToolFallback
- [x] P3-1: Added submitting state to HITL Approve/Reject buttons (prevent double-submit)
- [x] P3-2: Added useEffect to sync editedValue when preview.new_value changes
- [x] P3-4: Added role="region" and aria-label to WriteDiffView
- [x] P3-5: Added role="article" and aria-label to BuildingSummaryCard
- [x] P3-6: Removed void sourceId pattern from CrudToolRenderers
- [x] P3-7: Moved icons from metric numbers into label captions in ACMStatsResult
- [x] P3-9: Set showDevConsole={false} in CopilotProvider; removed CSS hide rules from globals.css
- [x] P3-10: Consolidated TOOL_LABELS into shared frontend/src/lib/constants/tool-labels.ts
- [x] P3-11: Removed dead getRiskBadgeVariant function from ACMTableResult
- [x] P3-12: Moved Mac detection to module-level IS_MAC constant in SmartChatInput
- [x] P3-13: Standardised all renderer root divs to my-2 (7 files)
- [x] P3-14: Capped ACMTableResult rows at 20 with "Show all X results" expandable button
- [x] ChatModelSelector: compact popover-based model picker created (ChatModelSelector.tsx)
- [x] ChatModelSelector wired into SmartChatPanel header (supervisor chat)
- [x] ChatModelSelector wired into JobCrudChatPanel header with useCoAgent state sync
- [x] model_id field added to SupervisorAgentState and CRUDAgentState TypedDicts
- [x] supervisor_agent.py and crud_agent.py read state.get("model_id") first, fall back to config.configurable.model_id
- [x] Selection persists to localStorage per chat context
- [x] Selector only renders when 2+ language models are registered
- [x] useSmartChat.ts exposes chatModelId/setChatModelId via useCoAgent state
- [x] Frontend build and lint pass

## Deferred

- useAgent v2 migration — staying on v1 useCoAgent per audit decision
- Bulk write tools — implement after single-record HITL is proven
- E2E Playwright tests — after runtime verification with live services
- copilotkit Python SDK endpoint migration — ag-ui-langgraph works fine

## Notes

- copilotkit v0.1.78 downgraded fastapi from 0.123.0→0.115.14 (compatible)
- `copilotkit_emit_state` is in `copilotkit.langgraph` submodule (not top-level)
- LangGraph's native `interrupt()` works with CopilotKit's `useLangGraphInterrupt`
- `confirmed_by` field in crud_audit uses 'user_hitl' for HITL writes
- Backend handles both dict and JSON string from resolve() for robustness
- `useRenderToolCall` render function requires ReactElement (not null) — use `<></>`
