# CopilotKit Chat — Usage & Testing Guide

## Overview

ACM-AI uses CopilotKit (`@copilotkit/react-core` and `@copilotkit/react-ui` v1.51.3) for two distinct AI chat interfaces:

- **Supervisor Chat** — Read-only queries against ACM records and documents. Available on source detail pages.
- **CRUD Chat** — Write operations on ACM records with human-in-the-loop (HITL) approval before any change is applied. Available on job detail pages.

Both chat surfaces connect to separate backend LangGraph graphs via the AG-UI protocol. All LLM inference happens in the Python backend; the Next.js runtime routes only the event stream.

---

## Architecture

### Service Communication Flow

```
Browser (port 8503)
  └─ Next.js Frontend
       ├─ /api/copilotkit  (CopilotRuntime lazy singleton)
       │     └─> FastAPI /api/agui/chat
       │               └─> supervisor_graph  (MemorySaver checkpointer)
       │
       └─ /copilot-crud  (CopilotRuntime lazy singleton)
             └─> FastAPI /api/agui/crud-chat
                       └─> crud_graph  (MemorySaver + interrupt())
```

Both runtime routes use the **lazy singleton pattern** — the `CopilotRuntime` is created once on the first request and reused for all subsequent requests in the same process. This prevents memory pressure and allows LangGraph's `MemorySaver` to persist thread state across turns.

The `AgUiAdapter` subclass (in each route file) overrides `EmptyAdapter.name` to return `"AgUiAdapter"` instead of `"EmptyAdapter"`, which bypasses the CopilotKit name blocklist. This is required because all LLM calls happen in the Python backend, not in the JS runtime.

### Two Chat Contexts

**Supervisor Chat** is mounted in `SmartChatPanel`. It wraps a `CopilotKit` provider at the application layout level (see `CopilotProvider`), pointing at `/api/copilotkit`. It is read-only: it can search ACM records, retrieve stats, and search document content. It cannot write data.

**CRUD Chat** is mounted in `JobCrudChatPanel`. It creates its own scoped `CopilotKit` provider pointing at `/copilot-crud`. This isolation means write-capable tools are never available from the Supervisor Chat runtime. The CRUD chat is scoped to a single `source_id` passed from the job detail page.

### AG-UI Protocol

The `ag-ui-langgraph` adapter (`add_langgraph_fastapi_endpoint`) translates LangGraph events into the AG-UI SSE event stream. Key event types flowing to the frontend include:

| Event | When it fires |
|-------|--------------|
| `TEXT_MESSAGE_START` | LLM begins a text turn |
| `TEXT_MESSAGE_CONTENT` | Streaming token (typewriter effect) |
| `TEXT_MESSAGE_END` | LLM text turn complete |
| `TOOL_CALL_START` | Agent calls a tool |
| `TOOL_CALL_ARGS` | Streaming tool arguments |
| `TOOL_CALL_END` | Tool call complete |
| `TOOL_CALL_RESULT` | Tool execution result |
| `STATE_SNAPSHOT` | Full agent state (triggers `useCoAgent`) |
| `STATE_DELTA` | Partial agent state update |
| `INTERRUPT` | Graph paused for HITL (triggers `useLangGraphInterrupt`) |
| `RUN_STARTED` | Graph run started |
| `RUN_FINISHED` | Graph run complete |
| `RUN_ERROR` | Graph run error |

---

## CopilotKit Hooks Reference

### useCopilotReadable

**File:** `frontend/src/components/chat/SmartChatPanel.tsx`

Exposes structured page context to the LLM on every turn. The supervisor agent can reference these values in its reasoning without the user having to repeat them.

```ts
useCopilotReadable({
  description: 'Current page context: source ID, notebook ID, and ACM data availability',
  value: {
    sourceId: sourceId || null,
    notebookId: notebookId || null,
    hasAcmData,
    acmContextEnabled: includeAcmContext,
  },
})
```

