# Story 1.11: Generic Configurable Parser with BAR Field Schema

Status: done

> **REDEFINED 2026-02-08:** Replaces old "Extensible Consultant Parser Framework".
> The old implementation (3 hardcoded parsers + registry) is committed but must be replaced.
> Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md` (CP-1)

## Story

As a system,
I want a single generic configurable parser driven by field schema configuration,
so that any ACM PDF format can be parsed using configurable field definitions from the BAR template.

## Acceptance Criteria

1. Load field schema from `register_row.schema.json` (47 fields with types, required/optional, column letters)
2. Load enum picklists from `register_enums.json` (controlled values per field)
3. Load business rules from config (e.g., Negative → N/A for Condition)
4. Single GenericParser class replaces PrensaParser, GreencapParser, GenericParser
5. Parser accepts field config at initialization (which fields to extract, column mappings)
6. Field config drives: extraction field list, enum validation, display names
7. Default config seeded from BAR Excel template (Clucth_Alexandra_District_BAR.xlsm)
8. API endpoint to read/update field configuration: GET/PUT /api/acm/field-config
9. UI can override field config (see E12-S4)
10. Remove PrensaParser and GreencapParser classes (consolidate into generic)

## Tasks / Subtasks

- [x] Task 1: Define Pydantic config models (AC: 1, 2, 3, 5)
  - [x] 1.1 Create `FieldDef` model in `parsers/field_config.py`
  - [x] 1.2 Create `BusinessRule` model
  - [x] 1.3 Create `FieldSchemaConfig` model wrapping fields, enums, rules
  - [x] 1.4 Add display_name → internal_name mapping helper
  - [x] 1.5 Add BAR column letter → internal_name mapping helper

- [x] Task 2: Create config loader (AC: 1, 2, 3, 7)
  - [x] 2.1 Create `parsers/config_loader.py` with `load_field_schema()` function
  - [x] 2.2 Load from JSON files: `register_row.schema.json` + `register_enums.json`
  - [x] 2.3 Transform JSON schema `x_excel.field_specs` into `FieldDef` list
  - [x] 2.4 Map each field's `enum` property to `register_enums.json` keys
  - [x] 2.5 Build `internal_name` mapping (snake_case from display name)
  - [x] 2.6 Cache loaded config as module-level singleton (same pattern as E1-S12 `_WORDING_RULES`)
  - [x] 2.7 Graceful fallback if JSON files missing (log warning, use hardcoded defaults)

- [x] Task 3: Rewrite GenericParser (AC: 4, 5, 6)
  - [x] 3.1 Rewrite `parsers/generic.py`: `GenericParser.__init__(config: FieldSchemaConfig)`
  - [x] 3.2 Implement `get_column_mapping()` from config fields (display_name → internal_name)
  - [x] 3.3 Implement `get_register_headers()` from config active fields
  - [x] 3.4 Implement `extract_items()` using config-driven column extraction
  - [x] 3.5 Implement `detect()` that always returns True (universal fallback)
  - [x] 3.6 Keep `extract_metadata()` logic from existing GenericParser (unchanged)

- [x] Task 4: Simplify parser module (AC: 4, 10)
  - [x] 4.1 Delete `parsers/prensa.py`
  - [x] 4.2 Delete `parsers/greencap.py`
  - [x] 4.3 Rewrite `parsers/__init__.py`: remove registry, export `GenericParser` + `load_field_schema()`
  - [x] 4.4 Keep `parsers/base.py` unchanged (RawACMItem, DocumentMeta, SourceLocation)
  - [x] 4.5 Add `get_parser()` function that instantiates GenericParser with loaded config

- [x] Task 5: Update extraction pipeline integration (AC: 4, 6)
  - [x] 5.1 Update `acm_extractor.py`: remove parser auto-detection logic
  - [x] 5.2 Load field config once at extraction start, pass to GenericParser
  - [x] 5.3 Keep `_create_header_map_from_parser()` working with new GenericParser
  - [x] 5.4 Verify normalizer integration unchanged (enums.py, recommendations.py, taxonomy.py)

- [x] Task 6: Add field-config API endpoints (AC: 8, 9)
  - [x] 6.1 Add Pydantic request/response models to `api/models.py`
  - [x] 6.2 Add `GET /api/acm/field-config` endpoint in `api/routers/acm.py`
  - [x] 6.3 Add `PUT /api/acm/field-config` endpoint in `api/routers/acm.py`
  - [x] 6.4 Add `POST /api/acm/field-config/reset` endpoint (restore defaults)

- [x] Task 7: Create database migration (AC: 8)
  - [x] 7.1 Create `migrations/17.surrealql` with `field_schema` table
  - [x] 7.2 Create `migrations/17_down.surrealql`
  - [x] 7.3 Seed default config from JSON files during migration or API startup

- [x] Task 8: Write tests (AC: all)
  - [x] 8.1 Test config loading from JSON files
  - [x] 8.2 Test FieldSchemaConfig validation
  - [x] 8.3 Test GenericParser with standard table data
  - [x] 8.4 Test GenericParser skips non-ACM tables
  - [x] 8.5 Test column mapping generation from config
  - [x] 8.6 Test API endpoints (GET/PUT /api/acm/field-config)
  - [x] 8.7 Regression: existing extraction still produces correct ACMRecord output
  - [x] 8.8 Test graceful fallback when config files missing

## Dev Notes

### Critical Context: This Is a REPLACEMENT, Not a New Feature

The old E1-S11 implemented 3 hardcoded parsers (PrensaParser, GreencapParser, GenericParser) with a registry pattern. That code exists in `open_notebook/extractors/parsers/`. **This story deletes prensa.py and greencap.py, rewrites generic.py, and removes the registry.** The old test file `tests/test_consultant_parsers.py` will need to be rewritten.

### Config Source of Truth Flow

```
BAR Excel Template → JSON Config Files → SurrealDB field_schema table
    ↓                     ↓                        ↓
  (manual import)   (default source)          (runtime source)
                                                   ↓
                    GenericParser ← loads config at extraction time
                         ↓
                  AG Grid columns ← reads config for column definitions (E2-S8)
                         ↓
                  Excel/CSV export ← reads config for column order/names (E5-S4)
