'use client'

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { AppShell } from '@/components/layout/AppShell'
import { UploadWizard } from '@/components/acm/UploadWizard'

/**
 * UploadPage — dedicated route for uploading a SAMP PDF and triggering extraction.
 *
 * URL: /upload
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */
export default function UploadPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Upload" reloadUrl="/jobs" />
      )}
    >
      <AppShell>
        <UploadWizard />
      </AppShell>
    </ErrorBoundary>
  )
}
