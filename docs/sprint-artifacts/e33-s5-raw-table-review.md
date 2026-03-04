# E33-S5: Raw Table Review (Opt-In)

**Sprint:** V3-6
**Story Points:** 3
**Risk:** MEDIUM
**Type:** Frontend (primary) + Backend (one new endpoint)
**Dependencies:** E31-S4 (RawExtraction domain model), E33-S2 (Building Grid + Item Grid two-view)

---

## 1. Overview

Raw Table Review gives compliance officers an opt-in view of the per-provider raw extraction output
(`raw_extraction` table) for a source document. Officers can inspect what Docling and MinerU extracted
page-by-page before consensus merge, make inline corrections to individual cell values, and optionally
re-trigger AI extraction using their corrected data.

The view is deliberately NOT in the default flow — it is accessed via a "Review Raw Tables" button on
the building grid page. The existing "Raw Tables" button in the source page top bar links to
`/jobs/${sourceId}?tab=raw-tables` (the old table-section view). This story replaces that link target
with `/source/${sourceId}/raw`.

**What this is NOT:**
- It is not a replacement for the consensus ACM register view (that is E33-S2).
- It does not modify ACMRecord rows directly — it modifies `raw_extraction.officer_edits[]` only.
- The re-process button fires the existing extract command with `force=true`; it does not implement a
  new extraction pipeline node.

---

## 2. File Changes

| # | Path | Type | Description |
|---|------|------|-------------|
| 1 | `frontend/src/app/(dashboard)/source/[id]/raw/page.tsx` | NEW | Next.js page for `/source/:id/raw`. Unwraps async params, wraps in ErrorBoundary, renders `RawTableReviewContent`. |
| 2 | `frontend/src/components/acm/RawTableGrid.tsx` | NEW | AG Grid component showing per-provider raw extraction rows. Editable `structured_json` cells with inline save. Provider tab bar (Docling / MinerU / Consensus). Edit history drawer. |
| 3 | `frontend/src/lib/hooks/useRawExtractions.ts` | NEW | React Query hooks: `useRawExtractions`, `usePatchRawExtraction`, `useReprocessExtraction`. |
| 4 | `frontend/src/lib/api/acm.ts` | MODIFY | Add `rawExtractions`, `patchRawExtraction`, and `reprocessFromRaw` methods to `acmApi`. |
| 5 | `frontend/src/lib/types/acm.ts` | MODIFY | Add `RawExtractionRecord`, `OfficerEdit`, `PatchRawExtractionRequest` types. |
| 6 | `frontend/src/app/(dashboard)/source/[id]/page.tsx` | MODIFY | Update "Raw Tables" button href from `/jobs/${sourceId}?tab=raw-tables` to `/source/${sourceId}/raw`. |
| 7 | `api/routers/acm.py` | MODIFY | Add `PATCH /api/acm/raw-extractions/{source_id}/{extraction_id}` endpoint. |
| 8 | `api/models.py` | MODIFY | Add `PatchRawExtractionRequest` and updated `RawExtractionResponse` (already has `officer_edits`; no change needed to response model). |

---

## 3. API Changes

### 3.1 Existing Endpoint (read, already present)

```
GET /api/acm/raw-extractions/{source_id}
  Query params:
    provider: str   (optional — "docling" | "mineru")
    page_number: int (optional)
  Response: RawExtractionListResponse
    {
      source_id: str,
      total: int,
      extractions: RawExtractionResponse[]
    }
```

`RawExtractionResponse` (existing, `api/models.py` line 644):
```python
{
  id: str,
  source_id: str,
  provider_id: str,          # "docling" | "mineru"
  extraction_backend: str,   # "docling:2.x" | "mineru:2.7"
  page_number: int,
  raw_html: str | None,
  raw_markdown: str | None,
  structured_json: str | None,   # JSON string of {headers, rows}
  bbox: dict | None,
  confidence: float | None,
  officer_edits: list[dict],     # existing audit trail field
  created_at: str | None
}
```

### 3.2 New Endpoint

```
PATCH /api/acm/raw-extractions/{source_id}/{extraction_id}
```

