# Sprint Change Proposal: Document Intelligence Pipeline, Settings UI & Knowledge Graph

> **Date:** 2026-02-07
> **Status:** ✅ APPROVED (2026-02-10)
> **Prepared by:** PM (via Course Correction Workflow)
> **Approved by:** Demi
> **Triggers:**
> 1. N8N Workflow Gap Analysis - Validated MVP extraction pipeline against codebase
> 2. New Feature Request - Settings/Configuration UI for extraction management
> 3. New Feature Request - Knowledge Graph Visualization with React Flow
> **Previous Proposals:** RAG Strategy Alignment (2026-02-07), Victorian BAR Format (2026-02-04)

---

## 1. Issue Summary

### Problem Statement

Analysis of the original approved MVP n8n workflow agent pipeline against the current ACM-AI codebase reveals **5 critical extraction intelligence gaps**. The n8n workflow had a sophisticated document understanding pipeline that the codebase does not replicate:

1. **No TOC/Document Structure Extraction** - The n8n "AI #TOC and Page Indexes" agent built full content hierarchies with page ranges. The codebase only looks for "Appendix B: Asbestos Register" markers.

2. **No Building Inventory Compilation** - The n8n "Get Complete Building List and Metadata" agent created a complete building inventory with page locations before extraction. The codebase processes the entire document in one pass.

3. **No Page-Level Section Tagging** - The n8n "AI - Tag Page with Sections" agent maintained conversational memory across pages with confidence-scored section assignments. The codebase has no equivalent.

4. **Minimal Document Metadata Extraction** - Only school_name and school_code are extracted. The n8n workflow extracted suburb, postcode, organization, document type, revision date, consultant info, regional classification.

5. **No Processing Group Optimization** - The n8n workflow grouped 3-5 pages by building complexity for targeted extraction. The codebase chunks by token limits, not logical document boundaries.

Additionally, two new features are requested:
- **Settings/Configuration UI** for managing extraction methods, AI models, and processing options
- **Knowledge Graph Visualization** using React Flow to visualize entity relationships per PDF

### Discovery Context
- **Discovered during:** N8N workflow validation against codebase
- **Evidence:** Complete n8n workflow JSON definitions with 5 agent configurations
- **Validated against:** `open_notebook/graphs/acm_extraction.py`, `open_notebook/extractors/`, `prompts/acm/`

### Impact Level
**MAJOR** - Requires new extraction pipeline stages, new epic, and new frontend pages

---

## 2. Impact Analysis

### 2.1 Epic Impact

| Epic | Status | Impact | Details |
|------|--------|--------|---------|
| E1 (Extraction) | in-progress | **HIGH** | +4 new stories for document intelligence pipeline |
| E2 (Spreadsheet) | in-progress | LOW | No changes |
| **NEW E12** | proposed | **NEW EPIC** | Extraction Settings & Configuration UI (4 stories) |
| **NEW E13** | proposed | **NEW EPIC** | Knowledge Graph Visualization (3 stories) |
| All others | various | None | No changes |

### 2.2 Artifact Changes Required

#### PRD Updates
- Section 2.1: Add FR-111 to FR-115 (Document Intelligence requirements)
- Section 2.3: Add FR-313 to FR-315 (Settings UI requirements)
- Section 4.2: Add Knowledge Graph component
- **NEW:** Section 5.9 Document Intelligence Pipeline
- **NEW:** Section 5.10 Settings & Configuration Architecture

#### Architecture Updates
- Section 5: Add Document Intelligence stages (Stage -1: Structure Analysis)
- Section 3.1: Add graph entity tables (school, building, room as separate tables)
- Section 6: Add Settings UI and Knowledge Graph component architecture
- **NEW:** Section 13 Knowledge Graph Architecture

