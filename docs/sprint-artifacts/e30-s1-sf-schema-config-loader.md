# Tech Spec: E30-S1 — SF Schema Config Loader

**Story ID:** E30-S1
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-1
**Story Points:** 5
**Risk Level:** HIGH
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:** None (first V3 story)

---

## User Story

As a system architect, I want the Salesforce field schema (Building__c and Item__c objects) loaded into a structured, queryable config at API startup so that all downstream V3 extraction agents, validators, and exporters share a single authoritative source of truth for SF field definitions, picklist values, and dependency chains.

---

## Acceptance Criteria

| ID  | Criterion | Verification Method |
|-----|-----------|---------------------|
| AC1 | Parse `building_fields_summary.md` (143 fields, 18 picklists) into a structured `BuildingFieldConfig` Pydantic model keyed by `API Name` | Unit test: assert `len(config.fields) == 143`, assert `len(config.picklists) == 18` |
| AC2 | Parse `item_fields_summary.md` (154 fields, 23 picklists) into a structured `ItemFieldConfig` Pydantic model keyed by `API Name` | Unit test: assert `len(config.fields) == 154`, assert `len(config.picklists) == 23` |
| AC3 | Build dependency chain: `Friability_of_Material__c` (2 values) → `ACM_Classification__c` (18 values) → `ACM_Sub_Classification__c` (133 values) with 36 valid Friability+Classification combos | Unit test: assert correct subclasses returned per (friability, classification) pair |
| AC4 | Build dependency chain: `Building_Type__c` (114 values) → `Building_Category__c` (13 values) | Unit test: assert category for known building types, assert 13 unique categories exist |
| AC5 | Migration 38 adds `building_fields`, `item_fields`, `picklists`, `dependencies`, and `version` fields to `field_schema` table using `DEFINE FIELD IF NOT EXISTS` (additive, does not break existing `field_schema:default`) | Migration SQL review + existing field_schema:default record remains intact after upgrade |
| AC6 | API startup idempotently loads SF schema to `field_schema:sf_v1` — only upserts when `version != "salesforce-v1"` or record is absent | Unit test: call loader twice, verify DB write count == 1 |
| AC7 | `GET /api/acm/field-schema` returns `SFFieldSchemaConfigResponse` JSON with building_fields, item_fields, picklists, and dependencies | Integration test: HTTP 200, response validates against schema |
| AC8 | Unit tests cover: valid config parse, malformed markdown row (missing column), empty picklist section, and missing source file (graceful error) | pytest: all 4 cases pass |
| AC9 | `Item_Name__c` 294-value picklist is loaded and queryable via `get_item_names_by_product_group(acm_classification: str) -> list[str]` helper using `ITEM_NAME_TO_PRODUCT_GROUP` mapping | Unit test: assert known item names returned for each of the 18 ACM product group values |

---

## Technical Design

### Overview

This story introduces a **parallel SF config track** alongside the existing BAR config track. It never modifies existing BAR models, loader functions, or DB records. All new SF code is additive.

### Architecture Decision: Additive-Only Pattern

The existing BAR field config system (`FieldDef`, `FieldSchemaConfig`, `load_field_schema()`, `field_schema:default`) must remain completely untouched. This story creates a separate, named record `field_schema:sf_v1` using new Pydantic models prefixed with `SF`.

```
Existing (preserved):                   New (additive):
----------------------------            ----------------------------
FieldDef                                SFFieldDef
FieldSchemaConfig                       SFFieldSchemaConfig
load_field_schema()                     load_sf_field_schema()
field_schema:default (SurrealDB)        field_schema:sf_v1 (SurrealDB)
GET /api/acm/field-config               GET /api/acm/field-schema
```

### Source Data Files

The loader reads from V3 reference markdown files that describe the Salesforce schema:

| File | Description | Fields | Picklists |
|------|-------------|--------|-----------|
| `V3/output/building_fields_summary.md` | Building__c field reference | 143 | 18 |
| `V3/output/item_fields_summary.md` | Item__c field reference | 154 | 23 |
| `V3/output/picklist-dependency-mappings.md` | Dependency chains | — | — |

These files are already committed to the repository and are the authoritative source for SF schema parsing.

### Pydantic Models — `open_notebook/extractors/parsers/field_config.py` (additions only)

```python
class SFFieldDef(BaseModel):
    """Definition of a single Salesforce object field."""

    api_name: str          # e.g. "Building_Type__c" — primary key
    label: str             # e.g. "Asset Type"
    field_type: str        # "string" | "picklist" | "boolean" | "date" | "datetime"
                           # | "double" | "currency" | "reference" | "textarea"
                           # | "id" | "location" | "url"
    length: Optional[int] = None
    nillable: bool = True
    custom: bool = False
    calc: bool = False      # Formula/rollup field
    updateable: bool = True
    notes: Optional[str] = None
    is_restricted_picklist: bool = False  # Derived from notes "Restricted picklist"
    is_dependent: bool = False            # Dependent on a controller picklist
    controller_field: Optional[str] = None  # API name of controller (if dependent)


class SFFieldSchemaConfig(BaseModel):
    """Complete Salesforce object field schema configuration."""

    object_name: str           # "Building__c" or "Item__c"
    object_label: str          # "Asset Class" or "Item"
    total_fields: int
    custom_fields: int
    picklist_fields: int
    fields: list[SFFieldDef]
    picklists: dict[str, list[str]]       # api_name -> [values]
    version: str = "salesforce-v1"


class SFDependencyChain(BaseModel):
    """A dependent picklist chain mapping."""

    controller_api_name: str    # e.g. "Friability_of_Material__c"
    dependent_api_name: str     # e.g. "ACM_Classification__c"
    mapping: dict[str, list[str]]  # controller_value -> [valid dependent values]


class SFSchemaBundle(BaseModel):
    """Full SF schema bundle stored in field_schema:sf_v1."""

    version: str = "salesforce-v1"
    building_fields: SFFieldSchemaConfig
    item_fields: SFFieldSchemaConfig
    picklists: dict[str, list[str]]       # Combined picklists across both objects
    dependencies: list[SFDependencyChain] # All dependency chains
    loaded_at: Optional[str] = None       # ISO timestamp when loaded
```

