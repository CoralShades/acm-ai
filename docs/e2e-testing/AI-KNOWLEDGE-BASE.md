# E2E Testing AI Knowledge Base

**Audience**: Claude Code agents, Codex agents, BMAD agents (qa-specialist, acm-e2e-tester, acm-ui-tester, orchestrator, docs-specialist).

This document is the single entry point for AI agents that need to understand, run, write, debug, or extend E2E tests in ACM-AI. It tells you what to read, in what order, and what to do with the information.

---

## How to Use This Directory

The `docs/e2e-testing/` directory contains 6 reference documents. **Do not guess** test patterns, fixture APIs, selector strategies, or route lists. **Read the relevant file first.**

### Decision Tree: Which File Do I Read?

```
What do I need to do?
|
|-- Write a new E2E test?
|   --> Read: guide.md (Section 3: Writing New Tests)
|   --> Read: cheat-sheet.md (Fixtures, Tags, Helpers, data-testid)
|
|-- Run existing tests?
|   --> Read: cheat-sheet.md (Commands section -- top of file)
|
|-- Debug a failing test?
|   --> Read: agent-browser.md (Failure Investigation section)
|   --> Read: framework.md (SelectorEngine, StateRecovery)
|
|-- Understand the framework architecture?
|   --> Read: framework.md (full document)
|
|-- Choose the right agent or skill?
|   --> Read: agents.md (When to Use Which -- bottom of file)
|
|-- Quick-reference a fixture, helper, or config?
|   --> Read: cheat-sheet.md (one-page, all tables)
|
|-- Add a data-testid to a component?
|   --> Read: guide.md (Section 6: data-testid Registry)
|   --> Then UPDATE guide.md and cheat-sheet.md registries after adding
```

---

## File Manifest

| File | Size | Read When |
|------|------|-----------|
| [README.md](README.md) | Index | Orientation -- first visit only |
| [guide.md](guide.md) | Full guide | Writing tests, understanding tiers, CI/CD, helpers |
| [cheat-sheet.md](cheat-sheet.md) | Quick ref | Looking up any command, fixture, helper, route, config |
| [agents.md](agents.md) | Agent ref | Choosing agent/skill, understanding workflows |
| [framework.md](framework.md) | Deep dive | Understanding self-healing internals, debugging complex failures |
| [agent-browser.md](agent-browser.md) | Patterns | Interactive browser debugging, visual regression, data extraction |

---

## Prescriptive Workflows for AI Agents

### Workflow 1: Write a New E2E Test

**When**: A story includes UI acceptance criteria, a new page/route, or a new API endpoint.

**Steps**:

1. **Read** `guide.md` Section 3 (Writing New Tests) for the import pattern, fixture list, tagging rules, and file placement.
2. **Read** `cheat-sheet.md` to find available fixtures, helpers, and existing `data-testid` values.
3. **Read** existing specs in `tests/e2e/specs/` to match conventions (use `Glob` on `tests/e2e/specs/*.spec.ts`).
4. **Determine tier and tag**:
   - Route loads / API health => `@smoke`, place in `smoke-walker.spec.ts` or new smoke file
   - Core user workflow (upload, jobs, export) => `@critical`, place in relevant spec
   - Feature-specific (settings, building detail, provenance) => `@feature`
   - Accessibility check => `@a11y`, place in `accessibility.spec.ts`
5. **Write the test** using this template:
   ```typescript
   import { test, expect } from '../../support/fixtures';

   test.describe('Feature Name @tag', () => {
     test('does specific thing', async ({ page, apiClient, healingPage }) => {
       // Use helpers from tests/e2e/helpers/ for common operations
       // Use healingPage for self-healing selector fallback
       // Use apiClient for direct API calls
     });
   });
   ```
6. **Add data-testid** to any component the test needs to select. Update the registry in `guide.md` Section 6 and `cheat-sheet.md`.
7. **Run** the test: `npx playwright test tests/e2e/specs/{file}.spec.ts --headed` to verify.
8. **Verify** CI config: if the test is smoke/critical, confirm it matches a `testMatch` pattern in `playwright.config.ts`.

### Workflow 2: Debug a Failing E2E Test

**When**: A test fails in CI or locally.

**Steps**:

1. **Read** the failure output (test name, error message, screenshot path).
2. **Read** `cheat-sheet.md` Recovery Levels and Selector Strategy Chain to understand self-healing behavior.
3. **Check** `test-results/healing-report.json` for recommendations (use `Read` tool).
4. **Read** `agent-browser.md` Failure Investigation section for the interactive debugging pattern:
   ```bash
   agent-browser open <failing-url>
   agent-browser snapshot -i -s "[data-testid='expected-element']"
   agent-browser eval 'document.querySelectorAll(".ag-row").length'
   agent-browser screenshot --annotate --full test-results/evidence/debug.png
   ```
5. **Diagnose** the root cause:
   - Missing element? => Add `data-testid`, update component
   - Selector drift? => Update selector in test, add `ElementContext` for better healing
   - API contract change? => Update `KEY_CONTRACTS` in `tests/e2e/framework/self-healing/api-contract-validator.ts`
   - Stuck state? => Check `StateRecovery` escalation in `framework.md`
6. **Fix and re-run**: `npx playwright test --grep "test name" --headed`

### Workflow 3: Add a New Page/Route

**When**: A new frontend route is created.

**Steps**:

1. **Add** the route to `STATIC_ROUTES` or `DYNAMIC_ROUTES` in `tests/e2e/framework/route-walker.ts`.
2. **Update** `cheat-sheet.md` Routes section.
3. **Add a smoke test** in `smoke-walker.spec.ts` (route walker will cover it automatically if added to the arrays).
4. **Add data-testid** to the new page's root component.
5. **Write feature tests** if the page has interactive elements (see Workflow 1).
6. **Run** smoke tier to verify: `npx playwright test --project=smoke`

### Workflow 4: Validate API Contract Changes

**When**: Backend API response shapes change.

**Steps**:

1. **Read** `framework.md` APIContractValidator section for the `KEY_CONTRACTS` map.
2. **Update** `KEY_CONTRACTS` in `tests/e2e/framework/self-healing/api-contract-validator.ts`.
3. **Update** `cheat-sheet.md` API Contracts table.
4. **Run** contract tests: `npx playwright test --grep "@api-contracts"`

### Workflow 5: Verify Story Completion (QA Gate)

**When**: A story is about to be marked complete.

**Steps**:

1. **Run smoke**: `npx playwright test --project=smoke` -- must pass.
2. **Run affected tier**: match the story's scope to a tier and run it.
3. **Check healing report**: `test-results/healing-report.json` -- zero `failed` and zero `fragile-selector` recommendations.
4. **Check route coverage**: all new routes must show `tested` status.
5. **Collect evidence**: screenshots in `test-results/evidence/` or `test-results/screenshots/`.
6. **Report**: include test count, pass/fail, screenshot paths in the story's dev agent record.

---

## Source File Quick Reference

Use these paths when you need to read or modify framework code directly.

### Framework Modules

| Module | Path | Key Exports |
|--------|------|-------------|
| Config | `tests/e2e/framework/self-healing/config.ts` | `SelectorStrategy`, `RecoveryLevel`, `STRATEGY_CHAIN`, `DEFAULT_CONFIG` |
| Selector Engine | `tests/e2e/framework/self-healing/selector-engine.ts` | `SelectorEngine`, `ElementContext`, `HealingResult` |
| State Recovery | `tests/e2e/framework/self-healing/state-recovery.ts` | `StateRecovery`, `RecoveryState` |
| API Validator | `tests/e2e/framework/self-healing/api-contract-validator.ts` | `APIContractValidator`, `KEY_CONTRACTS`, `ContractValidation`, `DriftReport` |
| Evidence | `tests/e2e/framework/self-healing/evidence-collector.ts` | `EvidenceCollector`, `EvidenceBundle` |
| Reporter | `tests/e2e/framework/self-healing/healing-reporter.ts` | `HealingReporter`, `HealingReport`, `TestResult` |
| Route Walker | `tests/e2e/framework/route-walker.ts` | `RouteWalker`, `STATIC_ROUTES`, `DYNAMIC_ROUTES`, `RouteWalkResult` |
| Accessibility | `tests/e2e/framework/accessibility.ts` | `auditPage`, `getCriticalViolations`, `AccessibilityViolation`, `AccessibilityAuditResult` |

### Fixtures

| Fixture | Path | Provides |
|---------|------|----------|
| Merged test | `tests/support/fixtures/index.ts` | `test`, `expect`, `apiClient`, `waitHelpers`, `healingPage`, `evidence`, `apiValidator` |
| Self-healing | `tests/support/fixtures/self-healing.ts` | `HealingPage`, `EvidenceCollector`, `APIContractValidator`, `SelectorEngine`, `StateRecovery` |

### Helpers

