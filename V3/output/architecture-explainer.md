# ACM-AI Backend Data Architecture — Plain English Guide

> **Audience:** Product owner / developer wanting to understand the system without reading code.
> **Written:** 2026-03-03
> **Covers:** Current pipeline + V3 target, all data models, Salesforce picklists, validation system.

---

## Table of Contents

1. [The Big Picture — What Does This System Actually Do?](#1-the-big-picture)
2. [The Two Salesforce Objects — Building vs ACM Item](#2-the-two-salesforce-objects)
3. [Dependent Picklists — Why Some Fields Lock Others](#3-dependent-picklists)
4. [The Extraction Pipeline — From PDF to Grid](#4-the-extraction-pipeline)
5. [The Data Models — Every Record Explained](#5-the-data-models)
6. [The Runtime Configuration Files — The Live Rulebooks](#6-the-runtime-configuration-files)
7. [The Validation System — Two Paths, One Goal](#7-the-validation-system)
8. [V3 Target — What Changes](#8-v3-target-what-changes)
9. [The 5-Table Data Flow — How AI Extraction Links to Raw Tables](#9-the-5-table-data-flow--how-ai-extraction-links-to-raw-tables)
10. [Pre-Extraction Intelligence — Page Count, TOC, Building Metadata](#10-pre-extraction-intelligence--page-count-toc-building-metadata)
11. [Persisted Pre-Extraction Intelligence (E30-S9)](#11-persisted-pre-extraction-intelligence-e30-s9)

---

## 1. The Big Picture

### What the system does (1 sentence)

ACM-AI reads a PDF asbestos register, extracts every asbestos item from every room in every building, classifies and validates each item, and produces two CSV files that you can load directly into Salesforce — one for buildings, one for ACM items.

### The real-world use case

You are an asbestos consultant. You have just finished a school inspection and produced a 200-page asbestos register PDF. Inside that PDF there is a table per building, with rows like:

```
Room 101 | Ceiling tiles | Non-friable | Chrysotile | Good | Encapsulation recommended
Room 102 | Pipe lagging  | Friable     | Crocidolite | Poor | Remove immediately
```

You need to get all of that into Salesforce. Manually, that could be 500+ rows across 20 buildings. ACM-AI automates the extraction, validates each row against Salesforce's own picklist rules, flags anything that won't import cleanly, and exports two CSVs ready for Salesforce Data Loader.

### High-level flow

```
Your PDF
   │
   ▼
[Upload to ACM-AI]
   │
   ▼
[Table Extraction]  ← Docling reads the PDF tables (V3: also MinerU)
   │
   ▼
[AI Interpretation] ← LLM reads the tables and structures each row into fields
   │
   ▼
[Classification]    ← Pattern matching assigns product group + product type
   │
   ▼
[Validation]        ← Two checks: BAR rules + Salesforce picklist chain rules
   │
   ▼
[Review Grid]       ← You see results in a table, fix any red/orange warnings
   │
   ▼
[Export]            ← Two CSVs: Building__c.csv + Item__c.csv → Salesforce Data Loader
```

---

## 2. The Two Salesforce Objects

### Why two objects?

In Salesforce, asbestos data is split into two related record types:

| Object | What it represents | How many per job |
|--------|-------------------|-----------------|
| `Building__c` | A physical building on the school campus | ~5–30 per job |
| `Item__c` | One ACM item found inside a building | ~10–500 per building |

They are **parent-child**: each `Item__c` has a `building_id` pointing to its parent `Building__c`.

### What's in a Building record?

Think of `Building__c` as the school's **asset register card** for that building:

```
Building Name:     Main Block
Building Type:     Primary school — Single storey
Building Category: Education
Year Built:        1965
Construction Type: Brick veneer
Roof Type:         Corrugated iron
School:            Broadmeadows Primary School
```

**Key dependency:** `Building Type` (114 options) controls which `Building Category` (13 options) are valid.
If you pick `Primary school — Single storey` as the type, Salesforce only allows `Education` as the category.
This is the **Building dependent picklist chain** (explained in Section 3).

### What's in an ACM Item record?

`Item__c` is one asbestos entry — one row from the PDF register:

```
Room/Location:          Room 101 — Ceiling
Item Description:       Suspended ceiling tiles with asbestos binder
Friability:             Non-friable
ACM Classification:     Vinyl products          ← constrained by Friability
ACM Sub-Classification: Ceiling tiles           ← constrained by Classification
Item Name:              Ceiling tiles (ACT)     ← freeform but restricted picklist
Material Condition:     Stable
Disturbance Potential:  Low
Sampled:                Yes
Sample Result:          Positive - Non-friable
Quantity:               50 m²
Hygienist Recommendation: maintain_in_situ
```

**Key dependency chain:** `Friability` → `ACM Classification` → `ACM Sub-Classification`.
These three fields are a **three-level dependent picklist** (explained in Section 3).

---

## 3. Dependent Picklists

### What is a dependent picklist?

In Salesforce, a dependent picklist is a field whose **available options change** depending on what you selected in another field. Like this:

```
You pick:    Friability = "Friable"
Then you see only:  [Cement products (f), Vinyl products (f), Insulation (f), ...]

You pick:    Friability = "Non-friable"
Then you see only:  [Cement products, Bitumen products, Vinyl products, Coatings, ...]
```

If you try to import a record with `Friability = "Non-friable"` but `ACM Classification = "Cement products (f)"` (which is the friable version), **Salesforce will reject it**. The `(f)` suffix means friable-only.

### The Item__c Three-Level Chain

This is the most important chain to understand. It has three levels:

```
Level 1: Friability_of_Material__c (2 options)
  │
  ├── "Non-friable" unlocks 9 Classification groups:
  │     Cement products
  │     Bitumen products
  │     Vinyl products
  │     Gasket/rope/friction products
  │     Coatings
  │     Reinforced plastics/resins (excluding bitumen products)
  │     Other non-friable products
  │     Insulation (non-friable)
  │     Textiles (non-friable)          ← NOTE: not yet in taxonomy JSON files
  │
  └── "Friable" unlocks 9 Classification groups (all with (f) suffix):
        Cement products (f)
        Vinyl products (f)
        Insulation (f)
        Gasket/rope/friction products (f)
        Textiles (f)
        Other friable products (f)
        Bitumen products (f)            ← NOTE: not yet in taxonomy JSON files
        Coatings (f)                    ← NOTE: not yet in taxonomy JSON files
        Reinforced plastics/resins ... (f) ← NOTE: not yet in taxonomy JSON files

Level 2: ACM_Classification__c (18 options total, 9 per friability)
  │
  └── Each group unlocks specific Sub-Classification options
        e.g. "Cement products" unlocks:
               Flat sheeting
               Corrugated roof sheeting
               Compressed flat sheeting
               Moulded products
               Pipes and pipe fittings
               Ridge capping
               Other cement products

Level 3: ACM_Sub_Classification__c (133 options total)
```

### Concrete example: Ceiling Tile

Your PDF says: `"Vinyl ceiling tile, non-friable"`

The system must produce:
```
Friability:             Non-friable
ACM Classification:     Vinyl products
ACM Sub-Classification: Ceiling tiles       ← MUST be exactly "Ceiling tiles" (sentence case)
```

If any of these three don't agree (e.g. `Vinyl products` + `Non-friable` but sub-classification is `Corrugated roof sheeting` which belongs to Cement), Salesforce rejects the record.

### The Building__c Two-Level Chain

Simpler — only two levels:

```
Level 1: Building_Type__c (114 options)
  e.g. "Primary school — Single storey"

Level 2: Building_Category__c (13 options)
  Each building type maps to exactly one category:
  ┌────────────────────────────────────────────┬─────────────────────┐
  │ Building Type contains...                  │ → Building Category  │
  ├────────────────────────────────────────────┼─────────────────────┤
  │ Primary school, High school, etc.          │ Education            │
  │ Hospital, Medical Centre, etc.             │ Health               │
  │ Sports centre, Pool, Oval facility, etc.   │ Recreation           │
  │ Office building, Admin centre, etc.        │ Administration       │
  │ Library, Gallery, Museum                   │ Cultural             │
  │ Workshop, Maintenance shed, etc.           │ Industrial           │
  │ House, Flat, Unit, etc.                    │ Residential          │
  │ Warehouse, Storage, etc.                   │ Warehousing          │
  │ Car park, Undercover parking               │ Car Park             │
  │ Pump station, Substation, etc.             │ Utility              │
  │ Canteen, Tuck shop, Kitchen                │ Food Service         │
  │ Covered walkway, Shed, Toilet block, etc.  │ Other Structures     │
  │ Court/tribunal/justice facility            │ Government           │
  └────────────────────────────────────────────┴─────────────────────┘
```

### How is this stored in Salesforce?

Salesforce encodes the dependency using a binary `validFor` field on each picklist value. Each bit position represents a controller value. The system reads this encoding from the raw metadata files (`V3/building-list.txt`, `V3/item-list.txt`) to know which combinations are valid.

---

## 4. The Extraction Pipeline

### 4a. Current Pipeline (what exists today)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: UPLOAD                                                     │
│                                                                      │
│  User uploads PDF via UI                                            │
│    └─► POST /sources (api/routers/sources.py)                       │
│           ├── Saves PDF to UPLOADS_FOLDER                           │
│           ├── Creates a Source stub record in SurrealDB             │
│           └── Submits "process_source" background job               │
│                                                                      │
│  Background worker picks up the job:                                │
│    └─► process_source_command() (commands/source_commands.py)       │
│           ├── Runs Docling DocumentConverter → extracts Markdown    │
│           │    (Docling sees the PDF structure, reads tables as HTML)│
│           ├── Saves source.full_text = the Markdown                 │
│           └── Stores each table in acm_table_section SurrealDB table│
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: ACM EXTRACTION (triggered by user clicking "Extract")     │
│                                                                      │
│  POST /acm/extract → acm_extract_command()                          │
│    └─► LangGraph pipeline (open_notebook/graphs/acm_extraction.py)  │
│                                                                      │
│  STAGE 1: STRUCTURE                                                 │
│    ├── extract_metadata:   Who is the consultant? What site?        │
│    ├── structure:          How many pages? Which page = building?   │
│    ├── inventory:          List of buildings, estimated complexity   │
│    └── tag_pages:          Label each page (register/cover/summary) │
│                                                                      │
│  STAGE 2: ORCHESTRATOR (per-building, up to 3 in parallel)         │
│    For each building:                                               │
│    ├── Slice content to that building's page range                  │
│    ├── Inject Docling table HTML from acm_table_section             │
│    └── Call LLM (Claude/OpenRouter) with extraction prompt          │
│         → Returns structured JSON with all ACM rows for that building│
│                                                                      │
│  STAGE 3: VALIDATE → CORRECT (corrective loop)                     │
│    ├── Check required fields, enum values, business rules           │
│    └── If failures → re-run LLM with corrections (max 2 retries)   │
│                                                                      │
│  STAGE 4: STORE                                                     │
│    For each extracted record:                                       │
│    ├── classify_product() → assign product group + type             │
│    ├── normalize_recommendation() → canonical hygienist action      │
│    ├── normalize_enum_value() → fix casing, synonym expansion       │
│    └── Save to acm_record table in SurrealDB                        │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: DISPLAY                                                   │
│                                                                      │
│  GET /acm/records?source_id=... → paginated query from SurrealDB   │
│  Frontend renders AG Grid with all records                          │
│  User reviews, edits cells, sees validation badges                  │
│                                                                      │
│  (Export to SF CSV — BAR format, SF Data Loader format)            │
└─────────────────────────────────────────────────────────────────────┘
```

### 4b. LangGraph Pipeline Node-by-Node

Each box below is a **node** in the LangGraph extraction graph. They run in sequence (with some parallel work inside the orchestrator stage):

| Node | Code file | What it does | Input | Output |
|------|-----------|-------------|-------|--------|
| `extract_metadata` | `metadata_extractor.py` | Reads the header/cover page. Who wrote this? Which school? What date? | raw Markdown | `DocumentMetadata` |
| `structure` | `document_structure.py` | Finds page numbers, building headers, room headers in Markdown | raw Markdown | `DocumentStructure` + page count |
| `inventory` | `building_inventory.py` | Builds a list of all buildings with estimated number of items and complexity | `DocumentStructure` | `BuildingInventory` |
| `tag_pages` | `page_tagger.py` | Labels each page with a type: `ASBESTOS_REGISTER`, cover, summary, etc. | raw Markdown + page count | `PageTags[]` |
| `orchestrate` | `orchestrator.py` | For each building, decides strategy + calls LLM | `BuildingInventory` + `PageTags` | `List[ACMExtractionRecord]` |
| `validate` | `acm_validator.py` | Checks every record against schema + business rules | `List[ACMExtractionRecord]` | pass/fail per record |
| `correct` | `acm_extraction.py` | Re-prompts LLM for records that failed validation | failed records | corrected records |
| `deduplicate` | `acm_extraction.py` | Removes content-identical records | all records | deduped records |
| `recover_no_access` | `no_access_recovery.py` | Scans raw text for "No Access"/"Not Sampled" the LLM might have missed | raw Markdown | synthetic records |
| `save` | `acm_extraction.py` | Classifies, normalizes, and saves each record to SurrealDB | `List[ACMExtractionRecord]` | `List[ACMRecord]` in DB |

### 4c. What Happens Inside the Orchestrator (the clever bit)

The orchestrator is where ACM-AI decides **how** to extract each building. It does this:

```
For each building in the inventory:

  1. "Is this building simple or complex?"
     SIMPLE  = few rooms, no multi-page tables → use REGEX_ONLY path
     COMPLEX = many rooms, merged cells, multi-page → use FULL_LLM path

  2. Slice the Markdown to just that building's pages

  3. Fetch Docling's pre-extracted tables for those pages
     (These are in acm_table_section — Docling already found the tables in Phase 1)

  4. Inject those tables into the LLM prompt with:
     "Here is the structured table. Use this as the primary data source."

  5. Call the LLM (up to 3 buildings at once in parallel)
     → LLM returns a JSON array of ACMExtractionRecord objects

  6. If yield is too low (LLM found fewer items than estimated):
     Escalate SIMPLE buildings to FULL_LLM and retry
```

This two-source approach (Docling tables + raw Markdown) is what makes extraction reliable: Docling handles cell boundaries correctly even with merged cells, while the LLM handles unstructured text around the table.

---

## 5. The Data Models

### 5a. ACMRecord — The Core Record

`ACMRecord` is the Python class (in `open_notebook/domain/acm.py`) that represents one asbestos item. Every field has **two names**: the BAR name (from the Excel register format) and the Salesforce API name.

Example — the same field, accessed two ways:
```python
record.friable          # BAR name → "Non Friable"
record.Friability_of_Material__c  # SF API name → "Non-friable"
```

This dual-naming (called `AliasChoices` in Pydantic) means the same record object works for both BAR Excel export and Salesforce CSV export without any transformation.

**Key fields and their SF mapping:**

| BAR Field Name | SF API Name | Example Value |
|---------------|-------------|---------------|
| `item_description` | `Name` | `Ceiling tiles — suspended grid system` |
| `friable` | `Friability_of_Material__c` | `Non-friable` |
| `acm_product_group` | `ACM_Classification__c` | `Vinyl products` |
| `acm_product_type` | `ACM_Sub_Classification__c` | `Ceiling tiles` |
| `item_name` | `Item_Name__c` | `Ceiling tiles (ACT)` |
| `material_condition` | `Condition__c` | `Stable` ← was "Good" in BAR |
| `disturbance_potential` | `Disturbance_Potential_of_Material__c` | `Low` |
| `sample_number` | `Sample_Number__c` | `34511-039-001` |
| `sample_result` | `Sample_Analysis_Result_Material_Status__c` | `Positive - Non-friable` |
| `hygienist_recommendations` | `ACM_Management_Actions__c` | `maintain_in_situ` |
| `building_id` | `Asset__c` (External ID) | `BLDG-001` |

### 5b. BuildingRecord — New in V3

`BuildingRecord` (in `open_notebook/domain/building_record.py`) is a new model added in E30-S2. It maps to Salesforce `Building__c`.

```python
class BuildingRecord:
    id: str                  # SurrealDB record ID
    name: str                # "Main Block"
    building_type: str       # "Primary school — Single storey"
    building_category: str   # "Education" (derived from type)
    year_built: Optional[int]
    construction_type: str
    roof_type: str
    source_id: str           # which PDF this came from
    notebook_id: str         # which notebook (project)
```

### 5c. SFDependencyChain — The Picklist Rules Object

This is an in-memory Python object (from `field_config.py`) that holds the allowed combinations for a dependent picklist:

```python
class SFDependencyChain:
    controller_api_name: str      # "Friability_of_Material__c"
    dependent_api_name: str       # "ACM_Classification__c"
    mapping: dict[str, list[str]] # {
                                  #   "Non-friable": ["Cement products", "Bitumen products", ...],
                                  #   "Friable":     ["Cement products (f)", "Vinyl products (f)", ...]
                                  # }
```

There are 3 of these objects:
1. `Friability_of_Material__c` → `ACM_Classification__c`
2. `ACM_Classification__c` → `ACM_Sub_Classification__c`
3. `Building_Type__c` → `Building_Category__c`

### 5d. ACMTableSection — The Raw Table Store

When Docling extracts tables from the PDF, each table is stored as an `acm_table_section` record:

```python
class ACMTableSection:
    source_id: str
    page_start: int
    page_end: int
    table_type: str          # "docling_direct_api"
    raw_html: str            # the HTML Docling produced
    markdown: str            # markdown version for LLM
    csv_content: str         # CSV version for export
    table_bbox: dict         # {x, y, width, height, page} — where on the page
```

This is why you can click a cell in the grid and jump to the source page in the PDF — every record knows its page and position.

### 5e. ClassificationResult — What the Taxonomy Returns

```python
class ClassificationResult:
    product_group: str    # "Vinyl products" (T-prefix stripped)
    product_type: str     # "Ceiling Tiles" ← NOTE: Title Case, SF wants "Ceiling tiles"
    confidence: float     # 0.9 for pattern match, 0.5 for LLM
    method: str           # "pattern" | "llm" | "none"
```

---

## 6. The Runtime Configuration Files

These files in `docs/samplePDF/instructions-sample/` are **not documentation** — they are **loaded at startup** by production code and cached in memory. Changing them changes system behavior immediately (on next restart).

### 6a. `register_enums.json` — The Allowed Value Lists

Defines every enum field and its allowed values. Used by the BAR validation path.

```json
{
  "Condition": ["Stable", "Minor damage", "Moderate damage", "Severely damaged"],
  "Friability": ["Non-friable", "Friable"],
  "SampleResult": [
    "Positive - Non-friable",
    "Positive - Friable",
    "Negative",
    "Not Sampled",
    "No Access"
  ],
  "YesNo": ["Yes", "No"],
  "DisturbancePotential": ["Low", "Medium", "High", "Very High"]
}
```

**Loaded by:** `config_loader.py:222` → `acm_validator.py:75`
**Used by:** `validate_enum_fields()` in BAR validation path

**Important:** `"Not Sampled"` and `"No Access"` are valid BAR values but NOT in SF picklists. This creates a known conflict between the two validation paths.

### 6b. `register_taxonomy.nonfriable.json` — Non-Friable Product Groups

Maps BAR taxonomy codes (T1-T8) to Salesforce product group names and their product types:

```json
[
  {
    "pc_code": "T1",
    "product_group_header": "T1 Cement products",
    "primary_classification": "Bitumen products",  ← BUG: rotated, never use this field
    "product_types": [
      "Flat sheeting",
      "Corrugated roof sheeting",
      "Ridge capping",
      ...
    ]
  },
  {
    "pc_code": "T2",
    "product_group_header": "T2 Bitumen products",
    ...
  }
]
```

**Loaded by:** `taxonomy.py:64` → `get_product_groups()`, `get_product_types()`
**Note:** `_strip_t_prefix()` removes "T1 " prefix from group names when returning them, so code gets `"Cement products"` not `"T1 Cement products"`.
**Bug:** `primary_classification` field is rotated one position — never use it. Use `product_group_header`.

### 6c. `register_taxonomy.friable.json` — Friable Product Groups

Same structure as non-friable, for T1(f)-T6(f). Same rotation bug. Same `_strip_t_prefix()` logic applies.

### 6d. `consultant_wording_rules.json` — How to Interpret Recommendations

Maps consultant free-text phrases to canonical action codes:

```json
{
  "consultant_phrases_to_actions": [
    {
      "pattern": "(?i)maintain.*current.*condition",
      "action": "maintain_in_situ"
    },
    {
      "pattern": "(?i)remove.*prior.*demolition|remove.*prior.*refurb",
      "action": "remove_prior_to_refurb_or_demolition"
    },
    ...
  ]
}
```

**Loaded by:** `recommendations.py:86`
**7 canonical actions:**

| Code | Meaning |
|------|---------|
| `maintain_in_situ` | Leave it, monitor it |
| `remove_prior_to_refurb_or_demolition` | Remove before any major works |
| `restrict_access_immediately` | Seal off the area now |
| `remedial_within_months` | Fix it within a set timeframe |
| `confirm_status_sampling` | Take a sample to confirm ACM |
| `height_or_access_restriction` | Can't inspect — area inaccessible |
| `leave_undisturbed_and_manage` | Hardcoded fallback — NOT yet in JSON file |

### 6e. `register_row.schema.json` — BAR Excel Column Definitions

Maps column letters (A-AU) in the BAR Excel template to field names and types:

```json
{
  "x_excel": {
    "field_specs": [
      { "column": "A", "display_name": "Site Name", "field_index": 0, "type": "string" },
      { "column": "AA", "display_name": "ACM Product Group", "field_index": 26, "type": ["string", "null"] },
      { "column": "AC", "display_name": "ACM Product Type", "field_index": 28, "type": ["string", "null"] }
    ]
  }
}
```

**Note:** Columns AA and AC (product group/type) are plain `string|null` — no enum constraint. The BAR schema provides NO validation for these fields. All ACM classification validation comes from the taxonomy files or the SF chain validator.

---

## 7. The Validation System

### 7a. Overview — Two Independent Paths

After extraction, every record goes through **two separate validation systems** that were built at different times:

```
Extracted record
      │
      ├──► PATH A (BAR Validation) ─────────────────────────────────────┐
      │    acm_validator.validate_enum_fields()                         │
      │    Checks against register_enums.json                          │
      │    ✓ "Not Sampled" → VALID (it's in the BAR enum list)         │
      │    ✗ "Stable" → might be an issue if old "Good" slips through  │
      │                                                                  │
      └──► PATH B (SF Validation) ──────────────────────────────────────┤
           sf_picklist_validator.validate_acm_chain()                   │
           Checks against SFSchemaBundle (from SF field schema)         │
           ✗ "Not Sampled" → INVALID (not in SF picklist)              │
           ✓ "Stable" → VALID (it IS in SF picklist)                   │
                                                                         │
      Both results combined in ValidationResult:                        │
      ├── validation_errors: list   ← blocking (from Path A)           │
      └── chain_warnings: list      ← non-blocking (from Path B)       │
```

**The key design decision:** Path B (SF chain warnings) is non-blocking — it produces orange/yellow badges in the grid but does NOT prevent the record from being saved. Only Path A errors (required fields missing, bad enum values) are blocking.

**The known conflict:** `"Not Sampled"` and `"No Access"` pass Path A but fail Path B. The UI will show these as chain warnings, meaning the user will see a warning badge but the record won't be blocked. The user needs to manually change these to SF-compatible values before exporting.

### 7b. Path A — BAR Validation (code-level)

**File:** `open_notebook/extractors/validators/acm_validator.py`

```python
def validate_acm_record(record: ACMExtractionRecord) -> ValidationResult:
    errors = []

    # 1. Required field check
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"Missing required field: {field}")

    # 2. Enum validation (Path A)
    enum_errors = validate_enum_fields(record, load_field_schema())
    errors.extend(enum_errors)

    # 3. Business rules
    if record.sample_result == "Negative":
        # Negative result must have condition=None and disturbance=None
        if record.material_condition:
            errors.append("Negative result cannot have material condition")

    # 4. SF chain validation (Path B — added in E30-S4)
    chain_warnings = validate_sf_chains(record)

    return ValidationResult(
        is_valid=(len(errors) == 0),
        errors=errors,
        chain_warnings=chain_warnings  # non-blocking
    )
```

### 7c. Path B — SF Chain Validation (code-level)

**File:** `open_notebook/extractors/validators/sf_picklist_validator.py`

```python
class SalesforcePicklistValidator:

    def validate_acm_chain(self, record: dict) -> list[ChainValidationIssue]:
        issues = []

        # Get field values (tries SF API names first, then BAR aliases)
        friability = _get_field_value(record, "Friability_of_Material__c")
        classification = _get_field_value(record, "ACM_Classification__c")
        sub_class = _get_field_value(record, "ACM_Sub_Classification__c")

        # Apply BAR→SF value normalization
        # "Non Friable" (BAR normalizer output) → "Non-friable" (SF picklist)
        # This mapping is in _BAR_TO_SF_VALUE dict

        # Check 1: Is Classification valid for this Friability?
        chain = _find_chain(dependencies, "Friability_of_Material__c", "ACM_Classification__c")
        valid_classifications = chain.mapping.get(friability)  # ["Cement products", "Bitumen products", ...]
        if classification not in valid_classifications:
            issues.append(ChainValidationIssue(..., policy_action="warn"))

        # Check 2: Is Sub-Classification valid for this Classification?
        chain2 = _find_chain(dependencies, "ACM_Classification__c", "ACM_Sub_Classification__c")
        valid_sub = chain2.mapping.get(classification)  # ["Flat sheeting", "Ridge capping", ...]
        if sub_class not in valid_sub:
            issues.append(ChainValidationIssue(..., policy_action="warn"))

        return issues
```

### 7d. The Known Casing Bug (F4)

There is a mismatch between what the taxonomy classifier outputs and what the SF chain validator expects:

```
taxonomy.py classify_product() returns:  "Flat Sheeting"  ← Title Case
SF chain validator expects:              "Flat sheeting"  ← sentence case

Result: every product type match fails in the SF chain validator
        → every record gets an orange "chain warning" badge
        even when the classification is actually correct
```

**Why it happens:** The taxonomy JSON files were created with Title Case product types. The SF picklist uses sentence case. `_strip_t_prefix()` was added in E30-S6 to strip the "T1" prefix but didn't fix casing.

**Planned fix:** Add a `_to_sf_sentence_case()` normalization step in `sf_picklist_validator.py` before the chain lookup. This is story E32-S4.

---

## 8. V3 Target — What Changes

### 8a. What Problem V3 Solves

The current pipeline relies on a **single extraction path**: Docling reads the PDF, the LLM interprets it. If Docling misreads a merged cell or the LLM hallucinates a field, there's no cross-check.

V3 adds a **second extraction provider** (MinerU) and a **consensus layer** between them. Think of it like two independent readers checking the same table — if they disagree on a cell, the system flags it for review rather than silently picking one answer.

### 8b. V3 Pipeline (target state)

```
                    PDF
                     │
         ┌───────────┴────────────┐
         ▼                        ▼
   [Docling]                 [MinerU 2.x]
   Structure-based           Vision-based
   HTML table parser         1.2B VLM model
   (reads PDF text streams)  (reads page images)
         │                        │
         └───────────┬────────────┘
                     ▼
            [Consensus Layer]
            Compares cell-by-cell
            Confidence scoring:
              HIGH:      both agree
              MEDIUM:    minor difference
              CONTESTED: significant mismatch → user review
                     │
                     ▼
            [Raw Extraction Table]
            Saved in raw_extraction table
            Provenance: which provider, page, bbox
                     │
                     ▼
            [AI Extraction Nodes]
            Building__c node:  extracts building fields
            Item__c node:      extracts ACM item fields
            (Two-phase — building header first, items second)
                     │
                     ▼
            [SF Validation + Correction Loop]
            Runs sf_picklist_validator
            Auto-corrects with LLM if chain fails
            Tracks correction history
                     │
                     ▼
            [Review Grid]
            Two-view: Building sidebar + Item grid
            Colour coding: green/orange/red by confidence + validation
            WARN badges for chain issues
            REJECT gate blocks export until resolved
                     │
                     ▼
            [Export]
            Building__c.csv + Item__c.csv
            Validated before export (no bad records slip through)
```

### 8c. New Data Models in V3

| Model | Story | What it adds |
|-------|-------|-------------|
| `BuildingRecord` | E30-S2 | ✅ Already done. SF Building__c parent record. |
| `raw_extraction_table` | E31-S4 | Per-provider extraction result with provenance |
| `NormalizedExtractionResult` | E31-S2 | Standardised output format from any provider |
| `ConsensusResult` | E31-S3 | Confidence-scored merged view of both providers |
| `EditHistoryEntry` | E33 | Every user edit tracked with before/after + reason |

### 8d. Schema Freeze Gate

The V3 sprint plan has a gate called `SCHEMA_FREEZE` that must be passed before any downstream work begins. This gate was **unlocked on 2026-03-03** when E30-S1 through E30-S6 were completed.

The gate means: "All SF field names, picklist rules, vocabulary mappings, and data model schemas are locked. No more changes to these without a documented migration."

This protects downstream stories (E31-E34) from being broken by schema changes.

---

## Quick Reference: Which File Does What?

| File | What it is | Affects |
|------|-----------|---------|
| `open_notebook/domain/acm.py` | `ACMRecord` Pydantic model | Every extracted record |
| `open_notebook/domain/building_record.py` | `BuildingRecord` Pydantic model | Building parent records |
| `open_notebook/graphs/acm_extraction.py` | LangGraph extraction pipeline | Core extraction flow |
| `open_notebook/extractors/orchestrator.py` | Per-building LLM dispatch | Which LLM gets called, when |
| `open_notebook/extractors/normalizers/taxonomy.py` | Product classification | `classify_product()`, `_strip_t_prefix()` |
| `open_notebook/extractors/normalizers/enums.py` | Enum normalization | Field value synonyms, case fixes |
| `open_notebook/extractors/normalizers/recommendations.py` | Recommendation normalization | consultant_wording_rules.json |
| `open_notebook/extractors/parsers/config_loader.py` | Runtime config loading | Loads all 5 JSON files |
| `open_notebook/extractors/parsers/field_config.py` | SF schema model | `SFDependencyChain`, `SFSchemaBundle` |
| `open_notebook/extractors/validators/acm_validator.py` | BAR validation (Path A) | Required fields, enum checks |
| `open_notebook/extractors/validators/sf_picklist_validator.py` | SF chain validation (Path B) | Dependent picklist checks |
| `docs/samplePDF/instructions-sample/register_enums.json` | BAR enum values (runtime) | Path A validation |
| `docs/samplePDF/instructions-sample/register_taxonomy.nonfriable.json` | Non-friable product groups (runtime) | `classify_product()` |
| `docs/samplePDF/instructions-sample/register_taxonomy.friable.json` | Friable product groups (runtime) | `classify_product()` |
| `docs/samplePDF/instructions-sample/consultant_wording_rules.json` | Recommendation patterns (runtime) | `normalize_recommendation()` |
| `docs/samplePDF/instructions-sample/register_row.schema.json` | BAR Excel column schema (runtime) | Field definitions |

---

## 9. The 5-Table Data Flow — How AI Extraction Links to Raw Tables

> **Added:** 2026-03-04. Answers: "Does AI replace the old table? How do you trace where a record came from?"

### 9a. The Layered Model (Nothing Gets Replaced)

The V3 architecture uses **separate tables at each layer** — raw extraction output is **never overwritten**. Each layer links back via foreign keys:

```
PDF (source)
  │
  ├─→ raw_extraction_table        ← Layer 1: Raw per-provider output
  │     (one row per provider per page)
  │     Has: raw_html, raw_markdown, bbox, officer_edits[]
  │     Links: source_id FK → source
  │
  ├─→ acm_table_section           ← Layer 2: Consensus-merged tables
  │     (merged from raw_extraction_table rows)
  │     Has: consensus_tier, consensus_scores, provider_results
  │     Links: source_id FK → source
  │
  ├─→ building_record              ← Layer 3: AI-extracted Building__c
  │     (one per building, Phase 3 Step A)
  │     Has: SF Building fields, extraction_provider, extraction_model
  │     Links: source_id FK → source
  │
  └─→ acm_record                   ← Layer 4: AI-extracted Item__c
        (one per ACM item, Phase 3 Step B)
        Has: SF Item fields, consensus_metadata, edit_history[]
        Links: building_id FK → building_record
               raw_row_id FK → raw_extraction_table  (provenance!)
               parent_table_id FK → acm_table_section
```

### 9b. Provenance Tracking — Every Record Knows Its Origin

Every `acm_record` carries:
- `raw_row_id` FK → the exact `raw_extraction_table` row it came from
- `parent_table_id` FK → the `acm_table_section` it belongs to
- `consensus_metadata` → `{tier, scores, votes}` showing provider agreement
- `edit_history[]` → `[{user, field, old_value, new_value, timestamp}]` tracking manual changes

Every `raw_extraction_table` row carries:
- `bbox` → `{x, y, width, height}` coordinates on the PDF page
- `page_number` → which page of the PDF
- `officer_edits[]` → corrections made to raw data before AI re-processing

### 9c. Manual Change Paths

| Path | Story | How It Works |
|------|-------|-------------|
| **Picklist editing** | E33-S3 | AG Grid inline editors with cascading SF picklists. Changes saved to `acm_record.edit_history[]` |
| **Record Wizard** | E33-S4 | Modal form for full-record editing. Bulk Fix All for common issues |
| **Raw Table Review** | E33-S5 | Edit raw provider output, corrections saved to `raw_extraction_table.officer_edits[]`, can re-run AI extraction from corrected raw data |
| **Chat-based corrections** | **NOT in V3 plan** | No story exists for chat-driven record corrections — flagged as a gap |

---

## 10. Pre-Extraction Intelligence — Page Count, TOC, Building Metadata

> **Added:** 2026-03-04. Answers: "Where do page count, TOC, and building metadata get saved? How do they link to extraction?"

### 10a. The Structure Analysis Phase (Phase 2 in the Pipeline)

Before any AI extraction happens, the pipeline runs 4 analysis nodes that build up an understanding of the document. These produce **transient Pydantic models** that flow through the LangGraph state — they are NOT persisted to the database as separate tables. They live in the graph state dict and are consumed by downstream nodes.

```
extract_metadata → extract_structure → compile_inventory → tag_pages
       │                  │                    │                │
       ▼                  ▼                    ▼                ▼
  DocumentMeta      DocumentStructure    BuildingInventory  PageTaggingResult
  (consultant,      (doc type, TOC,      (per-building      (per-page section
   site, date)       sections, pages)     page ranges,       labels, register
                                          rooms, years)      vs cover vs summary)
```

### 10b. What Each Model Contains

**DocumentStructure** (from `document_structure.py`):
```python
class DocumentStructure:
    document_type: DocumentType    # SAMP, ARA, Division_5, Unknown
    toc_present: bool              # Was a table of contents found?
    total_pages: int               # Total page count from PDF
    register_start_page: int       # Where does the asbestos register section begin?
    building_ids: list[str]        # ["B00A", "B00B", "B00C", ...]
    sections: list[Section]        # Hierarchical TOC: [{section_id: 4, title: "Asbestos Register", page_start: 12, page_end: 45}]
    metadata: dict                 # Extra metadata (document format, indicators found)
```

**BuildingMeta** (from `building_inventory.py` — one per building):
```python
class BuildingMeta:
    building_id: str              # "B00A"
    name: str                     # "Main Block"
    year: int                     # 1965 (from header "B00A - Main Block - 1965 - Brick")
    construction: str             # "Brick"
    purpose: str                  # "Education"
    area_m2: float                # 450.0
    levels: int                   # 2
    page_start: int               # 12 (first page of this building's register)
    page_end: int                 # 18 (last page)
    complexity: BuildingComplexity # SIMPLE or COMPLEX
    rooms: list[RoomMeta]         # [{room_id: "B00A-R0001", name: "External Movement", area_m2: 15.0}]
    acm_item_count_estimate: int  # 25 (estimated from room count * avg items/room)
```

**PageTag** (from `page_tagger.py` — one per page):
```python
class PageTag:
    page_number: int              # 12
    section_id: int               # 4 (= Asbestos Register)
    section_title: str            # "Asbestos Register"
    confidence: float             # 0.95
    page_type: PageType           # ASBESTOS_REGISTER, COVER_PAGE, SUMMARY, APPENDIX, etc.
    subsection: SubSectionTag     # Optional: which subsection within the section
    content_summary: str          # "Building B00A rooms R0001-R0015, 12 ACM items"
```

### 10c. How This Data Flows Into AI Extraction

The critical handoff is from `BuildingInventory` → `orchestrator.py`. Here's the flow:

```
1. compile_inventory() runs
   → Produces BuildingInventory with list of BuildingMeta objects
   → Each BuildingMeta has: name, year, construction, page_start, page_end, complexity, rooms

2. Orchestrator receives BuildingInventory from graph state
   → For each BuildingMeta:
     a. Slices the raw Markdown content to page_start..page_end
     b. Fetches pre-extracted Docling tables from acm_table_section for those pages
     c. Uses complexity to decide extraction strategy (REGEX_ONLY vs FULL_LLM)
     d. Injects building metadata into the LLM prompt:
        "Building: Main Block, Year: 1965, Construction: Brick, Pages: 12-18"

3. AI Extraction nodes run per-building:
   Step A (Building__c extraction):
     → LLM receives: building header text + page range + Docling tables
     → Returns: BuildingExtractionResult (name, type, category, year, address...)
     → Saved as building_record in SurrealDB

   Step B (Item__c extraction):
     → LLM receives: building's table HTML + page range + picklist values from field_schema
     → Returns: ACMItemExtractionResult[] (one per ACM row)
     → Saved as acm_record[] with building_id FK → building_record
```

### 10d. What Gets Persisted vs What's Transient

| Data | Persisted? | Where | When |
|------|:----------:|-------|------|
| `DocumentStructure` (TOC, page count, sections) | **No** | LangGraph state only | Created in Phase 2, consumed by orchestrator, discarded after pipeline completes |
| `BuildingInventory` (building list + metadata) | **No** | LangGraph state only | Same — transient |
| `PageTaggingResult` (per-page labels) | **No** | LangGraph state only | Same — transient |
| `DocumentMeta` (consultant, site, date) | **Partial** | Some fields copied to `source` record | `auto_populate_site_config()` copies site-level metadata to `site_config` table |
| `raw_extraction_table` (raw table HTML) | **Yes** | SurrealDB table | Created in Phase 1 (Docling/MinerU extraction) |
| `acm_table_section` (merged tables) | **Yes** | SurrealDB table | Created in Phase 1 after consensus |
| `building_record` (AI-extracted building) | **Yes** | SurrealDB table | Created in Phase 3 Step A |
| `acm_record` (AI-extracted items) | **Yes** | SurrealDB table | Created in Phase 3 Step B |

### 10e. The Gap: Building Metadata Is Not Persisted Separately

The `BuildingMeta` data (year, construction, levels, area, purpose) extracted during `compile_inventory()` is **transient** — it exists in the graph state and gets passed to the LLM prompt, but the structured `BuildingMeta` object itself is not saved to the database.

What IS saved:
- The LLM re-extracts building fields from the PDF text and saves them in `building_record` (the AI's interpretation)
- The `building_record` has fields like `Estimated_Year_Build_New__c`, `Construction_Type__c`, etc.

What's NOT saved:
- The regex-extracted `BuildingMeta` from the inventory phase (the structural pre-analysis)
- This means there's no "before AI" vs "after AI" comparison for building metadata specifically

This is a minor gap — the `building_record` fields come from the AI extraction prompt which receives the `BuildingMeta` data as context, so the AI output should be at least as good as the regex extraction. But if you wanted to compare "what the structure analysis found" vs "what the AI extracted", that data isn't persisted today.

---

---

## 11. Persisted Pre-Extraction Intelligence (E30-S9)

> **Implemented:** 2026-03-04. **Story:** E30-S9 (3 SP, V3-3). **GitHub Issue:** [#85](https://github.com/CoralShades/acm-ai/issues/85)
> **Design doc:** `docs/issues/v3-persist-pre-extraction-intelligence.md`

### The Problem (Section 10e above)

The 4 transient models (`DocumentMeta`, `DocumentStructure`, `BuildingInventory`, `PageTaggingResult`) were discarded after pipeline completion. This meant:
- No pre-AI vs post-AI building metadata comparison
- No frontend access to document overview (page count, TOC, building list)
- No re-extraction optimization (Phase 2 must rerun from scratch)
- No stored building page ranges for provenance

### The Solution

**Migration 41** creates a `source_intelligence` table storing all 4 models as JSON per source:

```
source_intelligence
├── source_id FK → source (UNIQUE)
├── document_meta: object       (DocumentMeta JSON, ~500 bytes)
├── document_structure: object  (DocumentStructure JSON, ~2 KB)
├── building_inventory: object  (BuildingInventory JSON, ~5-20 KB)
├── page_tags: object           (PageTaggingResult JSON, ~5-50 KB)
├── total_pages: int            (denormalized)
├── total_buildings: int        (denormalized)
├── document_type: string       (SAMP/ARA/Division_5)
├── register_page_range: object ({start, end})
└── created_at, updated_at
```

### Graph Wiring

A new `save_intelligence` node was inserted into the extraction graph between `tag_pages` and `orchestrate`:

```
extract_metadata → structure → inventory → tag_pages → save_intelligence → orchestrate → ...
```

The node is **non-blocking** — it catches all exceptions and logs a warning, so the pipeline continues even if persistence fails. The data is saved early (before the expensive orchestrator/LLM step), so the frontend can display it during extraction.

### API

- `GET /api/acm/source-intelligence/{source_id}` — Returns 200 with data or 404 if not yet extracted.
- Backend: `save_source_intelligence()` (upsert) and `get_source_intelligence()` (select) in `repository.py`.

### Frontend — Intelligence Tab

A new "Intelligence" tab (Brain icon) appears on the source detail page when data exists or extraction is running. It contains 4 sections:

1. **Document Overview** — grid of info cards: document type badge, total pages, buildings count, register page range, consultant, site info
2. **Building Inventory** — Radix `Accordion` (type="multiple"), one item per building; trigger shows ID + name + year + page range; content shows construction details, rooms table
3. **Table of Contents** — structured list of sections with IDs and page numbers
4. **Page Analysis** — scrollable table: page number, section, page type, confidence badge (color-coded green/yellow/orange/red), content summary

The hook (`useSourceIntelligence`) polls every 5 seconds during extraction via `refetchInterval: 5000`, stops when extraction completes. Skeleton loading states and empty state are provided.

### Key Files

| File | Purpose |
|------|---------|
| `migrations/41.surrealql` | Table definition |
| `open_notebook/database/repository.py` | `save_source_intelligence`, `get_source_intelligence` |
| `open_notebook/graphs/acm_extraction.py` | `save_intelligence_node`, graph edge wiring |
| `api/models.py` | `SourceIntelligenceResponse` |
| `api/routers/acm.py` | `GET /source-intelligence/{source_id}` |
| `frontend/src/lib/types/intelligence.ts` | TS interfaces for all 4 models |
| `frontend/src/lib/hooks/use-source-intelligence.ts` | React Query hook |
| `frontend/src/components/acm/SourceIntelligencePanel.tsx` | Panel with 4 sections |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | Tab integration |

---

*Document updated 2026-03-04. Sections 9-11: data flow layering, provenance tracking, structure analysis phase, building metadata flow, persisted pre-extraction intelligence (E30-S9 implemented).*
*References: V3/output/github-issue-e30s4-audit.md, V3/output/picklist-dependency-mappings.md, V3/prompts/findings.md, 04-architecture.md §14, GitHub #85.*
