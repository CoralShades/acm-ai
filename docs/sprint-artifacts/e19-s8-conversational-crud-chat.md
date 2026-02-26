# Story E19-S8: Conversational CRUD Chat (P1)

**Epic:** E19 — Standard User UX Redesign
**Priority:** P1
**Status:** Done
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S6

---

## User Story

**As a** compliance officer reviewing ACM records in a job,
**I want to** ask questions and make corrections using natural language in a chat interface,
**So that** I can query, update, add, and remove records without learning the grid interface for complex operations.

---

## Background

The existing Chat feature (E4) supports read-only ACM queries using CopilotKit + AG-UI + LangGraph supervisor agent. This story extends the chat to support full CRUD operations, scoped to the current job's records only. The global register chat remains read-only.

The taxonomy and mapping instructions from `docs/samplePDF/instructions-sample/` are used as context to ensure the agent understands ACM domain vocabulary correctly.

---

## Acceptance Criteria

### Chat Location
- [x] Conversational CRUD chat accessible from the Job Detail page (E19-S7) as a panel or tab
- [x] Available for jobs with status `published` or in `acm_review`
- [x] Global register chat (`/chat` route) remains read-only — no CRUD there

### Read Operations
- [x] "How many records are in Building A?" → agent returns count with rendered result card
- [x] "Show me all friable items" → agent renders filtered results in a mini AG Grid component in chat
- [x] "Which rooms have No Access records?" → agent queries and renders structured response

### Write Operations (scoped to current job only)
- [x] "Update the sample result for item X to Positive" → agent shows `preview_write` confirmation card
- [x] "Add a new record for the roof boiler room with Friable Non-Friable sheeting" → agent creates record with confirmation
- [x] "Delete the duplicate row for room 204" → agent shows affected row, requires explicit confirmation
- [x] "Mark the battery charger fuse cartridge as Not Sampled" → agent updates the field

### Confirmation Protocol (all write operations)
- [x] Agent generates a `preview_write` AG-UI component before any write:
  - Shows: operation type (UPDATE/INSERT/DELETE), affected record(s), field changes
  - [Confirm] and [Cancel] buttons rendered in chat
- [x] Write is NOT executed until user clicks [Confirm]
- [x] Agent executes write only after confirmation, then shows success message

### Audit Log
- [x] Every confirmed write logged to a new `crud_audit` table:
  - `job_id`, `timestamp`, `natural_language_input`, `generated_surql`, `operation`, `confirmed_by: 'user'`

### Domain Context
- [x] Agent loaded with taxonomy files as system context:
  - `register_taxonomy.nonfriable.json`
  - `register_taxonomy.friable.json`
  - `register_row.schema.json`
  - `register_enums.json`
  - `consultant_wording_rules.json`
- [x] Agent understands ACM domain terminology (friable, non-friable, NATA sample, BAR columns)

---

## Technical Notes

### Architecture Extension
```
Existing E4 Chat Flow:
User → CopilotKit → AG-UI SSE → Supervisor Agent → [read tools] → Response

New E19-S8 CRUD Chat Flow:
User → CopilotKit → AG-UI SSE → CRUD Agent → [read tools + preview_write tool] → Confirmation Component → [write tools] → Response
```

### New LangGraph Tools
```python
# New tools added to supervisor agent (scoped to source_id)
@tool
async def preview_write(operation: str, surql: str, source_id: str) -> PreviewResult:
    """Previews a write operation without executing it. Returns affected rows."""

@tool
async def execute_confirmed_write(operation_id: str, source_id: str) -> WriteResult:
    """Executes a previously previewed write after user confirmation."""

@tool
async def query_job_records(query: str, source_id: str) -> QueryResult:
    """Executes a read-only SurrealQL query scoped to source_id."""
```

### AG-UI Confirmation Component
```typescript
// New component rendered in chat stream
interface WriteConfirmationProps {
  operationType: 'UPDATE' | 'INSERT' | 'DELETE';
  affectedRecords: ACMRecord[];
  fieldChanges: FieldChange[];
  operationId: string;
  onConfirm: () => void;
  onCancel: () => void;
}
```

### Audit Log Migration
New migration (033) or bundled in 032:
```surql
DEFINE TABLE crud_audit SCHEMAFULL;
DEFINE FIELD job_id ON crud_audit TYPE record<source>;
DEFINE FIELD timestamp ON crud_audit TYPE datetime DEFAULT time::now();
DEFINE FIELD natural_language ON crud_audit TYPE string;
DEFINE FIELD generated_surql ON crud_audit TYPE string;
DEFINE FIELD operation ON crud_audit TYPE string;
DEFINE FIELD confirmed_by ON crud_audit TYPE string DEFAULT 'user';
```

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `open_notebook/graphs/chat.py` (or supervisor graph) | Modified — add CRUD tools + scope to source_id |
| `open_notebook/graphs/crud_tools.py` | **New** — preview_write, execute_write, query tools |
| `frontend/src/components/chat/WriteConfirmationCard.tsx` | **New** — confirmation AG-UI component |
| `frontend/src/app/jobs/[id]/chat/page.tsx` | **New** — job-scoped chat page |
| `migrations/033_crud_audit.surql` | **New** — audit log table |

---

## Dev Notes

⚠️ **Security note:** All SurrealDB write queries must be scoped with `WHERE source_id = $source_id` to prevent cross-job data modification. The LangGraph agent must validate that the source_id in every generated query matches the authenticated job context.

No extraction API cost — this story makes SurrealDB queries, not LLM extraction calls.

---

## Estimated Effort

XL (Extra Large) — LangGraph CRUD tools, confirmation protocol, audit logging, new chat UI components.

---

**Story Status:** ⬜ BACKLOG (P1 — implement after E19-S1..S7 are complete)
