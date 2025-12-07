# Technical Architecture - ACM-AI

> **Project:** ACM-AI v1.0
> **Date:** 2025-12-07
> **Status:** Draft

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
        │  │ ├─ acm_record   │◄─┼────┼──┤ └─ acm_extract(NEW) │  │    │                     │
        │  │ └─ embedding    │  │    │  └─────────────────────┘  │    │                     │
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
│   ├── acm/                    # NEW DIRECTORY
│   │   ├── ACMSpreadsheet.tsx  # AG Grid wrapper
│   │   ├── ACMCellViewer.tsx   # PDF modal for cell citations
│   │   ├── ACMToolbar.tsx      # Search, filter, export controls
│   │   ├── RiskBadge.tsx       # Risk status cell renderer
│   │   └── ACMContextToggle.tsx# Chat context switch
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

### 3.1 SurrealDB Tables

```sql
-- ACM Record Table
DEFINE TABLE acm_record SCHEMAFULL;

-- Core identification
DEFINE FIELD source_id ON acm_record TYPE record<source>;
DEFINE FIELD school_name ON acm_record TYPE string;
DEFINE FIELD school_code ON acm_record TYPE string;

-- Building hierarchy
DEFINE FIELD building_id ON acm_record TYPE string;
DEFINE FIELD building_name ON acm_record TYPE string;
DEFINE FIELD building_year ON acm_record TYPE option<int>;
DEFINE FIELD building_construction ON acm_record TYPE option<string>;

-- Room hierarchy
DEFINE FIELD room_id ON acm_record TYPE option<string>;
DEFINE FIELD room_name ON acm_record TYPE option<string>;
DEFINE FIELD room_area ON acm_record TYPE option<float>;
DEFINE FIELD area_type ON acm_record TYPE string;

-- ACM data
DEFINE FIELD product ON acm_record TYPE string;
DEFINE FIELD material_description ON acm_record TYPE string;
DEFINE FIELD extent ON acm_record TYPE string;
DEFINE FIELD location ON acm_record TYPE string;
DEFINE FIELD friable ON acm_record TYPE option<string>;
DEFINE FIELD material_condition ON acm_record TYPE option<string>;
DEFINE FIELD risk_status ON acm_record TYPE option<string>;
DEFINE FIELD result ON acm_record TYPE string;

-- Citation support
DEFINE FIELD page_number ON acm_record TYPE option<int>;
DEFINE FIELD extraction_confidence ON acm_record TYPE option<float>;

-- Timestamps
DEFINE FIELD created_at ON acm_record TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON acm_record TYPE datetime DEFAULT time::now();

-- Indexes for query performance
DEFINE INDEX acm_source ON acm_record FIELDS source_id;
DEFINE INDEX acm_building ON acm_record FIELDS building_id;
DEFINE INDEX acm_risk ON acm_record FIELDS risk_status;
DEFINE INDEX acm_room ON acm_record FIELDS room_id;
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

### 4.2 API Response Types

```typescript
interface ACMRecord {
  id: string;
  source_id: string;
  school_name: string;
  school_code: string;
  building_id: string;
  building_name: string;
  building_year?: number;
  building_construction?: string;
  room_id?: string;
  room_name?: string;
  room_area?: number;
  area_type: 'Exterior' | 'Interior' | 'Grounds';
  product: string;
  material_description: string;
  extent: string;
  location: string;
  friable?: 'Friable' | 'Non Friable';
  material_condition?: string;
  risk_status?: 'Low' | 'Medium' | 'High';
  result: string;
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
  };
  by_building: Array<{
    building_id: string;
    building_name: string;
    count: number;
  }>;
}
```

---

## 5. ACM Extraction Pipeline

### 5.1 Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ACM Extraction Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Stage 1: Source Processing (Existing)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PDF Upload → Docling → Markdown + Table JSON → Store in Source │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 2: ACM Table Detection (NEW)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Scan Docling output for ACM Register table patterns:           │   │
│  │  - Headers: "Product", "Material Description", "Extent", etc.   │   │
│  │  - Context: "Asbestos Register", "Building", "Room"             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 3: Hierarchical Parsing (NEW)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Parse building/room structure:                                  │   │
│  │  - Extract building header: "B00A - Admin Block - 1924"         │   │
│  │  - Extract room sections: "R0001 - External Movement"           │   │
│  │  - Associate ACM items with their room/building context         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 4: Record Creation (NEW)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Create ACMRecord for each row:                                  │   │
│  │  - Map columns to schema fields                                  │   │
│  │  - Capture page number for citations                             │   │
│  │  - Calculate extraction confidence                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 5: Storage & Indexing (NEW)                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  - Save ACMRecords to SurrealDB                                  │   │
│  │  - Generate embeddings for semantic search                       │   │
│  │  - Update source status                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Table Detection Patterns

```python
# Headers to identify ACM Register tables
ACM_TABLE_HEADERS = [
    "product",
    "material description",
    "extent",
    "location",
    "friable",
    "material condition",
    "risk status",
    "result"
]

