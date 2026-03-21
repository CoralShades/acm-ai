'use client';

import { useMemo } from 'react'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { DashboardSkeleton } from '@/components/skeletons/DashboardSkeleton';
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSources } from '@/lib/hooks/use-sources';
import { JobStatusPill } from '@/components/jobs/JobStatusPill';
import {
  FileText,
  CheckCircle,
  Upload,
  Clock,
  Loader2,
  Eye,
  ArrowUpRight,
} from 'lucide-react';
import Link from 'next/link';
import { useCreateDialogs } from '@/lib/hooks/use-create-dialogs';
import type { SourceListResponse } from '@/lib/types/api';

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays > 30) return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
  if (diffDays > 0) return `${diffDays}d ago`
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  if (diffHours > 0) return `${diffHours}h ago`
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  if (diffMinutes > 0) return `${diffMinutes}m ago`
  return 'just now'
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function DashboardPageContent() {
  const { data: sources, isLoading: sourcesLoading, error: sourcesError } = useSources();
  const { openSourceDialog } = useCreateDialogs();

  const totalSources = sources?.length || 0;

  const sortedSources = useMemo(() => {
    if (!sources) return []
    return [...sources].sort((a, b) => {
      const dateA = a.created ? new Date(a.created).getTime() : 0;
      const dateB = b.created ? new Date(b.created).getTime() : 0;
      return dateB - dateA;
    })
  }, [sources])

  // Aggregate stats
  const extracting = sources?.filter((s) => s.review_status === 'extracting').length ?? 0;
  const published = sources?.filter((s) => !s.review_status || s.review_status === 'published').length ?? 0;
  const inReview = sources?.filter((s) => {
    const st = s.review_status
    return st === 'pending_review' || st === 'building_review' || st === 'acm_review'
  }).length ?? 0;

  if (sourcesLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="flex h-full w-full max-w-none flex-col overflow-y-auto p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Your ACM compliance overview
          </p>
        </div>
        <Button onClick={openSourceDialog} className="shrink-0">
          <Upload className="w-4 h-4 mr-2" />
          Upload Document
        </Button>
      </div>

      {/* Job summary stat cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="rounded-xl shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">Total Documents</p>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="mt-2 text-2xl font-semibold">{totalSources}</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">AI Extracted</p>
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            </div>
            <p className="mt-2 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">{published}</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">Extracting</p>
              <Loader2 className={`h-4 w-4 text-[color:var(--vaea-teal-500)] ${extracting > 0 ? 'animate-spin' : ''}`} />
            </div>
            <p className="mt-2 text-2xl font-semibold text-[color:var(--vaea-teal-700)] dark:text-[color:var(--vaea-teal-100)]">{extracting}</p>
          </CardContent>
        </Card>

        <Card className="rounded-xl shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">In Review</p>
              <Clock className="h-4 w-4 text-[color:var(--vaea-gold)]" />
            </div>
            <p className="mt-2 text-2xl font-semibold text-[color:var(--vaea-gold)]">{inReview}</p>
          </CardContent>
        </Card>
      </div>

      {/* Documents table */}
      <Card className="rounded-xl shadow-sm flex-1">
        <CardHeader className="pb-3 px-4 pt-4 sm:px-6 sm:pt-6">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">Documents</CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link href="/jobs">
                View Jobs
                <ArrowUpRight className="ml-1.5 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="px-0 pb-2">
          {sourcesError ? (
            <p className="px-6 py-8 text-center text-sm text-destructive">Failed to load documents</p>
          ) : sortedSources.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <FileText className="mx-auto h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">No documents yet</p>
              <Button onClick={openSourceDialog} size="sm" className="mt-4">
                <Upload className="mr-2 h-3.5 w-3.5" />
                Upload your first document
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs font-medium text-muted-foreground">
                    <th className="px-4 py-2.5 sm:px-6">Document</th>
                    <th className="px-3 py-2.5 hidden sm:table-cell">Status</th>
                    <th className="px-3 py-2.5 text-right hidden md:table-cell">Buildings</th>
                    <th className="px-3 py-2.5 text-right hidden md:table-cell">Records</th>
                    <th className="px-3 py-2.5 text-right hidden lg:table-cell">Pages</th>
                    <th className="px-3 py-2.5 text-right hidden lg:table-cell">Size</th>
                    <th className="px-3 py-2.5 hidden sm:table-cell">Uploaded</th>
                    <th className="px-4 py-2.5 sm:px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {sortedSources.map((source) => (
                    <DocumentRow key={source.id} source={source} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DocumentRow({ source }: { source: SourceListResponse }) {
  const isExtracting = source.review_status === 'extracting'
  const jobHref = `/jobs/${source.id}`
  const sourceHref = `/source/${source.id}`

  return (
    <tr className="hover:bg-muted/50 transition-colors">
      <td className="px-4 py-3 sm:px-6">
        <Link href={sourceHref} className="group flex items-center gap-2 min-w-0">
          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="truncate font-medium group-hover:text-primary transition-colors max-w-[200px] sm:max-w-[280px]">
            {source.title || 'Untitled'}
          </span>
        </Link>
      </td>
      <td className="px-3 py-3 hidden sm:table-cell">
        <JobStatusPill review_status={source.review_status} className="text-[10px]" />
      </td>
      <td className="px-3 py-3 text-right tabular-nums text-muted-foreground hidden md:table-cell">
        {source.building_count ?? '—'}
      </td>
      <td className="px-3 py-3 text-right tabular-nums text-muted-foreground hidden md:table-cell">
        {(source.records_count ?? 0) > 0 ? source.records_count : '—'}
      </td>
      <td className="px-3 py-3 text-right tabular-nums text-muted-foreground hidden lg:table-cell">
        {source.page_count ? source.page_count : '—'}
      </td>
      <td className="px-3 py-3 text-right text-muted-foreground hidden lg:table-cell">
        {source.file_size ? formatFileSize(source.file_size) : '—'}
      </td>
      <td className="px-3 py-3 text-muted-foreground whitespace-nowrap hidden sm:table-cell">
        {formatRelativeDate(source.created)}
      </td>
      <td className="px-4 py-3 sm:px-6 text-right">
        <Button variant="ghost" size="sm" asChild className="h-7 px-2 text-xs">
          <Link href={isExtracting ? `${jobHref}/extract` : jobHref}>
            <Eye className="h-3 w-3 mr-1" />
            {isExtracting ? 'Track' : 'View'}
          </Link>
        </Button>
      </td>
    </tr>
  )
}

export default function DashboardPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Dashboard"
          reloadUrl="/"
        />
      )}
    >
      <AppShell>
        <DashboardPageContent />
      </AppShell>
    </ErrorBoundary>
  )
}
