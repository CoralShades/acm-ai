# Multi-Consultant PDF Format Adaptability — Architecture Design

> **Status:** Design Complete | **Date:** 2026-03-18 | **Branch:** ACMV3
>
> All documents processed by this pipeline are **ARA (Asbestos Register Assessment)** reports.
> Different consulting firms format the same ARA data differently. This design enables the
> pipeline to handle any consultant's table format without code changes.

---

## 1. Problem Statement

The extraction pipeline currently handles 3 consultant formats (Standard DET, Greencap/ARA, Clutch) via **32 hardcoded patterns** spread across 8 files. Adding a new consultant requires modifying code in 5+ locations. Key issues:

- **11 HIGH-severity patterns** that break extraction for unrecognised formats
- **Column header mapping** (`COLUMN_ALIASES`) is a single flat dict applied to all documents
- **Recovery functions** are calibrated to specific consultant vocabularies
- **LLM prompts** contain hardcoded consultant-specific examples
- **Broken import:** `clutch_detector.py` imports undefined symbols from `building_inventory.py`
- **Code duplication:** `_detect_ara_buildings()` implemented in both `building_inventory.py` and `ara_detector.py`

### Goal

A new consultant PDF format should be processable with **zero code changes** — either via automatic schema inference or by saving a format profile after first encounter.

---

## 2. Current Architecture: Column Header Flow

