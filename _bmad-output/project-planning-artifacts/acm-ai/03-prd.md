# Product Requirements Document (PRD) - ACM-AI

> **Product:** ACM-AI v1.0
> **Date:** 2025-12-07 (Updated: 2026-02-23)
> **Status:** v1.6 - Updated for E20 (Marketing-App Cross-Site Navigation & Domain Cutover)
> **Author:** John (Product Manager)
> **Change Log:** 2026-02-23 - v1.6: E20 Cross-Site Navigation and Domain Cutover (marketing as primary entrypoint, app on demo subdomain, bidirectional navigation links, env-driven host contract); 2026-02-22 - v1.5: E17 Live Extraction Intelligence (AG-UI extraction relay, A2A agent card, incremental record streaming, reasoning/tool observability, 6 new models); 2026-02-20 - v1.4: SCP-20260220 (Extraction Monitor + UX Enhancement, schema fields, table additions, MinerU primary); 2026-02-08 - v1.3 UX Audit &amp; Enterprise Readiness; Course correction: single generic configurable parser

---

## 1. Introduction

### 1.1 Purpose
This PRD defines the requirements for transforming Open Notebook into ACM-AI, a specialized platform for processing Asbestos Containing Material (ACM) compliance documents with intelligent extraction, spreadsheet visualization, and AI-powered querying.

### 1.2 Background
See [Product Brief](./02-product-brief.md) for business context and [System Analysis](./01-system-analysis.md) for technical foundation.

### 1.3 Scope
This document covers MVP requirements. Future enhancements are noted but not detailed.

### 1.4 Document Formats Supported
| Format | Description | Status |
|--------|-------------|--------|
| Victorian BAR | Building Asbestos Register (43-47 columns) | **Primary** |
| NSW SAMP | School Asbestos Management Plan | Supported |
| Prensa PDF | Asbestos assessment format (Prensa Pty Ltd) | Supported |
| Greencap PDF | Asbestos assessment format (Greencap) | Supported |

> **Note:** Prensa and Greencap formats are not separate parser implementations. All consultant formats are handled by the single generic configurable parser (see Section 5.7) driven by `field_schema` configuration in SurrealDB. Format-specific differences are expressed as JSON configuration, not code.

---

## 2. Functional Requirements

### 2.1 Document Processing (FR-100 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-101 | System shall accept PDF uploads up to 50MB | P0 | Upload succeeds for 50MB file within 30 seconds |
| FR-102 | System shall extract text and tables from PDFs using MinerU (primary) with Docling as fallback | P0 | MinerU processes PDF and returns structured table output; Docling used as fallback for text-based PDFs |
| FR-103 | System shall identify ACM Register tables within SAMP/BAR documents | P0 | Tables matching ACM schema are extracted with >90% accuracy |
| FR-104 | System shall parse hierarchical structure (Dept â†’ Agency â†’ Site â†’ Building â†’ Room â†’ ACM Item) | P0 | Hierarchy correctly represented in data model |
| FR-107 | System shall use configurable field definitions to parse any ACM PDF format via a single generic parser | P0 | Field schema config (register_row.schema.json, register_enums.json) drives parsing; single parser handles all consultant formats |
| FR-108 | System shall allow configuration of non-extractable fields | P0 | User can set Department, Building Type, etc. |
| FR-109 | System shall analyze document structure before extraction | P0 | TOC/inventory in Stage -1 |
| FR-110 | System shall detect format and select parser dynamically | P0 | Preflight identifies consultant |
| FR-111 | System shall route sections to optimal tool via orchestrator | P0 | MinerU/Docling per content type |
| FR-112 | System shall perform corrective re-extraction on failure | P1 | Max 3 LLM refinement attempts |
| FR-105 | System shall store page numbers for each extracted data row | P0 | Every ACM record has associated page_number |
| FR-106 | System shall handle multi-page tables | P1 | Tables spanning pages are merged correctly |

### 2.2 Data Model (FR-200 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-201 | System shall store ACM records with expanded Victorian BAR schema (~50 fields) | P0 | All BAR fields populated correctly |
| FR-202 | System shall link ACM records to source document | P0 | source_id foreign key maintained |
| FR-203 | System shall support vector embeddings for ACM records | P1 | Semantic search returns relevant records |
| FR-204 | System shall track extraction metadata (timestamp, confidence) | P1 | Metadata stored and accessible |
| FR-205 | System shall store organization hierarchy (Department, Agency, Sub Agency) | P0 | Victorian Government structure supported |
| FR-206 | System shall store location metadata (Address, Suburb, Postcode) | P0 | Full address information available |
| FR-207 | System shall store ACM classification (Product Group, Product Type) | P0 | BAR classification categories used |
| FR-208 | System shall store removal tracking data | P1 | Removal dates, quantities, certificates tracked |

### 2.3 Spreadsheet View (FR-300 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-301 | System shall display ACM data in AG Grid component | P0 | AG Grid renders with all columns |
| FR-302 | System shall support column sorting (ascending/descending) | P0 | Click column header sorts data |
| FR-303 | System shall support column filtering | P0 | Filter dropdowns work for enum columns |
| FR-304 | System shall support text search within grid | P0 | Search box filters visible rows |
| FR-305 | System shall support row grouping by Building/Room | P0 | Collapsible groups in grid |
| FR-306 | System shall highlight rows by risk status (color coding) | P1 | Low=green, Medium=yellow, High=red |
| FR-307 | System shall support column pinning | P1 | Building/Room columns can be pinned left |
| FR-308 | System shall support CSV export with all BAR columns | P0 | Download exports all 47 BAR columns |
| FR-309 | System shall support Excel BAR export | **P0** | Download as BAR-compliant .xlsx |
| FR-310 | System shall support BAR template configuration | P1 | User can upload/select BAR template |
| FR-311 | System shall support column visibility management | P1 | Show/hide columns, save presets |
| FR-312 | System shall support field mapping configuration | P1 | Map ACM-AI fields to BAR columns |

