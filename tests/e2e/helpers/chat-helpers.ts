/**
 * Smart Chat Helpers
 *
 * Helper functions for testing Smart Chat functionality:
 * - Sending messages
 * - Verifying agent responses
 * - Testing tool calls
 * - Validating context switching
 *
 * Usage:
 *   import { sendChatMessage, waitForAgentResponse, verifyToolCall } from './chat-helpers';
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

/**
 * Get chat input element
 *
 * @param page - Playwright page object
 * @returns Locator - Chat input locator
 */
function getChatInput(page: Page): Locator {
  return page.locator('textarea[placeholder*="message" i], input[placeholder*="message" i]');
}

/**
 * Get send button
 *
 * @param page - Playwright page object
 * @returns Locator - Send button locator
 */
function getSendButton(page: Page): Locator {
  return page.getByRole('button', { name: /send/i });
}

/**
 * Send a chat message
 *
 * @param page - Playwright page object
 * @param message - Message text
 * @returns Promise<void>
 */
export async function sendChatMessage(page: Page, message: string): Promise<void> {
  const input = getChatInput(page);
  await expect(input).toBeVisible();
  await input.fill(message);

  const sendButton = getSendButton(page);
  await expect(sendButton).toBeEnabled();
  await sendButton.click();
}

/**
 * Wait for agent response
 *
 * Waits for agent typing indicator to disappear and response to appear.
 *
 * @param page - Playwright page object
 * @param timeout - Timeout in milliseconds (default: 30s)
 * @returns Promise<void>
 */
export async function waitForAgentResponse(
  page: Page,
  timeout = 30000
): Promise<void> {
  // Wait for typing indicator to appear (agent is thinking)
  const typingIndicator = page.locator('[data-testid="typing-indicator"]');
  await typingIndicator.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {
    // Typing indicator may be very brief, that's ok
  });

  // Wait for typing indicator to disappear (response ready)
  await typingIndicator.waitFor({ state: 'hidden', timeout });

  // Wait for message to appear in chat
  await page.waitForSelector('[data-testid="chat-message"]:last-child', { timeout: 5000 });
}

/**
 * Get last chat message
 *
 * @param page - Playwright page object
 * @returns Promise<string> - Message text
 */
export async function getLastChatMessage(page: Page): Promise<string> {
  const lastMessage = page.locator('[data-testid="chat-message"]:last-child');
  await expect(lastMessage).toBeVisible();
  const text = await lastMessage.textContent();
  return text || '';
}

/**
 * Verify tool call was made
 *
 * Checks for tool call indicators in chat interface.
 *
 * @param page - Playwright page object
 * @param toolName - Expected tool name (e.g., "get_acm_stats", "search_acm")
 * @returns Promise<boolean> - True if tool call found
 */
export async function verifyToolCall(
  page: Page,
  toolName: string
): Promise<boolean> {
  const toolCallIndicator = page.locator(`[data-tool="${toolName}"]`);
  return toolCallIndicator.isVisible();
}

/**
 * Verify tool result renderer
 *
 * Checks for tool result visualization (e.g., ACM table, stats chart).
 *
 * @param page - Playwright page object
 * @param resultType - Expected result type (e.g., "acm-table", "acm-stats")
 * @returns Promise<boolean> - True if result rendered
 */
export async function verifyToolResult(
  page: Page,
  resultType: string
): Promise<boolean> {
  const resultRenderer = page.locator(`[data-result-type="${resultType}"]`);
  return resultRenderer.isVisible();
}

/**
 * Switch chat mode
 *
 * Switches between normal chat and smart chat modes.
 *
 * @param page - Playwright page object
 * @param mode - Chat mode ('normal' | 'smart')
 * @returns Promise<void>
 */
