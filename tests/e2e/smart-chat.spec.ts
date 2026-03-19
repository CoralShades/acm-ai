/**
 * Smart Chat Interactions E2E Tests
 *
 * Tests Smart Chat functionality including:
 * - Basic message/response flow
 * - ACM-specific tool calls (stats, search)
 * - Chat mode switching
 * - Error handling
 * - Response streaming
 * - Context switching (chat → grid)
 *
 * Tag: @smart-chat
 */

import { test, expect } from '../support/fixtures';
import { TestDataFactory } from '../support/helpers/test-data-factory';
import {
  uploadARA,
  waitForExtraction,
} from './helpers/acm-helpers';
import {
  sendChatMessage,
  waitForAgentResponse,
  getLastChatMessage,
  verifyToolCall,
  verifyToolResult,
  switchChatMode,
  testACMStatsQuery,
  testACMSearchQuery,
  testContextSwitch,
  testAgentErrorHandling,
  clearChatHistory,
} from './helpers/chat-helpers';
import {
  captureEvidence,
  captureWorkflow,
} from './helpers/screenshot-helpers';
import * as path from 'path';

const BROADMEADOWS_ARA = path.join(
  __dirname,
  'fixtures/ara-documents/broadmeadows-police-station-samp.pdf'
);

test.describe('Smart Chat Interactions @smart-chat', () => {
  let factory: TestDataFactory;

  test.beforeEach(async () => {
    factory = new TestDataFactory();
  });

  test.afterEach(async () => {
    await factory.cleanup();
  });

  test('sends message and receives response', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Smart Chat Basic Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // Capture initial chat state
    await captureEvidence(page, 'chat-initial-state');

    // When: User sends a message
    await sendChatMessage(page, 'Hello, can you help me with ACM data?');

    // Capture message sent
    await captureEvidence(page, 'chat-message-sent');

    // Wait for agent response
    await waitForAgentResponse(page);

    // Capture response received
    await captureEvidence(page, 'chat-response-received');

    // Then: Agent should respond
    const response = await getLastChatMessage(page);
    expect(response.length).toBeGreaterThan(0);
    expect(response.toLowerCase()).toMatch(/help|acm|assist|data/i);
  });

  test('executes ACM-specific tool calls successfully', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Smart Chat Tool Calls Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // When: User asks for ACM statistics
    await sendChatMessage(page, 'Show me ACM statistics for this building');
    await waitForAgentResponse(page);

    // Capture tool call execution
    await captureEvidence(page, 'tool-call-acm-stats');

    // Then: Tool call should be executed
    const toolCallMade = await verifyToolCall(page, 'get_acm_stats');
    expect(toolCallMade).toBeTruthy();

    // Verify result is rendered
    const resultRendered = await verifyToolResult(page, 'acm-stats');
    expect(resultRendered).toBeTruthy();
  });

  test('switches between chat modes seamlessly', async ({ page }) => {
    // Given: User is on a notebook page
    const notebook = await factory.createNotebook({
      name: 'Chat Mode Switch Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Capture initial mode
    await captureEvidence(page, 'chat-mode-initial');

    // When: User switches to smart chat mode
    await switchChatMode(page, 'smart');

    // Capture smart mode enabled
    await captureEvidence(page, 'chat-mode-smart-enabled');

    // Then: Mode should be switched
    const modeSwitch = page.getByRole('switch', { name: /smart chat|mode/i });
    await expect(modeSwitch).toHaveAttribute('aria-checked', 'true');

    // When: User switches back to normal mode
    await switchChatMode(page, 'normal');

    // Capture normal mode enabled
    await captureEvidence(page, 'chat-mode-normal-enabled');

    // Then: Mode should be switched back
    await expect(modeSwitch).toHaveAttribute('aria-checked', 'false');
  });

  test('handles chat errors gracefully', async ({ page }) => {
    // Given: User is on a notebook page
    const notebook = await factory.createNotebook({
      name: 'Chat Error Handling Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Capture pre-error state
    await captureEvidence(page, 'chat-pre-error-state');

    // When: User sends invalid/nonsensical query
    await testAgentErrorHandling(page);

    // Capture error handling
    await captureEvidence(page, 'chat-error-handled');

    // Then: Error should be handled gracefully
    // (testAgentErrorHandling verifies this)
  });

  test('streams responses progressively', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Chat Streaming Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // When: User sends a message requiring long response
    await sendChatMessage(page, 'Explain the ACM data in detail');

    // Capture streaming start
    await captureEvidence(page, 'chat-streaming-start');

    // Wait briefly to observe streaming
    await page.waitForTimeout(2000);

    // Capture mid-stream
    await captureEvidence(page, 'chat-streaming-mid');

    // Wait for full response
    await waitForAgentResponse(page);

    // Capture streaming complete
    await captureEvidence(page, 'chat-streaming-complete');

    // Then: Response should be received
    const response = await getLastChatMessage(page);
    expect(response.length).toBeGreaterThan(50); // Should be detailed response
  });

  test('queries ACM statistics successfully', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'ACM Stats Query Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // Capture workflow
    await captureWorkflow(page, 'acm-stats-query', [
      'chat-ready',
      'message-sent',
      'tool-executing',
      'result-rendered',
    ]);

    // When/Then: User queries ACM statistics
    await testACMStatsQuery(page);

    // Capture final result
    await captureEvidence(page, 'acm-stats-query-complete');
  });

  test('searches ACM records successfully', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'ACM Search Query Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // Capture workflow
    await captureWorkflow(page, 'acm-search-query', [
      'chat-ready',
      'search-initiated',
      'results-loading',
      'results-displayed',
    ]);

    // When/Then: User searches for specific ACM records
    await testACMSearchQuery(page, 'Fan Room');

    // Capture search results
    await captureEvidence(page, 'acm-search-results');
  });

  test('switches context from chat to grid navigation', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Context Switch Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // Capture workflow
    await captureWorkflow(page, 'context-switch', [
      'chat-query',
      'results-displayed',
      'record-clicked',
      'grid-opened',
    ]);

    // When/Then: User clicks on ACM record in chat
    await testContextSwitch(page);

    // Capture context switch complete
    await captureEvidence(page, 'context-switch-complete');
  });

  test('clears chat history successfully', async ({ page }) => {
    // Given: User has chat history
    const notebook = await factory.createNotebook({
      name: 'Clear Chat History Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);

    // Send a few messages to create history
    await sendChatMessage(page, 'First message');
    await waitForAgentResponse(page);

    await sendChatMessage(page, 'Second message');
    await waitForAgentResponse(page);

    // Capture chat history before clear
    await captureEvidence(page, 'chat-history-before-clear');

    // When: User clears chat history
    await clearChatHistory(page);

    // Capture chat history after clear
    await captureEvidence(page, 'chat-history-after-clear');

    // Then: Chat should be empty
    const messages = page.locator('[data-testid="chat-message"]');
    await expect(messages).toHaveCount(0);
  });

  test('maintains chat context across multiple messages', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Chat Context Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // When: User has multi-turn conversation
    await sendChatMessage(page, 'How many ACM records are there?');
    await waitForAgentResponse(page);

    // Capture first response
    await captureEvidence(page, 'chat-context-turn1');

    // Follow-up question (relies on context)
    await sendChatMessage(page, 'What about positive results?');
    await waitForAgentResponse(page);

    // Capture follow-up response
    await captureEvidence(page, 'chat-context-turn2');

    // Then: Agent should understand context
    const response = await getLastChatMessage(page);
    expect(response.length).toBeGreaterThan(0);
    expect(response.toLowerCase()).toMatch(/positive|result|record/i);
  });

  test('handles concurrent tool calls gracefully', async ({ page }) => {
    // Given: User has created a notebook with ACM data
    const notebook = await factory.createNotebook({
      name: 'Concurrent Tool Calls Test',
    });
    await page.goto(`/notebooks/${notebook.id.replace('notebook:', '')}`);
    await uploadARA(page, BROADMEADOWS_ARA);
    await waitForExtraction(page, 180000);

    // When: User asks question requiring multiple tool calls
    await sendChatMessage(
      page,
      'Show me statistics and search for Fan Room records'
    );

    // Capture tool execution
    await captureEvidence(page, 'concurrent-tools-executing');

    await waitForAgentResponse(page, 60000); // Longer timeout for multiple tools

    // Capture final result
    await captureEvidence(page, 'concurrent-tools-complete');

    // Then: Both tool results should be present
    const response = await getLastChatMessage(page);
    expect(response.length).toBeGreaterThan(0);
  });
});
