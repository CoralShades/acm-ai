# Product Requirements Document (PRD) - ACM-AI

> **Product:** ACM-AI v1.0
> **Date:** 2025-12-07 (Updated: 2026-02-04)
> **Status:** Draft - Updated for Victorian BAR Format
> **Author:** John (Product Manager)
> **Change Log:** Sprint Change Proposal approved 2026-02-04 - Victorian BAR format expansion

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

---

## 2. Functional Requirements

### 2.1 Document Processing (FR-100 Series)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-101 | System shall accept PDF uploads up to 50MB | P0 | Upload succeeds for 50MB file within 30 seconds |
| FR-102 | System shall extract text and tables from PDFs using Docling | P0 | Docling processes file and returns structured output |
| FR-103 | System shall identify ACM Register tables within SAMP/BAR documents | P0 | Tables matching ACM schema are extracted with >90% accuracy |
| FR-104 | System shall parse hierarchical structure (Dept → Agency → Site → Building → Room → ACM Item) | P0 | Hierarchy correctly represented in data model |
| FR-107 | System shall support multiple PDF provider formats (Prensa, Greencap) | P0 | Auto-detects and parses different assessment formats |
| FR-108 | System shall allow configuration of non-extractable fields | P0 | User can set Department, Building Type, etc. |
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
    { field: 'building_size_m2', headerName: 'Size (m²)', width: 80 },
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

> **Updated 2026-02-04:** Schema expanded from 20 to ~50 fields to support Victorian BAR format.

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

-- Sample & Testing
DEFINE FIELD nata_sample_number ON acm_record TYPE option<string>;
DEFINE FIELD sample_result ON acm_record TYPE option<string>;  -- Negative, Positive, Assumed positive
DEFINE FIELD hygiene_company ON acm_record TYPE option<string>;  -- Prensa Pty Ltd, Greencap, etc.

-- Assessment
DEFINE FIELD material_condition ON acm_record TYPE option<string>;  -- Good, Fair, Poor
DEFINE FIELD disturbance_potential ON acm_record TYPE option<string>;  -- Low, Medium, High
DEFINE FIELD extent ON acm_record TYPE option<string>;  -- Quantity/extent
DEFINE FIELD risk_status ON acm_record TYPE option<string>;  -- Low, Medium, High, Very High

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

### 5.3 BAR Export Format Specification (NEW)

The system shall export Excel files compliant with Victorian Government BAR format:

**Sheet Structure:**
- Main sheet: DATA ENTRY (all ACM records)
- Reference sheets (optional): Building Types, Product Types, Suburbs, etc.

**Column Order (47 columns):**
1. Department → 2. Agency → 3. Sub Agency → 4. Site Name → 5. Building Name
6. Building Type → 7. Building Address → 8. Suburb → 9. Postcode → 10. Owned or Leased
11. Building Unique ID → 12. Frequency of use → 13. Public Access? → 14. Date of Inspection
15. Estimated Year Built → 16. Est. Building Size (m2) → 17. Number of Levels
18. Construction Type → 19. Roof Type → 20. Internal / External → 21. Level
22. Room or Area → 23. Location in Room → 24. Specific Item/ACM Name
25. Friability of material → 26. ACM Product Group → 27. ACM Product Type
28. NATA Endorsed Sample number → 29. Sample Result → 30. Identifying Hygiene Company
31. Condition → 32. Disturbance Potential → 33. Quantity → 34. Labelled
35. Label Details → 36. Hygienist Recommendations → 37. Additional Comments
38. PSB Supplied ACM ID → 39. Assumed Removed? → 40. Date of Removal
41. Quantity Removed → 42. Asbestos Removal Notification No
43. EPA Waste Transport Certificate No → 44-47. (Optional additional fields)

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

**Victorian BAR Format (Primary):**
- `Clutch_Broadmeadows Police Station Div 5 34511-039 V2_done.pdf` - Prensa format (19 pages)
- `Clucth_Alexander_District_Hospital_Asbestos_Risk_Assessment_2020-09-07.pdf` - Greencap format (34 pages)

**Expected Output Templates:**
- `Clutch_Broadmeadows_Police_BAR.xlsx` - 43 columns, 32 records
- `Clucth_Alexandra_District_BAR.xlsm` - 47 columns, 533 records

**NSW SAMP Format (Legacy):**
- `1124_AsbestosRegister.pdf` - Bankstown North Public School
- `3980_AsbestosRegister.pdf` - Additional test case
- `4601_AsbestosRegister.pdf` - Additional test case

### 7.2 Test Scenarios

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| T-001 | Upload Prensa PDF (Broadmeadows) | ACM data extracted with 32 records |
| T-002 | Upload Greencap PDF (Alexandra) | ACM data extracted with 533 records |
| T-003 | Configure site metadata during upload | Department, Agency populated |
| T-004 | Export to BAR Excel | All 47 columns in correct order |
| T-005 | Filter by risk status "Low" | Only Low risk rows shown |
| T-006 | Click cell in spreadsheet | PDF viewer opens to correct page |
| T-007 | Ask "What asbestos is in Building A?" | Chat responds with cited data |
| T-008 | Export to CSV | All BAR columns included |
| T-009 | Toggle column visibility | Columns show/hide correctly |
| T-010 | AI classify product group | Correct Product Group assigned |
| T-011 | Upload non-ACM PDF | Graceful error or empty ACM view |

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
