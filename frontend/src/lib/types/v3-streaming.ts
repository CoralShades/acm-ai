export interface V3EventEnvelope {
  type: string
  operation_id: string
  timestamp: string
  data: Record<string, unknown>
}

export type V3EventCategory = 'extraction' | 'ai' | 'bulk' | 'hitl'

/** A single column mapping proposed by schema inference. */
export interface SchemaMappingItem {
  pdf_header: string
  sf_field: string
  confidence: number
}

/** Payload for hitl.schema_mapping_review events. */
export interface SchemaMappingReviewPayload {
  source_id: string
  mappings: SchemaMappingItem[]
  unmapped_headers: string[]
  overall_confidence: number
  detected_consultant: string | null
  header_signature: string
}

/** User's response to the HITL mapping review. */
export interface SchemaMappingResponse {
  action: 'approve' | 'modify' | 'reject'
  mappings?: SchemaMappingItem[]
}

/** Extraction complete payload */
export interface ExtractionCompletePayload {
  source_id: string
  records_saved: number
  buildings_count: number
  duration_ms: number
}

/** Extraction failed payload */
export interface ExtractionFailedPayload {
  source_id: string
  error: string
  stage: string
}
