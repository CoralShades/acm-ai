# Progress Log: E25-S3 Architecture Decision

## Session: 2026-02-27

### Phase 1: Research & Evidence Gathering — COMPLETE
- Read all 11 mandatory files
- E25-S2 spike: 29/31 from DataFrames alone, 9/9 "Same as", 4/6 "Not Sampled"
- E24 root cause: content-core serialization (column-major), not TableFormer itself
- E23 baseline: 28/31, missing 3 "Not Sampled" edge cases
- Codebase: source_commands clean, orchestrator clean, migration 18 schema sufficient
- comparison_summary.json confirms: 8 tables, 30 register rows, 22.41s processing

### Phase 2: Analysis & Decision — COMPLETE
- Synthesized findings into `findings.md`
- Identified key insight: E24 ≠ E25 because content-core bypass
- Validated Hybrid Approach A: PyMuPDF (unchanged) + Docling Direct API (parallel)
- Confirmed acm_table_section schema needs only 1 new field (structured_json)
- Designed separate feature flag: DOCLING_DIRECT_TABLE_EXTRACTION (not E24's flag)

### Phase 3: Document Production — COMPLETE
- Updated `docs/architecture/adr-tableformer-integration.md` with D5 section
  - Full empirical evidence citations from E25-S2
  - Updated Consequences section (What Improves, What Gets Worse, Risks)
  - Updated Migration Path for D5
  - Updated Related Documents
- Created `docs/architecture/e26-table-extraction-technical-design.md`
  - Complete technical design with code examples
  - Source processing changes (new function, storage, feature flag)
  - Pipeline integration (orchestrator changes, context injection, prompt)
  - Schema changes (1 new field migration)
  - Testing strategy (unit, integration, E2E, performance)
  - Rollout plan (3 phases, rollback plan)
  - Story breakdown (5 stories, 9 SP, critical path diagram)

### Phase 4: Commit & Finalize — PENDING
- Ready for git commit
- BMAD workflow updates pending
