# Product Requirements Document (PRD) - ACM-AI

> **Product:** ACM-AI v1.0
> **Date:** 2025-12-07
> **Status:** Draft
> **Author:** John (Product Manager)

---

## 1. Introduction

### 1.1 Purpose
This PRD defines the requirements for transforming Open Notebook into ACM-AI, a specialized platform for processing Asbestos Containing Material (ACM) compliance documents with intelligent extraction, spreadsheet visualization, and AI-powered querying.

### 1.2 Background
See [Product Brief](./02-product-brief.md) for business context and [System Analysis](./01-system-analysis.md) for technical foundation.

### 1.3 Scope
This document covers MVP requirements. Future enhancements are noted but not detailed.

---

## 2. Functional Requirements

### 2.1 Document Processing (FR-100 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-101 | System shall accept PDF uploads up to 50MB | P0 | Upload succeeds for 50MB file within 30 seconds |
| FR-102 | System shall extract text and tables from PDFs using Docling | P0 | Docling processes file and returns structured output |
| FR-103 | System shall identify ACM Register tables within SAMP documents | P0 | Tables matching ACM schema are extracted with >90% accuracy |
| FR-104 | System shall parse hierarchical structure (School → Building → Room → ACM Item) | P0 | Hierarchy correctly represented in data model |
| FR-105 | System shall store page numbers for each extracted data row | P0 | Every ACM record has associated page_number |
| FR-106 | System shall handle multi-page tables | P1 | Tables spanning pages are merged correctly |

### 2.2 Data Model (FR-200 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-201 | System shall store ACM records with schema defined in System Analysis | P0 | All fields populated correctly from sample PDFs |
| FR-202 | System shall link ACM records to source document | P0 | source_id foreign key maintained |
| FR-203 | System shall support vector embeddings for ACM records | P1 | Semantic search returns relevant records |
| FR-204 | System shall track extraction metadata (timestamp, confidence) | P1 | Metadata stored and accessible |

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
| FR-308 | System shall support CSV export | P0 | Download button exports current view |
| FR-309 | System shall support Excel export | P2 | Download as .xlsx (requires AG Grid Enterprise) |

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

### 2.6 Rebranding (FR-600 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-601 | Application title shall be "ACM-AI" | P0 | Browser title, header show "ACM-AI" |
| FR-602 | Logo shall reflect ACM-AI branding | P1 | New logo in header and favicon |
| FR-603 | Color scheme shall be professional/compliance-focused | P1 | Updated theme colors |
| FR-604 | Landing page shall describe ACM-AI purpose | P1 | Hero section explains value prop |

---

## 3. Non-Functional Requirements

### 3.1 Performance (NFR-100 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-101 | PDF processing shall complete within 60 seconds for 50-page document | P0 | Measured on reference hardware |
| NFR-102 | Spreadsheet shall render 1000+ rows without lag | P0 | Virtual scrolling enabled |
| NFR-103 | Chat response shall begin streaming within 3 seconds | P0 | First token latency measured |
| NFR-104 | Cell click to PDF display shall be <500ms | P1 | Cached pages load faster |

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
┌─────────────┬─────────────┬─────────────┐
│   Sources   │    Notes    │    Chat     │
└─────────────┴─────────────┴─────────────┘
```

ACM-AI layout (configurable):
```
Mode 1: Spreadsheet Focus
┌─────────────┬───────────────────────────┐
│   Sources   │      ACM Spreadsheet      │
│             ├───────────────────────────┤
│             │         Chat              │
└─────────────┴───────────────────────────┘

