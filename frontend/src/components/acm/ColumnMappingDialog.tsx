'use client'

import { useState, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type {
  SchemaMappingItem,
  SchemaMappingReviewPayload,
  SchemaMappingResponse,
} from '@/lib/types/v3-streaming'

/** Salesforce field options for the dropdown. */
const SF_FIELDS: { value: string; label: string }[] = [
  { value: 'Room_or_Area__c', label: 'Room / Area' },
  { value: 'Item_Name__c', label: 'Item / Material Name' },
  { value: 'Friability_of_Material__c', label: 'Friability' },
  { value: 'Condition__c', label: 'Condition' },
  { value: 'NATA_Endorsed_Sample_no__c', label: 'Sample Number' },
  { value: 'Sample_Analysis_Result_Material_Status__c', label: 'Sample Result' },
  { value: 'Quantity__c', label: 'Quantity' },
  { value: 'Hygienist_Recommendations__c', label: 'Recommendations' },
  { value: 'Accessibility__c', label: 'Accessibility' },
  { value: 'Asbestos_Type__c', label: 'Asbestos Type' },
  { value: 'Disturbance_Potential__c', label: 'Disturbance Potential' },
  { value: 'Specific_Location__c', label: 'Specific Location' },
  { value: 'Building_Code__c', label: 'Building Code' },
]

function confidenceBadge(confidence: number) {
  if (confidence >= 0.9) {
    return (
      <Badge variant="default" className="bg-green-600 text-white">
        {(confidence * 100).toFixed(0)}%
      </Badge>
    )
  }
  if (confidence >= 0.7) {
    return (
      <Badge variant="default" className="bg-yellow-500 text-black">
        {(confidence * 100).toFixed(0)}%
      </Badge>
    )
  }
  return (
    <Badge variant="destructive">
      {(confidence * 100).toFixed(0)}%
    </Badge>
  )
}

interface ColumnMappingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  payload: SchemaMappingReviewPayload | null
  isSubmitting: boolean
  error: string | null
  onSubmit: (response: SchemaMappingResponse) => Promise<void>
}

export function ColumnMappingDialog({
  open,
  onOpenChange,
  payload,
  isSubmitting,
  error,
  onSubmit,
}: ColumnMappingDialogProps) {
  // Local state for user-editable mappings
  const [editedMappings, setEditedMappings] = useState<SchemaMappingItem[]>([])
  const [hasEdits, setHasEdits] = useState(false)

  // Initialize local mappings when payload changes
  const initMappings = useCallback(
    (mappings: SchemaMappingItem[]) => {
      setEditedMappings(mappings.map((m) => ({ ...m })))
      setHasEdits(false)
    },
    []
  )

  // Update a single mapping's SF field
  const updateMapping = useCallback(
    (index: number, newSfField: string) => {
      setEditedMappings((prev) => {
        const updated = [...prev]
        updated[index] = { ...updated[index], sf_field: newSfField, confidence: 1.0 }
        return updated
      })
      setHasEdits(true)
    },
    []
  )

  const handleApprove = useCallback(async () => {
    if (hasEdits) {
      await onSubmit({ action: 'modify', mappings: editedMappings })
    } else {
      await onSubmit({ action: 'approve' })
    }
  }, [hasEdits, editedMappings, onSubmit])

  const handleReject = useCallback(async () => {
    await onSubmit({ action: 'reject' })
  }, [onSubmit])

  if (!payload) return null

  // Initialize mappings on first render with payload
  if (editedMappings.length === 0 && payload.mappings.length > 0) {
    initMappings(payload.mappings)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Review Column Mapping</DialogTitle>
          <DialogDescription>
            Schema inference confidence is{' '}
            <span className="font-semibold">
              {(payload.overall_confidence * 100).toFixed(0)}%
            </span>
            {payload.detected_consultant && (
              <> — detected format: <span className="font-semibold">{payload.detected_consultant}</span></>
            )}
            . Please review the proposed column mappings below.
          </DialogDescription>
        </DialogHeader>

        {/* Mapping table */}
        <div className="border rounded-md overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b">
                <th className="text-left px-3 py-2 font-medium">PDF Header</th>
                <th className="text-left px-3 py-2 font-medium">Salesforce Field</th>
                <th className="text-center px-3 py-2 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {editedMappings.map((mapping, index) => (
                <tr
                  key={mapping.pdf_header}
                  className="border-b last:border-b-0 hover:bg-muted/30"
                >
                  <td className="px-3 py-2 font-mono text-xs">
                    {mapping.pdf_header}
                  </td>
                  <td className="px-3 py-2">
                    <Select
                      value={mapping.sf_field}
                      onValueChange={(val) => updateMapping(index, val)}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SF_FIELDS.map((field) => (
                          <SelectItem key={field.value} value={field.value}>
                            {field.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {confidenceBadge(mapping.confidence)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Unmapped headers */}
        {payload.unmapped_headers.length > 0 && (
          <div className="mt-2 text-xs text-muted-foreground">
            <span className="font-medium">Unmapped headers:</span>{' '}
            {payload.unmapped_headers.join(', ')}
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="mt-2 text-sm text-destructive">{error}</div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={handleReject}
            disabled={isSubmitting}
          >
            Reject
          </Button>
          <Button
            onClick={handleApprove}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Submitting...'
              : hasEdits
                ? 'Approve Modified'
                : 'Approve'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
