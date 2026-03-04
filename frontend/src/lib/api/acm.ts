/**
 * ACM (Asbestos Containing Material) API Client
 */

import apiClient from './client'
import type {
  ACMRecord,
  ACMRecordListResponse,
  ACMStats,
  ACMRecordCreateRequest,
  ACMRecordUpdateRequest,
  ACMExtractResponse,
  ACMListParams,
  SiteConfig,
  SiteConfigRequest,
  SiteConfigTemplate,
  CommandJobStatusResponse,
  ACMRawTable,
  RawExtractionListResponse,
  RawExtractionRecord,
  PatchRawExtractionRequest,
} from '@/lib/types/acm'
import type { SourceIntelligence } from '@/lib/types/intelligence'
import type { BuildingListResponse } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

export const acmApi = {
  /**
   * List ACM records with filtering and pagination
   */
  list: async (params: ACMListParams): Promise<ACMRecordListResponse> => {
    const response = await apiClient.get<ACMRecordListResponse>('/acm/records', { params })
    return response.data
  },

  /**
   * Get a single ACM record by ID
   */
  get: async (recordId: string): Promise<ACMRecord> => {
    const response = await apiClient.get<ACMRecord>(`/acm/records/${recordId}`)
    return response.data
  },

  /**
   * Create a new ACM record
   */
  create: async (data: ACMRecordCreateRequest): Promise<ACMRecord> => {
    const response = await apiClient.post<ACMRecord>('/acm/records', data)
    return response.data
  },

  /**
   * Update an existing ACM record
   */
  update: async (recordId: string, data: ACMRecordUpdateRequest): Promise<ACMRecord> => {
    const response = await apiClient.put<ACMRecord>(`/acm/records/${recordId}`, data)
    return response.data
  },

  /**
   * Delete an ACM record
   */
  delete: async (recordId: string): Promise<void> => {
    await apiClient.delete(`/acm/records/${recordId}`)
  },

  /**
   * Get ACM statistics
   */
  stats: async (sourceId?: string): Promise<ACMStats> => {
    const params = sourceId ? { source_id: sourceId } : {}
    const response = await apiClient.get<ACMStats>('/acm/stats', { params })
    return response.data
  },

  /**
   * Trigger ACM extraction for a source.
   * Pass { force: true } to clear existing records and re-run extraction.
   */
  extract: async (sourceId: string, opts?: { force?: boolean }): Promise<ACMExtractResponse> => {
    const response = await apiClient.post<ACMExtractResponse>('/acm/extract', {
      source_id: sourceId,
      force: opts?.force ?? false,
    })
    return response.data
  },

  /**
   * Export ACM records as CSV
   */
  exportCsv: async (sourceId: string): Promise<Blob> => {
    const response = await apiClient.get('/acm/export', {
      params: { source_id: sourceId },
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Export ACM records as Excel
   */
  exportExcel: async (sourceId: string): Promise<Blob> => {
    const response = await apiClient.get('/acm/export/excel', {
      params: { source_id: sourceId },
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Export as SF-ready CSV (ZIP with Building__c.csv + Item__c.csv)
   */
  exportSfCsv: async (sourceId: string, buildingIds?: string[]): Promise<Blob> => {
    const params: Record<string, string> = { source_id: sourceId }
    if (buildingIds?.length) params.building_ids = buildingIds.join(',')
    const response = await apiClient.get('/acm/export/sf-csv', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Export as SF-ready Excel (2-sheet XLSX)
   */
  exportSfExcel: async (sourceId: string, buildingIds?: string[]): Promise<Blob> => {
    const params: Record<string, string> = { source_id: sourceId }
    if (buildingIds?.length) params.building_ids = buildingIds.join(',')
    const response = await apiClient.get('/acm/export/sf-excel', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Get job status for an extraction command
   */
  getJobStatus: async (jobId: string): Promise<CommandJobStatusResponse> => {
    const response = await apiClient.get<CommandJobStatusResponse>(`/commands/jobs/${jobId}`)
    return response.data
  },

  /**
   * Fetch raw table sections for a job.
   */
  getRawTables: async (sourceId: string): Promise<ACMRawTable[]> => {
    const response = await apiClient.get<ACMRawTable[]>(
      `/acm/jobs/${encodeURIComponent(sourceId)}/raw-tables`
    )
    return response.data
  },

  /**
   * Check if a source has ACM records
   */
  hasRecords: async (sourceId: string): Promise<boolean> => {
    const response = await apiClient.get<ACMRecordListResponse>('/acm/records', {
      params: { source_id: sourceId, limit: 1 }
    })
    return response.data.total > 0
  },

  // Site Configuration API
  /**
   * Get site configuration for a source
   */
  getConfig: async (sourceId: string): Promise<SiteConfig | null> => {
    const response = await apiClient.get<SiteConfig>('/acm/config', {
      params: { source_id: sourceId }
    })
    return response.data
  },

  /**
   * Create or update site configuration
   */
  saveConfig: async (data: SiteConfigRequest): Promise<SiteConfig> => {
    const response = await apiClient.post<SiteConfig>('/acm/config', data)
    return response.data
  },

  /**
   * Get site configuration templates
   */
  getConfigTemplates: async (limit: number = 20): Promise<SiteConfigTemplate[]> => {
    const response = await apiClient.get<{ templates: SiteConfigTemplate[] }>('/acm/config/templates', {
      params: { limit }
    })
    return response.data.templates ?? []
  },

  /**
   * Apply a template to a source's configuration
   */
  applyConfigTemplate: async (sourceId: string, templateSourceId: string): Promise<SiteConfig> => {
    const response = await apiClient.post<SiteConfig>('/acm/config/apply-template', {
      source_id: sourceId,
      template_source_id: templateSourceId
    })
    return response.data
  },

  /**
   * Get list of agencies for autocomplete
   */
  getAgencies: async (department?: string): Promise<string[]> => {
    const params = department ? { department } : {}
    const response = await apiClient.get<{ agencies: string[] }>('/acm/config/agencies', { params })
    return response.data.agencies
  },

  /**
   * Get pre-extraction intelligence for a source (E30-S9).
   * Returns null if no intelligence data exists (404).
   */
  getIntelligence: async (sourceId: string): Promise<SourceIntelligence | null> => {
    try {
      const response = await apiClient.get<SourceIntelligence>(
        `/acm/source-intelligence/${encodeURIComponent(sourceId)}`
      )
      return response.data
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number } }
        if (axiosErr.response?.status === 404) return null
      }
      throw err
    }
  },

  /**
   * List buildings for a source (V3 endpoint — E30-S2).
   * GET /api/acm/buildings?source_id={sourceId}
   */
  listBuildings: async (sourceId: string): Promise<BuildingListResponse> => {
    const response = await apiClient.get<BuildingListResponse>('/acm/buildings', {
      params: { source_id: sourceId },
    })
    return response.data
  },

  /**
   * Get SF field schema configuration (E32-S4).
   * GET /api/acm/field-schema
   */
  getFieldSchema: async (): Promise<SFFieldSchemaConfig> => {
    const response = await apiClient.get<SFFieldSchemaConfig>('/acm/field-schema')
    return response.data
  },

  /**
   * List raw extractions for a source (E31-S4 raw_extraction table).
   * Optionally filter by provider: "docling" | "mineru"
   */
  rawExtractions: async (sourceId: string, provider?: string): Promise<RawExtractionListResponse> => {
    const params: Record<string, string> = {}
    if (provider) params.provider = provider
    const response = await apiClient.get<RawExtractionListResponse>(
      `/acm/raw-extractions/${encodeURIComponent(sourceId)}`,
      { params }
    )
    return response.data
  },

  /**
   * Patch officer edits onto a raw extraction row.
   */
  patchRawExtraction: async (
    sourceId: string,
    extractionId: string,
    body: PatchRawExtractionRequest
  ): Promise<RawExtractionRecord> => {
    const response = await apiClient.patch<RawExtractionRecord>(
      `/acm/raw-extractions/${encodeURIComponent(sourceId)}/${encodeURIComponent(extractionId)}`,
      body
    )
    return response.data
  },

  /**
   * Get per-building validation error counts (E33-S4).
   * GET /api/acm/validation-summary?source_id=X
   */
  getValidationSummary: async (
    sourceId: string
  ): Promise<{ buildings: { building_id: string; error_count: number }[] }> => {
    const response = await apiClient.get<{
      buildings: { building_id: string; error_count: number }[]
    }>('/acm/validation-summary', { params: { source_id: sourceId } })
    return response.data
  },

  /**
   * Bulk fix auto-correctable validation issues (E33-S4).
   * POST /api/acm/bulk-fix?source_id=X&building_id=Y
   */
  bulkFix: async (
    sourceId: string,
    buildingId?: string
  ): Promise<{ fixed_count: number; remaining_errors: number }> => {
    const params: Record<string, string> = { source_id: sourceId }
    if (buildingId) params.building_id = buildingId
    const response = await apiClient.post<{ fixed_count: number; remaining_errors: number }>(
      '/acm/bulk-fix',
      null,
      { params }
    )
    return response.data
  },
}
