# E35-S7: SF-First Validation Pipeline

## Story

Harden the ACM validation pipeline so that Salesforce picklist values are the authoritative source of truth. Ensure SF validation runs before BAR validation, the correction loop never overwrites SF-valid fields, product type casing is normalized from Title Case (taxonomy.py) to SF sentence case, BAR enum values are mapped to their SF equivalents, and corruption scenarios from production issues are covered by regression tests. The Broadmeadows reference SAMP must produce at least 28/31 SF-valid records.

## Acceptance Criteria

- **AC1**: SF validation runs BEFORE BAR validation -- SF schema is source of truth
- **AC2**: Correction loop never overwrites SF-valid values
- **AC3**: F4 product type casing: Title Case to SF sentence case normalization
- **AC4**: BAR enum values mapped to SF equivalents
- **AC5**: 5+ corruption scenarios from docs/issues have regression tests
- **AC6**: Broadmeadows produces >=28/31 records with SF-valid values

## Technical Design

### Architecture Overview

The existing `validate_acm_record()` in `acm_validator.py` already implements SF-first ordering (Required -> SF flat enums -> SF chains -> Business rules -> BAR audit-only). The primary gaps are:

1. **No SF-canonical write-back**: `_normalize_to_sf_value()` in `sf_picklist_validator.py` normalizes case-insensitively during validation but does not mutate the record value to the SF-canonical form. The record retains the original casing (e.g., "Flat Sheeting" instead of "Flat sheeting"), which causes downstream SF import failures.

2. **No SF-valid field freezing in correction loop**: `correct_records()` in `acm_extraction.py` sends ALL invalid fields to the LLM for correction, including fields that already pass SF validation. The LLM can reintroduce BAR values (e.g., "Good" instead of SF "Stable") for fields that were already SF-valid.

3. **Incomplete BAR-to-SF value mapping**: `_BAR_TO_SF_VALUE` in `sf_picklist_validator.py` only covers Friability. Missing mappings for Condition ("Good" -> "Stable"), DisturbancePotential ("Medium" -> "Moderate"), and other divergent values.

4. **No regression test coverage** for known corruption scenarios discovered in production.

The implementation adds a normalization pass that writes SF-canonical values back to records, a field-freezing mechanism that protects SF-valid fields from LLM correction overwrites, expanded BAR-to-SF mappings, and comprehensive regression tests.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/validators/sf_picklist_validator.py` | Modify | Expand `_BAR_TO_SF_VALUE` dict for all fields; add `normalize_record_to_sf()` function that writes back SF-canonical values |
| `open_notebook/extractors/validators/acm_validator.py` | Modify | Add `normalize_to_sf_canonical()` that calls `normalize_record_to_sf()`; add `sf_valid_fields()` that returns set of field names passing SF validation; wire normalization into `validate_acm_record()` |
| `open_notebook/graphs/acm_extraction.py` | Modify | Add SF-valid field freezing in `correct_records()` and `_llm_correct_records()`; expand Layer 1 correctable issue types to include `invalid_sf_enum` and `sf_chain` |
| `prompts/acm/correction.jinja` | Modify | Add frozen-field instructions with "DO NOT MODIFY" section listing SF-valid fields |
| `open_notebook/extractors/normalizers/enums.py` | Modify | Add missing BAR-to-SF synonym mappings for Condition and DisturbancePotential fields |
| `tests/test_sf_first_validation.py` | New | 5+ corruption regression tests, SF-first ordering assertion, SF normalization tests, field-freezing tests |

### Detailed Changes

#### 1. `open_notebook/extractors/validators/sf_picklist_validator.py`

**Expand `_BAR_TO_SF_VALUE` (line 67-72)**

The current mapping only covers Friability. Expand to cover all four SF flat enum fields:

```python
_BAR_TO_SF_VALUE: dict[str, dict[str, str]] = {
    "Friability_of_Material__c": {
        "Non Friable": "Non-friable",
        "Friable": "Friable",
    },
    "Condition__c": {
        "Good": "Stable",        # BAR "Good" -> SF "Stable"
    },
    "Disturbance_Potential_of_Material__c": {
        "Medium": "Moderate",    # BAR "Medium" -> SF "Moderate"
    },
    "Sample_Analysis_Result_Material_Status__c": {
        # No known BAR-to-SF mismatches for sample_result currently,
        # but placeholder for future additions.
    },
}
```

**Add `normalize_record_to_sf()` function (new, after `_normalize_to_sf_value`)**

This function iterates over all SF-mappable fields in a record dict, applies `_BAR_TO_SF_VALUE` normalization, then calls `_normalize_to_sf_value()` for case-insensitive write-back. It mutates the record in-place and returns a set of field names that were normalized.

```python
def normalize_record_to_sf(record: dict) -> set[str]:
    """Normalize all SF-mappable fields to SF-canonical values in-place.

    Applies:
    1. BAR-to-SF value mapping (_BAR_TO_SF_VALUE)
    2. Case-insensitive normalization to SF picklist canonical casing

    Returns:
        Set of internal field names that were modified.
    """
