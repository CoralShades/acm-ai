# Story E19-S1: Migration 32 — Review Status + Clean Slate

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Must implement FIRST in E19**

---

## User Story

**As a** development team member performing the E19 sprint,
**I want to** add `review_status` to the `source` table and delete all existing `acm_record` rows,
**So that** all subsequent E19 stories operate on a clean database state with the new review workflow.

---

## Background

The new post-extraction review wizard requires tracking where each job (source) is in the review flow. Currently `source` has no such field. Additionally, all existing `acm_record` rows were extracted without the new review flow — they lack building mapping and schema-verified field values. Deleting them gives a clean slate; users will re-extract through the new wizard.

**⚠️ WARNING: This is a destructive migration. All `acm_record` data will be permanently deleted.** Inform users to export any needed data before applying this migration.

---

## Acceptance Criteria

### Database Changes
- [x] New field `review_status` added to `source` table with type `option<string>` and default `'pending_review'`
- [x] Migration sets all existing `source` records to `review_status = 'pending_review'`
- [x] All existing `acm_record` rows deleted via migration
- [x] Migration is idempotent (safe to re-run)
- [x] Migration registered in `AsyncMigrationManager` with correct version number (032)

### Review Status Values
- [x] Allowed values documented in migration file comments: `'extracting' | 'pending_review' | 'building_review' | 'acm_review' | 'published'`
- [x] Index created on `source.review_status` for efficient status-filtered queries

### Validation
- [x] After migration: `SELECT count() FROM acm_record GROUP ALL` returns 0
- [x] After migration: all `source` records have `review_status = 'pending_review'`
- [x] `uv run ruff check .` passes
- [x] `uv run pytest tests/` passes (no new test failures)

---

## Technical Notes

### Migration File
Create `migrations/032_review_status.surql`:
```surql
-- Migration 032: Add review_status to source, clean acm_record slate
-- ⚠️ DESTRUCTIVE: deletes all acm_record rows

-- Add review_status field
DEFINE FIELD review_status ON TABLE source TYPE option<string> DEFAULT 'pending_review';

-- Add index for status-filtered queries
DEFINE INDEX idx_source_review_status ON source FIELDS review_status;

-- Set all existing sources to pending_review
UPDATE source SET review_status = 'pending_review';

-- Delete all existing ACM records (clean slate for new review flow)
DELETE acm_record;
```

### Migration Registration
In `open_notebook/database/migrations.py` (or equivalent AsyncMigrationManager file):
Add migration 032 to both `up_migrations` and `down_migrations` lists. Follow the existing pattern from migrations 014-031.

### Pydantic Model Update
Update `Source` domain model (`open_notebook/domain/notebook.py` or similar) to include:
```python
review_status: Optional[str] = "pending_review"
```

### API Model Update
Update `SourceResponse` and `SourceCreate` schemas in `api/routers/` to include `review_status` field.

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `migrations/032_review_status.surql` | **New** — migration SQL |
| `open_notebook/database/migrations.py` | Modified — register migration 032 |
| `open_notebook/domain/notebook.py` | Modified — add review_status to Source model |
| `api/routers/sources.py` (or similar) | Modified — expose review_status in API responses |

---

## Dev Notes

No API cost risk — this story has no LLM calls.

Downstream impact: After this migration, users cannot see any ACM records in the register. This is expected — records must be re-extracted through the new review wizard (E19-S4 through E19-S6). Do not implement E19-S1 in isolation on production without having E19-S2 through E19-S7 ready to deploy.

---

## Estimated Effort

S (Small) — Standard migration + Pydantic model update. No frontend changes.

---

**Story Status:** ✅ DONE

---

## Dev Agent Record

**Implemented:** 2026-02-24
**Files changed:**
- `migrations/32.surrealql` (new — adds review_status field, clears acm_record)
- `migrations/32_down.surrealql` (new — rollback)
- `open_notebook/database/async_migrate.py` (registered migrations 28–32)
- `open_notebook/domain/notebook.py` (added review_status to Source model)
- `api/models.py` (added review_status to SourceResponse, SourceListResponse, SourceUpdate)
- `api/routers/sources.py` (PUT endpoint passes review_status through to DB)
- `tests/test_migration_32.py` (new — 16 unit tests)

**Tests added:** `tests/test_migration_32.py` (16 tests, all passing)
**Verification:** ruff ✓ | pytest 979 passed ✓ (excluding pre-existing live-DB tests)
