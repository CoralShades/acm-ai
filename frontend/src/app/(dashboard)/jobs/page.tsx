'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { EmptyState } from '@/components/common/EmptyState'
import { JobCard } from '@/components/jobs/JobCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useSourcesPaginated } from '@/lib/hooks/use-sources-paginated'
import { useCreateDialogs } from '@/lib/hooks/use-create-dialogs'
import { cn } from '@/lib/utils'
import { ClipboardList, Plus, RefreshCw, Search } from 'lucide-react'

type JobFilter =
  | 'all'
  | 'extracting'
  | 'pending_review'
  | 'acm_review'
  | 'published'

const FILTER_OPTIONS: Array<{ id: JobFilter; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'extracting', label: 'Extracting' },
  { id: 'pending_review', label: 'Pending' },
  { id: 'acm_review', label: 'In Review' },
  { id: 'published', label: 'Published' },
]

function JobsPageContent() {
  const router = useRouter()
  const { openSourceDialog } = useCreateDialogs()
  const [searchText, setSearchText] = useState('')
  const [activeFilter, setActiveFilter] = useState<JobFilter>('all')
  const { sources, loading, fetchMore } = useSourcesPaginated({
    limit: 30,
    sortBy: 'updated',
    sortOrder: 'desc',
  })

  useEffect(() => {
    sources.slice(0, 6).forEach((source) => {
      router.prefetch(`/jobs/${source.id}`)
      router.prefetch(`/jobs/${source.id}/extract`)
      router.prefetch(`/jobs/${source.id}/review/buildings`)
      router.prefetch(`/jobs/${source.id}/review/records`)
    })
  }, [router, sources])

  const handleRefetch = useCallback(() => {
    fetchMore(true)
  }, [fetchMore])

  const filteredSources = useMemo(() => {
    const normalizedSearch = searchText.trim().toLowerCase()
    return sources.filter((source) => {
      const rawStatus = source.review_status ?? 'published'
      // Fold building_review into pending_review for simplified filters
      const sourceStatus = rawStatus === 'building_review' ? 'pending_review' : rawStatus
      const matchesFilter = activeFilter === 'all' || sourceStatus === activeFilter
      if (!matchesFilter) return false

      if (!normalizedSearch) return true
      const title = (source.title || '').toLowerCase()
      const id = source.id.toLowerCase()
      return title.includes(normalizedSearch) || id.includes(normalizedSearch)
    })
  }, [activeFilter, searchText, sources])

  const stats = useMemo(() => {
    const extracting = sources.filter((source) => source.review_status === 'extracting').length
    const inReview = sources.filter((source) => {
      const status = source.review_status ?? 'published'
      return status === 'pending_review' || status === 'building_review' || status === 'acm_review'
    }).length
    const published = sources.filter((source) => {
      const status = source.review_status ?? 'published'
      return status === 'published'
    }).length
    return {
      total: sources.length,
      extracting,
      inReview,
      published,
    }
  }, [sources])

  if (loading) {
    return (
      <AppShell>
        <div className="w-full space-y-4 p-6" aria-busy="true">
          <span className="sr-only" role="status">Loading jobs</span>
          <Skeleton className="h-8 w-32" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-24 w-full rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-20 w-full rounded-xl" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <Skeleton key={index} className="h-52 w-full rounded-xl" />
            ))}
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex h-full w-full max-w-none flex-col overflow-y-auto p-6">
        <div className="mb-4 flex flex-shrink-0 items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Jobs</h1>
            <p className="text-muted-foreground">
              Track extraction and review progress for your SAMP documents
            </p>
          </div>
          <Button onClick={openSourceDialog} className="flex-shrink-0">
            <Plus className="mr-2 h-4 w-4" />
            New Job
          </Button>
        </div>

        {sources.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No jobs yet"
            description="Upload your first SAMP document to start extracting ACM register data."
            action={
              <Button onClick={openSourceDialog}>
                <Plus className="mr-2 h-4 w-4" />
                New Job
              </Button>
            }
          />
        ) : (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card className="rounded-xl shadow-sm">
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">Total Jobs</p>
                  <p className="mt-2 text-2xl font-semibold">{stats.total}</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl shadow-sm">
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">Extracting</p>
                  <p className="mt-2 text-2xl font-semibold text-[color:var(--vaea-teal-700)] dark:text-[color:var(--vaea-teal-100)]">
                    {stats.extracting}
                  </p>
                </CardContent>
              </Card>
              <Card className="rounded-xl shadow-sm">
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">In Review</p>
                  <p className="mt-2 text-2xl font-semibold text-[color:var(--vaea-gold)]">
                    {stats.inReview}
                  </p>
                </CardContent>
              </Card>
              <Card className="rounded-xl shadow-sm">
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">Published</p>
                  <p className="mt-2 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">
                    {stats.published}
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card className="rounded-xl shadow-sm">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="relative min-w-[260px] flex-1">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={searchText}
                      onChange={(event) => setSearchText(event.target.value)}
                      placeholder="Search jobs"
                      className="pl-9"
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {FILTER_OPTIONS.map((option) => (
                      <Button
                        key={option.id}
                        variant={activeFilter === option.id ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setActiveFilter(option.id)}
                        className={cn(
                          'rounded-full',
                          activeFilter === option.id &&
                            'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
                        )}
                      >
                        {option.label}
                      </Button>
                    ))}
                  </div>

                  <Button variant="outline" size="sm" onClick={handleRefetch}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-xl shadow-sm">
              <CardContent className="p-4">
                {filteredSources.length === 0 ? (
                  <EmptyState
                    icon={ClipboardList}
                    title="No matching jobs"
                    description="Adjust your filters or search text to see more results."
                  />
                ) : (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredSources.map((source) => (
                      <JobCard
                        key={source.id}
                        source={source}
                        onRefetch={handleRefetch}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
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