#### Epic/Story Updates
- E1-S16 (NEW): Document Structure & TOC Extraction
- E1-S17 (NEW): Building Inventory Compilation
- E1-S18 (NEW): Page-Level Section Tagging
- E1-S19 (NEW): Document Metadata Extraction Enhancement
- E12-S1 (NEW): Extraction Method Settings Page
- E12-S2 (NEW): AI Model Configuration UI
- E12-S3 (NEW): Processing Options Configuration
- E12-S4 (NEW): Parser Configuration Management
- E13-S1 (NEW): SurrealDB Graph Entity Schema
- E13-S2 (NEW): Knowledge Graph API & Data Service
- E13-S3 (NEW): React Flow Knowledge Graph Visualization

### 2.3 Story Count Impact

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total Stories | 62 | 73 | +11 |
| Stories Done | 50 | 50 | 0 |
| Stories Remaining | 12 | 23 | +11 |
| Total Epics | 11 | 13 | +2 |

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment

**Rationale:**
1. **Additive changes** - All new stories build on existing foundation without rework
2. **Clear n8n precedent** - The extraction intelligence gaps are well-defined from working n8n agents
3. **Independent workstreams** - Document intelligence, settings UI, and knowledge graph can be parallelized
4. **Maintains momentum** - Current in-progress work continues unaffected

### Implementation Strategy

**Phase 1: Document Intelligence (P0)**
1. E1-S16: Document Structure & TOC Extraction
2. E1-S17: Building Inventory Compilation
3. E1-S18: Page-Level Section Tagging
4. E1-S19: Document Metadata Extraction Enhancement

**Phase 2: Settings & Configuration (P1)**
5. E12-S1: Extraction Method Settings Page
6. E12-S2: AI Model Configuration UI
7. E12-S3: Processing Options Configuration
8. E12-S4: Parser Configuration Management

**Phase 3: Knowledge Graph (P1 - Optional)**
9. E13-S1: SurrealDB Graph Entity Schema
10. E13-S2: Knowledge Graph API & Data Service
11. E13-S3: React Flow Knowledge Graph Visualization

### Effort Estimate
- **Phase 1:** 1-2 sprints (core extraction intelligence)
- **Phase 2:** 1 sprint (settings UI)
- **Phase 3:** 1-2 sprints (knowledge graph, optional)

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Document structure varies across formats | Medium | Medium | Start with Prensa/Greencap patterns, extend via parser framework |
| LLM token costs for page-level processing | Medium | Low | Batch pages, use efficient models (Haiku for tagging) |
| React Flow learning curve | Low | Low | Well-documented library, many examples |
| SurrealDB graph query performance | Low | Medium | Use native graph traversal, index relationships |

---

## 4. Detailed Change Proposals

### CP#6: Document Structure & TOC Extraction (E1-S16) - PENDING

**Story:**

**As a** system
**I want** to extract document structure, table of contents, and hierarchical page mapping from PDF documents
**So that** the extraction pipeline understands document organization before processing individual sections

**Acceptance Criteria:**
- [ ] Extract TOC from document (if present) with page ranges
- [ ] Build content hierarchy: Section → Subsection → Page Range
- [ ] Identify register start pages (typically pages 13+ for SAMPs)
- [ ] Map document sections: policy pages vs register pages vs appendices
- [ ] Detect document type (SAMP, Asbestos Risk Assessment, Division 5, etc.)
- [ ] Extract total page count and document structure statistics
- [ ] Output: `DocumentStructure` Pydantic model with section hierarchy
- [ ] Works on Prensa, Greencap, and generic SAMP formats
- [ ] LangGraph node integrates into existing extraction pipeline as Stage -1

**Technical Notes:**
- Location: `open_notebook/extractors/document_structure.py` (new)
- Prompt template: `prompts/acm/structure_extraction.jinja` (new)
- Pydantic model: `DocumentStructure`, `Section`, `SubSection`
- Integration: Runs before Stage 0 (Preflight), output feeds into Stage 1
- Reference: N8N "AI #TOC and Page Indexes" agent prompt

---

