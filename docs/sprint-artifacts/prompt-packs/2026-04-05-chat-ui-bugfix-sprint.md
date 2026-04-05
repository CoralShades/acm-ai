# Session: Fix 5 chat & UI bugs with multi-agent team — model selection, session persistence, record counts, extraction status

## Skills to Load

/copilotkit — CopilotKit useCoAgent, AG-UI, tool rendering patterns
/langgraph-fundamentals — LangGraph StateGraph, nodes, edges, Command, Send, interrupt
/langgraph-persistence — checkpointer persistence, thread state, AsyncSqliteSaver
/langgraph-human-in-the-loop — interrupt(), Command(resume=), approval patterns
/langchain-fundamentals — LangChain create_agent, tools, middleware, model init
/langchain-middleware — HumanInterruptMiddleware, structured output
/langchain-dependencies — package versions, installation, dependency management
/langchain-rag — document loaders, RecursiveCharacterTextSplitter, retrieval patterns
/framework-selection — LangChain vs LangGraph vs Deep Agents decision framework
/acm-observability — Langfuse traces, LangGraph state inspection, cost analysis
/systematic-debugging — structured root-cause diagnosis before fixing
/e2e-test — Playwright E2E testing with self-healing selectors
/agent-browser — browser automation for real user simulation
/vaea-ui — VAEA design system enforcement for UI fixes
/verification-before-completion — verify all work before claiming done
/planning-with-files — persistent markdown plan for session continuity

---

## Prerequisites

Before starting this session, verify:

- Agent Teams enabled: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `.claude/settings.json` env
- Claude Code version >= 2.1.32: `claude --version`
- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503`
- Worker running: check `ps aux | grep run_worker` or Windows task manager
- Branch: `git checkout -b fix/chat-ui-bugs-2026-04-05` from `main`
- Plan files exist:
  - `D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md`
  - `D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md`
  - `D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md`

---

## Project Glossary

| Term | Definition |
|------|-----------|
| UnifiedChatPanel | Single chat component replacing SmartChatPanel + JobCrudChatPanel. Uses CopilotKit `useCoAgent` with `acm_agent`. |
| MemorySaver | In-memory LangGraph checkpointer — loses all state on API restart. Current chat persistence layer. |
| ChatModelSelector | Dropdown in chat panel for switching LLM model. Lists models from SurrealDB `model` table. |
| model_provisioning.py | Backend module that registers models in SurrealDB and maps them to LangChain/Esperanto providers. |
| ExtractionStatusBanner | Frontend component showing extraction progress/cancel button. Should reflect `source.processing_status`. |
| building_record.record_count | Field on BuildingRecord that should hold the count of ACM items per building. Currently NULL for all records (#119). |
| chatSessionStore | Zustand store managing chat session CRUD — fetch, create, rename, delete via REST API. |
| useUnifiedChat | React hook bridging CopilotKit `useCoAgent<UnifiedAgentState>` with `useRef` stability pattern. |
| AG-UI Protocol | Event streaming protocol between CopilotKit frontend and FastAPI backend via `ag-ui-langgraph`. |
| Agent Team | Experimental Claude Code feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`). Spawns multiple independent CC instances with shared task list, inter-agent messaging, and centralized lead. Unlike subagents, teammates communicate directly with each other. |
| TeamCreate | Tool to create an agent team. The main session becomes team lead. Teammates are spawned as full independent CC sessions. |
| Shared Task List | Coordination mechanism for agent teams. Tasks have 3 states (pending/in-progress/completed) with dependency tracking and file-locking for claim safety. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. Lives in `.claude/skills/`. |
| Subagent | Claude Code session spawned via Task tool. Reports back to caller only. Use Agent Teams when teammates need to communicate with each other. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. Teammates can require plan approval before implementing. |

---

## Current State

- Branch: `main` (last commit: `f6c76cef` — Add verify job detail retry image)
- PR #122 merged: 14 chat pipeline bug fixes (source_id propagation, HITL approval, concurrency)
- 12 open GitHub issues (see findings.md for full cross-reference)
- Chat system working end-to-end but with 4 user-reported bugs + 1 audit task
- MemorySaver in use (volatile — no durable persistence)
- Latest Anthropic models NOT registered (claude-haiku-4-5, claude-opus-4-6)

---

## Key Files

