/**
 * Smart Chat types - mirrors backend SupervisorState and tool result shapes.
 */

/** Backend SupervisorState from supervisor_agent.py */
export interface SupervisorAgentState {
  source_id: string | null
  notebook_id: string | null
  include_acm_context: boolean
  active_agents: string[]
  acm_results: Record<string, unknown> | null
  search_results: Record<string, unknown> | null
}

/** Parsed ACM record summary from tool results */
export interface ACMRecordSummary {
  id: string
  building_name: string | null
  room_name: string | null
  product: string
  material_description: string
  risk_status: string | null
  result: string
  location: string | null
  material_condition: string | null
}

/** ACM search results from search tools */
export interface ACMSearchResult {
  records: ACMRecordSummary[]
  total: number
  query_type: string
}

/** ACM stats results */
export interface ACMStatsResult {
  total_records: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  building_count: number
  room_count: number
}

/** Document search result */
export interface DocumentSearchResult {
  id: string
  title: string
  snippet: string
  score: number
  source_id: string
  source_type: string
}

/** Chat mode for the toggle switch */
export type ChatMode = 'classic' | 'smart'