### CP#7: Building Inventory Compilation (E1-S17) - PENDING

**Story:**

**As a** system
**I want** to compile a complete building inventory with page locations from the document structure
**So that** extraction can target specific page ranges per building for higher accuracy

**Acceptance Criteria:**
- [ ] Identify all building codes (B000-series, D-series for demountables)
- [ ] Extract building metadata: name, year, construction type, purpose
- [ ] Map each building to its document page range
- [ ] Classify building complexity (simple "No Asbestos" vs complex register data)
- [ ] Create processing groups of 3-5 pages based on building complexity
- [ ] Output: `BuildingInventory` with `BuildingMeta` entries
- [ ] Handles buildings spanning multiple pages
- [ ] Detects room codes (R000-series) within each building
- [ ] LangGraph node runs after structure extraction, before per-building extraction

**Technical Notes:**
- Location: `open_notebook/extractors/building_inventory.py` (new)
- Prompt template: `prompts/acm/building_inventory.jinja` (new)
- Pydantic models: `BuildingInventory`, `BuildingMeta`, `ProcessingGroup`
- Integration: Stage -1.5, between document structure and per-building extraction
- Reference: N8N "Get Complete Building List and Metadata" agent prompt

---

### CP#8: Page-Level Section Tagging (E1-S18) - PENDING

**Story:**

**As a** system
**I want** to tag each page with its section classification and confidence score
**So that** the extraction pipeline can apply section-specific extraction strategies

**Acceptance Criteria:**
- [ ] Standardized section taxonomy (0-7):
  - 0: Executive Summary (optional)
  - 1: Introduction / Scope
  - 2: Site Description / Building Information
  - 3: Methodology
  - 4: Asbestos Register / ACM Data
  - 5: Risk Assessment / Recommendations
  - 6: Conclusion
  - 7: Appendix (Lab Results, Certificates, Photos)
- [ ] Each page tagged with: section_id, section_title, confidence (0.0-1.0)
- [ ] Page type classification: title_page, toc_page, content, special
- [ ] Subsection detection using document's actual numbering
- [ ] Contextual awareness: tracks progression through document
- [ ] Output: `PageTag[]` array with section assignments
- [ ] Batch processing (process 3-5 pages per LLM call for efficiency)

**Technical Notes:**
- Location: `open_notebook/extractors/page_tagger.py` (new)
- Prompt template: `prompts/acm/page_tagging.jinja` (new)
- Pydantic model: `PageTag` with section, confidence, page_type
- Integration: Runs after building inventory, feeds targeted extraction
- Use efficient model (Haiku) for cost-effective page-level processing
- Reference: N8N "AI - Tag Page with Sections" agent prompt

---

### CP#9: Document Metadata Extraction Enhancement (E1-S19) - PENDING

**Story:**

**As a** system
**I want** to extract comprehensive document metadata beyond school_name and school_code
**So that** all BAR export fields are populated automatically where possible

**Acceptance Criteria:**
- [ ] Extract from cover page / header:
  - School/site name and code
  - Street address, suburb, postcode
  - Organization / agency name
  - Consultant company and contact
  - Report reference number
  - Revision date and version
  - Regional classification
- [ ] Extract from document body:
  - Inspection date(s)
  - Inspector/hygienist name(s)
  - Document scope (buildings covered)
  - Methodology references
- [ ] Populate `DocumentMeta` Pydantic model with all extracted fields
- [ ] Auto-fill SiteConfig fields from extracted metadata
- [ ] Confidence scoring per field (extracted vs inferred)
- [ ] Works on Prensa, Greencap, and generic formats
- [ ] Integration with existing ConsultantParser.extract_metadata()

**Technical Notes:**
- Location: `open_notebook/extractors/metadata_extractor.py` (new)
- Enhance existing `parsers/prensa.py` and `parsers/greencap.py` metadata methods
- Prompt template: `prompts/acm/metadata_extraction.jinja` (new)
- Auto-fill `site_config` table during upload flow
- Reference: N8N "Get Complete Building List and Metadata" metadata section

