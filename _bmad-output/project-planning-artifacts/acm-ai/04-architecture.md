# Technical Architecture - ACM-AI

> **Project:** ACM-AI v1.0
> **Date:** 2025-12-07 (Updated: 2026-02-08)
> **Status:** Draft - Updated for UX &amp; Enterprise Readiness
> **Change Log:**
> - 2026-02-08 - Frontend Design System Architecture (UX Audit)
> - 2026-02-08 - Sections 5.2, 5.3 rewritten: Generic Configurable Parser Architecture (course correction per `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md`)

---

## 1. Architecture Overview

### 1.1 High-Level System Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │           Browser Client            │
                                    │         (localhost:8502)            │
                                    └──────────────┬──────────────────────┘
                                                   │
                                    ┌──────────────▼──────────────────────┐
                                    │      Next.js Frontend (8502)        │
                                    │  ┌─────────────────────────────────┐│
                                    │  │ Components                      ││
                                    │  │ ├─ ACMSpreadsheet (AG Grid)     ││
                                    │  │ ├─ ACMCellViewer (PDF Modal)    ││
                                    │  │ ├─ ChatPanel (Enhanced)         ││
                                    │  │ └─ SourcePanel (Existing)       ││
                                    │  └─────────────────────────────────┘│
                                    │             │ /api/* proxy          │
                                    └─────────────┼───────────────────────┘
                                                  │
                                    ┌─────────────▼───────────────────────┐
                                    │      FastAPI Backend (5055)         │
                                    │  ┌─────────────────────────────────┐│
                                    │  │ Routers                         ││
                                    │  │ ├─ /api/acm/* (NEW)             ││
                                    │  │ ├─ /api/sources/*               ││
                                    │  │ ├─ /api/chat/*                  ││
                                    │  │ └─ /api/notes/*                 ││
                                    │  └─────────────────────────────────┘│
                                    └──────────────┬──────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
        ┌───────────▼───────────┐    ┌─────────────▼─────────────┐    ┌──────────▼──────────┐
        │   SurrealDB (8000)    │    │   Background Worker       │    │   Docling Service   │
        │  ┌─────────────────┐  │    │  ┌─────────────────────┐  │    │   (Local Python)    │
        │  │ Tables          │  │    │  │ Commands            │  │    │                     │
        │  │ ├─ source       │  │    │  │ ├─ process_source   │  │    │  PDF → Markdown     │
        │  │ ├─ note         │  │    │  │ ├─ run_transform    │  │    │  Table Extraction   │
        │  │ ├─ acm_record   │◄─┼────┼──┤ ├─ acm_extract(NEW) │  │    │                     │
        │  │ ├─ site_config  │  │    │  │ └─ acm_classify     │  │    │  Multi-format       │
        │  │ └─ embedding    │  │    │  └─────────────────────┘  │    │  (Prensa, Greencap) │
        │  └─────────────────┘  │    └───────────────────────────┘    └─────────────────────┘
        └───────────────────────┘
```

### 1.2 Data Flow

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌─────────────┐
│  Upload  │────►│   Docling   │────►│ ACM Parser   │────►│  SurrealDB    │────►│  AG Grid    │
│  PDF     │     │  Extract    │     │ Transform    │     │  acm_record   │     │  Display    │
└──────────┘     └─────────────┘     └──────────────┘     └───────────────┘     └─────────────┘
     │                  │                   │                    │                     │
     │                  ▼                   ▼                    ▼                     │
     │           ┌─────────────┐     ┌──────────────┐     ┌───────────────┐           │
     │           │  Markdown   │     │   Vector     │     │    Chat       │◄──────────┘
     │           │  Content    │     │  Embeddings  │     │   Context     │   Cell Click
     │           └─────────────┘     └──────────────┘     └───────────────┘
     │                                                           │
     └───────────────────────────────────────────────────────────┘
                              Citation Links
```

---

## 2. Component Architecture

### 2.1 Frontend Components

```
frontend/src/
├── app/
│   ├── layout.tsx              # Update: ACM-AI branding
│   ├── page.tsx                # Update: Landing page
│   └── sources/
│       └── [id]/
│           └── page.tsx        # Update: Add ACM view mode
│
├── components/
│   ├── acm/                    # ACM Components (Victorian BAR Support)
│   │   ├── ACMSpreadsheet.tsx  # AG Grid wrapper (47+ columns, 7 groups)
│   │   ├── ACMCellViewer.tsx   # PDF modal for cell citations
│   │   ├── ACMToolbar.tsx      # Search, filter, export controls
│   │   ├── RiskBadge.tsx       # Risk status cell renderer
│   │   ├── ACMContextToggle.tsx# Chat context switch
│   │   ├── SiteConfigForm.tsx  # NEW: Site configuration form
│   │   ├── ColumnVisibility.tsx# NEW: Column show/hide management
│   │   └── BARExportDialog.tsx # NEW: BAR Excel export options
│   │
│   ├── source/
│   │   └── ChatPanel.tsx       # Update: ACM context support
│   │
│   └── ui/                     # Existing shadcn components
│
├── lib/
│   ├── api/
│   │   └── acm.ts              # NEW: ACM API client
│   │
│   └── utils/
│       └── source-references.tsx # Update: Add ACM citation type
│
└── hooks/
    └── useACMRecords.ts        # NEW: React Query hook for ACM data
```

### 2.2 Backend Components

```
open_notebook/
├── domain/
│   └── acm.py                  # NEW: ACMRecord model + CRUD
│
├── transformations/
│   └── acm_extraction.py       # NEW: Docling → ACMRecord parser
│
└── migrations/
    └── acm_tables.surql        # NEW: SurrealDB schema

api/
└── routers/
    └── acm.py                  # NEW: ACM REST endpoints

commands/
└── acm_commands.py             # NEW: Background job handlers
```

---

## 3. Database Schema

### 3.1 SurrealDB Tables (Victorian BAR Format - Expanded)

> **Updated 2026-02-04:** Schema expanded from 20 to ~50 fields to support Victorian BAR format.
> See PRD Section 5.1 for complete field definitions.

```sql
-- ACM Record Table (Expanded for Victorian BAR)
DEFINE TABLE acm_record SCHEMAFULL;

-- Core identification
DEFINE FIELD source_id ON acm_record TYPE record<source>;

-- Organization Hierarchy (NEW - Victorian Government structure)
DEFINE FIELD department ON acm_record TYPE option<string>;  -- DJCS, DHHS, DET, etc.
DEFINE FIELD agency ON acm_record TYPE option<string>;
DEFINE FIELD sub_agency ON acm_record TYPE option<string>;
DEFINE FIELD site_name ON acm_record TYPE option<string>;

-- Building Information (Expanded - 15 fields)
DEFINE FIELD building_id ON acm_record TYPE string;
DEFINE FIELD building_name ON acm_record TYPE string;
DEFINE FIELD building_type ON acm_record TYPE option<string>;
DEFINE FIELD building_address ON acm_record TYPE option<string>;
DEFINE FIELD suburb ON acm_record TYPE option<string>;
DEFINE FIELD postcode ON acm_record TYPE option<string>;
DEFINE FIELD owned_or_leased ON acm_record TYPE option<string>;
DEFINE FIELD building_unique_id ON acm_record TYPE option<string>;
DEFINE FIELD frequency_of_use ON acm_record TYPE option<string>;
DEFINE FIELD public_access ON acm_record TYPE option<string>;
DEFINE FIELD date_of_inspection ON acm_record TYPE option<datetime>;
DEFINE FIELD building_year ON acm_record TYPE option<int>;
DEFINE FIELD building_size_m2 ON acm_record TYPE option<float>;
DEFINE FIELD number_of_levels ON acm_record TYPE option<int>;
DEFINE FIELD building_construction ON acm_record TYPE option<string>;
DEFINE FIELD roof_type ON acm_record TYPE option<string>;

-- Location (5 fields)
DEFINE FIELD area_type ON acm_record TYPE string;
DEFINE FIELD level ON acm_record TYPE option<string>;
DEFINE FIELD room_id ON acm_record TYPE option<string>;
DEFINE FIELD room_name ON acm_record TYPE option<string>;
DEFINE FIELD room_area ON acm_record TYPE option<float>;
DEFINE FIELD location ON acm_record TYPE string;

-- ACM Details (7 fields)
DEFINE FIELD product ON acm_record TYPE string;
DEFINE FIELD material_description ON acm_record TYPE option<string>;
DEFINE FIELD friable ON acm_record TYPE option<string>;
DEFINE FIELD acm_product_group ON acm_record TYPE option<string>;
DEFINE FIELD acm_product_type ON acm_record TYPE option<string>;
DEFINE FIELD nata_sample_number ON acm_record TYPE option<string>;
DEFINE FIELD sample_result ON acm_record TYPE option<string>;
DEFINE FIELD hygiene_company ON acm_record TYPE option<string>;

-- Assessment (4 fields)
DEFINE FIELD material_condition ON acm_record TYPE option<string>;
DEFINE FIELD disturbance_potential ON acm_record TYPE option<string>;
DEFINE FIELD extent ON acm_record TYPE option<string>;
DEFINE FIELD risk_status ON acm_record TYPE option<string>;

-- Documentation (5 fields)
DEFINE FIELD labelled ON acm_record TYPE option<string>;
DEFINE FIELD label_details ON acm_record TYPE option<string>;
DEFINE FIELD hygienist_recommendations ON acm_record TYPE option<string>;
DEFINE FIELD additional_comments ON acm_record TYPE option<string>;
DEFINE FIELD photo_reference ON acm_record TYPE option<string>;

-- Removal Tracking (7 fields - NEW)
DEFINE FIELD psb_acm_id ON acm_record TYPE option<string>;
DEFINE FIELD assumed_removed ON acm_record TYPE option<string>;
DEFINE FIELD date_of_removal ON acm_record TYPE option<datetime>;
DEFINE FIELD quantity_removed ON acm_record TYPE option<string>;
DEFINE FIELD removal_notification_no ON acm_record TYPE option<string>;
DEFINE FIELD epa_certificate_no ON acm_record TYPE option<string>;
DEFINE FIELD removal_comments ON acm_record TYPE option<string>;

-- Legacy NSW SAMP fields
DEFINE FIELD school_name ON acm_record TYPE option<string>;
DEFINE FIELD school_code ON acm_record TYPE option<string>;
DEFINE FIELD result ON acm_record TYPE option<string>;

-- Metadata
DEFINE FIELD page_number ON acm_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON acm_record TYPE option<float>;
DEFINE FIELD created_at ON acm_record TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON acm_record TYPE datetime DEFAULT time::now();

-- Indexes (expanded)
DEFINE INDEX acm_source ON acm_record FIELDS source_id;
DEFINE INDEX acm_building ON acm_record FIELDS building_id;
DEFINE INDEX acm_risk ON acm_record FIELDS risk_status;
DEFINE INDEX acm_department ON acm_record FIELDS department;
DEFINE INDEX acm_agency ON acm_record FIELDS agency;
DEFINE INDEX acm_suburb ON acm_record FIELDS suburb;
DEFINE INDEX acm_sample_result ON acm_record FIELDS sample_result;

-- Site Configuration Table (NEW)
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
DEFINE INDEX config_source ON site_config FIELDS source_id;
```

### 3.2 Relationships

```
┌─────────────┐         ┌─────────────┐
│   source    │ 1───────┤ acm_record  │ N
│   (PDF)     │         │             │
└─────────────┘         └─────────────┘
       │
       │ 1
       │
       ▼ N
┌─────────────┐
│    note     │
│  (insights) │
└─────────────┘
```

---

## 4. API Design

### 4.1 ACM Endpoints

```yaml
/api/acm/records:
  GET:
    description: List ACM records with filtering
    parameters:
      - source_id: string (required)
      - building_id: string (optional)
      - room_id: string (optional)
      - risk_status: enum [Low, Medium, High] (optional)
      - search: string (optional, full-text)
      - page: int (default: 1)
      - limit: int (default: 100)
    response:
      type: object
      properties:
        records: array[ACMRecord]
        total: int
        page: int
        pages: int

/api/acm/records/{id}:
  GET:
    description: Get single ACM record
    response:
      type: ACMRecord

/api/acm/extract:
  POST:
    description: Trigger ACM extraction for a source
    body:
      source_id: string (required)
    response:
      type: object
      properties:
        command_id: string
        status: string

/api/acm/export:
  GET:
    description: Export ACM records as CSV
    parameters:
      - source_id: string (required)
      - format: enum [csv, json] (default: csv)
    response:
      type: file (text/csv)

/api/acm/stats:
  GET:
    description: Summary statistics
    parameters:
      - source_id: string (optional)
    response:
      type: object
      properties:
        total_records: int
        by_risk_status: object
        by_building: array
```

### 4.2 API Response Types (Victorian BAR Format)

```typescript
// Full ACMRecord interface with Victorian BAR fields (~50 fields)
interface ACMRecord {
  id: string;
  source_id: string;

  // Organization Hierarchy
  department?: string;
  agency?: string;
  sub_agency?: string;
  site_name?: string;

  // Building Information
  building_id: string;
  building_name: string;
  building_type?: string;
  building_address?: string;
  suburb?: string;
  postcode?: string;
  owned_or_leased?: string;
  building_unique_id?: string;
  frequency_of_use?: string;
  public_access?: string;
  date_of_inspection?: string;
  building_year?: number;
  building_size_m2?: number;
  number_of_levels?: number;
  building_construction?: string;
  roof_type?: string;

  // Location
  area_type: 'Internal' | 'External';
  level?: string;
  room_id?: string;
  room_name?: string;
  room_area?: number;
  location: string;

  // ACM Details
  product: string;
  material_description?: string;
  friable?: 'Friable' | 'Non-friable';
  acm_product_group?: string;
  acm_product_type?: string;
  nata_sample_number?: string;
  sample_result?: 'Negative' | 'Positive' | 'Assumed positive' | 'Presumed Positive';
  hygiene_company?: string;

  // Assessment
  material_condition?: string;
  disturbance_potential?: 'Low' | 'Medium' | 'High';
  extent?: string;
  risk_status?: 'Low' | 'Medium' | 'High' | 'Very High';

  // Documentation
  labelled?: string;
  label_details?: string;
  hygienist_recommendations?: string;
  additional_comments?: string;
  photo_reference?: string;

  // Removal Tracking
  psb_acm_id?: string;
  assumed_removed?: string;
  date_of_removal?: string;
  quantity_removed?: string;
  removal_notification_no?: string;
  epa_certificate_no?: string;
  removal_comments?: string;

  // Legacy NSW SAMP
  school_name?: string;
  school_code?: string;
  result?: string;

  // Metadata
  page_number?: number;
  extraction_confidence?: number;
  created_at: string;
  updated_at: string;
}

interface ACMRecordList {
  records: ACMRecord[];
  total: number;
  page: number;
  pages: number;
}

interface ACMStats {
  total_records: number;
  by_risk_status: {
    Low: number;
    Medium: number;
    High: number;
    'Very High': number;
  };
  by_building: Array<{
    building_id: string;
    building_name: string;
    count: number;
  }>;
  by_department?: Array<{
    department: string;
    count: number;
  }>;
}

// NEW: Site Configuration interface
interface SiteConfig {
  id: string;
  source_id: string;
  department?: string;
  agency?: string;
  building_type?: string;
  owned_or_leased?: string;
  frequency_of_use?: string;
  public_access?: string;
  building_unique_id?: string;
  created_at: string;
  updated_at: string;
}

// NEW: BAR Export options
interface BARExportOptions {
  source_id: string;
  format: 'csv' | 'xlsx';
  include_reference_sheets?: boolean;
  column_order?: 'bar_standard' | 'custom';
  building_filter?: string[];
}
```

---

## 5. ACM Extraction Pipeline

> **Updated 2026-02-05:** Refactored to two-stage architecture (Extract → Interpret).
> See `docs/reference/extraction-pipeline.md` for complete specification.

### 5.1 Two-Stage Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ACM-AI Extraction Pipeline                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 0: PREFLIGHT                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────────────────────┐  │
│  │ PDF Upload  │───▶│ PDF Classifier│───▶│ Parser Router                 │  │
│  │             │    │ (digital/scan)│    │ (Docling + MinerU)            │  │
│  └─────────────┘    └──────────────┘    └────────────────────────────────┘  │
│                                                   │                          │
│  STAGE 1: EXTRACT (Verbatim with Provenance)      ▼                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────────┐ │ │
│  │ │   Docling    │   │    MinerU    │   │   Consultant Parser         │ │ │
│  │ │ (Text/Layout)│   │ (Tables→HTML)│   │   (Prensa/Greencap/etc)     │ │ │
│  │ └──────┬───────┘   └──────┬───────┘   └──────────────┬──────────────┘ │ │
│  │        │                  │                          │                 │ │
│  │        └──────────────────┼──────────────────────────┘                 │ │
│  │                           ▼                                            │ │
│  │              ┌─────────────────────────────┐                           │ │
│  │              │    Raw Extraction JSON      │                           │ │
│  │              │    (verbatim + provenance)  │                           │ │
│  │              └─────────────────────────────┘                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 2: INTERPRET (Normalize to BAR Schema)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────────┐ │ │
│  │ │ Field Mapper │   │ Normalizer   │   │   Taxonomy Classifier       │ │ │
│  │ │ (PDF → BAR)  │   │ (Enums)      │   │   (Product Group/Type)      │ │ │
│  │ └──────────────┘   └──────────────┘   └─────────────────────────────┘ │ │
│  │         │                  │                          │                │ │
│  │         └──────────────────┼──────────────────────────┘                │ │
│  │                            ▼                                           │ │
│  │ ┌─────────────────┐   ┌─────────────────────────────┐                  │ │
│  │ │ Business Rules  │   │   Schema Validator          │                  │ │
│  │ │ (Negative→N/A)  │   │   (BAR Compliance)          │                  │ │
│  │ └─────────────────┘   └─────────────────────────────┘                  │ │
│  │                            │                                           │ │
│  │                            ▼                                           │ │
│  │              ┌─────────────────────────────┐                           │ │
│  │              │   BAR-Compliant ACMRecord   │                           │ │
│  │              │   (validated, normalized)   │                           │ │
│  │              └─────────────────────────────┘                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  OUTPUT: Store + Index                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────────────┐  │
│  │  SurrealDB   │   │   Vector     │   │       Excel/CSV Export          │  │
│  │  (Records)   │   │  Embeddings  │   │       (BAR Format)              │  │
│  └──────────────┘   └──────────────┘   └─────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.1.1 Stage 1: EXTRACT

**Purpose:** Extract verbatim values with full provenance tracking.

**Key Principle:** Do NOT normalize at this stage - keep original consultant wording.

**Output Schema:**
```python
@dataclass
class RawExtraction:
    document_meta: DocumentMeta      # Site info from cover/header
    items: list[RawACMItem]          # Raw table rows
    extraction_timestamp: datetime
    parser_version: str

@dataclass
class SourceLocation:
    page: int
    table_id: Optional[int]
    row: Optional[int]
    confidence: float
```

### 5.1.2 Stage 2: INTERPRET

**Purpose:** Transform raw extraction to BAR-compliant records.

**Processing Steps:**
1. **Field Mapping:** Consultant columns → BAR columns
2. **Value Normalization:** Synonyms → Controlled enums (see PRD 5.5)
3. **Taxonomy Classification:** Item description → Product Group/Type (see PRD 5.6)
4. **Business Rules:** Apply BAR rules (e.g., Negative → N/A for Condition)
5. **Validation:** Validate against BAR schema

### 5.1.3 MinerU Integration

MinerU is used for table extraction due to superior handling of:
- Complex merged cells
- Multi-page table continuity
- HTML structure preservation

```python
from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter

class MineruTableExtractor:
    def extract_tables(self, pdf_path: str) -> list[dict]:
        pipe = UNIPipe(pdf_path, DiskReaderWriter())
        content = pipe.pipe_parse()
        tables = []
        for page_num, page_content in enumerate(content.pages):
            for element in page_content.elements:
                if element.type == "table":
                    tables.append({
                        "page": page_num + 1,
                        "html": element.html,
                        "bbox": element.bbox
                    })
        return tables
```

### 5.2 Generic Configurable Parser Architecture

> **Updated 2026-02-08:** Course correction -- replaced ConsultantParser ABC + registry pattern
> with a single GenericParser driven by `FieldSchemaConfig`. See
> `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md`.

**Design Rationale:** Instead of building a separate parser class per consultant (Prensa,
Greencap, etc.), a single `GenericParser` consumes a declarative field configuration that
describes column mappings, enums, and business rules. New consultant formats are supported
by adding/editing JSON config files rather than writing new Python classes.

#### 5.2.1 Config Source-of-Truth Flow

```
BAR Excel Template (authoritative field list)
        │
        ▼
JSON Config Files  (checked into repo: config/field_schemas/*.json)
        │
        ▼
SurrealDB `field_schema` table  (loaded at API startup / on-demand)
        │
        ├──▶ GenericParser        — loads config at extraction time
        ├──▶ AG Grid columns      — reads config for column definitions & groups
        └──▶ Excel / CSV export   — reads config for column order & display names
```

#### 5.2.2 Pydantic Configuration Models

```python
from pydantic import BaseModel
from typing import Optional

class FieldDef(BaseModel):
    """Single field definition derived from the BAR Excel template."""
    internal_name: str          # e.g. "material_condition"
    display_name: str           # e.g. "Material Condition"
    excel_column: str           # e.g. "AH" (BAR column letter)
    col_index: int              # 0-based position in BAR spreadsheet
    field_type: str             # "string" | "int" | "float" | "datetime" | "enum"
    required: bool              # True if BAR marks this as mandatory
    active: bool                # False to soft-hide without schema migration
    enum_name: Optional[str]    # Key into FieldSchemaConfig.enums (if field_type == "enum")
    group: str                  # UI column group: "Organization", "Building", "Location", etc.

class FieldSchemaConfig(BaseModel):
    """Complete field schema configuration loaded from JSON / SurrealDB."""
    fields: list[FieldDef]
    enums: dict[str, list[str]]          # e.g. {"risk_status": ["Low","Medium","High","Very High"]}
    business_rules: dict[str, str]       # e.g. {"negative_result_clears_condition": "true"}
    version: str                         # Semantic version of this config
    source_template: str                 # e.g. "Victorian BAR v4.2"
```

#### 5.2.3 GenericParser

```python
class GenericParser:
    """Single parser that handles any consultant format via FieldSchemaConfig."""

    def __init__(self, config: FieldSchemaConfig):
        self.config = config
        self._field_map = {f.internal_name: f for f in config.fields}

    def extract_items(self, tables: list[dict]) -> list[RawACMItem]:
        """Extract raw ACM items using config-driven column mapping."""
        ...

    def get_column_mapping(self) -> dict[str, str]:
        """Return mapping of display_name -> internal_name from config."""
        return {f.display_name: f.internal_name for f in self.config.fields if f.active}

    def get_export_columns(self) -> list[tuple[str, str]]:
        """Return (internal_name, excel_column) pairs in BAR column order."""
        return [
            (f.internal_name, f.excel_column)
            for f in sorted(self.config.fields, key=lambda f: f.col_index)
            if f.active
        ]
```

### 5.3 Unified Field Configuration Schema

> **Updated 2026-02-08:** Replaced hardcoded consultant pattern dictionaries with the
> unified `FieldSchemaConfig` described in Section 5.2. Consultant-specific header lists
> and regex patterns are no longer maintained in Python source; they are expressed
> declaratively in JSON config files.

#### 5.3.1 Configuration File Layout

```
config/field_schemas/
├── bar_v4.json            # Victorian BAR v4 template (default)
└── README.md              # How to derive a new config from a BAR Excel file
```

Each JSON file conforms to the `FieldSchemaConfig` Pydantic model (Section 5.2.2).

#### 5.3.2 SurrealDB `field_schema` Table

```sql
DEFINE TABLE field_schema SCHEMAFULL;
DEFINE FIELD version        ON field_schema TYPE string;
DEFINE FIELD source_template ON field_schema TYPE string;
DEFINE FIELD fields          ON field_schema TYPE array;       -- array of FieldDef objects
DEFINE FIELD enums           ON field_schema TYPE object;      -- enum_name -> values
DEFINE FIELD business_rules  ON field_schema TYPE object;      -- rule_name -> value
DEFINE FIELD active          ON field_schema TYPE bool DEFAULT true;
DEFINE FIELD created_at      ON field_schema TYPE datetime DEFAULT time::now();
DEFINE INDEX schema_version  ON field_schema FIELDS version;
```

#### 5.3.3 Config Consumers

| Consumer | How It Uses Config |
|----------|-------------------|
| **GenericParser** | Loads active `FieldSchemaConfig` at extraction time to map PDF columns to internal field names |
| **AG Grid (frontend)** | Fetches `/api/acm/field-schema` to build `ColDef[]` dynamically (field groups, display names, visibility) |
| **Excel/CSV Export** | Reads `col_index` and `excel_column` to produce BAR-ordered output with correct column headers |
| **Validation** | Uses `enums` and `business_rules` to validate and normalize extracted values |

#### 5.3.4 Regex Helpers (Retained)

The following structural patterns are still used by `GenericParser` for detecting building
and room header rows within extracted table data. They are not consultant-specific.

```python
# Building header pattern
BUILDING_PATTERN = r"^([A-Z]\d+[A-Z]?)\s*[-\u2013]\s*(.+?)(?:\s*[-\u2013]\s*(\d{4}))?$"
# Example: "B00A - Other-Dse Admin - 1924"

# Room header pattern
ROOM_PATTERN = r"^([A-Z]\d+[A-Z]?-R\d+)\s*[-\u2013]\s*(.+?)(?:\s*[-\u2013]\s*([\d.]+)\s*m\u00b2)?$"
# Example: "B00A-R0001 - External Movement"
```

### 5.4 Pipeline Observability

The extraction pipeline emits real-time events via Server-Sent Events (SSE) to provide full visibility into the 7-stage extraction process.

#### Event Emitter Architecture

```python
# api/extraction_events.py
class PipelineEventEmitter:
    """Manages SSE event broadcasting for a single extraction run."""

    def __init__(self, run_id: str, source_id: str):
        self.run_id = run_id
        self.source_id = source_id
        self._subscribers: list[asyncio.Queue] = []

    async def emit_stage_entered(self, stage_id: str, stage_name: str):
        """Broadcast stage transition event."""

    async def emit_stage_progress(self, stage_id: str, progress: float, message: str):
        """Broadcast progress update within a stage."""

    async def emit_stage_thinking(self, stage_id: str, thought: str, tool_selected: str):
        """Broadcast agent reasoning/decision event."""
```

#### Event Schemas

| Event Type | Payload Fields | When Emitted |
|------------|----------------|--------------|
| `pipeline:started` | run_id, source_id, stages[], total_stages | Pipeline run begins |
| `stage:entered` | run_id, stage_id, stage_name, entered_at, sub_step | Stage begins execution |
| `stage:progress` | run_id, stage_id, progress, message, records_so_far | Progress update within stage |
| `stage:thinking` | run_id, stage_id, thought, tool_selected, confidence | Agent reasoning/decision |
| `stage:completed` | run_id, stage_id, completed_at, duration_ms, records_extracted, summary | Stage finishes successfully |
| `stage:failed` | run_id, stage_id, failed_at, error, error_code, retry_available | Stage fails |
| `stage:skipped` | run_id, stage_id, reason | Stage intentionally skipped |
| `pipeline:completed` | run_id, source_id, total_duration_ms, total_records, confidence_distribution | All stages done |
| `pipeline:failed` | run_id, source_id, failed_at, error, last_successful_stage | Pipeline halted on error |

**SSE Endpoint:**
```
GET /api/extraction/{source_id}/events
Accept: text/event-stream
```

#### Frontend Integration

**Hook:** `usePipelineStatus(sourceId)`
- Opens SSE connection to event stream
- Reduces events into `PipelineRunState`
- Exposes current stage, progress, and full stage history
- Fallback to polling if SSE unavailable

**Components:**
- `PipelineVisualization` - Main container with 7-stage stepper
- `PipelineStage` - Individual stage row with status, progress, duration
- `StageDetail` - Expandable panel showing sub-steps and thinking steps
- `ThinkingSteps` - Agent reasoning log with timestamps

See `docs/ag-ui-pipeline-spec.md` for complete specification.

---

## 6. Chat Architecture

### 6.1 Overview

ACM-AI implements a supervisor agent pattern where a single orchestrating agent has direct access to all tools (both ACM and document search), rather than delegating through sub-agents. This architecture:

- Eliminates agent-to-agent communication overhead for same-process tools
- Provides real-time streaming via AG-UI protocol / CopilotKit
- Supports dynamic ACM context toggle for domain-specific queries
- Integrates with the frontend via SSE and custom tool result renderers

### 6.2 Supervisor Agent Pattern

The supervisor agent (`open_notebook/graphs/supervisor_agent.py`) uses a **ReAct loop** where it:

1. Receives user message
2. Decides which tools to invoke (ACM tools, search tools, or both)
3. Executes tools directly (no sub-agent delegation)
4. Synthesizes results into coherent response

**Direct Tool Access:**
```python
def _get_supervisor_tools(include_acm: bool = True):
    """Get the tools available to the supervisor."""
    tools = get_search_tools()  # Document search, note retrieval
    if include_acm:
        tools = get_acm_tools() + tools  # ACM record queries, building search
    return tools
```

**ReAct Loop Implementation:**
```python
def call_supervisor(state: SupervisorState, config: RunnableConfig) -> dict:
    # Set tool context for scoping (source_id, notebook_id)
    set_tool_context(source_id=source_id, notebook_id=notebook_id)

    # Get tools based on ACM context toggle
    tools = _get_supervisor_tools(include_acm=include_acm)

    # Build system prompt with context
    system_prompt = Prompter(prompt_template="supervisor").render(data=prompt_data)

    # Provision model with tools
    model = await provision_langchain_model_with_tools(payload, model_id, "chat", tools=tools)

    # Invoke and return AI message (may contain tool calls)
    return {"messages": [ai_message]}
```

The supervisor graph uses LangGraph's conditional edges to loop back after tool execution:
```
START → supervisor → (has tool calls?) → tools → supervisor → END
```

### 6.3 AG-UI Protocol Integration

AG-UI (Agent-User Interaction) protocol provides a standard for agents to communicate state, actions, and reasoning to frontend UIs. ACM-AI uses the `ag-ui-langgraph` adapter to expose the supervisor graph as an AG-UI compatible endpoint.

**Adapter Implementation:**
```python
# api/routers/agui_chat.py
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint

def register_agui_endpoints(app):
    agent = LangGraphAgent(
        name="supervisor",
        graph=supervisor_graph,
        description="ACM-AI supervisor agent for asbestos compliance queries"
    )
    add_langgraph_fastapi_endpoint(app, agent, "/api/agui/chat")
```

**SSE Endpoint:** `/api/agui/chat`
- Accepts `RunAgentInput` via POST
- Returns AG-UI SSE event stream
- Automatic LangGraph → AG-UI event mapping:
  - `ToolCallStart`, `ToolCallArgs`, `ToolCallEnd`, `ToolCallResult`
  - `TextMessageStart`, `TextMessageContent`, `TextMessageEnd`
  - State snapshots and deltas

**Event Mapping:**
LangGraph emits low-level node/edge events; the AG-UI adapter transforms these into standardized AG-UI events that CopilotKit can consume without custom parsing.

### 6.4 CopilotKit Frontend

CopilotKit is a React framework that implements the AG-UI protocol client-side, providing hooks and components for agent interaction.

**Provider Setup:**
```tsx
// SmartChatProvider wraps the chat component
<SmartChatProvider sourceId={sourceId} notebookId={notebookId} hasAcmData={hasAcmData}>
  <CopilotChat
    labels={{ title: 'Smart Chat' }}
    AssistantMessage={ACMAssistantMessage}
    Input={SmartChatInput}
    makeSystemMessage={(contextString) => /* build prompt with ACM context */ }
  />
