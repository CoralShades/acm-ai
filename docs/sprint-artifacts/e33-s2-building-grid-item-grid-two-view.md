# Story: E33-S2 — Building Grid + Item Grid (Two-View)

## Status
- Sprint: V3-3
- Story Points: 5
- Risk: HIGH
- Type: frontend
- Dependencies: GATE:SCHEMA_FREEZE (unlocked), E30-S2 (done)

---

## User Story

As an ACM compliance reviewer, I want a dedicated full-page two-panel view at `/source/:id` where I can select a building from a sidebar and immediately see all of its ACM items in a rich AG Grid — so that I can navigate, filter, and assess risk across the register without switching between wizard steps.

---

## Acceptance Criteria

1. **AC1**: Building list sidebar displays: building name, internal ID (`BLD#NNN`), record count, and a validation status badge (Complete / Incomplete / Unknown).
2. **AC2**: Clicking a building in the sidebar loads its ACM items into the main AG Grid.
3. **AC3**: AG Grid columns are generated dynamically from the `GET /api/acm/field-schema` endpoint (`item_fields.fields`), using SF `label` as column headers.
4. **AC4**: Sidebar detail section shows selected `BuildingRecord` metadata (address, type, year, levels, etc.) beneath the building list.
5. **AC5**: AG Grid rows display `ACMRecord` data including product, room/location, result, condition, friable, risk status, and all other record fields.
6. **AC6**: Column sorting, column filtering, and quick text search are functional across the grid.
7. **AC7**: Row grouping by room/area (`room_id` + `room_name`) is available and can be toggled via a toolbar button.
8. **AC8**: Risk status cells are color-coded: Low = green (`text-green-600 bg-green-50`), Medium = yellow (`text-yellow-600 bg-yellow-50`), High = red (`text-red-600 bg-red-50`).
9. **AC9**: Building and Room columns are pinned left so they remain visible during horizontal scroll.
10. **AC10**: A Zustand store (`buildingStore`) holds `selectedBuildingId`; React Query hooks (`useBuildings`, `useACMItems`) handle all data fetching with proper caching.
11. **AC11**: The page is reachable at URL `/source/:id`, implemented as `frontend/src/app/(dashboard)/source/[id]/page.tsx`.
12. **AC12**: TypeScript interfaces `BuildingRecord` and `ACMRecord` (V3 shape) are defined in `frontend/src/lib/types/building.ts`; `ACMRecord` re-exports from `frontend/src/lib/types/acm.ts` with no duplication.
13. **AC13**: When no buildings have been extracted, the sidebar shows an empty state: "No buildings extracted yet" with a secondary link to run extraction.

---

## Technical Design

### 1. Route and Layout

The dashboard layout (`frontend/src/app/(dashboard)/layout.tsx`) wraps all children with auth guards, `ErrorBoundary`, `CopilotProvider`, `CreateDialogsProvider`, `ModalProvider`, `CommandPalette`, and `NavigationProgress`. It does **not** include `AppShell` — that is added per-page. The new page must explicitly include `<AppShell>` just like the existing `/jobs/[id]/review/buildings/page.tsx` does.

**Route file**: `frontend/src/app/(dashboard)/source/[id]/page.tsx`
**URL**: `/source/:id` (the `(dashboard)` route group adds no URL segments)

Note: a pre-existing page at `frontend/src/app/(dashboard)/sources/[id]/page.tsx` (plural "sources") is the old source detail tab page and is **not** modified by this story. The new page uses singular `source` to provide the dedicated ACM two-view experience.

### 2. Component Architecture

```
SourceACMPage                            (page.tsx — async Next.js params via use())
├── <AppShell>
│   └── <ErrorBoundary>
│       └── <SourceACMViewContent sourceId={sourceId}>
│           ├── Header bar (source name, breadcrumb, search input)
│           └── <div className="flex h-[calc(100vh-Xpx)] overflow-hidden">
│               ├── <BuildingSidebar sourceId={sourceId}>       (left panel, w-72)
│               │   ├── Building list items (name, internal_id, record count, badge)
│               │   └── BuildingDetailPanel (selected building metadata)
│               └── <ItemGrid sourceId={sourceId}>             (right panel, flex-1)
│                   ├── Toolbar (grouping toggle, search, record count)
│                   └── <AgGridReact ...>
```