### Config Loader — `open_notebook/extractors/parsers/config_loader.py` (additions only)

New functions added to the bottom of the existing file, preserving all existing code:

```python
# --- SF Schema Config (V3) --- #

SF_SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "V3", "output"
)

_SF_SCHEMA: Optional[SFSchemaBundle] = None

def load_sf_field_schema() -> SFSchemaBundle:
    """Load Salesforce field schema from V3 markdown files.

    Returns cached bundle on subsequent calls.
    Raises SFSchemaLoadError on malformed source files.
    """
    ...

def _parse_sf_field_table(markdown_content: str, object_name: str) -> SFFieldSchemaConfig:
    """Parse a *_fields_summary.md markdown table into SFFieldSchemaConfig.

    Keyed on 'API Name' column (not Label).
    Handles:
    - Optional spaces around | delimiters
    - Empty cells (treats as None/default)
    - Boolean columns Y/blank -> True/False
    - 'Restricted picklist' detection from Notes column
    """
    ...

def _extract_picklist_values(markdown_content: str) -> dict[str, list[str]]:
    """Extract picklist value lists embedded in Notes column of field tables.

    Example Notes: "[Years: 1700-2029 (330 values)]"
    """
    ...

def _build_friability_chain() -> SFDependencyChain:
    """Build Friability_of_Material__c -> ACM_Classification__c dependency.

    Returns all 18 valid classification values grouped by the 2 friability values.
    """
    ...

def _build_acm_classification_chain() -> SFDependencyChain:
    """Build ACM_Classification__c -> ACM_Sub_Classification__c dependency.

    36 valid (friability, classification) combinations with product type lists.
    Source: picklist-dependency-mappings.md
    """
    ...

def _build_building_type_chain() -> SFDependencyChain:
    """Build Building_Type__c -> Building_Category__c dependency.

    114 building types -> 13 categories.
    Source: picklist-dependency-mappings.md
    """
    ...

# Item_Name__c product group mapping (294 values, not a dependent picklist)
ITEM_NAME_TO_PRODUCT_GROUP: dict[str, str] = {
    # Populated with all 294 item names mapped to their ACM_Classification group
    # e.g. "Corrugated Roof Sheeting": "Cement products",
    # e.g. "Lagging": "Insulation Products",
    ...
}

def get_item_names_by_product_group(acm_classification: str) -> list[str]:
    """Return all Item_Name__c values for a given ACM_Classification value.

    Args:
        acm_classification: e.g. "Cement products", "Insulation Products",
                            "Cement products (f)", "Insulation products (f)"

    Returns:
        Sorted list of item names belonging to that product group.
    """
    return sorted(
        name for name, group in ITEM_NAME_TO_PRODUCT_GROUP.items()
        if group == acm_classification
    )
```

#### Markdown Table Parsing Logic

The `*_fields_summary.md` files use a GitHub Flavored Markdown table with this column schema:

```
| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |
```

Parsing rules:
1. Skip lines until the header row containing `| # | API Name |` is found
2. Skip the separator row (`|---|---|...`)
3. For each data row, split on `|`, strip whitespace from each cell
4. Column `#` is integer (row number, 1-based)
5. `Nillable`, `Custom`, `Calc`, `Updateable` are boolean: `Y` = True, empty = False
6. `Length` is integer if present, None if empty
7. `Notes` contains free text; check for "Restricted picklist" substring to set `is_restricted_picklist`
8. `Notes` containing "Dependent on `<api_name>`" sets `is_dependent = True` and parses `controller_field`
9. `API Name` column is the primary key — never use `Label` as the key

#### Picklist Data Location

Picklist values are embedded in `picklist-dependency-mappings.md` and in the Notes column of the field tables. The loader uses hardcoded data structures (not runtime parsing of the full dependency file) for the three dependency chains, since the data is stable and well-defined.

### Startup Loader — `api/sf_schema_provisioning.py` (new file)

Follows the `run_model_provisioning()` pattern in `api/model_provisioning.py`.

