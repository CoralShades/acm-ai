'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, AlertTriangle, RotateCcw, Save, Calculator } from 'lucide-react'
import { fieldMappingApi } from '@/lib/api/field-mapping'
import type { FieldMapping, FieldMappingEntry } from '@/lib/types/field-mapping'

// ACM record fields available for mapping
const ACM_FIELDS = [
  { value: '', label: '— Unmapped —' },
  { value: 'school_name', label: 'School Name' },
  { value: 'school_code', label: 'School Code' },
  { value: 'building_id', label: 'Building Code' },
  { value: 'building_name', label: 'Building Name' },
  { value: 'building_year', label: 'Building Year' },
  { value: 'building_construction', label: 'Building Construction' },
  { value: 'room_id', label: 'Room ID' },
  { value: 'room_name', label: 'Room Name' },
  { value: 'room_area', label: 'Room Area' },
  { value: 'area_type', label: 'Area Type' },
  { value: 'floor_level', label: 'Floor Level' },
  { value: 'product', label: 'Product' },
  { value: 'material_description', label: 'Material Description' },
  { value: 'acm_product_group', label: 'ACM Product Group' },
  { value: 'extent', label: 'Extent' },
  { value: 'location', label: 'Location' },
  { value: 'friable', label: 'Friable' },
  { value: 'material_condition', label: 'Material Condition' },
  { value: 'disturbance_potential', label: 'Disturbance Potential' },
  { value: 'risk_status', label: 'Risk Status' },
  { value: 'result', label: 'Result' },
  { value: 'sample_no', label: 'Sample No' },
  { value: 'sample_result', label: 'Sample Result' },
  { value: 'quantity', label: 'Quantity' },
  { value: 'acm_labelled', label: 'ACM Labelled' },
  { value: 'acm_label_details', label: 'ACM Label Details' },
  { value: 'identifying_company', label: 'Identifying Company' },
  { value: 'hygienist_recommendations', label: 'Hygienist Recommendations' },
  { value: 'normalized_action', label: 'Normalized Action' },
  { value: 'psb_supplied_acm_id', label: 'PSB Supplied ACM ID' },
  { value: 'removal_status', label: 'Removal Status' },
  { value: 'date_of_removal', label: 'Date of Removal' },
  { value: 'extraction_confidence', label: 'Extraction Confidence' },
  { value: 'data_issues', label: 'Data Issues' },
  { value: 'page_number', label: 'Page Number' },
  { value: 'source_id', label: 'Source ID' },
  { value: 'id', label: 'Record ID' },
]

export function FieldMappingConfig() {
  const [mapping, setMapping] = useState<FieldMapping | null>(null)
  const [original, setOriginal] = useState<FieldMapping | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMapping = useCallback(async () => {
    try {
      setLoading(true)
      const data = await fieldMappingApi.get()
      setMapping(data)
      setOriginal(data)
      setError(null)
    } catch {
      setError('Failed to load field mapping')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMapping()
  }, [fetchMapping])

  const hasChanges =
    mapping && original && JSON.stringify(mapping.mappings) !== JSON.stringify(original.mappings)

  const handleFieldChange = (index: number, acmField: string) => {
    if (!mapping) return
    const updated = [...mapping.mappings]
    updated[index] = { ...updated[index], acm_field: acmField || null }
    setMapping({ ...mapping, mappings: updated })
  }

  const handleSave = async () => {
    if (!mapping) return
    try {
      setSaving(true)
      const updated = await fieldMappingApi.update({ mappings: mapping.mappings })
      setMapping(updated)
      setOriginal(updated)
      setError(null)
    } catch {
      setError('Failed to save mapping')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      setSaving(true)
      const defaults = await fieldMappingApi.reset()
      setMapping(defaults)
      setOriginal(defaults)
      setError(null)
    } catch {
      setError('Failed to reset mapping')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!mapping) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error || 'Failed to load mapping'}</AlertDescription>
      </Alert>
    )
  }

  const mappedCount = mapping.mappings.filter((m) => m.acm_field).length
  const totalCount = mapping.mappings.length

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <Label className="text-base font-medium">
            {mappedCount} of {totalCount} columns mapped
          </Label>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleSave} disabled={!hasChanges || saving} size="sm">
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save
          </Button>
          <Button variant="outline" onClick={handleReset} disabled={saving} size="sm">
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
      </div>

      {hasChanges && (
        <p className="text-sm text-amber-500">Unsaved changes</p>
      )}

      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-3 py-2 text-left font-medium w-8">#</th>
              <th className="px-3 py-2 text-left font-medium">BAR Column</th>
              <th className="px-3 py-2 text-left font-medium">ACM Field</th>
              <th className="px-3 py-2 text-left font-medium w-16">Type</th>
            </tr>
          </thead>
          <tbody>
            {mapping.mappings.map((entry: FieldMappingEntry, idx: number) => (
              <tr key={idx} className="border-b last:border-0">
                <td className="px-3 py-1.5 text-muted-foreground">{entry.bar_column_index + 1}</td>
                <td className="px-3 py-1.5 font-medium">{entry.bar_column}</td>
                <td className="px-3 py-1.5">
                  {entry.is_computed ? (
                    <div className="flex items-center gap-2">
                      <Calculator className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-muted-foreground text-xs">{entry.formula || 'Computed'}</span>
                    </div>
                  ) : (
                    <Select
                      value={entry.acm_field || ''}
                      onValueChange={(v) => handleFieldChange(idx, v)}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue placeholder="Unmapped" />
                      </SelectTrigger>
                      <SelectContent>
                        {ACM_FIELDS.map((f) => (
                          <SelectItem key={f.value} value={f.value}>
                            {f.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </td>
                <td className="px-3 py-1.5">
                  {entry.is_computed ? (
                    <Badge variant="outline" className="text-xs">Computed</Badge>
                  ) : entry.acm_field ? (
                    <Badge variant="secondary" className="text-xs">Mapped</Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs text-muted-foreground">Empty</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