```

Logic:
- For each field in `SF_FLAT_ENUM_FIELD_MAP` and `_FIELD_ALIASES` that maps to an SF API name:
  - Get the current value from the record (try internal name, then SF API name)
  - Apply `_BAR_TO_SF_VALUE` mapping if the field's SF API name has a mapping
  - Look up SF picklist values from the schema bundle
  - Call `_normalize_to_sf_value(value, sf_picklist_values)` to get canonical casing
  - If the canonical value differs from the original, write it back to the record under the internal field name
  - Track which fields were modified
- Also handle `acm_product_type` (ACM_Sub_Classification__c) normalization: taxonomy.py outputs Title Case (e.g., "Flat Sheeting"), but SF uses sentence case ("Flat sheeting"). The chain validation already calls `_normalize_to_sf_value()` but only for validation -- this function writes the result back.
- Return the set of modified field names

**Note**: This function needs access to the SF schema bundle. It should instantiate `SalesforcePicklistValidator` internally or accept a bundle parameter. For simplicity, accept an optional `schema_bundle` parameter and fall back to `load_sf_field_schema()`.

#### 2. `open_notebook/extractors/validators/acm_validator.py`

**Add `normalize_to_sf_canonical()` (new function, after `_normalize_enum_for_validation`)**

A thin wrapper that calls `sf_picklist_validator.normalize_record_to_sf()` with graceful degradation if SF schema is unavailable:

```python
def normalize_to_sf_canonical(record: dict) -> set[str]:
    """Normalize record values to SF-canonical forms.

    Graceful degradation: returns empty set if SF schema is unavailable.
    """
    try:
        from open_notebook.extractors.validators.sf_picklist_validator import (
            normalize_record_to_sf,
        )
        return normalize_record_to_sf(record)
    except (ImportError, OSError) as e:
        logger.debug(f"SF normalization skipped: {e}")
        return set()
```

**Add `sf_valid_fields()` (new function)**

Returns the set of field names in a record that currently pass SF flat enum validation. Used by the correction loop to identify which fields to freeze:

```python
def sf_valid_fields(record: dict) -> set[str]:
    """Return set of internal field names that pass SF flat enum validation.

    Used by the correction loop to freeze SF-valid fields from LLM overwrites.
    Graceful degradation: returns empty set if SF schema is unavailable.
    """
    try:
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SalesforcePicklistValidator,
            SF_FLAT_ENUM_FIELD_MAP,
        )
        sf_validator = SalesforcePicklistValidator()
        sf_issues = sf_validator.validate_flat_enums(record)
        # Fields with issues are NOT sf-valid
        invalid_fields = {i.dependent_field for i in sf_issues}
        # Return internal field names that have values and no SF issues
        valid = set()
        for internal_name, sf_api_name in SF_FLAT_ENUM_FIELD_MAP.items():
            value = record.get(internal_name)
            if value and sf_api_name not in invalid_fields:
                valid.add(internal_name)
        return valid
    except (ImportError, OSError) as e:
        logger.debug(f"SF valid field check skipped: {e}")
        return set()
```

**Wire normalization into `validate_acm_record()` (line 397-454)**

Add a normalization step at the top of `validate_acm_record()`, after the function docstring, before step 1 (Required fields):

```python
def validate_acm_record(record: dict) -> ValidationResult:
    # ... docstring ...

    # Step 0: Normalize to SF-canonical values before validation
    normalize_to_sf_canonical(record)

    all_issues: list[ValidationIssue] = []
    # ... rest of function unchanged ...
