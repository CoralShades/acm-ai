---
epic: Epic 21
story_id: E21-S1
title: Global Loading States & Transition Feedback
status: drafted
---

As a compliance officer,
I want visual feedback when pages load, buttons process, and extraction runs,
So that the app doesn't feel broken or unresponsive.

Acceptance Criteria:
- [ ] Button click states: all primary action buttons show spinner/disabled during API calls
- [ ] Page transitions: shimmer skeleton appears immediately when navigating between routes
  (Dashboard, Jobs, Buildings Review, Records Review, ACM Register, Settings)
- [ ] Extraction feedback: when extraction is running, show animated progress indicator
  on the job card AND on the extraction tab (not just empty space)
- [ ] Upload feedback: after file upload, show processing state before redirect
- [ ] API loading: all data-fetching components show skeleton (reuse E14-S4 patterns)
- [ ] Empty → Loading → Content → Error state machine for every page
- [ ] No blank white screens during any navigation

Technical Notes:
- Reuse existing Skeleton components from E14-S4 (frontend/src/components/skeletons/)
- Reuse shimmer animation from globals.css
- Add React Suspense boundaries at route level in app/(dashboard)/layout.tsx
- Add loading.tsx files for each route group (Next.js convention)
- Use React Query isLoading/isFetching states in all data components
- Add useTransition() for client-side navigation feedback
- Reference: E14-S4 tech spec for shimmer patterns

Key Files:
- frontend/src/app/(dashboard)/jobs/loading.tsx (NEW)
- frontend/src/app/(dashboard)/jobs/[id]/loading.tsx (NEW)
- frontend/src/app/(dashboard)/jobs/[id]/review/buildings/loading.tsx (NEW)
- frontend/src/app/(dashboard)/jobs/[id]/review/records/loading.tsx (NEW)
- frontend/src/app/(dashboard)/acm/loading.tsx (NEW)
- frontend/src/components/ui/LoadingButton.tsx (NEW or enhance existing)
- frontend/src/components/acm/ExtractionProgressPanel.tsx (MODIFY - enhance feedback)
