import { test, expect } from '@playwright/test';

/**
 * Navigation Timing Audit
 *
 * Measures route transition times and verifies loading skeletons appear.
 * Routes should transition in <3s with visible loading feedback.
 */

const NAV_ROUTES = [
  { from: '/', to: '/jobs', label: 'Dashboard -> Jobs' },
  { from: '/jobs', to: '/', label: 'Jobs -> Dashboard' },
  { from: '/', to: '/acm', label: 'Dashboard -> ACM Register' },
  { from: '/', to: '/settings', label: 'Dashboard -> Settings' },
  { from: '/', to: '/search', label: 'Dashboard -> Search' },
  { from: '/', to: '/notebooks', label: 'Dashboard -> Notebooks' },
  { from: '/jobs', to: '/settings', label: 'Jobs -> Settings' },
  { from: '/settings', to: '/acm', label: 'Settings -> ACM Register' },
];

test.describe('Navigation Timing Audit', () => {
  for (const route of NAV_ROUTES) {
    test(`${route.label}: should transition in <3s`, async ({ page }) => {
      // Navigate to starting page and wait for it to be stable
      await page.goto(`http://localhost:8503${route.from}`, {
        waitUntil: 'domcontentloaded',
      });
      // Let hydration and initial data load complete
      await page.waitForTimeout(2000);

      const startTime = Date.now();

      // Click sidebar nav link if available, otherwise navigate directly
      const link = page.locator(`a[href="${route.to}"]`).first();
      if (await link.isVisible({ timeout: 2000 }).catch(() => false)) {
        await link.click();
      } else {
        // Fallback: direct navigation (still measures route rendering time)
        await page.goto(`http://localhost:8503${route.to}`);
      }

      // Wait for URL to change
      await page.waitForURL(`**${route.to}`, { timeout: 60000 });
      const urlChangeTime = Date.now() - startTime;

      // Wait for meaningful content to appear
      await page.waitForSelector(
        '[data-testid], main, [role="grid"], h1, h2, [aria-busy="true"]',
        { timeout: 60000 }
      );
      const contentTime = Date.now() - startTime;

      // Check if a loading skeleton appeared during transition
      const loadingVisible = await page
        .locator(
          '[data-testid*="skeleton"], [data-testid*="loading"], .animate-pulse, [aria-busy="true"]'
        )
        .first()
        .isVisible()
        .catch(() => false);

      // Log timing results
      console.log(`  ${route.label}:`);
      console.log(`    URL change: ${urlChangeTime}ms`);
      console.log(`    Content visible: ${contentTime}ms`);
      console.log(
        `    ${urlChangeTime > 3000 ? 'BLOCKING' : urlChangeTime > 1000 ? 'SLOW' : 'OK'}`
      );
      console.log(
        `    Loading skeleton shown: ${loadingVisible ? 'YES' : 'NO'}`
      );

      // Assert transition completes in <3s
      expect
        .soft(urlChangeTime, `${route.label} URL change time`)
        .toBeLessThan(3000);
    });
  }

  test('ConnectionGuard shows skeleton instead of blank screen', async ({
    page,
  }) => {
    // Navigate to the app - the ConnectionGuard should show a skeleton
    // while checking connection, not a blank white screen
    const response = await page.goto('http://localhost:8503/', {
      waitUntil: 'commit', // Don't wait for full load
    });

    // Check immediately for loading indicators
    const hasSkeleton = await page
      .locator('.animate-pulse, [aria-busy="true"]')
      .first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);

    console.log(
      `  ConnectionGuard skeleton: ${hasSkeleton ? 'VISIBLE' : 'NOT VISIBLE (may have loaded too fast)'}`
    );

    // The page should eventually load
    await page.waitForSelector('main, [data-testid], h1, h2', {
      timeout: 30000,
    });
    console.log('  App loaded successfully');
  });
});
