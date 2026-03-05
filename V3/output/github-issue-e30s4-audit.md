## Summary

`docs/samplePDF/instructions-sample/` files are **loaded at runtime** by production code — they are NOT documentation. Mismatches between these files and Salesforce picklist values will cause silent validation failures, missed records, and SF import errors.

Discovered during E30-S4 audit (2026-03-03). Full findings in `V3/prompts/findings.md` (second section).

---

## Post-Implementation Status (E30-S4 + E30-S6 Completed)

> **Updated:** 2026-03-03 — after E30-S4 and E30-S6 shipped.

| Finding | Severity | Status | Resolution |
|---------|----------|--------|------------|
| F1: "Good"→"Stable" | FIXED | ✅ Resolved | register_enums.json + enums.py both use "Stable" |
| F2: Dual validation path | HIGH | ⚠️ Partially addressed | sf_picklist_validator.py has `_BAR_TO_SF_VALUE` normalization + WARN policy. "Not Sampled"/"No Access" BAR→SF mapping not yet explicit. |
| F3: 4 missing SF groups | HIGH | ⚠️ Partially addressed | T-prefix stripped at runtime via `_strip_t_prefix()`. 4 taxonomy groups (Textiles-NF, Bitumen-f, Coatings-f, Plastics-f) still absent from JSONs. SF schema is authoritative via E30-S4. |
| **F4: Product type casing** | **HIGH** | **✅ FIXED — E32-S4** | `_normalize_to_sf_value()` added to `sf_picklist_validator.py`; applied in Chain 2 (Sub-Classification only). Case-insensitive lookup normalizes taxonomy Title Case output to SF-canonical casing at validation boundary. |
| F5: primary_classification rotated | MEDIUM | ⚠️ Not addressed | No code comment gate. Current code is safe (uses `product_group_header`). |
| F6: Missing consultant action | LOW | ❌ Not fixed | Low priority — fallback handles it. |
| F7: No BAR enum for ACM fields | MEDIUM | ✅ Mitigated | SF schema (E30-S4) is now the authoritative source for ACM chain validation. |
| F8: SpecificUses gap | LOW | ✅ Deferred | Correct — out of scope. |

### F4 Resolved: E32-S4

**Fixed in E32-S4:** `_normalize_to_sf_value()` helper added to `sf_picklist_validator.py`.
Applied in Chain 2 (Classification → SubClassification) only. Uses case-insensitive lookup
to map taxonomy Title Case output to SF-canonical casing at the validation boundary.
Controller fields (Friability, Classification, Building Type) remain strict case-sensitive.

---

## Affected Runtime Consumers

| File | Loaded By | How Used |
|------|-----------|----------|
| `register_enums.json` | `config_loader.py` → `acm_validator.py:75` | Authoritative enum values for `validate_enum_fields()` |
| `register_row.schema.json` | `config_loader.py` | Field definitions, required fields, column mappings |
| `register_taxonomy.nonfriable.json` | `taxonomy.py:64` | Product group/type lookup for `classify_product()` |
| `register_taxonomy.friable.json` | `taxonomy.py:71` | Same |
| `consultant_wording_rules.json` | `recommendations.py:86` | Hygienist action regex patterns |

---

## F1: FIXED — Condition "Good" -> "Stable"

User already fixed `register_enums.json`. `enums.py` line 33 already had `"good": "Stable"`. No action needed.

---

## F2: HIGH — Dual Validation Path Creates Divergence Risk

Two independent enum validation paths that can contradict each other:

- Path A (current): record -> enums.py normalizer -> acm_validator.validate_enum_fields() -> register_enums.json (BAR values)
- Path B (E30-S4): record -> sf_picklist_validator.validate_acm_chain() -> SFSchemaBundle.dependencies (SF values)

Live conflicts:

| Field | register_enums.json | SF picklist | Conflict |
|-------|---------------------|-------------|---------|
| Sample Result | "Not Sampled" | (absent) | FAIL — passes BAR, rejected by SF |
| Sample Result | "No Access" | (absent) | FAIL — same |
| Sample Result | (absent) | "Negative - Treated as Positive" | SF value has no BAR equivalent |
| YesNo | "YES" / "NO" | "Yes" / "No" | Case mismatch — affects Labelled__c, Public_Access__c |

**Post-S4 status:** sf_picklist_validator.py has `_BAR_TO_SF_VALUE` mapping for `"Non Friable"→"Non-friable"`. WARN policy surfaces conflicts as `chain_warnings` (non-blocking). Full precedence rule (SF wins for export) not yet codified.

---

## F3: HIGH — Taxonomy JSONs Missing 4 Salesforce ACM_Classification Groups

These groups exist in Salesforce `ACM_Classification__c` but are absent from the taxonomy JSON files loaded by `taxonomy.py`:

| Missing SF Group | Runtime Impact |
|-----------------|----------------|
| Textiles (non-friable) | get_product_types("Textiles") returns [] |
| Bitumen products (f) | get_product_groups("Friable") misses this group |
| Coatings (f) | Same |
| Reinforced plastics/resins (excluding bitumen products) (f) | Same |

