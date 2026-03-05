/**
 * Evidence Collector
 *
 * Captures screenshots, console logs, network requests, and DOM snapshots
 * during E2E test runs for post-mortem analysis and healing diagnostics.
 */

import * as path from 'path';
import * as fs from 'fs';
import { Page } from '@playwright/test';

const EVIDENCE_DIR = path.join(__dirname, '../../../../test-results/evidence');

export interface EvidenceBundle {
  testName: string;
  timestamp: string;
  screenshots: string[];
  consoleLogs: Array<{ level: string; text: string; url: string }>;
  networkRequests: Array<{
    url: string;
    method: string;
    status: number;
    timing: number;
  }>;
  domSnapshot?: string;
}

function ensureEvidenceDir(): void {
  if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  }
}

export class EvidenceCollector {
  private consoleLogs: Array<{ level: string; text: string; url: string }> = [];
  private networkRequests: Array<{
    url: string;
    method: string;
    status: number;
    timing: number;
  }> = [];
  private requestTimings: Map<string, number> = new Map();

  /**
   * Attach console and network listeners to a Playwright page.
   * Call this once at the start of a test.
   */
  attach(page: Page): void {
    page.on('console', (msg) => {
      this.consoleLogs.push({
        level: msg.type(),
        text: msg.text(),
        url: page.url(),
      });
    });

    page.on('request', (request) => {
      const key = `${request.method()} ${request.url()}`;
      this.requestTimings.set(key, Date.now());
    });

    page.on('response', (response) => {
      const request = response.request();
      const key = `${request.method()} ${request.url()}`;
      const startTime = this.requestTimings.get(key);
      const timing = startTime ? Date.now() - startTime : 0;
      this.networkRequests.push({
        url: request.url(),
        method: request.method(),
        status: response.status(),
        timing,
      });
      this.requestTimings.delete(key);
    });
  }

  /**
   * Capture a screenshot and save it to the evidence directory.
   * @returns The absolute path to the saved screenshot.
   */
  async captureScreenshot(page: Page, name: string): Promise<string> {
    ensureEvidenceDir();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    const filepath = path.join(EVIDENCE_DIR, filename);
    await page.screenshot({ path: filepath, fullPage: true });
    return filepath;
  }

  /**
   * Capture a full evidence bundle including screenshot, logs, and requests.
   */
  async captureEvidence(page: Page, testName: string): Promise<EvidenceBundle> {
    const screenshotPath = await this.captureScreenshot(page, testName);
    const timestamp = new Date().toISOString();

    return {
      testName,
      timestamp,
      screenshots: [screenshotPath],
      consoleLogs: [...this.consoleLogs],
      networkRequests: [...this.networkRequests],
    };
  }

  /**
   * Save an evidence bundle as a JSON file.
   * @returns The absolute path to the saved JSON file.
   */
  save(bundle: EvidenceBundle): string {
    ensureEvidenceDir();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `evidence-${bundle.testName}-${timestamp}.json`;
    const filepath = path.join(EVIDENCE_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(bundle, null, 2), 'utf-8');
    return filepath;
  }

  /**
   * Clear accumulated logs and detach.
   */
  detach(): void {
    this.consoleLogs = [];
    this.networkRequests = [];
    this.requestTimings.clear();
  }
}
