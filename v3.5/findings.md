# Findings: Row Segmentation & Table Edge Cases

**Date:** 2026-03-07 (Updated)
**Decisions:**
- Primary input: **DoclingDocument JSON** (lossless — retains row_span, col_span, page_no, bbox, header flags)
- LLM prompt format: **Key-value pairs** (simplest for small Ollama models)
- Debug export: **HTML secondary** (for visual inspection alongside JSON primary)
- TableFormer mode: **ACCURATE** with `do_cell_matching=True`

---

## 1. Why DoclingDocument JSON Over HTML

| Capability | JSON | HTML | Markdown |
|------------|:----:|:----:|:--------:|
| Merged cell span info (`row_span`, `col_span`) | ✅ exact integers | ✅ attrs | ❌ flattened |
| Cell position (`start_row_offset_idx`, `start_col_offset_idx`) | ✅ | ❌ infer from DOM | ❌ |
| Page number per table (`prov.page_no`) | ✅ | ❌ lost | ❌ lost |
| Bounding box per cell | ✅ | ❌ lost | ❌ lost |
| Header detection (`column_header` flag) | ✅ explicit bool | Partial (`<th>`) | ❌ |
| Grid dimensions (`num_rows`, `num_cols`) | ✅ explicit | Count DOM elements | Count pipes |
| Empty cells | ✅ explicit empty text | Sometimes collapsed | Collapsed |
| Lossless round-trip | ✅ | ❌ | ❌ |

