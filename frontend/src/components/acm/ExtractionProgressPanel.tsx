'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ChevronDown, ChevronUp, CheckCircle2, XCircle } from 'lucide-react'
import { StageProgressPill } from './StageProgressPill'
import { ExtractionLogStream } from './ExtractionLogStream'
import type { ExtractionPhase } from '@/lib/hooks/use-extraction-progress'
import type { PipelineRunState, StageId } from '@/lib/types/pipeline'

interface ExtractionProgressPanelProps {
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  logEntries: string[]
  recordsCreated?: number
  errorMessage?: string
  onDismiss: () => void
}

const STAGE_ORDER: StageId[] = [
  'STRUCTURE',
  'PREFLIGHT',
  'ORCHESTRATOR',
  'EXTRACT',
  'VALIDATE',
  'CORRECT',
  'STORE',
]

export function ExtractionProgressPanel({
  phase,
  pipelineState,
  logEntries,
  recordsCreated,
  errorMessage,
  onDismiss,
}: ExtractionProgressPanelProps) {
  const [logsExpanded, setLogsExpanded] = useState(false)

  if (phase === 'idle') return null

  const stages = pipelineState?.stages
  const completedStages = stages
    ? Object.values(stages).filter((s) => s.status === 'complete').length
    : 0
  const totalStages = STAGE_ORDER.length
  const progressPercent = (completedStages / totalStages) * 100

  // Extracting phase
  if (phase === 'extracting') {
    return (
      <Card className="border-blue-500/50 bg-blue-50/50 dark:bg-blue-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            Extracting ACM Records
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stage Pills */}
          {stages && (
            <div className="flex flex-wrap gap-2">
              {STAGE_ORDER.map((stageId) => {
                const stage = stages[stageId]
                return stage ? <StageProgressPill key={stageId} stage={stage} /> : null
              })}
            </div>
          )}

          {/* Overall Progress Bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Overall Progress</span>
              <span className="font-medium">
                {completedStages} / {totalStages} stages
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-blue-500 transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Record Counter */}
          {pipelineState && pipelineState.total_records > 0 && (
            <div className="text-sm">
              <span className="text-muted-foreground">Records found: </span>
              <span className="font-medium">{pipelineState.total_records}</span>
            </div>
          )}

          {/* Expandable Logs */}
          {logEntries.length > 0 && (
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setLogsExpanded(!logsExpanded)}
                className="h-7 gap-1.5 px-2"
              >
                {logsExpanded ? (
                  <>
                    <ChevronUp className="h-3 w-3" />
                    <span className="text-xs">Hide Logs</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" />
                    <span className="text-xs">Show Logs ({logEntries.length})</span>
                  </>
                )}
              </Button>
              {logsExpanded && <ExtractionLogStream logEntries={logEntries} />}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // Completed phase
  if (phase === 'completed') {
    return (
      <Alert className="border-green-500/50 bg-green-50/50 dark:bg-green-950/20">
        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
        <AlertTitle className="text-green-700 dark:text-green-300">
          Extraction Complete
        </AlertTitle>
        <AlertDescription className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-green-900/80 dark:text-green-100/80">
              {recordsCreated !== undefined
                ? `${recordsCreated} record${recordsCreated !== 1 ? 's' : ''} extracted successfully.`
                : 'Extraction finished successfully.'}
            </span>
            <Button variant="ghost" size="sm" onClick={onDismiss}>
              Dismiss
            </Button>
          </div>

          {/* Stage Pills for completed extraction */}
          {stages && (
            <div className="flex flex-wrap gap-2">
              {STAGE_ORDER.map((stageId) => {
                const stage = stages[stageId]
                return stage ? <StageProgressPill key={stageId} stage={stage} /> : null
              })}
            </div>
          )}

          {/* Expandable Logs */}
          {logEntries.length > 0 && (
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setLogsExpanded(!logsExpanded)}
                className="h-7 gap-1.5 px-2"
              >
                {logsExpanded ? (
                  <>
                    <ChevronUp className="h-3 w-3" />
                    <span className="text-xs">Hide Logs</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" />
                    <span className="text-xs">View Logs ({logEntries.length})</span>
                  </>
                )}
              </Button>
              {logsExpanded && <ExtractionLogStream logEntries={logEntries} />}
            </div>
          )}
        </AlertDescription>
      </Alert>
    )
  }

  // Failed phase
  return (
    <Alert variant="destructive">
      <XCircle className="h-4 w-4" />
      <AlertTitle>Extraction Failed</AlertTitle>
      <AlertDescription className="space-y-3">
        <div className="flex items-center justify-between">
          <span>{errorMessage || 'An unexpected error occurred during extraction.'}</span>
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Dismiss
          </Button>
        </div>

        {/* Stage Pills for failed extraction */}
        {stages && (
          <div className="flex flex-wrap gap-2">
            {STAGE_ORDER.map((stageId) => {
              const stage = stages[stageId]
              return stage ? <StageProgressPill key={stageId} stage={stage} /> : null
            })}
          </div>
        )}

        {/* Expandable Logs */}
        {logEntries.length > 0 && (
          <div className="space-y-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLogsExpanded(!logsExpanded)}
              className="h-7 gap-1.5 px-2"
            >
              {logsExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  <span className="text-xs">Hide Logs</span>
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  <span className="text-xs">View Logs ({logEntries.length})</span>
                </>
              )}
            </Button>
            {logsExpanded && <ExtractionLogStream logEntries={logEntries} />}
          </div>
        )}
      </AlertDescription>
    </Alert>
  )
}
