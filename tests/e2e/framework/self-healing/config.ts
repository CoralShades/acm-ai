/**
 * Self-Healing Configuration
 *
 * Defines thresholds, selector strategies, and recovery levels
 * for the self-healing E2E test framework.
 */

export enum SelectorStrategy {
  DATA_TESTID = 'data-testid',
  ROLE_NAME = 'role-name',
  ARIA_LABEL = 'aria-label',
  TEXT_CONTENT = 'text-content',
  CSS = 'css',
  XPATH = 'xpath',
}

export interface StrategyPriority {
  strategy: SelectorStrategy;
  confidence: number;
}

export const STRATEGY_CHAIN: StrategyPriority[] = [
  { strategy: SelectorStrategy.DATA_TESTID, confidence: 1.0 },
  { strategy: SelectorStrategy.ROLE_NAME, confidence: 0.95 },
  { strategy: SelectorStrategy.ARIA_LABEL, confidence: 0.9 },
  { strategy: SelectorStrategy.TEXT_CONTENT, confidence: 0.8 },
  { strategy: SelectorStrategy.CSS, confidence: 0.6 },
  { strategy: SelectorStrategy.XPATH, confidence: 0.4 },
];

export enum RecoveryLevel {
  WAIT = 'wait',
  REFRESH = 'refresh',
  RESET = 'reset',
  FAIL = 'fail',
}

export interface HealingConfig {
  selectorTimeout: number;
  maxHealAttempts: number;
  visualDiffTolerance: number;
  recoveryLevels: RecoveryLevel[];
  evidenceDir: string;
  reportDir: string;
}

export const DEFAULT_CONFIG: HealingConfig = {
  selectorTimeout: 5000,
  maxHealAttempts: 3,
  visualDiffTolerance: 0.001,
  recoveryLevels: [RecoveryLevel.WAIT, RecoveryLevel.REFRESH, RecoveryLevel.RESET, RecoveryLevel.FAIL],
  evidenceDir: 'test-results/evidence',
  reportDir: 'test-results',
};