**Read (reference):**
- `D:/ailocal/acm-ai/api/model_provisioning.py` — model registration and provider mapping
- `D:/ailocal/acm-ai/open_notebook/graphs/checkpointer.py` — MemorySaver singleton
- `D:/ailocal/acm-ai/open_notebook/graphs/unified_agent.py` — unified chat graph
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — extraction pipeline (record_count)
- `D:/ailocal/acm-ai/api/routers/unified_sessions.py` — session CRUD REST API
- `D:/ailocal/acm-ai/frontend/src/components/chat/ChatModelSelector.tsx` — model dropdown
- `D:/ailocal/acm-ai/frontend/src/components/jobs/ExtractionStatusBanner.tsx` — extraction status UI
- `D:/ailocal/acm-ai/frontend/src/components/jobs/JobControls.tsx` — job action buttons
- `D:/ailocal/acm-ai/frontend/src/lib/stores/chatSessionStore.ts` — session state management
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useUnifiedChat.ts` — CopilotKit bridge hook

**Modify:**
- `D:/ailocal/acm-ai/api/model_provisioning.py` — update model registry with latest Anthropic models
- `D:/ailocal/acm-ai/open_notebook/graphs/checkpointer.py` — potentially upgrade to durable checkpointer
- `D:/ailocal/acm-ai/frontend/src/components/jobs/ExtractionStatusBanner.tsx` — fix stale state
- `D:/ailocal/acm-ai/frontend/src/lib/hooks/useUnifiedChat.ts` — add session history loading
- `D:/ailocal/acm-ai/frontend/src/lib/stores/chatSessionStore.ts` — add message restoration

**Create (if needed):**
- `D:/ailocal/acm-ai/migrations/XXXXXX_backfill_building_record_count.surql` — backfill migration

---

## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md

### Bug Details

**B1 — Model Selection (P1)**
Most models are unrecognized in the LangChain workflow. Haiku doesn't work, but Sonnet and llama3.1:8b do. Need to:
- Update model provisioning with latest Anthropic model IDs (claude-sonnet-4-5-20250514, claude-haiku-4-5-20251001, claude-opus-4-6-20250610)
- Sync available Ollama models and remove duplicates
- Ensure model name format matches what LangChain's `init_chat_model()` expects

**B2 — Chat Session Persistence (P1)**
When navigating to previous chats, they don't load previous context — it's empty. On page refresh, it should load the last conversation (within 10 min) or create a new one. Need to:
- Implement message history restoration from checkpointer on session switch
- Add auto-restore-or-create logic on page load/refresh
- Consider upgrading MemorySaver to AsyncSqliteSaver for durability

**B3 — Building Record Count NULL (P1, GitHub #119)**
When querying "list all buildings" in chat, it shows all 6 Alexander + 1 Broadmeadows buildings correctly, but tool cards and messages show 0 records. The frontend grid shows mapped records. The `building_record.record_count` field is NULL for all records in SurrealDB.

**B4 — Cancel Extraction Button on Completed Job (P2)**
Alexander job page still shows "Cancel Extraction" button even though extraction is already finished. Need to find root cause (not just hide it) using `/vaea-ui` design analysis.

**B5 — GitHub Issue Audit (P3)**
Cross-check all 12 open GitHub issues against current codebase state. Close any that are resolved. Triage the rest.

---

## Agent Strategy

Strategy: AGENT-TEAMS (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

Use `TeamCreate` to create a coordinated agent team with shared task list, inter-agent messaging,
and centralized management. The main session acts as Team Lead. Teammates are spawned as full
independent Claude Code instances that communicate via mailbox and shared task list.

> **Important**: Agent Teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json env.
> Each teammate has its own context window and loads project CLAUDE.md, MCP servers, and skills
> automatically. The lead's conversation history does NOT carry over to teammates.

### Prerequisite — Enable Agent Teams

Ensure this is in `.claude/settings.json` (or `.claude/settings.local.json`):
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Team Creation

```text
Create an agent team called "chat-bugfix-sprint" to fix 5 bugs across the chat and UI stack.
Spawn 7 teammates across 4 squads:

Squad 2 — Investigation (spawn in parallel, require plan approval):
- "ux-specialist" (opus): B4 root cause via /vaea-ui, extraction status UI audit, design enforcement
- "log-auditor" (opus): Tail SurrealDB/worker/API/frontend logs, Langfuse traces, SSE events
- "devils-advocate" (opus): Adversarial review of every fix — edge cases, regressions, silent failures

Squad 3 — Development (spawn after Squad 2 findings, require plan approval):
- "backend-dev" (opus): B1 model provisioning, B2 checkpointer upgrade, B3 record_count backfill
- "frontend-dev" (opus): B2 session restoration UI, B4 extraction status fix, model selector

