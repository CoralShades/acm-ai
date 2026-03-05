'use client'

import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useBulkEdit, useBulkValidate, useUpdateACMRecord } from '@/lib/hooks/useACMItems'
import { useV3SSE } from '@/lib/hooks/useV3SSE'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import type { ACMRecord } from '@/lib/types/acm'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import { fieldApiToRecordKey } from '@/lib/utils/acm-field-mapping'
import { CheckSquare, Undo2, Download, ShieldCheck, X } from 'lucide-react'

interface UndoSnapshot {
  field: string
  values: { id: string; oldValue: unknown }[]
}

interface BulkOperationsBarProps {
  sourceId: string
  selectedRecords: ACMRecord[]
  onClearSelection: () => void
  onValidationRefresh?: () => void
  schema: SFFieldSchemaConfig | null
}

export function BulkOperationsBar({
  sourceId,
  selectedRecords,
  onClearSelection,
  onValidationRefresh,
  schema,
}: BulkOperationsBarProps) {
  const [editField, setEditField] = useState('')
  const [editValue, setEditValue] = useState('')
  const [operationId, setOperationId] = useState('')
  const [isApplying, setIsApplying] = useState(false)
  const [progress, setProgress] = useState<{ processed: number; total: number } | null>(null)
  const [undoSnapshot, setUndoSnapshot] = useState<UndoSnapshot | null>(null)

  const bulkEdit = useBulkEdit()
  const bulkValidate = useBulkValidate()
  const updateRecord = useUpdateACMRecord()
  const { selectedBuildingIds } = useBuildingStore()
  const queryClient = useQueryClient()

  // SSE progress tracking for bulk edit
  useV3SSE({
    operationId,
    category: 'bulk',
    enabled: isApplying && !!operationId,
    onEvent: (event) => {
      if (event.type === 'bulk.progress' && event.data) {
        setProgress({
          processed: event.data.processed as number,
          total: event.data.total as number,
        })
      }
      if (event.type === 'bulk.complete') {
        setIsApplying(false)
        setProgress(null)
      }
    },
  })

  const handleApply = useCallback(async () => {
    if (!editField || !editValue || selectedRecords.length === 0) return

    // Snapshot current values for undo
    const snapshot: UndoSnapshot = {
      field: editField,
      values: selectedRecords.map((r) => ({
        id: r.id,
        oldValue: (r as unknown as Record<string, unknown>)[editField] ?? null,
      })),
    }
    setUndoSnapshot(snapshot)

    const opId = crypto.randomUUID()
    setOperationId(opId)
    setIsApplying(true)
    setProgress({ processed: 0, total: selectedRecords.length })

    try {
      await bulkEdit.mutateAsync({
        sourceId,
        body: {
          record_ids: selectedRecords.map((r) => r.id),
          field: editField,
          value: editValue,
          operation_id: opId,
        },
      })
      // Do NOT clear isApplying here — wait for bulk.complete SSE event
    } catch {
      // Only clear state on actual error (SSE won't fire on HTTP failure)
      setIsApplying(false)
      setProgress(null)
    }
  }, [editField, editValue, selectedRecords, sourceId, bulkEdit])

  const handleValidate = useCallback(async () => {
    await bulkValidate.mutateAsync({
      record_ids: selectedRecords.map((r) => r.id),
    })
    onValidationRefresh?.()
    onClearSelection()
  }, [selectedRecords, bulkValidate, onValidationRefresh, onClearSelection])

  const handleExportSelected = useCallback(() => {
    if (selectedBuildingIds.size === 0) return
    const params = new URLSearchParams({ source_id: sourceId })
    selectedBuildingIds.forEach((id) => params.append('building_ids', id))
    window.location.href = `/api/acm/export/csv?${params.toString()}`
  }, [selectedBuildingIds, sourceId])

  const handleUndo = useCallback(async () => {
    if (!undoSnapshot) return
    for (const { id, oldValue } of undoSnapshot.values) {
      await updateRecord.mutateAsync({
        recordId: id,
        data: { [undoSnapshot.field]: oldValue } as Parameters<typeof updateRecord.mutate>[0]['data'],
      })
    }
    queryClient.invalidateQueries({ queryKey: ['acm', 'items'] })
    setUndoSnapshot(null)
  }, [undoSnapshot, updateRecord, queryClient])

  // Build field options from schema
  const fieldOptions =
    schema?.item_fields.fields.map((f) => ({
      value: fieldApiToRecordKey(f.api_name),
      label: f.label,
    })) ?? []

  const count = selectedRecords.length
  const canApply = !!editField && !!editValue && !isApplying && count > 0
  const progressPct = progress
    ? Math.round((progress.processed / Math.max(progress.total, 1)) * 100)
    : 0

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-primary/5 border-b border-primary/20 shrink-0 flex-wrap">
      {/* Selection count */}
      <div className="flex items-center gap-1.5 text-sm font-medium">
        <CheckSquare className="h-4 w-4 text-primary" />
        <span>
          {count} record{count !== 1 ? 's' : ''} selected
        </span>
        <button
          type="button"
          onClick={onClearSelection}
          className="ml-1 rounded p-0.5 hover:bg-muted transition-colors"
          aria-label="Clear selection"
        >
          <X className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      </div>

      <div className="h-4 w-px bg-border" />

      {/* Bulk edit form */}
      <div className="flex items-center gap-2">
        <select
          value={editField}
          onChange={(e) => setEditField(e.target.value)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          aria-label="Field to bulk edit"
        >
          <option value="">Select field...</option>
          {fieldOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <Input
          placeholder="New value..."
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="h-8 w-40"
          aria-label="New field value"
          disabled={!editField}
        />
        <Button size="sm" onClick={handleApply} disabled={!canApply}>
          {isApplying ? `Applying... ${progressPct}%` : 'Apply'}
        </Button>
      </div>

      <div className="h-4 w-px bg-border" />

      {/* Action buttons */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleValidate}
        disabled={bulkValidate.isPending || count === 0}
        title="Re-run SF validation on selected records"
      >
        <ShieldCheck className="h-3.5 w-3.5 mr-1" />
        Validate
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handleExportSelected}
        disabled={selectedBuildingIds.size === 0}
        title={
          selectedBuildingIds.size === 0
            ? 'Select buildings in sidebar first'
            : `Export ${selectedBuildingIds.size} building(s)`
        }
      >
        <Download className="h-3.5 w-3.5 mr-1" />
        Export Selected
      </Button>

      {undoSnapshot && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleUndo}
          disabled={updateRecord.isPending}
          title={`Undo bulk edit of ${undoSnapshot.field}`}
        >
          <Undo2 className="h-3.5 w-3.5 mr-1" />
          Undo
        </Button>
      )}
    </div>
  )
}
