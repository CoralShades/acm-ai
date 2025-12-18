# Tech Spec: E2-S7 - Implement Building Tab Navigation

> **Story:** E2-S7
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Implement building tab navigation above the ACM spreadsheet to enable quick filtering between buildings in a school. This matches the existing MVP pattern at acm.coralshades.ai where users can click building tabs (B00A, B00B, etc.) to view records for specific buildings.

---

## User Story

**As a** user
**I want** ACM data organized by building tabs
**So that** I can quickly navigate between buildings in a school

---

## Acceptance Criteria

- [ ] Tab bar above spreadsheet showing all buildings (e.g., B00A, B00B, B00C)
- [ ] Tab shows building code and record count (e.g., "B00A (4)")
- [ ] Clicking tab filters grid to show only that building's records
- [ ] "All Buildings" tab option to show combined view
- [ ] Active tab visually highlighted
- [ ] Tabs auto-generated from ACM data (no hardcoding)
- [ ] Smooth transition when switching tabs
- [ ] Remember last selected tab per source (session persistence)

---

## Technical Design

### 1. Building Tabs Component

#### Location: `frontend/src/components/acm/BuildingTabs.tsx`

```tsx
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMemo } from "react";

interface BuildingTab {
  building_id: string;
  building_code: string;
  record_count: number;
}

interface BuildingTabsProps {
  records: ACMRecord[];
  selectedBuilding: string | null;
  onBuildingChange: (buildingId: string | null) => void;
}

export function BuildingTabs({
  records,
  selectedBuilding,
  onBuildingChange,
}: BuildingTabsProps) {
  // Extract unique buildings with counts
  const buildings = useMemo(() => {
    const buildingMap = new Map<string, BuildingTab>();

    records.forEach((record) => {
      const existing = buildingMap.get(record.building_id);
      if (existing) {
        existing.record_count++;
      } else {
        buildingMap.set(record.building_id, {
          building_id: record.building_id,
          building_code: record.building_code || record.building_id,
          record_count: 1,
        });
      }
    });

    // Sort alphabetically by building code
    return Array.from(buildingMap.values()).sort((a, b) =>
      a.building_code.localeCompare(b.building_code)
    );
  }, [records]);

  return (
    <Tabs
      value={selectedBuilding || "all"}
      onValueChange={(value) =>
        onBuildingChange(value === "all" ? null : value)
      }
    >
      <TabsList className="flex flex-wrap gap-1">
        {/* All Buildings tab */}
        <TabsTrigger
          value="all"
          className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
        >
          All Buildings ({records.length})
        </TabsTrigger>

        {/* Individual building tabs */}
        {buildings.map((building) => (
          <TabsTrigger
            key={building.building_id}
            value={building.building_id}
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            {building.building_code} ({building.record_count})
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
```

### 2. Integration with ACMGrid

#### Update: `frontend/src/components/acm/ACMGrid.tsx`

```tsx
import { BuildingTabs } from "./BuildingTabs";
import { useSessionStorage } from "@/hooks/useSessionStorage";
import { useMemo, useCallback } from "react";

interface ACMGridProps {
  sourceId: string;
  records: ACMRecord[];
}

export function ACMGrid({ sourceId, records }: ACMGridProps) {
  // Session persistence for selected building
  const [selectedBuilding, setSelectedBuilding] = useSessionStorage<string | null>(
    `acm-building-${sourceId}`,
    null
  );

  // Filter records by selected building
  const filteredRecords = useMemo(() => {
    if (!selectedBuilding) return records;
    return records.filter((r) => r.building_id === selectedBuilding);
  }, [records, selectedBuilding]);

  const handleBuildingChange = useCallback((buildingId: string | null) => {
    setSelectedBuilding(buildingId);
  }, [setSelectedBuilding]);

  return (
    <div className="flex flex-col gap-4">
      {/* Building Tabs */}
      <BuildingTabs
        records={records}
        selectedBuilding={selectedBuilding}
        onBuildingChange={handleBuildingChange}
      />

      {/* AG Grid with filtered data */}
      <div className="ag-theme-alpine h-[600px]">
        <AgGridReact
          rowData={filteredRecords}
          columnDefs={columnDefs}
          // ... other grid props
        />
      </div>
    </div>
  );
}
```

