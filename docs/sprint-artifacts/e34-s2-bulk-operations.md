# E34-S2: Bulk Operations — Tech Spec

## Overview

Adds multi-select and bulk operation capabilities to the ACM Register UI. Users can select
multiple ACM item records via AG Grid checkboxes, then apply a field edit, re-run validation,
export selected buildings, or undo the last bulk edit. SSE progress events keep the UI
responsive during long-running bulk operations.

---

## Background / Context

### What Already Exists

| Component | Location | Status |
|-----------|----------|--------|
| `ItemGrid` | `frontend/src/components/acm/ItemGrid.tsx` | Done (E33-S2/E33-S6), single-select |
| `/api/v3/stream/bulk/{op_id}` | `api/routers/v3_streaming.py` | Done (E31-S7) |
| `useV3SSE` hook | `frontend/src/lib/hooks/useV3SSE.ts` | Done (E31-S7), `category:'bulk'` supported |
| `PipelineEventBus` | `open_notebook/extractors/pipeline_event_bus.py` | Done (E31-S7) |
| `POST /api/acm/bulk-fix` | `api/routers/acm.py` | Done (E33-S4), validates whole source |
| `GET /api/acm/export/csv` | `api/routers/acm.py` | Done, no building filter |
| `GET /api/acm/export/excel` | `api/routers/acm.py` | Done, no building filter |
| `buildingStore` | `frontend/src/lib/stores/buildingStore.ts` | Done (E33-S2, E34-S1) |
| `BulkFixResponse` | `api/models.py` | Done, reuse |

### Key Patterns

- AG Grid `rowSelection="multiple"` with `checkboxSelection: true` on first data column
- `useGridApi` ref pattern: get api via `onGridReady` callback
- `useV3SSE` with `category: 'bulk'` already handles `bulk.progress` / `bulk.complete`
- PipelineEventBus is already in-process — call `await bus.publish(...)` from async endpoint
- Undo stored purely on frontend as a snapshot ref; calls individual `PATCH /api/acm/records/{id}` (existing endpoint) to restore

---

## Implementation Plan

### Backend Changes

#### 1. Add `BulkEditRequest` / `BulkEditResponse` models to `api/models.py`

```python
class BulkEditRequest(BaseModel):
    """Body for POST /api/acm/bulk-edit."""
    record_ids: List[str]          # SurrealDB IDs, e.g. ["acm_record:abc"]
    field: str                      # ACMRecord field name (snake_case)
    value: Any                      # New value (string, None, etc.)
    operation_id: str               # Client-generated UUID for SSE tracking

class BulkEditResponse(BaseModel):
    updated_count: int
    operation_id: str

class BulkValidateRequest(BaseModel):
    """Body for POST /api/acm/bulk-validate."""
    record_ids: List[str]

class BulkValidateResponse(BaseModel):
    fixed_count: int
    remaining_errors: int
```

#### 2. New `POST /api/acm/bulk-edit` endpoint in `api/routers/acm.py`

```python
@router.post("/bulk-edit", response_model=BulkEditResponse)
async def bulk_edit_records(
    request: BulkEditRequest,
    source_id: str = Query(..., description="Source ID for SSE auth")
):
    """Set a single field to the same value on all specified records.

    Publishes bulk.progress events (one per record) and bulk.complete at end.
    """
    from open_notebook.extractors.pipeline_event_bus import get_event_bus
    import uuid

    bus = get_event_bus()
    total = len(request.record_ids)
    updated = 0

    for i, record_id in enumerate(request.record_ids):
        rid = ensure_record_id(record_id)
        await repo_query(
            f"UPDATE $rid SET {request.field} = $val, updated = time::now();",
            {"rid": rid, "val": request.value}
        )
        updated += 1

        # Publish progress event every record
        await bus.publish(V3PipelineEvent(
            type="bulk.progress",
            operation_id=request.operation_id,
            data={
                "processed": updated,
                "total": total,
                "percent": round((updated / total) * 100),
            }
        ))

    await bus.publish(V3PipelineEvent(
        type="bulk.complete",
        operation_id=request.operation_id,
        data={"updated_count": updated, "field": request.field}
    ))

    return BulkEditResponse(updated_count=updated, operation_id=request.operation_id)
```

