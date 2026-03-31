/**
 * Unified Chat types — mirrors backend UnifiedAgentState.
 */

/** Backend UnifiedAgentState from unified_agent.py */
export interface UnifiedAgentState {
  source_id: string | null
  notebook_id: string | null
  model_id: string | null
  include_acm_context: boolean
  pending_operation: Record<string, unknown> | null
  session_id?: string | null
  /** Option A: session's LangGraph thread_id — controls checkpointer persistence */
  thread_id?: string | null
}
