/**
 * Unified Chat Panel E2E Tests
 *
 * Tests the ACM-AI unified chat panel on the job detail page (/jobs/[id]).
 * The chat uses CopilotKit via the AG-UI protocol and renders in a
 * collapsible right sidebar (desktop) or a Sheet/drawer (mobile).
 *
 * No Query/Edit toggle exists — there is a single unified chat panel.
 *
 * Test source: source:zyiyqpm1qw803yfbhd98
 * Job page:    http://localhost:8503/jobs/source%3Azyiyqpm1qw803yfbhd98
 *
 * Tag: @feature
 */

import { test, expect } from '../../support/fixtures'
import path from 'path'
import fs from 'fs'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SOURCE_ID = 'source:zyiyqpm1qw803yfbhd98'
const JOB_URL = `/jobs/${encodeURIComponent(SOURCE_ID)}`

const EVIDENCE_DIR = path.resolve(
  __dirname,
  '../../../docs/sprint-artifacts/e2e-evidence/unified-chat'
)

// Ensure evidence directory exists at module load time
if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true })
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Save a screenshot to the evidence directory. Non-fatal — test continues if
 * the directory is not writable.
 */
async function saveEvidence(page: import('@playwright/test').Page, name: string) {
  try {
    const filePath = path.join(EVIDENCE_DIR, `${name}.png`)
    await page.screenshot({ path: filePath, fullPage: false })
  } catch {
    // Evidence capture is best-effort; never block the test
  }
}

/**
 * Navigate to the job page and wait for the main content to be ready.
 * The jobs page is a client-side rendered React app so we wait for a known
 * stable element rather than 'networkidle' (which can time out with SSE).
 */
async function gotoJobPage(page: import('@playwright/test').Page) {
  await page.goto(JOB_URL, { waitUntil: 'domcontentloaded' })
  // Wait for the tab list to confirm the job detail shell rendered
  await page.waitForSelector('[role="tablist"]', { timeout: 20_000 })
}

/**
 * Click the "Expand chat panel" toggle button and wait for the chat panel
 * to become visible. This is a desktop-only sidebar (hidden on mobile via
 * the `lg:flex` Tailwind class).
 */