### 2.4 Citations and Provenance (FR-400 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-401 | System shall make each cell clickable | P0 | Cell click triggers event |
| FR-402 | System shall display PDF viewer showing source page on cell click | P0 | PDF opens to correct page |
| FR-403 | System shall highlight relevant region in PDF if bounding box available | P2 | Visual highlight on PDF page |
| FR-404 | Chat citations shall include cell-level references | P0 | Chat can cite specific rows/cells |
| FR-405 | Citation format: `[acm:record_id:field_name]` | P0 | Parser handles new citation type |

### 2.5 Chat Integration (FR-500 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-501 | Chat shall include ACM spreadsheet data in context | P0 | AI can answer "What's in Building X?" |
| FR-502 | Chat shall cite specific ACM records in responses | P0 | Response includes clickable citations |
| FR-503 | Chat shall understand ACM domain terminology | P1 | Correctly interprets "friable", "ACM", etc. |
| FR-504 | Chat shall answer questions about policy sections | P0 | Can explain SAMP procedures |
| FR-505 | Chat context selector shall include "ACM Data" option | P0 | User can toggle ACM context on/off |
| FR-506 | Chat shall use CopilotKit framework for AG-UI protocol | P0 | CopilotKit provider wraps application |
| FR-507 | Chat shall expose supervisor agent via AG-UI SSE endpoint | P0 | /api/agui/chat returns event stream |
| FR-508 | Chat shall render tool calls with custom result components | P0 | ACM queries shown in rich UI (tables, stats) |
| FR-509 | Chat shall support real-time streaming responses | P0 | Partial responses visible during generation |
| FR-510 | Chat shall handle ACM context toggle dynamically | P0 | Agent receives include_acm_context flag |

### 2.6 Rebranding (FR-600 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-601 | Application title shall be "ACM-AI" | P0 | Browser title, header show "ACM-AI" |
| FR-602 | Logo shall reflect ACM-AI branding | P1 | New logo in header and favicon |
| FR-603 | Color scheme shall be professional/compliance-focused | P1 | Updated theme colors |
| FR-604 | Landing page shall describe ACM-AI purpose | P1 | Hero section explains value prop |

### 2.7 UX &amp; Enterprise Readiness (FR-700 Series)

> **Added:** 2026-02-08 (UX Audit &amp; Enterprise Readiness Initiative - Lane B)
> **Spec References:** `docs/ux-audit.md`, `docs/design-system.md`, `docs/ui-ux-spec.md`,
> `docs/navigation-cleanup-spec.md`, `docs/state-loading-spec.md`, `docs/ag-ui-pipeline-spec.md`

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-701 | System shall use VAEA government branding (teal palette, logo, favicon) | P0 | All brand colors match VAEA specification |
| FR-702 | Navigation shall use WORKSPACE + CONFIGURE taxonomy | P0 | Sidebar redesigned per navigation-cleanup-spec |
| FR-703 | Brownfield features (Podcasts, Transformations, Notebooks) shall be hidden from navigation | P0 | Features inaccessible from nav but code preserved |
| FR-704 | All pages shall display skeleton loading placeholders during data fetch | P1 | Zero CLS, shimmer animation, aria-busy |
| FR-705 | Toast notifications shall provide promise-based feedback for long operations | P1 | Extraction/export shows loadingâ†’successâ†’error toasts |
| FR-706 | Application shall meet WCAG 2.1 AA accessibility standards | P1 | Color contrast, focus management, aria labels verified |
| FR-707 | Sources and Documents pages shall be merged into unified Documents view | P1 | Single /documents route with redirect from /sources |
| FR-708 | Application shall gracefully handle connection drops and session timeouts | P2 | Reconnection, offline indicator, timeout prompt |
| FR-709 | Keyboard navigation shall support all primary workflows | P2 | Command palette, grid nav, dialog shortcuts |
| FR-710 | Deep pages shall display breadcrumb navigation | P2 | Source detail, ACM register breadcrumbs |
| FR-711 | TypeScript types shall be auto-generated from Python Pydantic models | P2 | generate_types.py script, CI drift detection |

### 2.8 Extraction Monitor (FR-800 Series)

> **Added:** 2026-02-20 (SCP-20260220 â€” E15: Extraction Monitor & Live Logging UI)
> **Spec References:** `docs/sprint-artifacts/e15-s1-extraction-log-panel.md`, `docs/sprint-artifacts/e15-s2-extraction-monitor-page.md`

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-801 | System shall display extraction logs for any document in the Document Library (historical and live SSE) | P0 | Chevron expands inline `ExtractionProgressPanel` per document row; loads historical log for completed docs, live SSE for active docs |
| FR-802 | System shall provide a dedicated `/extraction-monitor` page with Active and History tabs, status filtering, and retry capability | P0 | Page accessible from sidebar CONFIGURE section; Active tab auto-refreshes 3s; History tab paginated with status/date filters; Retry button for failed/partial |

### 2.9 UX Enhancement (FR-900 Series)

> **Added:** 2026-02-20 (SCP-20260220 â€” E16: UX Enhancement Sprint + E9-S3)
> **Spec References:** `docs/sprint-artifacts/e16-s1-dashboard-home.md`, `docs/sprint-artifacts/e16-s2-record-detail-panel.md`, `docs/sprint-artifacts/e16-s3-empty-states.md`

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-901 | System shall display a statistics dashboard home page with ACM metrics (total records, buildings, risk breakdown) and charts | P1 | Dashboard at `/` shows 4 summary cards, risk donut chart, top 10 buildings bar chart, and recent extractions list; all data from `/api/acm/stats` |
| FR-902 | System shall provide a slide-out record detail panel showing all 47 ACM fields on row click | P0 | 380px right drawer slides in on grid row click; organises fields into 8 labeled sections; keyboard navigation (â†â†’); edit mode with save/cancel |
| FR-903 | System shall display empty state screens with appropriate CTAs when no documents or records exist | P1 | Empty states on Documents, ACM Register, Chat, and Extraction Monitor pages; dismissable onboarding hints on first visit |
| FR-904 | System shall support bulk document operations (select multiple â†’ delete/re-extract/export) | P1 | Checkbox selection in document list; bulk action toolbar appears; bulk delete, bulk re-extract, bulk CSV export |

### 2.10 Live Extraction Intelligence (FR-1000 Series)

