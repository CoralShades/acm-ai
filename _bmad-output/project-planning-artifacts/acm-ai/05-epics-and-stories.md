# Epics and User Stories - ACM-AI

> **Project:** ACM-AI v1.0
> **Date:** 2025-12-07 (Updated: 2026-02-04)
> **Status:** Draft - Updated for Victorian BAR Format
> **Change Log:** Sprint Change Proposal approved 2026-02-04 - Added 6 new stories, modified 6 existing

---

## Epic Overview

| Epic | Title | Priority | Stories | Status |
|------|-------|----------|---------|--------|
| E1 | ACM Data Extraction Pipeline | P0 | **12** (+5 new) | Done (7), New (5) |
| E2 | AG Grid Spreadsheet Integration | P0 | **8** (+1 new) | Done (7), New (1) |
| E3 | Cell Citations & PDF Viewer | P0 | 4 | Done |
| E4 | Chat with ACM Context | P0 | 4 | Done |
| E5 | Export Functionality | **P0** (promoted) | **4** (+2 new) | Done (2), New (2) |
| E6 | Rebranding to ACM-AI | P1 | 4 | Done |
| E7 | Upload Wizard | P0 | **7** (+1 new) | Done (6), New (1) |
| E8 | UI Refresh (Bento Grid) | P1 | 10 | In Progress |
| E9 | Document Library Management | P0 | 3 | Backlog |
| E10 | ACM-AI UI Simplification | P0 | 1 | Backlog |

> **2026-02-04 Update:** Victorian BAR format expansion added 6 new stories across E1, E2, E5, E7.
> E5 promoted from P1 to P0 (BAR Excel export is critical).
>
> **2026-02-05 Update:** Research integration added 3 new stories to E1:
> - E1-S10: MinerU table extraction
> - E1-S11: Extensible consultant parser framework
> - E1-S12: Consultant wording normalization
> Updated E1-S3 for two-stage pipeline and E1-S9 for official taxonomy.

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

### E1-S3: Implement Two-Stage ACM Extraction Pipeline (UPDATED 2026-02-05)
**As a** system
**I want** to extract ACM Register data using a two-stage pipeline
**So that** PDF tables become structured, BAR-compliant records with full provenance

**Acceptance Criteria:**
- [ ] **Stage 1 (EXTRACT):**
  - [ ] Extract verbatim values from PDF (no normalization)
  - [ ] Track provenance: page number, table ID, row/column, confidence
  - [ ] Output `RawExtraction` JSON with `DocumentMeta` and `RawACMItem[]`
  - [ ] Store raw extraction for audit/debugging
- [ ] **Stage 2 (INTERPRET):**
  - [ ] Map consultant columns → BAR columns
  - [ ] Normalize values to controlled enums (see PRD 5.5)
  - [ ] Classify products using taxonomy (see PRD 5.6)
  - [ ] Apply business rules (Negative → N/A for Condition/Disturbance)
  - [ ] Validate against BAR schema
  - [ ] Output validated `ACMRecord` objects
- [ ] Identifies ACM Register tables by header patterns
- [ ] Extracts hierarchical structure (Building → Room → Item)
- [ ] Works on Prensa and Greencap sample PDFs with >90% accuracy

**Technical Notes:**
- Location: `open_notebook/extraction/` (new module)
  - `pipeline.py` - Main orchestrator
  - `stage1_extract.py` - Verbatim extraction
  - `stage2_interpret.py` - Normalization and validation
- Reference: `docs/reference/extraction-pipeline.md`
- Reference: `docs/reference/bar-schema.md`

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

### E1-S6: Configure Local Embedding Pipeline
**As a** developer
**I want** to configure local embedding models for ACM data vectorization
**So that** semantic search works without external API calls (privacy requirement)

**Acceptance Criteria:**
- [ ] Local embedding model selected and configured (e.g., sentence-transformers, nomic-embed)
- [ ] Embedding pipeline integrated with ACM record creation
- [ ] Page content vectorized and stored in SurrealDB vector fields
- [ ] Semantic search API endpoint for ACM records
- [ ] Configuration option to choose between local and cloud embeddings
- [ ] Performance benchmarks documented (embedding speed, search latency)

**Technical Notes:**
- Location: `open_notebook/graphs/embeddings/` or new module
- Use Esperanto abstraction for model provider flexibility
- SurrealDB supports vector fields natively
- Consider batch embedding for large documents
- Reference: NFR-201 (local processing requirement)

