# Bug Fix: ACM Grid Column Naming & Structure Fixes

Status: done

## Story

As a **VAEA compliance officer**,
I want **ACM grid columns to use correct Victorian BAR terminology**,
so that **exported reports match regulatory requirements and field names are consistent**.

## Acceptance Criteria

1. "Building ID" column renamed to "Building Code" in grid, CSV, and Excel exports
2. `material_description` and `acm_product_type` merged into single "ACM Product Type" column with fallback logic
3. `risk_status` column removed from grid (risk calculation is external in VAEA system)
4. CSV export header "Material Condition" renamed to "Condition"
5. No regressions in grid rendering, sorting, or filtering

## Tasks / Subtasks

- [x] Task 1: Rename Building ID → Building Code in grid (AC: #1)
  - [x] 1.1 Update `ACMGrid.tsx` headerName and headerTooltip
- [x] Task 2: Merge material columns (AC: #2)
  - [x] 2.1 Replace `material_description` column with `acm_product_type` column using valueGetter fallback
  - [x] 2.2 Remove duplicate standalone `acm_product_type` column definition
- [x] Task 3: Remove risk_status column (AC: #3)
  - [x] 3.1 Remove `risk_status` column definition from ACMGrid.tsx
  - [x] 3.2 Remove unused `RiskStatusRenderer` function and `Badge` import
- [x] Task 4: Fix export headers (AC: #1, #4)
  - [x] 4.1 CSV export: "Building ID" → "Building Code"
  - [x] 4.2 CSV export: "Material Condition" → "Condition"
  - [x] 4.3 Excel export: "Building ID" → "Building Code"
- [x] Task 5: Build verification (AC: #5)
  - [x] 5.1 Frontend build passes
  - [x] 5.2 Backend lint passes

## Dev Notes

### Root Cause

Column naming regressions accumulated over multiple PRs. Original column names from early development didn't match Victorian BAR (Building Asbestos Register) terminology. The `risk_status` column was added prematurely — risk calculation is performed in the external VAEA system, not in ACM-AI.

### Merged Column Implementation

```tsx
{
  field: 'acm_product_type',
  headerName: 'ACM Product Type',
  headerTooltip: 'AI-classified product type (falls back to raw description)',
  valueGetter: (params) => {
    return params.data?.acm_product_type || params.data?.material_description || ''
  },
}
```

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/ACMGrid.tsx` | MODIFY | Column renames, merge, removal |
| `api/routers/acm.py` | MODIFY | CSV/Excel export header fixes |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 1 (Quick Wins)
- Removed unused RiskStatusRenderer and Badge import (lint cleanup)
- Victorian BAR terminology now consistent across grid + exports

### File List
- frontend/src/components/acm/ACMGrid.tsx (column definitions, removed renderer)
- api/routers/acm.py (CSV headers lines 294/304, Excel header line 409)
