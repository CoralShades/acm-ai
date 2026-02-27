# Epics and User Stories - ACM-AI

> **Project:** ACM-AI v1.0
> **Date:** 2025-12-07 (Updated: 2026-02-26)
> **Status:** Feature Complete + E22 Post-Audit Remediation Planned
> **Change Log:** 2026-02-26 — Epic 22 added (Post-Audit Remediation & Feature Completion, 5 stories, SCP-20260226B); 2026-02-26 — Epic 21 added (UX Loading States & Layout Consistency) + 3 post-audit bugs; 2026-02-23 — Epic 20 added (cross-site marketing-app navigation, env-driven URLs, Vercel domain cutover); 2026-02-22 — Final reconciliation: 7 remaining stories (E9-S3, E10-S1, E12-S2..S4, E13-S2, E13-S3) verified as implemented, marked Done; 112/122 done (92%); ALL feature epics complete; 2026-02-20 — E15 + E16 added, E9-S3/E10-S1 promoted

---

## Epic Overview

| Epic | Title | Priority | Stories | Status |
|------|-------|----------|---------|--------|
| E1 | ACM Data Extraction Pipeline | P0 | **31** | Done |
| E2 | AG Grid Spreadsheet Integration | P0 | **12** | Done |
| E3 | Cell Citations & PDF Viewer | P0 | 4 | Done |
| E4 | Chat with ACM Context | P0 | 4 | Done |
| E5 | Export Functionality | **P0** (promoted) | **4** | Done |
| E6 | Rebranding to ACM-AI | P1 | 4 | Done |
| E7 | Upload Wizard | P0 | **7** | Done |
| E8 | UI Refresh (Bento Grid) | P1 | 10 | Archived |
| E9 | Document Library Management | P0 | 3 | Done |
| E10 | ACM-AI UI Simplification | P0 | 1 | Done |
| E11 | Search & Retrieval Enhancement | P0/P1 | 2 | Done |
| E12 | Extraction Settings & Configuration UI | P1 | 4 | Done |
| E13 | Knowledge Graph Visualization | P1 | 3 | Done |
| E14 | UX & Enterprise Readiness | P0/P1 | 11 | Done |
| E15 | Extraction Monitor & Live Logging UI | P0 | 2 | Done |
| E16 | UX Enhancement Sprint | P0/P1 | 3 | Done |
| E17 | Live Extraction Intelligence — AG-UI + A2A + Observability | P0/P1 | 6 | Done |
| E19 | Marketing & Stakeholder Presentation | P1 | 1 | Done |
| E20 | Marketing-App Cross-Site Navigation & Domain Cutover | P0 | 2 | Done |
| E21 | UX Loading States & Layout Consistency | P1 | 3 | Drafted |
| E22 | Post-Audit Remediation & Feature Completion | P0/P1 | 5 | Drafted |
| E24 | TableFormer Table Structure Recognition | P0 | 4 | Done (flag OFF — regression) |
| E25 | Table Extraction Research Spike — Docling Direct API | P0 | 2 | Done |
| E26 | Docling Direct API Integration | P0 | 7 | Done (PROMOTE — 31/31, flag=true) |

> **2026-02-04 Update:** Victorian BAR format expansion added 6 new stories across E1, E2, E5, E7.
> E5 promoted from P1 to P0 (BAR Excel export is critical).
>
> **2026-02-05 Update:** Research integration added 3 new stories to E1:
> - E1-S10: MinerU table extraction
> - E1-S11: Extensible consultant parser framework
> - E1-S12: Consultant wording normalization
> Updated E1-S3 for two-stage pipeline and E1-S9 for official taxonomy.
>
> **2026-02-07 Update:** Document Intelligence Pipeline + Settings UI + Knowledge Graph:
> - E1-S16: Document Structure & TOC Extraction
> - E1-S17: Building Inventory Compilation
> - E1-S18: Page-Level Section Tagging
> - E1-S19: Document Metadata Extraction Enhancement
> - NEW Epic 12: Extraction Settings & Configuration UI (4 stories)
> - NEW Epic 13: Knowledge Graph Visualization (3 stories)
> Based on n8n workflow validation gap analysis.
>
> **2026-02-08 Update:** UX Audit & Enterprise Readiness initiative (Lane B):
> - NEW Epic 14: UX & Enterprise Readiness (11 stories, ALL DONE)
> - E14-S1 through E14-S11 implemented and merged to main via PR #7
>
> **2026-02-08 Update:** Course Correction - Generic Configurable Parser:
> - E1-S11 REDEFINED: "Extensible Parser Framework" -> "Generic Configurable Parser with BAR Field Schema"
>   - 3 parsers (Prensa, Greencap, Generic) -> 1 configurable parser driven by BAR template
>   - Status reset from done to backlog (requires reimplementation)
> - E12-S4 REDEFINED: "Parser Configuration Management" -> "BAR Field Schema Configuration UI"
> - E2-S8 ENHANCED: AG Grid columns generated from field config API
> - See: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md`

---

## Epic 1: ACM Data Extraction Pipeline

> **Implementation Evolution (2026-02-05 to 2026-02-08):**
> The pipeline evolved from the original 2-stage architecture (Stage 1: Extract, Stage 2: Interpret)
> to a comprehensive 7-stage document intelligence pipeline:
> - **Stage -1: Document Structure Analysis** (E1-S16) - TOC extraction, section hierarchy
> - **Stage -1.5: Building Inventory** (E1-S17) - Building metadata compilation, page ranges
> - **Stage 0: Preflight Validation** (Original design)
> - **Stage 0.5: Agentic Orchestrator** (E1-S20) - Planned for intelligent routing/correction
> - **Stage 1: Extraction** (E1-S3, E1-S10, E1-S11) - Verbatim extraction with MinerU, Generic Configurable Parser
> - **Stage 2: Interpretation** (E1-S3, E1-S9, E1-S12) - Normalization, taxonomy classification
> - **Stage 2.5: Corrective RAG Validation** (E1-S14, E1-S15) - Hybrid retrieval, contextual embeddings
> - **Stage 3: Post-Processing** (Original design)
>
> Additional enhancements include page-level section tagging (E1-S18), enhanced metadata extraction (E1-S19),
> and the shift from 3 specialized parsers to a single configurable parser driven by BAR field schema (E1-S11).
> Status: **20/20 stories complete** as of 2026-02-08.

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
  - [ ] Map consultant columns Ã¢â€ â€™ BAR columns
  - [ ] Normalize values to controlled enums (see PRD 5.5)
  - [ ] Classify products using taxonomy (see PRD 5.6)
  - [ ] Apply business rules (Negative Ã¢â€ â€™ N/A for Condition/Disturbance)
  - [ ] Validate against BAR schema
  - [ ] Output validated `ACMRecord` objects
- [ ] Identifies ACM Register tables by header patterns
- [ ] Extracts hierarchical structure (Building Ã¢â€ â€™ Room Ã¢â€ â€™ Item)
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

### E1-S11: Generic Configurable Parser with BAR Field Schema (REDEFINED 2026-02-08)
**As a** system
**I want** a single generic configurable parser driven by field schema configuration
**So that** any ACM PDF format can be parsed using configurable field definitions from the BAR template

> **Course Correction 2026-02-08:** Redefined from "Extensible Consultant Parser Framework".
> 3 specialized parsers (Prensa, Greencap, Generic) replaced by 1 configurable parser.
> BAR Excel template as single source of truth for fields, enums, rules.
> See: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md` (CP-1)

**Acceptance Criteria:**
- [ ] Load field schema from `register_row.schema.json` (47 fields with types, required/optional, column letters)
- [ ] Load enum picklists from `register_enums.json` (controlled values per field)
- [ ] Load business rules from config (e.g., Negative -> N/A for Condition)
- [ ] Single GenericParser class replaces PrensaParser, GreencapParser, GenericParser
- [ ] Parser accepts field config at initialization (which fields to extract, column mappings)
- [ ] Field config drives: extraction field list, enum validation, display names
- [ ] Default config seeded from BAR Excel template (Clucth_Alexandra_District_BAR.xlsm)
- [ ] API endpoint to read/update field configuration: GET/PUT /api/acm/field-config
- [ ] UI can override field config (see E12-S4)
- [ ] Remove PrensaParser and GreencapParser classes (consolidate into generic)

**Technical Notes:**
- Location: `open_notebook/extractors/parsers/`
  - `generic.py` - Rewritten GenericParser driven by FieldSchemaConfig
  - `field_config.py` - NEW: FieldSchemaConfig, FieldDef Pydantic models
  - `config_loader.py` - NEW: Load config from JSON/SurrealDB/Excel
  - `base.py` - KEEP: RawACMItem, DocumentMeta data classes still useful
  - `prensa.py` - DELETE: Absorbed into generic parser + config
  - `greencap.py` - DELETE: Absorbed into generic parser + config
