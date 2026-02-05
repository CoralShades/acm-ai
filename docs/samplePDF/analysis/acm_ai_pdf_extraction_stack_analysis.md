# ACM-AI PDF Extraction Tech Stack Analysis

## Executive Summary

This document analyzes PDF extraction tools against your requirement: **Extract Division 5 Asbestos Assessment PDFs → Excel Building Asbestos Registers (43 columns)**

**Recommendation: Enhance your current Docling stack with MinerU for table extraction and add a structured LLM extraction layer.**

---

## 1. Document Analysis: Your Specific Requirements

### Source PDF Structure (Division 5 Asbestos Assessment)
```
├── Cover Page (metadata)
├── Table of Contents
├── Executive Summary (text + bullets)
├── Asbestos Building Materials Register (COMPLEX TABLES - Pages 5-8)
│   ├── 19 columns per row
│   ├── Multi-page spanning
│   ├── Merged cells (Area/Level)
│   ├── Mixed data types (text, codes, dates, measurements)
│   └── Conditional formatting (positive/negative indicators)
├── NATA Laboratory Reports (structured results)
├── Risk Assessment Matrices
└── Statement of Limitations
```

### Target Excel Structure (43 columns)
| Category | Columns | Source Mapping |
|----------|---------|----------------|
| **Organization** | Department, Agency, Sub Agency, Site Name, Building Name | PDF header/metadata |
| **Building Details** | Building Type, Address, Suburb, Postcode, Owned/Leased, Year Built, Size, Levels | PDF Section 3 (Site Description) |
| **Location** | Internal/External, Level, Room or Area, Location in Room | Table Column 1-3 |
| **ACM Details** | Specific Item/ACM Name, Friability, ACM Product Group/Type | Table Columns 4-7 |
| **Sample Data** | NATA Sample Number, Sample Result | Table Column 6-7 + Lab Reports |
| **Risk Assessment** | Condition, Disturbance Potential, Quantity, Labelled | Table Columns 8-14 |
| **Recommendations** | Hygienist Recommendations, Additional Comments | Table Column 15 (Comments) |
| **Tracking** | PSB ACM ID, Removed?, Date Removed, Quantity Removed | Tracking metadata |

---

## 2. Current ACM-AI Setup Analysis

### Your Stack
```
CoralShades/acm-ai
├── Docling          → PDF parsing to Markdown
├── LangChain        → LLM orchestration
├── SurrealDB        → Document database
├── FastAPI          → Backend API
├── Next.js/React    → Frontend
└── Pydantic         → Data validation (ACMRecord model)
```

### Current Capabilities (Phase 1 Complete)
✅ PDF to Markdown conversion via Docling
✅ ACMRecord Pydantic model with 90%+ field accuracy
✅ Hierarchical context tracking (School → Building → Room → Item)
✅ Regex-based extraction from Markdown
✅ Background async processing
✅ 47 passing tests

### Current Gaps
❌ **Table extraction accuracy** - Docling's table parsing struggles with complex merged cells
❌ **Multi-page table continuity** - Tables spanning pages 5-8 lose context
❌ **Excel export** - Not yet implemented
❌ **Lab report parsing** - NATA sample results need structured extraction
❌ **Page citation linking** - Limited source tracking to specific page numbers

---

## 3. GitHub PDF Extraction Tools Comparison

### Tier 1: Recommended Additions

| Tool | Stars | Table Extraction | OCR | Self-Hosted | Integration Fit |
|------|-------|-----------------|-----|-------------|-----------------|
| **MinerU** | 51,901 | ⭐⭐⭐⭐⭐ (table-to-HTML) | ✅ 109 languages | ✅ | **EXCELLENT** - Best table extraction |
| **PaddleOCR** | 67,831 | ⭐⭐⭐⭐ (PP-Structure) | ✅ 100+ languages | ✅ | **EXCELLENT** - Production-grade |
| **Dolphin-v2** | 8,527 | ⭐⭐⭐⭐ (element-level) | ✅ VLM-based | ✅ | **GOOD** - Document parsing |
| **HunyuanOCR** | 1,436 | ⭐⭐⭐⭐ (structured output) | ✅ | ✅ | **GOOD** - Tencent's solution |

### Tier 2: Complementary Tools

| Tool | Purpose | Use Case for ACM-AI |
|------|---------|---------------------|
| **camelot-py** | Table extraction (vector-based) | Precise table bounds detection |
| **tabula-py** | Table extraction (Java) | Alternative for PDF tables |
| **pdfplumber** | Text/table extraction | Lightweight supplementary parsing |
| **RAG-Anything** | Multimodal RAG | Enhanced semantic search |

