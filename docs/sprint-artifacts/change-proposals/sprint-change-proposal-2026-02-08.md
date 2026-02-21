# Sprint Change Proposal - Generic Configurable Parser

> **Date:** 2026-02-08
> **Author:** San (facilitated by Correct Course workflow)
> **Status:** ✅ APPROVED (2026-02-10)
> **Approved by:** Demi
> **Change Scope:** Moderate
> **Branch:** Epic8
> **Reference Commits:** 3c3c63e, d7097f2 (ACM schema & extraction pipeline)

---

## 1. Issue Summary

### Problem Statement
The current ACM extraction architecture uses **3 specialized consultant parsers** (Prensa, Greencap, Generic) with hardcoded field definitions, column mappings, and detection patterns. Field definitions are duplicated across the parser layer, domain model, AG Grid columns, and export logic with no single source of truth.

### Discovery Context
During implementation of the extraction pipeline on the Epic8 branch, the user identified that maintaining 3 separate parsers with hardcoded fields is over-engineered. The Victorian BAR Excel template (`Clucth_Alexandra_District_BAR.xlsm`) already contains complete field definitions, enum picklists, and business rules across multiple sheets. This template should be the single source of truth driving the entire stack.

### Evidence
- BAR Excel template has 47 field definitions with types, required/optional flags, and column letters
- `register_row.schema.json` already captures the BAR field schema in JSON format
- `register_enums.json` already captures all picklist values
- 3 parsers (PrensaParser, GreencapParser, GenericParser) share the same BAR output schema with different input column mappings
- Field definitions are duplicated across: parsers, ACMRecord Pydantic model, AG Grid TypeScript column definitions, Excel export column ordering

---

## 2. Impact Analysis

### Epic Impact

| Epic | Severity | Description |
|------|----------|-------------|
| **E1** (Extraction Pipeline) | **High** | E1-S11 redefined from "extensible parser framework" to "generic configurable parser". E1-S3, E1-S12 modified. |
| **E12** (Settings/Config UI) | **High** | E12-S4 redefined from "parser management" to "BAR field schema configuration UI" |
| **E5** (Export) | **Moderate** | Export columns driven by field config instead of hardcoded mapping |
| **E2** (AG Grid) | **Moderate** | Column definitions generated from field config (E2-S8 enhancement) |
| **E13** (Knowledge Graph) | **Low** | Graph structure unchanged |
| **E14** (UX) | **None** | UI patterns unaffected |

### Story Impact

| Story | Change | Description |
|-------|--------|-------------|
| **E1-S11** | **Redefine** | "Extensible Consultant Parser Framework" → "Generic Configurable Parser with BAR Field Schema" |
| **E12-S4** | **Redefine** | "Parser Configuration Management" → "BAR Field Schema Configuration UI" |
| **E2-S8** | **Enhance** | Add: AG Grid columns generated from field config |
| **E1-S3** | **Minor** | Update: Stage 1 uses generic parser with field config |
| **E1-S12** | **Minor** | Update: Normalization rules part of field config |
| **E5-S4** | **Minor** | Field mapping config already aligns with this change |

### Artifact Conflicts

| Artifact | Conflict | Resolution |
|----------|----------|------------|
| **Architecture 5.2** | ConsultantParser ABC + registry pattern | Rewrite: Single GenericParser with FieldSchemaConfig |
| **Architecture 5.3** | Hardcoded consultant patterns | Replace: Unified field configuration schema |
| **PRD 5.4** | References consultant parsers | Update: Describe generic configurable parser |
| **PRD 5.7** | Lists Prensa/Greencap/Generic parsers | Replace: Configurable Field Schema section |
| **PRD FR-107** | "Support multiple PDF provider formats" | Reframe: "Configurable field definitions for any format" |
| **bar-schema.md** | Static reference doc | Update: Reference config-driven approach |
| **Parser tests** | Test 3 separate parsers | Rewrite: Test generic parser with config |

### Technical Impact

| Area | Impact |
|------|--------|
| **Backend parsers** | Delete `prensa.py`, `greencap.py`. Rewrite `generic.py`. Add `field_config.py`, `config_loader.py` |
| **Backend extractor** | Remove parser auto-detection in `acm_extractor.py`. Load field config instead |
| **Backend API** | Add `GET/PUT /api/acm/field-config` endpoint |
| **Frontend AG Grid** | Generate columnDefs from field config API response |
| **Frontend export** | Export columns driven by field config |
| **Database** | Add `field_schema` table for runtime config storage (no change to `acm_record` schema) |
| **Domain model** | ACMRecord Pydantic model UNCHANGED (fixed ~50 fields, config drives which are active) |

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment (Option 1)

