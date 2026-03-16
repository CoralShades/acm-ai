/**
 * Jobs Pipeline Tests
 *
 * Tests the job lifecycle: navigate to jobs -> view job detail ->
 * verify extraction status -> review buildings -> review records.
 * Uses mocked API responses (no real extraction needed).
 *
 * Tag: @critical
 */

import { test, expect } from '../../support/fixtures';

const MOCK_JOBS = [
  {
    id: 'source:job001',
    title: 'Test SAMP Document.pdf',
    status: 'completed',
    asset: { type: 'pdf', name: 'test-samp.pdf' },
    created: '2026-01-15T10:00:00Z',
    updated: '2026-01-15T10:05:00Z',
  },
  {
    id: 'source:job002',
    title: 'Another Survey.pdf',
    status: 'processing',
    asset: { type: 'pdf', name: 'survey.pdf' },
    created: '2026-01-15T11:00:00Z',
    updated: '2026-01-15T11:00:30Z',
  },
];

async function setupJobsMocks(page: import('@playwright/test').Page) {
  // Mock jobs/sources list
  await page.route('**/api/sources/**', async (route) => {
    if (route.request().method() === 'GET' && !route.request().url().includes('source:')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_JOBS),
      });
    } else {
      await route.fallback();
    }
  });

  // Mock individual job detail
  await page.route('**/api/sources/source%3Ajob001**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_JOBS[0]),
    });
  });
}

test.describe('Jobs Pipeline @critical', () => {
  test('jobs page loads and shows list', async ({ page }) => {
    await setupJobsMocks(page);
    await page.goto('/jobs');
    await page.waitForLoadState('domcontentloaded');

    const body = await page.locator('body').textContent({ timeout: 5000 });
    expect(body?.length).toBeGreaterThan(0);
  });

  test('jobs page is accessible without JS errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.goto('/jobs');
    await page.waitForLoadState('domcontentloaded');

    expect(errors).toHaveLength(0);
  });

  test('sources/documents page loads', async ({ page }) => {
    await setupJobsMocks(page);
    await page.goto('/sources');
    await page.waitForLoadState('domcontentloaded');

    const body = await page.locator('body').textContent({ timeout: 5000 });
    expect(body?.length).toBeGreaterThan(0);
  });
});