---

### CP#10: Extraction Settings & Configuration Epic (E12) - PENDING

**Epic 12: Extraction Settings & Configuration UI**

> **Rationale:** Operators need to manage extraction methods, AI models, processing options, and parser configurations without developer intervention. Currently these are hardcoded or require code changes.

#### E12-S1: Extraction Method Settings Page

**As a** user
**I want** a settings page to configure extraction methods and preferences
**So that** I can control how documents are processed without changing code

**Acceptance Criteria:**
- [ ] Settings page accessible from main navigation under "Settings"
- [ ] Extraction method selection:
  - Primary method: MinerU / Docling / Hybrid (default: Hybrid)
  - Fallback behavior: Enable/Disable automatic fallback
  - MinerU toggle: Enable/Disable MinerU table extraction
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
- Location: `frontend/src/app/(dashboard)/settings/extraction/page.tsx` (new)
- Backend: `api/routers/settings.py` (new)
- Domain: `open_notebook/domain/settings.py` (new)
- Use React Hook Form + Zod for form validation
- Store in `extraction_settings` SurrealDB table

#### E12-S2: AI Model Configuration UI

**As a** user
**I want** to configure which AI models are used for each extraction stage
**So that** I can balance cost, speed, and accuracy per operation

**Acceptance Criteria:**
- [ ] Model selection per extraction stage:
  - Structure analysis: Model dropdown (default: Claude Haiku)
  - Building inventory: Model dropdown (default: Claude Haiku)
  - ACM extraction: Model dropdown (default: Claude Sonnet)
  - Page tagging: Model dropdown (default: Claude Haiku)
  - Product classification: Model dropdown (default: Claude Sonnet)
  - Corrective validation: Model dropdown (default: Claude Sonnet)
- [ ] Available models populated from existing model registry
- [ ] Cost/speed indicator per model
- [ ] Test button: run extraction on sample page with selected model
- [ ] Settings saved per extraction stage
- [ ] API endpoints: GET/PUT `/api/settings/models`

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/models/page.tsx` (new)
- Integrate with existing Esperanto model abstraction
- Use existing `model` table for available models
- Show token usage estimates per model selection

#### E12-S3: Processing Options Configuration

**As a** user
**I want** to configure processing parameters like chunk size, confidence thresholds, and retry settings
**So that** I can tune extraction performance for different document types

**Acceptance Criteria:**
- [ ] Processing parameters:
  - Chunk size (tokens): Slider 2000-8000 (default: 4000)
  - Confidence threshold: Slider 0.0-1.0 (default: 0.7)
  - Max correction attempts: 1-5 (default: 3)
  - Batch size for page processing: 1-10 (default: 5)
- [ ] Timeout settings:
  - Per-page timeout (seconds): 10-120 (default: 30)
  - Total document timeout (minutes): 1-30 (default: 10)
- [ ] Output preferences:
  - Store raw extraction JSON: Yes/No (default: Yes)
  - Auto-classify products: Yes/No (default: Yes)
  - Auto-normalize wording: Yes/No (default: Yes)
- [ ] Presets: "Fast" (lower accuracy, faster), "Balanced" (default), "Thorough" (higher accuracy, slower)
- [ ] API endpoints: GET/PUT `/api/settings/processing`

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/processing/page.tsx` (new)
- Store in `processing_settings` SurrealDB table
- Presets are shortcuts that set multiple parameters at once

#### E12-S4: Parser Configuration Management

**As a** user
**I want** to view and manage consultant parser configurations
**So that** I can add support for new document formats and tune existing parsers

**Acceptance Criteria:**
- [ ] List all registered parsers with status (active/inactive)
- [ ] Per-parser details:
  - Parser name and description
  - Detection patterns (company markers)
  - Column mapping table (source column → BAR column)
  - Sample detection test: paste text, see if parser detects it