```
PDF File
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: DoclingAdapter.extract_tables()                        │
│   PDF → DocumentConverter → DoclingDocument                     │
│   Per table: table.data.model_dump() → {table_cells, num_rows}  │
│   Column headers: cells where column_header=True                │
│   Output: NormalizedTable with docling_json                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: source_commands._store_docling_tables()                │
│   NormalizedTable → SurrealDB acm_table_section                 │
│   Stores: raw_html, raw_text (markdown), docling_document_json  │
│   Headers: preserved in docling_document_json.table_cells       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Format Detection (format_detectors/__init__.py)        │
│   StandardFormatDetector → B###/D## headers (DET only)          │
│   ClutchDetector → | Site Details | pipe tables (BROKEN IMPORT) │
│   ARADetector → "Building Name:" text headers                   │
│   LLMDetector → fallback LLM classification                    │
│   Output: format_name, confidence, column_mapping (optional)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: row_segmenter.detect_column_mapping()                  │
│   *** CENTRAL BOTTLENECK ***                                    │
│   Reads header cells from docling_document_json                 │
│   Fuzzy-matches against COLUMN_ALIASES (flat dict, 11 entries)  │
│   Jaro-Winkler threshold: 0.70                                 │
│   Unrecognised headers → col_0, col_1, ... (data lost)         │
│   Output: {canonical_name: original_header_text}                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 5: row_segmenter.segment_docling_table()                  │
│   Builds RawTableRow per data row                               │
│   cells = {canonical_name: value}                               │
│   column_mapping = {canonical: original_header}                 │
│   _LEVEL_REGEX: English floor names only                        │
│   Output: List[RawTableRow]                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 6: row_extractor.build_kv_prompt()                        │
│   Shows ORIGINAL header labels to LLM                           │
│   LLM must produce fixed 13-field ACMItemRow JSON               │
│   Output: LLM response → ACMItemRow                             │
│   *** COLUMN HEADERS LOST AFTER THIS POINT ***                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 7: acm_row_mappers.map_item_row_to_extraction_record()    │
│   Normalizes friability, condition, disturbance, product        │
│   Classifies product → ACM_Classification + Sub_Classification  │
│   Output: ACMExtractionRecord (~35 fields)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 8: ACMRecord → SurrealDB                                  │
│   Each field has dual alias: Python name + SF API name (__c)    │
│   Original column headers: NOT stored                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardcoded Pattern Catalog

### 3.1 HIGH Severity (breaks extraction)

| # | File | Line | Pattern | Assumed Format | Fix |
|---|------|------|---------|---------------|-----|
| 1 | `building_inventory.py` | 29 | `_BUILDING_HEADER` regex `[A-Z]\d+[A-Z]?` | DET only | Move to StandardFormatDetector |
| 2 | `clutch_detector.py` | 13 | `_CLUTCH_BUILDING_NAME_PATTERN` import | **BROKEN** — symbol doesn't exist | Define in building_inventory or clutch_detector |
| 3 | `acm_extraction.py` | 2358 | `_ARA_ITEM_DESC_RE` product vocabulary | Alexander/Prensa | Derive from SF Item_Name__c picklist |
| 4 | `acm_extraction.py` | 2048 | `level_re` / `level_suffix_re` | Broadmeadows | Gate by format or accept RecoveryConfig |
| 5 | `acm_extraction.py` | 2295 | `"Not Sampled"` exact string | ARA/Prensa | Synonym list from config |
| 6 | `acm_extraction.py` | 2321 | `"Restricted Access\|Height Restricted"` | Alexander | Configurable restriction vocabulary |
| 7 | `acm_extraction.py` | 2274 | `section_header_re` "Name - Int/Ext - Level" | ARA only | Format-specific section header pattern |

### 3.2 MEDIUM Severity (degrades quality)

| # | File | Line | Pattern | Fix |
|---|------|------|---------|-----|
| 8 | `row_segmenter.py` | 26–84 | `COLUMN_ALIASES` flat dict (11 entries) | Merge with detector's column_mapping |
| 9 | `row_segmenter.py` | 101 | `_LEVEL_REGEX` English floor names | Accept override from detector |
| 10 | `building_inventory.py` | 35 | `_ROOM_HEADER` B###-R#### | Move to StandardFormatDetector |
| 11 | `clutch_detector.py` | 143 | Hardcoded column mapping | Load from config/DB |
| 12 | `ara_detector.py` | 81 | Hardcoded column mapping | Load from config/DB |
| 13 | `acm_extraction.py` | 2119 | `KNOWN_PRODUCT_KEYWORDS` | Source from SF picklist |
| 14 | `utils.py` | 363 | `_BUDGET_ROOM_RE` / `_BUDGET_ARA_RE` | Accept boundary pattern from detector |
| 15 | `building_inventory.py` | 391 | `_detect_ara_buildings()` duplicated | Delegate to ARADetector |

### 3.3 LOW Severity (cosmetic/docs)

| # | File | Line | Pattern |
|---|------|------|---------|
| 16 | `building_inventory.jinja` | 18–29 | Named consultant format sections |
| 17 | `v3_building_extraction.jinja` | 66–135 | Prensa + DET worked examples |
| 18 | `structure_extraction.jinja` | 54–78 | Named TOC examples |
| 19 | `metadata_extraction.jinja` | 10–44 | Prensa + Greencap named examples |
| 20 | `acm_extractor.py` | 180 | Legacy `SITE_NAME_PATTERN` (deprecated module) |

---

## 4. Salesforce Target Schema Summary

### 4.1 Minimum Viable Record

**Building__c:** `building_name` (required), `internal_id` (pipeline-generated), `source_id` (FK)

**Item__c:** `building_id` (required), `product` / Item_Name__c (required), `material_description` (required, auto-fallback), `result` (required, defaults to "Unknown")

### 4.2 Core Fields (present in every consultant format)

| Field | Typical PDF Variants | SF Target |
|-------|---------------------|-----------|
| Building ID | "Building", "Bldg", "Bldg No", "Asset Code" | Building_Code__c |
| Room/Area | "Room", "Room/Area", "Location", "Area" | Room_or_Area__c |
| Item/Material | "Item Name", "ACM Name", "Description", "Product", "Building Element" | Item_Name__c |
| Friability | "Friability", "F/NF", "Frig." | Friability_of_Material__c |
| Condition | "Condition", "ACM Condition" | Condition__c |
| Sample Result | "Sample Result", "Result", "Analysis Result", "ACM Status" | Sample_Analysis_Result_Material_Status__c |
| Sample Number | "Sample No", "Lab No", "NATA No", "Item No." | NATA_Endorsed_Sample_no__c |
| Recommendations | "Recommendations", "Hygienist Recommendations", "Action" | Hygienist_Recommendations__c |

### 4.3 Dependent Picklist Chains

```
Friability_of_Material__c
  └─→ ACM_Classification__c  (product group — "Cement products" vs "Cement products (f)")
        └─→ ACM_Sub_Classification__c  (product type — ~100+ values)

