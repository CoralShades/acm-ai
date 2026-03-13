'use client'

import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { ExtractionProgressPanel } from '@/components/acm/ExtractionProgressPanel'
import { RawExtractionTable } from '@/components/acm/RawExtractionTable'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useSource } from '@/lib/hooks/use-sources'
import { useExtractionProgress } from '@/lib/hooks/use-extraction-progress'
import { useExtractionStatus } from '@/lib/hooks/use-extraction-status'
import { useAGUIStream } from '@/lib/hooks/use-agui-stream'
import { acmApi } from '@/lib/api/acm'
import { ArrowRight, FileWarning } from 'lucide-react'

/**
 * Extract page — shows the ExtractionProgressPanel (stage pills + log) alongside
 * the RawExtractionTable (live-updating AG Grid) while the AI processes the document.
 *
 * URL: /jobs/{source_id}/extract
 * Story: E19-S4 Raw Extraction Table — Live Records During Extraction
 */
function ExtractPageContent() {
  const params = useParams()
  const router = useRouter()
  const sourceId = decodeURIComponent(params.id as string)
  const queryClient = useQueryClient()
  const [isRetrying, setIsRetrying] = useState(false)
  const [retryError, setRetryError] = useState<string | null>(null)

  const { data: source, isLoading: isLoadingSource } = useSource(sourceId)

  // Wire extraction progress for the ExtractionProgressPanel
  const extractionProgress = useExtractionProgress(sourceId)
  const extractionStatus = useExtractionStatus(sourceId)

  // AG-UI observability stream — uses the same commandId as extraction progress
  const aguiCommandId =
    extractionProgress.phase === 'extracting'
      ? sessionStorage.getItem(`acm-extraction-progress-${sourceId}`)
        ? JSON.parse(
            sessionStorage.getItem(`acm-extraction-progress-${sourceId}`) || '{}'
          ).commandId || null
        : source?.command_id || null
      : null
  const aguiStream = useAGUIStream(aguiCommandId)

  // Restore in-progress extraction from sessionStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return
    const progressSessionKey = `acm-extraction-progress-${sourceId}`
    const statusSessionKey = `acm-extraction-${sourceId}`
    let commandId: string | null = null

    const storedProgress = sessionStorage.getItem(progressSessionKey)
    if (storedProgress) {
      try {
        const parsed = JSON.parse(storedProgress)
        if (parsed.commandId && parsed.phase === 'extracting') {
          commandId = parsed.commandId
        }
      } catch {
        // Ignore malformed session data
      }
    }

    if (!commandId) {
      commandId = sessionStorage.getItem(statusSessionKey)
    }

    if (!commandId && source?.command_id) {
      commandId = source.command_id
    }

    if (commandId) {
      extractionProgress.startTracking(commandId)
      extractionStatus.startTracking(commandId)
    }

    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source?.command_id, sourceId])

  // Ensure records are fetched immediately once save/completion is reached
  useEffect(() => {
    const shouldRefreshRecords =
      extractionStatus.phase === 'completed' ||
      extractionStatus.currentStageId === 'STORE'

    if (!shouldRefreshRecords) return

    queryClient.invalidateQueries({
      queryKey: ['raw-extraction-records', sourceId],
    })
    queryClient.invalidateQueries({
      queryKey: ['acm', 'records', sourceId],
    })
  }, [
    extractionStatus.currentStageId,
    extractionStatus.phase,
    queryClient,
    sourceId,
  ])

  // Keep polling records while save/completion handoff is active
  useEffect(() => {
    const shouldPollRecords =
      extractionStatus.currentStageId === 'STORE' ||
      extractionStatus.phase === 'completed'

    if (!shouldPollRecords) return

    const interval = window.setInterval(() => {
      queryClient.invalidateQueries({
        queryKey: ['raw-extraction-records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
    }, 5000)

    return () => window.clearInterval(interval)
  }, [
    extractionStatus.currentStageId,
    extractionStatus.phase,
    queryClient,
    sourceId,
  ])

  const handleProceedToReview = () => {
    router.push(`/jobs/${sourceId}/review/buildings`)
  }

  const handleRetry = async () => {
    setIsRetrying(true)
    setRetryError(null)
    try {
      const response = await acmApi.extract(sourceId)
      if (response.command_id) {
        extractionProgress.startTracking(response.command_id)
        extractionStatus.startTracking(response.command_id)
      }
    } catch {
      setRetryError('Retry failed. Please try again.')
    } finally {
      setIsRetrying(false)
    }
  }

  const handleTableComplete = () => {
    // RawExtractionTable calls this when streaming ends — no extra action needed here
    // The user proceeds manually via the button
  }

  const isExtractionComplete = extractionStatus.phase === 'completed'
  const isExtractionFailed = extractionStatus.phase === 'failed'
  const extractionFailureMessage =
    retryError ||
    extractionStatus.errorMessage ||
    extractionProgress.errorMessage ||
    'Extraction failed. Please retry.'

  if (isLoadingSource) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <LoadingSpinner />
        </div>
      </AppShell>
    )
  }

  const sourceTitle = source?.title || `Job ${sourceId}`

  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6 overflow-y-auto">
        {/* Breadcrumbs */}
        <Breadcrumbs
          items={[
            { label: 'Home', href: '/' },
            { label: 'Jobs', href: '/jobs' },
            { label: sourceTitle, href: `/jobs/${sourceId}` },
            { label: 'Extract' },
          ]}
          className="mb-4 flex-shrink-0"
        />

        {/* Page header */}
        <div className="mb-6 flex-shrink-0 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileWarning className="h-6 w-6" />
              Extracting: {sourceTitle}
            </h1>
            <p className="text-muted-foreground mt-1">
              Records are written at the end of extraction. Follow stage progress
              below while processing runs.
            </p>
          </div>

          {/* Proceed to Review button — shown when extraction is complete */}
          {isExtractionComplete && (
            <Button onClick={handleProceedToReview} className="flex-shrink-0">
              Proceed to Building Review
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>

        <div className="space-y-6 flex-1">
          {/* Extraction Progress Panel (stage pills + log terminal) */}
          <ExtractionProgressPanel
            phase={extractionProgress.phase}
            pipelineState={extractionProgress.pipelineState}
            logEntries={extractionProgress.logEntries}
            recordsCreated={extractionProgress.recordsCreated}
            errorMessage={extractionProgress.errorMessage}
            onDismiss={extractionProgress.dismiss}
            reasoningText={aguiStream.reasoningTokens || undefined}
            toolCalls={
              aguiStream.activeToolCall
                ? [
                    {
                      id: aguiStream.activeToolCall.id,
                      name: aguiStream.activeToolCall.name,
                      status: 'running' as const,
                      startedAt: Date.now(),
                    },
                  ]
                : undefined
            }
            aguiStep={aguiStream.currentStep}
            aguiConnected={aguiStream.connected}
          />

          {isExtractionFailed && (
            <Alert variant="destructive" className="border-destructive/50">
              <AlertTitle>Extraction failed</AlertTitle>
              <AlertDescription className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <span>{extractionFailureMessage}</span>
                <Button
                  variant="outline"
                  onClick={handleRetry}
                  disabled={isRetrying}
                >
                  {isRetrying ? 'Retrying...' : 'Retry'}
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Raw Records Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">AI Mapped Records</CardTitle>
            </CardHeader>
            <CardContent>
              <RawExtractionTable
                sourceId={sourceId}
                phase={extractionProgress.phase}
                pipelineState={extractionProgress.pipelineState}
                onComplete={handleTableComplete}
              />
            </CardContent>
          </Card>

          {/* Bottom CTA — shown when complete so user can proceed without scrolling back up */}
          {isExtractionComplete && (
            <div className="flex justify-end pb-4">
              <Button onClick={handleProceedToReview} size="lg">
                Proceed to Building Review
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}

export default function ExtractPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Extract"
          reloadUrl="/jobs"
        />
      )}
    >
      <ExtractPageContent />
    </ErrorBoundary>
  )
}
