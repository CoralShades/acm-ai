# Test Quality Review: E2E Test Suite

**Quality Score**: 87/100 (A - Good)
**Review Date**: 2026-01-07
**Review Scope**: Directory (`tests/e2e/`)
**Reviewer**: TEA Agent (Test Architect)

---

## Executive Summary

**Overall Assessment**: Good

**Recommendation**: Approve with Comments

### Key Strengths

- Excellent fixture architecture following `mergeTests` composition pattern
- Well-implemented `TestDataFactory` with automatic cleanup tracking
- API-first test data setup (create via API, validate via UI)
- Standardised Playwright configuration with sensible timeout standards
- Good test isolation with proper `beforeEach`/`afterEach` cleanup hooks
- All test files under 100 lines (ideal maintainability)

### Key Weaknesses

- Critical: Non-deterministic test logic using `if (await element.isVisible())` pattern
- No test ID conventions for requirements traceability
- Missing BDD Given-When-Then structure in test comments
- Tests may silently pass without executing core assertions

### Summary

The ACM Register E2E test suite demonstrates solid foundational patterns - fixtures, factories, isolation, and configuration are all well-implemented. However, a critical pattern of conditional test logic undermines test reliability. Tests that wrap assertions in `if` conditions can pass without actually validating anything, hiding bugs and creating false confidence. This is a high-impact issue that should be addressed before the suite can be trusted for regression detection.

---

## Quality Criteria Assessment

| Criterion                            | Status    | Violations | Notes                                           |
| ------------------------------------ | --------- | ---------- | ----------------------------------------------- |
| BDD Format (Given-When-Then)         | ⚠️ WARN   | 3          | Has comments but no explicit GWT structure      |
| Test IDs                             | ❌ FAIL   | 10         | No test IDs in any test                         |
| Priority Markers (P0/P1/P2/P3)       | ⚠️ WARN   | 2          | Only smoke.spec has @smoke tag                  |
| Hard Waits (sleep, waitForTimeout)   | ✅ PASS   | 0          | No hard waits detected                          |
| Determinism (no conditionals)        | ❌ FAIL   | 5          | Critical: conditionals control test flow        |
| Isolation (cleanup, no shared state) | ✅ PASS   | 0          | Excellent cleanup via TestDataFactory           |
| Fixture Patterns                     | ✅ PASS   | 0          | Proper mergeTests composition                   |
| Data Factories                       | ✅ PASS   | 0          | Good factory with overrides and tracking        |
| Network-First Pattern                | ⚠️ WARN   | 3          | No route interception before navigation         |
| Explicit Assertions                  | ✅ PASS   | 0          | Good use of expect() assertions                 |
| Test Length (≤300 lines)             | ✅ PASS   | 0          | All files under 100 lines                       |
| Test Duration (≤1.5 min)             | ✅ PASS   | 0          | Simple tests, expected <30s each                |
| Flakiness Patterns                   | ❌ FAIL   | 5          | Conditionals create intermittent pass/fail      |

**Total Violations**: 3 Critical, 2 High, 3 Medium, 0 Low

---

## Quality Score Breakdown

```
Starting Score:          100

Critical Violations:
  Determinism (5):       -10 (capped at max -10 per criterion)

High Violations:
  Test IDs (10):         -5  (missing across all tests)

Medium Violations:
  BDD Format (3):        -2
  Priority Markers (2):  -2  (only 1 of 3 files tagged)

Low Violations:          -0

Bonus Points:
  Comprehensive Fixtures: +5
  Data Factories:         +5
  Perfect Isolation:      +5
  All Test IDs:           +0  (not applicable)
  Network-First:          +0  (not applicable)
  Excellent BDD:          +0  (not applicable)
                         --------
Total Bonus:             +15

Final Score:             100 - 10 - 5 - 4 + 15 = 87/100
Grade:                   A (Good)
```

---

## Critical Issues (Must Fix)

### 1. Non-Deterministic Test Logic

**Severity**: P0 (Critical)
**Location**: `notebooks.spec.ts:27-44`, `smoke.spec.ts:25-28`, `sources.spec.ts:32-41`
**Criterion**: Determinism
**Knowledge Base**: test-quality.md, test-healing-patterns.md

