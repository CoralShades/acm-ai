# CopilotKit Chat — Usage & Testing Guide

## Overview

ACM-AI uses CopilotKit (`@copilotkit/react-core` and `@copilotkit/react-ui` v1.51.3) for a single unified AI chat interface — **ACM-AI Chat** (`UnifiedChatPanel`). It replaces the previous dual-panel architecture (separate Supervisor Chat + CRUD Chat). Both query and write operations are handled by the same panel and the same backend graph.

The chat connects to the backend via the AG-UI protocol at a single endpoint (`/api/agui/chat`). All LLM inference happens in the Python backend; the Next.js runtime routes only the event stream.

---

## Architecture

### Service Communication Flow

```
Browser (port 8503)
  └─ Next.js Frontend
       └─ /api/copilotkit  (CopilotRuntime lazy singleton)
             └─> FastAPI /api/agui/chat
                       └─> unified_agent graph  (SqliteSaver checkpointer)
```

The runtime route uses the **lazy singleton pattern** — the `CopilotRuntime` is created once on the first request and reused for all subsequent requests. `SqliteSaver` (instead of the previous `MemorySaver`) persists thread state across sessions and server restarts.

The `AgUiAdapter` subclass overrides `EmptyAdapter.name` to return `"AgUiAdapter"`, bypassing the CopilotKit name blocklist. All LLM calls happen in the Python backend.

### Unified Agent

The backend `unified_agent` graph (`open_notebook/graphs/unified_agent.py`) is a single 6-node LangGraph graph that handles both read queries and write operations:

- **Nodes**: `agent`, `tools`, `check_write_approval` (interrupt/HITL), `execute_write`, `legacy_execute`, `END`
- **Tools**: 15 LLM-facing tools covering ACM queries, document search, record writes, bulk writes, schema info, SurrealQL query, user choice prompts, and undo
- **Checkpointer**: `SqliteSaver` singleton (`open_notebook/graphs/checkpointer.py`) — sessions persist across restarts
- **Intent Router**: `open_notebook/graphs/llm_router.py` — rule-based fast-path + LLM fallback; extracts entity hints (buildings, rooms, risk_levels, materials, record_ids) injected into the system prompt each turn

### Session Management

