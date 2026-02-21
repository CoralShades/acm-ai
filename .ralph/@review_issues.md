# Review Issues — Sprint Batch (13 Stories)

**Reviewer**: Adversarial Code Review
**Date**: 2026-02-22
**Scope**: E2-S8, E10-S1, E16-S3, E2-S11, E1-S23, E9-S3, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2

---

## ~~Issue 1: BAR Template Upload — No File Size Limit (DoS Vector)~~ FIXED
- Added 10 MB file size check before processing in `bar_templates.py:86`

## ~~Issue 2: BAR Template Upload — Unbounded openpyxl Parsing~~ ACCEPTED
- Acceptable risk for internal tool; covered by Issue 1 file size guard

## ~~Issue 3: Graph Backfill — Not Idempotent (CREATE Not UPSERT)~~ FIXED
- Replaced all `CREATE` with `UPSERT` in `graph_backfill.py`

## ~~Issue 4: Graph Backfill — Duplicate Relations on Re-run~~ FIXED
- Added deterministic relation IDs to all `RELATE` → `UPSERT` in `graph_backfill.py`

## ~~Issue 5: Extraction Settings — No Validation of extraction_method Value~~ FIXED
- Changed `extraction_method` from `str` to `Literal["mineru", "docling", "hybrid"]` in `settings.py`

## ~~Issue 6: Field Mapping PUT Endpoint — Accepts Raw dict (No Validation)~~ FIXED
- Created `FieldMappingUpdateRequest` Pydantic model in `api/models.py`
- Updated endpoint to use typed request model

## ~~Issue 7: Extraction Monitor — total Count is Items Length, Not True Total~~ FIXED
- Added separate COUNT query in `extraction_events.py:list_extraction_progress`

## ~~Issue 8: E2-S11 — Quantity Validator Missing from API Models~~ N/A
- `quantity` field is not present in `ACMRecordCreateRequest` or `ACMRecordUpdateRequest`
- Only exists in response/extraction models — no API input path to validate

## ~~Issue 9: Missing Tests — 8 of 13 Stories Have No Unit Tests~~ DEFERRED
- Out of scope for fix phase — tracked separately for test coverage sprint

## ~~Issue 10: E2-S11 — Empty String Bypasses Validators~~ FIXED
- Changed `if not v` to `if v is None` in all API model validators

## ~~Issue 11: CSV Export — Header Injection via Field Mapping Names~~ FIXED
- Added `_sanitize_csv_value()` to prefix formula-starting values with `'` in `acm.py`

## ~~Issue 12: datetime.utcnow() Deprecation~~ FIXED
- Replaced `datetime.utcnow` with `datetime.now(tz=UTC)` in `bar_template.py`
