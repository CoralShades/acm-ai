# Story E2-S11: BAR Field Type Safety

**Epic:** E2 — AG Grid Spreadsheet Integration
**Priority:** P0
**Status:** done
**Sprint:** Post-PR-30 hardening

---

## User Story

**As a** developer maintaining the ACM extraction pipeline,
**I want to** strengthen type safety for BAR field values across the schema, API models, and frontend form inputs,
**So that** invalid data is caught at the boundary (extraction, API, UI edit) rather than silently stored with wrong types or out-of-range values.

---

## Background

PR #30 (Feb 2026) added BAR Pydantic schema changes to fix the E2E gap sprint. That work partially covers this story by introducing stricter field definitions in the extraction schema. Before implementing, review what PR #30 already changed in:
- `open_notebook/extractors/acm_schemas.py` — `ACMExtractionRecord` schema
- `open_notebook/domain/acm.py` — `ACMRecord` domain model
- `api/models.py` — `ACMRecordResponse`, `ACMRecordCreateRequest`, `ACMRecordUpdateRequest`

**Do not duplicate or conflict with PR #30 changes.** Identify the remaining gaps after that work.

### Current State (as of sprint status 2026-02-20)

Key observations from reading the existing code:

- `quantity` is typed as `Optional[str]` in both `ACMExtractionRecord` (acm_schemas.py) and `ACMRecordResponse` (api/models.py) — no numeric validation enforced
- `acm_labelled` is `Optional[bool]` in domain model and extraction schema, but the BAR specification uses Y/N/NA string enum — the boolean representation may not survive the full round-trip correctly
- `result` is a plain `str` with documentation saying "use BAR vocabulary: Positive, Assumed Positive, Negative, Assumed Negative, Unknown" but no Pydantic enum enforces this
- `friable` is `Optional[str]` accepting any value; expected values are "Friable" or "Non Friable"
- `risk_status` is `Optional[str]`; expected values are "Low", "Medium", "High"
- `material_condition` is `Optional[str]`; expected values are "Good", "Fair", "Poor", "Damaged"
- `area_type` uses `str = Field(default="Interior")` with expected values "Interior", "Exterior", "Grounds" but no enum
- Frontend ACM record edit form uses generic text inputs for all these fields

---

## Acceptance Criteria

- [ ] **Schema enums defined** — Create Python enums (or `Literal` types) for constrained BAR fields:
  - `ResultEnum`: `Positive | Assumed Positive | Negative | Assumed Negative | Unknown`
  - `FriableEnum`: `Friable | Non Friable`
  - `RiskStatusEnum`: `Low | Medium | High`
  - `MaterialConditionEnum`: `Good | Fair | Poor | Damaged`
  - `AreaTypeEnum`: `Interior | Exterior | Grounds`
- [ ] **Quantity validator added** — `quantity` field: if numeric component is present, value must be >= 0; unit string is allowed (e.g., "10 m²", "5 linear meters"); reject negative numeric quantities
- [ ] **Labelled field alignment** — Reconcile `acm_labelled: Optional[bool]` in domain model with BAR's Y/N/NA string; document the mapping; ensure API response renders correctly
- [ ] **Pydantic `field_validator`s** applied in `ACMExtractionRecord` (acm_schemas.py) for:
  - `result` — validate against `ResultEnum` values (case-insensitive, strip whitespace)
  - `friable` — validate against `FriableEnum` values
  - `risk_status` — validate against `RiskStatusEnum` values
  - `material_condition` — validate against `MaterialConditionEnum` values
- [ ] **API model updated** — `ACMRecordResponse`, `ACMRecordCreateRequest`, and `ACMRecordUpdateRequest` in `api/models.py` use the same enums or `Optional[Literal[...]]` types for constrained fields
- [ ] **Invalid values rejected at API** — `PUT /api/acm/{id}` with an invalid `result` value (e.g., `"maybe"`) returns HTTP 422 with a clear error message identifying the field and allowed values
- [ ] **Frontend form inputs updated** — ACM record edit form uses type-appropriate controls:
  - `result` → select/radio with enum options
  - `friable` → select/radio with enum options
  - `risk_status` → select/radio with enum options
  - `material_condition` → select/radio with enum options
  - `area_type` → select with enum options
  - `quantity` → number input (or text input with pattern validation)
