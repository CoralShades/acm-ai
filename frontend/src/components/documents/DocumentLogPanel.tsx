'use client'

import { useEffect } from 'react'
import { RefreshCw, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { StageProgressPill } from '@/components/acm/StageProgressPill'
import { ExtractionLogStream } from '@/components/acm/ExtractionLogStream'
import { useDocumentLogPanel } from '@/lib/hooks/use-document-log-panel'
import type { StageId } from '@/lib/types/pipeline'

const STAGE_ORDER: StageId[] = [
  'STRUCTURE',
  'PREFLIGHT',
  'ORCHESTRATOR',
  'EXTRACT',
  'VALIDATE',
  'CORRECT',
  'STORE',
]

const ACTIVE_STATUSES = ['running', 'queued', 'new']

interface DocumentLogPanelProps {
  commandId: string
  sourceId: string
  status: string | undefined
  onRetry: () => void
  onClose: () => void
}

export function DocumentLogPanel(props: DocumentLogPanelProps) {
  const { commandId, status, onRetry, onClose } = props
  const isActive = ACTIVE_STATUSES.includes(status ?? '')
  const { pipelineState, logEntries, phase, isLoading } = useDocumentLogPanel(
    commandId,
    isActive
  )

  const showRetry = phase === 'failed' || status === 'failed'
  const stages = pipelineState?.stages

  // Escape key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  return (
    <div
      className="p-4 bg-muted/30 border-t space-y-3"
      role="region"
      aria-label="Extraction Log"
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose()
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Extraction Log</h4>
        <div className="flex gap-2 items-center">
          {showRetry && (
            <Button size="sm" variant="outline" onClick={onRetry} className="h-7 gap-1.5">
              <RefreshCw className="h-3 w-3" />
              Retry Extraction
            </Button>
          )}
          <Button
            size="icon"
            variant="ghost"
            onClick={onClose}
            className="h-7 w-7"
            aria-label="Close extraction log"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Loading spinner — shown when fetching initial data and no entries yet */}
      {isLoading && logEntries.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading extraction log...
        </div>
      )}

      {/* No data available after loading */}
      {!isLoading && logEntries.length === 0 && !pipelineState && (
        <p className="text-sm text-muted-foreground py-2">No log data available.</p>
      )}

      {/* Stage pills */}
      {stages && (
        <div className="flex flex-wrap gap-2">
          {STAGE_ORDER.map((stageId) => {
            const stage = stages[stageId]
            return stage ? <StageProgressPill key={stageId} stage={stage} /> : null
          })}
        </div>
      )}

      {/* Log stream */}
      {(logEntries.length > 0 || (!isLoading && pipelineState)) && (
        <ExtractionLogStream logEntries={logEntries} />
      )}
    </div>
  )
}
