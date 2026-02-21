import { apiClient } from './client'

export interface ExtractionProgressItem {
  id: string
  command_id: string
  source_id?: string
  status: string
  state?: Record<string, unknown>
  log_entries: string[]
  token_limit_exceeded: boolean
  chunk_count?: number
  created_at?: string
  updated_at?: string
}

export interface ExtractionProgressList {
  items: ExtractionProgressItem[]
  total: number
}

export const extractionMonitorApi = {
  async list(params?: {
    status?: string
    limit?: number
    offset?: number
  }): Promise<ExtractionProgressList> {
    const { data } = await apiClient.get('/acm/extraction-progress', { params })
    return data
  },
}
