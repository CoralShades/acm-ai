'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ClipboardList, Building2, Percent, Gauge, ArrowRight, RefreshCw } from 'lucide-react'

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
  missingFieldsPercent?: number | null
  extractionQualityScore?: number | null
  onReExtract?: () => void
}

export function JobOverviewTab({
  sourceId,
  recordCount,
  buildingCount,
  reviewStatus,
  missingFieldsPercent,
  extractionQualityScore,
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
              <Percent className="h-3.5 w-3.5" />
              Missing Fields %
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-sm font-semibold">
              {typeof missingFieldsPercent === 'number'
                ? `${missingFieldsPercent.toFixed(1)}%`
                : 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Gauge className="h-3.5 w-3.5" />
              Extraction Quality
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-sm font-semibold">
              {typeof extractionQualityScore === 'number'
                ? `${extractionQualityScore.toFixed(0)}/100`
                : statusLabel}
            </p>
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