Mode 2: Document Focus (existing behavior)
┌─────────────┬─────────────┬─────────────┐
│   Sources   │    Notes    │    Chat     │
└─────────────┴─────────────┴─────────────┘
```

### 4.2 New Components

| Component | Description | Location |
|-----------|-------------|----------|
| `ACMSpreadsheet` | AG Grid wrapper for ACM data | Main panel (new) |
| `ACMCellViewer` | Modal showing PDF page for selected cell | Overlay |
| `ACMContextToggle` | Toggle to include ACM data in chat | Chat panel header |
| `ACMExportButton` | Export dropdown (CSV, Excel) | Spreadsheet toolbar |

### 4.3 AG Grid Column Configuration

```typescript
const acmColumnDefs = [
  { field: 'building_id', headerName: 'Building', rowGroup: true, hide: true },
  { field: 'room_name', headerName: 'Room', rowGroup: true, hide: true },
  { field: 'product', headerName: 'Product', width: 150 },
  { field: 'material_description', headerName: 'Material', width: 180 },
  { field: 'extent', headerName: 'Extent', width: 100 },
  { field: 'location', headerName: 'Location', width: 120 },
  { field: 'friable', headerName: 'Friable', width: 100 },
  { field: 'material_condition', headerName: 'Condition', width: 130 },
  { field: 'risk_status', headerName: 'Risk', width: 80, cellRenderer: 'riskBadge' },
  { field: 'result', headerName: 'Result', width: 200 },
];
```

---

## 5. Data Requirements

### 5.1 ACM Record Schema

```sql
-- SurrealDB schema
DEFINE TABLE acm_record SCHEMAFULL;
DEFINE FIELD source_id ON acm_record TYPE record<source>;
DEFINE FIELD school_name ON acm_record TYPE string;
DEFINE FIELD school_code ON acm_record TYPE string;
DEFINE FIELD building_id ON acm_record TYPE string;
DEFINE FIELD building_name ON acm_record TYPE string;
DEFINE FIELD building_year ON acm_record TYPE option<int>;
DEFINE FIELD building_construction ON acm_record TYPE option<string>;
DEFINE FIELD room_id ON acm_record TYPE option<string>;
DEFINE FIELD room_name ON acm_record TYPE option<string>;
DEFINE FIELD room_area ON acm_record TYPE option<float>;
DEFINE FIELD area_type ON acm_record TYPE string; -- 'Exterior', 'Interior', 'Grounds'
DEFINE FIELD product ON acm_record TYPE string;
DEFINE FIELD material_description ON acm_record TYPE string;
DEFINE FIELD extent ON acm_record TYPE string;
DEFINE FIELD location ON acm_record TYPE string;
DEFINE FIELD friable ON acm_record TYPE option<string>;
DEFINE FIELD material_condition ON acm_record TYPE option<string>;
DEFINE FIELD risk_status ON acm_record TYPE option<string>;
DEFINE FIELD result ON acm_record TYPE string;
DEFINE FIELD page_number ON acm_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON acm_record TYPE option<float>;
DEFINE FIELD created_at ON acm_record TYPE datetime DEFAULT time::now();

DEFINE INDEX acm_source ON acm_record FIELDS source_id;
DEFINE INDEX acm_building ON acm_record FIELDS building_id;
DEFINE INDEX acm_risk ON acm_record FIELDS risk_status;
```

### 5.2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/acm/extract` | POST | Trigger ACM extraction for a source |
| `/api/acm/records` | GET | List ACM records (with filters) |
| `/api/acm/records/{id}` | GET | Get single ACM record |
| `/api/acm/export` | GET | Export records as CSV |
| `/api/acm/stats` | GET | Summary statistics for dashboard |

---

## 6. Integration Points

### 6.1 Existing Systems to Modify

| System | Modification |
|--------|--------------|
| Source processing | Add ACM extraction step post-Docling |
| Chat context builder | Include ACM records in context |
| Citation parser | Handle `[acm:...]` references |
| Frontend routing | Add ACM spreadsheet view |

### 6.2 New Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| ag-grid-react | ^31.x | Spreadsheet component |
| ag-grid-community | ^31.x | Core grid functionality |
| react-pdf | ^7.x | PDF viewer in modal |

---

## 7. Testing Requirements

### 7.1 Test Data

- `1124_AsbestosRegister.pdf` - Bankstown North Public School
- `3980_AsbestosRegister.pdf` - Additional test case
- `4601_AsbestosRegister.pdf` - Additional test case

### 7.2 Test Scenarios

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| T-001 | Upload valid SAMP PDF | ACM data extracted and displayed |
| T-002 | Filter by risk status "Low" | Only Low risk rows shown |
| T-003 | Click cell in spreadsheet | PDF viewer opens to correct page |
| T-004 | Ask "What asbestos is in Building A?" | Chat responds with cited data |
| T-005 | Export to CSV | File downloads with correct data |
| T-006 | Upload non-SAMP PDF | Graceful error or empty ACM view |

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
| Confirm AG Grid license approach | User | Before development |
| Validate extraction accuracy on all sample PDFs | Dev team | Phase 1 |
| Design review for rebranding | User | Phase 3 |

---

## 10. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| ACM | Asbestos Containing Material |
| SAMP | School Asbestos Management Plan |
| Friable | ACM that can be crumbled by hand pressure |
| Non-Friable | ACM with fibers bound in matrix |

### B. References

- [NSW DoE Asbestos Management](https://education.nsw.gov.au/)
- [Open Notebook Documentation](../index.md)
- [AG Grid Documentation](https://www.ag-grid.com/react-data-grid/)
- [Docling GitHub](https://github.com/docling-project/docling)