- [ ] Enable/disable individual parsers
- [ ] Parser priority ordering (drag-and-drop reorder)
- [ ] Column mapping editor: visual table mapping source → target fields
- [ ] Export/import parser configuration as JSON
- [ ] API endpoints: GET/PUT/POST `/api/settings/parsers`
- [ ] Read-only for built-in parsers, editable for custom

**Technical Notes:**
- Location: `frontend/src/app/(dashboard)/settings/parsers/page.tsx` (new)
- Backend: Extend `api/routers/settings.py`
- Store custom parser configs in `parser_config` SurrealDB table
- Built-in parsers (Prensa, Greencap, Generic) are code-defined, not DB-stored

---

### CP#11: Knowledge Graph Visualization Epic (E13) - PENDING

**Epic 13: Knowledge Graph Visualization**

> **Rationale:** Visual mapping of document entity relationships enables compliance auditing, risk assessment at a glance, and understanding extraction provenance. SurrealDB has native graph capabilities that should be leveraged.

#### E13-S1: SurrealDB Graph Entity Schema

**As a** developer
**I want** separate entity tables and relationship tables in SurrealDB
**So that** document entities have proper graph relationships instead of embedded string fields

**Acceptance Criteria:**
- [ ] New entity tables:
  - `school` (name, code, suburb, postcode, address, organization)
  - `building` (building_id, name, year, construction, purpose, size_m2, levels)
  - `room` (room_id, name, area, level, area_type)
- [ ] New relationship tables (SurrealDB RELATION type):
  - `school_has_building` (FROM school TO building)
  - `building_has_room` (FROM building TO room)
  - `room_has_acm` (FROM room TO acm_record)
  - `extracted_from` (FROM acm_record TO source, with page_number, confidence)
  - `has_risk_level` (FROM acm_record TO risk_level, optional)
- [ ] Migration script to create tables and backfill from existing acm_record data
- [ ] `acm_record` retains embedded fields for backward compatibility
- [ ] Graph traversal queries work: `school->school_has_building->building->building_has_room->room->room_has_acm->acm_record`
- [ ] Pydantic models for all new entities

**Technical Notes:**
- Migration: `migrations/XX.surrealql` (new)
- Domain models: `open_notebook/domain/graph_entities.py` (new)
- Backfill script: Extract unique schools/buildings/rooms from existing acm_records
- Keep acm_record embedded fields for direct queries (performance)
- Graph traversal for relationship visualization only

#### E13-S2: Knowledge Graph API & Data Service

**As a** frontend developer
**I want** API endpoints that return graph-structured data for visualization
**So that** React Flow can render entity relationship diagrams

**Acceptance Criteria:**
- [ ] API endpoints:
  - `GET /api/graph/source/{source_id}` - Full graph for a source document
  - `GET /api/graph/school/{school_id}` - School-centric graph
  - `GET /api/graph/building/{building_id}` - Building-centric graph
  - `GET /api/graph/stats/{source_id}` - Graph statistics (node/edge counts)
- [ ] Response format: React Flow compatible nodes and edges
  ```json
  {
    "nodes": [
      {"id": "school:1", "type": "school", "data": {"label": "Cabramatta West PS", "code": "3980"}, "position": {"x": 0, "y": 0}},
      {"id": "building:b00a", "type": "building", "data": {"label": "B00A - Admin", "risk_summary": {"high": 2, "medium": 5}}}
    ],
    "edges": [
      {"id": "e1", "source": "school:1", "target": "building:b00a", "type": "school_has_building"}
    ]
  }
  ```
- [ ] Auto-layout calculation (hierarchical top-down)
- [ ] Risk summary aggregation per node (count of high/medium/low items)
- [ ] Filter options: by risk level, by building, by ACM status

**Technical Notes:**
- Location: `api/routers/graph.py` (new)
- Service: `api/graph_service.py` (new)
- Use SurrealDB graph traversal for data fetching
- Auto-layout: dagre algorithm (compatible with React Flow)

