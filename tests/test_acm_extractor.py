"""
Unit tests for the ACM Register extraction module.

Tests the extraction of ACM records from Docling markdown output,
including table detection, header parsing, and row extraction.
Also tests the fallback mechanism from MinerU to markdown parsing.
"""

import pytest
from unittest.mock import patch, MagicMock


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
        assert record["result"] == "Detected"

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
        assert result[0]["result"] == "Not Detected"

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
        assert chunks[0]["page_number"] == 5, "Should extract page 5 from marker, not default to 1"

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

        headers = ["product", "material description", "extent", "location", "friable", "condition", "risk", "result"]
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
            sample_markdown,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=False
        )

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"

    def test_no_pdf_path_uses_markdown(self, sample_markdown):
        """Test that missing pdf_path falls back to markdown parsing."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        # use_mineru=True but no pdf_path - should use markdown
        result = extract_acm_records(
            sample_markdown,
            "source:123",
            pdf_path=None,
            use_mineru=True
        )

        assert len(result) == 1
        assert result[0]["product"] == "Floor Tiles"

    @patch("open_notebook.extractors.acm_extractor.MINERU_AVAILABLE", False)
    def test_mineru_not_available_fallback(self, sample_markdown):
        """Test fallback when MinerU is not installed."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
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
            sample_markdown,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
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
            sample_markdown,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
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
                "result": "Detected"
            }
        ]
        mock_mineru.return_value = mineru_records

        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            sample_markdown,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
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
            "",
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
        )

        assert result == []

    def test_none_markdown_with_pdf_path(self):
        """Test that None markdown with pdf_path still returns empty (MinerU returns empty too)."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(
            None,
            "source:123",
            pdf_path="/fake/path.pdf",
            use_mineru=True
        )

        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
