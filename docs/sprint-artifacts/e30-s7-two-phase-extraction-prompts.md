# Tech Spec: E30-S7 — Two-Phase Extraction Prompts

**Story ID:** E30-S7
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-3
**Story Points:** 3
**Risk Level:** HIGH
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:**
- E30-S6 (BAR->SF Vocabulary Transition — DONE, unlocked SCHEMA_FREEZE gate)
- E31-S2 (Provider Adapter Framework — DONE, defines adapter output shapes)

---

## User Story

As a pipeline developer, I want two-phase Jinja prompt templates that extract Building__c metadata and Item__c records using Salesforce API field names and runtime-injected picklist values, so that the AI extraction layer produces SF-aligned structured output without hardcoding picklist values in the templates.

---

## Problem Statement

The current extraction pipeline uses a single `building_extraction.jinja` template that extracts BAR-vocabulary records into `ACMExtractionResult` (a flat list of `ACMExtractionRecord` items). After the E30 schema alignment, the target data model has two distinct SF objects:

1. **Building__c** — building-level metadata (address, type, category, construction year, inspection company). One record per building.
2. **Item__c** — individual ACM items inside a building (friability, classification, item name, condition, disturbance potential, etc.). Many records per building.

Mixing both in a single LLM call creates ambiguity and makes picklist injection unwieldy because Building__c and Item__c use completely different picklists. The two-phase approach also provides a natural opportunity to pass building metadata (especially `ACM_Classification__c`) into the item extraction prompt to subset the 294-value `Item_Name__c` picklist.

**Key challenge:** 294 Item_Name values sent verbatim to the LLM in every call is noisy and wastes tokens. Item names cluster by product group (e.g., only insulation names are relevant when friability is Friable + classification is "Insulation Products (f)"). The context builder must subset this list intelligently.

---

## Solution Design

### Two-Phase Strategy

```
Phase 1 (Building__c meta):
  Input:  Building content, Building_Type__c picklist, small picklists
  Output: BuildingExtractionResult (building-level SF fields)

Phase 2 (Item__c records):
  Input:  Building content, Building meta from Phase 1, subsetted Item_Name__c list
  Output: ACMItemExtractionResult (list of ACMItemRecord)
```

Both phases are separate LLM calls run sequentially per building inside `_llm_extract_building()`. The feature is gated by the `ACM_V3_PROMPTS` environment variable (default `false` in V3-3). When the flag is `false`, the existing V2 path (`building_extraction.jinja` → `ACMExtractionResult`) is untouched.

### Feature Flag

```python
# In _llm_extract_building() (orchestrator.py)
ACM_V3_PROMPTS = os.getenv("ACM_V3_PROMPTS", "false").lower() == "true"
```

When `ACM_V3_PROMPTS=true`:
- Call `_v3_extract_building_meta()` — Phase 1 LLM call
- Call `_v3_extract_items()` with building meta from Phase 1 — Phase 2 LLM call
- Call `_normalize_v3_records()` to map SF field names → `ACMExtractionRecord` fields for compatibility

When `ACM_V3_PROMPTS=false` (default):
- Existing path unchanged — `building_extraction.jinja` → `ACMExtractionResult`

### Picklist Injection Architecture

A new `prompt_context_builder.py` module handles all picklist selection logic:

```
build_picklist_context(schema_bundle, acm_classification=None)
  -> dict with:
     - building_type_options: str (Building_Type__c values, one per line)
     - building_category_options: str (Building_Category__c values)
     - frequency_of_use_options: str
     - estimated_year_built_options: str (showing range hint, not all 230)
     - friability_options: str (Friability_of_Material__c: 2 values)
     - acm_classification_options: str (ACM_Classification__c: 18 values)
     - acm_sub_classification_options: str (ACM_Sub_Classification__c: full list)
     - item_name_options: str (Item_Name__c: subsetted by product group)
     - condition_options: str (Condition__c: 6 values)
     - disturbance_potential_options: str (Disturbance_Potential_of_Material__c: 6 values)
     - sample_result_options: str (Sample_Analysis_Result_Material_Status__c: 5 values)
     - internal_external_options: str (Internal_External__c: 3 values)
     - labelled_options: str (Labelled__c: 2 values)
```

**Item_Name__c subsetting logic:**

`_select_item_name_groups(building_context)` returns top 4 product groups relevant to the building context. Subset maps ACM_Classification__c → Item_Name groups:

| ACM_Classification__c | Primary Item_Name groups |
|-----------------------|-------------------------|
| `Cement products` / `Cement products (f)` | Ceiling, Roof, Wall, Eave, Soffit, Flue, Cladding |
| `Vinyl products` / `Vinyl products (f)` | Floor covering, Floor covering adhesive, Skirting, Beneath floor covering |
| `Insulation Products` / `Insulation products (f)` | Pipework insulation, Ductwork insulation, Boiler, Ceiling cavity, Roof cavity |
| `Gasket, friction products and adhesives` / `(f)` | Gasket(s), Flange joints, Expansion joint, Valve, Boiler gasket |
| `Coatings` / `Coatings (f)` | Textured coating, Render, Plaster |
| Other / Unknown | All 294 values (full list) |

