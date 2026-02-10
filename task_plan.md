# Task Plan: Fix Critical Regressions + E2E Validation

## Status: PLANNING → RESEARCHING
## Created: 2026-02-09
## Last Updated: 2026-02-09

---

## Objective
Fix two critical regressions (Source Not Found, AG Grid RowGroupingModule error) introduced during E1-S11..S20, verify fixes with Playwright MCP, and create a true end-to-end PDF extraction test.

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
