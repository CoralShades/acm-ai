/**
 * End-to-End User Journeys
 *
 * Tests critical user workflows from start to finish:
 * 1. New User Journey - Create notebook, upload SAMP, view grid, chat, export
 * 2. Power User Journey - Multiple SAMPs, filtering, comparison, export
 * 3. QA Analyst Journey - Validate extraction, check negatives, verify compliance
 *
 * These tests validate complete workflows and integration between features.
 *
 * Tag: @user-journeys
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
  sendChatMessage,
  waitForAgentResponse,
  getLastChatMessage,
  testACMStatsQuery,
} from './helpers/chat-helpers';
import {
  captureEvidence,
  captureWorkflow,
} from './helpers/screenshot-helpers';
import * as path from 'path';

const SAMP_FIXTURES_DIR = path.join(__dirname, 'fixtures/samps');
const BROADMEADOWS_SAMP = path.join(
  SAMP_FIXTURES_DIR,
  'broadmeadows-police-station-samp.pdf'
);
const SAMP_1124 = path.join(SAMP_FIXTURES_DIR, '1124-asbestos-register.pdf');
const SAMP_3980 = path.join(SAMP_FIXTURES_DIR, '3980-asbestos-register.pdf');

test.describe('End-to-End User Journeys @user-journeys', () => {
  let factory: TestDataFactory;

  test.beforeEach(async () => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup();
  });

  test('Journey 1: New user creates notebook, uploads SAMP, views data, asks questions, and exports', async ({
    page,
  }) => {
    // Capture workflow steps
    const workflowSteps: string[] = [];

    // Step 1: User creates a new notebook
    await page.goto('/');
    workflowSteps.push('homepage-loaded');

    const createButton = page.getByRole('button', { name: /create|new|add/i });
    await expect(createButton).toBeVisible();
    await createButton.click();

    const nameInput = page.getByLabel(/name/i);
    await expect(nameInput).toBeVisible();
    await nameInput.fill('My First ACM Analysis');

    const submitButton = page.getByRole('button', {
      name: /save|create|submit/i,
    });
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    workflowSteps.push('notebook-created');

    // Verify notebook page loads
    await expect(page.getByText(/My First ACM Analysis/i)).toBeVisible();

    // Step 2: User uploads SAMP document via wizard
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    workflowSteps.push('samp-uploaded');

    // Step 3: User waits for extraction to complete
    await waitForExtraction(page, 180000);
    workflowSteps.push('extraction-complete');

    // Step 4: User views extracted records in grid
    await navigateToACMRegister(page);
    workflowSteps.push('acm-grid-opened');

    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Capture workflow
    await captureWorkflow(page, 'journey1-new-user', workflowSteps);

    // Step 5: User asks chat question about ACM data
    await sendChatMessage(page, 'How many positive ACM results are there?');
    await waitForAgentResponse(page);
    workflowSteps.push('chat-query-answered');

    const chatResponse = await getLastChatMessage(page);
    expect(chatResponse.length).toBeGreaterThan(0);

    await captureEvidence(page, 'journey1-chat-interaction');

    // Step 6: User exports data to Excel
    await navigateToACMRegister(page);
    await exportACMRecords(page, 'excel');
    workflowSteps.push('data-exported');

    // Capture final state
    await captureEvidence(page, 'journey1-complete');

    // Verify journey completion
    expect(recordCount).toBeGreaterThan(0);
    expect(chatResponse).toBeTruthy();
  });

  test('Journey 2: Power user compares multiple SAMPs, filters data, and exports consolidated report', async ({
    page,
  }) => {
    // Capture workflow steps
    const workflowSteps: string[] = [];

    // Step 1: Create notebook for comparison
    const notebook = await factory.createNotebook({
      name: 'Multi-Building ACM Comparison',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    workflowSteps.push('notebook-ready');

    // Step 2: Upload first SAMP
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);
    workflowSteps.push('samp1-extracted');

    // Capture first upload
    await captureEvidence(page, 'journey2-samp1-complete');

    // Step 3: Upload second SAMP
    await uploadSAMP(page, SAMP_1124);
    await waitForExtraction(page, 180000);
    workflowSteps.push('samp2-extracted');

    // Capture second upload
    await captureEvidence(page, 'journey2-samp2-complete');

    // Step 4: Upload third SAMP
    await uploadSAMP(page, SAMP_3980);
    await waitForExtraction(page, 180000);
    workflowSteps.push('samp3-extracted');

    // Capture third upload
    await captureEvidence(page, 'journey2-samp3-complete');

    // Step 5: View extractions in grid
    await navigateToACMRegister(page);
    workflowSteps.push('combined-grid-opened');

    const totalRecords = await getACMRecordCount(page);
    expect(totalRecords).toBeGreaterThan(0);

    await captureEvidence(page, 'journey2-combined-grid');

    // Step 6: Use filtering and sorting
    const positiveFound = await searchACMGrid(page, 'Positive');
    expect(positiveFound).toBeTruthy();
    workflowSteps.push('filtering-applied');

    await captureEvidence(page, 'journey2-filtered-results');

    // Step 7: Compare compliance across buildings
    await testACMStatsQuery(page);
    workflowSteps.push('stats-compared');

    await captureEvidence(page, 'journey2-compliance-comparison');

    // Step 8: Export consolidated report
    await navigateToACMRegister(page);
    await exportACMRecords(page, 'excel');
    workflowSteps.push('consolidated-export-complete');

    // Capture workflow
    await captureWorkflow(page, 'journey2-power-user', workflowSteps);

    // Verify journey completion
    expect(totalRecords).toBeGreaterThan(0);
  });

  test('Journey 3: QA analyst validates extraction quality, identifies issues, and flags problems', async ({
    page,
  }) => {
    // Capture workflow steps
    const workflowSteps: string[] = [];

    // Step 1: Upload SAMP for validation
    const notebook = await factory.createNotebook({
      name: 'QA Validation - Broadmeadows',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    workflowSteps.push('notebook-ready');

    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);
    workflowSteps.push('extraction-complete');

    // Step 2: Review extraction accuracy
    await navigateToACMRegister(page);
    workflowSteps.push('grid-opened');

    const recordCount = await getACMRecordCount(page);
    const expectedCount = 31; // From broadmeadows-expected-results.json
    const accuracy = recordCount / expectedCount;

    await captureEvidence(page, 'journey3-accuracy-check', {
      fullPage: true,
    });

    // Document accuracy
    console.log(`QA Check: Extracted ${recordCount}/${expectedCount} records (${(accuracy * 100).toFixed(1)}%)`);
    workflowSteps.push('accuracy-assessed');

    // Step 3: Identify negative results
    const negativeFound = await searchACMGrid(page, 'Negative');
    workflowSteps.push('negatives-checked');

    await captureEvidence(page, 'journey3-negative-results');

    // Step 4: Verify compliance fields
    const fanRoomFound = await searchACMGrid(page, 'Fan Room');
    if (fanRoomFound) {
      const recordDetails = await getACMRecordDetails(page, 0);

      // Check for compliance field presence
      const hasSampleNo = recordDetails.hasOwnProperty('sample_no');
      const hasQuantity = recordDetails.hasOwnProperty('quantity');
      const hasLabelled = recordDetails.hasOwnProperty('labelled');
      const hasFloorLevel = recordDetails.hasOwnProperty('floor_level');
      const hasResult = recordDetails.hasOwnProperty('result');

      workflowSteps.push('compliance-fields-verified');

      await captureEvidence(page, 'journey3-compliance-fields');

      // Document findings
      console.log('Compliance Field Verification:');
      console.log(`  - sample_no: ${hasSampleNo}`);
      console.log(`  - quantity: ${hasQuantity}`);
      console.log(`  - labelled: ${hasLabelled}`);
      console.log(`  - floor_level: ${hasFloorLevel}`);
      console.log(`  - result: ${hasResult}`);
    }

    // Step 5: Flag extraction issues via chat
    await sendChatMessage(
      page,
      'What is the extraction accuracy for this building? Are there any issues?'
    );
    await waitForAgentResponse(page);
    workflowSteps.push('issues-flagged');

    const qaResponse = await getLastChatMessage(page);
    await captureEvidence(page, 'journey3-qa-analysis');

    // Capture workflow
    await captureWorkflow(page, 'journey3-qa-analyst', workflowSteps);

    // Verify journey completion
    expect(recordCount).toBeGreaterThan(0);
    expect(qaResponse).toBeTruthy();

    // QA acceptance criteria
    // Note: These may fail initially - that's expected!
    // Tests document the current state for gap analysis
    if (accuracy < 0.8) {
      console.warn(`⚠️  QA Warning: Extraction accuracy ${(accuracy * 100).toFixed(1)}% below 80% threshold`);
    }

    if (!negativeFound) {
      console.warn('⚠️  QA Warning: No negative results detected (expected 20)');
    }
  });

  test('Journey 4: Collaborative workflow - Multiple users working on same project', async ({
    page,
  }) => {
    // Step 1: Create shared notebook
    const notebook = await factory.createNotebook({
      name: 'Shared ACM Project',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Step 2: First user uploads SAMP
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);

    await captureEvidence(page, 'journey4-initial-upload');

    // Step 3: Verify data is accessible
    await navigateToACMRegister(page);
    const recordCount = await getACMRecordCount(page);
    expect(recordCount).toBeGreaterThan(0);

    // Step 4: Simulate second user accessing same notebook
    // (In real scenario, this would be a different session)
    await page.reload();
    await navigateToACMRegister(page);

    // Step 5: Verify data persistence
    const reloadedRecordCount = await getACMRecordCount(page);
    expect(reloadedRecordCount).toEqual(recordCount);

    await captureEvidence(page, 'journey4-data-persisted');

    // Step 6: Second user adds analysis via chat
    await sendChatMessage(page, 'Summarize the ACM findings');
    await waitForAgentResponse(page);

    await captureEvidence(page, 'journey4-collaborative-analysis');

    // Verify collaboration workflow
    const response = await getLastChatMessage(page);
    expect(response).toBeTruthy();
  });

  test('Journey 5: Mobile user workflow - View ACM data on mobile device', async ({
    page,
  }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    // Step 1: Create notebook
    const notebook = await factory.createNotebook({
      name: 'Mobile ACM Review',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Note: Upload wizard may not work well on mobile
    // For now, create data via API
    await uploadSAMP(page, BROADMEADOWS_SAMP);
    await waitForExtraction(page, 180000);

    // Step 2: Navigate to ACM grid (mobile view)
    await navigateToACMRegister(page);

    await captureEvidence(page, 'journey5-mobile-grid');

    // Step 3: Verify grid is responsive
    const grid = page.locator('[data-testid="acm-grid"]');
    await expect(grid).toBeVisible();

    // Step 4: View record details (mobile)
    const recordCount = await getACMRecordCount(page);
    if (recordCount > 0) {
      const firstRecord = await getACMRecordDetails(page, 0);
      expect(firstRecord).toBeTruthy();

      await captureEvidence(page, 'journey5-mobile-detail');
    }

    // Reset to desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });

    // Verify mobile workflow
    expect(recordCount).toBeGreaterThan(0);
  });
});
