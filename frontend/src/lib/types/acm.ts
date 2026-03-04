/**
 * ACM (Asbestos Containing Material) Record Types
 */

// NOTE: Generated types exist in ./generated/ (from Pydantic models).
// The ACMRecord type below is manually maintained for frontend compatibility.
// When the backend ACMRecord model changes, run 'npm run generate:types' and
// reconcile any field differences with this file.

export interface ACMRecord {
  id: string
  source_id: string
  school_name: string
  school_code?: string | null
  building_id: string
  building_name?: string | null
  building_year?: number | null
  building_construction?: string | null
  room_id?: string | null
  room_name?: string | null
  room_area?: number | null
  area_type?: string | null // 'Interior' | 'Exterior' | 'Grounds'
  product: string
  material_description: string
  extent?: string | null
  location?: string | null
  friable?: string | null // 'Friable' | 'Non-friable'
  material_condition?: string | null
  risk_status?: string | null // 'Low' | 'Medium' | 'High'
  result: string
  page_number?: number | null
  extraction_confidence?: number | null
  // Classification fields
  acm_product_group?: string | null
  acm_product_type?: string | null
  classification_confidence?: number | null
  classification_method?: string | null
  classification_override?: boolean | null
  // BAR compliance fields
  sample_no?: string | null
  sample_result?: string | null
  quantity?: string | null
  acm_labelled?: boolean | null
  acm_label_details?: string | null
  identifying_company?: string | null
  disturbance_potential?: string | null
  hygienist_recommendations?: string | null
  normalized_action?: string | null
  data_issues?: string[] | null
  floor_level?: string | null
  date_of_inspection?: string | null
  building_address?: string | null
  suburb?: string | null
  postcode?: string | null
  building_type?: string | null
  quantity_removed?: string | null
  removal_notification_no?: string | null
  epa_certificate_no?: string | null
  additional_comments?: string | null
  created?: string | null
  updated?: string | null
}

export interface ACMRecordListResponse {
  records: ACMRecord[]
  total: number
  page: number
  pages: number
  limit: number
}

export interface ACMStats {
  total_records: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  building_count: number
  room_count: number
  source_id?: string | null
}

export interface ACMRecordCreateRequest {
  source_id: string
  school_name: string
  school_code?: string
  building_id: string
  building_name?: string
  building_year?: number
  building_construction?: string
  building_type?: string
  room_id?: string
  room_name?: string
  room_area?: number
  area_type?: string
  product: string
  material_description: string
  extent?: string
  location?: string
  friable?: string
  acm_product_group?: string
  acm_product_type?: string
  material_condition?: string
  risk_status?: string
  result: string
  page_number?: number
}

export interface ACMRecordUpdateRequest {
  school_name?: string
  school_code?: string
  building_id?: string
  building_name?: string
  building_year?: number
  building_construction?: string
  building_type?: string
  room_id?: string
  room_name?: string
  room_area?: number
  area_type?: string
  product?: string
  material_description?: string
  extent?: string
  location?: string
  friable?: string
  acm_product_group?: string
  acm_product_type?: string
  material_condition?: string
  risk_status?: string
  result?: string
  page_number?: number
}

export interface ACMExtractRequest {
  source_id: string
}

export interface ACMExtractResponse {
  command_id: string
  status: string
  message: string
}

export interface ACMListParams {
  source_id: string
  building_id?: string
  room_id?: string
  risk_status?: string
  page?: number
  limit?: number
}

// Risk status type for filtering
export type RiskStatus = 'Low' | 'Medium' | 'High'

// Area type for filtering
export type AreaType = 'Interior' | 'Exterior' | 'Grounds'

// Friable type
export type FriableType = 'Friable' | 'Non-friable'

// Site Configuration Types for Victorian BAR Compliance
export interface SiteConfig {
  id?: string
  source_id: string
  department?: string | null
  agency?: string | null
  building_type?: string | null
  owned_or_leased?: string | null
  frequency_of_use?: string | null
  public_access?: string | null
  building_unique_id?: string | null
  is_bar_complete?: boolean
  missing_bar_fields?: string[]
}

export interface SiteConfigRequest {
  source_id: string
  department?: string
  agency?: string
  building_type?: string
  owned_or_leased?: string
  frequency_of_use?: string
  public_access?: string
  building_unique_id?: string
}

export interface SiteConfigTemplate {
  source_id: string
  source_title?: string
  department?: string
  agency?: string
  building_type?: string
  owned_or_leased?: string
  frequency_of_use?: string
  public_access?: string
}

// BAR Field Options
export const DEPARTMENTS = [
  'DJCS',
  'DHHS',
  'DET',
  'DOT',
  'DJPR',
  'Other',
] as const

export const BUILDING_TYPES = [
  'Police Station',
  'Hospital',
  'School',
  'Office',
  'Residential',
  'Industrial',
  'Other',
] as const

export const OWNERSHIP_OPTIONS = ['Owned', 'Leased'] as const

export const FREQUENCY_OPTIONS = [
  'Every day',
  'Every day with intermittent breaks',
  'Once every 3-5 days',
  'Every 2-3 weeks',
  'Once every 2-3 months',
  'Annually or less frequently',
] as const

export const PUBLIC_ACCESS_OPTIONS = ['YES', 'NO'] as const

// Raw Extraction types (E31-S4 raw_extraction table)
export interface OfficerEdit {
  field: string
  old_value: string
  new_value: string
  user: string
  timestamp: string // ISO 8601
}

export interface RawExtractionRecord {
  id: string
  source_id: string
  provider_id: string // "docling" | "mineru"
  extraction_backend: string
  page_number: number
  raw_html: string | null
  raw_markdown: string | null
  structured_json: string | null // JSON string: { headers: string[], rows: string[][] }
  bbox: Record<string, number> | null
  confidence: number | null
  officer_edits: OfficerEdit[]
  created_at: string | null
}

export interface RawExtractionListResponse {
  source_id: string
  total: number
  extractions: RawExtractionRecord[]
}

export interface PatchRawExtractionRequest {
  structured_json?: string
  edits: OfficerEdit[]
}

// Shape of parsed structured_json content
export interface StructuredJsonContent {
  headers: string[]
  rows: string[][]
}

export interface CommandJobStatusResponse {
  job_id: string
  status: 'new' | 'running' | 'completed' | 'failed' | 'canceled'
  result?: { success?: boolean; records_created?: number; error_message?: string }
  error_message?: string | null
  progress?: {
    state?: import('./pipeline').PipelineRunState
  }
}

export interface ACMRawTable {
  id: string
  source_id: string
  page_start: number
  page_end: number
  table_type?: string | null
  raw_html?: string | null
  raw_text?: string | null
  building_name?: string | null
}

// Re-export generated types that complement the manual types above.
// Generated from Pydantic models via 'npm run generate:types'.
// See frontend/src/lib/types/generated/ for the full generated type set.
export type { ACMExtractionOutput } from './generated/ACMExtractionOutput'
export type { ACMExtractionRecord } from './generated/ACMExtractionRecord'
export type { ACMExtractionResult } from './generated/ACMExtractionResult'
export type { BuildingRoomContext } from './generated/BuildingRoomContext'
export type { ConfidenceDistribution } from './generated/ConfidenceDistribution'
export type { ExtractionConfidence } from './generated/ExtractionConfidence'
export type { ExtractionStatus } from './generated/ExtractionStatus'
export type { TableBoundingBox } from './generated/TableBoundingBox'
