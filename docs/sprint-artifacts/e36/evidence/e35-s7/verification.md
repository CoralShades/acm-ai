# V7: E35-S7 — SF-First Validation (AC8)

## Verification Date: 2026-03-05

## Code Check: SF-First Validation Pipeline

**File**: `open_notebook/graphs/acm_extraction.py:2520-2568`

**Result**: PASS

The corrective RAG function implements field freezing:

1. Line 2553: `validation = validate_acm_record(record_dict)` — runs SF validation first
2. Line 2559: `frozen_fields = sf_valid_fields(record_dict)` — computes SF-valid fields to freeze
3. Lines 2562-2563: Filters issues to exclude frozen fields from correction prompt
4. Lines 2566-2568: If all issues are on frozen fields, skip LLM correction entirely
5. Lines 2571-2573: Builds `frozen_fields_display` for the correction prompt template

This ensures SF-valid field values are never modified by LLM correction.

## Code Check: SF Picklist Validator

**File**: `open_notebook/extractors/validators/sf_picklist_validator.py`

- `SalesforcePicklistValidator` validates dependent picklist chains
- Friability -> ACM_Classification -> ACM_Sub_Classification (36 valid combos)
- BuildingType -> BuildingCategory (114 -> 13 values)
- Uses runtime-loaded config from `config_loader.py`

## Unit Tests

- `test_sf_first_validation.py`: All tests PASS
- `test_sf_picklist_validator.py`: All tests PASS
- `test_acm_validator.py`: All tests PASS

Total: **315 passed, 1 skipped** across all E35-related test files.

## Verdict: PASS