When `acm_classification=None` (Phase 1 output not yet available, or "Other"), return top 4 most-common groups: Cement, Vinyl, Insulation, Gasket (~100 values total from those 4 groups).

---

## New Pydantic Models (`acm_schemas_v3.py`)

Create `open_notebook/extractors/acm_schemas_v3.py` with the following models. This file is NEW — it does not modify `acm_schemas.py`.

```python
from typing import List, Optional
from pydantic import BaseModel, Field


class BuildingExtractionResult(BaseModel):
    """Phase 1 output: SF Building__c fields extracted from document header."""

    # Core identity
    building_name: Optional[str] = None          # Building_Name__c
    building_type: Optional[str] = None          # Building_Type__c (picklist)
    building_category: Optional[str] = None      # Building_Category__c (picklist)

    # Address
    building_address: Optional[str] = None       # Building_Address__c
    suburb: Optional[str] = None                 # Suburb__c
    postcode: Optional[str] = None               # Postcode__c

    # Physical
    estimated_year_built: Optional[str] = None   # Estimated_Year_Build_New__c (picklist: 4-digit year string)
    construction_type: Optional[str] = None      # Construction_Type__c

    # Audit details
    date_of_audit: Optional[str] = None          # Date_of_Audit_Report__c
    frequency_of_use: Optional[str] = None       # Frequency_of_Use__c (picklist)
    identifying_company: Optional[str] = None    # Identifying_Hygiene_Consulting_Company__c

    # Quality metadata
    extraction_confidence: str = "medium"        # "high" | "medium" | "low"
    extraction_notes: Optional[str] = None


class ACMItemRecord(BaseModel):
    """Phase 2 output: One SF Item__c record (single ACM item in a building)."""

    # Location
    room_or_area: Optional[str] = None              # Room_or_Area__c
    internal_external: Optional[str] = None         # Internal_External__c (picklist)
    level: Optional[str] = None                     # Level__c
    location_in_room: Optional[str] = None          # Location_in_Room__c

    # ACM classification chain
    friability_of_material: Optional[str] = None    # Friability_of_Material__c (picklist: Non-friable | Friable)
    acm_classification: Optional[str] = None        # ACM_Classification__c (product group picklist)
    acm_sub_classification: Optional[str] = None    # ACM_Sub_Classification__c (product type picklist)
    item_name: Optional[str] = None                 # Item_Name__c (subsetted list)
    if_other_item_name: Optional[str] = None        # If_Other_Item_Name__c (free text when Item_Name = "Other")

    # Sample and assessment
    sample_result: Optional[str] = None             # Sample_Analysis_Result_Material_Status__c (picklist)
    nata_sample_no: Optional[str] = None            # NATA_Endorsed_Sample_no__c
    condition: Optional[str] = None                 # Condition__c (picklist)
    disturbance_potential: Optional[str] = None     # Disturbance_Potential_of_Material__c (picklist)
    quantity: Optional[float] = None                # Quantity__c
    labelled: Optional[str] = None                  # Labelled__c (Yes | No)
    labelled_details: Optional[str] = None          # Labelled_Details__c

    # Notes
    hygienist_recommendations: Optional[str] = None
    additional_comments: Optional[str] = None

    # Pipeline flags
    no_access: bool = False
    extraction_confidence: str = "medium"
    data_issues: List[str] = Field(default_factory=list)
    page_number: Optional[int] = None


class ACMItemExtractionResult(BaseModel):
    """Phase 2 output wrapper: all Item__c records for one building."""

    records: List[ACMItemRecord] = Field(default_factory=list)
    status: str = "valid"          # "valid" | "no_acm_data" | "invalid"
    extraction_notes: Optional[str] = None
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/acm_schemas_v3.py` | CREATE | `BuildingExtractionResult`, `ACMItemRecord`, `ACMItemExtractionResult` Pydantic models |
| `open_notebook/extractors/prompt_context_builder.py` | CREATE | `build_picklist_context()`, `_select_item_name_groups()`, picklist formatting helpers |
| `prompts/acm/v3_building_extraction.jinja` | CREATE | Phase 1 template: extracts Building__c fields with SF vocabulary + worked examples |
| `prompts/acm/v3_item_extraction.jinja` | CREATE | Phase 2 template: extracts Item__c records with subsetted Item_Name + SF picklists |
| `open_notebook/extractors/orchestrator.py` | MODIFY | Add feature flag check + `_v3_extract_building_meta()`, `_v3_extract_items()`, `_normalize_v3_records()` helpers inside `_llm_extract_building()` |
| `open_notebook/graphs/utils.py` | MODIFY | Add `_get_v3_building_schema()` and `_get_v3_item_schema()` cached schema helpers |
| `tests/test_acm_schemas_v3.py` | CREATE | Unit tests for new Pydantic models (field validation, optional handling, defaults) |
| `tests/test_prompt_context_builder.py` | CREATE | Unit tests for `build_picklist_context()` and `_select_item_name_groups()` |

---

## Implementation Notes

### 1. `acm_schemas_v3.py`

