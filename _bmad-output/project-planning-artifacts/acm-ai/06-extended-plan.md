# Extended Implementation Plan - ACM-AI v4.0

> **Created:** 2025-12-07
> **Last Updated:** 2026-03-31
> **Status:** Delivered
> **Scope:** 37 epics, 319 stories — core MVP through V3.5 per-row extraction, multi-consultant format, unified chat, and 20+ bug fix rounds

---

## Executive Summary

ACM-AI has evolved from a planning-stage prototype (8 epics, 35 stories) into a fully delivered asbestos compliance management platform spanning **37 epics and 319 stories**. This document records the extended plan as delivered through 2026-03-31.

**Delivery summary by phase:**

- **E1-E7: Core MVP** -- Extraction pipeline, AG Grid spreadsheet, cell citations, chat with ACM context, export, branding, upload wizard. ALL DONE.
- **E8: UI Refresh (Bento Grid)** -- ARCHIVED by decision 2026-02-08. E8-S11 (ACM Register Grid UI Polish) completed as standalone. All other E8 stories archived.
- **E9-E16: Enterprise Readiness** -- Document library, UI simplification, search/RAG, extraction settings, knowledge graph, UX enhancements, extraction monitor. ALL DONE.
- **E17-E20: Intelligence & Hardening** -- Live extraction intelligence, production hardening, stakeholder UX, extraction completeness. ALL DONE.
- **E21-E29: Post-Audit & Research** -- Loading states, post-audit remediation, MinerU, TableFormer, table extraction research, Docling Direct API, structured output resilience, not-sampled recovery, pipeline unification. ALL DONE (some stories archived).
- **E30-E35: V3 (Salesforce Alignment)** -- Foundation & schema, multi-provider extraction, AI processing & validation, frontend & UX, integration & polish, post-V3 hardening. ALL DONE (37/37 stories).
- **E36: E2E Verification** -- IN PROGRESS (4/8 stories done).
- **E37: V3.5 Per-Row Extraction** -- One LLM call per table row, 163 new tests. DONE.
- **MCS Sprint: Multi-Consultant Format** -- 246 records across 3 document formats, 13 stories. DONE.
- **Unified Chat: 3 phases** -- Smart chat panel, model selection, session persistence, 14 legacy files deleted, 13 stories. DONE.
- **Bug Fixes & Polish** -- 20+ standalone bug fix rounds addressing extraction accuracy, SurrealDB queries, frontend state, pipeline resilience. DONE.

---

## Current Progress

### Overall Status (2026-03-31)

| Metric | Count |
|--------|-------|
| Total Epics | 37 |
| Total Stories | 319 |
| Done | 289 (91%) |
| In Progress | 1 |
| Backlog | 3 |
| Archived | 16 |

### Key Milestones

| Date | Milestone |
|------|-----------|
| 2025-12-07 | Project kickoff, initial planning |
| 2026-02-22 | E1-E17 complete (core MVP + enterprise readiness) |
| 2026-02-27 | E23 MinerU extraction (90.3% accuracy) |
| 2026-02-28 | E26 Docling Direct API (100% Broadmeadows) |
| 2026-03-05 | V3 complete (E30-E35, 37/37 stories) |
| 2026-03-10 | V3.5 Per-Row Extraction (E37, 163 new tests) |
| 2026-03-18 | MCS Multi-Consultant Format (246 records, 3 formats) |
| 2026-03-22 | Unified Chat (3 phases, 14 legacy files deleted) |
| 2026-03-31 | Chat pipeline stabilized (4 debug rounds, 20+ fixes) |

---

## Epic 7: Upload Wizard -- DONE

> **Status:** All 6 stories complete.

### Overview
Replace the current 3-step add source dialog with a comprehensive multi-step wizard supporting batch uploads with better UX.

### E7-S1: Create Wizard Framework Component -- DONE
**As a** developer
**I want** a reusable multi-step wizard framework
**So that** I can build consistent wizard experiences

**Acceptance Criteria:**
- [x] `WizardContainer` component with step navigation
- [x] Progress indicator showing current step
- [x] Previous/Next/Finish buttons with proper states
- [x] Step validation before proceeding
- [x] Keyboard navigation support (Enter, Escape)
- [x] Mobile-responsive design

**Technical Notes:**
- Location: `frontend/src/components/ui/wizard.tsx`
- Reuse for other wizard flows (podcast creation, etc.)

---

### E7-S2: File Upload Step with Drag & Drop -- DONE
**As a** user
**I want** to drag and drop files or click to browse
**So that** uploading is intuitive

**Acceptance Criteria:**
- [x] Large drop zone with visual feedback
- [x] Click to browse fallback
- [x] File type validation with clear error messages
- [x] File size validation (configurable limit)
- [x] Preview of selected files with remove option
- [x] Batch support: up to 50 files
- [x] Progress indicator per file