```

This ensures that by the time validation runs, values like "Flat Sheeting" have already been normalized to "Flat sheeting", and "Good" has been normalized to "Stable".

#### 3. `open_notebook/graphs/acm_extraction.py`

**Add SF-valid field freezing in `correct_records()` (around line 2400-2441)**

Before Layer 1 correction, compute the set of SF-valid fields for each record and exclude them from correction:

```python
# In correct_records(), inside the per-record loop, before Layer 1:

# Compute SF-valid fields to freeze (AC2)
from open_notebook.extractors.validators.acm_validator import sf_valid_fields
frozen_fields = sf_valid_fields(record_dict)

# ... Layer 1 loop ...
for issue in validation.issues:
    # Skip frozen fields -- SF-valid values must not be overwritten
    if issue.field_name in frozen_fields:
        logger.info(
            f"Skipping correction of {issue.field_name}='{issue.current_value}' "
            f"— field is SF-valid (frozen)"
        )
        continue
    # ... rest of Layer 1 logic ...
```

**Add frozen-field filtering in `_llm_correct_records()` (around line 2500-2625)**

Before sending records to the LLM for correction:

1. Compute `frozen_fields = sf_valid_fields(record_dict)` for each record
2. Filter `validation.issues` to exclude frozen fields before rendering the correction prompt
3. Pass the frozen field names to the correction prompt template as a `frozen_fields` variable
4. After parsing the LLM response, reject any corrections to frozen fields:

```python
# After parsing LLM response (line 2604):
if isinstance(corrected, dict):
    for field, value in corrected.items():
        if field in frozen_fields:
            logger.warning(
                f"LLM attempted to modify frozen field {field} "
                f"(SF-valid), ignoring correction"
            )
            continue
        # ... existing correction logic ...
```

**Expand Layer 1 correctable issue types in `should_correct()` (line 2662-2665)**

The current `should_correct()` only considers `("enum_mismatch", "business_rule", "invalid_sf_enum")` as correctable. Add `"sf_chain"` and `"invalid_chain_value"` to the correctable set so that SF chain validation failures also trigger correction:

```python
correctable = [
    i
    for i in validation.issues
    if i.issue_type in (
        "enum_mismatch",
        "business_rule",
        "invalid_sf_enum",
        "sf_chain",
        "invalid_chain_value",
    )
]
```

**Expand Layer 1 correctable types in `correct_records()` (line 2417-2418)**

Currently Layer 1 only tries deterministic normalization for `issue.issue_type != "enum_mismatch"`. Extend to also attempt normalization for `invalid_sf_enum` issues:

```python
for issue in validation.issues:
    if issue.field_name in frozen_fields:
        continue
    if issue.issue_type not in ("enum_mismatch", "invalid_sf_enum"):
        still_invalid.append(issue)
        continue
    # ... existing Layer 1 normalization logic ...
```

#### 4. `prompts/acm/correction.jinja`

Add a "DO NOT MODIFY" section after the "Correction Instructions" section. This section lists fields that are already SF-valid and must not be changed by the LLM:

```jinja
{% if frozen_fields %}
## DO NOT MODIFY — SF-Valid Fields

The following fields have already been validated against Salesforce picklist values and are CORRECT. Do NOT change them, even if they look different from BAR terminology:

{% for field_name, field_value in frozen_fields.items() %}
- **{{ field_name }}**: `{{ field_value }}` (SF-valid — do not change)
{% endfor %}

**Important SF-BAR differences:**
- "Stable" is the correct SF value for BAR "Good" condition — do NOT change it to "Good"
- "Moderate" is the correct SF value for BAR "Medium" disturbance — do NOT change it to "Medium"
- "Non-friable" (with hyphen) is the correct SF value — do NOT change it to "Non Friable"
- Compound results like "Negative - Treated as Positive" are valid SF values — do NOT simplify
{% endif %}
```

This section is conditionally rendered only when `frozen_fields` is non-empty. The `frozen_fields` variable is a dict of `{field_name: current_value}` passed from `_llm_correct_records()`.

**Update the prompt rendering call in `_llm_correct_records()`** to pass the frozen fields:

```python
frozen_fields_display = {
    f: record_dict.get(f, "")
    for f in frozen_fields
    if record_dict.get(f)
}