</SmartChatProvider>
```

**Custom Hooks:**
- `useSmartChat({ sourceId, notebookId, hasAcmData })` - Manages ACM context toggle state
- `useSmartChatScope()` - Accesses current source/notebook scope from context

**Custom Renderers:**
- `ACMAssistantMessage` - Custom message renderer for ACM-specific formatting
- `ToolResultRenderers` - Renders tool invocation results (e.g., ACM record tables)
- `SmartChatInput` - Input component with ACM context toggle badge

**Streaming Support:**
CopilotKit automatically handles SSE streaming from the `/api/agui/chat` endpoint, updating the UI in real-time as the agent:
- Invokes tools
- Receives results
- Generates response text

### 6.5 ACM Context Management

ACM context is a **dynamic toggle** that controls whether the supervisor agent has access to ACM-specific tools (record queries, building search, compliance checks).

**Toggle Implementation:**
```tsx
// SmartChatPanel.tsx
const { includeAcmContext, setIncludeAcmContext } = useSmartChat({ sourceId, hasAcmData });

// Badge UI
<Badge onClick={() => setIncludeAcmContext(!includeAcmContext)}>
  <TableProperties /> ACM Data {includeAcmContext ? 'ON' : 'OFF'}
</Badge>
```

**Context Injection:**
When ACM context is enabled:
1. **Tool Availability:** `get_acm_tools()` are included in the supervisor's tool list
2. **System Prompt:** Modified to indicate ACM context is active:
   ```
   "ACM context is enabled - use ACM tools for structured data queries."
   ```
3. **Tool Scoping:** `set_tool_context(source_id, notebook_id)` ensures ACM tools only query relevant records

When disabled:
- Only document search and note retrieval tools available
- System prompt focuses on general document content
- ACM-specific queries return "ACM context is disabled" message

**Use Cases:**
- **ACM ON:** "Show all asbestos in Building B003", "What's the risk status of ceiling tiles?"
- **ACM OFF:** "Summarize the methodology section", "What does page 5 say about surveys?"

---

## 7. Frontend Integration

### 6.1 AG Grid Configuration (Victorian BAR Format - 47+ Columns)

> **Updated 2026-02-04:** Columns organized into 7 logical groups for visibility management.
> See PRD Section 4.3 for full column definitions.

```typescript
// frontend/src/components/acm/ACMSpreadsheet.tsx