- Reference: Architecture Section 5.2 (rewritten)
- Reference: `docs/samplePDF/instructions-sample/register_row.schema.json`
- Reference: `docs/samplePDF/instructions-sample/register_enums.json`

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

### E1-S16: Document Structure & TOC Extraction (NEW 2026-02-07)
**As a** system
**I want** to extract document structure, table of contents, and hierarchical page mapping
**So that** the extraction pipeline understands document organization before processing

**Acceptance Criteria:**
- [ ] Extract TOC from document (if present) with page ranges
- [ ] Build content hierarchy: Section -> Subsection -> Page Range
- [ ] Identify register start pages (typically pages 13+ for SAMPs)
- [ ] Map document sections: policy pages vs register pages vs appendices
- [ ] Detect document type (SAMP, Asbestos Risk Assessment, Division 5, etc.)
- [ ] Extract total page count and document structure statistics
- [ ] Output: `DocumentStructure` Pydantic model with section hierarchy
- [ ] Works on Prensa, Greencap, and generic SAMP formats

**Technical Notes:**
- Location: `open_notebook/extractors/document_structure.py`
- Prompt: `prompts/acm/structure_extraction.jinja`
- Integration: Runs as Stage -1, before Stage 0 (Preflight)
- Reference: N8N "AI #TOC and Page Indexes" agent

---

### E1-S17: Building Inventory Compilation (NEW 2026-02-07)
**As a** system
**I want** to compile a complete building inventory with page locations
**So that** extraction can target specific page ranges per building for higher accuracy

**Acceptance Criteria:**
- [ ] Identify all building codes (B000-series, D-series for demountables)
- [ ] Extract building metadata: name, year, construction type, purpose
- [ ] Map each building to its document page range
- [ ] Classify building complexity (simple "No Asbestos" vs complex register)
- [ ] Create processing groups of 3-5 pages based on building complexity
- [ ] Output: `BuildingInventory` with `BuildingMeta` entries
- [ ] Handles buildings spanning multiple pages
- [ ] Detects room codes (R000-series) within each building

**Technical Notes:**
- Location: `open_notebook/extractors/building_inventory.py`
- Prompt: `prompts/acm/building_inventory.jinja`
- Integration: Stage -1.5, between structure and per-building extraction
- Reference: N8N "Get Complete Building List and Metadata" agent

---

### E1-S18: Page-Level Section Tagging (NEW 2026-02-07)
**As a** system
**I want** to tag each page with its section classification and confidence score
**So that** the extraction pipeline can apply section-specific strategies

**Acceptance Criteria:**
- [ ] Standardized section taxonomy (0-7):
  - 0: Executive Summary, 1: Introduction, 2: Site Description
  - 3: Methodology, 4: Asbestos Register, 5: Risk Assessment
  - 6: Conclusion, 7: Appendix
- [ ] Each page tagged with: section_id, section_title, confidence (0.0-1.0)
- [ ] Page type classification: title_page, toc_page, content, special
- [ ] Subsection detection using document's actual numbering
- [ ] Contextual awareness: tracks progression through document
- [ ] Batch processing (3-5 pages per LLM call for efficiency)

**Technical Notes:**
- Location: `open_notebook/extractors/page_tagger.py`
- Prompt: `prompts/acm/page_tagging.jinja`
- Use efficient model (Haiku) for cost-effective page-level processing
- Reference: N8N "AI - Tag Page with Sections" agent

---

### E1-S19: Document Metadata Extraction Enhancement (NEW 2026-02-07)
**As a** system
**I want** to extract comprehensive document metadata beyond school_name and school_code
**So that** all BAR export fields are populated automatically where possible

**Acceptance Criteria:**
- [ ] Extract from cover page/header: address, suburb, postcode, organization, consultant, report reference, revision date, regional classification
- [ ] Extract from document body: inspection dates, inspector names, document scope, methodology
- [ ] Populate `DocumentMeta` Pydantic model with all extracted fields
- [ ] Auto-fill SiteConfig fields from extracted metadata
- [ ] Confidence scoring per field (extracted vs inferred)
- [ ] Works on Prensa, Greencap, and generic formats
- [ ] Integration with existing ConsultantParser.extract_metadata()

**Technical Notes:**
- Location: `open_notebook/extractors/metadata_extractor.py`
- Prompt: `prompts/acm/metadata_extraction.jinja`
- Enhance existing `parsers/prensa.py` and `parsers/greencap.py`
- Auto-fill `site_config` table during upload flow

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

> **Implementation Scope Expansion (2026-02-10):**
> Originally scoped as 4 basic stories for ACM-aware chat, the implementation expanded significantly
> to deliver a production-ready conversational AI interface:
> - **CopilotKit Integration** - Full CopilotKit provider setup with React hooks ecosystem
> - **AG-UI Protocol** - Server-sent events (SSE) streaming protocol for supervisor agent communication
> - **Supervisor Agent Backend** - FastAPI `/api/supervisor/stream` endpoint exposing LangGraph workflows
> - **Custom Tool Result Renderers** - ACM-specific renderers for extraction results, citations, tables
> - **Real-time Streaming** - SSE-based streaming responses with token-by-token rendering
> - **Dynamic Context Toggle** - User-controlled ACM context inclusion with visual indicators
>
> Implementation delivered across **15 files** (~1200 lines frontend, ~350 lines backend).
> Completed: **2026-02-10** via PR #16.
> Status: **All 4 original stories complete**, with significant value-add features included.

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
- UI: simple table with source Ã¢â€ â€™ target mapping
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
E1-S1 (Schema) Ã¢â€ â€™ E1-S2 (Domain Model) Ã¢â€ â€™ E1-S10 (MinerU) Ã¢â€ â€™ E1-S11 (Parser Framework)
                                              Ã¢â€ â€œ
                                        E1-S3 (Two-Stage Pipeline) Ã¢â€ â€™ E1-S12 (Wording Normalization)
                                              Ã¢â€ â€œ
                                        E1-S9 (Taxonomy Classification)
                                              Ã¢â€ â€œ
                                        E1-S4 (API) Ã¢â€ â€™ E1-S5 (Integration) Ã¢â€ â€™ E1-S6 Ã¢â€ â€™ E1-S7
                                              Ã¢â€ â€œ
# Victorian BAR stories
E1-S4 (API) Ã¢â€ â€™ E1-S8 (Site Config) Ã¢â€ â€™ E7-S7 (Upload Config)
E1-S3 (Extraction) Ã¢â€ â€™ E1-S9 (Product Classification)

# Spreadsheet (Ã¢Å“â€¦ DONE through E2-S7)
E2-S1 Ã¢â€ â€™ E2-S2 Ã¢â€ â€™ E2-S3/S4/S5/S6 Ã¢â€ â€™ E2-S7 (all done)
                  Ã¢â€ â€œ
# NEW: Column Visibility
E2-S7 Ã¢â€ â€™ E2-S8 (Column Visibility)

# Citations (Ã¢Å“â€¦ DONE)
E3-S1 Ã¢â€ â€™ E3-S2 Ã¢â€ â€™ E3-S3 Ã¢â€ â€™ E3-S4 (all done)

# Chat (Ã¢Å“â€¦ DONE)
E4-S1 Ã¢â€ â€™ E4-S2 Ã¢â€ â€™ E4-S3 Ã¢â€ â€™ E4-S4 (all done)

# Export (Ã¢Å“â€¦ S1-S2 DONE, NEW S3-S4)
E2-S2 Ã¢â€ â€™ E5-S1 Ã¢â€ â€™ E5-S2 (done)
              Ã¢â€ â€œ
E5-S2 Ã¢â€ â€™ E5-S3 (Template Management) Ã¢â€ â€™ E5-S4 (Field Mapping)

# Rebranding (Ã¢Å“â€¦ DONE)
E6-S1/S2/S3/S4 (all done)

# Upload Wizard (Ã¢Å“â€¦ DONE through E7-S6, NEW E7-S7)
E7-S1 Ã¢â€ â€™ E7-S2 Ã¢â€ â€™ E7-S3 Ã¢â€ â€™ E7-S4 Ã¢â€ â€™ E7-S5 Ã¢â€ â€™ E7-S6 (all done)
                              Ã¢â€ â€œ
E1-S8 (Site Config) Ã¢â€ â€™ E7-S7 (Upload Site Config)

# UI Refresh (IN PROGRESS)
E8-S1/S2 Ã¢â€ â€™ E8-S3/S4 Ã¢â€ â€™ E8-S5/S6/S7 (done) Ã¢â€ â€™ E8-S8/S9/S10 (drafted)

# Document Library (BACKLOG)
E1-S4 Ã¢â€ â€™ E9-S1 Ã¢â€ â€™ E9-S2 Ã¢â€ â€™ E9-S3

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

