# Tech Spec: E2-S6 - Add Search Bar to Spreadsheet

> **Story:** E2-S6
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Add a global search bar above the ACM spreadsheet that filters rows across all columns in real-time.

---

## User Story

**As a** user
**I want** to search across all columns
**So that** I can find any text in the data

---

## Acceptance Criteria

- [ ] Search input above grid
- [ ] Typing filters visible rows in real-time
- [ ] Searches across all text columns
- [ ] Clear button resets search
- [ ] Result count shown ("Showing X of Y records")

---

## Technical Design

### 1. Search Bar Component

Add search input to `ACMSpreadsheet.tsx`:

```tsx
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function ACMSpreadsheet({ sourceId }: Props) {
  const gridRef = useRef<AgGridReact>(null);
  const [searchText, setSearchText] = useState('');
  const [visibleCount, setVisibleCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  // Apply quick filter when search text changes
  useEffect(() => {
    if (gridRef.current?.api) {
      gridRef.current.api.setGridOption('quickFilterText', searchText);
    }
  }, [searchText]);

  // Track row counts
  const onModelUpdated = useCallback(() => {
    if (gridRef.current?.api) {
      setVisibleCount(gridRef.current.api.getDisplayedRowCount());
      setTotalCount(acmRecords?.length || 0);
    }
  }, [acmRecords]);

  const clearSearch = () => {
    setSearchText('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search Bar */}
      <div className="flex items-center gap-4 p-3 border-b bg-muted/30">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search all columns..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="pl-9 pr-9"
          />
          {searchText && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={clearSearch}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Result Count */}
        <span className="text-sm text-muted-foreground">
          Showing {visibleCount} of {totalCount} records
        </span>
      </div>

      {/* Grid */}
      <div className="ag-theme-custom flex-1">
        <AgGridReact
          ref={gridRef}
          onModelUpdated={onModelUpdated}
          // ... other props
        />
      </div>
    </div>
  );
}
```

### 2. Debounced Search (Performance)

For large datasets, debounce the search:

```tsx
import { useDebouncedValue } from '@/hooks/use-debounced-value';

const [searchText, setSearchText] = useState('');
const debouncedSearch = useDebouncedValue(searchText, 300);

useEffect(() => {
  if (gridRef.current?.api) {
    gridRef.current.api.setGridOption('quickFilterText', debouncedSearch);
  }
}, [debouncedSearch]);
```

### 3. Custom Quick Filter (Optional)

If you need to customize which columns are searchable:

```tsx
const doesExternalFilterPass = useCallback((node: IRowNode<ACMRecord>) => {
  if (!searchText) return true;

  const data = node.data;
  if (!data) return false;

  const searchLower = searchText.toLowerCase();

  // Search specific fields
  return (
    data.school_name?.toLowerCase().includes(searchLower) ||
    data.building_id?.toLowerCase().includes(searchLower) ||
    data.building_name?.toLowerCase().includes(searchLower) ||
    data.room_id?.toLowerCase().includes(searchLower) ||
    data.product?.toLowerCase().includes(searchLower) ||
    data.material_description?.toLowerCase().includes(searchLower) ||
    data.risk_status?.toLowerCase().includes(searchLower)
  );
}, [searchText]);

<AgGridReact
  isExternalFilterPresent={() => !!searchText}
  doesExternalFilterPass={doesExternalFilterPass}
/>
```

### 4. Keyboard Shortcut

Add Cmd/Ctrl+F to focus search:

```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
      e.preventDefault();
      searchInputRef.current?.focus();
    }
  };

  document.addEventListener('keydown', handleKeyDown);
  return () => document.removeEventListener('keydown', handleKeyDown);
}, []);
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add search bar |
| `frontend/src/hooks/use-debounced-value.ts` | New hook (if not exists) |

---

## Dependencies

- E2-S2: ACMSpreadsheet component created

---

## Testing

1. Type in search box - verify rows filter in real-time
2. Verify search works across all text columns
3. Click X button - verify search clears
4. Verify result count updates correctly
5. Test with empty search - verify all rows shown
6. Test Cmd/Ctrl+F keyboard shortcut
7. Test performance with large dataset (500+ rows)

---

## Estimated Complexity

**Low** - Uses AG Grid Quick Filter API

---