import { AgGridReact } from 'ag-grid-react';
import { ColDef, ColGroupDef, GridApi } from 'ag-grid-community';

// Column groups for Victorian BAR format
const columnGroupDefs: (ColDef | ColGroupDef)[] = [
  // Group 1: Organization
  {
    headerName: 'Organization',
    children: [
      { field: 'department', headerName: 'Department', width: 100, hide: true },
      { field: 'agency', headerName: 'Agency', width: 150, hide: true },
      { field: 'sub_agency', headerName: 'Sub Agency', width: 150, hide: true },
      { field: 'site_name', headerName: 'Site Name', width: 150, hide: true },
    ]
  },
  // Group 2: Building
  {
    headerName: 'Building',
    children: [
      { field: 'building_name', headerName: 'Building', width: 150, rowGroup: true },
      { field: 'building_type', headerName: 'Type', width: 100, hide: true },
      { field: 'building_address', headerName: 'Address', width: 180, hide: true },
      { field: 'suburb', headerName: 'Suburb', width: 100, hide: true },
      { field: 'postcode', headerName: 'Postcode', width: 80, hide: true },
      // ... additional building fields (see PRD 4.3)
    ]
  },
  // Group 3: Location
  {
    headerName: 'Location',
    children: [
      { field: 'area_type', headerName: 'Int/Ext', width: 80 },
      { field: 'level', headerName: 'Level', width: 80 },
      { field: 'room_name', headerName: 'Room/Area', width: 150, rowGroup: true },
      { field: 'location', headerName: 'Location in Room', width: 150 },
    ]
  },
  // Group 4: ACM Details
  {
    headerName: 'ACM Details',
    children: [
      { field: 'product', headerName: 'Item/ACM Name', width: 150 },
      { field: 'friable', headerName: 'Friability', width: 100, filter: 'agSetColumnFilter' },
      { field: 'acm_product_group', headerName: 'Product Group', width: 120, hide: true },
      { field: 'acm_product_type', headerName: 'Product Type', width: 120, hide: true },
      { field: 'nata_sample_number', headerName: 'Sample No.', width: 120 },
      { field: 'sample_result', headerName: 'Sample Result', width: 100, filter: 'agSetColumnFilter' },
    ]
  },
  // Group 5: Assessment
  {
    headerName: 'Assessment',
    children: [
      { field: 'material_condition', headerName: 'Condition', width: 100, filter: 'agSetColumnFilter' },
      { field: 'disturbance_potential', headerName: 'Disturb. Pot.', width: 100 },
      { field: 'extent', headerName: 'Quantity', width: 100 },
      { field: 'risk_status', headerName: 'Risk', width: 100, cellRenderer: 'riskBadgeRenderer', filter: 'agSetColumnFilter' },
    ]
  },
  // Group 6: Documentation (mostly hidden by default)
  {
    headerName: 'Documentation',
    children: [
      { field: 'labelled', headerName: 'Labelled', width: 80, hide: true },
      { field: 'hygienist_recommendations', headerName: 'Recommendations', width: 200, hide: true },
      { field: 'additional_comments', headerName: 'Comments', width: 200, hide: true },
      { field: 'photo_reference', headerName: 'Photo Ref', width: 100, hide: true },
    ]
  },
  // Group 7: Removal Tracking (hidden by default)
  {
    headerName: 'Removal',
    children: [
      { field: 'assumed_removed', headerName: 'Removed?', width: 80, hide: true },
      { field: 'date_of_removal', headerName: 'Removal Date', width: 120, hide: true },
      { field: 'removal_notification_no', headerName: 'Removal Notif.', width: 120, hide: true },
    ]
  },
];

