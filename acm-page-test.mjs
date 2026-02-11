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

const errors = [];
const consoleMessages = [];

// Listen for page errors
page.on('pageerror', error => {
  errors.push({ type: 'page-error', message: error.message });
  console.error('❌ Page error:', error.message);
});

// Listen for console messages
page.on('console', msg => {
  const message = { type: msg.type(), text: msg.text() };
  consoleMessages.push(message);
  if (msg.type() === 'error') {
    console.error('❌ Console error:', msg.text());
  }
});

try {
  console.log('🌐 Navigating to ACM page...');
  await page.goto('http://localhost:8502/acm', { waitUntil: 'networkidle', timeout: 30000 });

  console.log('📸 Taking desktop screenshot (1920x1080)...');
  await page.screenshot({
    path: join(screenshotsDir, 'acm-page-desktop-1920.png'),
    fullPage: true
  });

  // Get page info
  const title = await page.title();
  const url = page.url();
  console.log(`📄 Title: ${title}`);
  console.log(`🔗 URL: ${url}`);

  // Check for stats cards
  const statsCards = await page.locator('[class*="stat"], [data-testid*="stat"]').count();
  console.log(`📊 Stats cards found: ${statsCards}`);

  // Check for AG Grid
  const agGridRoot = await page.locator('.ag-root, .ag-root-wrapper').count();
  const agGridRows = await page.locator('.ag-row').count();
  console.log(`📋 AG Grid found: ${agGridRoot > 0 ? 'Yes' : 'No'}`);
  console.log(`📋 Grid rows: ${agGridRows}`);

  // Check for toolbar buttons
  const extractBtn = await page.locator('button:has-text("Extract"), button:has-text("extract")').count();
  const exportBtn = await page.locator('button:has-text("Export"), button:has-text("export")').count();
  const refreshBtn = await page.locator('button:has-text("Refresh"), button:has-text("refresh")').count();
  console.log(`🔘 Extract button: ${extractBtn > 0 ? 'Found' : 'Not found'}`);
  console.log(`🔘 Export button: ${exportBtn > 0 ? 'Found' : 'Not found'}`);
  console.log(`🔘 Refresh button: ${refreshBtn > 0 ? 'Found' : 'Not found'}`);

  // Check for source selector
  const sourceSelector = await page.locator('select, [role="combobox"]').count();
  console.log(`🎯 Source selector: ${sourceSelector > 0 ? 'Found' : 'Not found'}`);

  // Check for quick filter
  const quickFilter = await page.locator('input[placeholder*="filter" i], input[placeholder*="search" i]').count();
  console.log(`🔍 Quick filter: ${quickFilter > 0 ? 'Found' : 'Not found'}`);

  // Take mobile viewport screenshot
  console.log('📱 Taking mobile screenshot (768x1024)...');
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.waitForTimeout(500); // Allow responsive layout to render
  await page.screenshot({
    path: join(screenshotsDir, 'acm-page-mobile-768.png'),
    fullPage: true
  });

  // Get DOM snapshot
  console.log('💾 Saving HTML snapshot...');
  const html = await page.content();
  await writeFile(join(screenshotsDir, 'acm-page.html'), html, 'utf-8');

  // Test interactions if elements exist
  if (agGridRows > 0) {
    console.log('\n🧪 Testing interactions...');

    // Test column sorting
    await page.setViewportSize({ width: 1920, height: 1080 });
    const columnHeaders = await page.locator('.ag-header-cell').all();
    if (columnHeaders.length > 0) {
      console.log(`  ✓ Clicking first column header for sorting...`);
      await columnHeaders[0].click();
      await page.waitForTimeout(500);
      await page.screenshot({
        path: join(screenshotsDir, 'acm-page-sorted.png'),
        fullPage: true
      });
    }

    // Test quick filter if available
    if (quickFilter > 0) {
      console.log(`  ✓ Testing quick filter with "Fan Room"...`);
      const filterInput = page.locator('input[placeholder*="filter" i], input[placeholder*="search" i]').first();
      await filterInput.fill('Fan Room');
      await page.waitForTimeout(500);
      const filteredRows = await page.locator('.ag-row').count();
      console.log(`  ✓ Filtered rows: ${filteredRows}`);
      await page.screenshot({
        path: join(screenshotsDir, 'acm-page-filtered.png'),
        fullPage: true
      });
    }
  }

  // Generate bug report
  const bugs = [];

  if (agGridRoot === 0) {
    bugs.push({
      severity: 'Critical',
      component: 'AG Grid',
      description: 'AG Grid not found on page',
      expected: 'AG Grid should be present to display ACM records',
      actual: 'No AG Grid root element found'
    });
  }

  if (agGridRows === 0) {
    bugs.push({
      severity: 'Critical',
      component: 'Data Display',
      description: 'No records displayed in grid',
      expected: '8 ACM records should be displayed for Clutch_Broadmeadows.pdf',
      actual: 'Zero rows in grid'
    });
  }

  if (errors.length > 0) {
    bugs.push({
      severity: 'High',
      component: 'JavaScript',
      description: `${errors.length} JavaScript error(s) detected`,
      expected: 'No JavaScript errors',
      actual: errors.map(e => e.message).join('; ')
    });
  }

  // Save bug report
  const report = {
    timestamp: new Date().toISOString(),
    page: 'ACM Register',
    url: 'http://localhost:8502/acm',
    screenshots: [
      'acm-page-desktop-1920.png',
      'acm-page-mobile-768.png',
      'acm-page-sorted.png',
      'acm-page-filtered.png'
    ],
    elements: {
      statsCards,
      agGridRoot,
      agGridRows,
      extractBtn,
      exportBtn,
      refreshBtn,
      sourceSelector,
      quickFilter
    },
    errors,
    consoleMessages: consoleMessages.filter(m => m.type === 'error' || m.type === 'warning'),
    bugs
  };

  await writeFile(
    join(screenshotsDir, 'acm-page-report.json'),
    JSON.stringify(report, null, 2),
    'utf-8'
  );

  console.log('\n✅ Test completed successfully');
  console.log(`📊 ${bugs.length} bug(s) found`);
  console.log(`📸 Screenshots saved to: ${screenshotsDir}`);

} catch (error) {
  console.error('❌ Error:', error.message);
  await page.screenshot({
    path: join(screenshotsDir, 'acm-page-error.png'),
    fullPage: true
  });

  // Save error report
  await writeFile(
    join(screenshotsDir, 'acm-page-error.json'),
    JSON.stringify({ error: error.message, stack: error.stack }, null, 2),
    'utf-8'
  );
} finally {
  await browser.close();
  console.log('🔌 Browser closed');
}
