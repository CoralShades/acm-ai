# E2E Testing Developer Guide

## 1. Getting Started

### Prerequisites

```bash
# Install root dependencies (includes Playwright)
npm install

# Install frontend dependencies
cd frontend && npm install

# Install Playwright browsers
npx playwright install --with-deps chromium
```

### Running Tests

```bash
# By tier (recommended)
npx playwright test --project=smoke             # Tier 1: <30s, route walking + API health
npx playwright test --project=critical          # Tier 2: <5min, upload wizard + jobs pipeline
npx playwright test --project=feature           # Tier 3: <15min, settings + building detail
npx playwright test --project=accessibility     # A11y: <5min, WCAG 2.1 AA audits

# By tag
npx playwright test --grep @smoke
npx playwright test --grep @critical
npx playwright test --grep @feature
npx playwright test --grep @a11y
npx playwright test --grep "@api-contracts"

# Single file
npx playwright test tests/e2e/specs/smoke-walker.spec.ts

# Headed mode (visible browser)
npx playwright test --headed

# Debug mode (step through)
npx playwright test --debug

# List tests without running
npx playwright test --list

# Full suite
npx playwright test
```

### Understanding Results

| Artifact | Path | Description |
|----------|------|-------------|
| HTML report | `playwright-report/` | Interactive test report (open with `npx playwright show-report`) |
| JUnit XML | `test-results/junit.xml` | CI-compatible test results |
| Evidence | `test-results/evidence/` | Screenshots, console logs, network traces |
| Healing report | `test-results/healing-report.json` | Self-healing actions and recommendations |
| Screenshots | `test-results/screenshots/` | Workflow and error screenshots |

## 2. Test Architecture

### Directory Structure

```
tests/
  e2e/
    specs/                           # Test spec files (tiered)
      smoke-walker.spec.ts           # @smoke - Route walking
      api-contracts.spec.ts          # @smoke @api-contracts - API shapes
      upload-wizard.spec.ts          # @critical - Upload wizard flow
      jobs-pipeline.spec.ts          # @critical - Job lifecycle
      settings-pages.spec.ts         # @feature - Settings sub-pages
      building-detail.spec.ts        # @feature - Building detail page
      accessibility.spec.ts          # @a11y - WCAG audits
    framework/                       # Self-healing framework
      self-healing/
        config.ts                    # Thresholds, strategy chain, recovery levels
        selector-engine.ts           # Multi-strategy selector resolution
        state-recovery.ts            # Stuck-state recovery state machine
        api-contract-validator.ts    # API response shape validation
        evidence-collector.ts        # Screenshot, console, network evidence
        healing-reporter.ts          # Aggregated healing report
      route-walker.ts                # Automated route walking utility
      accessibility.ts               # axe-core WCAG 2.1 AA wrapper
    helpers/                         # Test helper functions
      index.ts                       # Central re-export
      acm-helpers.ts                 # ACM upload, grid, export helpers
      screenshot-helpers.ts          # Evidence capture helpers
      chat-helpers.ts                # Chat interaction helpers
  support/
    fixtures/
      index.ts                       # Merged test fixtures
      self-healing.ts                # HealingPage, EvidenceCollector, APIContractValidator
```

### Test Tiers

| Tier | Project | Tag | Trigger | Timeout | What It Tests |
|------|---------|-----|---------|---------|---------------|
| Smoke | `smoke` | `@smoke` | Every PR | <30s | All routes load, API health checks |
| Critical | `critical` | `@critical` | Merges to main | <5min | Upload wizard, jobs pipeline |
| Feature | `feature` | `@feature` | Nightly | <15min | Settings pages, building detail |
| A11y | `accessibility` | `@a11y` | Nightly | <5min | WCAG 2.1 AA compliance |

Tier dependencies: `critical` and `feature` depend on `smoke` passing first.

### Playwright Config Overview

Key settings from `playwright.config.ts`:

| Setting | Value |
|---------|-------|
| `testDir` | `./tests/e2e` |
| `testIgnore` | `**/framework/**`, `**/helpers/**` |
| `baseURL` | `http://localhost:8503` |
| `timeout` | 60s (test), 15s (action), 30s (navigation), 10s (expect) |
| `retries` | 2 in CI, 0 locally |
| `workers` | 1 in CI, auto locally |
| `viewport` | 1280x720 |
| `artifacts` | trace/screenshot/video on failure only |
| `webServer` | `cd frontend && npm run dev` (auto-starts frontend) |

## 3. Writing New Tests

### Import Pattern

```typescript
import { test, expect } from '../../support/fixtures';
```

This gives you access to all custom fixtures alongside the standard Playwright `page`.

### Available Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `page` | `Page` | Standard Playwright page (from base) |
| `apiClient` | `{ get, post, put, delete }` | Backend API client (port 5055) |
| `waitHelpers` | `{ waitForApi, waitForNetworkIdle }` | Async operation helpers |
| `healingPage` | `HealingPage` | Self-healing page wrapper |
| `evidence` | `EvidenceCollector` | Screenshot/log/network capture |
| `apiValidator` | `APIContractValidator` | API response shape validator |

### Example Test

```typescript
import { test, expect } from '../../support/fixtures';

test.describe('ACM Grid @feature', () => {
  test('displays building records', async ({ page, apiClient }) => {
    // Navigate to ACM register
    await page.goto('/source/source:test');
    await page.waitForSelector('[data-testid="item-grid"]');

    // Verify grid loaded
    const rows = page.locator('.ag-row');
    await expect(rows).not.toHaveCount(0);
  });
});
```

### Mock Route Interception

For tests that don't need real API responses:

```typescript
test('handles empty grid', async ({ page }) => {
  // Mock the buildings API
  await page.route('**/api/acm/buildings*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ buildings: [], total: 0 }),
    });
  });

  await page.goto('/source/source:test');
  await expect(page.getByText(/no buildings/i)).toBeVisible();
});
```

### Tagging Convention

| Tag | Usage | Where Tests Run |
|-----|-------|-----------------|
| `@smoke` | Route loads, API health | Every PR |
| `@critical` | Core user workflows | Merges to main |
| `@feature` | Feature-specific validation | Nightly |
| `@a11y` | Accessibility compliance | Nightly |
| `@api-contracts` | API response shape checks | Every PR (with smoke) |

Add tags to `test.describe` or individual `test()` names:

```typescript
test.describe('Upload Wizard @critical', () => { ... });
test('validates field schema @api-contracts', async () => { ... });
```

### Where to Put New Specs

- **Tiered specs**: `tests/e2e/specs/` (matched by project `testMatch` patterns)
- **General specs**: `tests/e2e/` root (caught by the `chromium` catch-all project)

## 4. Using Self-Healing

### HealingPage API

```typescript
test('self-healing example', async ({ healingPage }) => {
  // Navigate with state recovery on failure
  await healingPage.healingGoto('http://localhost:8503/acm');

  // Click with selector fallback chain
  await healingPage.healingClick('[data-testid="old-selector"]', {
    testId: 'new-selector',
    semanticRole: 'button',
    textContent: 'Click Me',
    ariaLabel: 'Action button',
  });

  // Fill with fallback
  await healingPage.healingFill('input.search', 'query', {
    ariaLabel: 'Search records',
  });

  // Wait with fallback
  await healingPage.healingWaitFor('.loading-done', {
    textContent: 'Ready',
  });
});
```

### ElementContext Interface

Provide as much context as possible for better healing:

```typescript
interface ElementContext {
  originalSelector: string;  // The CSS selector that failed
  testId?: string;           // data-testid value
  semanticRole?: string;     // ARIA role (button, textbox, etc.)
  textContent?: string;      // Visible text content
  ariaLabel?: string;        // aria-label value
  parentContext?: string;    // Parent selector for scoping
}
```