// Column visibility presets
const COLUMN_PRESETS = {
  essential: ['building_name', 'room_name', 'product', 'friable', 'material_condition', 'risk_status', 'sample_result'],
  full_bar: null, // Show all columns
  assessment_focus: ['building_name', 'room_name', 'product', 'material_condition', 'disturbance_potential', 'risk_status', 'hygienist_recommendations'],
  removal_tracking: ['building_name', 'room_name', 'product', 'assumed_removed', 'date_of_removal', 'quantity_removed', 'removal_notification_no'],
};

const defaultColDef: ColDef = {
  sortable: true,
  resizable: true,
  cellClass: 'cursor-pointer',
  filter: 'agTextColumnFilter',
};

const gridOptions = {
  rowGroupPanelShow: 'always',
  groupDefaultExpanded: 1,
  animateRows: true,
  enableCellTextSelection: true,
  sideBar: {
    toolPanels: ['columns', 'filters'],
    defaultToolPanel: '',
  },
};
```

### 6.2 Citation System Extension

```typescript
// frontend/src/lib/utils/source-references.tsx

// Existing patterns
const SOURCE_REFERENCE_PATTERN = /\[source:([^\]]+)\]/g;
const NOTE_REFERENCE_PATTERN = /\[note:([^\]]+)\]/g;
const INSIGHT_REFERENCE_PATTERN = /\[source_insight:([^\]]+)\]/g;

