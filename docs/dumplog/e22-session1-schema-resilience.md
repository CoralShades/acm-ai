You are implementing E22-S1: Schema Resilience — Normalize Instead of Reject.
You are Amelia (Developer). This is a backend-only fix.

## MANDATORY PRE-READ — Read ALL before writing ANY code

### Your story:
- docs/sprint-artifacts/e22-s1-schema-resilience.md

### Schema and validator files (THE CODE YOU'RE FIXING):
- open_notebook/extractors/acm_schemas.py — find ALL field_validators
- open_notebook/extractors/validators/acm_validator.py — find enum validation logic
- open_notebook/extractors/normalizers/enums.py — find existing synonym mappings

### Related completed stories (understand the design intent):
- docs/sprint-artifacts/e2-s11-bar-field-type-safety.md
- docs/sprint-artifacts/e1-s15-corrective-rag-validation-loop.md
- docs/sprint-artifacts/e1-s12-consultant-wording-normalization.md

### Enum reference:
- docs/samplePDF/instructions-sample/register_enums.json

### Current sprint state:
- docs/sprint-artifacts/sprint-status.yaml

## THE BUG

From extraction logs (Clutch Alexander District Hospital PDF):

```
Building Main Hospital Building schema-error fallback JSON parsing failed:
  1 validation error for ACMExtractionResult
  records.12.risk_status
    Value error, risk_status must be one of ['High', 'Low', 'Medium'],
    got 'Moderate' [type=value_error]
```

The LLM generates `risk_status: "Moderate"` but the Pydantic field_validator
only accepts `['High', 'Low', 'Medium']`. This causes the ENTIRE building's
records to be rejected — ALL records for Main Hospital Building are lost.

Note: The DISTURBANCE_SYNONYMS in enums.py already maps "medium" → "Moderate"
because BAR uses "Moderate" for disturbance_potential. But risk_status is a
DIFFERENT field — its valid values are High/Medium/Low, not High/Moderate/Low.
The LLM conflates the two.

There's also a provider schema/compat error for VMO Accommodations building:
```
Provider schema/compat error detected (Error code: 400 - compiled grammar is too large)
Falling back to direct invocation with manual JSON parsing.
```
This fallback path is MORE likely to produce non-standard enum values because
it doesn't have structured output constraints.

## FIX APPROACH

**Principle: Validators should NORMALIZE, not REJECT.** The LLM is not deterministic.
Strict rejection loses data. Normalization preserves data with a logged note.

### Task 1: Fix risk_status validator in acm_schemas.py

Find the risk_status field_validator. Change it from reject to normalize:

```python
RISK_STATUS_SYNONYMS = {
    "high": "High", "h": "High",
    "medium": "Medium", "med": "Medium", "m": "Medium",
    "moderate": "Medium",  # LLM conflates with disturbance_potential
    "low": "Low", "l": "Low",
    "none": None, "n/a": None, "na": None, "unknown": None, "-": None,
}

@field_validator("risk_status", mode="before")
@classmethod
def validate_risk_status(cls, v):
    if v is None:
        return v
    lookup = str(v).strip().lower()
    if lookup in RISK_STATUS_SYNONYMS:
        return RISK_STATUS_SYNONYMS[lookup]
    # Pass through unknown values rather than rejecting entire record
    logger.warning(f"Unknown risk_status value: '{v}' — passing through")
    return v
```

### Task 2: Audit ALL field_validators in ACMExtractionRecord

Read EVERY field_validator in acm_schemas.py. For each one, check:
1. Does it raise ValueError on unexpected input?
2. If yes → change to normalize-or-passthrough pattern (like Task 1)
3. Log unexpected values as warnings, don't raise

Fields to check: result, friable, material_condition, risk_status,
disturbance_potential, area_type, acm_labelled, and any others with validators.

### Task 3: Audit acm_validator.py enum validation

In the validators module, check if validate_enum_fields() raises errors
that could kill entire batches. If it does, change to:
- Attempt normalization using existing synonym maps in enums.py
- If normalization fails, add to data_issues list instead of raising
- Never reject an entire record for a single field mismatch

### Task 4: Check for List fields without defaults

Scan ACMExtractionRecord for any field like:
```python
some_field: List[str]  # No default — will fail if LLM returns null
```

If found, add `= Field(default_factory=list)` — this was the data_issues
bug from Phase 3B. Make sure it's not hiding elsewhere.

### Task 5: Add RISK_STATUS_SYNONYMS to enums.py

In `open_notebook/extractors/normalizers/enums.py`, add a risk_status
synonym dict alongside the existing DISTURBANCE_SYNONYMS, CONDITION_SYNONYMS, etc.
Update `normalize_enum_value()` to handle the `risk_status` field.

### Task 6: Verification

```bash
# Lint
uv run ruff check open_notebook/extractors/acm_schemas.py
uv run ruff check open_notebook/extractors/validators/
uv run ruff check open_notebook/extractors/normalizers/

# Tests — ALL must pass
uv run pytest tests/ -k "schema or validator or extraction or normaliz" -v --tb=short 2>&1 | tail -60

# Full suite
uv run pytest tests/ --tb=short 2>&1 | tail -20
```

### Task 7: Update BMAD Artifacts

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
e22-s1-schema-resilience: done  # 2026-02-26: Resilient validators — normalize instead of reject. risk_status Moderate→Medium, all validators audited.
```

### Task 8: Git Commit

```bash
git add open_notebook/ tests/ docs/
git commit -m "fix(e22-s1): resilient schema validators — normalize instead of reject

- risk_status: 'Moderate' → 'Medium' (LLM conflates with disturbance)
- All field_validators changed to normalize-or-passthrough pattern
- No validator raises ValueError on unexpected-but-close values
- Unknown values logged as warnings, added to data_issues
- Added RISK_STATUS_SYNONYMS to enums.py
- Prevents entire building loss from single field mismatch"
```

## GUARD RAILS
- Do NOT modify frontend files
- Do NOT change the extraction pipeline graph logic (only schema/validators)
- Do NOT change LLM prompts
- Do NOT change the corrective loop logic (E1-S15) — only change what validators do when they find mismatches
- REUSE existing normalize_enum_value() patterns from enums.py
