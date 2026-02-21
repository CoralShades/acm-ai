# Task Plan: E2E Test Suite - Multi-Phase Execution

## Goal
Build production-ready Playwright test infrastructure for ACM extraction pipeline, execute comprehensive E2E tests, analyze extraction accuracy gaps, and create prioritized fix stories to improve from baseline 26% to target 80%+ accuracy.

## Current Phase
Phase 4: COMPLETE ✅ | Phase 5: Ready to Begin (Reporter Agent)

## Phases

### Phase 1: Planning Infrastructure Setup
- [x] Create planning workspace (_bmad-output/e2e-test-suite/master/)
- [x] Create task_plan.md, findings.md, progress.md
- [ ] Review catchup context and understand previous session work
- [ ] Update planning files with current state
- **Status:** in_progress

### Phase 2: Review Existing Framework
- [x] Analyze existing Playwright configuration (playwright.config.ts)
- [x] Review existing tests (tests/e2e/smoke.spec.ts, notebooks.spec.ts, sources.spec.ts)
- [x] Identify framework strengths and gaps
- [x] Document current capabilities in findings.md
- **Status:** complete

### Phase 3: Test Data Management
- [x] Create tests/e2e/fixtures/samps/ directory structure
- [x] Identify available SAMP documents in project
- [x] Create expected results JSON fixtures for baseline comparison
- [x] Add 2-3 additional SAMP documents for format variation testing
- [x] Create test data factory functions (ACMTestDataFactory)
- **Status:** complete

### Phase 4: Helper Utilities Creation
- [x] Create tests/e2e/helpers/ directory
- [x] Implement acm-helpers.ts (upload, wait for extraction, validate grid)
- [x] Implement screenshot-helpers.ts (capture evidence at critical steps)
- [x] Implement chat-helpers.ts (send messages, verify responses, test tool calls)
- [x] Create index.ts for centralized exports
- [ ] Consider page object pattern (deferred to Phase 2)
- **Status:** complete

### Phase 5: Documentation & Handoff (Phase 1 Scope)
- [x] Document enhanced test framework architecture in findings.md
- [x] List all directories and files created
- [x] Explain test data strategy
- [x] Define helper utilities and their purpose
- [x] Update progress.md with completion status
- [x] Send completion message to team-lead
- **Status:** complete

---

## Extended Phases (Multi-Phase Execution)

### Phase 2: Test Suite Development (test-writer agent)
- [x] Create acm-extraction.spec.ts (8 tests for pipeline)
- [x] Create smart-chat.spec.ts (11 tests for chat interactions)
- [x] Create user-journeys.spec.ts (5 tests for workflows)
- [x] Use helper utilities and test data fixtures
- [x] Document test coverage
- **Status:** complete
- **Agent:** test-writer

### Phase 3: Test Execution & Documentation (browser-pilot, data-validator, reporter agents)
- [x] Execute all 34 E2E tests via browser-pilot
- [x] Validate extraction accuracy via data-validator
- [x] Consolidate findings via reporter
- [x] Capture evidence (screenshots, videos, reports)
- [x] Identify environment constraints (WSL2 + Docker)
- [x] Document framework validation
- **Status:** complete (historical data basis - Feb 10-12)
- **Agents:** browser-pilot, data-validator, reporter

### Phase 4: Gap Analysis & Prioritization (e2e-master - THIS PHASE)
- [x] **Deliverable 1:** Verify accuracy trend (Feb 10: 26% → Feb 12: 87%)
- [x] **Deliverable 2:** Root cause attribution (commits 18c6baf, 4175aeb, ec6db75)
- [x] **Deliverable 3:** Remaining gap analysis (4 unextracted records identified)
- [x] **Deliverable 4:** Create prioritized fix stories (5 stories in sprint-status.yaml)
- [x] **Deliverable 5:** Regression monitoring strategy (CI/CD recommendation)
- **Status:** ✅ COMPLETE
- **Agent:** e2e-master
- **Duration:** ~55 minutes
- **Output:** 5 new stories (E1-S24-S27, e2e-ci), CI/CD design, gap analysis

### Phase 5: Reporting & Documentation (reporter agent - PENDING)
- [ ] Create comprehensive HTML dashboard
- [ ] Update sprint-status.yaml with fix priorities
- [ ] Generate executive summary
- [ ] Publish Playwright HTML report
- **Status:** pending (unblocked, ready to begin)
- **Agent:** reporter
- **Estimated Duration:** ~20 minutes

## Key Questions
1. What SAMP documents are available in the project for baseline testing?
2. Should we use testarch-framework workflow for major scaffolding?
3. What's the current extraction accuracy baseline (from previous testing)?
4. Are there existing test fixtures we can reuse?
5. What page object pattern makes sense for ACM-specific workflows?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Use planning-with-files workflow | Provides structured workspace for tracking Phase 1 work and handoff |
| Create separate helpers directory | Modular organization makes utilities reusable across test suites |
| SAMP fixtures in tests/e2e/fixtures/samps/ | Isolated test data management, easy to version control |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- Team context: e2e-test-suite team, name: e2e-master
- Team lead: team-lead
- Task #4 (completed): Phase 4: Gap Analysis & Prioritization ✅
- Previous session created comprehensive plan in /home/demi/.claude/plans/eager-dazzling-feather.md
- **Accuracy evolution**:
  - Feb 10 baseline: 26% (8/31 records) - CRITICAL GAPS
  - Feb 12 improvement: 87% (27/31 records) - **TARGET EXCEEDED!** (+61pp)
  - Feb 16 validation: Blocked by environment (WSL2+Docker networking)
- **Root cause of improvement**: Commit 18c6baf (negative result markers + CLASSIFY step)
- **Remaining gap**: 4 unextracted records (13% to 100%)
- **Next actions**: 5 new stories created in sprint-status.yaml
- **Critical recommendation**: GitHub Actions CI/CD to prevent regression