**Request body** (`PatchRawExtractionRequest`):
```python
class OfficerEditEntry(BaseModel):
    field: str         # column name / key being corrected
    old_value: str
    new_value: str
    user: str          # from session / auth context — pass from frontend
    timestamp: str     # ISO 8601, generated on frontend

class PatchRawExtractionRequest(BaseModel):
    structured_json: Optional[str] = None  # full updated JSON string if cells changed
    edits: List[OfficerEditEntry]           # edit history entries to append
```

**Response:** The updated `RawExtractionResponse` (200 OK).

**Backend implementation (in `api/routers/acm.py`):**
1. Load `RawExtraction` by ID, verify `source_id` matches.
2. If `structured_json` provided, overwrite `extraction.structured_json`.
3. Append each `OfficerEditEntry` dict to `extraction.officer_edits`.
4. Call `extraction.save()`.
5. Return updated `RawExtractionResponse`.

```python
@router.patch(
    "/raw-extractions/{source_id}/{extraction_id}",
    response_model=RawExtractionResponse,
)
async def patch_raw_extraction(
    source_id: str,
    extraction_id: str,
    body: PatchRawExtractionRequest,
):
    """Append officer edits and optionally update structured_json for a raw extraction row."""
    try:
        extraction = await RawExtraction.get(extraction_id)
        if extraction is None:
            raise HTTPException(status_code=404, detail="Raw extraction not found")
        if str(extraction.source_id) != str(ensure_record_id(source_id)):
            raise HTTPException(status_code=403, detail="source_id mismatch")
        if body.structured_json is not None:
            extraction.structured_json = body.structured_json
        extraction.officer_edits = extraction.officer_edits + [
            e.model_dump() for e in body.edits
        ]
        await extraction.save()
        return RawExtractionResponse(
            id=str(extraction.id or ""),
            source_id=str(extraction.source_id),
            provider_id=extraction.provider_id,
            extraction_backend=extraction.extraction_backend,
            page_number=extraction.page_number,
            raw_html=extraction.raw_html,
            raw_markdown=extraction.raw_markdown,
            structured_json=extraction.structured_json,
            bbox=extraction.bbox,
            confidence=extraction.confidence,
            officer_edits=extraction.officer_edits,
            created_at=str(extraction.created_at) if extraction.created_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching raw extraction {extraction_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Note:** `RawExtraction.get(id)` — check if ObjectModel base has a `.get(id)` class method or if you
need `repo_query("SELECT * FROM raw_extraction WHERE id = $id", {"id": id})`. Use the same pattern as
other domain models in the file.

### 3.3 Re-process (existing endpoint, new frontend usage)

Re-process fires the existing extract endpoint with `force=True` so existing records are cleared:
```
POST /api/acm/extract
  { source_id: str, force: true }
```
The `ACMExtractCommand` already has `force: bool = False`. No backend change needed for re-process.

---

## 4. TypeScript Types

Add to `frontend/src/lib/types/acm.ts`:

```typescript
export interface OfficerEdit {
  field: string
  old_value: string
  new_value: string
  user: string
  timestamp: string  // ISO 8601
}

export interface RawExtractionRecord {
  id: string
  source_id: string
  provider_id: string           // "docling" | "mineru"
  extraction_backend: string
  page_number: number
  raw_html: string | null
  raw_markdown: string | null
  structured_json: string | null  // JSON string: { headers: string[], rows: string[][] }
  bbox: Record<string, number> | null
  confidence: number | null
  officer_edits: OfficerEdit[]
  created_at: string | null
}

export interface RawExtractionListResponse {
  source_id: string
  total: number
  extractions: RawExtractionRecord[]
}

export interface PatchRawExtractionRequest {
  structured_json?: string
  edits: OfficerEdit[]
}

// Shape of parsed structured_json content
export interface StructuredJsonContent {
  headers: string[]
  rows: string[][]
}
```

---

## 5. Hook Specifications

### `frontend/src/lib/hooks/useRawExtractions.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import type { PatchRawExtractionRequest } from '@/lib/types/acm'

export const RAW_EXTRACTION_QUERY_KEYS = {
  bySource: (sourceId: string, provider?: string) =>
    ['raw-extractions', sourceId, provider ?? 'all'] as const,
}

