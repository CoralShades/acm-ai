/**
 * Accessibility Audit Tests
 *
 * Runs axe-core WCAG 2.1 AA audits on key pages.
 * Reports violations by impact level.
 * Asserts no critical violations exist.
 *
 * Tag: @a11y
 */

import { test, expect } from '../../support/fixtures';
import { auditPage, getCriticalViolations } from '../framework/accessibility';

const KEY_PAGES = [
  { route: '/', name: 'Homepage' },
  { route: '/documents', name: 'Documents' },
  { route: '/sources', name: 'Sources' },
  { route: '/search', name: 'Search' },
  { route: '/settings', name: 'Settings' },
  { route: '/upload', name: 'Upload' },
  { route: '/jobs', name: 'Jobs' },
  { route: '/notebooks', name: 'Notebooks' },
];

test.describe('Accessibility Audits @a11y', () => {
  for (const { route, name } of KEY_PAGES) {
    test(`${name} (${route}) has no critical a11y violations`, async ({ page }) => {
      await page.goto(route);
      await page.waitForLoadState('domcontentloaded');

      const result = await auditPage(page, route);

      // Get critical and serious violations
      const critical = getCriticalViolations(result);

      // Log all violations for debugging (not just critical)
      if (result.violations.length > 0) {
        console.log(`\nAccessibility violations on ${route}:`);
        for (const v of result.violations) {
          console.log(`  [${v.impact}] ${v.id}: ${v.description}`);
        }
      }

      // Assert: no critical or serious violations
      expect(
        critical,
        `Critical/serious a11y violations on ${route}: ${critical.map((v) => `${v.id}: ${v.description}`).join('; ')}`
      ).toHaveLength(0);
    });
  }

  test('audit report summary', async ({ page }) => {
    // Run a quick audit on the homepage and log summary
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const result = await auditPage(page, '/');

    console.log(`\nAccessibility Audit Summary for /:`);
    console.log(`  Passes: ${result.passes}`);
    console.log(`  Violations: ${result.violations.length}`);
    console.log(`  Incomplete: ${result.incomplete}`);

    // This test always passes — it's for reporting purposes
    expect(result).toBeDefined();
  });
});
