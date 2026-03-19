# MCS1: Fix Critical Bugs — Detector Architecture Cleanup

## Status: COMPLETE

## Plan

- [x] 1. Create `pipe_table_detector.py` — define missing patterns, rename class to PipeTableDetector
- [x] 2. Create `text_header_detector.py` — rename class to TextHeaderDetector, import _detect_ara_buildings from building_inventory
- [x] 3. Update `__init__.py` — new imports and registrations
- [x] 4. Update `llm_detector.py` — structural format names in prompt
- [x] 5. Delete old files: `clutch_detector.py`, `ara_detector.py`
- [x] 6. Update `tests/test_format_registry.py` — rename all references, add new test classes
- [x] 7. Codebase sweep — confirmed no remaining references needing changes
- [x] 8. Run tests (33/34 pass, 1 pre-existing failure) and lint (clean)

## Key Decisions
- `_PIPE_TABLE_BUILDING_NAME_PATTERN` and `_PIPE_TABLE_LEVEL_SUFFIX` defined locally in pipe_table_detector.py (not in building_inventory.py)
- `_detect_ara_buildings` canonical location stays in `building_inventory.py` (avoids circular import); TextHeaderDetector imports it
- "Clutch" references in taxonomy.py, config_loader.py, and PDF filenames are about the asbestos product "clutch plates" — NOT changed
- `survey_date` parsed by PipeTableDetector but BuildingMeta lacks the field — test updated to verify parsing logic directly
- Text-header detector lookbehind edge case documented (pipe-table detector runs first by priority, so no production impact)
