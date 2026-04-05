# ACM-AI Chat System Debug & Fix — Comprehensive Prompt

> **Generated**: 2026-03-28
> **Target**: New Claude Code session with Agent Team
> **Scope**: 5 critical chat bugs in UnifiedChatPanel (CopilotKit/AG-UI path)
> **LangSmith Traces**: `b79a5e64-802d-4f9e-8d6d-49a1cc7f68f0`, `836739c3-b4b3-4ca2-b047-bf796aa3af02`

---

## INSTRUCTIONS FOR THE SESSION

### Step 0: Load ALL Required Skills (MANDATORY — do this FIRST)

Invoke every skill below before ANY investigation or coding. These are non-negotiable:

```
/systematic-debugging
/langgraph-fundamentals
/langgraph-persistence
/langgraph-human-in-the-loop
/langchain-dependencies
/langchain-middleware
/langchain-fundamentals
/multi-agent-patterns
/deep-agents-orchestration
/copilotkit
/subagent-driven-development
/planning-with-files
/vaea-ui
/e2e-test
/acm-observability
```

### Step 1: Fetch Latest Documentation via Context7

Before writing ANY code, fetch current docs for all libraries in play:

```
# CopilotKit (useRenderToolCall, useCoAgent, useLangGraphInterrupt, CopilotChat, AG-UI protocol)
context7: resolve-library-id "copilotkit" → query-docs "useRenderToolCall useCoAgent useLangGraphInterrupt AssistantMessage CopilotChat AG-UI protocol events streaming tool rendering"

# LangGraph Python (StateGraph, ToolNode, interrupt, Command, streaming, checkpointer)
context7: resolve-library-id "langgraph" → query-docs "StateGraph ToolNode interrupt Command streaming custom events tool results AG-UI FastAPI endpoint"

# AG-UI Protocol (event types, tool call events, text message content, state snapshot)
context7: resolve-library-id "ag-ui" → query-docs "AG-UI protocol events TEXT_MESSAGE_CONTENT TOOL_CALL_START TOOL_CALL_END state snapshot streaming"

# LangChain Core (tool decorator, ToolMessage, structured output)
context7: resolve-library-id "langchain" → query-docs "tool decorator ToolMessage structured output tool results return format"

# SurrealDB (query syntax, record IDs, type::thing)
context7: resolve-library-id "surrealdb" → query-docs "SurrealQL query syntax record ID type::thing WHERE clause"
```

### Step 2: Initialize Planning Files

Create these three files immediately:

**`task_plan.md`** — with all 5 issues as checkboxes
**`findings.md`** — research log (LangSmith traces, code analysis, root causes)
**`progress.md`** — session recovery journal

### Step 3: Spawn Agent Team

Create an agent team with the following structure. **All team members use `model: "opus"` except sonnet for simple tasks.**

---

## AGENT TEAM SPECIFICATION

### Team Lead (Coordinator)

```
Name: chat-debug-lead
Model: opus
Role: Pure orchestrator — delegates all work, tracks progress, synthesizes findings
Responsibilities:
  - Read task_plan.md, assign issues to specialists
  - Coordinate between frontend and backend fixes
  - Ensure fixes don't break each other
  - Update progress.md after each issue is resolved
  - Run verification after each fix
  - NEVER writes code directly
```

### Devils Advocate #1 (Code Quality)

```
Name: devils-advocate-code
Model: opus
Role: Adversarial reviewer of ALL code changes
Responsibilities:
  - Review every fix BEFORE it's committed
  - Check for regressions, missing edge cases, type safety
  - Verify fixes follow existing codebase patterns
  - Challenge assumptions about root causes
  - Ensure no orphaned imports or dead code introduced
  - Flag if a fix is treating symptoms instead of root cause
```

### Devils Advocate #2 (Functionality & UX)

