# Extended Implementation Plan - ACM-AI v1.0

> **Created:** 2025-12-07
> **Status:** Planning
> **Scope:** Original epics + Upload Wizard + UI Refresh

---

## Executive Summary

This plan extends the original ACM-AI implementation with two new epics:
- **E7: Upload Wizard** - Multi-step wizard with batch upload support
- **E8: UI Refresh** - Bento Grid design system overhaul

Combined with the original 6 epics (25 stories), this brings the total to **8 epics and 35+ stories**.

---

## Current Progress

### Completed Stories (2)
| Story | Title | Notes |
|-------|-------|-------|
| E1-S1 | Create ACM Data Model | Migration 10.surrealql applied |
| E1-S2 | Create ACM Record Domain Model | `open_notebook/domain/acm.py` |

### Ready for Implementation (6)
| Story | Title | Tech-Spec |
|-------|-------|-----------|
| E1-S3 | Implement ACM Extraction Transformation | Yes |
| E1-S4 | Create ACM API Endpoints | Yes |
| E2-S2 | Create ACMSpreadsheet Component | Yes |
| E3-S2 | Create PDF Viewer Modal | Yes |
| E4-S1 | Add ACM Records to Chat Context | Yes |
| E4-S3 | Generate ACM-Aware Chat Responses | Yes |

---

## New Epic 7: Upload Wizard

### Overview
Replace the current 3-step add source dialog with a comprehensive multi-step wizard supporting batch uploads with better UX.

### E7-S1: Create Wizard Framework Component
**As a** developer
**I want** a reusable multi-step wizard framework
**So that** I can build consistent wizard experiences

**Acceptance Criteria:**
- [ ] `WizardContainer` component with step navigation
- [ ] Progress indicator showing current step
- [ ] Previous/Next/Finish buttons with proper states
- [ ] Step validation before proceeding
- [ ] Keyboard navigation support (Enter, Escape)
- [ ] Mobile-responsive design

**Technical Notes:**
- Location: `frontend/src/components/ui/wizard.tsx`
- Reuse for other wizard flows (podcast creation, etc.)

---

### E7-S2: File Upload Step with Drag & Drop
**As a** user
**I want** to drag and drop files or click to browse
**So that** uploading is intuitive

**Acceptance Criteria:**
- [ ] Large drop zone with visual feedback
- [ ] Click to browse fallback
- [ ] File type validation with clear error messages
- [ ] File size validation (configurable limit)
- [ ] Preview of selected files with remove option
- [ ] Batch support: up to 50 files
- [ ] Progress indicator per file

**Technical Notes:**
- Use `react-dropzone` library
- Show file icons based on type
- Highlight ACM-specific file types (PDF)

---

### E7-S3: Document Type Detection Step
**As a** user
**I want** the system to detect document types automatically
**So that** I don't have to classify them manually

**Acceptance Criteria:**
- [ ] Auto-detect document type from filename/content
- [ ] Types: SAMP/ACM Register, General Document, Media, Other
- [ ] Manual override option per file
- [ ] Batch classification (apply to all similar)
- [ ] Visual cards showing detected type with confidence

**Technical Notes:**
- Simple heuristics: filename patterns, PDF metadata
- "ACM", "SAMP", "Asbestos", "Register" in filename → ACM type
- Show detected vs manual override indicator

---

### E7-S4: Processing Options Step
**As a** user
**I want** to configure how documents are processed
**So that** I get the right output for each type

**Acceptance Criteria:**
- [ ] ACM Documents: Enable ACM extraction toggle (default ON)
- [ ] All Documents: Embedding option (Yes/No/Ask)
- [ ] Transformation selection (multi-select)
- [ ] Notebook assignment (multi-select)
- [ ] Processing mode: Sync vs Async
- [ ] Preset configurations (save for reuse)

**Technical Notes:**
- Different options shown based on document type
- Smart defaults based on document type

---

### E7-S5: Review & Confirm Step
**As a** user
**I want** to review my selections before uploading
**So that** I can catch mistakes

