'use client'

import { useState, useEffect, useCallback } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  X,
  ChevronLeft,
  ChevronRight,
  Edit2,
  FileText,
  Save,
  XCircle,
  Loader2,
} from 'lucide-react'
import { useUpdateACMRecord } from '@/lib/hooks/use-acm'
import type { ACMRecord, ACMRecordUpdateRequest } from '@/lib/types/acm'
import { cn } from '@/lib/utils'

interface ACMRecordDetailPanelProps {
  record: ACMRecord
  sourceId: string
  hasPrev: boolean
  hasNext: boolean
  onPrev: () => void
  onNext: () => void
  onClose: () => void
  onViewInPdf?: (pageNumber: number) => void
  /** Called after a successful save so parent can update its record state */
  onRecordUpdated?: (record: ACMRecord) => void
}

// ---- Small display helpers ----

function RiskBadge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-xs text-muted-foreground">—</span>
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

function BoolBadge({ value }: { value: boolean | null | undefined }) {
  if (value === null || value === undefined)
    return <span className="text-xs text-muted-foreground">—</span>
  return (
    <Badge variant={value ? 'default' : 'secondary'}>{value ? 'YES' : 'NO'}</Badge>
  )
}

function ConfidenceBadge({ value }: { value: number | null | undefined }) {
  if (value === null || value === undefined)
    return <span className="text-xs text-muted-foreground">—</span>
  const pct = value <= 1 ? Math.round(value * 100) : Math.round(value)
  const color =
    pct >= 80
      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : pct >= 60
      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  return (
    <Badge variant="outline" className={color}>
      {pct}%
    </Badge>
  )
}

function DisplayField({
  label,
  value,
  children,
}: {
  label: string
  value?: string | number | boolean | null
  children?: React.ReactNode
}) {
  const display =
    value === null || value === undefined || value === ''
      ? '—'
      : typeof value === 'boolean'
      ? value
        ? 'YES'
        : 'NO'
      : String(value)

  return (
    <div className="grid grid-cols-[1fr_1fr] gap-x-3 py-1">
      <dt className="text-xs text-muted-foreground truncate">{label}</dt>
      <dd className="text-xs font-medium leading-tight break-words">
        {children ?? display}
      </dd>
    </div>
  )
}

function SectionHeader({ title }: { title: string }) {
  return (
    <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
      {title}
    </h3>
  )
}

// ---- Edit field helpers ----

function EditTextField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string | undefined
  onChange: (v: string) => void
}) {
  return (
    <div className="grid grid-cols-[1fr_1fr] gap-x-3 py-1 items-center">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="h-7 text-xs px-2"
      />
    </div>
  )
}

function EditSelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string | undefined
  options: string[]
  onChange: (v: string) => void
}) {
  return (
    <div className="grid grid-cols-[1fr_1fr] gap-x-3 py-1 items-center">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Select value={value ?? ''} onValueChange={onChange}>
        <SelectTrigger className="h-7 text-xs px-2">
          <SelectValue placeholder="—" />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o} value={o} className="text-xs">
              {o}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

// ---- Main panel ----

export function ACMRecordDetailPanel({
  record,
  sourceId,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
  onClose,
  onViewInPdf,
  onRecordUpdated,
}: ACMRecordDetailPanelProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<ACMRecordUpdateRequest>({})
  const updateRecord = useUpdateACMRecord()

  // Reset edit mode when record changes
  useEffect(() => {
    setIsEditing(false)
    setFormData({})
  }, [record.id])

  // Keyboard: Escape closes, arrows navigate (skip when inside grid or when editing)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (isEditing) {
          handleCancelEdit()
        } else {
          onClose()
        }
        return
      }
      // Don't navigate when focus is in AG Grid or in an input
      const active = document.activeElement
      if (
        active instanceof HTMLInputElement ||
        active instanceof HTMLTextAreaElement ||
        active instanceof HTMLSelectElement
      ) {
        return
      }
      const inGrid = active?.closest('.ag-theme-alpine')
      if (inGrid) return
      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        onPrev()
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        onNext()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, onClose, onPrev, onNext])

  const handleStartEdit = useCallback(() => {
    setFormData({
      product: record.product ?? undefined,
      material_description: record.material_description ?? undefined,
      school_name: record.school_name ?? undefined,
      school_code: record.school_code ?? undefined,
      building_id: record.building_id ?? undefined,
      building_name: record.building_name ?? undefined,
      building_year: record.building_year ?? undefined,
      building_construction: record.building_construction ?? undefined,
      room_id: record.room_id ?? undefined,
      room_name: record.room_name ?? undefined,
      area_type: record.area_type ?? undefined,
      extent: record.extent ?? undefined,
      location: record.location ?? undefined,
      friable: record.friable ?? undefined,
      material_condition: record.material_condition ?? undefined,
      risk_status: record.risk_status ?? undefined,
      result: record.result ?? undefined,
      page_number: record.page_number ?? undefined,
    })
    setIsEditing(true)
  }, [record])

  const handleCancelEdit = useCallback(() => {
    setIsEditing(false)
    setFormData({})
  }, [])

  const handleSave = useCallback(async () => {
    try {
      const updated = await updateRecord.mutateAsync({
        recordId: record.id,
        sourceId,
        data: formData,
      })
      setIsEditing(false)
      setFormData({})
      onRecordUpdated?.(updated)
    } catch {
      // toast is handled by useUpdateACMRecord
    }
  }, [record.id, sourceId, formData, updateRecord, onRecordUpdated])

  const setField = useCallback(
    (field: keyof ACMRecordUpdateRequest, value: string | number | undefined) => {
      setFormData((prev) => ({ ...prev, [field]: value }))
    },
    []
  )

  // Render field — either as editable input or display text
  const renderField = useCallback(
    (
      label: string,
      field: keyof ACMRecordUpdateRequest,
      displayValue: string | number | boolean | null | undefined,
      options?: string[]
    ) => {
      if (!isEditing) {
        return <DisplayField key={label} label={label} value={displayValue} />
      }
      const editVal = formData[field] as string | undefined
      if (options) {
        return (
          <EditSelectField
            key={label}
            label={label}
            value={editVal}
            options={options}
            onChange={(v) => setField(field, v)}
          />
        )
      }
      return (
        <EditTextField
          key={label}
          label={label}
          value={editVal}
          onChange={(v) => setField(field, v)}
        />
      )
    },
    [isEditing, formData, setField]
  )

  return (
    <div
      className={cn(
        'fixed inset-y-0 right-0 z-40 flex flex-col',
        'w-[380px] bg-background border-l shadow-xl',
        'animate-in slide-in-from-right duration-200'
      )}
      role="complementary"
      aria-label="ACM Record Details"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div className="min-w-0 flex-1 pr-2">
          <p className="text-sm font-semibold truncate">{record.product}</p>
          <p className="text-xs text-muted-foreground truncate">
            {[record.building_name, record.room_name].filter(Boolean).join(' › ') ||
              record.building_id}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {/* Arrow navigation */}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onPrev}
            disabled={!hasPrev}
            aria-label="Previous record"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onNext}
            disabled={!hasNext}
            aria-label="Next record"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          {/* Edit toggle */}
          {!isEditing && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleStartEdit}
              aria-label="Edit record"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
          {/* Close */}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onClose}
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Edit mode action bar */}
      {isEditing && (
        <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30 shrink-0">
          <span className="text-xs text-muted-foreground flex-1">Editing record</span>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleCancelEdit}
          >
            <XCircle className="h-3.5 w-3.5" />
            Cancel
          </Button>
          <Button
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleSave}
            disabled={updateRecord.isPending}
          >
            {updateRecord.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            Save
          </Button>
        </div>
      )}

      {/* Body */}
      <ScrollArea className="flex-1 px-4 py-3">
        <div className="space-y-5">
          {/* Organisation */}
          <div>
            <SectionHeader title="Organisation" />
            <dl>
              {renderField('Site Name', 'school_name', record.school_name)}
              {renderField('Code', 'school_code', record.school_code)}
            </dl>
          </div>
          <Separator />

          {/* Building */}
          <div>
            <SectionHeader title="Building" />
            <dl>
              {renderField('Building ID', 'building_id', record.building_id)}
              {renderField('Building Name', 'building_name', record.building_name)}
              {renderField('Year Built', 'building_year', record.building_year)}
              {renderField(
                'Construction',
                'building_construction',
                record.building_construction
              )}
            </dl>
          </div>
          <Separator />

          {/* Location */}
          <div>
            <SectionHeader title="Location" />
            <dl>
              {renderField(
                'Internal/External',
                'area_type',
                record.area_type,
                ['Interior', 'Exterior', 'Grounds']
              )}
              {renderField('Room ID', 'room_id', record.room_id)}
              {renderField('Room Name', 'room_name', record.room_name)}
              {renderField('Location', 'location', record.location)}
              <DisplayField label="Floor Level" value={record.floor_level} />
            </dl>
          </div>
          <Separator />

          {/* ACM Details */}
          <div>
            <SectionHeader title="ACM Details" />
            <dl>
              {renderField('Product', 'product', record.product)}
              {renderField('Material Description', 'material_description', record.material_description)}
              {renderField(
                'Friable',
                'friable',
                record.friable,
                ['Friable', 'Non-friable']
              )}
              <DisplayField label="Product Group" value={record.acm_product_group} />
              <DisplayField label="Product Type" value={record.acm_product_type} />
              <DisplayField label="Sample No." value={record.sample_no} />
              <DisplayField label="Sample Result" value={record.sample_result} />
              <DisplayField label="Quantity" value={record.quantity} />
            </dl>
          </div>
          <Separator />

          {/* Assessment */}
          <div>
            <SectionHeader title="Assessment" />
            <dl>
              {renderField(
                'Condition',
                'material_condition',
                record.material_condition,
                ['Good', 'Fair', 'Poor', 'Very Poor']
              )}
              <DisplayField
                label="Disturbance Potential"
                value={record.disturbance_potential}
              />
              {renderField('Extent', 'extent', record.extent)}
              <DisplayField label="Risk Status">
                <RiskBadge value={record.risk_status} />
              </DisplayField>
              <DisplayField
                label="Identifying Company"
                value={record.identifying_company}
              />
            </dl>
          </div>
          <Separator />

          {/* Documentation */}
          <div>
            <SectionHeader title="Documentation" />
            <dl>
              <DisplayField label="Labelled">
                <BoolBadge value={record.acm_labelled} />
              </DisplayField>
              <DisplayField label="Label Details" value={record.acm_label_details} />
              <DisplayField
                label="Recommendations"
                value={record.hygienist_recommendations}
              />
              {record.data_issues && record.data_issues.length > 0 && (
                <DisplayField label="Data Issues" value={record.data_issues.join('; ')} />
              )}
            </dl>
          </div>
          <Separator />

          {/* Metadata */}
          <div>
            <SectionHeader title="Metadata" />
            <dl>
              <DisplayField label="Page Number" value={record.page_number} />
              <DisplayField label="Extraction Confidence">
                <ConfidenceBadge value={record.extraction_confidence} />
              </DisplayField>
              <DisplayField label="Created" value={record.created} />
              <DisplayField label="Updated" value={record.updated} />
            </dl>
          </div>
        </div>
      </ScrollArea>

      {/* Footer */}
      {record.page_number && onViewInPdf && (
        <div className="px-4 py-3 border-t shrink-0">
          <Button
            variant="outline"
            size="sm"
            className="w-full gap-2"
            onClick={() => onViewInPdf(record.page_number!)}
          >
            <FileText className="h-4 w-4" />
            View in PDF (page {record.page_number})
          </Button>
        </div>
      )}
    </div>
  )
}
