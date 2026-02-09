"""
Unit tests for the ACM Register extraction module.

Tests the extraction of ACM records from Docling markdown output,
including table detection, header parsing, and row extraction.
Also tests the fallback mechanism from MinerU to markdown parsing.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestExtractACMRecords:
    """Test suite for the main extract_acm_records function."""

    def test_extract_empty_content_returns_empty_list(self):
        """Test that empty markdown returns empty list."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records("", "source:123")
        assert result == []

        result = extract_acm_records(None, "source:123")
        assert result == []

    def test_extract_simple_acm_table(self):
        """Test extraction of a simple ACM table."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# Test School - Asbestos Register

## Building: B00A - Admin Block - 1924

#### Room: B00A-R0001 - Main Office - 45.5m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Tiles | Vinyl asbestos tiles | 50m² | Floor | Non Friable | Good | Low | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 1
        record = result[0]
        assert record["source_id"] == "source:123"
        assert record["school_name"] == "Test School"
        assert record["building_id"] == "B00A"
        assert record["building_name"] == "Admin Block"
        assert record["building_year"] == 1924
        assert record["room_id"] == "B00A-R0001"
        assert record["room_name"] == "Main Office"
        assert record["room_area"] == 45.5
        assert record["product"] == "Floor Tiles"
        assert record["material_description"] == "Vinyl asbestos tiles"
        assert record["result"] == "Positive"  # "Detected" normalized to BAR canonical

    def test_extract_multiple_rows_same_room(self):
        """Test extraction of multiple rows within same room context."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School Name

## Building: B01 - Block A

#### Room: B01-R001 - Office

| Product | Material Description | Result |
|---------|---------------------|--------|
| Floor Tiles | Vinyl tiles | Detected |
| Pipe Lagging | ACM insulation | Detected |
| Ceiling Tiles | Acoustic tiles | Not Detected |
"""
        result = extract_acm_records(markdown, "source:456")

        assert len(result) == 3
        # All should have same building/room context
        for record in result:
            assert record["building_id"] == "B01"
            assert record["room_id"] == "B01-R001"

        assert result[0]["product"] == "Floor Tiles"
        assert result[1]["product"] == "Pipe Lagging"
        assert result[2]["product"] == "Ceiling Tiles"

    def test_handles_no_asbestos_detected(self):
        """Test that 'No Asbestos Detected' is normalized to 'Not Detected'."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block

#### Room: R1 - Room

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Floor covering | No Asbestos Detected |
"""
        result = extract_acm_records(markdown, "source:789")

        assert len(result) == 1
        assert (
            result[0]["result"] == "Negative"
        )  # "Not Detected" normalized to BAR canonical

    def test_skips_non_acm_tables(self):
        """Test that tables without ACM headers are skipped."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# Document

## Some Section

| Name | Date | Status |
|------|------|--------|
| John | 2024 | Active |

## Building: B1 - Block

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        # Should only extract from ACM table, not the first table
        assert len(result) == 1
        assert result[0]["product"] == "Tiles"


class TestBuildingHeaderParsing:
    """Test suite for building header regex patterns."""

    def test_building_pattern_with_year(self):
        """Test building pattern with year."""
        from open_notebook.extractors.acm_extractor import BUILDING_PATTERN

        line = "## Building: B00A - Admin Block - 1924"
        match = BUILDING_PATTERN.match(line)

        assert match is not None
        assert match.group(1) == "B00A"
        assert match.group(2) == "Admin Block"
        assert match.group(3) == "1924"

    def test_building_pattern_without_year(self):
        """Test building pattern without year."""
        from open_notebook.extractors.acm_extractor import BUILDING_PATTERN

        line = "## B01 - Main Building"
        match = BUILDING_PATTERN.match(line)

        assert match is not None
        assert match.group(1) == "B01"
        assert match.group(2) == "Main Building"
        assert match.group(3) is None

    def test_building_pattern_with_construction_type(self):
        """Test building pattern with construction type after year."""
        from open_notebook.extractors.acm_extractor import BUILDING_PATTERN

        line = "### B02A - Science Block - 1965 - Brick"
        match = BUILDING_PATTERN.match(line)

        assert match is not None
        assert match.group(1) == "B02A"
        assert match.group(2) == "Science Block"
        assert match.group(3) == "1965"
        assert match.group(4) == "Brick"


