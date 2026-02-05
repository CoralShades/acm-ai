# Asbestos Assessment PDF → Excel Extraction: Local LLM Solution

## Project Overview

**Client Requirement:** Automate extraction of asbestos assessment data from Division 5 PDF reports into a standardized Building Asbestos Register (BAR) Excel format.

**Data Privacy:** Full local processing required - no cloud APIs.

**Hardware:** RTX 4090 (24GB VRAM)

---

## PDF Structure Analysis

The Prensa Division 5 Asbestos Assessment PDFs contain:

| Section | Data Type | Extraction Complexity |
|---------|-----------|----------------------|
| Cover Page | Site metadata (address, client, job no.) | Low |
| Executive Summary | Key findings summary | Medium |
| **Asbestos Building Materials Register** | **Complex tables with 18+ columns** | **High** |
| Lab Analysis Reports | Sample results table | Medium |
| Site Description Table | Building info (year, size, levels) | Low |
| Risk Assessment Factors | Reference only | Skip |

### Critical Extraction Target: The Register Table (Pages 5-8)

The main register table has these columns that map to your BAR:
- Area/Level → Level (col 20)
- Room & Location → Room or Area (col 21)
- Feature → Location in Room (col 22)
- Item Description → Specific Item/ACM Name (col 23)
- Hazard Type → (always "Asbestos")
- Hazard Status → Sample Result (col 28)
- Sample Number → NATA Endorsed Sample number (col 27)
- Friability → Friability of material (col 24)
- Labelled Y/N → Labelled (col 33)
- Disturb. Potential → Disturbance Potential (col 31)
- Condition → Condition (col 30)
- Risk Status → (derived)
- Approx. Quantity → Quantity (col 32)
- Control Priority → (P1-P4)
- Comments & Recommendations → Hygienist Recommendations (col 35)
- Date of Identification → Date of Inspection (col 13)
- Reinspect Date → (not mapped)

---

## Recommended Model Stack

### Primary Model: **Qwen2.5-VL 72B** (Vision-Language)

**Why Vision over Text-only:**
1. The PDF register tables span multiple pages with complex merged cells
2. OCR + text extraction loses table structure
3. Vision models can "see" the table layout directly
4. Handles the embedded photographs in the register

**VRAM Usage:** ~42GB (needs quantization for 24GB)

### Alternative Stack for 24GB VRAM:

| Model | Size | Purpose | Quantization |
|-------|------|---------|--------------|
| **Qwen2.5-VL 32B** | ~18GB | Primary table extraction | Q4_K_M |
| **Qwen2.5 14B** | ~8GB | Data validation/normalization | Q8_0 |
| **Llama3.2-Vision 11B** | ~6GB | Backup/verification | Q8_0 |

### Recommended Setup:

```bash
# Primary extraction model
ollama pull qwen2.5-vl:32b-instruct-q4_K_M

# Validation model  
ollama pull qwen2.5:14b-instruct-q8_0

# Fallback
ollama pull llama3.2-vision:11b-instruct-q8_0
```

---

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    PDF Processing Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │   PDF    │───▶│  PDF to      │───▶│  Page Classifier      │  │
│  │  Input   │    │  Images      │    │  (Cover/TOC/Register/ │  │
│  └──────────┘    │  (pdf2image) │    │   Lab/Body)           │  │
│                  └──────────────┘    └───────────┬───────────┘  │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  EXTRACTION AGENTS                        │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │   │
│  │  │  Metadata      │  │  Register      │  │  Lab Report │ │   │
│  │  │  Extractor     │  │  Table Parser  │  │  Parser     │ │   │
│  │  │  (Cover/Site)  │  │  (Main Task)   │  │             │ │   │
│  │  └────────────────┘  └────────────────┘  └─────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 DATA TRANSFORMATION                       │   │
│  │  • Map PDF columns → BAR Excel columns                    │   │
│  │  • Normalize values (Good/Fair/Poor, P1-P4)              │   │
│  │  • Derive ACM Product Group/Type from description        │   │
│  │  • Handle "Same as XXX" sample references                │   │
│  │  • Populate constant fields (Department, Agency, etc.)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 VALIDATION LAYER                          │   │
│  │  • Cross-check sample numbers with Lab Report            │   │
│  │  • Verify quantity units (m², lm, units)                 │   │
│  │  • Check friability classification consistency           │   │
│  │  • Flag missing required fields                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 EXCEL OUTPUT                              │   │
│  │  • Generate BAR-compliant .xlsx                          │   │
│  │  • Apply formatting (colors, column widths)              │   │
│  │  • Add data validation dropdowns                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Field Mapping: PDF → Excel BAR

