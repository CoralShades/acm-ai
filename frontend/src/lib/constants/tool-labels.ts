/** Shared tool label maps used by AgentActivityIndicator and ToolErrorCard */

export const TOOL_LABELS: Record<string, string> = {
  search_acm_by_risk: 'ACM risk search',
  search_acm_by_building: 'ACM building search',
  search_acm_by_room: 'ACM room search',
  search_acm_by_product: 'ACM product search',
  get_acm_stats: 'ACM statistics',
  get_acm_record_detail: 'ACM record detail',
  list_acm_buildings: 'building list',
  search_documents_vector: 'vector search',
  search_documents_text: 'text search',
  preview_acm_write: 'write preview',
  write_acm_record: 'record write',
}

export const TOOL_ACTIVITY_LABELS: Record<string, string> = {
  search_acm_by_risk: 'Searching ACM by risk status...',
  search_acm_by_building: 'Searching ACM by building...',
  search_acm_by_room: 'Searching ACM by room...',
  search_acm_by_product: 'Searching ACM by product...',
  get_acm_stats: 'Getting ACM statistics...',
  get_acm_record_detail: 'Loading ACM record details...',
  list_acm_buildings: 'Listing buildings with ACM data...',
  search_documents_vector: 'Searching documents (semantic)...',
  search_documents_text: 'Searching documents (text)...',
}
