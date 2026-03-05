# V8: E35-S8 — Frontend Empty State (AC9)

## Verification Date: 2026-03-05

## Code Check: Empty State Components

**Result**: PASS

### BuildingSidebar.tsx (line 136)
```tsx
<p className="text-sm text-muted-foreground font-medium">No buildings extracted yet</p>
<p className="text-xs text-muted-foreground">
  Run extraction to populate buildings from the source document.
</p>
```
Shows friendly empty state message when no buildings exist.

### BuildingReviewGrid.tsx (line 453)
```tsx
overlayNoRowsTemplate='<span class="text-muted-foreground text-sm">No buildings found. Click "+ Add Building" to add one.</span>'
```
AG Grid empty state with actionable message.

### SourceIntelligencePanel.tsx (line 106)
```tsx
<p className="text-sm text-muted-foreground">No buildings detected.</p>
```
Intelligence panel shows empty state when no buildings detected.

### RawTableGrid.tsx (line 329-332)
Empty state for raw table grid with centered placeholder.

### useACMItems.ts (line 39-41)
```ts
// Limit retries to avoid console error noise for sources with no buildings (E35-S8)
retry: 1,
```
Reduces retry noise for empty sources.

### Source page (page.tsx line 54)
```tsx
// Validation summary for Fix All + Export guard (skip when no buildings)
```
Gracefully handles zero-building state in validation summary.

## API Verification

`GET /api/acm/buildings?source_id=source:2kjfxd6goehaj0njkam3` returns:
```json
{"buildings": [], "total": 0}
```
No crash, no 404 — returns empty array.

## Verdict: PASS