### useCopilotChatSuggestions

**File:** `frontend/src/components/chat/SmartChatPanel.tsx`

Generates dynamic chat starter suggestions based on page context. Suggestions change when the ACM toggle is flipped.

- ACM context ON: LLM generates compliance-focused suggestions (risk summaries, building searches, material lookups)
- ACM context OFF: LLM generates document content suggestions (summarize, find sections, explain terminology)

Maximum 3 suggestions shown. Dependencies are `[hasAcmData, includeAcmContext]`, so suggestions regenerate when either changes.

### useRenderToolCall

**File:** `frontend/src/components/chat/ToolResultRenderers.tsx` (9 renderers)
**File:** `frontend/src/components/jobs/CrudToolRenderers.tsx` (2 renderers)

Registers a React renderer for a named tool call. The renderer receives `{ status, args, result }` and returns JSX. The lifecycle maps to three states:

- `status === 'inProgress'` or `'executing'`: render a loading indicator
- `isErrorResult(result)`: render a `ToolErrorCard`
- Otherwise: render the result card

**Supervisor tools with registered renderers:**

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

**CRUD tools with registered renderers:**

| Tool name | Renderer | Output |
|-----------|----------|--------|
| `preview_acm_write` | Inline loading text | "Preparing write preview..." |
| `write_acm_record` | Inline success text | Green confirmation |

Note: The `preview_acm_write` renderer covers the loading state only. The actual approval UI is handled by `useLangGraphInterrupt`, not by this renderer.

### useDefaultTool

**File:** `frontend/src/components/chat/ToolResultRenderers.tsx`

Catches any tool call that does not have a specific `useRenderToolCall` registration. During execution it shows `AgentActivityIndicator`. On completion it shows the tool name and a raw JSON dump of the result in a muted card. This is the inline fallback; the separate `DefaultToolFallback` component in the renderers directory provides a richer version of the same pattern.

### useLangGraphInterrupt (HITL)

**File:** `frontend/src/components/jobs/CrudToolRenderers.tsx`

Triggered when the CRUD graph calls `interrupt()` after a `preview_write` tool result. The hook is gated on `eventValue?.type === 'write_approval'` so it only fires for write approval events.

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

When the user approves, `resolve` is called with `{ approved: true, edits }`. When rejected, it is called with `{ approved: false }`. The CRUD graph's `check_write_approval` node receives this value via `interrupt()` return and either executes or cancels the write.

### useCoAgentStateRender

**File:** `frontend/src/components/chat/SmartChatPanel.tsx`

Subscribes to intermediate state emitted by the supervisor graph via `copilotkit_emit_state`. While the graph is running, renders a small animated indicator inline with the chat messages.

- `nodeName === 'tools'` → shows "Searching..."
- Any other node → shows "Thinking..."
- `status !== 'inProgress'` → renders nothing

The supervisor graph emits state via `copilotkit_emit_state(config, {...})` in the `call_supervisor` node. This is non-fatal: if the `copilotkit` Python package is not installed, the `try/except` block around `from copilotkit.langgraph import copilotkit_emit_state` causes `_HAS_COPILOTKIT = False` and the emit is skipped.

### useCoAgent

**File:** `frontend/src/lib/hooks/useSmartChat.ts`

Manages the supervisor agent's shared state (`SupervisorAgentState`) with two-way sync to the LangGraph graph. The `setIncludeAcmContext` handler both updates local React state and calls `setState` to push the new value into the next graph invocation.

State shape (`SupervisorAgentState`):

```ts
{
  source_id: string | null
  notebook_id: string | null
  include_acm_context: boolean
  active_agents: string[]
  acm_results: Record<string, unknown> | null
  search_results: Record<string, unknown> | null
}
```

---

## UI Components

### Chat Components

