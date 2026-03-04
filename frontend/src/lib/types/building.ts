/**
 * V3 Building Record Types
 * Matches BuildingRecordResponse from api/models.py (E30-S2).
 */

/**
 * V3 BuildingRecord — matches BuildingRecordResponse from api/models.py (E30-S2).
 * internal_id pattern: BLD#{source_short}_{seq:03d}
 */
export interface BuildingRecord {
  id: string
  internal_id: string               // BLD#NNN identifier shown in sidebar
  source_id: string
  building_code: string | null
  building_name: string | null
  building_year: string | null
  building_construction: string | null
  building_address: string | null
  suburb: string | null
  postcode: string | null
  building_type: string | null
  building_category: string | null
  building_address_lga: string | null
  building_address_region: string | null
  roof_type: string | null
  number_of_levels: number | null
  est_building_size_m2: number | null
  frequency_of_use: string | null
  daily_duration: string | null
  level_of_activity: string | null
  public_access: string | null
  mobile_plant: string | null
  owned_or_leased: string | null
  asbestos_register_available: string | null
  audit_report_available: string | null
  date_of_audit_report: string | null
  no_identified_acms: number | null
  no_identified_acms_note: string | null
  site_name: string | null
  school_uid: string | null
  building_unique_id: string | null
  external_id: string | null
  building_out_of_scope: boolean | null
  building_out_of_scope_comments: string | null
  demolished_status: string | null
  demolition_date: string | null
  demolition_type: string | null
  demolition_comments: string | null
  additional_comments: string | null
  within_your_portfolio: string | null
  psb_district_region: string | null
  state: string | null
  country: string | null
  gps_coordinates: string | null
  capital_works_project_details: string | null
  possible_capital_works_project: string | null
  record_count: number                // ACM item count for this building (from API)
  created: string | null
  updated: string | null
}

export interface BuildingListResponse {
  buildings: BuildingRecord[]
  total: number
}

/** Validation status derived from building completeness — computed client-side */
export type BuildingValidationStatus = 'complete' | 'incomplete' | 'unknown'
