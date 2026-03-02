# Tech Spec: E30-S3 — ACM Record SF Item__c Alignment

**Story ID:** E30-S3
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-1
**Story Points:** 3
**Risk Level:** MEDIUM
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:** E30-S1 (SF Schema Config Loader) ✅ Completed

---

## User Story

As a data engineer, I want the ACMRecord domain model to support both BAR (Building Asbestos Register) field names and Salesforce Item__c API names, so that upstream extraction can write data using BAR vocabulary while downstream SF export can read data using SF field names — without breaking any existing functionality.

---

## Acceptance Criteria

| ID  | Criterion | Verification Method |
|-----|-----------|---------------------|
| AC1 | Pydantic `Field(alias=...)` added for 35+ SF Item__c field mappings | Unit test: construct ACMRecord using SF names via `model_validate(data)` |
| AC2 | Additive migration — new SF-named columns alongside existing BAR columns (no data loss) | Migration file runs idempotent; existing BAR columns untouched |
| AC3 | Missing SF fields added: `Internal_External__c`, `Labelled__c`, `ASSEA_Survey_Guide_Risk_Level__c`, `Date_Identified__c` | Unit test: new fields accept valid values, default to None |
| AC4 | `school_name` / `school_code` made optional (present in BAR, absent from SF model) | Unit test: ACMRecord validates without school_name |
| AC5 | New enum value for result field: `"Negative - Treated as Positive"` | Unit test: result validator accepts the new value |
| AC6 | Existing BAR field names continue to work (backward compatibility) | Unit test: construct ACMRecord using BAR names |
| AC7 | Unit tests verifying both BAR and SF field access patterns | Test file with ≥10 test cases covering dual-access |
| AC8 | Embedding fields preserved unchanged | Unit test: embedding fields not affected by alias changes |

---

## Technical Design

### 1. Pydantic Alias Strategy

Use Pydantic v2's `AliasChoices` with `populate_by_name=True` so both BAR and SF names work for input:

```python
from pydantic import ConfigDict, AliasChoices

class ACMRecord(ObjectModel):
    model_config = ConfigDict(populate_by_name=True)

    # Example: BAR name is "product", SF name is "Item_Name__c"
    product: str = Field(
        ...,
        validation_alias=AliasChoices("product", "Item_Name__c"),
        description="ACM product name",
    )
```

**Key design decisions:**
- `validation_alias=AliasChoices(...)` allows input from EITHER name
- `populate_by_name=True` ensures the Python attribute name (BAR) always works
- Serialization uses the Python attribute name by default (BAR names) — SF export can use `model_dump(by_alias=True)` with `serialization_alias`
- No `serialization_alias` added now — that's E33-S8's concern (SF export)

### 2. BAR → SF Field Mapping Table (35+ fields)

