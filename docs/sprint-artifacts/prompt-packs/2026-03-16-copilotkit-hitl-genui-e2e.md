# Session: Implement HITL, Generative UI, Bulk CRUD, and E2E Tests for CopilotKit Integration

## Skills to Load

/copilotkit — CopilotKit hooks, components, runtime, CoAgent, AG-UI, HITL, generative UI patterns
/langgraph-fundamentals — LangGraph StateGraph, nodes, edges, Command, streaming
/langgraph-human-in-the-loop — interrupt(), Command(resume=), approval workflows, error handling
/langchain-dependencies — Package versions, environment setup, copilotkit Python SDK
/e2e-test — Self-healing E2E testing with Playwright, selector healing, evidence collection
/frontend-design — Production-grade frontend interfaces, polished UI
/planning-with-files — Persistent markdown plan for session continuity
/verification-before-completion — Verify work before claiming done
/agent-browser — Browser automation for screenshot verification

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503`
- Branch: `git checkout ACMV3`
- CopilotKit packages: `cd frontend && npm ls @copilotkit/react-core` (should be ^1.51.3)
- ag-ui-langgraph: `cd "$CLAUDE_PROJECT_DIR" && uv run python -c "import ag_ui_langgraph; print('OK')"`
- Previous audit artifacts: `cat docs/sprint-artifacts/copilotkit-audit/findings.md` (must exist)
- Previous audit artifacts: `cat docs/sprint-artifacts/copilotkit-audit/task_plan.md` (must exist)

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| CopilotKit | Real-time AI copilot framework (v1.51.4) providing hooks and chat UI. Installed at `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`. |
| AG-UI Protocol | Event protocol from CopilotKit that streams agent actions to the frontend. 17 event types including `STATE_SNAPSHOT`, `TOOL_CALL_*`, `TEXT_MESSAGE_*`. |
| `interrupt()` | LangGraph function that pauses graph execution for human approval. Requires a checkpointer. Resumes with `Command(resume=<value>)`. |
| `useLangGraphInterrupt` | CopilotKit hook rendering LangGraph interrupt events. Receives `{ event, resolve }` — call `resolve(value)` to resume the graph. Supports `enabled` filter for multiple interrupt types. |
| `useCoAgentStateRender` | CopilotKit hook rendering agent intermediate state per graph node. Shows real-time progress during execution. |
| `useAgent` | CopilotKit v2 hook (superset of `useCoAgent`). Returns `{ agent }` with `.state`, `.setState()`, `.subscribe()`, `.setMessages()` (time-travel). Uses `agentId` prop. |
| `copilotkit` Python SDK | Python package (v0.1.78) wrapping ag-ui-langgraph. Provides `CopilotKitRemoteEndpoint`, `LangGraphAgent`, `copilotkit_emit_state`, `copilotkit_interrupt`, `copilotkit_customize_config`. |
| `useRenderToolCall` | CopilotKit hook for rendering backend-emitted tool calls. Already used in project (migrated from `useCopilotAction` in prior audit). |
| `useDefaultTool` | CopilotKit hook providing fallback UI for unregistered tool calls. Catches any agent tool call without a specific renderer. |
| Building__c | Salesforce object for a physical building. The extraction pipeline produces one `BuildingRecord` per building. |
| Item__c | Salesforce object for an individual ACM sample within a building. Maps to `ACMRecord`. |
| HITL | Human-in-the-loop — pattern where agent pauses for user approval. CopilotKit supports via `useLangGraphInterrupt` + `useHumanInTheLoop`. |
| WriteConfirmationCard | Existing React component showing CRUD write preview. Currently uses toast+chat-message confirmation. Needs HITL replacement. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |

---

## Current State

- Branch: ACMV3 (last commit: `54ec8f3d feat(ui): redesign Jobs Dashboard`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- CopilotKit version: `^1.51.3` (resolved 1.51.4) — 3 frontend packages + ag-ui-langgraph backend
- **Prior audit completed** — 5 critical bugs fixed, tool renderers refactored to `useRenderToolCall`, `useCopilotReadable` + `useCopilotChatSuggestions` added, MemorySaver added to CRUD graph
- **HITL NOT implemented** — CRUD writes still use toast+chat "confirm {id}" pattern
- **copilotkit Python SDK NOT installed** — using raw ag-ui-langgraph
- **useAgent v2 NOT migrated** — still on useCoAgent v1
- **No E2E tests** for any CopilotKit chat flows
- Two CopilotRuntime instances: supervisor (`/api/copilotkit`) + CRUD (`/copilot-crud`)
- Error rendering via `isErrorResult()` check (no TypeScript `"failed"` status in v1.51.4 render props)

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (audit context — MUST READ FIRST):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-audit/findings.md` — Complete audit with gap matrix
- `D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-audit/task_plan.md` — Prior phases + deferred items
- `D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-audit/progress.md` — What was already done
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/SKILL.md` — CopilotKit skill reference
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/references/human-in-the-loop.md` — HITL patterns
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/references/coagents-shared-state.md` — useAgent/useCoAgent
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/references/generative-ui.md` — Generative UI patterns
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/references/python-sdk.md` — Python SDK reference

**Read (existing implementation):**
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_agent.py` — CRUD graph (add interrupt())
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_tools.py` — CRUD tools (preview_write, confirm_write)
- `D:/ailocal/acm-ai/open_notebook/graphs/supervisor_agent.py` — Supervisor graph (add emit_state)
- `D:/ailocal/acm-ai/api/routers/agui_chat.py` — AG-UI endpoint registration
- `D:/ailocal/acm-ai/frontend/src/components/jobs/CrudToolRenderers.tsx` — CRUD tool renders (add HITL)
- `D:/ailocal/acm-ai/frontend/src/components/chat/ToolResultRenderers.tsx` — Tool renders (add defaultTool)
- `D:/ailocal/acm-ai/frontend/src/components/chat/SmartChatPanel.tsx` — Chat panel (add stateRender)
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useSmartChat.ts` — Agent hook (migrate to useAgent)
- `D:/ailocal/acm-ai/frontend/src/components/chat/WriteConfirmationCard.tsx` — Write preview card
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/ToolErrorCard.tsx` — Error card
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/ACMTableResult.tsx` — ACM table render
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/ACMStatsResult.tsx` — Stats render
- `D:/ailocal/acm-ai/frontend/src/lib/types/smart-chat.ts` — Agent state types

**Modify (backend):**
- `D:/ailocal/acm-ai/pyproject.toml` — Add copilotkit>=0.1.78 dependency
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_agent.py` — Add interrupt() for HITL approval
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_tools.py` — Add bulk_preview_write, bulk_confirm_write
- `D:/ailocal/acm-ai/open_notebook/graphs/supervisor_agent.py` — Add copilotkit_emit_state
- `D:/ailocal/acm-ai/api/routers/agui_chat.py` — Migrate to CopilotKitRemoteEndpoint (optional)

**Modify (frontend):**
- `D:/ailocal/acm-ai/frontend/src/components/jobs/CrudToolRenderers.tsx` — Replace toast with useLangGraphInterrupt
- `D:/ailocal/acm-ai/frontend/src/components/chat/ToolResultRenderers.tsx` — Add useDefaultTool
- `D:/ailocal/acm-ai/frontend/src/components/chat/SmartChatPanel.tsx` — Add useCoAgentStateRender
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useSmartChat.ts` — Migrate useCoAgent → useAgent