```
Name: devils-advocate-ux
Model: opus
Role: Adversarial reviewer of chat UI behavior
Responsibilities:
  - Verify thinking/processing UX matches ChatGPT-style spec
  - Check tool renderers actually appear in chat flow
  - Verify SQL query results display correctly
  - Test edge cases: empty results, errors, large datasets
  - Check mobile responsiveness of chat components
  - Validate HITL approval flow works end-to-end
```

### Frontend Developer (with /vaea-ui)

```
Name: frontend-dev
Model: opus
Skills: /vaea-ui, /copilotkit, /react-best-practices
Scope: frontend/src/components/chat/**, frontend/src/lib/hooks/**, frontend/src/lib/stores/**
Responsibilities:
  - Fix Issue #1: Thinking/processing message UX
  - Fix Issue #2: Tool renderer registration and display
  - Fix Issue #5: Record preview, building preview, edit/delete components
  - Ensure all 15 useRenderToolCall registrations work
  - Clean up orphaned renderers (ToolResultRenderers.tsx, WriteConfirmationCard.tsx)
  - Follow VAEA design system for all UI changes
```

### Backend/API/Database Developer

```
Name: backend-dev
Model: opus
Skills: /langgraph-fundamentals, /langgraph-persistence, /langchain-fundamentals, /langchain-middleware
Scope: open_notebook/graphs/**, api/routers/**, open_notebook/extractors/**
Responsibilities:
  - Fix Issue #3: Tool only queries acm_record table, ignoring source metadata, job data, buildings
  - Fix Issue #4: surreal_query tool failing — debug SurrealQL generation, guardrails, schema context
  - Ensure tool_context.py correctly propagates source_id/notebook_id
  - Verify all 15 tools return properly formatted results for AG-UI protocol
  - Check unified_agent.py graph topology and tool binding
  - Inspect LangSmith traces for tool call failures
```

### Tester

```
Name: tester
Model: opus
Skills: /e2e-test, /acm-observability, /systematic-debugging
Scope: tests/**, frontend/playwright**, verification
Responsibilities:
  - Write test cases for each of the 5 issues
  - Run existing tests to verify no regressions
  - Browser-test the chat panel after fixes (agent-browser)
  - Verify tool results render in the actual UI
  - Check LangSmith traces match expected tool call patterns
  - Run `cd frontend && npm run build` after frontend changes
  - Run `uv run pytest` after backend changes
```

### Log Sentinel

```
Name: log-sentinel
Model: opus
Scope: All service logs (API, worker, LangGraph, SurrealDB, frontend console)
Responsibilities:
  - Tail API logs during chat interactions for errors
  - Monitor SurrealDB query logs for failed queries
  - Watch LangGraph execution for tool call failures
  - Check browser console for JavaScript errors
  - Track AG-UI SSE event stream for missing/malformed events
  - Report any errors found to the team lead immediately
Commands to monitor:
  - API: Check stdout/stderr of `uv run run_api.py`
  - SurrealDB: `docker logs surrealdb --tail 50`
  - Frontend: Browser DevTools console
  - LangGraph: Check Langfuse traces at localhost:3000
```

---

## THE 5 ISSUES — DETAILED INVESTIGATION PLAN

### Issue #1: Thinking/Processing Messages Show as Regular Chat Bubbles

**Symptom**: When the user asks a question, all processing/thinking messages appear as full chat bubbles instead of small, transient indicators like ChatGPT/Claude show.

**Expected Behavior (ChatGPT-style)**:
- Small collapsible "Thinking..." text that updates in real-time (e.g., "Searching ACM records...", "Analyzing data...")
- Tool steps shown as collapsible accordion items (like ToolStepItem already does)
- Thinking indicator disappears/collapses when the actual response starts streaming
- NOT a full assistant message bubble for every intermediate state

**Files to Investigate**:

| File | What to Check |
|------|--------------|
| `frontend/src/components/chat/ACMAssistantMessage.tsx` | Lines 47-58: `isLoading` handler shows three-dot bounce — is this actually triggering? Or are intermediate AG-UI events creating separate message bubbles? |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | Each `useRenderToolCall` handler — are `status === 'inProgress'` states rendering as ToolStepItem (collapsible) or as separate messages? |
| `frontend/src/components/chat/renderers/ToolStepItem.tsx` | Does the collapsible step UI actually work? Check framer-motion animations, auto-collapse timer |
| `frontend/src/components/chat/renderers/AgentActivityIndicator.tsx` | Legacy indicator — is this being used anywhere? Should it be replaced? |
| `open_notebook/graphs/unified_agent.py` | Lines 47-50: `copilotkit_emit_state` — is this emitting state updates that CopilotKit renders as messages? |

**Root Cause Hypothesis**:
The AG-UI protocol emits `TEXT_MESSAGE_CONTENT` events for intermediate agent thoughts/reasoning. CopilotKit's `<CopilotChat>` renders each `TEXT_MESSAGE_CONTENT` as a new assistant message bubble. The `ACMAssistantMessage` component's `isLoading` check only fires BEFORE the first token — once tokens start flowing, every intermediate thought becomes a visible bubble.

**Investigation Steps**:
1. Check AG-UI event stream in browser DevTools Network tab — what events does `/api/agui/chat` emit?
2. Check if `copilotkit_emit_state` is creating extra message events
3. Check CopilotKit docs (Context7) for how to suppress intermediate messages or render them differently
4. Check if the unified_agent's system prompt includes instructions that cause verbose "thinking out loud" behavior
5. Compare with CopilotKit examples for proper thinking/tool-step rendering

**Fix Direction**:
- Configure CopilotKit to NOT render intermediate reasoning as full messages
- Ensure tool calls render ONLY via `useRenderToolCall` (as ToolStepItem), not as text bubbles
- Add a custom message filter or `renderActivityMessages` to suppress thinking content
- Research CopilotKit v1.51.3 `renderActivityMessages` prop for A2UI-style rendering

---

### Issue #2: Called Tools Not Working/Visible in Frontend Chat Panel

**Symptom**: When tools are called by the agent, their results don't appear in the chat UI or appear incorrectly.

**Files to Investigate**:

| File | What to Check |
|------|--------------|
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | All 15 `useRenderToolCall` registrations — are tool names matching exactly? |
| `frontend/src/components/chat/UnifiedChatPanel.tsx` | Is `<UnifiedToolRenderers />` mounted inside the CopilotKit provider? |
| `open_notebook/graphs/unified_agent.py` | Tool binding — are all 15 tools correctly bound to the agent? |
| `open_notebook/graphs/chat_tools/acm_tools.py` | Tool return format — do tools return strings that the frontend can parse as JSON? |
| `open_notebook/graphs/crud_tools.py` | CRUD tool return format — same question |

**Root Cause Hypothesis**:
1. Tool name mismatch between backend tool `@tool` names and frontend `useRenderToolCall` name strings
2. Tool results returned as non-JSON strings that frontend parsers can't handle
3. `UnifiedToolRenderers` not mounted inside CopilotKit context (would silently fail)
4. AG-UI protocol not emitting `TOOL_CALL_START`/`TOOL_CALL_END` events correctly

**Investigation Steps**:
1. Compare all 15 tool names in `acm_tools.py` and `crud_tools.py` `@tool` decorators against `useRenderToolCall` name strings in `UnifiedToolRenderers.tsx`
2. Check if tools return `json.dumps(...)` strings that the frontend `JSON.parse()` can handle
3. Verify `UnifiedToolRenderers` is rendered inside `<CopilotChat>` (not outside the provider)
4. Check browser console for "Unknown tool" or JSON parse errors during tool execution
5. Check AG-UI SSE event stream for `TOOL_CALL_START` and `TOOL_CALL_END` events

