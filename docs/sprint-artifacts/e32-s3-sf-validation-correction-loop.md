# E32-S3: SF Validation + Correction Loop — Tech Spec

**Story ID**: E32-S3
**Story Points**: 3
**Risk**: HIGH
**Type**: Backend
**Dependencies**: E32-S2 (done), E30-S4 (done)
**Sprint**: V3-4

---

## 1. Overview

This story fills specific gaps in the SF-first validation and correction loop pipeline. The core BAR→SF corruption issue is already resolved in the current codebase (E32-S7 implemented the SF-first validation path). E32-S3 adds the missing observability fields for per-record validation state (AC6), extends the BAR-004 business rule to correctly include SF compound result values (AC5), hardens the LLM correction prompt against "Negative - Treated as Positive" corruption (AC4 robustness), and adds targeted unit tests (AC8).

The majority of ACs are already satisfied by existing code. This story requires changes to exactly 6 files.

---

## 2. Background — Architect's Key Findings

The architect's review confirmed the following are already implemented and must NOT be re-implemented:

| Component | Location | Status |
|-----------|----------|--------|
| SF-first validation path (Path A = warnings, Path B = REJECT) | `acm_validator.py::validate_acm_record()` | DONE (E32-S7) |
| `validate_all_chains()` with REJECT policy (dependency chains) | `sf_picklist_validator.py` | DONE (E30-S4) |
| `should_correct()` routing includes `"invalid_sf_enum"` | `acm_extraction.py::should_correct()` | DONE |
| `_llm_correct_records()` with max 3 retry attempts | `acm_extraction.py` | DONE |
| `SalesforcePicklistValidator.validate_flat_enums()` | `sf_picklist_validator.py` | DONE (E30-S4) |
| `deduplicate_records()` node downstream | `acm_extraction.py` | DONE (AC7) |

### What This Story Adds

1. **AC6** — Per-record validation fields: `validation_status`, `validation_errors`, `correction_attempts` are missing from both the extraction schema (`ACMExtractionRecord`) and the domain model (`ACMRecord`). These fields need to be added and written during validation and correction.

2. **AC5** — BAR-004 business rule gap: The current `positive_values` set in `validate_business_rules()` only contains `{"Positive", "Assumed Positive"}`. It is missing the SF compound values `"Positive - Non-friable"`, `"Positive - Friable"`, and needs an explicit code comment that `"Negative - Treated as Positive"` is excluded from `negative_values` because it is positive-managed (friability IS required for it).

3. **AC4 robustness** — The `correction.jinja` prompt already contains a line about "Negative - Treated as Positive" but does not explicitly state that the LLM must NOT simplify it to "Negative". The SF compound positive values `"Positive - Non-friable"` / `"Positive - Friable"` also need to be listed explicitly to prevent the LLM from simplifying them.

4. **AC8** — Four new unit tests targeting the above gaps.

---

## 3. Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC1 | Pydantic validation against SF schema on every extracted record | DONE (E32-S7 `validate_acm_record()`) |
| AC2 | Picklist validation: exact case-sensitive match via `SalesforcePicklistValidator` | DONE (E30-S4) |
| AC3 | Dependency chain enforcement: Friability→Classification→SubClassification, BuildingType→Category | DONE (E30-S4 `validate_all_chains()` REJECT policy) |
| AC4 | AI correction loop: invalid values → single-record re-extraction (max 3 retries, Claude Sonnet) | DONE + robustness gap in `correction.jinja` |
| AC5 | Business rule: Negative result → Condition = N/A (negative), Disturbance = N/A (negative); "Negative - Treated as Positive" excluded | PARTIAL — `positive_values` set missing SF compound values |
| AC6 | Validation results stored per-record: `validation_status`, `validation_errors[]`, `correction_attempts` | MISSING — fields do not exist in schema or domain model |
| AC7 | Dedup: detect and merge duplicate records from correction retries | DONE (existing `deduplicate_records` node) |
| AC8 | Unit tests for correction loop with mock AI responses | PARTIAL — 4 specific tests missing |

---

## 4. File Changes

| # | File | Change Type | Description |
|---|------|-------------|-------------|
| 1 | `open_notebook/extractors/acm_schemas.py` | EXTEND | Add 3 fields to `ACMExtractionRecord`: `validation_status`, `validation_errors`, `correction_attempts` |
| 2 | `open_notebook/domain/acm.py` | EXTEND | Add same 3 fields to `ACMRecord` in the extraction metadata section (after `data_issues`) |
| 3 | `open_notebook/extractors/validators/acm_validator.py` | EXTEND | Extend `positive_values` set in `validate_business_rules()` to include SF compound values + add AC5 comment |
| 4 | `open_notebook/graphs/acm_extraction.py` | EXTEND | Write `validation_status` / `validation_errors` in `validate_records_strict()`; write `correction_attempts` in `_llm_correct_records()` |
| 5 | `prompts/acm/correction.jinja` | UPDATE | Extend "Common mappings" section with explicit SF compound value guidance |
| 6 | `tests/test_acm_validator.py` | ADD | 4 new unit tests in a new `TestE32S3Gaps` class |