### Evidence Collection

```typescript
test('with evidence', async ({ healingPage, evidence }) => {
  await healingPage.healingGoto('http://localhost:8503/acm');

  // Capture evidence bundle (screenshot + console + network)
  const bundle = await evidence.captureEvidence(healingPage.page, 'acm-grid-test');

  // Or capture just a screenshot
  await evidence.captureScreenshot(healingPage.page, 'grid-loaded');
});
```

### Reading the Healing Report

After a test run, check `test-results/healing-report.json`:

```json
{
  "timestamp": "2026-03-05T10:00:00.000Z",
  "totalTests": 29,
  "passed": 27,
  "failed": 0,
  "healed": 2,
  "skipped": 0,
  "healingActions": [
    {
      "strategy": "role-name",
      "confidence": 0.95,
      "suggestedFix": "Consider adding data-testid. Element was found via role=\"button\" name=\"Submit\"",
      "healingLog": "Resolved \".old-class\" via role-name (confidence: 0.95)"
    }
  ],
  "recommendations": [
    { "type": "add-testid", "message": "Consider adding data-testid..." },
    { "type": "missing-coverage", "message": "Route \"/advanced\" has no E2E test coverage" }
  ],
  "routeCoverage": { "/": "tested", "/acm": "tested", "/advanced": "untested" }
}
```

## 5. Available Helpers

### ACM Helpers

```typescript
import { uploadSAMP, waitForExtraction, navigateToACMRegister,
         getACMGridRows, getACMRecordCount, validateACMGrid,
         searchACMGrid, getACMRecordDetails, exportACMRecords } from '../helpers';
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `uploadSAMP` | `(page, filepath) => Promise<void>` | Upload PDF through 4-step wizard |
| `waitForExtraction` | `(page, timeout?) => Promise<void>` | Poll until extraction completes |
| `navigateToACMRegister` | `(page) => Promise<void>` | Navigate to ACM tab, wait for grid |
| `getACMGridRows` | `(page) => Promise<Locator>` | Get AG Grid row locators |
| `getACMRecordCount` | `(page) => Promise<number>` | Count visible grid rows |
| `validateACMGrid` | `(page, expectedCount, minAccuracy?) => Promise<void>` | Assert grid accuracy threshold |
| `searchACMGrid` | `(page, searchTerm) => Promise<boolean>` | Search grid, return if results found |
| `getACMRecordDetails` | `(page, rowIndex) => Promise<Record<string, string>>` | Click row, extract field values from dialog |
| `exportACMRecords` | `(page, format?) => Promise<void>` | Trigger CSV/Excel export |

### Screenshot Helpers

```typescript
import { captureEvidence, captureWorkflow, captureComparison,
         captureElement, captureGridState, captureError,
         captureMobileView } from '../helpers';
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `captureEvidence` | `(page, name, options?) => Promise<string>` | Named screenshot to evidence dir |
| `captureWorkflow` | `(page, workflowName, steps) => Promise<string[]>` | Multi-step workflow screenshots |
| `captureComparison` | `(page, name, beforeAction) => Promise<{before, after}>` | Before/after comparison |
| `captureElement` | `(page, selector, name) => Promise<string>` | Screenshot of specific element |
| `captureGridState` | `(page, gridSelector, name) => Promise<string>` | Grid-specific screenshot |
| `captureError` | `(page, errorName) => Promise<string>` | Full-page error screenshot |
| `captureMobileView` | `(page, name, viewport?) => Promise<string>` | Mobile viewport screenshot |

### Chat Helpers