> **Added:** 2026-02-22 (E17: Live Extraction Intelligence â€” AG-UI + A2A + Real-time Observability)
> **Spec References:** `docs/sprint-artifacts/e17-s1-agui-extraction-endpoint.md` through `e17-s6-new-openrouter-models.md`

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1001 | System shall emit AG-UI protocol events during extraction via SurrealDB relay (AGUIEventEmitter â†’ agui_events table â†’ SSE endpoint) | P0 | `GET /api/agui/extraction/{command_id}/stream` returns AG-UI compliant SSE; events include RunStarted, StepStarted/Finished, StateDelta, ToolCallStart/End, RunFinished/RunError |
| FR-1002 | System shall stream extracted records incrementally to the AG Grid during extraction via AG-UI StateDelta events | P0 | Records appear in AG Grid within 2s of each chunk; preview rows visually distinguished (italic/pulsing border); replaced by final records on completion |
| FR-1003 | System shall display reasoning tokens from thinking models (DeepSeek R1, Claude extended thinking) in a collapsible panel | P1 | "Agent Thinking" panel in ExtractionProgressPanel; streams tokens character-by-character; hidden by default; non-reasoning models: panel doesn't appear |
| FR-1004 | System shall display extraction tool call operations in a live feed showing step names, arguments, results, and durations | P1 | Each graph node transition shows as a tool call entry; in-flight calls show spinner; completed calls show check + result summary + duration |
| FR-1005 | System shall expose an A2A (Agent-to-Agent) agent card at `/.well-known/agent.json` with task lifecycle endpoints | P1 | `GET /.well-known/agent.json` returns valid A2A agent card; `POST /api/a2a/tasks` accepts extraction task; `GET /api/a2a/tasks/{id}` returns status |
| FR-1006 | System shall support 6 additional frontier AI models via OpenRouter: MiniMax M2.1, Kimi K2.5, DeepSeek V3.2, Claude Sonnet 4.6, GPT 5.2, Gemini 2.5 Pro | P1 | Models auto-provisioned on startup when `OPENROUTER_API_KEY` set; correct context windows and capability flags (structured output, tool calling) |
### 2.11 Cross-Site Navigation & Domain Topology (FR-1100 Series)

> **Added:** 2026-02-23 (E20: Marketing-App Linking & Vercel Domain Cutover)
> **Spec References:** `docs/sprint-artifacts/e20-s1-marketing-to-app-linking.md`, `docs/sprint-artifacts/e20-s2-app-to-marketing-navigation-cutover.md`

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1101 | System shall present the marketing site as the primary entrypoint for users | P0 | `vaea.coralshades.ai` serves marketing site content and canonical docs links |
| FR-1102 | Marketing site shall provide clear CTAs to open the application workspace | P0 | Header, hero CTA, and footer include `Open App` link to configured app host |
| FR-1103 | Application workspace shall provide links back to landing and docs | P0 | App sidebar and command palette include links to landing and docs on marketing host |
| FR-1104 | Cross-site URLs shall be environment-configurable per deployment | P0 | `NEXT_PUBLIC_APP_URL` and `NEXT_PUBLIC_MARKETING_URL` are documented and used by UI navigation |

### 2.10 UX Loading States (FR-1000 Series)

> **Added:** 2026-02-26 (SCP-20260226 — Post-Audit Fix Sprint)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1001 | All page transitions shall show shimmer skeleton loading states | P1 | No blank screens during route navigation |
| FR-1002 | All action buttons shall show loading/disabled state during API calls | P1 | Buttons show spinner during processing |
| FR-1003 | Extraction progress shall be visible in real-time on job pages | P1 | SSE progress wired to jobs flow |
| FR-1004 | Jobs pages shall use consistent layout matching ACM Register design | P1 | Same card/grid/toolbar patterns |


### 3.1 Performance (NFR-100 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-101 | Unified pipeline shall preserve Broadmeadows benchmark accuracy | P0 | Broadmeadows extraction remains 31/31 on orchestrator-only path |
| NFR-102 | Unified pipeline shall maintain Alexander baseline and support E29 target uplift | P0 | Alexander remains >=36/43 during unification and reaches >=40/43 after decomposition stories |
| NFR-103 | Measure phase shall run an automated benchmark harness before and after major pipeline changes | P0 | At least 3 benchmark documents execute with stored ground truth and report recall/precision/field accuracy |
| NFR-104 | Regression policy shall block release on unapproved quality degradation | P0 | No benchmark drops more than 2% recall from approved baseline unless explicit waiver is recorded |
| NFR-105 | Extraction latency and token usage shall be tracked as release gates | P1 | Baseline and post-change reports include per-document latency and token usage deltas |
| NFR-106 | Spreadsheet shall render 1000+ rows without lag | P0 | Virtual scrolling enabled |

### 3.2 Privacy and Security (NFR-200 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-201 | All document processing shall occur locally | P0 | No external API calls for extraction |
| NFR-202 | Uploaded documents shall not be transmitted externally | P0 | Network traffic audit confirms |
| NFR-203 | LLM calls may use configured providers (local or cloud) | P0 | Respects user's model configuration |

### 3.3 Usability (NFR-300 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-301 | User shall be able to upload and view ACM data in <5 clicks | P0 | UX test confirms |
| NFR-302 | Spreadsheet controls shall be intuitive to Excel users | P1 | No training required for basic ops |
| NFR-303 | Error messages shall be clear and actionable | P1 | User knows what to do on error |

### 3.4 Compatibility (NFR-400 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-401 | System shall work on Chrome, Firefox, Edge (latest 2 versions) | P0 | Cross-browser testing passes |
| NFR-402 | System shall work on desktop (1024px+ width) | P0 | Responsive layout works |
| NFR-403 | Mobile support is out of scope for MVP | P0 | Documented limitation |

---

## 4. User Interface Requirements

### 4.1 Layout Changes

Current Open Notebook layout (3-column):
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Sources   â”‚    Notes    â”‚    Chat     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