### 3. Data Flow

```
User lands on /source/:id
  └─> useBuildings(sourceId)         → GET /api/acm/buildings?source_id={id}
        → renders BuildingSidebar

User clicks a building
  └─> buildingStore.setSelectedBuilding(id)
        └─> useACMItems(sourceId, selectedBuildingId)  → GET /api/acm/records?source_id={id}&building_id={bldId}&limit=500
        └─> useFieldSchema()          → GET /api/acm/field-schema  (cached, staleTime=Infinity for session)
              → builds ColDef[] from item_fields.fields
              → renders ItemGrid
```

### 4. Zustand Store — `buildingStore.ts`

The `frontend/src/stores/` directory does not yet exist and must be created.

```typescript
// frontend/src/stores/buildingStore.ts
import { create } from 'zustand'

interface BuildingStoreState {
  selectedBuildingId: string | null
  setSelectedBuilding: (id: string | null) => void
}

export const useBuildingStore = create<BuildingStoreState>((set) => ({
  selectedBuildingId: null,
  setSelectedBuilding: (id) => set({ selectedBuildingId: id }),
}))
```

### 5. TypeScript Interfaces — `building.ts`

`BuildingRecord` currently exists only inside `BuildingReviewGrid.tsx` as a component-local interface. The new file consolidates the V3 shape (from `BuildingRecordResponse` in `api/models.py`) and exports it for shared use.

`ACMRecord` already exists in `frontend/src/lib/types/acm.ts`. Do **not** re-declare it in `building.ts`; import and re-export it if needed, or import directly from `acm.ts` in components.

```typescript
// frontend/src/lib/types/building.ts

/**
 * V3 BuildingRecord — matches BuildingRecordResponse from api/models.py (E30-S2).
 * internal_id pattern: BLD#{source_short}_{seq:03d}
 */
export interface BuildingRecord {
  id: string
  internal_id: string               // BLD#NNN identifier shown in sidebar
  source_id: string
  building_code: string | null
  building_name: string | null
  building_year: string | null
  building_construction: string | null
  building_address: string | null
  suburb: string | null
  postcode: string | null
  building_type: string | null
  building_category: string | null
  building_address_lga: string | null
  building_address_region: string | null
  roof_type: string | null
  number_of_levels: number | null
  est_building_size_m2: number | null
  frequency_of_use: string | null
  daily_duration: string | null
  level_of_activity: string | null
  public_access: string | null
  mobile_plant: string | null
  owned_or_leased: string | null
  asbestos_register_available: string | null
  audit_report_available: string | null
  date_of_audit_report: string | null
  no_identified_acms: number | null
  no_identified_acms_note: string | null
  site_name: string | null
  school_uid: string | null
  building_unique_id: string | null
  external_id: string | null
  building_out_of_scope: boolean | null
  building_out_of_scope_comments: string | null
  demolished_status: string | null
  demolition_date: string | null
  demolition_type: string | null
  demolition_comments: string | null
  additional_comments: string | null
  within_your_portfolio: string | null
  psb_district_region: string | null
  state: string | null
  country: string | null
  gps_coordinates: string | null
  capital_works_project_details: string | null
  possible_capital_works_project: string | null
  created: string | null
  updated: string | null
}

export interface BuildingListResponse {
  buildings: BuildingRecord[]
  total: number
}

/** Validation status derived from building completeness — computed client-side */
export type BuildingValidationStatus = 'complete' | 'incomplete' | 'unknown'

/** Derived summary shown in sidebar list items */
export interface BuildingSummary {
  building: BuildingRecord
  recordCount: number
  validationStatus: BuildingValidationStatus
}
```

### 6. API Client Extensions — `acm.ts`

Add two new methods to the existing `acmApi` object in `frontend/src/lib/api/acm.ts`:

```typescript
// Append to acmApi in frontend/src/lib/api/acm.ts

import type { BuildingListResponse } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

// Inside acmApi object:
listBuildings: async (sourceId: string): Promise<BuildingListResponse> => {
  const response = await apiClient.get<BuildingListResponse>('/acm/buildings', {
    params: { source_id: sourceId },
  })
  return response.data
},

getFieldSchema: async (): Promise<SFFieldSchemaConfig> => {
  const response = await apiClient.get<SFFieldSchemaConfig>('/acm/field-schema')
  return response.data
},
```