```typescript
import { sendChatMessage, waitForAgentResponse, getLastChatMessage,
         verifyToolCall, verifyToolResult, switchChatMode,
         testACMStatsQuery, testACMSearchQuery, testContextSwitch,
         testAgentErrorHandling, clearChatHistory } from '../helpers';
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `sendChatMessage` | `(page, message) => Promise<void>` | Type and send chat message |
| `waitForAgentResponse` | `(page, timeout?) => Promise<void>` | Wait for agent typing to finish |
| `getLastChatMessage` | `(page) => Promise<string>` | Get last message text |
| `verifyToolCall` | `(page, toolName) => Promise<boolean>` | Check if tool call indicator exists |
| `verifyToolResult` | `(page, resultType) => Promise<boolean>` | Check tool result visualization |
| `switchChatMode` | `(page, mode) => Promise<void>` | Toggle normal/smart chat mode |
| `testACMStatsQuery` | `(page) => Promise<void>` | End-to-end stats query test |
| `testACMSearchQuery` | `(page, searchTerm) => Promise<void>` | End-to-end search query test |
| `testContextSwitch` | `(page) => Promise<void>` | Test chat-to-grid navigation |
| `testAgentErrorHandling` | `(page) => Promise<void>` | Test graceful error handling |
| `clearChatHistory` | `(page) => Promise<void>` | Clear chat and verify empty |

## 6. data-testid Registry

Components with `data-testid` attributes:

| Component | data-testid | File |
|-----------|-------------|------|
| App Sidebar | `app-sidebar` | `components/layout/AppSidebar.tsx` |
| Building Sidebar | `building-sidebar` | `components/acm/BuildingSidebar.tsx` |
| Command Palette | `command-palette` | `components/common/CommandPalette.tsx` |
| Extraction Progress | `extraction-progress` | `components/acm/ExtractionProgress.tsx` |
| Item Grid | `item-grid` | `components/acm/ItemGrid.tsx` |
| Upload Wizard | `upload-wizard` | `components/acm/UploadWizard.tsx` |
| Upload Step 1 | `upload-step-1` | `components/acm/UploadWizard.tsx` |
| Upload Step 2 | `upload-step-2` | `components/acm/UploadWizard.tsx` |
| Upload Step 3 | `upload-step-3` | `components/acm/UploadWizard.tsx` |
| File Input | `file-input` | `components/acm/UploadWizard.tsx` |
| Mode Standard | `mode-standard` | `components/acm/UploadWizard.tsx` |
| Mode AI Enhanced | `mode-ai-enhanced` | `components/acm/UploadWizard.tsx` |
| Confirm File Name | `confirm-file-name` | `components/acm/UploadWizard.tsx` |
| Extract Button | `extract-button` | `components/acm/UploadWizard.tsx` |

**Adding new data-testid attributes:**
1. Add `data-testid="descriptive-name"` to the component's root element
2. Add the entry to this registry table
3. Use the testid in test selectors: `page.locator('[data-testid="descriptive-name"]')`

## 7. CI/CD Integration

### GitHub Actions Workflow

File: `.github/workflows/e2e-tests.yml`

| Trigger | Tiers Run | Timeout |
|---------|-----------|---------|
| Pull request to `main` | Smoke only | 30min |
| Push to `main` | Smoke + Critical | 30min |
| Nightly (6am UTC) | Smoke + Critical + Feature + A11y | 30min |
| Manual (`workflow_dispatch`) | All tiers | 30min |

### CI Steps

1. Start SurrealDB (Docker)
2. Setup Python 3.11 + `uv sync`
3. Setup Node.js 20 + `npm ci` (frontend)
4. Install Playwright browsers (`chromium`)
5. Start Backend API + Frontend
6. Run tests by tier
7. Upload artifacts

### Artifacts Uploaded

| Artifact | Contents | Retention |
|----------|----------|-----------|
| `smoke-results` | `test-results/` | 7 days |
| `critical-results` | `test-results/` | 7 days |
| `full-results` | `test-results/` + `playwright-report/` | 14 days |
| `healing-report` | `test-results/healing-report.json` | 14 days |

### Running Manually

Trigger via GitHub Actions UI: Actions > E2E Tests > Run workflow.