correction_prompt = prompter.render(
    data={
        "record_json": json.dumps(record_dict, indent=2, default=str),
        "validation_issues": [i.model_dump() for i in validation.issues],
        "frozen_fields": frozen_fields_display,
    }
)
```

#### 5. `open_notebook/extractors/normalizers/enums.py`

Minor additions to ensure the synonym maps produce SF-compatible values rather than BAR-only values.

**Condition synonyms (line 34-43)**: Already correct -- "Good" maps to "Stable" (added in E30-S6). No change needed.

**Disturbance synonyms (line 47-55)**: Already correct -- "Medium" maps to "Moderate". No change needed.

**Potential addition**: If any new BAR synonyms are discovered during AC5 regression testing that are not covered, add them to the appropriate synonym dict. The current maps appear complete for known values. This file is listed as a change target primarily for safety -- if the `_BAR_TO_SF_VALUE` expansion in `sf_picklist_validator.py` reveals gaps, they get patched here.

#### 6. `tests/test_sf_first_validation.py` (NEW)

A new test file with the following test functions:

**Test structure:**

```python
"""
Regression tests for SF-First Validation Pipeline.

Story: E35-S7
Tests: SF-first ordering, SF normalization write-back, field freezing,
       BAR-to-SF mapping, and 7 corruption scenario regressions.
"""