#### 3. New `POST /api/acm/bulk-validate` endpoint

Works like existing `/bulk-fix` but accepts explicit `record_ids`:

```python
@router.post("/bulk-validate", response_model=BulkValidateResponse)
async def bulk_validate_records(request: BulkValidateRequest):
    """Re-run SF validation on the specified records only."""
    from open_notebook.extractors.validators.acm_validator import validate_acm_record

    fixed_count = 0
    for record_id in request.record_ids:
        rid = ensure_record_id(record_id)
        rows = await repo_query("SELECT * FROM $rid;", {"rid": rid})
        if not rows:
            continue
        record_dict = dict(rows[0])
        result = validate_acm_record(record_dict)

        if result.is_valid:
            await repo_query(
                "UPDATE $rid SET validation_status = 'valid', validation_errors = [], updated = time::now();",
                {"rid": rid}
            )
            fixed_count += 1
        else:
            await repo_query(
                "UPDATE $rid SET validation_status = 'invalid', validation_errors = $errors, updated = time::now();",
                {"rid": rid, "errors": [e.message for e in result.errors]}
            )

    remaining_rows = await repo_query(
        "SELECT count() as cnt FROM acm_record WHERE id IN $ids AND array::len(validation_errors) > 0 GROUP ALL;",
        {"ids": [ensure_record_id(r) for r in request.record_ids]}
    )
    remaining = remaining_rows[0].get("cnt", 0) if remaining_rows else 0

    return BulkValidateResponse(fixed_count=fixed_count, remaining_errors=remaining)
```

#### 4. Add `building_ids` filter to CSV and Excel export endpoints

Modify `export_acm_records` (CSV) and `export_acm_excel`:

```python
@router.get("/export/csv")
async def export_acm_records(
    source_id: str = Query(...),
    building_ids: Optional[List[str]] = Query(None, description="Filter to specific buildings"),
):
    records = await ACMRecord.get_by_source(source_id)
    if building_ids:
        records = [r for r in records if r.get("building_id") in building_ids]
    ...
```

Same pattern for `/export/excel`.

### Frontend Changes

#### 5. Add `selectedBuildingIds` to `buildingStore`

File: `frontend/src/lib/stores/buildingStore.ts`

```typescript
// Add to BuildingState:
selectedBuildingIds: Set<string>
toggleBuildingSelection: (id: string) => void
selectAllBuildings: (ids: string[]) => void
clearBuildingSelections: () => void
```

These track which buildings are selected for export (separate from `selectedBuildingId` which is the currently-viewed building).

#### 6. Create `BulkOperationsBar` component

File: `frontend/src/components/acm/BulkOperationsBar.tsx` (new)

```typescript
interface BulkOperationsBarProps {
  sourceId: string
  selectedRecords: ACMRecord[]
  onClearSelection: () => void
  onValidationRefresh: () => void   // invalidate query after validate
  schema: SFFieldSchemaConfig | null
}
```

UI layout:
```
┌────────────────────────────────────────────────────────────────────────────────┐
│ [✓] 12 records selected   [Validate]  [Field ▾][Value      ][Apply]  [Undo]  [×] │
└────────────────────────────────────────────────────────────────────────────────┘
      ← count area         ← validate  ← bulk edit form ──────────────────────→
```

Internal state:
- `editField: string | null` — selected field for bulk edit
- `editValue: string` — value to apply
- `isApplying: boolean` — loading state during bulk edit
- `operationId: string` — UUID generated per Apply click for SSE
- `undoSnapshot: { field: string; values: { id: string; oldValue: any }[] } | null`

