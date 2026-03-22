/**
 * Chat session types — mirrors backend SessionResponse / SessionListResponse.
 */

export interface ChatSessionSummary {
  id: string
  title: string | null
  created: string | null
  updated: string | null
}

export interface SessionListResponse {
  sessions: ChatSessionSummary[]
  total: number
}