```

### Existing JSON Config Files (Ready to Use)

| File | Content | Path |
|------|---------|------|
| `register_row.schema.json` | 47 field definitions with types, column letters, required flags | `docs/samplePDF/instructions-sample/` |
| `register_enums.json` | All enum picklists (YesNo, SampleResult, Condition, etc.) | `docs/samplePDF/instructions-sample/` |
| `register_taxonomy.*.json` | Product classification (T1-T8 groups) | `docs/samplePDF/instructions-sample/` |
| `consultant_wording_rules.json` | Recommendation normalization patterns | `docs/samplePDF/instructions-sample/` |

The `register_row.schema.json` has an `x_excel.field_specs` array with 47 entries, each containing: `col_index`, `col_letter`, `name`, `required`, `optional`, `recommended`. The top-level `properties` section has types and inline `enum` arrays for controlled fields. The `required` array lists mandatory field names.

### Pydantic Config Models (Architecture Section 5.2)

```python
# parsers/field_config.py
from pydantic import BaseModel
from typing import Optional

class FieldDef(BaseModel):
    internal_name: str          # snake_case, e.g. "building_name"
    display_name: str           # BAR column header, e.g. "Building Name"
    excel_column: str           # e.g. "E"
    col_index: int              # 1-based position in BAR spreadsheet
    field_type: str             # "string" | "number" | "date" | "enum"
    required: bool
    active: bool = True         # Can be toggled off without schema change
    enum_name: Optional[str] = None  # Key into enums dict, e.g. "SampleResult"
    group: Optional[str] = None      # UI grouping, e.g. "building", "acm_details"

class BusinessRule(BaseModel):
    rule_id: str                # e.g. "negative_clears_condition"
    description: str
    enabled: bool = True

class FieldSchemaConfig(BaseModel):
    fields: list[FieldDef]
    enums: dict[str, list[str]]
    business_rules: list[BusinessRule]
    version: str
    source_template: Optional[str] = None