/**
 * Fetch all raw extractions for a source, optionally filtered by provider.
 * provider: "docling" | "mineru" | undefined (all)
 */
export function useRawExtractions(sourceId: string, provider?: string) {
  return useQuery({
    queryKey: RAW_EXTRACTION_QUERY_KEYS.bySource(sourceId, provider),
    queryFn: () => acmApi.rawExtractions(sourceId, provider),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  })
}

/**
 * Patch a single raw extraction row with officer edits.
 * Invalidates the raw-extractions list for the source on success.
 */
export function usePatchRawExtraction(sourceId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({
      extractionId,
      body,
    }: {
      extractionId: string
      body: PatchRawExtractionRequest
    }) => acmApi.patchRawExtraction(sourceId, extractionId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['raw-extractions', sourceId],
      })
      toast({ title: 'Edit saved', description: 'Correction recorded to audit trail.' })
    },
    onError: () => {
      toast({
        title: 'Save failed',
        description: 'Could not save officer correction. Please try again.',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Re-trigger AI extraction using officer-corrected raw data.
 * Uses existing /acm/extract with force=true to clear and rerun.
 */
export function useReprocessExtraction() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (sourceId: string) => acmApi.extract(sourceId, { force: true }),
    onSuccess: () => {
      toast({
        title: 'Re-processing started',
        description: 'AI extraction re-running with corrected data. Check the job page for progress.',
      })
    },
    onError: () => {
      toast({
        title: 'Re-process failed',
        description: 'Could not start re-extraction. Please try again.',
        variant: 'destructive',
      })
    },
  })
}
```

---

## 6. API Client Changes

Add to `frontend/src/lib/api/acm.ts` (inside the `acmApi` object):

```typescript
/**
 * List raw extractions for a source (E31-S4 raw_extraction table).
 * Optionally filter by provider: "docling" | "mineru"
 */
rawExtractions: async (sourceId: string, provider?: string): Promise<RawExtractionListResponse> => {
  const params: Record<string, string> = {}
  if (provider) params.provider = provider
  const response = await apiClient.get<RawExtractionListResponse>(
    `/acm/raw-extractions/${encodeURIComponent(sourceId)}`,
    { params }
  )
  return response.data
},

/**
 * Patch officer edits onto a raw extraction row.
 */
patchRawExtraction: async (
  sourceId: string,
  extractionId: string,
  body: PatchRawExtractionRequest
): Promise<RawExtractionRecord> => {
  const response = await apiClient.patch<RawExtractionRecord>(
    `/acm/raw-extractions/${encodeURIComponent(sourceId)}/${encodeURIComponent(extractionId)}`,
    body
  )
  return response.data
},
```

Also update the `extract` call signature to accept optional options:
```typescript
extract: async (sourceId: string, opts?: { force?: boolean }): Promise<ACMExtractResponse> => {
  const response = await apiClient.post<ACMExtractResponse>('/acm/extract', {
    source_id: sourceId,
    force: opts?.force ?? false,
  })
  return response.data
},
```

Import additions needed at top of `acm.ts`:
```typescript
import type {
  // ... existing imports ...
  RawExtractionListResponse,
  RawExtractionRecord,
  PatchRawExtractionRequest,
} from '@/lib/types/acm'
```

---

## 7. Component Specifications

### 7.1 Page: `frontend/src/app/(dashboard)/source/[id]/raw/page.tsx`

Follows exact same pattern as `frontend/src/app/(dashboard)/source/[id]/page.tsx`.

```tsx
'use client'

import { use } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { RawTableGrid } from '@/components/acm/RawTableGrid'

function RawTableReviewContent({ sourceId }: { sourceId: string }) {
  return (
    <AppShell>
      <RawTableGrid sourceId={sourceId} />
    </AppShell>
  )
}

export default function RawTableReviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Raw Table Review" reloadUrl="/sources" />
      )}
    >
      <RawTableReviewContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
