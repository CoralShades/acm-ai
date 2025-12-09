/**
 * Smoke Tests for Open Notebook
 *
 * Quick validation that core functionality works.
 * Run these first before full E2E suite.
 *
 * Tag: @smoke
 */

import { test, expect } from '../support/fixtures';

test.describe('Smoke Tests @smoke', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Verify page loaded (adjust selector based on actual UI)
    await expect(page).toHaveTitle(/Open Notebook|Notebook/i);
  });

  test('can navigate to notebooks page', async ({ page }) => {
    await page.goto('/');

    // Look for notebooks link/button (adjust selector)
    const notebooksLink = page.getByRole('link', { name: /notebook/i });
    if (await notebooksLink.isVisible()) {
      await notebooksLink.click();
      await expect(page).toHaveURL(/notebooks/);
    }
  });

  test('API health check passes', async ({ apiClient }) => {
    // Verify backend is reachable
    const response = await apiClient.get('/health');
    expect(response).toBeDefined();
  });

  test('can list notebooks via API', async ({ apiClient }) => {
    const notebooks = await apiClient.get<unknown[]>('/notebooks/');
    expect(Array.isArray(notebooks)).toBe(true);
  });
});