class TestRoomHeaderParsing:
    """Test suite for room header regex patterns."""

    def test_room_pattern_with_area(self):
        """Test room pattern with area."""
        from open_notebook.extractors.acm_extractor import ROOM_PATTERN

        line = "#### Room: B00A-R0001 - Main Office - 45.5m²"
        match = ROOM_PATTERN.match(line)

        assert match is not None
        assert match.group(1) == "B00A-R0001"
        assert match.group(2) == "Main Office"
        assert match.group(3) == "45.5"

    def test_room_pattern_without_area(self):
        """Test room pattern without area."""
        from open_notebook.extractors.acm_extractor import ROOM_PATTERN

        line = "#### B01-R001 - Storage Room"
        match = ROOM_PATTERN.match(line)

        assert match is not None
        assert match.group(1) == "B01-R001"
        assert match.group(2) == "Storage Room"
        assert match.group(3) is None


class TestAreaTypeParsing:
    """Test suite for area type header parsing."""

    def test_area_type_interior(self):
        """Test parsing Interior area type."""
        from open_notebook.extractors.acm_extractor import AREA_TYPE_PATTERN

        line = "### Area Type: Interior"
        match = AREA_TYPE_PATTERN.match(line)

        assert match is not None
        assert match.group(1).lower() == "interior"

    def test_area_type_exterior(self):
        """Test parsing Exterior area type."""
        from open_notebook.extractors.acm_extractor import AREA_TYPE_PATTERN

        line = "## Exterior"
        match = AREA_TYPE_PATTERN.match(line)

        assert match is not None
        assert match.group(1).lower() == "exterior"


class TestPageNumberTracking:
    """Test suite for page number extraction."""

    def test_page_marker_detection(self):
        """Test detection of page markers."""
        from open_notebook.extractors.acm_extractor import PAGE_PATTERN

        line = "--- Page 5 ---"
        match = PAGE_PATTERN.search(line)

        assert match is not None
        assert match.group(1) == "5"

    def test_page_context_in_extraction(self):
        """Test that page numbers are associated with records."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

--- Page 3 ---

## Building: B1 - Block

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |

--- Page 4 ---

| Product | Material Description | Result |
|---------|---------------------|--------|
| Lagging | Pipe wrap | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 2
        assert result[0]["page_number"] == 3
        assert result[1]["page_number"] == 4

    def test_small_content_with_page_markers(self):
        """Test that small content (below chunking threshold) still extracts page numbers.

        Regression test for bug where _chunk_content would return page_number=1
        for small content even when page markers indicated a different page.
        """
        from open_notebook.graphs.acm_extraction import _chunk_content

        # Small content that won't trigger chunking, but starts at page 5
        content = "--- Page 5 ---\nSmall ACM content here"
        chunks = _chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0]["page_number"] == 5, (
            "Should extract page 5 from marker, not default to 1"
        )

    def test_small_content_without_page_markers(self):
        """Test that small content without page markers defaults to page 1."""
        from open_notebook.graphs.acm_extraction import _chunk_content

        content = "Small ACM content with no page markers"
        chunks = _chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0]["page_number"] == 1, "Should default to page 1 when no markers"

    def test_small_content_html_comment_page_marker(self):
        """Test HTML comment style page markers in small content."""
        from open_notebook.graphs.acm_extraction import _chunk_content

        content = "<!-- Page 12 -->\nContent from page 12"
        chunks = _chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0]["page_number"] == 12

    def test_multi_page_table_per_row_page_numbers(self):
        """Bug 2: Table spanning multiple pages - rows after page marker get correct page.

        When a table spans multiple pages, Docling inserts page markers between rows.
        _extract_table_lines must NOT break at page markers, and _parse_acm_table
        must update context.current_page for each page marker encountered.
        """
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block

--- Page 2 ---

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl floor tiles | Detected |
| Lagging | Pipe insulation | Detected |
--- Page 3 ---
| Sheeting | Wall board | Detected |
| Gaskets | Flange gaskets | Detected |
--- Page 4 ---
| Rope | Door seals | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 5, f"Expected 5 records, got {len(result)}"
        assert result[0]["page_number"] == 2  # Tiles - page 2
        assert result[1]["page_number"] == 2  # Lagging - page 2
        assert result[2]["page_number"] == 3  # Sheeting - page 3
        assert result[3]["page_number"] == 3  # Gaskets - page 3
        assert result[4]["page_number"] == 4  # Rope - page 4

    def test_multi_page_table_with_empty_lines_around_markers(self):
        """Bug 2 variant: Page markers with blank lines before/after within table."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block

