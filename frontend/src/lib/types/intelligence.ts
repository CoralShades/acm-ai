/**
 * TypeScript interfaces for pre-extraction intelligence data (E30-S9).
 *
 * Mirrors the 4 Python Pydantic models:
 * - DocumentMeta (parsers/base.py)
 * - DocumentStructure (document_structure.py)
 * - BuildingInventory (building_inventory.py)
 * - PageTaggingResult (page_tagger.py)
 */

// --- DocumentMeta ---

export interface DocumentMeta {
  consultant_name: string
  site_name?: string | null
  site_address?: string | null
  report_date?: string | null
  report_reference?: string | null
  building_size?: string | null
  building_age?: string | null
  additional?: Record<string, string>
  suburb?: string | null
  postcode?: string | null
  organization?: string | null
  inspection_dates?: string[] | null
  inspector_names?: string[] | null
  document_scope?: string | null
  methodology?: string | null
  revision_date?: string | null
  regional_classification?: string | null
  field_confidence?: Record<string, string>
}

// --- DocumentStructure ---

export interface SubSection {
  subsection_number: string
  title: string
  page_start: number
  page_end?: number | null
}

export interface Section {
  section_id: number
  title: string
  page_start: number
  page_end?: number | null
  subsections: SubSection[]
}

// Note: 'SAMP' kept for backward compatibility — matches backend enum value which requires DB migration to change
export type DocumentType = 'SAMP' | 'ARA' | 'Division_5' | 'Unknown'

export interface DocumentStructure {
  document_type: DocumentType
  toc_present: boolean
  total_pages: number
  register_start_page?: number | null
  building_ids: string[]
  sections: Section[]
  metadata?: Record<string, unknown>
}

// --- BuildingInventory ---

export interface RoomMeta {
  room_id: string
  name: string
  area_m2?: number | null
  page?: number | null
}

export type BuildingComplexity = 'simple' | 'complex'

export interface BuildingMeta {
  building_id: string
  name?: string | null
  year?: number | null
  construction?: string | null
  purpose?: string | null
  area_m2?: number | null
  levels?: number | null
  page_start: number
  page_end?: number | null
  complexity: BuildingComplexity
  rooms: RoomMeta[]
  acm_item_count_estimate?: number | null
}

export interface ProcessingGroup {
  group_id: number
  building_ids: string[]
  page_start: number
  page_end: number
  estimated_pages: number
}

export interface BuildingInventory {
  buildings: BuildingMeta[]
  processing_groups: ProcessingGroup[]
  total_buildings: number
  document_type?: string | null
}

// --- PageTaggingResult ---

export type PageType = 'title_page' | 'toc_page' | 'content' | 'special'

export interface SubSectionTag {
  subsection_number: string
  title: string
  section_id: number
}

export interface PageTag {
  page_number: number
  section_id: number
  section_title: string
  confidence: number
  page_type: PageType
  subsection?: SubSectionTag | null
  content_summary?: string | null
}

export interface PageTaggingResult {
  pages: PageTag[]
  total_pages: number
  register_page_range?: [number, number] | null
}

// --- Combined Intelligence Response ---

export interface SourceIntelligence {
  id?: string | null
  source_id: string
  document_meta?: DocumentMeta | null
  document_structure?: DocumentStructure | null
  building_inventory?: BuildingInventory | null
  page_tags?: PageTaggingResult | null
  total_pages?: number | null
  total_buildings?: number | null
  document_type?: string | null
  register_page_range?: { start: number; end: number } | null
  created_at?: string | null
  updated_at?: string | null
}
