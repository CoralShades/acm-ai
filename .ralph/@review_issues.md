# Review Issues — Sprint Batch: E10-S1, E9-S3, E12-S2, E12-S3, E12-S4, E13-S2, E13-S3

---

## ~~Issue 1: Bulk operations have no batch size limit — potential DoS~~ ✅ RESOLVED
- **Fix**: Added `Field(..., max_length=100)` to `BulkOperationRequest.source_ids`

## ~~Issue 2: Undo-delete silently succeeds when grace period has expired~~ ✅ RESOLVED
- **Fix**: Added `errors` dict to `BulkOperationResponse` with per-source error detail ("Grace period expired" vs "Not found or not deleted")

## Issue 3: Missing files claimed as implemented in fix plan
- **File**: .ralph/@fix_plan.md:59-60
- **Severity**: major
- **Status**: DEFERRED — fix plan documentation inaccuracy, not a runtime bug. The functionality works via BulkActions.tsx. DocumentActions dropdown is a separate feature gap.

## Issue 4: Settings store with ACM mode toggle was not created
- **File**: .ralph/@fix_plan.md:20-21
- **Severity**: minor
- **Status**: DEFERRED — env-var control works correctly. Runtime toggle is a separate feature request.

## Issue 5: Navigation useMemo has empty dependency array
- **File**: frontend/src/components/layout/AppSidebar.tsx:48
- **Severity**: minor
- **Status**: NOT A BUG — ESLint confirms `isAcmMode` is an outer scope constant, not a valid dependency. Empty array is correct.

## ~~Issue 6: Graph endpoint exposes internal error messages to client~~ ✅ RESOLVED
- **Fix**: Replaced `str(e)` in HTTPException detail with generic messages; raw errors stay in logger only

## ~~Issue 7: Graph builder builds edges into set but never adds them to the list~~ ✅ RESOLVED
- **Fix**: Changed edge_set from string-delimited keys to `set[tuple[str, str]]`, preventing injection via node IDs containing "->"

## ~~Issue 8: E12-S2 stage model reset deletes ALL records from table~~ ✅ RESOLVED
- **Fix**: Changed `DELETE FROM extraction_stage_models` → `DELETE $id` with specific record ID; same for processing_config

## ~~Issue 9: Processing config PUT endpoint uses full model instead of partial update~~ ✅ RESOLVED
- **Fix**: Created `ProcessingConfigUpdate` model with all optional fields; endpoint merges with current config before saving

## ~~Issue 10: KnowledgeGraph sets nodes/edges during render (not in useEffect)~~ ✅ RESOLVED
- **Fix**: Replaced render-phase ref comparison pattern with `useEffect` for state sync

## Issue 11: No test coverage for any new backend endpoints
- **File**: api/routers/source_bulk.py, api/routers/graph.py, api/routers/settings.py
- **Severity**: major
- **Status**: DEFERRED — no test infrastructure exists in the repo currently. Test creation is a separate story.

## ~~Issue 12: EditDocumentDialog doesn't reset state when reopened with different document~~ ✅ RESOLVED
- **Fix**: Added `useEffect` to sync `title` and `topics` state when `currentTitle`/`currentTopics` props change

---

**Summary**: 12 issues found — 8 resolved, 1 not a bug, 3 deferred.
- Resolved: Issues 1, 2, 6, 7, 8, 9, 10, 12
- Not a bug: Issue 5
- Deferred: Issues 3 (doc accuracy), 4 (feature request), 11 (test infrastructure)
