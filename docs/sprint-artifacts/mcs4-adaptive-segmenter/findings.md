# MCS4: Adaptive Row Segmenter — Findings

## Key Observations

1. `detect_column_mapping()` at row_segmenter.py:178 — takes `header_cells: list[dict]`, returns `dict[str, str]`. Need to add `extra_mappings` param that takes priority over fuzzy matching.

2. `segment_docling_table()` at row_segmenter.py:276 — uses `_LEVEL_REGEX` at line 377. Need `level_regex` param.

3. `_recover_no_access_records()` at acm_extraction.py:2025 — hardcoded:
   - `no_access_re` (line 2048): "No access|Height restriction|Restricted Access"
   - `level_re` (line 2054): "Ground|First|Second|Third|Level|Roof|Basement"
   - `level_suffix_re` (line 2058): "floor|level|\\d"
   - `KNOWN_PRODUCT_KEYWORDS` (line 2125): set of 22 product words
   - Lookahead window: 30 lines

4. `_recover_not_sampled_records_ara()` at acm_extraction.py:2240 — hardcoded:
   - `section_header_re` (line 2280): "Name - Interior/Exterior - Level"
   - Lookback: 5 lines ("Asbestos" within 5 lines above)
   - Lookahead: 3 lines (restriction + "Presumed Positive" within 3 lines below)
   - `_ARA_ITEM_DESC_RE` (line 2364): specific product vocabulary

5. `_split_content_by_char_budget()` at utils.py:367 — uses `_BUDGET_ROOM_RE` then `_BUDGET_ARA_RE`. Need `content_boundary_re` param.

6. `RecoveryConfig` already exists at recovery_config.py — has all needed fields.

7. `InferredSchema` at schema_inference.py:29 — has `canonical_mapping`, `level_regex`, `recovery_config`.

8. `segment_multiple_tables()` also calls `segment_docling_table()` — must propagate new params.

## Backward Compatibility Strategy
- All new params default to `None`
- When `None`, use existing hardcoded values
- Existing tests unchanged — they don't pass new params
