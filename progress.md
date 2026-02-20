# Progress Log: Critical Bug Fixes + E2E Test

## Session: 2026-02-09

### Phase 1: Research & Diagnosis - COMPLETE
- [x] Check services running (SurrealDB, API, Frontend)
- [x] Playwright bug reproduction for Bug 1 (Source Not Found)
- [x] Playwright bug reproduction for Bug 2 (AG Grid error #200)
- [x] Code investigation for both bugs

### Phase 2: Bug Fixes - COMPLETE
- [x] Bug 1: Source Not Found - Root cause: stale API process. Killed and restarted.
- [x] Bug 2: AG Grid error #200 - Changed `enableGrouping = true` to `false` in ACMGrid.tsx
- [x] Applied Bug 2 fix to both main worktree and lane-b worktree

### Phase 3: Fix Verification - COMPLETE
- [x] Bug 1: Verified via curl (3 sources return 200) and Playwright (source detail loads)
- [x] Bug 2: Verified via Playwright (ACM tab loads, 2 records shown, no error #200)

### Phase 4: E2E PDF Extraction Test - COMPLETE
- [x] Research existing test patterns and extraction pipeline
- [x] Design E2E test architecture (4 test classes, 12 tests)
- [x] Implement tests/test_e2e_extraction.py
- [x] All 12 tests passing

### Phase 5: Final Verification - COMPLETE
- [x] Run full test suite: 812 passed, 5 failed (all 5 pre-existing)
- [x] No regressions from our changes
- [x] Pre-existing failures are from E1-S15 enum normalizer updates

## Summary of Changes

### Files Modified
1. `frontend/src/components/acm/ACMGrid.tsx` - Changed `enableGrouping = true` → `false` (line 114)
2. Same change in lane-b worktree

### Files Created
1. `tests/test_e2e_extraction.py` - 12 E2E tests for the extraction pipeline

### Test Results (12 new tests)
- TestRegexExtraction: 3 passed (baseline regex extraction)
- TestPipelineLegacyPath: 6 passed (full graph, legacy path)
- TestPipelineOrchestratorPath: 1 passed (full graph, orchestrator path)
- TestMineruToRecords: 2 passed (PDF fixture availability + regex from markdown)