| Helper Set | Path | Key Functions |
|------------|------|---------------|
| ACM | `tests/e2e/helpers/acm-helpers.ts` | `uploadSAMP`, `waitForExtraction`, `navigateToACMRegister`, `getACMGridRows`, `getACMRecordCount`, `validateACMGrid`, `searchACMGrid`, `getACMRecordDetails`, `exportACMRecords` |
| Screenshots | `tests/e2e/helpers/screenshot-helpers.ts` | `captureEvidence`, `captureWorkflow`, `captureComparison`, `captureElement`, `captureGridState`, `captureError`, `captureMobileView` |
| Chat | `tests/e2e/helpers/chat-helpers.ts` | `sendChatMessage`, `waitForAgentResponse`, `getLastChatMessage`, `verifyToolCall`, `verifyToolResult`, `switchChatMode`, `testACMStatsQuery`, `testACMSearchQuery`, `testContextSwitch`, `testAgentErrorHandling`, `clearChatHistory` |
| Central export | `tests/e2e/helpers/index.ts` | Re-exports all of the above |

### Spec Files

| Spec | Path | Tier | Tag |
|------|------|------|-----|
| Route walker | `tests/e2e/specs/smoke-walker.spec.ts` | smoke | `@smoke` |
| API contracts | `tests/e2e/specs/api-contracts.spec.ts` | smoke | `@smoke @api-contracts` |
| Upload wizard | `tests/e2e/specs/upload-wizard.spec.ts` | critical | `@critical` |
| Jobs pipeline | `tests/e2e/specs/jobs-pipeline.spec.ts` | critical | `@critical` |
| Settings pages | `tests/e2e/specs/settings-pages.spec.ts` | feature | `@feature` |
| Building detail | `tests/e2e/specs/building-detail.spec.ts` | feature | `@feature` |
| Accessibility | `tests/e2e/specs/accessibility.spec.ts` | a11y | `@a11y` |

### Config and CI

| File | Path |
|------|------|
| Playwright config | `playwright.config.ts` |
| CI workflow | `.github/workflows/e2e-tests.yml` |
| Agent: E2E tester | `.claude/agents/acm-e2e-tester.md` |
| Agent: UI tester | `.claude/agents/acm-ui-tester.md` |
| Skill: E2E test | `.claude/skills/e2e-test/SKILL.md` |
| Skill: Agent-browser | `.claude/skills/agent-browser/SKILL.md` |

---

## Agent Routing

| Agent | When to Invoke | Model |
|-------|---------------|-------|
| `acm-e2e-tester` | Full-stack flows: upload -> extraction -> grid -> export -> API | sonnet |
| `acm-ui-tester` | Component rendering, forms, responsive, a11y | sonnet |
| `qa-specialist` | Story AC coverage validation, missing test detection | sonnet |
| `docs-specialist` | After adding tests -- update this knowledge base and docs | sonnet |

---

## Rules for AI Agents

1. **Never write E2E tests from memory.** Always read the relevant docs first (`guide.md`, `cheat-sheet.md`).
2. **Always use the fixture import pattern**: `import { test, expect } from '../../support/fixtures';`
3. **Always tag tests** with the appropriate tier tag (`@smoke`, `@critical`, `@feature`, `@a11y`).
4. **Always provide ElementContext** when using `healingClick`/`healingFill`/`healingWaitFor` -- the more fields you provide (`testId`, `semanticRole`, `textContent`, `ariaLabel`), the better the healing.
5. **Always add data-testid** to components that tests select. Update both `guide.md` Section 6 and `cheat-sheet.md` registries.
6. **Always add new routes** to `STATIC_ROUTES` or `DYNAMIC_ROUTES` in `route-walker.ts`.
7. **Always update KEY_CONTRACTS** when API response shapes change.
8. **Always run smoke after changes**: `npx playwright test --project=smoke`.
9. **Never hardcode waits** (`waitForTimeout`). Use `waitHelpers.waitForApi()`, `waitHelpers.waitForNetworkIdle()`, or explicit element waits.
10. **Keep this knowledge base current.** If you add new helpers, fixtures, specs, or routes -- update the relevant docs in this directory.

---

## Cross-References

| Context | Reference |
|---------|-----------|
| Skill invocation guide | `docs/skills/02-testing-quality/README.md` |
| Project architecture | `docs/development/architecture.md` |
| API reference | `docs/development/api-reference.md` |
| CLAUDE.md (project rules) | `CLAUDE.md` (root) |
| Sprint artifacts | `docs/sprint-artifacts/` |
| Full docs index | `docs/index.md` |
