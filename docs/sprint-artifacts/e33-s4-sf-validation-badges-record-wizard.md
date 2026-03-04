# E33-S4: SF Validation Badges + Record Wizard

## Story

**ID**: E33-S4
**Title**: SF Validation Badges + Record Wizard
**Sprint**: V3-6
**Story Points**: 3
**Risk**: MEDIUM
**Type**: Frontend + Minor Backend
**Dependencies**: E33-S2 (Building Grid + Item Grid), E33-S3 (Dependent Picklist Cell Editors), E30-S4 (Dependent Picklist Validator)

### Acceptance Criteria

- AC1: Inline validation badges in AG Grid cells: red (invalid), orange (dependency chain violation), yellow (warning/low confidence)
- AC2: Badge tooltip shows specific error message
- AC3: Record wizard modal for editing from row double-click or Edit button
- AC4: Wizard shows all fields with SF picklist dropdowns and dependency chain guidance
- AC5: Bulk "Fix All" operation for common issues
- AC6: Validation error count shown in building sidebar badge
- AC7: Export button disabled with "X validation errors" tooltip when errors exist
- AC8: Unit tests for badge rendering and wizard field validation

---

## Overview

This story adds SF validation awareness to the ACM register UI. Records returned by the API already have `validation_status` and `validation_errors` from the extraction pipeline (E32-S3/E32-S7), but these fields are not yet exposed in the API response model or the frontend types. This story:

1. Exposes `validation_status` and `validation_errors` in the API response model (minor backend change)
2. Adds `ValidationBadge` cell renderer to AG Grid cells showing red/orange/yellow indicators
3. Builds a `RecordWizard` modal for editing individual records with full SF picklist support
4. Adds validation error count badges to the building sidebar
5. Blocks export when validation errors exist

---

## Technical Design

### Architecture

```
ACMRecordResponse (API) ──── validation_status, validation_errors ────┐
                                                                       │
                                     ┌─────────────────────────────────┤
                                     ▼                                 ▼
                          ValidationBadge.tsx                  RecordWizard.tsx
                          (AG Grid cellRenderer)              (Radix Dialog modal)
                                     │                                 │
                                     ▼                                 ▼
                          ItemGrid.tsx (integration)           DependentPicklistEditor
                                                              (mode="form", from E33-S3)
```

### Validation Status Color Mapping

| `validation_status` | Color | Badge | Meaning |
|---------------------|-------|-------|---------|
| `"invalid"` | Red | Error | SF enum/required field violation |
| `"failed_correction"` | Red | Error | Correction attempted but failed |
| `"corrected"` | Orange | Warning | Was invalid, auto-corrected (review recommended) |
| `null` (low confidence) | Yellow | Caution | `extraction_confidence === "low"` |
| `"valid"` | None | - | No badge shown |
| `null` (not low conf) | None | - | Not yet validated |

### Data Flow

1. API returns `validation_status` and `validation_errors` per record
2. `ItemGrid` passes records to AG Grid with `ValidationBadge` cell renderer on all editable columns
3. `ValidationBadge` checks if the current cell's field name appears in `validation_errors`
4. Building sidebar counts total validation errors across all records for each building
5. Export button checks aggregate error count

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `api/models.py` | Modify | Add `validation_status`, `validation_errors` to `ACMRecordResponse` |
| `frontend/src/lib/types/acm.ts` | Modify | Add `validation_status`, `validation_errors` to `ACMRecord` interface |
| `frontend/src/components/acm/ValidationBadge.tsx` | Create | AG Grid cell renderer showing red/orange/yellow validation badges with tooltips |
| `frontend/src/components/acm/RecordWizard.tsx` | Create | Radix Dialog modal for editing a single ACM record with SF picklist dropdowns |
| `frontend/src/components/acm/ItemGrid.tsx` | Modify | Integrate ValidationBadge renderer, add row double-click handler for wizard, add export button with validation guard |
| `frontend/src/components/acm/BuildingSidebar.tsx` | Modify | Add validation error count badge per building |
| `frontend/src/lib/hooks/useACMItems.ts` | Modify | Add `useUpdateACMRecord` mutation hook, add `useBulkFixRecords` mutation |
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | Modify | Add export button with validation error guard to top bar |
| `frontend/src/lib/api/acm.ts` | Modify | Add `bulkFix` API method (if backend endpoint exists, else client-side) |
| `frontend/src/__tests__/ValidationBadge.test.tsx` | Create | Unit tests for badge rendering |
| `frontend/src/__tests__/RecordWizard.test.tsx` | Create | Unit tests for wizard field validation |

---

## Component Specifications

### ValidationBadge (`ValidationBadge.tsx`)

Custom AG Grid cell renderer that wraps cell values with validation indicators.

```tsx
interface ValidationBadgeProps {
  value: unknown                    // Cell value from AG Grid
  data: ACMRecord                   // Full row data
  colDef: ColDef                    // Column definition (for field name)
}
```

**Behavior:**
- Reads `data.validation_status` and `data.validation_errors` from row data
- Checks if the current column's field name appears in any `validation_errors` entry
- Renders a colored dot/icon next to the cell value
- Tooltip (via `title` attribute or Radix Tooltip) shows the specific error message
- Color logic per the mapping table above

