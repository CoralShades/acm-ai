/**
 * ACM (Asbestos Containing Material) Record Types
 */

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
  friable?: string | null // 'Friable' | 'Non Friable'
  material_condition?: string | null
  risk_status?: string | null // 'Low' | 'Medium' | 'High'
  result: string
  page_number?: number | null
  extraction_confidence?: number | null
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
  room_id?: string
  room_name?: string
  room_area?: number
  area_type?: string
  product: string
  material_description: string
  extent?: string
  location?: string
  friable?: string
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
  room_id?: string
  room_name?: string
  room_area?: number
  area_type?: string
  product?: string
  material_description?: string
  extent?: string
  location?: string
  friable?: string
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
export type FriableType = 'Friable' | 'Non Friable'

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

export interface CommandJobStatusResponse {
  job_id: string
  status: 'new' | 'running' | 'completed' | 'failed' | 'canceled'
  result?: { success?: boolean; records_created?: number; error_message?: string }
  error_message?: string | null
}