---

## 5. Implementation Details

### 5.1 File 1: `open_notebook/extractors/acm_schemas.py`

Add three fields to `ACMExtractionRecord` after the existing `data_issues` field (after line 389, before the `coerce_data_issues` validator). These fields live in the "Extraction metadata" block.

```python
# Validation tracking (AC6 — E32-S3)
validation_status: Optional[str] = Field(
    default=None,
    description=(
        "Validation outcome: 'valid', 'corrected', 'failed_correction', 'invalid'. "
        "Set by validate_records_strict() and updated after each correction attempt."
    ),
)
validation_errors: List[str] = Field(
    default_factory=list,
    description=(
        "List of validation error strings from the last validation run. "
        "Format: '<field_name>: <issue_type> (current=<value>)'. "
        "Cleared and rewritten on each validation pass."
    ),
)
correction_attempts: int = Field(
    default=0,
    description=(
        "Number of LLM correction attempts made for this record. "
        "Incremented by _llm_correct_records() on each attempt. Max 3."
    ),
)
```

Placement: insert these three fields immediately after `data_issues` (after line 389 in the current file), before the `coerce_data_issues` validator method.

### 5.2 File 2: `open_notebook/domain/acm.py`

Add the same three fields to `ACMRecord` in the extraction metadata section, immediately after the existing `data_issues` field (around line 332):

```python
# Validation tracking (AC6 — E32-S3)
validation_status: Optional[str] = Field(
    default=None,
    description=(
        "Validation outcome: 'valid', 'corrected', 'failed_correction', 'invalid'. "
        "Populated during extraction pipeline."
    ),
)
validation_errors: Optional[List[str]] = Field(
    default=None,
    description="Validation error strings from final validation pass.",
)
correction_attempts: Optional[int] = Field(
    default=None,
    description="Number of LLM correction attempts made for this record (max 3).",
)
```

Note: In `ACMRecord` these fields are `Optional` with `None` defaults (matching the pattern of `data_issues` and `extraction_confidence` in that model). No `AliasChoices` needed — these are pipeline-internal fields not mapped to Salesforce.

### 5.3 File 3: `open_notebook/extractors/validators/acm_validator.py`

**Target function**: `validate_business_rules()` — the `positive_values` set at line 267.

Current code:
```python
# BAR-004: Positive results require friability
positive_values = {"Positive", "Assumed Positive"}
```

Replace with:
```python
# BAR-004: Positive results require friability populated.
# Includes SF compound values that are positive-managed.
# NOTE: "Negative - Treated as Positive" is intentionally excluded from
# negative_values above — it is positive-managed and friability IS required
# for these records (same as "Positive"/"Assumed Positive").
positive_values = {
    "Positive",
    "Assumed Positive",
    "Positive - Non-friable",   # SF compound value (AC5)
    "Positive - Friable",       # SF compound value (AC5)
    "Negative - Treated as Positive",  # Positive-managed despite negative analytical result
}
```

No other changes to this file.

### 5.4 File 4: `open_notebook/graphs/acm_extraction.py`

Two locations require changes.

**Location A: `validate_records_strict()`** — after the call to `validate_acm_record()` (around line 2152), write `validation_status` and `validation_errors` onto the record.

In the existing block that handles `validation.is_valid`:

```python
# Run strict enum + business rule validation
record_dict = { ... }
validation = validate_acm_record(record_dict)
correction_stats["total_validated"] = (
    correction_stats.get("total_validated", 0) + 1
)

# AC6: Write validation fields to record
if validation.is_valid:
    record.validation_status = "valid"
    record.validation_errors = []
else:
    record.validation_status = "invalid"
    record.validation_errors = [
        f"{vi.field_name}: {vi.issue_type} (current={vi.current_value!r})"
        for vi in validation.issues
    ]
    # Track issues on the record for potential correction (existing code)
    for vi in validation.issues:
        ...
```

The `validation_status = "valid"` branch is new. The `validation_status = "invalid"` + `validation_errors` block replaces / extends the existing `if not validation.is_valid:` block — the existing `data_issues.append(...)` call remains untouched below it.

**Location B: `_llm_correct_records()`** — increment `correction_attempts` on the record after each LLM call attempt (successful or not). In the per-record loop body, after `corrected = json.loads(text)` succeeds, add:

```python
# AC6: Track correction attempts on record
record.correction_attempts = getattr(record, "correction_attempts", 0) + 1
```

Also add the same increment in the `except Exception` branch so failed attempts are counted:

```python
except Exception as e:
    logger.warning(f"LLM correction failed for record {idx}: {e}")
    correction_stats["failed"] = correction_stats.get("failed", 0) + 1
    record.correction_attempts = getattr(record, "correction_attempts", 0) + 1  # AC6
```

Additionally, after a successful correction, update `validation_status` to reflect the corrected state. In `validate_records_strict()`, at the start of each pass (not just attempt 0), records that were previously `"invalid"` will be re-validated. The status will update naturally to `"valid"` if corrections succeed, or remain `"invalid"` after max retries. No additional logic is needed here — the `validate_records_strict()` rewrite on each loop pass handles it.

For records that exhaust all correction attempts and remain invalid, the final pass of `validate_records_strict()` will write `validation_status = "invalid"` and their `validation_errors` will reflect the final state. This is correct behaviour.

### 5.5 File 5: `prompts/acm/correction.jinja`

The current "Common mappings" section ends at:

```
- For negative results: Condition and Disturbance Potential should be "N/A (negative)"
```

Extend it with:

```
- "Negative - Treated as Positive" is a VALID SF value — do NOT simplify it to "Negative". These records are positive-managed and require Friability to be populated.
- "Positive - Non-friable" is a VALID SF value — do NOT simplify it to "Positive". It means the result is positive AND the material is non-friable.
- "Positive - Friable" is a VALID SF value — do NOT simplify it to "Positive". It means the result is positive AND the material is friable.
- If a record has result "Positive - Non-friable", the friable field must be "Non-friable"
- If a record has result "Positive - Friable", the friable field must be "Friable"
```

The full updated "Common mappings" section will be:

```
**Common mappings:**
- "Bonded" → "Non-friable"
- "Medium" → "Moderate" (Salesforce uses "Moderate" not "Medium")
- "Detected" → "Positive"
- "Not Detected" / "NAD" → "Negative"
- "Negative - Treated as Positive" is a VALID SF value — do NOT simplify it to "Negative". These records are positive-managed and require Friability to be populated.
- "Positive - Non-friable" is a VALID SF value — do NOT simplify it to "Positive". It means the result is positive AND the material is non-friable.
- "Positive - Friable" is a VALID SF value — do NOT simplify it to "Positive". It means the result is positive AND the material is friable.
- If a record has result "Positive - Non-friable", the friable field must be "Non-friable"
- If a record has result "Positive - Friable", the friable field must be "Friable"
- For negative results: Condition and Disturbance Potential should be "N/A (negative)"
```

### 5.6 File 6: `tests/test_acm_validator.py`

Add a new test class `TestE32S3Gaps` at the end of the file. Four tests are required:

**Test 1: BAR-004 includes SF compound positive values**

Verifies that `"Positive - Non-friable"` and `"Positive - Friable"` trigger the friability requirement when `friable` is `None`.

```python
class TestE32S3Gaps:
    """E32-S3 gap tests: AC5 BAR-004 compound values and AC6 validation fields."""

    def test_bar004_positive_non_friable_requires_friability(self):
        """'Positive - Non-friable' as sample_result should flag empty friable (BAR-004)."""
        record = {
            "sample_result": "Positive - Non-friable",
            "friable": None,
        }
        issues = validate_business_rules(record)
        friability_issues = [i for i in issues if i.field_name == "friable"]
        assert len(friability_issues) == 1

    def test_bar004_positive_friable_requires_friability(self):
        """'Positive - Friable' as sample_result should flag empty friable (BAR-004)."""
        record = {
            "sample_result": "Positive - Friable",
            "friable": None,
        }
        issues = validate_business_rules(record)
        friability_issues = [i for i in issues if i.field_name == "friable"]
        assert len(friability_issues) == 1
```

**Test 2: "Negative - Treated as Positive" requires friability (BAR-004)**

Verifies it is NOT in `negative_values` (so it does NOT trigger the N/A rule) but IS in `positive_values` (so it DOES trigger the friability rule).

```python
    def test_bar004_negative_treated_as_positive_requires_friability(self):
        """'Negative - Treated as Positive' should be treated as positive — friability required."""
        record = {
            "sample_result": "Negative - Treated as Positive",
            "friable": None,
            "material_condition": "Stable",
            "disturbance_potential": "Low",
        }
        issues = validate_business_rules(record)
        # Must NOT trigger N/A rule (it's not a true negative)
        na_issues = [
            i for i in issues
            if i.field_name in ("material_condition", "disturbance_potential")
        ]
        assert len(na_issues) == 0
        # Must trigger friability rule (positive-managed)
        friability_issues = [i for i in issues if i.field_name == "friable"]
        assert len(friability_issues) == 1

    def test_bar004_negative_treated_as_positive_with_friable_passes(self):
        """'Negative - Treated as Positive' with friable populated should pass BAR-004."""
        record = {
            "sample_result": "Negative - Treated as Positive",
            "friable": "Non-friable",
            "material_condition": "Stable",
            "disturbance_potential": "Low",
        }
        issues = validate_business_rules(record)
        assert len(issues) == 0
```

