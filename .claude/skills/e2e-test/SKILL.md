---
name: e2e-test
description: Self-Healing E2E Testing Workflow for ACM-AI. Runs Playwright tests with autonomous failure recovery, selector healing, API contract validation, and evidence collection. Integrates with agent-browser and chrome-devtools MCP.
---

# Self-Healing E2E Testing Workflow

## When to Use
- After implementing frontend/backend changes to verify nothing broke
- Before marking a story as complete (verification protocol)
- When running full regression testing
- When investigating reported UI bugs
- When validating accessibility compliance

## Quick Start

### Run Tests by Tier
```bash
npx playwright test --project=smoke             # Tier 1: <30s, all pages load
npx playwright test --project=critical          # Tier 2: <5min, core workflows
npx playwright test --project=feature           # Tier 3: <15min, feature tests
npx playwright test --project=accessibility     # Accessibility audits
npx playwright test                             # Full suite
```

### Tag-Based Execution
```bash
npx playwright test --grep @smoke              # Smoke tests only
npx playwright test --grep @critical           # Critical path tests
npx playwright test --grep @feature            # Feature tests
npx playwright test --grep @a11y               # Accessibility audits
npx playwright test --grep "@api-contracts"    # API contract validation
```

## Self-Healing Workflow (6 Phases)

1. **Parallel Research**: Analyze changed files, identify affected routes & APIs
2. **Test Selection**: Choose relevant test tier based on change scope
3. **Execute with Healing**: Run tests with selector fallback + state recovery
4. **Evidence Collection**: Screenshots, console logs, network traces on failure
5. **Auto-Fix (up to 3 attempts)**: If test fails due to code issue:
   a. Analyze failure (selector drift? API change? missing element?)
   b. Apply fix (add data-testid, update selector, fix component)
   c. Re-run failed test
6. **Report**: Generate healing report with recommendations

## Framework Architecture

```
tests/e2e/framework/
  self-healing/
    config.ts              # Thresholds, strategy chain, recovery levels
    selector-engine.ts     # Multi-strategy selector resolution
    state-recovery.ts      # Stuck-state recovery state machine
    api-contract-validator.ts  # API response shape validation
    evidence-collector.ts  # Screenshot, console, network evidence
    healing-reporter.ts    # Aggregated healing report
  route-walker.ts          # Automated route walking utility
  accessibility.ts         # axe-core WCAG 2.1 AA wrapper

tests/support/fixtures/
  self-healing.ts          # HealingPage, EvidenceCollector fixtures

tests/e2e/specs/
  smoke-walker.spec.ts     # @smoke - Route walking
  api-contracts.spec.ts    # @smoke @api-contracts - API shapes
  settings-pages.spec.ts   # @feature - Settings sub-pages
  upload-wizard.spec.ts    # @critical - Upload wizard flow
  jobs-pipeline.spec.ts    # @critical - Job lifecycle
  building-detail.spec.ts  # @feature - Building detail page
  accessibility.spec.ts    # @a11y - WCAG audits
```

## Test Tiers

| Tier | Project | Trigger | Timeout | Coverage |
|------|---------|---------|---------|----------|
| Smoke | `smoke` | Every PR | <30s | Route walking, API health |
| Critical | `critical` | Merges to main | <5min | Upload wizard, jobs pipeline |
| Feature | `feature` | Nightly | <15min | Settings, building detail |
| A11y | `accessibility` | Nightly | <5min | WCAG 2.1 AA audits |

## Integration with Agent-Browser

The self-healing workflow uses `agent-browser` for interactive debugging, visual verification, and state comparison. See `.claude/skills/agent-browser/SKILL.md` for full command reference.

### Core Debugging Workflow
```bash
# 1. Navigate to the failing page
agent-browser open http://localhost:8503/source/source%3Atest001

# 2. Get interactive element refs
agent-browser snapshot -i
# Output: @e1 [button] "Main Block", @e2 [input] "Search records...", @e3 [button] "Group by Room"

# 3. Interact using refs
agent-browser click @e1              # Click building in sidebar
agent-browser fill @e2 "asbestos"    # Type in search
agent-browser wait --load networkidle

# 4. Re-snapshot after page changes (refs are invalidated)
agent-browser snapshot -i

# 5. Visual comparison
agent-browser screenshot --annotate   # Numbered element labels on screenshot
agent-browser diff snapshot           # See what changed since last snapshot
```