```

### 7.2 Component: `frontend/src/components/acm/RawTableGrid.tsx`

**Props:**
```typescript
interface RawTableGridProps {
  sourceId: string
}
```

**Internal state:**
```typescript
const [activeProvider, setActiveProvider] = useState<'docling' | 'mineru' | 'all'>('all')
const [editHistoryRow, setEditHistoryRow] = useState<RawExtractionRecord | null>(null)
const [pendingEdits, setPendingEdits] = useState<Map<string, CellEdit[]>>(new Map())
```

**Provider tabs:** Three tabs — "All", "Docling", "MinerU". Switching tabs changes the `provider`
param passed to `useRawExtractions`. "All" passes `undefined` (shows all providers, sorted by
`page_number` then `provider_id`).

**AG Grid columns:**

| Field | Header | Width | Notes |
|-------|--------|-------|-------|
| `page_number` | Page | 80 | Pinned left, sortable |
| `provider_id` | Provider | 100 | Pinned left, badge renderer |
| `confidence` | Confidence | 100 | Render as percentage or "-" |
| `row_count` (derived) | Rows | 80 | Parse from `structured_json`, count rows |
| `col_count` (derived) | Cols | 80 | Parse from `structured_json`, count headers |
| `structured_json` | Preview | flex | Editable. Show truncated first row. Cell editor opens inline edit dialog. |
| `officer_edits` (derived) | Edits | 80 | Count of officer_edits entries. Click opens history drawer. |
| `actions` | — | 80 | "View HTML" button (opens iframe modal) |

**Editable cells approach (keep it simple for 3SP):**
- Do NOT implement full in-grid AG Grid editing for `structured_json` — that would require a custom
  AG Grid cell editor parsing and re-serializing JSON which is high risk for 3SP.
- Instead: clicking "Preview" column opens a simple modal with a `<textarea>` pre-filled with the
  pretty-printed JSON. Officer edits the JSON, clicks "Save". The hook calls `patchRawExtraction`.
- The modal auto-detects which fields changed and constructs the `OfficerEdit[]` array by diffing
  original vs new parsed JSON.
- AC2 is satisfied: edits save to `officer_edits[]`. AC4 (edit history) is satisfied via the audit
  trail recorded in `officer_edits`.

**Re-process button:**
- Shown in the top bar. Disabled while `patchRawExtraction` is pending.
- Shows a confirm dialog: "Re-run AI extraction using corrected raw data? Existing ACM records for
  this source will be cleared."
- On confirm: calls `useReprocessExtraction` mutate.

**Edit History Drawer:**
- A slide-over panel (use a Sheet component from Radix/shadcn if available, or a simple aside div).
- Triggered by clicking the "Edits" count cell on a row.
- Lists each `OfficerEdit` entry: field / old value / new value / user / timestamp.

**Empty state:** If `total === 0`, show: "No raw extraction data found. Run extraction first to
populate raw tables." with a "Go to Job" link to `/jobs/${sourceId}`.

**Loading state:** Use AG Grid's built-in `loading={isLoading}` prop (same as ItemGrid).

**Full layout structure:**
```
<div className="flex flex-col h-full overflow-hidden">
  {/* Top bar */}
  <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
    <Button variant="ghost" size="sm" asChild>
      <Link href={`/source/${sourceId}`}>
        <ArrowLeft /> Back to Register
      </Link>
    </Button>
    <h1>Raw Table Review</h1>
    <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50">
      Opt-In
    </Badge>
    <div className="ml-auto flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{total} raw extraction rows</span>
      <Button variant="outline" size="sm" onClick={() => setReprocessConfirmOpen(true)}>
        <RefreshCw /> Re-process
      </Button>
    </div>
  </div>

  {/* Provider tabs */}
  <div className="flex gap-1 px-4 py-2 border-b bg-muted/30 shrink-0">
    {['all', 'docling', 'mineru'].map(p => (
      <Button
        key={p}
        variant={activeProvider === p ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setActiveProvider(p as ...)}
      >
        {p === 'all' ? 'All Providers' : p.charAt(0).toUpperCase() + p.slice(1)}
      </Button>
    ))}
  </div>

  {/* AG Grid */}
  <div className="flex-1 min-h-0 overflow-hidden p-4">
    <div className="ag-theme-alpine h-full w-full" ...>
      <AgGridReact ... />
    </div>
  </div>
