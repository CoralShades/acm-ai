# V3 Implementation Progress

> Updated by docs-specialist after each completed story.

## Codebase Patterns Discovered

_This section carries forward across stories. Add patterns, conventions, and learnings here._

| Pattern | Discovered In | Description |
|---------|---------------|-------------|
| Additive-only SF models | E30-S1 | New SF Pydantic models alongside BAR models, separate DB record keys (sf_v1 vs default) |
| Markdown table parser | E30-S1 | Parse `*_fields_summary.md` keyed on API Name column, handle empty/boolean cells |
| Hardcoded dependency chains | E30-S1 | Dependency data from picklist-dependency-mappings.md hardcoded as Python dicts (not runtime-parsed) |
| BAR→SF value normalization | E30-S4 | BAR normalizer produces "Non Friable" but SF expects "Non-friable" — sf_picklist_validator has _BAR_TO_SF_VALUE mapping |
| WARN/REJECT policy separation | E30-S4 | chain_warnings field on ValidationResult separates non-blocking SF chain issues from blocking validation errors |

## Completed Stories

| Date | Story | Title | SP | Files Changed | Key Learnings |
|------|-------|-------|----|---------------|---------------|
| 2026-03-03 | E30-S1 | SF Schema Config Loader | 5 | field_config.py, config_loader.py, sf_schema_provisioning.py, models.py, acm.py, main.py, 38.surrealql, test_config_loader.py | Additive pattern, 137 building types (not 114), Item_Name__c is NOT dependent picklist |
| 2026-03-03 | E30-S2 | Building Record Table + Domain Model | 5 | building_record.py, building_record_service.py, building_record_router.py, 39.surrealql | Master-detail FK, building_record table, BuildingRecord domain model |
| 2026-03-03 | E30-S3 | ACM Record SF Item__c Alignment | 3 | acm.py, acm_schemas.py, 39.surrealql, test_acm_sf_alignment.py, test_domain.py | AliasChoices for dual BAR/SF access, populate_by_name=True, school_name now optional |
| 2026-03-03 | E30-S4 | Dependent Picklist Validator | 5 | sf_picklist_validator.py, acm_validator.py, __init__.py, test_sf_picklist_validator.py | 187 tests, BAR→SF normalization needed, WARN/REJECT policy split on ValidationResult |
| 2026-03-03 | E30-S6 | BAR→SF Vocabulary Transition | 2 | 17 files: taxonomy.py, enums.py, acm_schemas.py, config_loader.py, acm_validator.py, api/models.py, acm.py, 3 prompts, 5 test files | _strip_t_prefix helper, GATE:SCHEMA_FREEZE unlocked |

## Sprint Summary

| Sprint | Stories Done | SP Done | Status |
|--------|-------------|---------|--------|
| V3-1 | 4/6 | 18/22 | In Progress |
| V3-2 | 1/2 | 2/8 | In Progress |
| V3-3 | 0/7 | 0/19 | Not Started |
| V3-4 | 0/5 | 0/14 | Not Started |
| V3-5 | 0/4 | 0/11 | Not Started |
| V3-6 | 0/5 | 0/12 | Not Started |
| V3-7 | 0/4 | 0/11 | Not Started |

## Gate Milestones

| Gate | Status | Trigger Story | Date Unlocked |
|------|--------|---------------|---------------|
| SCHEMA_FREEZE | **UNLOCKED** | E30-S6 | 2026-03-03 |
| EXTRACTION_COMPLETE | Locked | E31-S6 | — |
| AI_COMPLETE | Locked | E32-S5 | — |
| UI_COMPLETE | Locked | E33-S8 | — |