**Technical Notes:**
- Use `react-dropzone` library
- Show file icons based on type
- Highlight ACM-specific file types (PDF)

---

### E7-S3: Document Type Detection Step -- DONE
**As a** user
**I want** the system to detect document types automatically
**So that** I don't have to classify them manually

**Acceptance Criteria:**
- [x] Auto-detect document type from filename/content
- [x] Types: ARA/ACM Register, General Document, Media, Other
- [x] Manual override option per file
- [x] Batch classification (apply to all similar)
- [x] Visual cards showing detected type with confidence

**Technical Notes:**
- Simple heuristics: filename patterns, PDF metadata
- "ACM", "SAMP", "Asbestos", "Register" in filename → ACM type
- Show detected vs manual override indicator

---

### E7-S4: Processing Options Step -- DONE
**As a** user
**I want** to configure how documents are processed
**So that** I get the right output for each type

**Acceptance Criteria:**
- [x] ACM Documents: Enable ACM extraction toggle (default ON)
- [x] All Documents: Embedding option (Yes/No/Ask)
- [x] Transformation selection (multi-select)
- [x] Notebook assignment (multi-select)
- [x] Processing mode: Sync vs Async
- [x] Preset configurations (save for reuse)

**Technical Notes:**
- Different options shown based on document type
- Smart defaults based on document type

---

### E7-S5: Review & Confirm Step -- DONE
**As a** user
**I want** to review my selections before uploading
**So that** I can catch mistakes

**Acceptance Criteria:**
- [x] Summary table of all files
- [x] Document type, notebooks, transformations per file
- [x] Edit button to go back to specific step
- [x] Total count and estimated processing time
- [x] "Start Upload" button with confirmation

**Technical Notes:**
- Collapsible sections for large batches
- Highlight any warnings (large files, unsupported types)

---

### E7-S6: Upload Progress & Results Step -- DONE
**As a** user
**I want** to see upload progress and results
**So that** I know what succeeded and failed

**Acceptance Criteria:**
- [x] Real-time progress per file
- [x] Overall progress bar
- [x] Success/failure status per file
- [x] Error messages for failures
- [x] Retry failed uploads option
- [x] "View Source" link for successful uploads
- [x] "Upload More" or "Done" actions

**Technical Notes:**
- Use WebSocket or polling for real-time updates
- Persist state in case of page refresh

---

## Epic 8: UI Refresh (Bento Grid Design) -- ARCHIVED

> **Status: ARCHIVED** -- Skipped by decision 2026-02-08. E8-S11 (ACM Register Grid UI Polish) was completed as a standalone story. All other E8 stories archived.

### Overview
Refresh the ACM-AI interface using a Bento Grid design system - card-based layouts optimized for data-heavy professional applications.

**Design Principles:**
- **Bento Grid Layout**: Uneven but organized card sections
- **Professional Color Palette**: Blues/teals for compliance/professional feel
- **Data-Focused**: Optimized for spreadsheets, tables, dashboards
- **Responsive**: Mobile-first with adaptive breakpoints

### E8-S1: Install UI/UX Pro Max Skill
**As a** developer
**I want** the design intelligence skill installed
**So that** I can generate consistent UI components

**Acceptance Criteria:**
- [ ] Clone ui-ux-pro-max-skill to `.claude/skills/`
- [ ] Verify search functionality works
- [ ] Document usage patterns for team

**Technical Notes:**
- Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Run: `git clone` into `.claude/skills/ui-ux-pro-max/`

---

### E8-S2: Define ACM-AI Design Tokens
**As a** designer/developer
**I want** a consistent design token system
**So that** the UI is cohesive

**Acceptance Criteria:**
- [ ] Color palette defined (primary, secondary, accent, semantic)
- [ ] Typography scale (headings, body, data)
- [ ] Spacing scale (consistent padding/margins)
- [ ] Border radius tokens
- [ ] Shadow tokens for elevation
- [ ] Dark mode variants

**Recommended Palette (Professional/Compliance):**
```css
--primary: oklch(0.55 0.15 220);     /* Teal-blue */
--primary-light: oklch(0.70 0.12 220);
--primary-dark: oklch(0.40 0.18 220);
--accent: oklch(0.65 0.20 45);        /* Amber for warnings */
--success: oklch(0.65 0.18 145);      /* Green */
--danger: oklch(0.55 0.22 25);        /* Red */
--neutral-50 to --neutral-950         /* Gray scale */
```

**Technical Notes:**
- Update `frontend/src/app/globals.css`
- Use OKLch color space (already in use)

---

