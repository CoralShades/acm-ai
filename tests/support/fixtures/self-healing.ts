/**
 * Self-Healing Playwright Fixtures
 *
 * Provides HealingPage (wrapping standard Page), EvidenceCollector,
 * and APIContractValidator as Playwright fixtures.
 *
 * Usage:
 *   import { test, expect } from '../support/fixtures';
 *   test('my test', async ({ healingPage, evidence, apiValidator }) => { ... });
 */

import { Page, Locator } from '@playwright/test';
import { SelectorEngine, ElementContext, HealingResult } from '../../e2e/framework/self-healing/selector-engine';
import { StateRecovery } from '../../e2e/framework/self-healing/state-recovery';
import { EvidenceCollector, EvidenceBundle } from '../../e2e/framework/self-healing/evidence-collector';
import { APIContractValidator } from '../../e2e/framework/self-healing/api-contract-validator';
import { DEFAULT_CONFIG } from '../../e2e/framework/self-healing/config';

/**
 * HealingPage wraps a standard Playwright Page with self-healing capabilities.
 * On selector failure, it falls back through the strategy chain before giving up.
 */
export class HealingPage {
  private engine: SelectorEngine;
  private recovery: StateRecovery;
  private evidence: EvidenceCollector;

  constructor(
    public readonly page: Page,
    engine?: SelectorEngine,
    recovery?: StateRecovery,
    evidence?: EvidenceCollector
  ) {
    this.engine = engine ?? new SelectorEngine();
    this.recovery = recovery ?? new StateRecovery();
    this.evidence = evidence ?? new EvidenceCollector();
    this.evidence.attach(page);
  }

  /**
   * Click an element with self-healing fallback.
   * If the primary selector fails, the engine tries alternatives.
   */
  async healingClick(selector: string, context?: Partial<ElementContext>): Promise<HealingResult | null> {
    const fullContext: ElementContext = { originalSelector: selector, ...context };

    // Try the original selector first
    try {
      const locator = this.page.locator(selector);
      await locator.first().click({ timeout: DEFAULT_CONFIG.selectorTimeout });
      return null; // No healing needed
    } catch {
      // Original failed — try self-healing
    }

    const result = await this.engine.resolve(this.page, fullContext);
    await result.locator.click({ timeout: DEFAULT_CONFIG.selectorTimeout });
    return result;
  }

  /**
   * Fill an input element with self-healing fallback.
   */
  async healingFill(selector: string, value: string, context?: Partial<ElementContext>): Promise<HealingResult | null> {
    const fullContext: ElementContext = { originalSelector: selector, ...context };

    try {
      const locator = this.page.locator(selector);
      await locator.first().fill(value, { timeout: DEFAULT_CONFIG.selectorTimeout });
      return null;
    } catch {
      // Original failed — try self-healing
    }

    const result = await this.engine.resolve(this.page, fullContext);
    await result.locator.fill(value, { timeout: DEFAULT_CONFIG.selectorTimeout });
    return result;
  }

  /**
   * Wait for an element with self-healing fallback.
   */
  async healingWaitFor(selector: string, context?: Partial<ElementContext>): Promise<HealingResult | null> {
    const fullContext: ElementContext = { originalSelector: selector, ...context };

    try {
      await this.page.locator(selector).first().waitFor({
        state: 'visible',
        timeout: DEFAULT_CONFIG.selectorTimeout,
      });
      return null;
    } catch {
      // Original failed — try self-healing
    }

    const result = await this.engine.resolve(this.page, fullContext);
    await result.locator.waitFor({
      state: 'visible',
      timeout: DEFAULT_CONFIG.selectorTimeout,
    });
    return result;
  }

  /**
   * Navigate with state recovery on failure.
   */
  async healingGoto(url: string): Promise<boolean> {
    try {
      await this.page.goto(url, { waitUntil: 'domcontentloaded' });
      this.recovery.reset();
      return true;
    } catch {
      return this.recovery.recover(this.page, url);
    }
  }

  /**
   * Get all healing actions recorded during this session.
   */
  getHealingLog(): HealingResult[] {
    return this.engine.getHealingLog();
  }

  /**
   * Collect evidence (screenshot, logs, network) for the current state.
   */
  async collectEvidence(testName: string): Promise<EvidenceBundle> {
    return this.evidence.captureEvidence(this.page, testName);
  }

  /**
   * Clean up — call in fixture teardown.
   */
  reportHealings(): HealingResult[] {
    const log = this.engine.getHealingLog();
    this.engine.clearLog();
    this.evidence.detach();
    this.recovery.reset();
    return log;
  }
}

// Re-export types for convenience
export type { EvidenceBundle, ElementContext, HealingResult };
export { EvidenceCollector, APIContractValidator, SelectorEngine, StateRecovery };
