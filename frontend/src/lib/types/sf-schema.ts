/**
 * Salesforce Field Schema Types
 * Matches SFFieldSchemaConfigResponse from api/models.py (E30-S2 / E32-S4).
 */

export interface SFFieldDef {
  api_name: string
  label: string
  field_type: string
  length: number | null
  nillable: boolean
  custom: boolean
  calc: boolean
  updateable: boolean
  notes: string | null
  is_restricted_picklist: boolean
  is_dependent: boolean
  controller_field: string | null
}

export interface SFFieldSchemaObject {
  object_name: string
  object_label: string
  total_fields: number
  custom_fields: number
  picklist_fields: number
  fields: SFFieldDef[]
  picklists: Record<string, string[]>
  version: string
}

export interface SFFieldSchemaConfig {
  version: string
  building_fields: SFFieldSchemaObject
  item_fields: SFFieldSchemaObject
  picklists: Record<string, string[]>
  dependencies: Array<{
    controller_api_name: string
    dependent_api_name: string
    mapping: Record<string, unknown>
  }>
  loaded_at: string | null
}
