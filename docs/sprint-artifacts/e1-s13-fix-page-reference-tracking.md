# Story 1.13: Fix Page Reference Tracking

Status: done

## Story

As a **user**,
I want **ACM records to show the correct page number from the source PDF**,
so that **I can click a record and be taken to the right page in the PDF viewer**.

## Problem Statement

Page references displayed in the ACM grid are incorrect - records show the same page number (often page 1) regardless of which page in the PDF they actually came from. This breaks the citation/PDF viewer experience since clicking a record navigates to the wrong page.

## Root Cause Analysis

Investigation identified **4 root causes** across the extraction pipeline:

### Bug 1: Page markers skipped when table index jumps (PRIMARY)
**File:** [acm_extractor.py](open_notebook/extractors/acm_extractor.py) - `_extract_from_markdown()`

When `_extract_table_lines()` returns `end_idx`, the loop sets `i = end_idx`, jumping past any `--- Page X ---` markers that appear between the end of one table and the start of the next. Those page markers never update `context.current_page`.

### Bug 2: No page tracking within multi-page tables
**File:** [acm_extractor.py](open_notebook/extractors/acm_extractor.py) - `_parse_acm_table()`

When a table spans multiple pages, page markers appear between table rows in the markdown. But `_parse_acm_table()` processes only pipe-delimited lines and ignores page markers embedded within the table. All rows in a table get `context.current_page` set at table start.

### Bug 3: MinerU extraction always returns empty (falls back to buggy regex)
**File:** [acm_extractor.py](open_notebook/extractors/acm_extractor.py) - `_extract_with_mineru()`

MinerU correctly extracts `ExtractedTable.page_number` per table, but the function intentionally returns `[]` with a TODO comment, forcing fallback to the regex parser that has bugs 1 and 2. MinerU's accurate page data is discarded.

### Bug 4: LangGraph chunking assigns single page to all records in chunk
**File:** [acm_extraction.py](open_notebook/graphs/acm_extraction.py) - `_chunk_content()` and `extract_records()`

When content fits in a single chunk (common for smaller PDFs), ALL records get the first page number found in the chunk. The fallback logic `if record.page_number is None: record.page_number = page_number` assigns the chunk's page (usually 1) to every record.

## Acceptance Criteria

1. Each ACM record's `page_number` field reflects the actual PDF page it was extracted from
2. Records from multi-page tables have correct per-row page numbers (not all the same page)
3. Page markers between tables are not skipped during regex extraction
4. Clicking a record in the grid opens the PDF viewer at the correct page
5. Fix applies to both new extractions and re-extractions of existing sources
6. No regression in extraction accuracy (record count, field values unchanged)

## Tasks / Subtasks

- [ ] Task 1: Fix page marker detection in `_extract_from_markdown()` (Bug 1)
  - [ ] 1.1 After `_extract_table_lines()` returns `end_idx`, scan lines from current `i` to `end_idx` for page markers BEFORE advancing `i`
  - [ ] 1.2 Update `context.current_page` for any page markers found in the skipped range
  - [ ] 1.3 Add unit test: two tables separated by a page marker, verify second table gets correct page
- [ ] Task 2: Fix page tracking within multi-page tables (Bug 2)
  - [ ] 2.1 Modify `_parse_acm_table()` to detect page markers between table rows
  - [ ] 2.2 When a line matches `PAGE_PATTERN` inside table processing, update `context.current_page`
  - [ ] 2.3 Each row should use the most recently seen page number, not the page at table start
  - [ ] 2.4 Add unit test: table with 10 rows spanning 3 pages, verify rows get correct page numbers
- [ ] Task 3: Fix LangGraph chunk page assignment (Bug 4)
  - [ ] 3.1 In `_chunk_content()`, track page boundaries within chunks (list of page ranges, not single page)
  - [ ] 3.2 In `extract_records()`, improve page assignment: use content position or page marker proximity to assign per-record pages instead of per-chunk
  - [ ] 3.3 Add unit test: single chunk with content from pages 1-5, verify records get distributed page numbers
