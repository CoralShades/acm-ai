# Story 1.21: Extraction Pipeline Observability & Structured Logging

Status: done

<!-- Aligns with AG-UI Pipeline Spec (docs/ag-ui-pipeline-spec.md) stage definitions -->
<!-- Precursor to full SSE streaming (future story) — instruments the backend first -->

## Story

As a **developer monitoring terminal output during extraction**,
I want **structured, stage-by-stage progress logging with metrics at each pipeline node**,
so that **I can see real-time extraction progress in the API/worker terminals including pages processed, tables extracted, records found, models used, and which pipeline stage is active**.

## Problem

Currently the extraction pipeline logs are sparse and unstructured:
- No logging during chunking (`_chunk_content`) — completely silent
- No logging during page assignment (`_assign_record_page`) — silent
- No logging of LangGraph node transitions — silent
- No logging of model/prompt selection
- Worker terminal shows only start and end — nothing during the 30s-3min extraction
- Existing `logger.info` messages are inconsistent in format and missing key metrics
- No visibility into which AI model was provisioned or what prompt template was used
- No per-chunk progress (e.g., "Chunk 3/7, pages 14-18, 12 records so far")

## Acceptance Criteria

1. **Stage transition logging**: Each LangGraph node emits a structured `[STAGE]` log on entry and exit with timing, e.g., `[STAGE] extract_metadata | STARTED` and `[STAGE] extract_metadata | COMPLETED in 1.2s | consultant=Prensa, fields=8`
2. **Chunk progress logging**: During `extract_records`, each chunk logs: chunk index/total, page range, records extracted, model used, e.g., `[EXTRACT] Chunk 3/7 | pages 14-18 | 12 records | model=gpt-4o | 2.3s`
3. **Pipeline summary logging**: At pipeline end, a summary block is logged with all metrics: total pages, total chunks, records created/rejected/unidentified, extraction time, model(s) used, strategy per building, confidence distribution
4. **Model/prompt tracking**: Log which AI model was provisioned and which prompt template was rendered for each LLM call (extraction, correction, classification)
5. **Pydantic event models created**: Create `open_notebook/extractors/pipeline_events.py` with the event models from AG-UI spec Section 11.5 (StageId, StageStatus, StageState, etc.) as foundation for future SSE streaming
6. **PipelineLogger utility class**: Create a reusable `PipelineLogger` that wraps `loguru` to emit structured stage logs and internally builds a `PipelineRunState` for future SSE integration
7. **Worker terminal output enhanced**: The `acm_extract` command in `commands/acm_commands.py` logs extraction progress including stage transitions, not just start/end
8. **Backward compatible**: All existing log messages preserved, new structured logs are additive

## Tasks / Subtasks