#### E13-S3: React Flow Knowledge Graph Visualization

**As a** user
**I want** an interactive knowledge graph view showing entity relationships for each PDF
**So that** I can visually understand the document structure and identify risk areas

**Acceptance Criteria:**
- [ ] Knowledge Graph page/tab accessible from source detail view
- [ ] React Flow canvas rendering:
  - School node (top level)
  - Building nodes (connected to school)
  - Room nodes (connected to buildings)
  - ACM item nodes (connected to rooms, color-coded by risk)
- [ ] Custom node components:
  - School node: name, code, address
  - Building node: name, year, construction, risk summary badge
  - Room node: name, area, ACM count
  - ACM node: product, risk color (red/yellow/green), friability icon
- [ ] Interactive features:
  - Click node to see details panel
  - Zoom and pan
  - Expand/collapse building or room groups
  - Filter by risk level (show only high-risk paths)
  - Minimap for navigation
- [ ] Layout options: Hierarchical (default), Force-directed
- [ ] Export graph as PNG/SVG
- [ ] Toggle between graph view and spreadsheet view

**Technical Notes:**
- Location: `frontend/src/components/acm/KnowledgeGraph.tsx` (new)
- Dependencies: `@xyflow/react` (React Flow v12+), `dagre` (layout)
- Custom nodes: `frontend/src/components/acm/graph-nodes/` (new directory)
- Integration: Tab in source detail page alongside spreadsheet
- Use React Query for data fetching from graph API
- Performance: Virtual rendering for large graphs (500+ nodes)

---

## 5. PRD Impact Summary

### New Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-111 | System shall extract document structure and TOC with page ranges before ACM extraction | P0 |
| FR-112 | System shall compile complete building inventory with page locations before per-building extraction | P0 |
| FR-113 | System shall tag each page with section classification and confidence score | P1 |
| FR-114 | System shall extract comprehensive document metadata (address, postcode, consultant, dates, etc.) | P0 |
| FR-115 | System shall support processing group optimization based on building complexity | P1 |
| FR-313 | System shall provide settings UI for configuring extraction methods and preferences | P1 |
| FR-314 | System shall provide settings UI for configuring AI models per extraction stage | P1 |
| FR-315 | System shall provide settings UI for managing parser configurations | P1 |
| FR-316 | System shall visualize document entity relationships as an interactive knowledge graph | P1 |
| FR-317 | System shall store document entities (school, building, room) as separate graph entities in SurrealDB | P1 |

---

## 6. Architecture Impact Summary

### New Pipeline Stages

```
STAGE -1: STRUCTURE ANALYSIS (NEW)
┌────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────┐ │
│ │ TOC Extraction   │──▶│ Building         │──▶│ Page-Level         │ │
│ │ & Structure      │   │ Inventory        │   │ Section Tagging    │ │
│ │ (E1-S16)         │   │ (E1-S17)         │   │ (E1-S18)           │ │
│ └──────────────────┘   └──────────────────┘   └────────────────────┘ │
│                                                        │             │
│ ┌──────────────────┐                                   │             │
│ │ Metadata         │◀──────────────────────────────────┘             │
│ │ Extraction       │                                                 │
│ │ (E1-S19)         │                                                 │
│ └──────────────────┘                                                 │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STAGE 0: PREFLIGHT (existing) → STAGE 0.5: AGENTIC ORCHESTRATOR → ...
```

### New Database Tables

```sql
-- Graph Entity Tables
DEFINE TABLE school SCHEMAFULL;
DEFINE TABLE building SCHEMAFULL;
DEFINE TABLE room SCHEMAFULL;

-- Graph Relationship Tables
DEFINE TABLE school_has_building TYPE RELATION FROM school TO building;
DEFINE TABLE building_has_room TYPE RELATION FROM building TO room;
DEFINE TABLE room_has_acm TYPE RELATION FROM room TO acm_record;
DEFINE TABLE extracted_from TYPE RELATION FROM acm_record TO source;

-- Settings Tables
DEFINE TABLE extraction_settings SCHEMAFULL;
DEFINE TABLE processing_settings SCHEMAFULL;
DEFINE TABLE parser_config SCHEMAFULL;
```