```

### display_name to internal_name Mapping

The JSON schema uses BAR display names (e.g. "Building Name"). The domain model uses snake_case internal names (e.g. `building_name`). The config loader must map between them. **Use a hardcoded lookup table** (not automatic conversion) because the mappings are not always predictable:

| BAR Display Name | ACMRecord Internal Name |
|------------------|------------------------|
| Department | department |
| Agency | agency |
| Sub Agency | sub_agency |
| Site Name (if applicable) | site_name |
| Building Name | building_name |
| Building Type | building_type |
| Building Address | building_address |
| Suburb | suburb |
| Postcode | postcode |
| Owned or Leased | owned_or_leased |
| Building Unique ID | building_unique_id |
| Frequency of use | frequency_of_use |
| Public Access? | public_access |
| Date of Inspection | date_of_inspection |
| Estimated Year Built | building_year |
| Est. Building Size (m2) | building_size_m2 |
| Number of Levels | number_of_levels |
| Construction Type | building_construction |
| Roof Type | roof_type |
| Internal / External | area_type |
| Level | level |
| Room or Area | room_name |
| Location in Room | location |
| Specific Item/ACM Name | product |
| Friability of material | friable |
| FIRABILITY NAME EXCEL | friability_display |
| ACM Product Group | acm_product_group |
| ACM GROUP NAME EXCEL | acm_group_display |
| ACM Product Type | acm_product_type |
| NATA Endorsed Sample number (if available) | sample_no |
| Sample Result | sample_result |
| Identifying Hygiene or Consulting Company | identifying_company |
| Condition | material_condition |
| Disturbance Potential | disturbance_potential |
| Quantity | quantity |
| Labelled | acm_labelled |
| Label Details | acm_label_details |
| Hygienist Recommendations | hygienist_recommendations |
| Additional Comments | additional_comments |
| PSB Supplied ACM ID | psb_supplied_acm_id |
| Assumed Removed? | assumed_removed |
| Date of Removal | date_of_removal |
| Quantity Removed | quantity_removed |
| Asbestos Removal Notification No | removal_notification_no |
| EPA Waste Transport Certificate No | epa_certificate_no |
| Removal Comments | removal_comments |
| Photo Reference Number | photo_reference |

### Business Rules (from BAR Instructions)

| Rule ID | Description | Implementation |
|---------|-------------|----------------|
| `negative_clears_condition` | When Sample Result is "Negative", set Condition to "N/A (negative)" | In `acm_extractor.py` Stage 2 interpretation |
| `assumed_negative_clears_condition` | When Sample Result is "Assumed Negative", set Condition to "N/A (assumed negative)" | Same |
| `negative_clears_disturbance` | When Sample Result is "Negative", set Disturbance Potential to "N/A (negative)" | Same |
| `assumed_negative_clears_disturbance` | When Sample Result is "Assumed Negative", set Disturbance Potential to "N/A (assumed negative)" | Same |

### File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/parsers/prensa.py` | **DELETE** | Absorbed into generic parser + config |
| `open_notebook/extractors/parsers/greencap.py` | **DELETE** | Absorbed into generic parser + config |
| `open_notebook/extractors/parsers/generic.py` | **REWRITE** | GenericParser driven by FieldSchemaConfig |
| `open_notebook/extractors/parsers/field_config.py` | **NEW** | FieldDef, BusinessRule, FieldSchemaConfig models |
| `open_notebook/extractors/parsers/config_loader.py` | **NEW** | Load config from JSON/SurrealDB |
| `open_notebook/extractors/parsers/__init__.py` | **SIMPLIFY** | Remove registry, export GenericParser + loader |
| `open_notebook/extractors/parsers/base.py` | **KEEP** | RawACMItem, DocumentMeta, SourceLocation unchanged |
| `open_notebook/extractors/acm_extractor.py` | **MODIFY** | Remove parser auto-detection, load field config |
| `api/routers/acm.py` | **ADD** | GET/PUT /api/acm/field-config endpoints |
| `api/models.py` | **ADD** | FieldSchemaConfigResponse, FieldDefResponse models |
| `migrations/17.surrealql` | **NEW** | field_schema table for runtime config |
| `migrations/17_down.surrealql` | **NEW** | Rollback migration |
| `tests/test_field_config.py` | **NEW** | Config loading + validation tests |
| `tests/test_generic_parser.py` | **NEW** | GenericParser with config tests |
| `tests/test_consultant_parsers.py` | **DELETE or REWRITE** | Old 3-parser tests replaced |

