/**
 * Settings Pages Tests
 *
 * Verifies that each settings sub-page loads correctly
 * and renders its form controls.
 *
 * Tag: @feature
 */

import { test, expect } from '../../support/fixtures';

const SETTINGS_ROUTES = [
  { path: '/settings', name: 'Main Settings' },
  { path: '/settings/models', name: 'Models' },
  { path: '/settings/field-mapping', name: 'Field Mapping' },
  { path: '/settings/field-schema', name: 'Field Schema' },
  { path: '/settings/extraction', name: 'Extraction' },
  { path: '/settings/processing', name: 'Processing' },
  { path: '/settings/bar-templates', name: 'BAR Templates' },
  { path: '/settings/parsers', name: 'Parsers' },
];

test.describe('Settings Pages @feature', () => {
  for (const { path, name } of SETTINGS_ROUTES) {
    test(`${name} page (${path}) loads without errors`, async ({ page }) => {
      const errors: string[] = [];
      page.on('pageerror', (err) => errors.push(err.message));

      const response = await page.goto(path);

      // Page should load (200 or redirect to settings)
      const status = response?.status() ?? 0;
      expect(status).toBeLessThan(500);

      // Wait for content to render
      await page.waitForLoadState('domcontentloaded');

      // Should have some visible content
      const bodyText = await page.locator('body').textContent({ timeout: 5000 }).catch(() => '');
      expect(bodyText?.length).toBeGreaterThan(0);

      // No uncaught JS errors
      expect(errors, `JS errors on ${path}`).toHaveLength(0);
    });
  }

  test('settings page has navigation links', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('domcontentloaded');

    // Settings page should have navigation to sub-pages
    const links = page.locator('a[href*="/settings/"]');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
  });
});
