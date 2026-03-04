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
| 2026-03-04 | E30-S7 | Two-Phase Extraction Prompts | 3 | preflight_extraction.j2, orchestrator_extraction.j2, source_commands.py, test_prompts.py | Preflight + Orchestrator prompts using ExtractionProvider adapters, integrated with source_commands.py |
| 2026-03-04 | E31-S1 | MinerU 2.x Integration + Validation | 2 | pyproject.toml, scripts/research/validate_mineru_v2.py, CLAUDE.md | MinerU 2.x installs in main venv, no separate .venv-mineru needed |
| 2026-03-04 | E31-S2 | Provider Adapter Framework | 3 | providers/base.py, docling_adapter.py, mineru_adapter.py, normalizer.py, __init__.py (registry), source_commands.py wired | ExtractionProvider Protocol, two adapters, ProviderRegistry, normalizer. Commit f1152678 |
| 2026-03-04 | E30-S9 | Persist Pre-Extraction Intelligence | 3 | 41.surrealql, repository.py, acm_extraction.py, models.py, acm.py, intelligence.ts, use-source-intelligence.ts, SourceIntelligencePanel.tsx, page.tsx, acm.ts | GitHub #85. source_intelligence table, save_intelligence graph node (tag_pages→save_intelligence→orchestrate), GET API, Intelligence tab with 4 sections |
| 2026-03-04 | E32-S6 | Ollama Model Evaluation Spike | 2 | ollama_model_eval.py, ollama-model-evaluation.md, open_notebook/graphs/utils.py | 4 models evaluated (llama3.1:8b, qwen2.5:7b, mistral:7b, phi4:latest). Recommended: qwen2.5:7b (98% enrichment, 0.78s/call). Updated model selection in utils.py. |
| 2026-03-04 | E31-S3 | Consensus Layer Core | 3 | consensus/engine.py, consensus/matcher.py, consensus/resolver.py, consensus/__init__.py, acm_schemas.py, test_consensus_engine.py, test_record_matcher.py | RecordMatcher (key-field anchor + Jaro-Winkler + row position), ConsensusEngine (confidence-weighted voting), ConflictResolver (L1-L4 escalation, L3 LLM stub). 78 tests |
| 2026-03-04 | E32-S4 | Classifier Update (SF Taxonomy) | 2 | sf_picklist_validator.py, test_sf_picklist_validator.py | Option B+ SF-schema normalization: _normalize_to_sf_value() for case-sensitive chain lookups. All 187+ existing tests pass |
| 2026-03-04 | E31-S4 | Raw Extraction Table + Storage | 2 | 42.surrealql, raw_extraction.py, raw_extraction_service.py, raw_extraction_router.py, source_commands.py, test_raw_extraction*.py (30 tests) | New raw_extraction table stores per-provider extraction outputs, RawExtraction domain model, GET /api/acm/raw-extractions/{source_id} endpoint, _store_raw_extractions() wiring |
| 2026-03-04 | E31-S5 | Pipeline Integration | 3 | source_commands.py, orchestrator_node.py, acm_extraction.py, consensus integration, test_pipeline_integration.py | Wire dual-provider extraction (Docling + MinerU) into orchestrator node, integrate consensus layer, unified extraction pipeline with provider switching |
| 2026-03-04 | E33-S2 | Building Grid + Item Grid (Two-View) | 5 | BuildingGrid.tsx, ItemGrid.tsx, SidebarWrapper.tsx, use-source-buildings.ts, use-building-items.ts, building.ts, item.ts, page.tsx | Two-view layout with Building sidebar (tree/search) + Item AG Grid. Buildings persisted via API. Item filtering by building_id. Dual-grid navigation pattern |
| 2026-03-04 | E31-S6 | Dual-Provider Benchmark | 2 | benchmark_harness.py, test_benchmark_harness.py, research reports | Benchmark framework for dual-provider extraction (Docling + MinerU) with consensus validation. Broadmeadows 31/31, Alexander ≥40/43 consensus validation |

## Sprint Summary

| Sprint | Stories Done | SP Done | Status |
|--------|-------------|---------|--------|
| V3-1 | 4/4 | 18/18 | Complete |
| V3-2 | 2/2 | 5/5 | Complete |
| V3-3 | 8/8 | 23/23 | Complete |
| V3-4 | 3/7 | 7/21 | In Progress |
| V3-5 | 0/5 | 0/15 | Not Started |
| V3-6 | 0/6 | 0/17 | Not Started |
| V3-7 | 0/4 | 0/9 | Not Started |

## Gate Milestones

| Gate | Status | Trigger Story | Date Unlocked |
|------|--------|---------------|---------------|
| SCHEMA_FREEZE | **UNLOCKED** | E30-S6 | 2026-03-03 |
| EXTRACTION_COMPLETE | **UNLOCKED** | E31-S6 | 2026-03-04 |
| AI_COMPLETE | Locked | E32-S5 | — |
| UI_COMPLETE | Locked | E33-S8 | — |