</div>
```

**AG Grid setup:** Follow the exact same pattern as `ItemGrid.tsx`:
- `ModuleRegistry.registerModules([AllCommunityModule])`
- `theme="legacy"` for ag-theme-alpine CSS
- `domLayout="normal"`
- `pagination={true}`, `paginationPageSize={50}`

**Derived columns:** `row_count` and `col_count` use `valueGetter` to parse `structured_json`:
```typescript
{
  headerName: 'Rows',
  width: 80,
  valueGetter: (params) => {
    if (!params.data?.structured_json) return 0
    try {
      const parsed = JSON.parse(params.data.structured_json)
      return Array.isArray(parsed.rows) ? parsed.rows.length : 0
    } catch { return '?' }
  },
}
```

---

## 8. Modify Existing Source Page

In `frontend/src/app/(dashboard)/source/[id]/page.tsx`, update the "Raw Tables" button:

```tsx
// BEFORE (line 44-49):
<Button variant="outline" size="sm" asChild>
  <Link href={`/jobs/${sourceId}?tab=raw-tables`}>
    <Table2 className="h-4 w-4 mr-1" />
    Raw Tables
  </Link>
</Button>

// AFTER:
<Button variant="outline" size="sm" asChild>
  <Link href={`/source/${sourceId}/raw`}>
    <Table2 className="h-4 w-4 mr-1" />
    Review Raw Tables
  </Link>
