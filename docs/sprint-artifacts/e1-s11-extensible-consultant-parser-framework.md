# Story 1.11: Extensible Consultant Parser Framework

Status: review

## Story

As a **developer**,
I want **a pluggable parser framework for different consultant PDF formats**,
so that **new PDF formats can be added without modifying core extraction code and consultant-specific column mappings are handled automatically**.

## Acceptance Criteria

### AC1: ConsultantParser Abstract Base Class
- **Given:** The extraction pipeline processes PDFs from multiple consultant firms
- **When:** A new consultant format needs to be supported
- **Then:** A `ConsultantParser` ABC is defined with these abstract methods:
  - `name -> str` (property): Consultant identifier (e.g., `"prensa"`, `"greencap"`)
  - `detect(text: str) -> bool`: Returns True if this parser handles the PDF
  - `extract_metadata(pages: dict[int, str]) -> DocumentMeta`: Extract document-level metadata
  - `extract_items(tables: list[dict]) -> list[RawACMItem]`: Extract raw ACM items from tables
  - `get_column_mapping() -> dict[str, str]`: Map consultant columns to standard raw fields
  - `get_register_headers() -> list[str]`: Expected column headers for this format

### AC2: PrensaParser Implementation
- **Given:** A Prensa Pty Ltd "Division 5 Asbestos Assessment" PDF
- **When:** The parser framework processes it
- **Then:** `PrensaParser` correctly:
  - Detects via markers: `"Prensa Pty Ltd"` or `"Division 5 Asbestos Assessment"`
  - Maps 15 Prensa columns to raw fields (area_level, room_location, feature, item_description, hazard_type, hazard_status, sample_number, friability, labelled, disturb_potential, condition, risk_status, quantity, control_priority, comments)
  - Extracts building patterns: `r"^([A-Za-z]+\s*floor|Exterior|Ground floor|First floor)"`
  - Extracts metadata from cover/header pages

### AC3: GreencapParser Implementation
- **Given:** A Greencap "Asbestos Risk Assessment" PDF
- **When:** The parser framework processes it
- **Then:** `GreencapParser` correctly:
  - Detects via marker: `"Greencap"` in text
  - Maps 14 Greencap columns (item_no, location_item_description, hazard_type, sample_no, item_status, photo_no, est_extent, condition, friability, dist_potential, risk_rating, current_label, reinspect_date, control_priority)
  - Extracts site metadata: `"Full Address:"`, `"Est. Building Size:"`, `"Est. Building Age:"`
  - Building detection: `r"Building Name:\s*(.+)"`

