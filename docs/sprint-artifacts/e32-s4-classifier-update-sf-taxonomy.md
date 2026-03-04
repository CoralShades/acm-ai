# Tech Spec: E32-S4 — Classifier Update: SF Taxonomy Sentence Case Normalization

**Story ID:** E32-S4
**Epic:** E32 — AI Processing & Validation
**Sprint:** V3-4 (can be pulled earlier — data fix, no dependencies)
**Story Points:** 2
**Risk Level:** MEDIUM
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:** E30-S4 (Dependent Picklist Validator — completed), E30-S6 (BAR→SF Vocabulary Transition — completed)

---

## User Story

As a data quality engineer, I want product types output by `classify_product()` to pass SF chain validation without false-positive casing mismatches, so that the dependent picklist validator correctly distinguishes real data errors from harmless case differences.

---

## Background: Finding F4

Post-implementation audit of E30-S4 discovered that `taxonomy.py` `CLASSIFICATION_PATTERNS` (lines 139–579) outputs ~60 product types in **Title Case** (e.g., "Flat Sheeting", "Ceiling Tiles"). Salesforce `ACM_Sub_Classification__c` uses **sentence case** (e.g., "Flat sheeting", "Ceiling tiles"). E30-S4 AC4 mandates strict case-sensitive matching, so every Title Case product type produces a false-positive chain validation issue.

Full details: `V3/output/github-issue-e30s4-audit.md` (Finding F4).

### Confirmed Mismatches (from V3/item-list.txt raw SF metadata)

| `classify_product()` output | SF `ACM_Sub_Classification__c` | Match? |
|-----------------------------|--------------------------------|--------|
| "Flat Sheeting"             | "Flat sheeting"                | FAIL   |
| "Corrugated Roof Sheeting"  | "Corrugated roof sheeting"     | FAIL   |
| "Ceiling Tiles"             | "Ceiling tiles"                | FAIL   |
| "Vinyl Tiles"               | "Vinyl tiles"                  | FAIL   |
| "Ridge Capping"             | "Ridge capping"                | FAIL   |
| "Clutch Plates"             | "Clutch plates"                | FAIL   |
| "Internal Lining"           | "Internal lining"              | FAIL   |
| "Cement Pipe"               | "Cement pipe"                  | FAIL   |
| "Cement Flue"               | "Cement flue"                  | FAIL   |
| "Water Tanks"               | "Water tanks"                  | FAIL   |
| "Roof Tiles"                | "Roof tiles"                   | FAIL   |
| "Rainwater Guttering"       | "Rainwater guttering"          | FAIL   |
| "Compressed Flat Sheeting"  | "Compressed flat sheeting"     | FAIL   |
| "Fire Door Core"            | "Fire door core"               | FAIL   |
| "Fire Rating Material"      | "Fire rated material"          | FAIL   |
| "Rope or Braided Gasket"    | "Rope or braided gasket"       | FAIL   |
| "Rubber Gasket"             | "Rubber gasket"                | FAIL   |
| "Loose Fill Insulation"     | "Loose fill insulation"        | FAIL   |
| "Textured Coating"          | "Textured coating"             | FAIL   |
| "Brake pads"                | "Brake pads"                   | OK     |
| "Mastic"                    | "Mastic"                       | OK     |
| "Lagging"                   | "Lagging"                      | OK     |
| "Millboard"                 | "Millboard"                    | OK     |

### Why Simple Sentence Case Conversion Won't Work

SF values contain exceptions that a naive `_to_sf_sentence_case()` would break:

| SF Value | Exception Type |
|----------|---------------|
| "CAF gasket(s)"             | Acronym — "CAF" must stay uppercase |
| "SMF insulation"            | Acronym — "SMF" must stay uppercase |
| "HRC fuse"                  | Acronym — "HRC" must stay uppercase |
| "Bituminous adhesive (BlackJack)" | Trade name in parens |
| "Sprayed insulation (Limpet)"     | Trade name in parens |
| "Laminated cement sheeting (Tilux)" | Trade name in parens |
| "Low density asbestos fibre board (asbestos insulated board)" | Parens content all lowercase (NOT Title Case like taxonomy.py outputs) |