### NEW Story Dependencies (Document Intelligence + Settings + Knowledge Graph 2026-02-07)
| New Story | Depends On | Blocks |
|-----------|------------|--------|
| E1-S16 (TOC/Structure) | E1-S3 (Pipeline, done) | E1-S17 (Inventory) |
| E1-S17 (Building Inventory) | E1-S16 (Structure) | E1-S18 (Page Tagging) |
| E1-S18 (Page Tagging) | E1-S17 (Inventory) | - |
| E1-S19 (Metadata Enhancement) | E1-S16 (Structure) | - |
| E12-S1 (Extraction Settings) | E1-S16/17/18/19 | E12-S2, E12-S3 |
| E12-S2 (Model Config UI) | E12-S1 | - |
| E12-S3 (Processing Config) | E12-S1 | - |
| E12-S4 (BAR Field Schema Config UI) | E1-S11 (Generic Configurable Parser) | - |
| E13-S1 (Graph Schema) | E1-S4 (API, done) | E13-S2 |
| E13-S2 (Graph API) | E13-S1 | E13-S3 |
| E13-S3 (React Flow UI) | E13-S2 | - |

---

## MVP Scope Summary (UPDATED 2026-02-04)

**Must Have (MVP):**
- E1: S1-S5 (extraction pipeline core) Ã¢Å“â€¦ DONE
- E1: **S10-S11 (NEW - MinerU, Parser Framework)** - Research Integration
- E1: **S8-S9, S12 (Site Config, Classification, Normalization)** - Victorian BAR
- E2: S1-S4, S7 (core spreadsheet + building tabs) Ã¢Å“â€¦ DONE
- E2: **S8 (NEW - Column Visibility)** - Victorian BAR
- E3: S1-S3 (citations) Ã¢Å“â€¦ DONE
- E4: S1, S3 (basic chat integration) Ã¢Å“â€¦ DONE
- **E5: S1-S2 (CSV + Excel BAR export)** - PROMOTED to MVP
- E6: S1 (basic rebrand) Ã¢Å“â€¦ DONE
- E7: S1-S6 (upload wizard) Ã¢Å“â€¦ DONE
- E7: **S7 (NEW - Site Config during upload)** - Victorian BAR
- E9: S1 (document library view)
- E10: S1 (UI simplification - focus on ACM workflow)

**Should Have:**
- E1: S6 (local embeddings for privacy) Ã¢Å“â€¦ DONE
- E2: S5, S6 (polish) Ã¢Å“â€¦ DONE
- E3: S4 (page numbers) Ã¢Å“â€¦ DONE
- E4: S2, S4 (chat polish) Ã¢Å“â€¦ DONE
- E5: **S3-S4 (NEW - Template Management, Field Mapping)**
- E6: S2-S4 (full rebrand) Ã¢Å“â€¦ DONE
- E9: S2, S3 (processing status, bulk actions)

**Must Have (MVP) - Document Intelligence (NEW 2026-02-07):**
- E1: **S16 (Document Structure & TOC)** - Pre-extraction intelligence
- E1: **S17 (Building Inventory)** - Targeted per-building extraction
- E1: **S19 (Metadata Enhancement)** - Auto-populate BAR fields

**Should Have - Document Intelligence:**
- E1: **S18 (Page-Level Section Tagging)** - Section-aware extraction
- E12: **S1-S4 (Settings & Configuration UI)** - Operational flexibility
- E13: **S1-S3 (Knowledge Graph Visualization)** - Visual compliance auditing

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

---

## Epic 12: Extraction Settings & Configuration UI (NEW 2026-02-07)

> **Created:** 2026-02-07 (Sprint Change Proposal - Document Intelligence Pipeline)
> **Rationale:** Operators need to manage extraction methods, AI models, processing options,
> and parser configurations without developer intervention.

### E12-S1: Extraction Method Settings Page
**As a** user
**I want** a settings page to configure extraction methods and preferences
**So that** I can control how documents are processed without changing code

**Acceptance Criteria:**
- [ ] Settings page accessible from navigation under "Settings"
- [ ] Extraction method selection: MinerU / Docling / Hybrid (default: Hybrid)
- [ ] Fallback behavior: Enable/Disable automatic fallback
- [ ] Document intelligence pipeline toggles:
  - Enable/Disable TOC extraction
  - Enable/Disable building inventory compilation
  - Enable/Disable page-level section tagging
  - Enable/Disable document metadata extraction
- [ ] Settings persisted in SurrealDB `extraction_settings` table
- [ ] Settings applied globally (default) or per-source override
- [ ] API endpoints: GET/PUT `/api/settings/extraction`
- [ ] Reset to defaults button

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/extraction/page.tsx`
- Backend: `api/routers/settings.py`
- Domain: `open_notebook/domain/settings.py`

---

### E12-S2: AI Model Configuration UI
**As a** user
**I want** to configure which AI models are used for each extraction stage
**So that** I can balance cost, speed, and accuracy per operation

**Acceptance Criteria:**
- [ ] Model selection per extraction stage:
  - Structure analysis, Building inventory, ACM extraction
  - Page tagging, Product classification, Corrective validation
- [ ] Available models populated from existing model registry
- [ ] Cost/speed indicator per model
- [ ] Test button: run extraction on sample page with selected model
- [ ] Settings saved per extraction stage
- [ ] API endpoints: GET/PUT `/api/settings/models`

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/models/page.tsx`
- Integrate with existing Esperanto model abstraction
- Use existing `model` table for available models

---

### E12-S3: Processing Options Configuration
**As a** user
**I want** to configure processing parameters like chunk size and confidence thresholds
**So that** I can tune extraction performance for different document types

**Acceptance Criteria:**
- [ ] Processing parameters: Chunk size (2000-8000), Confidence threshold (0.0-1.0), Max correction attempts (1-5), Batch size (1-10)
- [ ] Timeout settings: Per-page (10-120s), Total document (1-30min)
- [ ] Output preferences: Store raw JSON, Auto-classify, Auto-normalize
- [ ] Presets: "Fast", "Balanced" (default), "Thorough"
- [ ] API endpoints: GET/PUT `/api/settings/processing`

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/processing/page.tsx`
- Store in `processing_settings` SurrealDB table

---

### E12-S4: BAR Field Schema Configuration UI (REDEFINED 2026-02-08)
**As a** user
**I want** a UI to view and manage the BAR field schema configuration
**So that** I can configure which fields are extracted, customize display names, and manage picklist values

> **Course Correction 2026-02-08:** Redefined from "Parser Configuration Management".
> Replaces "manage multiple parsers" with "configure one field schema."
> See: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md` (CP-2)

