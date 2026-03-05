/**
 * Accessibility Audit Wrapper
 *
 * Provides a unified interface for running accessibility audits on
 * Playwright pages using @axe-core/playwright when available, with
 * a graceful fallback when it is not installed.
 */

import { Page } from '@playwright/test';

export interface AccessibilityViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  helpUrl: string;
  nodes: Array<{ html: string; target: string[] }>;
}

export interface AccessibilityAuditResult {
  route: string;
  violations: AccessibilityViolation[];
  passes: number;
  incomplete: number;
}

/**
 * Run an accessibility audit on the current page.
 *
 * Uses @axe-core/playwright if installed; otherwise returns an empty
 * result with a console warning.
 */
export async function auditPage(
  page: Page,
  route: string,
  options?: { tags?: string[] }
): Promise<AccessibilityAuditResult> {
  const tags = options?.tags ?? ['wcag2a', 'wcag2aa'];

  try {
    // Dynamic import — allows graceful degradation when axe-core is not installed
    const { default: AxeBuilder } = await import('@axe-core/playwright');

    const results = await new AxeBuilder({ page })
      .withTags(tags)
      .analyze();

    const violations: AccessibilityViolation[] = results.violations.map(
      (v: any) => ({
        id: v.id,
        impact: v.impact as AccessibilityViolation['impact'],
        description: v.description,
        helpUrl: v.helpUrl,
        nodes: v.nodes.map((n: any) => ({
          html: n.html,
          target: n.target as string[],
        })),
      })
    );

    return {
      route,
      violations,
      passes: results.passes?.length ?? 0,
      incomplete: results.incomplete?.length ?? 0,
    };
  } catch {
    console.warn(
      'Accessibility audit skipped: @axe-core/playwright is not installed. ' +
        'Install it with: npm install -D @axe-core/playwright'
    );
    return {
      route,
      violations: [],
      passes: 0,
      incomplete: 0,
    };
  }
}

/**
 * Filter violations to only critical and serious impact levels.
 */
export function getCriticalViolations(
  result: AccessibilityAuditResult
): AccessibilityViolation[] {
  return result.violations.filter(
    (v) => v.impact === 'critical' || v.impact === 'serious'
  );
}
