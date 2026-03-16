# Task Plan: HITL, Generative UI, Bulk CRUD, and E2E Tests

Date: 2026-03-16
Status: PHASE 1 COMPLETE, PHASE 2-3 IN PROGRESS

## Goal

Implement remaining CopilotKit features: HITL via interrupt(), copilotkit Python SDK,
useCoAgentStateRender, enhanced generative UI components, and useDefaultTool fallback.

## Steps

### Phase 1 — Backend Foundation (DONE)
- [x] Install copilotkit>=0.1.78 Python SDK
- [x] Redesign CRUD graph: add `check_write_approval` node with `interrupt()`
- [x] Extract `execute_pending_write()` from confirm_write for HITL use
- [x] Update CRUD system prompt (remove "type confirm" instructions)
- [x] Add copilotkit_emit_state to supervisor graph nodes
- [x] Backend lint passes (ruff check on all modified files)
- [x] Both graphs compile OK

### Phase 2 — Frontend HITL + Agent Hooks (IN PROGRESS)
- [ ] Create HITLApprovalDialog component (approve/reject/edit)
- [ ] Replace toast confirmation with useLangGraphInterrupt in CrudToolRenderers
- [ ] Add useDefaultTool fallback renderer to ToolResultRenderers
- [ ] Add useCoAgentStateRender to SmartChatPanel

### Phase 3 — Generative UI Components (IN PROGRESS)
- [ ] WriteDiffView — side-by-side old→new
- [ ] BuildingSummaryCard — building data in chat
- [ ] ItemDetailCard — expandable ACM item card
- [ ] ExtractionProgress — extraction progress indicator
- [ ] DefaultToolFallback — fallback renderer component

### Phase 4 — Verification
- [ ] Frontend build passes
- [ ] Frontend lint passes
- [ ] Backend tests pass (excluding 3 known pre-existing failures)
- [ ] All new components verified via build

### Deferred (separate stories)
- useAgent v2 migration — staying on v1 useCoAgent per audit decision
- Bulk write tools — implement after single-record HITL is proven
- E2E Playwright tests — after all components pass build
- copilotkit Python SDK endpoint migration — ag-ui-langgraph works fine

## Files Modified

| File | Change | Phase |
|------|--------|-------|
| `pyproject.toml` | Added copilotkit>=0.1.78 | 1 |
| `open_notebook/graphs/crud_agent.py` | Added check_write_approval node with interrupt() | 1 |
| `open_notebook/graphs/crud_tools.py` | Extracted execute_pending_write(), kept confirm_write as legacy | 1 |
| `open_notebook/graphs/supervisor_agent.py` | Added copilotkit_emit_state (non-fatal) | 1 |
| `frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` | NEW — HITL approval UI | 2 |
| `frontend/src/components/jobs/CrudToolRenderers.tsx` | useLangGraphInterrupt replaces toast | 2 |
| `frontend/src/components/chat/ToolResultRenderers.tsx` | Added useDefaultTool | 2 |
| `frontend/src/components/chat/SmartChatPanel.tsx` | Added useCoAgentStateRender | 2 |
| `frontend/src/components/chat/renderers/WriteDiffView.tsx` | NEW — diff view | 3 |
| `frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` | NEW — building card | 3 |
| `frontend/src/components/chat/renderers/ItemDetailCard.tsx` | NEW — ACM item card | 3 |
| `frontend/src/components/chat/renderers/ExtractionProgress.tsx` | NEW — progress indicator | 3 |
| `frontend/src/components/chat/renderers/DefaultToolFallback.tsx` | NEW — fallback renderer | 3 |

## Architecture Decisions

1. **LangGraph native interrupt()** over copilotkit_interrupt — documented CopilotKit pattern
2. **check_write_approval as separate node** — interrupt() must be in a node, not a tool
3. **Graph flow**: agent → tools → check_approval → agent (with interrupt for preview_write)
4. **confirm_write kept as legacy** — can be removed once HITL is verified in production
5. **copilotkit_emit_state guarded** — try/except import, non-fatal if SDK unavailable
6. **confirmed_by: 'user_hitl'** in crud_audit — distinguishes HITL from legacy text confirmation
