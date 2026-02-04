# Research Findings: ACM-AI Extraction Pipeline

> **Purpose:** Consolidated research findings for PRD/Architecture updates
> **Date:** 2026-02-05
> **Sources:** docs/samplePDF/analysis/*, docs/samplePDF/instructions-sample/*

---

## 1. Official BAR Schema Analysis

### Source: `register_row.schema.json`

The official Victorian BAR (Building Asbestos Register) has **47 columns** (A-AU):

| Column | Field Name | Type | Required | Notes |
|--------|------------|------|----------|-------|
| A | Department | string | Yes | DJCS, DHHS, DET, DOT, DJPR |
| B | Agency | string | Yes | Victoria Police, etc. |
| C | Sub Agency | string | Optional | |
| D | Site Name (if applicable) | string | Optional | |
| E | Building Name | string | Yes | |
| F | Building Type | string | Yes | |
| G | Building Address | string | Yes | |
| H | Suburb | string | Yes | |
| I | Postcode | string | Yes | |
| J | Owned or Leased | enum | Yes | [Owned, Leased] |
| K | Building Unique ID | string | Yes | |
| L | Frequency of use | enum | Yes | See enums |
| M | Public Access? | enum | Optional | [YES, NO] |
| N | Date of Inspection | date | Yes | |
| O | Estimated Year Built | number | Yes | |
| P | Est. Building Size (m2) | number | Yes | |
| Q | Number of Levels | number | Yes | |
| R | Construction Type | string | Yes | |
| S | Roof Type | string | Yes | |
| T | Internal / External | enum | Yes | [Internal, External, External & Internal] |
| U | Level | string | Yes | |
| V | Room or Area | string | Yes | |
| W | Location in Room | string | Yes | |
| X | Specific Item/ACM Name | string | Yes | |
| Y | Friability of material | enum | Yes | [Non-friable, Friable] |
| Z | FRIABILITY NAME EXCEL | string | Yes | Display name |
| AA | ACM Product Group | string | Yes | From taxonomy |
| AB | ACM GROUP NAME EXCEL | string | Yes | Display name |
| AC | ACM Product Type | string | Yes | From taxonomy |
| AD | NATA Endorsed Sample number | string | Yes | |
| AE | Sample Result | enum | Yes | [Positive, Assumed Positive, Negative, Assumed Negative] |
| AF | Identifying Hygiene Company | string | Yes | |
| AG | Condition | enum | Yes | [Poor, Fair, Good, Unknown, N/A (negative), N/A (assumed negative)] |
| AH | Disturbance Potential | enum | Yes | [High, Moderate, Low, Unknown, N/A (negative), N/A (assumed negative)] |
| AI | Quantity | number | Recommended | |
| AJ | Labelled | enum | Recommended | [YES, NO] |
| AK | Label Details | string | Recommended | |
| AL | Hygienist Recommendations | string | Recommended | |
| AM | Additional Comments | string | Recommended | |
| AN | PSB Supplied ACM ID | string | Recommended | |
| AO | Assumed Removed? | enum | Recommended | [YES, NO] |
| AP | Date of Removal | date | Recommended | |
| AQ | Quantity Removed | number | Recommended | |
| AR | Asbestos Removal Notification No | string | Recommended | |
| AS | EPA Waste Transport Certificate No | string | Recommended | |
| AT | Removal Comments | string | Recommended | |
| AU | Photo Reference Number | string | Recommended | |

### Key Differences from Current PRD

| Current PRD Field | Official BAR Field | Action |
|-------------------|-------------------|--------|
| `area_type` | `Internal / External` | Rename |
| `material_condition` | `Condition` | Rename |
| `extent` | `Quantity` | Rename |
| `hygiene_company` | `Identifying Hygiene or Consulting Company` | Rename |
| `risk_status` | (not in BAR) | Keep as derived field |
| Missing | `FRIABILITY NAME EXCEL` | Add |
| Missing | `ACM GROUP NAME EXCEL` | Add |
| Missing | `Removal Comments` | Add |
| Missing | `Photo Reference Number` | Add |

---

## 2. Enum Definitions

### Source: `register_enums.json`

#### SampleResult
```json
["Positive", "Assumed Positive", "Negative", "Assumed Negative"]
```

#### Condition
```json
["Poor", "Fair", "Good", "Unknown", "N/A (negative)", "N/A (assumed negative)"]
```

#### DisturbancePotential
```json
["High", "Moderate", "Low", "Unknown", "N/A (negative)", "N/A (assumed negative)"]
```
**Note:** Current PRD uses "Medium" - should be "Moderate"

#### Friability
```json
["Non-friable", "Friable"]
```

#### FrequencyOfUse
```json
[
  "Every day",
  "Every day with intermittent breaks",
  "Once every 3–5 days",
  "Every 2–3 weeks",
  "Once every 2–3 months",
  "Annually or less frequently"
]
```

#### InternalExternal
```json
["Internal", "External", "External & Internal"]
```
**Note:** Current PRD missing "External & Internal" option

#### SpecificUses (319 items)
Location-in-room values including:
- Above door, Air conditioning trunking, Ceiling, Floor covering
- Pipe insulation, Switchboard, Tile backing, etc.

---

## 3. ACM Product Taxonomy

### Source: `register_taxonomy.nonfriable.json` and `register_taxonomy.friable.json`

### Non-Friable Taxonomy (8 Groups)

| Code | Product Group | Sample Product Types |
|------|---------------|---------------------|
| T1 | Cement products | Flat Sheeting, Corrugated Roof Sheeting, Ridge Capping, Weatherboards |
| T2 | Bitumen products | Mastic, Bituminous Membrane, Malthoid, Electrical Components |
| T3 | Vinyl products | Vinyl sheet, Vinyl Tiles, Hessian backed Vinyl sheet |
| T4 | Gasket, friction products | Flange Gaskets, Mastic, Brake pads, Caulking |
| T5 | Coatings | Paint, Textured Coating |
| T6 | Reinforced plastics/resins | Electrical Components, Plastic, Toilet Cisterns |
| T7 | Other | Concrete, Mortar, Render, Grout, Paper |
| T8 | Insulation | Millboard, Lagging, Loose Fill Insulation, Fire Door Core |

### Friable Taxonomy (6 Groups)

| Code | Product Group | Sample Product Types |
|------|---------------|---------------------|
| T1 | Cement products (f) | Flat Sheeting, Tilux sheeting (friable versions) |
| T2 | Vinyl products (f) | Millboard/paper-backed sheet vinyl |
| T3 | Insulation products (f) | AIB, Lagging, Sprayed Insulation, Vermiculite |
| T4 | Gasket products (f) | Rope or Braided Gasket, Flange Gaskets |
| T5 | Textiles (f) | Fire blanket, Cloth, Gloves |
| T6 | Other (f) | Plaster/lath, Mortar |

### Classification Logic

```python
def classify_acm(item_description: str, friability: str) -> tuple[str, str]:
    """Returns (product_group, product_type)"""
    taxonomy = FRIABLE_TAXONOMY if friability == "Friable" else NONFRIABLE_TAXONOMY

    # Pattern matching logic
    for group in taxonomy["groups"]:
        for product_type in group["product_types"]:
            if product_type_matches(item_description, product_type):
                return (group["product_group_header"], product_type)

    return ("T7 Other", "Unknown")
```

---

## 4. Two-Stage Pipeline Design

### Source: `pipeline_design_extract_interpret.md`

### Stage 0: Preflight
1. Classify PDF type (digital vs scanned)
2. Choose parser (MinerU for tables, Docling for text)
3. Create page-level artifacts

### Stage 1: EXTRACT (Evidence → Raw Fields)

**Goal:** Extract verbatim values with provenance

**Output:** `raw_extraction.json`
```json
{
  "document_meta": {
    "client": "Victoria Police",
    "site": "Broadmeadows Police Station",
    "job_number": "34511-039",
    "inspection_date": "2020-04-08",
    "consultant": "Prensa Pty Ltd"
  },
  "items": [
    {
      "area_level": "Ground floor",
      "room_location": "Main foyer",
      "feature": "Floor",
      "item_description": "Vinyl sheet (cream)",
      "hazard_status": "Negative",
      "sample_number": "34511-039-001",
      "_source": {
        "page": 5,
        "table_id": 1,
        "row": 3,
        "confidence": 0.95
      }
    }
  ]
}
```

**Rule:** Do NOT normalize wording - keep original consultant phrasing

### Stage 2: INTERPRET (Raw → BAR-compliant)

**Goal:** Transform raw extraction to official BAR schema

**Steps:**
1. **Field mapping** - PDF columns → BAR columns
2. **Normalization** - Convert synonyms to controlled enums
3. **Derived rules** - If Negative/Assumed Negative, certain fields N/A
4. **Consultant wording → Canonical actions** - See normalization rules
5. **Validation** - Against register_row.schema.json
6. **Excel writer** - Output to BAR format

---

## 5. Consultant Wording Normalization

### Source: `consultant_wording_rules.json`

### Universal Actions

| Action | Description |
|--------|-------------|
| `maintain_in_situ` | Keep ACM in place, label, periodic review |
| `remove_prior_to_refurb_or_demolition` | Remove before demolition by licensed contractor |
| `restrict_access_immediately` | Restrict access and arrange abatement ASAP |
| `remedial_within_months` | Organise remedial works within ~3 months |
| `confirm_status_sampling` | Item not sampled; confirm via sampling |
| `height_or_access_restriction` | No access/height restriction; treat as presumed |

### Mapping Patterns

```json
{
  "\\bMaintain in current condition\\b": "maintain_in_situ",
  "\\blabel( and incorporate)? into an AMP\\b": "maintain_in_situ",
  "\\bRemove (under|by) .*licensed asbestos removal contractor\\b": "remove_prior_to_refurb_or_demolition",
  "\\bprior to demolition or refurbishment\\b": "remove_prior_to_refurb_or_demolition",
  "\\bRestrict access\\b|\\bASAP\\b": "restrict_access_immediately",
  "\\bwithin\\s*3\\s*months\\b|\\bnext few months\\b": "remedial_within_months"
}
```

---

## 6. MinerU Integration Points

### Source: `acm_ai_pdf_extraction_stack_analysis.md`

### Recommended Architecture

```
PDF Upload
    ↓
PDF Router (type detection)
    ↓
┌───────────────┬────────────────┐
│   Docling     │    MinerU      │
│ (Text+Layout) │ (Tables→HTML)  │
└───────┬───────┴───────┬────────┘
        │               │
        └───────┬───────┘
                ↓
        Content Merger
        (Page-aware assembly)
                ↓
        LLM Extraction Layer
        (Field mapping, validation)
                ↓
        ACMRecord Pydantic Model
```

### MinerU Capabilities
- Table detection: 5/5 stars
- Merged cell handling: 5/5 stars
- Multi-page tables: 4/5 stars
- Python native: Yes
- Self-hosted: Yes

### Installation
```bash
pip install mineru[all]
```

---

## 7. Sample Extractor Code Analysis

### Source: `asbestos_extractor.py`

### Key Patterns from Prototype

**ACM Product Mappings:**
```python
ACM_PRODUCT_MAPPINGS = {
    r'vinyl\s*(sheet|flooring)': ('Vinyl products', 'Vinyl sheet'),
    r'vinyl\s*tile': ('Vinyl products', 'Vinyl Tiles'),
    r'hessian\s*back': ('Vinyl products', 'Hessian backed Vinyl sheet'),
    r'(flange\s*)?mastic': ('Gasket, friction products', 'Mastic'),
    r'(fibre|fiber)\s*cement|fc\s*sheet': ('Cement products', 'Flat Sheeting'),
}
```

**Level Normalization:**
```python
def normalize_level(area_level: str) -> str:
    if 'ground' in area_level.lower():
        return 'Ground'
    elif 'first' in area_level.lower() or 'level 1' in area_level.lower():
        return 'Level 1'
    elif 'external' in area_level.lower():
        return 'Ground'  # External typically ground-referenced
    return area_level
```

**Internal/External Classification:**
```python
external_keywords = ['external', 'roof', 'boiler room', 'fan room', 'exterior', 'outside']
```

---

## 8. BAR Data Entry Rules

### Source: `alexander_instructions.txt`

### Key Rules
1. **Required fields:** A, B, E-L, N-AH
2. **Optional fields:** C, D, M, AI
3. **Conditional:** If Sample Result is 'negative' or 'assumed negative', leave AG (Condition) and AH (Disturbance Potential) as N/A
4. **Stop condition:** Stop entering data if building is leased (column L)
5. **No deletion:** Do not delete pre-populated data
6. **Removed ACM:** ACM that has been entirely removed does NOT need to be entered

---

## 9. Consultant Format Differences

### Prensa Format
- Headers: area/level, room & location, feature, item description, hazard status, sample number, friability, labelled y/n, condition, risk status
- Building pattern: "Ground floor", "First floor", "Exterior"
- 15 columns in register table

### Greencap Format
- Headers: item no., location-item description, hazard type, sample no., item status, photo no., est. extent, condition, friability, dist. potential, risk rating
- Building pattern: "Building Name: ..."
- Additional metadata: Full Address, Est. Building Size, Est. Building Age
- 14 columns in register table

### Extensibility Pattern
```python
class ConsultantParser(ABC):
    @abstractmethod
    def detect(self, pdf_text: str) -> bool:
        """Returns True if this parser handles this PDF format"""

    @abstractmethod
    def extract_metadata(self, pages: dict) -> DocumentMeta:
        """Extract site/building metadata"""

    @abstractmethod
    def extract_register(self, tables: list) -> list[RawACMItem]:
        """Extract raw ACM items from tables"""

    @abstractmethod
    def get_header_mapping(self) -> dict[str, str]:
        """Map consultant columns to standard fields"""
```

---

## 10. Gap Analysis Summary

| Gap | Current State | Required State | Priority |
|-----|---------------|----------------|----------|
| Pipeline architecture | Single-stage | Two-stage (Extract→Interpret) | High |
| Table extraction | Docling only | MinerU + Docling hybrid | High |
| Field naming | Custom names | Official BAR field names | High |
| Enum values | Incomplete | Full BAR enums | Medium |
| Product taxonomy | Not defined | Full T1-T8 taxonomy | Medium |
| Consultant wording | Not normalized | Regex-based normalization | Medium |
| Multi-consultant | Patterns exist | Formal extensible design | Medium |
| Provenance tracking | Page number only | Full source tracking | Medium |
