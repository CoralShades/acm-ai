/**
 * Chat session types — mirrors backend SessionResponse / SessionListResponse.
 */

export interface ChatSessionSummary {
  id: string
  title: string | null
  thread_id: string | null
  created: string | null
  updated: string | null
}

export interface SessionListResponse {
  sessions: ChatSessionSummary[]
  total: number
}

/** A single serialized LangChain message returned by the message history endpoint. */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool' | 'function' | string
  /** Plain string or multi-part content array (e.g. image + text). */
  content: string | Record<string, unknown>[]
  name?: string | null
  tool_calls?: Record<string, unknown>[] | null
  tool_call_id?: string | null
}

export interface MessageHistoryResponse {
  messages: ChatMessage[]
  total: number
}
