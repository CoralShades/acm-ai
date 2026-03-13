'use client'

import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  MoreVertical,
  Eye,
  RefreshCw,
  Trash2,
  Download,
  ClipboardList,
  FileSpreadsheet,
  Loader2,
} from 'lucide-react'
import { toast } from 'sonner'
import { JobStatusPill } from './JobStatusPill'
import { sourcesApi } from '@/lib/api/sources'
import type { SourceListResponse } from '@/lib/types/api'
import { useExtractionStatus } from '@/lib/hooks/use-extraction-status'

interface JobCardProps {
  source: SourceListResponse
  onRefetch: () => void
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 30) {
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }
  if (diffDays > 0) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  if (diffHours > 0) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
  if (diffMinutes > 0) return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`
  return 'just now'
}

export function JobCard({ source, onRefetch }: JobCardProps) {
  const router = useRouter()
  const isPublished = !source.review_status || source.review_status === 'published'
  const extractionStatus = useExtractionStatus(
    source.id,
    source.review_status === 'extracting' ? source.command_id : undefined
  )
  const isExtracting =
    source.review_status === 'extracting' || extractionStatus.phase === 'extracting'
  const stageIndex = extractionStatus.currentStageIndex ?? 1
  const totalStages = extractionStatus.totalStages
  const stageLabel = extractionStatus.currentStageLabel ?? 'Initializing'
  const progressValue = extractionStatus.progressPercent ?? 0

  const handleDownload = async () => {
    try {
      const response = await sourcesApi.downloadFile(source.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = window.document.createElement('a')
      a.href = url
      a.download = source.title || 'document'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download file')
    }
  }

  const handleReExtract = async () => {
    try {
      await sourcesApi.retry(source.id)
      toast.success('Re-extraction started')
      onRefetch()
    } catch {
      toast.error('Failed to start re-extraction')
    }
  }

  const handleDelete = async () => {
    try {
      await sourcesApi.delete(source.id)
      toast.success('Job deleted')
      onRefetch()
    } catch {
      toast.error('Failed to delete job')
    }
  }

  const primaryHref = isPublished
    ? `/jobs/${source.id}`
    : isExtracting
      ? `/jobs/${source.id}/extract`
      : `/jobs/${source.id}/review/buildings`

  // Extract bare ID for URL (strip 'source:' prefix if present)
  const rawId = source.id.replace(/^source:/, '')
  const exportCsvHref = `/api/acm/export/csv?source_id=${rawId}`
  const exportXlsxHref = `/api/acm/export/excel?source_id=${rawId}`

  return (
    <Card className="relative transition-shadow hover:shadow-md flex flex-col gap-0 py-0">
      <CardHeader className="px-4 pt-4 pb-3">
        <div className="flex items-start justify-between gap-2">
          {/* Icon + title */}
          <div className="flex items-center gap-2 min-w-0">
            <ClipboardList className="w-5 h-5 text-muted-foreground flex-shrink-0" />
            <h3 className="font-medium line-clamp-2 leading-snug text-sm">
              {source.title || 'Untitled Job'}
            </h3>
          </div>

          {/* Three-dot menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 flex-shrink-0"
                aria-label="Job actions"
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => router.push(`/jobs/${source.id}`)}>
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </DropdownMenuItem>
              {source.asset?.file_path && (
                <DropdownMenuItem onClick={handleDownload}>
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={handleReExtract}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Re-extract
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-3 space-y-2">
        {/* Status pill */}
        <JobStatusPill review_status={source.review_status} />

        {isExtracting && (
          <div className="rounded-lg border border-[color:var(--vaea-teal-300)]/50 bg-[color:var(--vaea-teal-100)]/20 p-2 dark:bg-[color:var(--vaea-teal-900)]/20">
            <div className="flex items-center gap-1.5 text-xs font-medium text-[color:var(--vaea-teal-900)] dark:text-[color:var(--vaea-teal-100)]">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>
                Extracting... Stage {stageIndex}/{totalStages} ({stageLabel})
              </span>
            </div>
            <div
              className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--vaea-teal-100)] dark:bg-[color:var(--vaea-teal-900)]/50"
              role="progressbar"
              aria-label="Extraction progress"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progressValue}
            >
              <div
                className="h-full bg-[color:var(--vaea-teal-500)] transition-all duration-500"
                style={{ width: `${progressValue}%` }}
              />
            </div>
          </div>
        )}

        {/* Uploaded date */}
        <p className="text-xs text-muted-foreground">
          Uploaded {formatRelativeDate(source.created)}
        </p>

        {/* Building and record counts */}
        {(typeof source.building_count === 'number' && source.building_count > 0 || source.insights_count > 0) && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {typeof source.building_count === 'number' && source.building_count > 0 && (
              <span>{source.building_count} building{source.building_count !== 1 ? 's' : ''}</span>
            )}
            {typeof source.building_count === 'number' && source.building_count > 0 && source.insights_count > 0 && (
              <span className="text-border">|</span>
            )}
            {source.insights_count > 0 && (
              <span>{source.insights_count} record{source.insights_count !== 1 ? 's' : ''}</span>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="px-4 pb-4 pt-0 flex flex-col gap-2 items-stretch">
        {/* Primary CTA */}
        <Button
          size="sm"
          variant={isPublished ? 'outline' : 'default'}
          className="w-full"
          asChild
        >
          <Link href={primaryHref}>
            {isPublished ? (
              <>
                <Eye className="w-3.5 h-3.5 mr-1.5" />
                View
              </>
            ) : (
              isExtracting ? 'View Extraction' : 'Review'
            )}
          </Link>
        </Button>

        {/* Export actions for published jobs */}
        {isPublished && source.insights_count > 0 && (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-xs h-7"
              asChild
            >
              <a href={exportCsvHref} target="_blank" rel="noopener noreferrer">
                <FileSpreadsheet className="w-3 h-3 mr-1" />
                CSV
              </a>
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-xs h-7"
              asChild
            >
              <a href={exportXlsxHref} target="_blank" rel="noopener noreferrer">
                <FileSpreadsheet className="w-3 h-3 mr-1" />
                Excel
              </a>
            </Button>
          </div>
        )}
      </CardFooter>
    </Card>
  )
}