Squad 4 — Verification & Docs (spawn after development):
- "browser-tester" (sonnet): /agent-browser E2E testing, real user messages, screenshot evidence
- "docs-updater" (haiku): sprint-status.yaml, architecture.md, prd.json, GitHub issues
```

### Team Composition (7 teammates + 1 lead = 8 agents)

**Lead (this session) — Command & Control**

| Role | Model | Responsibilities |
|------|-------|-----------------|
| Team Lead | opus | Coordinates all squads, creates shared tasks, reviews plans, gates merges, synthesizes findings |

**Squad 2 — Investigation (parallel, plan approval required)**

| Name | Model | Subagent Type | Focus | Skills |
|------|-------|---------------|-------|--------|
| `ux-specialist` | opus | `frontend-specialist` | B4 extraction status root cause, VAEA design audit | /vaea-ui, /baseline-ui |
| `log-auditor` | opus | `acm-observability-debugger` | Log tailing, Langfuse traces, SSE events, error correlation | /acm-observability |
| `devils-advocate` | opus | `e36-devils-advocate` | Adversarial review, edge cases, false positives, regressions | /systematic-debugging, /find-bugs |

**Squad 3 — Development (parallel per bug, plan approval required)**

| Name | Model | Subagent Type | Focus | Skills |
|------|-------|---------------|-------|--------|
| `backend-dev` | opus | `backend-specialist` | B1 model provisioning, B2 checkpointer, B3 record_count, API | /langchain-fundamentals, /langgraph-persistence, /langchain-dependencies |
| `frontend-dev` | opus | `frontend-specialist` | B2 session UI, B4 extraction banner, model selector, VAEA | /copilotkit, /vaea-ui, /react-best-practices |

**Squad 4 — Verification & Documentation (sequential after dev)**

| Name | Model | Subagent Type | Focus | Skills |
|------|-------|---------------|-------|--------|
| `browser-tester` | sonnet | `acm-e2e-tester` | E2E browser testing, user message simulation, screenshots | /agent-browser, /e2e-test, /acm-observability |
| `docs-updater` | haiku | `docs-specialist` | Sprint-status, architecture, prd, GitHub issues, CLAUDE.md | /sprint-status |

### Agent Teams Coordination Protocol

Teammates coordinate via **shared task list** and **direct messaging** (not just report-back).

**Phase 1 — Investigation (parallel teammates)**
1. Lead creates tasks in shared list for each investigation item (B1-B4 root cause)
2. Squad 2 teammates self-claim tasks and investigate in parallel
3. Teammates message each other directly to cross-check findings (e.g., log-auditor shares trace ID with ux-specialist)
4. Devil's Advocate challenges Squad 2 findings before Lead approves
5. Lead synthesizes findings → updates `findings.md`

**Phase 2 — Development (parallel teammates, plan approval)**
6. Lead creates implementation tasks based on Phase 1 findings
7. Backend Dev + Frontend Dev claim tasks and submit plans for approval
8. Lead reviews plans → approves or rejects with feedback
9. Approved teammates exit plan mode and implement
10. Devil's Advocate reviews each completed task — blocks if edge cases found
11. Backend Dev + Frontend Dev message each other for B2 (cross-layer coordination)

**Phase 3 — Integration & E2E (sequential)**
12. Lead creates E2E verification tasks after dev tasks complete
13. Browser Tester claims and runs full suite with real user messages:
    - "list all buildings" → verify record counts in tool cards
    - "show ACM stats" → verify tool rendering and animated components
    - Select Haiku model → send message → verify LLM responds
    - Navigate between sessions → verify history loads
    - Refresh page → verify auto-restore or new session
    - Check Alexander job → verify no cancel button
14. Log Auditor monitors all logs during E2E run — messages Browser Tester if errors found

**Phase 4 — Documentation & Close (parallel)**
15. Docs Specialist claims doc tasks and updates all artifacts
16. Lead creates/updates GitHub issues, runs final verification checklist
17. Devil's Advocate does final adversarial review of the full diff
18. Lead cleans up the team: shut down all teammates → `Clean up the team`

### Key Agent Teams Mechanics

- **Task claiming**: uses file locking to prevent race conditions when multiple teammates try to claim the same task
- **Plan approval**: Squad 2 and Squad 3 teammates must submit plans. Lead approves/rejects autonomously based on Phase 1 findings
- **Direct messaging**: teammates can message each other by name (e.g., `backend-dev` → `frontend-dev` for B2 cross-layer work)
- **Broadcast**: Lead can broadcast to all teammates simultaneously (use sparingly)
- **Task dependencies**: Phase 3 tasks depend on Phase 2 completion — auto-unblock when deps finish
- **Shutdown**: Lead sends shutdown request to each teammate when done. Teammates can approve/reject
- **Cleanup**: Only the Lead runs cleanup. Shut down all teammates first

### Fallback: Subagent Dispatch Pattern

If Agent Teams are not available (env var not set or version < 2.1.32), fall back to standard subagent dispatch:

1. Main session acts as Team Lead
2. Parallel `Task` tool calls for Squad 2 (3 subagents at once)
3. Wait → synthesize findings
4. Parallel `Task` tool calls for Squad 3 (2 subagents at once)
5. Wait → sequential `Task` calls for Squad 4 (Browser Tester, then Docs)

This loses inter-agent messaging and shared task list but preserves parallel execution.

### User Interview Protocol

Use `AskUserQuestion` tool (10+ rounds) to gather:
- Which models specifically fail? (exact names from the dropdown)
- Which Alexander job source_id? (for targeted debugging)
- Are you testing on localhost:8503 or production?
- Which browser? (for DevTools targeting)
- Any recent API/worker restarts?
- What does the network tab show when model selection fails?
- What error appears in console when chat session loads empty?
- Can you reproduce B4 consistently or intermittently?
- Priority order if time is limited?
- Any other bugs not listed?

---

## Context7 Directives

Run these at session start to load current library documentation. Each teammate should fetch
the docs relevant to their squad assignment.

**All teammates (core project deps):**
1. resolve-library-id for "copilotkit" → query-docs for "useCoAgent useLangGraphInterrupt session management AG-UI"
2. resolve-library-id for "langgraph" → query-docs for "StateGraph nodes edges Command interrupt checkpointer persistence"
3. resolve-library-id for "langchain" → query-docs for "init_chat_model ChatAnthropic ChatOllama create_agent tools"

**Backend Dev specifically:**
4. resolve-library-id for "langgraph" → query-docs for "AsyncSqliteSaver PostgresSaver checkpointer thread state replay"
5. resolve-library-id for "langchain" → query-docs for "HumanInterruptMiddleware structured output middleware"
6. resolve-library-id for "langchain" → query-docs for "package versions installation dependencies pip uv"
7. resolve-library-id for "langchain" → query-docs for "RAG document loaders RecursiveCharacterTextSplitter retrieval"

**Frontend Dev specifically:**
8. resolve-library-id for "framer-motion" → query-docs for "AnimatePresence motion.div spring transitions stagger"
9. resolve-library-id for "ag-ui-protocol" → query-docs for "LangGraphAGUIAgent event streaming protocol"
10. resolve-library-id for "zustand" → query-docs for "create store persist middleware"

**Browser Tester specifically:**
11. resolve-library-id for "playwright" → query-docs for "page locator click fill expect assertions"

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `cd "D:/ailocal/acm-ai" && uv run ruff check .` — Python lint (0 errors)
- [ ] `cd "D:/ailocal/acm-ai" && uv run pytest tests/ -x` — Backend tests (all pass)
- [ ] `cd "D:/ailocal/acm-ai/frontend" && npm run build` — Frontend build (0 errors)
- [ ] `curl http://localhost:5055/api/models` — API returns models including latest Anthropic
- [ ] `curl http://localhost:5055/api/models/defaults` — Defaults resolve to valid model names
- [ ] Chat: select Haiku → send "hello" → verify LLM responds (no error)
- [ ] Chat: navigate to previous session → verify messages load
- [ ] Chat: refresh page → verify last session auto-loads or new session created
- [ ] Chat: send "list all buildings" → verify tool cards show correct record counts
- [ ] Alexander job page: verify NO "Cancel Extraction" button shown
- [ ] Screenshot evidence saved to `docs/sprint-artifacts/evidence/`
- [ ] All 4 bugs verified fixed via /agent-browser E2E

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| MODIFY | 8+ | model_provisioning.py, checkpointer.py, ExtractionStatusBanner.tsx, useUnifiedChat.ts, chatSessionStore.ts, ChatModelSelector.tsx, JobControls.tsx, unified_agent.py |
| CREATE | 1-2 | backfill_building_record_count.surql, potentially AsyncSqliteSaver migration |
| DELETE | 0 | — |

---

## Commit Template

```
fix(chat): resolve model selection, session persistence, record counts, extraction status

- B1: Update model registry with latest Anthropic + Ollama model sync
- B2: Implement chat session history loading and auto-restore on refresh
- B3: Populate building_record.record_count after extraction
- B4: Fix extraction status banner showing cancel on completed jobs

Closes #106, #118, #119

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```