| Component | File | Purpose |
|-----------|------|---------|
| `CopilotChat` | `@copilotkit/react-ui` | Core chat UI shell (messages, input, title) |
| `SmartChatInput` | `SmartChatInput.tsx` | Custom input with ACM toggle badge |
| `ACMAssistantMessage` | `ACMAssistantMessage.tsx` | Custom assistant message renderer |

`SmartChatPanel` passes `AssistantMessage` and `Input` render props to `CopilotChat` to substitute the default components with ACM-specific ones.

### Tool Result Renderers

| Component | File | What it renders |
|-----------|------|----------------|
| `ACMTableResult` | `renderers/ACMTableResult.tsx` | Compact table: building, room, product, risk badge, result. Rows are clickable (opens record modal). |
| `ACMStatsResult` | `renderers/ACMStatsResult.tsx` | Stats grid (total records, buildings, rooms) + risk breakdown badges. Also handles building list mode when `data.buildings` array is present. |
| `SearchResult` | `renderers/SearchResult.tsx` | Document result cards with title, snippet, relevance score badge. Cards are clickable (opens source modal). |
| `AgentActivityIndicator` | `renderers/AgentActivityIndicator.tsx` | Spinning loader while tool executes; maps tool names to human-readable labels. |
| `ToolErrorCard` | `renderers/ToolErrorCard.tsx` | Red error badge when a tool returns `{ error: ... }`. Shows friendly label, not raw tool name. |

### Generative UI Components

These components are registered renderers or used by the HITL flow:

| Component | File | Purpose |
|-----------|------|---------|
| `HITLApprovalDialog` | `renderers/HITLApprovalDialog.tsx` | Amber approval card with Approve / Reject buttons and optional value edit |
| `WriteDiffView` | `renderers/WriteDiffView.tsx` | Before/after field diff display (strikethrough old, green new) |
| `BuildingSummaryCard` | `renderers/BuildingSummaryCard.tsx` | Building name, ID, record count, high-risk count card |
| `ItemDetailCard` | `renderers/ItemDetailCard.tsx` | Expandable ACM item card with primary fields + "N more fields" toggle |
| `ExtractionProgress` | `renderers/ExtractionProgress.tsx` | Progress bar with stage name and percentage for extraction jobs |
| `DefaultToolFallback` | `renderers/DefaultToolFallback.tsx` | Generic fallback: spinner/check/error icon + JSON result dump |

---

## HITL Write Approval Flow

### Step-by-Step

1. User types a write request in the CRUD Chat (e.g. "Set risk to High for the ceiling tile record in Building B")
2. CRUD agent calls the `preview_write` tool with operation details
3. `preview_write` stores the operation in `_pending_writes` (keyed by an 8-character UUID), returns JSON
4. LangGraph `ToolNode` executes the tool and adds the result as a `ToolMessage`
5. Graph edges route to `check_write_approval` node
6. `check_write_approval` detects the `"type": "preview_write"` payload and calls `interrupt({ "type": "write_approval", "preview": data })`
7. The interrupt pauses the graph and sends an `INTERRUPT` event via AG-UI SSE
8. Frontend `useLangGraphInterrupt` fires (gated on `eventValue.type === 'write_approval'`)
9. `HITLApprovalDialog` renders inline with the operation details (operation type, field name, new value, reason, record ID)
10. User clicks Approve: `resolve(JSON.stringify({ approved: true, edits: {} }))` resumes the graph
11. `check_write_approval` receives `{ approved: true }`, calls `execute_pending_write(operation_id)`
12. `execute_pending_write` verifies `source_id` ownership, runs the SurrealQL UPDATE or DELETE, and inserts a row into `crud_audit` with `confirmed_by: 'user_hitl'`
13. Node returns `AIMessage` with confirmation text
14. Graph routes back to `agent` node, which generates the final reply

### Edit Before Approving

`HITLApprovalDialog` includes a pencil icon button next to the new value. Clicking it replaces the value display with a text input pre-filled with the current `new_value`. When the user approves after editing, `resolve` is called with `{ approved: true, edits: { new_value: "<edited>" } }`. The `execute_pending_write` function applies the edit by overwriting `pending["new_value"]` before running the query.

