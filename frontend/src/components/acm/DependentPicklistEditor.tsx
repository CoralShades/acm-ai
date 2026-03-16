'use client'

import {
  forwardRef,
  useImperativeHandle,
  useState,
  useRef,
  useEffect,
  useMemo,
} from 'react'
import type { ICellEditorParams } from 'ag-grid-community'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import type { ACMRecord } from '@/lib/types/acm'
import { getFilteredOptions } from '@/hooks/useDependentPicklist'
import { cn } from '@/lib/utils'

// Params passed to the AG Grid cell editor via colDef.cellEditorSelector
export interface DependentPicklistEditorParams extends ICellEditorParams {
  fieldApiName: string
  schema: SFFieldSchemaConfig
}

// Props for standalone form mode usage
export interface DependentPicklistFormProps {
  mode: 'form'
  fieldApiName: string
  schema: SFFieldSchemaConfig
  rowData: Partial<ACMRecord>
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  id?: string
  className?: string
}

type DependentPicklistEditorProps =
  | ({ mode: 'grid' } & DependentPicklistEditorParams)
  | DependentPicklistFormProps

export const DependentPicklistEditor = forwardRef<
  { getValue: () => string },
  DependentPicklistEditorProps
>((props, ref) => {
  const isGrid = props.mode === 'grid'

  // In grid mode: read initial value and row data from ICellEditorParams
  const initialValue = isGrid ? (props.value as string) ?? '' : props.value
  const rowData = isGrid ? (props.data as Partial<ACMRecord>) : props.rowData
  const fieldApiName = props.fieldApiName
  const schema = props.schema

  const [selectedValue, setSelectedValue] = useState(initialValue)
  const selectRef = useRef<HTMLSelectElement>(null)

  // AG Grid contract: expose getValue() via ref
  useImperativeHandle(ref, () => ({
    getValue: () => selectedValue,
  }))

  // Focus the select on mount (required for AG Grid inline editing UX)
  useEffect(() => {
    selectRef.current?.focus()
  }, [])

  const { allValues, validValues, isDependent, controllerValue } = useMemo(
    () => getFilteredOptions(fieldApiName, rowData, schema),
    [fieldApiName, rowData, schema]
  )

  const validSet = useMemo(() => new Set(validValues), [validValues])

  // All options valid when: field is not dependent, OR dependent but no controller value set
  const showAllValid = !isDependent || controllerValue === null

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    setSelectedValue(val)
    if (!isGrid && props.mode === 'form') {
      props.onChange(val)
    }
  }

  return (
    <select
      ref={selectRef}
      value={selectedValue}
      onChange={handleChange}
      disabled={!isGrid && (props as DependentPicklistFormProps).disabled}
      aria-label={fieldApiName}
      className={cn(
        isGrid
          ? 'w-full h-full border-0 bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring'
          : 'flex h-9 w-full items-center rounded-md border border-input bg-background text-foreground px-3 py-1 pr-8 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 appearance-none bg-[length:16px_16px] bg-[position:right_8px_center] bg-no-repeat bg-[url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2724%27%20height%3D%2724%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%2371717a%27%20stroke-width%3D%272%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27m6%209%206%206%206-6%27/%3E%3C/svg%3E")]',
        !isGrid && (props as DependentPicklistFormProps).className
      )}
    >
      {(!isGrid && (props as DependentPicklistFormProps).placeholder) && (
        <option value="" disabled>
          {(props as DependentPicklistFormProps).placeholder}
        </option>
      )}
      {allValues.map((option) => {
        const isValid = showAllValid || validSet.has(option)
        return (
          <option
            key={option}
            value={option}
            disabled={!isValid}
            // AC5: visually grayed out via CSS — disabled options render
            // grayed out natively in all browsers; no hidden options
            aria-disabled={!isValid ? 'true' : undefined}
          >
            {option}
          </option>
        )
      })}
    </select>
  )
})

DependentPicklistEditor.displayName = 'DependentPicklistEditor'
