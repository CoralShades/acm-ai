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
  ProvenanceData,
} from '@/lib/types/acm'
import type { SourceIntelligence } from '@/lib/types/intelligence'
import type { BuildingListResponse, BuildingRecord, BuildingRecordUpdateRequest } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

/** Response shape from GET /api/acm/jobs/{sourceId}/buildings (legacy endpoint). */
interface JobBuildingResponse {
  building_id: string
  building_name?: string | null
  building_address?: string | null
  building_year?: number | null
  building_size_m2?: number | null
  number_of_levels?: number | null
  building_construction?: string | null
  roof_type?: string | null
  date_of_inspection?: string | null
  record_count?: number
  department?: string | null
  agency?: string | null
  sub_agency?: string | null
  site_name?: string | null
  building_type?: string | null
  owned_or_leased?: string | null
  building_unique_id?: string | null
  frequency_of_use?: string | null
  public_access?: string | null
  building_out_of_scope?: boolean | null
  building_out_of_scope_comments?: string | null
  additional_comments?: string | null
  suburb?: string | null
  postcode?: string | null
}

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
  extract: async (sourceId: string, opts?: { force?: boolean; mode?: string }): Promise<ACMExtractResponse> => {
    const response = await apiClient.post<ACMExtractResponse>('/acm/extract', {
      source_id: sourceId,
      force: opts?.force ?? false,
      mode: opts?.mode ?? 'ai_enhanced',
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
   * List buildings for a job source (legacy endpoint — derives from acm_record data).
   * GET /api/acm/jobs/{sourceId}/buildings
   * Works even when no V3 building_record entities exist.
   */
  listJobBuildings: async (sourceId: string): Promise<BuildingListResponse> => {
    const response = await apiClient.get<JobBuildingResponse[]>(
      `/acm/jobs/${encodeURIComponent(sourceId)}/buildings`
    )
    const jobBuildings = response.data ?? []
    // Adapt JobBuildingResponse → BuildingRecord shape for BuildingGrid compatibility
    const buildings: BuildingRecord[] = jobBuildings.map((jb) => ({
      id: `job_building:${sourceId}_${jb.building_id}`,
      internal_id: jb.building_id,
      source_id: sourceId,
      building_code: jb.building_id,
      building_name: jb.building_name ?? null,
      building_address: jb.building_address ?? null,
      suburb: jb.suburb ?? null,
      postcode: jb.postcode ?? null,
      state: null,
      building_type: jb.building_type ?? null,
      building_category: null,
      building_sub_category: null,
      building_risk_rating: null,
      building_year: jb.building_year != null ? String(jb.building_year) : null,
      building_construction: jb.building_construction ?? null,
      building_address_lga: null,
      building_address_region: null,
      roof_type: jb.roof_type ?? null,
      number_of_levels: jb.number_of_levels ?? null,
      est_building_size_m2: jb.building_size_m2 ?? null,
      frequency_of_use: jb.frequency_of_use ?? null,
      daily_duration: null,
      level_of_activity: null,
      public_access: jb.public_access ?? null,
      mobile_plant: null,
      asbestos_register_available: null,
      audit_report_available: null,
      date_of_audit_report: null,
      no_identified_acms: null,
      no_identified_acms_note: null,
      site_name: jb.site_name ?? null,
      school_uid: null,
      building_unique_id: jb.building_unique_id ?? null,
      external_id: null,
      owned_or_leased: jb.owned_or_leased ?? null,
      building_out_of_scope: null,
      building_out_of_scope_comments: null,
      demolished_status: null,
      demolition_date: null,
      demolition_type: null,
      demolition_comments: null,
      additional_comments: jb.additional_comments ?? null,
      within_your_portfolio: null,
      psb_district_region: null,
      country: null,
      gps_coordinates: null,
      capital_works_project_details: null,
      possible_capital_works_project: null,
      record_count: jb.record_count ?? 0,
      created: null,
      updated: null,
    }))
    return { buildings, total: buildings.length }
  },

  /**
   * Get a single building record by ID (E33-S7).
   * GET /api/acm/buildings/{building_id}
   */
  getBuilding: async (buildingId: string): Promise<BuildingRecord> => {
    const response = await apiClient.get<BuildingRecord>(
      `/acm/buildings/${encodeURIComponent(buildingId)}`
    )
    return response.data
  },

  /**
   * Update a building record (E33-S7).
   * PUT /api/acm/buildings/{building_id}
   */
  updateBuilding: async (buildingId: string, data: BuildingRecordUpdateRequest): Promise<BuildingRecord> => {
    const response = await apiClient.put<BuildingRecord>(
      `/acm/buildings/${encodeURIComponent(buildingId)}`,
      data
    )
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

  /** Get provenance data for a single ACM record (E33-S6) */
  getProvenance: async (recordId: string): Promise<ProvenanceData> => {
    const response = await apiClient.get<ProvenanceData>(
      `/acm/provenance/${encodeURIComponent(recordId)}`
    )
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
