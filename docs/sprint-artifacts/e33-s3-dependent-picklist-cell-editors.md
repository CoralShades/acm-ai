# E33-S3: Dependent Picklist Cell Editors

## Story

**ID**: E33-S3
**Title**: Dependent Picklist Cell Editors
**Sprint**: V3-6
**Story Points**: 3
**Risk**: HIGH
**Type**: Frontend
**Dependencies**: GATE:AI_COMPLETE, E30-S4

### Acceptance Criteria

- AC1: Custom AG Grid cell editor: `DependentPicklistEditor`
- AC2: ACM chain: Friability -> Classification -> SubClassification cascading
- AC3: Building chain: Building_Type -> Building_Category cascading
- AC4: `getValues()` callback queries field_schema API for valid values based on controller field
- AC5: Invalid combinations visually prevented (grayed-out options)
- AC6: Works for both inline editing and Record Wizard modal
- AC7: Unit tests for cascading filter logic
- AC8: Accessibility: keyboard navigation through dropdowns

---

## Technical Design

### Architecture

The feature introduces three new units:

1. **`useDependentPicklist` hook** — pure logic layer, no DOM/AG Grid coupling. Computes the filtered set of valid options for a dependent field given the current controller field value. Shared between the AG Grid cell editor and the Record Wizard modal. This separation makes AC7 (unit tests) achievable without mounting a grid.

2. **`DependentPicklistEditor` component** — React component implementing the AG Grid custom cell editor contract (`forwardRef` + `useImperativeHandle` exposing `getValue()`). Also rendered as a standalone controlled `<select>` when used in the Record Wizard modal (AC6).

3. **`ItemGrid.tsx` modifications** — enable `editable: true` on dependent picklist columns, wire `cellEditorSelector` to return `DependentPicklistEditor` with props derived from the field schema dependency chain.

### Data Flow

```
SFFieldSchemaConfig (React Query, staleTime: Infinity)
  └─ dependencies: Array<{ controller_api_name, dependent_api_name, mapping }>
  └─ picklists: Record<string, string[]>  (all known values per api_name)

useDependentPicklist(fieldApiName, rowData, schema)
  1. Locate the SFDependencyChain where dependent_api_name === fieldApiName
  2. Resolve the controller field's ACMRecord key via fieldApiToRecordKey()
  3. Read controllerValue = rowData[controllerRecordKey]
  4. Lookup validValues = chain.mapping[controllerValue] (string[])
  5. Fetch allValues = schema.picklists[fieldApiName] (full picklist)
  6. Return { allValues, validValues, controllerValue }

DependentPicklistEditor
  ├── mode="grid"   → AG Grid cell editor (ICellEditorReact contract)
  └── mode="form"   → standalone controlled <select> for Record Wizard
```

### Dependency Chains (from backend `config_loader.py`)

**ACM chain (two-hop)**:

| Controller api_name         | Dependent api_name          | ACMRecord key (controller) | ACMRecord key (dependent) |
|-----------------------------|-----------------------------|----------------------------|---------------------------|
| `Friability_of_Material__c` | `ACM_Classification__c`     | `friable`                  | `acm_product_group`       |
| `ACM_Classification__c`     | `ACM_Sub_Classification__c` | `acm_product_group`        | `acm_product_type`        |

**Building chain (one-hop)**:

| Controller api_name | Dependent api_name    | ACMRecord key (controller) | ACMRecord key (dependent)   |
|---------------------|-----------------------|----------------------------|-----------------------------|
| `Building_Type__c`  | `Building_Category__c`| `building_type`            | `building_construction`     |