### 3. Session Storage Hook

#### Location: `frontend/src/hooks/useSessionStorage.ts`

```tsx
import { useState, useEffect, useCallback } from "react";

export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void] {
  // Initialize state from session storage or initial value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;

    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Update session storage when value changes
  const setValue = useCallback(
    (value: T) => {
      try {
        setStoredValue(value);
        if (typeof window !== "undefined") {
          window.sessionStorage.setItem(key, JSON.stringify(value));
        }
      } catch (error) {
        console.warn(`Error setting sessionStorage key "${key}":`, error);
      }
    },
    [key]
  );

  return [storedValue, setValue];
}
```

### 4. Styling

#### Tab Styling (add to `globals.css` or component)

```css
/* Building tabs styling */
.building-tabs {
  @apply flex flex-wrap gap-1 p-1 bg-muted rounded-lg;
}

.building-tab {
  @apply px-3 py-1.5 text-sm font-medium rounded-md transition-colors;
  @apply hover:bg-background hover:text-foreground;
}

.building-tab[data-state="active"] {
  @apply bg-primary text-primary-foreground shadow-sm;
}

/* Tab with high-risk indicator (optional enhancement) */
.building-tab--has-high-risk {
  @apply border-l-2 border-l-destructive;
}
```

### 5. Optional Enhancement: Risk Indicators per Building

```tsx
// Enhanced building tab with risk summary
const buildingsWithRisk = useMemo(() => {
  const buildingMap = new Map<string, BuildingTab & { hasHighRisk: boolean }>();

  records.forEach((record) => {
    const existing = buildingMap.get(record.building_id);
    const isHighRisk = record.risk_status === "High";

    if (existing) {
      existing.record_count++;
      existing.hasHighRisk = existing.hasHighRisk || isHighRisk;
    } else {
      buildingMap.set(record.building_id, {
        building_id: record.building_id,
        building_code: record.building_code || record.building_id,
        record_count: 1,
        hasHighRisk: isHighRisk,
      });
    }
  });

  return Array.from(buildingMap.values()).sort((a, b) =>
    a.building_code.localeCompare(b.building_code)
  );
}, [records]);

// In render:
<TabsTrigger
  value={building.building_id}
  className={cn(
    "data-[state=active]:bg-primary",
    building.hasHighRisk && "border-l-2 border-l-destructive"
  )}
>
  {building.building_code} ({building.record_count})
  {building.hasHighRisk && <AlertTriangle className="w-3 h-3 ml-1 text-destructive" />}
</TabsTrigger>
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/BuildingTabs.tsx` | New component |
| `frontend/src/components/acm/ACMGrid.tsx` | Integrate BuildingTabs |
| `frontend/src/hooks/useSessionStorage.ts` | New hook (if not exists) |
| `frontend/src/app/globals.css` | Add tab styling (optional) |

---

## Dependencies

- E2-S2: ACMSpreadsheet Component (must be complete)
- E2-S4: Row Grouping (should be complete for consistency)
- Radix UI Tabs (already installed via shadcn/ui)

---

## Testing

1. Load ACM data with multiple buildings
2. Verify tabs show correct building codes and counts
3. Click each tab and verify grid filters correctly
4. Click "All Buildings" and verify full data shows
5. Refresh page and verify last selected tab persists
6. Test with source that has single building (should still work)
7. Test with source that has no ACM data (tabs should handle gracefully)

---

## Edge Cases

| Case | Behavior |
|------|----------|
| No ACM records | Hide tabs, show empty state |
| Single building | Still show tabs with "All" and building |
| Building code missing | Use building_id as fallback |
| Large number of buildings | Tabs wrap to multiple lines |

---

## Reference

Existing MVP pattern at `acm.coralshades.ai`:
- Tab bar with building codes: B00A, B00B, B00C, etc.
- Record count in parentheses
- Highlighted active tab
- Spreadsheet filters immediately on tab click

---

## Estimated Complexity

**Low** - Straightforward UI component with client-side filtering

---