ACM-AI layout (configurable):
```
Mode 1: Spreadsheet Focus
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Sources   â”‚      ACM Spreadsheet      â”‚
â”‚             â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚             â”‚         Chat              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Mode 2: Document Focus (existing behavior)
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Sources   â”‚    Notes    â”‚    Chat     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 4.2 New Components

| Component | Description | Location |
|-----------|-------------|----------|
| `ACMSpreadsheet` | AG Grid wrapper for ACM data | Main panel (new) |
| `ACMCellViewer` | Modal showing PDF page for selected cell | Overlay |
| `ACMContextToggle` | Toggle to include ACM data in chat | Chat panel header |
| `ACMExportButton` | Export dropdown (CSV, Excel) | Spreadsheet toolbar |

### 4.3 AG Grid Column Configuration (Victorian BAR Format)

Columns are organized into logical groups for visibility management:

```typescript
const acmColumnGroups = {
  // Group 1: Organization Hierarchy
  organization: [
    { field: 'department', headerName: 'Department', width: 100 },
    { field: 'agency', headerName: 'Agency', width: 150 },
    { field: 'sub_agency', headerName: 'Sub Agency', width: 150 },
    { field: 'site_name', headerName: 'Site Name', width: 150 },
  ],

  // Group 2: Building Information
  building: [
    { field: 'building_name', headerName: 'Building Name', width: 150, rowGroup: true },
    { field: 'building_type', headerName: 'Building Type', width: 120 },
    { field: 'building_address', headerName: 'Address', width: 180 },
    { field: 'suburb', headerName: 'Suburb', width: 120 },
    { field: 'postcode', headerName: 'Postcode', width: 80 },
    { field: 'owned_or_leased', headerName: 'Owned/Leased', width: 100 },
    { field: 'building_unique_id', headerName: 'Building ID', width: 100 },
    { field: 'frequency_of_use', headerName: 'Frequency', width: 100 },
    { field: 'public_access', headerName: 'Public Access', width: 100 },
    { field: 'date_of_inspection', headerName: 'Inspection Date', width: 120 },
    { field: 'building_year', headerName: 'Year Built', width: 80 },
    { field: 'building_size_m2', headerName: 'Size (mÂ²)', width: 80 },
    { field: 'number_of_levels', headerName: 'Levels', width: 70 },
    { field: 'building_construction', headerName: 'Construction', width: 120 },
    { field: 'roof_type', headerName: 'Roof Type', width: 100 },
  ],

  // Group 3: Location
  location: [
    { field: 'area_type', headerName: 'Int/Ext', width: 80 },
    { field: 'level', headerName: 'Level', width: 80 },
    { field: 'room_name', headerName: 'Room/Area', width: 150, rowGroup: true },
    { field: 'location', headerName: 'Location in Room', width: 150 },
  ],

  // Group 4: ACM Details
  acmDetails: [
    { field: 'product', headerName: 'Item/ACM Name', width: 150 },
    { field: 'friable', headerName: 'Friability', width: 100 },
    { field: 'acm_product_group', headerName: 'Product Group', width: 120 },
    { field: 'acm_product_type', headerName: 'Product Type', width: 120 },
    { field: 'nata_sample_number', headerName: 'Sample No.', width: 120 },
    { field: 'sample_result', headerName: 'Sample Result', width: 100 },
    { field: 'hygiene_company', headerName: 'Hygiene Co.', width: 150 },
  ],

  // Group 5: Assessment
  assessment: [
    { field: 'material_condition', headerName: 'Condition', width: 100 },
    { field: 'disturbance_potential', headerName: 'Disturb. Potential', width: 120 },
    { field: 'extent', headerName: 'Quantity', width: 100 },
    { field: 'risk_status', headerName: 'Risk', width: 80, cellRenderer: 'riskBadge' },
  ],

  // Group 6: Labeling & Documentation
  documentation: [
    { field: 'labelled', headerName: 'Labelled', width: 80 },
    { field: 'label_details', headerName: 'Label Details', width: 150 },
    { field: 'hygienist_recommendations', headerName: 'Recommendations', width: 200 },
    { field: 'additional_comments', headerName: 'Comments', width: 200 },
    { field: 'photo_reference', headerName: 'Photo Ref', width: 100 },
  ],

  // Group 7: Removal Tracking
  removal: [
    { field: 'psb_acm_id', headerName: 'PSB ACM ID', width: 100 },
    { field: 'assumed_removed', headerName: 'Removed?', width: 80 },
    { field: 'date_of_removal', headerName: 'Removal Date', width: 120 },
    { field: 'quantity_removed', headerName: 'Qty Removed', width: 100 },
    { field: 'removal_notification_no', headerName: 'Removal Notif.', width: 120 },
    { field: 'epa_certificate_no', headerName: 'EPA Cert.', width: 120 },
    { field: 'removal_comments', headerName: 'Removal Comments', width: 200 },
  ],
};

// Default visible columns (Essential view)
const defaultVisibleColumns = [
  'building_name', 'room_name', 'product', 'friable',
  'material_condition', 'risk_status', 'sample_result'
];
```

---

## 5. Data Requirements

### 5.1 ACM Record Schema (Victorian BAR Format - Expanded)

> **Updated 2026-02-05:** Schema aligned with official BAR template (47 columns A-AU).
> See `docs/reference/bar-schema.md` for authoritative field definitions.

```sql
-- SurrealDB schema - Victorian BAR Format
DEFINE TABLE acm_record SCHEMAFULL;

-- Core identification
DEFINE FIELD source_id ON acm_record TYPE record<source>;

-- Organization Hierarchy (NEW - Victorian Government structure)
DEFINE FIELD department ON acm_record TYPE option<string>;  -- DJCS, DHHS, DET, DOT, DJPR, etc.
DEFINE FIELD agency ON acm_record TYPE option<string>;  -- Victoria Police, Alexandra District Health
DEFINE FIELD sub_agency ON acm_record TYPE option<string>;  -- Specific station/facility
DEFINE FIELD site_name ON acm_record TYPE option<string>;  -- Site name if applicable

