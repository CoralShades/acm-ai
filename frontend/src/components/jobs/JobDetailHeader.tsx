import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, RefreshCw, FileSpreadsheet, Download, Pencil, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
  onRename: (newTitle: string) => Promise<void>
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
  onRename,
  onReExtract,
  onExportCsv,
  onExportExcel,
}: JobDetailHeaderProps) {
  const displayTitle = title || 'Untitled Job'
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [draftTitle, setDraftTitle] = useState(displayTitle)
  const [isSavingTitle, setIsSavingTitle] = useState(false)

  useEffect(() => {
    setDraftTitle(displayTitle)
  }, [displayTitle])

  const handleSaveTitle = async () => {
    const trimmed = draftTitle.trim()
    if (!trimmed || trimmed === displayTitle) {
      setIsEditingTitle(false)
      setDraftTitle(displayTitle)
      return
    }

    setIsSavingTitle(true)
    try {
      await onRename(trimmed)
      setIsEditingTitle(false)
    } finally {
      setIsSavingTitle(false)
    }
  }

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
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
        {isEditingTitle ? (
          <div className="flex items-center gap-2">
            <Input
              value={draftTitle}
              onChange={(e) => setDraftTitle(e.target.value)}
              className="h-8 w-72"
              disabled={isSavingTitle}
              aria-label="Edit job title"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveTitle}
              disabled={isSavingTitle}
            >
              <Check className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsEditingTitle(false)
                setDraftTitle(displayTitle)
              }}
              disabled={isSavingTitle}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold leading-tight">{displayTitle}</h1>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2"
              onClick={() => setIsEditingTitle(true)}
              aria-label="Edit job title"
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
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