- Place in `open_notebook/extractors/` alongside `acm_schemas.py`
- Do NOT modify `acm_schemas.py` or `ACMExtractionRecord` — V3 models are strictly additive
- `ACMItemRecord.sample_result` valid values: `"Positive"`, `"Assumed Positive"`, `"Negative"`, `"Assumed Negative"`, `"Negative - Treated as Positive"` (from `salesforce_enums.json` → `Sample_Analysis_Result_Material_Status__c`)
- `ACMItemRecord.condition` valid values: `"Poor"`, `"Fair"`, `"Stable"`, `"Unknown"`, `"N/A (negative)"`, `"N/A (assumed negative)"` (from `Condition__c`)
- `ACMItemRecord.friability_of_material` valid values: `"Non-friable"`, `"Friable"` (from `Friability_of_Material__c`)
- `ACMItemRecord.disturbance_potential` valid values: `"Low"`, `"Moderate"`, `"High"`, `"N/A (negative)"`, `"Unknown"`, `"N/A (assumed negative)"` (from `Disturbance_Potential_of_Material__c`)
- `ACMItemRecord.internal_external` valid values: `"Internal"`, `"External"`, `"External & Internal"` (from `Internal_External__c`)
- `ACMItemRecord.labelled` valid values: `"Yes"`, `"No"` (from `Labelled__c`)
- `BuildingExtractionResult.building_type` must match one of the 103 values in `Building_Type__c` picklist exactly
- `BuildingExtractionResult.building_category` must match one of the 13 `Building_Category__c` values
- No field validators needed in this story — validation will be handled by E30-S4's `SalesforcePicklistValidator` at runtime

### 2. `prompt_context_builder.py`

Create `open_notebook/extractors/prompt_context_builder.py`. The public API is:

```python
def build_picklist_context(
    schema_bundle: "SFSchemaBundle",
    acm_classification: Optional[str] = None,
) -> dict:
    """Build injectable picklist strings for V3 Jinja templates.

    Args:
        schema_bundle: Loaded SF schema bundle (from E30-S1 config loader).
        acm_classification: ACM_Classification__c value from Phase 1 result.
            Used to subset Item_Name__c options for Phase 2. If None, returns
            top 4 product group names (~100 values).

    Returns:
        Dict with keys: building_type_options, building_category_options,
        frequency_of_use_options, estimated_year_built_note,
        friability_options, acm_classification_options,
        acm_sub_classification_options, item_name_options,
        condition_options, disturbance_potential_options,
        sample_result_options, internal_external_options,
        labelled_options.
        All values are newline-joined strings of valid picklist values.
    """
```

**Private helpers:**

```python
def _select_item_name_groups(acm_classification: Optional[str]) -> List[str]:
    """Return relevant Item_Name__c values based on ACM_Classification__c.

    Groups:
      - Cement products / (f)     -> ceiling/wall/roof/eave/soffit items
      - Vinyl products / (f)      -> floor covering items + skirting
      - Insulation Products / (f) -> pipe/duct insulation items
      - Gasket...adhesives / (f)  -> gasket/flange/expansion items
      - Coatings / (f)            -> textured coating/render/plaster
      - Other / None              -> top 4 groups combined (~100 values)
    """

def _format_picklist(values: List[str]) -> str:
    """Join picklist values with newlines, one per line."""
    return "\n".join(f"- {v}" for v in values)
```

**Loading the SF schema bundle:**

The `schema_bundle` parameter accepts a `SFSchemaBundle` instance from `open_notebook/extractors/config_loader.py` (E30-S1). The context builder must NOT load the schema itself — it accepts an already-loaded bundle to avoid repeated I/O. The orchestrator holds responsibility for loading the bundle once and passing it down.

**Estimated_Year_Built handling:**

The picklist has 230 year values (1700-2029). Instead of injecting all 230, inject a note string: `"4-digit year between 1700-2029 (e.g., 1960, 1975, 2005)"`. This keeps the prompt concise.

**Item_Name groups to values mapping** (hardcoded constant in the module — picklist values are stable):