### Constant Fields (Same for all rows from one PDF):

| BAR Column | Source | Example Value |
|------------|--------|---------------|
| Department | Hardcoded | DJCS |
| Agency | PDF Cover | Victoria Police |
| Sub Agency | PDF Site Info | Broadmeadows Police Station |
| Site Name | PDF Site Info | Broadmeadows Police Station |
| Building Name | PDF Site Info | Broadmeadows Police Station |
| Building Type | Derived from Agency | Police Station |
| Building Address | PDF Site Info | 15 Dimboola Road |
| Suburb | PDF Site Info | Broadmeadows |
| Postcode | PDF Site Info | 3047 |
| Owned or Leased | Hardcoded/Inferred | Owned |
| Frequency of use | Hardcoded | Every day |
| Public Access? | Hardcoded | YES |
| Date of Inspection | PDF Assessment Date | 2020-04-08 |
| Estimated Year Built | PDF Table 1 | 1985 |
| Est. Building Size (m2) | PDF Table 1 | 6272 |
| Number of Levels | PDF Table 1 | 2 |
| Construction Type | PDF Table 1 | Brick |
| Roof Type | PDF Table 1 | Metal |
| Identifying Company | PDF Header | Prensa Pty Ltd |

### Per-Row Fields (From Register Table):

| BAR Column | PDF Register Column | Transform |
|------------|---------------------|-----------|
| Internal / External | Area/Level prefix or Room context | Map "External" locations |
| Level | Area/Level | Extract: Ground floor, First floor → Ground, Level 1 |
| Room or Area | Room & Location | Direct + title case |
| Location in Room | Feature | Map to standard terms |
| Specific Item/ACM Name | Item Description | Clean + standardize |
| Friability of material | Friability | Non-friable, Friable |
| ACM Product Group | Derived from Item Description | Use lookup table |
| ACM Product Type | Derived from Item Description | Use lookup table |
| NATA Sample Number | Sample Number | Direct, handle "Same as" |
| Sample Result | Hazard Status | Positive, Negative, Assumed Positive |
| Condition | Condition | Good, Fair, Poor, N/A (negative) |
| Disturbance Potential | Disturb. Potential | Low, Medium, High, N/A |
| Quantity | Approx. Quantity | Parse number + unit |
| Labelled | Labelled Y/N | YES, NO |
| Label Details | If Labelled=Yes | "Labelled" |
| Hygienist Recommendations | Comments & Recommendations | Direct |
| Additional Comments | Item Description color note | Extract color descriptions |

### ACM Product Group/Type Lookup:

| Item Description Contains | ACM Product Group | ACM Product Type |
|---------------------------|-------------------|------------------|
| vinyl, sheet vinyl | Vinyl products | Vinyl sheet |
| vinyl tile | Vinyl products | Vinyl Tiles |
| hessian back | Vinyl products | Hessian backed Vinyl sheet |
| mastic, flange mastic | Gasket, friction products and adhesives | Mastic |
| gasket | Gasket, friction products and adhesives | Gasket(s) |
| fibre cement, FC | Cement products | Flat Sheeting |
| fuse | Insulation Products | Electrical Components |
| internal lining, filing cabinet | Insulation Products | Internal Lining |

