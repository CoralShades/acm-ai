'use client'

import { use, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { WizardStepHeader } from '@/components/acm/WizardStepHeader'
import { BuildingReviewGrid } from '@/components/acm/BuildingReviewGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'

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

        <div className="flex-1 overflow-y-auto p-4">
          <BuildingReviewGrid sourceId={sourceId} />
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
