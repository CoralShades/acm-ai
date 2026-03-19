# MCS3: Format Profile Registry — Progress

## Session 1 — 2026-03-18

### Completed
- All 14 tasks complete
- Migration 54: `consultant_format_profile` table with UNIQUE index on `header_signature`
- `format_profile_repository.py`: get/save/delete/list/increment CRUD functions
- `schema_inference.py`: cache-hit/miss logic integrated (check before LLM, auto-save on miss)
- `format_profiles.py` router: GET/POST/DELETE endpoints registered under `/api/acm/format-profiles`
- 16 new tests all passing, 24 existing schema inference tests updated and passing (40 total)
- Lint clean across all files

### Files Created
- `migrations/54.surrealql` — consultant_format_profile table definition
- `migrations/54_down.surrealql` — rollback
- `open_notebook/extractors/format_profile_repository.py` — DB CRUD
- `api/routers/format_profiles.py` — FastAPI endpoints

### Files Modified
- `open_notebook/extractors/schema_inference.py` — added `_build_schema_from_profile()`, cache logic in `schema_inference_node()`
- `open_notebook/database/async_migrate.py` — registered migration 54 (up + down)
- `api/main.py` — registered `format_profiles` router
- `tests/test_schema_inference.py` — added format_profile_repository mocks to existing LLM tests
- `tests/test_format_profile_registry.py` — 16 new tests

### Key Decisions
- Cache hit threshold: confidence >= 0.8 (matches design doc HITL threshold)
- Manual profile creation sets `verified_by_user=True`, `sample_count=0`
- Auto-saved profiles set `verified_by_user=False`, `sample_count=1`
- Profile save failure is non-fatal (logged warning, extraction continues)
