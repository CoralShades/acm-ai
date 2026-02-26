---
epic: Epic 22
story_id: E22-S2
title: Dashboard Layout Regression Fix
status: done
---

As a compliance officer,
I want the dashboard to show the sidebar, header, and footer like all other pages,
So that navigation and page structure remain consistent.

Acceptance Criteria:
- [x] Dashboard (`/`) renders inside the `(dashboard)` layout wrapper with sidebar
- [x] All pages in the `(dashboard)` route group show consistent sidebar + header + footer
- [x] `loading.tsx` files do not break or bypass the layout wrapper
- [x] No blank white screen appears during dashboard navigation

Technical Notes:
- Ensure `frontend/src/app/(dashboard)/page.tsx` is rendered through `frontend/src/app/(dashboard)/layout.tsx` under all loading states
- Verify route-group behavior in Next.js App Router so loading boundaries preserve shell chrome
- Align dashboard entry route behavior with existing jobs/acm/source routes already using the shared layout

Key Files:
- frontend/src/app/(dashboard)/page.tsx
- frontend/src/app/(dashboard)/layout.tsx

Guard Rails:
- Do not introduce route-specific layout forks for `/`; use the existing shared dashboard shell
- Do not regress existing pages already rendering correctly within the `(dashboard)` group
- Keep this story focused on layout wrapper consistency and navigation stability only

## Sprint Status

- `docs/sprint-artifacts/sprint-status.yaml` updated to `e22-s2-dashboard-layout-fix: done` (2026-02-26)

## Workflow Status

- [x] Investigation complete: route placement, layout wrapper, middleware redirects, loading files, and layout/CSS checks
- [x] Root cause confirmed: `frontend/src/app/(dashboard)/page.tsx` rendered page content directly without shared shell wrapper
- [x] Fix complete: wrapped dashboard content in `AppShell` to restore sidebar/header/footer on `/`
- [x] Verification complete: `npm run build`, `npm run lint`, and manual navigation/theme/sidebar interactions

## Documented Changes

- `frontend/src/app/(dashboard)/page.tsx`
  - Added `AppShell` wrapper around `DashboardPageContent`
  - Updated main container class to full-height scrollable layout inside shared shell
- `docs/sprint-artifacts/sprint-status.yaml`
  - Marked story as done with root-cause/fix note

## Change Log

- 2026-02-26: Fixed dashboard root layout regression by restoring shared shell usage on `/` and documented sprint/workflow completion status.