**Acceptance Criteria:**
- [ ] Field Schema Editor: View/toggle/reorder 47 BAR fields, edit display names
- [ ] Picklist Value Editor: View/edit enum values per field, import from BAR template
- [ ] Business Rules Editor: View/enable/disable rules, add custom rules
- [ ] Config Import/Export: Import from BAR Excel, export as JSON, reset to defaults
- [ ] Config applies to: extraction, AG Grid columns, Excel/CSV export
- [ ] API endpoints: GET/PUT /api/settings/field-schema

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/field-schema/page.tsx`
- Backend: Extend `api/routers/settings.py` with field-schema endpoints
- Depends on: E1-S11 (Generic Configurable Parser must provide the config API)

---

## Epic 13: Knowledge Graph Visualization (NEW 2026-02-07)

> **Created:** 2026-02-07 (Sprint Change Proposal - Document Intelligence Pipeline)
> **Rationale:** Visual mapping of document entity relationships enables compliance auditing,
> risk assessment at a glance, and understanding extraction provenance.
> Uses React Flow for interactive graph rendering and SurrealDB native graph capabilities.

### E13-S1: SurrealDB Graph Entity Schema
**As a** developer
**I want** separate entity tables and relationship tables in SurrealDB
**So that** document entities have proper graph relationships

**Acceptance Criteria:**
- [ ] New entity tables: `school`, `building`, `room`
- [ ] New relationship tables (SurrealDB RELATION type):
  - `school_has_building` (FROM school TO building)
  - `building_has_room` (FROM building TO room)
  - `room_has_acm` (FROM room TO acm_record)
  - `extracted_from` (FROM acm_record TO source)
- [ ] Migration script to create tables and backfill from existing acm_record data
- [ ] `acm_record` retains embedded fields for backward compatibility
- [ ] Graph traversal queries work end-to-end
- [ ] Pydantic models for all new entities

**Technical Notes:**
- Migration: `migrations/XX.surrealql`
- Domain: `open_notebook/domain/graph_entities.py`
- Backfill: Extract unique schools/buildings/rooms from existing acm_records

---

### E13-S2: Knowledge Graph API & Data Service
**As a** frontend developer
**I want** API endpoints that return graph-structured data for React Flow
**So that** the frontend can render entity relationship diagrams

**Acceptance Criteria:**
- [ ] API endpoints:
  - `GET /api/graph/source/{source_id}` - Full graph for a source
  - `GET /api/graph/school/{school_id}` - School-centric graph
  - `GET /api/graph/building/{building_id}` - Building-centric graph
  - `GET /api/graph/stats/{source_id}` - Graph statistics
- [ ] Response format: React Flow compatible nodes and edges JSON
- [ ] Auto-layout calculation (hierarchical top-down via dagre)
- [ ] Risk summary aggregation per node
- [ ] Filter options: by risk level, by building, by ACM status

**Technical Notes:**
- Location: `api/routers/graph.py`, `api/graph_service.py`
- Use SurrealDB graph traversal for data fetching
- Auto-layout: dagre algorithm

---

### E13-S3: React Flow Knowledge Graph Visualization
**As a** user
**I want** an interactive knowledge graph showing entity relationships for each PDF
**So that** I can visually understand document structure and identify risk areas

**Acceptance Criteria:**
- [ ] Knowledge Graph tab in source detail view
- [ ] React Flow canvas with custom nodes:
  - School node (top level): name, code, address
  - Building node: name, year, construction, risk summary badge
  - Room node: name, area, ACM count
  - ACM node: product, risk color (red/yellow/green), friability icon
- [ ] Interactive features: click for details, zoom/pan, expand/collapse groups, risk filter, minimap
- [ ] Layout options: Hierarchical (default), Force-directed
- [ ] Export graph as PNG/SVG
- [ ] Toggle between graph view and spreadsheet view

**Technical Notes:**
- Location: `frontend/src/components/acm/KnowledgeGraph.tsx`
- Dependencies: `@xyflow/react` (React Flow v12+), `dagre`
- Custom nodes: `frontend/src/components/acm/graph-nodes/`
- Integration: Tab in source detail page alongside spreadsheet

---

## Epic 14: UX & Enterprise Readiness (NEW 2026-02-08)

> **Created:** 2026-02-08 (UX Audit & Enterprise Readiness Initiative - Lane B)
> **Rationale:** Government compliance mandates professional branding, accessibility standards,
> and streamlined navigation. UX audit findings drive 30 improvements across 11 stories.
> **Owner:** Lane B (Frontend)
> **Dependency:** E14-S1 (Design Tokens) is foundational -- all visual E14 stories depend on it.
> **Spec References:** `docs/ux-audit.md`, `docs/design-system.md`, `docs/ui-ux-spec.md`,
> `docs/navigation-cleanup-spec.md`, `docs/state-loading-spec.md`, `docs/ag-ui-pipeline-spec.md`

### E14-S1: Apply VAEA Branding and Design Tokens (P0)
**As a** government client
**I want** the application to use VAEA's official branding
**So that** it meets government presentation standards

**Acceptance Criteria:**
- [ ] CSS custom properties defined for VAEA color palette (light + dark mode)
- [ ] Tailwind 4 `@theme inline` configured with VAEA tokens
- [ ] OKLCH color space used for all brand colors
- [ ] VAEA logo (`VAEA-Ripple2-Logo_Print.png`) replaces current logo
- [ ] VAEA favicon replaces current favicon
- [ ] CoralShades vendor attribution in sidebar footer
- [ ] Focus ring color set to VAEA coral (#EB787A) for accessibility
- [ ] Government design patterns: left-border accent cards, system font stack, 12px border-radius

**Spec Reference:** `docs/design-system.md` Sections 1-6, 14 (Migration Checklist)

**Key Files to Modify:**
- `frontend/src/app/globals.css` -- Replace `:root` and `.dark` token blocks
- `frontend/tailwind.config.ts` -- Update `@theme inline` section
- `frontend/src/config/branding.ts` -- Update brand config
- `frontend/src/components/brand/Logo.tsx` -- Replace with VAEA logo
- `frontend/public/` -- Replace logo.svg, icon.svg, favicon, manifest.json

---

### E14-S2: Redesign Sidebar Navigation (P0)
**As a** compliance officer
**I want** a simplified navigation with WORKSPACE and CONFIGURE sections
**So that** I can easily find ACM-related features

**Acceptance Criteria:**
- [ ] Sidebar sections changed to WORKSPACE (Dashboard, Documents, ACM Register, Search) and CONFIGURE (Extraction, AI Models, Parsers, Processing, General)
- [ ] "Upload Document" primary CTA button at top of sidebar
- [ ] Create button dropdown replaced with single "Upload Document" action
- [ ] VAEA logo and CoralShades footer in sidebar
- [ ] Theme toggle and sign out in sidebar footer

**Spec Reference:** `docs/navigation-cleanup-spec.md` Section 3, `docs/ui-ux-spec.md` Section 3
**Depends On:** E14-S1 (needs VAEA tokens for sidebar styling)

**Key Files to Modify:**
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/lib/stores/navigation-store.ts`
- `frontend/src/components/common/AddButton.tsx`

---

### E14-S3: Hide Brownfield Features from Navigation (P0)
**As a** product owner
**I want** Podcasts, Transformations, and Notebooks hidden from navigation
**So that** the UI focuses on ACM compliance workflow

**Acceptance Criteria:**
- [ ] Podcasts removed from sidebar nav items
- [ ] Transformations removed from sidebar nav items
- [ ] Notebooks removed from sidebar nav items (pages still accessible via direct URL)
- [ ] Command palette entries for hidden features removed
- [ ] Create dialog no longer shows Notebook or Podcast options
- [ ] Code is preserved (not deleted) -- only nav entries removed

**Spec Reference:** `docs/navigation-cleanup-spec.md` Section 4

**Key Files to Modify:**
- `frontend/src/components/layout/AppSidebar.tsx`
- `frontend/src/components/common/CommandPalette.tsx`
- `frontend/src/components/common/AddButton.tsx` or create dialog

---

### E14-S4: Add Shimmer Skeleton Loading Screens (P1)
**As a** user
**I want** skeleton loading placeholders on every page
**So that** I see content structure immediately instead of a blank screen

**Acceptance Criteria:**
- [ ] Skeleton screen for Dashboard (bento grid layout)
- [ ] Skeleton screen for Documents page (card grid + filters)
- [ ] Skeleton screen for ACM Register (toolbar + AG Grid rows)
- [ ] Skeleton screen for Source Detail (panels layout)
- [ ] Skeleton screen for Search page
- [ ] Shimmer animation with CSS keyframes (2s linear infinite)
- [ ] Dark mode adaptation (lighter shimmer on dark surfaces)
- [ ] `aria-busy="true"` and screen reader announcements
- [ ] Zero CLS (skeleton dimensions match actual content)

**Spec Reference:** `docs/state-loading-spec.md` Section 4

**Key Files to Create:**
- `frontend/src/components/skeletons/DashboardSkeleton.tsx`
- `frontend/src/components/skeletons/DocumentsSkeleton.tsx`
- `frontend/src/components/skeletons/ACMRegisterSkeleton.tsx`
- `frontend/src/components/skeletons/SourceDetailSkeleton.tsx`
- `frontend/src/components/skeletons/SearchSkeleton.tsx`

---

### E14-S5: Enhance Toast System with Promise-Based Patterns (P1)
**As a** user
**I want** informative toast notifications during long operations
**So that** I know what's happening with extraction, export, and processing

**Acceptance Criteria:**
- [ ] Sonner `toast.promise()` used for extraction start/complete/fail
- [ ] Sonner `toast.promise()` used for Excel/CSV export
- [ ] Loading toast with manual ID for SSE/polling progress updates
- [ ] Risk-aware toast variants (border-l-4 with risk colors)
- [ ] Persistent toasts (`duration: Infinity`) for critical alerts
- [ ] Action buttons in toasts for human-in-the-loop workflows

**Spec Reference:** `docs/state-loading-spec.md` Section 6

**Key Files to Modify:**
- `frontend/src/lib/toast-patterns.ts` (new)
- `frontend/src/components/acm/ACMExtractionBanner.tsx`
- `frontend/src/lib/api/acm.ts`

---

### E14-S6: WCAG 2.1 AA Accessibility Audit and Fixes (P1)
**As a** government application
**I want** WCAG 2.1 AA compliance
**So that** the application meets government accessibility mandates

**Acceptance Criteria:**
- [ ] All interactive elements have visible focus indicators (VAEA coral ring)
- [ ] Color contrast ratio meets 4.5:1 for normal text, 3:1 for large text
- [ ] All images and icons have appropriate alt text or aria-labels
- [ ] AG Grid keyboard navigation verified and documented
- [ ] Form inputs have associated labels
- [ ] Pipeline visualization has `aria-live` regions for status updates
- [ ] Skip-to-content link on all pages
- [ ] Reduced motion preference respected (`prefers-reduced-motion`)

**Spec Reference:** `docs/ux-audit.md` Finding ACC-01, `docs/design-system.md` Section 8
**Depends On:** E14-S1 (needs VAEA tokens for focus ring colors)