### Tier 3: Specialized (Consider for Future)

| Tool | Stars | Specialty |
|------|-------|-----------|
| **marker** | High | Fast PDF→Markdown (alternative to Docling) |
| **zerox** | Emerging | Vision model PDF extraction |
| **unstructured** | High | Partition-based document parsing |

---

## 4. Comparative Analysis: Docling vs. Alternatives

### For Your Asbestos Assessment PDFs

| Capability | Docling (Current) | MinerU | PaddleOCR | Dolphin-v2 |
|------------|-------------------|--------|-----------|------------|
| **Table Detection** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Merged Cell Handling** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Multi-page Tables** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Layout Preservation** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Python Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Self-Hosted** | ✅ | ✅ | ✅ | ✅ |
| **Australian Data Sovereignty** | ✅ | ✅ | ✅ | ✅ |

### Verdict
**Keep Docling** for general document parsing, but **add MinerU** specifically for the Asbestos Building Materials Register tables.

---

## 5. Recommended Tech Stack

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ACM-AI Enhanced Pipeline                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │ PDF Upload   │───▶│ PDF Router   │───▶│ Document Type Classifier │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│                                                   │                      │
│                    ┌──────────────────────────────┼──────────────────┐  │
│                    ▼                              ▼                  ▼  │
│         ┌──────────────────┐           ┌─────────────────┐  ┌────────┐ │
│         │ Docling          │           │ MinerU          │  │PaddleOCR│ │
│         │ (Text + Layout)  │           │ (Tables→HTML)   │  │(OCR)   │ │
│         └────────┬─────────┘           └────────┬────────┘  └───┬────┘ │
│                  │                              │                │      │
│                  └──────────────┬───────────────┴────────────────┘      │
│                                 ▼                                        │
│                    ┌──────────────────────────┐                          │
│                    │ Content Merger           │                          │
│                    │ (Page-aware assembly)    │                          │
│                    └────────────┬─────────────┘                          │
│                                 ▼                                        │
│                    ┌──────────────────────────┐                          │
│                    │ LLM Extraction Layer     │                          │
│                    │ (Claude/Ollama)          │                          │
│                    │ - Field mapping          │                          │
│                    │ - Validation             │                          │
│                    │ - Enrichment             │                          │
│                    └────────────┬─────────────┘                          │
│                                 ▼                                        │
│                    ┌──────────────────────────┐                          │
│                    │ ACMRecord Pydantic Model │                          │
│                    │ (43 fields validated)    │                          │
│                    └────────────┬─────────────┘                          │
│                                 ▼                                        │
│         ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│         │ SurrealDB    │  │ Excel Export │  │ UI (Agentic Wizard)  │    │
│         │ (Storage)    │  │ (openpyxl)   │  │ (Next.js)            │    │
│         └──────────────┘  └──────────────┘  └──────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Required Stack Components

#### Layer 1: PDF Ingestion & Parsing

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **Docling** (keep) | General PDF→Markdown | `pip install docling` |
| **MinerU** (add) | Table extraction | `pip install mineru[all]` |
| **PaddleOCR** (optional) | Scanned PDF OCR | `pip install paddleocr paddlepaddle` |
| **pdfplumber** (add) | Page/bounds detection | `pip install pdfplumber` |

#### Layer 2: Content Processing

| Component | Purpose | Notes |
|-----------|---------|-------|
| **LangChain** (keep) | LLM orchestration | Already in stack |
| **Pydantic v2** (keep) | Data validation | ACMRecord model |
| **pandas** (add) | Data manipulation | For transformation |

#### Layer 3: Excel Generation

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **openpyxl** (add) | Excel creation with formatting | `pip install openpyxl` |
| **xlsxwriter** (optional) | Alternative Excel writer | `pip install xlsxwriter` |

#### Layer 4: Storage & Export

| Component | Purpose | Notes |
|-----------|---------|-------|
| **SurrealDB** (keep) | Document storage | Already in stack |
| **FastAPI** (keep) | API endpoints | Add export endpoint |

---

## 6. Implementation Strategy

### Phase 1: Enhanced Table Extraction (1-2 weeks)

```python
# acm_ai/extraction/mineru_extractor.py
from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter

class MineruTableExtractor:
    """Extract tables from Asbestos Assessment PDFs using MinerU"""
    
    def extract_tables(self, pdf_path: str) -> list[dict]:
        """Extract tables with HTML structure preservation"""
        # MinerU converts tables to HTML with structure
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

### Phase 2: ACM Field Mapper (1 week)

```python
# acm_ai/extraction/field_mapper.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