---

### E1-S8: Site Configuration Data Entry (NEW - Victorian BAR)
**As a** user
**I want** to configure site metadata that cannot be extracted from PDFs
**So that** my BAR exports are complete with all required fields

**Acceptance Criteria:**
- [ ] Configuration form for non-extractable fields:
  - Department (dropdown: DJCS, DHHS, DET, DOT, DJPR, etc.)
  - Agency (text with autocomplete)
  - Building Type (dropdown from BAR classification)
  - Owned or Leased (dropdown)
  - Frequency of use (dropdown)
  - Public Access? (YES/NO)
  - Building Unique ID (text)
- [ ] Configuration saved per source document
- [ ] Configuration can be applied as template for batch uploads
- [ ] Edit existing configuration after upload
- [ ] Validation: warn if required BAR fields are empty
- [ ] API endpoints: GET/POST `/api/acm/config`

**Technical Notes:**
- Location: `frontend/src/components/acm/SiteConfigForm.tsx`
- Backend: `api/routers/acm.py` - add config endpoints
- Store in `site_config` table (see PRD 5.1.1)
- Reference: Sprint Change Proposal CP#2

---

### E1-S9: ACM Product Classification (UPDATED 2026-02-05)
**As a** system
**I want** to automatically classify ACM items into Product Group/Type using official taxonomy
**So that** BAR export has proper classification columns (AA-AC) populated

**Acceptance Criteria:**
- [ ] **Pattern-based classification (primary):**
  - [ ] Regex patterns for common ACM types (vinyl, cement, gasket, etc.)
  - [ ] Select taxonomy based on friability (Non-friable: T1-T8, Friable: T1-T6)
  - [ ] Pattern matching against `docs/reference/product-taxonomy.md`
- [ ] **LLM fallback (for ambiguous items):**
  - [ ] Few-shot prompt with taxonomy context
  - [ ] Return product_group, product_type, confidence
- [ ] **User override capability:**
  - [ ] Manual correction via API
  - [ ] Override persisted in database
- [ ] **Taxonomy reference:**
  - [ ] Non-friable: T1 Cement, T2 Bitumen, T3 Vinyl, T4 Gasket, T5 Coatings, T6 Plastics, T7 Other, T8 Insulation
  - [ ] Friable: T1 Cement(f), T2 Vinyl(f), T3 Insulation(f), T4 Gasket(f), T5 Textiles(f), T6 Other(f)
- [ ] API endpoint: POST `/api/acm/classify`
- [ ] Batch classification for existing records

**Technical Notes:**
- Location: `open_notebook/extraction/normalizers/taxonomy.py`
- Reference: `docs/reference/product-taxonomy.md`
- Reference: `docs/samplePDF/instructions-sample/register_taxonomy.*.json`
- Integration: Called during Stage 2 (INTERPRET) of extraction pipeline

---

### E1-S10: MinerU Table Extraction Integration (NEW 2026-02-05)
**As a** system
**I want** to use MinerU for complex table extraction
**So that** merged cells and multi-page tables are extracted accurately

**Acceptance Criteria:**
- [ ] Install MinerU dependency (`pip install mineru[all]`)
- [ ] Create `MineruTableExtractor` class
- [ ] Extract tables from PDF pages with HTML structure
- [ ] Track table bounding boxes for provenance
- [ ] Handle merged cells correctly
- [ ] Stitch multi-page tables into single logical table
- [ ] Fallback to Docling if MinerU fails
- [ ] Performance: Process 20-page PDF in <30 seconds

**Technical Notes:**
- Location: `open_notebook/extraction/parsers/mineru_extractor.py`
- MinerU outputs HTML tables - parse to structured data
- Use page-level bounding boxes for citation linking
- Reference: `docs/reference/extraction-pipeline.md`

---

### E1-S11: Extensible Consultant Parser Framework (NEW 2026-02-05)
**As a** developer
**I want** a pluggable parser framework for different consultant formats
**So that** new PDF formats can be added without modifying core extraction code

**Acceptance Criteria:**
- [ ] Define `ConsultantParser` abstract base class with methods:
  - `detect(text: str) -> bool`
  - `extract_metadata(pages: dict) -> DocumentMeta`
  - `extract_items(tables: list) -> list[RawACMItem]`
  - `get_column_mapping() -> dict[str, str]`