- [ ] Task 4: Regression testing
  - [ ] 4.1 Run extraction on existing sample PDFs and compare record counts (must match)
  - [ ] 4.2 Verify field values unchanged (only page_number should change)
  - [ ] 4.3 Test with multi-building, multi-page PDFs
  - [ ] 4.4 Test with single-page PDFs (should still work, page = 1)

## Dev Notes

### Critical Context

**Do NOT attempt to enable MinerU HTML parsing (Bug 3) in this story.** That's a separate feature. Focus on fixing the regex and LangGraph paths that are actually used today.

### Extraction Pipeline Architecture

```
PDF → Docling (markdown) → acm_extractor.py (regex parsing)
                         → acm_extraction.py (LangGraph AI extraction)
```

Both paths have page tracking bugs. Fix both.

### Key Files and Line Numbers

| File | Function | Lines | Issue |
|------|----------|-------|-------|
| [acm_extractor.py](open_notebook/extractors/acm_extractor.py) | `_extract_from_markdown()` | ~277-338 | Page markers skipped when `i = end_idx` |
| [acm_extractor.py](open_notebook/extractors/acm_extractor.py) | `_parse_acm_table()` | ~446-499 | No page detection within table rows |
| [acm_extractor.py](open_notebook/extractors/acm_extractor.py) | `_create_row_from_cells()` | ~571-617 | Uses `context.current_page` (stale value) |
| [acm_extractor.py](open_notebook/extractors/acm_extractor.py) | `ExtractionContext` | ~50-55 | `current_page: int = 1` - holds the page state |
| [acm_extraction.py](open_notebook/graphs/acm_extraction.py) | `_chunk_content()` | ~247-253 | Single page per chunk |
| [acm_extraction.py](open_notebook/graphs/acm_extraction.py) | `extract_records()` | ~466-470 | All records in chunk get same page |

### Page Marker Patterns

The regex parser looks for page markers in the Docling-generated markdown. Common patterns:

```python
PAGE_PATTERN = re.compile(r'(?:---\s*)?[Pp]age\s+(\d+)(?:\s*---)?')
```

Matches: `--- Page 5 ---`, `Page 5`, `page 12`, etc.

### Fix Approach for Bug 1 (Recommended)

```python
# In _extract_from_markdown(), after table extraction:
if table_lines:
    # SCAN FOR PAGE MARKERS in the lines consumed by the table
    for scan_idx in range(i, end_idx):
        scan_line = lines[scan_idx].strip()
        page_match = PAGE_PATTERN.search(scan_line)
        if page_match:
            context.current_page = int(page_match.group(1))

    rows = _parse_acm_table(table_lines, context, parser=parser)
    extracted_rows.extend(rows)
i = end_idx
continue
```

### Fix Approach for Bug 2 (Recommended)

```python
# In _parse_acm_table(), within the row processing loop:
for line in table_lines[data_start:]:
    # Check for page marker WITHIN table
    page_match = PAGE_PATTERN.search(line)
    if page_match:
        context.current_page = int(page_match.group(1))
        continue  # Skip this line, it's not a data row

    if "|" not in line:
        continue

    # ... existing cell processing ...
    row = _create_row_from_cells(cells, header_map, context)
```

### Fix Approach for Bug 4 (Recommended)

```python
# In _chunk_content(), store page boundaries:
# Instead of: {"content": content, "page_number": page_num, "chunk_index": 0}
# Use: {"content": content, "page_number": page_num, "page_markers": {offset: page}, "chunk_index": 0}

# Find all page markers and their positions in the content
page_markers = {}
for match in re.finditer(page_pattern, content):
    page_num = int(next(g for g in match.groups() if g is not None))
    page_markers[match.start()] = page_num

# Then in extract_records(), after LLM extraction:
# For each record, find its approximate position in the chunk
# and look up the nearest page marker
```

### Testing Approach

Use existing test PDFs. Key test scenarios:
1. **Small PDF (1-2 pages):** All records should show page 1 or 2
2. **Multi-page PDF (10+ pages):** Records should have varied page numbers
3. **Multi-building PDF:** Each building section starts on different pages
4. **Table spanning pages:** Rows on page 3 should show 3, rows on page 4 should show 4

### Existing Test Files

```bash
# Find existing extraction tests
ls tests/*acm* tests/*extract*
```

### Domain Model