### New Frontend Routes

```
/settings/extraction    → E12-S1: Extraction Method Settings
/settings/models        → E12-S2: AI Model Configuration
/settings/processing    → E12-S3: Processing Options
/settings/parsers       → E12-S4: Parser Management
/sources/[id]/graph     → E13-S3: Knowledge Graph View (tab)
```

---

## 7. Story Dependencies

```
# Document Intelligence Pipeline (NEW)
E1-S3 (Pipeline, done) → E1-S16 (TOC/Structure)
E1-S16 (Structure) → E1-S17 (Building Inventory)
E1-S17 (Inventory) → E1-S18 (Page Tagging)
E1-S16 (Structure) → E1-S19 (Metadata Enhancement)

# Settings & Configuration (NEW)
E1-S16/17/18/19 (Pipeline features) → E12-S1 (Settings UI - to configure them)
E12-S1 (Extraction Settings) → E12-S2 (Model Config)
E12-S1 (Extraction Settings) → E12-S3 (Processing Config)
E1-S11 (Parser Framework) → E12-S4 (Parser Config UI)

# Knowledge Graph (NEW)
E1-S4 (API, done) → E13-S1 (Graph Schema)
E13-S1 (Schema) → E13-S2 (Graph API)
E13-S2 (API) → E13-S3 (React Flow UI)
```

---

## 8. Implementation Handoff

### Change Scope Classification
**MODERATE** - New stories and new epics, but no rework of existing completed work

### Immediate Actions

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Apply CP#6-CP#11 to PRD, Architecture, Epics documents | SM | P0 |
| 2 | Add new stories to sprint-status.yaml | SM | P0 |
| 3 | Draft tech-specs for E1-S16 through E1-S19 | SM/Architect | P0 |
| 4 | Draft tech-specs for E12 stories | SM/Architect | P1 |
| 5 | Draft tech-specs for E13 stories | SM/Architect | P1 |
| 6 | Install React Flow dependency | Dev | When E13 starts |

### New Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| @xyflow/react | ^12.x | React Flow knowledge graph visualization |
| dagre | ^0.8.x | Automatic graph layout algorithm |

### Success Criteria

- [ ] Document structure extraction works on Prensa and Greencap PDFs
- [ ] Building inventory compiled before per-building extraction
- [ ] Document metadata auto-populates site config fields
- [ ] Settings UI allows configuration without code changes
- [ ] Knowledge graph renders entity relationships for uploaded PDF
- [ ] All existing tests continue passing (zero regressions)

---

## 9. Approval

**Status:** ✅ APPROVED (2026-02-10)
**Approved by:** Demi

### Change Proposals - APPROVED

| CP# | Description | Priority | Status |
|-----|-------------|----------|--------|
| CP#6 | E1-S16: Document Structure & TOC Extraction | P0 | ✅ APPROVED |
| CP#7 | E1-S17: Building Inventory Compilation | P0 | ✅ APPROVED |
| CP#8 | E1-S18: Page-Level Section Tagging | P1 | ✅ APPROVED |
| CP#9 | E1-S19: Document Metadata Extraction Enhancement | P0 | ✅ APPROVED |
| CP#10 | E12: Extraction Settings & Configuration UI (4 stories) | P1 | ✅ APPROVED |
| CP#11 | E13: Knowledge Graph Visualization (3 stories) | P1 | ✅ APPROVED |

**Rationale for Approval:** Stories already implemented and tracked in sprint-status.yaml. Retrospective approval aligns documentation with actual project state.

---

*Generated by Course Correction Workflow - BMad Method*
*Date: 2026-02-07*
