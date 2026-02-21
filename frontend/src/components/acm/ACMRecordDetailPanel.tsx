'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { RecordFieldSection } from './RecordFieldSection'
import type { SectionField } from './RecordFieldSection'
import { useACMRecordDetail } from '@/lib/hooks/use-acm-record'
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
import type { ACMRecord, ACMRecordUpdateRequest } from '@/lib/types/acm'
import { cn } from '@/lib/utils'

interface ACMRecordDetailPanelProps {
  recordId: string | null
  open: boolean
  sourceId: string
  onClose: () => void
  onViewInPDF: (pageNumber: number) => void
  onNavigatePrev: () => void
  onNavigateNext: () => void
  hasPrev: boolean
  hasNext: boolean
}

function buildSections(record: ACMRecord): Array<{ title: string; fields: SectionField[] }> {
  return [
    {
      title: 'Organisation',
      fields: [
        { label: 'School Name', value: record.school_name },
        { label: 'School Code', value: record.school_code },
      ],
    },
    {
      title: 'Building',
      fields: [
        { label: 'Building ID', value: record.building_id },
        { label: 'Building Name', value: record.building_name },
        { label: 'Year Built', value: record.building_year },
        { label: 'Construction', value: record.building_construction },
      ],
    },
    {
      title: 'Location',
      fields: [
        { label: 'Area Type', value: record.area_type },
        { label: 'Floor Level', value: record.floor_level },
        { label: 'Room ID', value: record.room_id },
        { label: 'Room Name', value: record.room_name },
        { label: 'Room Area', value: record.room_area ? `${record.room_area} m²` : null },
        { label: 'Location', value: record.location },
      ],
    },
    {
      title: 'ACM Details',
      fields: [
        { label: 'Product', value: record.product },
        { label: 'Material Description', value: record.material_description },
        { label: 'Friable', value: record.friable, type: 'boolean' },
        { label: 'Product Group', value: record.acm_product_group },
        { label: 'Product Type', value: record.acm_product_type },
        { label: 'Sample No.', value: record.sample_no },
        { label: 'Sample Result', value: record.sample_result },
        { label: 'Quantity', value: record.quantity },
      ],
    },
    {
      title: 'Assessment',
      fields: [
        { label: 'Material Condition', value: record.material_condition },
        { label: 'Disturbance Potential', value: record.disturbance_potential },
        { label: 'Extent', value: record.extent },
        { label: 'Risk Status', value: record.risk_status, type: 'risk' },
        { label: 'Result', value: record.result },
        { label: 'Identifying Company', value: record.identifying_company },
      ],
    },
    {
      title: 'Documentation',
      fields: [
        { label: 'ACM Labelled', value: record.acm_labelled, type: 'boolean' },
        { label: 'Label Details', value: record.acm_label_details },
        { label: 'Hygienist Recommendations', value: record.hygienist_recommendations },
        { label: 'Normalized Action', value: record.normalized_action },
        { label: 'Classification Method', value: record.classification_method },
      ],
    },
    {
      title: 'Metadata',
      fields: [
        { label: 'Page Number', value: record.page_number },
        { label: 'Extraction Confidence', value: record.extraction_confidence, type: 'confidence' },
        { label: 'Classification Confidence', value: record.classification_confidence, type: 'confidence' },
        { label: 'Created', value: record.created },
        { label: 'Updated', value: record.updated },
      ],
    },
  ]
}

interface EditableFieldsProps {
  record: ACMRecord
  editData: ACMRecordUpdateRequest
  onChange: (updates: Partial<ACMRecordUpdateRequest>) => void
}

