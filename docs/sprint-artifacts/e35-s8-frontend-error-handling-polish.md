# E35-S8: Frontend Error Handling & Polish

**Story ID:** E35-S8
**Sprint:** V3-8
**Story Points:** 2
**Risk Level:** LOW
**Type:** frontend

## Summary

Polish the frontend ACM register views to handle edge cases gracefully: empty building data, missing/error states, and CopilotKit dev inspector z-index interference.

## Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC1 | BuildingSidebar shows "No buildings extracted yet" empty state (not error) | Already implemented |
| AC2 | No 500 console errors when viewing source with 0 buildings | Needs verification/fix |
| AC3 | Source page handles missing/empty building data gracefully | Needs verification/fix |
| AC4 | CopilotKit dev inspector does not block user interactions | Needs fix |

## Analysis

### AC1 — Already Done
`BuildingSidebar.tsx` already has a proper empty state at line 133-143 with a Building2 icon, descriptive text, and a link to extraction.

### AC2 — Console Error Prevention
The `useBuildings` hook calls `GET /api/acm/buildings?source_id=X`. When no buildings exist, the API should return `{ buildings: [], total: 0 }`. The hook is already wrapped in React Query with proper error handling. Need to ensure:
- `useValidationSummary` doesn't throw when buildings is empty
- `useV3BuildingStream` handles 0 buildings gracefully (division by zero in progress bar)
- No unguarded property access on empty/null building data

### AC3 — Graceful Empty Data
The source page (`page.tsx`) shows "Select a building to view its ACM items" when no building is selected. Need to ensure:
- The progress bar doesn't show `NaN%` when `buildings.length === 0`
- `BulkOperationsBar` and `ExportDialog` handle empty state
- ItemGrid handles empty `buildingId` gracefully

### AC4 — CopilotKit Dev Inspector
CopilotKit v1.x renders a floating dev inspector panel in development mode that can overlap interactive elements. Fix by adding CSS to suppress or lower its z-index, or disable it in the CopilotProvider config.

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | Guard against division-by-zero in progress bar, handle empty buildings gracefully |
| `frontend/src/components/acm/BuildingSidebar.tsx` | Ensure empty state is shown correctly (already done, verify) |
| `frontend/src/components/acm/ItemGrid.tsx` | Guard against empty/null data edge cases |
| `frontend/src/app/globals.css` | Add CSS to suppress CopilotKit dev inspector overlay in production |
| `frontend/src/components/providers/CopilotProvider.tsx` | Disable dev tools if CopilotKit supports it |

## Implementation Notes

- Minimal changes — only fix actual edge cases, don't refactor
- Focus on preventing runtime errors (NaN, null access, unhandled promise rejections)
- CopilotKit fix should be CSS-only or a single prop — no major refactoring