**Rationale:**
1. **Simplification, not expansion:** Replacing 3 parsers with 1 configurable parser reduces code complexity
2. **Config already exists:** `register_row.schema.json` and `register_enums.json` already define the BAR schema
3. **Minimal blast radius:** Keeping fixed Pydantic fields means domain model, DB schema, and most API code unchanged
4. **User control:** Config-driven approach gives users control without code changes
5. **Low risk:** Each layer (parser, grid, export) can be updated independently

**Effort Estimate:** Medium
- Parser refactoring: ~2-3 days
- Config loading + API: ~1-2 days
- AG Grid config integration: ~1 day
- Export config integration: ~1 day
- Testing: ~1-2 days

**Risk Assessment:** Low
- Fixed domain model means no DB migration needed
- Existing JSON configs provide ready-made defaults
- Each component can be updated independently (no big-bang)

**Timeline Impact:** Minimal - simplification may actually accelerate remaining extraction work

---

## 4. Detailed Change Proposals

### 4.1 Story Changes

#### CP-1: E1-S11 Redefinition

**Story:** E1-S11 Extensible Consultant Parser Framework

**OLD Title:** Extensible Consultant Parser Framework
**NEW Title:** Generic Configurable Parser with BAR Field Schema

**OLD Acceptance Criteria:**
- Define ConsultantParser ABC with detect(), extract_metadata(), extract_items(), get_column_mapping()
- Implement PrensaParser, GreencapParser, GenericParser
- Parser registry for automatic selection
- Document adding new parsers

**NEW Acceptance Criteria:**
- [ ] Load field schema from `register_row.schema.json` (47 fields with types, required/optional, column letters)
- [ ] Load enum picklists from `register_enums.json` (controlled values per field)
- [ ] Load business rules from config (e.g., Negative → N/A for Condition)
- [ ] Single GenericParser class replaces PrensaParser, GreencapParser, GenericParser
- [ ] Parser accepts field config at initialization (which fields to extract, column mappings)
- [ ] Field config drives: extraction field list, enum validation, display names
- [ ] Default config seeded from BAR Excel template (Clucth_Alexandra_District_BAR.xlsm)
- [ ] API endpoint to read/update field configuration: GET/PUT /api/acm/field-config
- [ ] UI can override field config (see E12-S4)
- [ ] Remove PrensaParser and GreencapParser classes (consolidate into generic)

**Rationale:** 3 separate parsers with hardcoded fields is over-engineered. A single parser with configurable fields from the BAR template is simpler, more maintainable, and gives users control.

---

#### CP-2: E12-S4 Redefinition

**Story:** E12-S4 Parser Configuration Management

**OLD Title:** Parser Configuration Management
**NEW Title:** BAR Field Schema Configuration UI

**OLD Acceptance Criteria:**
- List all registered parsers with status (active/inactive)
- Per-parser details: name, detection patterns, column mapping
- Enable/disable individual parsers
- Parser priority ordering (drag-and-drop)
- Column mapping editor
- Export/import parser configuration as JSON

**NEW Acceptance Criteria:**
- [ ] Field Schema Editor: View/toggle/reorder 47 BAR fields, edit display names
- [ ] Picklist Value Editor: View/edit enum values per field, import from BAR template
- [ ] Business Rules Editor: View/enable/disable rules, add custom rules
- [ ] Config Import/Export: Import from BAR Excel, export as JSON, reset to defaults
- [ ] Config applies to: extraction, AG Grid columns, Excel/CSV export
- [ ] API endpoints: GET/PUT /api/settings/field-schema

**Rationale:** Replaces "manage multiple parsers" with "configure one field schema."

---

#### CP-3: E2-S8 Enhancement

**Story:** E2-S8 Column Visibility Management

**Addition to Acceptance Criteria:**
- [ ] AG Grid column definitions generated from field schema config (not hardcoded TypeScript arrays)
- [ ] Column groups derived from field config categories
- [ ] New endpoint: GET /api/acm/field-config returns field definitions for frontend
- [ ] Frontend reads field config at page load to build columnDefs dynamically

**Rationale:** AG Grid columns driven by same config that drives extraction and export.

---

### 4.2 Architecture Changes

#### CP-4: Architecture Section 5.2 Rewrite

Replace "Extensible Consultant Parser Architecture" with "Generic Configurable Parser Architecture":

**Config Source of Truth:**
```
BAR Excel Template → JSON Config Files → SurrealDB field_schema table
    ↓                     ↓                        ↓
  (import)          (default source)          (runtime source)
                                                   ↓
                    GenericParser ← loads config at extraction time
                         ↓
                  AG Grid columns ← reads config for column definitions
                         ↓
                  Excel/CSV export ← reads config for column order/names
```

