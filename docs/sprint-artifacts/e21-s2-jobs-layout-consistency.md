---
epic: Epic 21
story_id: E21-S2
title: Jobs Pages Layout Consistency
status: drafted
---

As a compliance officer,
I want the jobs/review pages to use the same professional layout as the ACM Register page,
So that the UI feels consistent and polished throughout the workflow.

Acceptance Criteria:
- [ ] Jobs dashboard (/jobs) uses same card layout patterns as Dashboard home
- [ ] Job detail page (/jobs/[id]) uses same panel layout as Source Detail page
- [ ] Building review (/jobs/[id]/review/buildings) uses:
  - Same toolbar pattern as ACM Register (search, filters, actions bar)
  - Same AG Grid styling (row heights, header styles, hover states)
  - Same card wrapper with border and shadow
- [ ] Records review (/jobs/[id]/review/records) uses:
  - Same tab pattern as Job Detail page
  - Same AG Grid configuration as ACM Register
  - Same empty state patterns as E16-S3
- [ ] All pages use consistent spacing (p-6 outer, gap-4 between sections)
- [ ] All pages use VAEA design tokens from E14-S1
- [ ] Dark mode works consistently across all job pages

Technical Notes:
- DO NOT rebuild from scratch — adapt existing E19 components to match E14 patterns
- The "layout I like" is the ACM Register page: /acm
  - Study: frontend/src/app/(dashboard)/acm/page.tsx
  - Study: frontend/src/components/acm/ACMSpreadsheet.tsx
  - Apply same patterns to jobs pages
- Key design elements to copy from ACM Register:
  1. Top stats bar with summary cards
  2. Toolbar with search + filter + action buttons
  3. AG Grid with consistent column defs
  4. Card wrapper with rounded corners + shadow
- Reference existing skeletons from E14-S4 for loading states

Key Files to Modify:
- frontend/src/app/(dashboard)/jobs/page.tsx
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx
- frontend/src/app/(dashboard)/jobs/[id]/review/buildings/page.tsx
- frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx
- frontend/src/components/jobs/ (various components)
