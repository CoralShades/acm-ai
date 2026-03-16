'use client'

/**
 * ExtractionProgress — full-page progress wrapper for the /extraction/[id] route.
 *
 * Responsibilities:
 * - Restore in-flight extraction state from sessionStorage on mount
 * - Render ExtractionProgressPanel (stage pills + log stream)
 * - Show aggregate building-stage cards derived from PipelineRunState
 * - Auto-redirect to /source/:id on phase === 'completed' (2s delay)
 * - Show error toast for warnings when completed
 * - Show fatal error Dialog when phase === 'failed'
 *
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import {
  Building2,
  CheckCircle2,
  Database,
  Loader2,
  ShieldCheck,
  Table2,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ExtractionProgressPanel } from '@/components/acm/ExtractionProgressPanel'
import { useExtractionSSE } from '@/lib/hooks/useExtractionSSE'
import { useToast } from '@/lib/hooks/use-toast'
import { PIPELINE_STAGE_ORDER } from '@/lib/types/pipeline'
import { cn } from '@/lib/utils'

const RawTableViewer = dynamic(
  () => import('./RawTableViewer').then((m) => ({ default: m.RawTableViewer })),
  { ssr: false, loading: () => null }
)

/**
 * BuildingProgress — per-building data shape reserved for future SSE payloads.
 * Included now so ExtractionProgress can accept it without a rewrite later.
 */
export interface BuildingProgress {
  id: string
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  recordCount?: number
}

interface ExtractionProgressProps {
  sourceId: string
  /** Reserved for future per-building SSE data (currently unused). */
  buildings?: BuildingProgress[]
}

/** Derive a human-readable stage group label from active pipeline stages. */
type StageGroup = 'analyzing' | 'extracting' | 'validating' | 'storing'

function getActiveStageGroup(
  stages: Record<string, { status: string }> | undefined
): StageGroup | null {
  if (!stages) return null

  const analyzeStages: string[] = ['STRUCTURE', 'PREFLIGHT', 'ORCHESTRATOR', 'DOCLING_EXTRACTION']
  const extractStages: string[] = ['EXTRACT']
  const validateStages: string[] = ['VALIDATE', 'CORRECT']
  const storeStages: string[] = ['STORE', 'NO_ACCESS_RECOVERY']

  const isRunning = (ids: string[]) => ids.some((id) => stages[id]?.status === 'running')
  const isComplete = (ids: string[]) => ids.every((id) => stages[id]?.status === 'complete' || stages[id]?.status === 'skipped')

  if (isRunning(storeStages)) return 'storing'
  if (isRunning(validateStages)) return 'validating'
  if (isRunning(extractStages)) return 'extracting'
  if (isRunning(analyzeStages)) return 'analyzing'
  if (isComplete(storeStages)) return 'storing'
  return null
}

const STAGE_GROUP_CONFIG: Record<StageGroup, { label: string; description: string; Icon: typeof Loader2 }> = {
  analyzing: {
    label: 'Analyzing',
    description: 'Detecting document structure and building inventory',
    Icon: Building2,
  },
  extracting: {
    label: 'Extracting',
    description: 'Reading ACM records from each building section',
    Icon: Loader2,
  },
  validating: {
    label: 'Validating',
    description: 'Checking extracted records against SF schema',
    Icon: ShieldCheck,
  },
  storing: {
    label: 'Storing',
    description: 'Saving validated records to the register',
    Icon: Database,
  },
}