// NEW: ACM citation pattern
const ACM_REFERENCE_PATTERN = /\[acm:([^:]+):([^\]]+)\]/g;
// Format: [acm:record_id:field_name]
// Example: [acm:acm_record:abc123:risk_status]

interface ACMReference {
  type: 'acm';
  recordId: string;
  fieldName: string;
}

function parseACMReferences(text: string): ACMReference[] {
  const matches = [...text.matchAll(ACM_REFERENCE_PATTERN)];
  return matches.map(match => ({
    type: 'acm',
    recordId: match[1],
    fieldName: match[2]
  }));
}
```

---

## 7. Chat Context Integration

### 7.1 ACM Context Builder

```python
# api/routers/source_chat.py

def build_acm_context(source_id: str, max_tokens: int = 4000) -> str:
    """Build ACM context for chat."""
    records = ACMRecord.list_by_source(source_id)

    if not records:
        return ""

    context = "## ACM Register Data\n\n"
    context += "| Building | Room | Product | Material | Risk |\n"
    context += "|----------|------|---------|----------|------|\n"

    for record in records[:100]:  # Limit rows
        context += f"| {record.building_name} | {record.room_name or '-'} | "
        context += f"{record.product} | {record.material_description} | "
        context += f"{record.risk_status or '-'} |\n"

    # Add citation instructions
    context += "\n\nWhen referencing specific ACM data, use the format "
    context += "[acm:record_id:field_name] to cite the source.\n"

    return context
