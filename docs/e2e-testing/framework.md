# Self-Healing Framework Deep Dive

## Architecture

```
SelectorEngine  <-- config.ts (STRATEGY_CHAIN, DEFAULT_CONFIG)
     |
HealingPage (fixture)  <-- StateRecovery (HEALTHY -> DEGRADED -> STUCK -> FAILED)
     |
EvidenceCollector  -->  EvidenceBundle (JSON)
     |
HealingReporter  -->  healing-report.json (recommendations)
     |
APIContractValidator  -->  ContractValidation (drift detection)
```

All modules live in `tests/e2e/framework/self-healing/` with supporting utilities in `tests/e2e/framework/`.

---

## SelectorEngine

**File**: `tests/e2e/framework/self-healing/selector-engine.ts`

Tries multiple selector strategies in priority order to find elements, enabling tests to self-heal when selectors break due to UI changes.

### ElementContext

```typescript
interface ElementContext {
  originalSelector: string;  // The CSS selector that failed
  semanticRole?: string;     // ARIA role (button, textbox, link, etc.)
  textContent?: string;      // Visible text content
  ariaLabel?: string;        // aria-label attribute value
  testId?: string;           // data-testid attribute value
  parentContext?: string;    // Parent selector for scoping
}
```

### HealingResult

```typescript
interface HealingResult {
  locator: Locator;          // The resolved Playwright locator
  strategy: SelectorStrategy; // Which strategy succeeded
  confidence: number;        // 0.0 - 1.0
  suggestedFix?: string;     // Recommendation (e.g., "add data-testid")
  healingLog: string;        // Human-readable log entry
}
```

### API

```typescript
class SelectorEngine {
  constructor(config?: HealingConfig);

  // Resolve an element by trying each strategy in STRATEGY_CHAIN order.
  // Returns the first visible match. Throws if all strategies fail.
  async resolve(page: Page, context: ElementContext): Promise<HealingResult>;

  // Get all healing actions recorded during this session.
  getHealingLog(): HealingResult[];

  // Clear the healing log.
  clearLog(): void;
}
```

### Strategy Chain Resolution

For each strategy in `STRATEGY_CHAIN` (ordered by confidence):

1. Build a Playwright locator from the strategy + context
2. Check if the locator's first match is visible (1s timeout)
3. If visible: return `HealingResult` with the locator, strategy, and confidence
4. If not visible or error: try the next strategy
5. If all strategies fail: throw an error

Strategy-to-locator mapping:

| Strategy | Context Field Required | Locator Built |
|----------|----------------------|---------------|
| `data-testid` | `testId` | `page.locator('[data-testid="..."]')` |
| `role-name` | `semanticRole` | `page.getByRole(role, { name: textContent })` |
| `aria-label` | `ariaLabel` | `page.getByLabel(ariaLabel)` |
| `text-content` | `textContent` | `page.getByText(textContent)` |
| `css` | `originalSelector` | `page.locator(originalSelector)` |
| `xpath` | (skipped) | Always returns null (last resort only) |

---

## StateRecovery

**File**: `tests/e2e/framework/self-healing/state-recovery.ts`

Implements multi-level recovery when tests encounter stuck or degraded states.

### State Machine

```
HEALTHY  -->  DEGRADED (attempt 1: wait)
         -->  STUCK    (attempt 2: refresh)
         -->  RECOVERING (attempt 3: full reset)
         -->  FAILED   (attempt 4+: give up)
```

### RecoveryState Enum

```typescript
enum RecoveryState {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  STUCK = 'stuck',
  RECOVERING = 'recovering',
  FAILED = 'failed',
}
```

### API

```typescript
class StateRecovery {
  // Attempt recovery. Returns true if recovery succeeded.
  async recover(page: Page, url: string): Promise<boolean>;

  // Reset to HEALTHY state (call after successful navigation).
  reset(): void;

  // Get current state.
  getState(): RecoveryState;
}
```

### Recovery Levels

| Attempt | Level | Actions |
|---------|-------|---------|
| 1 | WAIT | `waitForTimeout(2000)` -- maybe just slow |
| 2 | REFRESH | `page.reload()` + `page.goto(url)` |
| 3 | RESET | Clear cookies + localStorage, navigate from `/`, then to `url` |
| 4+ | FAIL | Return `false` -- all levels exhausted |

---

## APIContractValidator

**File**: `tests/e2e/framework/self-healing/api-contract-validator.ts`

Validates API responses against expected field contracts to detect schema drift.

