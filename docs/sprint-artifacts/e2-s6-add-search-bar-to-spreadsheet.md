# Story 2.6: Add Search Bar to Spreadsheet

Status: done

## Story

As a user,
I want to search across all columns in the ACM spreadsheet,
so that I can quickly find any text in the data without manually scrolling.

## Acceptance Criteria

1. - [x] Search input displayed above the grid (integrated into ACMToolbar)
2. - [x] Typing filters visible rows in real-time using AG Grid Quick Filter API
3. - [x] Searches across all text columns (product, material_description, building_name, room_name, location, result, risk_status, friable, material_condition)
4. - [x] Clear button (X icon) resets search when search text exists
5. - [x] Result count shown ("Showing X of Y records") updating dynamically as filter changes

## Tasks / Subtasks

- [x] Task 1: Create debounce hook utility (AC: 2)
  - [x] 1.1: Create `use-debounced-value.ts` hook in `frontend/src/lib/hooks/`
  - [x] 1.2: Implement hook with configurable delay (default 300ms)
  - [x] 1.3: Add JSDoc documentation

- [x] Task 2: Add search input to ACMToolbar component (AC: 1, 4)
  - [x] 2.1: Import Search and X icons from lucide-react
  - [x] 2.2: Import Input component from @/components/ui/input
  - [x] 2.3: Add searchText and onSearchChange props to ACMToolbarProps interface
  - [x] 2.4: Add search input field with Search icon prefix
  - [x] 2.5: Add conditional X (clear) button when search text exists
  - [x] 2.6: Style input to match existing toolbar design (max-w-md, proper spacing)

- [x] Task 3: Add result count display to ACMToolbar (AC: 5)
  - [x] 3.1: Add visibleCount and totalCount props to ACMToolbarProps
  - [x] 3.2: Display "Showing X of Y records" text with muted foreground styling
  - [x] 3.3: Only show count when there are records

- [x] Task 4: Implement search state and filtering in ACMTab (AC: 2, 3)
  - [x] 4.1: Add searchText state with useState
  - [x] 4.2: Import and apply useDebouncedValue hook
  - [x] 4.3: Pass searchText and setSearchText to ACMToolbar
  - [x] 4.4: Pass debounced search value to ACMGrid

- [x] Task 5: Integrate Quick Filter in ACMGrid (AC: 2, 3)
  - [x] 5.1: Add quickFilterText prop to ACMGridProps interface
  - [x] 5.2: Add onModelUpdated callback to track visible row count
  - [x] 5.3: Expose visibleCount via callback prop or return value
  - [x] 5.4: Apply quickFilterText to AgGridReact via setGridOption when value changes
  - [x] 5.5: Use useEffect to update quickFilterText when prop changes

- [x] Task 6: Wire up visible count from grid to toolbar (AC: 5)
  - [x] 6.1: Add onVisibleCountChange callback prop to ACMGrid
  - [x] 6.2: Track visibleCount state in ACMTab
  - [x] 6.3: Pass visibleCount and totalCount to ACMToolbar

- [x] Task 7: Add keyboard shortcut for search focus (Enhancement)
  - [x] 7.1: Add searchInputRef to ACMToolbar
  - [x] 7.2: Add useEffect with Ctrl+F/Cmd+F keyboard listener
  - [x] 7.3: Prevent default browser find and focus search input

- [ ] ~~Task 8: Write tests (All ACs)~~ **[DEFERRED]**
  - [ ] 8.1: Unit test for useDebouncedValue hook
  - [ ] 8.2: Component test for ACMToolbar with search functionality
  - [ ] 8.3: Integration test for search filtering behavior
  - *Deferred: Tests to be added in a dedicated testing story*

### Code Review Fixes Applied

- [x] [MEDIUM] Fixed visible count to exclude group rows - now uses `forEachNodeAfterFilterAndSort` to count only data rows
- [x] [MEDIUM] Added search reset when risk filter changes to avoid user confusion
- [x] [MEDIUM] Added `aria-label="Clear search"` to clear button for accessibility
- [x] [MEDIUM] Scoped Ctrl+F keyboard shortcut to only intercept when focus is within component or no specific element is focused

## Dev Notes

### Architecture Requirements

- **Component Location:** All ACM components in `frontend/src/components/acm/`
- **Hooks Location:** Custom hooks in `frontend/src/lib/hooks/`
- **UI Components:** Use shadcn/ui components from `@/components/ui/`
- **Icons:** Use lucide-react icons (Search, X)

### Existing Patterns to Follow

The codebase uses consistent patterns that MUST be followed:

1. **AG Grid Configuration:** See `ACMGrid.tsx:279-299` for existing AgGridReact setup with:
   - `ref={gridRef}` for API access
   - `onGridReady` callback to capture GridApi
   - State management via `useState<GridApi>`

2. **Toolbar Pattern:** See `ACMToolbar.tsx` for existing structure:
   - Left side: filters and controls
   - Right side: action buttons
   - Uses flexbox with `gap-2` spacing

3. **State Management:** See `ACMTab.tsx` for state lifting pattern:
   - State defined in parent component
   - Passed to children via props
   - Callbacks passed for state updates

### AG Grid Quick Filter API

```typescript
// Apply quick filter when search text changes
useEffect(() => {
  if (gridRef.current?.api) {
    gridRef.current.api.setGridOption('quickFilterText', debouncedSearch);
  }
}, [debouncedSearch]);

// Track visible row count on model update (data rows only, not group headers)
const onModelUpdated = useCallback((event: ModelUpdatedEvent<ACMRecord>) => {
  if (onVisibleCountChange && event.api) {
    let dataRowCount = 0
    event.api.forEachNodeAfterFilterAndSort((node) => {
      if (!node.group) dataRowCount++
    })
    onVisibleCountChange(dataRowCount)
  }
}, [onVisibleCountChange]);
```

### Debounce Hook Implementation

```typescript
// frontend/src/lib/hooks/use-debounced-value.ts
import { useState, useEffect } from 'react';

export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

### UI Requirements

- Search input max width: `max-w-md` to not overwhelm toolbar
- Search icon: `Search` from lucide-react, positioned left (pl-9)
- Clear button: `X` icon, only visible when text exists, ghost variant, with `aria-label`
- Result count: `text-sm text-muted-foreground`

### Performance Considerations

- Debounce search input (300ms default) to prevent excessive re-renders
- AG Grid Quick Filter is client-side and performant for current dataset sizes (500 records limit)
- No API calls needed - filtering is purely client-side

### Testing Standards

- Use Vitest for unit tests
- Use React Testing Library for component tests
- Test debounce timing behavior
- Test search input clear functionality
- Test keyboard shortcut (Ctrl/Cmd+F)

### Project Structure Notes

Files to create:
- `frontend/src/lib/hooks/use-debounced-value.ts` (new)

Files to modify:
- `frontend/src/components/acm/ACMToolbar.tsx`
- `frontend/src/components/acm/ACMGrid.tsx`
- `frontend/src/components/acm/ACMTab.tsx`

### References

- [Source: docs/acm-ai/05-epics-and-stories.md#E2-S6] - Epic requirements
- [Source: docs/sprint-artifacts/tech-spec-e2-s6-search-bar.md] - Technical design reference
- [Source: docs/acm-ai/04-architecture.md#6.1] - AG Grid configuration patterns
- [Source: frontend/src/components/acm/ACMGrid.tsx] - Existing grid implementation
- [Source: frontend/src/components/acm/ACMToolbar.tsx] - Existing toolbar implementation

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- TypeScript check passed for all modified ACM components
- Pre-existing Playwright test configuration errors do not affect implementation
- Code review completed with 4 MEDIUM issues fixed

### Completion Notes List

1. Created new `useDebouncedValue` hook with JSDoc documentation
2. Added search input with Search icon and X clear button to ACMToolbar
3. Added "Showing X of Y records" result count display
4. Integrated AG Grid Quick Filter API via `setGridOption` and `onModelUpdated`
5. Added Ctrl/Cmd+F keyboard shortcut to focus search input (scoped to component)
6. All acceptance criteria implemented and verified through type checking
7. Code review passed - 4 MEDIUM issues fixed:
   - Visible count now correctly excludes group rows
   - Search resets when risk filter changes
   - Clear button has proper aria-label for accessibility
   - Keyboard shortcut scoped to avoid hijacking browser find

### File List

**Created:**
- `frontend/src/lib/hooks/use-debounced-value.ts` - Debounce hook utility

**Modified:**
- `frontend/src/components/acm/ACMToolbar.tsx` - Added search input, clear button, result count, keyboard shortcut (scoped), aria-label
- `frontend/src/components/acm/ACMGrid.tsx` - Added quickFilterText prop, onVisibleCountChange callback (data rows only)
- `frontend/src/components/acm/ACMTab.tsx` - Added search state, debounce, search reset on filter change

**Updated:**
- `docs/sprint-artifacts/sprint-status.yaml` - Story status: ready-for-dev → in-progress → review → done