# Building header pattern
BUILDING_PATTERN = r"^([A-Z]\d+[A-Z]?)\s*[-–]\s*(.+?)(?:\s*[-–]\s*(\d{4}))?$"
# Example: "B00A - Other-Dse Admin - 1924"

# Room header pattern
ROOM_PATTERN = r"^([A-Z]\d+[A-Z]?-R\d+)\s*[-–]\s*(.+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?$"
# Example: "B00A-R0001 - External Movement"
```

---

## 6. Frontend Integration

### 6.1 AG Grid Configuration

```typescript
// frontend/src/components/acm/ACMSpreadsheet.tsx

import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridApi } from 'ag-grid-community';

const columnDefs: ColDef[] = [
  {
    field: 'building_name',
    headerName: 'Building',
    rowGroup: true,
    hide: true,
    filter: 'agTextColumnFilter'
  },
  {
    field: 'room_name',
    headerName: 'Room',
    rowGroup: true,
    hide: true,
    filter: 'agTextColumnFilter'
  },
  {
    field: 'product',
    headerName: 'Product',
    width: 150,
    filter: 'agTextColumnFilter'
  },
  {
    field: 'material_description',
    headerName: 'Material',
    width: 180,
    filter: 'agTextColumnFilter'
  },
  {
    field: 'extent',
    headerName: 'Extent',
    width: 100
  },
  {
    field: 'location',
    headerName: 'Location',
    width: 120,
    filter: 'agTextColumnFilter'
  },
  {
    field: 'friable',
    headerName: 'Friable',
    width: 100,
    filter: 'agSetColumnFilter'
  },
  {
    field: 'material_condition',
    headerName: 'Condition',
    width: 130,
    filter: 'agSetColumnFilter'
  },
  {
    field: 'risk_status',
    headerName: 'Risk',
    width: 100,
    cellRenderer: 'riskBadgeRenderer',
    filter: 'agSetColumnFilter'
  },
  {
    field: 'result',
    headerName: 'Result',
    width: 200,
    filter: 'agSetColumnFilter'
  }
];

const defaultColDef: ColDef = {
  sortable: true,
  resizable: true,
  cellClass: 'cursor-pointer'
};

const gridOptions = {
  rowGroupPanelShow: 'always',
  groupDefaultExpanded: 1,
  animateRows: true,
  enableCellTextSelection: true
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

Run migration script to create `acm_record` table:

```bash
uv run python -m open_notebook.migrations.acm_tables
```

---

## Appendix A: File Locations Summary

| File | Purpose |
|------|---------|
| `open_notebook/domain/acm.py` | ACMRecord model |
| `open_notebook/transformations/acm_extraction.py` | Extraction pipeline |
| `open_notebook/migrations/acm_tables.surql` | DB schema |
| `api/routers/acm.py` | REST endpoints |
| `commands/acm_commands.py` | Background jobs |
| `frontend/src/components/acm/` | React components |
| `frontend/src/lib/api/acm.ts` | API client |
| `frontend/src/hooks/useACMRecords.ts` | Data hooks |
