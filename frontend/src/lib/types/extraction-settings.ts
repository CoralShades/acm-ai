export interface ExtractionSettings {
  id?: string
  extraction_method: 'mineru' | 'docling' | 'hybrid'
  fallback_enabled: boolean
  enable_toc_extraction: boolean
  enable_building_inventory: boolean
  enable_page_tagging: boolean
  enable_metadata_enhancement: boolean
  enable_corrective_rag: boolean
  max_correction_attempts: number
}
