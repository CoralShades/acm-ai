# Session: Audit CopilotKit integration and implement missing features across frontend, backend, and AI layers

## Skills to Load

/copilotkit — CopilotKit hooks, components, runtime, CoAgent, AG-UI patterns
/langgraph-fundamentals — LangGraph StateGraph, nodes, edges, streaming, interrupt()
/langchain-dependencies — Package versions, environment setup, dependency management
/frontend-design — Production-grade frontend interfaces, polished UI
/uncodixfy — Prevent generic AI UI patterns, enforce clean human-designed aesthetics
/ui-ux-pro-max — Seamless UI/UX across all screen types with animations and state management
/planning-with-files — Persistent markdown plan for session continuity
/find-skills — Discover additional skills as needed during session
/verification-before-completion — Verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503`
- Branch: `git checkout ACMV3`
- CopilotKit packages installed: `cd frontend && npm ls @copilotkit/react-core`
- Python AG-UI package: `cd "$CLAUDE_PROJECT_DIR" && uv run python -c "import ag_ui_langgraph; print('OK')"`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| CopilotKit | Real-time AI copilot framework (v1.51.3) providing hooks (`useCopilotAction`, `useCoAgent`) and chat UI (`CopilotChat`). Installed at `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`. |
| AG-UI Protocol | Event protocol from CopilotKit that streams agent actions to the frontend. Backend uses `ag-ui-langgraph` Python package to bridge LangGraph graphs. |
| CopilotRuntime | Server-side runtime that routes chat messages to agent backends. Two instances: `/api/copilotkit` (supervisor) and `/copilot-crud` (CRUD). |
| useCoAgent | CopilotKit hook binding frontend to a LangGraph agent's shared state. Currently used for `SupervisorAgentState` sync (source_id, notebook_id, acm_results). |
| useCopilotAction | Hook registering frontend-rendered tool results. Currently 11 registrations (9 search + 2 CRUD) with `available: 'disabled'` (render-only, not client-callable). |
| useCopilotReadable | Hook exposing frontend state to the AI agent as context. **NOT currently used** — state passes via `useCoAgent` instead. |
| LangGraph interrupt() | Function that pauses graph execution for human approval. **NOT currently used** — CRUD confirmation uses text-based "confirm {id}" pattern. |
| SupervisorState | LangGraph `TypedDict` for the supervisor agent: messages, source_id, notebook_id, include_acm_context, active_agents, acm_results, search_results. |
| CRUDAgentState | LangGraph `TypedDict` for the CRUD agent: messages, source_id. Tools: query_job_records, preview_write, confirm_write. |
| PipelineEventBus | Pub/sub bus emitting structured events to SSE endpoint during extraction. Separate from CopilotKit streaming. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |
| Generative UI | CopilotKit pattern where the AI agent returns React components (via `useCopilotAction` render callbacks) instead of plain text. |
| HITL | Human-in-the-loop — pattern where agent pauses for user approval before executing actions. CopilotKit supports via `useLangGraphInterrupt`. |

---

## Current State

- Branch: ACMV3 (last commit: `54ec8f3d feat(ui): redesign Jobs Dashboard`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- CopilotKit version: `^1.51.3` (3 packages in frontend/package.json)
- Python AG-UI: `ag-ui-langgraph>=0.0.25` in pyproject.toml
- Two chat runtimes active: supervisor (read-only at `/api/copilotkit`) and CRUD (write at `/copilot-crud`)
- CopilotProvider wraps entire dashboard layout with error boundary
- 11 `useCopilotAction` render-only tool registrations (9 search + 2 CRUD)
- 1 `useCoAgent` binding to supervisor agent state
- **Missing**: useCopilotReadable, useCopilotChat, useLangGraphInterrupt, useHumanInTheLoop, CopilotPopup, CopilotSidebar, CopilotTextarea, CopilotTask, useAgent (v2), copilotkit Python SDK
- Context7 MCP: may need session restart if non-functional — use `resolve-library-id` for "copilotkit" then `query-docs`

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (reference):**
- `D:/ailocal/acm-ai/frontend/package.json` — CopilotKit dependency versions
- `D:/ailocal/acm-ai/frontend/next.config.ts` — serverExternalPackages for @copilotkit/runtime
- `D:/ailocal/acm-ai/pyproject.toml` — ag-ui-langgraph dependency
- `D:/ailocal/acm-ai/docs/ag-ui-pipeline-spec.md` — AG-UI integration spec
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/SKILL.md` — CopilotKit skill reference
- `D:/ailocal/acm-ai/.claude/skills/copilotkit/references/` — 8 reference docs (ag-ui-protocol, coagents-shared-state, generative-ui, human-in-the-loop, python-sdk, runtime-adapters, styling-customization, troubleshooting)

