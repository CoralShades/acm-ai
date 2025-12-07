# System Analysis - ACM-AI

> **Purpose:** Document current Open Notebook capabilities and how they map to ACM-AI requirements
> **Last Updated:** 2025-12-07

## 1. Current Open Notebook Architecture

### 1.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 15 + React | Modern web UI |
| Backend API | FastAPI (Python) | REST API |
| Database | SurrealDB | Document + vector storage |
| Background Jobs | surreal-commands-worker | Async processing |
| Document Processing | content-core + Docling | PDF/document extraction |
| AI/LLM | Esperanto (multi-provider) | OpenAI, Anthropic, Ollama, etc. |

### 1.2 Key Components

```
┌─────────────────────────────────────────────────────────┐
│  Browser (localhost:8502)                               │
└────────────────┬────────────────────────────────────────┘
                 │
         ┌───────────────┐
         │   Next.js     │  ← Frontend (React)
         │   Port 8502   │    Proxies /api/* requests
         └───────┬───────┘
                 │
         ┌───────────────┐
         │   FastAPI     │  ← Backend API
         │   Port 5055   │
         └───────┬───────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───────────┐         ┌───────────────┐
│ SurrealDB │         │ Background    │
│ Port 8000 │         │ Worker        │
└───────────┘         └───────────────┘
```

### 1.3 Existing Features Relevant to ACM-AI

| Feature | Description | Reusability |
|---------|-------------|-------------|
| **Source Upload** | PDF, images, documents | Direct reuse |
| **Docling Integration** | Advanced PDF parsing with table extraction | Direct reuse |
| **Vector Search** | Semantic search across content | Direct reuse |
| **Citations** | Source references in chat `[source:id]` | Direct reuse |
| **Transformations** | Custom AI processing pipelines | Extend for ACM extraction |
| **Chat** | Context-aware conversations | Extend for spreadsheet context |
| **Notes** | AI-generated or manual notes | Direct reuse |

## 2. Docling Capabilities (Already Integrated)

### 2.1 Supported Formats
- PDF (with table extraction)
- DOCX, XLSX, PPTX
- Images (PNG, JPEG, TIFF, BMP)
- Markdown, HTML, CSV

### 2.2 Output Formats
- Markdown (default)
- HTML
- JSON (structured)

### 2.3 Table Extraction
Docling can extract tables from PDFs and preserve structure - **critical for Asbestos Register data**.

## 3. Citation System Analysis

### 3.1 Reference Types
```
[source:id]         → Links to source document
[note:id]           → Links to note
[source_insight:id] → Links to AI-generated insight
```

### 3.2 Rendering Pipeline
1. AI response contains inline references
2. `parseSourceReferences()` extracts references
3. `convertReferencesToCompactMarkdown()` creates numbered citations
4. Clickable links open modals with source details

### 3.3 Extension Needed for ACM-AI
New reference type needed:
```
[spreadsheet:id:row:col] → Links to specific cell in extracted data
```

## 4. Gap Analysis

### 4.1 What Exists vs What's Needed

| Capability | Current State | ACM-AI Requirement | Gap |
|------------|---------------|-------------------|-----|
| PDF Upload | ✅ Exists | Upload SAMP/Register PDFs | None |
| Table Extraction | ✅ Docling extracts tables | Extract ACM Register tables | Minor - need schema mapping |
| Structured Data View | ❌ Markdown only | AG Grid spreadsheet | **Major - New component** |
| Cell-level Citations | ❌ Document-level only | Click cell → see PDF source | **Major - New feature** |
| Data Export | ❌ None | Export to Excel/CSV | **Medium - New feature** |
| Branding | Open Notebook | ACM-AI | **Medium - Theming/naming** |

### 4.2 Components to Build

1. **AG Grid Integration**
   - Install and configure AG Grid React
   - Create ACMSpreadsheet component
   - Column definitions for Asbestos Register schema

2. **ACM Data Extraction Pipeline**
   - Transformation to parse Docling output
   - Schema mapping for different register formats
   - Store structured data in SurrealDB

3. **Spreadsheet-Chat Integration**
   - Include spreadsheet data in chat context
   - New citation type for cell references
   - Cell click → highlight in PDF (if available)

4. **Rebranding**
   - App name: ACM-AI
   - Logo and theme colors
   - Landing page messaging

## 5. Sample PDF Structure Analysis

### 5.1 Asbestos Register Table Schema

From `1124_AsbestosRegister.pdf`:

| Column | Description | Data Type |
|--------|-------------|-----------|
| Product | Type of building element | String |
| Material Description | ACM material type | String |
| Extent | Area/quantity | String (with units) |
| Location | Building/room location | String |
| Friable/Non Friable | Asbestos classification | Enum |
| Material Condition | Current state | String |
| Risk Status | Risk level | Enum (Low/Medium/High) |
| Result | ACM confirmation | Enum |

### 5.2 Document Sections
1. Cover page (School name, revision date)
2. Table of Contents
3. Policy sections (7 chapters)
4. Definitions glossary
5. Site Plan (image)
6. **Asbestos Register** (structured tables) ← Primary extraction target

### 5.3 Hierarchical Structure
```
School
└── Building (e.g., B00A - Other-Dse Admin - 1924)
    ├── Exterior
    │   └── ACM Items...
    └── Interior
        └── Room (e.g., R0001 - External Movement)
            └── ACM Items...
```

## 6. Technical Recommendations

### 6.1 Data Model Extension

```typescript
// New SurrealDB table for ACM data
interface ACMRecord {
  id: string;
  source_id: string;           // Link to source PDF
  school_name: string;
  school_code: string;
  building_id: string;
  building_name: string;
  room_id?: string;
  room_name?: string;
  product: string;
  material_description: string;
  extent: string;
  location: string;
  friable: 'Friable' | 'Non Friable' | null;
  material_condition: string;
  risk_status: 'Low' | 'Medium' | 'High';
  result: 'Asbestos-containing material' | 'Non asbestos-containing material' | 'Assumed asbestos-containing material';
  page_number?: number;         // For citation
  bounding_box?: number[];      // For PDF highlight
}
```

### 6.2 Processing Pipeline

```
PDF Upload → Docling Extract → ACM Parser → SurrealDB → AG Grid Display
                                   │
                                   └→ Vector Embeddings → Chat Context
```

### 6.3 AG Grid Configuration Needs

- Enterprise license (for Excel export, row grouping)
- Or Community edition with manual grouping
- Column pinning for building/room navigation
- Filter sidebar for risk status, condition
- Cell renderer for clickable citations

## 7. Next Steps

1. [ ] Create Product Brief with stakeholder goals
2. [ ] Define detailed PRD with acceptance criteria
3. [ ] Design technical architecture
4. [ ] Break down into epics and stories
5. [ ] Prioritize MVP scope
