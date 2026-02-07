'use client'

import { useRouter } from 'next/navigation'
import { sourcesApi } from '@/lib/api/sources'
import { SourceListResponse } from '@/lib/types/api'
import {
  useProcessingStatus,
  type ProcessingStats,
} from '@/lib/hooks/use-processing-status'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Eye,
  FileText,
  ExternalLink,
  Upload,
} from 'lucide-react'
import { toast } from 'sonner'

function getDocumentIcon(doc: SourceListResponse) {
  if (doc.asset?.file_path) return Upload
  if (doc.asset?.url) return ExternalLink
  return FileText
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatRelativeTime(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

// --- Status Summary Cards ---

interface StatusCardProps {
  title: string
  count: number
  icon: React.ReactNode
  colorClass: string
}

function StatusCard({ title, count, icon, colorClass }: StatusCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className={`p-2 rounded-lg ${colorClass}`}>{icon}</div>
        <div>
          <p className="text-2xl font-bold">{count}</p>
          <p className="text-sm text-muted-foreground">{title}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function StatusSummary({ stats }: { stats: ProcessingStats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatusCard
        title="In Progress"
        count={stats.inProgress}
        icon={<Loader2 className="w-5 h-5 animate-spin text-blue-600 dark:text-blue-400" />}
        colorClass="bg-blue-100 dark:bg-blue-900/30"
      />
      <StatusCard
        title="Pending"
        count={stats.pending}
        icon={<Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />}
        colorClass="bg-amber-100 dark:bg-amber-900/30"
      />
      <StatusCard
        title="Completed"
        count={stats.completed}
        icon={<CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />}
        colorClass="bg-green-100 dark:bg-green-900/30"
      />
      <StatusCard
        title="Failed"
        count={stats.failed}
        icon={<AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />}
        colorClass="bg-red-100 dark:bg-red-900/30"
      />
    </div>
  )
}

// --- In Progress Queue ---

function InProgressItem({ source }: { source: SourceListResponse }) {
  const router = useRouter()
  const Icon = getDocumentIcon(source)

  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
      <Loader2 className="w-4 h-4 animate-spin text-blue-500 flex-shrink-0" />
      <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{source.title || 'Untitled'}</p>
        <p className="text-xs text-muted-foreground">
          Started {formatRelativeTime(source.updated)}
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/sources/${source.id}`)}
      >
        <Eye className="w-4 h-4" />
      </Button>
    </div>
  )
}

function InProgressQueue({ sources }: { sources: SourceListResponse[] }) {
  if (sources.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          Processing ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {sources.map((source) => (
          <InProgressItem key={source.id} source={source} />
        ))}
      </CardContent>
    </Card>
  )
}

// --- Pending Queue ---

function PendingQueue({ sources }: { sources: SourceListResponse[] }) {
  if (sources.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Clock className="w-4 h-4 text-amber-500" />
          Pending ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {sources.map((source) => {
            const Icon = getDocumentIcon(source)
            return (
              <div
                key={source.id}
                className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg"
              >
                <Clock className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">
                    {source.title || 'Untitled'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Queued {formatRelativeTime(source.created)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

// --- Failed Queue ---

function FailedItem({
  source,
  onRetry,
}: {
  source: SourceListResponse
  onRetry: () => void
}) {
  const router = useRouter()
  const Icon = getDocumentIcon(source)
  const errorMessage =
    (source.processing_info?.error as string) || 'Processing failed'

  return (
    <div className="flex items-start gap-3 p-3 bg-destructive/5 border border-destructive/20 rounded-lg">
      <AlertCircle className="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          <span className="font-medium truncate">
            {source.title || 'Untitled'}
          </span>
          <Badge variant="destructive" className="text-xs flex-shrink-0">
            Failed
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {errorMessage}
        </p>
      </div>
      <div className="flex gap-1 flex-shrink-0">
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="w-3 h-3 mr-1" />
          Retry
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/sources/${source.id}`)}
        >
          <Eye className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}

function FailedQueue({
  sources,
  onRefetch,
}: {
  sources: SourceListResponse[]
  onRefetch: () => void
}) {
  if (sources.length === 0) return null

  const handleRetry = async (sourceId: string) => {
    try {
      await sourcesApi.retry(sourceId)
      toast.success('Re-processing started')
      onRefetch()
    } catch {
      toast.error('Failed to retry')
    }
  }

  return (
    <Card className="border-destructive/30">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-destructive">
          <AlertCircle className="w-4 h-4" />
          Failed ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {sources.map((source) => (
          <FailedItem
            key={source.id}
            source={source}
            onRetry={() => handleRetry(source.id)}
          />
        ))}
      </CardContent>
    </Card>
  )
}

// --- Recent Completions ---

function CompletedTable({ sources }: { sources: SourceListResponse[] }) {
  const router = useRouter()
  const recentSources = sources.slice(0, 15)

  if (recentSources.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <CheckCircle className="w-4 h-4 text-green-500" />
            Recently Completed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            No completed documents yet
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CheckCircle className="w-4 h-4 text-green-500" />
          Recently Completed ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-2.5 text-xs font-medium text-muted-foreground">
                  Document
                </th>
                <th className="text-left p-2.5 text-xs font-medium text-muted-foreground hidden sm:table-cell">
                  Completed
                </th>
                <th className="text-left p-2.5 text-xs font-medium text-muted-foreground hidden md:table-cell">
                  Chunks
                </th>
                <th className="text-left p-2.5 text-xs font-medium text-muted-foreground hidden md:table-cell">
                  Insights
                </th>
                <th className="w-10 p-2.5" />
              </tr>
            </thead>
            <tbody>
              {recentSources.map((source) => {
                const Icon = getDocumentIcon(source)
                return (
                  <tr
                    key={source.id}
                    className="border-b last:border-b-0 hover:bg-muted/30 cursor-pointer transition-colors"
                    onClick={() => router.push(`/sources/${source.id}`)}
                  >
                    <td className="p-2.5">
                      <div className="flex items-center gap-2 min-w-0">
                        <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <span className="text-sm font-medium truncate">
                          {source.title || 'Untitled'}
                        </span>
                      </div>
                    </td>
                    <td className="p-2.5 text-xs text-muted-foreground hidden sm:table-cell">
                      {formatDate(source.updated)}
                    </td>
                    <td className="p-2.5 text-sm text-muted-foreground hidden md:table-cell">
                      {source.embedded_chunks || '—'}
                    </td>
                    <td className="p-2.5 text-sm text-muted-foreground hidden md:table-cell">
                      {source.insights_count || '—'}
                    </td>
                    <td className="p-2.5">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Eye className="w-3 h-3" />
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Main Component ---

export function ProcessingStatus() {
  const { groups, stats, isLoading, refetch } = useProcessingStatus()

  if (isLoading) {
    return <ProcessingStatusSkeleton />
  }

  return (
    <div className="space-y-6">
      <StatusSummary stats={stats} />
      <InProgressQueue sources={groups.inProgress} />
      <FailedQueue sources={groups.failed} onRefetch={refetch} />
      <PendingQueue sources={groups.pending} />
      <CompletedTable sources={groups.completed} />
    </div>
  )
}

function ProcessingStatusSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="flex items-center gap-3 p-4">
              <Skeleton className="h-9 w-9 rounded-lg" />
              <div>
                <Skeleton className="h-7 w-10 mb-1" />
                <Skeleton className="h-4 w-16" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
