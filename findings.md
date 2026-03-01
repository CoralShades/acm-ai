# Findings — E29: Pipeline Unification Story Specs

## Source Documents
1. **Reconciled YAML** — 8 stories, 19 SP, 4 decision gates, measure-first strategy
2. **Execution Contract** — PM charter: gates, risks, DoD, external deps, out-of-scope list
3. **Architecture Delta** — Current→target diagrams, fallback matrix F1-F8, file impact map, telemetry plan, rollback plan

## Key Architectural Decisions
- `tag_pages → orchestrate_extraction` ALWAYS (unconditional edge)
- No-inventory documents get synthetic whole-document plan
- Legacy path retained but unreachable until S7 cleanup (after Gate 3)
- Decomposed agents run INSIDE orchestrator node (no new AG-UI stages)
- Telemetry tags for all fallback activations (F1-F8)

## Gate Dependencies
| Gate | After | Blocks | Key Criteria |
|------|-------|--------|--------------|
| Gate 1 | S2 | S3-S8 | >=3 benchmarks, ground truth, baseline metrics, CI entry |
| Gate 2 | S4 | S5-S8 | Broadmeadows 31/31, Alexander >=36/43, Docling injection confirmed |
| Gate 3 | S6 | S7-S8 | No regression ±2 records, latency/cost within thresholds |
| Gate 4 | S8 | — | E2E tests, benchmark pass, docs aligned, CI green |

## Parallelization
- S1 + S2 MAY be developed in parallel (different files)
- S2 cannot PASS gate until S1 merged (harness needs parser fix for Alexander)
- All other stories strictly sequential

## File Impact Summary (A=Add, M=Modify)
- S1: utils.py(M), test_json_parser.py(A)
- S2: benchmarks/(A), e29_benchmark_harness.py(A), test_benchmark_harness.py(A), baseline report(A)
- S3: acm_extraction.py(M), orchestrator.py(M), acm_schemas.py(M), tests(M)
- S4: orchestrator.py(M), strategy_registry.py(A), acm_schemas.py(M), tests(A)
- S5: table_parser.py(A), bar_mapper.py(A), tests(A)
- S6: context_enricher.py(A), classifier.py(A), validator.py(A), acm_extraction.py(M), tests(A)
- S7: e29_validation_gate.py(A), gate results(A), acm_extraction.py(M), orchestrator.py(M), source_commands.py(M), tests(M)
- S8: acm.py(M), ExportDialog.tsx(M), test_export.py(A), test_unified_pipeline.py(A), BMAD docs(M)

## External Dependencies
- SurrealDB (Docker) — all stories
- Broadmeadows PDF + ground truth — S2
- Alexander PDF + ground truth — S2
- 1 additional benchmark doc — S2
- Docling tables in DB — S3
- OpenRouter API key with Claude Sonnet 4.6 — S3+

## Codebase Verification (DONE)
- [x] `utils.py:497` — `parse_json_response()` exists; tries fenced JSON then brace-depth scan
- [x] `orchestrator.py:322` — `should_use_orchestrator(state)` returns False when no inventory (THE FORK)
- [x] `acm_extraction.py:2913-2917` — `add_conditional_edges("tag_pages", should_use_orchestrator)` (THE CONDITIONAL EDGE)
- [x] `acm_extraction.py:1027` — `prepare_context()` exists (LEGACY)
- [x] `acm_extraction.py:1152` — `extract_records()` exists (LEGACY)
- [x] `orchestrator.py:915` — `orchestrate_extraction()` async function exists
- [x] `acm_schemas.py:126` — `ACMExtractionRecord` exists
- [x] `acm_schemas.py:392` — `ACMExtractionResult` exists
- [x] `benchmarks/` — does NOT exist (S2 creates it)
- [x] `ExportDialog.tsx` — does NOT exist (S8 creates it or modifies existing export UI)
- [x] `docs/samplePDF/` — Both PDFs exist:
  - Broadmeadows: `Clutch_Broadmeadows.pdf` + `Clutch_Broadmeadows.csv` (ground truth)
  - Alexander: `Clucth_Alexander_District_Hospital.pdf` + `Alexander_GroundTruth.csv`
- [x] Export routes: `/export/csv`, `/export/excel` — uses `_get_export_mapping()` from field_mapping
  - Currently per-source only, NOT per-building or per-ACM-type

## Key Codebase Observations
- Graph routing: conditional edge at line 2913 is exactly what S3 replaces
- Legacy nodes: "prepare" (line 2899), "extract" (line 2900) in graph
- Export: already uses field mapping (schema-driven), but lacks per-building/ACM-type filtering
- No `ExportDialog.tsx` component exists — frontend export is handled elsewhere or needs creation
