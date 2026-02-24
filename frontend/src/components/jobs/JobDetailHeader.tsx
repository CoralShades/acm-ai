import Link from 'next/link'
import { ChevronRight, RefreshCw, FileSpreadsheet, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { JobStatusPill } from './JobStatusPill'

function formatRelativeDate(dateStr: string | null): string {
  if (!dateStr) return 'Unknown'
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

interface JobDetailHeaderProps {
  sourceId: string
  title: string | null
  reviewStatus: string | undefined
  createdAt: string | null
  recordCount?: number
  buildingCount?: number
  onReExtract: () => void
  onExportCsv: () => void
  onExportExcel: () => void
}

export function JobDetailHeader({
  title,
  reviewStatus,
  createdAt,
  recordCount,
  buildingCount,
  onReExtract,
  onExportCsv,
  onExportExcel,
}: JobDetailHeaderProps) {
  const displayTitle = title || 'Untitled Job'

  return (
    <div className="border-b bg-background px-4 py-4 flex-shrink-0">
      {/* Breadcrumb row */}
      <div className="flex items-center justify-between gap-4">
        <nav aria-label="Breadcrumb">
          <ol className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <li>
              <Link href="/jobs" className="hover:text-foreground transition-colors">
                Jobs
              </Link>
            </li>
            <li aria-hidden="true">
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
            </li>
            <li>
              <span className="text-foreground font-medium truncate max-w-[300px] inline-block">
                {displayTitle}
              </span>
            </li>
          </ol>
        </nav>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button variant="outline" size="sm" onClick={onReExtract}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Re-Extract
          </Button>
          <Button variant="outline" size="sm" onClick={onExportCsv}>
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={onExportExcel}>
            <FileSpreadsheet className="h-3.5 w-3.5 mr-1.5" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Title + meta row */}
      <div className="mt-3 flex items-center flex-wrap gap-x-3 gap-y-1.5">
        <h1 className="text-xl font-bold leading-tight">{displayTitle}</h1>
        <JobStatusPill review_status={reviewStatus} />
        {createdAt && (
          <span className="text-sm text-muted-foreground">
            Uploaded: {formatRelativeDate(createdAt)}
          </span>
        )}
        {recordCount !== undefined && (
          <span className="text-sm text-muted-foreground">
            {recordCount} record{recordCount !== 1 ? 's' : ''}
          </span>
        )}
        {buildingCount !== undefined && (
          <span className="text-sm text-muted-foreground">
            {buildingCount} building{buildingCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  )
}