-- Building Information (Expanded)
DEFINE FIELD building_id ON acm_record TYPE string;
DEFINE FIELD building_name ON acm_record TYPE string;
DEFINE FIELD building_type ON acm_record TYPE option<string>;  -- Police Station, Hospital, School
DEFINE FIELD building_address ON acm_record TYPE option<string>;  -- Full street address
DEFINE FIELD suburb ON acm_record TYPE option<string>;
DEFINE FIELD postcode ON acm_record TYPE option<string>;
DEFINE FIELD owned_or_leased ON acm_record TYPE option<string>;  -- Owned, Leased
DEFINE FIELD building_unique_id ON acm_record TYPE option<string>;  -- Government assigned ID
DEFINE FIELD frequency_of_use ON acm_record TYPE option<string>;  -- Every day, Weekly, etc.
DEFINE FIELD public_access ON acm_record TYPE option<string>;  -- YES, NO
DEFINE FIELD date_of_inspection ON acm_record TYPE option<datetime>;
DEFINE FIELD building_year ON acm_record TYPE option<int>;  -- Estimated year built
DEFINE FIELD building_size_m2 ON acm_record TYPE option<float>;
DEFINE FIELD number_of_levels ON acm_record TYPE option<int>;
DEFINE FIELD building_construction ON acm_record TYPE option<string>;  -- Brick, Metal, etc.
DEFINE FIELD roof_type ON acm_record TYPE option<string>;  -- Metal, Tile, etc.

-- Location within building
DEFINE FIELD area_type ON acm_record TYPE string;  -- Internal, External
DEFINE FIELD level ON acm_record TYPE option<string>;  -- Ground, First, Basement, etc.
DEFINE FIELD room_id ON acm_record TYPE option<string>;
DEFINE FIELD room_name ON acm_record TYPE option<string>;  -- Room or Area
DEFINE FIELD room_area ON acm_record TYPE option<float>;
DEFINE FIELD location ON acm_record TYPE string;  -- Location in room

-- ACM Item Details (Expanded)
DEFINE FIELD product ON acm_record TYPE string;  -- Specific Item/ACM Name
DEFINE FIELD material_description ON acm_record TYPE option<string>;
DEFINE FIELD friable ON acm_record TYPE option<string>;  -- Friable, Non-friable
DEFINE FIELD acm_product_group ON acm_record TYPE option<string>;  -- Cement products, Vinyl products, etc.
DEFINE FIELD acm_product_type ON acm_record TYPE option<string>;  -- Flat Sheeting, Vinyl sheet, etc.

-- Sample & Testing (BAR columns AD-AF)
DEFINE FIELD nata_sample_number ON acm_record TYPE option<string>;  -- BAR column AD
DEFINE FIELD sample_result ON acm_record TYPE option<string>;  -- Positive, Assumed Positive, Negative, Assumed Negative
DEFINE FIELD hygiene_company ON acm_record TYPE option<string>;  -- Identifying Hygiene or Consulting Company

-- Assessment (BAR columns AG-AH)
DEFINE FIELD material_condition ON acm_record TYPE option<string>;  -- Poor, Fair, Good, Unknown, N/A (negative), N/A (assumed negative)
DEFINE FIELD disturbance_potential ON acm_record TYPE option<string>;  -- High, Moderate, Low, Unknown, N/A (negative), N/A (assumed negative)
DEFINE FIELD extent ON acm_record TYPE option<string>;  -- Quantity (BAR column AI)
DEFINE FIELD risk_status ON acm_record TYPE option<string>;  -- Derived field (not in BAR export)

-- Labeling & Documentation
DEFINE FIELD labelled ON acm_record TYPE option<string>;  -- YES, NO
DEFINE FIELD label_details ON acm_record TYPE option<string>;
DEFINE FIELD hygienist_recommendations ON acm_record TYPE option<string>;
DEFINE FIELD additional_comments ON acm_record TYPE option<string>;
DEFINE FIELD photo_reference ON acm_record TYPE option<string>;

-- Removal Tracking (NEW - for BAR compliance)
DEFINE FIELD psb_acm_id ON acm_record TYPE option<string>;  -- PSB Supplied ACM ID
DEFINE FIELD assumed_removed ON acm_record TYPE option<string>;  -- YES, NO
DEFINE FIELD date_of_removal ON acm_record TYPE option<datetime>;
DEFINE FIELD quantity_removed ON acm_record TYPE option<string>;
DEFINE FIELD removal_notification_no ON acm_record TYPE option<string>;
DEFINE FIELD epa_certificate_no ON acm_record TYPE option<string>;
DEFINE FIELD removal_comments ON acm_record TYPE option<string>;

-- Legacy fields (NSW SAMP compatibility)
DEFINE FIELD school_name ON acm_record TYPE option<string>;
DEFINE FIELD school_code ON acm_record TYPE option<string>;
DEFINE FIELD result ON acm_record TYPE option<string>;  -- Legacy result field

