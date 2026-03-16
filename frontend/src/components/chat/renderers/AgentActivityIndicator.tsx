'use client'

import { Loader2, CheckCircle2 } from 'lucide-react'
import { TOOL_ACTIVITY_LABELS } from '@/lib/constants/tool-labels'

interface AgentActivityIndicatorProps {
  tool: string
  status: 'executing' | 'complete'
}

export function AgentActivityIndicator({
  tool,
  status,
}: AgentActivityIndicatorProps) {
  const label = TOOL_ACTIVITY_LABELS[tool] || `Running ${tool}...`

  return (
    <div role="status" aria-live="polite" className="flex items-center gap-2 text-xs text-muted-foreground py-1">
      {status === 'executing' ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <CheckCircle2 className="h-3 w-3 text-green-500 dark:text-green-400" />
      )}
      <span>{status === 'executing' ? label : label.replace('...', ' - done')}</span>
    </div>
  )
}
