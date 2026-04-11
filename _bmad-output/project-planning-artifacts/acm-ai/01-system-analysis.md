# System Analysis - ACM-AI

> **Purpose:** Document current ACM-AI system capabilities, architecture, and remaining work
> **Last Updated:** 2026-03-31

## 1. ACM-AI Architecture

### 1.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 15 + React 19 | Modern web UI |
| UI Components | Radix UI + Tailwind CSS 4 | Design system |
| State Management | Zustand + React Query | Client/server state |
| Data Grid | AG Grid | Enterprise spreadsheet (47+ columns, grouping, filtering) |
| Backend API | FastAPI (Python 3.11+) | REST API |
| AI Framework | LangChain/LangGraph | Agent workflows (acm_extraction, supervisor graphs) |
| AI Abstraction | Esperanto (multi-provider) | OpenAI, Anthropic, Ollama |
| Database | SurrealDB | Document + vector + graph storage |
| Background Jobs | surreal-commands-worker | Async processing |
| Document Processing | Docling (primary) + MinerU 2.x | PDF/table extraction |
| Chat | CopilotKit + AG-UI protocol | Unified LangGraph agent (15 tools, AsyncSqliteSaver) |
| Observability | Langfuse (self-hosted) + LangSmith | Tracing, cost tracking |
| Streaming | PipelineEventBus + SSE | Real-time extraction progress |

### 1.2 Architecture Diagram

```
Browser (8502/8503) → Next.js Frontend → /api/* proxy → FastAPI Backend (5055) → SurrealDB (8000)
                                                       → LangGraph Agents (acm_extraction, supervisor)
                                                       → Docling / MinerU 2.x extraction
                                                       → PipelineEventBus → SSE → Frontend
```

Service communication:
- Frontend proxies all `/api/*` requests to FastAPI on port 5055
- Background worker processes async commands (extraction, enrichment)
- SSE streaming delivers real-time extraction progress to the browser
- LangGraph API (port 2024) available for local graph debugging

### 1.3 Implemented Features

All features planned in the original gap analysis have been completed:

| Feature | Status | Epic | Details |
|---------|--------|------|---------|
| **AG Grid Integration** | DONE | E2 (12 stories) | 47+ columns, building/item two-view, column visibility presets, row grouping, localStorage column state |
| **ACM Data Extraction Pipeline** | DONE | E1 (31 stories) | V3 multi-provider consensus + V3.5 per-row extraction, 9-stage pipeline |
| **Cell Citations & PDF Viewer** | DONE | E3 (4 stories) | ProvenanceViewer with PDF.js + bounding box overlay, extraction lineage |
| **Chat with ACM Context** | DONE | E4 + Unified Chat rewrite | CopilotKit + AG-UI, 15 tools, session persistence, model selection |
| **Data Export** | DONE | E5 | CSV, Excel, BAR template, Salesforce Data Loader format |
| **VAEA Branding** | DONE | E6 | Government-style VAEA branding, design system in `.impeccable.md` |
| **Source Upload** | DONE | Inherited | PDF upload with auto-notebook creation, cascade delete |
| **Vector Search** | DONE | Inherited | Semantic search across content |
| **Transformations** | DONE | Inherited | Extended for ACM extraction pipeline |

## 2. Document Processing Capabilities

### 2.1 Docling (Primary Provider)

Docling is the primary extraction provider, integrated via the `DoclingAdapter` in the Provider Adapter Framework:

- **PDF table extraction**: Structural table parsing with TableFormer integration
- **DoclingDocument JSON**: Full structured document stored for per-row extraction
- **Direct API**: Provides DataFrames for structured table access
- **Feature flag**: `DOCLING_DIRECT_TABLE_EXTRACTION=true` (promoted to default)
- **Evaluated**: TableFormer integration evaluated across E24/E25/E26 research spikes

### 2.2 MinerU 2.x (Secondary Provider)

MinerU 2.x installs directly in the main `.venv/` (no separate venv required):

- **Merged cell handling**: Correctly parses HTML tables with `colspan` and `rowspan`
- **Multi-page tables**: Automatic stitching of tables spanning multiple pages
- **Bounding box tracking**: Captures table coordinates `{x, y, width, height, page}` for provenance
- **Fallback**: System works without MinerU via automatic fallback to regex parsing

### 2.3 Supported Input Formats

- PDF (with table extraction via Docling/MinerU)
- DOCX, XLSX, PPTX
- Images (PNG, JPEG, TIFF, BMP)
- Markdown, HTML, CSV

### 2.4 Multi-Provider Consensus

The V3 architecture uses a consensus layer for extraction quality:

