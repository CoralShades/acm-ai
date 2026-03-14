# Session: Debug ACM Extraction Pipeline — Trace Analysis, Prompt Overhaul, and Persistence Fixes

## Skills to Load

/systematic-debugging — structured diagnosis before proposing fixes
/acm-observability — query Langfuse/LangSmith traces, inspect graph state, debug Pydantic failures
/planning-with-files — persistent markdown plan for session continuity
/verification-before-completion — verify fixes before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Langfuse running: `curl http://localhost:3000` (self-hosted, traces available)
- LangSmith accessible: traces at smith.langchain.com
- Ollama running: `curl http://localhost:11434/api/tags` (check which models are loaded)
- Branch: ACMV3
- Ground truth file exists: `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json`
- PDF exists: `D:/ailocal/acm-ai/docs/samplePDF/Clutch_Broadmeadows.pdf`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| ExtractionState | LangGraph TypedDict carrying all data between pipeline nodes: source metadata, docling tables, building cache, extracted records, validation flags. |
| Building__c | Salesforce object for a physical building. The pipeline produces one `BuildingRecord` per building. |
| Item__c | Salesforce object for an individual ACM sample. Maps to `ACMRecord` / `ACMExtractionRecord`. |
| Broadmeadows | Ground truth benchmark: 1 building, 31 records, consultant "Prensa Pty Ltd". Expected extraction target. |
| Per-row extraction | v3.5 mode: one LLM call per table row via `row_extractor.py`. Activated by `ACM_ITEM_EXTRACTION_MODE=per_row`. |
| Bulk extraction | Legacy mode: one LLM call per building with all items at once. Activated by `ACM_ITEM_EXTRACTION_MODE=bulk`. |
| Docling tables | Structured table objects from Docling's `DoclingDocument` parser stored in `acm_table_section`; primary extraction input. |
| PipelineLogger | Per-run logger emitting structured events to `extraction_progress` table. Constructor: `(source_id, total_pages, command_id)`. |
| ObjectModel.save() | Returns `None` — mutates `self.id` in place. NEVER check return value. Check `self.id` after save. |
| Correction loop | Graph cycle: `validate_records_strict` -> `correct_records` -> back to validate. Max attempts configurable. |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |
| Subagent | Claude Code session spawned via Task tool for parallel work. Use `model: "opus"` for all subagents in this session. |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep. |

---

## Current State

