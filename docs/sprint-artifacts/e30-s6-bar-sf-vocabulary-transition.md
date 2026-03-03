# Tech Spec: E30-S6 — BAR->SF Vocabulary Transition

**Story ID:** E30-S6
**Epic:** E30 — V3 Foundation: Schema + Config
**Sprint:** V3-2
**Story Points:** 2
**Risk Level:** MEDIUM
**Story Type:** backend
**Status:** Ready for Development
**Dependencies:** E30-S3 (ACM Record SF Item__c Alignment — completed)
**Gate Trigger:** SCHEMA_FREEZE (completes with E30-S1 through E30-S5)

---

## User Story

As a data pipeline engineer, I want all BAR-specific vocabulary replaced with Salesforce picklist values throughout the codebase so that extracted records match SF picklist constraints and pass the SalesforcePicklistValidator (E30-S4) without chain validation warnings.

---

## Vocabulary Transitions

| BAR Value | SF Value | Where |
|-----------|----------|-------|
| `"Good"` (Condition) | `"Stable"` | Validators, normalizers, schemas, prompts, tests, register_enums.json |
| `"Non Friable"` (Friability) | `"Non-friable"` | Validators, schemas, prompts, tests |
| `"T1 Cement products"` etc. | `"Cement products"` (no T-prefix) | Taxonomy normalizer, classification prompt, tests |

---

## Acceptance Criteria

| ID  | Criterion | Verification Method |
|-----|-----------|---------------------|
| AC1 | "Good" replaced with "Stable" in all validators, normalizers, prompt templates, and test fixtures | Grep: `grep -rn '"Good"' --include='*.py' --include='*.jinja'` returns 0 results (excluding comments/docs) |
| AC2 | T-prefix product group names stripped in taxonomy.py output and classification.jinja examples | Unit test: `classify_product()` returns "Vinyl products" not "T3 Vinyl products" |
| AC3 | BAR field name references updated in acm_schemas.py (FRIABLE_VALUES, MATERIAL_CONDITION_VALUES) | Unit test: constants contain SF values |
| AC4 | Test files updated with SF vocabulary in fixtures and assertions | All tests pass |
| AC5 | Prompt templates updated for SF vocabulary | Manual review of extraction.jinja, building_extraction.jinja, classification.jinja |
| AC6 | Existing tests pass with updated vocabulary | pytest: all pass |
| AC7 | register_enums.json updated: "Good" -> "Stable" | JSON file check |

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `docs/samplePDF/instructions-sample/register_enums.json` | MODIFY | "Good" -> "Stable" in Condition enum |
| `open_notebook/extractors/acm_schemas.py` | MODIFY | Update FRIABLE_VALUES, MATERIAL_CONDITION_VALUES, field descriptions |
| `open_notebook/extractors/normalizers/enums.py` | MODIFY | "good" -> "Stable" in CONDITION_SYNONYMS |
| `open_notebook/extractors/validators/acm_validator.py` | MODIFY | "Non Friable" -> "Non-friable" in normalizer, "Non-friable"/"Friable" in business rules |
| `open_notebook/extractors/normalizers/taxonomy.py` | MODIFY | Strip T-prefixes from CLASSIFICATION_PATTERNS output |
| `open_notebook/domain/acm.py` | MODIFY | Update field description strings |
| `api/routers/acm.py` | MODIFY | Update docstring |
| `api/models.py` | MODIFY | Update description |
| `prompts/acm/extraction.jinja` | MODIFY | BAR->SF vocabulary in examples |
| `prompts/acm/building_extraction.jinja` | MODIFY | BAR->SF vocabulary in examples |
| `prompts/acm/classification.jinja` | MODIFY | Strip T-prefixes from examples |
| Multiple test files | MODIFY | Update fixtures and assertions |

---

## Dev Agent Record
- **Status**: Completed
- **Started**: 2026-03-03
- **Completed**: 2026-03-03
- **Build**: PASS
- **Tests**: PASS (17 files updated)
- **Review**: Verified — Good→Stable, Non Friable→Non-friable, T-prefix stripped via _strip_t_prefix()
- **Notes**: Gate trigger for SCHEMA_FREEZE — **GATE UNLOCKED**. F4 (product type sentence case) NOT in scope — Title Case remains in CLASSIFICATION_PATTERNS.
