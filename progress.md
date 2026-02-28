# Progress — E27-S4: Native JSON Schema Structured Outputs

## Session: 2026-02-28
### Status: PLANNING

### Reboot Check
1. **Last completed milestone**: E27-S3 (hard-lock provider routing) — committed and done
2. **Current active task**: E27-S4 planning — all mandatory files read, findings documented
3. **Blockers**: None — spike validation requires running extraction (needs services up)
4. **Files last modified**: findings.md, task_plan.md, progress.md (planning files)
5. **Next planned action**: Task 0 — create story file, then Task 1 — implement schema utilities

### Key Decisions
1. **Stage-specific injection** instead of modifying shared `_apply_openrouter_preferences()`:
   - `_inject_response_format(model, schema_dict, name)` applies ONLY to extraction calls
   - Other stages (document_structure, building_inventory, page_tagger) keep existing behavior
   - Rationale: shared function applies to ALL models; ACMExtractionResult schema would break non-extraction stages

2. **Conditional removal gate**: `_unwrap_completion_state()` is only removed IF spike confirms no wrapper (Scenario A). If wrapper persists (Scenario B), retain and document.

### Files Read (Pre-Read Complete)
- `open_notebook/graphs/utils.py` — full (549 lines)
- `open_notebook/extractors/orchestrator.py` — full (1014 lines)
- `open_notebook/extractors/document_structure.py` — full (268 lines)
- `open_notebook/extractors/building_inventory.py` — full (602 lines)
- `open_notebook/extractors/page_tagger.py` — full (478 lines)
- `open_notebook/graphs/acm_extraction.py` — lines 1-100, 1270-1350, 1430-1480
- `open_notebook/extractors/acm_schemas.py` — full (504 lines)
- `api/model_provisioning.py` — full (448 lines)
- `docs/sprint-artifacts/sprint-status.yaml` — epic-27 section
- `tests/test_completion_state_unwrap.py` — full (105 lines)
- `tests/test_openrouter_provider_routing.py` — full (367 lines)
