'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DependentPicklistEditor } from './DependentPicklistEditor'
import type { ACMRecord, ACMRecordUpdateRequest } from '@/lib/types/acm'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import { cn } from '@/lib/utils'
import { fieldApiToRecordKey } from '@/lib/utils/acm-field-mapping'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RecordWizardProps {
  record: ACMRecord | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (data: ACMRecordUpdateRequest) => void
  schema: SFFieldSchemaConfig | null
  isSaving?: boolean
}

// ---------------------------------------------------------------------------
// Field group definitions
// ---------------------------------------------------------------------------

type FieldGroup = {
  title: string
  fields: Array<{ key: keyof ACMRecord; label: string }>
}

const FIELD_GROUPS: FieldGroup[] = [
  {
    title: 'Location',
    fields: [
      { key: 'building_name', label: 'Building Name' },
      { key: 'room_id', label: 'Room ID' },
      { key: 'room_name', label: 'Room Name' },
      { key: 'floor_level', label: 'Floor Level' },
      { key: 'area_type', label: 'Area Type' },
      { key: 'location', label: 'Location' },
    ],
  },
  {
    title: 'Material',
    fields: [
      { key: 'product', label: 'ACM Product' },
      { key: 'material_description', label: 'Material Description' },
      { key: 'extent', label: 'Extent' },
      { key: 'quantity', label: 'Quantity' },
    ],
  },
  {
    title: 'Classification',
    fields: [
      { key: 'friable', label: 'Friability' },
      { key: 'acm_product_group', label: 'ACM Product Group' },
      { key: 'acm_product_type', label: 'ACM Product Type' },
    ],
  },
  {
    title: 'Results',
    fields: [
      { key: 'result', label: 'Result' },
      { key: 'sample_no', label: 'Sample No.' },
      { key: 'sample_result', label: 'Sample Result' },
      { key: 'risk_status', label: 'Risk Status' },
      { key: 'material_condition', label: 'Material Condition' },
    ],
  },
  {
    title: 'Assessment',
    fields: [
      { key: 'disturbance_potential', label: 'Disturbance Potential' },
      { key: 'hygienist_recommendations', label: 'Hygienist Recommendations' },
      { key: 'normalized_action', label: 'Normalized Action' },
    ],
  },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build an ACMRecordUpdateRequest from the current form values (only changed
 * fields are included so the backend PATCH is minimal).
 */
function buildUpdateRequest(
  original: ACMRecord,
  formValues: Partial<ACMRecord>
): ACMRecordUpdateRequest {
  const request: ACMRecordUpdateRequest = {}
  const keys = Object.keys(formValues) as Array<keyof ACMRecord>
  for (const k of keys) {
    const originalValue = original[k]
    const newValue = formValues[k]
    // Include if changed (cast to any for dynamic assignment)
    if (newValue !== originalValue) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(request as any)[k] = newValue
    }
  }
  return request
}

/**
 * Find the SF api_name for a given ACMRecord key by scanning the schema's
 * item_fields. Returns null if no mapping found.
 */
function findApiNameForKey(
  recordKey: keyof ACMRecord,
  schema: SFFieldSchemaConfig
): string | null {
  for (const fieldDef of schema.item_fields.fields) {
    if (fieldApiToRecordKey(fieldDef.api_name) === String(recordKey)) {
      return fieldDef.api_name
    }
  }
  return null
}

/**
 * Return the validation error string for a given field key, or null if none.
 */
