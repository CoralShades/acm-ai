---
epic: Epic 22
story_id: E22-S5
title: Extraction Streaming and Navigation Polish
status: drafted
---

As a compliance officer,
I want to see meaningful extraction progress and smooth page transitions,
So that the system feels responsive and trustworthy during long-running operations.

Acceptance Criteria:
- [ ] During extraction, show stage-by-stage progress prominently (stage names, X/7, elapsed time)
- [ ] When extraction completes, immediately fetch and display records (auto-poll records endpoint)
- [ ] Show a global navigation progress bar during Next.js page compilation/transitions
- [ ] Show smooth loading indicators when clicking between pages
- [ ] Provider schema/compatibility errors are visible in extraction log UI (not hidden)
- [ ] Optional backend path: if records are saved per-building, SSE emits per-building events

Technical Notes:
- Enhance extraction status UX in `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` with explicit stage framing and completion handoff
- Extend `frontend/src/hooks/use-extraction-progress.ts` for robust completion detection and immediate records refresh behavior
- Reuse existing SSE infrastructure first; optional backend work is only for per-building event granularity if needed
- Keep failure modes visible so provider/schema issues are surfaced to users and not swallowed in logs

Key Files:
- frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx
- frontend/src/hooks/use-extraction-progress.ts

Guard Rails:
- Do not replace existing SSE plumbing with polling-only behavior
- Do not hide provider compatibility errors behind generic failure messages
- Keep optional backend scope isolated; frontend polish goals must ship even if backend Option B is deferred
