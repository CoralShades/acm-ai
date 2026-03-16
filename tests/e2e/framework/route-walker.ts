/**
 * Route Walker
 *
 * Walks all known application routes and reports their status,
 * JS errors, and load times. Useful for smoke tests and route
 * coverage auditing.
 */

import { Page } from '@playwright/test';

/**
 * Static routes that don't require dynamic IDs.
 */
export const STATIC_ROUTES: string[] = [
  '/',
  '/notebooks',
  '/sources',
  '/documents',
  '/acm',
  '/search',
  '/settings',
  '/settings/models',
  '/settings/field-mapping',
  '/settings/field-schema',
  '/settings/extraction',
  '/settings/processing',
  '/settings/bar-templates',
  '/settings/parsers',
  '/upload',
  '/jobs',
  '/extraction-monitor',
  '/models',
  '/podcasts',
  '/transformations',
  '/advanced',
  '/test-grid',
  '/landing',
  '/login',
];

/**
 * Dynamic routes with placeholder IDs for testing.
 */
export const DYNAMIC_ROUTES: string[] = [
  '/notebooks/notebook:test',
  '/sources/source:test',
  '/source/source:test',
  '/jobs/source:test',
  '/extraction/source:test',
  '/jobs/source:test/chat',
  '/jobs/source:test/extract',
  '/jobs/source:test/review/buildings',
  '/jobs/source:test/review/records',
  '/source/source:test/building/building_record:test',
  '/source/source:test/provenance/acm_record:test',
  '/source/source:test/raw',
];

export interface RouteWalkResult {
  route: string;
  status: 'ok' | 'error' | 'redirect' | 'not-found';
  statusCode?: number;
  jsErrors: string[];
  loadTime: number;
  title?: string;
}

export class RouteWalker {
  /**
   * Walk all routes and return results for each.
   */
  async walkAll(
    page: Page,
    options?: { skipDynamic?: boolean; timeout?: number }
  ): Promise<RouteWalkResult[]> {
    const results: RouteWalkResult[] = [];
    const timeout = options?.timeout ?? 10000;

    for (const route of STATIC_ROUTES) {
      const result = await this.walkRoute(page, route, timeout);
      results.push(result);
    }

    if (!options?.skipDynamic) {
      for (const route of DYNAMIC_ROUTES) {
        const result = await this.walkRoute(page, route, timeout);
        results.push(result);
      }
    }

    return results;
  }

  /**
   * Walk a single route and report its status.
   */
  async walkRoute(
    page: Page,
    route: string,
    timeout?: number
  ): Promise<RouteWalkResult> {
    const jsErrors: string[] = [];
    const effectiveTimeout = timeout ?? 10000;

    // Collect JS errors during navigation
    const errorHandler = (error: Error) => {
      jsErrors.push(error.message);
    };
    page.on('pageerror', errorHandler);

    const startTime = Date.now();

    try {
      const response = await page.goto(route, {
        waitUntil: 'domcontentloaded',
        timeout: effectiveTimeout,
      });

      const loadTime = Date.now() - startTime;
      const statusCode = response?.status() ?? 0;
      const title = await page.title().catch(() => undefined);

      // Check for common error indicators in page content
      const bodyText = await page
        .locator('body')
        .textContent({ timeout: 2000 })
        .catch(() => '');

      let status: RouteWalkResult['status'] = 'ok';

      if (statusCode === 404 || (bodyText && bodyText.includes('404'))) {
        status = 'not-found';
      } else if (statusCode >= 500) {
        status = 'error';
      } else if (statusCode >= 300 && statusCode < 400) {
        status = 'redirect';
      } else if (jsErrors.length > 0) {
        status = 'error';
      }

      return { route, status, statusCode, jsErrors, loadTime, title };
    } catch (error) {
      const loadTime = Date.now() - startTime;
      return {
        route,
        status: 'error',
        jsErrors: [
          ...jsErrors,
          error instanceof Error ? error.message : String(error),
        ],
        loadTime,
      };
    } finally {
      page.removeListener('pageerror', errorHandler);
    }
  }

  /**
   * Get the list of static routes.
   */
  getStaticRoutes(): string[] {
    return [...STATIC_ROUTES];
  }

  /**
   * Get the list of dynamic routes.
   */
  getDynamicRoutes(): string[] {
    return [...DYNAMIC_ROUTES];
  }
}