function getFieldError(
  fieldKey: keyof ACMRecord,
  errors: string[],
  schema: SFFieldSchemaConfig | null
): string | null {
  if (!errors.length) return null

  // Try matching by record key name
  const keyStr = String(fieldKey)
  const directMatch = errors.find((e) => e.toLowerCase().includes(keyStr.toLowerCase()))
  if (directMatch) return directMatch

  // Also try matching by SF api_name (without __c suffix)
  if (schema) {
    const apiName = findApiNameForKey(fieldKey, schema)
    if (apiName) {
      const baseApiName = apiName.replace(/__c$/i, '').toLowerCase()
      const apiMatch = errors.find((e) => e.toLowerCase().includes(baseApiName))
      if (apiMatch) return apiMatch
    }
  }

  return null
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface FieldRowProps {
  fieldKey: keyof ACMRecord
  label: string
  formValues: Partial<ACMRecord>
  onChange: (key: keyof ACMRecord, value: string) => void
  schema: SFFieldSchemaConfig | null
  errors: string[]
  isDependent: boolean
  apiName: string | null
}

function FieldRow({
  fieldKey,
  label,
  formValues,
  onChange,
  schema,
  errors,
  isDependent,
  apiName,
}: FieldRowProps) {
  const rawValue = formValues[fieldKey]
  const stringValue = rawValue != null ? String(rawValue) : ''
  const fieldError = getFieldError(fieldKey, errors, schema)
  const fieldId = `wizard-field-${String(fieldKey)}`

  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={fieldId} className={cn(fieldError && 'text-destructive')}>
        {label}
      </Label>

      {isDependent && apiName && schema ? (
        // Dependent picklist — use DependentPicklistEditor in form mode
        <DependentPicklistEditor
          mode="form"
          fieldApiName={apiName}
          schema={schema}
          rowData={formValues as Partial<ACMRecord>}
          value={stringValue}
          onChange={(val) => onChange(fieldKey, val)}
          id={fieldId}
          className={cn(
            'h-9 rounded-md border border-input px-3 py-1 text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-ring',
            fieldError && 'border-destructive focus:ring-destructive/50'
          )}
        />
      ) : (
        <Input
          id={fieldId}
          value={stringValue}
          onChange={(e) => onChange(fieldKey, e.target.value)}
          aria-invalid={!!fieldError}
          className={cn(fieldError && 'border-destructive focus-visible:ring-destructive/50')}
        />
      )}

      {fieldError && (
        <p className="text-xs text-destructive" role="alert">
          {fieldError}
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function RecordWizard({
  record,
  open,
  onOpenChange,
  onSave,
  schema,
  isSaving = false,
}: RecordWizardProps) {
  // Initialise form values from record whenever record changes
  const [formValues, setFormValues] = useState<Partial<ACMRecord>>({})

  useEffect(() => {
    if (record) {
      setFormValues({ ...record })
    }
  }, [record])

  const handleFieldChange = useCallback((key: keyof ACMRecord, value: string) => {
    setFormValues((prev) => ({ ...prev, [key]: value }))
  }, [])

  const handleSave = useCallback(() => {
    if (!record) return
    const updateRequest = buildUpdateRequest(record, formValues)
    onSave(updateRequest)
  }, [record, formValues, onSave])

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (!isSaving) onOpenChange(nextOpen)
    },
    [isSaving, onOpenChange]
  )

  // Pull out validation info from the record (not formValues, as backend owns this)
  const errors = record?.validation_errors ?? []
  const status = record?.validation_status

  // Build a set of dependent field api_names from schema for quick lookup
  const dependentApiNames = new Set<string>(
    schema
      ? schema.item_fields.fields
          .filter((f) => f.is_dependent && !!f.controller_field)
          .map((f) => f.api_name)
      : []
  )

  function isDependentField(fieldKey: keyof ACMRecord, s: SFFieldSchemaConfig | null): boolean {
    if (!s) return false
    const apiName = findApiNameForKey(fieldKey, s)
    return apiName ? dependentApiNames.has(apiName) : false
  }

  // Summary error count for the dialog header
  const totalErrors = errors.length

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Edit Record
            {record && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                {record.building_name ?? record.building_id} / {record.room_name ?? record.room_id}
              </span>
            )}
          </DialogTitle>

          {/* Validation status banner */}
          {status && status !== 'valid' && (
            <div
              className={cn(
                'rounded-md px-3 py-2 text-sm',
                (status === 'invalid' || status === 'failed_correction') &&
                  'bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400',
                status === 'corrected' &&
                  'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400'
              )}
            >
              {status === 'invalid' && `${totalErrors} validation error${totalErrors !== 1 ? 's' : ''} — review highlighted fields`}
              {status === 'failed_correction' && `Auto-correction failed — ${totalErrors} error${totalErrors !== 1 ? 's' : ''} remain`}
              {status === 'corrected' && `Auto-corrected — ${totalErrors} field${totalErrors !== 1 ? 's' : ''} were adjusted`}
            </div>
          )}

          {/* Schema loading hint */}
          {!schema && (
            <p className="text-xs text-muted-foreground">
              Loading field schema — picklist dropdowns will appear shortly
            </p>
          )}
        </DialogHeader>

        {/* Scrollable form body */}
        <div className="overflow-y-auto flex-1 pr-1">
          {FIELD_GROUPS.map((group) => (
            <div key={group.title} className="mb-5">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                {group.title}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {group.fields.map(({ key, label }) => {
                  const apiName = schema ? findApiNameForKey(key, schema) : null
                  const isDependent = isDependentField(key, schema)
                  return (
                    <FieldRow
                      key={String(key)}
                      fieldKey={key}
                      label={label}
                      formValues={formValues}
                      onChange={handleFieldChange}
                      schema={schema}
                      errors={errors}
                      isDependent={isDependent}
                      apiName={apiName}
                    />
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        <DialogFooter className="gap-2 shrink-0 pt-2">
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving…' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