export function ExtractionProgress({ sourceId, buildings }: ExtractionProgressProps) {
  const router = useRouter()
  const { warning: toastWarning } = useToast()

  const {
    phase,
    pipelineState,
    logEntries,
    recordsCreated,
    errorMessage,
    aguiStep,
    aguiConnected,
    reasoningText,
    startTracking,
    dismiss,
  } = useExtractionSSE(sourceId)

  // Restore in-progress extraction from sessionStorage on mount (reload resilience)
  useEffect(() => {
    if (typeof window === 'undefined') return

    const progressKey = `acm-extraction-progress-${sourceId}`
    const simpleKey = `acm-extraction-${sourceId}`

    let commandId: string | null = null

    // Try the structured key first (written by useExtractionProgress)
    const storedProgress = sessionStorage.getItem(progressKey)
    if (storedProgress) {
      try {
        const parsed = JSON.parse(storedProgress)
        if (parsed.commandId && parsed.phase === 'extracting') {
          commandId = parsed.commandId
        }
      } catch {
        // Ignore malformed data
      }
    }

    // Fall back to the simple key written by UploadWizard
    if (!commandId) {
      commandId = sessionStorage.getItem(simpleKey)
    }

    if (commandId) {
      startTracking(commandId)
    }

    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId])

  // Auto-redirect to /source/:id when extraction completes
  useEffect(() => {
    if (phase !== 'completed') return

    const timer = setTimeout(() => {
      router.push(`/source/${encodeURIComponent(sourceId)}`)
    }, 2000)

    return () => clearTimeout(timer)
  }, [phase, sourceId, router])

  // Show warning toast when completed with pipeline warnings.
  // The fired-guard prevents duplicate toasts when pipelineState updates
  // after phase has already become 'completed'.
  useEffect(() => {
    if (phase !== 'completed') return
    if (warnToastFiredRef.current) return // already fired

    const stages = pipelineState?.stages
    if (!stages) return

    const hasStageErrors = Object.values(stages as Record<string, { error?: { message?: string } }>).some(
      (s) => s.error?.message
    )
    if (hasStageErrors) {
      warnToastFiredRef.current = true
      toastWarning('Extraction complete with warnings. Some stages reported issues.')
    }
  }, [phase, pipelineState, toastWarning])

  // Guard so the warning toast fires at most once per extraction completion,
  // even if pipelineState updates again after phase becomes 'completed'.
  const warnToastFiredRef = useRef(false)

  const handleRetry = () => {
    dismiss()
    router.refresh()
  }

  // Derive aggregate building-stage card
  const activeGroup = getActiveStageGroup(
    pipelineState?.stages as Record<string, { status: string }> | undefined
  )
  const totalBuildings = pipelineState?.total_buildings ?? 0
  const showBuildingCards = totalBuildings > 0 && activeGroup !== null

  // Calculate overall progress percentage
  const stages = pipelineState?.stages
  const completedStages = stages
    ? Object.values(stages).filter((s) => s.status === 'complete').length
    : 0
  const progressPercent = Math.round((completedStages / PIPELINE_STAGE_ORDER.length) * 100)

  // Show raw tables once DOCLING_EXTRACTION stage has started (running, complete, or any later stage active)
  const doclingStageStatus = stages?.DOCLING_EXTRACTION?.status
  const showRawTables =
    phase === 'completed' ||
    phase === 'failed' ||
    doclingStageStatus === 'running' ||
    doclingStageStatus === 'complete'

  return (
    <div className="flex flex-col h-full overflow-y-auto" data-testid="extraction-progress">
      <div className="max-w-4xl mx-auto w-full px-6 py-8 space-y-6">

        {/* Page header with overall progress percentage */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">Extraction Progress</h1>
          {phase === 'extracting' && (
            <p className="text-muted-foreground text-sm">
              {progressPercent}% complete — processing your SAMP document
            </p>
          )}
          {phase === 'completed' && (
            <p className="text-emerald-600 dark:text-emerald-400 text-sm font-medium">
              Extraction complete. Redirecting to ACM Register...
            </p>
          )}
        </div>

        {/* Building stage cards — shown when total_buildings > 0 */}
        {showBuildingCards && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(Object.keys(STAGE_GROUP_CONFIG) as StageGroup[]).map((group) => {
              const config = STAGE_GROUP_CONFIG[group]
              const isActive = group === activeGroup
              const isDone =
                activeGroup !== null &&
                (Object.keys(STAGE_GROUP_CONFIG) as StageGroup[]).indexOf(group) <
                  (Object.keys(STAGE_GROUP_CONFIG) as StageGroup[]).indexOf(activeGroup)
              const Icon = isActive ? Loader2 : isDone ? CheckCircle2 : config.Icon

              return (
                <Card
                  key={group}
                  className={cn(
                    'transition-colors',
                    isActive && 'border-teal-500/60 bg-teal-500/10',
                    isDone && 'border-emerald-500/40 bg-emerald-500/5'
                  )}
                >
                  <CardContent className="pt-4 pb-4 flex items-start gap-3">
                    <Icon
                      className={cn(
                        'mt-0.5 h-5 w-5 shrink-0',
                        isActive && 'animate-spin text-teal-600 dark:text-teal-400',
                        isDone && 'text-emerald-600 dark:text-emerald-400',
                        !isActive && !isDone && 'text-muted-foreground'
                      )}
                    />
                    <div className="min-w-0">
                      <p className="font-medium text-sm">{config.label}</p>
                      <p className="text-xs text-muted-foreground">{config.description}</p>
                      {isActive && totalBuildings > 0 && (
                        <p className="text-xs text-teal-700 dark:text-teal-300 mt-1">
                          {totalBuildings} building{totalBuildings !== 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}

        {/* Main extraction progress panel */}
        <ExtractionProgressPanel
          phase={phase}
          pipelineState={pipelineState}
          logEntries={logEntries}
          recordsCreated={recordsCreated}
          errorMessage={errorMessage}
          onDismiss={dismiss}
          reasoningText={reasoningText}
          aguiStep={aguiStep}
          aguiConnected={aguiConnected}
        />

        {/* Raw Docling tables — shown once document analysis is underway */}
        {showRawTables && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Table2 className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-lg font-semibold">Raw Tables Discovered</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Tables found in the document by Docling and MinerU. These feed into the ACM extraction pipeline.
            </p>
            <RawTableViewer
              sourceId={sourceId}
              refetchInterval={phase === 'extracting' ? 5000 : false}
            />
          </div>
        )}

        {/* Buildings prop forwarding (future per-building granularity) */}
        {buildings && buildings.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {buildings.map((building) => (
              <Card
                key={building.id}
                className={cn(
                  'transition-colors',
                  building.status === 'running' && 'border-teal-500/60 bg-teal-500/10',
                  building.status === 'complete' && 'border-emerald-500/40 bg-emerald-500/5',
                  building.status === 'error' && 'border-destructive/40 bg-destructive/5'
                )}
              >
                <CardContent className="pt-4 pb-4 flex items-center gap-3">
                  {building.status === 'running' ? (
                    <Loader2 className="h-4 w-4 animate-spin text-teal-600 dark:text-teal-400 shrink-0" />
                  ) : building.status === 'complete' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  ) : (
                    <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{building.name}</p>
                    {building.recordCount !== undefined && (
                      <p className="text-xs text-muted-foreground">
                        {building.recordCount} record{building.recordCount !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Fatal error dialog */}
      <Dialog
        open={phase === 'failed'}
        onOpenChange={(open) => {
          if (!open) dismiss()
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Extraction Failed</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            {errorMessage || 'An unexpected error occurred during extraction.'}
          </p>
          <DialogFooter>
            <Button onClick={() => router.push('/jobs')}>Back to Jobs</Button>
            <Button variant="outline" onClick={handleRetry}>
              Retry
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
