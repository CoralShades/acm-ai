# Docling Document JSON Fix — Progress

## Status: COMPLETE (2026-03-14)

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Diagnosis | DONE | 3 parallel subagents traced adapter→merge→store→DB. Root cause: SurrealDB FLEXIBLE keyword. |
| 2. Root Cause Analysis | DONE | TYPE option<object> without FLEXIBLE silently strips nested arrays. Direct SurrealQL test confirmed. |
| 3. Fix Implementation | DONE | Migration 51 adds FLEXIBLE. Test file fixed to use model_dump. 3 pre-existing test failures fixed. |
| 4. Node Data Flow Verification | DONE | All nodes pass data correctly. Per-row path enters `if dj:` branch with populated data. |
| 5. E2E Verification | DONE | 33/31 records extracted (2 extra from headers). All 2167 tests pass. Lint clean. |

## Key Metrics

| Metric | Before | After |
|--------|--------|-------|
| docling_document_json | `{}` (empty) | Populated (18-191 cells per table) |
| Extraction path | Bulk fallback | Per-row (confirmed via row_index markers) |
| Records extracted | 29 | 33 |
| Ground truth | 31 | 31 |
| Test failures | 3 pre-existing | 0 |
| Total tests passing | ~931 | 2167 |