### Visual Regression Testing
```bash
# Save baseline before changes
agent-browser open http://localhost:8503/acm && agent-browser wait --load networkidle
agent-browser screenshot baseline-acm.png

# After code changes, compare
agent-browser open http://localhost:8503/acm && agent-browser wait --load networkidle
agent-browser diff screenshot --baseline baseline-acm.png
# Output: mismatch percentage and diff image with changed pixels in red
```

### Page-by-Page Verification
```bash
# Verify upload wizard steps
agent-browser open http://localhost:8503/upload
agent-browser snapshot -i
# Look for: @eN [input type="file"], @eN [button] "Upload"

# Verify settings pages
agent-browser open http://localhost:8503/settings/models
agent-browser snapshot -i
# Look for: form inputs, save buttons

# Verify ACM register
agent-browser open http://localhost:8503/source/source%3Atest
agent-browser snapshot -i -C          # Include cursor-interactive elements (AG Grid cells)
```

### Failure Investigation Pattern
```bash
# When a Playwright test fails:
# 1. Open the exact URL that failed
agent-browser open http://localhost:8503/source/source%3Atest001

# 2. Check for the missing element
agent-browser snapshot -i -s "[data-testid='item-grid']"
# If empty: element is missing or has wrong testid

# 3. Get full page text for debugging
agent-browser get text body > /tmp/page-content.txt

# 4. Check console errors
agent-browser eval 'JSON.stringify(window.__e2e_errors || [])'

# 5. Take annotated screenshot as evidence
agent-browser screenshot --annotate --full test-results/evidence/failure.png
```

### Data Extraction for Test Verification
```bash
# Extract AG Grid row count
agent-browser eval 'document.querySelectorAll(".ag-row").length'

# Extract building sidebar items
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('[data-testid="building-sidebar"] button'))
    .map(b => b.textContent?.trim())
)
EVALEOF

# Check network requests made by the page
agent-browser eval 'JSON.stringify(performance.getEntriesByType("resource").filter(r => r.name.includes("/api/")).map(r => r.name))'
```

### Responsive Testing
```bash
# Test at different viewports
agent-browser open http://localhost:8503 --viewport 1280x720   # Desktop
agent-browser screenshot desktop.png
agent-browser open http://localhost:8503 --viewport 768x1024   # Tablet
agent-browser screenshot tablet.png
agent-browser open http://localhost:8503 --viewport 375x667    # Mobile
agent-browser screenshot mobile.png
```

## Selector Strategy Chain

When a selector fails, the engine tries alternatives in priority order:

| Priority | Strategy | Confidence | Example |
|----------|----------|------------|---------|
| 1 | data-testid | 1.0 | `[data-testid="acm-grid"]` |
| 2 | role+name | 0.95 | `getByRole('button', { name: 'Submit' })` |
| 3 | aria-label | 0.9 | `getByLabel('Search records')` |
| 4 | text content | 0.8 | `getByText('Upload')` |
| 5 | CSS selector | 0.6 | `.ag-row` |
| 6 | XPath | 0.4 | `//div[@class="grid"]` |

## State Recovery Levels

When a test gets stuck, recovery escalates:

1. **WAIT**: Extend timeout, poll slower (2s delay)
2. **REFRESH**: `page.reload()` + re-navigate to URL
3. **RESET**: Clear cookies/localStorage, navigate from `/`
4. **FAIL**: Mark test as failed after 3 attempts

## Evidence Artifacts

On test failure, evidence is automatically collected:
- Screenshots: `test-results/evidence/{testName}/screenshot.png`
- Console logs: `test-results/evidence/{testName}.json`
- Network requests: included in evidence JSON
- Healing report: `test-results/healing-report.json`
- Playwright report: `playwright-report/`
- JUnit XML: `test-results/junit.xml`

## API Contract Validation

Key endpoints validated for response shape:
- `GET /api/health` - status field
- `GET /api/notebooks/` - array with id, name
- `GET /api/sources/` - array with id, title
- `GET /api/models/` - array with name, provider
- `GET /api/models/defaults` - chat_model field
- `GET /api/acm/field-schema` - item_fields, building_fields objects

## Known Considerations

- **Port 8503**: Frontend dev server runs on 8503 (not 8502)
- **AG Grid virtual DOM**: Rows off-screen need scroll-into-view before assertions
- **AI-dependent tests**: Use mock route interception for CI (no real LLM)
- **axe-core**: Start with critical-only assertions, track improvement
- **Windows paths**: Use forward slashes and `$CLAUDE_PROJECT_DIR`