### KEY_CONTRACTS

```typescript
const KEY_CONTRACTS: Record<string, Record<string, string>> = {
  '/health':          { status: 'string' },
  '/notebooks/':      { '[].id': 'string', '[].name': 'string' },
  '/sources/':        { '[].id': 'string', '[].title': 'string' },
  '/models/':         { '[].name': 'string', '[].provider': 'string' },
  '/models/defaults': { chat_model: 'string' },
  '/acm/field-schema': { item_fields: 'object', building_fields: 'object' },
};
```

Array fields use `[].field` notation -- the response is expected to be an array and each item must have the specified field.

### ContractValidation

```typescript
interface ContractValidation {
  valid: boolean;             // true if no missing fields or type mismatches
  endpoint: string;
  missingFields: string[];    // Fields in contract but not in response
  extraFields: string[];      // Fields in response but not in contract
  typeMismatches: Array<{
    field: string;
    expected: string;         // e.g., 'string'
    actual: string;           // e.g., 'number'
  }>;
}
```

### DriftReport

```typescript
interface DriftReport {
  endpoint: string;
  validations: ContractValidation[];
  hasDrift: boolean;
}
```

### API

```typescript
class APIContractValidator {
  // Validate a parsed response object against expected fields.
  validate(
    response: Record<string, unknown>,
    expectedFields: Record<string, string>,
    endpoint: string
  ): ContractValidation;

  // Fetch an endpoint and validate its response.
  async validateEndpoint(
    apiBase: string,
    endpoint: string,
    expectedFields: Record<string, string>,
    fetchFn: (url: string) => Promise<unknown>
  ): Promise<ContractValidation>;
}
```

---

## EvidenceCollector

**File**: `tests/e2e/framework/self-healing/evidence-collector.ts`

Captures screenshots, console logs, and network requests during test runs.

### EvidenceBundle

```typescript
interface EvidenceBundle {
  testName: string;
  timestamp: string;
  screenshots: string[];       // Absolute paths to screenshot files
  consoleLogs: Array<{
    level: string;             // 'log', 'error', 'warning', etc.
    text: string;
    url: string;
  }>;
  networkRequests: Array<{
    url: string;
    method: string;            // 'GET', 'POST', etc.
    status: number;            // HTTP status code
    timing: number;            // Duration in milliseconds
  }>;
  domSnapshot?: string;
}
```

### Lifecycle

```typescript
// 1. Create and attach to page (in fixture setup)
const collector = new EvidenceCollector();
collector.attach(page);   // Starts listening to console + network events

// 2. Capture during test
const screenshot = await collector.captureScreenshot(page, 'step-name');
const bundle = await collector.captureEvidence(page, 'test-name');
const filepath = collector.save(bundle);  // Save bundle as JSON

// 3. Detach (in fixture teardown)
collector.detach();  // Clears logs, stops listening
```

### Save Paths

- Screenshots: `test-results/evidence/{name}-{timestamp}.png`
- Evidence JSON: `test-results/evidence/evidence-{testName}-{timestamp}.json`

---

## HealingReporter

**File**: `tests/e2e/framework/self-healing/healing-reporter.ts`

Aggregates test results, healing actions, and route coverage into a structured report.

### HealingReport

```typescript
interface HealingReport {
  timestamp: string;
  totalTests: number;
  passed: number;
  failed: number;
  healed: number;
  skipped: number;
  healingActions: HealingResult[];
  recommendations: Array<{
    type: string;              // 'add-testid', 'fragile-selector', 'missing-coverage', 'broken-route'
    message: string;
    file?: string;
    selector?: string;
  }>;
  routeCoverage: Record<string, 'tested' | 'untested' | 'failed'>;
}
```

### Recommendation Types

| Type | Meaning |
|------|---------|
| `add-testid` | A selector was healed via non-ideal strategy; add `data-testid` |
| `fragile-selector` | A selector resolved with confidence < 0.7 |
| `missing-coverage` | A route has no E2E test coverage |
| `broken-route` | A route is failing tests |

### API

```typescript
class HealingReporter {
  // Record a test result.
  addResult(testName: string, status: 'passed'|'failed'|'healed'|'skipped',
            healingActions?: HealingResult[], evidence?: EvidenceBundle): void;

  // Record route coverage status.
  addRouteCoverage(route: string, status: 'tested'|'untested'|'failed'): void;

  // Generate the full report.
  generateReport(): HealingReport;

  // Save report to disk. Returns absolute path.
  saveReport(outputDir?: string): string;

  // Get recommendations from healing actions and route coverage.
  getRecommendations(): Array<{ type: string; message: string; file?: string; selector?: string }>;
}
```