class BuildingAsbestosRegisterRow(BaseModel):
    """Maps to your 43-column Excel format"""
    
    # Organization (columns 1-5)
    department: str = "DJCS"
    agency: str = "Victoria Police"
    sub_agency: str
    site_name: str
    building_name: str
    
    # Building Details (columns 6-17)
    building_type: str = "Police Station"
    building_address: str
    suburb: str
    postcode: str
    owned_or_leased: str = "Owned"
    building_unique_id: Optional[str] = None
    frequency_of_use: str = "Every day"
    public_access: str = "YES"
    date_of_inspection: date
    estimated_year_built: int
    est_building_size_m2: float
    number_of_levels: int
    construction_type: str
    roof_type: str
    
    # Location (columns 18-22)
    internal_external: str  # "Internal" or "External"
    level: str  # "Ground", "First floor", "External"
    room_or_area: str
    location_in_room: str
    
    # ACM Details (columns 23-31)
    specific_item_acm_name: str
    friability_of_material: str  # "Friable" or "Non-friable"
    acm_product_group: str
    acm_product_type: str
    nata_sample_number: Optional[str]
    sample_result: str  # "Positive", "Negative", "Assumed Positive"
    identifying_company: str = "Prensa Pty Ltd"
    
    # Risk Assessment (columns 32-36)
    condition: Optional[str]  # "Good", "Fair", "Poor", "N/A (negative)"
    disturbance_potential: Optional[str]  # "Low", "Medium", "High"
    quantity: Optional[float]
    labelled: str  # "YES", "NO"
    label_details: Optional[str]
    
    # Recommendations (columns 37-38)
    hygienist_recommendations: Optional[str]
    additional_comments: Optional[str]
    
    # Tracking (columns 39-43)
    psb_supplied_acm_id: Optional[str]
    assumed_removed: Optional[str]
    date_of_removal: Optional[date]
    quantity_removed: Optional[float]
    asbestos_removal_notification_no: Optional[str]
    epa_waste_transport_certificate_no: Optional[str]
```

### Phase 3: Excel Export (1 week)

```python
# acm_ai/export/excel_exporter.py
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List
from .field_mapper import BuildingAsbestosRegisterRow