**New Pydantic Models:**
```python
class FieldDef(BaseModel):
    internal_name: str          # e.g., "department"
    display_name: str           # e.g., "Department"
    excel_column: str           # e.g., "A"
    col_index: int              # e.g., 1
    field_type: str             # "string", "number", "date", "enum"
    required: bool
    active: bool = True         # Can be toggled off
    enum_name: Optional[str]    # Reference to enum config (e.g., "OwnedOrLeased")
    group: Optional[str]        # Column group (e.g., "organization", "building")

class FieldSchemaConfig(BaseModel):
    fields: list[FieldDef]
    enums: dict[str, list[str]]
    business_rules: list[BusinessRule]
    version: str
    source_template: Optional[str]
```

---

### 4.3 PRD Changes

#### CP-5: PRD Section 5.7 Replacement

Replace "Consultant Format Support" with "Configurable Field Schema":

| Source | Purpose | Format |
|--------|---------|--------|
| BAR Excel Template | Seed defaults (field names, picklists, rules) | .xlsm/.xlsx |
| Field Schema Config | Runtime field definitions | JSON (SurrealDB) |
| Enum Config | Picklist values for validation | JSON (SurrealDB) |

#### CP-6: PRD FR-107 Update

**OLD:** "System shall support multiple PDF provider formats (Prensa, Greencap)"
**NEW:** "System shall use configurable field definitions to parse any ACM PDF format via a single generic parser"

---

### 4.4 Code File Changes

| File | Action | Description |
|------|--------|-------------|
| `parsers/prensa.py` | **DELETE** | Absorbed into generic parser + config |
| `parsers/greencap.py` | **DELETE** | Absorbed into generic parser + config |
| `parsers/generic.py` | **REWRITE** | GenericParser driven by FieldSchemaConfig |
| `parsers/field_config.py` | **NEW** | FieldSchemaConfig, FieldDef Pydantic models |
| `parsers/config_loader.py` | **NEW** | Load config from JSON/SurrealDB/Excel |
| `parsers/__init__.py` | **SIMPLIFY** | Remove registry, export GenericParser + config loader |
| `parsers/base.py` | **KEEP** | RawACMItem, DocumentMeta data classes still useful |
| `acm_extractor.py` | **MODIFY** | Remove parser auto-detection, load field config |
| `api/routers/acm.py` | **ADD** | GET/PUT /api/acm/field-config endpoints |
| `migrations/17.surrealql` | **NEW** | field_schema table for runtime config |

---

## 5. Implementation Handoff

### Change Scope: Moderate

This change requires:
- **Backend developer** for parser refactoring, config loading, API endpoints
- **Frontend developer** for AG Grid config integration, Settings UI (E12-S4)

### Handoff Plan

| Role | Responsibility | Priority |
|------|---------------|----------|
| **Dev Team** | Implement E1-S11 (generic parser + config) | P0 - Do first |
| **Dev Team** | Update acm_extractor.py to use config | P0 - Do with E1-S11 |
| **Dev Team** | Add field-config API endpoints | P0 - Do with E1-S11 |
| **Dev Team** | AG Grid columns from config (E2-S8 enhancement) | P1 - After parser |
| **Dev Team** | E12-S4 Settings UI | P2 - After core config works |
| **Dev Team** | Update PRD + Architecture docs | P2 - After implementation |

### Success Criteria
1. Single GenericParser extracts records from both Prensa and Greencap PDFs using field config
2. AG Grid columns render from field config API
3. Excel/CSV export uses field config for column ordering
4. Field config editable via API (UI optional for MVP)
5. Default config matches current BAR schema exactly (no regression)
6. All existing tests pass or are updated to reflect new architecture

---

## 6. Appendix

### A. Existing Config Files (Already Available)

| File | Content | Location |
|------|---------|----------|
| `register_row.schema.json` | 47 field definitions with types, required flags | `docs/samplePDF/instructions-sample/` |
| `register_enums.json` | All enum picklist values | `docs/samplePDF/instructions-sample/` |
| `register_taxonomy.*.json` | Product classification taxonomy | `docs/samplePDF/instructions-sample/` |
| `consultant_wording_rules.json` | Normalization rules | `docs/samplePDF/instructions-sample/` |
| `bar-schema.md` | Human-readable BAR schema reference | `docs/reference/` |

### B. BAR Excel Template

- **File:** `docs/samplePDF/Clucth_Alexandra_District_BAR.xlsm`
- **Sheets:** DATA ENTRY (main), Instructions, Reference data (picklists), Taxonomy
- **Use:** Seed default field config, provide picklist values, define business rules