Also: `classify_product()` hardcodes Textiles as Friable-only (lines 524-527 of taxonomy.py). Non-friable textile items will be misclassified.

**Post-S6 status:** `_strip_t_prefix()` strips T-codes at runtime. SF schema from `load_sf_field_schema()` is now authoritative for chain validation. But `classify_product()` still won't classify items into the 4 missing groups correctly.

---

## F4: HIGH — Product Type Casing Mismatch: Title Case vs SF Sentence Case

**STATUS: NOT FIXED — New story required.**

`CLASSIFICATION_PATTERNS` in `taxonomy.py` (lines 139-579) outputs Title Case. Salesforce `ACM_Sub_Classification__c` uses sentence case. E30-S4 AC4 says "Strict case-sensitive matching" — every entry below will fail:

| classify_product() output | SF ACM_Sub_Classification__c | Match |
|---------------------------|-------------------------------|-------|
| "Flat Sheeting" | "Flat sheeting" | FAIL |
| "Corrugated Roof Sheeting" | "Corrugated roof sheeting" | FAIL |
| "Ceiling Tiles" | "Ceiling tiles" | FAIL |
| "Vinyl Tiles" | "Vinyl tiles" | FAIL |
| "Ridge Capping" | "Ridge capping" | FAIL |
| "Clutch Plates" | "Clutch plates" | FAIL |
| "Brake pads" | "Brake pads" | OK |

**Required action (choose one):**
- (a) Fix all CLASSIFICATION_PATTERNS to use SF-exact casing
- **(b) Add case-normalization step in sf_picklist_validator.py between classification and chain validation (RECOMMENDED — lowest risk)**
- (c) Make chain validation case-insensitive (contradicts AC4)

---

## F5: MEDIUM — Taxonomy JSON primary_classification Field Is Rotated

Both taxonomy JSONs have `primary_classification` shifted by one position (data entry bug):

| pc_code | primary_classification (WRONG) | product_group_header (CORRECT) |
|---------|-------------------------------|-------------------------------|
| T1 nonfriable | "Bitumen products" | "T1 Cement products" |
| T2 nonfriable | "Cement products" | "T2 Bitumen products" |
| T2 friable | "Gasket products (f)" | "T2 Vinyl products" |

Current `taxonomy.py:128` is safe — uses `product_group_header`. Any new E30-S4 code reading `primary_classification` will get wrong group names.

**Required action:** Never use `primary_classification`. Use `product_group_header` or SF schema.

---

## F6: LOW — consultant_wording_rules.json Missing leave_undisturbed_and_manage

File has 6 canonical actions; code has 7. `leave_undisturbed_and_manage` is hardcoded in `recommendations.py:DEFAULT_PATTERNS` but absent from JSON. No E30-S4 impact — fallback handles it.

---

## F7: MEDIUM — BAR Schema Has No Enum Constraint on ACM Fields

`register_row.schema.json` columns AA (ACM Product Group) and AC (ACM Product Type) are plain `string|null` — no enum list. `config_loader.py` provides zero validation for these fields.

**Post-S4 status:** SF schema (E30-S4 `SalesforcePicklistValidator`) is now the sole source of truth for ACM classification chain validation. This finding is mitigated.

---

## F8: LOW — 16 SpecificUses Values Not in SF Item_Name__c

register_enums.json SpecificUses has ~320 values; SF Item_Name__c has 294. These 16 values exist in BAR enum but NOT in Salesforce (will fail SF import if extracted):

Above door, Adj to Heating Coils, Backing panel box lining, Electrical cabinet, Electrical cabinet door lining, Furnace door seal, Manhole cover, Motor room - Debris on floor, Old electrical cables, On floor, On ground, On shelf, Settled on surfaces, Strapping (Walls/ceiling etc.), Strapping to eave lining, Suspect Cement Sheet

Not in E30-S4 scope. Will need fallback (map to "Other") when Item_Name__c validation is added.

---

## Picklist Dependency Chains (Reference)

Full mappings in `V3/output/picklist-dependency-mappings.md`.

Item__c chains:
- Friability_of_Material__c -> ACM_Classification__c (18 values: 9 non-friable, 9 friable with (f) suffix)
- ACM_Classification__c -> ACM_Sub_Classification__c (133 values, group-dependent)

Building__c chain:
- Building_Type__c (114 values) -> Building_Category__c (13 values)

NOT a dependent picklist: Item_Name__c — confirmed from raw SF metadata (no controllerName). Standalone restricted picklist with 294 values.

---

## Files to Read Before Implementing F4 Fix

- `V3/prompts/findings.md` — full audit with code line references
- `V3/output/picklist-dependency-mappings.md` — complete SF dependency chains
- `open_notebook/extractors/normalizers/taxonomy.py` — CLASSIFICATION_PATTERNS (lines 139-579)
- `open_notebook/extractors/validators/sf_picklist_validator.py` — chain validator
- `V3/item-list.txt` — raw SF picklist values for ACM_Sub_Classification__c
