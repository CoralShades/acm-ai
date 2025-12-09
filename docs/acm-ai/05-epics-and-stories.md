# Epics and User Stories - ACM-AI

> **Project:** ACM-AI v1.0
> **Date:** 2025-12-07
> **Status:** Draft

---

## Epic Overview

| Epic | Title | Priority | Stories |
|------|-------|----------|---------|
| E1 | ACM Data Extraction Pipeline | P0 | 5 |
| E2 | AG Grid Spreadsheet Integration | P0 | 6 |
| E3 | Cell Citations & PDF Viewer | P0 | 4 |
| E4 | Chat with ACM Context | P0 | 4 |
| E5 | Export Functionality | P1 | 2 |
| E6 | Rebranding to ACM-AI | P1 | 4 |
| **E7** | **Upload Wizard** | **P0** | **6** |
| **E8** | **UI Refresh (Bento Grid)** | **P1** | **10** |

---

## Epic 1: ACM Data Extraction Pipeline

### E1-S1: Create ACM Data Model
**As a** developer
**I want** a SurrealDB schema for ACM records
**So that** extracted data has a consistent structure

**Acceptance Criteria:**
- [ ] `acm_record` table defined with all fields from PRD
- [ ] Indexes created for source_id, building_id, risk_status
- [ ] Migration script created
- [ ] Schema documented

**Technical Notes:**
- Location: `open_notebook/migrations/`
- Reference: PRD Section 5.1

---

### E1-S2: Create ACM Record Domain Model
**As a** developer
**I want** Python domain models for ACM records
**So that** I can work with typed data in the API

**Acceptance Criteria:**
- [ ] `ACMRecord` Pydantic model created
- [ ] CRUD operations implemented (create, read, list, delete)
- [ ] Model follows existing `open_notebook/domain/` patterns
- [ ] Unit tests for model validation

**Technical Notes:**
- Location: `open_notebook/domain/acm.py`
- Pattern: Follow `Source`, `Note` implementations

---

### E1-S3: Implement ACM Extraction Transformation
**As a** system
**I want** to extract ACM Register data from Docling output
**So that** PDF tables become structured records

**Acceptance Criteria:**
- [ ] New transformation `acm_extraction` registered
- [ ] Parses Docling markdown/JSON for tables
- [ ] Identifies ACM Register tables by header patterns
- [ ] Extracts hierarchical structure (Building → Room → Item)
- [ ] Associates page numbers with records
- [ ] Handles "No Asbestos" entries appropriately
- [ ] Works on all 3 sample PDFs with >90% accuracy

**Technical Notes:**
- Location: `open_notebook/transformations/acm_extraction.py`
- Input: Docling markdown output
- Output: List of `ACMRecord` objects

---

### E1-S4: Create ACM API Endpoints
**As a** frontend developer
**I want** REST endpoints for ACM data
**So that** the UI can fetch and display records

**Acceptance Criteria:**
- [ ] `GET /api/acm/records?source_id=xxx` returns records for a source
- [ ] `GET /api/acm/records/{id}` returns single record
- [ ] `POST /api/acm/extract` triggers extraction for a source
- [ ] Filtering by building_id, risk_status supported
- [ ] Pagination supported
- [ ] OpenAPI docs updated

**Technical Notes:**
- Location: `api/routers/acm.py`
- Add router to `api/main.py`

---

### E1-S5: Integrate ACM Extraction into Source Processing
**As a** user
**I want** ACM extraction to happen automatically when I upload a SAMP
**So that** I don't need to manually trigger it

**Acceptance Criteria:**
- [ ] Option to enable ACM extraction on source upload
- [ ] Processing status shown during extraction
- [ ] Errors handled gracefully with user feedback
- [ ] Can re-run extraction if needed

**Technical Notes:**
- Modify `commands/source_commands.py`
- Add ACM extraction as optional transformation

---

## Epic 2: AG Grid Spreadsheet Integration

### E2-S1: Install and Configure AG Grid
**As a** developer
**I want** AG Grid installed in the frontend
**So that** I can build the spreadsheet component

**Acceptance Criteria:**
- [ ] `ag-grid-react` and `ag-grid-community` installed
- [ ] AG Grid CSS imported and themed to match app
- [ ] License configured (Community edition)
- [ ] Basic grid renders in test page

**Technical Notes:**
- Run: `npm install ag-grid-react ag-grid-community`
- Add to: `frontend/src/app/globals.css`

---

### E2-S2: Create ACMSpreadsheet Component
**As a** user
**I want** to see ACM data in a spreadsheet view
**So that** I can easily scan and understand the data