### E8-S3: Create Bento Card Component
**As a** developer
**I want** a reusable bento card component
**So that** I can build grid layouts consistently

**Acceptance Criteria:**
- [ ] `BentoCard` component with size variants (sm, md, lg, xl)
- [ ] Header with title and optional actions
- [ ] Content area with padding options
- [ ] Footer slot for actions
- [ ] Hover state with subtle elevation
- [ ] Loading skeleton state
- [ ] Responsive sizing

**Technical Notes:**
- Location: `frontend/src/components/ui/bento-card.tsx`
- Use CSS Grid for layout
- Support `span` prop for grid-column/row spanning

---

### E8-S4: Create Bento Grid Layout Component
**As a** developer
**I want** a bento grid container component
**So that** cards arrange automatically

**Acceptance Criteria:**
- [ ] `BentoGrid` container with responsive columns
- [ ] Auto-placement algorithm
- [ ] Gap configuration
- [ ] Breakpoint support (1/2/3/4 columns)
- [ ] Named grid areas for complex layouts

**Technical Notes:**
```tsx
<BentoGrid cols={{ sm: 1, md: 2, lg: 3, xl: 4 }} gap="md">
  <BentoCard span={{ col: 2, row: 1 }}>Large card</BentoCard>
  <BentoCard>Small card</BentoCard>
  <BentoCard>Small card</BentoCard>
</BentoGrid>
```

---

### E8-S5: Redesign Dashboard/Home Page
**As a** user
**I want** a dashboard showing my ACM data overview
**So that** I can quickly understand my portfolio

**Acceptance Criteria:**
- [ ] Bento grid layout with key metrics
- [ ] Card 1: Total sources with recent activity
- [ ] Card 2: ACM summary (risk distribution chart)
- [ ] Card 3: Recent uploads list
- [ ] Card 4: Quick actions (upload, search, chat)
- [ ] Card 5: Processing queue status
- [ ] Responsive collapse on mobile

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/page.tsx`
- Use charts from existing charting library

---

### E8-S6: Redesign Sources List Page
**As a** user
**I want** the sources page to use bento layout
**So that** it's easier to scan and navigate

**Acceptance Criteria:**
- [ ] Grid view option (bento cards)
- [ ] List view option (current table)
- [ ] View toggle persisted
- [ ] Source cards show: title, type, date, ACM status
- [ ] Quick actions on hover
- [ ] Batch selection mode

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/sources/page.tsx`
- Reuse existing data fetching

---

### E8-S7: Redesign Source Detail Page
**As a** user
**I want** the source detail page organized as bento sections
**So that** information is easier to find

**Acceptance Criteria:**
- [ ] Header card: Source title, metadata, actions
- [ ] Content card: Document preview/text
- [ ] ACM card: Spreadsheet view (if ACM data exists)
- [ ] Chat card: Collapsible chat panel
- [ ] Notes card: Related notes
- [ ] Insights card: AI-generated insights
- [ ] Responsive stacking on mobile

**Technical Notes:**
- Major refactor of `frontend/src/app/(dashboard)/sources/[id]/page.tsx`
- Use `BentoGrid` for layout

---

### E8-S8: Update Navigation & Sidebar
**As a** user
**I want** modern navigation that matches the new design
**So that** the app feels cohesive

**Acceptance Criteria:**
- [ ] Updated sidebar with new color scheme
- [ ] Improved iconography
- [ ] Active state indicators
- [ ] Collapsible sections
- [ ] Quick access shortcuts
- [ ] Notification badges

**Technical Notes:**
- Location: `frontend/src/components/layout/AppSidebar.tsx`
- Keep existing structure, update styling

---

### E8-S9: Typography & Font Updates
**As a** user
**I want** professional, readable typography
**So that** data is easy to scan

**Acceptance Criteria:**
- [ ] Updated font pairing (Inter + monospace for data)
- [ ] Consistent heading hierarchy
- [ ] Data table typography optimized
- [ ] Line height and spacing adjusted
- [ ] Font weight scale defined

**Recommended Pairing:**
- Headings: Inter (700)
- Body: Inter (400)
- Data/Code: JetBrains Mono or Fira Code

**Technical Notes:**
- Update `frontend/src/app/layout.tsx`
- Configure in Tailwind

---

### E8-S10: Dark Mode Refinement
**As a** user
**I want** a polished dark mode
**So that** I can work comfortably at night

**Acceptance Criteria:**
- [ ] Dark mode colors reviewed and refined
- [ ] Sufficient contrast ratios (WCAG AA)
- [ ] No harsh whites or blacks
- [ ] Charts and data vis updated
- [ ] Smooth transition between modes

**Technical Notes:**
- Update CSS variables in `globals.css`
- Test with accessibility tools

---

