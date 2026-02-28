'use client'

import { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Database,
  FileSearch,
  Loader2,
  RefreshCw,
  Search,
  Settings2,
  Table2,
  TableProperties,
  XCircle,
  type LucideIcon,
} from 'lucide-react'
import { ExtractionLogStream } from './ExtractionLogStream'
import { ExtractionThinkingPanel } from './ExtractionThinkingPanel'
import { ExtractionToolCallFeed, type ToolCallEntry } from './ExtractionToolCallFeed'
import type { ExtractionPhase } from '@/lib/hooks/use-extraction-progress'
import {
  PIPELINE_STAGE_ORDER,
  type PipelineRunState,
  type StageId,
} from '@/lib/types/pipeline'
import { cn } from '@/lib/utils'

interface ExtractionProgressPanelProps {
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  logEntries: string[]
  recordsCreated?: number
  errorMessage?: string
  onDismiss: () => void
  // AG-UI observability (E17-S3, E17-S4)
  reasoningText?: string
  toolCalls?: ToolCallEntry[]
}

const STAGE_CONFIG: Record<StageId, { label: string; icon: LucideIcon }> = {
  STRUCTURE: { label: 'Document Analysis', icon: FileSearch },
  PREFLIGHT: { label: 'Format Detection', icon: Settings2 },
  ORCHESTRATOR: { label: 'Building Inventory', icon: Building2 },
  DOCLING_EXTRACTION: { label: 'Docling Tables', icon: TableProperties },
  EXTRACT: { label: 'Extracting Records', icon: Table2 },
  VALIDATE: { label: 'Validation', icon: CheckCircle2 },
  CORRECT: { label: 'Corrective Loop', icon: RefreshCw },
  NO_ACCESS_RECOVERY: { label: 'Recovery Scan', icon: Search },
  STORE: { label: 'Saving Records', icon: Database },
}

const WARNING_PATTERNS = [
  /provider schema\/compat/i,
  /compiled grammar is too large/i,
  /falling back/i,
  /must be one of/i,
  /\bwarning\b/i,
  /\berror\b/i,
  /\bfailed\b/i,
]

function formatDuration(ms: number | null | undefined): string | null {
  if (ms == null || Number.isNaN(ms) || ms < 0) return null
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return `${minutes}m ${remainder}s`
}

function cleanLogEntry(entry: string): string {
  return entry
    .replace(/^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]\s*/, '')
    .replace(/^\[PIPELINE\]\s*/, '')
    .trim()
}