---

## Implementation Approach

### Phase 1: PDF Pre-processing

```python
from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path, output_dir, dpi=300):
    """Convert PDF to high-res images for vision model"""
    images = convert_from_path(pdf_path, dpi=dpi)
    paths = []
    for i, img in enumerate(images):
        path = f"{output_dir}/page_{i+1:03d}.png"
        img.save(path, 'PNG')
        paths.append(path)
    return paths
```

### Phase 2: Page Classification

Classify each page to route to appropriate extractor:

```python
PAGE_TYPES = {
    'cover': ['Division 5 Asbestos Assessment', 'Client No:', 'Job No:'],
    'toc': ['Table of Contents', 'Executive Summary'],
    'executive': ['Executive Summary', 'significant key findings'],
    'register': ['Asbestos Register', 'Area / Level', 'Room & Location'],
    'lab_report': ['Bulk Sample Analysis', 'NATA', 'Chrysotile'],
    'methodology': ['Introduction', 'Methodology', 'Findings'],
    'appendix': ['Risk Assessment Factors', 'Priority Ratings']
}
```

### Phase 3: Vision-based Table Extraction

```python
import ollama
import base64
import json

def extract_register_table(image_path: str) -> list[dict]:
    """Use Qwen2.5-VL to extract table rows from register page"""
    
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    prompt = """Analyze this asbestos register table image. Extract ALL rows as JSON.

For each row, extract:
- area_level: The floor/area (e.g., "Ground floor", "First floor", "External")
- room_location: The room name
- feature: The building feature/element
- item_description: Material description with color
- hazard_status: "Positive", "Negative", or "Assumed positive"
- sample_number: The sample ID (e.g., "34511-039-001" or "Same as 34511-039-001")
- friability: "Non-friable" or "Friable"
- labelled: "Yes" or "No"
- disturbance_potential: "Low", "Medium", "High", or "-"
- condition: "Good", "Fair", "Poor", or "-"
- quantity: The amount with unit (e.g., "3 units", "2m2", "10 lm", "Throughout")
- comments: Recommendations text

Return ONLY valid JSON array. Example:
[
  {
    "area_level": "Ground floor",
    "room_location": "Main foyer",
    "feature": "Floor",
    "item_description": "Vinyl sheet (cream)",
    "hazard_status": "Negative",
    "sample_number": "34511-039-001",
    "friability": "Non-friable",
    "labelled": "No",
    "disturbance_potential": "-",
    "condition": "-",
    "quantity": "-",
    "comments": "-"
  }
]"""

    response = ollama.chat(
        model='qwen2.5-vl:32b-instruct-q4_K_M',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [img_b64]
        }],
        options={'temperature': 0.1}
    )
    
    # Parse JSON from response
    text = response['message']['content']
    # Extract JSON array from response
    start = text.find('[')
    end = text.rfind(']') + 1
    return json.loads(text[start:end])
```

### Phase 4: Data Transformation