- Branch: ACMV3 (last commit: `feat(frontend): complete frontend audit`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Pipeline audit completed: 42 SurrealDB tables cataloged, 11 orphaned tables identified
- Knowledge graph tables removed (migration 50)
- Per-row extraction pipeline (v3.5) is the current default path
- Broadmeadows PDF should yield: 1 building ("Broadmeadows Police Station"), 31 Item__c records

### Trace IDs for This Debug Session

**Langfuse:**
- `8270cdb0a7abef32ee4c445541d3b80a`
- `38c0555b95e99d893b7a973dda5cdf88`

**LangSmith / LangGraph:**
- `fdfc9f9d-51b1-4f9b-94b8-cf723eb46f70`
- `6a010e5d-f7eb-4c31-99e0-7475ba51581c`

### Known Issues

1. **Record count**: Pipeline produces fewer than expected 30-31 records from Broadmeadows PDF
2. **Field accuracy**: Extracted fields are wrong or empty for key Item__c fields
3. **Persistence**: Records may not be saved to SurrealDB correctly
4. **Prompt quality**: Node prompts are overly descriptive and produce unpredictable LLM output

---

## Key Files

Files this session will read and modify.

**Read (trace analysis):**
- `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json` — ground truth (31 records)
- `D:/ailocal/acm-ai/docs/samplePDF/Clutch_Broadmeadows.pdf` — source PDF

**Read (pipeline understanding):**
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — main LangGraph graph (all 11 nodes)
- `D:/ailocal/acm-ai/commands/source_commands.py` — pre-graph extraction orchestration
- `D:/ailocal/acm-ai/open_notebook/extractors/orchestrator.py` — extraction strategy
- `D:/ailocal/acm-ai/open_notebook/extractors/row_extractor.py` — per-row item extraction
- `D:/ailocal/acm-ai/open_notebook/extractors/row_segmenter.py` — table row segmentation
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — building inventory extraction
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_extractor.py` — metadata extraction
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/docling_adapter.py` — Docling table extraction
- `D:/ailocal/acm-ai/open_notebook/domain/acm.py` — ACMRecord, BuildingRecord models
- `D:/ailocal/acm-ai/open_notebook/domain/acm_row_schemas.py` — ACMItemRow schema
- `D:/ailocal/acm-ai/open_notebook/domain/acm_row_mappers.py` — ACMItemRow -> ACMExtractionRecord
- `D:/ailocal/acm-ai/open_notebook/graphs/utils.py` — Ollama settings, model resolution

**Read (observability config):**
- `D:/ailocal/acm-ai/open_notebook/observability/langfuse_config.py` — Langfuse wiring
- `D:/ailocal/acm-ai/open_notebook/observability/logfire_config.py` — Logfire/Pydantic trace config

**Modify (prompts — verify with user before applying):**
- `D:/ailocal/acm-ai/prompts/acm/row_extraction.jinja` — per-row item extraction prompt
- `D:/ailocal/acm-ai/prompts/acm/row_split.jinja` — row segmentation prompt
- `D:/ailocal/acm-ai/prompts/acm/metadata_extraction.jinja` — metadata prompt (if exists)
- `D:/ailocal/acm-ai/prompts/acm/building_inventory.jinja` — building inventory prompt (if exists)
- `D:/ailocal/acm-ai/prompts/acm/` — all other ACM prompt templates

**Modify (Python code — verify with user before applying):**
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — node prompt construction
- `D:/ailocal/acm-ai/open_notebook/extractors/row_extractor.py` — per-row extraction logic
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_extractor.py` — metadata extraction logic
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — building inventory logic

**Write (output):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/findings.md` — debug findings
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/task_plan.md` — task plan
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/progress.md` — progress tracker

---

## Plan

Read `docs/sprint-artifacts/pipeline-debug/task_plan.md` before starting. Update it as you work.

### Task Plan Reference

- task_plan.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/findings.md`
- progress.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pipeline-debug/progress.md`

### Execution Strategy

**Phase 1 — Trace Analysis (diagnose before fixing)**

Step 1: Query Langfuse traces for both trace IDs. For each trace:
- Extract the model used (Ollama? Cloud? Which model name?)
- Extract extraction mode (per_row vs bulk)
- Count LLM calls per node
- Identify token usage and truncation warnings
- Extract input/output for each graph node
- Note any errors, exceptions, or fallback triggers

Step 2: Query LangSmith for both run IDs. For each run:
- Inspect the graph execution flow (which nodes ran, which were skipped)
- Extract the ExtractionState at each node boundary
- Identify where records are lost (state has N records at node X, fewer at node Y)
- Check if `save_records` node was reached and what it persisted

Step 3: Compare extraction output against Broadmeadows ground truth:
- How many buildings detected? (expected: 1)
- How many records extracted? (expected: 31)
- Which records are missing?
- Which fields are wrong vs ground truth?

**Phase 2 — Root Cause Analysis**

Step 4: For each node that produced incorrect output:
- Read the current Jinja2 prompt template
- Read the Python code that constructs the prompt
- Identify: Is the issue the prompt? The input data? The model config? The output parsing?
- Document specific failure modes (e.g., "model returned conversational text instead of JSON")

Step 5: Check persistence path:
- Verify `ObjectModel.save()` is called correctly (check for return-value anti-pattern)
- Verify SurrealDB queries in `save_records` node
- Check if building_record IDs are generated correctly
- Check if acm_record foreign keys (source_id, building_record_id) are set

**Phase 3 — Prompt Overhaul (Ollama-first)**

Step 6: For EACH node prompt, rewrite optimized for Ollama:
- Shorter, more structured prompts (Ollama models struggle with long instructions)
- Explicit JSON schema in prompt (not just "return JSON")
- Few-shot examples where beneficial
- Clear field-by-field extraction instructions
- Remove ambiguous language and redundant descriptions
- Add `format="json"` to all ChatOllama calls

**CRITICAL: Present each rewritten prompt to the user for approval before applying.**

Step 7: Fix Python code issues found in Phase 2:
- Fix any `save()` return-value anti-patterns
- Fix any SurrealDB persistence bugs
- Fix any model config issues (num_ctx, format, etc.)

**Phase 4 — Verification**

Step 8: Re-run the Broadmeadows extraction with fixed prompts
Step 9: Compare output against ground truth — must hit 30-31 records
Step 10: Verify records are persisted in SurrealDB

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent research work items in parallel.
**All subagents MUST use `model: "opus"`.**

### Phase 1 Subagents (launch in parallel)

**Subagent 1: langfuse-trace-analyst**
- Model: opus
- Task: Query Langfuse API at localhost:3000 for trace IDs `8270cdb0a7abef32ee4c445541d3b80a` and `38c0555b95e99d893b7a973dda5cdf88`. Extract: model name, extraction mode, per-node LLM inputs/outputs, token counts, errors, latency. Return structured findings.
- Skills: /acm-observability, /systematic-debugging

**Subagent 2: langsmith-trace-analyst**
- Model: opus
- Task: Query LangSmith API for run IDs `fdfc9f9d-51b1-4f9b-94b8-cf723eb46f70` and `6a010e5d-f7eb-4c31-99e0-7475ba51581c`. Extract: graph execution flow, ExtractionState at each node boundary, record count progression, which nodes were skipped, errors. Return structured findings.
- Skills: /acm-observability, /systematic-debugging

**Subagent 3: prompt-auditor**
- Model: opus
- Task: Read ALL Jinja2 templates in `prompts/acm/` and ALL prompt construction code in `acm_extraction.py`, `row_extractor.py`, `metadata_extractor.py`, `building_inventory.py`. For each prompt: assess clarity, JSON compliance, Ollama suitability, length, and identify specific issues. Return structured audit.
- Skills: /systematic-debugging

**Subagent 4: persistence-auditor**
- Model: opus
- Task: Read `save_records` node in `acm_extraction.py`, `ObjectModel.save()` in `domain/base.py`, building ID generation, and all SurrealDB write paths. Identify any persistence bugs (return-value checks on save(), FK resolution, race conditions). Cross-reference with known bugs in CLAUDE.md. Return structured findings.
- Skills: /systematic-debugging

### Phase 2 (after Phase 1 completes)

Synthesize all 4 subagent outputs. Identify root causes. Present to user with:
- Ranked list of issues by impact
- Proposed prompt rewrites for each node
- Proposed code fixes

Wait for user approval before applying any changes.

### Phase 3 (after user approval)

Apply approved changes. Run verification.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "langgraph" -> query-docs for "StateGraph nodes edges TypedDict state"
2. resolve-library-id for "langchain" -> query-docs for "ChatOllama format json structured output"
3. resolve-library-id for "surrealdb" -> query-docs for "CREATE UPDATE UPSERT record type binding"
4. resolve-library-id for "langfuse" -> query-docs for "trace observation API Python SDK"

---

## Verification Checklist

Run these checks before marking the session complete. All must pass.

- [ ] Langfuse traces analyzed — both trace IDs inspected, findings documented
- [ ] LangSmith runs analyzed — both run IDs inspected, findings documented
- [ ] Root causes identified — each issue has a specific diagnosis (not just "prompt is bad")
- [ ] All prompt rewrites presented to user and approved before applying
- [ ] All code fixes presented to user and approved before applying
- [ ] `uv run ruff check .` — Python lint passes (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests pass
- [ ] Re-run Broadmeadows extraction — produces 30-31 records (within 1 of ground truth)
- [ ] Records persisted in SurrealDB — `SELECT count() FROM acm_record WHERE source_id = $sid GROUP ALL` returns >= 30
- [ ] Building persisted — `SELECT * FROM building_record WHERE source_id = $sid` returns 1 record with name "Broadmeadows Police Station"
- [ ] Key fields populated — sample_no, room_name, product, location are non-empty on extracted records
- [ ] findings.md updated with complete diagnosis and resolution
- [ ] progress.md shows all steps completed

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | ~20 | graph, extractors, domain models, observability config, ground truth |
| MODIFY | ~10 | prompts/acm/*.jinja (templates), acm_extraction.py, row_extractor.py, metadata_extractor.py, building_inventory.py, utils.py |
| NEW | 3 | pipeline-debug/task_plan.md, findings.md, progress.md |
| DELETE | 0 | -- |

---

## Commit Template

When work is complete, use this commit message structure:

```
fix(extraction): overhaul pipeline prompts for Ollama accuracy — Broadmeadows 31/31 records

Rewrite all ACM node prompts (metadata, inventory, building, item extraction)
for Ollama-first JSON compliance. Fix persistence bugs in save_records path.
Validated against Broadmeadows ground truth benchmark.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

---

## Critical Rules

1. **NEVER apply prompt or code changes without presenting to user first** — show diff, explain rationale, wait for approval
2. **All subagents use `model: "opus"`** — no sonnet or haiku for this session
3. **Diagnose BEFORE fixing** — follow /systematic-debugging strictly. No guessing.
4. **Compare against ground truth** — every change must be validated against `broadmeadows.json`
5. **Ollama-first optimization** — prompts must work with 8b local models (short, structured, explicit JSON format)
6. **`ObjectModel.save()` returns None** — never check return value, check `self.id` after save
7. **Use `$CLAUDE_PROJECT_DIR`** or `D:/ailocal/acm-ai` (forward slashes) — never `/d/` or `D:\`
