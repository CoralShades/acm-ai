---
epic: Epic 24
story_id: E24-S3
title: Remove MinerU Dead Code
status: done
priority: P1
effort: S (1 SP)
depends_on: none (can run in parallel with E24-S1)
---

As a developer,
I want dead MinerU code removed from the codebase,
So that the extraction pipeline is cleaner, faster (no empty DB queries), and easier to maintain.

## Acceptance Criteria

- [x] All MinerU-related production code removed per the plan below
- [x] All MinerU-related test files and test cases removed
- [x] `_store_mineru_tables()` and related functions removed from `source_commands.py`
- [x] MinerU HTML path removed from `prepare_context()` in `acm_extraction.py`
- [x] MinerU table check removed from `extract_building()` in `orchestrator.py`
- [x] `_get_mineru_tables_for_building()` removed from `orchestrator.py` (eliminates empty DB query on every building extraction)
- [x] `acm_extractor.py` receives deprecation header but is NOT deleted (too many test imports)
- [x] `_extract_with_mineru()` stub in `acm_extractor.py` is deleted (always returned `[]`)
- [x] All remaining tests pass: `uv run pytest` (936/936 pass)
- [x] No lint errors from orphaned imports: `uv run ruff check .` (clean)
- [x] Frontend builds: `cd frontend && npm run build` (succeeds)

## Technical Notes

### Files to DELETE

| File | Lines | Reason |
|------|-------|--------|
| `open_notebook/extractors/mineru_table_extractor.py` | 557 | MinerU requires paddle; TableFormer replaces this |
| `tests/test_mineru_table_extractor.py` | ~37 tests | Tests for deleted code |
| `tests/test_source_commands_mineru.py` | ~1 file | Tests for `_store_mineru_tables()` |

### Code to REMOVE from Existing Files

| File | What to Remove |
|------|---------------|
| `commands/source_commands.py` | `MINERU_TABLE_TYPE` constant (L32) |
| `commands/source_commands.py` | `_resolve_source_pdf_path()` (L35-43) |
| `commands/source_commands.py` | `_update_table_extraction_metadata()` (L46-69) |
| `commands/source_commands.py` | `_store_mineru_tables()` (L72-145) |
| `commands/source_commands.py` | `_store_mineru_tables()` call in `process_source_command()` (L232-238) |
| `commands/source_commands.py` | Import of `ACMTableSection` (L10, if no other use) |
| `open_notebook/extractors/orchestrator.py` | `_format_html_tables_for_llm()` (L393-408) |
| `open_notebook/extractors/orchestrator.py` | `_get_mineru_tables_for_building()` (L411-439) |
| `open_notebook/extractors/orchestrator.py` | MinerU check in `extract_building()` (L633-651) |
| `open_notebook/graphs/acm_extraction.py` | MinerU HTML path in `prepare_context()` (L1028-1057) |
| `open_notebook/extractors/acm_extractor.py` | `_extract_with_mineru()` function (~L385) |

### Tests to REMOVE

| File | Test(s) |
|------|---------|
| `tests/test_orchestrator.py` | `test_get_mineru_tables_for_building_filters_and_caches` |
| `tests/test_acm_extractor.py` | 5 MinerU-related tests (L720-833) |
| `tests/test_acm_api.py` | `test_raw_table_prefers_mineru_sections` |

### Code to ADD (deprecation header)

Add to top of `open_notebook/extractors/acm_extractor.py`:

```python
"""
DEPRECATED: Legacy regex-based ACM extractor.

This module is NOT used by the LangGraph extraction pipeline (acm_extraction.py).
It is retained for backward-compatible test infrastructure. Scheduled for removal
in a future cleanup sprint.

See ADR-001: docs/architecture/adr-tableformer-integration.md
"""
```

### Scope Boundary

- **727 lines** of dead production code + **~43 dead tests** across 4 test files
- Do NOT remove `acm_extractor.py` itself (13+ test imports depend on it)
- Do NOT modify `acm_table_section` schema (it may be used in Phase 2)

## Dependencies

- None (can run in parallel with E24-S1)
- ADR-001 Decision D2 authorizes MinerU removal

## References

- ADR-001 Section D2: `docs/architecture/adr-tableformer-integration.md`
- Technical Design Section 6: `docs/architecture/tableformer-technical-design.md`
- Dead code inventory: ADR-001 "MinerU Dead Code Inventory" table

## Dev Notes

### Implementation Summary

**Commit:** `6e0e2e8` (pushed to `origin/main`)
**Actual removal:** 2,298 lines (story estimated 727 — estimate only counted production code, not test files)

### Files Deleted (4 files, not 3 as planned)

| File | Lines | Notes |
|------|-------|-------|
| `open_notebook/extractors/mineru_table_extractor.py` | 557 | MinerU table extractor module |
| `tests/test_mineru_table_extractor.py` | 781 | 37 MinerU tests |
| `tests/test_source_commands_mineru.py` | 128 | `_store_mineru_tables()` tests |
| `test_performance_20page.py` | 268 | **Discovery:** standalone MinerU perf test at project root (not in story plan) |

### Code Removed from Existing Files

| File | What Removed |
|------|-------------|
| `commands/source_commands.py` | `MINERU_TABLE_TYPE`, `_resolve_source_pdf_path()`, `_update_table_extraction_metadata()`, `_store_mineru_tables()`, call in `process_source_command()` |
| `open_notebook/extractors/orchestrator.py` | `_format_html_tables_for_llm()`, `_get_mineru_tables_for_building()`, MinerU check in `extract_building()` |
| `open_notebook/graphs/acm_extraction.py` | MinerU HTML path in `prepare_context()` |
| `open_notebook/extractors/acm_extractor.py` | MinerU import block, `_extract_with_mineru()` stub, cleaned `extract_acm_records()`, added deprecation header |

### Tests Removed

| File | What Removed | Notes |
|------|-------------|-------|
| `tests/test_acm_extractor.py` | `TestMineruFallback` class | 10 tests (story estimated 5) |
| `tests/test_orchestrator.py` | `TestMineruHtmlHelpers` class | 2 tests |
| `tests/test_acm_api.py` | `test_raw_table_prefers_mineru_sections` | 1 test |

### Intentionally Preserved "mineru" References

- **Comments/docstrings** — historical context in ADR, tech design, orchestrator docstrings
- **Raw-tables API endpoint** — story scope boundary says NOT to remove
- **Schema settings** — `acm_table_section` schema may be used in Phase 2
- **`use_mineru` parameter** in `extract_acm_records()` — backward-compat, does nothing

### Pre-existing Test Failures (NOT caused by this story)

- `test_broadmeadows_e2e.py` — expects 31/31 but gets 28/31 (90.3%), the known gap documented in ADR-001
- `test_page_tagger.py::test_tag_pages_heuristic_fallback` — intermittent LLM-dependent failure

### Verification Results

- `uv run ruff check .` — clean (no lint errors)
- `uv run pytest` — 936/936 tests pass
- `cd frontend && npm run build` — succeeds