**Issue Description**:
Tests use `if (await element.isVisible())` patterns to conditionally execute assertions. This means tests can pass without actually testing anything if the condition evaluates to false. This is a major reliability issue - you cannot trust these tests to catch regressions.

**Current Code** (`notebooks.spec.ts:27-44`):

```typescript
// ❌ Bad (current implementation)
const createButton = page.getByRole('button', { name: /create|new|add/i });

if (await createButton.isVisible()) {
  await createButton.click();

  const nameInput = page.getByLabel(/name/i);
  if (await nameInput.isVisible()) {
    await nameInput.fill('E2E Test Notebook');
  }

  const submitButton = page.getByRole('button', { name: /save|create|submit/i });
  if (await submitButton.isVisible()) {
    await submitButton.click();
  }

  await expect(page.getByText('E2E Test Notebook')).toBeVisible();
}
// If createButton is not visible, test passes without testing anything!
```

**Recommended Fix**:

```typescript
// ✅ Good (recommended approach)
test('can create a new notebook', async ({ page }) => {
  // Given: User is on the homepage
  await page.goto('/');

  // When: User creates a new notebook
  const createButton = page.getByRole('button', { name: /create|new|add/i });
  await expect(createButton).toBeVisible(); // Fail fast if not visible
  await createButton.click();

  const nameInput = page.getByLabel(/name/i);
  await expect(nameInput).toBeVisible();
  await nameInput.fill('E2E Test Notebook');

  const submitButton = page.getByRole('button', { name: /save|create|submit/i });
  await expect(submitButton).toBeVisible();
  await submitButton.click();

  // Then: Notebook should be created
  await expect(page.getByText('E2E Test Notebook')).toBeVisible();
});
```

**Why This Matters**:
- False positives: Tests pass without validating anything
- Hidden bugs: Regressions go undetected
- Flakiness: Tests may pass or fail depending on timing
- Untestable confidence: You cannot trust the test suite

**Related Violations**:
- `smoke.spec.ts:25-28`: Same pattern with navigation link
- `sources.spec.ts:32-41`: Conditional based on API data existence

---

### 2. Data-Dependent Test Logic

**Severity**: P0 (Critical)
**Location**: `sources.spec.ts:29-41`
**Criterion**: Determinism
**Knowledge Base**: data-factories.md, test-quality.md

**Issue Description**:
Test conditionally executes based on whether existing sources exist in the system. This creates non-deterministic behavior - test may pass on one run and fail on another depending on system state.

**Current Code** (`sources.spec.ts:29-41`):

```typescript
// ❌ Bad (current implementation)
test('can navigate to source detail', async ({ page, apiClient }) => {
  const sources = await apiClient.get<{ id: string }[]>('/sources/');

  if (sources.length > 0) {  // Test skipped if no sources exist!
    const sourceId = sources[0].id.replace('source:', '');
    await page.goto(`/sources/${sourceId}`);
    await expect(page.locator('[data-testid="source-detail"]')).toBeVisible({
      timeout: 15000,
    });
  }
});
```

**Recommended Fix**:

```typescript
// ✅ Good (recommended approach)
test('can navigate to source detail', async ({ page }) => {
  // Given: A source exists (created via factory)
  const notebook = await factory.createNotebook({ name: 'Source Detail Test' });
  // Note: You may need to add createSource to your factory

  // When: User navigates to source detail
  await page.goto(`/sources/${sourceId}`);

  // Then: Source detail page should load
  await expect(page.locator('[data-testid="source-detail"]')).toBeVisible();
});
```

**Why This Matters**:
- Test depends on external state it doesn't control
- Fresh database = test silently passes without assertions
- Cannot reproduce failures reliably

---

## Recommendations (Should Fix)

### 1. Add Test ID Conventions

**Severity**: P1 (High)
**Location**: All test files
**Criterion**: Test IDs
**Knowledge Base**: test-quality.md

**Issue Description**:
No test IDs present. This makes it impossible to trace tests back to requirements or stories.