**Read + Audit (existing CopilotKit code):**
- `D:/ailocal/acm-ai/frontend/src/components/providers/CopilotProvider.tsx` — CopilotKit provider with error boundary
- `D:/ailocal/acm-ai/frontend/src/app/api/copilotkit/route.ts` — Supervisor runtime route
- `D:/ailocal/acm-ai/frontend/src/app/copilot-crud/route.ts` — CRUD runtime route
- `D:/ailocal/acm-ai/frontend/src/components/chat/SmartChatPanel.tsx` — Main CopilotChat UI
- `D:/ailocal/acm-ai/frontend/src/components/chat/ToolResultRenderers.tsx` — 9 useCopilotAction render registrations
- `D:/ailocal/acm-ai/frontend/src/components/jobs/JobCrudChatPanel.tsx` — CRUD chat panel (nested CopilotKit provider)
- `D:/ailocal/acm-ai/frontend/src/components/jobs/CrudToolRenderers.tsx` — 2 CRUD tool renderers
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useSmartChat.ts` — useCoAgent binding
- `D:/ailocal/acm-ai/frontend/src/lib/types/smart-chat.ts` — SupervisorAgentState types
- `D:/ailocal/acm-ai/frontend/src/components/chat/ACMAssistantMessage.tsx` — Custom assistant message
- `D:/ailocal/acm-ai/frontend/src/app/globals.css` — CopilotKit CSS import

**Read + Audit (backend AG-UI):**
- `D:/ailocal/acm-ai/api/routers/agui_chat.py` — AG-UI endpoint registration
- `D:/ailocal/acm-ai/api/main.py` — AGUI endpoint mounting
- `D:/ailocal/acm-ai/open_notebook/graphs/supervisor_agent.py` — Supervisor LangGraph graph
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_agent.py` — CRUD LangGraph graph
- `D:/ailocal/acm-ai/open_notebook/extractors/agui_event_emitter.py` — AG-UI event emitter
- `D:/ailocal/acm-ai/open_notebook/graphs/agent_cards.py` — A2A agent card metadata

**Potentially Modify (based on audit findings):**
- Frontend components for new CopilotKit features
- Backend graphs for LangGraph interrupt() HITL
- Package versions if upgrade needed
- New hooks/components for missing features

---

## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items in parallel.

### Phase 1 — Research (parallel subagents)

Subagents:
- **copilotkit-docs-researcher** (sonnet): Fetch CopilotKit v1 and v2 documentation via Context7 MCP. Topics: setup, hooks (useCopilotAction, useCopilotReadable, useCoAgent, useAgent), CopilotRuntime, CoAgents with LangGraph, HITL (useLangGraphInterrupt), generative UI, streaming, multi-agent, shared state, subgraphs, chat-with-your-data. Also fetch from https://docs.copilotkit.ai/llms.txt via WebFetch.
- **langgraph-docs-researcher** (sonnet): Fetch LangGraph documentation via Context7 MCP. Topics: interrupt(), Command(resume=), human-in-the-loop, streaming, subgraphs, multi-agent patterns.
- **codebase-gap-analyzer** (sonnet): Deep-read ALL existing CopilotKit code files listed above. For each feature in the audit list, determine: (a) is it implemented, (b) if yes — is it correct per current docs, (c) if no — what's needed. Produce a gap matrix.

### Phase 2 — Implementation Planning (sequential)

After research completes:
- Cross-reference CopilotKit v2 docs against current v1.51.3 implementation
- Identify breaking changes if upgrading to v2
- Prioritize features by impact: HITL > shared state > generative UI > streaming > multi-agent
- Update task_plan.md with concrete implementation steps

### Phase 3 — Implementation (parallel subagents)

Subagents:
- **frontend-implementer** (sonnet): Implement missing CopilotKit hooks and components
- **backend-implementer** (sonnet): Add LangGraph interrupt() support, update AG-UI endpoints
- **ui-ux-reviewer** (sonnet): Review all chat UI for design quality using /frontend-design + /uncodixfy + /ui-ux-pro-max patterns

### Phase 4 — Verification (sequential)

