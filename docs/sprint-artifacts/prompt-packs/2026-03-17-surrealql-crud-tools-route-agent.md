# Session: Add SurrealQL CRUD tools and route agent for CopilotKit chat with guardrails and streaming

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/langgraph-fundamentals — LangGraph graph/node/state patterns (tool nodes, conditional edges)
/langgraph-human-in-the-loop — HITL patterns for write operations (preview → approve → execute)
/copilotkit — CopilotKit integration patterns (useCoAgent, tool renderers, AG-UI streaming)
/pydantic-models-py — Pydantic models for tool input/output schemas and guardrails
/verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Frontend running: `curl http://localhost:8503`
- Branch: `git checkout ACMV3` (or create feature branch `feat/surrealql-crud-tools`)
- File exists: `D:/ailocal/acm-ai/open_notebook/graphs/crud_agent.py`
- File exists: `D:/ailocal/acm-ai/open_notebook/graphs/crud_tools.py`
- File exists: `D:/ailocal/acm-ai/open_notebook/database/repository.py`
- File exists: `D:/ailocal/acm-ai/api/routers/agui_chat.py`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| SurrealQL | SurrealDB's query language. Supports `SELECT`, `CREATE`, `UPDATE`, `DELETE`, `RELATE`, with `$var` parameterized bindings. Always use `repo_query(query, vars)` — never string interpolation. |
| crud_agent.py | The existing LangGraph CRUD graph at `open_notebook/graphs/crud_agent.py`. Has `route_entry → agent → tools` loop + structural HITL via `execute_write_node`. |
| crud_tools.py | Existing CRUD tools at `open_notebook/graphs/crud_tools.py`. Currently has `query_job_records` (hardcoded branches), `preview_write`, `execute_pending_write`. |
| HITL (Human-in-the-Loop) | The preview → approve → execute pattern. `preview_write` returns JSON for frontend rendering. User clicks Approve → message "Approved. Execute operation #xxx" → `route_entry` intercepts → `execute_write_node` runs. |
| repo_query | Core DB primitive at `open_notebook/database/repository.py`. Executes raw SurrealQL with `$vars` parameterization. All new tools MUST use this — never raw string formatting. |
| _tool_context | Module-level dict in chat_tools that holds `{source_id, notebook_id}`. Set by `set_tool_context()` before each agent invocation. Use `_build_source_filter()` for WHERE clauses. |
| Route agent | A LangGraph node that classifies user intent (read/write/analytics/off-topic) and conditionally routes to different tool subsets. Replaces flat tool binding with intent-aware dispatch. |
| AG-UI Protocol | CopilotKit's event streaming protocol. Tool calls emit `ToolCallStart`, `ToolCallArgs`, `ToolCallEnd` events automatically via `ag-ui-langgraph`. |
| CrudToolRenderers | Frontend component at `frontend/src/components/jobs/CrudToolRenderers.tsx` that renders CRUD tool results. Uses `useRenderToolCall` for each tool name. |
| ExtractionState | LangGraph TypedDict carrying pipeline state. CRUD agent has its own state — do NOT mix with extraction state. |
| Guardrails | Input validation (table/field allowlisting, operation type restrictions) and output validation (result size limits, error wrapping) applied to SurrealQL tools. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Model: `sonnet` for complex, `haiku` for simple. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |
| _pending_writes | Dict in crud_tools.py keyed by operation ID. `preview_write` stores operations here; `execute_pending_write` consumes them after HITL approval. |

---

## Current State

