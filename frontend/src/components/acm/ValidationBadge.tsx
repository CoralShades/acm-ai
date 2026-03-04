'use client'

import type { ICellRendererParams } from 'ag-grid-community'
import type { ACMRecord } from '@/lib/types/acm'

// ---- helpers ----------------------------------------------------------------

/**
 * Check whether a given field name appears in any of the validation error
 * strings. Errors are formatted as e.g. "Unrecognized friable: xyz" so we
 * match the field name as a substring (case-insensitive).
 */
function getFieldError(fieldName: string | undefined, errors: string[]): string | null {
  if (!fieldName || !errors?.length) return null
  const match = errors.find((e) => e.toLowerCase().includes(fieldName.toLowerCase()))
  return match ?? null
}

/**
 * Truncate a list of errors for tooltip display.
 * Shows first 3 errors and appends "and N more..." if there are extras.
 */
function formatTooltip(errors: string[]): string {
  if (errors.length <= 3) return errors.join('\n')
  const preview = errors.slice(0, 3).join('\n')
  return `${preview}\n…and ${errors.length - 3} more`
}

// ---- component --------------------------------------------------------------

// AG Grid provides: value, data, colDef — no extra params needed
type ValidationBadgeParams = ICellRendererParams<ACMRecord>

/**
 * AG Grid custom cell renderer that wraps a cell value with a small colored
 * dot when a validation issue exists for the cell's field.
 *
 * Color mapping:
 *   red    — validation_status "invalid" or "failed_correction" + this field has an error
 *   orange — validation_status "corrected" + this field was corrected
 *   yellow — extraction_confidence === "low" (any field, no per-field error required)
 */
export function ValidationBadge(params: ValidationBadgeParams) {
  const { value, data, colDef } = params

  if (!data) return <span>{value ?? ''}</span>

  const fieldName = colDef?.field as string | undefined
  const errors = data.validation_errors ?? []
  const status = data.validation_status

  // extraction_confidence is a number 0–1; treat < 0.5 as "low"
  const confidence = data.extraction_confidence
  const isLowConfidence = typeof confidence === 'number' && confidence < 0.5

  const fieldError = getFieldError(fieldName, errors)

  // Determine badge properties
  let badgeColor: string | null = null
  let tooltipText: string | null = null

  if (fieldError && (status === 'invalid' || status === 'failed_correction')) {
    badgeColor = 'bg-red-500'
    tooltipText = fieldError
  } else if (fieldError && status === 'corrected') {
    badgeColor = 'bg-orange-500'
    tooltipText = `Corrected: ${fieldError}`
  } else if (isLowConfidence) {
    badgeColor = 'bg-yellow-500'
    tooltipText = 'Low extraction confidence'
  }

  // Show all per-record errors in a row-level tooltip when no field-specific
  // error matches but the record has issues (e.g. looking at a non-errored field
  // in an invalid record).
  const rowTooltip =
    !tooltipText && errors.length > 0 && (status === 'invalid' || status === 'failed_correction')
      ? formatTooltip(errors)
      : null

  if (!badgeColor && !rowTooltip) return <span>{value ?? ''}</span>

  return (
    <span
      className="inline-flex items-center gap-1.5 w-full"
      title={tooltipText ?? rowTooltip ?? undefined}
    >
      {badgeColor && (
        <span
          className={`inline-block w-2 h-2 rounded-full shrink-0 ${badgeColor}`}
          aria-hidden="true"
        />
      )}
      <span className="truncate">{value ?? ''}</span>
    </span>
  )
}