**Implementation approach:** Use as `cellRenderer` on all data columns (not group columns). The renderer checks if the cell's field has an error; if not, it renders the value plain.

### RecordWizard (`RecordWizard.tsx`)

Modal dialog for editing a single ACM record.

```tsx
interface RecordWizardProps {
  record: ACMRecord | null          // Record to edit (null = closed)
  onClose: () => void
  onSave: (updated: ACMRecordUpdateRequest) => void
  schema: SFFieldSchemaConfig       // For picklist dropdowns
  sourceId: string
}
```

**Behavior:**
- Opens on row double-click or "Edit" context action in AG Grid
- Displays all editable fields in a scrollable form
- Dependent picklist fields use `DependentPicklistEditor` in `mode="form"` (from E33-S3)
- Non-picklist fields use standard `<Input>` components
- Shows validation errors inline next to invalid fields (red text)
- Save button calls `PUT /api/acm/records/{id}` via React Query mutation
- Cancel button closes without saving

**Field layout:**
- Group fields by category: Location (building, room), Material (product, description, condition), Classification (friability, product group/type), Results (sample, risk)
- Each field shows: label, input/select, validation error (if any)

### BuildingSidebar Enhancement

Add a small badge showing validation error count next to each building:

```tsx
// In BuildingSidebar.tsx, after record_count display
{validationErrorCount > 0 && (
  <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
    {validationErrorCount} error{validationErrorCount !== 1 ? 's' : ''}
  </span>
)}
```

**Data source:** Need per-building validation counts. Options:
- **Option A (chosen):** Add a `GET /api/acm/validation-summary?source_id=X` endpoint returning `{ buildings: [{ building_id, error_count, warning_count }] }`
- **Option B:** Compute client-side from loaded records (only works when records are loaded)

We'll use **Option A** as it works without loading all records upfront. This requires a small backend addition.

### Bulk Fix All (AC5)

For common auto-fixable issues (e.g., enum normalization, case corrections):
- Button in the top bar: "Fix All (N issues)"
- Calls `POST /api/acm/bulk-fix?source_id=X&building_id=Y`
- Backend runs `validate_acm_record()` on each record and applies auto-corrections
- Returns count of fixed records
- React Query invalidates the items cache

If the backend endpoint doesn't exist yet, implement a lightweight version:
- Frontend sends batch `PUT` requests for records where `validation_status === "corrected"` to re-validate

---

## API Dependencies

### Existing Endpoints (no changes needed)
- `GET /api/acm/records?source_id=X&building_id=Y` — list records (add validation fields)
- `PUT /api/acm/records/{id}` — update a single record
- `GET /api/acm/field-schema` — SF field schema for picklist dropdowns

### New/Modified Endpoints

1. **Modify `ACMRecordResponse`** in `api/models.py`:
   ```python
   validation_status: Optional[str] = None  # "valid", "corrected", "failed_correction", "invalid"
   validation_errors: List[str] = Field(default_factory=list)
   ```

2. **New endpoint: `GET /api/acm/validation-summary`**:
   ```python
   @router.get("/validation-summary")
   async def get_validation_summary(source_id: str):
       # Query SurrealDB for count of records with validation_errors per building
       return { "buildings": [{ "building_id": "...", "error_count": N }] }
   ```

3. **New endpoint: `POST /api/acm/bulk-fix`**:
   ```python
   @router.post("/bulk-fix")
   async def bulk_fix_records(source_id: str, building_id: Optional[str] = None):
       # Re-validate and auto-correct fixable records
       return { "fixed_count": N, "remaining_errors": M }
   ```

---

## Testing Strategy

### Unit Tests (`frontend/src/__tests__/ValidationBadge.test.tsx`)
- Renders no badge when `validation_status === "valid"`
- Renders red badge when `validation_status === "invalid"`
- Renders orange badge when `validation_status === "corrected"`
- Renders yellow badge when `extraction_confidence === "low"`
- Tooltip shows error message from `validation_errors`
- Handles null/undefined validation fields gracefully

### Unit Tests (`frontend/src/__tests__/RecordWizard.test.tsx`)
- Renders all editable fields from record
- Shows validation error messages inline
- Dependent picklist fields render as selects
- Save button calls onSave with updated values
- Cancel button calls onClose
- Form validates required fields before save

### Integration (manual verification)
- Double-click row opens RecordWizard
- Edit a field, save, verify grid updates
- Building sidebar shows correct error counts
- Export button disabled when errors exist

---

## Edge Cases

1. **Records without validation data**: When `validation_status` is null and `validation_errors` is empty, show no badge. This is the normal state for records not yet re-validated.
2. **Many validation errors**: If a record has >5 errors, tooltip should show first 3 with "and N more..." suffix.
3. **Concurrent editing**: If another user fixes records while wizard is open, React Query refetch on save should show latest data.
4. **Empty building**: Buildings with 0 records should show no error badge.
5. **Schema loading**: If field schema hasn't loaded yet, RecordWizard should show a loading spinner for picklist fields.

---

## Out of Scope

- Chat-based record corrections (no V3 story exists)
- Per-field provenance in wizard (E33-S6 scope)
- Undo support for edits (E34-S2 scope)
- Building-level validation (only item-level)
- Custom validation rules beyond SF picklists and BAR business rules
