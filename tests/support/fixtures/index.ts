/**
 * Merged Test Fixtures for Open Notebook E2E Tests
 *
 * Pattern: Pure functions → Fixtures → mergeTests composition
 * Each fixture provides one isolated concern (auth, API, network, etc.)
 *
 * Usage:
 *   import { test, expect } from '../support/fixtures';
 *   test('my test', async ({ page, apiClient }) => { ... });
 */

import { test as base, mergeTests, expect } from '@playwright/test';

// Types for custom fixtures
type TestFixtures = {
  /** API client for backend calls (FastAPI on port 5055) */
  apiClient: {
    get: <T = unknown>(endpoint: string) => Promise<T>;
    post: <T = unknown>(endpoint: string, data?: unknown) => Promise<T>;
    put: <T = unknown>(endpoint: string, data?: unknown) => Promise<T>;
    delete: <T = unknown>(endpoint: string) => Promise<T>;
  };

  /** Wait helpers for async operations */
  waitHelpers: {
    waitForApi: (urlPattern: string | RegExp, timeout?: number) => Promise<void>;
    waitForNetworkIdle: (timeout?: number) => Promise<void>;
  };
};

// Base test with custom fixtures
const customTest = base.extend<TestFixtures>({
  // API Client fixture - for direct backend interaction
  apiClient: async ({ request }, use) => {
    const apiUrl = process.env.API_URL || 'http://localhost:5055/api';

    const client = {
      get: async <T = unknown>(endpoint: string): Promise<T> => {
        const response = await request.get(`${apiUrl}${endpoint}`);
        if (!response.ok()) {
          throw new Error(`API GET ${endpoint} failed: ${response.status()}`);
        }
        return response.json();
      },

      post: async <T = unknown>(endpoint: string, data?: unknown): Promise<T> => {
        const response = await request.post(`${apiUrl}${endpoint}`, { data });
        if (!response.ok()) {
          throw new Error(`API POST ${endpoint} failed: ${response.status()}`);
        }
        return response.json();
      },

      put: async <T = unknown>(endpoint: string, data?: unknown): Promise<T> => {
        const response = await request.put(`${apiUrl}${endpoint}`, { data });
        if (!response.ok()) {
          throw new Error(`API PUT ${endpoint} failed: ${response.status()}`);
        }
        return response.json();
      },

      delete: async <T = unknown>(endpoint: string): Promise<T> => {
        const response = await request.delete(`${apiUrl}${endpoint}`);
        if (!response.ok()) {
          throw new Error(`API DELETE ${endpoint} failed: ${response.status()}`);
        }
        return response.json();
      },
    };

    await use(client);
  },

  // Wait helpers fixture - for async operations
  waitHelpers: async ({ page }, use) => {
    const helpers = {
      waitForApi: async (urlPattern: string | RegExp, timeout = 30000) => {
        await page.waitForResponse(
          (response) => {
            const url = response.url();
            return typeof urlPattern === 'string'
              ? url.includes(urlPattern)
              : urlPattern.test(url);
          },
          { timeout }
        );
      },

      waitForNetworkIdle: async (timeout = 10000) => {
        await page.waitForLoadState('networkidle', { timeout });
      },
    };

    await use(helpers);
  },
});

// Export merged test with all fixtures
export const test = mergeTests(base, customTest);
export { expect };