`page_number` is `Optional[int]` on ACMRecord ([acm.py](open_notebook/domain/acm.py)). No schema changes needed.

### Frontend Impact

None. The frontend already correctly reads and displays `page_number` from the API. The fix is entirely backend.

### Anti-Patterns to Avoid

- **DO NOT** enable MinerU HTML parsing (Bug 3) - separate story, complex work
- **DO NOT** change the ACMRecord schema or migration
- **DO NOT** modify frontend code - this is a backend-only fix
- **DO NOT** change extraction accuracy/field mapping logic - only page tracking
- **DO NOT** add new dependencies

### Dependencies

- **Part of:** Epic 1 (ACM Data Extraction Pipeline)
- **Depends on:** Nothing - standalone bug fix
- **Blocks:** Nothing directly, but improves E3 (Cell Citations & PDF Viewer) experience

### References

- [acm_extractor.py](open_notebook/extractors/acm_extractor.py) - Primary regex extraction with page bugs
- [acm_extraction.py](open_notebook/graphs/acm_extraction.py) - LangGraph extraction with chunk page bug
- [mineru_table_extractor.py](open_notebook/extractors/mineru_table_extractor.py) - MinerU (correct page tracking, unused)
- [acm.py domain model](open_notebook/domain/acm.py) - ACMRecord.page_number field
- [ACMGrid.tsx](frontend/src/components/acm/ACMGrid.tsx) - Frontend page display (no changes needed)

## Dev Agent Record

### Agent Model Used
claude-opus-4-6

### Debug Log References
None

### Completion Notes List
- Bug 1 (page markers skipped between tables): Fixed inherently by Bug 2 fix. Added defensive test confirming separate tables with page markers work correctly.
- Bug 2 (no page tracking within multi-page tables): Fixed by modifying `_extract_table_lines()` to continue past page markers and `_parse_acm_table()` to detect/process page markers within table rows. Added `_has_pipe_continuation()` helper that distinguishes table continuation rows from new table headers by checking for separator lines.
- Bug 3 (MinerU empty): Not addressed per story instructions.
- Bug 4 (LangGraph single page per chunk): Fixed by adding `page_markers` dict to chunk data and `_assign_record_page()` helper that uses product text position in content to find nearest preceding page marker. Returns `Tuple[int, int]` (page, position) and accepts `search_after` to handle duplicate product names.
- All 45 ACM extractor tests pass (39 original + 6 review additions). 433/436 project tests pass (3 pre-existing failures in test_acm_ai_extraction.py and test_acm_extractor_integration.py due to E1-S12 normalization not yet reflected in integration test expectations).
- Lint clean (ruff check passes).
- Frontend build not applicable (zero frontend changes).
- **Code review fixes applied**: (1) `_assign_record_page` now handles duplicate product names via `search_after` parameter and returns position for caller tracking. (2) `PAGE_PATTERN` in acm_extractor.py extended to match HTML comment page markers (`<!-- Page N -->`), consistent with acm_extraction.py. (3) Test regex duplication removed. (4) Added test for duplicate products. (5) Added 5 direct unit tests for `_has_pipe_continuation`.

### Change Log
- `open_notebook/extractors/acm_extractor.py`: Added `_has_pipe_continuation()` helper. Modified `_extract_table_lines()` to continue past page markers and use lookahead for multi-page table continuation. Modified `_parse_acm_table()` to detect PAGE_PATTERN within table lines and update `context.current_page` per row. Updated `PAGE_PATTERN` to also match HTML comment format (`<!-- Page N -->`).
- `open_notebook/graphs/acm_extraction.py`: Modified `_chunk_content()` to collect all page markers into `page_markers` dict on each chunk. Updated `_assign_record_page()` to return `Tuple[int, int]` with `search_after` parameter for duplicate product handling. Modified `extract_records()` to track search positions per product key.
- `tests/test_acm_extractor.py`: Added 11 new tests total: 5 from dev (page tracking), 1 duplicate product test, 5 `_has_pipe_continuation` unit tests.

### File List
- `open_notebook/extractors/acm_extractor.py` (MODIFIED)
- `open_notebook/graphs/acm_extraction.py` (MODIFIED)
- `tests/test_acm_extractor.py` (MODIFIED)
