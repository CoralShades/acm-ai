You are implementing E22-S4: Building Tabs in ACM Register + Job ACM Records.
You are Amelia (Developer). Frontend-only.

## MANDATORY PRE-READ — Read ALL before writing ANY code

### Your story:
- docs/sprint-artifacts/e22-s4-building-tabs-everywhere.md

### THE REFERENCE (page that ALREADY HAS building tabs — extract this pattern):
- frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx
  Study how it creates building tabs: "All Records (16) | Mortuary Buildings (7) | ..."
  Study how it filters the grid when a tab is selected.

### Pages that NEED building tabs:
- frontend/src/app/(dashboard)/acm/page.tsx — ACM Register
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx — Job Detail ACM Records tab

### The grid component:
- frontend/src/components/acm/ACMSpreadsheet.tsx

### Existing tab components:
- Check what Tab/TabsList/TabsTrigger is used from shadcn/ui
- grep -rn "TabsTrigger\|TabsList" frontend/src/ --include="*.tsx" | head -10

## DESIGN BRIEF

The review records page (Step 2 of the review wizard) already has building tabs:
```
[All Records (16)] [Mortuary Buildings (7)] [Myrtle Street Clinic (2)] [Nurses Accom (2)] [Pathology Dept (1)] [VMO Accom (4)]
```

But the ACM Register page and the Job Detail ACM Records tab show ALL records
flat with no building grouping. The user wants the SAME building tabs everywhere.

Problem from screenshots: the existing building tabs in the review wizard have
overlapping text when there are many buildings (bad spacing). Fix this too.

## IMPLEMENTATION TASKS

### Task 1: Extract BuildingTabFilter as Reusable Component

Study the review records page to understand how building tabs are created.
Extract the tab-building logic into a reusable component:

```tsx
// frontend/src/components/acm/BuildingTabFilter.tsx

interface BuildingTabFilterProps {
  records: ACMRecord[]           // All records for the source
  selectedBuilding: string | null // null = "All Records"
  onBuildingChange: (buildingId: string | null) => void
}

export function BuildingTabFilter({ records, selectedBuilding, onBuildingChange }: BuildingTabFilterProps) {
  // Group records by building
  // Create a tab for each building with record count
  // Handle "All Records" tab
  // Horizontal scroll when too many tabs (overflow-x-auto)
  // Fix spacing so tabs don't overlap
}
```

Key implementation details:
- Group records by building name/code
- Count records per building
- Render as horizontal scrollable tab bar
- Use `overflow-x-auto` with `whitespace-nowrap` to prevent overlap
- Each tab shows: "Building Name (count)"
- "All Records (total)" as first tab, always selected by default

### Task 2: Fix Tab Overlap/Spacing

The current review wizard building tabs overlap (Image 10 annotation).
Root cause is likely:
- Tabs using `flex-wrap` when they should use `overflow-x-auto`
- Or no `whitespace-nowrap` on the tab container
- Or min-width not set on individual tabs

Fix:
```tsx
<div className="flex overflow-x-auto gap-1 pb-2 border-b scrollbar-thin">
  {buildings.map(building => (
    <button
      key={building.id}
      className={cn(
        "px-3 py-1.5 text-sm rounded-md whitespace-nowrap transition-colors",
        "hover:bg-muted",
        selectedBuilding === building.id
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground"
      )}
      onClick={() => onBuildingChange(building.id)}
    >
      {building.name} ({building.count})
    </button>
  ))}
</div>
```

### Task 3: Wire into ACM Register Page

File: `frontend/src/app/(dashboard)/acm/page.tsx`

Add BuildingTabFilter above the ACM grid:
1. Get the list of unique buildings from the records data
2. Add state: `const [selectedBuilding, setSelectedBuilding] = useState<string | null>(null)`
3. Filter records passed to ACMSpreadsheet based on selected building
4. Place BuildingTabFilter between the toolbar and the grid

### Task 4: Wire into Job Detail ACM Records Tab

File: `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`

In the ACM Records tab content:
1. Same pattern as Task 3
2. Add BuildingTabFilter above the records grid
3. Filter records by selected building

### Task 5: Update Review Records Page to Use Reusable Component

File: `frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx`

Replace the inline building tab logic with the new BuildingTabFilter component.
This ensures consistency and removes duplicate code.

### Task 6: Verification

```bash
cd frontend
npm run build    # MUST pass
npm run lint     # MUST pass
```

Manual checks:
- ACM Register page: building tabs appear, clicking filters records
- Job Detail ACM Records tab: building tabs appear, clicking filters records
- Review records wizard: building tabs still work, no overlap
- Tab counts match record counts per building
- Horizontal scroll works when many buildings
- "All Records" tab shows total count

### Task 7: Update BMAD Artifacts

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
e22-s4-building-tabs-everywhere: done  # 2026-02-26: Reusable BuildingTabFilter component, wired into ACM Register + Job Detail ACM Records + review records. Horizontal scroll, no overlap.
```

### Task 8: Git Commit

```bash
git add frontend/ docs/
git commit -m "feat(e22-s4): building tabs in ACM Register and Job Detail

- New reusable BuildingTabFilter component
- Wired into ACM Register page (/acm)
- Wired into Job Detail ACM Records tab
- Updated review records wizard to use shared component
- Fixed tab overlap/spacing with horizontal scroll
- Building counts accurate and reactive"
```

## GUARD RAILS
- Do NOT modify Python files
- Do NOT change AG Grid column definitions or data models
- Do NOT modify the review wizard flow (step progression, publish logic)
- Do NOT change how records are fetched — only how they're filtered client-side
- REUSE existing shadcn/ui Tab components where possible
- The component should work with zero records (show empty state)