--- Page 1 ---

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl floor tiles | Detected |

--- Page 2 ---

| Lagging | Pipe insulation | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 2, f"Expected 2 records, got {len(result)}"
        assert result[0]["page_number"] == 1
        assert result[1]["page_number"] == 2

    def test_page_marker_after_table_updates_context_for_next_table(self):
        """Bug 1: Page marker between two separate tables updates context correctly.

        Even when _extract_table_lines absorbs page markers (Bug 2 fix),
        context.current_page should be correct for the next table.
        """
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block A

--- Page 2 ---

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl floor tiles | Detected |

--- Page 5 ---

## Building: B2 - Block B

| Product | Material Description | Result |
|---------|---------------------|--------|
| Lagging | Pipe insulation | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 2
        assert result[0]["page_number"] == 2
        assert result[1]["page_number"] == 5

    def test_chunk_content_includes_page_markers_dict(self):
        """Bug 4: _chunk_content should track ALL page markers in chunk, not just first.

        When content fits in a single chunk, page_markers dict maps character offsets
        to page numbers so extract_records can assign per-record pages.
        """
        from open_notebook.graphs.acm_extraction import _chunk_content

        content = """--- Page 1 ---
Building A data and ACM records here
--- Page 2 ---
More building data on second page
--- Page 3 ---
Third page content with ACM items"""

        chunks = _chunk_content(content)
        assert len(chunks) == 1
        assert chunks[0]["page_number"] == 1
        assert "page_markers" in chunks[0]
        markers = chunks[0]["page_markers"]
        # Should have 3 page markers
        pages_found = sorted(markers.values())
        assert pages_found == [1, 2, 3]

    def test_assign_record_pages_from_markers(self):
        """Bug 4: Records should get page numbers based on their position in content.

        When LLM doesn't set page_number, the fallback should use page_markers
        to find the nearest preceding page marker based on the record's product
        text position in the chunk content.
        """
        from open_notebook.graphs.acm_extraction import _assign_record_page

        chunk_content = """--- Page 1 ---
| Floor Tiles | Vinyl asbestos tiles | Detected |
--- Page 3 ---
| Pipe Lagging | Insulation wrap | Detected |
--- Page 5 ---
| Rope Seals | Door gaskets | Detected |"""

        # Build page_markers from known marker positions (no regex duplication)
        page_markers = {}
        for marker, page in [
            ("--- Page 1 ---", 1),
            ("--- Page 3 ---", 3),
            ("--- Page 5 ---", 5),
        ]:
            page_markers[chunk_content.find(marker)] = page

        page, pos = _assign_record_page("Floor Tiles", chunk_content, page_markers, 1)
        assert page == 1 and pos >= 0
        page, pos = _assign_record_page("Pipe Lagging", chunk_content, page_markers, 1)
        assert page == 3 and pos >= 0
        page, pos = _assign_record_page("Rope Seals", chunk_content, page_markers, 1)
        assert page == 5 and pos >= 0

    def test_assign_record_page_duplicate_products(self):
        """Bug 4 edge case: duplicate product names get correct pages via search_after.

        When the same product appears multiple times in a chunk (e.g., same product
        in different rooms), search_after should advance past the first occurrence
        so the second record gets the correct page.
        """
        from open_notebook.graphs.acm_extraction import _assign_record_page

        chunk_content = """--- Page 1 ---
| Tiles | Room A vinyl floor | Detected |
--- Page 4 ---
| Tiles | Room B vinyl floor | Detected |"""

        page_markers = {}
        for marker, page in [("--- Page 1 ---", 1), ("--- Page 4 ---", 4)]:
            page_markers[chunk_content.find(marker)] = page

        # First "Tiles" is on page 1
        page1, pos1 = _assign_record_page("Tiles", chunk_content, page_markers, 1)
        assert page1 == 1
        assert pos1 >= 0

        # Second "Tiles" (searching after first) is on page 4
        page2, pos2 = _assign_record_page(
            "Tiles", chunk_content, page_markers, 1, search_after=pos1 + len("Tiles")
        )
        assert page2 == 4
        assert pos2 > pos1


