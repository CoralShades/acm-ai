import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright Configuration for Open Notebook E2E Tests
 *
 * Timeout Standards:
 * - Action: 15s (click, fill, etc.)
 * - Navigation: 30s (goto, reload)
 * - Expect: 10s (assertions)
 * - Test: 60s (full test)
 *
 * Environment:
 * - Set TEST_ENV=local|staging|production
 * - Uses dotenv for environment variables
 */

// Load .env from project root
import { config as dotenvConfig } from 'dotenv';
dotenvConfig({ path: path.resolve(__dirname, '.env') });

export default defineConfig({
  testDir: './tests/e2e',
  testIgnore: ['**/framework/**', '**/helpers/**'],
  outputDir: './test-results',

  // Parallel execution
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Timeout configuration (standardized)
  timeout: 60 * 1000,
  expect: {
    timeout: 10 * 1000,
  },

  use: {
    // Base URL - matches Open Notebook frontend
    baseURL: process.env.BASE_URL || 'http://localhost:8503',

    // Action/Navigation timeouts
    actionTimeout: 15 * 1000,
    navigationTimeout: 30 * 1000,

    // Artifacts - failure only (saves space)
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Browser context
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },

  // Reporters
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  // Browser projects
  projects: [
    {
      name: 'smoke',
      testMatch: /smoke|route-walker/,
      grep: /@smoke/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'critical',
      testMatch: /upload-wizard|jobs-pipeline/,
      grep: /@critical/,
      dependencies: ['smoke'],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'feature',
      testMatch: /settings|building|provenance/,
      grep: /@feature/,
      dependencies: ['smoke'],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'accessibility',
      testMatch: /accessibility/,
      grep: /@a11y/,
      dependencies: ['smoke'],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Web server configuration (starts frontend automatically)
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:8503',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
