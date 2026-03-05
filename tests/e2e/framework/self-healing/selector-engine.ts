/**
 * Self-Healing Selector Engine
 *
 * Tries multiple selector strategies in priority order to find elements,
 * enabling tests to self-heal when selectors break due to UI changes.
 */

import { Page, Locator } from '@playwright/test';
import {
  SelectorStrategy,
  STRATEGY_CHAIN,
  HealingConfig,
  DEFAULT_CONFIG,
} from './config';

export interface ElementContext {
  originalSelector: string;
  semanticRole?: string;
  textContent?: string;
  ariaLabel?: string;
  testId?: string;
  parentContext?: string;
}

export interface HealingResult {
  locator: Locator;
  strategy: SelectorStrategy;
  confidence: number;
  suggestedFix?: string;
  healingLog: string;
}

export class SelectorEngine {
  private config: HealingConfig;
  private healingActions: HealingResult[] = [];

  constructor(config?: HealingConfig) {
    this.config = config ?? { ...DEFAULT_CONFIG };
  }

  /**
   * Resolve an element using the strategy chain. Tries each strategy in
   * priority order and returns the first one that finds a visible element.
   */
  async resolve(page: Page, context: ElementContext): Promise<HealingResult> {
    for (const { strategy, confidence } of STRATEGY_CHAIN) {
      const locator = this.buildLocator(page, strategy, context);
      if (!locator) continue;

      try {
        const isVisible = await locator
          .first()
          .isVisible({ timeout: 1000 })
          .catch(() => false);

        if (isVisible) {
          const result: HealingResult = {
            locator: locator.first(),
            strategy,
            confidence,
            suggestedFix: this.buildSuggestedFix(strategy, context),
            healingLog: `Resolved "${context.originalSelector}" via ${strategy} (confidence: ${confidence})`,
          };
          this.healingActions.push(result);
          return result;
        }
      } catch {
        // Strategy failed, try next
      }
    }

    throw new Error(
      `Self-healing failed: could not resolve element for selector "${context.originalSelector}" ` +
        `after trying ${STRATEGY_CHAIN.length} strategies`
    );
  }

  /**
   * Get the accumulated healing log.
   */
  getHealingLog(): HealingResult[] {
    return [...this.healingActions];
  }

  /**
   * Clear the healing log.
   */
  clearLog(): void {
    this.healingActions = [];
  }

  /**
   * Build a Playwright locator for the given strategy and context.
   * Returns null if the context doesn't have enough information for
   * that strategy.
   */
  private buildLocator(
    page: Page,
    strategy: SelectorStrategy,
    context: ElementContext
  ): Locator | null {
    switch (strategy) {
      case SelectorStrategy.DATA_TESTID:
        if (!context.testId) return null;
        return page.locator(`[data-testid="${context.testId}"]`);

      case SelectorStrategy.ROLE_NAME:
        if (!context.semanticRole) return null;
        return page.getByRole(context.semanticRole as any, {
          name: context.textContent,
        });

      case SelectorStrategy.ARIA_LABEL:
        if (!context.ariaLabel) return null;
        return page.getByLabel(context.ariaLabel);

      case SelectorStrategy.TEXT_CONTENT:
        if (!context.textContent) return null;
        return page.getByText(context.textContent);

      case SelectorStrategy.CSS:
        if (!context.originalSelector) return null;
        return page.locator(context.originalSelector);

      case SelectorStrategy.XPATH:
        // XPATH is a last-resort fallback; skip in the automatic chain
        return null;

      default:
        return null;
    }
  }

  /**
   * Generate a suggestion for how to fix the original test selector
   * based on the strategy that actually worked.
   */
  private buildSuggestedFix(
    strategy: SelectorStrategy,
    context: ElementContext
  ): string | undefined {
    switch (strategy) {
      case SelectorStrategy.DATA_TESTID:
        return undefined; // Already the best strategy
      case SelectorStrategy.ROLE_NAME:
        return `Consider adding data-testid. Element was found via role="${context.semanticRole}" name="${context.textContent}"`;
      case SelectorStrategy.ARIA_LABEL:
        return `Consider adding data-testid. Element was found via aria-label="${context.ariaLabel}"`;
      case SelectorStrategy.TEXT_CONTENT:
        return `Add data-testid to element found via text content "${context.textContent}" for more stable selection`;
      case SelectorStrategy.CSS:
        return `CSS selector "${context.originalSelector}" is fragile. Add data-testid for stability`;
      case SelectorStrategy.XPATH:
        return `XPATH fallback used — element needs a data-testid attribute urgently`;
      default:
        return undefined;
    }
  }
}
