# ACM-AI Extraction Pipeline Architecture

> **Version:** 1.0
> **Date:** 2026-02-05
> **Pattern:** Two-Stage (Extract → Interpret)

This document defines the extraction pipeline architecture for processing asbestos assessment PDFs into BAR-compliant records.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ACM-AI Extraction Pipeline                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 0: PREFLIGHT                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────────────────────┐  │
│  │ PDF Upload  │───▶│ PDF Classifier│───▶│ Parser Router                 │  │
│  └─────────────┘    │ (digital/scan)│    │ (Docling + MinerU)            │  │
│                     └──────────────┘    └────────────────────────────────┘  │
│                                                                              │
│  STAGE 1: EXTRACT (Verbatim with Provenance)                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────────┐ │ │
│  │ │   Docling    │   │    MinerU    │   │   Consultant Parser         │ │ │
│  │ │ (Text/Layout)│   │ (Tables→HTML)│   │   (Format-specific)         │ │ │
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
│  │                           │                                            │ │
│  │                           ▼                                            │ │
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

---

## Stage 0: Preflight

### Purpose
Classify the input PDF and route to appropriate parsers.

### PDF Classification
```python
class PDFType(Enum):
    DIGITAL_TEXT = "digital"      # Native PDF with embedded text
    SCANNED_IMAGE = "scanned"     # Scanned document requiring OCR
    HYBRID = "hybrid"             # Mixed digital and scanned pages
```

### Parser Selection
| PDF Type | Text Parser | Table Parser |
|----------|-------------|--------------|
| Digital | Docling | MinerU |
| Scanned | Docling + OCR | MinerU + Vision Model |
| Hybrid | Per-page routing | Per-page routing |

### Consultant Detection
```python
CONSULTANT_MARKERS = {
    "prensa": ["Prensa Pty Ltd", "Division 5 Asbestos Assessment"],
    "greencap": ["Greencap", "Asbestos Risk Assessment"],
    "generic": []  # Fallback
}
```

---

## Stage 1: EXTRACT

### Purpose
Extract **verbatim values** from the PDF with **full provenance tracking**.

### Key Principle
> **Do NOT normalize at this stage.** Keep original consultant wording exactly as written.

### Output Schema: `RawExtraction`

```python
@dataclass
class SourceLocation:
    """Provenance tracking for extracted values"""
    page: int
    table_id: Optional[int] = None
    row: Optional[int] = None
    col: Optional[int] = None
    bbox: Optional[tuple[float, float, float, float]] = None  # x1, y1, x2, y2
    confidence: float = 1.0

@dataclass
class RawACMItem:
    """Single ACM item extracted verbatim from PDF"""
    # Raw fields from PDF (consultant-specific naming)
    area_level: Optional[str] = None
    room_location: Optional[str] = None
    feature: Optional[str] = None
    item_description: Optional[str] = None
    hazard_type: Optional[str] = None
    hazard_status: Optional[str] = None
    sample_number: Optional[str] = None
    friability: Optional[str] = None
    labelled: Optional[str] = None
    disturbance_potential: Optional[str] = None
    condition: Optional[str] = None
    risk_status: Optional[str] = None
    quantity: Optional[str] = None
    control_priority: Optional[str] = None
    comments: Optional[str] = None
    photo_reference: Optional[str] = None

    # Provenance
    source: SourceLocation

@dataclass
class DocumentMeta:
    """Metadata extracted from PDF header/cover"""
    consultant: str
    client: Optional[str] = None
    site_name: Optional[str] = None
    building_name: Optional[str] = None
    address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    inspection_date: Optional[str] = None
    job_number: Optional[str] = None
    year_built: Optional[int] = None
    building_size_m2: Optional[float] = None
    number_of_levels: Optional[int] = None
    construction_type: Optional[str] = None
    roof_type: Optional[str] = None

@dataclass
class RawExtraction:
    """Complete extraction output from Stage 1"""
    document_meta: DocumentMeta
    items: list[RawACMItem]
    extraction_timestamp: datetime
    parser_version: str
```

### Extraction Components

#### Docling (Text + Layout)
- Page text extraction
- Section header detection
- Building/Room hierarchy parsing
- Cover page metadata

#### MinerU (Table Extraction)
- Complex table detection
- Merged cell handling
- Multi-page table continuity
- HTML structure output

### Consultant-Specific Parsers