- [ ] **Backward compatibility** — Records already in the database with non-conforming values are not broken; validators use `mode="before"` with normalization where possible (e.g., strip whitespace, title-case) before enforcing
- [ ] **Tests pass** — `uv run pytest` passes after changes; add at least one test per new validator

---

## Technical Notes

### Files to Modify

| File | Change |
|------|--------|
| `open_notebook/extractors/acm_schemas.py` | Add `field_validator`s to `ACMExtractionRecord`; define enum constants |
| `open_notebook/domain/acm.py` | Align field types with enums; add domain-level validators |
| `api/models.py` | Update `ACMRecordResponse`, `ACMRecordCreateRequest`, `ACMRecordUpdateRequest` with typed enums |
| `frontend/src/components/acm/ACMRecordEditForm.tsx` (or equivalent edit form) | Replace text inputs with select/radio for enum fields; number input for quantity |

### Pydantic Validator Pattern

Use `field_validator` with `mode="before"` for normalization + validation:

```python
from pydantic import field_validator

@field_validator("result", mode="before")
@classmethod
def validate_result(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    normalized = v.strip().title()
    allowed = {"Positive", "Assumed Positive", "Negative", "Assumed Negative", "Unknown"}
    if normalized not in allowed:
        raise ValueError(f"result must be one of {sorted(allowed)}, got '{v}'")
    return normalized
```

### Quantity Validator Pattern

`quantity` stores a human-readable string with units (e.g., "10 m²"). A simple numeric guard:

```python
import re

@field_validator("quantity", mode="before")
@classmethod
def validate_quantity(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    # Extract leading numeric part if present
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)", str(v))
    if match:
        numeric = float(match.group(1))
        if numeric < 0:
            raise ValueError(f"quantity cannot be negative, got '{v}'")
    return v
```

### acm_labelled Alignment

The current `ACMExtractionRecord.acm_labelled: Optional[bool]` maps to the BAR field that shows Y/N/NA. Recommended approach:
- Keep `bool` in the extraction schema (the LLM outputs True/False naturally)
- In `ACMRecordResponse` (API layer), expose as `Optional[str]` with values "Y" / "N" / None, converting in the response serializer or adding a `@computed_field`
- In the edit form, show as a 3-option control: YES / NO / Not Assessed

Alternatively, if PR #30 already changed this, align with that decision.

### Frontend Select Component

Use Radix UI `Select` or a simple `<select>` with the allowed values. Example for `result`:

```tsx
const RESULT_OPTIONS = [
  "Positive",
  "Assumed Positive",
  "Negative",
  "Assumed Negative",
  "Unknown",
] as const;

// In form:
<Select value={field.value} onValueChange={field.onChange}>
  <SelectTrigger />
  <SelectContent>
    {RESULT_OPTIONS.map((opt) => (
      <SelectItem key={opt} value={opt}>{opt}</SelectItem>
    ))}
  </SelectContent>
</Select>
```

---

## Dependencies

- **Requires:** E2-S1 (done), E2-S2 (done)
- **Partially covered by:** PR #30 (Feb 2026) BAR Pydantic schema changes — review before implementing
- **Blocks:** None directly; improves data quality for all downstream features

---

## Implementation Note

Review the full diff of PR #30 before writing any new code. The BAR Pydantic schema work in that PR may have already added some of the validators or typed fields described here. Only implement what remains incomplete. Document in the Dev Agent Record which specific gaps PR #30 left open.

---

## Estimated Effort

M (Medium) — Backend validators are straightforward Pydantic patterns. Frontend input type changes require touching the edit form component and ensuring type-safe option lists. The main complexity is auditing PR #30 first to avoid duplication.

---

## Dev Agent Record

_To be filled in during implementation._

### Agent Model Used

_TBD_

### Completion Notes

_TBD_

### File List

_TBD_