A minimal TypeScript type for the field schema response must also be defined in `frontend/src/lib/types/sf-schema.ts` (new file):

```typescript
// frontend/src/lib/types/sf-schema.ts
export interface SFFieldDef {
  api_name: string
  label: string
  field_type: string
  length: number | null
  nillable: boolean
  custom: boolean
  calc: boolean
  updateable: boolean
  notes: string | null
  is_restricted_picklist: boolean
  is_dependent: boolean
  controller_field: string | null
}

export interface SFFieldSchemaObject {
  object_name: string
  object_label: string
  total_fields: number
  custom_fields: number
  picklist_fields: number
  fields: SFFieldDef[]
  picklists: Record<string, string[]>
  version: string
}

export interface SFFieldSchemaConfig {
  version: string
  building_fields: SFFieldSchemaObject
  item_fields: SFFieldSchemaObject
  picklists: Record<string, string[]>
  dependencies: Array<{
    controller_api_name: string
    dependent_api_name: string
    mapping: Record<string, unknown>
  }>
  loaded_at: string | null
}
```

### 7. React Query Hooks

Located in `frontend/src/lib/hooks/` (consistent with existing `use-acm.ts` pattern).

**`useBuildings.ts`**

```typescript
// frontend/src/lib/hooks/useBuildings.ts
import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

export const BUILDING_QUERY_KEYS = {
  list: (sourceId: string) => ['buildings', 'v3', sourceId] as const,
}

export function useBuildings(sourceId: string) {
  return useQuery({
    queryKey: BUILDING_QUERY_KEYS.list(sourceId),
    queryFn: () => acmApi.listBuildings(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  })
}
```

**`useACMItems.ts`**

```typescript
// frontend/src/lib/hooks/useACMItems.ts
import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

export const ACM_ITEMS_QUERY_KEYS = {
  byBuilding: (sourceId: string, buildingId: string | null) =>
    ['acm', 'items', sourceId, buildingId] as const,
  fieldSchema: () => ['acm', 'field-schema'] as const,
}

export function useACMItems(sourceId: string, buildingId: string | null) {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.byBuilding(sourceId, buildingId),
    queryFn: () =>
      acmApi.list({ source_id: sourceId, building_id: buildingId ?? undefined, limit: 500 }),
    enabled: !!sourceId && !!buildingId,
    staleTime: 30 * 1000,
  })
}

export function useFieldSchema() {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.fieldSchema(),
    queryFn: () => acmApi.getFieldSchema(),
    staleTime: Infinity,   // schema is session-stable
  })
}
```

### 8. ItemGrid — Column Generation from Field Schema

The `ItemGrid` component generates `ColDef[]` dynamically from `item_fields.fields` returned by the field schema API. Two columns (`Building_Code__c` / `building_code` and `room_id`) are always pinned left regardless of schema order.

```typescript
// Inside ItemGrid.tsx — useMemo for colDefs
const columnDefs = useMemo<ColDef<ACMRecord>[]>(() => {
  if (!fieldSchema) return []

  const pinnedLeft = new Set(['building_code', 'room_id', 'room_name'])
  const RISK_FIELD = 'risk_status'

  return fieldSchema.item_fields.fields.map((fieldDef): ColDef<ACMRecord> => {
    const key = fieldDef.api_name as keyof ACMRecord
    const colDef: ColDef<ACMRecord> = {
      field: key,
      headerName: fieldDef.label,
      sortable: true,
      filter: true,
      resizable: true,
      ...(pinnedLeft.has(String(key)) && { pinned: 'left' as const, width: 160 }),
    }

    // Risk status color renderer
    if (String(key) === RISK_FIELD) {
      colDef.cellRenderer = RiskStatusRenderer
      colDef.width = 110
    }

    return colDef
  })
}, [fieldSchema])
```

### 9. Risk Status Cell Renderer