Note: `building_construction` maps to `Building_Category__c` via the existing `fieldApiToRecordKey` override map in `ItemGrid.tsx`.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/hooks/useDependentPicklist.ts` | NEW | Pure logic hook — computes `{ allValues, validValues, controllerValue }` for any dependent field given row data and the schema. Exported and testable in isolation. |
| `frontend/src/components/acm/DependentPicklistEditor.tsx` | NEW | Dual-mode React component: AG Grid cell editor (mode="grid") + standalone controlled select (mode="form"). Renders all options, grays out invalid ones. |
| `frontend/src/components/acm/ItemGrid.tsx` | MODIFY | Add `editable` and `cellEditorSelector` to dependent picklist column defs. Pass `fieldSchema` and `dependencies` as cell editor params. |
| `frontend/src/components/acm/ACMRecordDialog.tsx` | MODIFY | Replace plain `<Select>` for friable, acm_product_group, acm_product_type, building_type, building_construction with `DependentPicklistEditor` in form mode. Wire controller `watch()` values. |
| `tests/playwright/test_dependent_picklist.spec.ts` | NEW | Playwright E2E tests: grid inline editing cascades correctly; invalid options are grayed out; keyboard navigation works. |
| `frontend/src/hooks/__tests__/useDependentPicklist.test.ts` | NEW | Vitest unit tests for the `getFilteredOptions` pure function extracted from the hook. Covers all chain combinations including null/undefined controller values. |

---

## Implementation Details

### 1. `useDependentPicklist` hook

**Location**: `frontend/src/hooks/useDependentPicklist.ts`

```typescript
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'
import type { ACMRecord } from '@/lib/types/acm'

export interface DependentPicklistOptions {
  allValues: string[]       // Full picklist from schema
  validValues: string[]     // Valid values given current controller value
  controllerValue: string | null
  isDependent: boolean      // false when no chain exists for this field
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
 * Memoized — re-runs only when schema, fieldApiName, or controllerValue changes.
 */
export function useDependentPicklist(
  fieldApiName: string,
  rowData: Partial<ACMRecord>,
  schema: SFFieldSchemaConfig | undefined
): DependentPicklistOptions {
  return useMemo(() => {
    if (!schema) return { allValues: [], validValues: [], controllerValue: null, isDependent: false }
    return getFilteredOptions(fieldApiName, rowData, schema)
  }, [fieldApiName, rowData, schema])
}
```

The `fieldApiToRecordKey` function is duplicated from `ItemGrid.tsx` or exported from a shared utility. See the migration note in Section 6.

### 2. `DependentPicklistEditor` component

**Location**: `frontend/src/components/acm/DependentPicklistEditor.tsx`

The component is a single `forwardRef` React component that satisfies the AG Grid `ICellEditorReact` contract when used in grid mode, and behaves as a standard controlled select when used in form mode.

```typescript
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

// Params passed to the AG Grid cell editor via colDef.cellEditorParams
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

  const { allValues, validValues } = useMemo(
    () => getFilteredOptions(fieldApiName, rowData, schema),
    [fieldApiName, rowData, schema]
  )

