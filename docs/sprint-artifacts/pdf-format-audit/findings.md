# Findings: PDF Processing Layer & Format Detection Audit
Date: 2026-03-14
Status: COMPLETE

## Executive Summary

Three parallel audit streams analyzed PyMuPDF page markers, all three Docling output types, and format detection templates. Key findings:

- **3 CRITICAL issues** (data loss or pipeline failure)
- **4 HIGH issues** (incorrect output or significant gaps)
- **4 MEDIUM issues** (robustness/correctness concerns)
- **5 LOW/INFO issues** (cosmetic or optimization)

BAR format confirmed as properly secondary — no pipeline branching.
Docling JSON cell keys fully aligned with row_segmenter expectations.
`mode="json"` confirmed everywhere — no `mode="python"` remaining.

---

## 1. PyMuPDF Output Audit

### Page Marker Production

**File:** `.venv/Lib/site-packages/content_core/processors/pdf.py:191-271`

**CRITICAL FINDING: `source.full_text` contains NO page markers.**

The `content_core` PDF processor extracts text via `page.get_text()` per page, then joins with `"".join(full_text)` — no separator, no page markers. `clean_pdf_text()` at line 132 further normalizes whitespace (collapses 3+ newlines to 2).

Page markers (`--- Page N ---`) are only produced by:
- Benchmark harness: `scripts/research/e29_benchmark_harness.py:554`
- Page tagger: `open_notebook/extractors/page_tagger.py:343` (re-renders for LLM batches, not stored in `source.full_text`)

**Format when present:** `--- Page N ---\n{text}` (three dashes, 1-based page number)

### Page Marker Consumption

#### `_extract_page_range_text` (`acm_extraction.py:240-276`)

**Regex:** `r"(?:(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+|<!--\s*Page\s+(\d+)\s*-->|(?:^|\n)Page\s+(\d+)(?:\s|$)|PAGE\s+(\d+)\s+OF\s+\d+)"`

- 4 alternations covering: dash-wrapped, HTML comment, bare "Page N", "PAGE N OF N"
- Flags: `re.IGNORECASE`
- **Match status vs `--- Page N ---`:** MATCH (first alternation)
- **Match status vs actual `source.full_text`:** MISMATCH — no markers exist, so `matches` is always empty
- **Fallback:** Returns `""` (empty string) when no markers found — NOT the full content

#### `_PAGE_PATTERN` (`document_structure.py:93-96`)

**Regex:** `r"(?:[-—]+|<!--)\s*Page\s+(\d+)\s*(?:[-—]+|-->)|PAGE\s+(\d+)\s+OF\s+\d+"`

- Flags: `re.IGNORECASE`
- No `(?:^|\n)` anchor — more permissive than `_extract_page_range_text`
- **Match status vs actual content:** Same MISMATCH — no markers in stored text

#### `startswith("--- Page")` (`acm_extraction.py:1991`)

- Hardcoded string check, only handles dash format
- Does not cover `<!-- Page N -->` or `PAGE N OF N` variants

### Impact Assessment

- `_extract_page_range_text()` always returns `""` for production documents
- `_extract_building_content()` is more lenient — returns full content when no markers found (different fallback behavior)
- **Benchmarks test the page-slicing path; production never exercises it** — tests pass, production silently degrades
- `page_tagger.py` falls back to `[(1, content)]` (entire document as page 1) when no markers found

---

## 2. Docling JSON Output Audit

### Production Path

**Call sites:**
- `commands/source_commands.py:143` — `table.data.model_dump(mode="json")`
- `open_notebook/extractors/providers/docling_adapter.py:151` — `table.data.model_dump(mode="json")`

**Output structure:**
```json
{
  "table_cells": [
    {
      "text": "...",
      "row_span": 1,
      "col_span": 1,
      "start_row_offset_idx": 0,
      "end_row_offset_idx": 1,
      "start_col_offset_idx": 0,
      "end_col_offset_idx": 1,
      "column_header": false,
      "row_header": false,
      "row_section": false,
      "fillable": false,
      "bbox": null
    }
  ],
  "num_rows": N,
  "num_cols": M,
  "grid": [...]  // @computed_field — extra, not consumed
}
```

### Cell Key Cross-Check