---

## Acceptance Criteria

| ID  | Criterion | Verification Method |
|-----|-----------|---------------------|
| AC1 | Product types from `classify_product()` pass SF chain validation after normalization | Unit test: Title Case product types resolve to SF values |
| AC2 | All 133 `ACM_Sub_Classification__c` values have correct case in SF chain lookups | Unit test: parametrize over classification→sub_classification chain, all valid combos pass |
| AC3 | Case-sensitive matching still enforced for controller values (`Friability_of_Material__c`, `ACM_Classification__c`) | Unit test: lowercase controller values still rejected |
| AC4 | Existing E30-S4 test suite passes — no regression | `pytest tests/test_sf_picklist_validator.py` — all 187+ tests pass |
| AC5 | F4 finding in `V3/output/github-issue-e30s4-audit.md` updated to FIXED | Manual: status table updated |

---

## Technical Design

### Approach: SF-Schema-Based Case Normalization (Option B+)

Instead of a fragile `_to_sf_sentence_case()` heuristic, use the **SF schema itself** as the normalization source. The chain's `valid_values` already contain the correct SF casing. Build a case-insensitive index from those values to normalize taxonomy output.

This is a refinement of the audit's recommended Option (b): normalization still happens in `sf_picklist_validator.py` between classification output and chain lookup, but uses SF schema values instead of casing rules.

### Implementation Detail

#### 1. New helper function in `sf_picklist_validator.py`

```python
def _normalize_to_sf_value(value: str, valid_values: list[str]) -> str:
    """Normalize a value to its SF-canonical casing using case-insensitive lookup.

    If value matches a valid_values entry case-insensitively but not
    case-sensitively, returns the SF-correct version. Otherwise returns
    the original value unchanged (which will then fail strict validation
    if it's truly invalid).

    This handles the taxonomy.py Title Case → SF sentence case gap
    without hardcoding casing rules or maintaining a manual mapping table.
    """
    # Exact match — fast path, no normalization needed
    if value in valid_values:
        return value

    # Case-insensitive lookup
    value_lower = value.lower()
    for sf_value in valid_values:
        if sf_value.lower() == value_lower:
            return sf_value

    # No match — return original (will fail validation, which is correct)
    return value
```

#### 2. Apply normalization in `validate_acm_chain()` — Sub-Classification only

In the existing `validate_acm_chain()` method, after reading `sub_classification` from the record and before the `sub_classification not in valid_values` check, normalize:

```python
# Chain 2: Classification → SubClassification
if classification and sub_classification:
    chain = _find_chain(...)
    if chain:
        valid_values = chain.mapping.get(classification)
        if valid_values is not None and isinstance(valid_values, list):
            # Normalize sub_classification to SF casing
            sub_classification = _normalize_to_sf_value(sub_classification, valid_values)
            if sub_classification not in valid_values:
                issues.append(...)
```

#### 3. What does NOT change

- **Controller fields**: `Friability_of_Material__c` and `ACM_Classification__c` remain strictly case-sensitive. No normalization applied to these — they use the existing `_BAR_TO_SF_VALUE` mapping from E30-S4 for known BAR→SF differences (e.g., "Non Friable" → "Non-friable").
- **Building chain**: `Building_Type__c` → `Building_Category__c` — no change. Building values don't have the Title Case vs sentence case gap.
- **CLASSIFICATION_PATTERNS**: No changes to `taxonomy.py`. The ~60 patterns continue to output Title Case. Normalization happens at the validation boundary, not at the source.
- **LLM classification**: `classify_with_llm()` output also gets normalized at the same boundary — no change needed.

### Why Not Fix taxonomy.py Directly (Option A)?

