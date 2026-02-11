import { chromium } from 'playwright';
import { mkdir, writeFile } from 'fs/promises';
import { join } from 'path';

const screenshotsDir = '/mnt/d/ailocal/acm-ai/_bmad-output/implementation-artifacts/screenshots';
await mkdir(screenshotsDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 }
});
const page = await context.newPage();

const bugs = [];
const errors = [];

page.on('pageerror', error => {
  errors.push({ type: 'page-error', message: error.message });
  console.error('❌ Page error:', error.message);
});

try {
  console.log('🌐 Navigating to http://localhost:8502/acm...');
  const response = await page.goto('http://localhost:8502/acm', { waitUntil: 'networkidle', timeout: 30000 });

  const finalUrl = page.url();
  console.log(`🔗 Final URL: ${finalUrl}`);

  if (finalUrl !== 'http://localhost:8502/acm') {
    bugs.push({
      severity: 'Critical',
      component: 'Routing',
      description: '/acm route redirects to wrong page',
      expected: 'URL should stay at /acm',
      actual: `URL redirected to ${finalUrl}`
    });
    console.log('❌ BUG: /acm redirected to ' + finalUrl);
  }

  // Try clicking the ACM Register link
  console.log('\n🖱️  Clicking "ACM Register" link in sidebar...');
  const acmLink = page.locator('text="ACM Register"').first();
  if (await acmLink.count() > 0) {
    await acmLink.click();
    await page.waitForLoadState('networkidle');

    const acmUrl = page.url();
    console.log(`🔗 After click URL: ${acmUrl}`);

    await page.screenshot({
      path: join(screenshotsDir, 'acm-page-after-click.png'),
      fullPage: true
    });

    // Now check for ACM page elements
    console.log('\n🔍 Inspecting ACM page elements...');

    const statsCards = await page.locator('[class*="stat"], [data-testid*="stat"]').count();
    const agGridRoot = await page.locator('.ag-root, .ag-root-wrapper').count();
    const agGridRows = await page.locator('.ag-row').count();

    console.log(`📊 Stats cards: ${statsCards}`);
    console.log(`📋 AG Grid: ${agGridRoot > 0 ? 'Yes' : 'No'}`);
    console.log(`📋 Grid rows: ${agGridRows}`);

    // Check for toolbar
    const toolbar = await page.locator('[role="toolbar"], [class*="toolbar"]').count();
    console.log(`🔧 Toolbar: ${toolbar > 0 ? 'Found' : 'Not found'}`);

    // Check for quick filter
    const quickFilter = await page.locator('input[placeholder*="filter" i], input[placeholder*="search" i]').count();
    console.log(`🔍 Quick filter: ${quickFilter > 0 ? 'Found' : 'Not found'}`);

    // Check for source selector
    const sourceSelector = await page.locator('select, [role="combobox"], [class*="Select"]').count();
    console.log(`🎯 Source selector: ${sourceSelector > 0 ? 'Found' : 'Not found'}`);

    // Check for buttons
    const buttons = await page.locator('button').all();
    console.log(`🔘 Buttons found: ${buttons.length}`);
    for (const btn of buttons.slice(0, 10)) {
      const text = await btn.textContent();
      if (text && text.trim()) {
        console.log(`  - "${text.trim()}"`);
      }
    }

    // Test column headers if grid exists
    if (agGridRoot > 0) {
      const headers = await page.locator('.ag-header-cell').all();
      console.log(`\n📊 Column headers: ${headers.length}`);
      for (const header of headers.slice(0, 10)) {
        const text = await header.textContent();
        console.log(`  - ${text?.trim()}`);
      }

      // Test sorting
      if (headers.length > 0) {
        console.log('\n🧪 Testing column sorting...');
        await headers[0].click();
        await page.waitForTimeout(500);
        await page.screenshot({
          path: join(screenshotsDir, 'acm-page-sorted-column.png'),
          fullPage: true
        });
      }
    }

    // Test quick filter if available
    if (quickFilter > 0) {
      console.log('\n🧪 Testing quick filter with "Fan Room"...');
      const filterInput = page.locator('input[placeholder*="filter" i], input[placeholder*="search" i]').first();
      await filterInput.fill('Fan Room');
      await page.waitForTimeout(1000);
      const filteredRows = await page.locator('.ag-row').count();
      console.log(`  ✓ Filtered rows: ${filteredRows}`);
      await page.screenshot({
        path: join(screenshotsDir, 'acm-page-filter-fan-room.png'),
        fullPage: true
      });

      // Clear filter
      await filterInput.clear();
      await page.waitForTimeout(500);
    }

    // Test responsive at mobile size
    console.log('\n📱 Testing mobile viewport (768x1024)...');
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: join(screenshotsDir, 'acm-page-mobile-actual.png'),
      fullPage: true
    });

    // Test tablet size
    console.log('📱 Testing tablet viewport (1024x768)...');
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: join(screenshotsDir, 'acm-page-tablet-1024.png'),
      fullPage: true
    });

    // Back to desktop for risk badge check
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);

    // Check for risk status badges
    const badges = await page.locator('[class*="badge"], [class*="Badge"]').all();
    console.log(`\n🏷️  Badges found: ${badges.length}`);
    let lowRiskGreen = false;
    for (const badge of badges.slice(0, 20)) {
      const text = await badge.textContent();
      const color = await badge.evaluate(el => window.getComputedStyle(el).backgroundColor);
      if (text?.toLowerCase().includes('low') && (color.includes('green') || color.includes('34, 197') || color.includes('0, 128, 0'))) {
        lowRiskGreen = true;
        console.log(`  ✓ Low risk badge is green: ${text.trim()}`);
      }
    }

    // Document bugs
    if (agGridRoot === 0) {
      bugs.push({
        severity: 'Critical',
        component: 'AG Grid',
        description: 'AG Grid not rendered on ACM page',
        expected: 'AG Grid should display ACM records',
        actual: 'No AG Grid found'
      });
    }

    if (agGridRows === 0) {
      bugs.push({
        severity: 'Critical',
        component: 'Data Display',
        description: 'No ACM records displayed in grid',
        expected: '8 records for Clutch_Broadmeadows.pdf',
        actual: 'Zero rows'
      });
    }

    if (!lowRiskGreen) {
      bugs.push({
        severity: 'Low',
        component: 'UI/UX',
        description: 'Risk status badge color not verified',
        expected: 'Low risk = green badge',
        actual: 'Could not verify green color for low risk'
      });
    }

  } else {
    bugs.push({
      severity: 'Critical',
      component: 'Navigation',
      description: 'ACM Register link not found in sidebar',
      expected: 'ACM Register link should be visible in sidebar',
      actual: 'Link not found'
    });
  }

  // Save final report
  const report = {
    timestamp: new Date().toISOString(),
    test: 'ACM Register Page UI/UX Bug Hunt',
    bugs,
    errors,
    screenshots: [
      'acm-page-after-click.png',
      'acm-page-sorted-column.png',
      'acm-page-filter-fan-room.png',
      'acm-page-mobile-actual.png',
      'acm-page-tablet-1024.png'
    ]
  };

  await writeFile(
    join(screenshotsDir, 'acm-page-bug-report.json'),
    JSON.stringify(report, null, 2),
    'utf-8'
  );

  console.log(`\n✅ Bug hunt completed`);
  console.log(`📊 ${bugs.length} bug(s) found`);
  console.log(`📸 Screenshots saved to: ${screenshotsDir}`);

} catch (error) {
  console.error('❌ Error:', error.message);
  await page.screenshot({
    path: join(screenshotsDir, 'acm-page-test-error.png'),
    fullPage: true
  });
} finally {
  await browser.close();
  console.log('🔌 Browser closed');
}