### Docling Config

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
result = converter.convert(pdf_path)
doc_json = result.document.export_to_dict()
```

### Known TableFormer Limitations
1. **Dropped cell text:** Short/bullet text occasionally missing from output despite being in input tokens. Must detect and recover via raw PDF text.
2. **First column misidentification:** Sometimes not recognized as table. No config fix.
3. **Columnar merge artifacts:** Adjacent narrow columns merged into one.

**Mitigation:** Compare extracted row count against heuristic expectation. If low, flag for review or fall back to MinerU/text.

---

## 2. Edge Case Catalog

### Type A: Standard Single-Page Table (EASY, ~60%)
JSON cells grouped by `start_row_offset_idx`. Skip `column_header: true` rows. Each remaining group = one `RawTableRow`.

### Type B: Multi-Page Table (COMMON, ~25%)
Multiple table objects with same `num_cols`. Merge, deduplicate overlap rows (compare last row of table N with first data row of table N+1 by text). Carry forward headers.

### Type C: Merged Cells — Room Spanning Items (COMMON, ~40%)
JSON provides `row_span: 3` on room cell. Build span registry: `{(row_idx, col_idx): cell_text}`. When assembling row N+1, fill from registry. Mark `carried_forward_fields`.

### Type D: Hierarchical Text / No Table (UNCOMMON, ~5%)
No table objects for building's page range. Fall back to Markdown text parsing with regex for level/room/item patterns. Create synthetic rows with `is_synthetic=True`.

### Type E1: Multi-Item Cell (~5% of rows)
Single cell contains `\n`-separated items + material keywords. Flag `needs_llm_split=True`. LLM splits into individual items.

### Type E2: Note/Comment Row
Single cell spanning all columns, no material keywords. Skip. Store text in `extraction_notes`.

### Type E3: Sub-Header Row
Single cell spanning all columns, matches level regex `^(LEVEL|GROUND|FIRST|SECOND|ROOF|BASEMENT|EXTERNAL)\b`. Update `current_level` context for subsequent rows.

### Type F: Not Sampled / No Access (KNOWN GAP, ~5-10%)
Not in tables. Regex scan of raw Markdown: `{location} [—–-] ["']?(Not Sampled|No Access)["']?`. Create synthetic rows.

### Type G: Different Column Orders (~30% of PDFs)
Fuzzy match headers to canonical names using `COLUMN_ALIASES` dict with `rapidfuzz.fuzz.ratio()` at 70% threshold.

```python
COLUMN_ALIASES = {
    "room_location": ["room", "room/area", "area", "location", "room no"],
    "item_description": ["material", "product", "item", "description", "product description", "acm type"],
    "friability": ["friable", "f/nf", "friability", "type"],
    "condition": ["condition", "material condition", "state", "assessment"],
    "sample_number": ["sample", "sample#", "sample no", "nata no"],
    "sample_result": ["result", "lab result", "analysis"],
    "quantity": ["quantity", "qty", "area", "extent", "m²"],
    "recommendation": ["recommendation", "action", "management"],
    "accessibility": ["access", "accessible"],
    "asbestos_type": ["asbestos type", "fibre type", "fibre"],
    "disturbance_potential": ["disturbance", "dp", "risk"],
    "specific_location": ["specific location", "position", "element", "where"],
}
```

### Type H: Split/Fragmented Tables (RARE, ~2%)
Two table objects with different `num_cols` but shared key column. JOIN on shared column by header fuzzy match.

---

## 3. RawTableRow Data Model

```python
from pydantic import BaseModel, Field
from typing import Optional

class RawTableRow(BaseModel):
    """One row from a PDF table, ready for per-row LLM extraction."""
    
    # Source tracking
    source_id: str
    building_id: str
    table_index: int = Field(description="Which table within building (0-indexed)")
    row_index: int = Field(description="Row position within table (0-indexed)")
    page_number: int = Field(description="PDF page from Docling prov.page_no")
    
    # Content (from DoclingDocument JSON)
    cells: dict[str, str] = Field(description="Column header → cell value. Canonical names where mapped.")
    raw_text: str = Field(description="Plain text concatenation for fallback/debug")
    
    # Column mapping
    column_mapping: dict[str, str] = Field(default_factory=dict, description="Canonical → original header")
    
    # Segmentation metadata
    confidence: float = Field(default=1.0)
    needs_llm_split: bool = Field(default=False, description="Multi-item cell, Type E1")
    is_synthetic: bool = Field(default=False, description="From text scan, not table (Type D/F)")
    carried_forward_fields: list[str] = Field(default_factory=list, description="Merged cell inheritance (Type C)")
    edge_case_type: Optional[str] = Field(default=None, description="A, B, C, D, E1, E2, E3, F, G, H")
    extraction_notes: Optional[str] = Field(default=None, description="Context from note/sub-header rows")
    current_level: Optional[str] = Field(default=None, description="Floor/level from sub-header (Type E3)")
    
    # Provenance from Docling JSON
    source_table_num_rows: Optional[int] = Field(default=None)
    source_table_num_cols: Optional[int] = Field(default=None)
    bbox: Optional[dict] = Field(default=None, description="Bounding box from Docling prov")
    
    # HTML debug
    debug_html: Optional[str] = Field(default=None, description="HTML <tr> for visual debugging")
```

---

## 4. Per-Row LLM Prompt — Key-Value Pairs

### Standard Row
```
SYSTEM:
You extract one ACM item from a building register row.
Fill JSON fields using ONLY the row data. If not present, set null.
Respond with ONLY valid JSON.

HUMAN:
Building: Main Block (Primary school — Single storey, 1965, Brick veneer)
Level: Ground Floor

Row data:
  Room: Room 101
  Location: Ceiling
  Material: Suspended ceiling tiles with asbestos binder
  Friable: No
  Condition: Good
  Sample Number: 34511-039-001
  Result: Positive - Chrysotile
  Quantity: 50 m²
  Recommendation: Maintain in situ
```

### Building KV from RawTableRow
```python
def build_kv_prompt(row: RawTableRow, building_context: str) -> str:
    lines = [f"Building: {building_context}"]
    if row.current_level:
        lines.append(f"Level: {row.current_level}")
    if row.extraction_notes:
        lines.append(f"Note: {row.extraction_notes}")
    lines.append("\nRow data:")
    for canonical, value in row.cells.items():
        if value.strip():
            original = row.column_mapping.get(canonical, canonical)
            lines.append(f"  {original}: {value}")
    return "\n".join(lines)
```

---

## 5. Deterministic Post-Processing (No LLM)

```
ACMItemRowSimple (from LLM)
  → is_friable bool → "Friable" / "Non-friable"
  → item_description → classify_product() → Classification + Sub-Classification
  → condition → normalize_enum_value() → SF picklist value
  → recommendation → normalize_recommendation() → canonical
  → Business rule: Negative → N/A for condition + disturbance
  → Dependency chain validation (Python)
  → ACMRecord (full SF field names, ready for Salesforce)
```

---

## 6. Multiple Tables Per Building

| Scenario | Detection | Strategy |
|----------|-----------|----------|
| 1 table | `len(tables) == 1` | Parse directly |
| 2+ tables, same `num_cols` | Column count match | Merge (Type B), deduplicate overlaps |
| 2+ tables, different `num_cols` | Mismatch + shared key col | JOIN (Type H) |
| 0 tables | No table objects in range | Text parsing (Type D) + scan (Type F) |
| Table + inline text | Both present | Table → rows, then text scan for Type F |

---

## 7. HTML Debug Export

Generate `debug_html` per row and full debug table per building for browser inspection:

```python
def generate_debug_html(row: RawTableRow) -> str:
    cells_html = "".join(f"<td>{html.escape(v)}</td>" for v in row.cells.values())
    flags = []
    if row.carried_forward_fields: flags.append(f"merged:{','.join(row.carried_forward_fields)}")
    if row.needs_llm_split: flags.append("needs_split")
    if row.is_synthetic: flags.append("synthetic")
    if row.edge_case_type: flags.append(f"type:{row.edge_case_type}")
    flag_attr = f' data-flags="{" ".join(flags)}"' if flags else ""
    return f"<tr{flag_attr}>{cells_html}</tr>"
```

---

## 8. Open Questions

1. **Confidence threshold:** ≥0.8 auto-extract, <0.8 extract + flag?
2. **MinerU fallback priority:** Use MinerU `raw_extraction_table` when Docling tables empty?
3. **Column mapping cache:** Store in `ExtractionState` dict (per-pipeline-run) or DB (persist)?
4. **TableFormer text drops:** When detected, should we re-extract with `do_cell_matching=False` as retry?
