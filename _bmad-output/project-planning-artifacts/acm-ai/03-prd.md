# Product Requirements Document (PRD) - ACM-AI

> **Product:** ACM-AI v3.0
> **Date:** 2025-12-07 (Updated: 2026-03-02)
> **Status:** v3.0 - V3 Scope Expansion (Salesforce Alignment, Multi-Provider Extraction, Consensus Layer, Two-View UI)
> **Author:** John (Product Manager)
> **Change Log:** 2026-03-02 - v3.0: V3 Scope Expansion — Salesforce schema alignment (FR-1400 series, E30), multi-provider extraction + consensus layer (FR-1500, E31), two-view building/item UI (FR-1600, E33), SSE streaming (FR-1700, E34), AI strategy with capability registry (FR-1800, E32), 32 new stories across 5 epics (89 SP). Source: Party Mode synthesis + SF alignment SCP + multi-agent audit; 2026-03-01 - v1.7: E29 reconciliation (unified orchestrator, benchmark-gated NFRs, decision gates); 2026-02-23 - v1.6: E20 Cross-Site Navigation and Domain Cutover (marketing as primary entrypoint, app on demo subdomain, bidirectional navigation links, env-driven host contract); 2026-02-22 - v1.5: E17 Live Extraction Intelligence (AG-UI extraction relay, A2A agent card, incremental record streaming, reasoning/tool observability, 6 new models); 2026-02-20 - v1.4: SCP-20260220 (Extraction Monitor + UX Enhancement, schema fields, table additions, MinerU primary); 2026-02-08 - v1.3 UX Audit &amp; Enterprise Readiness; Course correction: single generic configurable parser

---

## 1. Introduction

### 1.1 Purpose
This PRD defines the requirements for transforming Open Notebook into ACM-AI, a specialized platform for processing Asbestos Containing Material (ACM) compliance documents with intelligent extraction, spreadsheet visualization, and AI-powered querying.

### 1.2 Background
See [Product Brief](./02-product-brief.md) for business context and [System Analysis](./01-system-analysis.md) for technical foundation.