1. **Provider Adapters**: `DoclingAdapter`, `MinerUAdapter` normalize output to `NormalizedExtractionResult`
2. **Record Matching**: 3-stage matching (exact, fuzzy, positional) via `RecordMatcher`
3. **Consensus Engine**: Confidence-weighted voting across provider results
4. **Conflict Resolution**: L1-L4 escalation (identical, majority, confidence, flag)

## 3. Citation System

### 3.1 Reference Types

```
[source:id]               -> Links to source document
[note:id]                 -> Links to note
[source_insight:id]       -> Links to AI-generated insight
[acm:record_id:field_name] -> Links to specific ACM record field (NEW)
```

### 3.2 ProvenanceViewer

The citation system was extended with a full provenance tracking component:

- **PDF.js integration**: Renders source PDF pages with bounding box overlay
- **Extraction lineage**: Shows provider, model, confidence score, edit history
- **Field-level provenance**: Each ACM record field traces back to its extraction source
- **Bounding box data**: Stored in `ACMRecord.table_bbox` field `{x, y, width, height, page}`

### 3.3 Rendering Pipeline

1. AI response or grid cell contains inline references
2. `parseSourceReferences()` extracts references
3. `convertReferencesToCompactMarkdown()` creates numbered citations
4. Clickable links open ProvenanceViewer modal with PDF overlay

## 4. Gap Analysis

### 4.1 Completed Gaps (All Original Gaps Closed)

| Capability | Original State | ACM-AI Requirement | Status |
|------------|---------------|-------------------|--------|
| PDF Upload | Existed | Upload ARA/Register PDFs | DONE -- direct reuse |
| Table Extraction | Docling extracted tables | Extract ACM Register tables | DONE -- V3 multi-provider + schema mapping |
| Structured Data View | Markdown only | AG Grid spreadsheet | DONE -- AG Grid with 47+ columns, building/item two-view |
| Cell-level Citations | Document-level only | Click cell -> see PDF source | DONE -- ProvenanceViewer with PDF.js + bbox |
| Data Export | None | Export to Excel/CSV | DONE -- CSV, Excel, BAR template, SF Data Loader format |
| Branding | Open Notebook | ACM-AI / VAEA | DONE -- VAEA government branding |

### 4.2 Current Gaps / Future Work

| Area | Status | Notes |
|------|--------|-------|
| Mobile Support | Out of scope | Desktop-first government application |
| Multi-User Auth / RBAC | Not started | Currently single-user local deployment |
| Cloud Deployment | Not started | Local-only; RunPod used for GPU inference |
| Salesforce Data Loader Direct Integration | Planned | Currently export-only (SF Data Loader CSV format) |
| E2E Verification Suite | In progress | E36 S5-S8 backlog |
| Jobs/Source Unification | In progress | MCS11 sprint |

## 5. Document Format Support

### 5.1 Supported ARA Formats

The system now supports multiple Asbestos Register Assessment (ARA) document formats:

| Format | Consultant | Detection |
|--------|-----------|-----------|
| Victorian BAR | Various | `StandardFormatDetector` |
| ARA (pipe-table) | Various | `PipeTableDetector` |
| Prensa | Prensa | Format-specific parser |
| Greencap | Greencap | Format-specific parser |
| Clutch | Clutch | Format-specific parser |

Multi-consultant format support via schema inference (MCS sprint). 246 records extracted across 4 PDFs / 3 formats during validation.

### 5.2 Extraction Pipeline

```
PDF Upload -> Docling Extract -> Schema Inference -> Orchestrator -> Per-Row LLM -> Validate -> Save
                                      |                                  |
                                      v                                  v
                              Format Detection              Truncation Protection
                              (Pipe/Text/Standard)          (TruncationError -> cloud retry)
```

Per-row extraction (V3.5 default):
- One LLM call per table row -> 13 Item__c fields -> deterministic post-processing
- Row segmenter handles 8 edge case types (merged cells, split rows, etc.)
- Configurable: `ACM_ITEM_EXTRACTION_MODE=per_row` (default) or `bulk`

### 5.3 Hierarchical Data Model (Salesforce Schema Alignment)

```
Site
+-- Building (Building__c -- SF schema, 13+ fields)
    +-- External
    |   +-- ACM Items (Item__c -- SF schema, 47+ fields)
    +-- Internal
        +-- Room / Area
            +-- ACM Items (Item__c)
```

Key domain models:
- `Building__c`: Site name, building code, building name, year built, construction type
- `Item__c`: Product, material description, extent, location, friability, condition, risk status, result, accessibility, recommendations
- SF API names used as field aliases in `open_notebook/domain/acm.py`
- Dependent picklist validation via `SalesforcePicklistValidator`

### 5.4 ACM Record Schema

