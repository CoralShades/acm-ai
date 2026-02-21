export interface FieldMappingEntry {
  bar_column: string
  bar_column_index: number
  acm_field: string | null
  is_computed: boolean
  formula?: string | null
}

export interface FieldMapping {
  id?: string
  name: string
  is_active: boolean
  mappings: FieldMappingEntry[]
  notes?: string | null
}