These four tests can be imported with the existing import block at the top of `test_acm_validator.py` — `validate_business_rules` is already imported.

---

## 6. Test Plan

### New Tests (AC8)

| Test | Class | Covers |
|------|-------|--------|
| `test_bar004_positive_non_friable_requires_friability` | `TestE32S3Gaps` | AC5: SF compound value "Positive - Non-friable" triggers BAR-004 |
| `test_bar004_positive_friable_requires_friability` | `TestE32S3Gaps` | AC5: SF compound value "Positive - Friable" triggers BAR-004 |
| `test_bar004_negative_treated_as_positive_requires_friability` | `TestE32S3Gaps` | AC5: "Negative - Treated as Positive" not in negative_values, IS in positive_values |
| `test_bar004_negative_treated_as_positive_with_friable_passes` | `TestE32S3Gaps` | AC5: Passes when friable is populated |

### Regression Coverage (Existing Tests That Must Remain Green)

| Test Class | Covers |
|------------|--------|
| `TestValidateBusinessRules` | All 6 existing BAR rule tests — must pass with extended `positive_values` |
| `TestSFFirstValidation` | `test_negative_treated_as_positive_passes_sf_validation`, `test_negative_treated_as_positive_is_not_corrected` — must still pass |
| `TestCorrectiveLoopRouter` | All 5 loop routing tests — unaffected by field additions |
| `TestCorrectionPromptTemplate` | Existing 2 template render tests — must pass after `correction.jinja` update |

### Verification Command

```bash
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/test_acm_validator.py -v
```

All tests in `test_acm_validator.py` must pass. No new test file is required — the new class is added to the existing file.

---

## 7. Data Flow Notes

### AC6 Field Lifecycle

```
validate_records_strict() [first pass, attempt=0]
  → record.validation_status = "valid" | "invalid"
  → record.validation_errors = [] | ["field: issue_type (current='val')", ...]

correct_records() [Layer 1 auto + Layer 2 LLM]
  → _llm_correct_records()
      → record.correction_attempts += 1  (per LLM call attempt)

validate_records_strict() [second pass, attempt=1]
  → record.validation_status overwrites to "valid" if corrections succeeded

[after max_correction_attempts]
  → record.validation_status = "invalid" (final state for uncorrectable records)
  → record.validation_errors reflects remaining issues
```

The `validation_status` field uses these string values:
- `"valid"` — passed all validation checks
- `"invalid"` — failed validation, either during loop or after max retries
- The value `"corrected"` is NOT used in this story (correction success is implicitly `"valid"` on the next pass)

### ACMRecord Persistence

The three new fields on `ACMRecord` are stored in SurrealDB as part of the record document. No migration is required — SurrealDB is schemaless for these document-level fields. The fields default to `None` so existing stored records are unaffected.

---

## 8. Risk Notes

**Risk: HIGH** — This story modifies `validate_business_rules()` which is in the hot path for every extracted record. The `positive_values` set change must not break existing tests for `"Positive"` and `"Assumed Positive"`. The new values are additive, not replacements.

**Risk: BAR-004 false positives** — If the SF schema contains `"Positive - Non-friable"` as a `sample_result` picklist value, this change correctly enforces that friability must be populated. If that field does not exist in the SF schema (i.e., the extracted value itself is invalid), the SF flat enum validator will catch it first and send it to the correction loop before BAR-004 is evaluated. No double-counting occurs.

**Risk: `correction_attempts` increment** — The increment is guarded by `getattr(record, "correction_attempts", 0)` as a fallback in case the field is not yet set on a record constructed before this story (e.g., from a cached state). This is defensive but safe.

---

## 9. Definition of Done

- [ ] All 6 files changed as specified
- [ ] `validation_status`, `validation_errors`, `correction_attempts` fields present in `ACMExtractionRecord` and `ACMRecord`
- [ ] `validate_records_strict()` writes `validation_status` and `validation_errors` on every record per pass
- [ ] `_llm_correct_records()` increments `correction_attempts` on every attempt (success and failure)
- [ ] `positive_values` in `validate_business_rules()` includes SF compound values and "Negative - Treated as Positive"
- [ ] `correction.jinja` prompt explicitly warns against simplifying compound SF values
- [ ] 4 new tests in `TestE32S3Gaps` added to `tests/test_acm_validator.py`
- [ ] `uv run pytest tests/test_acm_validator.py -v` passes with zero failures
- [ ] `uv run ruff check open_notebook/extractors/acm_schemas.py open_notebook/domain/acm.py open_notebook/extractors/validators/acm_validator.py open_notebook/graphs/acm_extraction.py` passes clean