```python
class ACMRecord:
    source_id: str                    # Link to source PDF
    building_code: str                # Building__c reference
    building_name: str
    room_id: Optional[str]
    room_name: Optional[str]
    product: str                      # Type of building element
    material_description: str         # ACM material type
    extent: str                       # Area/quantity
    location: str                     # Building/room location
    friability: str                   # Friable / Non-Friable
    material_condition: str           # Current state
    risk_status: str                  # Low / Medium / High
    result: str                       # ACM confirmation
    accessibility: Optional[str]
    recommendations: Optional[str]
    page_start: Optional[int]         # For citation (coerced from str via BeforeValidator)
    page_end: Optional[int]
    table_bbox: Optional[dict]        # {x, y, width, height, page} for PDF overlay
    # ... 47+ total fields aligned to Salesforce Item__c schema
```

## 6. Current Architecture Details

### 6.1 Processing Pipeline (9 Stages)

| Stage | StageId | Purpose |
|-------|---------|---------|
| 1 | STRUCTURE | Document structure analysis, format detection |
| 2 | PREFLIGHT | Pre-extraction intelligence gathering |
| 3 | ORCHESTRATOR | Building inventory compilation, page range assignment |
| 4 | DOCLING_EXTRACTION | Docling/MinerU table extraction (runs outside graph) |
| 5 | EXTRACT | LLM extraction (per-row or bulk mode) |
| 6 | VALIDATE | Salesforce picklist validation, field normalization |
| 7 | CORRECT | Auto-correction of validation failures |
| 8 | NO_ACCESS_RECOVERY | Recovery of "No Access" flagged areas |
| 9 | STORE | Persist to SurrealDB |

### 6.2 Chat Architecture

- **CopilotKit + AG-UI protocol**: Unified LangGraph agent with 15 tools
- **AsyncSqliteSaver**: Session persistence across page reloads
- **Model selection**: User-configurable via UI, persisted to SurrealDB
- **SmartChatPanel**: Frontend component with `useSmartChat` hook (uses `useRef` for `setState` stability)

### 6.3 Observability Stack

| Tool | Purpose | Access |
|------|---------|--------|
| **Langfuse** (self-hosted) | Production monitoring, cost tracking, trace archive | `localhost:3000` |
| **LangSmith** (cloud) | Dev prompt iteration, auto-tracing all graphs | `smith.langchain.com` |
| **LangGraph API** (local) | Debug graph state, invoke/inspect threads | `127.0.0.1:2024/docs` |
| **Logfire SDK** (dev) | Pydantic validation traces -> Langfuse via OTel | Routes to Langfuse |
| **erdantic** (dev CLI) | Static ER diagrams of Pydantic model relationships | Local SVG files |
| **JSON Crack** (Docker) | Interactive JSON tree viewer for graph state | `localhost:8888` |

### 6.4 Frontend Route Hierarchy

| Route | Role | Priority |
|-------|------|----------|
| `/jobs` | Primary landing -- job cards with live status counters | **P0** |
| `/jobs/[id]` | Primary detail view -- all tabs, SSE streaming, bulk ops, chat | **P0** |
| `/jobs/[id]/extract` | Extraction monitoring (during extraction) | P1 |
| `/source/[id]` | Secondary ACM Register view (linked from jobs) | P2 |
| `/ai-editor` | AI-Editor list (auto-created per upload) | P2 |
| `/ai-editor/[id]` | AI-Editor detail -- sources, notes, chat columns | P2 |

### 6.5 Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/acm/buildings` | GET | Building records with record_count |
| `/api/acm/field-schema` | GET | Salesforce field schema config |
| `/api/acm/raw-extractions/{source_id}` | GET | Raw extraction records |
| `/api/acm/provenance/{record_id}` | GET | Record provenance with consensus data |
| `/api/acm/intelligence/{source_id}` | GET | Pre-extraction intelligence |
| `/api/acm/bulk-edit` | POST | Bulk field edit |
| `/api/acm/bulk-validate` | POST | Bulk re-validation |
| `/api/acm/validation-summary/{source_id}` | GET | Validation summary |
| `/api/sources/{source_id}/live-stats` | GET | Live extraction counters for polling |
| `/api/v3/stream/{category}/{id}` | GET | SSE streaming endpoints |

## 7. Remaining Work

### 7.1 In Progress

- **MCS11**: Jobs/source route unification -- E2E verification
- **E36 S5-S8**: End-to-end verification, benchmarking, auditing (backlog)
- **V3-8 S3-S8**: 6 remaining stories, 18 story points

### 7.2 Future

- **Salesforce Direct Integration**: Push records directly to SF org (currently export-only)
- **Multi-User Auth / RBAC**: Role-based access control for team use
- **Cloud Deployment**: Move beyond local/RunPod to hosted environment
- **Mobile Support**: Out of scope for government desktop application
- **Chat-based Record Corrections**: No V3 story exists (gap in architecture)
