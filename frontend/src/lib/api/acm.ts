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
} from '@/lib/types/acm'

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
   * Trigger ACM extraction for a source
   */
  extract: async (sourceId: string): Promise<ACMExtractResponse> => {
    const response = await apiClient.post<ACMExtractResponse>('/acm/extract', {
      source_id: sourceId,
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
   * Get job status for an extraction command
   */
  getJobStatus: async (jobId: string): Promise<CommandJobStatusResponse> => {
    const response = await apiClient.get<CommandJobStatusResponse>(`/commands/jobs/${jobId}`)
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
    return response.data.templates
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
}
