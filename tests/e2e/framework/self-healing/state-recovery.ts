/**
 * State Recovery
 *
 * Implements multi-level recovery when E2E tests encounter stuck or
 * degraded application states. Escalates through wait, refresh, and
 * full reset strategies.
 */

import { Page } from '@playwright/test';

export enum RecoveryState {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  STUCK = 'stuck',
  RECOVERING = 'recovering',
  FAILED = 'failed',
}

export class StateRecovery {
  private state: RecoveryState = RecoveryState.HEALTHY;
  private attemptCount: number = 0;

  /**
   * Attempt to recover the page to a usable state.
   * Escalates through increasingly aggressive recovery levels.
   *
   * @returns true if recovery succeeded, false if all levels exhausted
   */
  async recover(page: Page, url: string): Promise<boolean> {
    try {
      if (this.attemptCount === 0) {
        // Level 1: Simple wait — maybe the page is just slow
        this.state = RecoveryState.DEGRADED;
        this.attemptCount++;
        await page.waitForTimeout(2000);
        return true;
      }

      if (this.attemptCount === 1) {
        // Level 2: Refresh and re-navigate
        this.state = RecoveryState.STUCK;
        this.attemptCount++;
        await page.reload({ waitUntil: 'networkidle' });
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        return true;
      }

      if (this.attemptCount === 2) {
        // Level 3: Full reset — clear all state and start fresh
        this.state = RecoveryState.RECOVERING;
        this.attemptCount++;
        await page.context().clearCookies();
        await page.evaluate(() => localStorage.clear());
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        return true;
      }

      // Level 4+: All recovery levels exhausted
      this.state = RecoveryState.FAILED;
      this.attemptCount++;
      return false;
    } catch {
      // If recovery itself fails, mark as failed
      this.state = RecoveryState.FAILED;
      this.attemptCount++;
      return false;
    }
  }

  /**
   * Reset recovery state back to healthy.
   */
  reset(): void {
    this.state = RecoveryState.HEALTHY;
    this.attemptCount = 0;
  }

  /**
   * Get the current recovery state.
   */
  getState(): RecoveryState {
    return this.state;
  }
}