```python
_CEMENT_ITEMS = [
    "Ceiling", "Ceiling Lining", "Ceiling tiles", "Ceiling and awning",
    "Ceiling and vertical infill panel", "Ceiling and walls", "Ceiling cavity",
    "Ceiling Strapping", "Roof", "Roof cavity", "Roof covering", "Roofing",
    "Wall(s)", "Wall lining", "Wall cladding", "Wall covering", "Wall panelling",
    "Eave lining", "Eave and awning", "Eave and porch ceiling",
    "Soffit", "Soffit penetration", "Gable lining",
    "Flue", "Down pipe", "Gutter", "Ridge capping",
    "Cladding", "Infill panels", "Infill panels below windows",
    "Fascia", "Flashing", "Corrugated sheeting", "Flat sheeting",
]

_VINYL_ITEMS = [
    "Floor covering", "Floor covering (beneath carpet)", "Floor covering (lower layer)",
    "Floor covering (upper layer)", "Floor covering adhesive", "Floor covering lining",
    "Flooring", "Floor", "Floor (below screed)", "Floor and walls",
    "Floor Cavity/void", "Floor underlay", "Floor penetration",
    "Skirting", "Beneath floor covering", "Beneath carpet", "Beneath slab(s)",
]

_INSULATION_ITEMS = [
    "Pipework insulation", "Pipework", "Pipework brackets",
    "Pipework flange joints", "Pipework joint",
    "Ductwork insulation", "Ductwork", "Ductwork flange joint",
    "Boiler", "Boiler gasket", "Insulation", "Internal insulation (suspected)",
    "Ceiling cavity", "Roof cavity", "Return air plenum",
    "Air conditioning re-heat unit", "Air conditioning trunking",
    "Air handling unit", "Calorifier", "Hot water system",
    "Heater", "Heater flue", "Heating coils", "Lagging",
]

_GASKET_ITEMS = [
    "Gasket(s)", "Flange joints", "Expansion joint", "Valve",
    "Boiler gasket", "Pump flange joints", "Gland Packing",
    "Seal", "Oven door seal", "Door seal",
    "Joint", "Pebblecrete joint", "Penetration packing", "Penetration sealant",
    "Rope and string",
]

_COATING_ITEMS = [
    "Textured coating", "Render", "Plaster", "Mortar", "Grout",
    "Paint", "Putty", "Silicone", "Mastic", "Caulking",
]

_ACM_CLASS_TO_ITEMS: Dict[str, List[str]] = {
    "Cement products":    _CEMENT_ITEMS,
    "Cement products (f)": _CEMENT_ITEMS,
    "Vinyl products":     _VINYL_ITEMS,
    "Vinyl products (f)": _VINYL_ITEMS,
    "Insulation Products":  _INSULATION_ITEMS,
    "Insulation products (f)": _INSULATION_ITEMS,
    "Gasket, friction products and adhesives": _GASKET_ITEMS,
    "Gasket, friction products and adhesives (f)": _GASKET_ITEMS,
    "Coatings": _COATING_ITEMS,
    "Coatings (f)": _COATING_ITEMS,
}

_DEFAULT_ITEM_GROUPS = _CEMENT_ITEMS + _VINYL_ITEMS + _INSULATION_ITEMS + _GASKET_ITEMS
```

When `acm_classification` is provided and in the map, return the matching list plus 5 common catch-all items: `["Other", "Unknown", "Debris", "Dust", "Dust and debris"]`. When not in map or None, return `_DEFAULT_ITEM_GROUPS`.

### 3. `v3_building_extraction.jinja`

Template variables (all passed via `data={}` in `Prompter.render()`):

| Variable | Type | Description |
|----------|------|-------------|
| `content` | str | Building section text (same as current building_extraction.jinja) |
| `building_context` | dict | From `_create_building_prompt_context()` (building_id, building_name, page_start, page_end, etc.) |
| `picklists` | dict | From `build_picklist_context(schema_bundle)` — Phase 1 only needs building-level keys |

**Key sections to include:**

1. Role statement: "You are extracting building-level metadata for a Salesforce Building__c record."
2. Building context block (building ID, page range from `building_context`)
3. SF field name reference table with label, API name, and picklist hint for each extractable field
4. Worked examples: a Prensa-format ARA document header → BuildingExtractionResult, a SAMP document header → BuildingExtractionResult
5. Instructions to leave fields null if not present in document
6. Picklist injection blocks using `{{ picklists.building_type_options }}` etc.
7. Output format section referencing `BuildingExtractionResult` schema

**Worked example (AC8 — Prensa ARA format):**

```
INPUT:
  Asbestos Risk Assessment
  Building Name: Broadmeadows Police Complex
  Full Address: 21–25 Pearcedale Parade, Broadmeadows VIC 3047
  Construction Type: Brick/Concrete
  Number of Levels: 1
  Date of Report: March 2024
  Identifying Company: Prensa Pty Ltd

OUTPUT:
  building_name: "Broadmeadows Police Complex"
  building_address: "21-25 Pearcedale Parade"
  suburb: "Broadmeadows"
  postcode: "3047"
  construction_type: "Brick/Concrete"
  date_of_audit: "March 2024"
  identifying_company: "Prensa Pty Ltd"
  building_type: "Police Station"   <- choose from Building_Type__c picklist
  extraction_confidence: "high"
```

### 4. `v3_item_extraction.jinja`

Template variables:

| Variable | Type | Description |
|----------|------|-------------|
| `content` | str | Building section text |
| `building_context` | dict | Same as Phase 1 |
| `building_meta` | dict | Phase 1 result serialised: `building_result.model_dump()` |
| `picklists` | dict | Full picklist context including `item_name_options` (subsetted) |

**Key sections to include:**

1. Role statement with SF Item__c context
2. Building identity block from `building_meta` (name, address, type)
3. Critical extraction rules (same "every row = one record" rules from `building_extraction.jinja`)
4. SF field names reference table with API name, label, picklist values for constrained fields
5. Worked example 1: Prensa "Same as" reference row → ACMItemRecord
6. Worked example 2: SAMP "Assumed positive" fuse cartridge → ACMItemRecord
7. Worked example 3: "No Access" entry → ACMItemRecord
8. Item_Name subsetting note: "Use one of the provided Item_Name options; write exact value including punctuation. Use 'Other' if none match, and fill If_Other_Item_Name__c with the literal text."
9. Picklist blocks injected from `picklists` dict
10. Output format referencing `ACMItemExtractionResult` schema

**SF vocabulary mapping table to include (AC8):**