function EditableFields({ record, editData, onChange }: EditableFieldsProps) {
  const val = <K extends keyof ACMRecordUpdateRequest>(
    key: K,
    fallback: ACMRecord[keyof ACMRecord]
  ): string => String(editData[key] ?? fallback ?? '')

  return (
    <div className="space-y-6">
      {/* Organisation */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Organisation</h3>
        <Separator />
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">School Name</Label>
            <Input
              value={val('school_name', record.school_name)}
              onChange={(e) => onChange({ school_name: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">School Code</Label>
            <Input
              value={val('school_code', record.school_code)}
              onChange={(e) => onChange({ school_code: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Building */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Building</h3>
        <Separator />
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Building ID</Label>
            <Input
              value={val('building_id', record.building_id)}
              onChange={(e) => onChange({ building_id: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Building Name</Label>
            <Input
              value={val('building_name', record.building_name)}
              onChange={(e) => onChange({ building_name: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Year Built</Label>
            <Input
              type="number"
              value={editData.building_year ?? record.building_year ?? ''}
              onChange={(e) => onChange({ building_year: e.target.value ? Number(e.target.value) : undefined })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Construction</Label>
            <Input
              value={val('building_construction', record.building_construction)}
              onChange={(e) => onChange({ building_construction: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Location */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Location</h3>
        <Separator />
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Area Type</Label>
            <Select
              value={editData.area_type ?? record.area_type ?? ''}
              onValueChange={(v) => onChange({ area_type: v })}
            >
              <SelectTrigger className="h-7 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Interior">Interior</SelectItem>
                <SelectItem value="Exterior">Exterior</SelectItem>
                <SelectItem value="Grounds">Grounds</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Room ID</Label>
            <Input
              value={val('room_id', record.room_id)}
              onChange={(e) => onChange({ room_id: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Room Name</Label>
            <Input
              value={val('room_name', record.room_name)}
              onChange={(e) => onChange({ room_name: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Room Area (m²)</Label>
            <Input
              type="number"
              value={editData.room_area ?? record.room_area ?? ''}
              onChange={(e) => onChange({ room_area: e.target.value ? Number(e.target.value) : undefined })}
              className="h-7 text-sm"
            />
          </div>
          <div className="col-span-2 space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Location</Label>
            <Input
              value={val('location', record.location)}
              onChange={(e) => onChange({ location: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
        </div>
      </div>

      {/* ACM Details */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">ACM Details</h3>
        <Separator />
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Product</Label>
            <Input
              value={val('product', record.product)}
              onChange={(e) => onChange({ product: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="col-span-2 space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Material Description</Label>
            <Input
              value={val('material_description', record.material_description)}
              onChange={(e) => onChange({ material_description: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Friable</Label>
            <Select
              value={editData.friable ?? record.friable ?? ''}
              onValueChange={(v) => onChange({ friable: v })}
            >
              <SelectTrigger className="h-7 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Friable">Friable</SelectItem>
                <SelectItem value="Non-friable">Non-friable</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Result</Label>
            <Input
              value={val('result', record.result)}
              onChange={(e) => onChange({ result: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Extent</Label>
            <Input
              value={val('extent', record.extent)}
              onChange={(e) => onChange({ extent: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Page Number</Label>
            <Input
              type="number"
              value={editData.page_number ?? record.page_number ?? ''}
              onChange={(e) => onChange({ page_number: e.target.value ? Number(e.target.value) : undefined })}
              className="h-7 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Assessment */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Assessment</h3>
        <Separator />
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Material Condition</Label>
            <Input
              value={val('material_condition', record.material_condition)}
              onChange={(e) => onChange({ material_condition: e.target.value })}
              className="h-7 text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-[11px] uppercase tracking-wide">Risk Status</Label>
            <Select
              value={editData.risk_status ?? record.risk_status ?? ''}
              onValueChange={(v) => onChange({ risk_status: v })}
            >
              <SelectTrigger className="h-7 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Low">Low</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="High">High</SelectItem>
                <SelectItem value="Presumed">Presumed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  )
}

export function ACMRecordDetailPanel({
  recordId,
  open,
  sourceId,
  onClose,
  onViewInPDF,
  onNavigatePrev,
  onNavigateNext,
  hasPrev,
  hasNext,
}: ACMRecordDetailPanelProps) {
  const { record, isLoading, isEditing, isSaving, setIsEditing, saveRecord } =
    useACMRecordDetail(recordId)
  const [editData, setEditData] = useState<ACMRecordUpdateRequest>({})

  // Reset edit state when record changes
  useEffect(() => {
    setEditData({})
    setIsEditing(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordId])

  // Keyboard shortcuts: Escape, ArrowLeft, ArrowRight
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept keys when focus is in an input/select
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') {
          if (isEditing) setIsEditing(false)
        }
        return
      }
      if (e.key === 'Escape') {
        if (isEditing) {
          setIsEditing(false)
        } else {
          onClose()
        }
      }
      if (e.key === 'ArrowLeft' && !isEditing) {
        onNavigatePrev()
      }
      if (e.key === 'ArrowRight' && !isEditing) {
        onNavigateNext()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, isEditing, onClose, setIsEditing, onNavigatePrev, onNavigateNext])

  const handleEditChange = useCallback((updates: Partial<ACMRecordUpdateRequest>) => {
    setEditData((prev) => ({ ...prev, ...updates }))
  }, [])

  const handleSave = useCallback(async () => {
    if (!record) return
    try {
      await saveRecord(editData, sourceId)
    } catch {
      // Toast shown by mutation's onError handler in useUpdateACMRecord
    }
  }, [record, editData, saveRecord, sourceId])

  const handleCancelEdit = useCallback(() => {
    setEditData({})
    setIsEditing(false)
  }, [setIsEditing])

  const sections = record ? buildSections(record) : []

  return (
    <div
      className={cn(
        'fixed right-0 top-0 bottom-0 z-40 w-[380px]',
        'bg-background border-l shadow-xl',
        'flex flex-col',
        'transition-transform duration-200 ease-in-out',
        open ? 'translate-x-0' : 'translate-x-full'
      )}
      aria-label="ACM Record Detail Panel"
      role="complementary"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b shrink-0">
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onNavigatePrev}
            disabled={!hasPrev || isEditing}
            title="Previous record (←)"
            aria-label="Previous record"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onNavigateNext}
            disabled={!hasNext || isEditing}
            title="Next record (→)"
            aria-label="Next record"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <span className="text-sm font-semibold truncate flex-1 min-w-0">
          {record?.product || 'ACM Record'}
        </span>

        <div className="flex items-center gap-0.5 shrink-0">
          {record?.page_number != null && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onViewInPDF(record.page_number!)}
              title={`View in PDF (page ${record.page_number})`}
              aria-label="View in PDF"
            >
              <FileText className="h-4 w-4" />
            </Button>
          )}
          {!isEditing && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setIsEditing(true)}
              title="Edit record"
              aria-label="Edit record"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onClose}
            title="Close panel (Esc)"
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Edit mode action bar */}
      {isEditing && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 border-b shrink-0">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={isSaving}
            className="h-7"
          >
            {isSaving ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <Save className="mr-1 h-3 w-3" />
            )}
            Save
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancelEdit}
            disabled={isSaving}
            className="h-7"
          >
            <XCircle className="mr-1 h-3 w-3" />
            Cancel
          </Button>
          <span className="text-xs text-muted-foreground">Esc to cancel</span>
        </div>
      )}

      {/* Body */}
      <ScrollArea className="flex-1">
        <div className="px-4 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !record ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              No record selected
            </div>
          ) : isEditing ? (
            <EditableFields
              record={record}
              editData={editData}
              onChange={handleEditChange}
            />
          ) : (
            <div className="space-y-6">
              {sections
                .filter((s) => s.fields.length > 0)
                .map((section) => (
                  <RecordFieldSection
                    key={section.title}
                    title={section.title}
                    fields={section.fields}
                  />
                ))}
              {record.data_issues && record.data_issues.length > 0 && (
                <div className="space-y-1 p-2 rounded-md bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800">
                  <p className="text-xs font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wide">
                    Data Issues
                  </p>
                  <ul className="text-xs text-amber-600 dark:text-amber-400 space-y-0.5">
                    {record.data_issues.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
