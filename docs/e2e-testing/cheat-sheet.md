# E2E Testing Cheat Sheet

## Commands

```bash
# By tier
npx playwright test --project=smoke
npx playwright test --project=critical
npx playwright test --project=feature
npx playwright test --project=accessibility

# By tag
npx playwright test --grep @smoke
npx playwright test --grep @critical
npx playwright test --grep @feature
npx playwright test --grep @a11y
npx playwright test --grep "@api-contracts"

# Single file
npx playwright test tests/e2e/specs/smoke-walker.spec.ts

# Headed / Debug
npx playwright test --headed
npx playwright test --debug

# List tests
npx playwright test --list

# Show report
npx playwright show-report
```

## Fixtures

| Fixture | Type | Usage |
|---------|------|-------|
| `page` | `Page` | `await page.goto('/acm')` |
| `apiClient` | `{ get, post, put, delete }` | `await apiClient.get('/health')` |
| `waitHelpers` | `{ waitForApi, waitForNetworkIdle }` | `await waitHelpers.waitForNetworkIdle()` |
| `healingPage` | `HealingPage` | `await healingPage.healingClick(sel, ctx)` |
| `evidence` | `EvidenceCollector` | `await evidence.captureEvidence(page, name)` |
| `apiValidator` | `APIContractValidator` | `apiValidator.validate(resp, fields, endpoint)` |

Import: `import { test, expect } from '../../support/fixtures';`

## Tags

| Tag | Meaning | When It Runs |
|-----|---------|-------------|
| `@smoke` | Pages load, API health | Every PR |
| `@critical` | Core workflows (upload, jobs) | Merges to main |
| `@feature` | Feature-specific tests | Nightly |
| `@a11y` | WCAG 2.1 AA audits | Nightly |
| `@api-contracts` | API response shape checks | Every PR |

## ACM Helpers

```typescript
uploadSAMP(page, filepath)                            // Upload PDF via wizard
waitForExtraction(page, timeout?)                      // Poll until extraction done
navigateToACMRegister(page)                            // Go to ACM tab
getACMGridRows(page) → Locator                         // Get AG Grid rows
getACMRecordCount(page) → number                       // Count visible rows
validateACMGrid(page, expectedCount, minAccuracy?)     // Assert accuracy
searchACMGrid(page, searchTerm) → boolean              // Search grid
getACMRecordDetails(page, rowIndex) → Record           // Get row field values
exportACMRecords(page, format?)                        // Trigger CSV/Excel export
```

## Screenshot Helpers

```typescript
captureEvidence(page, name, options?)       → string       // Named screenshot
captureWorkflow(page, name, steps)          → string[]     // Multi-step screenshots
captureComparison(page, name, action)       → {before, after}
captureElement(page, selector, name)        → string       // Element screenshot
captureGridState(page, gridSelector, name)  → string       // Grid screenshot
captureError(page, errorName)               → string       // Full-page error screenshot
captureMobileView(page, name, viewport?)    → string       // Mobile viewport
```

## Chat Helpers

```typescript
sendChatMessage(page, message)              // Type + send
waitForAgentResponse(page, timeout?)        // Wait for typing to finish
getLastChatMessage(page) → string           // Get last message text
verifyToolCall(page, toolName) → boolean    // Check tool call indicator
verifyToolResult(page, resultType) → boolean // Check result visualization
switchChatMode(page, 'normal'|'smart')      // Toggle chat mode
clearChatHistory(page)                      // Clear + verify empty
```

## data-testid Registry

| data-testid | Component |
|-------------|-----------|
| `app-sidebar` | AppSidebar |
| `building-sidebar` | BuildingSidebar |
| `command-palette` | CommandPalette |
| `extraction-progress` | ExtractionProgress |
| `item-grid` | ItemGrid |
| `upload-wizard` | UploadWizard |
| `upload-step-1` | UploadWizard step 1 |
| `upload-step-2` | UploadWizard step 2 |
| `upload-step-3` | UploadWizard step 3 |
| `file-input` | UploadWizard file input |
| `mode-standard` | UploadWizard standard mode |
| `mode-ai-enhanced` | UploadWizard AI mode |
| `confirm-file-name` | UploadWizard confirm |
| `extract-button` | UploadWizard extract |

## Routes Covered

### Static Routes (24)

```
/                    /notebooks           /sources
/documents           /acm                 /search
/settings            /settings/models     /settings/field-mapping
/settings/field-schema  /settings/extraction  /settings/processing
/settings/bar-templates /settings/parsers  /upload
/jobs                /extraction-monitor  /models
/podcasts            /transformations     /advanced
/test-grid           /landing             /login
```

### Dynamic Routes (12)

```
/notebooks/notebook:test                          /sources/source:test
/source/source:test                               /jobs/source:test
/extraction/source:test                           /jobs/source:test/chat
/jobs/source:test/extract                         /jobs/source:test/review/buildings
/jobs/source:test/review/records                  /source/source:test/building/building_record:test
/source/source:test/provenance/acm_record:test    /source/source:test/raw
```

## API Contracts Validated

| Endpoint | Expected Fields |
|----------|-----------------|
| `GET /health` | `status: string` |
| `GET /notebooks/` | `[].id: string`, `[].name: string` |
| `GET /sources/` | `[].id: string`, `[].title: string` |
| `GET /models/` | `[].name: string`, `[].provider: string` |
| `GET /models/defaults` | `chat_model: string` |
| `GET /acm/field-schema` | `item_fields: object`, `building_fields: object` |

## Selector Strategy Chain

| Priority | Strategy | Confidence | Example |
|----------|----------|------------|---------|
| 1 | `data-testid` | 1.0 | `[data-testid="acm-grid"]` |
| 2 | `role+name` | 0.95 | `getByRole('button', { name: 'Submit' })` |
| 3 | `aria-label` | 0.9 | `getByLabel('Search records')` |
| 4 | `text-content` | 0.8 | `getByText('Upload')` |
| 5 | `css` | 0.6 | `.ag-row` |
| 6 | `xpath` | 0.4 | `//div[@class="grid"]` |

## Recovery Levels

| Level | Action | When |
|-------|--------|------|
| 1. WAIT | 2s delay | First failure (maybe just slow) |
| 2. REFRESH | `page.reload()` + re-navigate | Second failure |
| 3. RESET | Clear cookies/localStorage, navigate from `/` | Third failure |
| 4. FAIL | Mark test failed | All attempts exhausted |

## Agent-Browser Quick Commands

```bash
agent-browser open <url>              # Navigate
agent-browser snapshot -i             # Get interactive element refs
agent-browser click @e1               # Click element
agent-browser fill @e2 "text"         # Fill input
agent-browser screenshot              # Take screenshot
agent-browser screenshot --annotate   # Annotated screenshot
agent-browser diff snapshot           # Compare to last snapshot
agent-browser wait --load networkidle # Wait for network idle
agent-browser eval 'expression'       # Run JS in browser
agent-browser close                   # Close browser
```

## Evidence Paths

| Artifact | Location |
|----------|----------|
| Screenshots | `test-results/screenshots/` |
| Evidence bundles | `test-results/evidence/` |
| Healing report | `test-results/healing-report.json` |
| HTML report | `playwright-report/` |
| JUnit XML | `test-results/junit.xml` |
| Traces | `test-results/` (on failure) |

## Config Defaults

```typescript
{
  selectorTimeout: 5000,        // 5s per selector attempt
  maxHealAttempts: 3,            // 3 healing attempts before fail
  visualDiffTolerance: 0.001,    // 0.1% pixel tolerance
  evidenceDir: 'test-results/evidence',
  reportDir: 'test-results',
}
```