- [x] Task 1: Create Pydantic pipeline event models (AC: #5)
  - [x] 1.1 Create `open_notebook/extractors/pipeline_events.py` with StageId, StageStatus, StageState, PipelineRunState, and all event models from AG-UI spec Section 11.5
  - [x] 1.2 Include `PipelineRunStatus` enum (idle, running, completed, failed, partial)
  - [x] 1.3 Include stage metadata constants (name, description per stage)

- [x] Task 2: Create PipelineLogger utility (AC: #1, #6)
  - [x] 2.1 Create `open_notebook/extractors/pipeline_logger.py` with `PipelineLogger` class
  - [x] 2.2 Methods: `stage_enter(stage_id, message)`, `stage_progress(stage_id, progress, message, **metrics)`, `stage_complete(stage_id, summary, **metrics)`, `stage_fail(stage_id, error)`
  - [x] 2.3 Each method logs a structured line via `loguru` AND updates internal `PipelineRunState`
  - [x] 2.4 Format: `[PIPELINE] [STAGE_NAME] STATUS | message | key=value pairs`
  - [x] 2.5 `summary()` method returns final `PipelineRunState` with all timings and metrics

- [x] Task 3: Instrument extraction graph nodes (AC: #1, #2, #3, #4)
  - [x] 3.1 Pass `PipelineLogger` instance through `ExtractionState` (add to TypedDict)
  - [x] 3.2 Instrument `extract_metadata` node: log entry/exit with consultant name, field count
  - [x] 3.3 Instrument `extract_structure` node: log document type, register start page, building count
  - [x] 3.4 Instrument `compile_inventory` node: log building count, page ranges
  - [x] 3.5 Instrument `tag_page_sections` node: log pages tagged, register range
  - [x] 3.6 Instrument `prepare_context` node: log content length, chunks created, token counts
  - [x] 3.7 Instrument `extract_records` node: per-chunk logging with chunk index/total, page range, records extracted, model used, prompt template, time per chunk
  - [x] 3.8 Instrument `validate_records` / `validate_records_strict`: log accepted/rejected counts, rejection reasons
  - [x] 3.9 Instrument `correct_records`: log auto-corrected/LLM-corrected/failed counts, model used
  - [x] 3.10 Instrument `deduplicate_records`: log duplicates merged
  - [x] 3.11 Instrument `save_records`: log parent sections created, records saved, embedding status
  - [x] 3.12 Log model provisioning in `provision_langchain_model` calls: model name, max_tokens

- [x] Task 4: Add pipeline summary to extraction output (AC: #3)
  - [x] 4.1 Add `pipeline_run` field to `ACMExtractionOutput` (Optional[dict] — serialized PipelineRunState)
  - [x] 4.2 In `extract_acm_from_source`, collect PipelineLogger summary and include in output
  - [x] 4.3 Log final summary block at pipeline end: total stages completed, total time, records created/rejected, confidence distribution, models used

- [x] Task 5: Enhance worker command logging (AC: #7)
  - [x] 5.1 In `acm_commands.py`, log extraction start with source title and page count
  - [x] 5.2 Log pipeline summary from extraction result
  - [x] 5.3 Log embedding progress (starting, count, time)

- [x] Task 6: Tests (AC: #1-#8)
  - [x] 6.1 Unit test PipelineLogger: stage transitions, timing, summary generation
  - [x] 6.2 Unit test pipeline event models: serialization, enum values
  - [x] 6.3 Integration test: verify extraction produces pipeline_run in output

## Dev Notes

### AG-UI Pipeline Spec Reference

The full spec is at `docs/ag-ui-pipeline-spec.md` (DRAFT). This story implements the **backend instrumentation layer** — Pydantic models and structured logging. Future stories will add:
- SSE endpoint (`GET /api/extraction/{source_id}/events`)
- Frontend pipeline visualization component
- CopilotKit integration

### Pipeline Stage Mapping to Graph Nodes

| Stage ID | AG-UI Stage Name | Graph Node(s) |
|----------|-----------------|---------------|
| `-1` | Document Structure Analysis | `extract_metadata`, `extract_structure`, `compile_inventory`, `tag_page_sections` |
| `0` | Preflight | (inline in `prepare_context`) |
| `0.5` | Agentic Orchestrator | `orchestrate_extraction` (E1-S20) |
| `1` | Extract | `extract_records` (chunk loop) |
| `2` | Interpret | `validate_records`, `validate_records_strict` |
| `2.5` | Corrective Validation | `correct_records` (loop) |
| `3` | Enrich & Store | `save_records` + embedding in `acm_commands.py` |

### Structured Log Format

```
[PIPELINE] ============================================================
[PIPELINE] Starting extraction for source:abc123 (52 pages)
[PIPELINE] ============================================================
[PIPELINE] [STRUCTURE] STARTED | Extracting document metadata...
[PIPELINE] [STRUCTURE] COMPLETED in 1.2s | consultant=Prensa, fields=8
[PIPELINE] [STRUCTURE] STARTED | Compiling building inventory...
[PIPELINE] [STRUCTURE] COMPLETED in 0.8s | buildings=4, pages=14-48
[PIPELINE] [ORCHESTRATOR] STARTED | Planning extraction strategy...
[PIPELINE] [ORCHESTRATOR] COMPLETED in 0.3s | strategy: 3x FULL_LLM, 1x REGEX_ONLY
[PIPELINE] [EXTRACT] STARTED | Processing 7 chunks across 4 buildings
[PIPELINE] [EXTRACT] Chunk 1/7 | pages 14-18 | model=openrouter/google/gemini-2.0-flash | 12 records | 2.3s
[PIPELINE] [EXTRACT] Chunk 2/7 | pages 19-24 | model=openrouter/google/gemini-2.0-flash | 18 records | 3.1s
...
[PIPELINE] [EXTRACT] COMPLETED in 18.4s | 87 raw records from 7 chunks
[PIPELINE] [VALIDATE] STARTED | Validating 87 records...
[PIPELINE] [VALIDATE] COMPLETED in 0.1s | 82 accepted, 5 rejected (missing: product=3, result=2)
[PIPELINE] [CORRECT] STARTED | Correcting 8 records with issues...
[PIPELINE] [CORRECT] COMPLETED in 1.5s | auto=5, llm=2, failed=1 | model=openrouter/google/gemini-2.0-flash
[PIPELINE] [STORE] STARTED | Saving 82 records...
[PIPELINE] [STORE] COMPLETED in 2.1s | 82 saved, 4 parent sections, enriched_text generated
[PIPELINE] ============================================================
[PIPELINE] EXTRACTION COMPLETE | 82 records in 24.4s
[PIPELINE]   Pages processed: 52 | Chunks: 7 | Buildings: 4
[PIPELINE]   Records: 82 created, 5 rejected, 3 unidentified
[PIPELINE]   Confidence: high=68, medium=12, low=2
[PIPELINE]   Models: openrouter/google/gemini-2.0-flash (extraction, correction)
[PIPELINE]   Strategy: FULL_LLM=3, REGEX_ONLY=1
[PIPELINE] ============================================================
```

### Key Architecture Decisions

1. **PipelineLogger is passed through ExtractionState** — not a global singleton. Each extraction run gets its own logger instance for isolation.
2. **Loguru structured logging** — uses existing loguru, not a new logging framework. Structured fields via `logger.bind()` or formatted strings.
3. **PipelineRunState is in-memory** — not persisted to DB in this story. Future SSE story will stream it.
4. **Model name tracking** — `provision_langchain_model` returns the model object; we need to capture the model ID used and pass it back through state.
5. **No frontend changes** — this story is purely backend terminal output enhancement.

### Existing Infrastructure to Reuse

- `open_notebook/graphs/utils.py:provision_langchain_model()` — model provisioning (needs model_id passthrough)
- `open_notebook/extractors/acm_schemas.py:ExtractionState` — state TypedDict (add pipeline_logger field)
- `commands/acm_commands.py:ACMExtractionOutput` — output model (add pipeline_run field)
- `open_notebook/graphs/acm_extraction.py:extract_acm_from_source()` — main entry point (instantiate PipelineLogger)
- `docs/ag-ui-pipeline-spec.md` Section 11.5 — Pydantic event model definitions (copy and adapt)

### References

- [AG-UI Pipeline Transparency Spec](docs/ag-ui-pipeline-spec.md) — Full observability spec (DRAFT)
- [E1-S20 Story](e1-s20-agentic-extraction-orchestrator.md) — OrchestratorStats pattern
- [acm_extraction.py](open_notebook/graphs/acm_extraction.py) — Main extraction graph
- [acm_commands.py](commands/acm_commands.py) — Worker command
- [acm_schemas.py](open_notebook/extractors/acm_schemas.py) — Extraction state/models

## File List

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/pipeline_events.py` | Created | Pydantic event models (StageId, StageStatus, StageState, PipelineRunState, SSE events) |
| `open_notebook/extractors/pipeline_logger.py` | Created | PipelineLogger utility class wrapping loguru |
| `open_notebook/graphs/acm_extraction.py` | Modified | Added pipeline_logger to ExtractionState, instrumented all graph nodes, pipeline summary |
| `open_notebook/extractors/acm_schemas.py` | Modified | Added pipeline_run field to ACMExtractionOutput |
| `commands/acm_commands.py` | Modified | Enhanced worker logging (source title, embedding progress) |
| `tests/test_pipeline_observability.py` | Created | 36 tests: event models, PipelineLogger, log format verification, integration |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes
1. Created `pipeline_events.py` with 7 StageId enums, 5 StageStatus values, 5 PipelineRunStatus values, 7 stage metadata constants, full set of SSE event models adapted from AG-UI spec Section 11.5
2. Created `PipelineLogger` class with stage_enter/progress/complete/fail/skip lifecycle, model tracking, complete() and fail() summary methods that emit formatted [PIPELINE] banner blocks
3. Instrumented all 10 graph nodes: extract_metadata, extract_structure, compile_inventory, tag_page_sections, prepare_context, extract_records (per-chunk), validate_records_strict, correct_records, deduplicate_records, save_records
4. PipelineLogger is per-run (not singleton), passed through ExtractionState TypedDict, with null-safe access via `_get_pipeline_logger()` for backward compatibility
5. Pipeline summary includes: total pages, chunks, buildings, records created/rejected, confidence distribution, models used, strategy distribution
6. Worker command enhanced: logs source title + text length on start, [PIPELINE] [EMBED] STARTED/COMPLETED for embedding phase
7. All existing log messages preserved — new [PIPELINE] logs are purely additive
8. 36 tests total: 7 for enums, 5 for event model serialization, 11 for PipelineLogger lifecycle, 2 for ACMExtractionOutput pipeline_run field, 5 for state models, 6 for structured log format verification

### Senior Developer Review (AI)

**Reviewer**: Code Review Workflow (adversarial)
**Date**: 2026-02-10
**Outcome**: Approved with fixes applied

**Issues Found**: 3 High, 3 Medium, 1 Low — **all fixed automatically**

| ID | Severity | Issue | Fix |
|----|----------|-------|-----|
| H1 | HIGH | ORCHESTRATOR stage never instrumented | Created `orchestrate_with_logging` wrapper, added `stage_skip` in `prepare_context` |
| H2 | HIGH | Prompt template never logged (AC #4) | Added `[PIPELINE] Prompt template: acm/extraction` and `acm/correction` log lines |
| H3 | HIGH | Model ID logged is request, not resolved | Extract actual model name from `model.model_name` or `model.model` after provisioning |
| M1 | MEDIUM | `stage_complete` on error path masks failure | Added `warnings=1` metric to `stage_complete` in `tag_page_sections` exception handler |
| M2 | MEDIUM | Dedup progress logged under STORE before entry | Moved `stage_enter(STORE)` to `deduplicate_records`, changed save to `stage_progress` |
| M3 | MEDIUM | Tests don't verify log format | Added 6 `TestStructuredLogFormat` tests using loguru sink capture |
| L1 | LOW | `now_iso()` returns str for datetime fields | Added `now_utc()` returning `datetime`, updated `pipeline_logger.py` to use it |

**Post-fix test results**: 36/36 observability tests pass, 849/853 total pass (4 pre-existing failures unrelated to E1-S21). Pydantic serialization warnings for datetime fields eliminated.

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-10 | Implemented E1-S21: Pipeline observability with structured logging | Provide real-time extraction progress visibility in API/worker terminals |
| 2026-02-10 | Code review fixes: 7 issues (3H, 3M, 1L) all resolved | Adversarial review found ORCHESTRATOR gap, model ID tracking, prompt template logging, test coverage |
