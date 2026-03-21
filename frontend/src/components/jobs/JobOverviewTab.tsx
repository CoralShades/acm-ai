'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ClipboardList, Building2, Percent, Gauge, ArrowRight, RefreshCw, FileText, MapPin, Calendar, User, AlertTriangle, CheckCircle2, Wrench } from 'lucide-react'
import { acmApi } from '@/lib/api/acm'
import type { SourceIntelligence } from '@/lib/types/intelligence'

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
  validationSummary?: { buildings: { building_id: string; error_count: number }[] } | null
  onBulkFix?: () => void
  isBulkFixing?: boolean
  onNavigateToRecords?: () => void
}

export function JobOverviewTab({
  sourceId,
  recordCount,
  buildingCount,
  reviewStatus,
  missingFieldsPercent,
  extractionQualityScore,
  onReExtract,
  validationSummary,
  onBulkFix,
  isBulkFixing,
  onNavigateToRecords,
}: JobOverviewTabProps) {
  const statusLabel = reviewStatus ? (STATUS_LABELS[reviewStatus] ?? reviewStatus) : 'Published'
  const totalErrors = validationSummary?.buildings?.reduce((sum, b) => sum + b.error_count, 0) ?? 0
  const errorBuildingCount = validationSummary?.buildings?.filter(b => b.error_count > 0).length ?? 0

  const { data: intelligence } = useQuery<SourceIntelligence | null>({
    queryKey: ['source-intelligence', sourceId],
    queryFn: () => acmApi.getIntelligence(sourceId),
    enabled: !!sourceId,
    staleTime: 60_000,
    retry: 1,
  })

  const docMeta = intelligence?.document_meta
  const buildingInventory = intelligence?.building_inventory

  return (
    <div className="max-w-4xl space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="rounded-xl shadow-sm">
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

        <Card className="rounded-xl shadow-sm">
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

        <Card className="rounded-xl shadow-sm">
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

        <Card className="rounded-xl shadow-sm">
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

      {/* Validation Summary */}
      {totalErrors > 0 && (
        <Card className="rounded-xl shadow-sm border-red-200 dark:border-red-900/50">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Validation Issues
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">{totalErrors}</p>
                <p className="text-xs text-muted-foreground">total errors across {errorBuildingCount} buildings</p>
              </div>
              <div className="flex gap-2 ml-auto">
                {onBulkFix && (
                  <Button size="sm" variant="outline" onClick={onBulkFix} disabled={isBulkFixing}>
                    <Wrench className="h-3.5 w-3.5 mr-1.5" />
                    Fix All
                  </Button>
                )}
                {onNavigateToRecords && (
                  <Button size="sm" variant="outline" onClick={onNavigateToRecords}>
                    View Errors
                    <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {totalErrors === 0 && recordCount > 0 && (
        <Card className="rounded-xl shadow-sm border-green-200 dark:border-green-900/50">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Validation Passed
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <p className="text-sm text-muted-foreground">All {recordCount} records pass validation.</p>
          </CardContent>
        </Card>
      )}

      {/* Document Metadata (from intelligence API) */}
      {docMeta && (docMeta.consultant_name || docMeta.site_name || docMeta.site_address || docMeta.report_date || intelligence?.document_type) && (
        <Card className="rounded-xl shadow-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-sm font-semibold">Document Metadata</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {docMeta.consultant_name && (
                <div className="flex items-start gap-2">
                  <User className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Consultant</p>
                    <p className="text-sm font-medium">{docMeta.consultant_name}</p>
                  </div>
                </div>
              )}
              {(docMeta.site_name || docMeta.site_address) && (
                <div className="flex items-start gap-2">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Site / Address</p>
                    <p className="text-sm font-medium">
                      {[docMeta.site_name, docMeta.site_address].filter(Boolean).join(' — ')}
                    </p>
                  </div>
                </div>
              )}
              {docMeta.report_date && (
                <div className="flex items-start gap-2">
                  <Calendar className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Inspection / Report Date</p>
                    <p className="text-sm font-medium">{docMeta.report_date}</p>
                  </div>
                </div>
              )}
              {intelligence?.document_type && (
                <div className="flex items-start gap-2">
                  <FileText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Document Type</p>
                    <p className="text-sm font-medium">{intelligence.document_type}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Building Inventory */}
            {(buildingInventory?.buildings?.length ?? 0) > 0 && (
              <div className="mt-4 border-t pt-3">
                <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Building Inventory ({buildingInventory?.total_buildings ?? 0})
                </p>
                <div className="space-y-1.5">
                  {(buildingInventory?.buildings ?? []).map((b) => (
                    <div
                      key={b.building_id}
                      className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-1.5 text-sm"
                    >
                      <span className="font-medium">{b.name ?? b.building_id}</span>
                      <span className="text-xs text-muted-foreground">
                        pp. {b.page_start}
                        {b.page_end != null && b.page_end !== b.page_start
                          ? `–${b.page_end}`
                          : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