**Known Tool Name Drift** (from codebase analysis):
- Legacy `ToolResultRenderers.tsx` registers: `search_acm_by_product`, `search_documents_vector`, `search_documents_text`
- Active `UnifiedToolRenderers.tsx` registers: `search_acm_by_material`, `search_documents`, `text_search_documents`
- Backend tools: `search_acm_by_material`, `search_documents`, `text_search_documents`
- **If any tool name doesn't match exactly, the renderer won't fire — tool result appears as raw text or nothing**

---

### Issue #3: Tools Only Query acm_record Table, Ignore Other Data

**Symptom**: When user asks questions, the agent only calls ACM-specific tools (search_acm_by_*) and fails to reference source metadata, job data, building records, or other related tables.

**Files to Investigate**:

| File | What to Check |
|------|--------------|
| `open_notebook/graphs/unified_agent.py` | System prompt template — does it instruct the agent about ALL available tools and when to use each? |
| `open_notebook/graphs/chat_tools/acm_tools.py` | 7 ACM tools — all scope to `acm_record` table only |
| `open_notebook/graphs/chat_tools/search_tools.py` | 2 search tools — query `source_embedding` and `source_insight` tables |
| `open_notebook/graphs/crud_tools.py` | `surreal_query` — CAN query any table but relies on LLM generating correct SurrealQL |
| `open_notebook/graphs/crud_tools.py` | `get_schema_info` — does it expose ALL table schemas or just acm_record? |
| `prompts/` | Chat system prompt template — what context does the agent receive about available data? |

**Root Cause Hypothesis**:
1. System prompt doesn't adequately describe the full data model (buildings, sources, metadata, jobs)
2. The 7 ACM tools are too specific — there's no generic "query buildings" or "get source metadata" tool
3. `surreal_query` exists but the LLM doesn't know when/how to use it effectively
4. `get_schema_info` may not return enough schema context for the LLM to construct proper queries
5. Tool descriptions may be too narrow, not mentioning related data

**Investigation Steps**:
1. Read the system prompt template used by `call_unified_agent` — check what data context it provides
2. Check `get_schema_info` tool — what schema does it actually return?
3. Check if there are tools for querying `source`, `building`, `notebook`, `note` tables
4. Check LangSmith traces to see what tools the agent actually calls and why
5. Evaluate whether new tools are needed (e.g., `get_source_metadata`, `list_buildings`, `get_job_status`)

**Fix Direction**:
- Enhance system prompt to describe the full data model and when to use each tool
- Add missing tools for buildings, source metadata, job data
- Improve `surreal_query` schema context to include all relevant tables
- Add tool descriptions that explicitly mention related data queries

---

### Issue #4: SQL/SurrealQL Query Tool Failing

**Symptom**: The `surreal_query` tool fails to execute queries and doesn't return results.

**Files to Investigate**:

| File | What to Check |
|------|--------------|
| `open_notebook/graphs/crud_tools.py` | `surreal_query` function — full implementation, error handling |
| `open_notebook/graphs/guardrails.py` | `ALLOWED_ACM_FIELDS`, `ALLOWED_BUILDING_FIELDS`, `validate_read_query` — are guardrails too restrictive? |
| `open_notebook/graphs/tool_context.py` | `get_tool_scope()` — is source_id correctly propagated? |
| `open_notebook/database/` | SurrealDB query execution — connection handling, error responses |

**Root Cause Hypothesis**:
1. LLM generates invalid SurrealQL syntax (e.g., SQL instead of SurrealQL)
2. Guardrails (`validate_read_query`) reject valid queries as dangerous
3. `source_id` not correctly injected into WHERE clause — `type::thing()` issue (known SurrealDB pattern)
4. `_build_source_filter()` in acm_tools doesn't handle the scope correctly
5. SurrealDB connection issues or timeout
6. Schema context given to the LLM is incomplete/outdated

**Investigation Steps**:
1. Read `surreal_query` implementation fully — trace the query generation flow
2. Check `guardrails.py` — what queries get blocked and why?
3. Check `DB_SCHEMA_CONTEXT` — does it accurately describe the current schema?
4. Run a manual test: call `surreal_query` with a simple query and check the error
5. Check LangSmith traces for the exact SurrealQL generated and the error response
6. Check if `type::thing('source:xxx')` is used correctly for record reference comparisons