Changing 60+ patterns in `CLASSIFICATION_PATTERNS` would:
1. Touch 440+ lines of production code
2. Risk introducing typos in regex-adjacent strings
3. Still not handle LLM classification output (which could return any casing)
4. Break if SF picklist values change casing in future releases

Option B+ (schema-based normalization) handles all sources of sub-classification values and auto-adapts if SF values change.

### Why Not Make Matching Case-Insensitive (Option C)?

E30-S4 AC4 mandates strict case-sensitive matching. Relaxing it would:
1. Contradict E30-S4's acceptance criteria
2. Mask genuinely invalid values that differ by more than case
3. Diverge from Salesforce's own restricted picklist behavior

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/validators/sf_picklist_validator.py` | MODIFY | Add `_normalize_to_sf_value()` helper; apply in `validate_acm_chain()` Chain 2 (Sub-Classification check) |
| `tests/test_sf_picklist_validator.py` | MODIFY | Add `TestSubClassificationNormalization` test class |
| `V3/output/github-issue-e30s4-audit.md` | MODIFY | Update F4 row to FIXED |

---

## Database Changes

None.

---

## API Changes

None. Validation is internal to the extraction/validation pipeline.

---

## Frontend Changes

None (backend-only story).

---

## Test Plan

### New Tests — add to `tests/test_sf_picklist_validator.py`

#### TestSubClassificationNormalization (new class)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_title_case_sub_classification_passes` | Record with `ACM_Sub_Classification__c="Flat Sheeting"` (Title Case) passes chain validation (normalized to SF's "Flat sheeting") |
| 2 | `test_multiple_title_case_types_pass` | Parametrize: "Ceiling Tiles", "Vinyl Tiles", "Ridge Capping", "Corrugated Roof Sheeting", "Clutch Plates", "Internal Lining", "Water Tanks" — all pass after normalization |
| 3 | `test_already_correct_case_passes` | "Brake pads" (already sentence case) still passes — normalization is idempotent |
| 4 | `test_acronym_values_pass` | "CAF gasket(s)", "SMF insulation" — already correct, normalization doesn't corrupt them |
| 5 | `test_truly_invalid_sub_classification_still_fails` | "TOTALLY MADE UP VALUE" still fails validation (normalization doesn't create false passes) |
| 6 | `test_controller_fields_not_normalized` | "cement products" (lowercase Classification) still fails — normalization is Sub-Classification only |
| 7 | `test_friability_still_case_sensitive` | "non-friable" (lowercase) still fails — controller normalization unchanged |
| 8 | `test_normalize_to_sf_value_helper` | Direct unit tests of `_normalize_to_sf_value()`: exact match returns original, case-insensitive match returns SF value, no match returns original |

#### Regression — existing tests

All existing E30-S4 tests must continue to pass. The normalization is additive — it converts false-positive failures into correct passes, but does not relax validation for genuinely invalid values.

### Manual Verification

After implementation, run:
```bash
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/test_sf_picklist_validator.py -v
```

Verify: zero failures, test count increased by ~8-10 tests.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Normalization creates false passes for genuinely invalid values | LOW | HIGH | `_normalize_to_sf_value()` only matches when case-insensitive lookup succeeds against actual SF schema values. Truly invalid values return unchanged and fail strict validation. |
| SF schema values change in future | LOW | LOW | Normalization uses SF schema at runtime. If SF values change, the schema bundle is updated and normalization auto-adapts. |
| Performance impact of case-insensitive lookup | NEGLIGIBLE | NONE | O(n) scan of ~30 valid values per classification group. Called once per record during validation. Sub-millisecond. |

---

## Dev Agent Record
- **Status**: Ready for Development
- **Estimated Effort**: 2 SP
- **Files to Read Before Starting**: This spec, `sf_picklist_validator.py`, `tests/test_sf_picklist_validator.py`, `V3/item-list.txt` (lines 805-1600 for SF ACM_Sub_Classification__c values)
