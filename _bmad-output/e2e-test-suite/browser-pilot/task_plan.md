# Browser Pilot - Task Plan
## Phase 3: Test Execution & Documentation

**Agent**: Browser Pilot
**Phase**: 3 of 5
**Started**: 2026-02-16 09:31 GMT+11

## Mission
Execute Playwright E2E tests, capture evidence screenshots, and document execution results for the ACM-AI test suite.

## Test Suite Inventory

**Primary Test Files** (from Phase 2):
- `acm-extraction.spec.ts` (12KB, ~8 scenarios)
- `smart-chat.spec.ts` (11KB, ~11 scenarios)
- `user-journeys.spec.ts` (12KB, ~5 workflows)

**Legacy Test Files** (pre-existing):
- `notebooks.spec.ts` (2KB)
- `smoke.spec.ts` (1.3KB)
- `sources.spec.ts` (1.7KB)

**Supporting Infrastructure**:
- `tests/e2e/helpers/` - Test helper utilities
- `tests/e2e/fixtures/` - Test fixtures and data
- `playwright.config.ts` - Playwright configuration

**Total Expected Scenarios**: ~24 (from Phase 2 specs)

## Tasks

### Task 1: Environment Verification ✓
- [x] Verify planning directory created
- [x] Verify screenshot directory created
- [x] Locate test files
- [ ] Check service status (Frontend:8502, Backend:5055, SurrealDB:8000)
- [ ] Verify Playwright installation

### Task 2: Test Execution
- [ ] Run full E2E test suite with Playwright
- [ ] Execute with `--headed` for visibility
- [ ] Capture screenshots at critical steps
- [ ] Record pass/fail status for each test
- [ ] Note execution times
- [ ] Capture error messages for failures

### Task 3: Evidence Collection
- [ ] Save screenshots to `_bmad-output/e2e-test-suite/screenshots/`
- [ ] Use naming convention: `{test-name}-{step}-{timestamp}.png`
- [ ] Copy Playwright HTML report to `_bmad-output/e2e-test-suite/playwright-report/`
- [ ] Document evidence paths in findings

### Task 4: Results Documentation
- [ ] Create test execution summary (total/passed/failed/skipped)
- [ ] Document each failed test with details
- [ ] List passing tests
- [ ] Note any warnings or environment issues
- [ ] Calculate overall pass rate

### Task 5: Progress Tracking
- [ ] Update progress.md throughout execution
- [ ] Track blockers and issues
- [ ] Estimate completion time
- [ ] Final status update

### Task 6: Team Communication
- [ ] Send completion message to team-lead
- [ ] Include pass/fail summary
- [ ] Report major findings
- [ ] Confirm readiness for next phase

## Success Criteria
- ✅ All test scenarios executed
- ✅ Pass/fail status documented for each
- ✅ Screenshots captured for failures
- ✅ Evidence organized in proper directories
- ✅ Playwright HTML report preserved
- ✅ Findings.md complete with actionable details
- ✅ Team lead notified of completion

## Execution Strategy

1. **Pre-flight**: Verify environment and services
2. **Execute**: Run Playwright tests with evidence capture
3. **Document**: Record results in findings.md
4. **Organize**: Save all evidence to proper locations
5. **Report**: Update progress and notify team lead

## Notes
- Distinguish between real test failures vs environment issues
- If services aren't running, document as blocker (not test failure)
- Use Playwright MCP tools if manual verification needed
- Capture screenshots for both passes (key moments) and failures
