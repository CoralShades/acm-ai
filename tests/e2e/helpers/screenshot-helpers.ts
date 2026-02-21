/**
 * Screenshot Helpers
 *
 * Capture evidence screenshots at critical test steps.
 * Saves screenshots with timestamps and descriptive names.
 *
 * Usage:
 *   import { captureEvidence, captureWorkflow } from './screenshot-helpers';
 */

import type { Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const SCREENSHOT_DIR = path.join(__dirname, '../../../test-results/screenshots');

/**
 * Ensure screenshot directory exists
 */
function ensureScreenshotDir(): void {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
}

/**
 * Generate screenshot filename with timestamp
 *
 * @param name - Descriptive name
 * @param suffix - Optional suffix
 * @returns Filename
 */
function generateFilename(name: string, suffix?: string): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const safeName = name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const suffixPart = suffix ? `-${suffix}` : '';
  return `${timestamp}-${safeName}${suffixPart}.png`;
}

/**
 * Capture evidence screenshot
 *
 * Saves screenshot with descriptive name and timestamp.
 *
 * @param page - Playwright page object
 * @param name - Descriptive name (e.g., "acm-grid-loaded")
 * @param options - Screenshot options
 * @returns Promise<string> - Path to saved screenshot
 */
export async function captureEvidence(
  page: Page,
  name: string,
  options: {
    fullPage?: boolean;
    selector?: string;
  } = {}
): Promise<string> {
  ensureScreenshotDir();

  const filename = generateFilename(name);
  const filepath = path.join(SCREENSHOT_DIR, filename);

  if (options.selector) {
    const element = page.locator(options.selector);
    await element.screenshot({ path: filepath });
  } else {
    await page.screenshot({
      path: filepath,
      fullPage: options.fullPage ?? false,
    });
  }

  return filepath;
}

/**
 * Capture workflow step screenshots
 *
 * Captures multiple screenshots for a multi-step workflow.
 *
 * @param page - Playwright page object
 * @param workflowName - Workflow name (e.g., "upload-wizard")
 * @param steps - Step descriptions
 * @returns Promise<string[]> - Paths to saved screenshots
 */
export async function captureWorkflow(
  page: Page,
  workflowName: string,
  steps: string[]
): Promise<string[]> {
  const screenshots: string[] = [];

  for (let i = 0; i < steps.length; i++) {
    const stepNum = String(i + 1).padStart(2, '0');
    const filename = generateFilename(workflowName, `step${stepNum}-${steps[i]}`);
    const filepath = path.join(SCREENSHOT_DIR, filename);

    await page.screenshot({ path: filepath, fullPage: false });
    screenshots.push(filepath);

    // Wait a moment between screenshots
    await page.waitForTimeout(500);
  }

  return screenshots;
}

/**
 * Capture comparison screenshots (before/after)
 *
 * @param page - Playwright page object
 * @param name - Descriptive name
 * @param beforeAction - Action to perform between screenshots
 * @returns Promise<{ before: string; after: string }>
 */
export async function captureComparison(
  page: Page,
  name: string,
  beforeAction: () => Promise<void>
): Promise<{ before: string; after: string }> {
  ensureScreenshotDir();

  const beforeFilename = generateFilename(name, 'before');
  const afterFilename = generateFilename(name, 'after');

  const beforePath = path.join(SCREENSHOT_DIR, beforeFilename);
  const afterPath = path.join(SCREENSHOT_DIR, afterFilename);

  // Capture before
  await page.screenshot({ path: beforePath });

  // Perform action
  await beforeAction();

  // Capture after
  await page.screenshot({ path: afterPath });

  return { before: beforePath, after: afterPath };
}

/**
 * Capture element screenshot
 *
 * Captures screenshot of specific element (e.g., ACM grid, chat panel).
 *
 * @param page - Playwright page object
 * @param selector - Element selector
 * @param name - Descriptive name
 * @returns Promise<string> - Path to saved screenshot
 */
export async function captureElement(
  page: Page,
  selector: string,
  name: string
): Promise<string> {
  ensureScreenshotDir();

  const filename = generateFilename(name);
  const filepath = path.join(SCREENSHOT_DIR, filename);

  const element = page.locator(selector);
  await element.screenshot({ path: filepath });

  return filepath;
}

/**
 * Capture grid state (ACM grid, AG Grid, etc.)
 *
 * @param page - Playwright page object
 * @param gridSelector - Grid selector
 * @param name - Descriptive name
 * @returns Promise<string> - Path to saved screenshot
 */
export async function captureGridState(
  page: Page,
  gridSelector: string,
  name: string
): Promise<string> {
  return captureElement(page, gridSelector, name);
}

/**
 * Capture error state
 *
 * Captures full page screenshot when an error occurs.
 *
 * @param page - Playwright page object
 * @param errorName - Error description
 * @returns Promise<string> - Path to saved screenshot
 */
export async function captureError(
  page: Page,
  errorName: string
): Promise<string> {
  ensureScreenshotDir();

  const filename = generateFilename(`error-${errorName}`);
  const filepath = path.join(SCREENSHOT_DIR, filename);

  await page.screenshot({ path: filepath, fullPage: true });

  return filepath;
}

/**
 * Capture mobile viewport screenshot
 *
 * @param page - Playwright page object
 * @param name - Descriptive name
 * @param viewport - Viewport size (default: 375x667 - iPhone SE)
 * @returns Promise<string> - Path to saved screenshot
 */
export async function captureMobileView(
  page: Page,
  name: string,
  viewport = { width: 375, height: 667 }
): Promise<string> {
  ensureScreenshotDir();

  // Set mobile viewport
  await page.setViewportSize(viewport);

  const filename = generateFilename(name, 'mobile');
  const filepath = path.join(SCREENSHOT_DIR, filename);

  await page.screenshot({ path: filepath, fullPage: false });

  // Reset to desktop viewport
  await page.setViewportSize({ width: 1280, height: 720 });

  return filepath;
}