Sessions are managed via `SessionDropdown` in the chat header and `chatSessionStore` (Zustand). REST endpoints for session CRUD are provided by `api/routers/unified_sessions.py`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/sessions` | List all chat sessions |
| `POST` | `/api/sessions` | Create a new session |
| `PATCH` | `/api/sessions/{id}` | Rename a session |
| `DELETE` | `/api/sessions/{id}` | Delete a session |

If a session 404s (e.g., deleted on another device), the store degrades gracefully and auto-creates a new session.

### AG-UI Protocol

The `ag-ui-langgraph` adapter translates LangGraph events into the AG-UI SSE event stream:

| Event | When it fires |
|-------|--------------|
| `TEXT_MESSAGE_START` | LLM begins a text turn |
| `TEXT_MESSAGE_CONTENT` | Streaming token (typewriter effect) |
| `TEXT_MESSAGE_END` | LLM text turn complete |
| `TOOL_CALL_START` | Agent calls a tool |
| `TOOL_CALL_ARGS` | Streaming tool arguments |
| `TOOL_CALL_END` | Tool call complete |
| `TOOL_CALL_RESULT` | Tool execution result |
| `STATE_SNAPSHOT` | Full agent state |
| `STATE_DELTA` | Partial agent state update |
| `INTERRUPT` | Graph paused for HITL write approval |
| `RUN_STARTED` | Graph run started |
| `RUN_FINISHED` | Graph run complete |
| `RUN_ERROR` | Graph run error |

---

## CopilotKit Hooks Reference

### useLangGraphInterrupt (HITL)

Triggered when the unified graph calls `interrupt()` after a `preview_write` or `preview_bulk_write` tool result. Gated on `eventValue?.type === 'write_approval'`.

```ts
useLangGraphInterrupt({
  enabled: ({ eventValue }) => eventValue?.type === 'write_approval',
  render: ({ event, resolve }) => {
    const preview = event.value?.preview
    return (
      <HITLApprovalDialog
        preview={preview}
        onApprove={(edits) => resolve(JSON.stringify({ approved: true, edits: edits || {} }))}
        onReject={() => resolve(JSON.stringify({ approved: false }))}
      />
    )
  },
})
```

### useRenderToolCall

Registers a React renderer for a named tool call. Receives `{ status, args, result }` and returns JSX. Lifecycle: `inProgress/executing → complete/error`.

**Unified tools with registered renderers (`UnifiedToolRenderers`):**

| Tool name | Renderer | Output |
|-----------|----------|--------|
| `search_acm_by_risk` | `ACMTableResult` | Tabular ACM records |
| `search_acm_by_building` | `ACMTableResult` | Tabular ACM records |
| `search_acm_by_room` | `ACMTableResult` | Tabular ACM records |
| `search_acm_by_product` | `ACMTableResult` | Tabular ACM records |
| `get_acm_stats` | `ACMStatsResult` | Stats cards |
| `get_acm_record_detail` | `ACMTableResult` | Single record detail |
| `list_acm_buildings` | `ACMStatsResult` | Building list |
| `search_documents_vector` | `SearchResult` | Document result cards |
| `search_documents_text` | `SearchResult` | Document result cards |
| `preview_write` | `ToolStepItem` | Step indicator (loading/complete) |
| `preview_bulk_write` | `ToolStepItem` | Step indicator (loading/complete) |
| `write_acm_record` | `ToolStepItem` | Green confirmation |
| `surreal_query` | `QueryResultCard` | SurrealQL query results |
| `get_schema_info` | `ToolStepItem` | Schema info indicator |
| `undo_last_write` | `ToolStepItem` | Undo confirmation |

### useDefaultTool

Catches any tool call without a specific renderer. Shows `AgentActivityIndicator` during execution, then a muted card with the tool name and raw JSON result on completion.

### ToolStepItem

ChatGPT-style step indicator component. Shows a spinner while a tool is executing and a checkmark on completion. Used for write operations where the result is conveyed by the agent's follow-up text rather than a structured card.

---

## UI Components

### Chat Components

| Component | File | Purpose |
|-----------|------|---------|
| `UnifiedChatPanel` | `components/chat/UnifiedChatPanel.tsx` | Main chat shell — session dropdown, model selector, tool renderers |
| `SessionDropdown` | `components/chat/SessionDropdown.tsx` | Create, switch, rename, delete sessions |
| `ToolStepItem` | `components/chat/ToolStepItem.tsx` | Animated step indicator for tool calls |
| `CopilotChat` | `@copilotkit/react-ui` | Core chat UI (messages, input) |

### Tool Result Renderers

| Component | File | What it renders |
|-----------|------|----------------|
| `ACMTableResult` | `renderers/ACMTableResult.tsx` | Compact table: building, room, product, risk badge. Rows are clickable (opens record modal). |
| `ACMStatsResult` | `renderers/ACMStatsResult.tsx` | Stats grid (total records, buildings, rooms) + risk breakdown badges. |
| `SearchResult` | `renderers/SearchResult.tsx` | Document result cards with title, snippet, relevance score badge. |
| `QueryResultCard` | `renderers/QueryResultCard.tsx` | SurrealQL query results table. |
| `AgentActivityIndicator` | `renderers/AgentActivityIndicator.tsx` | Spinner while tool executes; maps tool names to human-readable labels. |
| `ToolErrorCard` | `renderers/ToolErrorCard.tsx` | Red error badge when a tool returns `{ error: ... }`. |

### Generative UI Components

| Component | File | Purpose |
|-----------|------|---------|
| `HITLApprovalDialog` | `renderers/HITLApprovalDialog.tsx` | Write approval card with Approve / Reject / edit-before-approve |
| `WriteDiffView` | `renderers/WriteDiffView.tsx` | Before/after field diff display |
| `BuildingSummaryCard` | `renderers/BuildingSummaryCard.tsx` | Building name, ID, record count, high-risk count |
| `ItemDetailCard` | `renderers/ItemDetailCard.tsx` | Expandable ACM item card |
| `ExtractionProgress` | `renderers/ExtractionProgress.tsx` | Progress bar for extraction status |
| `DefaultToolFallback` | `renderers/DefaultToolFallback.tsx` | Generic fallback: spinner/check/error + JSON dump |

---

## HITL Write Approval Flow

### Step-by-Step

1. User types a write request (e.g. "Set risk to High for the ceiling tile record in Building B")
2. Unified agent calls the `preview_write` tool with operation details
3. `preview_write` stores the operation in `_pending_writes` (keyed by UUID), returns JSON
4. LangGraph `ToolNode` executes the tool, adds `ToolMessage` to state
5. Graph edges route to `check_write_approval` node
6. `check_write_approval` detects the `"type": "preview_write"` payload and calls `interrupt({ "type": "write_approval", "preview": data })`
7. The interrupt pauses the graph and sends an `INTERRUPT` event via AG-UI SSE
8. Frontend `useLangGraphInterrupt` fires (gated on `eventValue.type === 'write_approval'`)
9. `HITLApprovalDialog` renders inline with the operation details
10. User clicks Approve: `resolve(JSON.stringify({ approved: true, edits: {} }))` resumes the graph
11. `check_write_approval` receives `{ approved: true }`, calls `execute_pending_write(operation_id)`
12. `execute_pending_write` verifies `source_id` ownership, runs the SurrealQL UPDATE or DELETE, inserts into `crud_audit` with `confirmed_by: 'user_hitl'`
13. Node returns `AIMessage` with confirmation text
14. Graph routes back to `agent` node, which generates the final reply

### Security Model

- All writes are scoped to `source_id`. `execute_pending_write` verifies `pending["source_id"] == source_id`.
- The SurrealQL UPDATE and DELETE first check `SELECT id FROM acm_record WHERE id = $rid AND source_id = $sid`.
- `ALLOWED_ACM_FIELDS` allowlist prevents SQL injection via field name injection.

---

## Backend Graph Details

### Unified Agent (`open_notebook/graphs/unified_agent.py`)

- **State**: `UnifiedAgentState` (messages, source_id, session_id, pending_writes, model_id)
- **Nodes**: `agent`, `tools`, `check_write_approval`, `execute_write`, `legacy_execute`, `END`
- **Edges**: `START → agent → [tools | END]`, `tools → check_write_approval → [execute_write | agent]`
- **Checkpointer**: `SqliteSaver` singleton (persistent, survives restarts)
- **Tools exposed to LLM** (15): `search_acm_by_risk`, `search_acm_by_building`, `search_acm_by_room`, `search_acm_by_product`, `get_acm_stats`, `get_acm_record_detail`, `semantic_search_acm`, `search_documents`, `text_search_documents`, `surreal_query`, `preview_write`, `preview_bulk_write`, `get_schema_info`, `ask_user_choice`, `undo_last_write`

### LLM Intent Router (`open_notebook/graphs/llm_router.py`)

- Rule-based fast-path classifies common query patterns without an LLM call
- LLM fallback for ambiguous intent
- Entity extraction: buildings, rooms, risk_levels, materials, record_ids
- Extracted hints are injected into the unified_agent system prompt on each turn to improve tool selection accuracy
- 17 unit tests: `tests/test_llm_router.py`

---

## Streaming and Real-Time Features

### SSE Event Streaming

CopilotKit renders text progressively via `TEXT_MESSAGE_CONTENT` events. Tool call rendering follows a three-stage lifecycle: `TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_RESULT`. `ToolStepItem` transitions through `inProgress → executing → complete` as these events arrive.

---

## Testing Guide

### Prerequisites

```bash
# Start SurrealDB
docker compose up -d surrealdb

