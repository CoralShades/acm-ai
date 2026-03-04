# Tech Spec: E30-S4 — Dependent Picklist Validator

**Story ID:** E30-S4
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-1
**Story Points:** 5
**Risk Level:** HIGH
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:** E30-S1 (SF Schema Config Loader — completed)

---

## User Story

As a data quality engineer, I want dependent picklist chains validated at extraction and export time so that invalid Friability→Classification→SubClassification and BuildingType→BuildingCategory combinations are caught early and surfaced to users before data reaches Salesforce.

---

## Acceptance Criteria

| ID   | Criterion | Verification Method |
|------|-----------|---------------------|
| AC1  | `SalesforcePicklistValidator` class with `validate_acm_chain()` and `validate_building_chain()` methods | Unit test: class instantiates, methods callable |
| AC2  | ACM chain: Friability→Classification→SubClassification validates all 36 valid (friability, classification) combinations from `SFSchemaBundle.dependencies` | Unit test: all 36 combos pass, invalid combos fail |
| AC3  | Building chain: BuildingType→BuildingCategory validates all 114 type→category mappings from `SFSchemaBundle.dependencies` | Unit test: all 114 mappings pass, unmapped types fail |
| AC4  | Strict case-sensitive matching — "cement products" ≠ "Cement products" | Unit test: lowercase input rejected, exact case accepted |
| AC5  | WARN policy: `validate(record, policy="warn")` returns `ValidationResult` with issues but `is_valid=True` (non-blocking) | Unit test: invalid chain returns issues with `policy_action="warn"` |
| AC6  | REJECT policy: `validate(record, policy="reject")` returns `ValidationResult` with `is_valid=False` (blocking) | Unit test: invalid chain returns `is_valid=False` |
| AC7  | Business rule BAR-001: Negative result → Condition = N/A (negative), Disturbance = N/A (negative) — integrated into chain validation | Unit test: negative result with non-N/A condition fails |
| AC8  | Validator loads dependency chain definitions from `load_sf_field_schema()` at runtime (not hardcoded) | Unit test: mock `load_sf_field_schema()` with custom chains, validator uses them |
| AC9  | Exhaustive unit tests: all 36 valid Friability×Classification combos, all 114 BuildingType→Category mappings | pytest: parametrize over all valid combos |
| AC10 | Integration with `acm_validator.py`: `validate_acm_record()` calls `SalesforcePicklistValidator` chain validation when SF schema is available | Unit test: `validate_acm_record()` returns chain validation issues |

---

## Technical Design

### Overview

This story creates a new `SalesforcePicklistValidator` class that validates dependent picklist chains using the `SFSchemaBundle` loaded by E30-S1. It integrates into the existing `acm_validator.py` validation pipeline.

### Architecture Decision: Separate Validator Module

Create `sf_picklist_validator.py` as a new module in the validators package, keeping the SF-specific chain validation separate from the BAR-centric `acm_validator.py`. The existing validator gains a new `validate_sf_chains()` function that delegates to the new module.

### Key Design Points

1. **Runtime chain loading**: The validator calls `load_sf_field_schema()` from `config_loader.py` (E30-S1) to get `SFSchemaBundle.dependencies` at runtime. No hardcoded mappings in the validator itself.

2. **Two-phase chain validation**:
   - ACM chain: `Friability_of_Material__c` → `ACM_Classification__c` → `ACM_Sub_Classification__c` (three SFDependencyChain lookups)
   - Building chain: `Building_Type__c` → `Building_Category__c` (one SFDependencyChain lookup)

3. **Policy enum**: `ValidationPolicy.WARN` (non-blocking, issues surfaced as badges) vs `ValidationPolicy.REJECT` (blocking, prevents export). The policy is a parameter, not a global setting — extraction uses WARN, export uses REJECT.

4. **Case-sensitive matching**: Exact string match against `SFDependencyChain.mapping` keys/values. No `.lower()` normalization. This matches Salesforce's behavior for restricted picklists.

5. **BAR-001 integration**: The existing `validate_business_rules()` in `acm_validator.py` already handles BAR-001 (negative→N/A). The new validator adds chain validation alongside it, not replacing it.

### V3 Compliance
- **SF field names**: `Friability_of_Material__c`, `ACM_Classification__c`, `ACM_Sub_Classification__c`, `Building_Type__c`, `Building_Category__c`, `Sample_Analysis_Result_Material_Status__c`, `Condition__c`, `Disturbance_Potential_of_Material__c`
- **Provider pattern**: N/A (validation is provider-agnostic)
- **Provenance**: N/A
- **SSE events**: N/A

### Class Design

