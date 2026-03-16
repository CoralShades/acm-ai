/**
 * Smoke Tests for VAEA | ACM AI
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

    // Verify page loaded — app is branded as "VAEA | ACM AI"
    await expect(page).toHaveTitle(/VAEA|ACM/i);
  });

  test('can navigate to jobs page', async ({ page }) => {
    // Given: User is on the homepage
    await page.goto('/');

    // When: User clicks the Jobs link (primary nav item in ACM mode)
    const jobsLink = page.getByRole('link', { name: /jobs/i });
    await expect(jobsLink).toBeVisible();
    await jobsLink.click();

    // Then: User should be on the jobs page
    await expect(page).toHaveURL(/jobs/);
  });

  test('API health check passes', async ({ apiClient }) => {
    // Verify backend is reachable
    const response = await apiClient.get('/health');
    expect(response).toBeDefined();
  });

  test('can list notebooks via API', async ({ apiClient }) => {
    const notebooks = await apiClient.get<unknown[]>('/notebooks');
    expect(Array.isArray(notebooks)).toBe(true);
  });
});