## Post-E8 Epics: Full Delivery Summary (E9-E37 + Sprints)

The following epics were delivered after the original E1-E8 plan. See `05-epics-and-stories.md` for full story details, acceptance criteria, and implementation notes.

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| E9 | Document Library Management | 3 | Done |
| E10 | UI Simplification | 1 | Done |
| E11 | Search & Retrieval (RAG) | 2 | Done |
| E12 | Extraction Settings UI | 4 | Done |
| E13 | Knowledge Graph | 3 | Done |
| E14 | UX & Enterprise Readiness | 11 | Done |
| E15 | Extraction Monitor | 2 | Done |
| E16 | UX Enhancement | 3 | Done |
| E17 | Live Extraction Intelligence | 6 | Done |
| E18 | Production Hardening | 7 | Done |
| E19 | Standard User UX | 8 | Done |
| E20 | Extraction Completeness | 6 | Done |
| E21 | Loading States | 4 | Done |
| E22 | Post-Audit Remediation | 5 | Done |
| E23 | MinerU Table Extraction | 4 | Done |
| E24 | TableFormer Activation | 4 | Done (2 archived) |
| E25 | Table Extraction Research | 3 | Done |
| E26 | Docling Direct API | 7 | Done |
| E27 | Structured Output Resilience | 4 | Done |
| E28 | Not Sampled Recovery | 3 | Done |
| E29 | Pipeline Unification | 10 | Partial (4 done, 6 archived) |
| E30 | V3 Foundation & Schema | 9 | Done |
| E31 | Multi-Provider Extraction | 8 | Done |
| E32 | AI Processing & Validation | 8 | Done |
| E33 | Frontend & UX (V3) | 8 | Done |
| E34 | Integration & Polish (V3) | 4 | Done |
| E35 | Post-V3 Hardening | 8 | Done |
| E36 | E2E Verification | 8 | In Progress (4/8) |
| E37 | Per-Row Extraction (V3.5) | 8 | Done |
| MCS | Multi-Consultant Format | 13 | Done |
| UC | Unified Chat | 13 | Done |
| -- | Bug Fixes & Polish | 30+ | Done |

---

## Implementation Order (Actual)

### Phase 1: Core MVP (Dec 2025 - Feb 2026)
- E1-E7: Extraction pipeline, AG Grid, citations, chat, export, branding, upload wizard

### Phase 2: Enterprise Readiness (Feb 2026)
- E9-E16: Document library, search, settings, knowledge graph, UX, extraction monitor

### Phase 3: Intelligence & Hardening (Feb 2026)
- E17-E20: Live intelligence, production hardening, stakeholder UX, extraction completeness

### Phase 4: Post-Audit & Research (Feb 2026)
- E21-E29: Loading states, remediation, MinerU, TableFormer, Docling, structured output, pipeline unification

### Phase 5: V3 Salesforce Alignment (Mar 2026)
- E30-E35: Schema alignment, multi-provider, AI processing, frontend, integration, hardening (37/37 stories)

### Phase 6: V3.5 + Sprints (Mar 2026)
- E37: Per-row extraction (163 new tests)
- MCS: Multi-consultant format (246 records, 3 formats)
- UC: Unified chat (3 phases, 14 legacy files deleted)
- 20+ bug fix rounds

### Phase 7: Verification (ongoing)
- E36: E2E verification (4/8 complete as of 2026-03-31)

---

## Story Count Summary (Final)

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| E1 | ACM Data Extraction Pipeline | 5 | Done |
| E2 | AG Grid Spreadsheet | 6 | Done |
| E3 | Cell Citations & PDF | 4 | Done |
| E4 | Chat with ACM Context | 4 | Done |
| E5 | Export Functionality | 2 | Done |
| E6 | Rebranding | 4 | Done |
| E7 | Upload Wizard | 6 | Done |
| E8 | UI Refresh (Bento Grid) | 10 | Archived |
| E9-E29 | Enterprise + Research | 88 | Done (8 archived) |
| E30-E35 | V3 Salesforce Alignment | 45 | Done |
| E36 | E2E Verification | 8 | In Progress (4/8) |
| E37 | Per-Row Extraction (V3.5) | 8 | Done |
| MCS | Multi-Consultant Format | 13 | Done |
| UC | Unified Chat | 13 | Done |
| -- | Bug Fixes & Polish | 30+ | Done |
| **Total** | | **319** | **289 done (91%)** |

---

## Resources

- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)
- [Docling Documentation](https://ds4sd.github.io/docling/)
- [MinerU Documentation](https://github.com/opendatalab/MinerU)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SurrealDB Documentation](https://surrealdb.com/docs)

---

*Extended Plan created: 2025-12-07 | Last updated: 2026-03-31*