### Reject Flow

Clicking Reject calls `resolve(JSON.stringify({ approved: false }))`. The `check_write_approval` node returns `AIMessage(content="Write operation #{id} was cancelled.")`. The pending operation remains in `_pending_writes` with `status: "pending"` but will never be executed since execution only happens in `check_write_approval`.

### Security Model

- All writes are scoped to `source_id`. `execute_pending_write` verifies `pending["source_id"] == source_id` before executing.
- The SurrealQL UPDATE and DELETE first run a `SELECT id FROM acm_record WHERE id = $rid AND source_id = $sid` check. If the record is not in the job, the write is rejected.
- The `_pending_writes` dict is in-memory per process. Operations do not survive API restarts.

---

## Backend Graph Details

### Supervisor Graph (`open_notebook/graphs/supervisor_agent.py`)

- State: `SupervisorState` (messages, source_id, notebook_id, include_acm_context, active_agents, acm_results, search_results)
- Nodes: `supervisor` (calls LLM with tools), `tools` (ToolNode)
- Edges: `START → supervisor → [tools | END]`, `tools → supervisor` (loop)
- Checkpointer: `MemorySaver` (in-memory, per thread)
- Tools available (when ACM context ON): `search_acm_by_risk`, `search_acm_by_building`, `search_acm_by_room`, `search_acm_by_material`, `get_acm_stats`, `get_acm_record_detail`, `semantic_search_acm`, `search_documents`, `text_search_documents`
- Tools available (when ACM context OFF): `search_documents`, `text_search_documents` only

### CRUD Graph (`open_notebook/graphs/crud_agent.py`)

- State: `CRUDAgentState` (messages, source_id)
- Nodes: `agent` (calls LLM with CRUD tools), `tools` (ToolNode), `check_approval` (interrupt logic)
- Edges: `START → agent → [tools | END]`, `tools → check_approval → agent`
- Checkpointer: `MemorySaver`
- Tools exposed to LLM: `query_job_records`, `preview_write` (the LLM never calls `execute_pending_write` directly)

---

## Streaming and Real-Time Features

### SSE Event Streaming

CopilotKit renders text progressively via `TEXT_MESSAGE_CONTENT` events (typewriter effect). Tool call rendering follows a three-stage lifecycle driven by `TOOL_CALL_START`, `TOOL_CALL_ARGS`, and `TOOL_CALL_RESULT` events. The `useRenderToolCall` hook transitions the rendered JSX through `inProgress → executing → complete` as these events arrive.

### copilotkit_emit_state

The supervisor graph calls `copilotkit_emit_state(config, state_dict)` from within the `call_supervisor` node to push intermediate state updates to the frontend. `useCoAgentStateRender` subscribes to these updates and renders the "Thinking..." / "Searching..." indicator.

The Python-side import is guarded:

```python
try:
    from copilotkit.langgraph import copilotkit_emit_state
    _HAS_COPILOTKIT = True
except ImportError:
    _HAS_COPILOTKIT = False
```

The emit call is wrapped in a `try/except` so the graph works correctly even if `copilotkit` is not installed or the emit fails.

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

#### 1. Supervisor Chat — Basic Stats Query

1. Navigate to a source with extracted ACM data at `/source/{id}`
2. Open the Smart Chat panel
3. Verify the "ACM Register data included in context" banner is visible (teal strip at top of chat)
4. Verify 2-3 domain-aware chat suggestions appear below the input
5. Type: "How many records does this document have?"
6. Verify: `AgentActivityIndicator` with "Getting ACM statistics..." appears during execution
7. Verify: `ACMStatsResult` card renders with total record count, building count, room count
8. Verify: Risk breakdown badges (High / Medium / Low) appear if data is present

#### 2. Supervisor Chat — Tabular Record Search

