# Session: Audit and fix the ACM extraction pipeline execution order, resilience, and Bug Fix 12 (N1-N9)

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/systematic-debugging — structured diagnosis before proposing fixes
/find-bugs — systematic bug discovery across pipeline
/acm-observability — Langfuse/LangSmith trace analysis reference
/langgraph-fundamentals — LangGraph graph/node/state patterns
/dogfood — E2E exploration with real extraction runs
/verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Worker running: check for `run_worker.py` process
- Branch: `git checkout ACMV3`
- Test PDF available: `docs/samplePDF/Clutch_Broadmeadows_2.pdf`
- Read audit findings: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------|
| ExtractionState | LangGraph TypedDict carrying all data between pipeline nodes (source metadata, docling tables, building cache, extracted records, validation flags) |
| Building__c | Salesforce object representing a physical building. Pipeline produces one `BuildingRecord` per building |
| Item__c | Salesforce object for individual ACM sample. Maps to `ACMExtractionRecord` |
| Pre-extraction stages | STRUCTURE, PREFLIGHT, ORCHESTRATOR — gather metadata, validate source, plan extraction strategy |
| PipelineLogger | Per-run structured logger. Constructor: `(source_id, total_pages=0, command_id=None)` |
| ExtractionProvider | Protocol class all adapters implement: `extract_tables()`, `extract_text()`, `is_available()` |
| ObjectModel.save() | Returns None, mutates self.id. NEVER check return value — check self.id after save |
| Per-row extraction | v3.5 mode: one LLM call per table row → 9 fields → deterministic post-processing |
| Correction loop | `correct_node` re-validates low-confidence records. Triggered when confidence < threshold |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name` |
| Subagent | Claude Code session spawned via Task tool for parallel work |
| Plan mode | Session starts by reading/writing `task_plan.md` to prevent scope creep |

---

## Current State

- Branch: ACMV3 (last commit: `36093f78` — test(e2e): update smoke tests for VAEA|ACM branding)
- Pipeline has broken to 0 records 3 times after code changes (Bug Fix 11, Pipeline Debug, Dogfood)
- Bug Fix 12 has 9 unresolved issues (N1-N9) + 3 LangSmith observations (L1-L3)
- Ground truth: Broadmeadows 28-31/31 (varies), Alexander 36-43/43
- Per-row extraction (v3.5) operational but fragile
- Known recurring root causes: ObjectModel.save() trap, SurrealDB record ID as model name, provider mismatch

---

## Key Files

**Read (reference):**
- `open_notebook/graphs/acm_extraction.py` — main extraction graph (9 stages)
- `open_notebook/extractors/orchestrator.py` — orchestrator node (page ranges, docling tables)
- `open_notebook/graphs/utils.py` — `_apply_ollama_extraction_settings()`, `_get_db_extraction_model()`
- `open_notebook/domain/base.py` — `ObjectModel.save()` — returns None trap
- `open_notebook/extractors/providers/base.py` — ExtractionProvider protocol
- `open_notebook/extractors/providers/docling_adapter.py` — Docling table extraction
- `open_notebook/extractors/row_extractor.py` — per-row extraction
- `open_notebook/extractors/row_segmenter.py` — row segmentation engine
- `commands/source_commands.py` — source processing entry point
- `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md` — audit findings F1-F5

**Modify (likely):**
- `open_notebook/graphs/acm_extraction.py` — defensive patterns, error handling
- `open_notebook/graphs/utils.py` — provider routing fixes
- `open_notebook/extractors/orchestrator.py` — page range and table injection fixes
- `commands/source_commands.py` — pipeline initialization hardening

**Create (likely):**
- `tests/test_pipeline_integration.py` — integration tests for full pipeline on known PDFs

---

## Plan

Read `docs/sprint-artifacts/pipeline-audit-2026-03-18/task_plan.md` before starting. Update it as you work.

### Approach

1. **Trace analysis** — Run extraction on Broadmeadows PDF, collect Langfuse traces, identify current failure points
2. **Bug Fix 12 triage** — Read N1-N9 issue docs, classify by severity, fix in priority order
3. **Defensive patterns** — Add assertions/guards for the 6 recurring root causes:
   - `ObjectModel.save()` return value → assert `self.id` after save
   - SurrealDB record ID as model name → validate before LLM call
   - Provider model mismatch → type-check provider before routing
   - `num_ctx` overwrite → respect caller's value
   - Page range overlap → use OVERLAP not CONTAINMENT
   - `asyncio.gather` race → pre-assign IDs before gather
4. **Integration test** — Create a test that runs the full pipeline on a fixture PDF and asserts record count
5. **Verify** — Run extraction, confirm ground truth match

### Task Plan Reference
- task_plan.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/task_plan.md`
- findings.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md`
- progress.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/progress.md`

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items.

Subagents:
- trace-analyst: Run extraction on Broadmeadows, collect Langfuse traces, document current failure points (use acm-observability-debugger agent)
- bug-triage: Read Bug Fix 12 N1-N9 docs, classify by severity, produce fix plan
- defensive-coder: Apply defensive patterns to the 6 recurring root causes (after trace-analyst + bug-triage complete)
- test-writer: Create integration test for full pipeline (after defensive-coder)
- verifier: Run full pipeline + test suite (after all above)

Dispatch trace-analyst and bug-triage in parallel. Sequential after that.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "langgraph" → query-docs for "node conditional edges state typing interrupt"
2. resolve-library-id for "surrealdb.py" → query-docs for "record ID binding query parameters"
3. resolve-library-id for "pydantic" → query-docs for "model_validate model_dump json mode"

---

## Verification Checklist

Run these commands in order before marking the session complete. All must pass.

- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] Run extraction on Broadmeadows PDF — verify >=28/31 records
- [ ] Bug Fix 12 N1-N9 issues: all HIGH severity fixed
- [ ] New integration test passes: `uv run pytest tests/test_pipeline_integration.py -v`

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 10 | acm_extraction.py, orchestrator.py, utils.py, base.py, providers/base.py, docling_adapter.py, row_extractor.py, row_segmenter.py, source_commands.py, findings.md |
| MODIFY | 4 | acm_extraction.py, utils.py, orchestrator.py, source_commands.py |
| NEW | 1 | test_pipeline_integration.py |

---

## Commit Template

When work is complete, use this commit message structure:

```
fix(pipeline): harden extraction pipeline execution — Bug Fix 12 N1-N9, defensive patterns, integration tests

- Fix Bug Fix 12 issues N1-N9 from extraction audit
- Add defensive patterns for 6 recurring root causes
- Add integration test for full pipeline on known PDFs
- Verify: Broadmeadows >=28/31 records

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