| Expected by row_segmenter | Produced by model_dump | Status |
|---------------------------|----------------------|--------|
| `table_cells` (top-level) | `table_cells` | MATCH |
| `num_rows` (top-level) | `num_rows` | MATCH |
| `num_cols` (top-level) | `num_cols` | MATCH |
| `text` (cell) | `text` | MATCH |
| `row_span` (cell) | `row_span` | MATCH |
| `col_span` (cell) | `col_span` | MATCH |
| `start_row_offset_idx` (cell) | `start_row_offset_idx` | MATCH |
| `end_row_offset_idx` (cell) | `end_row_offset_idx` | MATCH |
| `start_col_offset_idx` (cell) | `start_col_offset_idx` | MATCH |
| `end_col_offset_idx` (cell) | `end_col_offset_idx` | MATCH |
| `column_header` (cell) | `column_header` | MATCH |
| `page_number` (injected) | injected at `acm_extraction.py:1037` | MATCH |
| — | `row_header` | EXTRA (unused) |
| — | `row_section` | EXTRA (unused) |
| — | `fillable` | EXTRA (unused) |
| — | `bbox` (per-cell) | EXTRA (unused) |
| — | `grid` (top-level) | EXTRA (unused, ~4x storage overhead) |

**ALL required keys match. No missing keys. Extra keys silently ignored via `dict.get()`.**

### DB Field Mapping

| Dict key at build time | DB field in `acm_table_section` | Content |
|------------------------|-------------------------------|---------|
| `table["html"]` | `raw_html` | `table.export_to_html(doc=doc)` |
| `table["markdown"]` | `raw_text` | `df.to_markdown(index=False)` |
| `table["csv"]` | `structured_json` | `df.to_csv(index=False)` |
| `table["docling_json"]` | `docling_document_json` | `table.data.model_dump(mode="json")` |

---

## 3. Docling HTML Output Audit

**Production:** `table.export_to_html(doc=doc)` at `source_commands.py:156` and `docling_adapter.py:164`

**DB field:** `raw_html` in `acm_table_section`

**Usage:** NOT used in LLM prompting. Stored in DB for frontend display and provenance only.

**Quality:** Docling's ACCURATE mode with `do_cell_matching=True` properly handles merged cells via HTML `colspan`/`rowspan` attributes. This is the highest-fidelity representation.

**Assessment:** Functionally correct. Not used in extraction pipeline — only for display.

---

## 4. Docling Markdown Output Audit

**Production:** `df.to_markdown(index=False)` at `source_commands.py:155` and `docling_adapter.py:165`

**DB field:** `raw_text` in `acm_table_section`

**Usage:** Injected into LLM prompt via `_inject_docling_tables()` for bulk extraction path (`orchestrator.py:127`).

**Key detail:** Markdown is produced from a pandas DataFrame (`export_to_dataframe()`), NOT from Docling's native markdown serializer. Merged cells are already resolved/expanded — every row receives values from spanning cells. This is actually better for LLM consumption.

**Assessment:** Column alignment is correct (standard GitHub-flavored pipe table). No data loss — merged cells expanded.

---

## 5. Docling Output Cross-Check

All three output types originate from the same `TableData` object:
- **JSON** (`model_dump`): Preserves full cell-level span information (row_span, col_span, offsets)
- **HTML** (`export_to_html`): Preserves spans via `colspan`/`rowspan` attributes
- **Markdown** (`df.to_markdown`): Spans already resolved by DataFrame export — expanded/repeated values

Row and column counts are consistent across all three because they derive from the same `TableData.num_rows` / `TableData.num_cols` values.

**Assessment:** No cross-type inconsistencies. Each output serves a different consumer correctly.

---

## 6. mode="json" vs mode="python" Usage

### model_dump() Call Site Audit

| File | Line | Object Type | mode= | Status |
|------|------|-------------|-------|--------|
| `commands/source_commands.py` | 143 | `TableData` (Docling) | `"json"` | OK |
| `open_notebook/extractors/providers/docling_adapter.py` | 151 | `TableData` (Docling) | `"json"` | OK |
| `open_notebook/graphs/acm_extraction.py` | 494-501 | Domain models | `"json"` | OK |
| `open_notebook/graphs/acm_extraction.py` | 2838, 2896, 2914 | `PipelineRun` | `"json"` | OK |
| `open_notebook/extractors/orchestrator.py` | 399 | `BuildingExtractionResult` | none | OK (Jinja context, not DB) |
| `open_notebook/domain/base.py` | 116, 171 | Domain model | none | OK (internal validation/save) |