```python
class ConsultantParser(ABC):
    """Abstract base for consultant-specific extraction logic"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Consultant identifier"""

    @abstractmethod
    def detect(self, text: str) -> bool:
        """Returns True if this parser handles this PDF"""

    @abstractmethod
    def extract_metadata(self, pages: dict[int, str]) -> DocumentMeta:
        """Extract document metadata from cover/header pages"""

    @abstractmethod
    def extract_items(self, tables: list[dict]) -> list[RawACMItem]:
        """Extract ACM items from table data"""

    @abstractmethod
    def get_register_headers(self) -> list[str]:
        """Expected column headers for this format"""
```

#### Prensa Parser
```python
class PrensaParser(ConsultantParser):
    name = "prensa"

    HEADERS = [
        "area / level", "room & location", "feature", "item description",
        "hazard type", "hazard status", "sample number", "friability",
        "labelled y/n", "disturb. potential", "condition", "risk status",
        "approx. quantity", "control priority", "comments & recommendations"
    ]

    def detect(self, text: str) -> bool:
        return "Prensa Pty Ltd" in text or "Division 5 Asbestos Assessment" in text
```

#### Greencap Parser
```python
class GreencapParser(ConsultantParser):
    name = "greencap"

    HEADERS = [
        "item no.", "location - item description", "hazard type",
        "sample no.", "item status", "photo no.", "est. extent",
        "condition", "friability", "dist. potential", "risk rating",
        "current label", "reinspect date", "control priority"
    ]

    def detect(self, text: str) -> bool:
        return "Greencap" in text
```

---

## Stage 2: INTERPRET

### Purpose
Transform raw extraction into **BAR-compliant** `ACMRecord` with:
- Field mapping (consultant columns → BAR columns)
- Value normalization (synonyms → controlled enums)
- Taxonomy classification (item description → Product Group/Type)
- Business rule application
- Validation

### Processing Steps

#### Step 1: Field Mapping
```python
PRENSA_TO_BAR = {
    "area_level": "level",
    "room_location": "room_name",
    "feature": "location",
    "item_description": "product",
    "hazard_status": "sample_result",
    "sample_number": "nata_sample_number",
    "friability": "friable",
    "labelled": "labelled",
    "condition": "material_condition",
    "disturb_potential": "disturbance_potential",
    "quantity": "extent",
    "comments": "hygienist_recommendations",
}
```

#### Step 2: Value Normalization
```python
SAMPLE_RESULT_SYNONYMS = {
    "positive": "Positive",
    "pos": "Positive",
    "negative": "Negative",
    "neg": "Negative",
    "presumed": "Assumed Positive",
    "presumed positive": "Assumed Positive",
    "assumed": "Assumed Positive",
    "not sampled": "Assumed Positive",  # If appears in register, assumed positive
}

CONDITION_SYNONYMS = {
    "good": "Good",
    "fair": "Fair",
    "poor": "Poor",
    "-": None,  # Not applicable
    "n/a": None,
}

DISTURBANCE_SYNONYMS = {
    "low": "Low",
    "medium": "Moderate",  # Note: BAR uses "Moderate", not "Medium"
    "high": "High",
    "-": None,
}
```

#### Step 3: Taxonomy Classification
```python
def classify_product(item_description: str, friability: str) -> tuple[str, str]:
    """
    Classify ACM item into Product Group and Product Type.

    Returns: (product_group, product_type)
    """
    taxonomy = FRIABLE_TAXONOMY if friability == "Friable" else NONFRIABLE_TAXONOMY

    # Pattern-based classification
    patterns = [
        (r"vinyl\s*(sheet|flooring)", "T3 Vinyl products", "Vinyl sheet"),
        (r"vinyl\s*tile", "T3 Vinyl products", "Vinyl Tiles"),
        (r"hessian\s*back", "T3 Vinyl products", "Hessian backed Vinyl sheet"),
        (r"(fibre|fiber)\s*cement|fc\s*sheet|flat\s*sheet", "T1 Cement products", "Flat Sheeting"),
        (r"mastic|flange.*mastic", "T4 Gasket products", "Mastic"),
        (r"gasket", "T4 Gasket products", "Gasket(s)"),
        (r"insulation|lagging", "T8 Insulation" if not friability == "Friable" else "T3 Insulation products", "Insulation"),
    ]

    desc_lower = item_description.lower()
    for pattern, group, ptype in patterns:
        if re.search(pattern, desc_lower):
            return (group, ptype)

    # LLM fallback for unclear cases
    return classify_with_llm(item_description, taxonomy)
```