- [ ] Implement `PrensaParser` with column mapping:
  - area_level, room_location, feature, item_description, hazard_status, sample_number, etc.
- [ ] Implement `GreencapParser` with different column mapping
- [ ] Implement `GenericParser` as fallback
- [ ] Parser registry for automatic selection
- [ ] Document adding new parsers in developer guide

**Technical Notes:**
- Location: `open_notebook/extraction/parsers/`
  - `base.py` - Abstract base class
  - `prensa.py` - Prensa Pty Ltd parser
  - `greencap.py` - Greencap parser
  - `generic.py` - Fallback parser
- Reference: Architecture Section 5.2

---

### E1-S12: Consultant Wording Normalization (NEW 2026-02-05)
**As a** system
**I want** to normalize consultant recommendations to canonical actions
**So that** hygienist recommendations are consistent across different consultants

**Acceptance Criteria:**
- [ ] Define canonical actions:
  - `maintain_in_situ` - Keep ACM in place, label, periodic review
  - `remove_prior_to_refurb` - Remove before demolition by licensed contractor
  - `restrict_access_immediately` - Restrict access and arrange abatement ASAP
  - `remedial_within_months` - Organise remedial works within ~3 months
  - `confirm_status_sampling` - Item not sampled, confirm via sampling
  - `height_or_access_restriction` - No access, treat as presumed
- [ ] Regex pattern matching for consultant phrases
- [ ] Store both raw recommendation and normalized action
- [ ] Support custom patterns via configuration

**Technical Notes:**
- Location: `open_notebook/extraction/normalizers/recommendations.py`
- Reference: `docs/samplePDF/instructions-sample/consultant_wording_rules.json`

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

### E2-S7: Implement Building Tab Navigation
**As a** user
**I want** ACM data organized by building tabs
**So that** I can quickly navigate between buildings in a school

**Acceptance Criteria:**
- [ ] Tab bar above spreadsheet showing all buildings (e.g., B00A, B00B, B00C)
- [ ] Tab shows building code and record count (e.g., "B00A (4)")
- [ ] Clicking tab filters grid to show only that building's records
- [ ] "All Buildings" tab option to show combined view
- [ ] Active tab visually highlighted
- [ ] Tabs auto-generated from ACM data (no hardcoding)
- [ ] Smooth transition when switching tabs
- [ ] Remember last selected tab per source (session persistence)

**Technical Notes:**
- Location: `frontend/src/components/acm/BuildingTabs.tsx`
- Use Radix UI Tabs or similar accessible component
- Filter grid data client-side for performance
- Consider: group by building_id field from ACM records
- Reference: Existing MVP at acm.coralshades.ai uses this pattern

---

### E2-S8: Column Visibility Management (NEW - Victorian BAR)
**As a** user
**I want** to show/hide columns and save my preferences
**So that** I can focus on relevant data without clutter from 47+ columns

**Acceptance Criteria:**
- [ ] Column visibility panel (sidebar or dropdown)
- [ ] Toggle individual columns on/off
- [ ] Preset views available:
  - "Essential" (7 key columns)
  - "Full BAR" (all 47 columns)
  - "Assessment Focus" (assessment-related columns)
  - "Removal Tracking" (removal-related columns)
- [ ] Save custom column views with name
- [ ] Apply saved view to current spreadsheet
- [ ] Default view per user preference
- [ ] Column visibility persists in localStorage

**Technical Notes:**
- Location: `frontend/src/components/acm/ColumnVisibility.tsx`
- Use AG Grid Column API for visibility control
- Store preferences in localStorage or user settings
- Reference: Architecture Section 6.1 COLUMN_PRESETS
- Reference: Sprint Change Proposal CP#4

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

## Epic 5: Export Functionality (PROMOTED to P0)

> **2026-02-04 Update:** Epic promoted from P1 to P0. BAR-compliant Excel export is critical for Victorian Government submissions. Added 2 new stories.

### E5-S1: Implement CSV Export (UPDATED)
**As a** user
**I want** to download ACM data as CSV with all BAR columns
**So that** I can use it in other tools and submit to government systems

**Acceptance Criteria:**
- [ ] Export button in spreadsheet toolbar
- [ ] **UPDATED:** Exports ALL 47 BAR columns (not just visible)
- [ ] **UPDATED:** Column order matches BAR specification
- [ ] File named with source name and date
- [ ] UTF-8 encoding for special characters
- [ ] **NEW:** Option to export selected buildings only