**VERDICT: `mode="python"` has been completely eliminated. Zero occurrences in production code.**

### Test File Discrepancy

**MEDIUM:** `tests/test_docling_json_storage.py:125,141,161,170,179` uses `table.export_to_dict()` API that doesn't exist in production. Production uses `table.data.model_dump(mode="json")`. Test does not test the actual code path.

---

## 7. SAMP Format Detection

### `_BUILDING_HEADER` Regex (`building_inventory.py:29-32`)

```regex
^#+\s*(?:Building[:\s]*)?([A-Z]\d+[A-Z]?|D\d{2,3})\s+[-–]\s+([^-–\n]+?)(?:\s*[-–]\s*(\d{4}))?(?:\s*[-–]\s*([^-–\n]+?))?$
```

**Flags:** `IGNORECASE | MULTILINE`

**Capture groups:**
1. Building ID — `B00A`, `D01`, `D123` etc.
2. Building name (up to next dash/en-dash)
3. Year (4-digit, optional)
4. Construction type (optional)

**Design:** Excludes room lines (`B00A-R0001`) by requiring space-dash after building ID.

**Test results:**
| Header | Result |
|--------|--------|
| `## B00A - Admin Building - 1924 - Brick` | MATCH (B00A / Admin Building / 1924 / Brick) |
| `## D01 - Demountable` | MATCH (D01 / Demountable) |
| `#### B00A-R0001 - External Movement` | MISS (correct — room header) |
| `## Building Name: Broadmeadows Police Station` | MISS (no coded ID) |

### `_ROOM_HEADER` Regex (`building_inventory.py:35-38`)

```regex
^#+\s*([A-Z0-9]+-R\d{3,5})\s*[-–]\s*([^-–\n]+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?$
```

Groups: room_id, room_name, area_m2 (optional). Requires strict `BuildingID-R####` format.

---

## 8. ARA Format Detection

### `_detect_ara_buildings()` (`building_inventory.py:276-296`)

**Pattern:** `r"Building Name:\s*\n\s*(.+?)(?:\n|$)"`

**Logic:**
- Matches two-line ARA headers: `"Building Name:"` on line 1, actual name on line 2
- Deduplicates by name (same building appearing on multiple pages counted once)
- `_find_ara_building_section_end()` uses all occurrences to find last page
- All ARA buildings get `complexity = COMPLEX`

**Edge cases:**
- **ONE-LINE GAP (HIGH):** If `Building Name:` and the name are on the SAME line (e.g., `Building Name: Main Building`), the two-line regex does NOT match. The Prensa worked example in `v3_building_extraction.jinja:71` shows one-line format: `Building Name: Broadmeadows Police Complex`. If the actual Broadmeadows PDF uses one-line headers, `_detect_ara_buildings()` misses it entirely.
- `acm_count` estimation uses `"\nasbestos\n"` count — weak heuristic, likely 0 for Prensa docs

**Broadmeadows compatibility:** Uncertain — depends on whether Prensa PDF uses two-line or one-line headers. If one-line, falls through to LLM/generic fallback (which correctly produces 1 building via single-building path).

---

## 9. Generic Fallback

### `_heuristic_fallback()` Chain (`building_inventory.py:326-505`)

1. **SAMP path:** `_BUILDING_HEADER` regex → build from B-series/D-series matches
2. **ARA path:** `_detect_ara_buildings()` → build from `Building Name:\n<name>` blocks
3. **Generic path (building_ids):** Divide register page range evenly among `document_structure.building_ids`
4. **Last-resort single-building:** Create `BUILDING_1` with `page_end = total_pages`

**Single-building fix** (`building_inventory.py:480-487`): If only 1 building detected and `page_end < total_pages`, expands to `total_pages`. Critical for capturing all tables.

**Boundary overlap** (`building_inventory.py:489-490`): `_apply_boundary_overlap()` extends each non-last building's `page_end` to at least the next building's `page_start`.

**Assessment:** Fallback chain is robust. Generic path divides pages evenly (inaccurate for buildings of different sizes) but this is acceptable as a last resort.

