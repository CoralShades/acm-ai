'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Columns3, Check } from 'lucide-react'
import {
  useColumnPresetStore,
  PRESET_COLUMNS,
  PRESET_LABELS,
  type PresetName,
} from '@/lib/stores/column-visibility-store'
import type { GridApi } from 'ag-grid-community'

// Fallback display names when field-config API is unavailable
const FALLBACK_DISPLAY_NAMES: Record<string, string> = {
  building_id: 'Building Code',
  building_name: 'Building Name',
  room_id: 'Room ID',
  room_name: 'Room Name',
  product: 'ACM Name',
  acm_product_type: 'ACM Product Type',
  material_description: 'Material Description',
  result: 'Result',
  friable: 'Friability',
  material_condition: 'Condition',
  risk_status: 'Risk Status',
  area_type: 'Internal/External',
  hygienist_recommendations: 'Hygienist Recommendations',
  page_number: 'Page',
  sample_no: 'Sample No',
  sample_result: 'Sample Result',
  quantity: 'Quantity',
  floor_level: 'Floor Level',
  acm_labelled: 'Labelled',
  identifying_company: 'Identifying Company',
  acm_product_group: 'Product Group',
  disturbance_potential: 'Disturbance Potential',
  accessibility: 'Accessibility',
  reassessment_date: 'Reassessment Date',
  area_sqm: 'Area (sqm)',
  unit_of_measure: 'Unit of Measure',
  removal_priority: 'Removal Priority',
  removal_date: 'Removal Date',
  removal_contractor: 'Removal Contractor',
  removal_method: 'Removal Method',
  disposal_certificate_no: 'Disposal Certificate No',
  verification_date: 'Verification Date',
}

interface FieldInfo {
  internal_name: string
  display_name: string
}

interface ColumnVisibilityPickerProps {
  gridApi: GridApi | null
  onResetColumns: () => void
  disabled?: boolean
}

const PRESET_ORDER: Exclude<PresetName, 'custom'>[] = [
  'essential',
  'full-bar',
  'assessment-focus',
  'removal-tracking',
]

export function ColumnVisibilityPicker({
  gridApi,
  onResetColumns,
  disabled = false,
}: ColumnVisibilityPickerProps) {
  const { activePreset, setActivePreset } = useColumnPresetStore()
  const [fieldInfos, setFieldInfos] = useState<FieldInfo[]>([])
  const [open, setOpen] = useState(false)

  // Fetch field config from API for display names
  useEffect(() => {
    let cancelled = false
    async function fetchFields() {
      try {
        const res = await fetch('/api/acm/field-config')
        if (res.ok) {
          const data = await res.json()
          if (!cancelled && data.fields) {
            setFieldInfos(
              data.fields.map((f: { internal_name: string; display_name: string }) => ({
                internal_name: f.internal_name,
                display_name: f.display_name,
              }))
            )
          }
        }
      } catch {
        // Fall back to grid columns
      }
    }
    fetchFields()
    return () => { cancelled = true }
  }, [])

  // Get columns from grid API, falling back to field config
  const columns = useMemo(() => {
    if (!gridApi) return []
    const allCols = gridApi.getColumns() ?? []
    return allCols
      .filter((col) => {
        const id = col.getColId()
        // Exclude action column and ag-Grid internal columns
        return id && !id.startsWith('ag-') && id !== '0' // actions column has no field
      })
      .map((col) => {
        const id = col.getColId()
        const fieldInfo = fieldInfos.find((f) => f.internal_name === id)
        const headerName = col.getColDef().headerName
        return {
          colId: id,
          displayName: fieldInfo?.display_name || headerName || FALLBACK_DISPLAY_NAMES[id] || id,
          visible: col.isVisible(),
        }
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-compute when popover opens
  }, [gridApi, fieldInfos, open])

  const handleToggleColumn = useCallback(
    (colId: string) => {
      if (!gridApi) return
      const col = gridApi.getColumn(colId)
      if (!col) return
      const newVisible = !col.isVisible()
      gridApi.setColumnsVisible([colId], newVisible)
      setActivePreset('custom')
    },
    [gridApi, setActivePreset]
  )

  const handleApplyPreset = useCallback(
    (preset: Exclude<PresetName, 'custom'>) => {
      if (!gridApi) return
      const presetCols = PRESET_COLUMNS[preset]
      const allCols = gridApi.getColumns() ?? []
      const isFullBar = preset === 'full-bar'

      const stateArray = allCols.map((col) => {
        const id = col.getColId()
        // Always show the actions column
        const isActions = id === '0' || col.getColDef().headerName === 'Actions'
        return {
          colId: id,
          hide: isActions ? false : isFullBar ? false : !presetCols.includes(id),
        }
      })

      gridApi.applyColumnState({ state: stateArray })
      setActivePreset(preset)
    },
    [gridApi, setActivePreset]
  )

  const handleReset = useCallback(() => {
    onResetColumns()
    setActivePreset('essential')
    setOpen(false)
  }, [onResetColumns, setActivePreset])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled} title="Column visibility">
          <Columns3 className="mr-1 h-4 w-4" />
          Columns
          {activePreset !== 'essential' && (
            <span className="ml-1 text-xs text-muted-foreground">
              ({PRESET_LABELS[activePreset]})
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="start">
        {/* Preset Buttons */}
        <div className="flex flex-wrap gap-1 p-3 border-b">
          {PRESET_ORDER.map((preset) => (
            <Button
              key={preset}
              variant={activePreset === preset ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-7"
              onClick={() => handleApplyPreset(preset)}
            >
              {PRESET_LABELS[preset]}
            </Button>
          ))}
          {activePreset === 'custom' && (
            <span className="text-xs text-muted-foreground self-center ml-1">Custom</span>
          )}
        </div>

        {/* Column List */}
        <div
          className="max-h-[320px] overflow-y-auto p-2"
          role="listbox"
          aria-label="Toggle column visibility"
        >
          {columns.map((col) => (
            <button
              key={col.colId}
              role="option"
              aria-selected={col.visible}
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm rounded hover:bg-muted cursor-pointer text-left"
              onClick={() => handleToggleColumn(col.colId)}
              onKeyDown={(e) => {
                if (e.key === ' ') {
                  e.preventDefault()
                  handleToggleColumn(col.colId)
                }
              }}
            >
              <div
                className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                  col.visible
                    ? 'bg-primary border-primary text-primary-foreground'
                    : 'border-muted-foreground/30'
                }`}
              >
                {col.visible && <Check className="h-3 w-3" />}
              </div>
              <span className="truncate">{col.displayName}</span>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t p-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            onClick={handleReset}
          >
            Reset to Default
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