1. Type: "Show all high risk records"
2. Verify: `AgentActivityIndicator` shows "Searching ACM by risk status..." during execution
3. Verify: `ACMTableResult` renders with building, room, product, risk badge columns
4. Type: "Find records in Building A" (use an actual building name from the data)
5. Verify: `ACMTableResult` renders building-scoped results
6. Click a row in the table — verify the record detail modal opens

#### 3. Supervisor Chat — ACM Context Toggle

1. Locate the "ACM Data ON" badge at the bottom of the chat panel (below the input)
2. Click the badge to toggle it OFF
3. Verify: "ACM Register data included in context" banner disappears
4. Verify: Chat suggestions regenerate to document-focused prompts
5. Type: "Summarize this document"
6. Verify: Agent uses `search_documents` (vector search) rather than ACM tools
7. Toggle ACM back ON and verify the banner returns

#### 4. Supervisor Chat — useCoAgentStateRender Indicator

1. Ask a query that triggers tool execution (any ACM search)
2. While the agent is running, verify the animated blue pulse dot appears with "Thinking..." or "Searching..." text
3. The indicator disappears automatically when the response completes

#### 5. CRUD Chat — HITL Write Approval

1. Navigate to a job detail page
2. Locate and open the CRUD Chat panel (title: "ACM CRUD Assistant")
3. Type: "Change the risk status of record [ID] to High" (use a real record ID from the job)
4. Verify: Loading text "Preparing write preview..." appears briefly
5. **Verify: `HITLApprovalDialog` appears** — amber card with amber "UPDATE — Approval Required" header, `#<operation_id>` in monospace
6. Verify dialog shows: field name, new value in green code badge, record ID, and reason text
7. Click "Approve"
8. Verify: Dialog disappears; green confirmation row appears ("Updated risk_status on record ... to 'High'.")
9. Verify: Agent sends a confirmation message in the chat

#### 6. CRUD Chat — HITL Reject

1. Request another update
2. When `HITLApprovalDialog` appears, click "Reject"
3. Verify: Agent responds with "Write operation #\<id> was cancelled."

#### 7. CRUD Chat — Edit Before Approve

1. Request an update
2. When `HITLApprovalDialog` appears, verify the pencil icon appears next to the new value
3. Click the pencil icon — verify the value text changes to an editable text input
4. Change the value to something different
5. Click "Approve"
6. Verify: The edited value (not the original) was applied to the record

#### 8. CRUD Chat — Read Query

1. Type: "How many records does this job have?"
2. Verify: Agent calls `query_job_records` and responds with a text count
3. Note: `query_job_records` returns plain text, not JSON, so no structured card renders — the count appears in the agent's text response

#### 9. Default Tool Fallback

1. If any unexpected tool call occurs (one not registered in `ToolResultRenderers`), verify `useDefaultTool` catches it
2. Should show tool name in a muted border card with JSON result dump (max height 10rem)
3. `DefaultToolFallback.tsx` provides the standalone component variant (spinner / checkmark / alert icon based on status)

#### 10. Error Handling

1. Stop the FastAPI backend process
2. Send a message in either chat
3. Verify: `ToolErrorCard` renders for any tool that fails (destructive-colored, "Failed to execute \<label>. Try rephrasing your request.")
4. Verify: `CopilotProvider` logs `[CopilotKit] Runtime error:` to the browser console
5. In development mode, verify `showDevConsole` prop causes the CopilotKit dev console to appear
6. Restart the backend — verify subsequent messages succeed without a page reload

### Build Verification

```bash
# Backend
uv run ruff check .          # Lint (must pass clean)
uv run pytest tests/ -x      # Tests

# Frontend
cd frontend
npm run build                # Full build with TypeScript type check (must pass)
npm run lint                 # ESLint
```

---

## Configuration

### Environment Variables

```env
# Required: sets the backend URL for Next.js API routes to proxy to
INTERNAL_API_URL=http://localhost:5055
```

