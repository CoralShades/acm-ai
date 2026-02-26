You are Bob (Scrum Master). Create Sprint Change Proposal and story files for Epic 22.

## MANDATORY PRE-READ

Read these files first to understand current state:
- docs/sprint-artifacts/sprint-status.yaml
- _bmad-output/project-planning-artifacts/acm-ai/03-prd.md
- _bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml
- _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md

Also read these completed stories for format reference:
- docs/sprint-artifacts/e21-s1-loading-states-transitions.md
- docs/sprint-artifacts/e21-s2-jobs-layout-consistency.md
- docs/sprint-artifacts/e21-s3-extraction-progress-feedback.md
- docs/sprint-artifacts/e19-s7-job-detail-page.md

## EPIC 22: Post-Audit Remediation & Feature Completion

### Background

Phase 6+7 (Epic 21) completed loading states, layout consistency, and SSE wiring.
User testing with the Clutch Alexander District Hospital PDF revealed 10 remaining
issues across backend schema bugs, layout regressions, missing features, and UX gaps.

### Stories to Create

**E22-S1: Schema Resilience — Normalize Instead of Reject**
Priority: P0 (Backend)
As a system, I want field validators to normalize unexpected LLM values instead of rejecting entire buildings, so that extraction doesn't lose records due to minor enum mismatches.
Key ACs:
- risk_status validator normalizes "Moderate" → "Medium" instead of raising ValueError
- ALL field_validators in ACMExtractionRecord and acm_validator.py follow normalize-or-passthrough pattern
- No field validator raises ValueError for unexpected but close values — it normalizes and logs
- data_issues list captures normalization events (e.g., "Normalized risk_status: Moderate → Medium")
- All existing tests still pass
Files: open_notebook/extractors/acm_schemas.py, open_notebook/extractors/validators/acm_validator.py, open_notebook/extractors/normalizers/enums.py

**E22-S2: Dashboard Layout Regression Fix**
Priority: P0 (Frontend)
As a compliance officer, I want the dashboard to show the sidebar, header, and footer like all other pages, so the navigation is consistent.
Key ACs:
- Dashboard (/) renders inside the (dashboard) layout wrapper with sidebar
- All pages in (dashboard) route group show consistent sidebar + header + footer
- loading.tsx files don't break the layout wrapper
- No blank white screen on dashboard navigation
Files: frontend/src/app/(dashboard)/page.tsx, frontend/src/app/(dashboard)/layout.tsx

**E22-S3: Job Detail Page = Source Detail Layout (PDF + Chat + Content)**
Priority: P1 (Frontend — LARGEST story)
As a compliance officer, I want the job detail page to show the PDF preview, extracted text, and chat widget in the same layout as the source document page, so I can review everything in context.
Key ACs:
- New "Content" tab on job detail page showing: rendered markdown of source.full_text (styled with react-markdown), PDF file download/preview link
- Chat widget/panel on right side of job detail page (inline, not separate route)
- Uses existing CopilotProvider + CRUD chat endpoint
- Chat panel collapses on narrow screens to floating button
- Unicode arrows on all buttons render correctly (not \u2192 text)
- Job detail matches Source Detail page layout (two-column: content left, chat right)
Reference: frontend/src/app/(dashboard)/sources/[id]/page.tsx, tech-spec-e8-s7-source-detail.md

**E22-S4: Building Tabs in ACM Register + Job ACM Records**
Priority: P1 (Frontend)
As a compliance officer, I want per-building tabs above the records grid on both the ACM Register page and the Job Detail ACM Records tab, so I can filter records by building instead of scrolling through all records.
Key ACs:
- Reusable BuildingTabFilter component extracted from review records page
- Tabs show: [All Records (N)] [Building A (X)] [Building B (Y)] ...
- Selecting a tab filters the AG Grid to that building's records
- Tabs scroll horizontally when there are many buildings (no overlap)
- Tab spacing fixed (no text overlapping as in review wizard)
- Building counts accurate and update when records change
- Wired into: /acm page, /jobs/[id] ACM Records tab, /jobs/[id]/review/records
Reference: frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx (already has building tabs)

**E22-S5: Extraction Streaming & Navigation Polish**
Priority: P1 (Frontend + optional Backend)
As a compliance officer, I want to see meaningful progress during extraction and smooth page transitions, so the system feels responsive.
Key ACs:
- During extraction, show stage-by-stage progress prominently (stage names, X/7, elapsed time)
- When extraction completes, immediately fetch and display records (auto-poll records endpoint)
- Global navigation progress bar during Next.js page compilation
- Smooth loading indicator when clicking between pages
- Provider schema/compat errors logged in extraction log UI (not hidden)
- If backend Option B: records saved per-building, SSE emits per-building events
Files: frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx, frontend/src/hooks/use-extraction-progress.ts

## FILES TO CREATE

1. docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260226-post-phase67-remediation.md
   - Standard SCP format (see existing SCPs in that directory)
   - Reference Epic 22, 5 stories, dependency chain

2. docs/sprint-artifacts/e22-s1-schema-resilience.md
3. docs/sprint-artifacts/e22-s2-dashboard-layout-fix.md
4. docs/sprint-artifacts/e22-s3-job-detail-source-layout.md
5. docs/sprint-artifacts/e22-s4-building-tabs-everywhere.md
6. docs/sprint-artifacts/e22-s5-extraction-streaming-polish.md

Each story file should follow the EXACT format of existing stories (e.g., e21-s1).
Include: YAML frontmatter, user story, acceptance criteria (as checkboxes),
technical notes with key files, and guard rails.

## ARTIFACTS TO UPDATE

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
# Epic 22: Post-Audit Remediation & Feature Completion (P0/P1)
# 0/5 stories complete — EPIC IN PROGRESS
# SCP: docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260226-post-phase67-remediation.md
epic-22: in-progress
e22-s1-schema-resilience: drafted
e22-s2-dashboard-layout-fix: drafted
e22-s3-job-detail-source-layout: drafted
e22-s4-building-tabs-everywhere: drafted
e22-s5-extraction-streaming-polish: drafted
```

Update _bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml change log:
```
# 2026-02-26: SCP-20260226B — Epic 22 Post Phase 6+7 Remediation
#   - 5 stories drafted for schema resilience, dashboard layout, job detail redesign,
#     building tabs, and extraction streaming polish
#   - Triggered by: user testing screenshots showing 10 remaining issues
#   - Dependencies: E22-S1 (backend) runs first, S2-S4 (frontend) in parallel, S5 last
```

Update _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md:
Add Epic 22 section with all 5 stories.

## GUARD RAILS
- PLANNING ONLY — do NOT modify any code files
- Use existing story format exactly
- All story files go in docs/sprint-artifacts/
- COMMIT: git add docs/ _bmad-output/ && git commit -m "docs(bmad): SCP-20260226B Epic 22 post-remediation sprint — 5 stories"