export function ExtractionProgressPanel({
  phase,
  pipelineState,
  logEntries,
  recordsCreated,
  errorMessage,
  onDismiss,
  reasoningText,
  toolCalls,
}: ExtractionProgressPanelProps) {
  const [logsExpanded, setLogsExpanded] = useState(false)
  const [nowMs, setNowMs] = useState(() => Date.now())

  useEffect(() => {
    if (phase !== 'extracting') return
    const interval = window.setInterval(() => {
      setNowMs(Date.now())
    }, 1000)
    return () => window.clearInterval(interval)
  }, [phase])

  const stages = pipelineState?.stages
  const completedStages = stages
    ? Object.values(stages).filter((s) => s.status === 'complete').length
    : 0
  const totalStages = PIPELINE_STAGE_ORDER.length
  const progressPercent = (completedStages / totalStages) * 100

  const currentStageId = stages
    ? PIPELINE_STAGE_ORDER.find((stageId) => stages[stageId]?.status === 'running')
    : undefined

  const currentStage = currentStageId ? stages?.[currentStageId] : undefined
  const currentStageElapsed = currentStage?.entered_at
    ? Date.parse(currentStage.entered_at)
    : NaN
  const elapsedLabel = Number.isNaN(currentStageElapsed)
    ? null
    : formatDuration(nowMs - currentStageElapsed)

  const warningMessages = useMemo(() => {
    const messages: string[] = []

    if (stages) {
      for (const stageId of PIPELINE_STAGE_ORDER) {
        const stageError = stages[stageId]?.error?.message
        if (stageError) {
          messages.push(stageError.trim())
        }
      }
    }

    for (const entry of logEntries) {
      if (WARNING_PATTERNS.some((pattern) => pattern.test(entry))) {
        const cleaned = cleanLogEntry(entry)
        if (cleaned) {
          messages.push(cleaned)
        }
      }
    }

    return Array.from(new Set(messages)).slice(-6)
  }, [logEntries, stages])

  const warningsBlock =
    warningMessages.length > 0 ? (
      <div className="space-y-2 rounded-md border border-destructive/40 bg-destructive/5 p-3">
        <h4 className="text-sm font-medium text-destructive">Extraction Warnings</h4>
        <div className="space-y-1.5">
          {warningMessages.map((message, index) => (
            <div
              key={`${message}-${index}`}
              className="rounded bg-destructive/10 px-2 py-1.5 text-xs text-destructive"
            >
              {message}
            </div>
          ))}
        </div>
      </div>
    ) : null

  if (phase === 'idle') return null

  // Extracting phase
  if (phase === 'extracting') {
    return (
      <Card className="border-primary/50 bg-primary/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Loader2 className="h-4 w-4 animate-spin" />
            Extraction in Progress
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stage progression */}
          {stages && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-foreground">Pipeline Stages</span>
                <span className="text-muted-foreground">
                  {completedStages} / {totalStages} complete
                </span>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {PIPELINE_STAGE_ORDER.map((stageId, index) => {
                  const stage = stages[stageId]
                  const stageStatus = stage?.status ?? 'pending'
                  const isCurrent = stageStatus === 'running'
                  const isComplete = stageStatus === 'complete'
                  const isFailed = stageStatus === 'failed'
                  const StageIcon =
                    isCurrent
                      ? Loader2
                      : isComplete
                        ? CheckCircle2
                        : STAGE_CONFIG[stageId].icon

                  const stageElapsed = isCurrent
                    ? elapsedLabel
                    : formatDuration(stage?.duration_ms)

                  return (
                    <div
                      key={stageId}
                      className={cn(
                        'rounded-md border p-3 transition-colors',
                        isCurrent &&
                          'border-teal-500/60 bg-teal-500/10 text-teal-800 dark:text-teal-200',
                        isComplete &&
                          'border-emerald-500/50 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200',
                        isFailed &&
                          'border-destructive/50 bg-destructive/10 text-destructive',
                        !isCurrent &&
                          !isComplete &&
                          !isFailed &&
                          'border-border/60 bg-muted/40 text-muted-foreground'
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2">
                          <StageIcon
                            className={cn(
                              'mt-0.5 h-4 w-4 shrink-0',
                              isCurrent && 'animate-spin',
                              isComplete && 'text-emerald-600 dark:text-emerald-400'
                            )}
                          />
                          <div>
                            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                              Stage {index + 1}
                            </p>
                            <p className="text-sm font-medium">
                              {STAGE_CONFIG[stageId].label}
                            </p>
                          </div>
                        </div>
                        {stageElapsed && (
                          <span className="text-[11px] font-medium">
                            {isCurrent ? `Elapsed ${stageElapsed}` : stageElapsed}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
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
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {currentStageId === 'EXTRACT' && (
            <p className="text-sm text-muted-foreground">
              AI is analyzing each building&apos;s asbestos records. This typically
              takes 60-90 seconds. Records will appear when processing is complete.
            </p>
          )}

          {currentStageId === 'STORE' && (
            <p className="text-sm text-muted-foreground">
              Saving extracted records now. The records table will refresh as soon
              as persistence completes.
            </p>
          )}

          {currentStageId &&
            currentStage?.message &&
            currentStageId !== 'EXTRACT' &&
            currentStageId !== 'STORE' && (
              <p className="text-sm text-muted-foreground">{currentStage.message}</p>
            )}

          {/* Record Counter */}
          {pipelineState && pipelineState.total_records > 0 && (
            <div className="text-sm">
              <span className="text-muted-foreground">Records found: </span>
              <span className="font-medium">{pipelineState.total_records}</span>
            </div>
          )}

          {warningsBlock}

          {/* Tool Call Feed (E17-S4) */}
          {toolCalls && toolCalls.length > 0 && (
            <ExtractionToolCallFeed toolCalls={toolCalls} />
          )}

          {/* Reasoning/Thinking Panel (E17-S3) */}
          {reasoningText && <ExtractionThinkingPanel reasoningText={reasoningText} />}

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

          {warningsBlock}

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

        {warningsBlock}

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