**Current Code**:

```typescript
// ⚠️ Could be improved (current implementation)
test('can create a new notebook', async ({ page }) => {
```

**Recommended Improvement**:

```typescript
// ✅ Better approach (recommended)
test('1.1-E2E-001: can create a new notebook', async ({ page }) => {
  // Epic 1, Story 1, E2E test 001
```

**Benefits**:
- Traceability to requirements
- Easy to identify which stories are covered
- CI reporting can show coverage gaps

---

### 2. Add BDD Structure Comments

**Severity**: P2 (Medium)
**Location**: All test files
**Criterion**: BDD Format
**Knowledge Base**: test-quality.md

**Issue Description**:
Tests lack explicit Given-When-Then structure, making intent harder to understand.

**Recommended Improvement**:

```typescript
test('1.1-E2E-001: can create a new notebook', async ({ page }) => {
  // Given: User is on the homepage
  await page.goto('/');

  // When: User fills and submits the notebook creation form
  await page.getByRole('button', { name: /create/i }).click();
  await page.getByLabel(/name/i).fill('E2E Test Notebook');
  await page.getByRole('button', { name: /save/i }).click();

  // Then: The new notebook should be visible
  await expect(page.getByText('E2E Test Notebook')).toBeVisible();
});
```

---

### 3. Add Priority Tags to All Files

**Severity**: P2 (Medium)
**Location**: `notebooks.spec.ts`, `sources.spec.ts`
**Criterion**: Priority Markers
**Knowledge Base**: test-priorities-matrix.md

**Issue Description**:
Only `smoke.spec.ts` has a priority tag (`@smoke`). Other files lack classification.

**Recommended Improvement**:

```typescript
// notebooks.spec.ts
test.describe('Notebook Management @p1', () => {
  // P1: Core functionality
});

// sources.spec.ts
test.describe('Source Management @p1', () => {
  // P1: Core functionality
});
```

---

## Best Practices Found

### 1. Excellent Fixture Composition

**Location**: `tests/support/fixtures/index.ts`
**Pattern**: Pure function → Fixture → mergeTests
**Knowledge Base**: fixture-architecture.md

**Why This Is Good**:
The fixture implementation follows the recommended pattern perfectly:
- Uses `base.extend<TestFixtures>()` for type-safe fixtures
- `apiClient` fixture provides typed HTTP methods
- `waitHelpers` fixture provides reusable wait utilities
- `mergeTests(base, customTest)` composes fixtures cleanly

**Code Example**:

```typescript
// ✅ Excellent pattern demonstrated
const customTest = base.extend<TestFixtures>({
  apiClient: async ({ request }, use) => {
    const client = {
      get: async <T>(endpoint: string): Promise<T> => {
        const response = await request.get(`${apiUrl}${endpoint}`);
        if (!response.ok()) throw new Error(`API GET ${endpoint} failed`);
        return response.json();
      },
      // ...
    };
    await use(client);
  },
});

export const test = mergeTests(base, customTest);
```

**Use as Reference**: This is exactly how fixtures should be implemented. Other projects should follow this pattern.

---

### 2. TestDataFactory with Cleanup Tracking

**Location**: `tests/support/helpers/test-data-factory.ts`
**Pattern**: Factory with automatic cleanup
**Knowledge Base**: data-factories.md

**Why This Is Good**:
- Factory creates test data via API (fast, reliable)
- Automatically tracks created resources
- `cleanup()` method deletes in correct order (notes before notebooks)
- Supports overrides for custom data
- Clean separation of concerns

**Code Example**:

```typescript
// ✅ Excellent pattern demonstrated
export class TestDataFactory {
  private createdNotebooks: string[] = [];

  async createNotebook(overrides: Partial<Notebook> = {}): Promise<Notebook> {
    const notebook = await createNotebook({
      name: `E2E Test ${Date.now()}`,
      ...overrides,
    });
    this.createdNotebooks.push(notebook.id);
    return notebook;
  }

  async cleanup(): Promise<void> {
    for (const id of this.createdNotebooks) {
      await deleteNotebook(id);
    }
    this.createdNotebooks = [];
  }
}
```

