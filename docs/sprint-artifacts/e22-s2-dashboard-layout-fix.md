---
epic: Epic 22
story_id: E22-S2
title: Dashboard Layout Regression Fix
status: drafted
---

As a compliance officer,
I want the dashboard to show the sidebar, header, and footer like all other pages,
So that navigation and page structure remain consistent.

Acceptance Criteria:
- [ ] Dashboard (`/`) renders inside the `(dashboard)` layout wrapper with sidebar
- [ ] All pages in the `(dashboard)` route group show consistent sidebar + header + footer
- [ ] `loading.tsx` files do not break or bypass the layout wrapper
- [ ] No blank white screen appears during dashboard navigation

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