Building_Type__c
  └─→ Building_Category__c

Sample_Result == "Negative"  →  Condition = "N/A (negative)", Disturbance = "N/A (negative)"
Sample_Result == "Assumed Negative"  →  Condition/Disturbance = "N/A (assumed negative)"
```

### 4.4 Current Mapping Chain

```
PDF Column Header (raw text)
  → COLUMN_ALIASES fuzzy match → canonical name (11 known)
  → build_kv_prompt() → LLM sees original headers
  → ACMItemRow (13 fields) → fixed schema
  → map_item_row_to_extraction_record() → ACMExtractionRecord (~35 fields)
  → ACMRecord → SF API names (__c aliases)
```

---

## 5. Proposed Architecture: Dynamic Schema Inference

### 5.1 Overview

```
PDF → Docling tables → Extract column headers → Schema Inference →
  → Column Mapping → Adaptive Row Segmenter → LLM Extraction → SF Mapping
```

New components (shaded):

```
                    ┌─────────────────────────┐
                    │  ██ FORMAT PROFILE DB ██ │  SurrealDB: consultant_format_profile
                    │  header_signature_hash   │
                    │  column_mapping          │
                    │  level_regex             │
                    │  recovery_config         │
                    └────────┬────────────────┘
                             │ cache hit?
                             │
PDF → Docling ──► ██ SCHEMA INFERENCE NODE ██ ──► Column Mapping
                  │  1. Collect all headers    │     │
                  │  2. Check format profile   │     │
                  │  3. LLM inference (miss)   │     │
                  │  4. HITL confirm (<0.8)    │     │
                  └────────────────────────────┘     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ Adaptive Segmenter   │
                                          │ Dynamic COLUMN_ALIASES│
                                          │ Configurable LEVEL_RE │
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ Format-Aware Prompts │
                                          │ Dynamic field lists   │
                                          │ Format-specific hints │
                                          └──────────────────────┘
```

### 5.2 Schema Inference Node

A new LangGraph node between PREFLIGHT and ORCHESTRATOR.

**Input:**
- All unique column headers from `acm_table_section.docling_document_json` for this source
- First 3 data rows as sample values
- Detected format name (from format detector)

**Process:**
1. Compute `header_signature` = sorted hash of unique header text strings
2. Check `consultant_format_profile` table for cached mapping
3. On **cache hit** (confidence ≥ 0.8): use cached `ColumnMapping`
4. On **cache miss**: invoke LLM with schema inference prompt

**LLM Schema Inference Prompt:**
```
You are mapping PDF table column headers to Salesforce ACM fields.

Given these column headers from a PDF register:
{{ headers | join(", ") }}

And these sample data rows:
{{ sample_rows }}

Map each header to the most appropriate Salesforce field:
{{ sf_field_catalog }}

Output JSON:
{
  "mappings": [
    {"pdf_header": "Room/Area", "sf_field": "Room_or_Area__c", "confidence": 0.95},
    {"pdf_header": "F/NF", "sf_field": "Friability_of_Material__c", "confidence": 0.90},
    ...
  ],
  "unmapped_headers": ["Column X"],
  "overall_confidence": 0.87,
  "detected_consultant": "Prensa Pty Ltd"
}
```

5. If `overall_confidence < 0.8`: trigger HITL — show user the proposed mapping for confirmation
6. On confirmation: save to `consultant_format_profile` for future cache hits

**Output:** `InferredSchema` dataclass:
```python
@dataclass
class InferredSchema:
    column_mapping: dict[str, str]      # pdf_header → sf_field_api_name
    canonical_mapping: dict[str, str]   # pdf_header → canonical_name (for segmenter)
    level_regex: re.Pattern | None      # format-specific floor/level pattern
    recovery_config: RecoveryConfig     # format-specific recovery settings
    confidence: float                   # overall confidence score
    consultant_name: str | None         # detected consultant firm
    profile_id: str | None              # SurrealDB record ID if cached