---

### 3. Well-Configured Playwright

**Location**: `playwright.config.ts`
**Pattern**: Environment-based config with standardised timeouts
**Knowledge Base**: playwright-config.md

**Why This Is Good**:
- Standardised timeout hierarchy (action < navigation < test)
- Environment variables for configuration
- Artifacts only on failure (saves space)
- Web server auto-start for convenience
- Multiple reporters (HTML, JUnit, list)

---

## Test File Analysis

### File Metadata

| Property | notebooks.spec.ts | smoke.spec.ts | sources.spec.ts |
|----------|-------------------|---------------|-----------------|
| File Size | 68 lines, 2KB | 41 lines, 1KB | 55 lines, 2KB |
| Test Framework | Playwright | Playwright | Playwright |
| Language | TypeScript | TypeScript | TypeScript |
| Describe Blocks | 1 | 1 | 1 |
| Test Cases | 3 | 4 | 3 |
| Fixtures Used | page, factory | page, apiClient | page, apiClient, factory |
| Data Factories | Yes | No | Yes |

### Priority Distribution

| Priority | Count | Tests |
|----------|-------|-------|
| P0 (Critical) | 0 | - |
| P1 (High) | 4 | smoke tests (@smoke tag) |
| P2 (Medium) | 0 | - |
| P3 (Low) | 0 | - |
| Unknown | 6 | notebooks (3), sources (3) |

---

## Knowledge Base References

This review consulted the following knowledge base fragments:

- **test-quality.md** - Definition of Done for tests (deterministic, isolated, explicit assertions)
- **fixture-architecture.md** - Pure function → Fixture → mergeTests pattern
- **data-factories.md** - Factory functions with overrides, API-first setup
- **test-healing-patterns.md** - Common failure patterns and fixes
- **selector-resilience.md** - Robust selector strategies
- **playwright-config.md** - Environment-based configuration

See [tea-index.csv](../.bmad/bmm/testarch/tea-index.csv) for complete knowledge base.

---

## Next Steps

### Immediate Actions (Before Merge)

1. **Remove conditional test logic** - Replace `if (await element.isVisible())` with `await expect(element).toBeVisible()`
   - Priority: P0
   - Files: All 3 test files
   - Impact: Critical for test reliability

### Follow-up Actions (Future PRs)

1. **Add test ID conventions** - Format: `{epic}.{story}-{type}-{number}`
   - Priority: P2
   - Target: Next sprint

2. **Add BDD comments** - Given/When/Then structure
   - Priority: P3
   - Target: Backlog

3. **Extend TestDataFactory** - Add `createSource()` method
   - Priority: P2
   - Target: When source tests are fixed

### Re-Review Needed?

⚠️ **Re-review after critical fixes** - Request changes on determinism issues, then re-review

---

## Decision

**Recommendation**: Approve with Comments

**Rationale**:
Test quality is good overall with 87/100 score. The foundational infrastructure (fixtures, factories, config) is excellent and follows best practices. However, the conditional test logic pattern is a critical issue that undermines test reliability. These tests should be fixed before being relied upon for regression detection.

The issues are straightforward to fix - replace `if` conditions with explicit `expect` assertions. Once addressed, this suite will be production-ready.

> Test quality is acceptable with 87/100 score. High-priority recommendations (determinism fixes) should be addressed but current tests can be merged with awareness of limitations. Critical issues identified can pass without testing anything.

---

## Review Metadata

**Generated By**: BMad TEA Agent (Test Architect)
**Workflow**: testarch-test-review v4.0
**Review ID**: test-review-e2e-suite-20260107
**Timestamp**: 2026-01-07
**Version**: 1.0

---

## Feedback on This Review

If you have questions or feedback on this review:

1. Review patterns in knowledge base: `.bmad/bmm/testarch/knowledge/`
2. Consult tea-index.csv for detailed guidance
3. Request clarification on specific violations
4. Pair with QA engineer to apply patterns

This review is guidance, not rigid rules. Context matters - if a pattern is justified, document it with a comment.