- Run frontend build: `cd frontend && npm run build`
- Run backend tests: `uv run pytest tests/ -x`
- Run lint: `uv run ruff check .` + `cd frontend && npm run lint`
- Browser verification of chat UI on all affected pages

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "copilotkit" → query-docs for "setup installation React Next.js hooks useCopilotAction useCopilotReadable useCoAgent"
2. resolve-library-id for "copilotkit" → query-docs for "CopilotRuntime backend LangGraph CoAgent shared state"
3. resolve-library-id for "copilotkit" → query-docs for "human in the loop HITL useLangGraphInterrupt interrupt approval"
4. resolve-library-id for "copilotkit" → query-docs for "generative UI streaming multi-agent subgraphs"
5. resolve-library-id for "copilotkit" → query-docs for "CopilotChat CopilotPopup CopilotSidebar styling customization"
6. resolve-library-id for "langgraph" → query-docs for "interrupt Command resume human-in-the-loop approval"
7. resolve-library-id for "langgraph" → query-docs for "subgraphs multi-agent streaming"
8. WebFetch: https://docs.copilotkit.ai/llms.txt — full CopilotKit documentation index

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors)
- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass, excluding 3 known pre-existing failures)
- [ ] `npm ls @copilotkit/react-core` — CopilotKit package version confirmed
- [ ] Verify CopilotProvider loads without error boundary triggering
- [ ] Verify supervisor chat sends/receives messages at `/jobs/[id]/chat`
- [ ] Verify CRUD chat confirmation flow works
- [ ] Document all gaps found in findings.md
- [ ] Update task_plan.md with implementation status

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 25+ | All existing CopilotKit frontend/backend files, docs, skill references |
| MODIFY | TBD | Based on audit findings — hooks, components, graphs, package.json |
| CREATE | TBD | New components/hooks for missing CopilotKit features |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
feat(copilotkit): audit and implement missing CopilotKit features

- Audit existing CopilotKit v1.51.3 integration
- [List specific features added/fixed based on findings]

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```

---

## Audit Baseline (Pre-Session Findings)

### What EXISTS (implemented)

| Feature | Status | Files |
|---------|--------|-------|
| CopilotChat (inline) | ✅ Active | SmartChatPanel.tsx, JobCrudChatPanel.tsx |
| CopilotKit provider | ✅ Active | CopilotProvider.tsx (with error boundary) |
| useCopilotAction (render-only) | ✅ 11 registrations | ToolResultRenderers.tsx (9), CrudToolRenderers.tsx (2) |
| useCoAgent | ✅ Supervisor state sync | useSmartChat.ts |
| CopilotRuntime (supervisor) | ✅ `/api/copilotkit` | frontend/src/app/api/copilotkit/route.ts |
| CopilotRuntime (CRUD) | ✅ `/copilot-crud` | frontend/src/app/copilot-crud/route.ts |
| AG-UI backend bridge | ✅ ag-ui-langgraph | api/routers/agui_chat.py |
| Custom assistant message | ✅ Markdown + refs | ACMAssistantMessage.tsx |
| Custom chat input | ✅ ACM toggle | SmartChatInput.tsx |
| LangGraph supervisor graph | ✅ StateGraph + MemorySaver | supervisor_agent.py |
| LangGraph CRUD graph | ✅ StateGraph | crud_agent.py |
| AG-UI event emitter | ✅ Pipeline events | agui_event_emitter.py |

### What is MISSING (not implemented)

| Feature | Priority | Notes |
|---------|----------|-------|
| useCopilotReadable | Medium | State passed via useCoAgent instead — may want both |
| useCopilotChat (programmatic) | Low | Manual chat control not needed yet |
| useLangGraphInterrupt / HITL | **High** | CRUD confirmation uses text "confirm {id}" — should use proper interrupt() |
| useAgent (v2) | **High** | Still on useCoAgent (v1) — check if upgrade needed |
| CopilotPopup / CopilotSidebar | Medium | Only CopilotChat (inline) used |
| CopilotTextarea | Low | No form AI-assist use case yet |
| CopilotTask | Low | No programmatic task triggers |
| copilotkit Python SDK | Medium | Using ag-ui-langgraph directly — check if SDK adds value |
| @ag-ui/client in package.json | Low | Transitive dep only, dynamically imported |
| copilotkit_emit_state (Python) | Medium | AGUIEventEmitter fills role via SurrealDB polling |
| useCopilotAdditionalInstructions | Low | Could add system context |
| useCopilotChatSuggestions | Medium | Could improve chat UX with suggested queries |
| Multi-agent architecture | **High** | Two separate runtimes — could unify with proper multi-agent |
| Shared state (bidirectional) | **High** | useCoAgent has it, but needs review for completeness |
| Subgraph support | Medium | No subgraph integration with CopilotKit |
| Streaming improvements | Medium | Review current streaming vs CopilotKit best practices |
