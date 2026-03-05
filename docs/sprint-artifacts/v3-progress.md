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
| 2026-03-04 | E32-S1 | Building__c AI Extraction Node | 3 | building_extraction_node.py, test_building_extraction.py, acm_extraction.py, building_prompt.j2 | Claude Sonnet extraction node for Building__c fields, integrated into orchestrator pipeline, produces structured BuildingData for SF sync |
| 2026-03-04 | E32-S6 | Ollama Model Evaluation Spike | 2 | ollama_model_eval.py, ollama-model-evaluation.md, open_notebook/graphs/utils.py | 4 models evaluated (llama3.1:8b, qwen2.5:7b, mistral:7b, phi4:latest). Recommended: qwen2.5:7b (98% enrichment, 0.78s/call). Updated model selection in utils.py. |
| 2026-03-04 | E31-S3 | Consensus Layer Core | 3 | consensus/engine.py, consensus/matcher.py, consensus/resolver.py, consensus/__init__.py, acm_schemas.py, test_consensus_engine.py, test_record_matcher.py | RecordMatcher (key-field anchor + Jaro-Winkler + row position), ConsensusEngine (confidence-weighted voting), ConflictResolver (L1-L4 escalation, L3 LLM stub). 78 tests |
| 2026-03-04 | E32-S4 | Classifier Update (SF Taxonomy) | 2 | sf_picklist_validator.py, test_sf_picklist_validator.py | Option B+ SF-schema normalization: _normalize_to_sf_value() for case-sensitive chain lookups. All 187+ existing tests pass |
| 2026-03-04 | E31-S4 | Raw Extraction Table + Storage | 2 | 42.surrealql, raw_extraction.py, raw_extraction_service.py, raw_extraction_router.py, source_commands.py, test_raw_extraction*.py (30 tests) | New raw_extraction table stores per-provider extraction outputs, RawExtraction domain model, GET /api/acm/raw-extractions/{source_id} endpoint, _store_raw_extractions() wiring |
| 2026-03-04 | E31-S5 | Pipeline Integration | 3 | source_commands.py, orchestrator_node.py, acm_extraction.py, consensus integration, test_pipeline_integration.py | Wire dual-provider extraction (Docling + MinerU) into orchestrator node, integrate consensus layer, unified extraction pipeline with provider switching |
| 2026-03-04 | E33-S2 | Building Grid + Item Grid (Two-View) | 5 | BuildingGrid.tsx, ItemGrid.tsx, SidebarWrapper.tsx, use-source-buildings.ts, use-building-items.ts, building.ts, item.ts, page.tsx | Two-view layout with Building sidebar (tree/search) + Item AG Grid. Buildings persisted via API. Item filtering by building_id. Dual-grid navigation pattern |
| 2026-03-04 | E33-S1 | Upload Wizard + Extraction Progress | 3 | UploadWizard.tsx, ExtractionProgress.tsx, upload.ts, use-upload-progress.ts, /api/acm/upload, PipelineEventBus, SSE stream consumer | Multi-step upload wizard, real-time extraction progress via SSE stream, stage-by-stage pipeline visibility, frontend progress UI integrated with PipelineEventBus |
| 2026-03-04 | E31-S6 | Dual-Provider Benchmark | 2 | benchmark_harness.py, test_benchmark_harness.py, research reports | Benchmark framework for dual-provider extraction (Docling + MinerU) with consensus validation. Broadmeadows 31/31, Alexander ≥40/43 consensus validation |
| 2026-03-04 | E31-S7 | PipelineEventBus + SSE Infrastructure | 3 | PipelineEventBus class, SSE endpoints, Zustand streaming integration, frontend progress stream | Event bus for pipeline stage transitions, /api/acm/extraction-progress/{id}/stream SSE endpoint, frontend real-time progress UI |
| 2026-03-04 | E32-S5 | Extraction Pipeline E2E Test | 3 | tests/test_v3_e2e_pipeline.py, test_raw_extraction_storage.py, test_consensus_engine.py, acm_extractor.py | 8 test classes, 16 always-run tests covering full V3 pipeline FK integrity, raw extraction storage, consensus field population, SF field name conformance. GATE:AI_COMPLETE unlocked |
| 2026-03-05 | E32-S8 | Ollama Token-Budget Content Chunking | 2 | open_notebook/graphs/utils.py, open_notebook/extractors/orchestrator.py, tests/test_ollama_chunking.py | Replaces _truncate_content_for_ollama hard-cut with _ollama_split_by_budget multi-pass loop. Records beyond budget no longer silently dropped. 11 unit tests. |
| 2026-03-05 | E31-S8 | Pre-Extraction Quality Hardening | 3 | acm_extractor.py, mineru_adapter.py, docling_adapter.py, page_tagger.py, building_inventory.py, prompt_context_builder.py, orchestrator.py, test_extraction.py | PyMuPDF page-count fallback (AC1), LLM retry logic with exponential backoff (AC2), field_confidence top-level column in extraction results (AC3), cover page detection window bounded to 3 pages (AC4) |
| 2026-03-05 | E33-S5 | Raw Table Review | 3 | RawTableReview.tsx, raw-table-review hook, /source/:id raw table tab, AG Grid with sorting/filtering | Opt-in raw extraction table viewer, shows provider outputs (Docling/MinerU) side-by-side, integrated into two-view layout |
| 2026-03-05 | E33-S4 | SF Validation Badges + Record Wizard | 3 | ValidationBadges.tsx, RecordWizard.tsx, BulkFixPanel.tsx, ValidationErrorSummary.tsx, use-validation-badges.ts, useRecordWizard.ts | Inline validation badges in AG Grid (pass/warn/fail), record wizard modal for field edits, bulk fix feature, error count in building sidebar. V3-6 |
| 2026-03-05 | E34-S1 | Record-by-Record Streaming | 2 | streaming utilities (backend), RecordStreamingConsumer.tsx (frontend), useRecordStreaming.ts, acm.ts API | SSE-based streaming of validated records from backend to frontend grid. Records appear as they complete validation. Real-time row addition with status indication. |
| 2026-03-05 | E34-S2 | Bulk Operations | 2 | BulkOperationsPanel.tsx, useBulkOperations.ts, bulk-operations API, AG Grid multi-select integration | Multi-select records in grid, bulk edit/validate/export. Integrates with field schema API for bulk field updates. |
| 2026-03-05 | E34-S3 | Performance Optimization | 2 | Performance tuning across extraction pipeline | Broadmeadows <120s, Alexander <300s target benchmarks. Pipeline throughput and latency optimization. |
| 2026-03-05 | E34-S4 | Canonical Artifact Update | 3 | CLAUDE.md, README.md, PRD, architecture, epics, sprint-status.yaml, prd.json | Documentation audit — all V3 canonical artifacts reconciled with ground truth. V3 Architecture Patterns added to CLAUDE.md. |
| 2026-03-05 | E30-S8 | Ollama + Anthropic Direct + OpenRouter Provider Priority | 3 | open_notebook/graphs/utils.py, tests/test_openrouter_provider_routing.py | provision_extraction_fallback_model() uses ACM_ANTHROPIC_API_KEY. Priority: Ollama→Anthropic→OpenRouter. No bare env var bleed. |
| 2026-03-05 | E35-S1 | Fix Sync Upload asyncio.run() Error | 2 | api/routers/sources.py, tests/test_sync_upload.py | Replace execute_command_sync (asyncio.run) with submit_command + await wait_for_command. 10 tests. |
| 2026-03-05 | E35-S2 | Persist Model Defaults to SurrealDB | 2 | model_settings_service.py, model_settings_router.py, 45.surrealql, test_model_settings.py | SurrealDB model_settings table, PUT /api/models/defaults endpoint, PATCH /api/models/{id} updates persisted. Fixes Ollama model resets on API restart. |
| 2026-03-05 | E35-S3 | Ollama Extraction Hardening | 3 | open_notebook/graphs/utils.py, open_notebook/extractors/orchestrator.py, tests/test_ollama_extraction_settings.py | Fixed stale chunking test, added 5 new tests for _apply_ollama_extraction_settings (format=json, num_ctx tuning, content truncation). Validated end-to-end. |

## Sprint Summary

| Sprint | Stories Done | SP Done | Status |
|--------|-------------|---------|--------|
| V3-1 | 4/4 | 18/18 | Complete |
| V3-2 | 2/2 | 5/5 | Complete |
| V3-3 | 8/8 | 23/23 | Complete |
| V3-4 | 8/8 | 23/23 | Complete |
| V3-5 | 5/5 | 15/15 | Complete |
| V3-6 | 5/5 | 14/14 | Complete |
| V3-7 | 4/4 | 9/9 | Complete |
| V3-8 | 3/8 | 7/22 | In Progress |

**V3 Core: 37/37 stories done (100%). V3-8 Hardening: 3/8 stories (38%), 7/22 SP (32%).**

## Gate Milestones

| Gate | Status | Trigger Story | Date Unlocked |
|------|--------|---------------|---------------|
| SCHEMA_FREEZE | **UNLOCKED** | E30-S6 | 2026-03-03 |
| EXTRACTION_COMPLETE | **UNLOCKED** | E31-S6 | 2026-03-04 |
| AI_COMPLETE | **UNLOCKED** | E32-S5 | 2026-03-04 |
| UI_COMPLETE | **UNLOCKED** | E33-S8 | 2026-03-05 |