**Key Files to Modify:**
- `frontend/src/app/globals.css` -- Focus ring styles, skip-to-content
- `frontend/src/app/layout.tsx` -- Skip-to-content link
- `frontend/src/components/acm/ACMSpreadsheet.tsx` -- AG Grid a11y
- Multiple component files for aria-labels

---

### E14-S7: Merge Sources and Documents into Unified View (P1)
**As a** user
**I want** a single Documents page instead of separate Sources and Documents views
**So that** I have one place to find all my uploaded files

**Acceptance Criteria:**
- [ ] `/sources` and `/documents` merged into unified `/documents` route
- [ ] `/sources` redirects to `/documents` via middleware
- [ ] `/sources/[id]` continues to work (source detail page)
- [ ] Grid/table/list view toggle preserved
- [ ] All document filters available
- [ ] Bulk actions preserved

**Spec Reference:** `docs/navigation-cleanup-spec.md` Section 5

**Key Files to Modify:**
- `frontend/src/app/documents/page.tsx` (new or merge)
- `frontend/src/middleware.ts` -- Add redirect
- `frontend/src/components/layout/AppSidebar.tsx` -- Update nav

---

### E14-S8: Improve Error Recovery and Disconnect Handling (P2)
**As a** user
**I want** graceful handling of connection drops and errors
**So that** I don't lose my work or get confused when something fails

**Acceptance Criteria:**
- [ ] Enhanced `ConnectionGuard` with reconnection attempts
- [ ] Session timeout detection with re-authentication prompt
- [ ] Offline indicator banner
- [ ] Route-level error boundaries on all dashboard pages
- [ ] Retry logic in API client for transient failures
- [ ] Network status check on window focus

**Spec Reference:** `docs/state-loading-spec.md` Section 8

**Key Files to Create/Modify:**
- `frontend/src/components/common/ConnectionGuard.tsx` (enhance)
- `frontend/src/components/common/OfflineBanner.tsx` (new)
- `frontend/src/components/common/ErrorBoundary.tsx` (new or enhance)
- `frontend/src/lib/api/client.ts` -- Retry logic

---

### E14-S9: Expand Keyboard Navigation and Shortcuts (P2)
**As a** power user
**I want** keyboard shortcuts for common actions
**So that** I can work efficiently without a mouse

**Acceptance Criteria:**
- [ ] Command palette (Cmd+K) entries for all primary actions
- [ ] AG Grid keyboard navigation (arrow keys, Enter to expand)
- [ ] Escape to close dialogs/panels
- [ ] Tab navigation through pipeline stages
- [ ] Shortcut cheat sheet accessible via `?` key

**Spec Reference:** `docs/ux-audit.md` Finding NAV-03

**Key Files to Modify:**
- `frontend/src/components/common/CommandPalette.tsx`
- `frontend/src/components/acm/ACMSpreadsheet.tsx`
- `frontend/src/components/common/KeyboardShortcutSheet.tsx` (new)

---

### E14-S10: Add Breadcrumb Navigation for Deep Pages (P2)
**As a** user viewing a source detail page
**I want** breadcrumb navigation showing my location
**So that** I can easily navigate back to the parent page

**Acceptance Criteria:**
- [ ] Breadcrumb component created following VAEA design tokens
- [ ] Breadcrumbs shown on: Source detail, ACM Register (within source), Notebook detail
- [ ] Links are functional (clicking "Documents" goes to documents list)
- [ ] Responsive: truncated with ellipsis on mobile

**Spec Reference:** `docs/ui-ux-spec.md` Section 7

**Key Files to Create/Modify:**
- `frontend/src/components/common/Breadcrumbs.tsx` (new)
- `frontend/src/app/sources/[id]/page.tsx` -- Add breadcrumbs
- `frontend/src/app/sources/[id]/acm/page.tsx` -- Add breadcrumbs

---

### E14-S11: Set Up Pydantic-to-TypeScript Type Generation (P2)
**As a** developer
**I want** TypeScript types auto-generated from Python Pydantic models
**So that** frontend and backend types are always in sync

**Acceptance Criteria:**
- [ ] `scripts/generate_types.py` created
- [ ] Generates TypeScript interfaces from ACMRecord, ACMExtractionOutput, etc.
- [ ] Output to `frontend/src/lib/types/generated/`
- [ ] `npm run generate:types` script in package.json
- [ ] CI workflow detects type drift on PRD model changes

**Spec Reference:** `docs/ag-ui-pipeline-spec.md` Section 7

**Key Files to Create:**
- `scripts/generate_types.py`
- `frontend/src/lib/types/generated/acm.ts` (output)
- `.github/workflows/type-check.yml` (CI)

---

## Epic 15: Extraction Monitor & Live Logging UI

> **Priority:** P0
> **Added:** 2026-02-20 (SCP-20260220)
> **Status:** Done (2/2 stories)
> **Rationale:** Backend SSE pipeline and frontend log components (ExtractionProgressPanel, ExtractionLogStream,
> StageProgressPill, use-extraction-progress.ts) were fully implemented in E1-S21 but are only accessible
> during the upload wizard. This epic surfaces them persistently throughout the app.

### E15-S1: Extraction Log Panel in Document Library (P0)
**As a** compliance officer reviewing document processing
**I want** to click any document and see the full extraction log with stage-by-stage progress
**So that** I can understand what the AI extracted, identify failures, and retry without re-uploading

**Acceptance Criteria:**
- [ ] Document Library rows have expand chevron
- [ ] Expanding shows ExtractionProgressPanel (stage pills + log terminal)
- [ ] Active docs: live SSE stream via `/api/acm/extraction-progress/{commandId}/stream`
- [ ] Completed docs: loads historical log via REST fallback endpoint
- [ ] Stage pills: STRUCTURE, PREFLIGHT, ORCHESTRATOR, EXTRACT, VALIDATE, CORRECT, STORE
- [ ] Log terminal scrollable, monospace, Copy All button
- [ ] Retry button for failed/partial extractions
- [ ] Keyboard accessible (Enter/Space expand, Escape collapse)

**Technical Notes:**
- All backend and frontend components exist Ã¢â‚¬â€ wiring only
- Requires `command_id` exposed in `SourceResponse` from `api/models.py`

**Key Files:** `frontend/src/components/documents/DocumentRow.tsx`, `api/models.py`

**Story File:** `docs/sprint-artifacts/e15-s1-extraction-log-panel.md`

---

### E15-S2: Dedicated Extraction Monitor Page (P0)
**As a** system administrator
**I want** a single page showing all active and historical extractions with full log detail
**So that** I can monitor system health, debug failures, and manage the extraction queue

**Acceptance Criteria:**
- [ ] Route: `/extraction-monitor` in sidebar CONFIGURE section
- [ ] Active tab: live SSE per extraction, auto-refresh
- [ ] History tab: paginated list, filter by status + date range
- [ ] Expandable log terminal per extraction
- [ ] Retry button for failed/partial
- [ ] Empty states for both tabs

**Technical Notes:**
- New `GET /api/acm/extraction-progress` list endpoint needed
- Reuses ExtractionProgressPanel from E15-S1

**Key Files:** `frontend/src/app/(dashboard)/extraction-monitor/page.tsx`, `api/routers/extraction_events.py`

**Story File:** `docs/sprint-artifacts/e15-s2-extraction-monitor-page.md`

---

## Epic 16: UX Enhancement Sprint

> **Priority:** P0 (E16-S2) / P1 (E16-S1, E16-S3)
> **Added:** 2026-02-20 (SCP-20260220)
> **Status:** Done (3/3 stories)
> **Rationale:** Three high-impact UX patterns absent after E14: no system dashboard, no full-record view,
> no empty states. E9-S3 (bulk operations) promoted from drafted to ready-for-dev alongside this epic.

### E16-S1: Dashboard Home Page with ACM Stats (P1)
**As a** user opening ACM-AI
**I want** a dashboard overview with system metrics and quick actions
**So that** I understand the system state at a glance

**Acceptance Criteria:**
- [ ] New home route with summary cards: total records, buildings, documents processed, risk breakdown
- [ ] Risk distribution donut chart (Recharts)
- [ ] Top 10 buildings by record count (horizontal bar chart)
- [ ] Recent activity: last 5 extractions with status
- [ ] Quick actions: Upload SAMP, View ACM Register, Extraction Monitor
- [ ] Skeleton loading for all sections
- [ ] New backend endpoint: `GET /api/acm/stats`

**Key Files:** `frontend/src/app/(dashboard)/page.tsx`, `api/routers/stats.py`

**Story File:** `docs/sprint-artifacts/e16-s1-dashboard-home.md`

---

### E16-S2: ACM Record Detail Slide-Out Panel (P0)
**As a** compliance officer reviewing records
**I want** to click an ACM record row to see all its fields in a readable panel
**So that** I can review full record details without horizontal scrolling

