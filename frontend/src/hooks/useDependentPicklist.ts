import { useMemo } from 'react'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import type { ACMRecord } from '@/lib/types/acm'
import { fieldApiToRecordKey } from '@/lib/utils/acm-field-mapping'

export interface DependentPicklistOptions {
  allValues: string[]
  validValues: string[]
  controllerValue: string | null
  isDependent: boolean
}

/**
 * Pure function — extract valid options for a dependent field given the
 * controller field's current value. Suitable for unit testing without a hook.
 *
 * @param fieldApiName  SF api_name of the dependent field
 * @param rowData       Current row data (ACMRecord or partial form values)
 * @param schema        SFFieldSchemaConfig from the field-schema API
 * @param keyMapper     Function mapping SF api_name -> ACMRecord key (defaults to fieldApiToRecordKey)
 */
export function getFilteredOptions(
  fieldApiName: string,
  rowData: Partial<ACMRecord>,
  schema: SFFieldSchemaConfig,
  keyMapper: (apiName: string) => string = fieldApiToRecordKey
): DependentPicklistOptions {
  const chain = schema.dependencies.find(
    (d) => d.dependent_api_name === fieldApiName
  )

  const allValues: string[] = schema.picklists[fieldApiName] ?? []

  if (!chain) {
    return { allValues, validValues: allValues, controllerValue: null, isDependent: false }
  }

  const controllerKey = keyMapper(chain.controller_api_name) as keyof ACMRecord
  const controllerValue = (rowData[controllerKey] as string | null | undefined) ?? null

  if (!controllerValue) {
    // No controller value set — all options are valid (show all, none grayed out)
    return { allValues, validValues: allValues, controllerValue: null, isDependent: true }
  }

  // mapping value can be string (building chain) or string[] (ACM chain)
  const raw = chain.mapping[controllerValue]
  const validValues: string[] = Array.isArray(raw) ? raw : raw ? [raw as string] : []

  return { allValues, validValues, controllerValue, isDependent: true }
}

/**
 * React hook wrapping getFilteredOptions for use in components.
 * Memoized — re-runs only when schema, fieldApiName, or rowData changes.
 */
export function useDependentPicklist(
  fieldApiName: string,
  rowData: Partial<ACMRecord>,
  schema: SFFieldSchemaConfig | undefined
): DependentPicklistOptions {
  return useMemo(() => {
    if (!schema) {
      return { allValues: [], validValues: [], controllerValue: null, isDependent: false }
    }
    return getFilteredOptions(fieldApiName, rowData, schema)
  }, [fieldApiName, rowData, schema])
}