class TestHasPipeContinuation:
    """Tests for the _has_pipe_continuation helper that distinguishes table
    continuation rows from new table headers after gaps."""

    def test_continuation_after_empty_line(self):
        """Data row after empty line is a continuation (no header+separator)."""
        from open_notebook.extractors.acm_extractor import _has_pipe_continuation

        lines = [
            "| Row1 | data |",
            "",  # gap
            "| Row2 | data |",  # continuation
        ]
        assert _has_pipe_continuation(lines, 2) is True

    def test_new_table_after_empty_line(self):
        """Header + separator after empty line is a new table, not continuation."""
        from open_notebook.extractors.acm_extractor import _has_pipe_continuation

        lines = [
            "| Row1 | data |",
            "",  # gap
            "| Product | Result |",  # header
            "|---------|--------|",  # separator → new table
        ]
        assert _has_pipe_continuation(lines, 2) is False

    def test_page_marker_before_continuation(self):
        """Page marker then data row is a continuation."""
        from open_notebook.extractors.acm_extractor import _has_pipe_continuation

        lines = [
            "| Row1 | data |",
            "",
            "--- Page 3 ---",
            "| Row2 | data |",
        ]
        assert _has_pipe_continuation(lines, 2) is True

    def test_non_pipe_line_after_gap(self):
        """Non-pipe text after gap ends the table."""
        from open_notebook.extractors.acm_extractor import _has_pipe_continuation

        lines = [
            "| Row1 | data |",
            "",
            "## Building: B2 - Block",
        ]
        assert _has_pipe_continuation(lines, 2) is False

    def test_end_of_file(self):
        """No more lines after gap returns False."""
        from open_notebook.extractors.acm_extractor import _has_pipe_continuation

        lines = ["| Row1 | data |", ""]
        assert _has_pipe_continuation(lines, 2) is False


class TestParseContext:
    """Test suite for ParseContext dataclass."""

    def test_parse_context_defaults(self):
        """Test ParseContext has correct defaults."""
        from open_notebook.extractors.acm_extractor import ParseContext

        ctx = ParseContext()

        assert ctx.school_name == ""
        assert ctx.building_id == ""
        assert ctx.room_id is None
        assert ctx.area_type == "Interior"
        assert ctx.current_page == 1


class TestExtractedACMRow:
    """Test suite for ExtractedACMRow conversion."""

    def test_to_acm_record_dict(self):
        """Test conversion to dict format."""
        from open_notebook.extractors.acm_extractor import ExtractedACMRow

        row = ExtractedACMRow(
            school_name="Test School",
            school_code="TS001",
            building_id="B1",
            building_name="Main",
            building_year=1990,
            building_construction="Brick",
            room_id="B1-R1",
            room_name="Office",
            room_area=50.0,
            area_type="Interior",
            page_number=5,
            product="Tiles",
            material_description="Floor tiles",
            result="Detected",
        )

        result = row.to_acm_record_dict("source:123")

        assert result["source_id"] == "source:123"
        assert result["school_name"] == "Test School"
        assert result["building_id"] == "B1"
        assert result["page_number"] == 5


class TestTableDetection:
    """Test suite for ACM table detection logic."""

    def test_looks_like_table_header_positive(self):
        """Test positive detection of ACM table headers."""
        from open_notebook.extractors.acm_extractor import _looks_like_table_header

        # Should detect ACM tables
        assert _looks_like_table_header("| Product | Material Description | Result |")
        assert _looks_like_table_header("| product | material description | result |")

    def test_looks_like_table_header_negative(self):
        """Test rejection of non-ACM table headers."""
        from open_notebook.extractors.acm_extractor import _looks_like_table_header

        # Should not detect non-ACM tables
        assert not _looks_like_table_header("| Name | Date | Status |")
        assert not _looks_like_table_header("| Column1 | Column2 |")