Undo logic:
- Before calling bulk-edit, snapshot current values from `selectedRecords`
- After bulk-edit completes, show "Undo" button
- Undo: POST individual PATCH calls using existing `useUpdateACMRecord` mutation for each record

SSE progress:
- `useV3SSE({ operationId, category: 'bulk', enabled: isApplying })`
- Show progress: "Applying... 8/12 (67%)" during operation

Bulk validate:
- POST to `/api/acm/bulk-validate` with selected record IDs
- On success: call `onValidationRefresh()` to invalidate queries

Export selected buildings:
- Read `selectedBuildingIds` from `useBuildingStore()`
- If empty: show tooltip "Select buildings in sidebar first"
- Call `/api/acm/export/csv?source_id=X&building_ids=B1&building_ids=B2` (multi-value query param)

#### 7. Modify `ItemGrid` for multi-select + callback

File: `frontend/src/components/acm/ItemGrid.tsx`

Changes:
1. Add `onSelectionChanged?: (records: ACMRecord[]) => void` to `ItemGridProps`
2. Change `rowSelection="single"` → `rowSelection="multiple"`
3. Remove `suppressRowClickSelection={true}` (replaced by checkbox behavior)
4. Add `checkboxSelection: true` and `headerCheckboxSelection: true` to first pinned data column (`building_id` or dedicated checkbox col)
5. Add `onSelectionChanged` handler that calls `props.onSelectionChanged?.(api.getSelectedRows())`
6. Store grid api ref for programmatic select-all: `const gridApiRef = useRef<GridApi | null>(null)` set in `onGridReady`

"Select by building" = button in BulkOperationsBar: "Select All in View" that calls `gridApiRef.current?.selectAll()`. Exposed via `onSelectAll?: () => void` prop.

#### 8. Modify `/source/[id]` page

File: `frontend/src/app/(dashboard)/source/[id]/page.tsx`

- Add `selectedRecords: ACMRecord[]` state
- Pass `onSelectionChanged={(recs) => setSelectedRecords(recs)}` to `ItemGrid`
- Render `<BulkOperationsBar>` between the progress bar and the two-panel body when `selectedRecords.length > 0`
- Pass `schema={fieldSchema}` from `useFieldSchema()` to `BulkOperationsBar`

#### 9. Modify `BuildingSidebar` for building selection checkboxes

File: `frontend/src/components/acm/BuildingSidebar.tsx`

- Read `selectedBuildingIds`, `toggleBuildingSelection` from `useBuildingStore()`
- Add small checkbox to each building row (before the building name)
- Clicking checkbox calls `toggleBuildingSelection(building.internal_id)` without changing `selectedBuildingId`

#### 10. Add `useBulkEdit` and `useBulkValidate` hooks to `useACMItems.ts`

```typescript
export function useBulkEdit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (args: { sourceId: string; body: BulkEditRequest }) =>
      apiClient.post(`/api/acm/bulk-edit?source_id=${args.sourceId}`, args.body),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'items'] })
    },
  })
}

export function useBulkValidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: BulkValidateRequest) =>
      apiClient.post('/api/acm/bulk-validate', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'items'] })
      queryClient.invalidateQueries({ queryKey: ['acm', 'validation-summary'] })
    },
  })
}
```

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `api/models.py` | modify | Add `BulkEditRequest`, `BulkEditResponse`, `BulkValidateRequest`, `BulkValidateResponse` |
| `api/routers/acm.py` | modify | Add `POST /bulk-edit`, `POST /bulk-validate`; add `building_ids` filter to CSV+Excel export |
| `frontend/src/lib/stores/buildingStore.ts` | modify | Add `selectedBuildingIds`, `toggleBuildingSelection`, `selectAllBuildings`, `clearBuildingSelections` |
| `frontend/src/components/acm/BulkOperationsBar.tsx` | create | Bulk ops UI: count, edit form, validate, export selected, undo, SSE progress |
| `frontend/src/components/acm/ItemGrid.tsx` | modify | Multi-select checkboxes, `onSelectionChanged` callback, `gridApiRef` |
| `frontend/src/components/acm/BuildingSidebar.tsx` | modify | Building-level selection checkboxes for export |
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | modify | `selectedRecords` state, pass `onSelectionChanged` to grid, render `BulkOperationsBar` |
| `frontend/src/lib/hooks/useACMItems.ts` | modify | Add `useBulkEdit`, `useBulkValidate` mutation hooks |