**Technical Notes:**
- Backend endpoint `/api/acm/export/csv`
- Reference: PRD Section 5.3 for column order

---

### E5-S2: Implement Excel BAR Export (PROMOTED to P0)
**As a** user
**I want** to download ACM data as BAR-compliant Excel
**So that** I can submit to Victorian Government systems

**Acceptance Criteria:**
- [ ] Export as .xlsx format
- [ ] **CRITICAL:** Column headers match BAR template exactly
- [ ] **CRITICAL:** Column order matches BAR specification (47 columns)
- [ ] Column widths auto-sized
- [ ] Header row formatted with freeze
- [ ] Risk status cells color-coded
- [ ] **NEW:** Data validation dropdowns for enum fields (where possible)
- [ ] **NEW:** Multiple sheets support if needed
- [ ] **NEW:** Include reference sheets from BAR template (optional)

**Technical Notes:**
- Backend export using `openpyxl` or `xlsxwriter`
- NOT dependent on AG Grid Enterprise
- API endpoint: `/api/acm/export/excel`
- Reference: PRD Section 5.3 BAR Export Format Specification
- Reference: Sprint Change Proposal CP#3

---

### E5-S3: BAR Template Management (NEW - Victorian BAR)
**As a** user
**I want** to use official BAR Excel templates
**So that** exports are guaranteed to be compliant

**Acceptance Criteria:**
- [ ] Upload official BAR template (.xlsm/.xlsx)
- [ ] System extracts column structure from template
- [ ] Validates ACM-AI schema maps to all template columns
- [ ] Shows mapping gaps/warnings
- [ ] Template versioning support
- [ ] Default template bundled with system
- [ ] API endpoint: GET/POST `/api/acm/templates`

**Technical Notes:**
- Parse template header row for column names
- Store template metadata in database
- Alert on template updates from government
- Location: `api/routers/acm.py` - add template endpoints
- Reference: Sprint Change Proposal CP#3

---

### E5-S4: Export Field Mapping Configuration (NEW - Victorian BAR)
**As a** power user
**I want** to configure how ACM-AI fields map to BAR columns
**So that** I can customize exports for different BAR versions

**Acceptance Criteria:**
- [ ] UI to view current field mappings
- [ ] Ability to map ACM-AI fields to BAR columns
- [ ] Support for computed/derived fields
- [ ] Default mappings pre-configured
- [ ] Export mapping configuration for backup/sharing
- [ ] Import mapping configuration
- [ ] API endpoint: GET/PUT `/api/acm/mappings`

**Technical Notes:**
- Store mappings in JSON configuration
- UI: simple table with source → target mapping
- Location: `frontend/src/components/acm/FieldMappingConfig.tsx`
- Reference: Sprint Change Proposal CP#3

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

## Story Dependencies (UPDATED 2026-02-05)

```
# Core Extraction Pipeline - REFACTORED for Two-Stage Architecture
E1-S1 (Schema) → E1-S2 (Domain Model) → E1-S10 (MinerU) → E1-S11 (Parser Framework)
                                              ↓
                                        E1-S3 (Two-Stage Pipeline) → E1-S12 (Wording Normalization)
                                              ↓
                                        E1-S9 (Taxonomy Classification)
                                              ↓
                                        E1-S4 (API) → E1-S5 (Integration) → E1-S6 → E1-S7
                                              ↓
# Victorian BAR stories
E1-S4 (API) → E1-S8 (Site Config) → E7-S7 (Upload Config)
E1-S3 (Extraction) → E1-S9 (Product Classification)

# Spreadsheet (✅ DONE through E2-S7)
E2-S1 → E2-S2 → E2-S3/S4/S5/S6 → E2-S7 (all done)
                  ↓
# NEW: Column Visibility
E2-S7 → E2-S8 (Column Visibility)

# Citations (✅ DONE)
E3-S1 → E3-S2 → E3-S3 → E3-S4 (all done)

# Chat (✅ DONE)
E4-S1 → E4-S2 → E4-S3 → E4-S4 (all done)

# Export (✅ S1-S2 DONE, NEW S3-S4)
E2-S2 → E5-S1 → E5-S2 (done)
              ↓
E5-S2 → E5-S3 (Template Management) → E5-S4 (Field Mapping)

# Rebranding (✅ DONE)
E6-S1/S2/S3/S4 (all done)

# Upload Wizard (✅ DONE through E7-S6, NEW E7-S7)
E7-S1 → E7-S2 → E7-S3 → E7-S4 → E7-S5 → E7-S6 (all done)
                              ↓
E1-S8 (Site Config) → E7-S7 (Upload Site Config)

# UI Refresh (IN PROGRESS)
E8-S1/S2 → E8-S3/S4 → E8-S5/S6/S7 (done) → E8-S8/S9/S10 (drafted)

# Document Library (BACKLOG)
E1-S4 → E9-S1 → E9-S2 → E9-S3

# UI Simplification (BACKLOG)
E10-S1 (independent)
```

