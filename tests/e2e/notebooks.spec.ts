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
    // Given: User is on the homepage
    await page.goto('/');

    // When: User clicks create button and fills form
    const createButton = page.getByRole('button', { name: /create|new|add/i });
    await expect(createButton).toBeVisible();
    await createButton.click();

    const nameInput = page.getByLabel(/name/i);
    await expect(nameInput).toBeVisible();
    await nameInput.fill('E2E Test Notebook');

    const submitButton = page.getByRole('button', { name: /save|create|submit/i });
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Then: Notebook should be created and visible
    await expect(page.getByText('E2E Test Notebook')).toBeVisible();
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
