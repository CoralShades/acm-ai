/**
 * Pipeline Types - Backend PipelineRunState models
 */

export type StageId = 'STRUCTURE' | 'PREFLIGHT' | 'ORCHESTRATOR' | 'EXTRACT' | 'VALIDATE' | 'CORRECT' | 'STORE'

export type StageStatus = 'pending' | 'running' | 'complete' | 'failed' | 'skipped'

export type PipelineStatus = 'idle' | 'running' | 'completed' | 'failed' | 'partial'

export interface StageError {
  message: string
  code: string
  records_affected: number
}

export interface StageState {
  id: StageId
  status: StageStatus
  entered_at: string | null
  completed_at: string | null
  duration_ms: number | null
  progress: number
  message: string | null
  record_count: number | null
  metrics: Record<string, string | number | boolean>
  error: StageError | null
}

export interface PipelineRunState {
  run_id: string
  source_id: string
  status: PipelineStatus
  started_at: string | null
  completed_at: string | null
  total_duration_ms: number | null
  stages: Record<StageId, StageState>
  total_pages: number
  total_chunks: number
  total_buildings: number
  total_records: number
  records_rejected: number
  records_unidentified: number
  confidence_distribution: Record<string, number>
  models_used: string[]
  strategy_distribution: Record<string, number>
}

export interface ExtractionProgressResponse {
  status: string
  state: PipelineRunState
  log_entries: string[]
}

export interface ExtractionProgressEvent {
  status: string
  state: PipelineRunState
  log_entries: string[]
}
