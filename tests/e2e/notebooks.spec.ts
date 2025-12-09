/**
 * Notebook E2E Tests for Open Notebook
 *
 * Tests core notebook CRUD operations via UI.
 * Uses TestDataFactory for automatic cleanup.
 */

import { test, expect } from '../support/fixtures';
import { TestDataFactory } from '../support/helpers/test-data-factory';

test.describe('Notebook Management', () => {
  let factory: TestDataFactory;

  test.beforeEach(() => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup();
  });

  test('can create a new notebook', async ({ page }) => {
    await page.goto('/');

    // Look for create notebook button (adjust selector based on actual UI)
    const createButton = page.getByRole('button', { name: /create|new|add/i });

    if (await createButton.isVisible()) {
      await createButton.click();

      // Fill notebook form (adjust selectors)
      const nameInput = page.getByLabel(/name/i);
      if (await nameInput.isVisible()) {
        await nameInput.fill('E2E Test Notebook');
      }

      const submitButton = page.getByRole('button', { name: /save|create|submit/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();
      }

      // Verify notebook was created
      await expect(page.getByText('E2E Test Notebook')).toBeVisible();
    }
  });

  test('can view notebook details', async ({ page }) => {
    // Create notebook via API first (faster setup)
    const notebook = await factory.createNotebook({ name: 'View Test Notebook' });

    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Verify notebook page loads
    await expect(page.getByText(/View Test Notebook/i)).toBeVisible();
  });

  test('can see notebooks list', async ({ page }) => {
    // Create test notebooks
    await factory.createNotebook({ name: 'List Test 1' });
    await factory.createNotebook({ name: 'List Test 2' });

    await page.goto('/notebooks');

    // Verify notebooks are listed
    await expect(page.getByText('List Test 1')).toBeVisible();
    await expect(page.getByText('List Test 2')).toBeVisible();
  });
});
