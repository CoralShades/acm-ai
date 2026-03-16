/**
 * Building Detail Page Tests
 *
 * Tests the /source/[id] page with BuildingSidebar and ItemGrid.
 * Uses mocked API responses for buildings, records, and field schema.
 *
 * Tag: @feature
 */

import { test, expect } from '../../support/fixtures';

const MOCK_SOURCE_ID = 'source:test001';
const ENCODED_SOURCE_ID = encodeURIComponent(MOCK_SOURCE_ID);

const MOCK_BUILDINGS = [
  {
    id: 'building_record:bld001',
    internal_id: 'BLD#TEST_001',
    source_id: MOCK_SOURCE_ID,
    building_code: 'B01',
    building_name: 'Main Block',
    building_address: '10 Test Street',
    record_count: 3,
    created: '2026-01-01T00:00:00Z',
    updated: '2026-01-01T00:00:00Z',
  },
];

const MOCK_RECORDS = [
  {
    id: 'acm_record:r001',
    source_id: MOCK_SOURCE_ID,
    building_id: 'B01',
    room_id: 'RM-001',
    room_name: 'Boiler Room',
    product: 'Pipe lagging',
    result: 'Detected',
    risk_status: 'High',
    friable: 'Friable',
    material_condition: 'Poor',
    created: '2026-01-01T00:00:00Z',
    updated: '2026-01-01T00:00:00Z',
  },
];

const MOCK_FIELD_SCHEMA = {
  version: '1.0.0',
  building_fields: { object_name: 'Building__c', fields: [], picklists: {}, version: '1.0.0' },
  item_fields: {
    object_name: 'ACM_Item__c',
    fields: [
      { api_name: 'room_name', label: 'Room Name', field_type: 'string', nillable: true, updateable: true },
      { api_name: 'product', label: 'ACM Product', field_type: 'string', nillable: true, updateable: true },
      { api_name: 'risk_status', label: 'Risk Status', field_type: 'picklist', nillable: true, updateable: true },
    ],
    picklists: { risk_status: ['Low', 'Medium', 'High'] },
    version: '1.0.0',
  },
  picklists: {},
  dependencies: [],
  loaded_at: '2026-01-01T00:00:00Z',
};

async function setupBuildingMocks(page: import('@playwright/test').Page) {
  await page.route('**/api/acm/buildings**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ buildings: MOCK_BUILDINGS, total: MOCK_BUILDINGS.length }),
    });
  });

  await page.route('**/api/acm/records**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ records: MOCK_RECORDS, total: MOCK_RECORDS.length, page: 1, pages: 1, limit: 500 }),
    });
  });

  await page.route('**/api/acm/field-schema**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_FIELD_SCHEMA),
    });
  });
}

test.describe('Building Detail Page @feature', () => {
  test('page loads at /source/:id', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await setupBuildingMocks(page);
    await page.goto(`/source/${ENCODED_SOURCE_ID}`);
    await page.waitForLoadState('domcontentloaded');

    // Page should load with building sidebar content
    await expect(page.getByText('Buildings')).toBeVisible({ timeout: 15000 });
    expect(errors).toHaveLength(0);
  });

  test('building sidebar shows building names', async ({ page }) => {
    await setupBuildingMocks(page);
    await page.goto(`/source/${ENCODED_SOURCE_ID}`);

    await expect(page.getByText('Main Block')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('BLD#TEST_001')).toBeVisible();
  });

  test('clicking a building loads the item grid', async ({ page }) => {
    await setupBuildingMocks(page);
    await page.goto(`/source/${ENCODED_SOURCE_ID}`);

    await page.getByText('Main Block').click();

    // AG Grid should appear
    await expect(
      page.locator('[data-testid="item-grid"], .ag-root-wrapper')
    ).toBeVisible({ timeout: 15000 });
  });

  test('item grid shows record data after building selection', async ({ page }) => {
    await setupBuildingMocks(page);
    await page.goto(`/source/${ENCODED_SOURCE_ID}`);

    await page.getByText('Main Block').click();

    // Record data should be visible
    await expect(page.getByText('Pipe lagging')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Boiler Room')).toBeVisible();
  });
});