**Acceptance Criteria:**
- [ ] Click row Ã¢â€ â€™ 380px right slide-out drawer
- [ ] All 47 fields in 8 organized sections (org, building, location, ACM details, assessment, docs, removal, metadata)
- [ ] Empty fields shown as "Ã¢â‚¬â€", booleans as YES/NO badges
- [ ] "View in PDF" button opens existing PDF viewer at page_number
- [ ] Edit mode toggle Ã¢â€ â€™ inline editing Ã¢â€ â€™ Save/Cancel Ã¢â€ â€™ PUT /api/acm/{id}
- [ ] Ã¢â€ Â Ã¢â€ â€™ arrow keys cycle through records
- [ ] Escape closes panel

**Key Files:** `frontend/src/components/acm/ACMRecordDetailPanel.tsx`, `frontend/src/components/acm/ACMSpreadsheet.tsx`

**Story File:** `docs/sprint-artifacts/e16-s2-record-detail-panel.md`

---

### E16-S3: Empty States & Onboarding Hints (P1)
**As a** new user opening ACM-AI
**I want** helpful guidance when there are no documents or records
**So that** I know what to do next

**Acceptance Criteria:**
- [ ] Documents page empty state: upload CTA
- [ ] ACM Register empty state: "extract a SAMP" prompt
- [ ] Chat empty state: "add ACM context" guide
- [ ] Extraction Monitor empty states (active + history tabs)
- [ ] Dismissable onboarding hints on Documents page and ACM Register (localStorage)
- [ ] Shared EmptyState and OnboardingHint components

**Key Files:** `frontend/src/components/common/EmptyState.tsx`, `frontend/src/components/common/OnboardingHint.tsx`

**Story File:** `docs/sprint-artifacts/e16-s3-empty-states.md`

---

## Epic 17: Live Extraction Intelligence Ã¢â‚¬â€ AG-UI + A2A + Real-time Observability

> **Added:** 2026-02-22
> **Priority:** P0/P1
> **Status:** Done (6/6 stories)

**Goal:** Transform the extraction pipeline from a black box into a live, observable, interoperable system. Records appear incrementally, agent reasoning is visible, tool calls are tracked, and the service is discoverable via A2A protocol.

**Dependencies:** Builds on existing AG-UI/CopilotKit infrastructure (E4 chat), PipelineLogger (E1-S3), SSE extraction progress (E15).

---

### E17-S1: AG-UI Extraction Pipeline Endpoint (P0) Ã¢â‚¬â€ Done

**As a** developer integrating with the extraction pipeline
**I want** AG-UI compliant SSE events emitted during extraction
**So that** the frontend can display real-time extraction state via CopilotKit

**Acceptance Criteria:**
- [x] `GET /api/agui/extraction/{command_id}/stream` returns AG-UI compliant SSE
- [x] Events: RunStarted, StepStarted/Finished per node, StateDelta, ToolCallStart/End, RunFinished/RunError
- [x] Existing SSE at `/api/acm/extraction-progress/` unchanged
- [x] 500ms poll interval, heartbeat every 15s
- [x] Stream auto-closes on RunFinished/RunError

**Key Files:** `open_notebook/extractors/agui_event_emitter.py`, `api/routers/agui_extraction.py`, `migrations/21.surrealql`, `open_notebook/graphs/acm_extraction.py`

**Story File:** `docs/sprint-artifacts/e17-s1-agui-extraction-endpoint.md`

---

### E17-S2: Incremental Record Streaming to AG Grid (P0) Ã¢â‚¬â€ Done

**As a** user running extraction
**I want** records to appear in the AG Grid as they are extracted (not all at the end)
**So that** I can see progress and catch issues early

**Acceptance Criteria:**
- [x] Records appear in AG Grid within 2s of each chunk being processed
- [x] Preview records visually distinguished (italic/ghost styling with pulsing border)
- [x] On completion, preview records replaced by final saved records
- [x] Chunk progress counter visible (e.g., "Chunk 3/8")

**Key Files:** `frontend/src/lib/hooks/use-extraction-agent.ts`, `frontend/src/components/acm/PreviewRecordBadge.tsx`, `frontend/src/components/acm/ACMGrid.tsx`, `frontend/src/components/acm/ACMTab.tsx`

**Story File:** `docs/sprint-artifacts/e17-s2-incremental-record-streaming.md`

---

### E17-S3: Reasoning Token Display (P1) Ã¢â‚¬â€ Done

**As a** user using reasoning models (DeepSeek R1, Claude extended thinking)
**I want** to see the model's reasoning process during extraction
**So that** I can understand how the AI is interpreting the document

**Acceptance Criteria:**
- [x] Collapsible "Agent Thinking" panel in ExtractionProgressPanel
- [x] Streams reasoning tokens character-by-character
- [x] Hidden by default, user can expand
- [x] Non-reasoning models: panel doesn't appear

**Key Files:** `frontend/src/components/acm/ExtractionThinkingPanel.tsx`, `frontend/src/components/acm/ExtractionProgressPanel.tsx`

**Story File:** `docs/sprint-artifacts/e17-s3-reasoning-token-display.md`

---

### E17-S4: Extraction Tool Call Observability (P1) Ã¢â‚¬â€ Done

**As a** user monitoring an extraction
**I want** to see which extraction step is running and what it's doing
**So that** I can understand progress and diagnose issues

**Acceptance Criteria:**
- [x] Each graph node transition shows as a tool call entry
- [x] In-flight calls show spinner + elapsed time
- [x] Completed calls show check + result summary + duration
- [x] Args displayed: chunk_index, page_range, model_id, content_length

**Key Files:** `frontend/src/components/acm/ExtractionToolCallFeed.tsx`, `frontend/src/components/acm/ExtractionProgressPanel.tsx`

**Story File:** `docs/sprint-artifacts/e17-s4-extraction-tool-observability.md`

---

### E17-S5: A2A Agent Card + Task Lifecycle (P1) Ã¢â‚¬â€ Done

**As a** developer building multi-agent workflows
**I want** the extraction service discoverable via A2A protocol
**So that** other agents can find and invoke extraction capabilities

**Acceptance Criteria:**
- [x] `GET /.well-known/agent.json` returns valid A2A agent card
- [x] `POST /api/a2a/tasks` accepts extraction task, returns task_id
- [x] `GET /api/a2a/tasks/{task_id}` returns status (submitted/working/completed/failed)
- [x] A2A task maps to existing `acm_extract` surreal-command internally

**Key Files:** `api/routers/a2a.py`, `api/static/.well-known/agent.json`, `api/main.py`

**Story File:** `docs/sprint-artifacts/e17-s5-a2a-agent-card.md`

---

### E17-S6: New OpenRouter Model Additions (P1) Ã¢â‚¬â€ Done

**As a** user wanting access to frontier AI models
**I want** 6 new models available via OpenRouter
**So that** I can choose the best model for extraction quality/cost

**Models Added:**
- MiniMax M2.1 (`minimax/minimax-m2.1`, 196K context)
- Kimi K2.5 (`moonshotai/kimi-k2.5`, 262K context)
- DeepSeek V3.2 (`deepseek/deepseek-v3.2`, 163K context)
- Claude Sonnet 4.6 (`anthropic/claude-sonnet-4.6`, 1M context)
- GPT 5.2 (`openai/gpt-5.2`, 400K context)
- Gemini 2.5 Pro (`google/gemini-2.5-pro`, 1M context)

**Acceptance Criteria:**
- [x] 6 new models in `MODEL_CATALOG`
- [x] `_PROVIDER_DEFAULTS` entries for each with correct context_window/max_output
- [x] `supports_structured_output` and `supports_tool_calling` detection updated
- [x] `seed_model_catalog()` creates them on startup when `OPENROUTER_API_KEY` set

**Key Files:** `api/model_provisioning.py`, `open_notebook/domain/models.py`

**Story File:** `docs/sprint-artifacts/e17-s6-new-openrouter-models.md`

---

## Epic 20: Marketing-App Cross-Site Navigation & Domain Cutover

> **Added:** 2026-02-23
> **Priority:** P0
> **Status:** Done (2/2 stories)

### E20-S1: Marketing to App Linking (P0) â€” Done
**As a** user landing on the public website  
**I want** obvious and consistent calls-to-action to open the app workspace  
**So that** I can move from marketing content into the product quickly

**Acceptance Criteria:**
- [x] Header includes external `Open App` action using environment-configured host
- [x] Hero primary CTA uses `Open App` and targets app host
- [x] Footer includes `Open App` in Product links
- [x] URL source is `NEXT_PUBLIC_APP_URL` with safe default for production subdomain

**Key Files:** `marketing-site/src/components/Navigation.tsx`, `marketing-site/src/components/landing/Hero.tsx`, `marketing-site/src/components/Footer.tsx`, `marketing-site/src/lib/site-urls.ts`

