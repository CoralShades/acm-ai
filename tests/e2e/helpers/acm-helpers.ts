/**
 * ACM Test Helpers
 *
 * Helper functions for ACM-specific E2E testing:
 * - File upload workflows
 * - Extraction monitoring
 * - ACM grid validation
 * - Record comparison
 *
 * Usage:
 *   import { uploadARA, waitForExtraction, validateACMGrid } from './acm-helpers';
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

/**
 * Upload an ARA (Asbestos Register Assessment) PDF file through the UI
 *
 * Navigates through the 4-step upload wizard:
 * 1. File selection
 * 2. Site configuration
 * 3. Organization
 * 4. Processing options (ACM enabled)
 *
 * @param page - Playwright page object
 * @param filepath - Path to ARA PDF file
 * @returns Promise<void>
 */
export async function uploadARA(page: Page, filepath: string): Promise<void> {
  // Navigate to documents library
  await page.goto('/');
  const addSourceButton = page.getByRole('button', { name: /add source|upload/i });
  await expect(addSourceButton).toBeVisible();
  await addSourceButton.click();

  // Step 1: Upload file
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(filepath);

  // Wait for file to be uploaded
  await page.waitForSelector('text=/uploaded|ready/i', { timeout: 10000 });

  // Step 2: Site configuration (may be optional)
  const nextButton = page.getByRole('button', { name: /next|continue/i });
  if (await nextButton.isVisible()) {
    await nextButton.click();
  }

  // Step 3: Organization (may be optional)
  if (await nextButton.isVisible()) {
    await nextButton.click();
  }

  // Step 4: Processing options - ensure ACM extraction is enabled
  const acmCheckbox = page.locator('input[type="checkbox"]', {
    has: page.locator('text=/ACM|asbestos/i'),
  });
  if (await acmCheckbox.isVisible()) {
    await acmCheckbox.check();
  }

  // Submit upload
  const submitButton = page.getByRole('button', { name: /submit|upload|finish/i });
  await expect(submitButton).toBeVisible();
  await submitButton.click();

  // Wait for success notification
  await page.waitForSelector('text=/success|uploaded|processing/i', {
    timeout: 15000,
  });
}

/**
 * Wait for ACM extraction to complete
 *
 * Monitors extraction progress indicators until completion.
 * Throws if extraction fails or times out.
 *
 * @param page - Playwright page object
 * @param timeout - Timeout in milliseconds (default: 120s)
 * @returns Promise<void>
 */
export async function waitForExtraction(
  page: Page,
  timeout = 120000
): Promise<void> {
  const startTime = Date.now();

  // Look for extraction progress indicators
  const completedIndicator = page.locator('text=/extraction complete|processing complete/i');

  while (Date.now() - startTime < timeout) {
    // Check if extraction is complete
    if (await completedIndicator.isVisible()) {
      return;
    }

    // Check for error states
    const errorIndicator = page.locator('text=/extraction failed|error/i');
    if (await errorIndicator.isVisible()) {
      throw new Error('ACM extraction failed');
    }

    await page.waitForTimeout(2000); // Poll every 2 seconds
  }

  throw new Error(`Extraction timeout after ${timeout}ms`);
}

/**
 * Navigate to ACM register tab
 *
 * @param page - Playwright page object
 * @returns Promise<void>
 */
export async function navigateToACMRegister(page: Page): Promise<void> {
  const acmTab = page.getByRole('tab', { name: /ACM|asbestos/i });
  await expect(acmTab).toBeVisible();
  await acmTab.click();

  // Wait for ACM grid to load
  await page.waitForSelector('[data-testid="acm-grid"]', { timeout: 10000 });
}

/**
 * Get ACM grid rows
 *
 * @param page - Playwright page object
 * @returns Promise<Locator> - AG Grid row locators
 */
export async function getACMGridRows(page: Page): Promise<Locator> {
  const grid = page.locator('[data-testid="acm-grid"]');
  await expect(grid).toBeVisible();

  // AG Grid uses .ag-row for rows
  return grid.locator('.ag-row');
}

/**
 * Get ACM record count from grid
 *
 * @param page - Playwright page object
 * @returns Promise<number>
 */
export async function getACMRecordCount(page: Page): Promise<number> {
  const rows = await getACMGridRows(page);
  return rows.count();
}

/**
 * Validate ACM grid contains expected records
 *
 * @param page - Playwright page object
 * @param expectedCount - Expected number of records
 * @param minAccuracy - Minimum accuracy threshold (0-1)
 * @returns Promise<void>
 */
export async function validateACMGrid(
  page: Page,
  expectedCount: number,
  minAccuracy = 0.8
): Promise<void> {
  await navigateToACMRegister(page);

  const actualCount = await getACMRecordCount(page);
  const accuracy = actualCount / expectedCount;

  expect(accuracy).toBeGreaterThanOrEqual(
    minAccuracy,
    `ACM extraction accuracy ${(accuracy * 100).toFixed(1)}% is below threshold ${(minAccuracy * 100).toFixed(1)}%`
  );
}

/**
 * Search ACM grid for specific record
 *
 * @param page - Playwright page object
 * @param searchTerm - Room name, product, or other field value
 * @returns Promise<boolean> - True if record found
 */
export async function searchACMGrid(
  page: Page,
  searchTerm: string
): Promise<boolean> {
  const searchInput = page.locator('input[placeholder*="Search" i]');
  await expect(searchInput).toBeVisible();
  await searchInput.fill(searchTerm);

  // Wait for grid to update
  await page.waitForTimeout(500);

  const rows = await getACMGridRows(page);
  const count = await rows.count();

  return count > 0;
}

/**
 * Get ACM record details from grid row
 *
 * @param page - Playwright page object
 * @param rowIndex - Row index (0-based)
 * @returns Promise<Record<string, string>> - Record field values
 */
export async function getACMRecordDetails(
  page: Page,
  rowIndex: number
): Promise<Record<string, string>> {
  const rows = await getACMGridRows(page);
  const row = rows.nth(rowIndex);

  // Click row to open detail dialog
  await row.click();

  // Wait for detail dialog
  const dialog = page.locator('[role="dialog"]');
  await expect(dialog).toBeVisible();

  // Extract field values from dialog
  const details: Record<string, string> = {};
  const fields = await dialog.locator('[data-field]').all();

  for (const field of fields) {
    const name = await field.getAttribute('data-field');
    const value = await field.textContent();
    if (name && value) {
      details[name] = value.trim();
    }
  }

  // Close dialog
  const closeButton = dialog.getByRole('button', { name: /close/i });
  await closeButton.click();

  return details;
}

/**
 * Export ACM records as CSV/Excel
 *
 * @param page - Playwright page object
 * @param format - Export format ('csv' | 'excel')
 * @returns Promise<void>
 */
export async function exportACMRecords(
  page: Page,
  format: 'csv' | 'excel' = 'csv'
): Promise<void> {
  await navigateToACMRegister(page);

  const exportButton = page.getByRole('button', { name: /export/i });
  await expect(exportButton).toBeVisible();
  await exportButton.click();

  // Select format from dropdown
  const formatOption = page.getByRole('menuitem', {
    name: new RegExp(format, 'i'),
  });
  await expect(formatOption).toBeVisible();

  // Start download
  const downloadPromise = page.waitForEvent('download');
  await formatOption.click();
  const download = await downloadPromise;

  // Verify download
  const extension = format === 'csv' ? 'csv' : 'xlsx';
  const filename = download.suggestedFilename();
  expect(filename).toMatch(new RegExp(`\\.${extension}$`));
}
