# MCS5: Format-Agnostic Prompts — Progress

## Session 1: 2026-03-18

### Completed
- All 10 tasks complete
- Added `detected_format` field to `InferredSchema` (schema_inference.py)
- Created 3 format example YAML files (standard, ara, pipe_table)
- Made `building_inventory.jinja` format-conditional with fallback to generic guidance
- Made `row_extraction.jinja` accept dynamic `extraction_fields` list
- Made `v3_building_extraction.jinja` example-conditional by format
- Added `build_extraction_fields()` helper to derive field list from InferredSchema
- Updated `build_kv_prompt()` / `extract_single_row()` / `extract_all_rows()` to accept extraction_fields
- Wired `detected_format` into graph node prompt contexts (building inventory + v3 building + items)
- 30 tests written and passing
- Lint clean

### Key Decisions
- Templates use `{% set _format = detected_format or format_name or "" %}` for dual-source compat
- `extraction_fields` enriches field descriptions with original PDF column names
- `build_extraction_fields()` requires ≥4 mapped fields to activate (otherwise uses defaults)
- Standard DET example is the fallback when format is unknown/None (backward compat)

### Files Modified
- `open_notebook/extractors/schema_inference.py` — detected_format field, build_extraction_fields()
- `open_notebook/extractors/row_extractor.py` — extraction_fields parameter threading
- `open_notebook/extractors/orchestrator.py` — detected_format in v3_building_extraction context
- `open_notebook/graphs/acm_extraction.py` — detected_format + extraction_fields wiring
- `prompts/acm/building_inventory.jinja` — format-conditional sections
- `prompts/acm/row_extraction.jinja` — dynamic extraction_fields
- `prompts/acm/v3_building_extraction.jinja` — format-conditional worked examples

### Files Created
- `prompts/acm/format_examples/standard.yaml`
- `prompts/acm/format_examples/ara.yaml`
- `prompts/acm/format_examples/pipe_table.yaml`
- `tests/test_format_agnostic_prompts.py` (30 tests)
- `docs/sprint-artifacts/mcs5-agnostic-prompts/` (task_plan, findings, progress)
