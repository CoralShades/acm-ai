'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Edit2 } from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'

interface ACMRecordDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  record: ACMRecord | null
  onEdit: (record: ACMRecord) => void
}

function DetailField({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  const displayValue = value === null || value === undefined || value === ''
    ? '—'
    : typeof value === 'boolean'
    ? value ? 'Yes' : 'No'
    : String(value)

  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</dt>
      <dd className="text-sm">{displayValue}</dd>
    </div>
  )
}

function RiskBadge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-sm text-muted-foreground">—</span>

  const variants: Record<string, string> = {
    High: 'bg-risk-high-bg text-risk-high-foreground',
    Medium: 'bg-risk-medium-bg text-risk-medium-foreground',
    Low: 'bg-risk-low-bg text-risk-low-foreground',
    Presumed: 'bg-risk-presumed-bg text-risk-presumed-foreground',
  }

  return (
    <Badge variant="secondary" className={variants[value] || ''}>
      {value}
    </Badge>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-sm font-semibold text-foreground">{children}</h3>
}

export function ACMRecordDetailDialog({
  open,
  onOpenChange,
  record,
  onEdit,
}: ACMRecordDetailDialogProps) {
  if (!record) return null

  const handleEdit = () => {
    onOpenChange(false)
    onEdit(record)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px] max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>ACM Record Details</DialogTitle>
          <DialogDescription>
            {record.product} — {record.material_description}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6">
            {/* Building */}
            <div className="space-y-3">
              <SectionTitle>Building</SectionTitle>
              <dl className="grid grid-cols-3 gap-4">
                <DetailField label="Building ID" value={record.building_id} />
                <DetailField label="Building Name" value={record.building_name} />
                <DetailField label="Year Built" value={record.building_year} />
              </dl>
            </div>

            <Separator />

            {/* Location */}
            <div className="space-y-3">
              <SectionTitle>Location</SectionTitle>
              <dl className="grid grid-cols-3 gap-4">
                <DetailField label="Room ID" value={record.room_id} />
                <DetailField label="Room Name" value={record.room_name} />
                <DetailField label="Room Area" value={record.room_area ? `${record.room_area} m²` : null} />
                <DetailField label="Internal/External" value={record.area_type} />
                <DetailField label="Location" value={record.location} />
                <DetailField label="Extent" value={record.extent} />
                <DetailField label="Floor Level" value={record.floor_level} />
              </dl>
            </div>

            <Separator />

            {/* ACM Details */}
            <div className="space-y-3">
              <SectionTitle>ACM Details</SectionTitle>
              <dl className="grid grid-cols-3 gap-4">
                <DetailField label="ACM Name" value={record.product} />
                <div className="col-span-2">
                  <DetailField label="Material Description" value={record.material_description} />
                </div>
                <DetailField label="ACM Product Group" value={record.acm_product_group} />
                <DetailField label="ACM Product Type" value={record.acm_product_type} />
                <DetailField label="Result" value={record.result} />
                <DetailField label="Sample Result" value={record.sample_result} />
                <DetailField label="Sample No." value={record.sample_no} />
              </dl>
            </div>

            <Separator />

            {/* Assessment */}
            <div className="space-y-3">
              <SectionTitle>Assessment</SectionTitle>
              <dl className="grid grid-cols-3 gap-4">
                <DetailField label="Friability" value={record.friable} />
                <DetailField label="Material Condition" value={record.material_condition} />
                <DetailField label="Disturbance Potential" value={record.disturbance_potential} />
                <div className="space-y-1">
                  <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Risk Status</dt>
                  <dd><RiskBadge value={record.risk_status} /></dd>
                </div>
              </dl>
            </div>

            <Separator />

            {/* Recommendations */}
            {record.hygienist_recommendations && (
              <>
                <div className="space-y-3">
                  <SectionTitle>Recommendations</SectionTitle>
                  <p className="text-sm whitespace-pre-wrap">{record.hygienist_recommendations}</p>
                </div>
                <Separator />
              </>
            )}

            {/* Metadata */}
            <div className="space-y-3">
              <SectionTitle>Metadata</SectionTitle>
              <dl className="grid grid-cols-3 gap-4">
                <DetailField label="Page Number" value={record.page_number} />
                <DetailField label="Extraction Confidence" value={record.extraction_confidence} />
                <DetailField label="ACM Labelled" value={record.acm_labelled} />
                {record.data_issues && record.data_issues.length > 0 && (
                  <div className="col-span-3 space-y-1">
                    <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Data Issues</dt>
                    <dd className="text-sm text-amber-600 dark:text-amber-400">
                      {record.data_issues.join('; ')}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={handleEdit}>
            <Edit2 className="mr-2 h-4 w-4" />
            Edit Record
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
