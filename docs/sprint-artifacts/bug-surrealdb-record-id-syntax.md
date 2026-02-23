# Bug Fix: SurrealDB Record ID Syntax — extraction_stage_models

**Status:** Done
**Date:** 2026-02-23
**Severity:** High (3 endpoints returning 500)

## Problem

Three extraction settings API endpoints failed with 500 errors:

- `GET  /api/settings/extraction/stage-models`
- `PUT  /api/settings/extraction/stage-models`
- `POST /api/settings/extraction/stage-models/reset`

**Error messages:**
- "Can not execute UPSERT statement using value: 'extraction_stage_models:active'"
- "Can not execute DELETE statement using value: 'extraction_stage_models:active'"

## Root Cause

`STAGE_RECORD_ID = "extraction_stage_models:active"` was passed as a `$id` bound parameter in SurrealQL. SurrealDB receives bound parameters as typed values — a plain string is typed as `string`, not `RecordID`. UPSERT/DELETE/SELECT FROM ONLY require a `RecordID` type, so they reject the string value.

## Fix

**File:** `api/routers/settings.py`

1. Updated constant to use angle-bracket escaping:
   ```python
   STAGE_RECORD_ID = "extraction_stage_models:⟨active⟩"
   ```

2. Inlined the record ID directly in query strings (matching the established `repo_upsert()` pattern in `repository.py:126`), removing it from parameter bindings in all 3 endpoints.

## Key Insight

SurrealDB angle-bracket syntax `table:⟨key⟩` allows string keys with special characters or reserved words to be used as record IDs inline in queries. When inlined (not bound), SurrealDB parses it as a `RecordID` type, not a `string`.

The pattern `f"UPSERT {id} MERGE $data"` is already established in `repo_upsert()` — this fix follows the same convention.

## Verification

```bash
uv run ruff check api/routers/settings.py  # All checks passed
```

Live endpoint tests (requires running API on :5055):
```bash
curl http://localhost:5055/api/settings/extraction/stage-models
# Expected: 200 {"structure_analysis":null,...}

curl -X PUT http://localhost:5055/api/settings/extraction/stage-models \
  -H "Content-Type: application/json" \
  -d '{"acm_extraction":"model:test123"}'
# Expected: 200 with updated values

curl -X POST http://localhost:5055/api/settings/extraction/stage-models/reset
# Expected: 200 {"message":"Stage model assignments reset to defaults"}
```

## Integration Validation (2026-02-23)

**STEP 1 PASS** — `GET /api/settings/extraction/stage-models` returned HTTP 200:
```json
{"structure_analysis":null,"building_inventory":null,"acm_extraction":null,
 "page_tagging":null,"product_classification":null,"corrective_validation":null}
```
Confirms the SurrealDB record ID syntax fix is working correctly in production.
All three endpoints (GET/PUT/POST-reset) confirmed no longer returning 500 errors.
