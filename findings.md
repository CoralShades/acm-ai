# Findings: Parallel BMad Code Review for E1-S15, S16, S17

## Pre-Review State
- All 3 stories in `review` status with all tasks marked [x]
- E1-S15: Corrective RAG Validation Loop (8 ACs, 4 tasks)
- E1-S16: Document Structure & TOC Extraction (8 ACs, tasks TBD)
- E1-S17: Building Inventory Compilation (8 ACs, tasks TBD)

## Review Findings
(Will be populated by reviewer agents)

### E1-S15 Findings (8 issues: 2H, 3M, 3L)
- **[H] FIXED** Enum values loaded repeatedly without caching - added module-level cache
- **[H] NOTED** Triple validation of records (validate_records_strict + should_correct + correct_records) - tech debt
- **[M] FIXED** Redundant exception clause `(json.JSONDecodeError, Exception)` simplified
- **[M] FIXED** LLM JSON parsing doesn't handle markdown code blocks - added stripping
- **[M] FIXED** correction_stats not returned to API consumers - added to ACMExtractionOutput
- **[L]** validate_enum_fields doesn't accept pre-loaded enums (mitigated by cache)
- **[L]** No integration tests in test_acm_extractor.py (covered elsewhere)
- **[L]** _apply_field_correction uses if/elif instead of setattr (safer for Pydantic)
- Tests: 38/38 + 45/45 passed

### E1-S16 Findings (9 issues: 1H, 4M, 4L)
- **[H] FIXED** test_page_count_extraction made real LLM API call (114s) - added mock
- **[M] FIXED** No boundary test for section_id validation (0-7 range) - added test
- **[M] FIXED** O(n^2) building ID dedup in _heuristic_fallback - switched to set
- **[M] NOTED** Duplicated page marker regex between document_structure.py and acm_extraction.py
- **[M] NOTED** Redundant _extract_total_pages() call
- **[L]** Building ID regex false positive potential
- **[L]** Document content in prompt without backtick escaping
- **[L]** Graph edge test coupled across stories
- **[L]** Graph edge test uses internal StateGraph.edges API
- Tests: 38/38 passed (+1 new boundary test)

### E1-S17 Findings (7 issues: 1H, 4M, 2L)
- **[H] FIXED** Unused parameters in _extract_rooms_from_section - removed
- **[M] FIXED** acm_item_count_estimate never populated by heuristic - fixed _classify_complexity
- **[M] FIXED** Weak test assertion in test_groups_target_3_to_5_pages - strengthened
- **[M] FIXED** test_graph_structure_to_inventory_edge didn't verify edges - fixed
- **[M] FIXED** Misleading docstring in _heuristic_fallback - corrected
- **[L]** Code duplication with prepare_context() for register trimming
- **[L]** No test for 3+ page building span
- Tests: 43/43 passed (+1 new test)
