'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ClipboardList, Building2, Activity, Calendar, ArrowRight, RefreshCw } from 'lucide-react'

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

const STATUS_LABELS: Record<string, string> = {
  extracting: 'Extracting',
  pending_review: 'Pending Review',
  building_review: 'Review: Buildings',
  acm_review: 'Review: Records',
  published: 'Published',
}

interface JobOverviewTabProps {
  sourceId: string
  recordCount: number
  buildingCount: number
  reviewStatus: string | undefined
  createdAt: string | null
  onReExtract?: () => void
}

export function JobOverviewTab({
  sourceId,
  recordCount,
  buildingCount,
  reviewStatus,
  createdAt,
  onReExtract,
}: JobOverviewTabProps) {
  const statusLabel = reviewStatus ? (STATUS_LABELS[reviewStatus] ?? reviewStatus) : 'Published'

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <ClipboardList className="h-3.5 w-3.5" />
              Total Records
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-2xl font-bold">{recordCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5" />
              Buildings
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-2xl font-bold">{buildingCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5" />
              Status
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-sm font-semibold">{statusLabel}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              Uploaded
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-sm font-semibold">{formatRelativeDate(createdAt)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Quick Actions
        </h2>
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <Button variant="outline" asChild>
            <Link href={`/jobs/${sourceId}/review/buildings`}>
              Re-Review Buildings
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href={`/jobs/${sourceId}/review/records`}>
              Re-Review Records
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          {onReExtract && (
            <Button variant="outline" onClick={onReExtract}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Re-Extract
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