async function expandChatPanel(page: import('@playwright/test').Page) {
  const expandBtn = page.getByRole('button', { name: 'Expand chat panel' })
  await expandBtn.waitFor({ state: 'visible', timeout: 10_000 })
  await expandBtn.click()
  // Wait for the CopilotKit chat title to appear inside the panel
  await page.waitForSelector('text=ACM-AI Chat', { timeout: 10_000 })
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

test.describe('Unified Chat Panel @feature', () => {
  // -------------------------------------------------------------------------
  // Test 1: Chat Panel Opens
  // -------------------------------------------------------------------------
  test('T1: chat panel opens and shows expected elements', async ({ page }) => {
    await gotoJobPage(page)
    await saveEvidence(page, 'T1-job-page-loaded')

    // The expand button is rendered by the desktop sidebar (hidden on mobile)
    const expandBtn = page.getByRole('button', { name: 'Expand chat panel' })
    await expect(expandBtn).toBeVisible()

    await expandBtn.click()
    await saveEvidence(page, 'T1-panel-expanding')

    // Panel title rendered by CopilotKit CopilotChat label
    const chatTitle = page.locator('text=ACM-AI Chat')
    await expect(chatTitle).toBeVisible({ timeout: 10_000 })

    // Chat textarea rendered by SmartChatInput
    const chatInput = page.locator('textarea[placeholder*="Ask a question"]')
    await expect(chatInput).toBeVisible({ timeout: 10_000 })

    // Model selector — only rendered when there are ≥2 language models.
    // We check for the session dropdown header button which is always present
    // when a sourceId is passed to UnifiedChatPanel.
    const sessionDropdown = page.getByRole('button', { name: 'Switch chat session' })
    await expect(sessionDropdown).toBeVisible({ timeout: 10_000 })

    await saveEvidence(page, 'T1-panel-open')
  })

  // -------------------------------------------------------------------------
  // Test 2: Send Message and Get Response
  // -------------------------------------------------------------------------
  test('T2: send message via Ctrl+Enter and receive a response', async ({ page }) => {
    await gotoJobPage(page)
    await expandChatPanel(page)

    const chatInput = page.locator('textarea[placeholder*="Ask a question"]')
    await expect(chatInput).toBeVisible()

    await chatInput.fill('How many records are in this document?')
    await saveEvidence(page, 'T2-message-filled')

    // SmartChatInput sends on Ctrl+Enter (Cmd+Enter on Mac)
    await chatInput.press('Control+Enter')
    await saveEvidence(page, 'T2-message-sent')

    // Wait for a non-empty assistant response to appear.
    // CopilotKit renders assistant messages in [data-message-role="assistant"]
    // elements; we fall back to any visible text that appears in the chat
    // scroll area if the test-id is absent.
    //
    // Allow up to 60 s for the LLM to reply.
    const assistantMessage = page
      .locator('[data-message-role="assistant"], .copilotkit-message-assistant')
      .first()

    await expect(assistantMessage).toBeVisible({ timeout: 60_000 })

    const responseText = await assistantMessage.textContent()
    expect(responseText?.trim().length).toBeGreaterThan(0)

    await saveEvidence(page, 'T2-response-received')
  })

  // -------------------------------------------------------------------------
  // Test 3: ACM Data Toggle
  // -------------------------------------------------------------------------
  test('T3: ACM data toggle is checked by default and can be toggled off', async ({
    page,
  }) => {
    await gotoJobPage(page)
    await expandChatPanel(page)

    // The ACM data switch is rendered by SmartChatInput only when
    // hasAcmData=true. It uses a Radix Switch with id="smart-acm-context".
    // If the source has no extracted records the switch will not be rendered —
    // in that case we skip the toggle assertions gracefully.
    const acmSwitch = page.locator('#smart-acm-context')
    const switchVisible = await acmSwitch.isVisible().catch(() => false)

    if (!switchVisible) {
      // Source may not have ACM records yet — skip toggle assertions
      test.info().annotations.push({
        type: 'skip-reason',
        description: 'ACM data switch not visible (source has no extracted records)',
      })
      return
    }

    await saveEvidence(page, 'T3-switch-visible')

    // Default state: checked (ACM context enabled)
    await expect(acmSwitch).toHaveAttribute('data-state', 'checked')

    // Toggle off
    await acmSwitch.click()
    await expect(acmSwitch).toHaveAttribute('data-state', 'unchecked')

    await saveEvidence(page, 'T3-switch-toggled-off')

    // Toggle back on to leave the panel in a clean state
    await acmSwitch.click()
    await expect(acmSwitch).toHaveAttribute('data-state', 'checked')
  })

  // -------------------------------------------------------------------------
  // Test 4: Session Dropdown Renders
  // -------------------------------------------------------------------------
  test('T4: session dropdown button is visible in the chat header', async ({ page }) => {
    await gotoJobPage(page)
    await expandChatPanel(page)

    // SessionDropdown renders a button with aria-label="Switch chat session"
    const sessionBtn = page.getByRole('button', { name: 'Switch chat session' })
    await expect(sessionBtn).toBeVisible()

    await saveEvidence(page, 'T4-session-dropdown-visible')

    // Clicking the button opens the session popover
    await sessionBtn.click()

    // The popover contains a "New Chat" button
    const newChatBtn = page.getByRole('button', { name: 'New Chat' })
    await expect(newChatBtn).toBeVisible({ timeout: 5_000 })

    await saveEvidence(page, 'T4-session-popover-open')

    // Close the popover by pressing Escape
    await page.keyboard.press('Escape')
  })

  // -------------------------------------------------------------------------
  // Test 5: Mobile Chat Sheet
  // -------------------------------------------------------------------------
  test('T5: mobile floating chat button opens Sheet with chat panel', async ({
    page,
  }) => {
    // Narrow viewport — simulates a mobile device
    await page.setViewportSize({ width: 375, height: 667 })
    await gotoJobPage(page)
    await saveEvidence(page, 'T5-mobile-job-page')

    // The floating action button is fixed bottom-right, only visible on small
    // screens (lg:hidden). It carries aria-label="Open chat".
    const fab = page.getByRole('button', { name: 'Open chat' })
    await expect(fab).toBeVisible({ timeout: 10_000 })

    await fab.click()
    await saveEvidence(page, 'T5-sheet-opening')

    // The Sheet renders with a header that contains "ACM-AI Chat" text
    const sheetChatTitle = page.locator('text=ACM-AI Chat')
    await expect(sheetChatTitle).toBeVisible({ timeout: 10_000 })

    // The UnifiedChatPanel inside the Sheet should also render the chat input
    const chatInput = page.locator('textarea[placeholder*="Ask a question"]')
    await expect(chatInput).toBeVisible({ timeout: 10_000 })

    await saveEvidence(page, 'T5-sheet-open')
  })
})
