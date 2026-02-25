---
epic: Epic 21
story_id: E21-S3
title: Extraction Progress Real-Time Feedback
status: drafted
---

As a compliance officer,
I want to see real-time progress when my document is being extracted,
So that I know the system is working and how long it will take.

Acceptance Criteria:
- [ ] After upload + extraction trigger, user sees animated progress indicator
- [ ] Progress indicator shows: current stage name, stage progress (x/7), elapsed time
- [ ] Stages light up sequentially as extraction progresses through pipeline
- [ ] When extraction completes, auto-transition to review page (or show "Review" CTA)
- [ ] If extraction fails, show clear error message with retry button
- [ ] Extraction progress visible from both:
  a) The job detail page (/jobs/[id]) — in an "Extraction" tab
  b) The jobs list (/jobs) — as a progress bar on the job card
- [ ] Uses existing SSE infrastructure from E15/E17 (PipelineLogger + ExtractionProgressPanel)

Technical Notes:
- The SSE infrastructure EXISTS (E17-S1, E15-S1) but is not wired into the E19 jobs flow
- ExtractionProgressPanel.tsx already renders stage progress — just not shown in jobs
- use-extraction-progress.ts hook exists — import it in job pages
- Wire: /jobs/[id] extraction tab → ExtractionProgressPanel → use-extraction-progress
- Add condensed progress bar to JobCard component for list view

Key Files:
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx (MODIFY - add extraction tab content)
- frontend/src/components/jobs/JobCard.tsx (MODIFY - add progress indicator)
- frontend/src/components/acm/ExtractionProgressPanel.tsx (existing, wire in)
- frontend/src/hooks/use-extraction-progress.ts (existing, import)
