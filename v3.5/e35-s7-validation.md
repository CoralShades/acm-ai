# E35-S7 Validation Report: normalize_to_sf + BAR Removal

**Date:** 2026-03-07
**Validator:** Claude Code (Opus 4.6)
**Branch:** ACMV3

## Summary

E35-S7 added a `normalize_to_sf` graph node between `orchestrate`/`extract_items` and `validate` in the LangGraph extraction pipeline, and removed the entire BAR template system (14 files deleted). This validation confirms that these changes haven't broken frontend SSE streaming, AG-UI display, exports, or navigation.

**Overall Verdict: PASS**

## Validation Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Frontend build (`npm run build`) | PASS | All routes compiled, no missing imports |
| 2 | Backend lint (`ruff check .`) | PASS | All checks passed |
| 3 | test_orchestrator.py | PASS | 18/18 passed |
| 4 | test_sf_normalizer.py | PASS | 22/22 passed |
| 5 | test_sf_first_validation.py | PASS | 17/17 passed, 1 skipped (fixture-dependent) |
| 6 | Stale `bar_template` refs (backend) | CLEAN | 0 matches in api/, open_notebook/, commands/ |
| 7 | Stale `field_mapping` refs (backend) | CLEAN | 0 matches (excl. migrations, local vars in acm.py) |
| 8 | Stale BAR refs (frontend) | CLEAN | 0 matches for bar-template, BARTemplate, FieldMapping |
| 9 | Stale BAR imports (frontend) | CLEAN | 0 matches for bar_templates, bar-templates, barTemplate |
| 10 | StageId enum alignment | MATCH | Backend (9 stages) = Frontend (9 stages), same order |
| 11 | normalize_to_sf in StageId | NOT present | Correct — silent node, no SSE events |
| 12 | Export endpoints | Unchanged | `_get_export_columns()` is sync, no DB reads |
| 13 | SSE endpoints | Unchanged | v3_streaming.py, agui_extraction.py — zero BAR refs |

## StageId Enum (9 stages, backend = frontend)

| # | Stage |
|---|-------|
| 1 | STRUCTURE |
| 2 | PREFLIGHT |
| 3 | ORCHESTRATOR |
| 4 | DOCLING_EXTRACTION |
| 5 | EXTRACT |
| 6 | VALIDATE |
| 7 | CORRECT |
| 8 | NO_ACCESS_RECOVERY |
| 9 | STORE |

## Test Summary

- **Total tests:** 58
- **Passed:** 57
- **Skipped:** 1 (`test_broadmeadows_sf_valid_record_count` — requires external fixture)
- **Failed:** 0
- **Duration:** 3.81s
- **Warnings:** 3 (Pydantic v2 deprecation, non-blocking)

## Critical Files Verified

| File | Role | Status |
|------|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Graph with normalize_to_sf node | Clean |
| `open_notebook/extractors/pipeline_events.py` | StageId enum (9 stages) | Clean |
| `api/routers/acm.py` | Export endpoints | Clean |
| `api/routers/v3_streaming.py` | SSE streaming | Clean |
| `api/routers/agui_extraction.py` | AG-UI SSE | Clean |
| `api/main.py` | Router registration (24 routers, no bar_templates) | Clean |
| `frontend/src/lib/types/pipeline.ts` | Frontend StageId | Matches backend |
| `frontend/src/components/acm/ExtractionProgress.tsx` | Progress UI | Clean |
| `frontend/src/components/acm/ExtractionProgressPanel.tsx` | Progress panel | Clean |
| `frontend/src/config/navigation.ts` | Nav config | Clean |
| `frontend/src/lib/hooks/useV3SSE.ts` | SSE hook | Clean |
| `frontend/src/lib/stores/streamingStore.ts` | SSE store | Clean |
| `migrations/46.surrealql` | BAR table removal | Correct |

## Notes

- `acm-field-mapping.ts` utility in frontend is preserved — it maps ACMRecord keys to display labels and is NOT part of the BAR template system
- `open_notebook/domain/acm.py` has a local variable `field_mappings` in `to_sf_dict()` — this is SF field mapping logic, NOT the deleted BAR `field_mapping` table
- Old worktrees in `.claude/worktrees/fix-a-no-access-markers/` still contain BAR code — these are isolated git worktrees and do not affect the main codebase
