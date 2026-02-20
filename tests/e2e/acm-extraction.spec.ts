/**
 * ACM Extraction Pipeline E2E Tests
 *
 * Tests core ACM extraction functionality from SAMP PDFs.
 * Validates extraction accuracy, negative detection, merged cells,
 * multi-page tables, field completeness, and export functionality.
 *
 * Target: 95%+ extraction accuracy (30/31 records from Broadmeadows SAMP)
 * Baseline: 87% accuracy (27/31 records as of Sprint 1)
 *
 * Tag: @acm-extraction
 */

import { test, expect } from '../support/fixtures';
import { TestDataFactory } from '../support/helpers/test-data-factory';
import {
  uploadSAMP,
  waitForExtraction,
  navigateToACMRegister,
  getACMRecordCount,
  validateACMGrid,
  searchACMGrid,
  getACMRecordDetails,
  exportACMRecords,
} from './helpers/acm-helpers';
import {
  captureEvidence,
  captureWorkflow,
  captureError,
} from './helpers/screenshot-helpers';
import * as path from 'path';
import * as fs from 'fs';

// Test data paths
const SAMP_FIXTURES_DIR = path.join(__dirname, 'fixtures/samps');
const BROADMEADOWS_SAMP = path.join(
  SAMP_FIXTURES_DIR,
  'broadmeadows-police-station-samp.pdf'
);
const SAMP_1124 = path.join(SAMP_FIXTURES_DIR, '1124-asbestos-register.pdf');
const SAMP_3980 = path.join(SAMP_FIXTURES_DIR, '3980-asbestos-register.pdf');
const EXPECTED_RESULTS_FILE = path.join(
  SAMP_FIXTURES_DIR,
  'broadmeadows-expected-results.json'
);

// Load expected results
const expectedResults = JSON.parse(
  fs.readFileSync(EXPECTED_RESULTS_FILE, 'utf-8')
);
const EXPECTED_RECORD_COUNT = expectedResults.metadata.total_records; // 31
const TARGET_ACCURACY = 0.95; // 95%
const TARGET_EXTRACTED_COUNT = Math.ceil(EXPECTED_RECORD_COUNT * TARGET_ACCURACY); // 30

