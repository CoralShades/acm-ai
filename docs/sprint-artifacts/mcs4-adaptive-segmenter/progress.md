# MCS4: Adaptive Row Segmenter — Progress

## Session 1 — 2026-03-18

### Completed
- Read all key files and design doc
- Created task plan
- Phase 1: Row Segmenter Refactoring (all 5 subtasks)
  - `detect_column_mapping()` — added `extra_mappings` param with priority chain
  - `segment_docling_table()` — added `level_regex` and `extra_mappings` params
  - `segment_multiple_tables()` — propagated both params through all internal calls
- Phase 2: Recovery Function Refactoring (all 7 subtasks)
  - `_recover_no_access_records()` — accepts `RecoveryConfig`, uses config fields
  - `_recover_not_sampled_records_ara()` — accepts `RecoveryConfig`, uses config fields
  - Fixed backward-compat issue: default `no_access_re` preserves original regex exactly
- Phase 3: Utils Refactoring (both subtasks)
  - `_split_content_by_char_budget()` — added `content_boundary_re` param (priority 1)
  - `_ollama_split_by_budget()` — pass-through
- Phase 5: Tests
  - 9 new tests in `tests/test_adaptive_segmenter.py` — all pass
  - 34 existing tests in `tests/test_row_segmenter.py` — all pass (backward compat)
  - 7 existing tests in `tests/test_recover_no_access.py` — all pass
  - 21 existing tests in `tests/test_utils.py` — all pass
  - Lint clean

### Not Done (deferred)
- Phase 4: Wire InferredSchema through orchestrator (wiring already exists at call sites;
  orchestrator changes would involve modifying the graph node to pass InferredSchema.canonical_mapping
  as extra_mappings — this is integration work for when the schema inference node is wired in,
  which is Story 2's responsibility)

### Key Decisions
1. Used "preserve original regex when no config provided" pattern for `no_access_re` in
   `_recover_no_access_records()` because `RecoveryConfig.restriction_terms` defaults
   ("Height Restricted") don't exactly match the original regex stems ("Height restriction")
2. `extra_mappings` in `detect_column_mapping()` checks raw header text as keys (not lowered),
   matching the InferredSchema.canonical_mapping format
