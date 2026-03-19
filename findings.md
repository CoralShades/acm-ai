# MCS11 Findings — Jobs vs Source Page Audit

## Audit Date: 2026-03-19

### Visual Audit (Screenshots)

| Page | Screenshot | Observations |
|------|-----------|-------------|
| `/jobs/source:ID` Overview | `audit-job-detail.png` | 6 tabs, stats cards, Re-Extract — no SSE, no live progress |
| `/jobs/source:ID` Buildings | `audit-job-buildings.png` | **BUG**: "No Rows To Show" despite 2 buildings (V3 API returns 0) → **FIXED** with `useJobBuildings` |
| `/jobs/source:ID` Buildings (fixed) | `audit-job-buildings-fixed.png` | 2 buildings now visible via legacy API fallback |
| `/jobs/source:ID` ACM Records | `audit-job-acm.png` | Records work, building filter tabs, but no bulk ops/search/validation |
| `/source/source:ID` | `audit-source-page.png` | "No buildings extracted yet" — V3 API has no data for this source |
| User D1.png | Production reference | Shows the ideal layout for jobs page |
| User view3.png | Production reference | Shows buildings grid with data |

### Two Buildings APIs (Root Cause of Buildings Bug)

1. **V3 endpoint**: `GET /api/acm/buildings?source_id=X`
   - Queries `building_record` table (E30-S2)
   - Only populated by V3 extraction pipeline
   - Returns 0 for sources extracted via old pipeline

2. **Legacy endpoint**: `GET /api/acm/jobs/{source_id}/buildings`
   - Derives buildings from `acm_record` data
   - Always works — joins acm_record GROUP BY building_id
   - Returns full building data for all extraction modes

**Fix applied**: Created `useJobBuildings` hook + `acmApi.listJobBuildings()` adapter that maps `BuildingResponse` → `BuildingRecord` shape. Jobs page tries V3 first, falls back to legacy.

### Feature Distribution Analysis

| Feature | `/jobs/[id]` | `/source/[id]` | Gap Priority |
|---------|:-----------:|:--------------:|:------------|
| SSE live streaming | No | Yes | **P0** — core UX |
| Building status badges | No | Yes | **P0** — progress visibility |
| Live progress bar + ETA | No | Yes | **P0** |
| Bulk edit/validate | No | Yes | **P1** — core workflow |
| Validation error counts | No | Yes | **P1** |
| Quick text search | No | Yes | **P2** |
| Group by Room | No | Yes | **P2** |
| Building selection persistence | useState | Zustand | **P3** |
| Save phase tracking | No | Yes (MCS10) | **P0** |
| CRUD Chat (CopilotKit) | Yes | No | Jobs-only |
| Content/Log/Raw Tables | Yes | No | Jobs-only |

### Hooks Usage Comparison

| Hook | `/jobs/[id]` | `/source/[id]` |
|------|:-----------:|:--------------:|
| `useV3BuildingStream` | No | Yes |
| `useV3SSE` | No | Yes (indirect) |
| `useBuildings` | Yes | Yes |
| `useJobBuildings` | Yes (MCS10 fix) | No |
| `useACMItems` | No (uses raw fetch) | Yes (per-building) |
| `useValidationSummary` | No | Yes |
| `useBulkFix` | No | Yes |
| `useBuildingStore` (Zustand) | No | Yes |
| `useACMStats` | Yes | No |
| `useSource` | Yes | No |

### State Management Gap

- `/jobs/[id]` uses `useState` for building selection → resets on tab navigation
- `/source/[id]` uses Zustand `useBuildingStore` → persists across navigation
- `/jobs/[id]` fetches ALL records upfront (500 limit) → inefficient
- `/source/[id]` fetches per-building on demand → efficient

### SSE Event Flow (for reference)

```
ai.building_extracted → building in DB, invalidate buildings query
ai.items_extracted    → items extracted (not saved), update status to "Validating"
ai.validation_complete → validation done, status to "Saving..."
ai.save_started       → save phase begins
ai.save_progress      → per-building save status
ai.save_complete      → items NOW in DB, invalidate items query, clear statuses
```

### Sub-pages Under /jobs/[id]/ (Discovery)

| Route | Purpose | Has SSE? |
|-------|---------|----------|
| `/jobs/[id]/extract` | Extraction monitoring | **YES** — richest SSE (dual category) |
| `/jobs/[id]/review/buildings` | Building review wizard | No |
| `/jobs/[id]/review/records` | Records review wizard | No |
| `/jobs/[id]/chat` | Standalone chat | No |

The `/jobs/[id]/extract` page has the MOST complete SSE experience (subscribes to both `extraction` and `ai` categories + AG-UI stream). This is separate from the main jobs detail page.