| # | BAR Field (Python attr) | SF API Name (alias) | Type | Notes |
|---|------------------------|---------------------|------|-------|
| 1 | `product` | `Item_Name__c` | str | Required |
| 2 | `material_description` | `Material_Description__c` | str | Required (custom SF field) |
| 3 | `building_id` | `Building_Code__c` | str | Required |
| 4 | `building_name` | `Building_Name__c` | Optional[str] | |
| 5 | `room_name` | `Room_or_Area__c` | Optional[str] | |
| 6 | `room_area` | `Room_Area__c` | Optional[float] | |
| 7 | `location` | `Location_in_Room__c` | Optional[str] | |
| 8 | `friable` | `Friability_of_Material__c` | Optional[str] | Picklist |
| 9 | `material_condition` | `Condition__c` | Optional[str] | Picklist |
| 10 | `risk_status` | `Risk_Rating__c` | Optional[str] | |
| 11 | `result` | `Sample_Analysis_Result_Material_Status__c` | str | Required, picklist |
| 12 | `extent` | `Extent__c` | Optional[str] | Custom SF field |
| 13 | `sample_no` | `NATA_Endorsed_Sample_no__c` | Optional[str] | |
| 14 | `identifying_company` | `Identifying_Hygiene_Consulting_Company__c` | Optional[str] | |
| 15 | `quantity` | `Quantity__c` | Optional[str] | SF is double, BAR is str |
| 16 | `acm_labelled` | `ACM_Labelled__c` | Optional[bool] | |
| 17 | `acm_label_details` | `Labelled_Details__c` | Optional[str] | |
| 18 | `floor_level` | `Level__c` | Optional[str] | |
| 19 | `date_of_inspection` | `Survey_Date__c` | Optional[str] | |
| 20 | `hygienist_recommendations` | `Hygienist_Recommendations__c` | Optional[str] | |
| 21 | `psb_supplied_acm_id` | `ID_provided_by_metro__c` | Optional[str] | |
| 22 | `removal_status` | `Removal_Status__c` | Optional[str] | Picklist |
| 23 | `date_of_removal` | `Removed_Date__c` | Optional[str] | |
| 24 | `quantity_removed` | `Quantity_Removed__c` | Optional[str] | |
| 25 | `removal_notification_no` | `Asbestos_Removal_Notification_No__c` | Optional[str] | |
| 26 | `epa_certificate_no` | `EPA_Waste_Transport_Certificate_No__c` | Optional[str] | |
| 27 | `no_access` | `No_Access__c` | Optional[bool] | |
| 28 | `additional_comments` | `Additional_Comments__c` | Optional[str] | |
| 29 | `disturbance_potential` | `Disturbance_Potential_of_Material__c` | Optional[str] | |
| 30 | `acm_product_group` | `ACM_Classification__c` | Optional[str] | |
| 31 | `acm_product_type` | `ACM_Sub_Classification__c` | Optional[str] | |
| 32 | `smf_present` | `SMF_Present__c` | Optional[str] | |
| 33 | `area_type` | `Internal_External__c` | Optional[str] | Existing field, new SF alias |
| 34 | `building_year` | `Building_Year__c` | Optional[int] | Custom SF field |
| 35 | `building_construction` | `Building_Construction__c` | Optional[str] | Custom SF field |
| 36 | `page_number` | `Page_Number__c` | Optional[int] | Custom SF field |
| 37 | `room_id` | `Room_ID__c` | Optional[str] | Custom SF field |

### 3. New SF Fields (AC3)

Four fields that exist in SF Item__c but are missing from the current BAR model:

```python
# Internal/External location (SF: Internal_External__c)
# Note: area_type already exists with values "Interior"/"Exterior"/"Grounds"
# SF uses "Internal"/"External" — the alias maps to area_type

# Labelled picklist (SF: Labelled__c)
# Note: acm_labelled is bool, SF Labelled__c is picklist "Yes"/"No"/"Unknown"
# Add new field alongside existing bool for SF compatibility
labelled_sf: Optional[str] = Field(
    default=None,
    validation_alias=AliasChoices("labelled_sf", "Labelled__c"),
    description="SF picklist: 'Yes', 'No', 'Unknown' (maps to acm_labelled bool)",
)

# ASSEA Survey Guide Risk Level (SF: ASSEA_Survey_Guide_Risk_Level__c)
assea_risk_level: Optional[str] = Field(
    default=None,
    validation_alias=AliasChoices("assea_risk_level", "ASSEA_Survey_Guide_Risk_Level__c"),
    description="ASSEA Survey Guide risk level (separate from BAR risk_status)",
)

# Date Identified (SF: Survey_Date__c maps here)
date_identified: Optional[str] = Field(
    default=None,
    validation_alias=AliasChoices("date_identified", "Date_Identified__c"),
    description="Date the ACM was first identified/recorded",
)
```

### 4. Make school_name Optional (AC4)

Current: `school_name: str` (required, with validator)
Change to: `school_name: Optional[str] = None`

Update the validator to allow None:
```python
@field_validator("school_name")
@classmethod
def validate_school_name(cls, v):
    if v is not None:
        v = v.strip()
        if not v:
            return None
    return v
```

### 5. New Result Enum Value (AC5)

Add `"Negative - Treated as Positive"` to `RESULT_VALUES` in `acm_schemas.py`:

```python
RESULT_VALUES = {
    "Positive",
    "Assumed Positive",
    "Negative",
    "Assumed Negative",
    "Negative - Treated as Positive",  # NEW (V3)
    "Not Sampled",
    "No Access",
    "Unknown",
}
```

### 6. Migration (Additive Only)

File: `migrations/39.surrealql`

```sql
-- Migration 39: SF Item__c alignment — additive columns (E30-S3)
-- Adds new fields only. Existing columns are NOT renamed or removed.

DEFINE FIELD IF NOT EXISTS labelled_sf       ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS assea_risk_level  ON TABLE acm_record TYPE option<string>;
DEFINE FIELD IF NOT EXISTS date_identified   ON TABLE acm_record TYPE option<string>;
```

Note: No column renames. SF aliases are handled at the Pydantic layer, not the DB layer. The DB continues to use BAR column names. Only genuinely new fields need new DB columns.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/domain/acm.py` | **Modify** | Add `model_config`, `validation_alias` to 35+ fields, make `school_name` optional, add 3 new fields |
| `open_notebook/extractors/acm_schemas.py` | **Modify** | Add `"Negative - Treated as Positive"` to `RESULT_VALUES` |
| `migrations/39.surrealql` | **Create** | Additive migration for 3 new SF fields |
| `migrations/39_down.surrealql` | **Create** | Rollback migration |
| `tests/test_acm_sf_alignment.py` | **Create** | Unit tests for dual BAR/SF field access (AC1-AC8) |

---

## Test Plan

### test_acm_sf_alignment.py

```
test_construct_with_bar_names           — AC6: BAR names work as before
test_construct_with_sf_names            — AC1: SF names work via aliases
test_construct_mixed_bar_sf             — AC1: Mix of BAR and SF names
test_school_name_optional               — AC4: No school_name is valid
test_school_name_still_works            — AC4: school_name still accepted when provided
test_result_negative_treated_positive   — AC5: New result value accepted
test_result_existing_values_unchanged   — AC5: Old result values still work
test_new_field_labelled_sf              — AC3: labelled_sf field works
test_new_field_assea_risk_level         — AC3: assea_risk_level field works
test_new_field_date_identified          — AC3: date_identified field works
test_embedding_fields_preserved         — AC8: Embedding fields unchanged
test_sf_alias_area_type                 — AC1: Internal_External__c → area_type
test_model_dump_uses_bar_names          — AC6: model_dump() returns BAR names
test_all_35_sf_aliases_resolve          — AC1: All 35+ aliases resolve correctly
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alias conflicts with existing `Field(alias=...)` | Medium | Audit all existing Field() calls — none currently use alias |
| `_prepare_save_data()` sends alias keys to DB | High | Verify `model_dump()` uses Python attr names (default behavior) |
| Existing extraction code breaks | Medium | `populate_by_name=True` ensures BAR names still work |
| Migration number collision with E30-S2 | Low | E30-S2 not yet implemented; use 39, adjust if needed |

---

## Out of Scope

- SF serialization aliases (E33-S8: SF Export)
- Building__c field alignment (E30-S2: Building Record)
- Picklist value validation against SF schema (E30-S4: Dependent Picklist Validator)
- Data migration of existing records (E30-S5)
- BAR→SF vocabulary renaming in prompts (E30-S6)

---

## Dev Agent Instructions

1. Start by modifying `open_notebook/domain/acm.py`:
   - Add `model_config = ConfigDict(populate_by_name=True)` to ACMRecord
   - Import `AliasChoices` from pydantic
   - Add `validation_alias=AliasChoices(bar_name, sf_name)` to each mapped field
   - Make `school_name` Optional with updated validator
   - Add 3 new fields: `labelled_sf`, `assea_risk_level`, `date_identified`
2. Modify `open_notebook/extractors/acm_schemas.py`:
   - Add `"Negative - Treated as Positive"` to `RESULT_VALUES`
3. Create `migrations/39.surrealql` and `migrations/39_down.surrealql`
4. Create `tests/test_acm_sf_alignment.py` with all test cases
5. Run `uv run ruff check .` and `uv run pytest tests/test_acm_sf_alignment.py -v`
6. Run full test suite: `uv run pytest` — ensure no regressions