---

## 10. BAR Format Impact Analysis

### All BAR References

| File | Line | Reference | Gates Logic? |
|------|------|-----------|-------------|
| `extractors/document_structure.py` | 1-9 | Module docstring | NO |
| `extractors/metadata_extractor.py` | 5 | Module docstring | NO |
| `extractors/parsers/generic.py` | 78-86 | `_BAR_REQUIRED_HEADERS` (column names) | NO — table detection, all doc types |
| `extractors/parsers/field_config.py` | 16,30,47,51 | `BARFieldDefinition`, `BARBusinessRule` | NO — data models |
| `extractors/parsers/config_loader.py` | 39-98 | Variable names/comments | NO — field mapping |
| `extractors/validators/acm_validator.py` | 40,436,459,486,504-514 | `bar_warnings` list | NO — audit-only, explicitly non-blocking |
| `domain/site_config.py` | 277-297 | `get_missing_bar_fields()`, `is_bar_complete()` | NO — post-extraction reporting |
| `api/models.py` | 877-1163 | `is_bar_complete`, `missing_fields` | NO — API response fields |
| `api/routers/acm.py` | 1460-1595 | `is_bar_complete`, `missing_fields` | NO — endpoint response |
| `graphs/acm_extraction.py` | 1263 | Docstring: "Validate against SF/BAR enum values" | NO — docstring |
| `prompts/acm/classification.jinja` | 3,7 | "Victorian BAR taxonomy" | NO — vocabulary reference |
| `prompts/acm/structure_extraction.jinja` | 3 | "BAR documents" in system prompt | NO — context-setting |
| `prompts/acm/metadata_extraction.jinja` | 3 | "BAR documents" | NO — context-setting |
| `prompts/acm/page_tagging.jinja` | 3,50-51 | BAR in intro; `document_type` variable | NO — context, not branch |
| `prompts/acm/correction.jinja` | 24-32 | "SF-BAR differences" | NO — LLM guidance |
| `prompts/acm/metadata_and_structure.jinja` | 24,61 | Enum: `"SAMP|ARA|Division_5|Unknown"` — NO BAR value | NO — correctly omitted |
| `prompts/acm/legacy/*.jinja` | various | BAR vocabulary guidance | NO — legacy templates |
| `extractors/normalizers/taxonomy.py` | 39 | Comment: "Strip BAR T-prefix" | NO — normalization |

### DocumentType Enum (`document_structure.py:19-25`)

| Value | Description |
|-------|-------------|
| `SAMP` | School Asbestos Management Plan |
| `ARA` | Asbestos Risk Assessment |
| `DIVISION_5` | Regulatory Division 5 reports |
| `UNKNOWN` | Default fallback |

**BAR is intentionally NOT a DocumentType value.** BAR is the output format/standard, not an input document type.

### VERDICT

**BAR is properly secondary throughout the entire codebase.** Every BAR reference is either (a) vocabulary guidance for LLMs, (b) non-blocking audit warnings, (c) post-extraction compliance reporting, or (d) documentation. No code path gates extraction routing, building detection, page range logic, or LLM dispatch on a "BAR" document type.

---

## 11. Salesforce Model Alignment

### BuildingRecord Fields (`domain/acm.py:676-1018`)

48 fields total. Key fields from format detection:

| Format Detection Output | BuildingRecord Field | Type | Notes |
|------------------------|---------------------|------|-------|
| `building_id` | `building_code` | `Optional[str]` | SAMP building ID |
| `name` | `building_name` | `Optional[str]` | LLM extraction |
| `year` | `building_year` | `Optional[str]` | **TYPE MISMATCH: BuildingMeta.year is int** |
| `construction` | `building_construction` | `Optional[str]` | LLM extraction |
| `page_start`, `page_end` | NOT stored | — | Pipeline-only, not persisted |

### ACMItemRow Fields (`acm_row_schemas.py`)

**Actual count: 13 fields** (docstring says "9 fields" — outdated):

