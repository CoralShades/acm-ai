'use client'

import { useCallback } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { EmptyState } from '@/components/common/EmptyState'
import { DocumentsSkeleton } from '@/components/skeletons/DocumentsSkeleton'
import { JobCard } from '@/components/jobs/JobCard'
import { Button } from '@/components/ui/button'
import { useSourcesPaginated } from '@/lib/hooks/use-sources-paginated'
import { useCreateDialogs } from '@/lib/hooks/use-create-dialogs'
import { ClipboardList, Plus } from 'lucide-react'

function JobsPageContent() {
  const { sources, loading, fetchMore } = useSourcesPaginated({
    limit: 30,
    sortBy: 'updated',
    sortOrder: 'desc',
  })

  const { openSourceDialog } = useCreateDialogs()

  const handleRefetch = useCallback(() => {
    fetchMore(true)
  }, [fetchMore])

  if (loading) {
    return (
      <AppShell>
        <DocumentsSkeleton />
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        {/* Page header */}
        <div className="mb-6 flex-shrink-0 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Jobs</h1>
            <p className="text-muted-foreground">
              Track extraction and review progress for your SAMP documents
            </p>
          </div>
          <Button onClick={openSourceDialog} className="flex-shrink-0">
            <Plus className="w-4 h-4 mr-2" />
            New Job
          </Button>
        </div>

        {/* Empty state */}
        {sources.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No jobs yet"
            description="Upload your first SAMP document to start extracting ACM register data."
            action={
              <Button onClick={openSourceDialog}>
                <Plus className="w-4 h-4 mr-2" />
                New Job
              </Button>
            }
          />
        ) : (
          /* Job cards grid */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 overflow-auto">
            {sources.map((source) => (
              <JobCard
                key={source.id}
                source={source}
                onRefetch={handleRefetch}
              />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}

export default function JobsPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Jobs"
          reloadUrl="/jobs"
        />
      )}
    >
      <JobsPageContent />
    </ErrorBoundary>
  )
}