**Known SurrealDB Patterns** (from CLAUDE.md):
- `type::thing()` is REQUIRED for record ref comparison — plain string comparison returns zero results
- `RecordID` objects in query results must be converted to `str()` in Python
- LLM often returns numeric fields as strings — use `BeforeValidator` for coercion

---

### Issue #5: Record Preview, Building Preview, Edit/Delete Components Not Showing

**Symptom**: Frontend components for tool results (record detail, building summary, edit, delete, update) are not visible or invokable in the chat.

**Files to Investigate**:

| File | Status |
|------|--------|
| `frontend/src/components/chat/renderers/ItemDetailCard.tsx` | **ORPHANED** — defined but not imported by any active renderer |
| `frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` | **ORPHANED** — defined but not imported by any active renderer |
| `frontend/src/components/chat/renderers/WriteDiffView.tsx` | **ORPHANED** — defined but not imported |
| `frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` | **ORPHANED** — superseded by HITLApprovalCard |
| `frontend/src/components/chat/renderers/DefaultToolFallback.tsx` | **ORPHANED** — not used by active renderers |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | Active — but missing renderers for detail/preview/edit tools |

**Root Cause Hypothesis**:
1. Components exist but are never imported/used by `UnifiedToolRenderers.tsx`
2. Tools that would trigger these components (e.g., `get_acm_record_detail`) may not be returning data in the expected format
3. HITL write flow (preview_write → interrupt → approve → execute) may not be wiring the approval card correctly
4. `useRenderToolCall` for `get_acm_record_detail` renders a single-row `ACMTableResult` — not the richer `ItemDetailCard`
5. No tool exists for "building preview" — `list_acm_buildings` returns stats, not a building detail view

**Fix Direction**:
- Wire orphaned renderers into `UnifiedToolRenderers.tsx` for appropriate tools
- Use `ItemDetailCard` for `get_acm_record_detail` instead of single-row ACMTableResult
- Use `BuildingSummaryCard` for a new `get_building_detail` tool (or enhance existing)
- Ensure HITL write flow renders `HITLApprovalCard` correctly via `useLangGraphInterrupt`
- Add edit/delete tool renderers that show confirmation dialogs before execution

---

## LANGSMITH TRACE ANALYSIS

The following traces should be inspected in LangSmith to understand real-world tool call behavior:

| Trace ID | Purpose |
|----------|---------|
| `b79a5e64-802d-4f9e-8d6d-49a1cc7f68f0` | Analyze: What tools were called? Did they succeed? What SurrealQL was generated? What was returned? |
| `836739c3-b4b3-4ca2-b047-bf796aa3af02` | Same analysis — compare patterns between two conversations |

**What to Look For in Each Trace**:
1. Which tools did the LLM decide to call? (tool_calls in AIMessage)
2. Did any tool calls fail? What error was returned in ToolMessage?
3. For `surreal_query`: What SurrealQL was generated? Was it valid? Did guardrails block it?
4. For ACM tools: Did they return results? Were results properly formatted as JSON strings?
5. For the system prompt: What instructions/context did the agent receive?
6. How many LLM turns occurred? Was the agent looping or stuck?

**Access**: LangSmith at `smith.langchain.com` or via `LANGSMITH_API_KEY` env var.

---

## VERIFICATION CHECKLIST (Post-Fix)

After ALL 5 issues are fixed, verify:

- [ ] `cd frontend && npm run build` passes (no TypeScript/import errors)
- [ ] `uv run pytest` passes (no backend test regressions)
- [ ] `uv run ruff check .` passes (no lint errors)
- [ ] Chat panel loads without errors on `/jobs/[id]` page
- [ ] Typing a question shows ChatGPT-style thinking indicator (not a full message)
- [ ] Tool calls render as collapsible `ToolStepItem` elements in the chat
- [ ] ACM search tools return and display results in `ACMTableResult`
- [ ] `surreal_query` successfully executes a query and displays results
- [ ] Agent queries MULTIPLE tables (not just acm_record) when appropriate
- [ ] `get_acm_record_detail` shows a rich record preview card
- [ ] HITL write approval flow works: preview_write → interrupt → approval card → execute
- [ ] No JavaScript errors in browser console during chat interaction
- [ ] No errors in API logs during chat interaction
- [ ] Session switching works (SessionDropdown)
- [ ] Model selection works (ChatModelSelector)

---

## CODEBASE MAP (Key Files)

### Backend — Chat Graph

| File | Purpose |
|------|---------|
| `open_notebook/graphs/unified_agent.py` | Main LangGraph agent — state, nodes, edges, tool binding |
| `open_notebook/graphs/chat_tools/__init__.py` | Tool registry — exports get_acm_tools(), get_search_tools() |
| `open_notebook/graphs/chat_tools/acm_tools.py` | 7 ACM query tools (search by risk/building/room/material, stats, detail, semantic) |
| `open_notebook/graphs/chat_tools/search_tools.py` | 2 document search tools (vector, BM25) |
| `open_notebook/graphs/crud_tools.py` | CRUD tools: surreal_query, preview_write, execute_pending_write, get_schema_info, etc. |
| `open_notebook/graphs/guardrails.py` | Query validation, allowed fields, schema context |
| `open_notebook/graphs/tool_context.py` | Thread-safe source_id/notebook_id propagation via contextvars |
| `open_notebook/graphs/checkpointer.py` | AsyncSqliteSaver checkpointer management |
| `open_notebook/graphs/utils.py` | Model provisioning with tool binding |
| `api/routers/agui_chat.py` | AG-UI chat endpoint registration (POST /api/agui/chat) |
| `api/routers/unified_sessions.py` | Chat session CRUD REST API |
| `prompts/` | Jinja2 prompt templates for the agent |

### Frontend — Chat UI

| File | Purpose |
|------|---------|
| `frontend/src/components/chat/UnifiedChatPanel.tsx` | Main chat panel — CopilotChat, HITL interrupt, suggestions |
| `frontend/src/components/chat/ACMAssistantMessage.tsx` | Custom assistant message renderer (thinking indicator, markdown) |
| `frontend/src/components/chat/SmartChatInput.tsx` | Custom input with ACM context toggle |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | 15 tool result renderers via useRenderToolCall |
| `frontend/src/components/chat/SmartChatProvider.tsx` | React context for chat scope |
| `frontend/src/components/chat/SessionDropdown.tsx` | Session switcher |
| `frontend/src/components/chat/ChatModelSelector.tsx` | Model selector |
| `frontend/src/components/chat/renderers/ToolStepItem.tsx` | Collapsible tool step UI (ChatGPT-style) |
| `frontend/src/components/chat/renderers/ACMTableResult.tsx` | ACM record table renderer |
| `frontend/src/components/chat/renderers/ACMStatsResult.tsx` | Stats cards + risk chart |
| `frontend/src/components/chat/renderers/SearchResult.tsx` | Document search results |
| `frontend/src/components/chat/renderers/HITLApprovalCard.tsx` | Write approval card (HITL) |
| `frontend/src/components/chat/renderers/ItemDetailCard.tsx` | Record detail card (**ORPHANED**) |
| `frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` | Building detail card (**ORPHANED**) |
| `frontend/src/components/chat/renderers/WriteDiffView.tsx` | Write diff view (**ORPHANED**) |
| `frontend/src/components/chat/renderers/RiskDistributionChart.tsx` | Risk distribution bar chart |
| `frontend/src/components/chat/renderers/ToolErrorCard.tsx` | Error display for failed tools |
| `frontend/src/lib/hooks/useUnifiedChat.ts` | Primary chat hook (useCoAgent) |
| `frontend/src/lib/stores/chatSessionStore.ts` | Zustand session store |
| `frontend/src/lib/types/unified-chat.ts` | TypeScript state types |
| `frontend/src/components/providers/CopilotProvider.tsx` | CopilotKit provider wrapper |