```typescript
function RiskStatusRenderer({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-muted-foreground">-</span>

  const colorMap: Record<string, string> = {
    Low: 'text-green-600 bg-green-50 dark:bg-green-950/30',
    Medium: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/30',
    High: 'text-red-600 bg-red-50 dark:bg-red-950/30',
  }
  const classes = colorMap[value] ?? 'text-muted-foreground'

  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${classes}`}>
      {value}
    </span>
  )
}
```

### 10. BuildingSidebar — Validation Status Badge Logic

Validation status is computed client-side from the `BuildingRecord` fields. A building is considered "complete" if it has both `building_name` and `building_address` populated. Extend this heuristic as schema requirements become known.

```typescript
function deriveValidationStatus(b: BuildingRecord): BuildingValidationStatus {
  if (!b.building_name && !b.building_address) return 'unknown'
  if (b.building_name && b.building_address) return 'complete'
  return 'incomplete'
}
```

Badge colors:
- `complete`: `bg-green-100 text-green-800`
- `incomplete`: `bg-yellow-100 text-yellow-800`
- `unknown`: `bg-gray-100 text-gray-600`

### 11. AG Grid Configuration

Following the established pattern in `ACMGrid.tsx`:

```typescript
ModuleRegistry.registerModules([AllCommunityModule])

<AgGridReact
  theme="legacy"                    // ag-theme-alpine CSS compat
  rowData={records}
  columnDefs={columnDefs}
  defaultColDef={{ resizable: true, suppressMenu: true }}
  loading={isLoading}
  animateRows={true}
  rowSelection="single"
  suppressRowClickSelection={true}
  pagination={true}
  paginationPageSize={100}
  paginationPageSizeSelector={[50, 100, 250]}
  quickFilterText={quickFilterText}
  domLayout="normal"
  alwaysShowHorizontalScroll={true}
  // Grouping (toggled by toolbar)
  {...(enableGrouping ? {
    groupDisplayType: 'groupRows',
    groupDefaultExpanded: 1,
    autoGroupColumnDef: { headerName: 'Room / Area', minWidth: 260 },
  } : {})}
/>
```

The CSS vars block (dark mode theming) must be included with `<style jsx global>` exactly as in `ACMGrid.tsx`.

### 12. Page Layout — Full Height Two-Panel

```typescript
// frontend/src/app/(dashboard)/source/[id]/page.tsx
'use client'

export default function SourceACMPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Source ACM View" reloadUrl="/sources" />
      )}
    >
      <SourceACMViewContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}

