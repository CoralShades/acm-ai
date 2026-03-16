# Bug: _get_db_extraction_model() Returns SurrealDB Record ID as Model Name

**Status**: RESOLVED (2026-03-12)
**Severity**: P0 (blocks ALL extraction)
**Found in**: Bug Fix 11 Phase 8

## Symptom

After restarting services with Phase 1-7 fixes, extraction produces 0 records:
```
Primary extraction model: ollama/model:znay2wr8u9q39lxj2q37
model "model:znay2wr8u9q39lxj2q37" not found, try pulling it first (status code: 404)
```

## Root Cause

`default_extraction_model` in `open_notebook:default_models` stores a SurrealDB record ID (e.g. `model:znay2wr8u9q39lxj2q37`) because `find_or_create_model()` in `api/model_provisioning.py:213` returns `existing[0].get("id")`.

`_get_db_extraction_model()` in `utils.py` read this value and returned it as-is. The `"/"` check (for stripping provider prefix) never matched because record IDs use `:` not `/`.

This value was passed to Ollama as the model name → 404 on every LLM call → metadata fails → heuristic fallback has no data → 0 buildings → 0 records.

## Cascade Effect

| Stage | Error | Impact |
|-------|-------|--------|
| Metadata extraction | 404 → heuristic fallback | `consultant=Unknown, buildings=0` |
| Building inventory | 404 → heuristic fallback | 0 buildings (no `document_structure` data) |
| Building extraction | No inventory → skip | 0 buildings saved |
| Item extraction | No inventory → skip | 0 records |

## Fix

`_get_db_extraction_model()` now detects `model:xxx` record IDs and resolves them via direct record reference:
```sql
SELECT name FROM model:{record_part};
```

**Note**: The initial fix used `SELECT name FROM model WHERE id = $mid` with param binding, but SurrealDB doesn't auto-cast string params to record IDs. The final fix uses direct record reference with alphanumeric sanitization to prevent injection.

**File**: `open_notebook/graphs/utils.py:860-897`

## Related Fixes (same session)

- `docling_adapter.py:151` — `model_dump(mode="json")` for serializable output
- `utils.py:281-285` — `num_ctx` overwrite prevention
- `row_extractor.py:149` — loguru builtin shadow fix
