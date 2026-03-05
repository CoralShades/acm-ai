export interface V3EventEnvelope {
  type: string
  operation_id: string
  timestamp: string
  data: Record<string, unknown>
}

export type V3EventCategory = 'extraction' | 'ai' | 'bulk'