| Document Text | SF Field | SF Value |
|---------------|----------|----------|
| "Non Friable" / "Non-Friable" | Friability_of_Material__c | Non-friable |
| "Friable" | Friability_of_Material__c | Friable |
| "Good Condition" / "Good" | Condition__c | Stable |
| "Fair" / "Fair Condition" | Condition__c | Fair |
| "Poor" / "Poor Condition" | Condition__c | Poor |
| "Low" (disturbance) | Disturbance_Potential_of_Material__c | Low |
| "Medium" (disturbance) | Disturbance_Potential_of_Material__c | Moderate |
| "High" (disturbance) | Disturbance_Potential_of_Material__c | High |
| "Interior" / "Internal" | Internal_External__c | Internal |
| "Exterior" / "External" | Internal_External__c | External |
| "Positive" | Sample_Analysis_Result_Material_Status__c | Positive |
| "Assumed Positive" / "Presumed Positive" | Sample_Analysis_Result_Material_Status__c | Assumed Positive |
| "Negative" | Sample_Analysis_Result_Material_Status__c | Negative |
| "Assumed Negative" / "Presumed Negative" | Sample_Analysis_Result_Material_Status__c | Assumed Negative |

### 5. `orchestrator.py` Modifications

Add the following functions inside `orchestrator.py`, below the existing `_llm_extract_building()` function. Do NOT rename or alter the signature of `_llm_extract_building()`.

**New private helpers to add:**

```python
async def _v3_extract_building_meta(
    building_content: str,
    plan: BuildingExtractionPlan,
    state: dict,
    schema_bundle: Optional[Any],
) -> Optional["BuildingExtractionResult"]:
    """Phase 1: Extract Building__c metadata using v3_building_extraction.jinja.

    Returns None on failure (falls back to continuing without building meta).
    """

async def _v3_extract_items(
    building_content: str,
    plan: BuildingExtractionPlan,
    building_meta: Optional["BuildingExtractionResult"],
    state: dict,
    schema_bundle: Optional[Any],
) -> "ACMItemExtractionResult":
    """Phase 2: Extract Item__c records using v3_item_extraction.jinja.

    building_meta is passed from Phase 1 to subset Item_Name__c picklist.
    Returns ACMItemExtractionResult (records may be empty if no ACM data).
    """

def _normalize_v3_records(
    building_meta: Optional["BuildingExtractionResult"],
    item_result: "ACMItemExtractionResult",
    plan: BuildingExtractionPlan,
) -> List[ACMExtractionRecord]:
    """Map V3 SF field names -> ACMExtractionRecord for pipeline compatibility.

    This mapping bridges V3 two-phase output to the existing V2 ACMExtractionRecord
    format so that validate -> correct -> deduplicate -> save stages are unchanged.

    Field mapping:
      ACMItemRecord.room_or_area          -> ACMExtractionRecord.room_name
      ACMItemRecord.item_name             -> ACMExtractionRecord.product
      ACMItemRecord.acm_sub_classification -> ACMExtractionRecord.material_description
      ACMItemRecord.sample_result         -> ACMExtractionRecord.result + sample_result
      ACMItemRecord.nata_sample_no        -> ACMExtractionRecord.sample_no
      ACMItemRecord.condition             -> ACMExtractionRecord.material_condition
      ACMItemRecord.disturbance_potential -> ACMExtractionRecord.disturbance_potential
      ACMItemRecord.friability_of_material -> ACMExtractionRecord.friable
      ACMItemRecord.internal_external     -> ACMExtractionRecord.area_type (Internal->"Interior", External->"Exterior")
      ACMItemRecord.page_number           -> ACMExtractionRecord.page_number
      ACMItemRecord.no_access             -> ACMExtractionRecord.no_access
      ACMItemRecord.data_issues           -> ACMExtractionRecord.data_issues
      BuildingExtractionResult.building_name -> ACMExtractionRecord.building_name
    """
```

**Modification inside `_llm_extract_building()`:**

At the top of `_llm_extract_building()`, after reading `model_id` and `doc_meta` from state, add:

```python
ACM_V3_PROMPTS = os.getenv("ACM_V3_PROMPTS", "false").lower() == "true"
if ACM_V3_PROMPTS:
    # Load SF schema bundle once (cached via E30-S1 config_loader)
    schema_bundle = None
    try:
        from open_notebook.extractors.config_loader import load_sf_field_schema
        schema_bundle = load_sf_field_schema()
    except Exception as e:
        logger.warning(f"Could not load SF schema bundle for V3 prompts: {e}")

    building_meta = await _v3_extract_building_meta(
        building_content, plan, state, schema_bundle
    )
    item_result = await _v3_extract_items(
        building_content, plan, building_meta, state, schema_bundle
    )
    return _normalize_v3_records(building_meta, item_result, plan)
# ... existing V2 path follows unchanged
```

**Model provisioning for V3 calls:** Use the same `provision_langchain_model()` pattern as the existing `_llm_extract_building()`. Both Phase 1 and Phase 2 use `temperature=0.1, max_tokens=32768`.

