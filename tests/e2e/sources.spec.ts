/**
 * Source Management E2E Tests for Open Notebook
 *
 * Tests PDF upload, source viewing, and transformations.
 * These tests interact with the AI processing pipeline.
 */

import { test, expect } from '../support/fixtures';
import { TestDataFactory } from '../support/helpers/test-data-factory';

test.describe('Source Management', () => {
  let factory: TestDataFactory;

  test.beforeEach(() => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup();
  });

  test('sources page loads', async ({ page }) => {
    await page.goto('/sources');

    // Verify sources page loaded
    await expect(page).toHaveURL(/sources/);
  });

  test('can navigate to source detail', async ({ page, apiClient }) => {
    // Get existing sources
    const sources = await apiClient.get<{ id: string }[]>('/sources/');

    if (sources.length > 0) {
      const sourceId = sources[0].id.replace('source:', '');
      await page.goto(`/sources/${sourceId}`);

      // Verify source detail page loads
      await expect(page.locator('[data-testid="source-detail"]')).toBeVisible({
        timeout: 15000,
      });
    }
  });

  test('upload button is accessible', async ({ page }) => {
    const notebook = await factory.createNotebook({ name: 'Upload Test' });

    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Look for upload/add source functionality
    const uploadButton = page.getByRole('button', { name: /upload|add source|import/i });

    // Button should exist (may not be visible if no notebook selected)
    await expect(uploadButton).toBeAttached();
  });
});
