'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
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
import { acmApi } from '@/lib/api/acm'
import { FileWarning } from 'lucide-react'

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
  const [isRetrying, setIsRetrying] = useState(false)
  const [retryError, setRetryError] = useState<string | null>(null)

  const { data: source, isLoading: isLoadingSource } = useSource(sourceId)

  // Wire extraction progress for the ExtractionProgressPanel
  const extractionProgress = useExtractionProgress(sourceId)
  const extractionStatus = useExtractionStatus(sourceId)

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
              Records appear below as the AI processes each section of the document.
            </p>
          </div>

          {/* Proceed to Review button — shown when extraction is complete */}
          {isExtractionComplete && (
            <Button onClick={handleProceedToReview} className="flex-shrink-0">
              Proceed to Building Review &rarr;
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
              <CardTitle className="text-base">Live Record Stream</CardTitle>
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
                Proceed to Building Review &rarr;
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