```

### 7.2 System Prompt Enhancement

```python
ACM_SYSTEM_PROMPT = """
You are an ACM-AI assistant helping users understand Asbestos Containing Material
data from School Asbestos Management Plans (SAMPs).

When answering questions about ACM data:
1. Reference specific records using [acm:record_id:field_name] format
2. Explain ACM terminology when asked (friable, non-friable, risk levels)
3. Cite page numbers when available
4. Warn about high-risk items prominently
5. Follow NSW Department of Education asbestos management guidelines

Key terminology:
- Friable: ACM that can be crumbled by hand pressure (higher risk)
- Non-Friable: ACM with fibers bound in matrix (lower risk when intact)
- Risk Status: Low/Medium/High based on condition and accessibility
"""
```

---

## 8. Security Considerations

### 8.1 Data Privacy

| Concern | Mitigation |
|---------|------------|
| Document confidentiality | All processing local, no external API calls for extraction |
| LLM data exposure | User controls LLM provider (local Ollama or cloud) |
| Database access | SurrealDB runs locally, no external exposure |

### 8.2 Input Validation

```python
# api/routers/acm.py

from pydantic import BaseModel, validator

class ACMExtractRequest(BaseModel):
    source_id: str

    @validator('source_id')
    def validate_source_id(cls, v):
        # Validate format and existence
        if not v.startswith('source:'):
            raise ValueError('Invalid source ID format')
        return v

