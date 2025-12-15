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