class AsbestosRegisterExporter:
    """Export ACM records to Victorian Government BAR format"""
    
    HEADERS = [
        "Department", "Agency", "Sub Agency", "Site Name (if applicable)",
        "Building Name", "Building Type", "Building Address", "Suburb",
        "Postcode", "Owned or Leased", "Building Unique ID", "Frequency of use",
        "Public Access?", "Date of Inspection", "Estimated Year Built",
        "Est. Building Size (m2)", "Number of Levels", "Construction Type",
        "Roof Type", "Internal / External", "Level", "Room or Area",
        "Location in Room", "Specific Item/ACM Name", "Friability of material",
        "ACM Product Group", "ACM Product Type", 
        "NATA Endorsed Sample number (if available)", "Sample Result",
        "Identifying Hygiene or Consulting Company", "Condition",
        "Disturbance Potential", "Quantity", "Labelled", "Label Details",
        "Hygienist Recommendations", "Additional Comments",
        "PSB Supplied ACM ID", "Assumed Removed?", "Date of Removal",
        "Quantity Removed", "Asbestos Removal Notification No",
        "EPA Waste Transport Certificate No"
    ]
    
    def export(self, records: List[BuildingAsbestosRegisterRow], 
               output_path: str) -> str:
        wb = Workbook()
        ws = wb.active
        ws.title = "Asbestos Register"
        
        # Header row with formatting
        header_fill = PatternFill(start_color="002060", 
                                   end_color="002060", 
                                   fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col, header in enumerate(self.HEADERS, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        
        # Data rows
        for row_idx, record in enumerate(records, start=2):
            data = record.model_dump()
            for col_idx, field in enumerate(self.HEADERS, start=1):
                field_key = field.lower().replace(" ", "_").replace("?", "")
                value = data.get(field_key, "")
                ws.cell(row=row_idx, column=col_idx, value=value)
        
        # Auto-fit column widths
        for column in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
        
        wb.save(output_path)
        return output_path
```

### Phase 4: Agentic Workflow Integration (1-2 weeks)

```python
# acm_ai/agents/extraction_agent.py
from langchain.agents import AgentExecutor
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic

@tool
def extract_pdf_metadata(pdf_path: str) -> dict:
    """Extract site information from PDF cover page and section 3"""
    # Implementation using Docling for text extraction
    pass

@tool  
def extract_acm_register(pdf_path: str) -> list[dict]:
    """Extract Asbestos Building Materials Register table using MinerU"""
    # Implementation using MinerU for precise table extraction
    pass

@tool
def extract_lab_results(pdf_path: str) -> list[dict]:
    """Extract NATA laboratory sample analysis results"""
    # Parse lab report pages for sample numbers and results
    pass

@tool
def validate_and_map_fields(raw_data: dict) -> BuildingAsbestosRegisterRow:
    """Validate and map extracted data to 43-column format"""
    # Use Pydantic model for validation
    pass

@tool
def export_to_excel(records: list, output_path: str) -> str:
    """Export validated records to Excel BAR format"""
    # Use openpyxl exporter
    pass

class ACMExtractionAgent:
    """Agentic workflow for Division 5 PDF → Excel conversion"""
    
    def __init__(self, llm_provider: str = "anthropic"):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        self.tools = [
            extract_pdf_metadata,
            extract_acm_register,
            extract_lab_results,
            validate_and_map_fields,
            export_to_excel
        ]
        self.agent = AgentExecutor.from_agent_and_tools(
            agent=self._create_agent(),
            tools=self.tools,
            verbose=True
        )
    
    def process_pdf(self, pdf_path: str, output_excel: str) -> str:
        """Full extraction workflow"""
        return self.agent.invoke({
            "input": f"Extract all ACM data from {pdf_path} and export to {output_excel}"
        })
```

---

## 7. Dependencies to Add

### pyproject.toml additions

```toml
[project]
dependencies = [
    # Existing
    "docling>=0.1.0",
    "langchain>=0.1.0",
    "pydantic>=2.0",
    "surrealdb>=0.3.0",
    "fastapi>=0.109.0",
    
    # New: PDF Extraction
    "mineru[all]>=0.1.0",           # Table extraction
    "pdfplumber>=0.10.0",           # Page/bounds detection
    "paddleocr>=2.7.0",             # OCR (optional)
    "paddlepaddle>=2.5.0",          # PaddleOCR backend
    
    # New: Excel Export
    "openpyxl>=3.1.0",              # Excel generation
    "pandas>=2.0",                   # Data manipulation
    
    # New: LLM Providers
    "langchain-anthropic>=0.1.0",   # Claude integration
    "langchain-ollama>=0.1.0",      # Local models
]
```

### Docker additions

```dockerfile
# Add MinerU dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PaddlePaddle for PaddleOCR
RUN pip install paddlepaddle-gpu || pip install paddlepaddle
```

---

## 8. Migration Path from Current Setup

### Week 1-2: Add MinerU Integration
1. Install MinerU alongside Docling
2. Create hybrid extractor that routes tables to MinerU
3. Test on sample Broadmeadows PDF

### Week 3: Field Mapping Layer
1. Implement BuildingAsbestosRegisterRow Pydantic model
2. Create mapping functions from raw extraction to model
3. Add validation rules for Australian asbestos standards

### Week 4: Excel Export
1. Implement openpyxl-based exporter
2. Match exact format from target Excel template
3. Add formatting (colors, column widths, headers)

### Week 5-6: Agentic Workflow
1. Wrap extraction steps as LangChain tools
2. Create AgentExecutor with reasoning loop
3. Integrate with existing UI wizard

---

## 9. Key Decisions

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| **Keep Docling?** | ✅ Yes | Good for general text/layout; complement with MinerU |
| **Add MinerU?** | ✅ Yes (Primary) | Best table extraction, outputs HTML, Python native |
| **Add PaddleOCR?** | ⚡ Optional | Only if handling scanned PDFs |
| **Replace SurrealDB?** | ❌ No | Works well for document storage |
| **LLM for extraction?** | ✅ Yes | Field mapping and validation |
| **Local models?** | ✅ Yes (Ollama) | Data sovereignty for sensitive ACM data |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MinerU table accuracy <90% | Medium | High | Fall back to manual review flag |
| Multi-page table continuity issues | Medium | Medium | Implement page stitching logic |
| NATA lab report format variations | Low | Medium | Train extraction prompts on variations |
| Excel format compliance | Low | High | Automated validation against template |
| Processing time for large PDFs | Medium | Low | Async processing (already implemented) |

---

## Conclusion

Your **ACM-AI stack is well-architected** with Docling + LangChain + SurrealDB. The recommended enhancements:

1. **Add MinerU** for superior table extraction (the Asbestos Building Materials Register)
2. **Implement BuildingAsbestosRegisterRow** Pydantic model (43 fields)
3. **Add openpyxl exporter** for Excel generation
4. **Create agentic workflow** with LangChain tools for the wizard UI

This approach leverages your existing investment while addressing the specific challenges of complex asbestos assessment PDFs.

**Estimated effort: 4-6 weeks** to full implementation.
