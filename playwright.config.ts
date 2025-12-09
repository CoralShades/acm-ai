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
    baseURL: process.env.BASE_URL || 'http://localhost:8502',

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
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment for cross-browser testing:
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Web server configuration (starts frontend automatically)
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:8502',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
