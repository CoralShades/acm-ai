# Task Plan: Fix Critical Regressions + E2E Validation

## Status: NEW SESSION - RESEARCHING
## Created: 2026-02-09
## Last Updated: 2026-02-10

## User Answers (Clarification)

## Objective (2026-02-09 - COMPLETED)
~~Fix two critical regressions (Source Not Found, AG Grid RowGroupingModule error) introduced during E1-S11..S20, verify fixes with Playwright MCP, and create a true end-to-end PDF extraction test.~~

## NEW Objective (2026-02-10)
Fix two NEW critical bugs discovered during post-git-cleanup E2E testing:
1. **Frontend Turbopack 500 Error** (BLOCKER) - No pages load, complete UI failure
2. **API Upload Asyncio Loop Error** (HIGH) - PDF uploads fail with `asyncio.run() cannot be called from a running event loop`

Then create GitHub issues and implement fixes in a bug-fix branch.

---

## Phases

### Phase 1: Research & Diagnosis
- [ ] 1.1 Verify services are running (SurrealDB, API, Frontend)
- [ ] 1.2 Use Playwright MCP to reproduce "Source Not Found" bug
- [ ] 1.3 Use Playwright MCP to reproduce AG Grid RowGroupingModule error
- [ ] 1.4 Investigate backend source routes/services for regression
- [ ] 1.5 Investigate frontend AG Grid configuration
- [ ] 1.6 Check git diff for E1-S11..S20 changes that could cause regressions

### Phase 2: Fix Source Not Found
- [ ] 2.1 Identify root cause
- [ ] 2.2 Implement fix
- [ ] 2.3 Verify fix with Playwright MCP

### Phase 3: Fix AG Grid RowGroupingModule Error
- [ ] 3.1 Find AG Grid configuration in frontend
- [ ] 3.2 Register RowGroupingModule from ag-grid-enterprise
- [ ] 3.3 Verify fix with Playwright MCP

### Phase 4: E2E PDF Extraction Test
- [ ] 4.1 Identify test fixtures and existing patterns
- [ ] 4.2 Design E2E test: PDF → MinerU → LangGraph pipeline → assertions
- [ ] 4.3 Implement and run E2E test

### Phase 5: Final Verification
- [ ] 5.1 Full Playwright verification of both fixes
- [ ] 5.2 Run test suite for regression check
- [ ] 5.3 Update sprint status if needed

---

## NEW PHASES (2026-02-10)

### Phase 6: Playwright Verification & Diagnosis
- [ ] 6.1 Load Playwright MCP tools for browser automation
- [ ] 6.2 Verify services status (SurrealDB, API, Frontend)
- [ ] 6.3 Reproduce Bug #1: Frontend Turbopack 500 error
- [ ] 6.4 Reproduce Bug #2: API upload asyncio error via curl
- [ ] 6.5 Capture frontend `next dev` terminal output for detailed stack trace
- [ ] 6.6 Investigate frontend routing, SSR/RSC errors, API proxy config
- [ ] 6.7 Investigate `api/routers/sources.py` upload flow (lines 335-400)
- [ ] 6.8 Document findings with screenshots/logs

### Phase 7: Create GitHub Issues
- [ ] 7.1 Create Issue #1: Frontend Turbopack 500 Runtime Error
- [ ] 7.2 Create Issue #2: API Upload Asyncio Event Loop Conflict
- [ ] 7.3 Capture issue URLs for reference

### Phase 8: Branch & Fix Bug #1 (Turbopack)
- [ ] 8.1 Create branch `fix/turbopack-runtime-error`
- [ ] 8.2 Identify root cause from stack trace
- [ ] 8.3 Implement fix (potential: SSR config, routing, API proxy)
- [ ] 8.4 Test with `npm run dev`
- [ ] 8.5 Verify with Playwright: pages load without 500 errors

### Phase 9: Fix Bug #2 (Asyncio Upload)
- [ ] 9.1 Identify `asyncio.run()` call in `api/routers/sources.py`
- [ ] 9.2 Replace with proper `await` usage within async context
- [ ] 9.3 Test upload via curl: `POST /api/sources` with PDF
- [ ] 9.4 Verify via Playwright: UI upload completes successfully

### Phase 10: Full E2E Verification
- [ ] 10.1 Frontend loads without Turbopack errors
- [ ] 10.2 PDF upload via UI succeeds
- [ ] 10.3 ACM extraction completes and displays in grid
- [ ] 10.4 Run full test suite for regressions
- [ ] 10.5 Take screenshots as evidence

### Phase 11: Commit & PR
- [ ] 11.1 Commit fixes with semantic commit messages
- [ ] 11.2 Update GitHub issues with fix commits
- [ ] 11.3 Create PR linking to issues
- [ ] 11.4 Merge to main after verification

---

## Decisions Log
| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| - | - | - | - |

## Blockers
| # | Blocker | Status | Resolution |
|---|---------|--------|------------|
| - | - | - | - |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