# Start API (port 5055)
uv run run_api.py

# Start frontend (port 8503)
cd frontend && npm run dev

# Upload a PDF and run extraction to populate ACM data before testing
```

### Manual Testing Scenarios

#### 1. Basic Stats Query

1. Navigate to a job detail page at `/jobs/{id}`
2. Open the ACM-AI Chat panel
3. Type: "How many records does this document have?"
4. Verify: `ACMStatsResult` card renders with total record count, building count, room count

#### 2. Tabular Record Search

1. Type: "Show all high risk records"
2. Verify: `ACMTableResult` renders with building, room, product, risk badge columns
3. Click a row — verify the record detail modal opens

#### 3. Session Management

1. Click the session dropdown in the chat header
2. Create a new session — verify an empty chat starts
3. Switch back to the previous session — verify message history is restored
4. Rename a session via the dropdown edit control
5. Delete a session — verify it is removed from the dropdown

#### 4. HITL Write Approval

1. Type: "Change the risk status of record [ID] to High"
2. Verify: `ToolStepItem` appears with "Preparing write preview..." briefly
3. Verify: `HITLApprovalDialog` appears — amber card with "UPDATE — Approval Required"
4. Verify dialog shows: field name, new value (green code badge), record ID, reason
5. Click "Approve"
6. Verify: Dialog disappears; agent sends confirmation message

#### 5. HITL Reject

1. Request an update
2. When `HITLApprovalDialog` appears, click "Reject"
3. Verify: Agent responds with "Write operation cancelled."

#### 6. Edit Before Approve

1. Request an update
2. When `HITLApprovalDialog` appears, click the pencil icon next to the new value
3. Change the value; click "Approve"
4. Verify: The edited value (not the original) was applied

#### 7. Error Handling

1. Stop the FastAPI backend
2. Send a message
3. Verify: `ToolErrorCard` renders for any failed tool call

### Build Verification

```bash
# Backend
uv run ruff check .
uv run pytest tests/ -x