```

### 5.3 Consultant Format Profile (SurrealDB)

```sql
DEFINE TABLE consultant_format_profile SCHEMAFULL;
DEFINE FIELD header_signature   ON consultant_format_profile TYPE string;   -- sorted hash of headers
DEFINE FIELD consultant_name    ON consultant_format_profile TYPE option<string>;
DEFINE FIELD column_mapping     ON consultant_format_profile TYPE object;   -- {pdf_header: sf_field}
DEFINE FIELD canonical_mapping  ON consultant_format_profile TYPE object;   -- {pdf_header: canonical}
DEFINE FIELD level_regex        ON consultant_format_profile TYPE option<string>;  -- regex pattern string
DEFINE FIELD recovery_config    ON consultant_format_profile TYPE option<object>;
DEFINE FIELD confidence         ON consultant_format_profile TYPE float;
DEFINE FIELD verified_by_user   ON consultant_format_profile TYPE bool DEFAULT false;
DEFINE FIELD sample_count       ON consultant_format_profile TYPE int DEFAULT 1;  -- how many docs used this
DEFINE FIELD created_at         ON consultant_format_profile TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at         ON consultant_format_profile TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_header_sig ON consultant_format_profile FIELDS header_signature UNIQUE;
```

### 5.4 Adaptive Row Segmenter

Replace the static `COLUMN_ALIASES` with a merge strategy:

```python
def detect_column_mapping(
    header_cells: list[dict],
    extra_mappings: dict[str, str] | None = None,  # NEW: from InferredSchema
) -> dict[str, str]:
    """Map raw PDF headers to canonical field names.

    Priority order:
    1. extra_mappings (from schema inference / format profile)
    2. COLUMN_ALIASES (built-in fuzzy matching)
    3. Pass-through as col_N (unknown headers)
    """
    mapping = {}
    for cell in header_cells:
        raw = cell["text"].strip()
        # Priority 1: explicit mapping from schema inference
        if extra_mappings and raw in extra_mappings:
            mapping[extra_mappings[raw]] = raw
            continue
        # Priority 2: existing fuzzy match against COLUMN_ALIASES
        best_canonical, score = _fuzzy_match(raw, COLUMN_ALIASES)
        if score >= _JW_THRESHOLD:
            mapping[best_canonical] = raw
            continue
        # Priority 3: pass-through
        mapping[f"col_{cell['start_col_offset_idx']}"] = raw
    return mapping
```

Similarly, `_LEVEL_REGEX` becomes configurable:

```python
def segment_docling_table(
    docling_json: dict,
    ...,
    level_regex: re.Pattern | None = None,  # NEW: from InferredSchema
) -> list[RawTableRow]:
    effective_level_re = level_regex or _LEVEL_REGEX
    ...
```

### 5.5 Recovery Config

Format-specific recovery settings extracted from the hardcoded patterns:

```python
@dataclass
class RecoveryConfig:
    """Format-specific configuration for record recovery functions."""
    # "Not Sampled" synonyms
    not_sampled_terms: list[str] = field(default_factory=lambda: [
        "Not Sampled", "Not Accessible", "Access Denied", "No Access"
    ])
    # Confirmation terms (what follows "Not Sampled")
    confirmation_terms: list[str] = field(default_factory=lambda: [
        "Presumed Positive", "Assumed Positive", "Assumed"
    ])
    # Access restriction vocabulary
    restriction_terms: list[str] = field(default_factory=lambda: [
        "Restricted Access", "Height Restricted", "Live Electrical",
        "Confined Space", "Inaccessible"
    ])
    # Section header regex (ARA: "Name - Interior/Exterior - Level")
    section_header_re: re.Pattern | None = None
    # Level detection regex override
    level_re: re.Pattern | None = None
    # Product keyword set for no-access recovery
    product_keywords: set[str] | None = None
    # Scan window sizes
    lookback_lines: int = 5
    lookahead_lines: int = 3
    # Content boundary pattern for Ollama chunking
    content_boundary_re: re.Pattern | None = None
