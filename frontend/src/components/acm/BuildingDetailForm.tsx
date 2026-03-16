'use client'

import { useState, useMemo, useCallback } from 'react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { DependentPicklistEditor } from '@/components/acm/DependentPicklistEditor'
import { cn } from '@/lib/utils'
import type { BuildingRecord } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import type { ACMRecord } from '@/lib/types/acm'

interface BuildingDetailFormProps {
  building: BuildingRecord
  sourceId: string
  schema: SFFieldSchemaConfig | null
  onSave: (data: Partial<BuildingRecord>) => void
  isSaving: boolean
}

type FormValues = Partial<BuildingRecord>

/** Humanize a snake_case field name into a readable label. */
function humanize(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Derive a display label from the SF field schema or fall back to humanized key. */
function fieldLabel(key: string, schema: SFFieldSchemaConfig | null): string {
  if (!schema) return humanize(key)
  const found = schema.building_fields.fields.find(
    (f) =>
      f.api_name
        .replace(/__c$/i, '')
        .toLowerCase()
        .replace(/_/g, '_') === key
  )
  return found?.label ?? humanize(key)
}

/** Fields that are read-only (not editable by officers). */
const READ_ONLY_FIELDS = new Set(['id', 'internal_id', 'source_id', 'record_count', 'created', 'updated'])

/** Fields that are boolean (use Checkbox). */
const BOOLEAN_FIELDS = new Set(['building_out_of_scope'])

/** Fields that are numeric. */
const NUMERIC_FIELDS = new Set(['number_of_levels', 'est_building_size_m2', 'no_identified_acms'])

/** The dependent picklist field for buildings — category depends on type. */
const DEPENDENT_PICKLIST_FIELD = 'building_category'
const DEPENDENT_PICKLIST_API_NAME = 'Building_Category__c'

/** Regular picklist fields — look up from schema.building_fields.picklists. */
const PICKLIST_FIELDS = new Set([
  'building_type',
  'roof_type',
  'frequency_of_use',
  'daily_duration',
  'level_of_activity',
  'public_access',
  'mobile_plant',
  'owned_or_leased',
  'asbestos_register_available',
  'audit_report_available',
  'within_your_portfolio',
  'demolished_status',
  'demolition_type',
  'possible_capital_works_project',
  'psb_district_region',
])

/**
 * Map a BuildingRecord field key to the SF api_name used in schema.building_fields.picklists.
 * Most keys just need __c suffix uppercased PascalCase, but there are explicit mappings.
 */
function buildingKeyToApiName(key: string): string {
  const overrides: Record<string, string> = {
    building_type: 'Building_Type__c',
    building_category: 'Building_Category__c',
    roof_type: 'Roof_Type__c',
    frequency_of_use: 'Frequency_of_Use__c',
    daily_duration: 'Daily_Duration__c',
    level_of_activity: 'Level_of_Activity__c',
    public_access: 'Public_Access__c',
    mobile_plant: 'Mobile_Plant__c',
    owned_or_leased: 'Owned_or_Leased__c',
    asbestos_register_available: 'Asbestos_Register_Available__c',
    audit_report_available: 'Audit_Report_Available__c',
    within_your_portfolio: 'Within_Your_Portfolio__c',
    demolished_status: 'Demolished_Status__c',
    demolition_type: 'Demolition_Type__c',
    possible_capital_works_project: 'Possible_Capital_Works_Project__c',
    psb_district_region: 'PSB_District_Region__c',
  }
  return overrides[key] ?? key
}

/**
 * Field groups for the building detail form.
 * Each group has a title and an ordered list of BuildingRecord field keys.
 */
const FIELD_GROUPS: { title: string; fields: string[] }[] = [
  {
    title: 'Identity',
    fields: [
      'building_code',
      'building_name',
      'internal_id',
      'external_id',
      'building_unique_id',
      'site_name',
      'school_uid',
    ],
  },
  {
    title: 'Location',
    fields: [
      'building_address',
      'suburb',
      'postcode',
      'state',
      'country',
      'building_address_lga',
      'building_address_region',
      'gps_coordinates',
      'psb_district_region',
    ],
  },
  {
    title: 'Construction',
    fields: [
      'building_type',
      'building_category',
      'building_construction',
      'roof_type',
      'number_of_levels',
      'est_building_size_m2',
      'building_year',
    ],
  },
  {
    title: 'Usage',
    fields: [
      'frequency_of_use',
      'daily_duration',
      'level_of_activity',
      'public_access',
      'mobile_plant',
      'owned_or_leased',
      'within_your_portfolio',
    ],
  },
  {
    title: 'Inspection',
    fields: [
      'asbestos_register_available',
      'audit_report_available',
      'date_of_audit_report',
      'no_identified_acms',
      'no_identified_acms_note',
    ],
  },
  {
    title: 'Demolition',
    fields: [
      'demolished_status',
      'demolition_date',
      'demolition_type',
      'demolition_comments',
      'building_out_of_scope',
      'building_out_of_scope_comments',
    ],
  },
  {
    title: 'Other',
    fields: [
      'additional_comments',
      'capital_works_project_details',
      'possible_capital_works_project',
    ],
  },
]

function FieldInput({
  fieldKey,
  value,
  onChange,
  schema,
  formValues,
}: {
  fieldKey: string
  value: string | number | boolean | null | undefined
  onChange: (key: string, val: string | number | boolean | null) => void
  schema: SFFieldSchemaConfig | null
  formValues: FormValues
}) {
  const inputId = `field-${fieldKey}`

  if (READ_ONLY_FIELDS.has(fieldKey)) {
    return (
      <Input
        id={inputId}
        value={value != null ? String(value) : ''}
        disabled
        className="bg-muted/50 cursor-not-allowed"
        aria-readonly="true"
      />
    )
  }

  if (BOOLEAN_FIELDS.has(fieldKey)) {
    return (
      <div className="flex items-center h-9">
        <Checkbox
          id={inputId}
          checked={Boolean(value)}
          onCheckedChange={(checked) => onChange(fieldKey, Boolean(checked))}
        />
      </div>
    )
  }

  if (fieldKey === DEPENDENT_PICKLIST_FIELD && schema) {
    return (
      <DependentPicklistEditor
        mode="form"
        fieldApiName={DEPENDENT_PICKLIST_API_NAME}
        schema={schema}
        rowData={formValues as Partial<ACMRecord>}
        value={typeof value === 'string' ? value : ''}
        onChange={(val) => onChange(fieldKey, val || null)}
        placeholder="-- Select --"
        id={inputId}
      />
    )
  }

  if (PICKLIST_FIELDS.has(fieldKey) && schema) {
    const apiName = buildingKeyToApiName(fieldKey)
    const options: string[] =
      schema.building_fields.picklists[apiName] ??
      schema.picklists[apiName] ??
      []

    if (options.length > 0) {
      return (
        <select
          id={inputId}
          value={typeof value === 'string' ? value : ''}
          onChange={(e) => onChange(fieldKey, e.target.value || null)}
          className={cn(
            'flex h-9 w-full items-center rounded-md border border-input bg-transparent px-3 py-1 text-sm',
            'shadow-xs transition-[color,box-shadow] outline-none',
            'focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'appearance-none bg-[url("data:image/svg+xml;charset=UTF-8,%3csvg%20xmlns%3d%22http%3a%2f%2fwww.w3.org%2f2000%2fsvg%22%20width%3d%2212%22%20height%3d%2212%22%20viewBox%3d%220%200%2012%2012%22%3e%3cpath%20fill%3d%22%236b7280%22%20d%3d%22M2%204l4%204%204-4%22%2f%3e%3c%2fsvg%3e")] bg-[length:12px] bg-[right_12px_center] bg-no-repeat pr-8'
          )}
        >
          <option value="">-- Select --</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      )
    }
  }

  if (NUMERIC_FIELDS.has(fieldKey)) {
    return (
      <Input
        id={inputId}
        type="number"
        value={value != null ? String(value) : ''}
        onChange={(e) => {
          const parsed = e.target.value === '' ? null : Number(e.target.value)
          onChange(fieldKey, parsed)
        }}
      />
    )
  }

  // Default: text input
  return (
    <Input
      id={inputId}
      type="text"
      value={typeof value === 'string' ? value : value != null ? String(value) : ''}
      onChange={(e) => onChange(fieldKey, e.target.value || null)}
    />
  )
}

export function BuildingDetailForm({
  building,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  sourceId,
  schema,
  onSave,
  isSaving,
}: BuildingDetailFormProps) {
  const [formValues, setFormValues] = useState<FormValues>(() => ({ ...building }))

  // Compute dirty fields — fields that differ from the original building
  const dirtyFields = useMemo(() => {
    const dirty: Partial<BuildingRecord> = {}
    for (const key of Object.keys(formValues) as Array<keyof BuildingRecord>) {
      if (READ_ONLY_FIELDS.has(key)) continue
      const orig = building[key]
      const curr = formValues[key]
      // Use loose equality to handle null vs undefined
      if (curr !== orig) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(dirty as any)[key] = curr
      }
    }
    return dirty
  }, [formValues, building])

  const isDirty = Object.keys(dirtyFields).length > 0

  const handleChange = useCallback(
    (key: string, val: string | number | boolean | null) => {
      setFormValues((prev) => ({ ...prev, [key]: val }))
    },
    []
  )

  const handleSave = () => {
    if (isDirty) onSave(dirtyFields)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Form body — scrollable */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {FIELD_GROUPS.map((group) => (
          <section key={group.title}>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4 pb-2 border-b">
              {group.title}
            </h2>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {group.fields.map((fieldKey) => {
                const value = formValues[fieldKey as keyof BuildingRecord]
                const label = fieldLabel(fieldKey, schema)
                const isReadOnly = READ_ONLY_FIELDS.has(fieldKey)
                const inputId = `field-${fieldKey}`

                return (
                  <div key={fieldKey} className="flex flex-col gap-1.5">
                    <Label
                      htmlFor={inputId}
                      className={cn(
                        'text-xs',
                        isReadOnly && 'text-muted-foreground'
                      )}
                    >
                      {label}
                      {isReadOnly && (
                        <span className="ml-1 text-xs text-muted-foreground font-normal">
                          (read-only)
                        </span>
                      )}
                    </Label>
                    <FieldInput
                      fieldKey={fieldKey}
                      value={value}
                      onChange={handleChange}
                      schema={schema}
                      formValues={formValues}
                    />
                  </div>
                )
              })}
            </div>
          </section>
        ))}
      </div>

      {/* Save footer */}
      <div className="shrink-0 border-t px-6 py-4 bg-background flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isDirty
            ? `${Object.keys(dirtyFields).length} unsaved change${Object.keys(dirtyFields).length !== 1 ? 's' : ''}`
            : 'No changes'}
        </p>
        <Button
          onClick={handleSave}
          disabled={!isDirty || isSaving}
          size="sm"
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  )
}