**Create (frontend — new components):**
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` — HITL approval UI
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/BulkPreviewCard.tsx` — Bulk operation preview
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` — Building data in chat
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/ItemDetailCard.tsx` — ACM item detail in chat
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/WriteDiffView.tsx` — Old→new field diff
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/ExtractionProgress.tsx` — Extraction progress render
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/DefaultToolFallback.tsx` — Default tool UI

**Create (E2E tests):**
- `D:/ailocal/acm-ai/frontend/e2e/copilotkit-supervisor-chat.spec.ts` — Supervisor chat E2E
- `D:/ailocal/acm-ai/frontend/e2e/copilotkit-crud-chat.spec.ts` — CRUD chat + HITL E2E
- `D:/ailocal/acm-ai/frontend/e2e/copilotkit-tool-rendering.spec.ts` — Tool card rendering E2E

---

## Plan

Read `docs/sprint-artifacts/copilotkit-audit/task_plan.md` before starting. Create new plan files for this session.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-impl/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-impl/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/copilotkit-impl/progress.md

### Implementation Phases

#### Phase 1 — Backend Foundation (sequential)
1. Install `copilotkit>=0.1.78` Python SDK: `uv add copilotkit`
2. Add `interrupt()` to CRUD graph preview-write flow:
   - Before `confirm_write` execution: `result = interrupt({"type": "write_approval", "preview": preview_data})`
   - Resume with `Command(resume={"approved": True/False, "edits": {...}})`
3. Add `copilotkit_emit_state` to supervisor graph nodes for intermediate progress
4. Add bulk write tools: `preview_bulk_write`, `confirm_bulk_write`
5. Optionally migrate `agui_chat.py` to use `CopilotKitRemoteEndpoint` + `LangGraphAgent`

#### Phase 2 — Frontend HITL + useAgent (parallel subagents)
1. Create `HITLApprovalDialog.tsx` — approve/reject/edit UI component
2. Replace toast-based CRUD confirmation with `useLangGraphInterrupt`:
   ```tsx
   useLangGraphInterrupt({
     enabled: ({ eventValue }) => eventValue.type === 'write_approval',
     render: ({ event, resolve }) => (
       <HITLApprovalDialog
         preview={event.value.preview}
         onApprove={(edits) => resolve({ approved: true, edits })}
         onReject={() => resolve({ approved: false })}
       />
     ),
   })
   ```
3. Migrate `useSmartChat.ts` from `useCoAgent` → `useAgent`
4. Add `useCoAgentStateRender` to SmartChatPanel for supervisor progress
5. Add `useDefaultTool` fallback renderer

#### Phase 3 — Generative UI Components (parallel subagents)
1. Create `BuildingSummaryCard.tsx` — rich building data card for chat
2. Create `ItemDetailCard.tsx` — expandable ACM item card with all fields
3. Create `WriteDiffView.tsx` — side-by-side old→new for field changes
4. Create `BulkPreviewCard.tsx` — batch operation preview with per-row approve/reject
5. Create `ExtractionProgress.tsx` — useCoAgentStateRender extraction progress

#### Phase 4 — E2E Tests with Screenshot Verification (sequential, after implementation)
1. Set up Playwright config for CopilotKit chat testing
2. **Supervisor chat test**: Navigate to source page → open chat → send message → verify assistant response appears → screenshot
3. **Tool rendering test**: Trigger ACM search via chat → verify ACMTableResult card renders → screenshot
4. **CRUD chat test**: Navigate to job page → open CRUD chat → request record update → verify HITL approval dialog appears → approve → verify confirmation → screenshot
5. **Bulk operation test**: Request bulk update → verify BulkPreviewCard → approve → screenshot
6. **Error state test**: Trigger tool error → verify ToolErrorCard renders → screenshot
7. **Chat suggestions test**: Open empty chat → verify useCopilotChatSuggestions renders suggestions → screenshot
8. **useCopilotReadable test**: Verify agent response references page context (sourceId, notebookId)

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items in parallel.

### Phase 1 — Backend (sequential, one agent)

Single `backend-specialist` agent:
- Install copilotkit Python SDK
- Redesign CRUD graph with interrupt()
- Add copilotkit_emit_state to supervisor
- Add bulk write tools
- Run `uv run ruff check .` and `uv run pytest tests/ -x` after changes

### Phase 2 — Frontend (parallel subagents after backend completes)

Subagents:
- **hitl-implementer** (sonnet): useLangGraphInterrupt + HITLApprovalDialog + useAgent migration
- **genui-builder** (sonnet): BuildingSummaryCard, ItemDetailCard, WriteDiffView, BulkPreviewCard, ExtractionProgress, DefaultToolFallback
- After both complete: `cd frontend && npm run build && npm run lint`

### Phase 3 — E2E Testing (sequential, after frontend build passes)

Single `e2e-tester` agent:
- Write all Playwright specs
- Run each test with `npx playwright test <spec>`
- Capture screenshots to `docs/sprint-artifacts/copilotkit-impl/screenshots/`
- Report pass/fail with screenshot evidence

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "copilotkit" → query-docs for "useLangGraphInterrupt interrupt human-in-the-loop approval HITL resolve"
2. resolve-library-id for "copilotkit" → query-docs for "useAgent useCoAgent v2 shared state agentId setState time-travel"
3. resolve-library-id for "copilotkit" → query-docs for "useCoAgentStateRender intermediate state progress node render"
4. resolve-library-id for "copilotkit" → query-docs for "useDefaultTool useRenderToolCall fallback renderer"
5. resolve-library-id for "copilotkit" → query-docs for "copilotkit Python SDK FastAPI copilotkit_emit_state copilotkit_interrupt LangGraphAgent"
6. resolve-library-id for "langgraph" → query-docs for "interrupt Command resume human-in-the-loop approval checkpointer"
7. resolve-library-id for "langgraph" → query-docs for "streaming StateGraph MemorySaver SqliteSaver persist"
8. resolve-library-id for "playwright" → query-docs for "screenshot test expect toHaveScreenshot locator"

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass, excluding 3 known pre-existing failures)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors, warnings OK)
- [ ] `uv run python -c "from copilotkit import LangGraphAgent; print('SDK OK')"` — copilotkit SDK installed
- [ ] Verify CRUD graph has interrupt() — `grep "interrupt(" open_notebook/graphs/crud_agent.py`
- [ ] Verify useAgent replaces useCoAgent — `grep "useAgent" frontend/src/lib/hooks/useSmartChat.ts`
- [ ] Verify useLangGraphInterrupt exists — `grep "useLangGraphInterrupt" frontend/src/components/jobs/CrudToolRenderers.tsx`
- [ ] Verify useCoAgentStateRender exists — `grep "useCoAgentStateRender" frontend/src/components/chat/SmartChatPanel.tsx`
- [ ] Verify useDefaultTool exists — `grep "useDefaultTool" frontend/src/components/chat/ToolResultRenderers.tsx`
- [ ] E2E: `npx playwright test copilotkit-supervisor-chat` — PASS with screenshot
- [ ] E2E: `npx playwright test copilotkit-crud-chat` — PASS with screenshot
- [ ] E2E: `npx playwright test copilotkit-tool-rendering` — PASS with screenshot
- [ ] All screenshots saved to `docs/sprint-artifacts/copilotkit-impl/screenshots/`
- [ ] Update `docs/sprint-artifacts/copilotkit-impl/progress.md` with final status

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 20+ | Audit artifacts, skill references, existing CopilotKit code |
| MODIFY | 8 | pyproject.toml, crud_agent.py, crud_tools.py, supervisor_agent.py, CrudToolRenderers.tsx, ToolResultRenderers.tsx, SmartChatPanel.tsx, useSmartChat.ts |
| CREATE | 10 | HITLApprovalDialog.tsx, BulkPreviewCard.tsx, BuildingSummaryCard.tsx, ItemDetailCard.tsx, WriteDiffView.tsx, ExtractionProgress.tsx, DefaultToolFallback.tsx, 3 E2E test specs |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
feat(copilotkit): implement HITL, generative UI, and E2E tests

- Add LangGraph interrupt() + useLangGraphInterrupt for CRUD write approval
- Install copilotkit Python SDK with copilotkit_emit_state for state streaming
- Migrate useCoAgent → useAgent v2 for time-travel and multi-agent
- Add useCoAgentStateRender for supervisor progress display
- Add useDefaultTool fallback renderer for unregistered tool calls
- Create generative UI components: BuildingSummaryCard, ItemDetailCard,
  WriteDiffView, BulkPreviewCard, ExtractionProgress, HITLApprovalDialog
- Add bulk CRUD operation tools and multi-step approval flow
- Add E2E Playwright tests with screenshot verification for all chat flows

Co-Authored-By: Claude <noreply@anthropic.com>
```
