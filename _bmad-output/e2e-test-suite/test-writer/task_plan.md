# Phase 2: Test Suite Development - Task Plan

**Agent:** test-writer
**Phase:** 2 of 5 (Test Specification)
**Created:** 2026-02-16
**Status:** In Progress

## Mission

Write comprehensive E2E test specifications for ACM extraction pipeline, Smart Chat interactions, and full application workflows.

## Context from Phase 1

### Infrastructure Ready
- ✅ Playwright configured at `playwright.config.ts`
- ✅ Test data: 3 SAMP PDFs in `tests/e2e/fixtures/samps/`
- ✅ Expected results: `broadmeadows-expected-results.json` (31 records)
- ✅ Helper utilities: `tests/e2e/helpers/` (27 functions)
  - acm-helpers.ts: Upload, wait, validate, export
  - chat-helpers.ts: Send messages, verify responses, tool calls
  - screenshot-helpers.ts: Capture evidence

### Current Metrics
- Baseline: 26% extraction accuracy (8/31 records)
- Target: 80%+ extraction accuracy (25/31 records)
- Gaps: Negative detection, compliance fields, sample_no, quantity

## Task Breakdown

### Task 1: Create Planning Files ✅
- [x] Create `_bmad-output/e2e-test-suite/test-writer/` directory
- [x] Write task_plan.md (this file)
- [x] Write progress.md
- [x] Write findings.md

### Task 2: Write ACM Extraction Pipeline Tests
**File:** `tests/e2e/acm-extraction.spec.ts`

**Test Scenarios:**
1. **Happy Path** - Broadmeadows SAMP with 80%+ accuracy
   - Upload SAMP using uploadSAMP()
   - Wait for extraction using waitForExtraction()
   - Validate grid using validateACMGrid()
   - Compare against broadmeadows-expected-results.json
   - Assert: >= 25/31 records (80%)

2. **Negative Detection** - Correctly identify negative ACM results
   - Upload SAMP with negative results
   - Verify negative detection in grid
   - Assert: negative records captured

3. **Merged Cells** - Handle merged cells in SAMP tables
   - Upload SAMP 1124 or 3980 (merged cells)
   - Verify cell parsing accuracy

4. **Multi-page Tables** - Stitch multi-page ACM tables
   - Upload multi-page SAMP
   - Verify page stitching

5. **Field Completeness** - Extract all compliance fields
   - Verify: sample_no, quantity, labelled, floor_level, result
   - Current gap: 0% on compliance fields

6. **Export Validation** - Export ACM records
   - Export as CSV
   - Export as Excel
   - Verify download

### Task 3: Write Smart Chat Tests
**File:** `tests/e2e/smart-chat.spec.ts`

**Test Scenarios:**
1. **Basic Messaging** - Send message and receive response
2. **ACM Tool Calls** - Execute ACM-specific tool calls
3. **Mode Switching** - Switch between chat modes
4. **Error Handling** - Handle chat errors gracefully
5. **Response Streaming** - Stream responses progressively
6. **ACM Stats Query** - Test ACM statistics query
7. **ACM Search Query** - Test ACM search functionality
8. **Context Switch** - Test chat → grid navigation
9. **Clear History** - Clear chat history

### Task 4: Write Full Workflow Tests
**File:** `tests/e2e/user-journeys.spec.ts`

**Test Scenarios:**
1. **Journey 1: New User** - Create notebook and upload SAMP
   - Create notebook
   - Upload SAMP via wizard
   - View extracted records
   - Ask chat question
   - Export to Excel

2. **Journey 2: Power User** - Compare multiple SAMPs
   - Upload 3 SAMP documents
   - View extractions in grid
   - Use filtering and sorting
   - Compare compliance
   - Export consolidated report

3. **Journey 3: QA Analyst** - Validate extraction quality
   - Upload SAMP
   - Review extraction accuracy
   - Identify negative results
   - Verify compliance fields
   - Flag extraction issues

### Task 5: Documentation
- Document test strategy in findings.md
- Track progress in progress.md
- Note any blockers or questions

## Success Criteria

✅ Planning files created (`_bmad-output/e2e-test-suite/test-writer/`)
⬜ `acm-extraction.spec.ts` written with 5+ test scenarios
⬜ `smart-chat.spec.ts` written with 5+ test scenarios
⬜ `user-journeys.spec.ts` written with 3 critical journeys
⬜ All tests use helper utilities from Phase 1
⬜ Tests are executable (no syntax errors)
⬜ Documentation complete

## Constraints

- **Use existing helpers** - Don't recreate utilities
- **Follow patterns** - Use smoke.spec.ts, notebooks.spec.ts as templates
- **Use fixtures** - From `tests/e2e/fixtures/samps/`
- **Focus on accuracy** - Primary goal is extraction validation
- **Don't execute** - That's Phase 3
- **Make deterministic** - Avoid flaky timing

## Timeline

- **Task 1:** Planning Files - 15 minutes ✅
- **Task 2:** ACM Extraction Tests - 45 minutes
- **Task 3:** Smart Chat Tests - 30 minutes
- **Task 4:** User Journeys Tests - 30 minutes
- **Task 5:** Documentation - 15 minutes

**Total Estimated Time:** 2 hours 15 minutes

## Next Steps

1. ✅ Create planning files
2. ⬜ Write acm-extraction.spec.ts
3. ⬜ Write smart-chat.spec.ts
4. ⬜ Write user-journeys.spec.ts
5. ⬜ Update documentation
6. ⬜ Send completion message to team-lead
