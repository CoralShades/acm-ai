"""
Unit tests for the MinerU Table Extraction module.

Tests the extraction of tables from PDFs using MinerU (magic-pdf),
including HTML parsing, bounding box tracking, merged cell detection,
and multi-page table stitching.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestMineruTableExtractorInit:
    """Test suite for MineruTableExtractor initialization."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', False)
    def test_init_raises_import_error_when_mineru_unavailable(self):
        """Test that ImportError is raised when MinerU is not installed."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        with pytest.raises(ImportError, match="MinerU.*not installed"):
            MineruTableExtractor()

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_init_with_default_parse_method(self):
        """Test initialization with default parse method."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        assert extractor.parse_method == "auto"

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_init_with_custom_parse_method(self):
        """Test initialization with custom parse method."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor(parse_method="ocr")
        assert extractor.parse_method == "ocr"


class TestTableBoundingBox:
    """Test suite for TableBoundingBox dataclass."""

    def test_bounding_box_creation(self):
        """Test creating a TableBoundingBox."""
        from open_notebook.extractors.mineru_table_extractor import TableBoundingBox

        bbox = TableBoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0
        assert bbox.page == 1

    def test_bounding_box_to_dict(self):
        """Test serialization of TableBoundingBox to dict."""
        from open_notebook.extractors.mineru_table_extractor import TableBoundingBox

        bbox = TableBoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        bbox_dict = bbox.to_dict()

        assert bbox_dict == {
            "x": 10.0,
            "y": 20.0,
            "width": 100.0,
            "height": 50.0,
            "page": 1
        }


class TestExtractedTable:
    """Test suite for ExtractedTable dataclass."""

    def test_extracted_table_creation(self):
        """Test creating an ExtractedTable."""
        from open_notebook.extractors.mineru_table_extractor import (
            ExtractedTable,
            TableBoundingBox
        )

        bbox = TableBoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        table = ExtractedTable(
            html="<table><tr><td>Test</td></tr></table>",
            bbox=bbox,
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        assert table.html == "<table><tr><td>Test</td></tr></table>"
        assert table.bbox == bbox
        assert table.page_number == 1
        assert table.row_count == 1
        assert table.col_count == 1
        assert table.has_merged_cells is False
        assert table.table_index == 0

    def test_extracted_table_to_dict(self):
        """Test serialization of ExtractedTable to dict."""
        from open_notebook.extractors.mineru_table_extractor import (
            ExtractedTable,
            TableBoundingBox
        )

        bbox = TableBoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        table = ExtractedTable(
            html="<table><tr><td>Test</td></tr></table>",
            bbox=bbox,
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        table_dict = table.to_dict()

        assert table_dict["html"] == "<table><tr><td>Test</td></tr></table>"
        assert table_dict["bbox"] == bbox.to_dict()
        assert table_dict["page_number"] == 1
        assert table_dict["row_count"] == 1
        assert table_dict["col_count"] == 1
        assert table_dict["has_merged_cells"] is False
        assert table_dict["table_index"] == 0


class TestEstimateColCount:
    """Test suite for column count estimation."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_estimate_col_count_simple_table(self):
        """Test column count estimation for simple table."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html = "<table><tr><th>Col1</th><th>Col2</th><th>Col3</th></tr></table>"

        col_count = extractor._estimate_col_count(html)
        assert col_count == 3

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_estimate_col_count_with_td(self):
        """Test column count estimation with td elements."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html = "<table><tr><td>A</td><td>B</td></tr></table>"

        col_count = extractor._estimate_col_count(html)
        assert col_count == 2

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_estimate_col_count_mixed_th_td(self):
        """Test column count with mixed th and td in first row."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html = "<table><tr><th>Header</th><td>Data1</td><td>Data2</td></tr></table>"

        col_count = extractor._estimate_col_count(html)
        assert col_count == 3

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_estimate_col_count_no_tr(self):
        """Test column count estimation with no tr tags."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html = "<table></table>"

        col_count = extractor._estimate_col_count(html)
        assert col_count == 0

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_estimate_col_count_empty_string(self):
        """Test column count estimation with empty string."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        col_count = extractor._estimate_col_count("")
        assert col_count == 0


class TestExtractTableFromBlock:
    """Test suite for extracting tables from MinerU content blocks."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_with_html_field(self):
        """Test extracting table when HTML is in 'html' field."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": "<table><tr><td>Test</td></tr></table>",
            "bbox": [10, 20, 100, 50],
            "page": 0
        }

        table = extractor._extract_table_from_block(block, 0)

        assert table is not None
        assert table.html == "<table><tr><td>Test</td></tr></table>"
        assert table.bbox.x == 10.0
        assert table.bbox.y == 20.0
        assert table.page_number == 1  # Converted from 0-indexed

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_with_text_field(self):
        """Test extracting table when HTML is in 'text' field."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "text": "<table><tr><td>Data</td></tr></table>",
            "bbox": {"x": 5, "y": 10, "width": 200, "height": 100},
            "page_number": 2
        }

        table = extractor._extract_table_from_block(block, 1)

        assert table is not None
        assert table.html == "<table><tr><td>Data</td></tr></table>"
        assert table.bbox.x == 5.0
        assert table.page_number == 3  # Converted from 0-indexed (2 + 1)

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_detects_merged_cells(self):
        """Test that merged cells are detected via colspan/rowspan."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": '<table><tr><td colspan="2">Merged</td></tr></table>',
            "bbox": [0, 0, 100, 50],
            "page": 0
        }

        table = extractor._extract_table_from_block(block, 0)

        assert table is not None
        assert table.has_merged_cells is True

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_counts_rows(self):
        """Test that row count is correctly calculated."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": "<table><tr><td>R1</td></tr><tr><td>R2</td></tr><tr><td>R3</td></tr></table>",
            "bbox": [0, 0, 100, 50],
            "page": 0
        }

        table = extractor._extract_table_from_block(block, 0)

        assert table is not None
        assert table.row_count == 3

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_with_empty_html_returns_none(self):
        """Test that empty HTML returns None."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": "",
            "bbox": [0, 0, 100, 50],
            "page": 0
        }

        table = extractor._extract_table_from_block(block, 0)
        assert table is None

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_with_dict_bbox(self):
        """Test bounding box extraction from dict format."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": "<table><tr><td>Test</td></tr></table>",
            "bbox": {"x": 15, "y": 25, "width": 150, "height": 75},
            "page": 1
        }

        table = extractor._extract_table_from_block(block, 0)

        assert table is not None
        assert table.bbox.x == 15.0
        assert table.bbox.y == 25.0
        assert table.bbox.width == 150.0
        assert table.bbox.height == 75.0

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_table_with_default_bbox(self):
        """Test that default bbox is used when none provided."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        block = {
            "type": "table",
            "html": "<table><tr><td>Test</td></tr></table>",
            "page": 0
        }

        table = extractor._extract_table_from_block(block, 0)

        assert table is not None
        assert table.bbox.x == 0.0
        assert table.bbox.y == 0.0
        assert table.bbox.width == 0.0
        assert table.bbox.height == 0.0


class TestMergeTableHtml:
    """Test suite for merging HTML tables."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_merge_simple_tables(self):
        """Test merging two simple HTML tables."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html1 = "<table><tr><td>Row1</td></tr></table>"
        html2 = "<table><tr><td>Row2</td></tr></table>"

        merged = extractor._merge_table_html(html1, html2)

        assert "<tr><td>Row1</td></tr>" in merged
        assert "<tr><td>Row2</td></tr>" in merged
        assert merged.endswith("</table>")
        # Should only have one opening table tag (from first table)
        assert merged.count("<table") == 1

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_merge_removes_closing_tag_from_first(self):
        """Test that closing </table> is removed from first table."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html1 = "<table><tr><td>A</td></tr></table>"
        html2 = "<table><tr><td>B</td></tr></table>"

        merged = extractor._merge_table_html(html1, html2)

        # Count </table> tags - should only be one at the end
        assert merged.count("</table>") == 1
        assert merged.strip().endswith("</table>")

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_merge_removes_opening_tag_from_second(self):
        """Test that opening <table> is removed from second table."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        html1 = "<table><tr><td>A</td></tr></table>"
        html2 = "<table class='test'><tr><td>B</td></tr></table>"

        merged = extractor._merge_table_html(html1, html2)

        # Should only have one <table tag (from first table)
        assert merged.count("<table") == 1


class TestStitchMultipageTables:
    """Test suite for multi-page table stitching."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_stitch_adjacent_pages_similar_columns(self):
        """Test stitching tables on adjacent pages with similar columns."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        extractor = MineruTableExtractor()

        table1 = ExtractedTable(
            html="<table><tr><td>A</td><td>B</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 1),
            page_number=1,
            row_count=1,
            col_count=2,
            has_merged_cells=False,
            table_index=0
        )

        table2 = ExtractedTable(
            html="<table><tr><td>C</td><td>D</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 2),
            page_number=2,
            row_count=1,
            col_count=2,
            has_merged_cells=False,
            table_index=1
        )

        stitched = extractor._stitch_multipage_tables([table1, table2])

        assert len(stitched) == 1
        assert stitched[0].page_number == 1
        assert stitched[0].row_count == 2
        assert "<td>A</td>" in stitched[0].html
        assert "<td>C</td>" in stitched[0].html

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_no_stitch_non_adjacent_pages(self):
        """Test that tables on non-adjacent pages are not stitched."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        extractor = MineruTableExtractor()

        table1 = ExtractedTable(
            html="<table><tr><td>A</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 1),
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        table2 = ExtractedTable(
            html="<table><tr><td>B</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 3),
            page_number=3,  # Not adjacent
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=1
        )

        stitched = extractor._stitch_multipage_tables([table1, table2])

        assert len(stitched) == 2  # Not stitched

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_no_stitch_different_column_counts(self):
        """Test that tables with different column counts are not stitched."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        extractor = MineruTableExtractor()

        table1 = ExtractedTable(
            html="<table><tr><td>A</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 1),
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        table2 = ExtractedTable(
            html="<table><tr><td>B</td><td>C</td><td>D</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 2),
            page_number=2,
            row_count=1,
            col_count=3,  # Different column count
            has_merged_cells=False,
            table_index=1
        )

        stitched = extractor._stitch_multipage_tables([table1, table2])

        assert len(stitched) == 2  # Not stitched

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_stitch_empty_list_returns_empty(self):
        """Test that empty list returns empty list."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        stitched = extractor._stitch_multipage_tables([])
        assert stitched == []

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_stitch_single_table_returns_unchanged(self):
        """Test that single table returns unchanged."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        extractor = MineruTableExtractor()

        table = ExtractedTable(
            html="<table><tr><td>A</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 1),
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        stitched = extractor._stitch_multipage_tables([table])
        assert len(stitched) == 1
        assert stitched[0] == table

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_stitch_preserves_merged_cells_flag(self):
        """Test that stitching preserves merged cells flag from either table."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        extractor = MineruTableExtractor()

        table1 = ExtractedTable(
            html="<table><tr><td>A</td></tr></table>",
            bbox=TableBoundingBox(0, 0, 100, 50, 1),
            page_number=1,
            row_count=1,
            col_count=1,
            has_merged_cells=False,
            table_index=0
        )

        table2 = ExtractedTable(
            html='<table><tr><td colspan="2">B</td></tr></table>',
            bbox=TableBoundingBox(0, 0, 100, 50, 2),
            page_number=2,
            row_count=1,
            col_count=1,
            has_merged_cells=True,
            table_index=1
        )

        stitched = extractor._stitch_multipage_tables([table1, table2])

        assert len(stitched) == 1
        assert stitched[0].has_merged_cells is True


class TestParseTablesFromContent:
    """Test suite for parsing tables from MinerU content output."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_parse_table_blocks(self):
        """Test parsing table blocks from content list."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        content_list = [
            {
                "type": "text",
                "text": "Some text"
            },
            {
                "type": "table",
                "html": "<table><tr><td>Data</td></tr></table>",
                "bbox": [0, 0, 100, 50],
                "page": 0
            }
        ]

        tables = extractor._parse_tables_from_content(content_list, "", "test.pdf")

        assert len(tables) == 1
        assert tables[0].html == "<table><tr><td>Data</td></tr></table>"

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_parse_skips_non_table_blocks(self):
        """Test that non-table blocks are skipped."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        content_list = [
            {
                "type": "text",
                "text": "Not a table"
            },
            {
                "type": "image",
                "path": "image.png"
            }
        ]

        tables = extractor._parse_tables_from_content(content_list, "", "test.pdf")
        assert len(tables) == 0

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_parse_handles_malformed_blocks(self):
        """Test that malformed table blocks are logged and skipped."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        content_list = [
            {
                "type": "table",
                # Missing html field - should be skipped
                "bbox": [0, 0, 100, 50],
                "page": 0
            }
        ]

        tables = extractor._parse_tables_from_content(content_list, "", "test.pdf")
        assert len(tables) == 0  # Malformed block skipped

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_parse_assigns_table_indices(self):
        """Test that table indices are correctly assigned."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()
        content_list = [
            {
                "type": "table",
                "html": "<table><tr><td>Table1</td></tr></table>",
                "bbox": [0, 0, 100, 50],
                "page": 0
            },
            {
                "type": "table",
                "html": "<table><tr><td>Table2</td></tr></table>",
                "bbox": [0, 0, 100, 50],
                "page": 0
            }
        ]

        tables = extractor._parse_tables_from_content(content_list, "", "test.pdf")

        assert len(tables) == 2
        assert tables[0].table_index == 0
        assert tables[1].table_index == 1


class TestExtractTablesFromPdf:
    """Test suite for main PDF extraction method."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    def test_extract_raises_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent PDF."""
        from open_notebook.extractors.mineru_table_extractor import MineruTableExtractor

        extractor = MineruTableExtractor()

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            extractor.extract_tables_from_pdf("non_existent.pdf")

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    @patch('open_notebook.extractors.mineru_table_extractor.Path.exists')
    @patch('open_notebook.extractors.mineru_table_extractor.MineruTableExtractor._run_mineru_extraction')
    def test_extract_with_stitching_enabled(self, mock_extract, mock_exists):
        """Test extraction with multi-page stitching enabled."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        mock_exists.return_value = True

        # Mock returning two tables on adjacent pages
        mock_tables = [
            ExtractedTable(
                html="<table><tr><td>A</td></tr></table>",
                bbox=TableBoundingBox(0, 0, 100, 50, 1),
                page_number=1,
                row_count=1,
                col_count=1,
                has_merged_cells=False,
                table_index=0
            ),
            ExtractedTable(
                html="<table><tr><td>B</td></tr></table>",
                bbox=TableBoundingBox(0, 0, 100, 50, 2),
                page_number=2,
                row_count=1,
                col_count=1,
                has_merged_cells=False,
                table_index=1
            )
        ]
        mock_extract.return_value = mock_tables

        extractor = MineruTableExtractor()
        tables = extractor.extract_tables_from_pdf("test.pdf", stitch_multipage=True)

        # Tables should be stitched
        assert len(tables) == 1

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    @patch('open_notebook.extractors.mineru_table_extractor.Path.exists')
    @patch('open_notebook.extractors.mineru_table_extractor.MineruTableExtractor._run_mineru_extraction')
    def test_extract_with_stitching_disabled(self, mock_extract, mock_exists):
        """Test extraction with multi-page stitching disabled."""
        from open_notebook.extractors.mineru_table_extractor import (
            MineruTableExtractor,
            ExtractedTable,
            TableBoundingBox
        )

        mock_exists.return_value = True

        mock_tables = [
            ExtractedTable(
                html="<table><tr><td>A</td></tr></table>",
                bbox=TableBoundingBox(0, 0, 100, 50, 1),
                page_number=1,
                row_count=1,
                col_count=1,
                has_merged_cells=False,
                table_index=0
            ),
            ExtractedTable(
                html="<table><tr><td>B</td></tr></table>",
                bbox=TableBoundingBox(0, 0, 100, 50, 2),
                page_number=2,
                row_count=1,
                col_count=1,
                has_merged_cells=False,
                table_index=1
            )
        ]
        mock_extract.return_value = mock_tables

        extractor = MineruTableExtractor()
        tables = extractor.extract_tables_from_pdf("test.pdf", stitch_multipage=False)

        # Tables should NOT be stitched
        assert len(tables) == 2


class TestConvenienceFunction:
    """Test suite for the convenience function."""

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', True)
    @patch('open_notebook.extractors.mineru_table_extractor.Path.exists')
    @patch('open_notebook.extractors.mineru_table_extractor.MineruTableExtractor._run_mineru_extraction')
    def test_convenience_function(self, mock_extract, mock_exists):
        """Test the extract_tables_from_pdf convenience function."""
        from open_notebook.extractors.mineru_table_extractor import (
            extract_tables_from_pdf,
            ExtractedTable,
            TableBoundingBox
        )

        mock_exists.return_value = True
        mock_extract.return_value = [
            ExtractedTable(
                html="<table><tr><td>Test</td></tr></table>",
                bbox=TableBoundingBox(0, 0, 100, 50, 1),
                page_number=1,
                row_count=1,
                col_count=1,
                has_merged_cells=False,
                table_index=0
            )
        ]

        tables = extract_tables_from_pdf("test.pdf", parse_method="ocr")

        assert len(tables) == 1
        assert tables[0].html == "<table><tr><td>Test</td></tr></table>"

    @patch('open_notebook.extractors.mineru_table_extractor.MINERU_AVAILABLE', False)
    def test_convenience_function_raises_import_error(self):
        """Test convenience function raises ImportError when MinerU unavailable."""
        from open_notebook.extractors.mineru_table_extractor import extract_tables_from_pdf

        with pytest.raises(ImportError, match="MinerU.*not installed"):
            extract_tables_from_pdf("test.pdf")