**Error handling:** Both `_v3_extract_building_meta()` and `_v3_extract_items()` must catch all exceptions and log warnings. Phase 1 returning None does NOT block Phase 2 — proceed without building meta (picklist uses default item groups). Phase 2 failure returns an empty `ACMItemExtractionResult`.

### 6. `graphs/utils.py` Modifications

Add two new cached schema helpers following the exact `_get_acm_extraction_schema()` pattern (line 214):

```python
# Module-level caches for V3 schemas (E30-S7)
_V3_BUILDING_JSON_SCHEMA: dict | None = None
_V3_ITEM_JSON_SCHEMA: dict | None = None


def _get_v3_building_schema() -> dict:
    """Lazily generate and cache JSON Schema for BuildingExtractionResult."""
    global _V3_BUILDING_JSON_SCHEMA
    if _V3_BUILDING_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult
        _V3_BUILDING_JSON_SCHEMA = pydantic_to_openrouter_schema(BuildingExtractionResult)
    return _V3_BUILDING_JSON_SCHEMA


def _get_v3_item_schema() -> dict:
    """Lazily generate and cache JSON Schema for ACMItemExtractionResult."""
    global _V3_ITEM_JSON_SCHEMA
    if _V3_ITEM_JSON_SCHEMA is None:
        from open_notebook.extractors.acm_schemas_v3 import ACMItemExtractionResult
        _V3_ITEM_JSON_SCHEMA = pydantic_to_openrouter_schema(ACMItemExtractionResult)
    return _V3_ITEM_JSON_SCHEMA
```

Both helpers are used in `_v3_extract_building_meta()` and `_v3_extract_items()` via `_inject_response_format(model, _get_v3_building_schema(), "BuildingExtractionResult")` and `_inject_response_format(model, _get_v3_item_schema(), "ACMItemExtractionResult")`.

### Key Code Patterns to Follow

| Pattern | Source Location |
|---------|----------------|
| Lazy cached JSON schema | `open_notebook/graphs/utils.py:210-223` (`_get_acm_extraction_schema`) |
| LLM provisioning | `open_notebook/extractors/orchestrator.py:511-518` (inside `_llm_extract_building`) |
| `_inject_response_format` usage | `open_notebook/extractors/orchestrator.py:521-523` |
| `parse_json_response` + `model_validate` | `open_notebook/extractors/orchestrator.py:569-574` |
| `Prompter(prompt_template="acm/...")` | `open_notebook/extractors/orchestrator.py:528-536` |
| `provision_langchain_model` import | `open_notebook/extractors/orchestrator.py:493` |
| Feature flag env var pattern | `os.getenv("DOCLING_DIRECT_TABLE_EXTRACTION", "false").lower() == "true"` in `commands/source_commands.py` |

### `_normalize_v3_records()` Detailed Field Mapping

This is the bridge between V3 SF-named output and the existing `ACMExtractionRecord`. Keep it in sync with E30-S3 field aliases.

```
SF Name (ACMItemRecord)               → ACMExtractionRecord field
-------------------------------------------------------------------
item_name                              product
acm_sub_classification                 material_description
room_or_area                           room_name
level                                  floor_level
location_in_room                       location
friability_of_material                 friable
acm_classification                     acm_product_group
sample_result                          result + sample_result
nata_sample_no                         sample_no
condition                              material_condition
disturbance_potential                  disturbance_potential
quantity (float)                       quantity (str, via str() conversion)
internal_external "Internal"           area_type = "Interior"
internal_external "External"           area_type = "Exterior"
internal_external "External & Internal" area_type = "Exterior"  (dominant)
no_access                              no_access
data_issues                            data_issues
page_number                            page_number
hygienist_recommendations              hygienist_recommendations
additional_comments                    additional_comments
if_other_item_name                     (append to data_issues: "Item name: <value>")
labelled "Yes"                         acm_labelled = True
labelled "No"                          acm_labelled = False

From BuildingExtractionResult (if not None):
building_name                          building_name
identifying_company                    identifying_company
```

