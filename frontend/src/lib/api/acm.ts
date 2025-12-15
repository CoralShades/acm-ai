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
}