class ACMFilterParams(BaseModel):
    source_id: str
    building_id: Optional[str] = None
    room_id: Optional[str] = None
    risk_status: Optional[Literal['Low', 'Medium', 'High']] = None
    page: int = 1
    limit: int = 100

    @validator('limit')
    def validate_limit(cls, v):
        return min(max(v, 1), 1000)  # Cap at 1000
```

---

## 9. Performance Considerations

### 9.1 Optimization Strategies

| Area | Strategy |
|------|----------|
| Large PDFs | Async processing via background worker |
| Many records | AG Grid virtual scrolling (default) |
| PDF viewing | Page-level lazy loading |
| Search | SurrealDB indexes + quick filter in AG Grid |
| Chat context | Token limiting + record sampling |

### 9.2 Caching

```typescript
// frontend/src/hooks/useACMRecords.ts

import { useQuery } from '@tanstack/react-query';

export function useACMRecords(sourceId: string, filters?: ACMFilters) {
  return useQuery({
    queryKey: ['acm-records', sourceId, filters],
    queryFn: () => fetchACMRecords(sourceId, filters),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!sourceId
  });
}
```

---

## 10. Technology Decisions

### 10.1 Why AG Grid?

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| React Table | Missing built-in grouping, filtering UI |
| Handsontable | Less performant with large datasets |
| SheetJS | Spreadsheet engine, not display component |
| Custom implementation | Too much effort for feature set needed |

**AG Grid advantages:**
- Built-in row grouping
- Virtual scrolling (1000+ rows)
- Enterprise-grade filtering
- Cell renderers for custom display
- CSV export built-in

### 10.2 Why Extend Citations?

The existing citation system is well-designed and proven:
- Already handles multiple reference types
- Parsing and rendering infrastructure exists
- Users familiar with citation clicks
- Modal display system reusable

Adding `[acm:...]` references is minimal effort.

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/unit/test_acm_extraction.py

def test_detect_acm_table():
    """Test ACM table detection from Docling output."""

def test_parse_building_header():
    """Test building header regex parsing."""

def test_parse_room_header():
    """Test room header regex parsing."""

def test_create_acm_record():
    """Test ACMRecord creation from table row."""
```

### 11.2 Integration Tests

```python
# tests/integration/test_acm_api.py

def test_extract_from_sample_pdf():
    """Test full extraction pipeline on sample PDF."""

def test_list_records_with_filters():
    """Test record listing with various filters."""

def test_csv_export():
    """Test CSV export functionality."""
```

### 11.3 E2E Tests

```typescript
// frontend/e2e/acm-spreadsheet.spec.ts

test('displays ACM data in grid', async ({ page }) => {
  // Upload PDF
  // Wait for extraction
  // Verify grid renders
  // Test filtering
  // Test cell click → PDF modal
});
```

---

## 12. Deployment Notes

### 12.1 Dependencies to Add

```bash
# Frontend
npm install ag-grid-react ag-grid-community react-pdf

# Backend (if not already present)
# Docling already integrated via content-core
```

### 12.2 Environment Variables

No new environment variables required - leverages existing configuration.

### 12.3 Database Migration

The `acm_record` table is created by migration #10 (`migrations/10.surrealql`).
Migrations run automatically on API startup, or manually via:

```bash
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import asyncio; from open_notebook.database.async_migrate import AsyncMigrationManager; asyncio.run(AsyncMigrationManager().run_migration_up())"
```

---

## 13. Frontend Design System Architecture

> **Added:** 2026-02-08 (UX Audit &amp; Enterprise Readiness Initiative - Lane B)
> **Spec References:** `docs/design-system.md`, `docs/ag-ui-pipeline-spec.md`, `docs/state-loading-spec.md`

### 13.1 VAEA Design Token System

```
CSS Custom Properties (:root / .dark)
    └── Tailwind 4 @theme inline
        └── Component-level tokens (shadcn/ui variants)
            └── AG Grid theme overrides
```