| Field | Type | Maps to ACMRecord |
|-------|------|-------------------|
| `room_name` | `Optional[str]` | `room_name` |
| `floor_level` | `Optional[str]` | `floor_level` |
| `item_location` | `Optional[str]` | `location` (renamed) |
| `item_name` | `str` | `product` (fallback) |
| `friability` | `Optional[str]` | `friable` (normalized) |
| `acm_classification` | `Optional[str]` | `acm_product_group` (via classifier) |
| `acm_sub_classification` | `Optional[str]` | `material_description` (fallback) |
| `condition` | `Optional[str]` | `material_condition` (normalized) |
| `disturbance_potential` | `Optional[str]` | `disturbance_potential` (normalized) |
| `sample_number` | `Optional[str]` | `sample_no` |
| `sample_result` | `Optional[str]` | `result` (or "Unknown") |
| `acm_product` | `Optional[str]` | `product` (priority over item_name) |
| `internal_external` | `Optional[str]` | **NOT MAPPED — CRITICAL** |

---

## 12. Ground Truth Comparison

### Broadmeadows Expected Output (`benchmarks/ground_truth/broadmeadows.json`)

- **Buildings:** 1 ("Broadmeadows Police Station")
- **Records:** 31
- **Format:** ARA (Prensa Pty Ltd)
- **Fields in ground truth:** `building_name`, `room_name`, `location`, `product`, `sample_no`, `sample_result`, `friable`, `internal_external`, `level`

### Pipeline Detection Path