### NEW Story Dependencies (Victorian BAR + Research Integration 2026-02-05)
| New Story | Depends On | Blocks |
|-----------|------------|--------|
| E1-S10 (MinerU Integration) | E1-S2 (Domain Model) | E1-S3 (Pipeline) |
| E1-S11 (Parser Framework) | E1-S2 (Domain Model) | E1-S3 (Pipeline) |
| E1-S12 (Wording Normalization) | E1-S3 (Pipeline) | E5-S2 (Export) |
| E1-S8 (Site Config) | E1-S4 (API) | E7-S7 (Upload Config) |
| E1-S9 (Product Classification) | E1-S3 (Extraction) | E5-S2 (Excel Export) |
| E2-S8 (Column Visibility) | E2-S7 (Building Tabs) | - |
| E5-S3 (Template Management) | E5-S2 (Excel Export) | E5-S4 |
| E5-S4 (Field Mapping) | E5-S3 (Templates) | - |
| E7-S7 (Upload Site Config) | E1-S8, E7-S4 | - |

---

## MVP Scope Summary (UPDATED 2026-02-04)

**Must Have (MVP):**
- E1: S1-S5 (extraction pipeline core) ✅ DONE
- E1: **S10-S11 (NEW - MinerU, Parser Framework)** - Research Integration
- E1: **S8-S9, S12 (Site Config, Classification, Normalization)** - Victorian BAR
- E2: S1-S4, S7 (core spreadsheet + building tabs) ✅ DONE
- E2: **S8 (NEW - Column Visibility)** - Victorian BAR
- E3: S1-S3 (citations) ✅ DONE
- E4: S1, S3 (basic chat integration) ✅ DONE
- **E5: S1-S2 (CSV + Excel BAR export)** - PROMOTED to MVP
- E6: S1 (basic rebrand) ✅ DONE
- E7: S1-S6 (upload wizard) ✅ DONE
- E7: **S7 (NEW - Site Config during upload)** - Victorian BAR
- E9: S1 (document library view)
- E10: S1 (UI simplification - focus on ACM workflow)

**Should Have:**
- E1: S6 (local embeddings for privacy) ✅ DONE
- E2: S5, S6 (polish) ✅ DONE
- E3: S4 (page numbers) ✅ DONE
- E4: S2, S4 (chat polish) ✅ DONE
- E5: **S3-S4 (NEW - Template Management, Field Mapping)**
- E6: S2-S4 (full rebrand) ✅ DONE
- E9: S2, S3 (processing status, bulk actions)

**Could Have:**
- E8: All stories (UI refresh - nice to have) - In Progress

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

### E7-S7: Site Configuration During Upload (NEW - Victorian BAR)
**As a** user uploading ACM documents
**I want** to configure site metadata during upload
**So that** my documents are BAR-export ready immediately

**Acceptance Criteria:**
- [ ] Site configuration step appears after document type detection
- [ ] Pre-fill from PDF metadata where available (Address, Building Name)
- [ ] Dropdown selections for enum fields:
  - Department (DJCS, DHHS, DET, etc.)
  - Building Type
  - Owned or Leased
  - Frequency of use
  - Public Access?
- [ ] Validation: warn if required BAR fields are empty
- [ ] Copy configuration between similar documents
- [ ] Template configuration for recurring sites
- [ ] "Apply to all files" checkbox for batch uploads
- [ ] "Configure later" option with reminder

**Technical Notes:**
- Reuse SiteConfigForm component from E1-S8
- Store with source record metadata
- Location: Integrate into `frontend/src/components/wizard/` steps
- Reference: Sprint Change Proposal CP#5

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

