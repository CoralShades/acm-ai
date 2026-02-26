---
epic: Epic 22
story_id: E22-S3
title: Job Detail Page Matches Source Detail Layout (PDF + Chat + Content)
status: done
---

As a compliance officer,
I want the job detail page to show the PDF preview, extracted text, and chat widget in the same layout as the source document page,
So that I can review all context and actions from one place.

Acceptance Criteria:
- [x] Add a new `Content` tab on job detail with rendered markdown from `source.full_text` and a PDF download/preview link
- [x] Add an inline chat panel on the right side of job detail (not a separate route)
- [x] Use existing `CopilotProvider` and CRUD chat endpoint integration
- [x] Chat panel collapses on narrow screens into a floating button workflow
- [x] Unicode arrow labels on buttons render correctly as glyphs (not escaped `\\u2192` text)
- [x] Job detail layout matches Source Detail two-column pattern (content left, chat right)

Technical Notes:
- Use `frontend/src/app/(dashboard)/sources/[id]/page.tsx` as the structural reference for panel composition and responsive breakpoints
- Render markdown with `react-markdown` using the existing app styling patterns for prose content
- Keep chat state and actions inside the job detail page context so CRUD operations remain source-scoped
- Reference design intent from `docs/sprint-artifacts/tech-spec-e8-s7-source-detail.md`

Key Files:
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx
- frontend/src/app/(dashboard)/sources/[id]/page.tsx
- docs/sprint-artifacts/tech-spec-e8-s7-source-detail.md

Guard Rails:
- Do not create a separate `/jobs/[id]/chat` route as part of this story
- Preserve existing job detail tabs and actions while adding `Content` and inline chat behavior
- Keep mobile behavior accessible and deterministic (collapse pattern, no hidden unreachable chat)

## Dev Agent Record

- Implemented Source-style two-column job detail layout with left tabbed content and right inline CRUD chat panel.
- Added `Content` tab rendering `source.full_text` markdown and exposing `Open PDF` + `Download PDF` actions.
- Reused existing CRUD runtime via `/copilot-crud` and kept `/jobs/[id]/chat` route as fallback.
- Added desktop chat collapse toggle and mobile floating-chat-sheet behavior.
- Fixed arrow rendering issues in job flow buttons by switching to icon-backed labels.

## File List

- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- `frontend/src/components/jobs/JobContentPanel.tsx`
- `frontend/src/components/jobs/JobCrudChatPanel.tsx`
- `frontend/src/components/jobs/CrudToolRenderers.tsx`
- `frontend/src/app/(dashboard)/jobs/[id]/chat/page.tsx`
- `frontend/src/components/acm/WizardStepHeader.tsx`
- `frontend/src/app/(dashboard)/jobs/[id]/review/buildings/page.tsx`
- `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx`
- `frontend/src/app/(dashboard)/page.tsx`
- `docs/sprint-artifacts/sprint-status.yaml`