**Building ID:** Always use `plan.building_id` from the orchestrator plan, not from the building meta (the plan's ID comes from the document structure analysis and is authoritative).

---

## Test Spec

### `tests/test_acm_schemas_v3.py`

**Class `TestBuildingExtractionResult`:**

| Test | Assertion |
|------|-----------|
| `test_minimal_creation` | `BuildingExtractionResult()` instantiates with all None fields, `extraction_confidence="medium"` |
| `test_full_creation` | All 11 fields populated, model_dump() returns correct keys |
| `test_confidence_default` | `extraction_confidence` defaults to `"medium"` |
| `test_extraction_notes_optional` | `extraction_notes=None` is valid |

**Class `TestACMItemRecord`:**

| Test | Assertion |
|------|-----------|
| `test_minimal_creation` | `ACMItemRecord()` instantiates with defaults |
| `test_data_issues_default` | `data_issues` defaults to `[]` (not None) |
| `test_no_access_default` | `no_access` defaults to `False` |
| `test_quantity_float` | `quantity=10.5` is valid, `quantity=None` is valid |
| `test_full_sf_fields` | All 17 fields populated, model_dump() round-trips correctly |

**Class `TestACMItemExtractionResult`:**

| Test | Assertion |
|------|-----------|
| `test_empty_result` | `ACMItemExtractionResult()` has `records=[]`, `status="valid"` |
| `test_with_records` | List of 3 `ACMItemRecord` items accepted |
| `test_status_values` | `"valid"`, `"no_acm_data"`, `"invalid"` all accepted as strings |
| `test_model_dump_roundtrip` | `model_validate(model_dump())` roundtrip succeeds |

### `tests/test_prompt_context_builder.py`

**Class `TestSelectItemNameGroups`:**

| Test | Assertion |
|------|-----------|
| `test_cement_products_group` | `_select_item_name_groups("Cement products")` includes "Ceiling", "Roof", "Wall(s)", "Eave lining" |
| `test_cement_products_friable` | `_select_item_name_groups("Cement products (f)")` returns same set as non-friable |
| `test_vinyl_products_group` | Returns "Floor covering", "Skirting", "Beneath floor covering" |
| `test_insulation_group` | Returns "Pipework insulation", "Ductwork insulation", "Boiler" |
| `test_gasket_group` | Returns "Gasket(s)", "Flange joints", "Expansion joint" |
| `test_coating_group` | Returns "Textured coating", "Render", "Plaster" |
| `test_none_classification` | Returns union of top 4 groups (cement + vinyl + insulation + gasket) |
| `test_unknown_classification` | `_select_item_name_groups("Other")` returns default groups |
| `test_always_includes_other` | Every group result includes "Other" and "Unknown" catch-all values |
| `test_no_duplicates` | `len(result) == len(set(result))` — no duplicate Item_Name values |

**Class `TestBuildPicklistContext`:**

| Test | Assertion |
|------|-----------|
| `test_returns_required_keys` | Dict contains all 13 expected keys |
| `test_building_type_options_formatted` | `picklists["building_type_options"]` is non-empty string, contains "Classroom", "School" |
| `test_building_category_options` | Contains "Educational and training facilities" |
| `test_friability_options` | Contains "Non-friable" and "Friable" |
| `test_acm_classification_options` | Contains all 18 `ACM_Classification__c` values |
| `test_sample_result_options` | Contains all 5 `Sample_Analysis_Result_Material_Status__c` values |
| `test_condition_options` | Contains "Stable", "Poor", "Fair", "N/A (negative)" |
| `test_estimated_year_built_note` | Returns string with "1700" and "2029" (range note, not all 230 years) |
| `test_item_name_subsets_by_classification` | When `acm_classification="Vinyl products"`, `item_name_options` contains "Floor covering" |
| `test_item_name_default_without_classification` | Without classification, returns ~100 items from top 4 groups |
| `test_with_mock_schema_bundle` | Works with a mock `SFSchemaBundle` that has minimal picklist data |

**Benchmark test stubs (AC6, AC7 — structure only, no LLM required):**

```python
class TestBroadmeadowsBenchmarkStructure:
    """Verifies test structure for benchmark validation (AC6).

    NOTE: These are structure-only tests. The actual LLM call is NOT made.
    They verify that the two-phase pipeline can be invoked with correct inputs.
    """
    def test_phase1_can_receive_building_content(self):
        # Verify BuildingExtractionResult can be instantiated with
        # typical Broadmeadows header fields
        result = BuildingExtractionResult(
            building_name="Broadmeadows Police Complex",
            building_address="21-25 Pearcedale Parade",
            suburb="Broadmeadows",
            postcode="3047",
            building_type="Police Station",
        )
        assert result.building_name == "Broadmeadows Police Complex"

    def test_phase2_can_receive_item_records(self):
        # Verify ACMItemExtractionResult can hold typical item records
        item = ACMItemRecord(
            room_or_area="Boiler Room",
            item_name="Pipework insulation",
            acm_classification="Insulation Products",
            sample_result="Positive",
            friability_of_material="Non-friable",
            condition="Stable",
        )
        result = ACMItemExtractionResult(records=[item])
        assert len(result.records) == 1


class TestAlexanderBenchmarkStructure:
    """Verifies test structure for Alexander benchmark (AC7)."""
    def test_normalize_v3_records_handles_ara_format(self):
        # Alexander uses ARA format — item records have room_or_area not room_id
        item = ACMItemRecord(
            room_or_area="External",
            internal_external="External",
            item_name="Eave lining",
            acm_sub_classification="Flat sheeting",
            sample_result="Assumed Positive",
            friability_of_material="Non-friable",
        )
        result = ACMItemExtractionResult(records=[item])
        # Stub plan
        from open_notebook.extractors.orchestrator import BuildingExtractionPlan, ExtractionStrategy
        plan = BuildingExtractionPlan(
            building_id="B001",
            building_name="Main Building",
            page_range=(1, 10),
            strategy=ExtractionStrategy.FULL_LLM,
            complexity="complex",
        )
        normalized = _normalize_v3_records(None, result, plan)
        assert len(normalized) == 1
        assert normalized[0].product == "Eave lining"
        assert normalized[0].area_type == "Exterior"
```

---

## Acceptance Criteria Checklist

| ID | Criterion | How to Verify |
|----|-----------|---------------|
| AC1 | `prompts/acm/v3_building_extraction.jinja` exists and extracts Building__c fields only | `Glob("prompts/acm/v3_building_extraction.jinja")` finds file; template variables include `picklists.building_type_options` |
| AC2 | `prompts/acm/v3_item_extraction.jinja` exists and extracts Item__c fields with SF vocabulary | `Glob("prompts/acm/v3_item_extraction.jinja")` finds file; template includes `acm_classification`, `item_name_options`, SF mapping table |
| AC3 | Dynamic picklist injection: prompts receive valid picklist values from `build_picklist_context()` at runtime | `test_build_picklist_context.py::test_returns_required_keys` passes; `test_building_type_options_formatted` confirms SF values injected |
| AC4 | Item_Name__c subsetting: 294 values filtered by classification context | `test_prompt_context_builder.py::test_item_name_subsets_by_classification` passes; vinyl classification returns floor items, not insulation items |
| AC5 | Structured output: `BuildingExtractionResult` and `ACMItemExtractionResult` Pydantic models exist in `acm_schemas_v3.py` | `tests/test_acm_schemas_v3.py` all pass; `Glob("open_notebook/extractors/acm_schemas_v3.py")` finds file |
| AC6 | Broadmeadows benchmark: test structure exists (no LLM run required) | `TestBroadmeadowsBenchmarkStructure` tests pass without API calls |
| AC7 | Alexander benchmark: no regression test structure exists | `TestAlexanderBenchmarkStructure` tests pass without API calls |
| AC8 | Worked examples in both templates | Review `v3_building_extraction.jinja` for Prensa/ARA header example; review `v3_item_extraction.jinja` for "Same as", "Assumed positive", "No Access" examples |

---

## Verification Protocol

Before marking this story done, run:

```bash
# 1. Lint
uv run ruff check open_notebook/extractors/acm_schemas_v3.py
uv run ruff check open_notebook/extractors/prompt_context_builder.py
uv run ruff check open_notebook/extractors/orchestrator.py
uv run ruff check open_notebook/graphs/utils.py

# 2. Tests
uv run pytest tests/test_acm_schemas_v3.py -v
uv run pytest tests/test_prompt_context_builder.py -v

# 3. Full test suite (no regressions)
uv run pytest tests/ -x --ignore=tests/test_e2e_extraction.py

# 4. File existence check
# All 8 files listed in File Changes table must exist
```

**Expected test counts:** `test_acm_schemas_v3.py` ~12 tests, `test_prompt_context_builder.py` ~20 tests.

**Pre-existing failures to ignore:** `test_e2e_extraction.py::test_full_pipeline_produces_records`, `test_field_config_api.py::test_update_field_config_toggle_active`, `test_source_commands_docling.py::test_creates_acm_table_section_records`.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Phase 1 LLM returns wrong `building_type` (hallucination outside picklist) | MEDIUM | LOW | Picklist values are injected into prompt; `_normalize_v3_records()` passes raw string through; validation is E30-S4's job |
| `_select_item_name_groups()` returns wrong groups for a rare classification | LOW | MEDIUM | Default group returns 100 most common items; "Other" always included; `if_other_item_name` escape hatch |
| `build_picklist_context()` fails when `schema_bundle` not loaded | LOW | MEDIUM | Wrap in try/except; fall back to empty strings for missing picklists; LLM will extract without constraints |
| `_normalize_v3_records()` field mapping diverges from E30-S3 aliases | MEDIUM | HIGH | Add explicit assertion test that normalized record fields are non-None for a typical item; cross-reference E30-S3 `AliasPath` definitions |
| Feature flag defaulting to false means V3 path never tested in CI | LOW | LOW | Test `_normalize_v3_records()` directly without the flag; integration test uses `ACM_V3_PROMPTS=true` env in test setup |

---

## Dependencies

| Direction | Story | Relationship |
|-----------|-------|-------------|
| Depends on | E30-S6 (BAR->SF Vocabulary) | SF picklist values used in prompts are E30-S6 canonical (e.g., "Stable" not "Good", "Non-friable" not "Non Friable") |
| Depends on | E31-S2 (Provider Adapter Framework) | Adapter output shapes confirmed; `ACMExtractionRecord` field set stable |
| Depends on | E30-S1 (SF Schema Config Loader) | `load_sf_field_schema()` provides `SFSchemaBundle` for `build_picklist_context()` |
| Blocks | E32-S1 (Building AI Extraction Node) | E32-S1 uses `v3_building_extraction.jinja` + `BuildingExtractionResult` defined here |
| Blocks | E32-S2 (Item AI Extraction Node) | E32-S2 uses `v3_item_extraction.jinja` + `ACMItemExtractionResult` defined here |

---

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Completion Notes

_To be filled by dev agent_

### File List

| Action | File Path |
|--------|-----------|
| CREATE | `open_notebook/extractors/acm_schemas_v3.py` |
| CREATE | `open_notebook/extractors/prompt_context_builder.py` |
| CREATE | `prompts/acm/v3_building_extraction.jinja` |
| CREATE | `prompts/acm/v3_item_extraction.jinja` |
| MODIFY | `open_notebook/extractors/orchestrator.py` |
| MODIFY | `open_notebook/graphs/utils.py` |
| CREATE | `tests/test_acm_schemas_v3.py` |
| CREATE | `tests/test_prompt_context_builder.py` |