---

## Epic 9: Document Library Management

### E9-S1: Create Document Library View
**As a** user
**I want** a dedicated view to manage all my uploaded documents
**So that** I can organize, monitor, and maintain my ACM document collection

**Acceptance Criteria:**
- [ ] Document Library page accessible from main navigation
- [ ] Grid/List view toggle for document display
- [ ] Show for each document: name, type, upload date, processing status, ACM record count
- [ ] Filter by: document type (SAMP, ACM Register, Other), processing status, date range
- [ ] Sort by: name, date, type, record count
- [ ] Search documents by name or content keywords
- [ ] Bulk selection with multi-select checkboxes
- [ ] Quick actions: View, Re-process, Delete, Download original

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/documents/page.tsx`
- Reuse existing Source model, extend with ACM-specific metadata
- Consider: separate route vs enhanced Sources page
- Reference: PRD Section 4.1 mentions Sources panel but lacks dedicated management

---

### E9-S2: Document Processing Status Dashboard
**As a** user
**I want** to see real-time processing status for all documents
**So that** I know what's being processed and can identify failures

**Acceptance Criteria:**
- [ ] Processing queue visualization (pending, in-progress, completed, failed)
- [ ] Real-time status updates via polling or WebSocket
- [ ] Progress percentage for documents being processed
- [ ] Estimated time remaining for large documents
- [ ] Error details with actionable messages for failures
- [ ] Retry button for failed documents
- [ ] Cancel button for in-progress documents
- [ ] Processing history log

**Technical Notes:**
- Location: `frontend/src/components/documents/ProcessingStatus.tsx`
- Backend: extend existing source processing to emit status events
- Consider: use React Query for polling or integrate WebSocket for real-time
- Reference: E7-S6 covers upload progress, this extends to full lifecycle

---

### E9-S3: Document Actions and Bulk Operations
**As a** user
**I want** to perform actions on documents individually and in bulk
**So that** I can efficiently manage my document collection

**Acceptance Criteria:**
- [ ] Individual document actions: View details, Open spreadsheet, Re-extract ACM, Delete
- [ ] Bulk actions: Delete selected, Re-process selected, Export selected
- [ ] Confirmation dialogs for destructive actions
- [ ] Progress feedback for bulk operations
- [ ] Undo capability for recent deletions (soft delete with grace period)
- [ ] Archive functionality (hide without delete)
- [ ] Document metadata editing (rename, add tags/notes)

**Technical Notes:**
- Location: `frontend/src/components/documents/DocumentActions.tsx`
- Backend: Add bulk operation endpoints to ACM API
- Consider: optimistic updates for better UX
- Reference: Existing MVP has basic actions, this adds comprehensive management

---

## Epic 10: ACM-AI UI Simplification

### E10-S1: Simplify Navigation for ACM-AI Focus
**As a** user
**I want** a simplified UI focused on ACM document management
**So that** I'm not distracted by features irrelevant to my ACM compliance workflow

**Acceptance Criteria:**
- [ ] Hide "Notebooks" navigation item (not needed for ACM workflow)
- [ ] Hide "Podcasts" navigation item (not relevant to compliance)
- [ ] Hide "Transformations" navigation item (advanced feature, not POC scope)
- [ ] Hide "Advanced" navigation item (developer features)
- [ ] Keep "Sources" navigation (document management)
- [ ] Keep "ACM Register" navigation (core functionality)
- [ ] Keep "Ask and Search" navigation (semantic search for compliance questions)
- [ ] Keep "Models" navigation (AI model configuration for local inference)
- [ ] Keep "Settings" navigation (user preferences)
- [ ] Navigation items hidden via feature flag or environment config
- [ ] Hidden items easily re-enabled via configuration (no hard delete)
- [ ] UI feels cohesive with reduced navigation (no empty groups)

**Technical Notes:**
- Location: `frontend/src/components/layout/AppSidebar.tsx`
- Implementation options:
  - Environment variable: `NEXT_PUBLIC_ACM_MODE=true`
  - Feature flag in settings
  - Conditional rendering in navigation config
- Keep hidden component code intact for future re-enablement
- Group navigation items logically after reduction:
  - "Documents": Sources
  - "ACM": ACM Register
  - "Search": Ask and Search
  - "Settings": Models, Settings
- Reference: Analysis of `AppSidebar.tsx` navigation structure
