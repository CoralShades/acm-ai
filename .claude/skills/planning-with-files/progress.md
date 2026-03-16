# Session Progress (2026-03-07)

## Reboot Check
1. **Last milestone**: S7 committed (d4d6bae4) and pushed to origin/ACMV3. SF normalization node + BAR removal complete.
2. **Active task**: Two pending user requests — (1) Observability stack validation, (2) Frontend SSE/AG-UI verification.
3. **Blockers**: None for pending tasks. E31-S3 still the V3 critical path blocker.
4. **Last modified**: 33 files in S7 commit — key new files: `sf_normalizer.py`, `test_sf_normalizer.py`, `migrations/46.surrealql`. Key deletions: 14 BAR template files.
5. **Next action**: Spawn subagents for observability validation (Task 1) and frontend SSE verification (Task 2). Use Context7 for LangChain/Pydantic docs. Use /planning-with-files to manage context.

## S7 Session Summary (2026-03-07)

### What was done
- **Part A**: Created `sf_normalizer.py` with `normalize_extraction_record()` and batch wrapper. Added `normalize_to_sf_node` to graph between extract_items/orchestrate and validate. Both extraction paths now converge on SF normalization before validation. 22 tests pass.
- **Part C**: Deleted 14 BAR template files (5 backend, 9 frontend). Removed router from main.py, models from models.py, 3 field mapping endpoints from acm.py router. Replaced async `_get_export_mapping()` with sync `_get_export_columns()`. Added migration 46 to drop bar_template/field_mapping tables. Frontend build clean.
- **Part B**: Renamed `_BAR_TO_SF_VALUE` → `_VALUE_ALIASES`, `_BAR_ONLY_VALUES` → `_LEGACY_VALUES`. Updated docstrings/comments in enums.py, taxonomy.py, sf_picklist_validator.py, acm_validator.py, acm.py, acm_schemas.py. Renamed test file. Updated test imports.

### Key decisions
- Used `model_construct()` in tests to bypass Pydantic validators that pre-normalize values during construction
- Kept migration files 23/26 intact (existing DBs already ran them); added new migration 46 for table drops
- `_get_export_columns()` is now sync (no DB lookup needed) — simplifies CSV/Excel export
- `@/lib/utils/acm-field-mapping` is NOT part of the BAR system (it's the SF API→record key mapper) — left untouched

### Test results
- 378 relevant tests pass (22 new + 356 existing)
- 5 pre-existing failures unrelated to S7 (broadmeadows e2e, pipeline state flow, prompt render, cover page, protocol check)
- Frontend build passes, ruff lint clean on all modified files

## Pending User Requests (carry forward)
1. Observability stack validation — subagents with Context7, LangChain/Pydantic skills, E2E testing
2. Frontend SSE/AG-UI verification — check streaming endpoints, processing logs after S7 changes