### Orphaned Files (candidates for cleanup or reactivation)

| File | Status |
|------|--------|
| `frontend/src/components/chat/ToolResultRenderers.tsx` | Orphaned — old tool name registrations, no importer |
| `frontend/src/components/chat/WriteConfirmationCard.tsx` | Orphaned — superseded by HITLApprovalCard |
| `frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` | Orphaned — superseded by HITLApprovalCard |
| `frontend/src/components/chat/renderers/DefaultToolFallback.tsx` | Orphaned — inline fallback in UnifiedToolRenderers |
| `frontend/src/components/chat/renderers/AgentActivityIndicator.tsx` | Legacy — only used by orphaned ToolResultRenderers |

---

## ENVIRONMENT & SERVICES

```bash
# Start all services before debugging:
# 1. Docker Desktop running
# 2. SurrealDB: docker compose up -d surrealdb (port 8000)
# 3. API: uv run run_api.py (port 5055)
# 4. Worker: uv run run_worker.py --import-modules commands
# 5. Frontend: cd frontend && npm run dev (port 8502)
# 6. (Optional) LangGraph dev: uv run langgraph dev --no-browser (port 2024)

# Key env vars (in .env):
SURREAL_URL=ws://localhost:8000/rpc
LANGSMITH_API_KEY=<required for trace inspection>
LANGCHAIN_TRACING_V2=true
```

---

## SYSTEMATIC DEBUGGING PROTOCOL

For EACH of the 5 issues, follow this exact sequence:

### Phase 1: Evidence Gathering (NO FIXES YET)
1. Read the error messages / reproduce the bug
2. Check recent git changes (`git log --oneline -20`)
3. Inspect LangSmith traces for the two provided trace IDs
4. Check browser console for JS errors
5. Check API logs for Python errors
6. Document findings in `findings.md`

### Phase 2: Root Cause Analysis
1. Trace data flow backward from symptom to source
2. Compare working vs broken behavior
3. Form a SINGLE hypothesis: "I think X is the root cause because Y"
4. Document hypothesis in `findings.md`

### Phase 3: Minimal Fix
1. Make the SMALLEST possible change to test the hypothesis
2. ONE variable at a time
3. Verify: does the fix resolve the issue?
4. If NOT → form NEW hypothesis, do NOT stack fixes

### Phase 4: Verification
1. Run build checks (`npm run build`, `pytest`, `ruff check`)
2. Browser-test the chat (agent-browser or manual)
3. Mark issue as resolved in `task_plan.md`
4. Update `progress.md`

---

## PRIORITY ORDER

Fix in this order (each unlocks the next):

1. **Issue #4 (surreal_query failing)** — Foundation: if queries don't work, nothing else will
2. **Issue #3 (only queries acm_record)** — Depends on #4: agent needs working query tools to use multiple tables
3. **Issue #2 (tools not rendering)** — Depends on #3: tools must return results before we can render them
4. **Issue #1 (thinking messages)** — UI-only: can fix independently but easier to verify once tools work
5. **Issue #5 (orphaned renderers)** — Wire up components once tool results are flowing correctly

---

## CONSTRAINTS

- **WSL path rule**: Always use `/mnt/d/ailocal/acm-ai` or `$CLAUDE_PROJECT_DIR`, NEVER `cd /d/...` or `D:\...`
- **Python**: Always `uv run ...` — never bare `python` or `pip`
- **Frontend**: npm is on Windows, not WSL — `cd frontend && npm run dev` via PowerShell
- **Commits**: Conventional commits (`fix:`, `feat:`, `refactor:`)
- **All LLM calls use OpenRouter** — not direct Anthropic/OpenAI keys
- **SurrealDB record IDs**: Use `type::thing('table:id')` for WHERE clause comparisons
