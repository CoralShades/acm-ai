# Task Plan: E25-S3 Architecture Decision + E26 Technical Design

## Goal
Review E25 research spike results and produce architecture decision (ADR D5) + E26 implementation blueprint for integrating Docling Direct API into the extraction pipeline.

## Phases

### Phase 1: Research & Evidence Gathering [COMPLETE]
- [x] Read E25-S2 comparison report (docs/reviews/e25-table-extraction-comparison.md)
- [x] Read E24 validation results (docs/reviews/e24-validation-results.md)
- [x] Read E23 baseline results (docs/reviews/e23-validation-results.md)
- [x] Read current ADR (docs/architecture/adr-tableformer-integration.md)
- [x] Read current tech design (docs/architecture/tableformer-technical-design.md)
- [x] Read source.py (open_notebook/graphs/source.py)
- [x] Read source_commands.py (commands/source_commands.py)
- [x] Read orchestrator.py (open_notebook/extractors/orchestrator.py)
- [x] Read acm_extraction.py (open_notebook/graphs/acm_extraction.py)
- [x] Read migration 18 (migrations/18.surrealql)
- [x] Read raw comparison data (research-output/e25/comparison_summary.json)

### Phase 2: Analysis & Decision [COMPLETE]
- [x] Synthesize E25-S2 metrics (DataFrame row counts, column mappings, processing time)
- [x] Identify E24 vs E25 key difference (content-core bypass)
- [x] Validate Hybrid Approach A feasibility against existing codebase
- [x] Map DataFrame columns to BAR fields (positional mapping confirmed)
- [x] Assess acm_table_section schema sufficiency (1 new field needed)

### Phase 3: Document Production [COMPLETE]
- [x] Update ADR-001 with D5 section (cite empirical evidence)
- [x] Create E26 technical design document
- [x] Define E26 stories with story points (5 stories, 9 SP)

### Phase 4: Commit & Finalize [IN PROGRESS]
- [ ] Git commit with conventional commit message
- [ ] Update sprint status / relevant BMAD artifacts

## Decisions Log
| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D5 | Integrate Docling Direct API (Hybrid Approach A) | E25 spike: 29/31 DataFrames, bypasses content-core fragmentation | 2026-02-27 |
| - | Separate feature flag from E24 | DOCLING_DIRECT_TABLE_EXTRACTION ≠ DOCLING_TABLE_STRUCTURE | 2026-02-27 |
| - | 1 new schema field only | structured_json on acm_table_section (migration 18 covers rest) | 2026-02-27 |
| - | Orchestrator injection (not prepare_context) | Orchestrator handles per-building; prepare_context is legacy path | 2026-02-27 |