If `INTERNAL_API_URL` is not set, both runtime routes default to `http://localhost:5055`.

### Frontend Runtime URLs

| Chat | Next.js route | Backend endpoint |
|------|--------------|-----------------|
| Supervisor | `/api/copilotkit` | `/api/agui/chat` |
| CRUD | `/copilot-crud` | `/api/agui/crud-chat` |

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
| `frontend/src/components/providers/CopilotProvider.tsx` | App-level CopilotKit provider with error boundary; points at `/api/copilotkit` |
| `frontend/src/app/api/copilotkit/route.ts` | Supervisor CopilotRuntime — lazy singleton, registers `supervisor` and `default` HttpAgent |
| `frontend/src/app/copilot-crud/route.ts` | CRUD CopilotRuntime — lazy singleton, registers `crud` and `default` HttpAgent |
| `frontend/src/components/chat/SmartChatPanel.tsx` | Supervisor chat UI — registers all CopilotKit hooks and renders `CopilotChat` |
| `frontend/src/components/jobs/JobCrudChatPanel.tsx` | CRUD chat UI — scoped `CopilotKit` provider + `CrudToolRenderers` + `CopilotChat` |
| `frontend/src/components/chat/ToolResultRenderers.tsx` | 9 supervisor tool renderers + `useDefaultTool` fallback |
| `frontend/src/components/jobs/CrudToolRenderers.tsx` | `useLangGraphInterrupt` HITL + 2 CRUD tool renderers |
| `frontend/src/lib/hooks/useSmartChat.ts` | `useCoAgent` wrapper — manages supervisor state and ACM context toggle |
| `frontend/src/lib/types/smart-chat.ts` | `SupervisorAgentState` and tool result type definitions |
| `frontend/src/components/chat/renderers/ACMTableResult.tsx` | Tabular ACM record display with risk badges |
| `frontend/src/components/chat/renderers/ACMStatsResult.tsx` | Stats grid and building list card |
| `frontend/src/components/chat/renderers/SearchResult.tsx` | Document search result cards |
| `frontend/src/components/chat/renderers/AgentActivityIndicator.tsx` | Loading/complete indicator per tool |
| `frontend/src/components/chat/renderers/ToolErrorCard.tsx` | Error state for failed tools |
| `frontend/src/components/chat/renderers/HITLApprovalDialog.tsx` | HITL write approval card (approve / reject / edit) |
| `frontend/src/components/chat/renderers/WriteDiffView.tsx` | Before/after field diff display |
| `frontend/src/components/chat/renderers/BuildingSummaryCard.tsx` | Building summary with record and risk counts |
| `frontend/src/components/chat/renderers/ItemDetailCard.tsx` | Expandable ACM item card |
| `frontend/src/components/chat/renderers/ExtractionProgress.tsx` | Progress bar for extraction status |
| `frontend/src/components/chat/renderers/DefaultToolFallback.tsx` | Fallback renderer for unregistered tools |
| `open_notebook/graphs/supervisor_agent.py` | Supervisor LangGraph — ReAct loop with ACM + search tools, `copilotkit_emit_state` |
| `open_notebook/graphs/crud_agent.py` | CRUD LangGraph — `query_job_records` + `preview_write` + `interrupt()` approval node |
| `open_notebook/graphs/crud_tools.py` | CRUD tool implementations + `execute_pending_write` + `_pending_writes` store |
| `open_notebook/graphs/chat_tools/acm_tools.py` | ACM query tools: `search_acm_by_risk`, `search_acm_by_building`, `search_acm_by_room`, `search_acm_by_material`, `get_acm_stats`, `get_acm_record_detail`, `semantic_search_acm` |
| `open_notebook/graphs/chat_tools/search_tools.py` | Document search tools: `search_documents` (vector), `text_search_documents` |
| `api/routers/agui_chat.py` | `register_agui_endpoints()` and `register_crud_agui_endpoint()` — called from `api/main.py` |