```python
"""
SF Schema Provisioning Module

Idempotently loads Salesforce field schema into SurrealDB field_schema:sf_v1
at API startup.
"""

from loguru import logger
from open_notebook.database.repository import repo_query
from open_notebook.extractors.parsers.config_loader import load_sf_field_schema

SF_SCHEMA_RECORD_ID = "field_schema:sf_v1"
SF_SCHEMA_VERSION = "salesforce-v1"


async def run_sf_schema_provisioning() -> None:
    """Main entry point. Called from api/main.py lifespan after run_model_provisioning().

    Idempotent: only writes to DB if record is absent or version differs.
    Non-fatal: logs warning on failure, does not block API startup.
    """
    try:
        # Check if current version is already loaded
        existing = await repo_query(
            f"SELECT version FROM {SF_SCHEMA_RECORD_ID}"
        )
        if existing and existing[0].get("version") == SF_SCHEMA_VERSION:
            logger.info(
                f"SF schema already at version {SF_SCHEMA_VERSION}, skipping provisioning"
            )
            return

        # Load and upsert
        schema = load_sf_field_schema()
        await _upsert_sf_schema(schema)
        logger.success(
            f"SF schema provisioning complete: version={SF_SCHEMA_VERSION}, "
            f"building_fields={len(schema.building_fields.fields)}, "
            f"item_fields={len(schema.item_fields.fields)}"
        )

    except Exception as e:
        logger.warning(f"SF schema provisioning failed (non-fatal): {e}")


async def _upsert_sf_schema(schema: SFSchemaBundle) -> None:
    """Write schema bundle to field_schema:sf_v1."""
    import json
    from datetime import datetime, timezone

    schema.loaded_at = datetime.now(timezone.utc).isoformat()
    schema_dict = schema.model_dump()

    await repo_query(
        """
        UPSERT $id SET
            version = $version,
            building_fields = $building_fields,
            item_fields = $item_fields,
            picklists = $picklists,
            dependencies = $dependencies,
            loaded_at = $loaded_at,
            updated = time::now()
        """,
        {
            "id": SF_SCHEMA_RECORD_ID,
            "version": schema.version,
            "building_fields": json.dumps(schema_dict["building_fields"]),
            "item_fields": json.dumps(schema_dict["item_fields"]),
            "picklists": json.dumps(schema_dict["picklists"]),
            "dependencies": json.dumps(schema_dict["dependencies"]),
            "loaded_at": schema.loaded_at,
        }
    )
```

### `api/main.py` — Startup Hook (additive change)

Add import and call in the lifespan function, after `run_model_provisioning()`:

```python
from api.sf_schema_provisioning import run_sf_schema_provisioning

# In lifespan(), after run_model_provisioning():
try:
    await run_sf_schema_provisioning()
except Exception as e:
    logger.warning(f"SF schema provisioning failed (non-fatal): {e}")
```

### API Endpoint — `api/routers/acm.py` (additive change)

New endpoint alongside existing `/field-config`:

```python
@router.get("/field-schema", response_model=SFFieldSchemaConfigResponse)
async def get_sf_field_schema():
    """
    Get the current Salesforce field schema configuration.

    Returns the SF schema bundle loaded from field_schema:sf_v1.
    Falls back to in-memory parse if DB record not yet populated.
    """
```

### API Response Model — `api/models.py` (additions only)

```python
# =============================================================================
# SF Field Schema Config Models (E30-S1 — V3 Foundation)
# =============================================================================

class SFFieldDefResponse(BaseModel):
    """Single Salesforce field definition."""
    api_name: str
    label: str
    field_type: str
    length: Optional[int] = None
    nillable: bool
    custom: bool
    calc: bool
    updateable: bool
    notes: Optional[str] = None
    is_restricted_picklist: bool
    is_dependent: bool
    controller_field: Optional[str] = None


class SFDependencyChainResponse(BaseModel):
    """A dependent picklist chain."""
    controller_api_name: str
    dependent_api_name: str
    mapping: Dict[str, List[str]]


class SFFieldSchemaObjectResponse(BaseModel):
    """Field schema for a single SF object."""
    object_name: str
    object_label: str
    total_fields: int
    custom_fields: int
    picklist_fields: int
    fields: List[SFFieldDefResponse]
    picklists: Dict[str, List[str]]
    version: str


class SFFieldSchemaConfigResponse(BaseModel):
    """Full SF schema bundle response."""
    version: str
    building_fields: SFFieldSchemaObjectResponse
    item_fields: SFFieldSchemaObjectResponse
    picklists: Dict[str, List[str]]
    dependencies: List[SFDependencyChainResponse]
    loaded_at: Optional[str] = None
```

### V3 Compliance

This story is the foundation for V3 and must not compromise existing functionality:

