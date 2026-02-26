---
epic: Epic 22
story_id: E22-S4
title: Building Tabs in ACM Register and Job ACM Records
status: drafted
---

As a compliance officer,
I want per-building tabs above records grids on the ACM Register and Job Detail ACM Records tab,
So that I can filter records by building instead of scrolling through everything.

Acceptance Criteria:
- [ ] Extract a reusable `BuildingTabFilter` component from the review records page implementation
- [ ] Tabs display as: `[All Records (N)] [Building A (X)] [Building B (Y)] ...`
- [ ] Selecting a tab filters AG Grid rows to the selected building
- [ ] Tabs scroll horizontally when building count is high, with no overlap
- [ ] Tab spacing is fixed so labels do not overlap (review wizard regression resolved)
- [ ] Building counts are accurate and update when records change
- [ ] Wire the reusable tabs into `/acm`, `/jobs/[id]` ACM Records tab, and `/jobs/[id]/review/records`

Technical Notes:
- Use existing review records behavior in `frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx` as the extraction source
- Keep filtering logic consistent across all three surfaces to avoid divergent counting/filter rules
- Ensure tabs remain keyboard accessible and usable on smaller viewports via horizontal scrolling

Key Files:
- frontend/src/app/(dashboard)/acm/page.tsx
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx
- frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx
- frontend/src/components/acm/BuildingTabFilter.tsx

Guard Rails:
- Do not duplicate tab implementations per page; shared component is required
- Do not break existing AG Grid sorting/filtering while applying building-level filtering
- Keep count computation source-of-truth aligned with the currently loaded row set