**Story File:** `docs/sprint-artifacts/e20-s1-marketing-to-app-linking.md`

---

### E20-S2: App to Marketing Navigation + Domain Cutover Contract (P0) â€” Done
**As a** user inside the app workspace  
**I want** direct links back to landing and documentation  
**So that** I can move between product usage and informational content without confusion

**Acceptance Criteria:**
- [x] App sidebar includes `Visit Landing` and `Documentation` external links
- [x] Command palette includes external commands for landing/docs
- [x] URL source is `NEXT_PUBLIC_MARKETING_URL` and derived docs URL
- [x] Env examples document cross-site URL contract for Vercel deployments
- [x] Deployment docs define root-domain marketing + demo subdomain app topology

**Key Files:** `frontend/src/config/navigation.ts`, `frontend/src/components/layout/AppSidebar.tsx`, `frontend/src/components/common/CommandPalette.tsx`, `frontend/src/lib/site-urls.ts`, `docs/marketing-site/deployment.md`

**Story File:** `docs/sprint-artifacts/e20-s2-app-to-marketing-navigation-cutover.md`

---

## Epic 21: UX Loading States & Layout Consistency

> **Added:** 2026-02-26 (SCP-20260226)
> **Priority:** P1
> **Status:** Drafted (0/3 stories)

### E21-S1: Global Loading States & Transition Feedback (P1)
**As a** compliance officer,
**I want** visual feedback when pages load, buttons process, and extraction runs,
**So that** the app doesn't feel broken or unresponsive.

**Acceptance Criteria:**
- [ ] Button click states: all primary action buttons show spinner/disabled during API calls
- [ ] Page transitions: shimmer skeleton appears immediately when navigating between routes
- [ ] Extraction feedback: when extraction is running, show animated progress indicator
- [ ] Upload feedback: after file upload, show processing state before redirect
- [ ] API loading: all data-fetching components show skeleton
- [ ] Empty → Loading → Content → Error state machine for every page
- [ ] No blank white screens during any navigation

**Specific Implementation:**
- Reuse existing Skeleton components from E14-S4
- Add React Suspense boundaries at route level in app/(dashboard)/layout.tsx
- Add loading.tsx files for each route group

**Story File:** `docs/sprint-artifacts/e21-s1-loading-states-transitions.md`

---

### E21-S2: Jobs Pages Layout Consistency (P1)
**As a** compliance officer,
**I want** the jobs/review pages to use the same professional layout as the ACM Register page,
**So that** the UI feels consistent and polished throughout the workflow.

**Acceptance Criteria:**
- [ ] Jobs dashboard (`/jobs`) uses same card layout patterns as Dashboard home
- [ ] Job detail page (`/jobs/[id]`) uses same panel layout as Source Detail page
- [ ] Building review (`/jobs/[id]/review/buildings`) uses same toolbar pattern as ACM Register
- [ ] Records review (`/jobs/[id]/review/records`) uses same tab pattern as Job Detail page
- [ ] All pages use consistent spacing (p-6 outer, gap-4 between sections)
- [ ] All pages use VAEA design tokens from E14-S1
- [ ] Dark mode works consistently across all job pages

**Specific Implementation:**
- Adapt existing E19 components to match E14 patterns (do not rebuild from scratch)
- Reference the ACM Register page (`/acm`) as the layout standard

**Story File:** `docs/sprint-artifacts/e21-s2-jobs-layout-consistency.md`

---

### E21-S3: Extraction Progress Real-Time Feedback (P1)
**As a** compliance officer,
**I want** to see real-time progress when my document is being extracted,
**So that** I know the system is working and how long it will take.

**Acceptance Criteria:**
- [ ] After upload + extraction trigger, user sees animated progress indicator
- [ ] Progress indicator shows: current stage name, stage progress (x/7), elapsed time
- [ ] Stages light up sequentially as extraction progresses through pipeline
- [ ] When extraction completes, auto-transition to review page
- [ ] If extraction fails, show clear error message with retry button
- [ ] Extraction progress visible from Job Detail page (`/jobs/[id]`) extraction tab
- [ ] Extraction progress visible from Jobs list (`/jobs`) as progress bar on job card

**Specific Implementation:**
- Wire existing SSE infrastructure (`ExtractionProgressPanel`) into Jobs flow
- Use `use-extraction-progress` hook

**Story File:** `docs/sprint-artifacts/e21-s3-extraction-progress-feedback.md`

---

## Epic 22: Post-Audit Remediation & Feature Completion

> **Added:** 2026-02-26 (SCP-20260226B)
> **Priority:** P0/P1
> **Status:** Drafted (0/5 stories)

### E22-S1: Schema Resilience - Normalize Instead of Reject (P0)
**As a** system,
**I want** field validators to normalize unexpected LLM values instead of rejecting entire buildings,
**So that** extraction does not lose records due to minor enum mismatches.

**Acceptance Criteria:**
- [ ] `risk_status` validator normalizes `Moderate` -> `Medium` instead of raising `ValueError`
- [ ] All `field_validator` logic in `ACMExtractionRecord` and `acm_validator.py` follows normalize-or-passthrough behavior
- [ ] No field validator raises `ValueError` for close enum variants; it normalizes and logs
- [ ] `data_issues` captures normalization events
- [ ] Existing tests still pass

**Specific Implementation:**
- Apply shared normalization contract across schema-level and validator-level logic
- Persist and log normalization decisions for auditability

**Story File:** `docs/sprint-artifacts/e22-s1-schema-resilience.md`

---

### E22-S2: Dashboard Layout Regression Fix (P0)
**As a** compliance officer,
**I want** the dashboard to show the sidebar, header, and footer like all other pages,
**So that** navigation and layout remain consistent.

**Acceptance Criteria:**
- [ ] Dashboard (`/`) renders through the `(dashboard)` layout wrapper
- [ ] All `(dashboard)` pages show consistent sidebar + header + footer
- [ ] `loading.tsx` files do not break layout wrapper rendering
- [ ] No blank white screen during dashboard navigation

**Specific Implementation:**
- Align root dashboard route behavior with existing route-group shell behavior
- Validate loading boundary interactions in App Router

**Story File:** `docs/sprint-artifacts/e22-s2-dashboard-layout-fix.md`

---

### E22-S3: Job Detail = Source Detail Layout (PDF + Chat + Content) (P1)
**As a** compliance officer,
**I want** the job detail page to include PDF preview, extracted content, and inline chat in one layout,
**So that** I can review everything in context.

**Acceptance Criteria:**
- [ ] Add `Content` tab with rendered markdown (`source.full_text`) and PDF download/preview link
- [ ] Add right-side inline chat panel on job detail page (not separate route)
- [ ] Reuse existing `CopilotProvider` and CRUD chat endpoint integration
- [ ] Chat collapses on narrow screens to a floating button pattern
- [ ] Unicode arrow labels render correctly and are not shown as escaped strings
- [ ] Match Source Detail two-column layout (content left, chat right)

**Specific Implementation:**
- Use `sources/[id]` detail page layout as the implementation reference
- Keep chat and content scoped to job detail route context

**Story File:** `docs/sprint-artifacts/e22-s3-job-detail-source-layout.md`

---

### E22-S4: Building Tabs in ACM Register + Job ACM Records (P1)
**As a** compliance officer,
**I want** per-building tabs on records grids,
**So that** I can filter by building without scrolling large combined datasets.

**Acceptance Criteria:**
- [ ] Extract reusable `BuildingTabFilter` from review-records implementation
- [ ] Tabs show All Records and per-building counts
- [ ] Tab selection filters AG Grid rows by building
- [ ] Tabs scroll horizontally without overlap when many buildings exist
- [ ] Spacing and labels are fixed (no overlap regression)
- [ ] Building counts remain accurate as records change
- [ ] Wire into `/acm`, `/jobs/[id]` ACM Records tab, and `/jobs/[id]/review/records`

**Specific Implementation:**
- Consolidate tab UI and count/filter logic into one shared component
- Reuse existing review records behavior as baseline

**Story File:** `docs/sprint-artifacts/e22-s4-building-tabs-everywhere.md`

---

### E22-S5: Extraction Streaming & Navigation Polish (P1)
**As a** compliance officer,
**I want** meaningful extraction progress and smooth page transitions,
**So that** long-running operations feel responsive and transparent.

**Acceptance Criteria:**
- [ ] Show stage-by-stage extraction progress (stage names, X/7, elapsed time)
- [ ] Auto-fetch and display records immediately when extraction completes
- [ ] Show global navigation progress bar during page compilation/transitions
- [ ] Show smooth loading indicator when navigating between pages
- [ ] Surface provider schema/compatibility errors in extraction log UI
- [ ] Optional backend path: per-building save + per-building SSE events

**Specific Implementation:**
- Enhance `extract/page.tsx` and `use-extraction-progress.ts` first
- Keep backend Option B isolated and optional behind frontend-first polish delivery