1. **BAR config isolation**: `FieldDef`, `FieldSchemaConfig`, `load_field_schema()`, `_load_db_field_config()`, `_save_db_field_config()`, and `GET /api/acm/field-config` are all untouched.
2. **DB record isolation**: `field_schema:default` is the BAR record. `field_schema:sf_v1` is the SF record. The migration uses `DEFINE FIELD IF NOT EXISTS` so existing records are not affected.
3. **No import pollution**: `magic_pdf`, `paddle`, or any MinerU imports must not be added to this module.
4. **Test isolation**: `tests/test_field_config.py` (9 BAR tests) and `tests/test_field_config_api.py` must continue to pass unchanged.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/parsers/field_config.py` | MODIFY (additive) | Add `SFFieldDef`, `SFFieldSchemaConfig`, `SFDependencyChain`, `SFSchemaBundle` Pydantic models at bottom of file |
| `open_notebook/extractors/parsers/config_loader.py` | MODIFY (additive) | Add `load_sf_field_schema()`, `_parse_sf_field_table()`, `_extract_picklist_values()`, `_build_friability_chain()`, `_build_acm_classification_chain()`, `_build_building_type_chain()`, `ITEM_NAME_TO_PRODUCT_GROUP`, `get_item_names_by_product_group()` |
| `api/sf_schema_provisioning.py` | CREATE | `run_sf_schema_provisioning()` startup loader |
| `api/models.py` | MODIFY (additive) | Add `SFFieldDefResponse`, `SFDependencyChainResponse`, `SFFieldSchemaObjectResponse`, `SFFieldSchemaConfigResponse` |
| `api/routers/acm.py` | MODIFY (additive) | Add `GET /api/acm/field-schema` endpoint and import new models |
| `api/main.py` | MODIFY (additive) | Import and call `run_sf_schema_provisioning()` in lifespan, after `run_model_provisioning()` |
| `migrations/38.surrealql` | CREATE | Additive `DEFINE FIELD IF NOT EXISTS` for SF columns on `field_schema` table |
| `migrations/38_down.surrealql` | CREATE | No-op rollback (fields are optional, removing them is not safe) |
| `tests/test_config_loader.py` | CREATE | Unit tests for SF config parsing (AC1–AC4, AC6, AC8, AC9) |

**Files NOT to modify:**
- `open_notebook/extractors/parsers/generic.py`
- `open_notebook/extractors/acm_validator.py`
- `tests/test_field_config.py`
- `tests/test_field_config_api.py`

---

## Database Changes

### Migration 38: `migrations/38.surrealql`

```sql
-- Migration 38: Add SF schema columns to field_schema table (E30-S1 V3 Foundation)
-- Additive only — existing field_schema:default record is NOT affected.
-- New record field_schema:sf_v1 uses these new columns.

