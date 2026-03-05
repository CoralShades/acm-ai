'use client'

import { use } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { ProvenanceViewer } from '@/components/acm/ProvenanceViewer'

function ProvenancePageContent({
  sourceId,
  recordId,
}: {
  sourceId: string
  recordId: string
}) {
  return (
    <AppShell>
      <ProvenanceViewer
        sourceId={sourceId}
        recordId={recordId}
        mode="page"
      />
    </AppShell>
  )
}

/**
 * ProvenancePage — full-page provenance viewer for a single ACM record.
 *
 * URL: /source/[id]/provenance/[recordId]
 * Story: E33-S6 Provenance Viewer (AC6)
 */
export default function ProvenancePage({
  params,
}: {
  params: Promise<{ id: string; recordId: string }>
}) {
  const { id: sourceId, recordId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Record Provenance" reloadUrl="/sources" />
      )}
    >
      <ProvenancePageContent
        sourceId={decodeURIComponent(sourceId)}
        recordId={decodeURIComponent(recordId)}
      />
    </ErrorBoundary>
  )
}
