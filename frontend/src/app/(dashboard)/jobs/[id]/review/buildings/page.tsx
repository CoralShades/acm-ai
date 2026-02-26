'use client'

import { use, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { WizardStepHeader } from '@/components/acm/WizardStepHeader'
import { BuildingReviewGrid } from '@/components/acm/BuildingReviewGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useSource } from '@/lib/hooks/use-sources'
import { useExtractionStatus } from '@/lib/hooks/use-extraction-status'
import { AlertTriangle } from 'lucide-react'

/**
 * BuildingReviewPageContent — inner content for the building review wizard step.
 *
 * On mount: sets the source review_status to 'building_review'.
 * On Next: sets review_status to 'acm_review' then navigates to the records step.
 * On Cancel: navigates back to the extract page.
 *
 * URL: /jobs/{source_id}/review/buildings
 * Story: E19-S5 Building Review Wizard Step 1
 */
function BuildingReviewPageContent({ sourceId }: { sourceId: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { data: source } = useSource(sourceId)
  const extractionStatus = useExtractionStatus(
    sourceId,
    source?.review_status === 'extracting' ? source.command_id : undefined
  )
  const wasExtractingRef = useRef(false)

  // On mount: mark the review as started
  useEffect(() => {
    fetch(`/api/sources/${encodeURIComponent(sourceId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: 'building_review' }),
    }).catch(() => {
      // Non-critical: don't block the UI if the status update fails
    })
  }, [sourceId])

  useEffect(() => {
    if (wasExtractingRef.current && extractionStatus.phase === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['buildings', sourceId] })
    }
    wasExtractingRef.current = extractionStatus.phase === 'extracting'
  }, [extractionStatus.phase, queryClient, sourceId])

  const handleCancel = useCallback(() => {
    router.push(`/jobs/${sourceId}/extract`)
  }, [router, sourceId])

  const handleNext = useCallback(async () => {
    // Mark review as progressed to ACM record review step
    try {
      await fetch(`/api/sources/${encodeURIComponent(sourceId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_status: 'acm_review' }),
      })
    } catch {
      // Non-critical: proceed to next step regardless
    }
    router.push(`/jobs/${sourceId}/review/records`)
  }, [router, sourceId])

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
        <WizardStepHeader
          currentStep={1}
          totalSteps={2}
          stepTitle="Review Buildings"
          onCancel={handleCancel}
          onNext={handleNext}
          nextLabel="Next: Review Records \u2192"
        />

        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {extractionStatus.phase === 'extracting' && (
              <Alert className="border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/20 dark:text-amber-200">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Extraction in progress</AlertTitle>
                <AlertDescription>
                  Extraction in progress (Stage {extractionStatus.currentStageIndex ?? 1}/
                  {extractionStatus.totalStages})... Buildings will appear as processed.
                </AlertDescription>
              </Alert>
            )}

            <div className="rounded-xl border bg-card p-4 shadow-sm">
              <BuildingReviewGrid sourceId={sourceId} />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}

/**
 * BuildingReviewPage — Next.js 15 page component with async params.
 *
 * URL: /jobs/[id]/review/buildings
 */
export default function BuildingReviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Building Review"
          reloadUrl="/jobs"
        />
      )}
    >
      <BuildingReviewPageContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