---

## RouteWalker

**File**: `tests/e2e/framework/route-walker.ts`

Walks all known application routes and reports their status, JS errors, and load times.

### Route Lists

**Static routes** (24): `/`, `/notebooks`, `/sources`, `/documents`, `/acm`, `/search`, `/settings`, `/settings/models`, `/settings/field-mapping`, `/settings/field-schema`, `/settings/extraction`, `/settings/processing`, `/settings/bar-templates`, `/settings/parsers`, `/upload`, `/jobs`, `/extraction-monitor`, `/models`, `/podcasts`, `/transformations`, `/advanced`, `/test-grid`, `/landing`, `/login`

**Dynamic routes** (4): `/notebooks/notebook:test`, `/sources/source:test`, `/source/source:test`, `/jobs/source:test`

### RouteWalkResult

```typescript
interface RouteWalkResult {
  route: string;
  status: 'ok' | 'error' | 'redirect' | 'not-found';
  statusCode?: number;
  jsErrors: string[];
  loadTime: number;          // Milliseconds
  title?: string;
}
```

### API

```typescript
class RouteWalker {
  // Walk all routes (static + dynamic).
  async walkAll(page: Page, options?: {
    skipDynamic?: boolean;
    timeout?: number;
  }): Promise<RouteWalkResult[]>;

  // Walk a single route.
  async walkRoute(page: Page, route: string, timeout?: number): Promise<RouteWalkResult>;

  // Get route lists.
  getStaticRoutes(): string[];
  getDynamicRoutes(): string[];
}
```

---

## Accessibility

**File**: `tests/e2e/framework/accessibility.ts`

Wraps `@axe-core/playwright` for WCAG 2.1 AA audits with graceful fallback when axe-core is not installed.

### AccessibilityViolation

```typescript
interface AccessibilityViolation {
  id: string;                  // e.g., 'color-contrast', 'label'
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  helpUrl: string;             // Link to axe rule documentation
  nodes: Array<{
    html: string;              // The offending HTML element
    target: string[];          // CSS selectors to the element
  }>;
}
```

### AccessibilityAuditResult

```typescript
interface AccessibilityAuditResult {
  route: string;
  violations: AccessibilityViolation[];
  passes: number;
  incomplete: number;
}
```

### API

```typescript
// Run WCAG 2.1 AA audit on current page.
async function auditPage(
  page: Page,
  route: string,
  options?: { tags?: string[] }  // Default: ['wcag2a', 'wcag2aa']
): Promise<AccessibilityAuditResult>;

// Filter to critical + serious violations only.
function getCriticalViolations(
  result: AccessibilityAuditResult
): AccessibilityViolation[];
```

---

## Config

**File**: `tests/e2e/framework/self-healing/config.ts`

### Enums

```typescript
enum SelectorStrategy {
  DATA_TESTID = 'data-testid',
  ROLE_NAME   = 'role-name',
  ARIA_LABEL  = 'aria-label',
  TEXT_CONTENT = 'text-content',
  CSS         = 'css',
  XPATH       = 'xpath',
}

enum RecoveryLevel {
  WAIT    = 'wait',
  REFRESH = 'refresh',
  RESET   = 'reset',
  FAIL    = 'fail',
}
```

### STRATEGY_CHAIN

```typescript
const STRATEGY_CHAIN: StrategyPriority[] = [
  { strategy: SelectorStrategy.DATA_TESTID,  confidence: 1.0  },
  { strategy: SelectorStrategy.ROLE_NAME,    confidence: 0.95 },
  { strategy: SelectorStrategy.ARIA_LABEL,   confidence: 0.9  },
  { strategy: SelectorStrategy.TEXT_CONTENT,  confidence: 0.8  },
  { strategy: SelectorStrategy.CSS,          confidence: 0.6  },
  { strategy: SelectorStrategy.XPATH,        confidence: 0.4  },
];
```

### DEFAULT_CONFIG

```typescript
const DEFAULT_CONFIG: HealingConfig = {
  selectorTimeout: 5000,        // 5s per selector attempt
  maxHealAttempts: 3,            // Max healing retries
  visualDiffTolerance: 0.001,    // 0.1% pixel mismatch tolerance
  recoveryLevels: [WAIT, REFRESH, RESET, FAIL],
  evidenceDir: 'test-results/evidence',
  reportDir: 'test-results',
};
```