**Acceptance Criteria:**
- [ ] Summary table of all files
- [ ] Document type, notebooks, transformations per file
- [ ] Edit button to go back to specific step
- [ ] Total count and estimated processing time
- [ ] "Start Upload" button with confirmation

**Technical Notes:**
- Collapsible sections for large batches
- Highlight any warnings (large files, unsupported types)

---

### E7-S6: Upload Progress & Results Step
**As a** user
**I want** to see upload progress and results
**So that** I know what succeeded and failed

**Acceptance Criteria:**
- [ ] Real-time progress per file
- [ ] Overall progress bar
- [ ] Success/failure status per file
- [ ] Error messages for failures
- [ ] Retry failed uploads option
- [ ] "View Source" link for successful uploads
- [ ] "Upload More" or "Done" actions

**Technical Notes:**
- Use WebSocket or polling for real-time updates
- Persist state in case of page refresh

---

## New Epic 8: UI Refresh (Bento Grid Design)

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

## Implementation Order

### Phase 1: Foundation (Current)
1. ~~E1-S1: ACM Data Model~~ ✅
2. ~~E1-S2: ACM Domain Model~~ ✅
3. **E1-S3: ACM Extraction** ← Next
4. **E1-S4: ACM API Endpoints**

### Phase 2: UI Framework
5. E8-S1: Install UI/UX Pro Max Skill
6. E8-S2: Define Design Tokens
7. E8-S3: Bento Card Component
8. E8-S4: Bento Grid Layout

### Phase 3: Upload Wizard
9. E7-S1: Wizard Framework
10. E7-S2: File Upload Step
11. E7-S3: Document Type Detection
12. E7-S4: Processing Options
13. E7-S5: Review & Confirm
14. E7-S6: Upload Progress

### Phase 4: ACM Spreadsheet
15. E2-S1: Install AG Grid
16. E2-S2: ACMSpreadsheet Component
17. E2-S3: Sorting/Filtering
18. E2-S4: Row Grouping
19. E2-S5: Risk Color Coding
20. E2-S6: Search Bar

### Phase 5: UI Refresh Pages
21. E8-S5: Dashboard Redesign
22. E8-S6: Sources List Redesign
23. E8-S7: Source Detail Redesign
24. E8-S8: Navigation Update
25. E8-S9: Typography Update
26. E8-S10: Dark Mode Refinement

### Phase 6: Citations & Chat
27. E3-S1: Clickable Cells
28. E3-S2: PDF Viewer Modal
29. E3-S3: ACM Citation Type
30. E4-S1: ACM in Chat Context
31. E4-S3: ACM-Aware Responses

### Phase 7: Polish & Export
32. E1-S5: Integration with Source Processing
33. E5-S1: CSV Export
34. E6-S1: Rebranding (title, name)

---

## Story Count Summary

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| E1 | ACM Data Extraction Pipeline | 5 | 2 done, 3 pending |
| E2 | AG Grid Spreadsheet | 6 | All pending |
| E3 | Cell Citations & PDF | 4 | All pending |
| E4 | Chat with ACM Context | 4 | All pending |
| E5 | Export Functionality | 2 | All pending |
| E6 | Rebranding | 4 | All pending |
| **E7** | **Upload Wizard** | **6** | **NEW** |
| **E8** | **UI Refresh (Bento Grid)** | **10** | **NEW** |
| **Total** | | **41** | |

---

## Dependencies

```
E8-S1 → E8-S2 → E8-S3 → E8-S4
                    ↓
              E8-S5/S6/S7/S8

E7-S1 → E7-S2 → E7-S3 → E7-S4 → E7-S5 → E7-S6

E1-S1 → E1-S2 → E1-S3 → E1-S4 → E1-S5
              ↓
        E2-S1 → E2-S2 → ...
              ↓
        E3-S1 → E3-S2 → E3-S3
              ↓
        E4-S1 → E4-S3
```

---

## Resources

- [UI/UX Pro Max Skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
- [Bento Grid Design Patterns](https://bentogrids.com/)
- [Magic UI Bento Component](https://magicui.design/docs/components/bento-grid)
- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)

---

*Extended Plan created: 2025-12-07*