```

### 5.6 Format-Agnostic Prompts

Replace hardcoded consultant sections with Jinja variables:

**building_inventory.jinja:**
```jinja
{% if detected_format == "clutch" %}
### Clutch/Greencap Pipe-Table Format
Look for: | Building Name: | <value> | Number of Levels: | <value> |
{% elif detected_format == "standard" %}
### Standard DET Format
Look for: ## B001 - Building Name
{% elif detected_format == "ara" %}
### ARA Text-Header Format
Look for: Building Name:\n  <value>
{% else %}
### Unknown Format
Identify building names from any structural pattern...
{% endif %}
```

**row_extraction.jinja:**
```jinja
Extract the following fields from the row data:
{% for field in extraction_fields %}
- {{ field.sf_label }}: {{ field.description }}
{% endfor %}

{# Dynamic field list from InferredSchema instead of hardcoded 13 fields #}
```

---

## 6. Extension Points Summary

| Extension Point | File:Line | Current State | Change |
|-----------------|-----------|--------------|--------|
| `detect_column_mapping()` | `row_segmenter.py:178` | Flat COLUMN_ALIASES | Accept `extra_mappings` param |
| `segment_docling_table()` | `row_segmenter.py:276` | Fixed `_LEVEL_REGEX` | Accept `level_regex` param |
| `build_kv_prompt()` | `row_extractor.py:45` | Fixed 13-field schema | Accept dynamic field list |
| `extract_single_row()` system prompt | `row_extractor.py:113` | Hardcoded Jinja template | Template accepts `extraction_fields` |
| Pre-extraction header scan | `docling_document_json` | Not utilized for schema | New schema inference node |
| `_recover_no_access_records()` | `acm_extraction.py:2019` | Hardcoded Broadmeadows patterns | Accept RecoveryConfig |
| `_recover_not_sampled_records_ara()` | `acm_extraction.py:2234` | Hardcoded ARA patterns | Accept RecoveryConfig |
| `_split_content_by_char_budget()` | `utils.py:363` | DET + ARA boundary regex | Accept boundary pattern |

---

## 7. Implementation Stories

### Story 1: Fix Critical Bugs (prerequisite)
**SP: 3 | Dependencies: none**

- Fix broken `clutch_detector.py` import (`_CLUTCH_BUILDING_NAME_PATTERN`, `_CLUTCH_LEVEL_SUFFIX`)
- Deduplicate `_detect_ara_buildings()` between `building_inventory.py` and `ara_detector.py`
- Add regression tests for all 3 format detectors

### Story 2: Schema Inference Node
**SP: 8 | Dependencies: Story 1**

- Create `open_notebook/extractors/schema_inference.py`
- Implement header collection from `acm_table_section.docling_document_json`
- Design and test LLM schema inference prompt
- Create `InferredSchema` dataclass
- Wire as new LangGraph node between PREFLIGHT and ORCHESTRATOR
- Add unit tests with mock Docling table data

### Story 3: Consultant Format Profile Registry
**SP: 5 | Dependencies: Story 2**

- Create SurrealDB migration for `consultant_format_profile` table
- Implement cache-hit/miss logic with header signature hashing
- Create API endpoints: `GET /api/acm/format-profiles`, `POST /api/acm/format-profiles`
- Add profile auto-save on successful extraction
- Add `sample_count` increment on cache hits

### Story 4: Adaptive Row Segmenter
**SP: 5 | Dependencies: Story 2**

- Add `extra_mappings` parameter to `detect_column_mapping()`
- Add `level_regex` parameter to `segment_docling_table()`
- Create `RecoveryConfig` dataclass
- Refactor `_recover_no_access_records()` to accept `RecoveryConfig`
- Refactor `_recover_not_sampled_records_ara()` to accept `RecoveryConfig`
- Update `_split_content_by_char_budget()` to accept boundary pattern
- Backward-compatible: existing behavior unchanged when no extra params passed

### Story 5: Format-Agnostic Prompts
**SP: 5 | Dependencies: Story 2**

- Add `detected_format` and `extraction_fields` Jinja variables to all ACM prompts
- Make building_inventory.jinja format-conditional
- Make row_extraction.jinja dynamic (field list from InferredSchema)
- Make v3_building_extraction.jinja example-conditional
- Add format-specific example library (YAML/JSON)

### Story 6: HITL Mapping Confirmation UI
**SP: 8 | Dependencies: Stories 2, 3**

- Frontend: Column mapping review dialog
- Show: PDF header → SF field mapping with confidence indicators
- User actions: approve, modify, reject individual mappings
- On approve: save to format profile registry
- SSE integration: pause extraction, show dialog, resume on confirmation
- Use existing PipelineEventBus for SSE communication

### Story 7: Validation with 3+ Consultant Formats
**SP: 5 | Dependencies: Stories 1–5**

- Test with Broadmeadows (Standard DET) — must match existing benchmarks
- Test with Alexander (ARA/Prensa) — must match existing benchmarks
- Test with at least 1 new consultant format (Clutch/Greencap pipe-table)
- Benchmark: accuracy, record count, field coverage vs. manual extraction
- Document format profile for each tested consultant

### Dependency Graph

```
Story 1 (fix bugs)
  │
  ▼
Story 2 (schema inference) ──────────┐
  │                                   │
  ├──► Story 3 (format registry) ─────┤
  │                                   │
  ├──► Story 4 (adaptive segmenter)   ├──► Story 7 (validation)
  │                                   │
  └──► Story 5 (agnostic prompts) ────┘
                                      │
Story 6 (HITL UI) ◄──────────────────┘
```

**Total SP: 39 | Estimated sprints: 3–4 (10 SP/sprint)**

---

## 8. Regression Safety

### Existing Benchmarks

| Document | Format | Record Count | Benchmark File |
|----------|--------|-------------|----------------|
| Broadmeadows Police Station | Standard DET | 31 records | `tests/e2e/fixtures/ara-documents/broadmeadows-expected-results.json` |
| Alexander District Hospital | ARA/Prensa | 43 records | (manual count from E35 benchmark) |

### Regression Rules

1. All changes must be **backward-compatible** — existing behavior unchanged when no `InferredSchema` is provided
2. New parameters have sensible defaults matching current hardcoded values
3. `COLUMN_ALIASES` remains as the fallback layer — never removed, only supplemented
4. Recovery functions use existing patterns as defaults in `RecoveryConfig`
5. CI gate: both benchmark documents must produce identical record counts before/after

### Testing Strategy

- **Unit tests:** Mock Docling table data → verify `detect_column_mapping()` with and without extra_mappings
- **Integration tests:** Full pipeline run on benchmark PDFs → verify record counts match
- **Schema inference tests:** Mock LLM responses → verify `InferredSchema` construction
- **Format profile tests:** Cache hit/miss scenarios → verify correct mapping reuse

---

## 9. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM schema inference produces wrong mappings | Records have wrong field values | Confidence threshold + HITL fallback |
| Format profile cache collision (different formats, same header hash) | Wrong cached mapping applied | Include column count + order in hash |
| Dynamic prompts degrade existing format accuracy | Benchmark regression | Feature-flag new prompts, A/B test |
| Schema inference adds latency to extraction | Slower pipeline | Cache hits skip LLM call; inference is one-time per source |
| MinerU path has no docling_json | Schema inference unavailable | Fall back to bulk mode (existing behavior) |

---

## 10. Files Reference

### Files to Create
| File | Purpose |
|------|---------|
| `open_notebook/extractors/schema_inference.py` | Schema inference node + InferredSchema |
| `open_notebook/extractors/recovery_config.py` | RecoveryConfig dataclass |
| `migrations/NNNN_consultant_format_profile.surql` | SurrealDB migration |
| `api/routers/format_profiles.py` | API endpoints for format profiles |
| `frontend/src/components/acm/ColumnMappingDialog.tsx` | HITL mapping UI |

### Files to Modify
| File | Change |
|------|--------|
| `row_segmenter.py` | Add `extra_mappings` + `level_regex` params |
| `row_extractor.py` | Accept dynamic field list |
| `acm_extraction.py` | Wire schema inference node; refactor recovery functions |
| `orchestrator.py` | Pass InferredSchema through pipeline |
| `utils.py` | Accept boundary pattern in chunking |
| `building_inventory.jinja` | Format-conditional sections |
| `row_extraction.jinja` | Dynamic field list |
| `v3_building_extraction.jinja` | Format-conditional examples |
| `clutch_detector.py` | Fix broken import |
| `building_inventory.py` | Remove duplicated ARA detection |