test.describe('ACM Extraction Pipeline @acm-extraction', () => {
  let factory: TestDataFactory;

  test.beforeEach(async () => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup();
  });

  test('extracts all records from Broadmeadows SAMP with 95%+ accuracy', async ({
    page,
  }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Extraction Accuracy Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Capture initial state
    await captureEvidence(page, 'notebook-initial-state');

    // When: User uploads Broadmeadows SAMP
    await uploadSAMP(page, BROADMEADOWS_SAMP);

    // Capture upload workflow
    await captureWorkflow(page, 'broadmeadows-upload', [
      'file-selected',
      'upload-started',
      'processing',
    ]);

    // Wait for extraction to complete
    await waitForExtraction(page, 180000); // 3 minute timeout

    // Capture extraction complete state
    await captureEvidence(page, 'extraction-complete');

    // Navigate to ACM register
    await navigateToACMRegister(page);

    // Capture ACM grid state
    await captureEvidence(page, 'acm-grid-loaded');

    // Then: Verify extraction accuracy meets 95%+ threshold
    const actualCount = await getACMRecordCount(page);
    const accuracy = actualCount / EXPECTED_RECORD_COUNT;

    // Capture final grid state
    await captureEvidence(page, `acm-grid-final-count-${actualCount}`);

    // Log accuracy for debugging
    console.log(
      `Extraction: ${actualCount}/${EXPECTED_RECORD_COUNT} records (${(accuracy * 100).toFixed(1)}% accuracy)`
    );

    // Assert accuracy threshold (95% = 30/31 records)
    expect(actualCount).toBeGreaterThanOrEqual(TARGET_EXTRACTED_COUNT);
    expect(accuracy).toBeGreaterThanOrEqual(TARGET_ACCURACY);

    // Verify some expected records exist
    const positiveRecordFound = await searchACMGrid(page, 'Fan Room');
    expect(positiveRecordFound).toBeTruthy();

    const assumedPositiveFound = await searchACMGrid(page, 'Fuse cartridge');
    expect(assumedPositiveFound).toBeTruthy();
  });

  test('correctly identifies negative ACM results', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Negative Detection Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads Broadmeadows SAMP (contains 20 negative results)
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);
    await navigateToACMRegister(page);

    // Then: Verify negative results are extracted
    // Expected: 20 negative results from Broadmeadows SAMP
    const negativeRecordFound = await searchACMGrid(page, 'Main Foyer');
    expect(negativeRecordFound).toBeTruthy();

    // Search for negative result marker
    const negativeFound = await searchACMGrid(page, 'Negative');
    expect(negativeFound).toBeTruthy();

    // Capture evidence
    await captureEvidence(page, 'negative-results-detected');

    // Verify at least some negative records exist
    // (Full validation would require grid filtering by result type)
    const totalRecords = await getACMRecordCount(page);
    expect(totalRecords).toBeGreaterThan(8); // Baseline only extracted positives/assumed
  });

  test('handles merged cells in SAMP tables correctly', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Merged Cells Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads SAMP with merged cells (1124)
    await uploadSAMP(page, SAMP_1124);
    await waitForExtraction(page, 180000);

    // Capture extraction workflow
    await captureWorkflow(page, 'samp-1124-merged-cells', [
      'upload-complete',
      'extraction-processing',
      'extraction-complete',
    ]);

    await navigateToACMRegister(page);

    // Then: Verify records were extracted (any count > 0 indicates parsing succeeded)
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Capture grid state
    await captureEvidence(page, 'merged-cells-grid-loaded', {
      selector: '[data-testid="acm-grid"]',
    });

    // Verify grid contains valid data (check first row has required fields)
    if (recordCount > 0) {
      const firstRecord = await getACMRecordDetails(page, 0);
      expect(firstRecord).toHaveProperty('room_name');
      expect(firstRecord).toHaveProperty('product');
    }
  });

  test('stitches multi-page ACM tables correctly', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Multi-Page Table Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads SAMP with multi-page table (3980)
    await uploadSAMP(page, SAMP_3980);
    await waitForExtraction(page, 180000);

    // Capture workflow
    await captureWorkflow(page, 'samp-3980-multipage', [
      'upload-started',
      'extraction-processing',
      'page-stitching',
      'extraction-complete',
    ]);

    await navigateToACMRegister(page);

    // Then: Verify records from multiple pages are extracted
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Capture evidence
    await captureEvidence(page, 'multipage-table-stitched');

    // Verify data integrity (records should have complete fields)
    if (recordCount > 0) {
      const firstRecord = await getACMRecordDetails(page, 0);
      expect(firstRecord.room_name).toBeTruthy();
      expect(firstRecord.product).toBeTruthy();
    }
  });

  test('extracts all compliance fields completely', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Field Completeness Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads Broadmeadows SAMP
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);
    await navigateToACMRegister(page);

    // Then: Verify compliance fields are extracted
    // Critical fields: sample_no, quantity, labelled, floor_level, result
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Capture grid state
    await captureEvidence(page, 'compliance-fields-grid', {});

    // Check first positive/assumed positive record for field completeness
    const fanRoomFound = await searchACMGrid(page, 'Fan Room');
    expect(fanRoomFound).toBeTruthy();

    if (fanRoomFound) {
      const fanRoomRecord = await getACMRecordDetails(page, 0);

      // Verify compliance fields exist (values may vary)
      expect(fanRoomRecord).toHaveProperty('sample_no');
      expect(fanRoomRecord).toHaveProperty('quantity');
      expect(fanRoomRecord).toHaveProperty('labelled');
      expect(fanRoomRecord).toHaveProperty('floor_level');
      expect(fanRoomRecord).toHaveProperty('result');

      // Capture record detail
      await captureEvidence(page, 'fan-room-record-detail');

      // Verify non-null values for positive result
      expect(fanRoomRecord.sample_no).toBeTruthy();
      expect(fanRoomRecord.result).toMatch(/positive|detected/i);
    }
  });

  test('extracts BAR compliance fields from SAMP documents', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'BAR Compliance Fields Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads Broadmeadows SAMP (contains BAR fields)
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);
    await navigateToACMRegister(page);

    // Then: Verify BAR compliance fields appear in grid
    // BAR fields: identifying_company, date_inspected, inspection_type,
    //             bar_report_no, date_of_bar_report, asbestos_assessor, result_classification
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Capture grid with BAR columns
    await captureEvidence(page, 'bar-fields-grid');

    // Verify BAR columns are visible in grid
    const grid = page.locator('[data-testid="acm-grid"]');
    await expect(grid).toBeVisible();

    // Check that BAR field column headers exist
    // Note: AG Grid may virtualize columns, so we check for data presence instead
    const firstRecord = await getACMRecordDetails(page, 0);

    // Verify BAR fields exist in record structure
    const barFields = [
      'identifying_company',
      'date_inspected',
      'inspection_type',
      'bar_report_no',
      'date_of_bar_report',
      'asbestos_assessor',
      'result_classification',
    ];

    barFields.forEach(field => {
      expect(firstRecord).toHaveProperty(field);
    });

    // Capture record detail with BAR fields
    await captureEvidence(page, 'bar-fields-record-detail');

    // Verify at least some BAR fields have non-null values
    // (Not all SAMPs have all BAR fields, but Broadmeadows should have some)
    const hasAnyBARValue = barFields.some(field => {
      const value = firstRecord[field];
      return value && value !== '' && value !== 'null' && value !== 'undefined';
    });

    expect(hasAnyBARValue).toBeTruthy();
  });

  test('exports ACM records as CSV successfully', async ({ page }) => {
    // Given: User has uploaded SAMP and extracted ACM records
    const notebook = await factory.createNotebook({
      name: 'ACM CSV Export Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);

    // Capture pre-export state
    await captureEvidence(page, 'pre-export-grid');

    // When: User exports ACM records as CSV
    await exportACMRecords(page, 'csv');

    // Capture export workflow
    await captureEvidence(page, 'csv-export-complete');

    // Then: CSV file should be downloaded
    // (Playwright automatically captures download events)
    // Verification is handled in exportACMRecords helper
  });

  test('exports ACM records as Excel successfully', async ({ page }) => {
    // Given: User has uploaded SAMP and extracted ACM records
    const notebook = await factory.createNotebook({
      name: 'ACM Excel Export Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);

    // Capture pre-export state
    await captureEvidence(page, 'pre-export-grid-excel');

    // When: User exports ACM records as Excel
    await exportACMRecords(page, 'excel');

    // Capture export workflow
    await captureEvidence(page, 'excel-export-complete');

    // Then: Excel file should be downloaded
    // (Verification handled in exportACMRecords helper)
  });

  test('handles extraction errors gracefully', async ({ page }) => {
    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'ACM Error Handling Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    try {
      // When: User attempts to upload invalid file (trigger error)
      // Note: This test may need adjustment based on actual error handling
      const invalidFile = path.join(__dirname, 'fixtures/invalid-file.txt');

      // If invalid file doesn't exist, skip this test
      if (!fs.existsSync(invalidFile)) {
        test.skip();
        return;
      }

      await uploadSAMP(page, invalidFile);

      // Then: Error message should be displayed
      const errorMessage = page.locator('text=/error|failed|invalid/i');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      // Capture error state
      await captureError(page, 'extraction-error-handling');
    } catch (error) {
      // Capture error state
      await captureError(page, 'extraction-error-unexpected');
      throw error;
    }
  });

  /**
   * Baseline Test: Alexander District Hospital SAMP
   *
   * TODO: Establish accuracy baseline for Alexander District Hospital
   *
   * This test is a placeholder for establishing extraction accuracy
   * baseline on a second SAMP document. Currently skipped until the
   * PDF file is added to fixtures/samps/ directory.
   *
   * Steps to enable:
   * 1. Add alexander-district-hospital-samp.pdf to tests/e2e/fixtures/samps/
   * 2. Create alexander-expected-results.json with ground truth data
   * 3. Update ALEXANDER_SAMP and ALEXANDER_EXPECTED_RESULTS paths below
   * 4. Remove test.skip() to enable the test
   *
   * Expected outcome:
   * - Extraction completes successfully
   * - Record count > 0 (actual baseline TBD)
   * - Accuracy measurement for comparison with Broadmeadows
   */
  test.skip('establishes extraction baseline for Alexander District Hospital SAMP', async ({
    page,
  }) => {
    // Test fixture paths (to be added)
    const ALEXANDER_SAMP = path.join(
      SAMP_FIXTURES_DIR,
      'alexander-district-hospital-samp.pdf'
    );
    const ALEXANDER_EXPECTED_RESULTS = path.join(
      SAMP_FIXTURES_DIR,
      'alexander-expected-results.json'
    );

    // Skip if fixture files don't exist yet
    if (!fs.existsSync(ALEXANDER_SAMP)) {
      console.log('⏭️  Skipping Alexander District Hospital baseline - fixture not found');
      return;
    }

    // Given: User has created a notebook
    const notebook = await factory.createNotebook({
      name: 'Alexander District Hospital Baseline',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // When: User uploads Alexander District Hospital SAMP
    await uploadSAMP(page, ALEXANDER_SAMP);

    // Capture upload workflow
    await captureWorkflow(page, 'alexander-upload', [
      'file-selected',
      'upload-started',
      'processing',
    ]);

    // Wait for extraction to complete
    await waitForExtraction(page, 180000);

    // Navigate to ACM register
    await navigateToACMRegister(page);

    // Capture grid state
    await captureEvidence(page, 'alexander-grid-loaded');

    // Then: Verify extraction completed and records were extracted
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // If expected results exist, calculate accuracy
    if (fs.existsSync(ALEXANDER_EXPECTED_RESULTS)) {
      const alexResults = JSON.parse(
        fs.readFileSync(ALEXANDER_EXPECTED_RESULTS, 'utf-8')
      );
      const expectedCount = alexResults.metadata.total_records;
      const accuracy = recordCount / expectedCount;

      console.log(
        `📊 Alexander District Hospital Baseline: ${recordCount}/${expectedCount} records (${(accuracy * 100).toFixed(1)}% accuracy)`
      );

      // Capture final state with accuracy
      await captureEvidence(
        page,
        `alexander-baseline-${recordCount}-of-${expectedCount}`
      );

      // Document baseline (no assertion yet - just measuring)
      expect(recordCount).toBeGreaterThan(0);
    } else {
      console.log(`📊 Alexander District Hospital: ${recordCount} records extracted (ground truth TBD)`);
      await captureEvidence(page, `alexander-baseline-${recordCount}-records`);
    }
  });
});