#### Step 4: Business Rules
```python
def apply_business_rules(record: ACMRecord) -> ACMRecord:
    """Apply BAR business rules to record"""

    # Rule 1: Negative sample handling
    if record.sample_result in ["Negative", "Assumed Negative"]:
        record.material_condition = f"N/A ({record.sample_result.lower()})"
        record.disturbance_potential = f"N/A ({record.sample_result.lower()})"

    # Rule 2: Sample number normalization
    if record.nata_sample_number:
        if record.nata_sample_number.lower().startswith("same as"):
            record.nata_sample_number = record.nata_sample_number.replace(
                "same as", "As Per"
            ).strip()

    return record
```

#### Step 5: Validation
```python
def validate_record(record: ACMRecord) -> list[ValidationError]:
    """Validate record against BAR schema"""
    errors = []

    # Required field check
    for field in REQUIRED_FIELDS:
        if getattr(record, field) is None:
            errors.append(ValidationError(field, "Required field is missing"))

    # Enum validation
    if record.sample_result not in SAMPLE_RESULT_ENUM:
        errors.append(ValidationError("sample_result", f"Invalid value: {record.sample_result}"))

    if record.material_condition not in CONDITION_ENUM:
        errors.append(ValidationError("material_condition", f"Invalid value: {record.material_condition}"))

    return errors
```

#### Step 6: Recommendation Normalization
```python
RECOMMENDATION_PATTERNS = [
    (r"\bMaintain in current condition\b", "maintain_in_situ"),
    (r"\blabel( and incorporate)? into an AMP\b", "maintain_in_situ"),
    (r"\bRemove (under|by) .*licensed asbestos removal contractor\b", "remove_prior_to_refurb"),
    (r"\bprior to demolition or refurbishment\b", "remove_prior_to_refurb"),
    (r"\bRestrict access\b|\bASAP\b", "restrict_access_immediately"),
    (r"\bwithin\s*3\s*months\b|\bnext few months\b", "remedial_within_months"),
]

def normalize_recommendation(raw_recommendation: str) -> str:
    """Map consultant wording to canonical action"""
    for pattern, action in RECOMMENDATION_PATTERNS:
        if re.search(pattern, raw_recommendation, re.IGNORECASE):
            return action
    return "review_required"
```

---

## Output: ACMRecord

The final output is a fully validated `ACMRecord` that:
1. Conforms to official BAR schema
2. Has all enum values from controlled vocabularies
3. Has product classification from taxonomy
4. Includes full provenance tracking
5. Passes all validation rules

```python
@dataclass
class ACMRecord:
    """BAR-compliant ACM record"""
    id: str
    source_id: str

    # Organization (from site config)
    department: str
    agency: str
    sub_agency: Optional[str]
    site_name: Optional[str]

    # Building (47 fields total - see bar-schema.md)
    # ...

    # Provenance
    page_number: int
    extraction_confidence: float
    raw_extraction_id: str  # Link to Stage 1 output
```

---

## Implementation Notes

### File Locations
```
open_notebook/
├── extraction/
│   ├── __init__.py
│   ├── pipeline.py          # Main pipeline orchestrator
│   ├── stage1_extract.py    # Stage 1 logic
│   ├── stage2_interpret.py  # Stage 2 logic
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py          # ConsultantParser ABC
│   │   ├── prensa.py        # Prensa parser
│   │   ├── greencap.py      # Greencap parser
│   │   └── generic.py       # Fallback parser
│   ├── normalizers/
│   │   ├── __init__.py
│   │   ├── enums.py         # Enum normalization
│   │   ├── taxonomy.py      # Product classification
│   │   └── recommendations.py # Recommendation normalization
│   └── validators/
│       ├── __init__.py
│       └── bar_schema.py    # BAR validation rules
```

### Dependencies
```toml
[project.dependencies]
docling = ">=0.1.0"
mineru = {version = ">=0.1.0", extras = ["all"]}
pdfplumber = ">=0.10.0"
```

---

## References

- Two-stage design: `docs/samplePDF/instructions-sample/pipeline_design_extract_interpret.md`
- BAR schema: `docs/reference/bar-schema.md`
- Product taxonomy: `docs/reference/product-taxonomy.md`