**Acceptance Criteria:**
- [ ] Component renders AG Grid with ACM column definitions
- [ ] Fetches data from `/api/acm/records` on source selection
- [ ] Loading state shown during fetch
- [ ] Empty state shown when no ACM data
- [ ] Error state shown on API failure

**Technical Notes:**
- Location: `frontend/src/components/acm/ACMSpreadsheet.tsx`
- Use React Query for data fetching

---

### E2-S3: Implement Column Sorting and Filtering
**As a** user
**I want** to sort and filter the ACM data
**So that** I can find specific records quickly

**Acceptance Criteria:**
- [ ] Click column header to sort ascending/descending
- [ ] Filter icon in header opens filter menu
- [ ] Text filter for string columns
- [ ] Dropdown filter for enum columns (Risk Status, Friable, Result)
- [ ] Filter state persists during session

**Technical Notes:**
- AG Grid built-in functionality
- Configure `filter: true` on columns

---

### E2-S4: Implement Row Grouping
**As a** user
**I want** to see ACM data grouped by Building and Room
**So that** I can navigate the hierarchy easily

**Acceptance Criteria:**
- [ ] Building rows are collapsible groups
- [ ] Room rows are nested within Building groups
- [ ] ACM items shown as leaf rows
- [ ] Group expand/collapse icons work
- [ ] "Expand All" / "Collapse All" buttons available

**Technical Notes:**
- Use AG Grid row grouping feature
- Set `rowGroup: true` on building_id, room_id columns

---

### E2-S5: Implement Risk Status Color Coding
**As a** user
**I want** risk levels visually highlighted
**So that** I can quickly identify high-risk items

**Acceptance Criteria:**
- [ ] Low risk: green background/badge
- [ ] Medium risk: yellow/amber background/badge
- [ ] High risk: red background/badge
- [ ] Colors accessible (sufficient contrast)
- [ ] Custom cell renderer for Risk Status column

**Technical Notes:**
- Create `RiskBadgeCellRenderer` component
- Use Tailwind colors

---

### E2-S6: Add Search Bar to Spreadsheet
**As a** user
**I want** to search across all columns
**So that** I can find any text in the data

**Acceptance Criteria:**
- [ ] Search input above grid
- [ ] Typing filters visible rows in real-time
- [ ] Searches across all text columns
- [ ] Clear button resets search
- [ ] Result count shown ("Showing X of Y records")

**Technical Notes:**
- Use AG Grid Quick Filter API
- `api.setQuickFilter(searchText)`

---

## Epic 3: Cell Citations & PDF Viewer

### E3-S1: Make Cells Clickable
**As a** user
**I want** to click a cell to see its source
**So that** I can verify the extracted data

**Acceptance Criteria:**
- [ ] All cells have click handler
- [ ] Click event includes record ID and field name
- [ ] Visual feedback on hover (cursor change)
- [ ] Click opens citation modal

**Technical Notes:**
- Use AG Grid `onCellClicked` event
- Pass data to modal component

---

### E3-S2: Create PDF Viewer Modal
**As a** user
**I want** to see the source PDF page when I click a cell
**So that** I can see exactly where the data came from

**Acceptance Criteria:**
- [ ] Modal opens with PDF viewer
- [ ] PDF loads to correct page number
- [ ] Page navigation controls available
- [ ] Zoom controls available
- [ ] Close button works
- [ ] Responsive sizing

**Technical Notes:**
- Use `react-pdf` library
- Location: `frontend/src/components/acm/ACMCellViewer.tsx`

---

### E3-S3: Implement ACM Citation Reference Type
**As a** system
**I want** to parse `[acm:id:field]` citation format
**So that** chat can reference specific ACM data

**Acceptance Criteria:**
- [ ] Parser recognizes `[acm:record_id:field_name]` pattern
- [ ] Converts to clickable link in chat messages
- [ ] Click opens same citation modal as spreadsheet cell click
- [ ] Gracefully handles invalid references

**Technical Notes:**
- Extend `frontend/src/lib/utils/source-references.tsx`
- Add new regex pattern and handler

---

### E3-S4: Store Page Numbers During Extraction
**As a** system
**I want** to track which PDF page each ACM record came from
**So that** citations can link to the correct page

**Acceptance Criteria:**
- [ ] Extraction pipeline captures page numbers
- [ ] Page number stored in `acm_record.page_number`
- [ ] Works correctly for multi-page registers
- [ ] Falls back gracefully if page number unavailable

