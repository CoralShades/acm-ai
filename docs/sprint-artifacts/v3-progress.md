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
| Non-blocking graph node persistence | E30-S9 | save_intelligence_node catches all exceptions so pipeline continues even if DB write fails — transient data survives in graph state regardless |

## Completed Stories

| Date | Story | Title | SP | Files Changed | Key Learnings |
|------|-------|-------|----|---------------|---------------|
| 2026-03-03 | E30-S1 | SF Schema Config Loader | 5 | field_config.py, config_loader.py, sf_schema_provisioning.py, models.py, acm.py, main.py, 38.surrealql, test_config_loader.py | Additive pattern, 137 building types (not 114), Item_Name__c is NOT dependent picklist |
| 2026-03-03 | E30-S2 | Building Record Table + Domain Model | 5 | building_record.py, building_record_service.py, building_record_router.py, 39.surrealql | Master-detail FK, building_record table, BuildingRecord domain model |
| 2026-03-03 | E30-S3 | ACM Record SF Item__c Alignment | 3 | acm.py, acm_schemas.py, 39.surrealql, test_acm_sf_alignment.py, test_domain.py | AliasChoices for dual BAR/SF access, populate_by_name=True, school_name now optional |
| 2026-03-03 | E30-S4 | Dependent Picklist Validator | 5 | sf_picklist_validator.py, acm_validator.py, __init__.py, test_sf_picklist_validator.py | 187 tests, BAR→SF normalization needed, WARN/REJECT policy split on ValidationResult |
| 2026-03-03 | E30-S6 | BAR→SF Vocabulary Transition | 2 | 17 files: taxonomy.py, enums.py, acm_schemas.py, config_loader.py, acm_validator.py, api/models.py, acm.py, 3 prompts, 5 test files | _strip_t_prefix helper, GATE:SCHEMA_FREEZE unlocked |
| 2026-03-04 | E30-S5 | Data Migration Script | 3 | v3_data_migration.py, v3_data_migration_rollback.py, test_v3_data_migration.py, async_migrate.py, e30-s5 tech spec | 33 tests, idempotent, dry-run mode, Good→Stable vocab migration, migrations 37-40 registered |
| 2026-03-04 | E31-S1 | MinerU 2.x Integration + Validation | 2 | pyproject.toml, scripts/research/validate_mineru_v2.py, CLAUDE.md | MinerU 2.x installs in main venv, no separate .venv-mineru needed |
| 2026-03-04 | E30-S9 | Persist Pre-Extraction Intelligence | 3 | 41.surrealql, repository.py, acm_extraction.py, models.py, acm.py, intelligence.ts, use-source-intelligence.ts, SourceIntelligencePanel.tsx, page.tsx, acm.ts | GitHub #85. source_intelligence table, save_intelligence graph node (tag_pages→save_intelligence→orchestrate), GET API, Intelligence tab with 4 sections |
| 2026-03-04 | E32-S6 | Ollama Model Evaluation Spike | 2 | ollama_model_eval.py, ollama-model-evaluation.md, open_notebook/graphs/utils.py | 4 models evaluated (llama3.1:8b, qwen2.5:7b, mistral:7b, phi4:latest). Recommended: qwen2.5:7b (98% enrichment, 0.78s/call). Updated model selection in utils.py. |

## Sprint Summary

| Sprint | Stories Done | SP Done | Status |
|--------|-------------|---------|--------|
| V3-1 | 4/4 | 18/18 | Complete |
| V3-2 | 2/2 | 5/5 | Complete |
| V3-3 | 4/8 | 10/20 | In Progress |
| V3-4 | 0/6 | 0/17 | Not Started |
| V3-5 | 0/4 | 0/13 | Not Started |
| V3-6 | 0/6 | 0/17 | Not Started |
| V3-7 | 0/4 | 0/9 | Not Started |

## Gate Milestones

| Gate | Status | Trigger Story | Date Unlocked |
|------|--------|---------------|---------------|
| SCHEMA_FREEZE | **UNLOCKED** | E30-S6 | 2026-03-03 |
| EXTRACTION_COMPLETE | Locked | E31-S6 | — |
| AI_COMPLETE | Locked | E32-S5 | — |
| UI_COMPLETE | Locked | E33-S8 | — |
