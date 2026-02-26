---
epic: Epic 22
story_id: E22-S3
title: Job Detail Page Matches Source Detail Layout (PDF + Chat + Content)
status: drafted
---

As a compliance officer,
I want the job detail page to show the PDF preview, extracted text, and chat widget in the same layout as the source document page,
So that I can review all context and actions from one place.

Acceptance Criteria:
- [ ] Add a new `Content` tab on job detail with rendered markdown from `source.full_text` and a PDF download/preview link
- [ ] Add an inline chat panel on the right side of job detail (not a separate route)
- [ ] Use existing `CopilotProvider` and CRUD chat endpoint integration
- [ ] Chat panel collapses on narrow screens into a floating button workflow
- [ ] Unicode arrow labels on buttons render correctly as glyphs (not escaped `\\u2192` text)
- [ ] Job detail layout matches Source Detail two-column pattern (content left, chat right)

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
