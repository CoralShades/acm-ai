'use client'

import { use } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { RawTableGrid } from '@/components/acm/RawTableGrid'

function RawTableReviewContent({ sourceId }: { sourceId: string }) {
  return (
    <AppShell>
      <RawTableGrid sourceId={sourceId} />
    </AppShell>
  )
}

/**
 * RawTableReviewPage — Next.js 15 page component with async params.
 *
 * URL: /source/[id]/raw
 * Story: E33-S5 Raw Table Review (Opt-In)
 */
export default function RawTableReviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Raw Table Review" reloadUrl="/jobs" />
      )}
    >
      <RawTableReviewContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