class TestHeaderMapping:
    """Test suite for header to field mapping."""

    def test_create_header_map(self):
        """Test header mapping creation."""
        from open_notebook.extractors.acm_extractor import _create_header_map

        headers = [
            "product",
            "material description",
            "extent",
            "location",
            "friable",
            "condition",
            "risk",
            "result",
        ]
        mapping = _create_header_map(headers)

        assert mapping["product"] == 0
        assert mapping["material_description"] == 1
        assert mapping["extent"] == 2
        assert mapping["location"] == 3
        assert mapping["friable"] == 4
        assert mapping["material_condition"] == 5
        assert mapping["risk_status"] == 6
        assert mapping["result"] == 7


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_handles_missing_cells(self):
        """Test handling of missing/empty cells - should skip rows with missing required fields."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        # Should be skipped because material_description is empty (required field)
        assert len(result) == 0

    def test_handles_no_building_context(self):
        """Test handling when no building header is found."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 1
        assert result[0]["building_id"] == "Unknown"

    def test_multiple_buildings(self):
        """Test extraction across multiple buildings."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block A

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |

## Building: B2 - Block B

| Product | Material Description | Result |
|---------|---------------------|--------|
| Lagging | Pipe | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 2
        assert result[0]["building_id"] == "B1"
        assert result[1]["building_id"] == "B2"


class TestMineruFallback:
    """Test suite for MinerU extraction with fallback to markdown parsing."""

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content for testing fallback."""
        return """# Test School - Asbestos Register

## Building: B00A - Admin Block - 1924

#### Room: B00A-R0001 - Main Office - 45.5m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Tiles | Vinyl asbestos tiles | 50m² | Floor | Non Friable | Good | Low | Detected |
"""

    def test_backward_compatibility_markdown_only(self, sample_markdown):
        """Test that existing code calling with just markdown still works."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        # Call without pdf_path or use_mineru - should use markdown parsing
        result = extract_acm_records(sample_markdown, "source:123")

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"
        assert result[0]["building_id"] == "B00A"

    def test_use_mineru_disabled(self, sample_markdown):
        """Test that use_mineru=False forces markdown parsing."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        # Even with pdf_path provided, should skip MinerU if disabled
        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path="/fake/path.pdf", use_mineru=False
        )

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"

    def test_no_pdf_path_uses_markdown(self, sample_markdown):
        """Test that missing pdf_path falls back to markdown parsing."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        # use_mineru=True but no pdf_path - should use markdown
        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path=None, use_mineru=True
        )

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"

    @patch("open_notebook.extractors.acm_extractor.MINERU_AVAILABLE", False)
    def test_mineru_not_available_fallback(self, sample_markdown):
        """Test fallback when MinerU is not installed."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"

    @patch("open_notebook.extractors.acm_extractor.MINERU_AVAILABLE", True)
    @patch("open_notebook.extractors.acm_extractor._extract_with_mineru")
    def test_mineru_returns_empty_fallback(self, mock_mineru, sample_markdown):
        """Test fallback when MinerU returns no records."""
        # Mock MinerU to return empty list
        mock_mineru.return_value = []

        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        # Should fall back to markdown parsing
        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"
        mock_mineru.assert_called_once_with("/fake/path.pdf", "source:123")

    @patch("open_notebook.extractors.acm_extractor.MINERU_AVAILABLE", True)
    @patch("open_notebook.extractors.acm_extractor._extract_with_mineru")
    def test_mineru_exception_fallback(self, mock_mineru, sample_markdown):
        """Test fallback when MinerU raises an exception."""
        # Mock MinerU to raise an exception
        mock_mineru.side_effect = Exception("MinerU extraction failed")

        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        # Should fall back to markdown parsing
        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"
        mock_mineru.assert_called_once()

    @patch("open_notebook.extractors.acm_extractor.MINERU_AVAILABLE", True)
    @patch("open_notebook.extractors.acm_extractor._extract_with_mineru")
    def test_mineru_success_no_fallback(self, mock_mineru, sample_markdown):
        """Test that successful MinerU extraction skips fallback."""
        # Mock MinerU to return records
        mineru_records = [
            {
                "source_id": "source:123",
                "school_name": "MinerU School",
                "building_id": "B99",
                "product": "MinerU Extracted Tiles",
                "material_description": "From MinerU",
                "result": "Detected",
            }
        ]
        mock_mineru.return_value = mineru_records

        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown, "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        # Should use MinerU results, not markdown
        assert len(result) == 1
        assert result[0]["product"] == "MinerU Extracted Tiles"
        assert result[0]["building_id"] == "B99"
        mock_mineru.assert_called_once()

    def test_empty_markdown_with_pdf_path(self):
        """Test that empty markdown with pdf_path still returns empty (MinerU returns empty too)."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            "", "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        assert result == []

    def test_none_markdown_with_pdf_path(self):
        """Test that None markdown with pdf_path still returns empty (MinerU returns empty too)."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            None, "source:123", pdf_path="/fake/path.pdf", use_mineru=True
        )

        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