**Story File:** `docs/sprint-artifacts/e22-s5-extraction-streaming-polish.md`

---

## Technical Bug Fixes (Standalone)

> **Added:** 2026-02-26 (SCP-20260226)
> **Status:** Drafted

### Post-Audit Fixes
1. **bug-frontend-build-lightning-css**: Fix lighting CSS build issues in frontend
2. **bug-stale-commands-cleanup**: Fix and clean up stale application and database commands
3. **bug-agui-path-alignment**: Correct paths and naming for AG-UI tools to align with technical debt items

---

## Epic 25: Table Extraction Research Spike — Docling Direct API (P0)

> **Added:** 2026-02-27
> **Status:** Done
> **Evidence:** `docs/reviews/e25-table-extraction-comparison.md`

### E25-S1: Environment Setup + Tool Verification — Done
**Story File:** N/A (research spike)

### E25-S2: PyMuPDF vs Docling Direct API Comparison — Done
**As a** architect,
**I want** empirical comparison of PyMuPDF and Docling Direct API on Broadmeadows,
**So that** I can make an evidence-based architecture decision for E26.

**Key Results:**
- Docling DataFrames: 29/31 (93.5%), 9/9 "Same as", 4/6 "Not Sampled"
- Processing time: 22.41s (acceptable)
- Page 8 gap: 2 records missing (below TableFormer detection threshold)
- Recommendation: Hybrid Approach A (PyMuPDF + Docling Direct API)

**Story File:** `docs/reviews/e25-table-extraction-comparison.md`

### E25-S3: Architecture Decision + E26 Technical Design — Done
**As a** architect,
**I want** an ADR decision and technical design based on E25-S2 evidence,
**So that** implementation can proceed with a validated blueprint.

**Deliverables:**
- ADR-001 D5: `docs/architecture/adr-tableformer-integration.md`
- E26 Technical Design: `docs/architecture/e26-table-extraction-technical-design.md`
- E26 stories: 5 stories, 9 SP

---

## Epic 26: Docling Direct API Integration (P0)

> **Added:** 2026-02-27
> **Status:** Done (PROMOTE — 31/31, 100%)
> **ADR:** ADR-001 D5 (PROMOTED 2026-02-28)
> **Tech Design:** `docs/architecture/e26-table-extraction-technical-design.md`
> **Target:** Broadmeadows >= 30/31 (96.8%), Alexander maintains 54/54
> **Result:** Broadmeadows 31/31 (100%), Alexander 52/52 (maintained)
> **Total:** 7 stories, 12 SP

### E26-S1: Add Docling Direct API Extraction to Source Processing [M — 3 SP]
**As a** system,
**I want** to extract structured DataFrames from PDFs using Docling Direct API,
**So that** row-coherent table data is available for LLM extraction.

**Acceptance Criteria:**
- [ ] `_extract_tables_with_docling()` runs Docling DocumentConverter on PDFs
- [ ] Feature flag `DOCLING_DIRECT_TABLE_EXTRACTION` controls the path (default: false)
- [ ] DataFrames stored in `acm_table_section` with `table_type="docling_direct_api"`
- [ ] Sample number normalization: `34511-039- 001` → `34511-039-001`
- [ ] Hazard status normalization: strip "Asbestos " prefix
- [ ] Per-table error handling — one failure doesn't block others
- [ ] `source.full_text` remains PyMuPDF output (unchanged)
- [ ] Unit tests for extraction, normalization, storage
- [ ] New migration adds `structured_json` field to `acm_table_section`

**File Changes:**
- `commands/source_commands.py` — new functions + integration
- `migrations/N.surrealql` — `structured_json` field
- `.env.example` — new flag
- `tests/test_source_commands_docling.py` — new tests

**Story File:** `docs/sprint-artifacts/e26-s1-docling-direct-api.md`

---

### E26-S2: Broadmeadows DataFrame Validation [S — 1 SP]
**As a** QA engineer,
**I want** to validate Docling DataFrames against E25 spike results,
**So that** the integration produces the expected table structure.

**Acceptance Criteria:**
- [ ] 8 tables stored in `acm_table_section` (3 register, 5 other)
- [ ] 30 register rows across tables on pages 5-7
- [ ] 9/9 "Same as" rows present
- [ ] 4/6 "Not Sampled" rows present (matching E25 spike)
- [ ] DataFrame column structure matches E25 report
- [ ] Validation report: `docs/reviews/e26-s2-validation-results.md`

**Depends On:** E26-S1

---

### E26-S3: Inject Docling Tables into Orchestrator Context [M — 3 SP]
**As a** system,
**I want** the orchestrator to inject Docling DataFrame markdown into LLM context,
**So that** the LLM receives structured table data alongside full_text for better extraction.

**Acceptance Criteria:**
- [ ] `_get_docling_tables()` loads tables from `acm_table_section` by page range
- [ ] `_inject_docling_tables()` appends DataFrame markdown to building content
- [ ] Supplementary prompt instruction for structured table handling
- [ ] "Same as", "Not Sampled", "No Access" explicitly mentioned in prompt
- [ ] If no Docling tables: existing behavior unchanged
- [ ] Integration test: extraction with Docling tables produces >= 29 records

**File Changes:**
- `open_notebook/extractors/orchestrator.py` — new functions + modify `extract_building()`
- `prompts/acm/building_extraction.j2` — add structured table instruction
- `tests/test_orchestrator_docling.py` — new tests

**Depends On:** E26-S1

---

### E26-S4: Accuracy Validation — Target 30+/31 [S — 1 SP]
**As a** product owner,
**I want** full pipeline validation with a decision gate,
**So that** we only promote the feature flag when accuracy targets are met.

**Acceptance Criteria:**
- [ ] Full extraction pipeline on Broadmeadows with Docling tables ON
- [ ] Cross-reference against ground truth CSV (31 records)
- [ ] Decision gate: >= 30/31 → promote flag; < 28/31 → rollback
- [ ] Alexander regression check: must maintain 54/54
- [ ] Record #9 (Switch Room / Battery Charger) must be captured
- [ ] Validation report: `docs/reviews/e26-s4-validation-results.md`

**Depends On:** E26-S3

---

### E26-S5: Frontend — Enhanced Raw Tables Display [S — 1 SP]
**As a** compliance officer,
**I want** the Raw Tables tab to show Docling-extracted tables,
**So that** I can review high-quality structured table data from PDFs.

**Acceptance Criteria:**
- [ ] Raw Tables tab displays Docling tables from `acm_table_section`
- [ ] HTML rendering quality verified (clean `<table>` elements)
- [ ] Markdown fallback works for non-HTML consumers
- [ ] No regression for non-Docling sources
- [ ] Optional: "Source" indicator showing extraction method

**Can run in parallel with S3-S4.**
**Depends On:** E26-S1

---

### E26-S6: Accuracy Fixes — Dedup + Prompt + Regex Fallback [M — 3 SP]
**Status**: Done

- Added `location` to dedup key (fixed Record #9 merge)
- Strengthened structured table extraction prompt ("each row = one record")
- Added `_recover_no_access_records()` regex fallback (Records #30, #31)
- Result: 31/31 (100%) on Broadmeadows

**Depends On:** E26-S4

---

### E26-S7: Alexander Ground Truth + Closeout [S — 1 SP]
**Status**: Done

- Installed 43-record ground truth CSV (manually cleaned from BAR xlsm)
- Promoted `DOCLING_DIRECT_TABLE_EXTRACTION` flag to `true`
- Updated ADR-001 D5 decision status to PROMOTED
- E26 total: 7 stories, 12 SP

**Depends On:** E26-S6

---

## Epic 27: Structured Output Resilience (P1 — Bug Fix)

**Priority**: P1
**Goal**: Fix the `completionState` JSON envelope wrapping that breaks Pydantic structured output parsing in the orchestrator and pre-extraction intelligence modules, recovering Alexander District Hospital extraction from 0/43 to >= 40/43.
**Trigger**: E26-S4 validation revealed 0/43 Alexander extraction (all 6 building-level LLM calls fail due to OpenRouter `completionState` envelope)
**GitHub Issue**: https://github.com/CoralShades/acm-ai/issues/81

### E27-S1: Fix completionState Wrapper Parsing in Orchestrator [M — 3 SP]
**Status**: Drafted

- Add `_unwrap_completion_state()` utility to `graphs/utils.py`
- Add fallback path in orchestrator's `_invoke()` for `ValidationError` from `with_structured_output()`
- Apply same unwrapping to `document_structure.py`, `building_inventory.py`, `page_tagger.py`
- Unit tests for unwrapping + fallback path
- Integration validation: Alexander >= 40/43, Broadmeadows maintains 31/31
- Story file: `docs/sprint-artifacts/e27-s1-completionstate-wrapper-parsing-fix.md`

**Depends On:** None (standalone bug fix)