**Technical Notes:**
- Docling output may include page info
- May need to track during table parsing

---

## Epic 4: Chat with ACM Context

### E4-S1: Add ACM Records to Chat Context
**As a** user
**I want** the AI to know about my ACM data
**So that** I can ask questions about it

**Acceptance Criteria:**
- [ ] ACM records included in chat context when toggled on
- [ ] Context formatted as readable table/summary
- [ ] Token limit respected (truncate if needed)
- [ ] Context clearly labeled as "ACM Register Data"

**Technical Notes:**
- Modify `api/routers/source_chat.py`
- Format ACM data as markdown table in context

---

### E4-S2: Create ACM Context Toggle
**As a** user
**I want** to control whether ACM data is included in chat
**So that** I can have focused conversations

**Acceptance Criteria:**
- [ ] Toggle switch in chat panel header
- [ ] Default: ON when ACM data exists for selected source
- [ ] Visual indicator shows when ACM context is active
- [ ] Toggle state persists during session

**Technical Notes:**
- Location: `frontend/src/components/source/ChatPanel.tsx`
- Store state in React context or URL params

---

### E4-S3: Generate ACM-Aware Chat Responses
**As a** user
**I want** the AI to cite specific ACM records
**So that** I can trust and verify the answers

**Acceptance Criteria:**
- [ ] AI responses include `[acm:...]` citations when relevant
- [ ] Citations are clickable and show source
- [ ] AI answers domain questions accurately
- [ ] System prompt includes ACM domain guidance

**Technical Notes:**
- Update system prompt in chat handler
- Include citation format instructions

---

### E4-S4: Support ACM-Specific Questions
**As a** user
**I want** to ask natural questions like "What's the risk level in Building A?"
**So that** I get useful answers without complex queries

**Acceptance Criteria:**
- [ ] AI correctly interprets building/room references
- [ ] AI summarizes risk status when asked
- [ ] AI explains ACM terminology when asked
- [ ] AI references policy sections when relevant

**Technical Notes:**
- Primarily prompt engineering
- Test with sample questions

---

## Epic 5: Export Functionality

### E5-S1: Implement CSV Export
**As a** user
**I want** to download ACM data as CSV
**So that** I can use it in other tools

**Acceptance Criteria:**
- [ ] Export button in spreadsheet toolbar
- [ ] Exports currently filtered/visible data
- [ ] File named with source name and date
- [ ] All columns included with proper headers
- [ ] UTF-8 encoding for special characters

**Technical Notes:**
- Use AG Grid `exportDataAsCsv()` API
- Or backend endpoint `/api/acm/export?format=csv`

---

### E5-S2: Implement Excel Export (P2)
**As a** user
**I want** to download ACM data as Excel
**So that** I get formatted spreadsheet

**Acceptance Criteria:**
- [ ] Export as .xlsx option
- [ ] Column widths auto-sized
- [ ] Header row formatted
- [ ] Risk status cells color-coded (if possible)

**Technical Notes:**
- Requires AG Grid Enterprise OR
- Backend export using `openpyxl` library
- May defer to post-MVP

---

## Epic 6: Rebranding to ACM-AI

### E6-S1: Update Application Name and Title
**As a** user
**I want** the app to be called "ACM-AI"
**So that** I know its purpose

**Acceptance Criteria:**
- [ ] Browser tab title: "ACM-AI"
- [ ] Header shows "ACM-AI" logo/text
- [ ] package.json name updated
- [ ] API docs title updated

**Technical Notes:**
- Update `frontend/src/app/layout.tsx`
- Update `api/main.py` title

---

### E6-S2: Create New Logo and Favicon
**As a** user
**I want** a professional logo for ACM-AI
**So that** the app looks polished

**Acceptance Criteria:**
- [ ] Logo designed (SVG format)
- [ ] Favicon created (multiple sizes)
- [ ] Logo used in header
- [ ] Favicon appears in browser tab

**Technical Notes:**
- Place in `frontend/public/`
- Update `favicon.ico`, `icon.png`

---

### E6-S3: Update Color Theme
**As a** user
**I want** a professional color scheme
**So that** the app feels appropriate for compliance work

**Acceptance Criteria:**
- [ ] Primary color updated (suggested: blue/teal)
- [ ] Accent color for risk indicators
- [ ] Dark mode colors adjusted
- [ ] Consistent across all components

**Technical Notes:**
- Update Tailwind config
- Modify CSS variables

---

### E6-S4: Update Landing/Home Page
**As a** new user
**I want** to understand what ACM-AI does
**So that** I can start using it effectively