- Branch: ACMV3 (last commit: `docs: Update BMAD artifacts for dogfood session`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Existing CRUD chat: `/jobs/[id]/chat` page with `JobCrudChatPanel` → `/copilot-crud` → `/api/agui/crud-chat` → `crud_graph`
- Current `query_job_records` tool: hardcoded SurrealQL branches (count, buildings, no_access, friable, high_risk, fallback) — limited and brittle
- Current HITL flow: `preview_write` → `CrudToolRenderers` → `HITLApprovalDialog` → `execute_pending_write` — working and must be preserved
- Supervisor graph: flat ReAct loop with 9 tools (7 ACM read + 2 search), no routing
- SurrealDB tables available: `acm_record`, `building_record`, `source`, `notebook`, `note`, `raw_extraction_table`, `acm_table_section`, `source_intelligence`, `crud_audit`
- Frontend port: 8503

---

## Key Files

Files this session will read or modify. Verify all paths exist before starting.

**Read (reference):**
- `D:/ailocal/acm-ai/open_notebook/database/repository.py` — DB primitives (repo_query, repo_create, repo_update, repo_delete)
- `D:/ailocal/acm-ai/open_notebook/graphs/supervisor_agent.py` — existing supervisor graph pattern
- `D:/ailocal/acm-ai/open_notebook/graphs/chat_tools/acm_tools.py` — existing ACM read tools (7 tools, _tool_context pattern)
- `D:/ailocal/acm-ai/open_notebook/graphs/chat_tools/search_tools.py` — existing search tools
- `D:/ailocal/acm-ai/open_notebook/domain/acm.py` — ACMRecord, BuildingRecord domain models
- `D:/ailocal/acm-ai/api/routers/agui_chat.py` — AG-UI endpoint registration (register_crud_agui_endpoint)
- `D:/ailocal/acm-ai/frontend/src/components/jobs/JobCrudChatPanel.tsx` — CRUD chat panel with inline CopilotKit provider
- `D:/ailocal/acm-ai/frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` — existing HITL approval dialog
- `D:/ailocal/acm-ai/frontend/src/app/copilot-crud/route.ts` — Next.js CRUD bridge route
- `D:/ailocal/acm-ai/prompts/supervisor.jinja` — supervisor system prompt template
- `D:/ailocal/acm-ai/migrations/` — SurrealDB schema (table definitions, indexes)

**Modify:**
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_tools.py` — replace `query_job_records` with dynamic SurrealQL tool, add guardrails
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_agent.py` — add route_intent node, rewire graph with conditional edges
- `D:/ailocal/acm-ai/frontend/src/components/jobs/CrudToolRenderers.tsx` — add renderers for new tool result types
- `D:/ailocal/acm-ai/prompts/` — add/modify prompt templates for route agent and SurrealQL generation

**Create:**
- `D:/ailocal/acm-ai/open_notebook/graphs/crud_tools_v2.py` — new SurrealQL CRUD tools with guardrails (or extend crud_tools.py)
- `D:/ailocal/acm-ai/open_notebook/graphs/guardrails.py` — input/output guardrails (table allowlist, field validation, result limits)
- `D:/ailocal/acm-ai/prompts/crud/route_intent.jinja` — route agent system prompt
- `D:/ailocal/acm-ai/prompts/crud/surrealql_generator.jinja` — SurrealQL generation prompt with schema context
- `D:/ailocal/acm-ai/tests/test_crud_tools_v2.py` — unit tests for new tools
- `D:/ailocal/acm-ai/tests/test_route_agent.py` — route agent classification tests

---

## Plan

Read `docs/sprint-artifacts/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: D:/ailocal/acm-ai/docs/sprint-artifacts/task_plan.md
- findings.md: D:/ailocal/acm-ai/docs/sprint-artifacts/findings.md
- progress.md: D:/ailocal/acm-ai/docs/sprint-artifacts/progress.md

### Implementation Architecture

#### 1. SurrealQL Query Tool (read path)
```
User message → route_intent_node → "read" → surreal_query tool
  → LLM generates SurrealQL SELECT from schema context + user intent
  → Guardrails validate: only SELECT allowed, tables in allowlist, $vars parameterized
  → repo_query(generated_sql, vars) executes
  → Output guardrails: cap result rows, format as structured JSON
  → Return to chat as tool result → CrudToolRenderers renders table
```

#### 2. SurrealQL Mutation Tools (write path — preserves existing HITL)
```
User message → route_intent_node → "write" → preview_surreal_write tool
  → LLM generates SurrealQL UPDATE/CREATE/DELETE with preview
  → Guardrails validate: table in allowlist, operation type allowed, fields valid
  → Stores in _pending_writes (same pattern as existing preview_write)
  → Frontend renders HITLApprovalDialog
  → User approves → execute_pending_surreal_write → repo_query + audit log
```

#### 3. Route Agent Node
```python
# In crud_agent.py — new conditional routing
def route_intent(state: CrudState) -> str:
    """Classify user intent from last message."""
    # Uses small/fast LLM call or rule-based classifier
    # Returns: "read" | "write" | "analytics" | "general"

# Graph wiring:
START → route_entry → (HITL approval?) → execute_write → END
                   → (normal?) → route_intent → read_agent / write_agent / general_agent
```

#### 4. Guardrails Module
```python
# open_notebook/graphs/guardrails.py
ALLOWED_TABLES = {"acm_record", "building_record", "source", "acm_table_section", ...}
ALLOWED_WRITE_TABLES = {"acm_record", "building_record"}  # subset
BLOCKED_OPERATIONS = {"DROP", "REMOVE", "DEFINE", "INFO"}

def validate_surreal_query(query: str, operation: str) -> GuardrailResult:
    """Validate generated SurrealQL before execution."""

def cap_results(results: list, max_rows: int = 100) -> list:
    """Limit result set size."""
```

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items in parallel.

Subagents:
- **backend-tools**: Implement SurrealQL tools + guardrails in `open_notebook/graphs/` (Steps 2-6)
- **backend-graph**: Create route agent node and rewire crud_agent.py graph (Steps 7-8)
- **frontend-renderers**: Update CrudToolRenderers for new tool result types (Step 9)
- **verifier**: Run verification checklist after all complete (Steps 11-12)

Spawn backend-tools and frontend-renderers in parallel. Then backend-graph (depends on tools). Then verifier last.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "copilotkit" → query-docs for "useCoAgent useRenderToolCall tool renderers streaming"
2. resolve-library-id for "langgraph" → query-docs for "tool node conditional edges routing StateGraph add_conditional_edges"
3. resolve-library-id for "surrealdb python" → query-docs for "parameterized queries SELECT UPDATE CREATE DELETE"
4. resolve-library-id for "langchain" → query-docs for "@tool decorator StructuredTool async tool definition"

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run ruff format --check .` — Python formatting (0 changes needed)
- [ ] `uv run pytest tests/test_crud_tools_v2.py -v` — New CRUD tool tests pass
- [ ] `uv run pytest tests/test_route_agent.py -v` — Route agent tests pass
- [ ] `uv run pytest tests/ -x` — Full backend test suite passes
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `cd frontend && npm run lint` — Frontend lint (no new errors)
- [ ] Manual: open `/jobs/{id}/chat`, send "how many buildings are there?" → get structured result
- [ ] Manual: open `/jobs/{id}/chat`, send "update building BLD#001 address to 123 Main St" → get HITL preview
- [ ] Manual: approve the preview → verify DB write + audit log entry
- [ ] Manual: send "drop table acm_record" → verify guardrail blocks the request
- [ ] Screenshot: save evidence to `docs/sprint-artifacts/crud-tools/`

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| NEW | 6 | crud_tools_v2.py (or extend crud_tools.py), guardrails.py, route_intent.jinja, surrealql_generator.jinja, test_crud_tools_v2.py, test_route_agent.py |
| MODIFY | 4 | crud_tools.py, crud_agent.py, CrudToolRenderers.tsx, prompts/ |
| READ | 11 | repository.py, supervisor_agent.py, acm_tools.py, search_tools.py, acm.py, agui_chat.py, JobCrudChatPanel.tsx, HITLApprovalDialog.tsx, route.ts, supervisor.jinja, migrations/ |
| DELETE | 0 | — |

---

## Commit Template

When work is complete, use this commit message structure:

```
feat(crud-chat): add SurrealQL CRUD tools with route agent and guardrails

- Replace hardcoded query_job_records with dynamic SurrealQL generation tool
- Add input guardrails (table allowlist, operation validation, parameterized queries)
- Add output guardrails (result size caps, error wrapping)
- Create route_intent node for intent classification (read/write/analytics)
- Rewire crud_agent.py graph with conditional routing
- Update CrudToolRenderers for new tool result types
- Add prompt templates for SurrealQL generation and intent routing
- Preserve existing HITL preview→approve→execute pattern for writes

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Critical Patterns to Follow

### 1. NEVER use string interpolation for SurrealQL
```python
# WRONG — SQL injection risk
query = f"SELECT * FROM {table} WHERE name = '{user_input}'"

# CORRECT — always use $vars
query = "SELECT * FROM acm_record WHERE name = $name"
result = await repo_query(query, {"name": user_input})
```

### 2. Preserve the _tool_context pattern
```python
# crud_tools.py already uses set_tool_context() — new tools must respect it
from open_notebook.graphs.chat_tools.acm_tools import _tool_context, _build_source_filter
```

### 3. Preserve the HITL approval flow
```python
# preview_write stores in _pending_writes
# execute_pending_write consumes after user approval
# route_entry in crud_agent.py intercepts "Approved. Execute operation #xxx"
# DO NOT allow LLM to call execute_pending_write directly
```

### 4. Use existing repo primitives
```python
from open_notebook.database.repository import repo_query, repo_create, repo_update, repo_delete
# All return parsed results with RecordID→string conversion via parse_record_ids()
```

### 5. SurrealDB record ID quirk
```python
# WHERE id = $mid with string "model:xxx" does NOT auto-cast to record ID
# Must use direct reference: SELECT ... FROM acm_record:xxx;
# Or use ensure_record_id() to get a RecordID object
```