DEFINE FIELD IF NOT EXISTS building_fields ON TABLE field_schema TYPE option<string>;
DEFINE FIELD IF NOT EXISTS item_fields     ON TABLE field_schema TYPE option<string>;
DEFINE FIELD IF NOT EXISTS picklists       ON TABLE field_schema TYPE option<string>;
DEFINE FIELD IF NOT EXISTS dependencies    ON TABLE field_schema TYPE option<string>;
DEFINE FIELD IF NOT EXISTS loaded_at       ON TABLE field_schema TYPE option<string>;
```

Note: `building_fields`, `item_fields`, `picklists`, and `dependencies` are stored as JSON strings (type `option<string>`) to avoid SurrealDB nested object schema complexity. This matches the existing `config_json` field pattern in `field_schema:default`.

### Migration 38 Down: `migrations/38_down.surrealql`

```sql
-- Migration 38 down: No-op — removing optional fields would delete data from any
-- field_schema:sf_v1 records. Fields are additive and safe to leave.
-- To fully revert, manually DELETE field_schema:sf_v1;
RETURN "38_down: no-op";
```

### Resulting DB Record Shape (`field_schema:sf_v1`)

```json
{
  "id": "field_schema:sf_v1",
  "version": "salesforce-v1",
  "building_fields": "<JSON string of SFFieldSchemaConfig>",
  "item_fields": "<JSON string of SFFieldSchemaConfig>",
  "picklists": "<JSON string of combined picklists dict>",
  "dependencies": "<JSON string of [SFDependencyChain, ...]>",
  "loaded_at": "2026-03-03T00:00:00.000Z",
  "created": "2026-03-03T00:00:00.000Z",
  "updated": "2026-03-03T00:00:00.000Z"
}
```

---

## API Changes

### New Endpoint

#### `GET /api/acm/field-schema`

Returns the complete Salesforce schema bundle.

**Request:** No parameters.

**Response: 200 OK**

```json
{
  "version": "salesforce-v1",
  "loaded_at": "2026-03-03T10:00:00.000Z",
  "building_fields": {
    "object_name": "Building__c",
    "object_label": "Asset Class",
    "total_fields": 143,
    "custom_fields": 130,
    "picklist_fields": 18,
    "version": "salesforce-v1",
    "fields": [
      {
        "api_name": "Building_Type__c",
        "label": "Asset Type",
        "field_type": "picklist",
        "length": 255,
        "nillable": false,
        "custom": true,
        "calc": false,
        "updateable": true,
        "notes": "Restricted picklist; Select from the dropdown list provided in the Resource Centre Tab",
        "is_restricted_picklist": true,
        "is_dependent": false,
        "controller_field": null
      }
    ],
    "picklists": {
      "Building_Type__c": ["Commercial", "School", "..."],
      "Building_Category__c": ["Agriculture", "Commercial and retail", "..."]
    }
  },
  "item_fields": {
    "object_name": "Item__c",
    "object_label": "Item",
    "total_fields": 154,
    "custom_fields": 142,
    "picklist_fields": 23,
    "version": "salesforce-v1",
    "fields": [
      {
        "api_name": "Friability_of_Material__c",
        "label": "Friability of Material",
        "field_type": "picklist",
        "length": 255,
        "nillable": true,
        "custom": true,
        "calc": false,
        "updateable": true,
        "notes": "Restricted picklist; ...",
        "is_restricted_picklist": true,
        "is_dependent": false,
        "controller_field": null
      },
      {
        "api_name": "ACM_Classification__c",
        "label": "ACM Product Group",
        "field_type": "picklist",
        "length": 255,
        "nillable": true,
        "custom": true,
        "calc": false,
        "updateable": true,
        "notes": "Dependent on Friability_of_Material__c; Restricted picklist; ...",
        "is_restricted_picklist": true,
        "is_dependent": true,
        "controller_field": "Friability_of_Material__c"
      }
    ],
    "picklists": {
      "Friability_of_Material__c": ["Non-friable", "Friable"],
      "ACM_Classification__c": ["Cement products", "Bitumen products", "..."],
      "Item_Name__c": ["Corrugated Roof Sheeting", "Lagging", "..."]
    }
  },
  "picklists": {
    "Building_Type__c": ["..."],
    "Building_Category__c": ["..."],
    "Friability_of_Material__c": ["Non-friable", "Friable"],
    "ACM_Classification__c": ["..."],
    "ACM_Sub_Classification__c": ["..."],
    "Item_Name__c": ["..."]
  },
  "dependencies": [
    {
      "controller_api_name": "Friability_of_Material__c",
      "dependent_api_name": "ACM_Classification__c",
      "mapping": {
        "Non-friable": ["Bitumen products", "Cement products", "Coatings", "Gasket, friction products and adhesives", "Insulation Products", "Other", "Reinforced plastics/resins (excluding bitumen products)", "Textiles", "Vinyl products"],
        "Friable": ["Bitumen products (f)", "Cement products (f)", "Coatings (f)", "Gasket, friction products and adhesives (f)", "Insulation products (f)", "Other (f)", "Reinforced plastics/resins (excluding bitumen products) (f)", "Textiles (f)", "Vinyl products (f)"]
      }
    },
    {
      "controller_api_name": "ACM_Classification__c",
      "dependent_api_name": "ACM_Sub_Classification__c",
      "mapping": {
        "Cement products": ["Ceiling Tiles", "Cement Flue", "..."],
        "Insulation products (f)": ["AIB (Asbestos Insulated Board)", "Lagging", "..."]
      }
    },
    {
      "controller_api_name": "Building_Type__c",
      "dependent_api_name": "Building_Category__c",
      "mapping": {
        "School": "Educational and training facilities",
        "Hospital": "Health services"
      }
    }
  ]
}
```

**Response: 500 Internal Server Error** (if schema files cannot be parsed and DB has no cached version)

```json
{
  "detail": "SF schema not available: <error message>"
}
```

### Preserved Existing Endpoints (no changes)

| Endpoint | Status |
|----------|--------|
| `GET /api/acm/field-config` | Unchanged — BAR config |
| `PUT /api/acm/field-config` | Unchanged — BAR config |
| `POST /api/acm/field-config/reset` | Unchanged — BAR config |

---

## Frontend Changes

None. This story is backend-only. The new API endpoint is consumed by future V3 stories (E30-S2 onwards).

---

## Test Plan

### Unit Tests — `tests/test_config_loader.py`

#### TestSFFieldParsing (covers AC1, AC2)

```python
class TestSFFieldParsing:

    def test_building_fields_count(self):
        """AC1: Assert 143 building fields parsed."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        assert len(config.fields) == 143
        assert config.total_fields == 143

    def test_building_picklist_count(self):
        """AC1: Assert 18 picklist fields in building config."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        picklist_fields = [f for f in config.fields if f.field_type == "picklist"]
        assert len(picklist_fields) == 18

    def test_building_field_keyed_by_api_name(self):
        """AC1: API Name used as key, not Label."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        api_names = {f.api_name for f in config.fields}
        assert "Building_Type__c" in api_names
        assert "Building_Category__c" in api_names
        # Label should NOT be used as the key
        assert "Asset Type" not in api_names

    def test_item_fields_count(self):
        """AC2: Assert 154 item fields parsed."""
        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        assert len(config.fields) == 154
        assert config.total_fields == 154

    def test_item_picklist_count(self):
        """AC2: Assert 23 picklist fields in item config."""
        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        picklist_fields = [f for f in config.fields if f.field_type == "picklist"]
        assert len(picklist_fields) == 23

    def test_dependent_picklist_detected(self):
        """AC2: ACM_Classification__c marked as dependent."""
        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        acm_class = next(f for f in config.fields if f.api_name == "ACM_Classification__c")
        assert acm_class.is_dependent is True
        assert acm_class.controller_field == "Friability_of_Material__c"

    def test_restricted_picklist_detected(self):
        """AC1: Building_Type__c has is_restricted_picklist=True."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        bldg_type = next(f for f in config.fields if f.api_name == "Building_Type__c")
        assert bldg_type.is_restricted_picklist is True

    def test_boolean_column_parsing(self):
        """AC8: Nillable=False when cell is empty (non-required field)."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        # Building_Type__c has Nillable='' (empty = False/not nillable)
        bldg_type = next(f for f in config.fields if f.api_name == "Building_Type__c")
        assert bldg_type.nillable is False

    def test_formula_field_calc_true(self):
        """AC8: Calc=True for formula fields."""
        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        # Department__c: "Formula" in Notes column, Calc column = Y
        dept = next(f for f in config.fields if f.api_name == "Department__c")
        assert dept.calc is True
```

#### TestDependencyChains (covers AC3, AC4)

```python
class TestDependencyChains:

    def test_friability_chain_values(self):
        """AC3: Friability controller has exactly 2 values."""
        chain = _build_friability_chain()
        assert chain.controller_api_name == "Friability_of_Material__c"
        assert chain.dependent_api_name == "ACM_Classification__c"
        assert len(chain.mapping) == 2
        assert "Non-friable" in chain.mapping
        assert "Friable" in chain.mapping

    def test_non_friable_classifications(self):
        """AC3: Non-friable has 9 valid classifications."""
        chain = _build_friability_chain()
        non_friable = chain.mapping["Non-friable"]
        assert len(non_friable) == 9
        assert "Cement products" in non_friable
        assert "Insulation Products" in non_friable
        assert "Textiles" in non_friable

    def test_friable_classifications(self):
        """AC3: Friable has 9 valid classifications (with (f) suffix)."""
        chain = _build_friability_chain()
        friable = chain.mapping["Friable"]
        assert len(friable) == 9
        assert "Cement products (f)" in friable
        assert "Insulation products (f)" in friable

    def test_classification_to_subclassification_cement(self):
        """AC3: Cement products has correct product types."""
        chain = _build_acm_classification_chain()
        cement_types = chain.mapping["Cement products"]
        assert "Corrugated Roof Sheeting" in cement_types
        assert "Flat Sheeting" in cement_types
        assert "Weatherboards" in cement_types

    def test_classification_to_subclassification_insulation_friable(self):
        """AC3: Insulation products (f) includes AIB."""
        chain = _build_acm_classification_chain()
        insulation_f = chain.mapping["Insulation products (f)"]
        assert "AIB (Asbestos Insulated Board)" in insulation_f
        assert "Lagging" in insulation_f

    def test_building_type_chain_category_count(self):
        """AC4: Exactly 13 unique Building_Category__c values."""
        chain = _build_building_type_chain()
        assert chain.controller_api_name == "Building_Type__c"
        assert chain.dependent_api_name == "Building_Category__c"
        unique_categories = set(chain.mapping.values())
        assert len(unique_categories) == 13

    def test_building_type_school_category(self):
        """AC4: School building type maps to Educational and training facilities."""
        chain = _build_building_type_chain()
        assert chain.mapping["School"] == "Educational and training facilities"

    def test_building_type_hospital_category(self):
        """AC4: Hospital maps to Health services."""
        chain = _build_building_type_chain()
        assert chain.mapping["Hospital"] == "Health services"

    def test_building_type_total_values(self):
        """AC4: 114 building types have a category assignment."""
        chain = _build_building_type_chain()
        assert len(chain.mapping) == 114
```

#### TestSFSchemaLoader (covers AC6)

```python
class TestSFSchemaLoader:

    def test_load_returns_schema_bundle(self):
        """AC6: load_sf_field_schema returns SFSchemaBundle."""
        bundle = load_sf_field_schema()
        assert isinstance(bundle, SFSchemaBundle)
        assert bundle.version == "salesforce-v1"

    def test_load_is_cached(self):
        """AC6: Second call returns same object (in-memory cache)."""
        bundle1 = load_sf_field_schema()
        bundle2 = load_sf_field_schema()
        assert bundle1 is bundle2

    def test_bundle_has_three_dependency_chains(self):
        """AC3+AC4: Bundle contains all three dependency chains."""
        bundle = load_sf_field_schema()
        chain_controllers = {c.controller_api_name for c in bundle.dependencies}
        assert "Friability_of_Material__c" in chain_controllers
        assert "ACM_Classification__c" in chain_controllers
        assert "Building_Type__c" in chain_controllers
```

#### TestSFSchemaEdgeCases (covers AC8)

```python
class TestSFSchemaEdgeCases:

    def test_malformed_row_missing_column(self):
        """AC8: Malformed row (wrong number of columns) is skipped with warning."""
        malformed_md = (
            "# Test__c — Field Reference\n"
            "**Total fields:** 1  **Custom fields:** 1  **Picklist fields:** 0\n"
            "## Field Table\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------|------------|-------|\n"
            "| 1 | Missing_Columns__c | Too Short |\n"  # Only 3 cols, should be skipped
            "| 2 | Valid_Field__c | Valid Label | string | 255 | Y | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(malformed_md, "Test__c")
        # Malformed row is skipped; valid row is parsed
        assert len(config.fields) == 1
        assert config.fields[0].api_name == "Valid_Field__c"

    def test_empty_picklist_section(self):
        """AC8: Object with 0 picklist fields produces empty picklists dict."""
        no_picklist_md = (
            "# Test__c — Field Reference\n"
            "**Total fields:** 1  **Custom fields:** 1  **Picklist fields:** 0\n"
            "## Field Table\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------|------------|-------|\n"
            "| 1 | Name__c | Name | string | 255 | Y | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(no_picklist_md, "Test__c")
        assert config.picklists == {}
        assert config.picklist_fields == 0

    def test_missing_source_file_raises(self):
        """AC8: Missing source file raises SFSchemaLoadError (not FileNotFoundError)."""
        from open_notebook.extractors.parsers.config_loader import SFSchemaLoadError
        import pytest
        with pytest.raises(SFSchemaLoadError):
            _parse_sf_field_table_from_path("/nonexistent/path/missing.md", "Test__c")

    def test_empty_cell_length_is_none(self):
        """AC8: Empty Length cell parses to None."""
        row_md = (
            "# Test__c — Field Reference\n"
            "**Total fields:** 1  **Custom fields:** 0  **Picklist fields:** 0\n"
            "## Field Table\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------|------------|-------|\n"
            "| 1 | Boolean_Field__c | Boolean | boolean |  |  | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(row_md, "Test__c")
        assert config.fields[0].length is None
        assert config.fields[0].nillable is False  # Empty = False
```

#### TestItemNameLookup (covers AC9)

```python
class TestItemNameLookup:

    def test_item_names_for_cement_products(self):
        """AC9: Returns known cement product item names."""
        names = get_item_names_by_product_group("Cement products")
        assert "Corrugated Roof Sheeting" in names
        assert "Flat Sheeting" in names
        assert "Weatherboards" in names
        assert len(names) > 10

    def test_item_names_for_insulation_friable(self):
        """AC9: Returns item names for friable insulation group."""
        names = get_item_names_by_product_group("Insulation products (f)")
        assert "Lagging" in names
        assert "AIB (Asbestos Insulated Board)" in names

    def test_item_names_unknown_group_returns_empty(self):
        """AC9: Unknown product group returns empty list."""
        names = get_item_names_by_product_group("NonExistentGroup")
        assert names == []

    def test_item_names_total_coverage(self):
        """AC9: Sum of all item names across all groups == 294."""
        all_groups = [
            "Cement products", "Bitumen products", "Vinyl products",
            "Gasket, friction products and adhesives", "Coatings",
            "Reinforced plastics/resins (excluding bitumen products)", "Other",
            "Insulation Products", "Textiles",
            "Cement products (f)", "Vinyl products (f)",
            "Insulation products (f)", "Gasket, friction products and adhesives (f)",
            "Textiles (f)", "Other (f)", "Bitumen products (f)",
            "Coatings (f)", "Reinforced plastics/resins (excluding bitumen products) (f)",
        ]
        total = sum(len(get_item_names_by_product_group(g)) for g in all_groups)
        # 294 unique item names; some appear in multiple groups, so total may exceed 294
        # but verify the ITEM_NAME_TO_PRODUCT_GROUP dict has >= 294 unique names
        from open_notebook.extractors.parsers.config_loader import ITEM_NAME_TO_PRODUCT_GROUP
        assert len(ITEM_NAME_TO_PRODUCT_GROUP) >= 294

    def test_get_item_names_sorted(self):
        """AC9: Result is sorted alphabetically."""
        names = get_item_names_by_product_group("Cement products")
        assert names == sorted(names)
```

### Integration Tests

#### TestSFSchemaAPIEndpoint (covers AC7)

Located in `tests/test_config_loader.py` (integration section, requires DB) or a dedicated `tests/test_sf_schema_api.py`:

```python
@pytest.mark.asyncio
class TestSFSchemaAPIEndpoint:

    async def test_get_field_schema_returns_200(self, async_client):
        """AC7: GET /api/acm/field-schema returns HTTP 200."""
        response = await async_client.get("/api/acm/field-schema")
        assert response.status_code == 200

    async def test_get_field_schema_response_structure(self, async_client):
        """AC7: Response validates against SFFieldSchemaConfigResponse."""
        response = await async_client.get("/api/acm/field-schema")
        data = response.json()
        assert data["version"] == "salesforce-v1"
        assert "building_fields" in data
        assert "item_fields" in data
        assert "picklists" in data
        assert "dependencies" in data

    async def test_get_field_schema_building_field_count(self, async_client):
        """AC7: Building object reports 143 fields."""
        response = await async_client.get("/api/acm/field-schema")
        data = response.json()
        assert data["building_fields"]["total_fields"] == 143

    async def test_get_field_schema_item_field_count(self, async_client):
        """AC7: Item object reports 154 fields."""
        response = await async_client.get("/api/acm/field-schema")
        data = response.json()
        assert data["item_fields"]["total_fields"] == 154

    async def test_bar_field_config_unaffected(self, async_client):
        """Regression: GET /api/acm/field-config still returns BAR config."""
        response = await async_client.get("/api/acm/field-config")
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        assert "enums" in data
        assert "business_rules" in data
        # BAR config does NOT have 'building_fields' or 'item_fields' keys
        assert "building_fields" not in data
        assert "item_fields" not in data
```

### Test Coverage Matrix

| AC  | Test Class | Test Method(s) |
|-----|-----------|----------------|
| AC1 | TestSFFieldParsing | `test_building_fields_count`, `test_building_picklist_count`, `test_building_field_keyed_by_api_name`, `test_restricted_picklist_detected` |
| AC2 | TestSFFieldParsing | `test_item_fields_count`, `test_item_picklist_count`, `test_dependent_picklist_detected`, `test_boolean_column_parsing`, `test_formula_field_calc_true` |
| AC3 | TestDependencyChains | `test_friability_chain_values`, `test_non_friable_classifications`, `test_friable_classifications`, `test_classification_to_subclassification_cement`, `test_classification_to_subclassification_insulation_friable` |
| AC4 | TestDependencyChains | `test_building_type_chain_category_count`, `test_building_type_school_category`, `test_building_type_hospital_category`, `test_building_type_total_values` |
| AC5 | Migration review | Schema diff confirms `DEFINE FIELD IF NOT EXISTS`, no removal of existing fields |
| AC6 | TestSFSchemaLoader | `test_load_returns_schema_bundle`, `test_load_is_cached`, `test_bundle_has_three_dependency_chains` |
| AC7 | TestSFSchemaAPIEndpoint | All 5 async endpoint tests |
| AC8 | TestSFSchemaEdgeCases | `test_malformed_row_missing_column`, `test_empty_picklist_section`, `test_missing_source_file_raises`, `test_empty_cell_length_is_none` |
| AC9 | TestItemNameLookup | All 5 item name tests |

---

## Implementation Notes for Dev Agent

### Critical Ordering Rules

1. Implement and test `_parse_sf_field_table()` first — all other parser functions depend on it.
2. Hardcode the dependency chain data (from `picklist-dependency-mappings.md`) as Python dicts rather than parsing the markdown at runtime. This avoids parsing complexity and ensures stability.
3. The `ITEM_NAME_TO_PRODUCT_GROUP` dict must be hand-authored from the picklist-dependency-mappings.md data. It maps each of the 294+ item names to their primary `ACM_Classification__c` group. Note: some item names appear in multiple groups (e.g., "Debris", "Dust") — for those, assign the most specific or first-listed group.

### Markdown Parsing Pitfalls

The field table markdown has these edge cases to handle:

```
# Optional spaces around pipe: "| Y | Y |" vs "| Y |Y|"
# Empty cell vs whitespace: "|  |" vs "| |"
# Multi-word Notes with semicolons: "Restricted picklist; Dependent on Foo__c; Select from..."
# Length column empty for boolean/location/reference types
# Calc column 'Y' for formula fields — present in both Building and Item tables
```

### SFSchemaLoadError

Define this as a custom exception in `config_loader.py`:

```python
class SFSchemaLoadError(Exception):
    """Raised when SF schema source files cannot be parsed."""
    pass
```

### Startup Loader — Non-Fatal Contract

The `run_sf_schema_provisioning()` function follows the same non-fatal contract as `run_model_provisioning()`:
- Catches all exceptions
- Logs warning but does not re-raise
- API starts successfully even if SF schema provisioning fails
- The `GET /api/acm/field-schema` endpoint falls back to in-memory load if DB record is absent

### Version Gate for Idempotency

The startup loader checks `version == "salesforce-v1"` before writing. This means:
- First boot: record absent → write
- Subsequent boots: record present with correct version → skip
- Schema data update: bump `SF_SCHEMA_VERSION` constant in `sf_schema_provisioning.py` → next boot rewrites

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Naming collision: Label vs API Name as dict key | HIGH — wrong field addressed in V3 extraction | Always key on `API Name` column; unit test explicitly asserts API Name used not Label |
| `field_schema:default` conflict | HIGH — BAR config overwritten | Use separate `field_schema:sf_v1` record ID; migration uses `IF NOT EXISTS` only |
| Markdown column count variation | MEDIUM — parse errors silently drop rows | Validate column count == 10 per row; skip and warn on mismatch; unit test covers this |
| `Item_Name__c` treated as dependent picklist | MEDIUM — wrong dependency chain built | Explicitly documented as independent; `get_item_names_by_product_group()` uses flat mapping not dependency chain |
| Existing BAR tests broken | HIGH — regression in E1 functionality | `tests/test_field_config.py` and `tests/test_field_config_api.py` listed as DO NOT MODIFY; run both suites before marking complete |
| Large `ITEM_NAME_TO_PRODUCT_GROUP` dict | LOW — maintenance burden | Hardcode once from `picklist-dependency-mappings.md`; single source of truth; 294+ entries |

---

## Dev Agent Record

### Build Verification Checklist

- [ ] `uv run ruff check . --fix` passes with no errors
- [ ] `uv run pytest tests/test_config_loader.py -v` — all new tests pass
- [ ] `uv run pytest tests/test_field_config.py tests/test_field_config_api.py -v` — all 9+ existing BAR tests still pass
- [ ] `cd frontend && npm run build` — no frontend build errors (frontend not modified, but verify no import side effects)
- [ ] `GET /api/acm/field-schema` returns 200 with correct counts
- [ ] `GET /api/acm/field-config` still returns BAR config unchanged

### Files Verified

- [ ] `open_notebook/extractors/parsers/field_config.py` — new models added, existing models unchanged
- [ ] `open_notebook/extractors/parsers/config_loader.py` — new functions added, `load_field_schema()` unchanged
- [ ] `api/sf_schema_provisioning.py` — created
- [ ] `api/models.py` — new response models added
- [ ] `api/routers/acm.py` — new endpoint added
- [ ] `api/main.py` — `run_sf_schema_provisioning()` called in lifespan
- [ ] `migrations/38.surrealql` — created with `IF NOT EXISTS` guards
- [ ] `migrations/38_down.surrealql` — created (no-op)
- [ ] `tests/test_config_loader.py` — created with all test classes

### Implementation Status

| Task | Status | Notes |
|------|--------|-------|
| Pydantic models (`field_config.py`) | Pending | |
| Config loader functions (`config_loader.py`) | Pending | |
| `ITEM_NAME_TO_PRODUCT_GROUP` dict | Pending | Source: picklist-dependency-mappings.md |
| Startup provisioner (`sf_schema_provisioning.py`) | Pending | |
| API response models (`models.py`) | Pending | |
| API endpoint (`acm.py`) | Pending | |
| `api/main.py` lifespan hook | Pending | |
| Migration 38 | Pending | |
| Unit tests | Pending | |
| Integration tests | Pending | |

---

*Tech spec authored by Ralph Scrum Master — 2026-03-03*