---

## Acceptance Criteria Mapping

| AC | Implementation |
|----|----------------|
| AC1: Multi-select (checkbox, select all, select by building) | `rowSelection="multiple"` + `checkboxSelection`/`headerCheckboxSelection` in AG Grid; "Select All in View" button in BulkOperationsBar calls `gridApi.selectAll()`; building checkboxes in sidebar |
| AC2: Bulk edit a field value | `POST /api/acm/bulk-edit`; BulkOperationsBar field dropdown + value input + Apply |
| AC3: Bulk validate selected records | `POST /api/acm/bulk-validate` with selected IDs; "Validate" button in BulkOperationsBar |
| AC4: Bulk export selected buildings | Building checkboxes in sidebar tracked in `selectedBuildingIds`; export adds `building_ids` query params |
| AC5: SSE progress for bulk operations | `useV3SSE` with `category:'bulk'` in BulkOperationsBar; renders "Applying... N/M (X%)" |
| AC6: Undo support for bulk edits | Snapshot old values before Apply; show "Undo" button; undo POSTes old values via `useUpdateACMRecord` for each record |

---

## Test Plan

### Backend Tests

1. **`test_bulk_edit`** (`tests/test_acm_sf_alignment.py` or new file):
   - Mock `repo_query`; call `bulk_edit_records` with 3 record IDs, field `"material_condition"`, value `"Good"`
   - Assert `repo_query` called 3× with UPDATE and once final bulk.complete published
   - Assert `BulkEditResponse.updated_count == 3`

2. **`test_bulk_validate`**:
   - Mock `repo_query` to return records with validation errors; mock `validate_acm_record` to return `is_valid=True` for all
   - Assert `BulkValidateResponse.fixed_count == N` and UPDATE called for each

3. **`test_export_building_filter`**:
   - Call export_acm_records with `building_ids=["BLD001"]`; assert only records with `building_id="BLD001"` are returned

### Frontend Tests

1. **`buildingStore` selection actions**: Test `toggleBuildingSelection` adds/removes IDs, `selectAllBuildings` sets all, `clearBuildingSelections` empties.

2. **`BulkOperationsBar` renders**: Mount with 3 selected records and schema. Assert count "3 records selected" shown, Apply button disabled until field+value selected.

3. **`ItemGrid` selection callback**: Verify `onSelectionChanged` prop is called when rows are selected (mock AG Grid).

4. **Build verification**: `cd frontend && npm run build` must pass — no TypeScript errors.

---

## Notes / Risks

- **Risk 1 (LOW)**: `headerCheckboxSelection: true` requires AG Grid Community — already registered via `AllCommunityModule`.
- **Risk 2 (LOW)**: Building-level checkboxes use `internal_id` (e.g. `BLD#001`) for `building_ids` export filter. The export filter matches `record.building_id` which stores the same value.
- **Risk 3 (LOW)**: Undo is one-level only — the snapshot is replaced on each Apply. This is acceptable for 2 SP scope.
- **Risk 4 (LOW)**: `POST /api/acm/bulk-edit` field name must be a valid ACMRecord field. No server-side validation added in this story (out of scope); field validation happens at extraction time.
- **Risk 5 (LOW)**: For undo with large selections (100+), individual PATCH calls may be slow — acceptable for the scope. A batch undo endpoint can be added in a later story.
