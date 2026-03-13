'use client'

import { use, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { WizardStepHeader } from '@/components/acm/WizardStepHeader'
import { BuildingTabFilter } from '@/components/acm/BuildingTabFilter'
import { ACMReviewGrid } from '@/components/acm/ACMReviewGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import type { ACMRecord } from '@/lib/types/acm'

/**
 * RecordsReviewPageContent — inner content for the ACM records review wizard step.
 *
 * On Next: calls publish endpoint then navigates to the jobs list.
 * On Cancel: navigates back to the buildings review step.
 *
 * URL: /jobs/{source_id}/review/records
 * Story: E19-S6 ACM Schema Mapping Wizard — Step 2 (Frontend)
 */
function RecordsReviewPageContent({ sourceId }: { sourceId: string }) {
  const router = useRouter()
  const [selectedBuilding, setSelectedBuilding] = useState<string | null>(null)
  const [showPublishDialog, setShowPublishDialog] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)

  // Fetch records to drive building tab filters
  const { data: records = [], refetch: refetchRecords } = useQuery<ACMRecord[]>({
    queryKey: ['acm-records', sourceId],
    queryFn: () =>
      fetch(`/api/acm/records?source_id=${encodeURIComponent(sourceId)}&limit=500`)
        .then((r) => r.json())
        .then((d) => (Array.isArray(d) ? d : (d.records ?? []))),
    staleTime: 30_000,
  })

  const handleCancel = useCallback(() => {
    router.push(`/jobs/${sourceId}/review/buildings`)
  }, [router, sourceId])

  const handlePublish = useCallback(async () => {
    setIsPublishing(true)
    try {
      await fetch(`/api/acm/jobs/${encodeURIComponent(sourceId)}/publish`, {
        method: 'POST',
      })
    } catch {
      // Non-critical: proceed to jobs list regardless
    } finally {
      setIsPublishing(false)
      setShowPublishDialog(false)
      router.push('/jobs')
    }
  }, [router, sourceId])

  const handleRecordsDataChanged = useCallback(() => {
    void refetchRecords()
  }, [refetchRecords])

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
        <WizardStepHeader
          currentStep={2}
          totalSteps={2}
          stepTitle="Review ACM Records"
          onCancel={handleCancel}
          onNext={() => setShowPublishDialog(true)}
          nextLabel="Publish to Register"
        />

        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            <Card className="rounded-xl shadow-sm">
              <CardContent className="p-4">
                <BuildingTabFilter
                  records={records}
                  selectedBuilding={selectedBuilding}
                  onBuildingChange={setSelectedBuilding}
                />
              </CardContent>
            </Card>

            <Card className="rounded-xl shadow-sm">
              <CardContent className="p-4">
                <ACMReviewGrid
                  sourceId={sourceId}
                  buildingId={selectedBuilding}
                  onDataChanged={handleRecordsDataChanged}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Publish confirmation dialog */}
      <ConfirmDialog
        open={showPublishDialog}
        onOpenChange={setShowPublishDialog}
        title="Publish to ACM Register?"
        description={`This will publish ${records.length} record${records.length !== 1 ? 's' : ''} to the ACM Register. This action marks the job as complete.`}
        confirmText="Publish"
        onConfirm={handlePublish}
        isLoading={isPublishing}
      />
    </AppShell>
  )
}

/**
 * RecordsReviewPage — Next.js 15 page component with async params.
 *
 * URL: /jobs/[id]/review/records
 */
export default function RecordsReviewPage({
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
          pageName="ACM Records Review"
          reloadUrl="/jobs"
        />
      )}
    >
      <RecordsReviewPageContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