### 1.3 Scope
This document covers MVP requirements (Epics 1-20, 29) and V3 scope expansion (Epics 30-34). V3 adds Salesforce schema alignment, multi-provider extraction with consensus, two-view building/item UI, and AI capability routing. See [Section 11: V3 Scope](#11-v3-scope-expansion) for detailed delineation of V3 additions.

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

### 2.12 Salesforce Schema Alignment (FR-1400 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion — SCP-20260301-SF, APPROVED)
> **Source:** [SCP-20260301-SF-salesforce-alignment.md](../../../V3/SCP-20260301-SF-salesforce-alignment.md)
> **Epic:** E30 — Foundation & SF Schema

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1401 | Store Building data in `building_record` table mapped to SF Building__c fields | P0 | `building_record` table exists with 29+ extractable SF Building__c fields; BuildingRecord Pydantic model validates; CRUD API endpoints return Building data |
| FR-1402 | Store ACM data in `acm_record` table mapped to SF Item__c fields | P0 | `acm_record` contains SF Item__c field aliases for 35+ fields; Pydantic aliases resolve SF API names; existing BAR fields preserved during transition |
| FR-1403 | Enforce Friability → ACM_Classification → ACM_Sub_Classification dependency chain | P0 | 18 ACM_Classification values × 2 Friability values = 36 valid combinations enforced; invalid combinations flagged with inline badge; export blocked for unresolved violations |
| FR-1404 | Enforce Building_Type → Building_Category dependency chain | P0 | 114 Building_Type values map to 13 Building_Category values; cascading dropdown filters valid categories based on selected type; invalid combinations flagged |
| FR-1405 | Validate picklist values against exact SF values (case-sensitive) | P0 | All picklist fields validated against SF-defined values; case-sensitive matching (e.g., "Stable" not "stable"); BAR "Good" mapped to SF "Stable" |
| FR-1406 | Export Building__c Data Loader CSV | P0 | CSV file generated with exact SF Building__c API field names as headers; all picklist values are valid SF values; External_ID__c field populated |
| FR-1407 | Export Item__c Data Loader CSV | P0 | CSV file generated with exact SF Item__c API field names as headers; Building external ID present for parent-child Data Loader matching; referential integrity verified |
| FR-1408 | Load SF schema from JSON config (describe metadata) | P0 | SF schema parsed from building_list.txt and item_list.txt into SalesforceSchemaConfig; loaded into field_schema table (version = salesforce-v1); picklist values and dependency chains available at runtime |
| FR-1409 | Use Anthropic Claude Sonnet as default AI interpretation provider for Building__c and Item__c extraction | P0 | Direct ChatAnthropic API used for extraction by default; OpenRouter MUST remain fully supported as fallback (admin-configurable toggle); Ollama local permitted for embeddings, classification fallback, and enrichment; all non-extraction AI tasks (chat, search) continue via Esperanto/OpenRouter |
| FR-1410 | Extract Building and ACM fields in separate AI calls | P0 | Two-phase extraction per building: Building__c fields extracted first, then Item__c fields; each phase uses dedicated prompt with SF field names and constrained picklist values |
| FR-1411 | Provide context-relevant Item_Name subsets by Product Group | P1 | Item_Name__c choices (294 values) constrained by selected ACM_Classification/Product Group context; prompt receives subset of ≤50 relevant values per classification |
| FR-1412 | Business rule: Negative result → Condition = N/A (negative) | P0 | When Sample_Analysis_Result_Material_Status__c is "Negative" or "Assumed Negative", Condition__c auto-set to "N/A (negative)" or "N/A (assumed negative)"; Disturbance_Potential__c likewise set to N/A variant; enforced in validator AND extraction prompt |

### 2.13 Multi-Provider Extraction (FR-1500 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion — Party Mode Synthesis)
> **Source:** [v3-party-mode-plan.md](../../../V3/output/v3-party-mode-plan.md) § PRD Delta
> **Epic:** E31 — Multi-Provider Extraction

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1501 | Support 2+ table extraction providers (Docling + MinerU) with consensus merging | P0 | Both Docling (structure-based) and MinerU (hybrid: VLM + pipeline) execute per document; raw results stored per-provider; consensus merge produces unified table sections; Broadmeadows accuracy ≥31/31 with consensus |
| FR-1502 | Per-field confidence scoring with consensus tier (HIGH/MEDIUM/LOW/CONTESTED) | P0 | Each merged record has consensus_tier assignment; HIGH = all providers agree; MEDIUM = 2/3 agree or >0.8 confidence; LOW = single provider; CONTESTED = disagreement on high-stakes field (result, friable, condition) |
| FR-1503 | Store raw per-provider extraction results for provenance | P0 | `raw_extraction_table` stores per-provider output with provider_id, page_number, raw_html, raw_markdown, structured_json, bbox, and confidence; officer_edits array tracks manual corrections |
| FR-1504 | Sequential GPU execution to prevent VRAM contention | P1 | Docling runs first (~4 GB, ~22s), MinerU hybrid runs second (~10 GB, ~15-20s); no concurrent GPU allocation; total dual-provider time ≤42s for 20-page document |
| FR-1505 | Provider adapter interface for adding future extraction providers | P1 | ExtractionProvider protocol defined with async extract method; DoclingAdapter and MinerUAdapter implement protocol; NormalizedExtractionResult schema normalizes both HTML tables and VLM image-based markdown; new provider requires only adapter implementation |
| FR-1506 | Cross-page table stitching (via MinerU) | P0 | Tables spanning multiple PDF pages merged into single logical table; MinerU hybrid backend handles multi-page stitching; stitched table coordinates tracked in bbox metadata |

### 2.14 UI / UX Flows (FR-1600 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion — Party Mode Synthesis)
> **Source:** [v3-party-mode-plan.md](../../../V3/output/v3-party-mode-plan.md) § PRD Delta
> **Epic:** E33 — Frontend & UX

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1601 | Upload wizard with provider selection (Quick/Thorough) | P0 | 3-step wizard: (1) drop PDF, (2) select provider mode (Quick = Docling only, Thorough = Docling + MinerU with consensus), (3) confirm and extract; wizard validates file type and size before submission |
| FR-1602 | SSE-powered extraction progress with building-by-building completion | P0 | Progress page shows stage labels, building cards with status; buildings appear as extraction completes; officers can navigate to completed buildings while extraction continues |
| FR-1603 | Two-view layout: building list + item grid per building | P0 | Building list sidebar shows all buildings for a source; clicking a building shows its Item__c records in AG Grid; building-by-building workflow matches SF officer workflow |
| FR-1604 | AG Grid dependent picklist cascading (SF dependency chains) | P0 | Custom cell editors for Friability→ACM_Classification→ACM_Sub_Classification; BuildingType→BuildingCategory; `getValues()` callback filters valid values based on controller field selection |
| FR-1605 | Inline SF validation badges (red/orange/yellow) | P0 | Invalid picklist values show red badge; dependency chain violations show orange badge; low-confidence consensus fields show yellow badge; export button grayed out with "X validation errors" until all resolved |
| FR-1606 | Raw table review (opt-in, editable) | P1 | Editable AG Grid showing raw extraction output at `/source/:id/raw`; officer corrections saved to `raw_extraction_table.officer_edits[]`; link to re-run AI processing on corrected raw data |
| FR-1607 | Provenance viewer (PDF.js + bbox overlay + lineage table) | P1 | Slide-over panel: top = PDF page rendered with highlighted bounding box; bottom = extraction lineage (provider, model, confidence, edit history); accessible via "Source" button on each record row |
| FR-1608 | Record wizard with SF picklist guidance | P1 | Modal dialog for editing individual records; dependent picklist dropdowns cascade correctly; SF field names shown alongside human-readable labels; save validates against SF schema |
| FR-1609 | Bulk operations (multi-select, bulk edit, bulk validate) | P1 | Multi-select checkboxes in AG Grid; bulk edit changes field for all selected records; bulk validate re-runs SF validation; bulk export generates CSV for selected buildings; SSE progress for bulk operations |
| FR-1610 | Building ID auto-assignment (BLD#NNN) during extraction | P0 | Server-side building ID generated during extraction: `BLD#{source_short}_{seq:03d}`; deterministic, generated in orchestrator; NOT the SF `Building_Name__c` field |

### 2.15 Streaming & Observability (FR-1700 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion — Party Mode Synthesis)
> **Source:** [v3-party-mode-plan.md](../../../V3/output/v3-party-mode-plan.md) § PRD Delta
> **Epic:** E34 — Integration, Streaming & Polish

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1701 | SSE endpoints for extraction, AI processing, and bulk operations | P0 | Three SSE endpoint categories filtered by operation ID; Zustand streaming store for frontend state; SSE triggers React Query refetch on data changes |
| FR-1702 | Record-by-record streaming to AG Grid during extraction | P1 | Records appear in AG Grid as they pass validation; officers can work on completed buildings while extraction continues; building completion events trigger grid update |
| FR-1703 | Full extraction lineage: table → record → field with provider, model, confidence, edit history | P0 | Each ACM record stores extraction_provider, extraction_model, consensus_metadata (tier, scores, votes), and edit_history (user, field, old, new, timestamp); lineage queryable via API |
| FR-1704 | PipelineEventBus for worker→SSE event relay | P1 | In-memory `asyncio.Queue`-based event bus; no external message broker required; SSE endpoints subscribe to bus; events include stage transitions, record completions, errors |

### 2.16 AI Strategy (FR-1800 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion — Party Mode Synthesis)
> **Source:** [v3-party-mode-plan.md](../../../V3/output/v3-party-mode-plan.md) § PRD Delta
> **Epic:** E32 — AI Processing & Validation

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1801 | Capability registry with ModelCapability enum (EXTRACTION, CLASSIFICATION, ENRICHMENT, EMBEDDING, CHAT, SEARCH) | P0 | ModelCapability enum defines 6 task types; ModelPolicy maps each task type to default provider + fallback; admin settings page allows per-task provider routing |
| FR-1802 | Ollama local for embeddings (zero cloud dependency) | P1 | Embedding generation uses Ollama local exclusively (nomic-embed-text or similar); no cloud API calls for embeddings; $0 embedding cost; data never leaves machine |
| FR-1803 | AI model selection invisible to end users (admin settings only) | P0 | Upload wizard shows no model selection; officers interact with accuracy results not model choices; admin settings page provides provider routing configuration |
| FR-1804 | Structured output via Pydantic models + Claude tool_use | P0 | BuildingExtractionResult and ACMItemExtractionResult Pydantic schemas used for Claude structured output via tool_use; schemas compatible with both Anthropic direct API and OpenRouter request/response formats |

---

## 3. Non-Functional Requirements

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

### 3.5 V3 Performance Targets (NFR-500 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-501 | Dual-provider extraction (Docling + MinerU) shall complete within 120 seconds for Broadmeadows (19 pages) | P0 | End-to-end pipeline time measured from upload to records-in-DB; sequential GPU execution: Docling (~22s) + MinerU hybrid (~20s) + consensus (~1s) + AI extraction |
| NFR-502 | Dual-provider extraction shall complete within 300 seconds for Alexander (34 pages) | P0 | End-to-end pipeline time including multi-building extraction, validation, and correction loops |
| NFR-503 | Consensus layer record matching shall complete in under 1 second per table section | P1 | Measured from provider results ready to consensus merge complete; per-field voting and conflict resolution included |
| NFR-504 | GPU memory shall not exceed 10 GB peak during any single extraction phase | P1 | Sequential execution prevents VRAM contention; Docling (~4 GB) and MinerU hybrid (~10 GB) never run concurrently; monitored via nvidia-smi |
| NFR-505 | V3 extraction accuracy shall equal or exceed V1 benchmarks | P0 | Broadmeadows ≥31/31 records; Alexander ≥40/43 records (after completionState fix baseline); all picklist values valid SF values |

### 3.6 Data Sovereignty & Compliance (NFR-600 Series)

> **Added:** 2026-03-02 (V3 Scope Expansion)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-601 | Anthropic API data shall not be used for model training | P0 | Anthropic API terms confirm; documented in deployment guide |
| NFR-602 | Ollama embedding and classification operations shall be fully local | P0 | No network calls during embedding/classification; verified via network traffic audit |
| NFR-603 | Exported CSV/Excel files shall contain only SF-validated field values | P0 | Export blocked if any record has unresolved validation errors; all picklist values match exact SF values |
| NFR-604 | Edit history shall be immutable and auditable | P1 | All record modifications tracked in edit_history array; entries include user, field, old value, new value, timestamp; no deletion of history entries |

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

### 4.4 V3 UI Structure (NEW - 2026-03-02)

> **Added:** V3 Scope Expansion — Two-view layout, upload wizard, provenance viewer

**V3 Page Flow:**
```
/upload           → Upload Wizard (3 steps: drop PDF, select provider mode, extract)
/extraction/:id   → Extraction Progress (SSE-powered, stage labels, building cards)
/source/:id/raw   → Raw Table Review (opt-in, editable AG Grid)
/source/:id       → Building Grid (sidebar list) + Item Grid (per-building)
/source/:id/provenance/:recordId → Provenance Viewer (PDF.js + lineage)
/source/:id/export → Export Dialog (Building__c + Item__c, CSV/Excel)
/admin/settings   → AI Provider Config, Field Schema, Site Config
```

**V3 New Components:**

| Component | Description | Location |
|-----------|-------------|----------|
| `UploadWizard` | 3-step wizard: drop PDF, select provider mode, extract | /upload page |
| `ExtractionProgress` | SSE-powered progress with building cards and stage labels | /extraction/:id page |
| `BuildingListSidebar` | Building list with drill-down selection | Source detail sidebar |
| `ItemGrid` | AG Grid for Item__c records filtered by selected building | Source detail main panel |
| `DependentPicklistEditor` | AG Grid custom cell editor with cascading SF picklist values | Grid cell editors |
| `ValidationBadge` | Inline red/orange/yellow badge for SF validation status | Grid cell renderer |
| `RecordWizardModal` | Modal for editing individual records with SF picklist guidance | Overlay |
| `ProvenanceViewer` | PDF.js + bbox overlay + extraction lineage table | Slide-over panel |
| `RawTableReview` | Editable AG Grid for raw extraction output | /source/:id/raw page |
| `SFExportDialog` | Export dialog for Building__c + Item__c CSV/Excel | /source/:id/export |

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

### 5.1.5 Building Record Table (V3 — E30-S2)

> **Added:** 2026-03-02 (V3 Scope Expansion — SF Building__c alignment)

Stores building-level data as a first-class entity, mapped to SF Building__c extractable fields. Master-detail relationship: `acm_record.building_id → building_record.id`.

```sql
DEFINE TABLE building_record SCHEMAFULL;
DEFINE FIELD source_id ON building_record TYPE record<source>;
DEFINE FIELD internal_id ON building_record TYPE string;            -- BLD#001, BLD#002 (auto-assigned)
DEFINE FIELD building_name ON building_record TYPE option<string>;  -- SF: Building_Name__c
DEFINE FIELD building_address ON building_record TYPE option<string>; -- SF: Building_Address__c
DEFINE FIELD suburb ON building_record TYPE option<string>;         -- SF: Suburb__c (custom derived)
DEFINE FIELD postcode ON building_record TYPE option<string>;       -- SF: Postcode__c (custom derived)
DEFINE FIELD state ON building_record TYPE option<string>;          -- SF: State__c (custom derived)
DEFINE FIELD construction_type ON building_record TYPE option<string>; -- SF: Construction_Type__c
DEFINE FIELD building_type ON building_record TYPE option<string>;  -- SF: Building_Type__c (picklist, 114 values)
DEFINE FIELD building_category ON building_record TYPE option<string>; -- SF: Building_Category__c (dependent on Building_Type__c)
DEFINE FIELD estimated_year_built ON building_record TYPE option<string>; -- SF: Estimated_Year_Build_New__c
DEFINE FIELD number_of_levels ON building_record TYPE option<string>; -- SF: Number_of_Levels__c (custom derived)
DEFINE FIELD est_building_size ON building_record TYPE option<string>; -- SF: Est_Building_Size_m2__c
DEFINE FIELD date_of_inspection ON building_record TYPE option<string>; -- SF: Date_of_Inspection__c (formula)
DEFINE FIELD roof_type ON building_record TYPE option<string>;      -- SF: Roof_Type__c (custom derived)
DEFINE FIELD frequency_of_use ON building_record TYPE option<string>; -- SF: Frequency_of_Use__c (picklist)
DEFINE FIELD owned_or_leased ON building_record TYPE option<string>; -- SF: Owned_or_Leased__c (custom derived)
DEFINE FIELD department ON building_record TYPE option<string>;     -- From site_config
DEFINE FIELD organisation ON building_record TYPE option<string>;   -- From site_config
DEFINE FIELD page_number ON building_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON building_record TYPE option<float>;
DEFINE FIELD extraction_provider ON building_record TYPE option<string>;
DEFINE FIELD extraction_model ON building_record TYPE option<string>;
DEFINE FIELD created_at ON building_record TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON building_record TYPE datetime DEFAULT time::now();

DEFINE INDEX bldg_source ON building_record FIELDS source_id;
DEFINE INDEX bldg_internal_id ON building_record FIELDS internal_id;
```

### 5.1.6 Raw Extraction Table (V3 — E31-S4)

> **Added:** 2026-03-02 (V3 Scope Expansion — Per-provider provenance storage)

Stores raw extraction output per provider BEFORE consensus merging and AI interpretation. Full provenance chain.

```sql
DEFINE TABLE raw_extraction_table SCHEMAFULL;
DEFINE FIELD source_id ON raw_extraction_table TYPE record<source>;
DEFINE FIELD provider_id ON raw_extraction_table TYPE string;      -- "docling", "mineru", "google_docai"
DEFINE FIELD extraction_backend ON raw_extraction_table TYPE option<string>; -- "pipeline", "vlm", "hybrid", null
DEFINE FIELD page_number ON raw_extraction_table TYPE int;
DEFINE FIELD raw_html ON raw_extraction_table TYPE option<string>;
DEFINE FIELD raw_markdown ON raw_extraction_table TYPE option<string>;
DEFINE FIELD structured_json ON raw_extraction_table TYPE option<object>;
DEFINE FIELD bbox ON raw_extraction_table TYPE option<object>;     -- {x, y, width, height}
DEFINE FIELD confidence ON raw_extraction_table TYPE option<float>;
DEFINE FIELD officer_edits ON raw_extraction_table TYPE option<array<object>>; -- [{field, old, new, user, timestamp}]
DEFINE FIELD created_at ON raw_extraction_table TYPE datetime DEFAULT time::now();

DEFINE INDEX raw_source ON raw_extraction_table FIELDS source_id;
DEFINE INDEX raw_provider ON raw_extraction_table FIELDS provider_id;
```

### 5.1.7 V3 Schema Additions to Existing Tables

> **Added:** 2026-03-02 (V3 Scope Expansion)

**acm_record — V3 field additions:**
```sql
-- Building FK (replaces freeform building_id string)
DEFINE FIELD building_id ON acm_record TYPE option<record<building_record>>;
-- Raw provenance link
DEFINE FIELD raw_row_id ON acm_record TYPE option<record<raw_extraction_table>>;
-- Extraction metadata
DEFINE FIELD extraction_provider ON acm_record TYPE option<string>;
DEFINE FIELD extraction_model ON acm_record TYPE option<string>;
-- Consensus metadata
DEFINE FIELD consensus_metadata ON acm_record TYPE option<object>; -- {tier, scores, votes}
-- Edit history (immutable audit trail)
DEFINE FIELD edit_history ON acm_record TYPE option<array<object>>; -- [{user, field, old, new, timestamp}]
-- Note: SF field names are exposed via Pydantic aliases, not separate DB columns
```

**acm_table_section — V3 field additions:**
```sql
-- Multi-provider consensus data
DEFINE FIELD provider_results ON acm_table_section TYPE option<object>;   -- {docling: {...}, mineru: {...}}
DEFINE FIELD consensus_tier ON acm_table_section TYPE option<string>;     -- HIGH, MEDIUM, LOW, CONTESTED
DEFINE FIELD consensus_scores ON acm_table_section TYPE option<object>;   -- Per-field agreement data
```

**site_config — V3 field additions:**
```sql
-- SF-specific officer-configured fields
DEFINE FIELD department_sf ON site_config TYPE option<string>;     -- SF: Department__c context
DEFINE FIELD organisation_sf ON site_config TYPE option<string>;   -- SF: Organisation__c
DEFINE FIELD building_type_default ON site_config TYPE option<string>; -- Default Building_Type__c
DEFINE FIELD building_category_default ON site_config TYPE option<string>; -- Default Building_Category__c
```

**field_schema — V3 evolution:**
```sql
-- Evolve to support SF picklist values and dependency chains
-- version = "salesforce-v1" for SF-aligned config
-- config_json contains: {building_fields, item_fields, picklists, dependencies}
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

**V3 API Endpoints (NEW — 2026-03-02):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/acm/buildings` | GET | List building records for a source (filterable) |
| `/api/acm/buildings/{id}` | GET | Get single building record |
| `/api/acm/buildings/{id}` | PUT | Update building record |
| `/api/acm/buildings/{id}` | DELETE | Delete building and cascade to child ACM records |
| `/api/acm/buildings/{id}/items` | GET | List ACM items for a specific building |
| `/api/acm/export/sf/building` | GET | Export Building__c Data Loader CSV |
| `/api/acm/export/sf/item` | GET | Export Item__c Data Loader CSV |
| `/api/acm/export/sf/excel` | GET | Export Excel with Building__c + Item__c sheets |
| `/api/acm/raw-tables/{source_id}` | GET | List raw extraction tables for a source |
| `/api/acm/raw-tables/{id}` | PUT | Update raw extraction table (officer edits) |
| `/api/acm/sf-schema` | GET | Get active Salesforce schema config (picklists, dependencies) |
| `/api/acm/sf-schema/validate` | POST | Validate records against SF schema |
| `/api/acm/provenance/{record_id}` | GET | Get extraction lineage for a record |
| `/api/admin/ai-config` | GET | Get AI provider routing configuration |
| `/api/admin/ai-config` | PUT | Update AI provider routing (admin only) |

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

### 5.3.1 Salesforce Export Format Specification (V3 — NEW)

> **Added:** 2026-03-02 (V3 Scope Expansion — FR-1406, FR-1407)

The system shall export CSV/Excel files compatible with Salesforce Data Loader:

**File Structure:**
- `Building__c.csv` — One row per building, exact SF Building__c API field names as headers
- `Item__c.csv` — One row per ACM item, exact SF Item__c API field names as headers, Building External_ID__c for parent linkage
- Excel: Two sheets (Building__c, Item__c) in a single .xlsx file

**Data Loader Requirements:**
- All picklist values must be exact SF values (case-sensitive)
- External_ID__c populated for upsert matching
- Building parent-child linking via Building External ID in Item__c sheet
- All validation errors must be resolved before export is permitted

**Export Validation Gate:**
Export is blocked if any record has unresolved SF validation errors. Export button shows "X validation errors — resolve before export" until clean.

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

### 5.4.1 V3 Target Pipeline (NEW - 2026-03-02)

> **Added:** V3 Scope Expansion — 5-phase pipeline with multi-provider extraction and SF-aligned validation

```
Phase 1: PDF Processing (E31)
  PDF → PyMuPDF (text)
      + Docling (structure-based HTML tables)
      + MinerU hybrid (VLM image-based + pipeline, auto-routes)
  → raw_extraction_table (per-provider, includes VLM output)
  → Consensus Layer (per-field weighted voting, 3-stage matching)
  → acm_table_section (consensus-merged, provider_results JSONB)

Phase 2: Structure Analysis (existing + enhanced)
  Table-derived structure (page ranges, building groups)
  + Heuristic enrichment (TOC, building names, metadata)
  → Building Inventory + Page Tags

Phase 3: AI Extraction — per building (E32)
  Orchestrator → Building__c extraction (Claude Sonnet, SF field names)
               → Item__c extraction (Claude Sonnet, SF picklist values)
  → Raw BuildingRecord + ACMRecord candidates

Phase 4: Validation & Correction (E32)
  Pydantic schema validation (SF field types)
  → SF picklist validation (exact case-sensitive values)
  → Dependency chain validation (Friability→Classification, BuildingType→Category)
  → AI correction loop (Claude Sonnet, max 3 retries, single-record context)
  → Dedup + No-Access recovery
  → Negative→N/A business rule enforcement

Phase 5: Review & Export (E33, E34)
  → building_record + acm_record in SurrealDB
  → AG Grid (building list sidebar + item grid, dependent picklists)
  → Provenance viewer (PDF.js + bbox overlay)
  → Export: Building__c.csv + Item__c.csv (SF Data Loader ready)
```

**V3 Fallback additions:**
- Provider failure: skip failed provider, continue with remaining providers; non-fatal
- Consensus conflict: L1 weighted vote → L2 provider priority → L3 LLM arbitration → L4 human escalation (CONTESTED badge)
- AI extraction failure: Anthropic direct → OpenRouter fallback → skip building + preserve partial
- SF validation failure: WARN during editing (inline badges), REJECT on export

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

**V3 Salesforce Vocabulary Alignment (2026-03-02):**

| BAR Value | SF Value | Affected Field | Migration |
|-----------|----------|---------------|-----------|
| `Good` | `Stable` | Condition (Condition__c) | BAR "Good" has NO SF equivalent — map to "Stable" |
| `T3 Vinyl products` | `Vinyl products` | ACM_Classification__c | Remove "T3" prefix for SF picklist match |
| `product` | `Item_Name__c` | Item name field | Pydantic alias; 294 valid values from SF picklist |
| `friable` | `Friability_of_Material__c` | Friability field | Pydantic alias |
| `material_condition` | `Condition__c` | Condition field | Pydantic alias + value mapping |
| `acm_product_group` | `ACM_Classification__c` | Product group | Pydantic alias + value mapping |
| `acm_product_type` | `ACM_Sub_Classification__c` | Product type | Pydantic alias |
| `labelled` (bool) | `Labelled__c` (picklist "Yes"/"No") | Labelled field | Type change: boolean → picklist |

> **Note:** SF adds `Negative - Treated as Positive` to Sample_Analysis_Result_Material_Status__c (not in current BAR enum). SF Condition values: `Poor`, `Fair`, `Stable`, `Unknown`, `N/A (negative)`, `N/A (assumed negative)`.

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

**V3 Test Scenarios (NEW — 2026-03-02):**

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| T-V3-001 | Dual-provider extraction on Broadmeadows | Docling + MinerU both execute; consensus merge produces ≥31/31 records |
| T-V3-002 | Dual-provider extraction on Alexander | Consensus ≥40/43 after completionState fix baseline |
| T-V3-003 | SF picklist validation — valid values | All extracted picklist values match exact SF values (case-sensitive) |
| T-V3-004 | SF picklist validation — invalid values | Invalid values flagged with inline red badge; export blocked |
| T-V3-005 | Dependent picklist chain — Friability→Classification | Selecting "Non-friable" filters to 8 valid ACM_Classification values; "Friable" filters to 6 |
| T-V3-006 | Dependent picklist chain — BuildingType→Category | Selecting Building_Type filters to valid Building_Category values (114→13 mapping) |
| T-V3-007 | Two-phase AI extraction | Building__c fields extracted in first call; Item__c fields in second; both stored correctly |
| T-V3-008 | Building__c.csv export | CSV headers match SF API names; all values valid SF picklist values; External_ID__c populated |
| T-V3-009 | Item__c.csv export | CSV headers match SF API names; Building external ID present for parent-child linkage |
| T-V3-010 | Export validation gate | Export button disabled when validation errors exist; enabled when all clean |
| T-V3-011 | Consensus tier assignment | HIGH when all providers agree; MEDIUM for 2/3; LOW for single provider; CONTESTED for disagreement |
| T-V3-012 | Provider failure fallback | When MinerU fails, extraction continues with Docling only; non-fatal toast notification |
| T-V3-013 | Anthropic→OpenRouter fallback | When Anthropic direct fails, extraction falls back to OpenRouter; admin toggle works |
| T-V3-014 | Two-view building/item layout | Building list sidebar; click building shows filtered items; building-by-building navigation |
| T-V3-015 | Provenance viewer | Click "Source" on record; PDF renders with bbox highlight; lineage table shows provider, model, confidence |
| T-V3-016 | Building ID auto-assignment | Buildings assigned BLD#NNN IDs during extraction; deterministic, sequential |
| T-V3-017 | "Good"→"Stable" migration | All BAR "Good" values correctly mapped to SF "Stable" in extraction, validation, and export |
| T-V3-018 | Negative→N/A business rule (SF) | Negative result auto-sets Condition__c and Disturbance_Potential__c to N/A variants |
| T-V3-019 | Cascading delete | Deleting a building_record cascades to child acm_records |
| T-V3-020 | Edit history audit trail | All record modifications tracked in edit_history with user, field, old, new, timestamp |

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

### V3 Phase 5: Foundation & SF Schema (E30)
- Salesforce schema config loader and dependency chain mappings
- Building Record table + domain model (SF Building__c)
- ACM Record SF Item__c field alignment
- Dependent picklist validator
- Data migration (BAR→SF vocabulary)
- Two-phase extraction prompts (Building__c + Item__c)
- Anthropic Claude direct API + OpenRouter fallback

### V3 Phase 6: Multi-Provider Extraction (E31)
- MinerU 2.x integration (hybrid backend)
- Provider adapter framework
- Consensus layer (record matching + per-field voting)
- Raw extraction table storage
- Pipeline integration + benchmark validation

### V3 Phase 7: AI Processing & Validation (E32)
- Two-phase Building__c + Item__c AI extraction
- SF-aligned validation + correction loop
- Classifier update (SF taxonomy)
- Ollama model evaluation spike

### V3 Phase 8: Frontend & UX (E33)
- Upload wizard with provider selection
- Two-view building/item grid layout
- Dependent picklist cell editors
- Validation badges + record wizard
- Raw table review + provenance viewer
- Salesforce-ready export

### V3 Phase 9: Integration & Polish (E34)
- PipelineEventBus + SSE endpoints
- Record-by-record streaming
- Bulk operations
- Performance optimization
- Canonical artifact update

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
| Building__c | Salesforce custom object representing a physical building/asset |
| Item__c | Salesforce custom object representing an ACM item within a building |
| Data Loader | Salesforce bulk data import tool using CSV files |
| Dependent Picklist | SF picklist where valid values depend on another field's selection |
| Consensus Layer | V3 component that merges extraction results from multiple providers |
| VLM | Vision Language Model — MinerU backend that processes page images |
| Hybrid Backend | MinerU mode that auto-routes pages to pipeline or VLM based on complexity |

### B. References

- [Victorian Government Asbestos Management](https://www.worksafe.vic.gov.au/asbestos)
- [NSW DoE Asbestos Management](https://education.nsw.gov.au/)
- [Open Notebook Documentation](../index.md)
- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)
- [Docling GitHub](https://github.com/docling-project/docling)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Salesforce Data Loader Guide](https://developer.salesforce.com/docs/atlas.en-us.dataLoader.meta/dataLoader/)

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
| 2026-03-02 | 3.0 | **V3 Scope Expansion:** FR-1400 series (SF alignment, 12 FRs); FR-1500 series (multi-provider extraction, 6 FRs); FR-1600 series (UI/UX flows, 10 FRs); FR-1700 series (streaming, 4 FRs); FR-1800 series (AI strategy, 4 FRs); FR-1409 amended (Anthropic default + OpenRouter fallback); NFR-500 (V3 performance), NFR-600 (data sovereignty); Building Record schema (§5.1.5), Raw Extraction Table (§5.1.6), V3 schema additions (§5.1.7); V3 pipeline architecture (§5.4.1); SF vocabulary mapping (§5.5); SF export format (§5.3.1); V3 UI structure (§4.4); 20 V3 test scenarios; V3 rollout phases 5-9; Section 11 V3 Scope |

---

## 11. V3 Scope Expansion

> **Added:** 2026-03-02
> **Source Documents:** [Party Mode Synthesis](../../../V3/output/v3-party-mode-plan.md), [SF Alignment SCP](../../../V3/SCP-20260301-SF-salesforce-alignment.md), [Multi-Agent Audit](../../../V3/output/e30-multi-agent-audit-unified.md)

### 11.1 V3 Overview

V3 transforms ACM-AI from a BAR-centric extraction tool into a Salesforce-aligned compliance platform with multi-provider extraction, consensus-based accuracy, and two-phase building/item data model. All original PRD content (Epics 1-20, 29) is preserved; V3 adds Epics 30-34.

**Key V3 Capabilities:**
1. **Salesforce Schema Alignment** — Data model split into Building__c + Item__c with dependent picklist validation and SF Data Loader export
2. **Multi-Provider Extraction** — Docling (structure-based) + MinerU (vision-based hybrid) with per-field consensus merging
3. **Two-Phase AI Extraction** — Separate Building__c and Item__c extraction calls per building using Claude Sonnet
4. **Two-View UI** — Building list sidebar + item grid, dependent picklist cascading, SF validation badges
5. **Full Provenance** — Raw per-provider data, consensus metadata, extraction lineage, edit history audit trail
6. **AI Capability Routing** — 6-task-type capability registry with per-task provider routing (Anthropic, OpenRouter, Ollama)

### 11.2 V3 Epic Boundary Summary

| Epic | Scope | Stories | SP | Dependencies |
|------|-------|--------:|---:|-------------|
| E30: Foundation & SF Schema | SF schema config, building record model, dependent picklist validation, data migration, extraction prompts, Anthropic direct API | 8 | 20 | E29 complete |
| E31: Multi-Provider Extraction | MinerU 2.x integration, provider adapters, consensus layer, raw storage, pipeline integration | 6 | 17 | E30 (schema freeze) |
| E32: AI Processing & Validation | Two-phase extraction, SF validation + correction, classifier update, Ollama evaluation | 6 | 18 | E30, E31 |
| E33: Frontend & UX | Upload wizard, building/item grid, picklist editors, validation badges, provenance viewer, export | 7 | 22 | E30, E32 |
| E34: Integration & Polish | EventBus + SSE, record streaming, bulk operations, performance, artifact update | 5 | 12 | E30-E33 |
| **TOTAL** | | **32** | **89** | |

### 11.3 V3 Dependency Graph

```
E30 (Foundation & SF Schema) ─── SCHEMA FREEZE GATE ──┐
                                                       │
E31 (Multi-Provider) ─────────────────────────────────┤
                                                       │
                      E32 (AI Processing) ─────────────┤
                                                       │
                      E33-S1,S2 (Core UI) ─────────────┤  ← can start after E30
                                                       │
                      E33-S3-S7 (Advanced UI) ─────────┤  ← after E32
                                                       │
                      E34 (Integration) ───────────────┘  ← after E32+E33-S2

Critical path: E30 → E31 → E32 → E33-S3 → E34
Parallel lane: E33-S1,S2 can start after E30 (API contracts defined)
```

### 11.4 V3 Data Model Overview

```
source
  ├── raw_extraction_table (per-provider: Docling, MinerU)
  │     └── bbox, raw HTML/markdown, officer_edits[]
  ├── acm_table_section (consensus-merged, provider_results JSONB)
  │     └── consensus_tier (HIGH/MEDIUM/LOW/CONTESTED)
  ├── building_record (SF Building__c mapped, 29+ fields)
  │     └── acm_record (SF Item__c mapped, 35+ fields)
  │           └── edit_history[], consensus_metadata
  ├── site_config (officer-configured SF fields)
  └── field_schema (SF picklists, dependency chains, version=salesforce-v1)
```

### 11.5 V3 AI Capability Routing

| Task Type | Default Provider | Fallback | Admin Override? |
|-----------|-----------------|----------|:--------------:|
| EXTRACTION | Anthropic Claude Sonnet (direct API) | OpenRouter (same or alt model) | YES |
| CLASSIFICATION | Regex patterns (80% hit rate) | Ollama local → Claude Sonnet | YES |
| ENRICHMENT | Ollama local (llama3.1:8b) | Claude Haiku via OpenRouter | YES |
| EMBEDDING | Ollama local (nomic-embed-text) | None (local only) | NO |
| CHAT | Esperanto/OpenRouter (user-selected) | N/A | YES |
| SEARCH | Esperanto/OpenRouter | N/A | YES |

### 11.6 V3 FR Traceability

| FR Series | Epic | Source Document | Status |
|-----------|------|-----------------|--------|
| FR-1401–FR-1412 | E30 | SCP-20260301-SF-salesforce-alignment.md | APPROVED |
| FR-1501–FR-1506 | E31 | v3-party-mode-plan.md § PRD Delta | NEW |
| FR-1601–FR-1610 | E33 | v3-party-mode-plan.md § PRD Delta | NEW |
| FR-1701–FR-1704 | E34 | v3-party-mode-plan.md § PRD Delta | NEW |
| FR-1801–FR-1804 | E32 | v3-party-mode-plan.md § PRD Delta | NEW |