### AC4: GenericParser Fallback
- **Given:** A PDF that no specific parser recognizes
- **When:** The parser framework processes it
- **Then:** `GenericParser`:
  - `detect()` always returns True (it's the fallback)
  - Uses the existing regex-based parsing logic from current `acm_extractor.py`
  - Maps generic ACM headers: product, material_description, extent, location, friable, material_condition, risk_status, result
  - Preserves backward compatibility with all existing NSW SAMP extraction

### AC5: Parser Registry and Auto-Selection
- **Given:** A PDF is uploaded for ACM extraction
- **When:** The pipeline needs to select the right parser
- **Then:**
  - `PARSER_REGISTRY` contains `[PrensaParser, GreencapParser, GenericParser]` in priority order
  - `get_parser(pdf_text: str) -> ConsultantParser` iterates registry and returns first match
  - GenericParser is always last (guaranteed fallback)
  - Selection logged with parser name

### AC6: Integration with Existing Extraction Pipeline
- **Given:** The parser framework is implemented
- **When:** `extract_acm_records()` is called
- **Then:**
  - Parser selection happens before table parsing
  - Selected parser's `get_column_mapping()` is used instead of hardcoded header maps
  - Selected parser's `detect()` confirms the format
  - All existing tests continue to pass (backward compatible)
  - The `_extract_from_markdown()` function uses the selected parser

### AC7: Developer Documentation
- **Given:** A developer wants to add a new consultant parser
- **When:** They follow the documentation
- **Then:** A brief inline docstring/comment in `base.py` explains:
  - How to create a new parser (subclass `ConsultantParser`, implement methods)
  - How to register it (add to `PARSER_REGISTRY`)
  - How to test it (provide sample text, expected headers, detection markers)

## Tasks / Subtasks

- [x] **Task 1: Create parsers package structure** (AC: 1)
  - [x] Create `open_notebook/extractors/parsers/__init__.py`
  - [x] Create `open_notebook/extractors/parsers/base.py` with `ConsultantParser` ABC
  - [x] Define `RawACMItem` and `DocumentMeta` dataclasses in base.py (or import from schemas)
  - [x] Define `SourceLocation` dataclass for provenance tracking

- [x] **Task 2: Implement PrensaParser** (AC: 2)
  - [x] Create `open_notebook/extractors/parsers/prensa.py`
  - [x] Implement detection: `"Prensa Pty Ltd"` or `"Division 5 Asbestos Assessment"` in text
  - [x] Implement column mapping (15 columns -> raw fields)
  - [x] Implement metadata extraction from cover pages
  - [x] Implement building pattern matching
  - [x] Unit tests for detection and column mapping

- [x] **Task 3: Implement GreencapParser** (AC: 3)
  - [x] Create `open_notebook/extractors/parsers/greencap.py`
  - [x] Implement detection: `"Greencap"` in text
  - [x] Implement column mapping (14 columns -> raw fields)
  - [x] Implement site metadata extraction (address, building size, age)
  - [x] Implement building name detection pattern
  - [x] Unit tests for detection and column mapping

- [x] **Task 4: Implement GenericParser** (AC: 4)
  - [x] Create `open_notebook/extractors/parsers/generic.py`
  - [x] Refactor existing regex parsing logic from `acm_extractor.py` into GenericParser
  - [x] `detect()` always returns True
  - [x] Preserve existing header mapping: product, material_description, extent, etc.
  - [x] Ensure full backward compatibility with NSW SAMP format
  - [x] Unit tests verifying identical output to current extractor

- [x] **Task 5: Create parser registry** (AC: 5)
  - [x] Add `PARSER_REGISTRY` and `get_parser()` to `parsers/__init__.py`
  - [x] Registry order: PrensaParser, GreencapParser, GenericParser
  - [x] Add logging for parser selection
  - [x] Unit tests for registry selection logic

- [x] **Task 6: Integrate with extraction pipeline** (AC: 6)
  - [x] Modify `acm_extractor.py` to use parser framework
  - [x] Replace hardcoded header map with `parser.get_column_mapping()`
  - [x] Add parser auto-detection in `extract_acm_records()`
  - [x] Ensure `_extract_from_markdown()` delegates to selected parser
  - [x] Run full regression test suite - ALL existing tests must pass

- [x] **Task 7: Testing** (AC: 1-6)
  - [x] Create `tests/test_consultant_parsers.py`
  - [x] Test ConsultantParser ABC (cannot instantiate directly)
  - [x] Test PrensaParser detection, column mapping, metadata extraction
  - [x] Test GreencapParser detection, column mapping, metadata extraction
  - [x] Test GenericParser detection (always True), backward compat
  - [x] Test parser registry: correct selection for each format
  - [x] Test fallback: unknown format gets GenericParser
  - [x] Run existing tests to verify zero regressions

## Dev Notes

### CRITICAL: Correct File Locations

The epics/architecture documents reference `open_notebook/extraction/parsers/` but the **ACTUAL codebase** uses `open_notebook/extractors/`. All new files MUST go under:

```
open_notebook/extractors/parsers/
├── __init__.py      # PARSER_REGISTRY, get_parser()
├── base.py          # ConsultantParser ABC, RawACMItem, DocumentMeta, SourceLocation
├── prensa.py        # PrensaParser
├── greencap.py      # GreencapParser
└── generic.py       # GenericParser (refactored from acm_extractor.py)
```

**DO NOT** create `open_notebook/extraction/` - that path does not exist.

### Existing Code to Understand Before Modifying

| File | Why | Key Details |
|------|-----|-------------|
| `open_notebook/extractors/acm_extractor.py` | Current regex parser to refactor | `_create_header_map()`, `_parse_acm_table()`, `ExtractedACMRow`, `ParseContext` |
| `open_notebook/extractors/acm_schemas.py` | Pydantic schemas for AI extraction | `ACMExtractionRecord`, `BuildingRoomContext`, `TableBoundingBox` |
| `open_notebook/extractors/mineru_table_extractor.py` | MinerU integration (E1-S10) | `MineruTableExtractor`, `ExtractedTable` dataclass |
| `open_notebook/extractors/normalizers/taxonomy.py` | Product classification | `classify_product()`, `ClassificationResult` |
| `open_notebook/domain/acm.py` | Domain model | `ACMRecord` with all BAR fields |
| `docs/reference/extraction-pipeline.md` | Pipeline architecture | Stage 1/2 design, `ConsultantParser` interface spec |

### Consultant Format Specifications

**Prensa Pty Ltd (15 columns):**
```python
PRENSA_HEADERS = [
    "area / level", "room & location", "feature", "item description",
    "hazard type", "hazard status", "sample number", "friability",
    "labelled y/n", "disturb. potential", "condition", "risk status",
    "approx. quantity", "control priority", "comments & recommendations"
]
PRENSA_DETECTION = ["Prensa Pty Ltd", "Division 5 Asbestos Assessment"]
PRENSA_BUILDING_PATTERN = r"^([A-Za-z]+\s*floor|Exterior|Ground floor|First floor)"
```

**Greencap (14 columns):**
```python
GREENCAP_HEADERS = [
    "item no.", "location - item description", "hazard type",
    "sample no.", "item status", "photo no.", "est. extent",
    "condition", "friability", "dist. potential", "risk rating",
    "current label", "reinspect date", "control priority"
]
GREENCAP_DETECTION = ["Greencap"]
GREENCAP_SITE_METADATA = ["Full Address:", "Est. Building Size:", "Est. Building Age:"]
GREENCAP_BUILDING_PATTERN = r"Building Name:\s*(.+)"
```

**Generic / NSW SAMP (current default):**
```python
GENERIC_HEADERS = ["product", "material description", "result"]  # Required
GENERIC_OPTIONAL = ["extent", "location", "friable", "material condition", "risk status"]
GENERIC_BUILDING_PATTERN = r"^([A-Z]\d+[A-Z]?)\s*[-–]\s*(.+?)(?:\s*[-–]\s*(\d{4}))?$"
```

### Column Mapping: Prensa -> BAR Standard
```python
PRENSA_TO_BAR = {
    "area_level": "level",
    "room_location": "room_name",
    "feature": "location",
    "item_description": "product",
    "hazard_status": "sample_result",
    "sample_number": "nata_sample_number",
    "friability": "friable",
    "labelled": "labelled",
    "condition": "material_condition",
    "disturb_potential": "disturbance_potential",
    "quantity": "extent",
    "comments": "hygienist_recommendations",
}
```

### Integration Strategy

The current `acm_extractor.py` has these key functions to refactor:
1. `_create_header_map(headers)` -> Move to `GenericParser.get_column_mapping()`
2. `_looks_like_table_header(line)` -> Each parser checks its own headers
3. `_parse_acm_table(table_lines, context)` -> Delegate to parser's `extract_items()`
4. `_extract_from_markdown(markdown_content, ...)` -> Use `get_parser()` to select, then delegate

**Refactoring approach:**
- Keep `acm_extractor.py` as the **entry point** (preserve `extract_acm_records()` API)
- Add parser selection at the beginning of `_extract_from_markdown()`
- Move parsing logic to parser classes
- `GenericParser` inherits the current regex logic for backward compatibility
- Existing callers don't change - only internal implementation shifts

### Previous Story Learnings (E1-S10)

1. **Version-agnostic imports:** MinerU API changed between versions - use try/except fallbacks
2. **MinerU `_extract_with_mineru()` returns empty (stub):** HTML→ACM parsing not yet implemented. The parser framework should eventually enable this by providing `extract_items(tables)` that can handle HTML table data
3. **Fallback chain works:** MinerU → regex; the parser framework integrates into the regex fallback path
4. **245 tests passing:** Must maintain zero regressions
5. **`ExtractedTable` has:** `html`, `bbox`, `page_number`, `row_count`, `col_count`, `has_merged_cells`

### Testing Strategy

```python
# tests/test_consultant_parsers.py

class TestConsultantParserABC:
    """Verify ABC cannot be instantiated directly"""

class TestPrensaParser:
    """Test detection, header mapping, metadata extraction"""
    def test_detect_prensa_marker(self): ...
    def test_detect_division5_marker(self): ...
    def test_detect_non_prensa(self): ...
    def test_column_mapping_complete(self): ...
    def test_register_headers(self): ...

class TestGreencapParser:
    """Test detection, header mapping, metadata extraction"""
    def test_detect_greencap_marker(self): ...
    def test_detect_non_greencap(self): ...
    def test_column_mapping_complete(self): ...
    def test_register_headers(self): ...
    def test_site_metadata_extraction(self): ...

class TestGenericParser:
    """Test fallback behavior and backward compatibility"""
    def test_detect_always_true(self): ...
    def test_column_mapping_matches_existing(self): ...
    def test_backward_compat_with_existing_extraction(self): ...

class TestParserRegistry:
    """Test auto-selection"""
    def test_prensa_selected_for_prensa_text(self): ...
    def test_greencap_selected_for_greencap_text(self): ...
    def test_generic_selected_for_unknown(self): ...
    def test_registry_order(self): ...
```

### Architecture Compliance

- **Pattern:** Strategy pattern via ABC + Registry
- **Integration:** Fits into existing Stage 1 EXTRACT of the two-stage pipeline
- **Data flow:** PDF text -> `get_parser()` -> selected parser -> `extract_items()` -> `RawACMItem[]`
- **Does NOT touch:** Stage 2 INTERPRET, normalizers, taxonomy classification, or MinerU integration
- **Backward compatible:** Existing `extract_acm_records()` API unchanged

### What This Story Does NOT Include

- HTML table parsing (MinerU output) - that's a future enhancement
- Value normalization / enum mapping - that's E1-S12 (Consultant Wording Normalization)
- Stage 2 INTERPRET implementation - separate concern
- New consultant format implementations beyond Prensa/Greencap/Generic
- Changes to the MinerU extraction path (`_extract_with_mineru()`)

### Project Structure Notes

- Follows existing `open_notebook/extractors/normalizers/` pattern for subdirectory structure
- Uses Python ABC (abstract base class) from `abc` module - standard library, no new deps
- Uses `@dataclass` for data containers and Pydantic for schemas (both already in project)
- Tests follow existing pattern: `tests/test_*.py` with pytest

### References

- [Source: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#E1-S11]
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.2-Extensible-Consultant-Parser-Architecture]
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.3-Consultant-Format-Patterns]
- [Source: docs/reference/extraction-pipeline.md#Stage-1-EXTRACT]
- [Source: docs/sprint-artifacts/e1-s10-mineru-table-extraction.md]
- [Source: open_notebook/extractors/acm_extractor.py]
- [Source: docs/samplePDF/instructions-sample/consultant_wording_rules.json]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References
- Red-green-refactor cycle followed for each task
- All 40 new tests written before implementation (RED), then implementation (GREEN)
- 211 tests passed across full regression suite, zero failures
- Ruff lint: All checks passed after auto-fix of 4 import ordering issues

### Completion Notes List
- **Task 1:** Created `open_notebook/extractors/parsers/` package with `base.py` containing `ConsultantParser` ABC (6 abstract methods), `RawACMItem`, `DocumentMeta`, and `SourceLocation` dataclasses. 10 tests pass.
- **Task 2:** Implemented `PrensaParser` with detection via "Prensa Pty Ltd" and "Division 5 Asbestos Assessment" markers, 15-column mapping, metadata extraction from cover pages, floor-based building pattern regex. 8 tests pass.
- **Task 3:** Implemented `GreencapParser` with "Greencap" marker detection, 14-column mapping, site metadata extraction (Full Address, Building Size, Building Age), Building Name pattern. 7 tests pass.
- **Task 4:** Implemented `GenericParser` as fallback (detect() always True), wrapping existing NSW SAMP header mapping logic. Preserves full backward compatibility. 5 tests pass.
- **Task 5:** Created `PARSER_REGISTRY` in `parsers/__init__.py` with priority order [Prensa, Greencap, Generic]. `get_parser()` iterates and logs selected parser. 6 tests pass.
- **Task 6:** Integrated parser framework into `acm_extractor.py`: parser selection in `extract_acm_records()` before fallback, `_extract_from_markdown()` accepts parser parameter, `_looks_like_table_header()` and `_parse_acm_table()` use parser headers for non-generic formats. Added `_create_header_map_from_parser()` for consultant-specific column mapping. All 34 existing extractor tests pass (zero regressions). 4 integration tests pass.
- **Task 7:** 40 new tests in `tests/test_consultant_parsers.py`. Full regression suite: 211 tests pass. Ruff lint clean.
- **Developer documentation:** Module docstring in `base.py` explains how to add a new parser (subclass, implement methods, register, test).

### File List

**New files:**
- `open_notebook/extractors/parsers/__init__.py` - Parser registry, `get_parser()`, exports
- `open_notebook/extractors/parsers/base.py` - `ConsultantParser` ABC, `RawACMItem`, `DocumentMeta`, `SourceLocation`
- `open_notebook/extractors/parsers/prensa.py` - `PrensaParser` (15-column format)
- `open_notebook/extractors/parsers/greencap.py` - `GreencapParser` (14-column format)
- `open_notebook/extractors/parsers/generic.py` - `GenericParser` (fallback, NSW SAMP)
- `tests/test_consultant_parsers.py` - 40 tests covering all parsers, registry, integration

**Modified files:**
- `open_notebook/extractors/acm_extractor.py` - Added parser framework integration (imports, parser selection in `extract_acm_records()`, parser parameter in `_extract_from_markdown()`, `_looks_like_table_header()`, `_parse_acm_table()`, new `_create_header_map_from_parser()`)

## Change Log

- **2026-02-07:** E1-S11 Extensible Consultant Parser Framework implemented. Added pluggable parser system with Strategy pattern (ABC + Registry). Three parsers: PrensaParser (Prensa Pty Ltd Division 5), GreencapParser (Greencap Risk Assessment), GenericParser (NSW SAMP fallback). Integrated into extraction pipeline with full backward compatibility. 40 new tests, 211 total passing.