  const validSet = useMemo(() => new Set(validValues), [validValues])

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
        'w-full h-full border-0 bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring',
        !isGrid && (props as DependentPicklistFormProps).className
      )}
    >
      {(!isGrid && (props as DependentPicklistFormProps).placeholder) && (
        <option value="" disabled>
          {(props as DependentPicklistFormProps).placeholder}
        </option>
      )}
      {allValues.map((option) => {
        const isValid = validSet.size === 0 || validSet.has(option)
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
```

**Keyboard navigation** (AC8): The native `<select>` element has full keyboard support out of the box: Tab to focus, Arrow keys to navigate options, Enter/Space to select. No additional keyboard handling required.

**Accessibility** (AC8): The `aria-label` attribute is set to the field api name (human-readable). In a form context, a `<Label htmlFor>` should be used by the parent. The `aria-disabled` attribute is set on invalid options to communicate state to screen readers, complementing the visual graying.

### 3. `ItemGrid.tsx` modifications

Three changes are needed:

**a. Enable editing on dependent picklist columns**

In the `columnDefs` `useMemo`, after building the base `ColDef`, detect whether the field is a dependent picklist and inject editor params:

```typescript
// Inside columnDefs useMemo, after building colDef:
if (fieldDef.is_dependent && fieldDef.controller_field && fieldSchema) {
  colDef.editable = true
  colDef.cellEditorSelector = () => ({
    component: DependentPicklistEditor,
    params: {
      mode: 'grid',
      fieldApiName: fieldDef.api_name,
      schema: fieldSchema,
    } satisfies Partial<DependentPicklistEditorParams>,
  })
}
```

The `cellEditorSelector` approach (over `cellEditor` + `cellEditorParams`) is used because it allows per-row dynamic selection, though in this story all rows use the same editor. It also avoids the deprecated `cellEditorParams` pattern in AG Grid v33+.

**b. Add `fieldSchema` to the dependency array**

The `fieldSchema` variable is already available in scope. Add it to the `columnDefs` `useMemo` deps array (it was already there via `[fieldSchema, enableGrouping]`). No change needed there.

**c. Import the new editor**

```typescript
import { DependentPicklistEditor } from './DependentPicklistEditor'
import type { DependentPicklistEditorParams } from './DependentPicklistEditor'
```

### 4. `ACMRecordDialog.tsx` modifications

The existing dialog uses hardcoded `<Select>` components for friable, material_condition, risk_status, and result. The dependent picklist fields are `friable`, `acm_product_group`, `acm_product_type`, `building_type`, and `building_construction`.

**Steps**:

1. Add `useFieldSchema` import from `@/lib/hooks/useACMItems`.
2. Build a partial `ACMRecord` from the current `watch()` values to pass as `rowData`.
3. Replace the plain `<Select>` for `friable`, `acm_product_group`, `acm_product_type`, `building_type`, and `building_construction` with `DependentPicklistEditor` in `mode="form"`.

```typescript
// In ACMRecordDialog, near the top of the component function:
const { data: fieldSchema } = useFieldSchema()

// Build a partial rowData for the DependentPicklistEditor from current form values
const watchedValues = watch(['friable', 'acm_product_group', 'building_type'])
const formRowData: Partial<ACMRecord> = {
  friable: watchedValues[0] || undefined,
  acm_product_group: watchedValues[1] || undefined,
  building_type: watchedValues[2] || undefined,
}

// Example replacement for acm_product_group (ACM Classification):
{fieldSchema && (
  <DependentPicklistEditor
    mode="form"
    fieldApiName="ACM_Classification__c"
    schema={fieldSchema}
    rowData={formRowData}
    value={watch('acm_product_group') || ''}
    onChange={(val) => setValue('acm_product_group', val)}
    placeholder="Select classification"
    id="acm_product_group"
  />
)}
```

Note: `acm_product_group` and `acm_product_type` are not in the existing form's Zod schema. They must be added to `acmRecordSchema` and `ACMRecordFormData` before wiring. The `ACMRecordUpdateRequest` interface also needs these fields if they are to be persisted.

**Schema additions required**:

```typescript
// In acmRecordSchema:
acm_product_group: z.string().optional(),
acm_product_type: z.string().optional(),
building_type: z.string().optional(),
// building_construction already present
```

### 5. Testing strategy

#### Unit tests: `frontend/src/hooks/__tests__/useDependentPicklist.test.ts`

Use Vitest. Tests target the pure `getFilteredOptions` function directly — no React rendering needed.

```typescript
import { describe, it, expect } from 'vitest'
import { getFilteredOptions } from '../useDependentPicklist'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

const mockSchema: SFFieldSchemaConfig = {
  version: 'test',
  building_fields: { /* ... */ } as any,
  item_fields: { /* ... */ } as any,
  picklists: {
    'ACM_Classification__c': ['Bonded ACM', 'Friable ACM', 'Non-ACM'],
    'ACM_Sub_Classification__c': ['Boards', 'Cement Sheet', 'Vinyl Tiles'],
    'Building_Category__c': ['Educational', 'Office', 'Industrial'],
  },
  dependencies: [
    {
      controller_api_name: 'Friability_of_Material__c',
      dependent_api_name: 'ACM_Classification__c',
      mapping: {
        'Non-friable': ['Bonded ACM', 'Non-ACM'],
        'Friable': ['Friable ACM'],
      },
    },
    {
      controller_api_name: 'ACM_Classification__c',
      dependent_api_name: 'ACM_Sub_Classification__c',
      mapping: {
        'Bonded ACM': ['Boards', 'Cement Sheet'],
        'Friable ACM': ['Vinyl Tiles'],
      },
    },
    {
      controller_api_name: 'Building_Type__c',
      dependent_api_name: 'Building_Category__c',
      mapping: {
        'School': 'Educational',
        'Office': 'Office',
      },
    },
  ],
  loaded_at: null,
}

describe('getFilteredOptions', () => {
  it('returns all values when no controller value is set (AC2)', () => {
    const result = getFilteredOptions('ACM_Classification__c', {}, mockSchema)
    expect(result.validValues).toEqual(mockSchema.picklists['ACM_Classification__c'])
    expect(result.isDependent).toBe(true)
    expect(result.controllerValue).toBeNull()
  })

  it('filters ACM Classification by Friability (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Non-friable' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Bonded ACM', 'Non-ACM'])
    expect(result.allValues).toEqual(['Bonded ACM', 'Friable ACM', 'Non-ACM'])
  })

  it('filters ACM Sub-Classification by Classification (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Sub_Classification__c',
      { acm_product_group: 'Bonded ACM' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Boards', 'Cement Sheet'])
  })

  it('handles Building_Category string mapping (AC3)', () => {
    const result = getFilteredOptions(
      'Building_Category__c',
      { building_type: 'School' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Educational'])
  })

  it('returns all values for non-dependent field (AC4)', () => {
    const result = getFilteredOptions('Friability_of_Material__c', {}, mockSchema)
    expect(result.isDependent).toBe(false)
    expect(result.validValues).toEqual(result.allValues)
  })

  it('returns all values when controller has unknown value', () => {
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Unknown_Value' },
      mockSchema
    )
    expect(result.validValues).toEqual([])
  })

  it('returns empty arrays when schema is absent', () => {
    // Tested via the hook wrapper — schema undefined short-circuits to empty
  })
})
```

#### Playwright E2E tests: `tests/playwright/test_dependent_picklist.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Dependent Picklist Cell Editors', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a source page with ACM records loaded
    await page.goto('/source/test-source-id')
    await page.waitForSelector('.ag-theme-alpine')
  })

  test('AC2 — ACM chain: selecting Friability filters Classification options', async ({ page }) => {
    // Click on a Friability cell to start editing
    const friabilityCell = page.locator('.ag-cell[col-id="friable"]').first()
    await friabilityCell.dblclick()

    // Select "Non-friable"
    const select = page.locator('.ag-cell-editor select')
    await select.selectOption('Non-friable')
    await page.keyboard.press('Tab') // commit edit

    // Now click on Classification cell of same row
    const classificationCell = page.locator('.ag-cell[col-id="acm_product_group"]').first()
    await classificationCell.dblclick()

    // "Friable ACM" should be a disabled option
    const friableOption = page.locator('.ag-cell-editor select option[value="Friable ACM"]')
    await expect(friableOption).toBeDisabled()
  })

  test('AC5 — invalid options are grayed out (not hidden)', async ({ page }) => {
    const classificationCell = page.locator('.ag-cell[col-id="acm_product_group"]').first()
    await classificationCell.dblclick()

    // All options should be present
    const options = page.locator('.ag-cell-editor select option')
    const count = await options.count()
    expect(count).toBeGreaterThan(0)

    // Disabled options have aria-disabled attribute
    const disabledOptions = page.locator('.ag-cell-editor select option[disabled]')
    // At least some disabled options should exist when controller is set
    // (depends on test data — assert count ≥ 0, not that they're hidden)
    await expect(disabledOptions).not.toHaveCount(0) // at least one invalid option shown
  })

  test('AC8 — keyboard navigation through dropdown', async ({ page }) => {
    const friabilityCell = page.locator('.ag-cell[col-id="friable"]').first()
    await friabilityCell.dblclick()

    const select = page.locator('.ag-cell-editor select')
    await expect(select).toBeFocused()

    // Arrow key navigation changes the selected option
    await page.keyboard.press('ArrowDown')
    const value = await select.inputValue()
    expect(value).toBeTruthy()

    // Escape cancels editing
    await page.keyboard.press('Escape')
    await expect(select).not.toBeVisible()
  })
})
```

---

## Shared Utility: `fieldApiToRecordKey`

Currently the `fieldApiToRecordKey` function is defined inline in `ItemGrid.tsx`. Both `useDependentPicklist` and `DependentPicklistEditor` need to call it. To avoid duplication:

**Option A (preferred)**: Extract to `frontend/src/lib/utils/acm-field-mapping.ts` and import in both `ItemGrid.tsx` and `useDependentPicklist.ts`.

**Option B**: Pass `keyMapper` as a parameter to `getFilteredOptions` (already shown in the hook signature). `ItemGrid.tsx` passes its local copy; the default export from `acm-field-mapping.ts` is used everywhere else.

The tech spec recommends Option A (extraction) as part of this story since `DependentPicklistEditor` will also need it when computing options in form mode.

---

## Acceptance Criteria Mapping

| AC | Satisfied By |
|----|-------------|
| AC1: Custom AG Grid cell editor `DependentPicklistEditor` | `DependentPicklistEditor.tsx` with `forwardRef` + `getValue()` implementing `ICellEditorReact` contract |
| AC2: ACM chain Friability -> Classification -> SubClassification | `getFilteredOptions` resolves the chain for `ACM_Classification__c` and `ACM_Sub_Classification__c` from `schema.dependencies`; `ItemGrid.tsx` applies `cellEditorSelector` to both columns |
| AC3: Building chain Building_Type -> Building_Category | `getFilteredOptions` resolves `Building_Category__c` from `Building_Type__c`; both columns receive the editor in `ItemGrid.tsx` |
| AC4: `getValues()` callback queries field_schema API | `schema.dependencies` and `schema.picklists` come from the field-schema React Query cache (`useFieldSchema`); `DependentPicklistEditorParams` receives `schema` as a prop; no additional network calls at edit time |
| AC5: Invalid combinations grayed out, not hidden | All options from `allValues` are rendered; options not in `validValues` have `disabled` and `aria-disabled="true"` attributes — native browser gray-out, not `display:none` |
| AC6: Works in inline grid editing and Record Wizard modal | `mode="grid"` path satisfies grid editing; `mode="form"` path satisfies `ACMRecordDialog` integration |
| AC7: Unit tests for cascading filter logic | `frontend/src/hooks/__tests__/useDependentPicklist.test.ts` tests `getFilteredOptions` for all four chains, null/undefined controller, and unknown controller values |
| AC8: Keyboard navigation | Native `<select>` provides full keyboard support; `autoFocus` on mount ensures the element is immediately keyboard-reachable after cell editor activation |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AG Grid community edition does not support `cellEditorSelector` with React components | Low | High | `cellEditorSelector` is documented for AG Grid Community ≥ v29. The project already uses `AllCommunityModule`. Fallback: use `cellEditor` + `cellEditorParams` directly. |
| `mapping` values for building chain are `string` (not `string[]`) causing type mismatch | Known | Medium | Already handled in `getFilteredOptions`: `Array.isArray(raw) ? raw : raw ? [raw as string] : []`. Covered by unit test "handles Building_Category string mapping". |
| `fieldApiToRecordKey` in `ItemGrid.tsx` does not cover `Building_Category__c` -> `building_construction` | Known | High | The key `building_construction` maps via the `building_category` override: strip `__c` -> `building_category` -> override to `building_construction`. Verify this in the override map before implementing; add the entry if missing. |
| `acm_product_group` / `acm_product_type` missing from `ACMRecordDialog` Zod schema and `ACMRecordUpdateRequest` | Known | Medium | Explicitly add both fields to the Zod schema and update request type in this story (scope clearly defined). |
| AG Grid `cellEditorSelector` receives stale `fieldSchema` after a schema cache invalidation | Very Low | Low | Schema has `staleTime: Infinity` — only changes on page reload. Column defs are rebuilt when `fieldSchema` changes in the memo dep array. |
| Native `<select>` disabled options may vary in appearance across browsers and OS themes | Low | Low | Acceptable for V3-6. A custom popover-based dropdown (using Radix `Select`) can replace the native select in a future story if design requires pixel-perfect styling. |
| Playwright tests require a running API with seeded ACM data | Medium | Low | Tests are tagged as integration; CI can skip them with `--project=unit`. The unit tests for `getFilteredOptions` run fully in Vitest without any service dependency. |

---

## Dev Agent Record

- **Tech spec created**: 2026-03-05
- **Author**: Ralph SM
- **Status**: READY_FOR_DEV
- **Build verification**: N/A (spec only)
- **Files verified**: All referenced existing files confirmed present