function SourceACMViewContent({ sourceId }: { sourceId: string }) {
  const [quickFilter, setQuickFilter] = useState('')
  const [enableGrouping, setEnableGrouping] = useState(false)
  const { selectedBuildingId } = useBuildingStore()

  return (
    <AppShell>
      <div className="flex flex-col h-screen overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
          <h1 className="text-lg font-semibold truncate">ACM Register</h1>
          <div className="ml-auto flex items-center gap-2">
            <Input
              placeholder="Search records..."
              value={quickFilter}
              onChange={(e) => setQuickFilter(e.target.value)}
              className="w-60"
            />
            <Button
              variant={enableGrouping ? 'default' : 'outline'}
              size="sm"
              onClick={() => setEnableGrouping((v) => !v)}
            >
              Group by Room
            </Button>
          </div>
        </div>
        {/* Two-panel body */}
        <div className="flex flex-1 overflow-hidden">
          <BuildingSidebar sourceId={sourceId} />
          <div className="flex-1 overflow-hidden p-4">
            {selectedBuildingId ? (
              <ItemGrid
                sourceId={sourceId}
                buildingId={selectedBuildingId}
                quickFilterText={quickFilter}
                enableGrouping={enableGrouping}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Select a building to view its ACM items
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
```

### 13. Empty State (AC13)

When `useBuildings` returns an empty array and is not loading:

```tsx
// Inside BuildingSidebar
{buildings.length === 0 && !isLoading && (
  <div className="flex flex-col items-center gap-3 p-6 text-center">
    <Building2 className="h-10 w-10 text-muted-foreground/40" />
    <p className="text-sm text-muted-foreground font-medium">No buildings extracted yet</p>
    <p className="text-xs text-muted-foreground">
      Run extraction to populate buildings from the source document.
    </p>
    <Button variant="outline" size="sm" asChild>
      <Link href={`/jobs/${sourceId}/extract`}>Go to Extraction</Link>
    </Button>
  </div>
)}
```

### V3 Compliance

- **SF field names as headers**: Column headers come from `SFFieldDef.label` (Salesforce human-readable labels), not hardcoded BAR names. This aligns with the V3 SF-first taxonomy from E30-S2 and E32-S4.
- **BuildingRecord domain model**: Uses `internal_id` (`BLD#NNN`) from the domain model, not the legacy `building_id` string.
- **Dual API endpoint awareness**: The V3 buildings endpoint is `GET /api/acm/buildings` (not the older `/api/acm/jobs/{id}/buildings`). The old endpoint is used only by `BuildingReviewGrid` for wizard flow.
- **No ACMRecord re-declaration**: `ACMRecord` is imported from `frontend/src/lib/types/acm.ts` to avoid drift from the canonical type.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | CREATE | New dedicated two-view page at `/source/:id` |
| `frontend/src/components/acm/BuildingSidebar.tsx` | CREATE | Left sidebar: building list, detail panel, empty state |
| `frontend/src/components/acm/ItemGrid.tsx` | CREATE | AG Grid for ACM items; dynamic columns from field schema |
| `frontend/src/stores/buildingStore.ts` | CREATE | Zustand store for `selectedBuildingId` (creates `stores/` dir) |
| `frontend/src/lib/types/building.ts` | CREATE | `BuildingRecord`, `BuildingListResponse`, `BuildingSummary` interfaces |
| `frontend/src/lib/types/sf-schema.ts` | CREATE | `SFFieldDef`, `SFFieldSchemaObject`, `SFFieldSchemaConfig` interfaces |
| `frontend/src/lib/hooks/useBuildings.ts` | CREATE | React Query hook: `useBuildings(sourceId)` |
| `frontend/src/lib/hooks/useACMItems.ts` | CREATE | React Query hooks: `useACMItems(sourceId, buildingId)`, `useFieldSchema()` |
| `frontend/src/lib/api/acm.ts` | MODIFY | Add `acmApi.listBuildings()` and `acmApi.getFieldSchema()` methods |

---

## Database Changes

None. All data is read from existing `building_record` and `acm_record` tables populated by E30-S2.

---

## API Changes

None. Backend endpoints already exist from E30-S2:
- `GET /api/acm/buildings?source_id={id}` → `BuildingRecordListResponse`
- `GET /api/acm/records?source_id={id}&building_id={id}&limit=500` → `ACMRecordListResponse`
- `GET /api/acm/field-schema` → `SFFieldSchemaConfigResponse`

---

## Frontend Changes

### New Files (detailed)

**`BuildingSidebar.tsx`** responsibilities:
- Calls `useBuildings(sourceId)` — shows skeleton on loading, error state on failure
- For each building: renders `internal_id`, `building_name`, record count badge, validation status badge
- Calls `useBuildingStore()` to read/write `selectedBuildingId`
- Highlights selected building with `bg-primary/10 border-l-2 border-primary`
- Below list: `BuildingDetailPanel` — renders key `BuildingRecord` fields in a two-column grid (address, type, year, levels, ownership, frequency of use)
- Empty state per AC13

**`ItemGrid.tsx`** responsibilities:
- Receives `sourceId`, `buildingId`, `quickFilterText`, `enableGrouping` as props
- Calls `useACMItems(sourceId, buildingId)` and `useFieldSchema()`
- Builds `ColDef[]` from `fieldSchema.item_fields.fields`
- Pins `building_code` and `room_id` left
- Applies `RiskStatusRenderer` to `risk_status` field
- Applies row grouping config when `enableGrouping=true` — groups by `room_id`
- Uses AG Grid `theme="legacy"` with `ag-theme-alpine` CSS vars
- Shows loading overlay via `loading={isLoading}` prop
- Keyboard hints bar below grid (arrow keys, Enter, Space, ?)
- Visible row count display: "Showing X of Y records"

**`SourceACMViewContent`** (inner component in page.tsx) responsibilities:
- Manages `quickFilter` and `enableGrouping` local state
- Renders top toolbar with search `Input` and "Group by Room" `Button`
- Splits layout into 72-unit sidebar and flex-1 main area
- Shows "Select a building" placeholder when `selectedBuildingId` is null

### Modified Files

**`frontend/src/lib/api/acm.ts`**:
- Import `BuildingListResponse` from `@/lib/types/building`
- Import `SFFieldSchemaConfig` from `@/lib/types/sf-schema`
- Add `listBuildings` and `getFieldSchema` methods as described in Technical Design §6

---

## Test Plan

### Unit Tests

| Test | File | Description |
|------|------|-------------|
| `deriveValidationStatus` pure function | `__tests__/building-utils.test.ts` | complete/incomplete/unknown logic |
| `useBuildings` hook | `__tests__/useBuildings.test.ts` | calls correct URL, disabled when no sourceId |
| `useACMItems` hook | `__tests__/useACMItems.test.ts` | disabled when buildingId is null, enabled when set |
| `buildingStore` | `__tests__/buildingStore.test.ts` | setSelectedBuilding updates state correctly |
| `acmApi.listBuildings` | `__tests__/acm-api.test.ts` | GET /acm/buildings with source_id param |
| `acmApi.getFieldSchema` | `__tests__/acm-api.test.ts` | GET /acm/field-schema |

### Integration / E2E Tests (Playwright)

| Test | Description |
|------|-------------|
| Navigate to `/source/:id` | Page loads without JS error, `<BuildingSidebar>` is visible |
| Click a building | AG Grid renders with > 0 columns and > 0 rows |
| Empty state | When no buildings returned, empty state message is visible |
| Risk badge color | Row with `risk_status=High` has `bg-red-50` class applied |
| Quick filter | Typing in search box reduces visible row count |
| Group by room toggle | Clicking "Group by Room" adds group rows to grid |
| Column pin | Horizontal scroll does not hide the building/room columns |

### Build Verification (Required per Story Verification Protocol)

```bash
cd frontend && npm run build    # Must pass — no missing imports or type errors
cd frontend && npm run lint     # No ESLint errors
```

---

## Implementation Notes and Risks

### HIGH Risk Items

1. **Field schema column generation**: The `item_fields.fields` list from `/api/acm/field-schema` may include fields whose `api_name` does not map 1:1 to `ACMRecord` TypeScript interface keys (e.g., SF `__c` suffixed names vs camelCase backend names). The dev agent must inspect the actual API response and add a `fieldApiToRecordKey()` normalizer if needed. Do NOT assume `api_name` === `ACMRecord` property name.

2. **ACMRecord field coverage**: The existing `ACMRecord` interface in `acm.ts` uses BAR-era field names (e.g., `building_id`, `building_name` directly on the record). After E30-S3 (ACM Record SF Item Alignment), these may have changed. Verify the actual fields returned by `GET /api/acm/records` at implementation time and align column `field` values accordingly.

3. **Zustand `stores/` directory**: The directory does not exist. Create it. Verify that the Zustand version already installed in the project supports `create()` without additional config (check `package.json` for `zustand` version).

4. **BuildingRecord vs BuildingReviewGrid.BuildingRecord**: The `BuildingReviewGrid.tsx` component defines its own local `BuildingRecord` interface for the wizard flow (uses `building_id`, not `internal_id`). Do **not** alter `BuildingReviewGrid.tsx`. The new `frontend/src/lib/types/building.ts` defines the V3 shape from `BuildingRecordResponse`. These two types are intentionally different and serve different endpoints.

5. **Sidebar width and grid height**: The two-panel layout must fill the viewport height without overflowing. Use `h-screen` on the outer container and `overflow-hidden` on the flex body. The AG Grid wrapper needs explicit `h-full` or `h-[calc(100vh-Npx)]` where N accounts for the top bar height. Measure carefully; this is a common source of layout defects.

6. **Column pinning with dynamic ColDefs**: AG Grid's `pinned: 'left'` in `ColDef` works at grid initialization. If the `columnDefs` array is re-generated after schema loads, confirm that column state is applied correctly. Use `key` prop on `AgGridReact` or re-apply column state via `gridApi.applyColumnState()` in `onGridReady` if needed.

---

## Dev Agent Record

- Status: Not Started
- Started: —
- Completed: —
- Build: —
- Tests: —
- Review: —
- Notes: —