**Acceptance Criteria:**
- [ ] Hero section explains ACM-AI purpose
- [ ] Key features listed
- [ ] Quick start instructions visible
- [ ] Call-to-action to upload first document

**Technical Notes:**
- Location: `frontend/src/app/page.tsx`
- Keep simple for MVP

---

## Story Dependencies

```
E1-S1 → E1-S2 → E1-S3 → E1-S4 → E1-S5
                  ↓
E2-S1 → E2-S2 → E2-S3/S4/S5/S6
                  ↓
E3-S1 → E3-S2 → E3-S3
   ↑
E1-S3 (page numbers) → E3-S4

E4-S1 → E4-S2 → E4-S3 → E4-S4

E2-S2 → E5-S1 → E5-S2

E6-S1/S2/S3/S4 (independent, can be done anytime)
```

---

## MVP Scope Summary

**Must Have (MVP):**
- E1: All stories (extraction pipeline)
- E2: S1-S4 (core spreadsheet)
- E3: S1-S3 (citations)
- E4: S1, S3 (basic chat integration)
- E6: S1 (basic rebrand)

**Should Have:**
- E2: S5, S6 (polish)
- E3: S4 (page numbers)
- E4: S2, S4 (chat polish)
- E5: S1 (CSV export)
- E6: S2-S4 (full rebrand)

**Could Have:**
- E5: S2 (Excel export)

---

## Epic 7: Upload Wizard

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
- Reuse for other wizard flows

---

### E7-S2: File Upload Step with Drag & Drop
**As a** user
**I want** to drag and drop files or click to browse
**So that** uploading is intuitive

**Acceptance Criteria:**
- [ ] Large drop zone with visual feedback
- [ ] Click to browse fallback
- [ ] File type validation with clear error messages
- [ ] File size validation
- [ ] Preview of selected files with remove option
- [ ] Batch support: up to 50 files
- [ ] Progress indicator per file

**Technical Notes:**
- Use `react-dropzone` library
- Show file icons based on type

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
- Filename patterns: "ACM", "SAMP", "Asbestos", "Register"
- Show detected vs manual override indicator

---

### E7-S4: Processing Options Step
**As a** user
**I want** to configure how documents are processed
**So that** I get the right output for each type

**Acceptance Criteria:**
- [ ] ACM Documents: Enable ACM extraction toggle (default ON)
- [ ] All Documents: Embedding option
- [ ] Transformation selection (multi-select)
- [ ] Notebook assignment (multi-select)
- [ ] Processing mode: Sync vs Async

**Technical Notes:**
- Different options based on document type
- Smart defaults

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
- Use polling for real-time updates

---

## Epic 8: UI Refresh (Bento Grid Design)

### E8-S1: Install UI/UX Pro Max Skill
**As a** developer
**I want** the design intelligence skill installed
**So that** I can generate consistent UI components

**Acceptance Criteria:**
- [ ] Clone ui-ux-pro-max-skill to `.claude/skills/`
- [ ] Verify search functionality works
- [ ] Document usage patterns

**Technical Notes:**
- Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

---

### E8-S2: Define ACM-AI Design Tokens
**As a** designer/developer
**I want** a consistent design token system
**So that** the UI is cohesive

**Acceptance Criteria:**
- [ ] Color palette defined (primary, secondary, accent, semantic)
- [ ] Typography scale (headings, body, data)
- [ ] Spacing scale
- [ ] Border radius tokens
- [ ] Shadow tokens for elevation
- [ ] Dark mode variants

**Technical Notes:**
- Update `frontend/src/app/globals.css`
- Use OKLch color space

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

**Technical Notes:**
- Use CSS Grid for layout

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
- [ ] Card 4: Quick actions
- [ ] Responsive collapse on mobile

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/page.tsx`

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
- Location: `frontend/src/app/(dashboard)/sources/[id]/page.tsx`

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

**Technical Notes:**
- Location: `frontend/src/components/layout/AppSidebar.tsx`

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

**Technical Notes:**
- Update `frontend/src/app/layout.tsx`

---

### E8-S10: Dark Mode Refinement
**As a** user
**I want** a polished dark mode
**So that** I can work comfortably at night

**Acceptance Criteria:**
- [ ] Dark mode colors reviewed and refined
- [ ] Sufficient contrast ratios (WCAG AA)
- [ ] Charts and data vis updated
- [ ] Smooth transition between modes

**Technical Notes:**
- Update CSS variables in `globals.css`
