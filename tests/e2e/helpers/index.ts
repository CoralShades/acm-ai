/**
 * E2E Test Helpers - Central Export
 *
 * Re-exports all helper functions for easy importing.
 *
 * Usage:
 *   import { uploadARA, captureEvidence, sendChatMessage } from '../helpers';
 */

// ACM Helpers
export {
  uploadARA,
  waitForExtraction,
  navigateToACMRegister,
  getACMGridRows,
  getACMRecordCount,
  validateACMGrid,
  searchACMGrid,
  getACMRecordDetails,
  exportACMRecords,
} from './acm-helpers';

// Screenshot Helpers
export {
  captureEvidence,
  captureWorkflow,
  captureComparison,
  captureElement,
  captureGridState,
  captureError,
  captureMobileView,
} from './screenshot-helpers';

// Chat Helpers
export {
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
} from './chat-helpers';