-- BAR Compliance fields (Added: PR #30 / E1-S12 / E1-S14)
DEFINE FIELD quantity ON acm_record TYPE option<string>;  -- Sample quantity (e.g. '10 mÂ²', '5 linear meters')
DEFINE FIELD acm_labelled ON acm_record TYPE option<bool>;  -- Boolean: whether ACM is labelled on-site
DEFINE FIELD acm_label_details ON acm_record TYPE option<string>;  -- Label details if labelled
DEFINE FIELD identifying_company ON acm_record TYPE option<string>;  -- Hygiene/consulting company (supplements hygiene_company)
DEFINE FIELD floor_level ON acm_record TYPE option<string>;  -- Floor level (e.g. 'Ground', 'Level 1', 'Roof')
DEFINE FIELD normalized_action ON acm_record TYPE option<string>;  -- Normalised consultant action wording (E1-S12, migration 15)
DEFINE FIELD enriched_text ON acm_record TYPE option<string>;  -- Contextual embedding enrichment text (E1-S14, migration 16)

-- Parent Document Retrieval (E11-S1, migration 18)
DEFINE FIELD parent_table_id ON acm_record TYPE option<record<acm_table_section>>;  -- Link to raw table section for provenance

-- Metadata
DEFINE FIELD page_number ON acm_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON acm_record TYPE option<float>;
DEFINE FIELD created_at ON acm_record TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON acm_record TYPE datetime DEFAULT time::now();

-- Indexes for query performance
DEFINE INDEX acm_source ON acm_record FIELDS source_id;
DEFINE INDEX acm_building ON acm_record FIELDS building_id;
DEFINE INDEX acm_risk ON acm_record FIELDS risk_status;
DEFINE INDEX acm_department ON acm_record FIELDS department;
DEFINE INDEX acm_agency ON acm_record FIELDS agency;
DEFINE INDEX acm_suburb ON acm_record FIELDS suburb;
DEFINE INDEX acm_sample_result ON acm_record FIELDS sample_result;
```

### 5.1.1 Site Configuration Schema (NEW)

For fields that cannot be extracted from PDFs, site configuration is stored separately:

```sql
DEFINE TABLE site_config SCHEMAFULL;
DEFINE FIELD source_id ON site_config TYPE record<source>;
DEFINE FIELD department ON site_config TYPE option<string>;
DEFINE FIELD agency ON site_config TYPE option<string>;
DEFINE FIELD building_type ON site_config TYPE option<string>;
DEFINE FIELD owned_or_leased ON site_config TYPE option<string>;
DEFINE FIELD frequency_of_use ON site_config TYPE option<string>;
DEFINE FIELD public_access ON site_config TYPE option<string>;
DEFINE FIELD building_unique_id ON site_config TYPE option<string>;
DEFINE FIELD created_at ON site_config TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON site_config TYPE datetime DEFAULT time::now();

DEFINE INDEX config_source ON site_config FIELDS source_id;
```

### 5.1.2 Field Schema Table (E1-S11, migration 17)

Runtime field configuration store. Loaded from JSON config files at startup; drives the GenericParser, AG Grid columns, and BAR export.

```sql
DEFINE TABLE field_schema SCHEMAFULL;
DEFINE FIELD config_json ON TABLE field_schema TYPE string;  -- Serialized FieldSchemaConfig JSON
DEFINE FIELD version ON TABLE field_schema TYPE string;      -- Semantic version of config
DEFINE FIELD created ON TABLE field_schema TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON TABLE field_schema TYPE datetime DEFAULT time::now();
```

### 5.1.3 Parent Document Retrieval Table (E11-S1, migration 18)

Stores raw HTML/text table sections as parent documents for extracted ACM records, enabling provenance and citation.

```sql
DEFINE TABLE acm_table_section SCHEMAFULL;
DEFINE FIELD source_id ON acm_table_section TYPE record<source>;
DEFINE FIELD page_start ON acm_table_section TYPE int;
DEFINE FIELD page_end ON acm_table_section TYPE int;
DEFINE FIELD raw_html ON acm_table_section TYPE option<string>;  -- Original HTML from MinerU
DEFINE FIELD raw_text ON acm_table_section TYPE option<string>;  -- Plain text fallback
DEFINE FIELD building_name ON acm_table_section TYPE option<string>;
DEFINE FIELD table_type ON acm_table_section TYPE option<string>;
DEFINE FIELD created ON acm_table_section TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON acm_table_section TYPE option<datetime>;
```

### 5.1.4 Extraction Progress Table (migration 19)

Stores per-run pipeline state for SSE streaming and polling. Keyed by `command_id` (unique per extraction job).

```sql
DEFINE TABLE extraction_progress SCHEMAFULL;
DEFINE FIELD command_id ON extraction_progress TYPE string;   -- Job ID from surreal-commands
DEFINE FIELD run_id ON extraction_progress TYPE string;
DEFINE FIELD source_id ON extraction_progress TYPE string;
DEFINE FIELD status ON extraction_progress TYPE string;       -- "running", "completed", "failed"
DEFINE FIELD state_json ON extraction_progress TYPE string;   -- Serialized PipelineRunState JSON
DEFINE FIELD log_entries ON extraction_progress TYPE array DEFAULT [];
DEFINE FIELD log_entries.* ON extraction_progress TYPE string;
DEFINE FIELD updated_at ON extraction_progress TYPE datetime DEFAULT time::now();
DEFINE FIELD created_at ON extraction_progress TYPE datetime DEFAULT time::now();
DEFINE INDEX idx_extraction_progress_command ON extraction_progress FIELDS command_id UNIQUE;
```

### 5.2 API Endpoints (Expanded)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/acm/extract` | POST | Trigger ACM extraction for a source |
| `/api/acm/records` | GET | List ACM records (with filters for all 50 fields) |
| `/api/acm/records/{id}` | GET | Get single ACM record |
| `/api/acm/records/{id}` | PUT | Update ACM record (for site config fields) |
| `/api/acm/export/csv` | GET | Export records as CSV with all BAR columns |
| `/api/acm/export/excel` | GET | Export records as BAR-compliant Excel |
| `/api/acm/stats` | GET | Summary statistics for dashboard |
| `/api/acm/config` | GET | Get site configuration for a source |
| `/api/acm/config` | POST | Create/update site configuration |
| `/api/acm/templates` | GET | List available BAR templates |
| `/api/acm/templates/{id}` | GET | Get specific BAR template |
| `/api/acm/mappings` | GET | Get field mapping configuration |
| `/api/acm/mappings` | PUT | Update field mapping configuration |
| `/api/acm/classify` | POST | AI classification for Product Group/Type |
| `/api/acm/extraction-progress/{command_id}/stream` | GET | SSE stream â€” real-time pipeline events (text/event-stream) |
| `/api/acm/extraction-progress/{command_id}` | GET | REST polling fallback â€” current extraction state and log entries |
| `/api/acm/field-schema` | GET | Active field schema config for AG Grid dynamic column definitions |

### 5.3 BAR Export Format Specification (NEW)

The system shall export Excel files compliant with Victorian Government BAR format:

**Sheet Structure:**
- Main sheet: DATA ENTRY (all ACM records)
- Reference sheets (optional): Building Types, Product Types, Suburbs, etc.

**Column Order (47 columns):**
1. Department â†’ 2. Agency â†’ 3. Sub Agency â†’ 4. Site Name â†’ 5. Building Name
6. Building Type â†’ 7. Building Address â†’ 8. Suburb â†’ 9. Postcode â†’ 10. Owned or Leased
11. Building Unique ID â†’ 12. Frequency of use â†’ 13. Public Access? â†’ 14. Date of Inspection
15. Estimated Year Built â†’ 16. Est. Building Size (m2) â†’ 17. Number of Levels
18. Construction Type â†’ 19. Roof Type â†’ 20. Internal / External â†’ 21. Level
22. Room or Area â†’ 23. Location in Room â†’ 24. Specific Item/ACM Name
25. Friability of material â†’ 26. ACM Product Group â†’ 27. ACM Product Type
28. NATA Endorsed Sample number â†’ 29. Sample Result â†’ 30. Identifying Hygiene Company
31. Condition â†’ 32. Disturbance Potential â†’ 33. Quantity â†’ 34. Labelled
35. Label Details â†’ 36. Hygienist Recommendations â†’ 37. Additional Comments
38. PSB Supplied ACM ID â†’ 39. Assumed Removed? â†’ 40. Date of Removal
41. Quantity Removed â†’ 42. Asbestos Removal Notification No
43. EPA Waste Transport Certificate No â†’ 44. Removal Comments â†’ 45. Photo Reference Number

### 5.4 Extraction Pipeline Architecture

Epic 29 establishes a single-path extraction contract with benchmark-gated rollout.

**Authoritative flow (E29):**

```
tag_pages -> orchestrate_extraction (always)
          -> validate_records
          -> correct_records
          -> deduplicate_records
          -> recover_records
          -> save_records
```

**Key requirements:**
- All documents use the orchestrator path, including single-building and no-inventory inputs.
- When inventory is missing, the system creates a synthetic whole-document plan and continues in orchestrator.
- Docling table context injection is available to both single-building and multi-building documents.
- `parse_json_response()` must handle fenced JSON, preamble text, and truncation errors.

**Fallback contract:**
- No inventory: create synthetic whole-document extraction plan.
- No table context: continue with text-only extraction, non-fatal.
- LLM schema/format issues: parse JSON from raw response and validate with Pydantic.
- Validation failures: targeted correction retries (max 3), then deterministic error reporting.

**Decision gates (release controls):**
1. Baseline harness gate (>=3 benchmark docs, reproducible metrics).
2. Unified-path parity gate (Broadmeadows 31/31, Alexander baseline maintained).
3. Cleanup gate (legacy path removal only after no-regression confirmation).
4. Release readiness gate (benchmark + E2E pass + docs synchronized).

**Observability:** SSE + structured logs for stage transitions, benchmark telemetry, retries,
and correction outcomes.

### 5.5 Enum Definitions (NEW - 2026-02-05)

> Source: `docs/samplePDF/instructions-sample/register_enums.json`

| Enum | Values |
|------|--------|
| Sample Result | `Positive`, `Assumed Positive`, `Negative`, `Assumed Negative` |
| Condition | `Poor`, `Fair`, `Good`, `Unknown`, `N/A (negative)`, `N/A (assumed negative)` |
| Disturbance Potential | `High`, `Moderate`, `Low`, `Unknown`, `N/A (negative)`, `N/A (assumed negative)` |
| Friability | `Non-friable`, `Friable` |
| Internal/External | `Internal`, `External`, `External & Internal` |
| Owned or Leased | `Owned`, `Leased` |
| Yes/No | `YES`, `NO` |
| Frequency of Use | `Every day`, `Every day with intermittent breaks`, `Once every 3â€“5 days`, `Every 2â€“3 weeks`, `Once every 2â€“3 months`, `Annually or less frequently` |

**Business Rules:**
- If Sample Result is `Negative` or `Assumed Negative`:
  - Set Condition to `N/A (negative)` or `N/A (assumed negative)`
  - Set Disturbance Potential to `N/A (negative)` or `N/A (assumed negative)`
- Note: BAR uses `Moderate` not `Medium` for Disturbance Potential

### 5.6 ACM Product Taxonomy (NEW - 2026-02-05)

> See `docs/reference/product-taxonomy.md` for complete classification.

**Non-Friable Taxonomy (8 Groups):**
| Code | Product Group | Examples |
|------|---------------|----------|
| T1 | Cement products | Flat Sheeting, Corrugated Roof, Weatherboards |
| T2 | Bitumen products | Mastic, Bituminous Membrane, Malthoid |
| T3 | Vinyl products | Vinyl sheet, Vinyl Tiles, Hessian backed |
| T4 | Gasket, friction products | Flange Gaskets, Caulking, Mastic |
| T5 | Coatings | Paint, Textured Coating |
| T6 | Reinforced plastics/resins | Electrical Components, Toilet Cisterns |
| T7 | Other | Mortar, Grout, Plaster, Render |
| T8 | Insulation | Millboard, Lagging, Fire Door Core |

**Friable Taxonomy (6 Groups):**
| Code | Product Group | Examples |
|------|---------------|----------|
| T1 | Cement products (f) | Damaged/degraded cement products |
| T2 | Vinyl products (f) | Paper-backed vinyl |
| T3 | Insulation products (f) | AIB, Lagging, Sprayed Insulation, Vermiculite |
| T4 | Gasket products (f) | Rope Gasket, Braided Gasket |
| T5 | Textiles (f) | Fire blanket, Cloth, Gloves |
| T6 | Other (f) | Plaster/lath, Mortar |

**Classification Approach:**
1. Pattern-based rules for common ACM types (regex matching)
2. LLM fallback for ambiguous items (with confidence score)
3. User override capability for manual correction

### 5.7 Consultant Format Support (Updated 2026-02-08)

The system uses a **single generic configurable parser** driven by BAR field schema configuration, rather than per-consultant parser implementations.

**Configuration-Driven Parsing Pipeline:**
```
BAR Excel template â†’ JSON config files â†’ SurrealDB field_schema table â†’ runtime parser
```

**Schema Sources:**
| Config File | Purpose | Content |
|-------------|---------|---------|
| `register_row.schema.json` | Field definitions | 47 BAR fields with types, validation rules, and column mappings |
| `register_enums.json` | Picklist values | Controlled vocabulary for all enum fields (Sample Result, Condition, etc.) |

**Runtime Flow:**
1. Field definitions loaded from `field_schema` table in SurrealDB (seeded from JSON configs)
2. Generic parser uses field schema to map extracted columns to BAR fields
3. Enum validation applied from `register_enums.json` picklists
4. Same parser handles all consultant formats (Prensa, Greencap, or any other) without format-specific code

**Extensibility:**
- New fields added by updating `register_row.schema.json` and re-seeding the `field_schema` table
- New picklist values added by updating `register_enums.json`
- No per-consultant parser code required; column mapping is configuration, not code

---

## 6. Integration Points

### 6.1 Existing Systems to Modify

| System | Modification |
|--------|--------------|
| Source processing | Add ACM extraction step post-MinerU/Docling |
| Chat context builder | Include ACM records in context |
| Citation parser | Handle `[acm:...]` references |
| Frontend routing | Add ACM spreadsheet view |

### 6.2 New Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| ag-grid-react | ^31.x | Spreadsheet component |
| ag-grid-community | ^31.x | Core grid functionality |
| react-pdf | ^7.x | PDF viewer in modal |
| mineru | ^0.1.0 | Table extraction (MinerU) |
| docling | ^0.1.0 | Text/layout extraction |
| openpyxl | ^3.1.0 | Excel BAR export |

---

## 7. Testing Requirements

### 7.1 Test Data

**Benchmark harness (minimum set):**
- `Clutch_Broadmeadows Police Station Div 5 34511-039 V2_done.pdf` (Prensa, 19 pages)
- `Clucth_Alexander_District_Hospital_Asbestos_Risk_Assessment_2020-09-07.pdf` (ARA/Greencap-style, 34 pages)
- One additional consultant format benchmark (Greencap/Generic/edge-case), each with ground truth records

**Ground truth artifacts:**
- Per-benchmark `ground_truth.json` with expected record-level fields
- Per-benchmark `last_run.json` with latest benchmark metrics
- Validation reports in `docs/reviews/` for gate decisions

**Operational test corpus (non-gating):**
- `1124_AsbestosRegister.pdf` (NSW SAMP)
- `3980_AsbestosRegister.pdf`
- `4601_AsbestosRegister.pdf`

### 7.2 Test Scenarios

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| T-001 | Unified-path run on Broadmeadows | Orchestrator path used; 31/31 records |
| T-002 | Unified-path run on Alexander | All buildings produce records; >=36/43 baseline maintained |
| T-003 | JSON parser fence/preamble handling | Fenced and prefixed model outputs parse successfully |
| T-004 | Truncated JSON handling | Clear truncation error, not generic "No JSON object found" |
| T-005 | Synthetic plan fallback (no inventory) | Extraction continues via orchestrator whole-document plan |
| T-006 | Benchmark harness execution | >=3 benchmark docs produce recall/precision/field accuracy report |
| T-007 | Legacy cleanup gate validation | No regression after legacy path removal |
| T-008 | Export to BAR Excel | All BAR columns in configured order |
| T-009 | Per-building/ACM-type export | Correct grouping and schema-driven fields |
| T-010 | Spreadsheet filtering and column visibility | Filters and toggles behave without regression |
| T-011 | PDF citation navigation from spreadsheet | Correct page open and cell context |
| T-012 | Upload non-ACM PDF | Graceful error path or empty ACM view |

---

## 8. Rollout Plan

### Phase 1: Foundation
- AG Grid integration
- ACM data model and API
- Basic extraction pipeline

### Phase 2: Core Features
- Cell citations
- PDF viewer integration
- Chat context enhancement

### Phase 3: Polish
- Rebranding
- Export functionality
- Error handling improvements

### Phase 4: Validation
- User testing with real SAMPs
- Performance optimization
- Documentation

---

## 9. Open Items

| Item | Owner | Due |
|------|-------|-----|
| Validate extraction accuracy on all sample PDFs | Dev team | Phase 1 |
| Design review for rebranding | User | Phase 3 |

---

## 10. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| ACM | Asbestos Containing Material |
| BAR | Building Asbestos Register (Victorian Government format) |
| SAMP | School Asbestos Management Plan (NSW format) |
| Friable | ACM that can be crumbled by hand pressure |
| Non-Friable | ACM with fibers bound in matrix |
| DJCS | Department of Justice and Community Safety (Victoria) |
| DHHS | Department of Health and Human Services (Victoria) |
| DET | Department of Education and Training (Victoria) |
| NATA | National Association of Testing Authorities |
| PSB | Property Services Branch |
| EPA | Environment Protection Authority |

### B. References

- [Victorian Government Asbestos Management](https://www.worksafe.vic.gov.au/asbestos)
- [NSW DoE Asbestos Management](https://education.nsw.gov.au/)
- [Open Notebook Documentation](../index.md)
- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)
- [Docling GitHub](https://github.com/docling-project/docling)

### C. Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-07 | 1.0 | Initial PRD |
| 2026-02-04 | 1.1 | Victorian BAR format expansion (Sprint Change Proposal) |
| 2026-02-08 | 1.2 | UX Audit &amp; Enterprise Readiness - FR-700 series (11 requirements) |
| 2026-02-08 | 1.3 | Course correction: replaced 3 consultant parsers (Prensa, Greencap, Generic) with 1 generic configurable parser driven by BAR field schema configuration (FR-107, Section 5.7). See `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md` |
| 2026-02-20 | 1.4 | SCP-20260220: FR-102 updated (MinerU primary); 7 new `acm_record` fields (quantity, acm_labelled, identifying_company, floor_level, normalized_action, enriched_text, parent_table_id); 3 new tables (field_schema Â§5.1.2, acm_table_section Â§5.1.3, extraction_progress Â§5.1.4); 3 new API endpoints (extraction-progress SSE/REST, field-schema); FR-800 series (Extraction Monitor, E15); FR-900 series (UX Enhancement, E16); Section 1.4 note on generic parser; Section 9 resolved AG Grid license item |
| 2026-02-23 | 1.6 | Added FR-1100 series for cross-site marketing-app navigation, canonical root-domain behavior, and env-configurable URL contract for Vercel multi-project deployment |
| 2026-03-01 | 1.7 | Epic 29 reconciliation: unified orchestrator path contract, parser resilience requirement, benchmark-gated NFRs, and decision-gate release controls added. |
