'use client'

import { use } from 'react'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { AppShell } from '@/components/layout/AppShell'
import { ExtractionProgress } from '@/components/acm/ExtractionProgress'

/**
 * ExtractionPage — SSE-powered progress view while extraction runs.
 * Automatically redirects to /source/:id on completion.
 *
 * URL: /extraction/[id]  (id = URL-encoded source ID)
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */
export default function ExtractionPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Extraction" reloadUrl="/jobs" />
      )}
    >
      <AppShell>
        <ExtractionProgress sourceId={decodeURIComponent(id)} />
      </AppShell>
    </ErrorBoundary>
  )
}
