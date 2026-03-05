/**
 * Healing Reporter
 *
 * Aggregates test results, healing actions, and route coverage into
 * a structured report with actionable recommendations.
 */

import * as path from 'path';
import * as fs from 'fs';
import { HealingResult } from './selector-engine';
import { EvidenceBundle } from './evidence-collector';

const REPORT_DIR = path.join(__dirname, '../../../../test-results');

export interface HealingReport {
  timestamp: string;
  totalTests: number;
  passed: number;
  failed: number;
  healed: number;
  skipped: number;
  healingActions: HealingResult[];
  recommendations: Array<{
    type: string;
    message: string;
    file?: string;
    selector?: string;
  }>;
  routeCoverage: Record<string, 'tested' | 'untested' | 'failed'>;
}

export interface TestResult {
  status: 'passed' | 'failed' | 'healed' | 'skipped';
  healingActions: HealingResult[];
  evidence?: EvidenceBundle;
}

export class HealingReporter {
  private results: Map<string, TestResult> = new Map();
  private routeCoverage: Map<string, 'tested' | 'untested' | 'failed'> = new Map();

  /**
   * Record the result of a test.
   */
  addResult(
    testName: string,
    status: TestResult['status'],
    healingActions?: HealingResult[],
    evidence?: EvidenceBundle
  ): void {
    this.results.set(testName, {
      status,
      healingActions: healingActions ?? [],
      evidence,
    });
  }

  /**
   * Record the coverage status of a route.
   */
  addRouteCoverage(
    route: string,
    status: 'tested' | 'untested' | 'failed'
  ): void {
    this.routeCoverage.set(route, status);
  }

  /**
   * Generate the full healing report.
   */
  generateReport(): HealingReport {
    let passed = 0;
    let failed = 0;
    let healed = 0;
    let skipped = 0;
    const allHealingActions: HealingResult[] = [];

    for (const result of this.results.values()) {
      switch (result.status) {
        case 'passed':
          passed++;
          break;
        case 'failed':
          failed++;
          break;
        case 'healed':
          healed++;
          break;
        case 'skipped':
          skipped++;
          break;
      }
      allHealingActions.push(...result.healingActions);
    }

    const recommendations = this.getRecommendations();
    const routeCoverage: Record<string, 'tested' | 'untested' | 'failed'> = {};
    for (const [route, status] of this.routeCoverage.entries()) {
      routeCoverage[route] = status;
    }

    return {
      timestamp: new Date().toISOString(),
      totalTests: this.results.size,
      passed,
      failed,
      healed,
      skipped,
      healingActions: allHealingActions,
      recommendations,
      routeCoverage,
    };
  }

  /**
   * Save the report to disk as JSON.
   * @returns Absolute path to the saved report file.
   */
  saveReport(outputDir?: string): string {
    const dir = outputDir ?? REPORT_DIR;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const filepath = path.join(dir, 'healing-report.json');
    const report = this.generateReport();
    fs.writeFileSync(filepath, JSON.stringify(report, null, 2), 'utf-8');
    return filepath;
  }

  /**
   * Generate actionable recommendations from healing actions.
   */
  getRecommendations(): Array<{
    type: string;
    message: string;
    file?: string;
    selector?: string;
  }> {
    const recommendations: Array<{
      type: string;
      message: string;
      file?: string;
      selector?: string;
    }> = [];

    const seen = new Set<string>();

    for (const result of this.results.values()) {
      for (const action of result.healingActions) {
        // Only recommend for non-ideal strategies
        if (action.strategy === 'data-testid') continue;

        const key = `${action.strategy}:${action.healingLog}`;
        if (seen.has(key)) continue;
        seen.add(key);

        if (action.suggestedFix) {
          recommendations.push({
            type: 'add-testid',
            message: action.suggestedFix,
            selector: action.healingLog,
          });
        }

        if (action.confidence < 0.7) {
          recommendations.push({
            type: 'fragile-selector',
            message: `Low-confidence selector (${action.confidence}): ${action.healingLog}. This selector is likely to break.`,
            selector: action.healingLog,
          });
        }
      }
    }

    // Route coverage recommendations
    for (const [route, status] of this.routeCoverage.entries()) {
      if (status === 'untested') {
        recommendations.push({
          type: 'missing-coverage',
          message: `Route "${route}" has no E2E test coverage`,
        });
      }
      if (status === 'failed') {
        recommendations.push({
          type: 'broken-route',
          message: `Route "${route}" is failing — investigate and fix`,
        });
      }
    }

    return recommendations;
  }
}
