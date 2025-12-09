# Open Notebook Test Suite

This directory contains all tests for Open Notebook, organized by type.

## Structure

```
tests/
├── e2e/                    # End-to-end Playwright tests
│   ├── smoke.spec.ts       # Quick smoke tests (run first)
│   ├── notebooks.spec.ts   # Notebook CRUD operations
│   └── sources.spec.ts     # Source management tests
├── support/                # Test infrastructure
│   ├── fixtures/           # Playwright fixtures (mergeTests pattern)
│   │   └── index.ts        # Main fixture exports
│   ├── helpers/            # Pure utility functions
│   │   ├── api-helpers.ts  # API interaction helpers
│   │   └── test-data-factory.ts  # Test data creation
│   └── page-objects/       # Page object models (optional)
├── conftest.py             # Python pytest configuration
├── test_*.py               # Python unit/integration tests
└── README.md               # This file
```

## Quick Start

### Prerequisites

1. **Backend running** (SurrealDB + FastAPI):
   ```bash
   make start-all
   # Or manually:
   docker compose up -d surrealdb
   uv run run_api.py
   ```

2. **Install Playwright** (first time only):
   ```bash
   npx playwright install --with-deps chromium
   ```

### Running E2E Tests

```bash
# Run all E2E tests
npx playwright test

# Run smoke tests only (fast)
npx playwright test --grep @smoke

# Run with UI (visual debugging)
npx playwright test --ui

# Run headed (see browser)
npx playwright test --headed

# Run specific file
npx playwright test tests/e2e/notebooks.spec.ts

# Debug mode (pause on failure)
npx playwright test --debug
```

### Running Python Tests

```bash
# All Python tests
uv run pytest

# With coverage
uv run pytest --cov=open_notebook

# Specific file
uv run pytest tests/test_domain.py
```

## Architecture

### Fixture Pattern (Pure Functions + mergeTests)

```typescript
// 1. Pure function (tests/support/helpers/api-helpers.ts)
export async function createNotebook(data) {
  // Framework-agnostic, unit-testable
  return fetch('/api/notebooks', { method: 'POST', body: data });
}

// 2. Fixture wrapper (tests/support/fixtures/index.ts)
export const test = base.extend({
  apiClient: async ({ request }, use) => {
    await use({ get, post, put, delete });
  },
});

// 3. Test usage
import { test, expect } from '../support/fixtures';

test('my test', async ({ page, apiClient }) => {
  const data = await apiClient.get('/notebooks/');
});
```

### Test Data Factory (Auto-Cleanup)

```typescript
import { TestDataFactory } from '../support/helpers/test-data-factory';

test.describe('My Tests', () => {
  let factory: TestDataFactory;

  test.beforeEach(() => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup(); // Deletes all created data
  });

  test('creates notebook', async () => {
    const notebook = await factory.createNotebook({ name: 'Test' });
    // notebook tracked for cleanup
  });
});
```

## Configuration

### Environment Variables

```bash
# .env (copy from .env.example)
BASE_URL=http://localhost:8502      # Frontend URL
API_URL=http://localhost:5055/api   # Backend API
TEST_ENV=local                      # Environment: local|staging|production
```

### Timeout Standards

| Type       | Timeout | Description                    |
|------------|---------|--------------------------------|
| Action     | 15s     | click, fill, type              |
| Navigation | 30s     | goto, reload                   |
| Expect     | 10s     | assertions                     |
| Test       | 60s     | full test timeout              |

## Best Practices

### Selectors

Use `data-testid` attributes for stable selectors:

```typescript
// Good
await page.getByTestId('create-notebook-button').click();

// Avoid
await page.click('.btn.btn-primary.new-notebook');
```

### Test Isolation

Each test should:
1. Create its own test data
2. Clean up after itself
3. Not depend on other tests

### API-First Setup

Use API calls for test setup (faster than UI):

```typescript
// Fast: API setup
const notebook = await factory.createNotebook({ name: 'Test' });
await page.goto(`/notebooks/${notebook.id}`);

// Slow: UI setup
await page.goto('/notebooks');
await page.click('[data-testid="create"]');
await page.fill('[data-testid="name"]', 'Test');
await page.click('[data-testid="save"]');
```

## CI Integration

Tests run on push/PR via GitHub Actions. Artifacts (screenshots, videos, traces) are uploaded on failure.

```yaml
# .github/workflows/e2e.yml
- name: Run E2E tests
  run: npx playwright test
  env:
    TEST_ENV: staging

- name: Upload artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-report
    path: playwright-report/
```

## Knowledge Base References

- **Fixture Architecture**: `testarch/knowledge/fixture-architecture.md`
- **Playwright Config**: `testarch/knowledge/playwright-config.md`
- **Data Factories**: `testarch/knowledge/data-factories.md`
- **Test Quality**: `testarch/knowledge/test-quality.md`

## Troubleshooting

### Tests timeout

1. Check backend is running: `curl http://localhost:5055/api/health`
2. Check frontend is running: `curl http://localhost:8502`
3. Increase timeout in `playwright.config.ts`

### Flaky tests

1. Use `test.describe.configure({ mode: 'serial' })` for dependent tests
2. Add explicit waits: `await page.waitForLoadState('networkidle')`
3. Use data-testid selectors (more stable than CSS)

### Browser not found

```bash
npx playwright install --with-deps chromium
```