# Frontend
cd frontend
npm run build
npm run lint
```

---

## Configuration

### Environment Variables

```env
INTERNAL_API_URL=http://localhost:5055
```

If `INTERNAL_API_URL` is not set, the runtime route defaults to `http://localhost:5055`.

### Frontend Runtime URLs

| Chat | Next.js route | Backend endpoint |
|------|--------------|-----------------|
| Unified | `/api/copilotkit` | `/api/agui/chat` |

### Package Versions

| Package | Version | Where |
|---------|---------|-------|
| `@copilotkit/react-core` | `^1.51.3` | `frontend/package.json` |
| `@copilotkit/react-ui` | `^1.51.3` | `frontend/package.json` |
| `@copilotkit/runtime` | `^1.51.3` | `frontend/package.json` |
| `@ag-ui/client` | `^0.0.43` | `frontend/package.json` |
| `ag-ui-langgraph` | `>=0.0.25` | `pyproject.toml` |
| `copilotkit` | `>=0.1.78` | `pyproject.toml` |

---

## File Map

| File | Purpose |
|------|---------|
| `frontend/src/components/providers/CopilotProvider.tsx` | App-level CopilotKit provider; points at `/api/copilotkit` |
| `frontend/src/app/api/copilotkit/route.ts` | Unified CopilotRuntime — lazy singleton, registers `unified` and `default` HttpAgent |
| `frontend/src/components/chat/UnifiedChatPanel.tsx` | Unified chat UI — session dropdown, tool renderers, model selector, `CopilotChat` |
| `frontend/src/components/chat/SessionDropdown.tsx` | Session picker — create, switch, rename, delete |
| `frontend/src/components/chat/ToolStepItem.tsx` | ChatGPT-style animated step indicator for tool calls |
| `frontend/src/lib/stores/chatSessionStore.ts` | Zustand store for session list and active session |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | All 16+ tool renderers + `useLangGraphInterrupt` HITL |
| `frontend/src/components/chat/renderers/ACMTableResult.tsx` | Tabular ACM record display with risk badges |
| `frontend/src/components/chat/renderers/ACMStatsResult.tsx` | Stats grid and building list card |
| `frontend/src/components/chat/renderers/SearchResult.tsx` | Document search result cards |
| `frontend/src/components/chat/renderers/QueryResultCard.tsx` | SurrealQL query results table |
| `frontend/src/components/chat/renderers/AgentActivityIndicator.tsx` | Loading/complete indicator per tool |
| `frontend/src/components/chat/renderers/ToolErrorCard.tsx` | Error state for failed tools |
| `frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` | HITL write approval card (approve / reject / edit) |
| `frontend/src/components/chat/renderers/WriteDiffView.tsx` | Before/after field diff display |
| `frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` | Building summary with record and risk counts |
| `frontend/src/components/chat/renderers/ItemDetailCard.tsx` | Expandable ACM item card |
| `frontend/src/components/chat/renderers/ExtractionProgress.tsx` | Progress bar for extraction status |
| `frontend/src/components/chat/renderers/DefaultToolFallback.tsx` | Fallback renderer for unregistered tools |
| `open_notebook/graphs/unified_agent.py` | Unified LangGraph — 6 nodes, 15 tools, interrupt-based HITL, SqliteSaver |
| `open_notebook/graphs/llm_router.py` | LLM intent router with rule-based fast-path + entity extraction |
| `open_notebook/graphs/tool_context.py` | Thread-safe `contextvars` tool context |
| `open_notebook/graphs/checkpointer.py` | SqliteSaver singleton for persistent sessions |
| `open_notebook/graphs/chat_tools/acm_tools.py` | ACM query tools (search by risk, building, room, material; stats; detail; semantic search) |
| `open_notebook/graphs/chat_tools/search_tools.py` | Document search tools (vector + text) |
| `open_notebook/graphs/crud_tools.py` | Write tools: `preview_write`, `preview_bulk_write`, `execute_pending_write`, `undo_last_write`, `surreal_query`, `get_schema_info`, `ask_user_choice` |
| `api/routers/agui_chat.py` | Single unified AG-UI endpoint at `/api/agui/chat` |
| `api/routers/unified_sessions.py` | Session CRUD REST endpoints |
| `prompts/unified_agent.jinja` | Unified system prompt (all 7 DB tables, 15 tools) |
