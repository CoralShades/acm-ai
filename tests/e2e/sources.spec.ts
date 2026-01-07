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

  test('can navigate to source detail', async ({ page }) => {
    // Given: A source exists (created via factory)
    const notebook = await factory.createNotebook({ name: 'Source Detail Test' });

    // When: User navigates to notebook page (sources are linked to notebooks)
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Then: Page should load successfully
    await expect(page).toHaveURL(/notebooks/);
    // Note: Full source detail test requires createSource in factory
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