### Project Structure Notes

- Parser files live at `open_notebook/extractors/parsers/` (NOT `open_notebook/extraction/`)
- Normalizers live at `open_notebook/extractors/normalizers/`
- API models at `api/models.py`, routers at `api/routers/acm.py`
- Tests at `tests/test_*.py` (flat structure, no subdirectories)
- Migrations at `migrations/N.surrealql` (next available: 17)

### Existing Patterns to Follow

**Config caching (from E1-S12 normalizers):**
```python
_FIELD_SCHEMA: Optional[FieldSchemaConfig] = None

def load_field_schema() -> FieldSchemaConfig:
    global _FIELD_SCHEMA
    if _FIELD_SCHEMA is not None:
        return _FIELD_SCHEMA
    # Load from JSON, cache, return
```

**ReDoS protection (from E1-S12 code review):**
Any user-supplied regex patterns in business rules must be wrapped in `try/except re.error`.

**Test patterns (from E1-S12):**
- Class grouping by acceptance criterion: `TestConfigLoading`, `TestGenericParserExtraction`
- Import within test methods (not module level)
- Descriptive names: `test_load_config_has_47_fields`
- Strong assertions: exact counts, deep field value checks

**Migration pattern (from migrations 15-16):**
```sql
-- Migration 17: Add field_schema table for configurable parser (E1-S11)
DEFINE TABLE IF NOT EXISTS field_schema SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS version ON field_schema TYPE string;
-- ... etc
```

**API model pattern (from existing acm.py):**
- Suffix with `Response` for GET returns, `Request` for POST/PUT bodies
- Use `Field(..., description="...")` for documentation
- Use `ConfigDict(protected_namespaces=())` if needed

### Integration with Other Stories

| Story | Integration Point | Notes |
|-------|------------------|-------|
| E1-S3 (Pipeline) | Stage 1 uses GenericParser with field config | Already done, just swap parser source |
| E1-S12 (Normalization) | Normalizers called after parser output, unchanged | No changes needed |
| E1-S14 (Embeddings) | Uses field schema to determine embeddable fields | Future, API already provides config |
| E2-S8 (AG Grid) | Frontend reads `/api/acm/field-config` for columnDefs | Depends on this story's API |
| E5-S4 (Export) | Export reads field config for column order/names | Depends on this story's API |
| E12-S4 (Settings UI) | Settings UI calls field-config API | Depends on this story |

### What NOT to Do