import pytest
from unittest.mock import patch, MagicMock
from open_notebook.extractors.validators.acm_validator import (
    validate_acm_record,
    normalize_to_sf_canonical,
    sf_valid_fields,
    ValidationResult,
)
from open_notebook.extractors.validators.sf_picklist_validator import (
    _normalize_to_sf_value,
    normalize_record_to_sf,
    _BAR_TO_SF_VALUE,
    SF_FLAT_ENUM_FIELD_MAP,
)
```

**AC1 Tests (SF-first ordering):**

| Test | Description |
|------|-------------|
| `test_sf_validation_runs_before_bar` | Patch SF validator and BAR `validate_enum_fields` with side_effect trackers. Assert SF flat enum validation is called before BAR. Validates the call order in `validate_acm_record()`. |
| `test_sf_unavailable_falls_back_to_bar` | Patch SF import to raise `ImportError`. Assert BAR validation issues are in `result.issues` (blocking), not `bar_warnings`. Validates graceful degradation. |

**AC2 Tests (field freezing):**

| Test | Description |
|------|-------------|
| `test_sf_valid_fields_returns_correct_set` | Create a record with `material_condition="Stable"` (SF-valid) and `friable="Non Friable"` (BAR, not SF-valid). Assert `sf_valid_fields()` returns `{"material_condition"}` but not `"friable"`. |
| `test_frozen_fields_not_overwritten_by_correction` | Simulate a record where `material_condition` is SF-valid ("Stable") but `friable` is invalid. Run through `correct_records()` (mocked LLM returns `{"material_condition": "Good", "friable": "Non-friable"}`). Assert `material_condition` remains "Stable" (frozen), `friable` is corrected to "Non-friable". |

**AC3 Tests (Title Case to sentence case):**

| Test | Description |
|------|-------------|
| `test_normalize_product_type_title_to_sentence_case` | Record with `acm_product_type="Flat Sheeting"`. After `normalize_record_to_sf()`, assert value is `"Flat sheeting"` (SF sentence case). |
| `test_normalize_to_sf_value_case_insensitive` | Direct unit test of `_normalize_to_sf_value("Flat Sheeting", ["Flat sheeting", "Other"])` returns `"Flat sheeting"`. |

**AC4 Tests (BAR-to-SF mapping):**

| Test | Description |
|------|-------------|
| `test_bar_good_maps_to_sf_stable` | Record with `material_condition="Good"`. After `normalize_record_to_sf()`, assert value is `"Stable"`. |
| `test_bar_medium_maps_to_sf_moderate` | Record with `disturbance_potential="Medium"`. After normalization, assert value is `"Moderate"`. |
| `test_bar_non_friable_maps_to_sf_hyphenated` | Record with `friable="Non Friable"` (BAR). After normalization, assert value is `"Non-friable"` (SF). |
| `test_bar_to_sf_value_map_completeness` | Assert `_BAR_TO_SF_VALUE` has entries for `Friability_of_Material__c`, `Condition__c`, `Disturbance_Potential_of_Material__c`. |

**AC5 Tests (corruption regression -- 7 scenarios):**

| # | Test | Corruption Scenario | Assertion |
|---|------|---------------------|-----------|
| 1 | `test_corruption_compound_value_simplification` | LLM simplifies "Negative - Treated as Positive" to "Negative" | After validation, "Negative - Treated as Positive" is preserved. Simulates LLM correction returning simplified value; frozen-field guard rejects it. |
| 2 | `test_corruption_title_case_product_type` | taxonomy.py outputs "Flat Sheeting" (Title Case) | After `normalize_record_to_sf()`, `acm_product_type` is "Flat sheeting" (sentence case). Validates AC3 at regression level. |
| 3 | `test_corruption_bar_medium_reintroduction` | LLM correction reintroduces "Medium" for `disturbance_potential` after it was normalized to "Moderate" | After normalization + frozen-field guard, "Moderate" is preserved and LLM's "Medium" is rejected. |
| 4 | `test_corruption_good_condition_wrong_sf_mapping` | Record has `material_condition="Good"` which correction loop changes to BAR "Good" instead of SF "Stable" | After normalization, "Good" becomes "Stable". Frozen-field guard prevents reintroduction. |
| 5 | `test_corruption_friability_overwrite_compound_result` | Record has `sample_result="Positive - Non-friable"` and `friable="Non-friable"`. LLM correction changes `friable` to "Friable" (wrong). | Frozen-field logic on `friable` (if SF-valid) prevents overwrite. Business rule BAR-004 validates consistency. |
| 6 | `test_corruption_double_normalization` | Record normalized BAR -> SF ("Medium" -> "Moderate"), then correction loop re-normalizes BAR ("Moderate" back to "Moderate"). Idempotency check. | After two normalization passes, value remains "Moderate" (no double-conversion). |
| 7 | `test_corruption_no_access_not_sampled_loop` | Record has `sample_result="No Access"` (BAR-only, absent from SF picklists). Correction loop should NOT auto-correct this to a valid SF value -- it needs user review. | `validate_acm_record()` returns `needs_user_review` issue type (non-blocking warn), not `invalid_sf_enum` rejection. Correction loop skips it. |

**AC6 Test (Broadmeadows integration):**

| Test | Description |
|------|-------------|
| `test_broadmeadows_sf_valid_record_count` | Integration test (marked `@pytest.mark.integration`) that loads the Broadmeadows reference extraction output, runs `validate_acm_record()` + `normalize_to_sf_canonical()` on each record, and asserts `>= 28` out of 31 records are `is_valid=True`. Requires the Broadmeadows fixture data. If fixture data is unavailable, the test is skipped with `pytest.mark.skipif`. |

### Test Plan

| Test | File | Validates |
|------|------|-----------|
| `test_sf_validation_runs_before_bar` | `tests/test_sf_first_validation.py` | AC1 |
| `test_sf_unavailable_falls_back_to_bar` | `tests/test_sf_first_validation.py` | AC1 |
| `test_sf_valid_fields_returns_correct_set` | `tests/test_sf_first_validation.py` | AC2 |
| `test_frozen_fields_not_overwritten_by_correction` | `tests/test_sf_first_validation.py` | AC2 |
| `test_normalize_product_type_title_to_sentence_case` | `tests/test_sf_first_validation.py` | AC3 |
| `test_normalize_to_sf_value_case_insensitive` | `tests/test_sf_first_validation.py` | AC3 |
| `test_bar_good_maps_to_sf_stable` | `tests/test_sf_first_validation.py` | AC4 |
| `test_bar_medium_maps_to_sf_moderate` | `tests/test_sf_first_validation.py` | AC4 |
| `test_bar_non_friable_maps_to_sf_hyphenated` | `tests/test_sf_first_validation.py` | AC4 |
| `test_bar_to_sf_value_map_completeness` | `tests/test_sf_first_validation.py` | AC4 |
| `test_corruption_compound_value_simplification` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_title_case_product_type` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_bar_medium_reintroduction` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_good_condition_wrong_sf_mapping` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_friability_overwrite_compound_result` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_double_normalization` | `tests/test_sf_first_validation.py` | AC5 |
| `test_corruption_no_access_not_sampled_loop` | `tests/test_sf_first_validation.py` | AC5 |
| `test_broadmeadows_sf_valid_record_count` | `tests/test_sf_first_validation.py` | AC6 |

### Implementation Order

1. **Phase 1 -- Normalization** (AC3, AC4): Expand `_BAR_TO_SF_VALUE` in `sf_picklist_validator.py`, add `normalize_record_to_sf()`. Add `normalize_to_sf_canonical()` and `sf_valid_fields()` wrappers in `acm_validator.py`. Wire `normalize_to_sf_canonical()` into `validate_acm_record()` as Step 0.

