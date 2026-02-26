# ACM Extraction Pipeline Analysis
**Date**: 2026-02-25
**Purpose**: Comprehensive analysis of how the ACM extraction pipeline works, what's broken, and what's missing
**Audience**: Developer/owner wanting to understand the full system

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Pipeline Architecture Overview](#2-pipeline-architecture-overview)
3. [Detailed Execution Trace](#3-detailed-execution-trace)
4. [MinerU vs Docling: What Actually Runs](#4-mineru-vs-docling-what-actually-runs)
5. [Why You Get 17 Records Instead of 31](#5-why-you-get-17-records-instead-of-31)
6. [Why Anthropic Falls Back to Direct JSON Parsing](#6-why-anthropic-falls-back-to-direct-json-parsing)
7. [Why Records Arrive All At Once](#7-why-records-arrive-all-at-once)
8. [Why the Frontend Doesn't Show the Table Before AI Extraction](#8-why-the-frontend-doesnt-show-the-table-before-ai-extraction)
9. [AG-UI SSE Streaming Status](#9-ag-ui-sse-streaming-status)
10. [A2A Protocol Status](#10-a2a-protocol-status)
11. [Gap Analysis & Recommendations](#11-gap-analysis--recommendations)

---

## 1. Executive Summary

The ACM extraction pipeline has a **functional core** but several layers of infrastructure are either broken, dead code, or not wired up:

| Component | Status | Impact |
|-----------|--------|--------|
| PDF Upload + Source Creation | Working | - |
| Worker Command Queue | Working | - |
| Docling/Markdown Text Parsing | Working (via source processing) | PDF text is available |
| MinerU Table Extraction | **Dead code** — always returns `[]` | No structured table extraction before AI |
| LLM Extraction (LangGraph) | Working but fragile | Structured output fails → JSON fallback |
| Structured Output (`with_structured_output`) | **Fails every time** | "Grammar too large" from Anthropic |
| JSON Fallback Parsing | Working | The actual production path |
| Dedup + Validation + Save | Working | Records land in SurrealDB |
| AG-UI Event Emitter | Backend emits events | Events written to DB but frontend doesn't consume them |
| AG-UI SSE Endpoints | Backend endpoints exist | 2 endpoints, neither consumed by upload flow |
| Frontend Live Extraction Page | Exists (`/jobs/[id]/extract`) | Upload flow **skips** this page entirely |
| Frontend Record Display | Working (one-shot REST) | All records fetched after extraction completes |
| A2A Protocol | **Stub only** — tasks never complete | Not functional |

**Root cause of 17 records**: The worker process was running **stale code** before our 4 fixes were committed. The fixes improved extraction from 16/31 to 28/31 in testing, but the running worker never loaded the new code. You must **restart the worker** to pick up the changes.

---

## 2. Pipeline Architecture Overview

```
                     FRONTEND                              API                    WORKER
                   ┌──────────┐                     ┌────────────┐         ┌─────────────┐
                   │ Upload   │──POST /api/sources──│ Create     │         │             │
                   │ Dialog   │                     │ Source     │         │             │
                   └────┬─────┘                     └──────┬─────┘         │             │
                        │                                  │              │             │
                        │                                  ▼              │             │
                        │──POST /api/acm/extract──→ Submit command ──────→│ acm_extract │
                        │                          to surreal-commands    │  _command   │
                        │                                                │             │
                        │                                                │   ┌─────────┴──────────┐
                        │                                                │   │ LangGraph Pipeline  │
                        │                                                │   │ extract_metadata    │
                   ┌────┴─────┐                                          │   │ structure           │
                   │ Navigate │                                          │   │ inventory           │
                   │ to       │                                          │   │ tag_pages           │
                   │ /review/ │                                          │   │ orchestrate/extract │
                   │buildings │                                          │   │ validate            │
                   └────┬─────┘                                          │   │ deduplicate         │
                        │                                                │   │ save (to SurrealDB) │
                        │                                                │   └─────────┬──────────┘
                        │                                                │             │
                   ┌────┴─────┐                     ┌────────────┐       │             │
                   │ Fetch    │──GET /api/acm/records─│ Query     │←──────┘             │
                   │ Results  │                     │ SurrealDB  │                      │
                   └──────────┘                     └────────────┘                      │
                                                                                        ▼
                                                                              Embed records (Ollama)
```

### Key Architectural Facts
- **Extraction is async**: The API queues a command; the worker picks it up
- **Worker is a separate process**: Must be restarted to pick up code changes
- **No streaming to frontend**: Records saved in batch, fetched via REST
- **MinerU is dead code**: Table extraction was planned but never implemented
- **Docling (via `process_source`)**: Used only for raw text extraction, not table structure
- **All AI extraction is via LLM**: The LangGraph graph sends markdown text to Claude and parses the response

---

## 3. Detailed Execution Trace

### Step 1: Frontend Upload
**File**: `frontend/src/components/sources/AddSourceDialog.tsx:326-378`

User fills the 4-step wizard (Content → Site Config → Organization → Processing) and clicks Submit:

```
1. createSource.mutateAsync()      → POST /api/sources (creates source + uploads file)
2. acmApi.extract(source.id)       → POST /api/acm/extract (queues extraction command)
3. acmApi.saveConfig(source.id, …) → POST /api/acm/config (saves BAR metadata)
4. router.push(`/jobs/${id}/review/buildings`)  → Navigates away immediately
```

The `command_id` from step 2 is stored in `sessionStorage` under key `acm-extraction-{sourceId}`.

### Step 2: API Queues Command
**File**: `api/routers/acm.py:247-274`

```python
POST /api/acm/extract
  → CommandService.submit_command_job("open_notebook", "acm_extract", {
      "source_id": source_id,
      "model_id": model_id,
      "force": force
    })
  → Returns { command_id, status: "submitted" }
```

This creates a row in the SurrealDB `command` table with `status: "new"`.

### Step 3: Worker Picks Up Command
**File**: `commands/acm_commands.py:64-275`

The `surreal-commands` worker polls the `command` table. When it finds `status: "new"`:

1. **Atomic claim** (line 82-108): `UPDATE command SET status='running', claimed_by=... WHERE status='new'` — prevents race conditions
2. **Wait for source text** (line 120-147): Polls up to 120 seconds for `source.full_text` to be populated (by the `process_source` command that runs in parallel)
3. **Call extraction** (line 196): `extract_acm_from_source(source, model_id, force, command_id)`
4. **Embed records** (line 237-275): After extraction, uses Ollama `mxbai-embed-large` for vector embeddings

### Step 4: Source Text — Where Does It Come From?
**File**: `commands/source_commands.py` (process_source command)

When a source is created, a `process_source` command runs in parallel:
- Uses **Docling** (via `DocumentConverter`) to convert the PDF to markdown text
- Stores the result in `source.full_text` in SurrealDB
- This is the **raw text** that the LLM later receives — it's markdown, not structured tables

**Important**: Docling converts the PDF to markdown. It does NOT do structured table extraction. The markdown may contain pipe-delimited tables, but they're often poorly formatted or broken across pages.

### Step 5: LangGraph Extraction Pipeline
**File**: `open_notebook/graphs/acm_extraction.py:2341-2387`

The pipeline is a LangGraph `StateGraph` with these nodes:

```
START
  → extract_metadata      (extract school name, report date, etc.)
  → structure              (identify document sections: TOC, cover, buildings)
  → inventory              (compile building inventory from headers)
  → tag_pages              (classify each page: building_register, floor_plan, etc.)
  → [conditional: should_use_orchestrator?]
      → YES: orchestrate   (parallel per-building extraction, max 3 concurrent)
      → NO:  prepare → extract (sequential chunk-by-chunk)
  → validate               (BAR enum validation, field normalization)
  → [conditional: should_correct?]
      → YES: correct → validate (max 2 correction rounds)
      → NO: continue
  → deduplicate            (merge duplicate records by composite key)
  → save                   (write ACMRecord objects to SurrealDB)
END
```

### Step 6: LLM Extraction (The Critical Step)
**File**: `open_notebook/graphs/acm_extraction.py:1230-1458`

For each building/chunk, the pipeline:
1. Builds a prompt from `building_extraction.jinja` (the template we fixed)
2. Sends the markdown text + prompt to Claude via OpenRouter
3. **First tries** `model.with_structured_output(ACMExtractionResult)` — this ALWAYS FAILS (see Section 6)
4. **Falls back** to `model.ainvoke()` + `parse_json_response()` — this is what actually works
5. Parses the JSON into `ACMExtractionRecord` Pydantic models
6. Returns list of records

### Step 7: Dedup + Save
**File**: `open_notebook/graphs/acm_extraction.py:2067-2285`

- **Dedup**: `_generate_dedup_key()` creates composite key: `{school}_{building}_{area}_{room}_{product}_{sample_no}_{desc_hash}` — records with matching keys are merged
- **Save**: Creates `ACMRecord` domain objects and calls `await record.save()` to SurrealDB

### Step 8: Frontend Fetches Results
**File**: `api/routers/acm.py:65`

```
GET /api/acm/records?source_id={id}&limit=500
```

One-shot REST query. No streaming. No incremental delivery. The frontend `useACMRecords` hook fetches all records at once with `staleTime: 30s`.

---

## 4. MinerU vs Docling: What Actually Runs

### TL;DR: Neither is used for table extraction. Only Docling is used, and only for raw text.

### Docling
- **Used by**: `process_source` command (parallel to extraction)
- **Purpose**: Convert PDF → markdown text
- **How**: `DocumentConverter` from the `docling` library
- **Output**: `source.full_text` — raw markdown with page breaks
- **Does NOT**: Extract structured tables, identify columns, or produce tabular data

### MinerU
- **File**: `open_notebook/extractors/mineru_table_extractor.py`
- **Status**: **DEAD CODE**
- **The function `_extract_with_mineru()` in `acm_extractor.py:385-422` always returns `[]`** with a TODO comment: "Implement HTML table parsing to ACM records in future iteration"
- Even if `magic_pdf` is installed and GPU is available, no actual table extraction occurs
- The `acm_extractor.py` file itself is the **legacy regex-based parser** — it is NOT called by the LangGraph AI pipeline at all

### What actually parses the tables?
**The LLM does everything.** The pipeline sends raw markdown text (from Docling) to Claude and asks it to:
1. Identify building headers
2. Find BAR register tables
3. Extract individual records from the tables
4. Return structured JSON

This is why accuracy depends entirely on the LLM prompt quality and the markdown formatting.

---

## 5. Why You Get 17 Records Instead of 31

There are **three compounding causes**:

### Cause 1: Worker Running Stale Code (PRIMARY CAUSE)
The worker process (`uv run run_worker.py`) loads Python modules at startup. When you modify code and commit, the **running worker still has the old code in memory**. Our 4 fixes (committed as `d44e211`) are:

| Fix | What It Does | Impact |
|-----|-------------|--------|
| FIX 1 | Added `sample_no` to dedup key | Prevents false merges (was losing ~2 records) |
| FIX 2 | Rewrote prompt rules 8, 11 + completeness counter | LLM now extracts "As Per" and "Not Sampled" rows |
| FIX 3 | Expanded valid schema values | "Not Sampled", "No Access", "N/A (negative)" no longer rejected |
| FIX 5 | Route Anthropic models to Anthropic provider only | Prevents Google provider rejecting anthropic-beta header |

**To apply**: Stop and restart the worker process.

### Cause 2: Structured Output Failure → Degraded Prompt Handling
The `with_structured_output()` call always fails (see Section 6). The fallback path (`parse_json_response()`) works but may handle the prompt context differently, potentially losing some instruction emphasis.

### Cause 3: LLM Extraction Limitations
Even with all fixes applied, our E2E test shows 28/31 (not 31/31). The 3 still-missing records are all "Not Sampled" / "No Access" items that the LLM consistently fails to extract:

1. Switch Room / Fuse cartridge (Not Sampled)
2. Lift Foyer / Lift / Internal lining (Not Sampled)
3. Main Foyer / Room Adjacent Disabled Toilet (No Access)

These items appear in the PDF as rows with minimal data (no sample number, no lab result) and the LLM treats them as non-records despite explicit prompt instructions.

---

## 6. Why Anthropic Falls Back to Direct JSON Parsing

### The Error
```
Error code: 400
"The compiled grammar is too large, which would cause performance issues.
 Simplify your tool schemas or reduce the number of strict tools."
Provider: Anthropic
```

### Root Cause
LangChain's `with_structured_output()` converts the Pydantic schema `ACMExtractionResult` into a tool/function schema and sends it to the API with `strict: true`. The `ACMExtractionResult` schema is complex:

- It contains a list of `ACMExtractionRecord` objects
- Each `ACMExtractionRecord` has 40+ fields
- Many fields have `Literal` type constraints (enum values)
- Several fields have complex validation rules

When Anthropic (via OpenRouter) receives this schema, it compiles a **constrained grammar** to ensure the output conforms. The schema is too complex for the grammar compiler, so it rejects the request.

### The Fallback Path
```
acm_extraction.py:1387-1458

1. with_structured_output() → 400 error from Anthropic
2. Catches exception
3. Re-calls model.ainvoke() WITHOUT structured output (plain text response)
4. parse_json_response() extracts JSON from the text response
5. Validates against Pydantic schemas manually
```

### In the Orchestrator (separate fallback)
```
orchestrator.py:499-544

1. is_provider_schema_error(error) detects the 400
2. Logs: "Provider schema/compat error detected"
3. Falls back to direct invocation with manual JSON parsing
4. This is the log message you're seeing
```

### Impact
The JSON fallback **works** — it's actually the production path. But it means:
- The LLM gets no schema enforcement during generation (may produce invalid JSON)
- Response parsing must handle edge cases (trailing commas, missing brackets, etc.)
- `parse_json_response()` has heuristic JSON extraction from mixed text/JSON responses

### Fix Options
1. **Simplify the schema**: Reduce fields or split into multiple smaller tool calls (significant refactor)
2. **Always use JSON mode**: Skip `with_structured_output()` entirely and go straight to JSON parsing (easy, already working)
3. **Use Anthropic native API**: Instead of OpenRouter, call Anthropic directly which may handle the schema differently

---

## 7. Why Records Arrive All At Once

### Architecture Reason
The LangGraph pipeline runs as a batch process in the worker:

```
extract_metadata → structure → inventory → tag_pages → orchestrate → validate → deduplicate → save
```

The `save` node runs **at the very end** and writes ALL records to SurrealDB in one batch. There is no intermediate save point.

### Frontend Reason
The frontend fetches records via:
```
GET /api/acm/records?source_id={id}
```

This is a one-shot REST query with `staleTime: 30s`. It doesn't poll. It doesn't use SSE. The query is only invalidated when `useExtractionStatus` detects that the extraction command has completed.

### The Streaming Infrastructure That Exists But Isn't Used

There IS a `RawExtractionTable` component that was designed for incremental display:
- **File**: `frontend/src/components/acm/RawExtractionTable.tsx`
- Uses `useExtractionAgent()` (CopilotKit `useCoAgent`)
- Designed to receive records via AG-UI `StateDelta` events
- Located on the `/jobs/[id]/extract` page

**BUT**: The upload wizard navigates to `/jobs/[id]/review/buildings`, completely bypassing the extract page. The live extraction table is never shown in the primary user flow.

### AG-UI Events ARE Emitted (But Not Consumed)
The backend `AGUIEventEmitter` writes `StateDelta` events to the `agui_events` SurrealDB table as records are extracted. The SSE endpoint at `/api/agui/extraction/{command_id}/stream` serves these events. But:

1. The frontend upload flow skips the extract page
2. The building review page has NO SSE connection
3. The record review page uses REST, not SSE

---

## 8. Why the Frontend Doesn't Show the Table Before AI Extraction

### There Is No Pre-AI Table View

The pipeline does not have a "show raw PDF table → then run AI on it" step. The design is:

1. Docling converts PDF → markdown (raw text, not structured data)
2. The LLM receives the markdown and extracts structured records
3. Records are saved to the database
4. Frontend fetches records from the database

There is no intermediate step where the user sees the raw table data from the PDF before AI processing. This would require:
- MinerU (or similar) to extract structured tables from the PDF
- A frontend component to display the raw table
- A user action to trigger AI extraction on the raw table

MinerU was supposed to fill this gap but is **dead code** (always returns `[]`).

### The Upload Flow Routing Problem

Even the existing live extraction view is skipped:

```
AddSourceDialog.tsx:378
  router.push(`/jobs/${createdSource.id}/review/buildings`)
                        ↑
          Goes directly to review — skips /jobs/{id}/extract
```

The `/jobs/{id}/extract` page shows:
- `ExtractionProgressPanel` with stage progress pills
- `RawExtractionTable` with live-streaming records

But the user never sees this page during the primary upload flow.

### Building Review Page Has No Extraction Awareness

The `BuildingReviewGrid` at `/jobs/[id]/review/buildings`:
- Fetches buildings via `GET /api/acm/jobs/{sourceId}/buildings`
- `staleTime: 30_000`, no polling, no SSE
- No banner showing "Extraction in progress..."
- No automatic refresh when extraction completes
- If extraction hasn't finished, the user sees an empty grid

---

## 9. AG-UI SSE Streaming Status

### Backend: Partially Implemented

| Component | File | Status |
|-----------|------|--------|
| `AGUIEventEmitter` class | `open_notebook/extractors/agui_event_emitter.py` | **Implemented** — emits RunStarted, StepStarted, StepFinished, StateDelta, ToolCallStart/End, RunFinished, RunError events |
| Event persistence | Same file | **Implemented** — writes to `agui_events` SurrealDB table via fire-and-forget tasks |
| AG-UI SSE endpoint | `api/routers/agui_extraction.py` | **Implemented** — `GET /api/agui/extraction/{command_id}/stream` polls `agui_events` table |
| Pipeline Logger SSE | `api/routers/extraction_events.py` | **Implemented** — `GET /api/acm/extraction-progress/{command_id}/stream` polls `extraction_progress` table |
| Emitter injection | `open_notebook/graphs/acm_extraction.py:2431-2432` | **Implemented** — emitter created when `command_id` is provided |
| Stage event calls | Throughout `acm_extraction.py` | **Implemented** — emit calls at extract_metadata, structure, inventory, tag_pages, extract, validate, correct, deduplicate, save |

### Frontend: Partially Implemented (But Not Wired)

| Component | File | Status |
|-----------|------|--------|
| `ExtractionProgressPanel` | `frontend/src/components/acm/ExtractionProgressPanel.tsx` | **Implemented** — shows 7 stage pills, log stream, progress bar |
| `ExtractionThinkingPanel` | `frontend/src/components/acm/ExtractionThinkingPanel.tsx` | **Implemented** — shows LLM reasoning text |
| `ExtractionToolCallFeed` | `frontend/src/components/acm/ExtractionToolCallFeed.tsx` | **Implemented** — shows tool call events |
| `useExtractionProgress` hook | `frontend/src/hooks/use-extraction-progress.ts` | **Implemented** — connects to PipelineLogger SSE endpoint |
| `useExtractionAgent` hook | `frontend/src/hooks/use-extraction-agent.ts` | **Implemented** — CopilotKit `useCoAgent` for AG-UI streaming |
| `RawExtractionTable` | `frontend/src/components/acm/RawExtractionTable.tsx` | **Implemented** — live AG Grid with streaming records |
| `/jobs/[id]/extract` page | `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` | **Implemented** — combines ExtractionProgressPanel + RawExtractionTable |

### The Gap: Wiring

1. **Upload flow skips extract page** — navigates to `/review/buildings` instead
2. **Building review page has no SSE** — doesn't import any extraction hooks
3. **Job detail "Extraction Log" tab** — shows ExtractionProgressPanel but only if you navigate there manually
4. **Two parallel SSE systems** — PipelineLogger and AGUIEventEmitter produce separate event streams; frontend consumes PipelineLogger but not AG-UI events in the main flow
5. **CopilotKit runtime** — `useExtractionAgent` relies on a CopilotKit `useCoAgent` hook which needs a CopilotKit runtime context; not clear if this is configured for the extraction agent

### What You'd See If It Worked

If the upload flow went to `/jobs/[id]/extract` instead of `/review/buildings`:
- Stage progress pills would light up as each pipeline stage completes
- Log messages would stream in real-time
- Records would appear one-by-one in the RawExtractionTable
- LLM thinking/reasoning would show in the expandable panel
- A "Proceed to Review" button would appear when done

---

## 10. A2A Protocol Status

### Status: Stub Only — Not Functional

| Component | File | Status |
|-----------|------|--------|
| A2A router | `api/routers/a2a.py` | **Stub** — `POST /api/a2a/tasks` creates a task in `a2a_tasks` table with status `submitted` |
| A2A task model | `open_notebook/domain/a2a.py` (if exists) | Not verified |
| Worker → A2A callback | None | **Missing** — worker never writes back to `a2a_tasks` table |
| A2A agent routing | None | **Missing** — no agent-to-agent dispatch mechanism |

The A2A (Agent-to-Agent) protocol was planned but only the API endpoint exists. Tasks created via `POST /api/a2a/tasks` are stuck at `submitted` status forever because:
1. The worker's `acm_extract_command` uses the `command` table, not `a2a_tasks`
2. No callback writes task completion back to the A2A table
3. No agent-to-agent routing or delegation exists

---

## 11. Gap Analysis & Recommendations

### Critical (Causing Extraction Failure)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 1 | **Worker running stale code** | 17 records instead of 28 | Restart the worker process |
| 2 | **Structured output always fails** | Extra latency (double API call) | Consider skipping `with_structured_output()` entirely |

### High Priority (Broken UX)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 3 | **Upload flow skips extract page** | No live extraction feedback | Change `AddSourceDialog.tsx:378` to navigate to `/jobs/{id}/extract` instead |
| 4 | **Building review has no extraction awareness** | User sees empty grid during extraction | Add `useExtractionStatus` hook + "Extraction in progress" banner |
| 5 | **AG-UI events emitted but not consumed** | Wasted backend work, no frontend benefit | Wire `useExtractionAgent` to the extract page (or create new consumption hook) |

### Medium Priority (Dead Code / Tech Debt)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 6 | **MinerU is dead code** | No structured table extraction | Either implement or remove |
| 7 | **acm_extractor.py (regex parser) unused** | Confusing codebase | Remove or archive |
| 8 | **Two parallel SSE systems** | Confusion, maintenance overhead | Consolidate PipelineLogger + AGUIEventEmitter |
| 9 | **A2A tasks never complete** | Non-functional feature | Implement callback or remove stub |
| 10 | **`useExtractionAgent` (CopilotKit)** never used in main flow | Dead frontend code | Wire up or remove |

### Low Priority (3 Missing Records)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 11 | **3 "Not Sampled" records not extracted** | 28/31 vs 31/31 | Further prompt engineering or multi-pass extraction |

---

## Appendix A: Key File Reference

### Extraction Pipeline (execution order)
| Step | File | Function/Line | What It Does |
|------|------|--------------|-------------|
| 1 | `frontend/src/components/sources/AddSourceDialog.tsx:348-360` | `submitSingleSource()` | Triggers extraction via API |
| 2 | `api/routers/acm.py:247-274` | `POST /api/acm/extract` | Queues command to SurrealDB |
| 3 | `commands/acm_commands.py:64-275` | `acm_extract_command()` | Worker picks up and processes |
| 4 | `open_notebook/graphs/acm_extraction.py:2393` | `extract_acm_from_source()` | Entry point to LangGraph |
| 5 | `open_notebook/graphs/acm_extraction.py:523-600` | `extract_metadata()` | Extract school name, date, etc. |
| 6 | `open_notebook/graphs/acm_extraction.py:603-750` | `structure_document()` | Identify document sections |
| 7 | `open_notebook/graphs/acm_extraction.py:753-900` | `compile_inventory()` | Build building inventory |
| 8 | `open_notebook/graphs/acm_extraction.py:903-1050` | `tag_pages()` | Classify pages by type |
| 9 | `open_notebook/extractors/orchestrator.py:237` | `orchestrate()` | Per-building parallel extraction |
| 10 | `open_notebook/graphs/acm_extraction.py:1230-1458` | `extract_records()` | LLM call + JSON parsing |
| 11 | `open_notebook/graphs/acm_extraction.py:1481-1755` | `validate_records()` | BAR enum validation |
| 12 | `open_notebook/graphs/acm_extraction.py:2067` | `deduplicate_records()` | Merge duplicate records |
| 13 | `open_notebook/graphs/acm_extraction.py:2122-2285` | `save_records()` | Write to SurrealDB |

### AG-UI / SSE
| File | What It Does |
|------|-------------|
| `open_notebook/extractors/agui_event_emitter.py` | Emits AG-UI events to SurrealDB |
| `open_notebook/extractors/pipeline_logger.py` | Logs pipeline progress to SurrealDB |
| `api/routers/agui_extraction.py` | SSE endpoint: `/api/agui/extraction/{cmd}/stream` |
| `api/routers/extraction_events.py` | SSE endpoint: `/api/acm/extraction-progress/{cmd}/stream` |
| `frontend/src/hooks/use-extraction-progress.ts` | Consumes PipelineLogger SSE |
| `frontend/src/hooks/use-extraction-agent.ts` | CopilotKit AG-UI streaming (unused) |
| `frontend/src/components/acm/ExtractionProgressPanel.tsx` | Stage progress UI |
| `frontend/src/components/acm/RawExtractionTable.tsx` | Live record streaming table |
| `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` | Live extraction page (skipped in upload flow) |

### Dead Code
| File | Why Dead |
|------|----------|
| `open_notebook/extractors/mineru_table_extractor.py` | `_extract_with_mineru()` returns `[]` |
| `open_notebook/extractors/acm_extractor.py` | Legacy regex parser, not called by LangGraph pipeline |
| `frontend/src/hooks/use-extraction-agent.ts` | CopilotKit hook, never imported in main flow |

---

## Appendix B: Log Analysis

### Your Worker Log Decoded

```
2026-02-25 13:28:10.862 | WARNING | orchestrator:_llm_extract_building:503
  Building Broadmeadows Police Station: Provider schema/compat error detected
  (Error code: 400 - "The compiled grammar is too large")
  Falling back to direct invocation with manual JSON parsing.
```
**Translation**: Anthropic rejected the structured output schema. The pipeline fell back to direct `ainvoke()` + `parse_json_response()`. This fallback **is working correctly** — it's the expected production path.

```
2026-02-25 13:29:09.648 | INFO | acm_embedding_service:embed_records:63
  Starting ACM embedding for 17 records
```
**Translation**: After extraction completed, 17 records were saved and then embedded. The low count (17 vs 31) is because the worker ran with pre-fix code.

```
2026-02-25 13:29:10.381 | INFO | acm_embedding_service:embed_records:121
  ACM embedding complete: 17/17 records embedded
```
**Translation**: All 17 records were successfully embedded with the Ollama `mxbai-embed-large` model.
