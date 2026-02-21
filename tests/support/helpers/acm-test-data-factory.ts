/**
 * ACM Test Data Factory Extension
 *
 * Extends TestDataFactory with ACM-specific methods for:
 * - Source creation with file upload
 * - ACM extraction monitoring
 * - Test SAMP document management
 *
 * Usage:
 *   const factory = new ACMTestDataFactory();
 *   const source = await factory.createSourceFromSAMP('broadmeadows-police-station-samp.pdf');
 *   await factory.waitForExtraction(source.id);
 *   await factory.cleanup();
 */

import { TestDataFactory } from './test-data-factory';
import type { Notebook } from './api-helpers';
import * as path from 'path';
import * as fs from 'fs';

const API_URL = process.env.API_URL || 'http://localhost:5055/api';

export interface Source {
  id: string;
  title?: string;
  full_text?: string;
  notebook_id?: string;
  created: string;
  updated: string;
}

export interface ACMRecord {
  id: string;
  source_id: string;
  room_name?: string;
  product?: string;
  result?: string;
  floor_level?: string;
  area_type?: string;
  friable?: string;
  material_condition?: string;
  risk_status?: string;
  created: string;
  updated: string;
}

export interface ExtractionStatus {
  source_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  stage?: string;
  progress?: number;
  acm_count?: number;
  error?: string;
}

export class ACMTestDataFactory extends TestDataFactory {
  private createdSources: string[] = [];
  private createdACMRecords: string[] = [];

  /**
   * Create a source from a SAMP PDF file
   *
   * @param sampFilename - Filename in tests/e2e/fixtures/samps/
   * @param notebook - Optional notebook (creates one if not provided)
   * @returns Source object
   */
  async createSourceFromSAMP(
    sampFilename: string,
    notebook?: Notebook
  ): Promise<Source> {
    const nb = notebook || (await this.createNotebook({ name: 'E2E ACM Test' }));
    const sampPath = path.join(
      __dirname,
      '../../e2e/fixtures/samps',
      sampFilename
    );

    if (!fs.existsSync(sampPath)) {
      throw new Error(`SAMP file not found: ${sampPath}`);
    }

    // Create FormData for file upload
    const formData = new FormData();
    const fileBuffer = fs.readFileSync(sampPath);
    const blob = new Blob([fileBuffer], { type: 'application/pdf' });
    formData.append('file', blob, sampFilename);
    formData.append('notebook_id', nb.id);
    formData.append('enable_acm_extraction', 'true');

    const response = await fetch(`${API_URL}/sources/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload SAMP: ${response.status}`);
    }

    const source = await response.json();
    this.createdSources.push(source.id);
    return source;
  }

  /**
   * Wait for ACM extraction to complete
   *
   * @param sourceId - Source ID to monitor
   * @param timeout - Timeout in milliseconds (default: 120s)
   * @returns Final extraction status
   */
  async waitForExtraction(
    sourceId: string,
    timeout = 120000
  ): Promise<ExtractionStatus> {
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds

    while (Date.now() - startTime < timeout) {
      const status = await this.getExtractionStatus(sourceId);

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Extraction timeout after ${timeout}ms for source ${sourceId}`);
  }

  /**
   * Get current extraction status
   */
  async getExtractionStatus(sourceId: string): Promise<ExtractionStatus> {
    const response = await fetch(`${API_URL}/sources/${sourceId}/extraction-status`);

    if (!response.ok) {
      throw new Error(`Failed to get extraction status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get ACM records for a source
   */
  async getACMRecords(sourceId: string): Promise<ACMRecord[]> {
    const response = await fetch(`${API_URL}/acm-records?source_id=${sourceId}`);

    if (!response.ok) {
      throw new Error(`Failed to get ACM records: ${response.status}`);
    }

    const records = await response.json();
    // Track for cleanup
    records.forEach((record: ACMRecord) => {
      this.createdACMRecords.push(record.id);
    });

    return records;
  }

  /**
   * Create ACM record manually (for testing edge cases)
   */
  async createACMRecord(
    sourceId: string,
    overrides: Partial<ACMRecord> = {}
  ): Promise<ACMRecord> {
    const response = await fetch(`${API_URL}/acm-records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_id: sourceId,
        room_name: 'Test Room',
        product: 'Test Product',
        result: 'Positive',
        ...overrides,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create ACM record: ${response.status}`);
    }

    const record = await response.json();
    this.createdACMRecords.push(record.id);
    return record;
  }

  /**
   * Delete an ACM record
   */
  async deleteACMRecord(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/acm-records/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete ACM record: ${response.status}`);
    }
  }

  /**
   * Delete a source
   */
  async deleteSource(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/sources/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete source: ${response.status}`);
    }
  }

  /**
   * Extended cleanup - includes sources and ACM records
   */
  async cleanup(): Promise<void> {
    // Delete ACM records first
    for (const recordId of this.createdACMRecords) {
      try {
        await this.deleteACMRecord(recordId);
      } catch (error) {
        console.warn(`Failed to cleanup ACM record ${recordId}:`, error);
      }
    }
    this.createdACMRecords = [];

    // Delete sources
    for (const sourceId of this.createdSources) {
      try {
        await this.deleteSource(sourceId);
      } catch (error) {
        console.warn(`Failed to cleanup source ${sourceId}:`, error);
      }
    }
    this.createdSources = [];

    // Call parent cleanup for notebooks and notes
    await super.cleanup();
  }

  /**
   * Get count of tracked ACM resources
   */
  get acmTrackedCount(): {
    sources: number;
    acm_records: number;
    notebooks: number;
    notes: number;
  } {
    const parentCount = super.trackedCount;
    return {
      sources: this.createdSources.length,
      acm_records: this.createdACMRecords.length,
      ...parentCount,
    };
  }
}