export async function switchChatMode(
  page: Page,
  mode: 'normal' | 'smart'
): Promise<void> {
  const modeSwitch = page.getByRole('switch', { name: /smart chat|mode/i });
  await expect(modeSwitch).toBeVisible();

  const isSmartMode = await modeSwitch.isChecked();
  const targetSmartMode = mode === 'smart';

  if (isSmartMode !== targetSmartMode) {
    await modeSwitch.click();
  }

  // Verify mode switched
  await expect(modeSwitch).toHaveAttribute(
    'aria-checked',
    String(targetSmartMode)
  );
}

/**
 * Test ACM stats query
 *
 * Sends query for ACM statistics and verifies response.
 *
 * @param page - Playwright page object
 * @returns Promise<void>
 */
export async function testACMStatsQuery(page: Page): Promise<void> {
  await sendChatMessage(page, 'Show me ACM statistics');
  await waitForAgentResponse(page);

  // Verify tool call
  const toolCallMade = await verifyToolCall(page, 'get_acm_stats');
  expect(toolCallMade).toBeTruthy();

  // Verify result rendered
  const resultRendered = await verifyToolResult(page, 'acm-stats');
  expect(resultRendered).toBeTruthy();
}

/**
 * Test ACM search query
 *
 * Sends query to search ACM records and verifies results.
 *
 * @param page - Playwright page object
 * @param searchTerm - Search term (e.g., "fan room")
 * @returns Promise<void>
 */
export async function testACMSearchQuery(
  page: Page,
  searchTerm: string
): Promise<void> {
  await sendChatMessage(page, `Search ACM records for "${searchTerm}"`);
  await waitForAgentResponse(page);

  // Verify tool call
  const toolCallMade = await verifyToolCall(page, 'search_acm');
  expect(toolCallMade).toBeTruthy();

  // Verify result rendered (table)
  const resultRendered = await verifyToolResult(page, 'acm-table');
  expect(resultRendered).toBeTruthy();

  // Verify search term appears in results
  const lastMessage = await getLastChatMessage(page);
  expect(lastMessage.toLowerCase()).toContain(searchTerm.toLowerCase());
}

/**
 * Test context switch (chat → grid)
 *
 * Verifies clicking on ACM record in chat opens detail in grid.
 *
 * @param page - Playwright page object
 * @returns Promise<void>
 */
export async function testContextSwitch(page: Page): Promise<void> {
  // Send query that returns ACM records
  await sendChatMessage(page, 'Show me all positive ACM results');
  await waitForAgentResponse(page);

  // Click on first record in chat results
  const recordLink = page.locator('[data-testid="acm-record-link"]').first();
  await expect(recordLink).toBeVisible();
  await recordLink.click();

  // Verify navigation to ACM tab
  await page.waitForSelector('[data-testid="acm-grid"]', { timeout: 5000 });

  // Verify detail dialog opened
  const dialog = page.locator('[role="dialog"]');
  await expect(dialog).toBeVisible();
}

/**
 * Test agent error handling
 *
 * Sends invalid query and verifies graceful error handling.
 *
 * @param page - Playwright page object
 * @returns Promise<void>
 */
export async function testAgentErrorHandling(page: Page): Promise<void> {
  await sendChatMessage(page, 'invalid query %%% nonsense');
  await waitForAgentResponse(page);

  const lastMessage = await getLastChatMessage(page);

  // Should get helpful error message, not crash
  expect(lastMessage.toLowerCase()).toMatch(
    /sorry|error|understand|clarify|help/
  );
}

/**
 * Clear chat history
 *
 * @param page - Playwright page object
 * @returns Promise<void>
 */
export async function clearChatHistory(page: Page): Promise<void> {
  const clearButton = page.getByRole('button', { name: /clear|reset/i });
  await expect(clearButton).toBeVisible();
  await clearButton.click();

  // Confirm if dialog appears
  const confirmButton = page.getByRole('button', { name: /confirm|yes/i });
  if (await confirmButton.isVisible()) {
    await confirmButton.click();
  }

  // Verify chat is empty
  const messages = page.locator('[data-testid="chat-message"]');
  await expect(messages).toHaveCount(0);
}