**Architecture:**
- **Color Space:** OKLCH for perceptual uniformity across light/dark modes
- **Token Layers:** Brand → Semantic → Component (3-tier cascade)
- **Dark Mode:** Class-based toggle (`.dark` class on `<html>`) via `next-themes`
- **Brand Colors:** VAEA Teal primary (#0D7377), Coral accent (#EB787A), Navy (#1B2B4B)
- **Reference:** `docs/design-system.md`

**Token Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│  Brand Layer (VAEA Palette)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ --vaea-teal: oklch(0.52 0.09 185)                       ││
│  │ --vaea-coral: oklch(0.65 0.14 15)                       ││
│  │ --vaea-navy: oklch(0.27 0.04 260)                       ││
│  └──────────────────────┬──────────────────────────────────┘│
│                         ▼                                    │
│  Semantic Layer (Role-based)                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ --primary: var(--vaea-teal)                              ││
│  │ --accent: var(--vaea-coral)                              ││
│  │ --destructive: oklch(0.55 0.2 25)                       ││
│  │ --background, --foreground, --muted, --border           ││
│  └──────────────────────┬──────────────────────────────────┘│
│                         ▼                                    │
│  Component Layer (shadcn/ui + AG Grid)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Button, Card, Dialog → use semantic tokens               ││
│  │ AG Grid → .ag-theme-custom uses --ag-* mapped tokens    ││
│  │ Risk badges → use --risk-low/medium/high/very-high      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 13.2 AG-UI Protocol & CopilotKit Integration

```
Browser ──SSE──▶ FastAPI ──Events──▶ LangGraph Nodes
                    │
    PipelineEventEmitter (asyncio.Queue per subscriber)
```

**Status:** ✅ **Phase 1 (implemented)**
- **Live Endpoint:** `/api/agui/chat` (AG-UI protocol via `ag-ui-langgraph` adapter)
- **Frontend:** `CopilotProvider`, `SmartChatPanel`, custom tool result renderers
- **Backend:** `supervisor_agent.py` exposed via `LangGraphAgent` adapter

**Transport Strategy:**
- **Phase 1:** SSE (Server-Sent Events) for real-time extraction progress and chat streaming
- **Fallback:** 3-second polling via existing `useExtractionStatus` hook

**State Management:**
- Zustand `pipeline-progress-store` tracks multi-stage extraction
- 7-stage pipeline: Upload → Parse → Extract → Interpret → Validate → Store → Index
- Each stage has: status (pending/active/complete/error), progress %, timing

**Event Schema:**
```typescript
interface PipelineEvent {
  type: 'stage_start' | 'stage_progress' | 'stage_complete' | 'stage_error';
  stage: string;
  progress?: number;
  message?: string;
  timestamp: string;
}
```

**Reference:** `docs/ag-ui-pipeline-spec.md`

### 13.3 State Management Extensions

Three new Zustand stores extend the existing state management architecture:

```
┌──────────────────────────────────────────────────────────┐
│  Existing Stores                                          │
│  ├── source-store (React Query)                          │
│  ├── chat-store (Zustand)                                │
│  └── notebook-store (Zustand)                            │
│                                                           │
│  New Stores (E14)                                        │
│  ├── pipeline-progress-store  ← SSE events               │
│  │   └── Multi-stage extraction tracking                 │
│  │   └── Per-source progress state                       │
│  │                                                        │
│  ├── notification-store  ← Background job alerts          │
│  │   └── Persistent notification queue                    │
│  │   └── Toast integration (Sonner)                      │
│  │   └── Read/unread state                               │
│  │                                                        │
│  └── feature-flags-store  ← Dual-persona mode            │
│      └── Simple vs Advanced UI toggle                    │
│      └── Per-user preference persistence                 │
│      └── Feature visibility rules                        │
└──────────────────────────────────────────────────────────┘
```

**Store Patterns:**
- All stores use Zustand with `persist` middleware for local storage
- Pipeline store uses `subscribeWithSelector` for granular re-renders
- Notification store integrates with Sonner toast library
- Feature flags drive conditional rendering of advanced features

**Reference:** `docs/state-loading-spec.md`

### 13.4 Navigation Architecture

```
┌──────────────────────────────────────────────────────────┐
│  AppSidebar                                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │ VAEA Logo + Brand Header                            │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ [Upload Document] CTA Button                        │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ WORKSPACE                                           │  │
│  │  ├── Dashboard (/)                                  │  │
│  │  ├── Documents (/documents)                         │  │
│  │  ├── ACM Register (/sources/[id]/acm)              │  │
│  │  └── Search (/search)                               │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ CONFIGURE                                           │  │
│  │  ├── Extraction (/settings/extraction)              │  │
│  │  ├── AI Models (/settings/models)                   │  │
│  │  ├── Parsers (/settings/parsers)                    │  │
│  │  ├── Processing (/settings/processing)              │  │
│  │  └── General (/settings/general)                    │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Footer: Theme Toggle | CoralShades | Sign Out      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Hidden Features (preserved, no nav entry):**
- Podcasts (`/podcasts`) - accessible via direct URL only
- Transformations (`/transformations`) - accessible via direct URL only
- Notebooks (`/notebooks`) - accessible via direct URL only

**Reference:** `docs/navigation-cleanup-spec.md`

### 13.5 Smart Chat Components

Smart Chat provides an AI-powered interface for querying ACM data and document content using the supervisor agent architecture (Section 6).

**Component Hierarchy:**
```
<SmartChatProvider>                     // Context provider
  <SmartChatPanel>                      // Main container
    <CopilotChat>                       // CopilotKit chat component
      <ACMAssistantMessage />           // Custom message renderer
      <SmartChatInput />                // Input with ACM toggle
      <ToolResultRenderers />           // Tool invocation renderers
```

**Key Components:**

| Component | File | Purpose |
|-----------|------|---------|
| `SmartChatProvider` | `frontend/src/components/chat/SmartChatProvider.tsx` | Provides source/notebook scope context |
| `SmartChatPanel` | `frontend/src/components/chat/SmartChatPanel.tsx` | Main container with CopilotKit integration |
| `ACMAssistantMessage` | `frontend/src/components/chat/ACMAssistantMessage.tsx` | Custom renderer for ACM-formatted responses |
| `SmartChatInput` | `frontend/src/components/chat/SmartChatInput.tsx` | Input with ACM context toggle badge |
| `ToolResultRenderers` | `frontend/src/components/chat/ToolResultRenderers.tsx` | Renders ACM tool invocation results (tables, charts) |
| `ACMContextToggle` | `frontend/src/components/acm/ACMContextToggle.tsx` | Standalone ACM context toggle component |

**Hooks:**

| Hook | File | Purpose |
|------|------|---------|
| `useSmartChat` | `frontend/src/lib/hooks/useSmartChat.ts` | Manages ACM context toggle state |
| `useSmartChatScope` | `frontend/src/components/chat/SmartChatProvider.tsx` | Accesses current source/notebook scope |

**Features:**
- Real-time streaming via SSE from `/api/agui/chat`
- Dynamic ACM context toggle (enables/disables ACM-specific tools)
- Custom tool result renderers for ACM record tables
- System prompt injection with source/notebook context
- Indicator badge when ACM data is included in context

### 13.6 Pipeline Visualization Components

Pipeline visualization provides real-time feedback during the 7-stage ACM extraction process.

**Component Hierarchy:**
```
<PipelineVisualization>                 // Main container
  <ProgressIndicator />                 // Overall progress bar
  <PipelineStage stage="-1">           // Document Structure
    <StageHeader />                     // Icon, status, duration
    <StageDetail>                       // Expandable panel
      <ThinkingSteps />                // Agent reasoning log
      <SubStepList />                  // Sub-step progress
      <StageMetrics />                 // Record counts, timings
  <PipelineStage stage="0" />          // Preflight
  <PipelineStage stage="0.5" />        // Orchestrator
  <PipelineStage stage="1" />          // Extract
  <PipelineStage stage="2" />          // Interpret
  <PipelineStage stage="2.5" />        // Validate
  <PipelineStage stage="3" />          // Enrich & Store
  <PipelineSummary />                  // Final stats
  <ErrorRecoveryPanel />               // Retry/override actions
```

**Key Components:**

| Component | Purpose | File Location |
|-----------|---------|---------------|
| `PipelineVisualization` | Main container, manages SSE connection | `frontend/src/components/acm/PipelineVisualization.tsx` |
| `PipelineStage` | Individual stage row (icon, status, timer) | `frontend/src/components/acm/PipelineStage.tsx` |
| `StageDetail` | Expandable detail panel | `frontend/src/components/acm/StageDetail.tsx` |
| `ThinkingSteps` | Agent reasoning/decision log | `frontend/src/components/acm/ThinkingSteps.tsx` |

**Hook:**

| Hook | Purpose | File Location |
|------|---------|---------------|
| `usePipelineStatus` | SSE connection to `/api/extraction/{source_id}/events`, reduces events into `PipelineRunState` | `frontend/src/lib/hooks/use-pipeline-status.ts` |

**Features:**
- 7-stage vertical stepper with real-time status updates
- Stage-level progress bars and duration timers
- Expandable detail panels with sub-step breakdowns
- Agent "thinking steps" showing tool selection reasoning
- Error recovery UI with retry/override options
- Final summary with confidence distribution
- Fallback to polling if SSE connection fails

**Reference:** See `docs/ag-ui-pipeline-spec.md` for complete specification.

---

## Appendix A: File Locations Summary

| File | Purpose |
|------|---------|
| `open_notebook/domain/acm.py` | ACMRecord model |
| `open_notebook/transformations/acm_extraction.py` | Extraction pipeline |
| `migrations/10.surrealql` | DB schema (up migration) |
| `migrations/10_down.surrealql` | DB schema (down migration) |
| `open_notebook/database/async_migrate.py` | Migration runner |
| `api/routers/acm.py` | REST endpoints |
| `commands/acm_commands.py` | Background jobs |
| `frontend/src/components/acm/` | React components |
| `frontend/src/lib/api/acm.ts` | API client |
| `frontend/src/hooks/useACMRecords.ts` | Data hooks |