```python
class ValidationPolicy(str, Enum):
    WARN = "warn"      # Non-blocking: surface issues as badges
    REJECT = "reject"  # Blocking: prevent export

class ChainValidationIssue(BaseModel):
    chain_name: str          # "acm_chain" or "building_chain"
    controller_field: str    # SF API name of controller
    controller_value: str    # Actual value
    dependent_field: str     # SF API name of dependent
    dependent_value: str     # Actual value
    valid_values: list[str]  # What was expected
    issue_type: str          # "invalid_chain_value"
    policy_action: str       # "warn" or "reject"

class SalesforcePicklistValidator:
    def __init__(self):
        """Loads SF schema bundle from config_loader at init time."""

    def validate_acm_chain(self, record: dict, policy: ValidationPolicy) -> list[ChainValidationIssue]:
        """Validate Friability → Classification → SubClassification chain."""

    def validate_building_chain(self, record: dict, policy: ValidationPolicy) -> list[ChainValidationIssue]:
        """Validate BuildingType → BuildingCategory chain."""

    def validate_all_chains(self, record: dict, policy: ValidationPolicy) -> ValidationResult:
        """Run all chain validations and return combined result."""
```

### Field Mapping: ACM Record dict keys → SF API names

The validator needs to map between the ACM record's internal field names (used in `acm_validator.py`) and SF API names (used in the dependency chains):

| Record Key | SF API Name |
|------------|-------------|
| `friable` / `Friability_of_Material__c` | `Friability_of_Material__c` |
| `acm_classification` / `ACM_Classification__c` | `ACM_Classification__c` |
| `acm_sub_classification` / `ACM_Sub_Classification__c` | `ACM_Sub_Classification__c` |
| `building_type` / `Building_Type__c` | `Building_Type__c` |
| `building_category` / `Building_Category__c` | `Building_Category__c` |
| `sample_result` / `Sample_Analysis_Result_Material_Status__c` | `Sample_Analysis_Result_Material_Status__c` |
| `material_condition` / `Condition__c` | `Condition__c` |
| `disturbance_potential` / `Disturbance_Potential_of_Material__c` | `Disturbance_Potential_of_Material__c` |

The validator should accept both key styles (internal BAR name or SF API name) to work with both legacy and V3 record formats.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/validators/sf_picklist_validator.py` | CREATE | `SalesforcePicklistValidator` class with chain validation |
| `open_notebook/extractors/validators/__init__.py` | MODIFY | Export new validator class and types |
| `open_notebook/extractors/validators/acm_validator.py` | MODIFY | Add `validate_sf_chains()` call in `validate_acm_record()` |
| `tests/test_sf_picklist_validator.py` | CREATE | Exhaustive unit tests for all chains |

---

## Database Changes

None. Dependency chains are already stored in `field_schema:sf_v1` by E30-S1's `load_sf_field_schema()`.

---

## API Changes

None. Validation is internal to the extraction/export pipeline. Frontend AC5/AC6 (WARN badges, grayed export button) will be handled by E33-series frontend stories.

---

## Frontend Changes

None (backend-only story). AC5 and AC6 define the validation *policies* but the UI rendering is a separate concern for E33 stories.

---

## Test Plan

### Unit Tests — `tests/test_sf_picklist_validator.py`

1. **test_validator_instantiates**: `SalesforcePicklistValidator()` loads schema without error
2. **test_acm_chain_all_36_valid_combos**: Parametrize over all 36 (friability, classification) pairs → all pass
3. **test_acm_chain_invalid_classification_for_friability**: Non-friable + "(f)" classification → fails
4. **test_acm_chain_invalid_sub_classification**: Valid classification + wrong sub-classification → fails
5. **test_building_chain_all_114_types**: Parametrize over all 114 building types → correct category
6. **test_building_chain_unknown_type**: Unmapped building type → validation issue
7. **test_case_sensitive_matching**: "cement products" (lowercase) rejected, "Cement products" accepted
8. **test_warn_policy_returns_valid_true**: Invalid chain + WARN → `is_valid=True`, issues non-empty
9. **test_reject_policy_returns_valid_false**: Invalid chain + REJECT → `is_valid=False`
10. **test_bar001_negative_result_na_condition**: Negative sample + non-N/A condition → issue
11. **test_runtime_schema_loading**: Mock `load_sf_field_schema()` with custom chains → validator uses them
12. **test_missing_fields_skipped**: Record missing friability field → no chain error (skip)
13. **test_integration_validate_acm_record**: `validate_acm_record()` includes chain validation issues

### Integration Tests

None required — chain data comes from `config_loader.py` which has its own E30-S1 tests.

---

## Dev Agent Record
- **Status**: Completed
- **Started**: 2026-03-03
- **Completed**: 2026-03-03
- **Build**: PASS
- **Tests**: PASS (187 tests)
- **Review**: Audit completed — see V3/prompts/findings.md (F1-F8)
- **Notes**: BAR→SF normalization added (_BAR_TO_SF_VALUE). WARN/REJECT policy split on ValidationResult. F4 (product type casing) remains open — separate story needed.