2. **Phase 2 -- Field Freezing** (AC2): Add frozen-field computation in `correct_records()` and `_llm_correct_records()`. Update `correction.jinja` with the DO NOT MODIFY section. Expand correctable issue types in `should_correct()`.

3. **Phase 3 -- Tests** (AC1, AC5, AC6): Write all tests in `tests/test_sf_first_validation.py`. Run the full test suite to confirm no regressions.

4. **Phase 4 -- Verification**: Run `ruff check . --fix && ruff format .` for lint compliance. Run `pytest tests/test_sf_first_validation.py -v` to confirm all new tests pass. Run `pytest tests/test_sf_picklist_validator.py -v` to confirm no regressions in existing SF tests.

### Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `normalize_record_to_sf()` double-writes cause unexpected mutations | Records get wrong values if normalization is applied twice | Medium | Idempotency test (`test_corruption_double_normalization`). Normalization is designed to be idempotent -- applying it twice produces the same result. |
| SF schema files unavailable in test/CI environment | Tests that depend on real SF schema fail | Medium | Graceful degradation in `normalize_to_sf_canonical()` and `sf_valid_fields()` returns empty set. Tests use `load_sf_field_schema()` fixture with `pytest.importorskip` or mock bundles for unit tests. |
| LLM ignores "DO NOT MODIFY" instruction in correction prompt | LLM overwrites frozen fields despite prompt instruction | High | Prompt-level instruction is defense-in-depth only. The code-level guard in `_llm_correct_records()` (rejecting corrections to frozen fields) is the authoritative enforcement. LLM prompt just reduces unnecessary correction attempts. |
| `acm_product_type` normalization breaks when SF schema lacks Sub_Classification picklist data | Normalization silently skips, leaving Title Case in the record | Low | `normalize_record_to_sf()` logs a debug message when picklist data is unavailable. The existing chain validation in `validate_acm_chain()` already normalizes at the chain level as a backstop. |
| Broadmeadows integration test flaky due to extraction non-determinism | AC6 test fails intermittently | Medium | Test validates post-extraction validation results, not extraction itself. Uses stored/fixture extraction output, not live extraction. Mark as `@pytest.mark.integration` so it only runs explicitly. |
| Expanding `_BAR_TO_SF_VALUE` introduces false corrections for edge-case values | A BAR value that is also a valid SF value gets wrongly remapped | Low | `_BAR_TO_SF_VALUE` only maps values that differ between BAR and SF. Values that are identical in both systems (e.g., "Friable") have identity mappings or are omitted. Each mapping is validated against the actual SF picklist values in the test suite. |

### Key Implementation Notes

1. **`normalize_record_to_sf()` must handle both internal field names and SF API names.** Records in the pipeline use internal names (`friable`, `material_condition`) but the SF validator uses SF API names (`Friability_of_Material__c`, `Condition__c`). The function should read from internal names and write back to internal names.

2. **The `acm_product_type` field is NOT in `SF_FLAT_ENUM_FIELD_MAP`** -- it is validated through the chain validator (Classification -> SubClassification chain). `normalize_record_to_sf()` needs to also handle chain-validated fields by looking up the valid values from the chain mapping for the current controller value.

3. **`_apply_field_correction()` (line 2486-2498) only handles 4 fields**: `sample_result`, `material_condition`, `friable`, `disturbance_potential`. If `acm_product_type` or `acm_product_group` corrections are needed in the future, this function must be extended.

4. **The `should_correct()` function (line 2627)** currently filters to `("enum_mismatch", "business_rule", "invalid_sf_enum")`. Adding `"sf_chain"` and `"invalid_chain_value"` ensures chain validation failures also trigger the correction loop. However, chain issues may not be correctable by the LLM -- monitor for correction-loop cycling.

5. **`_BAR_ONLY_VALUES` (line 85)** contains `{"Not Sampled", "No Access"}`. These should remain as `needs_user_review` (non-blocking warn), NOT be auto-corrected. The corruption regression test `test_corruption_no_access_not_sampled_loop` validates this.

## Dev Agent Record

| Field | Value |
|-------|-------|
| Build status | PENDING |
| Files verified | PENDING |
| Pages verified | N/A (backend-only story) |
| Screenshot path | N/A |
| Tests written | PENDING |
| Tests passing | PENDING |
| Lint status | PENDING |
