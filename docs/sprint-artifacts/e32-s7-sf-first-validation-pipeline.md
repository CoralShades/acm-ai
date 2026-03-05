# E32-S7 Tech Spec: SF-First Validation Pipeline

**Story ID:** E32-S7
**Title:** SF-First Validation Pipeline
**Sprint:** V3-5
**Story Points:** 5
**Risk Level:** HIGH
**Type:** backend
**Priority:** P0

## Story Summary

Promote SF picklist validation from informational to the primary blocking authority for
`sample_result`, `material_condition`, `friable`, and `disturbance_potential`. Demote BAR
`validate_enum_fields()` to non-blocking audit mode (`bar_warnings`). Promote SF chain
validation from WARN to REJECT policy. Ensure graceful degradation when SF schema files
are unavailable.

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC1 | SF flat enum validation is the primary blocking validator for sample_result, material_condition, friable, disturbance_potential | ✅ |
| AC2 | BAR `validate_enum_fields()` demoted to `bar_warnings` (non-blocking, audit-only) | ✅ |
| AC3 | SF chain validation promoted from WARN to REJECT policy (blocking) | ✅ |
| AC4 | `Negative - Treated as Positive` passes SF validation without correction | ✅ |
| AC5 | `Not Sampled` and `No Access` flagged as `needs_user_review` (not rejected or auto-corrected) | ✅ |
| AC6 | Graceful degradation: if SF schema unavailable, BAR path used as fallback | ✅ |

## File Changes

| File | Change |
|------|--------|
| `open_notebook/extractors/validators/sf_picklist_validator.py` | Add `SF_FLAT_ENUM_FIELD_MAP`, `_BAR_ONLY_VALUES`, `validate_flat_enums()` method to `SalesforcePicklistValidator` |
| `open_notebook/extractors/validators/acm_validator.py` | Refactor `validate_acm_record()` to SF-first pipeline; demote BAR enums to `bar_warnings`; add `bar_warnings` field to `ValidationResult` |
| `tests/test_sf_picklist_validator.py` | Add `TestSFPrimaryFlatEnums` class with 7 tests covering flat enum validation |
| `tests/test_acm_validator.py` | Add `TestSFFirstValidation` class with 4 tests covering SF-first pipeline |

## Implementation Notes

### Validation Order in `validate_acm_record()`

```
1. Required fields — always blocking
2. SF flat enum validation — blocking (primary authority)
3. SF chain validation (REJECT policy) — blocking
4. Business rules — always blocking (BAR & SF share N/A values)
5. BAR enum validation — audit-only (bar_warnings, non-blocking)
```

### Graceful Degradation

When SF schema files are unavailable (`SFSchemaLoadError`, `ImportError`, `OSError`),
the validator falls back to BAR enum validation as blocking (preserves prior behavior).

### `ValidationResult` Model

```python
class ValidationResult(BaseModel):
    is_valid: bool
    issues: list[ValidationIssue] = []
    chain_warnings: list[ValidationIssue] = []  # WARN-policy SF chain issues
    bar_warnings: list[ValidationIssue] = []     # BAR audit issues (non-blocking)
```

### BAR-Only Values

`"Not Sampled"` and `"No Access"` are valid in BAR register but absent from SF picklists.
These are flagged with `issue_type="needs_user_review"` and `policy_action="warn"` — they
never trigger the correction loop.

### `Negative - Treated as Positive`

This compound SF value is present in the SF `Sample_Analysis_Result_Material_Status__c`
picklist. It must pass flat enum validation without triggering correction (AC4).

## Dependencies

- E30-S4 (Dependent Picklist Validator) — provides `SalesforcePicklistValidator` and `ValidationPolicy`
- E32-S4 (Classifier Update SF Taxonomy) — ensures SF taxonomy values are in scope