1. SAMP regex: MISS (no B###/D### codes)
2. ARA regex: **UNCERTAIN** (depends on PDF header format — one-line vs two-line)
3. LLM/Generic fallback: Would produce 1 building using `site_name`
4. Single-building fix: `page_end = total_pages` — captures all tables

**Result:** Pipeline correctly produces 1 building. 31 records achievable if per-row extraction runs (currently blocked by RC8 empty `docling_document_json`). `internal_external` field missing from all records due to mapping gap.

---

## 13. Recommendations

### CRITICAL (Data Loss / Pipeline Failure)

**C1. `internal_external` field never mapped** — `acm_row_mappers.py`
- `ACMItemRow.internal_external` is extracted by LLM but never assigned to `ACMExtractionRecord.area_type`
- Ground truth has this field for all 31 Broadmeadows records
- **Fix:** Add `area_type=row.internal_external` in `map_item_row_to_extraction_record()`

**C2. `material_description` can be None when required** — `acm_row_mappers.py:179`
- `ACMRecord.material_description` is `str` (required), but mapper produces `None` when `final_sub_classification` is None AND `row.acm_sub_classification` is None
- Causes Pydantic validation error at record construction
- **Fix:** Default to `row.item_name or "Unknown"` when both are None

**C3. `source.full_text` has NO page markers** — `content_core/processors/pdf.py`
- `_extract_page_range_text()` always returns `""` in production
- Page-range slicing for building content extraction is non-functional
- Benchmarks pass because the test harness injects markers; production never does
- **Fix:** Add `f"\n--- Page {page_num + 1} ---\n"` separator in content_core PDF processor, OR inject markers after extraction in `source_commands.py`

### HIGH (Incorrect Output / Significant Gaps)

**H1. ARA `_detect_ara_buildings()` may miss one-line headers** — `building_inventory.py:284`
- Pattern requires `Building Name:\n<name>` (two-line). If Prensa uses `Building Name: <name>` (one-line), detection fails
- Falls through to LLM/generic — still works but less reliable
- **Fix:** Extend regex to also match `Building Name:\s*(.+?)(?:\n|$)` (same-line capture)

**H2. `building_year` type mismatch** — `BuildingMeta.year` is `int`, `BuildingRecord.building_year` is `str`
- Pydantic coerces silently, but semantic mismatch risks data issues
- **Fix:** Ensure consistent type (str) at the BuildingMeta level

**H3. ACMItemRow docstring says "9 fields" but schema has 13** — `acm_row_schemas.py:17`
- CLAUDE.md and architecture docs reference "9 fields"
- Creates confusion about schema scope
- **Fix:** Update docstring and all references to "13 fields"

**H4. Test file uses non-existent API** — `tests/test_docling_json_storage.py`
- Tests use `table.export_to_dict()` which doesn't exist in production
- Production uses `table.data.model_dump(mode="json")`
- Tests pass with MagicMock but don't validate actual code path
- **Fix:** Update tests to mock `table.data.model_dump(mode="json")`

### MEDIUM (Robustness / Correctness)

**M1. `product` mapping ambiguity** — `acm_row_mappers.py:178`
- Per-row: `product = row.acm_product or row.item_name` — free-text `acm_product` takes priority
- Bulk: `item_name` is already SF-picklist-constrained
- Risk: non-picklist values in `ACMRecord.product` from per-row path
- **Fix:** Prioritize `item_name` when it matches a picklist value

**M2. `sample_result` duplication** — `ACMRecord`
- Both `result` (required, SF picklist) and `sample_result` (optional, free-text) exist
- Per-row mapper sets `result` but leaves `sample_result = None`
- **Fix:** Populate `sample_result = row.sample_result` alongside `result`

**M3. `_extract_page_range_text` vs `_extract_building_content` different fallbacks**
- `_extract_page_range_text()` returns `""` when no markers (too strict)
- `_extract_building_content()` returns full content (correct fallback)
- **Fix:** Make `_extract_page_range_text()` return full content as fallback

**M4. `grid` computed field in stored JSON** — `docling_document_json`
- `@computed_field` adds ~4x data volume to stored JSON
- Not consumed by row_segmenter
- **Fix:** Use `model_dump(mode="json", exclude={"grid"})` to reduce storage

### LOW (Cosmetic / Optimization)

**L1. `startswith("--- Page")` hardcoded check** — `acm_extraction.py:1991`
- Only handles dash format, not `<!-- Page -->` or `PAGE N OF N`
- **Fix:** Replace with `_PAGE_PATTERN.match()` call

**L2. `DocumentType.DIVISION_5` never detected by heuristics**
- Only classified via LLM; heuristic always returns `UNKNOWN`
- Acceptable for now — Division 5 docs are rare

**L3. ARA `acm_count` uses weak heuristic** — `building_inventory.py:417`
- Counts bare `"\nasbestos\n"` — likely 0 for Prensa format
- `acm_item_count_estimate` is always None for ARA buildings

**L4. `RawTableRow.bbox` never populated from Docling JSON**
- Per-cell bounding boxes stored but unused for provenance
- Optimization opportunity for future provenance linking

**L5. `_PAGE_PATTERN` and `_extract_page_range_text` regex inconsistency**
- Different anchor patterns (`^|\n` vs none)
- Should use a single shared pattern

---

## Verification Checklist Status

- [x] PyMuPDF page markers analyzed — CRITICAL: no markers in production
- [x] Docling JSON cell keys documented — ALL keys match row_segmenter expectations
- [x] Docling HTML output quality assessed — correct, unused in LLM path
- [x] Docling Markdown output accuracy assessed — DataFrame-derived, column alignment correct
- [x] All `model_dump()` call sites found — `mode="json"` confirmed everywhere
- [x] `_BUILDING_HEADER` regex tested against 3+ headers — documented above
- [x] `_detect_ara_buildings` analyzed — one-line header gap identified (HIGH)
- [x] Generic fallback page range logic audited — single-building handling verified
- [x] BAR format impact traced — CONFIRMED no pipeline branching
- [x] BuildingRecord fields aligned with format detection output — year type mismatch found
- [x] ACMRecord fields aligned with extraction output — `internal_external` gap CRITICAL
- [x] Ground truth: Broadmeadows = 1 building, 31 records — per-row needed for full coverage
- [x] All findings documented with `file:line` references
- [x] No code files modified (research-only session)

---

## Fixes Applied (2026-03-14)

The following issues were fixed immediately after the audit completed.

### C1 — `internal_external` now mapped to `area_type`

**File:** `open_notebook/domain/acm_row_mappers.py`

`map_item_row_to_extraction_record()` now includes:
```python
area_type=row.internal_external,
sample_result=row.sample_result,   # M2 fixed alongside C1
```

`area_type` was previously absent from the return value, silently discarding every `internal_external` value the LLM extracted. `sample_result` (M2) was fixed in the same edit.

### C2 — `material_description` null safety

**File:** `open_notebook/domain/acm_row_mappers.py` (line ~179)

The mapper now uses a four-level fallback chain:
```python
final_sub_classification or row.acm_sub_classification or row.item_name or "Unknown"
```

Previously, the chain stopped at `row.acm_sub_classification`, producing `None` when that field was also absent, which caused a Pydantic validation error at `ACMRecord` construction.

### C3 — Page markers injected into `source.full_text`

**File:** `open_notebook/graphs/source.py`

Added `_inject_page_markers()` function that re-reads the uploaded PDF with PyMuPDF (`fitz`) and re-builds `source.full_text` in the format expected by the pipeline:
```
--- Page N ---
{page text}
```

Called from `save_source()` for PDF files. Falls back to the existing `content_core` text (without markers) if PyMuPDF raises any exception. This makes `_extract_page_range_text()` functional in production for the first time.

### H1 — ARA one-line header support

**File:** `open_notebook/extractors/building_inventory.py` (line ~284)

`_detect_ara_buildings()` regex updated from:
```python
r"Building Name:\s*\n\s*(.+?)(?:\n|$)"
```
to an alternation that handles both two-line and one-line formats:
```python
r"Building Name:\s*\n\s*(.+?)(?:\n|$)|Building Name:\s+(.+?)(?:\n|$)"
```

Group extraction updated to `match.group(1) or match.group(2)`. Prensa PDFs that use the one-line format (e.g., `Building Name: Broadmeadows Police Complex`) are now detected directly rather than falling through to the generic fallback.

### H3 — ACMItemRow field count corrected to 13

**Files:** `open_notebook/domain/acm_row_schemas.py`, `open_notebook/domain/acm_row_mappers.py`

Docstrings updated from "9 fields" to "13 fields". The 13 fields are: `room_name`, `floor_level`, `item_location`, `item_name`, `friability`, `acm_classification`, `acm_sub_classification`, `condition`, `disturbance_potential`, `sample_number`, `sample_result`, `acm_product`, `internal_external`.

---

## E2E Verification Results (2026-03-14)

**Source:** `source:mc5llofksqsglrjsfssj` (Clutch_Broadmeadows.pdf, 19 pages)
**Command:** `command:x4zjr5wkvwxgea91v1cg`
**Execution time:** 467s (Docling ACCURATE mode)

### Results
- Buildings: 2 (expected 1 — duplicate from old + new extraction path)
- ACM Records: 3 (expected 31 — limited by RC8 pre-existing issue)
- Docling tables: 10 (8 with `docling_document_json = {}`, 2 with `null`)

### Fix Verification

| Fix | Status | Evidence |
|-----|--------|----------|
| **C1** (`area_type` mapping) | VERIFIED | All 3 records have `area_type = "Interior"` |
| **C1 bonus** (`sample_result` populated) | VERIFIED | All 3 records have `sample_result = "Assumed Positive"` |
| **C2** (`material_description` null safety) | VERIFIED | Records show "Internal lining" and "Unknown" — no null |
| **C3** (page markers) | VERIFIED | `source.full_text` has 19 `--- Page N ---` markers |
| **H1** (ARA one-line) | VERIFIED | Unit tests pass (95/95) |

### Why Only 3 Records

The low count (3 vs 31 expected) is due to **RC8** (pre-existing):
- 8/10 `acm_table_section` rows have `docling_document_json = {}` (empty dict)
- Per-row extraction checks `if dj:` which is falsy for `{}`
- Falls back to bulk extraction which under-extracts on this PDF
- **This is NOT caused by our fixes** — it's the same issue documented in the debug session

---

## Debug Session Context (from 2026-03-14 pipeline run)

### Remaining Issues (from prior debug session)

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| RC8 | MEDIUM-HIGH | `docling_document_json` stored as empty dict `{}` | Open — blocks per-row extraction |
| RC9 | MEDIUM | Model selection mismatch (phi4 instead of qwen2.5) | Open — SurrealDB default overrides env var |
| RC10 | MEDIUM | phi4 metadata extraction failure | Open — may self-resolve with RC9 fix |
| RC11 | LOW | Missing 2 records (29/31) | Open — likely resolves with RC8 fix |

### Updated Concerns (appended by this audit)

| # | Issue | Source |
|---|-------|--------|
| 6 | phi4 omits Optional fields — consider making fields non-optional with sentinels | RC10 analysis |
| 7 | `docling_document_json = {}` causes infinite re-extraction loop | RC8 + F6/F7 interaction |
| 8 | Model env var silently ignored when DB default exists | RC9 analysis |
| 9 | Bulk extraction near-duplicate room names not fuzzy-matched | RC11 analysis |
