# E2E Testing Infrastructure

ACM-AI includes a self-healing, tiered E2E testing framework built on Playwright. Tests are organized into 4 tiers (smoke, critical, feature, accessibility), supported by a selector healing engine, state recovery, API contract validation, and evidence collection.

## Quick Links

| Document | Description |
|----------|-------------|
| [Developer Guide](guide.md) | Setup, running, writing, and debugging tests |
| [Cheat Sheet](cheat-sheet.md) | One-page quick reference for all commands, fixtures, helpers |
| [Agent Reference](agents.md) | `acm-e2e-tester` and `acm-ui-tester` capabilities and workflows |
| [Framework Deep Dive](framework.md) | Self-healing architecture, config, classes, recovery flow |
| [Agent-Browser Patterns](agent-browser.md) | Browser automation patterns for ACM-specific debugging |
| [AI Knowledge Base](AI-KNOWLEDGE-BASE.md) | Agent-facing reference: decision tree, workflows, rules, routing |

## At a Glance

- **Test count**: ~170 tests across 7 spec files, 4 tiers
- **Framework modules**: 8 (selector engine, state recovery, evidence collector, healing reporter, API contract validator, route walker, accessibility auditor, config)
- **Helper libraries**: 3 (ACM helpers, screenshot helpers, chat helpers)
- **Routes covered**: 24 static + 4 dynamic
- **CI/CD**: GitHub Actions with tiered execution (smoke every PR, critical on merge, full nightly)

## Entry Points

```bash
# Run all tests
npx playwright test

# Run by tier
npx playwright test --project=smoke
npx playwright test --project=critical
npx playwright test --project=feature
npx playwright test --project=accessibility

# Run by tag
npx playwright test --grep @smoke
npx playwright test --grep @critical
```

## Key Paths

| Path | Purpose |
|------|---------|
| `playwright.config.ts` | Playwright configuration with tiered projects |
| `tests/e2e/specs/` | Test spec files (7 files) |
| `tests/e2e/framework/` | Self-healing framework modules |
| `tests/e2e/helpers/` | ACM, screenshot, and chat helper functions |
| `tests/support/fixtures/` | Playwright fixtures (merged test, self-healing) |
| `test-results/` | Test output, evidence, healing report |
| `playwright-report/` | HTML report |
| `.github/workflows/e2e-tests.yml` | CI/CD workflow |

## Agents and Skills

Two agents and two skills power automated E2E workflows:

- **`acm-e2e-tester`** agent: Full-stack E2E testing (upload, extraction, grid, export, API)
- **`acm-ui-tester`** agent: Component-level UI testing (rendering, forms, responsive, a11y)
- **`e2e-test`** skill: Self-healing test execution with autonomous failure recovery
- **`agent-browser`** skill: Interactive browser automation CLI for debugging

See [Agent Reference](agents.md) for detailed usage.