</Button>
```

---

## 9. Test Plan

### 9.1 Backend Tests

**File:** `tests/test_raw_extraction_patch.py` (new)

| Test | Description |
|------|-------------|
| `test_patch_raw_extraction_appends_edits` | PATCH with valid body appends to `officer_edits`, returns 200 with updated record |
| `test_patch_raw_extraction_updates_structured_json` | Providing `structured_json` field overwrites it; edits still appended |
| `test_patch_raw_extraction_source_mismatch_returns_403` | source_id in path does not match record's source_id → 403 |
| `test_patch_raw_extraction_not_found_returns_404` | Non-existent extraction_id → 404 |
| `test_patch_raw_extraction_empty_edits_valid` | Empty `edits: []` with `structured_json` update is valid → 200 |

Use `pytest` fixtures pattern from existing `tests/test_record_matcher.py` or
`tests/test_consensus_engine.py` for async test setup.

### 9.2 Frontend Hook Tests

**File:** `frontend/src/lib/hooks/__tests__/useRawExtractions.test.ts` (new, if test infra exists)

If the project does not have a frontend unit test setup (check for `jest.config.*` or `vitest.config.*`),
skip frontend unit tests and cover via E2E only.

| Test | Description |
|------|-------------|
| `useRawExtractions fetches all providers` | MSW mock of GET returns list, hook returns data |
| `usePatchRawExtraction calls PATCH and invalidates cache` | Verify query invalidation on success |
| `useReprocessExtraction calls POST /acm/extract with force=true` | Verify payload |

### 9.3 E2E / Smoke Test Checklist

Manual verification steps before marking story done:

1. Navigate to `/source/:id` — "Review Raw Tables" button is visible in top bar.
2. Click button — redirected to `/source/:id/raw`.
3. If no raw extractions exist: empty state message shown with "Go to Job" link.
4. If raw extractions exist: AG Grid loads with rows grouped by page/provider.
5. Provider tab switching filters grid correctly.
6. Click "Preview" on a row with `structured_json` — edit modal opens with JSON.
7. Modify a value in the textarea, click Save — toast "Edit saved" appears, grid refreshes.
8. Click "Edits" count on that row — history drawer shows the edit with user/timestamp.
9. "Re-process" button shows confirm dialog. Cancel does nothing.
10. Confirm re-process — toast "Re-processing started" appears.
11. Build passes: `cd frontend && npm run build` (no type errors).

---

## 10. Implementation Notes and Gotchas

### 10.1 `structured_json` is a JSON string, not an object

`RawExtraction.structured_json` is stored as a JSON string in SurrealDB (not a native object).
Frontend must `JSON.parse()` to read and `JSON.stringify()` to write. If parsing fails, show
`"Unparseable JSON"` rather than crashing.

Expected shape after parsing:
```json
{ "headers": ["Location", "ACM Type", "Condition"], "rows": [["Room 1A", "Carpet Tile", "Good"]] }
```
This shape comes from `NormalizedTable` in the provider adapter layer (E31-S2). Do not assume it —
handle missing `headers` or `rows` keys gracefully.

### 10.2 `RawExtraction.get()` method availability

Check whether `ObjectModel` base class has a `get(id)` class method. If not, use `repo_query`:
```python
result = await repo_query("SELECT * FROM raw_extraction WHERE id = $id", {"id": extraction_id})
extraction = RawExtraction(**result[0]) if result else None
```

### 10.3 User identification for officer_edits

The frontend should pass the logged-in user's email or name as the `user` field in `OfficerEdit`.
Check `frontend/src/lib/stores/auth-store.ts` or the `useAuth` hook for the current user object.
If unauthenticated or unavailable, pass `"unknown"`.

### 10.4 Re-process uses existing extract command

`acmApi.extract(sourceId, { force: true })` posts to `/api/acm/extract` with `{ source_id, force: true }`.
The existing `ACMExtractCommand` in `commands/acm_commands.py` (line 73) has `force: bool = False`.
When `force=True` the command deletes existing records before re-running. This is the correct
behavior: officers correct raw data, then the AI re-reads from the (corrected) raw extraction rows.

**Important:** The current extraction pipeline (E31-S5) reads from PDF/provider adapters directly —
it does NOT yet read from `raw_extraction` table as input. So "re-process from corrected data" is
aspirational for the current sprint. The re-process button should communicate this clearly in the
confirm dialog: "Re-run AI extraction (pipeline will re-process the source document; officer edits
to raw data are stored for future pipeline integration)."

### 10.5 "Consensus" tab

AC3 mentions "consensus merged" as a third provider tab. The consensus output is stored in
`acm_record`, not in `raw_extraction`. For 3SP scope, implement the third tab as a message:
"Consensus view is available on the Register page" with a link to `/source/${sourceId}`. This
avoids scope creep while satisfying the AC intent.

### 10.6 Edit modal JSON diffing

To build the `OfficerEdit[]` array from the modal:
```typescript
function diffStructuredJson(
  original: StructuredJsonContent,
  updated: StructuredJsonContent
): OfficerEdit[] {
  const edits: OfficerEdit[] = []
  // Compare row by row, cell by cell
  updated.rows.forEach((row, rowIdx) => {
    row.forEach((cell, colIdx) => {
      const oldCell = original.rows[rowIdx]?.[colIdx] ?? ''
      if (cell !== oldCell) {
        const header = updated.headers[colIdx] ?? `col_${colIdx}`
        edits.push({
          field: `row[${rowIdx}].${header}`,
          old_value: oldCell,
          new_value: cell,
          user: currentUser,
          timestamp: new Date().toISOString(),
        })
      }
    })
  })
  return edits
}
```

### 10.7 AG Grid community edition — no enterprise features

The project uses `AllCommunityModule`. Do not use enterprise features (row pinning, master-detail,
etc.). Keep the grid simple.

### 10.8 Build verification before marking complete

```bash
# Backend
cd D:/ailocal/acm-ai
uv run ruff check api/routers/acm.py api/models.py
uv run pytest tests/test_raw_extraction_patch.py -v

# Frontend
cd D:/ailocal/acm-ai/frontend
npm run build
```

Both must pass before this story is marked Done.

---

## 11. Acceptance Criteria Mapping

| AC | Satisfied By |
|----|-------------|
| AC1: Route `/source/:id/raw` with AG Grid | `raw/page.tsx` + `RawTableGrid.tsx` |
| AC2: Editable cells save to `officer_edits[]` | Edit modal + `patchRawExtraction` PATCH endpoint |
| AC3: Provider tabs (Docling / MinerU / Consensus) | Three tabs in `RawTableGrid`; Consensus tab shows nav link |
| AC4: Edit history `{user, field, old_value, new_value, timestamp}` | `OfficerEdit` type + `officer_edits[]` field in `raw_extraction` |
| AC5: Re-process button | Top bar button → confirm dialog → `useReprocessExtraction` |
| AC6: Opt-in, not in default flow | Page only reachable via "Review Raw Tables" button, not in sidebar or default nav |
| AC7: Accessible via "Review Raw Tables" button on building grid page | Button update in `/source/[id]/page.tsx` |