```python
def transform_to_bar(pdf_metadata: dict, register_rows: list[dict]) -> list[dict]:
    """Transform extracted data to BAR format"""
    
    bar_rows = []
    
    for row in register_rows:
        bar_row = {
            # Constant fields from PDF metadata
            'Department': 'DJCS',
            'Agency': pdf_metadata['agency'],
            'Sub Agency': pdf_metadata['site_name'],
            'Site Name (if applicable)': pdf_metadata['site_name'],
            'Building Name': pdf_metadata['building_name'],
            'Building Type': infer_building_type(pdf_metadata['agency']),
            'Building Address': pdf_metadata['address'],
            'Suburb': pdf_metadata['suburb'],
            'Postcode': pdf_metadata['postcode'],
            'Owned or Leased': 'Owned',
            'Building Unique ID': None,
            'Frequency of use': 'Every day',
            'Public Access?': 'YES',
            'Date of Inspection': pdf_metadata['inspection_date'],
            'Estimated Year Built': pdf_metadata['year_built'],
            'Est. Building Size (m2)': pdf_metadata['building_size'],
            'Number of Levels': pdf_metadata['levels'],
            'Construction Type': pdf_metadata['construction'],
            'Roof Type': pdf_metadata['roof_type'],
            'Identifying Hygiene or Consulting Company': pdf_metadata['consultant'],
            
            # Per-row fields
            'Internal / External': classify_internal_external(row['area_level'], row['room_location']),
            'Level': normalize_level(row['area_level']),
            'Room or Area': title_case(row['room_location']),
            'Location in Room': map_feature_to_location(row['feature']),
            'Specific Item/ACM Name': standardize_item_name(row['feature'], row['item_description']),
            'Friability of material': row['friability'],
            'ACM Product Group': lookup_product_group(row['item_description']),
            'ACM Product Type': lookup_product_type(row['item_description']),
            'NATA Endorsed Sample number (if available)': normalize_sample_number(row['sample_number']),
            'Sample Result': normalize_result(row['hazard_status']),
            'Condition': normalize_condition(row['condition'], row['hazard_status']),
            'Disturbance Potential': normalize_disturbance(row['disturbance_potential'], row['hazard_status']),
            'Quantity': parse_quantity(row['quantity']),
            'Labelled': 'YES' if row['labelled'].lower() == 'yes' else 'NO',
            'Label Details': 'Labelled' if row['labelled'].lower() == 'yes' else None,
            'Hygienist Recommendations': row['comments'] if row['comments'] != '-' else None,
            'Additional Comments': extract_color_note(row['item_description']),
        }
        
        bar_rows.append(bar_row)
    
    return bar_rows
```

---

## Performance Benchmarks (Expected)

| Metric | Qwen2.5-VL 32B Q4 | Llama3.2-Vision 11B |
|--------|-------------------|---------------------|
| Pages/minute | ~2-3 | ~5-6 |
| Table accuracy | 92-95% | 85-88% |
| VRAM usage | ~18GB | ~8GB |
| Batch processing (10 PDFs) | ~15-20 min | ~8-10 min |

**Accuracy Factors:**
- Clean scanned PDFs: +5%
- Complex merged cells: -3%
- Handwritten annotations: -10%
- Low resolution: -8%

---

## Deployment Options

### Option 1: Simple Script (Recommended for Start)

```bash
# Directory structure
asbestos-extractor/
├── main.py
├── extractors/
│   ├── cover.py
│   ├── register.py
│   └── lab_report.py
├── transformers/
│   └── bar_mapper.py
├── utils/
│   ├── pdf_utils.py
│   └── excel_writer.py
└── config/
    ├── field_mappings.yaml
    └── product_lookups.yaml
```

### Option 2: n8n Workflow Integration

Build as n8n custom node or use:
- PDF Split node → Image conversion
- HTTP Request nodes → Local Ollama API
- Code nodes → Python transformation
- Spreadsheet node → Excel output

### Option 3: Full RAG System

If they need querying/search across historical reports:
- Ingest all PDFs into vector store
- Use hybrid search (semantic + keyword)
- Chat interface for "Find all sites with friable asbestos"

---

## Next Steps

1. **Validate model selection** - Run benchmarks on 3-5 sample PDFs
2. **Refine prompts** - Iterate on extraction prompts for edge cases
3. **Build lookup tables** - Complete ACM Product Group/Type mappings
4. **Error handling** - Handle malformed tables, missing data
5. **Human review UI** - Build simple interface for QA checks

---

## Questions for Client

1. Are all PDFs from Prensa, or multiple consultants? (affects template variations)
2. Do they need the photograph column extracted?
3. What's the expected volume? (affects batching strategy)
4. Do they need incremental updates or full regeneration?
5. Integration with existing systems (SharePoint, database)?

---

*Analysis prepared for Raava Innovations*
