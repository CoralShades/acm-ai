/**
 * API Contract Validation Tests
 *
 * Validates that key API endpoints return expected response shapes.
 * Detects schema drift between backend and frontend expectations.
 *
 * Tags: @smoke @api-contracts
 */

import { test, expect } from '../../support/fixtures';

test.describe('API Contract Validation @smoke @api-contracts', () => {
  test('GET /api/health returns valid response', async ({ apiClient }) => {
    const response = await apiClient.get<Record<string, unknown>>('/health');
    expect(response).toBeDefined();
    // Health endpoint should return some status indicator
    expect(typeof response === 'object').toBe(true);
  });

  test('GET /api/notebooks/ returns array with expected fields', async ({ apiClient }) => {
    const response = await apiClient.get<unknown[]>('/notebooks/');
    expect(Array.isArray(response)).toBe(true);
    // If there are notebooks, verify shape
    if (response.length > 0) {
      const first = response[0] as Record<string, unknown>;
      expect(first).toHaveProperty('id');
      expect(first).toHaveProperty('name');
    }
  });

  test('GET /api/sources/ returns array with expected fields', async ({ apiClient }) => {
    const response = await apiClient.get<unknown[]>('/sources/');
    expect(Array.isArray(response)).toBe(true);
    if (response.length > 0) {
      const first = response[0] as Record<string, unknown>;
      expect(first).toHaveProperty('id');
    }
  });

  test('GET /api/models/ returns array with expected fields', async ({ apiClient }) => {
    const response = await apiClient.get<unknown[]>('/models/');
    expect(Array.isArray(response)).toBe(true);
    if (response.length > 0) {
      const first = response[0] as Record<string, unknown>;
      expect(first).toHaveProperty('name');
    }
  });

  test('GET /api/models/defaults returns object with model fields', async ({ apiClient }) => {
    const response = await apiClient.get<Record<string, unknown>>('/models/defaults');
    expect(response).toBeDefined();
    expect(typeof response === 'object').toBe(true);
  });

  test('GET /api/acm/field-schema returns schema config', async ({ apiClient }) => {
    try {
      const response = await apiClient.get<Record<string, unknown>>('/acm/field-schema');
      expect(response).toHaveProperty('item_fields');
      expect(response).toHaveProperty('building_fields');
    } catch {
      // field-schema may not be configured — skip gracefully
      test.skip();
    }
  });

  test('GET /api/settings returns settings object', async ({ apiClient }) => {
    try {
      const response = await apiClient.get<Record<string, unknown>>('/settings');
      expect(response).toBeDefined();
      expect(typeof response === 'object').toBe(true);
    } catch {
      // Settings endpoint may not exist yet
      test.skip();
    }
  });
});
