# V3 Implementation Progress

> Updated by docs-specialist after each completed story.

## Codebase Patterns Discovered

_This section carries forward across stories. Add patterns, conventions, and learnings here._

| Pattern | Discovered In | Description |
|---------|---------------|-------------|
| Additive-only SF models | E30-S1 | New SF Pydantic models alongside BAR models, separate DB record keys (sf_v1 vs default) |
| Markdown table parser | E30-S1 | Parse `*_fields_summary.md` keyed on API Name column, handle empty/boolean cells |
| Hardcoded dependency chains | E30-S1 | Dependency data from picklist-dependency-mappings.md hardcoded as Python dicts (not runtime-parsed) |

## Completed Stories

| Date | Story | Title | SP | Files Changed | Key Learnings |
|------|-------|-------|----|---------------|---------------|
| 2026-03-03 | E30-S1 | SF Schema Config Loader | 5 | field_config.py, config_loader.py, sf_schema_provisioning.py, models.py, acm.py, main.py, 38.surrealql, test_config_loader.py | Additive pattern, 137 building types (not 114), Item_Name__c is NOT dependent picklist |

## Sprint Summary

| Sprint | Stories Done | SP Done | Status |
|--------|-------------|---------|--------|
| V3-1 | 1/6 | 5/22 | In Progress |
| V3-2 | 0/2 | 0/8 | Not Started |
| V3-3 | 0/7 | 0/19 | Not Started |
| V3-4 | 0/5 | 0/14 | Not Started |
| V3-5 | 0/4 | 0/11 | Not Started |
| V3-6 | 0/5 | 0/12 | Not Started |
| V3-7 | 0/4 | 0/11 | Not Started |

## Gate Milestones

| Gate | Status | Trigger Story | Date Unlocked |
|------|--------|---------------|---------------|
| SCHEMA_FREEZE | Locked | E30-S6 | — |
| EXTRACTION_COMPLETE | Locked | E31-S6 | — |
| AI_COMPLETE | Locked | E32-S5 | — |
| UI_COMPLETE | Locked | E33-S8 | — |
