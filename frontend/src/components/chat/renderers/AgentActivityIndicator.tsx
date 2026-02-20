'use client'

import { Loader2, CheckCircle2 } from 'lucide-react'

const TOOL_LABELS: Record<string, string> = {
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

interface AgentActivityIndicatorProps {
  tool: string
  status: 'executing' | 'complete'
}

export function AgentActivityIndicator({
  tool,
  status,
}: AgentActivityIndicatorProps) {
  const label = TOOL_LABELS[tool] || `Running ${tool}...`

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
      {status === 'executing' ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <CheckCircle2 className="h-3 w-3 text-green-500" />
      )}
      <span>{status === 'executing' ? label : label.replace('...', ' - done')}</span>
    </div>
  )
}
