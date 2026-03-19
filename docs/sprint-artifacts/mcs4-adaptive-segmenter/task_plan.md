# MCS4: Adaptive Row Segmenter — Task Plan

## Phase 1: Row Segmenter Refactoring
- [ ] 1.1 Add `extra_mappings: dict[str, str] | None = None` to `detect_column_mapping()`
- [ ] 1.2 Implement priority: extra_mappings → COLUMN_ALIASES fuzzy → pass-through
- [ ] 1.3 Add `level_regex: re.Pattern | None = None` to `segment_docling_table()`
- [ ] 1.4 Implement `effective_level_re = level_regex or _LEVEL_REGEX`
- [ ] 1.5 Propagate `extra_mappings` and `level_regex` through `segment_multiple_tables()`

## Phase 2: Recovery Function Refactoring
- [ ] 2.1 Refactor `_recover_no_access_records()` — accept `RecoveryConfig` param
- [ ] 2.2 Use `recovery_config.restriction_terms` instead of hardcoded regex
- [ ] 2.3 Use `recovery_config.product_keywords` instead of `KNOWN_PRODUCT_KEYWORDS`
- [ ] 2.4 Refactor `_recover_not_sampled_records_ara()` — accept `RecoveryConfig` param
- [ ] 2.5 Use `recovery_config.section_header_re` instead of hardcoded ARA regex
- [ ] 2.6 Use `recovery_config.not_sampled_terms` and `confirmation_terms`
- [ ] 2.7 Use `recovery_config.lookback_lines` / `lookahead_lines`

## Phase 3: Utils Refactoring
- [ ] 3.1 Add `content_boundary_re: re.Pattern | None` to `_split_content_by_char_budget()`
- [ ] 3.2 Use provided pattern, fall back to `_BUDGET_ROOM_RE` then `_BUDGET_ARA_RE`

## Phase 4: Pipeline Wiring
- [ ] 4.1 Wire `InferredSchema` through orchestrator to segmenter

## Phase 5: Tests
- [ ] 5.1 Tests for `detect_column_mapping()` with `extra_mappings`
- [ ] 5.2 Tests for `segment_docling_table()` with custom `level_regex`
- [ ] 5.3 Tests for recovery functions with custom `RecoveryConfig`
- [ ] 5.4 Backward compat: all existing tests pass with no extra params

## Phase 6: Verification
- [ ] 6.1 `uv run pytest tests/test_row_segmenter.py -v` — all pass
- [ ] 6.2 `uv run pytest tests/test_adaptive_segmenter.py -v` — all pass
- [ ] 6.3 `uv run pytest tests/ -x` — full suite
- [ ] 6.4 `uv run ruff check .` — lint clean
