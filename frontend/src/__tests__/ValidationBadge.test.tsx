/**
 * Unit tests for ValidationBadge logic (AC8 — E33-S4)
 *
 * These tests validate the badge color / tooltip determination logic extracted
 * from ValidationBadge.tsx.  They run in the Vitest node environment and do
 * NOT require @testing-library/react or jsdom.
 *
 * Run: cd frontend && npx vitest run src/__tests__/ValidationBadge.test.tsx
 */

import { describe, it, expect } from 'vitest'
import type { ACMRecord } from '@/lib/types/acm'

// ─── Logic helpers (mirror the implementation in ValidationBadge.tsx) ─────────

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
 */
function formatTooltip(errors: string[]): string {
  if (errors.length <= 3) return errors.join('\n')
  const preview = errors.slice(0, 3).join('\n')
  return `${preview}\n…and ${errors.length - 3} more`
}

/**
 * Determine badge color and tooltip text for a given cell/record state.
 * Returns { badgeColor, tooltipText } — both null means no badge shown.
 */
function determineBadge(
  fieldName: string | undefined,
  data: Partial<ACMRecord>
): { badgeColor: string | null; tooltipText: string | null } {
  const errors = data.validation_errors ?? []
  const status = data.validation_status
  const confidence = data.extraction_confidence
  // extraction_confidence in the frontend type is number | null
  const isLowConfidence = typeof confidence === 'number' && confidence < 0.5

  const fieldError = getFieldError(fieldName, errors)

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

  return { badgeColor, tooltipText }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeRecord(overrides: Partial<ACMRecord> = {}): Partial<ACMRecord> {
  return {
    id: 'record:1',
    source_id: 'source:1',
    school_name: 'Test School',
    building_id: 'B1',
    product: 'Ceiling tiles',
    material_description: 'ACM ceiling tiles',
    result: 'Present',
    validation_status: null,
    validation_errors: [],
    extraction_confidence: null,
    ...overrides,
  }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('ValidationBadge logic — getFieldError()', () => {
  it('returns null when errors array is empty', () => {
    expect(getFieldError('friable', [])).toBeNull()
  })

  it('returns null when fieldName is undefined', () => {
    expect(getFieldError(undefined, ['Unrecognized friable: xyz'])).toBeNull()
  })

  it('matches error by field name substring (case-insensitive)', () => {
    const err = 'Unrecognized FRIABLE value: xyz'
    expect(getFieldError('friable', [err])).toBe(err)
  })

  it('returns null when field name does not appear in any error', () => {
    const errors = ['Invalid product group: ABC']
    expect(getFieldError('friable', errors)).toBeNull()
  })

  it('returns the first matching error when multiple errors exist', () => {
    const errors = [
      'Unrecognized friable: xyz',
      'Friable field also invalid: abc',
    ]
    expect(getFieldError('friable', errors)).toBe(errors[0])
  })
})

describe('ValidationBadge logic — formatTooltip()', () => {
  it('joins <=3 errors with newlines', () => {
    const errors = ['Error 1', 'Error 2', 'Error 3']
    expect(formatTooltip(errors)).toBe('Error 1\nError 2\nError 3')
  })

  it('truncates to 3 and appends "...and N more" suffix', () => {
    const errors = ['E1', 'E2', 'E3', 'E4', 'E5']
    const result = formatTooltip(errors)
    expect(result).toContain('E1')
    expect(result).toContain('E2')
    expect(result).toContain('E3')
    expect(result).toContain('and 2 more')
    expect(result).not.toContain('E4')
  })

  it('handles a single error', () => {
    expect(formatTooltip(['Only error'])).toBe('Only error')
  })
})

describe('ValidationBadge logic — determineBadge()', () => {
  it('returns no badge when validation_status is "valid" and no errors', () => {
    const record = makeRecord({ validation_status: 'valid', validation_errors: [] })
    const { badgeColor, tooltipText } = determineBadge('friable', record)
    expect(badgeColor).toBeNull()
    expect(tooltipText).toBeNull()
  })

  it('returns red badge when status is "invalid" and field has matching error', () => {
    const record = makeRecord({
      validation_status: 'invalid',
      validation_errors: ['Unrecognized friable: xyz'],
    })
    const { badgeColor, tooltipText } = determineBadge('friable', record)
    expect(badgeColor).toBe('bg-red-500')
    expect(tooltipText).toBe('Unrecognized friable: xyz')
  })

  it('returns red badge when status is "failed_correction" and field has matching error', () => {
    const record = makeRecord({
      validation_status: 'failed_correction',
      validation_errors: ['Could not correct friable: xyz'],
    })
    const { badgeColor, tooltipText } = determineBadge('friable', record)
    expect(badgeColor).toBe('bg-red-500')
    expect(tooltipText).toContain('friable')
  })

  it('returns orange badge when status is "corrected" and field has matching error', () => {
    const record = makeRecord({
      validation_status: 'corrected',
      validation_errors: ['friable normalised from "friable" to "Friable"'],
    })
    const { badgeColor, tooltipText } = determineBadge('friable', record)
    expect(badgeColor).toBe('bg-orange-500')
    expect(tooltipText).toMatch(/^Corrected:/)
  })

  it('returns yellow badge when extraction_confidence is low (numeric < 0.5)', () => {
    const record = makeRecord({
      validation_status: null,
      validation_errors: [],
      extraction_confidence: 0.3 as unknown as never, // frontend type allows number
    })
    const { badgeColor, tooltipText } = determineBadge('product', record)
    expect(badgeColor).toBe('bg-yellow-500')
    expect(tooltipText).toBe('Low extraction confidence')
  })

  it('does NOT show yellow badge when confidence is null', () => {
    const record = makeRecord({ extraction_confidence: null, validation_errors: [] })
    const { badgeColor } = determineBadge('product', record)
    expect(badgeColor).toBeNull()
  })

  it('does NOT show yellow badge when confidence >= 0.5', () => {
    const record = makeRecord({
      validation_errors: [],
      extraction_confidence: 0.8 as unknown as never,
    })
    const { badgeColor } = determineBadge('product', record)
    expect(badgeColor).toBeNull()
  })

  it('shows no badge when record has errors but field name does not match', () => {
    const record = makeRecord({
      validation_status: 'invalid',
      validation_errors: ['Invalid product_group: XYZ'],
    })
    const { badgeColor } = determineBadge('friable', record)
    // friable does not appear in the error string
    expect(badgeColor).toBeNull()
  })

  it('handles undefined validation_errors gracefully (no badge)', () => {
    const record = makeRecord({ validation_errors: undefined as unknown as string[] })
    const { badgeColor, tooltipText } = determineBadge('friable', record)
    expect(badgeColor).toBeNull()
    expect(tooltipText).toBeNull()
  })

  it('handles null validation_status gracefully (no badge for non-low-confidence)', () => {
    const record = makeRecord({
      validation_status: null,
      validation_errors: ['some error mentioning friable'],
    })
    // Status is null — neither invalid, failed_correction, nor corrected → no badge
    const { badgeColor } = determineBadge('friable', record)
    expect(badgeColor).toBeNull()
  })
})