- **DO NOT** create a `config/field_schemas/` directory - config is loaded from existing `docs/samplePDF/instructions-sample/` JSON files
- **DO NOT** modify the `ACMRecord` domain model - field config controls which fields are active, not the model shape
- **DO NOT** modify the `acm_record` database table - no migration needed for the record table
- **DO NOT** add parser auto-detection - there is ONE parser now
- **DO NOT** create consultant-specific anything - the whole point is one generic parser
- **DO NOT** duplicate normalizer logic - normalizers (enums.py, recommendations.py, taxonomy.py) remain separate, called by the extraction pipeline after parsing

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md] - Full course correction details
- [Source: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#E1-S11] - Updated story definition
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.2] - Rewritten parser architecture
- [Source: _bmad-output/project-planning-artifacts/acm-ai/03-prd.md#FR-107] - Updated functional requirement
- [Source: docs/samplePDF/instructions-sample/register_row.schema.json] - 47 BAR field definitions
- [Source: docs/samplePDF/instructions-sample/register_enums.json] - Enum picklist values
- [Source: docs/reference/bar-schema.md] - BAR schema reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Pre-existing test failures confirmed: 2 in `test_acm_ai_extraction.py` (ConfidenceDistribution issue), 3 in `test_acm_extractor_integration.py` (sample PDF accuracy). Verified by running tests against pre-change code via `git stash`.

### Completion Notes List

- All 8 tasks completed via TDD red-green-refactor cycle
- Replaced 3 hardcoded parsers (PrensaParser, GreencapParser, GenericParser with registry) with single config-driven GenericParser
- Backward compatibility maintained: `_COMPAT_COLUMN_MAP` preserves short header names for existing markdown tables
- `get_parser()` API unchanged (accepts optional pdf_text for compat, but no longer uses it for selection)
- 47 BAR field definitions loaded from existing `register_row.schema.json`
- Code review fixes (2026-02-10): Corrected sprint status key/status, added migration 19 for structured field_schema fields, enhanced API validation (47-field requirement, unique columns, enum references), added 5 integration tests
- 497 tests pass (72 E1-S11 tests), 5 pre-existing failures (not introduced by this story)
- Lint clean (ruff check passes)

### Build Verification

- `uv run pytest tests/` — 497 passed, 5 pre-existing failures (72 E1-S11 tests total: 19 config, 13 parser, 24 consultant, 11 API, 5 integration)
- `uv tool run ruff check` — All checks passed
- Code Review (2026-02-10) — 4 HIGH + 2 MEDIUM issues fixed, all tests pass

### File List

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/parsers/field_config.py` | NEW | FieldDef, BusinessRule, FieldSchemaConfig Pydantic models |
| `open_notebook/extractors/parsers/config_loader.py` | NEW | JSON config loader with 47-field mapping and singleton caching |
| `open_notebook/extractors/parsers/generic.py` | REWRITE | Config-driven GenericParser replacing old hardcoded version |
| `open_notebook/extractors/parsers/__init__.py` | SIMPLIFY | Removed registry, exports GenericParser + get_parser() + load_field_schema() |
| `open_notebook/extractors/parsers/prensa.py` | DELETE | Absorbed into generic config-driven parser |
| `open_notebook/extractors/parsers/greencap.py` | DELETE | Absorbed into generic config-driven parser |
| `open_notebook/extractors/parsers/base.py` | MODIFY | Updated docstring from old 3-parser instructions to single-parser architecture |
| `open_notebook/extractors/acm_extractor.py` | MODIFY | Removed parser auto-detection, dead code guards, unused _create_header_map_from_parser |
| `api/models.py` | ADD | FieldDefResponse, BusinessRuleResponse, FieldSchemaConfigResponse, FieldSchemaConfigUpdateRequest (enhanced validation in code review M1) |
| `api/routers/acm.py` | ADD | GET/PUT /api/acm/field-config, POST /api/acm/field-config/reset (updated _save_db_field_config in code review H4) |
| `migrations/17.surrealql` | NEW | field_schema table for runtime config |
| `migrations/17_down.surrealql` | NEW | Rollback migration |
| `migrations/19.surrealql` | NEW | Add structured fields to field_schema (code review fix H4) |
| `migrations/19_down.surrealql` | NEW | Rollback migration 19 |
| `tests/test_field_config.py` | NEW | 19 tests for config models and loader |
| `tests/test_generic_parser.py` | NEW | 13 tests for GenericParser behavior |
| `tests/test_consultant_parsers.py` | REWRITE | 24 tests updated for single-parser architecture |
| `tests/test_field_config_api.py` | NEW | 11 tests for field-config API endpoints |
| `tests/test_acm_extractor_integration.py` | ADD | 5 integration tests for E1-S11 field config pipeline (code review fix M2) |

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-09 | Tasks 1-8 implemented | Full story implementation via TDD |
| 2026-02-09 | Code review fixes (7 issues) | H1: Updated base.py stale docstring. H2: Removed dead code paths (parser.name != "generic" guards, unused _create_header_map_from_parser). H3: Wired PUT/reset endpoints to SurrealDB field_schema table for persistence. M1/M2: Made GenericParser config-driven extraction with BAR display name detection. M3: Improved enum matching with subset fallback. M4: Added validation to FieldSchemaConfigUpdateRequest. L1: Removed unused imports in test_field_config_api.py. |
| 2026-02-10 | Adversarial code review fixes (6 issues) | **H2**: Updated sprint-status.yaml status from review→done. **H3**: Fixed story key mismatch (old: e1-s11-extensible-consultant-parser-framework, new: e1-s11-generic-configurable-parser). **H4**: Created migration 19 with structured fields (active_field_names, field_count, source_template) for efficient querying. Updated _save_db_field_config() to populate structured fields. **M1**: Enhanced API validation - added checks for: exactly 47 fields (BAR requirement), unique excel_column values, valid enum references. **M2**: Added 5 integration tests in TestE1S11FieldConfigIntegration class validating full extraction pipeline with field config. All tests pass (72 total for E1-S11). |
