"""
MinerU Table Extraction from PDF Documents

Uses MinerU (magic-pdf) to extract tables with HTML structure, bounding boxes,
and page numbers from PDF documents. Handles merged cells and multi-page tables.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

try:
    # Try importing from magic_pdf (version-agnostic approach)
    import magic_pdf
    # Try different possible import paths (API changed between versions)
    try:
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
    except (ImportError, AttributeError):
        # Fallback for older versions or different API structure
        try:
            from magic_pdf.operators.pipes import PipeResult
            UNIPipe = None  # Will be handled in the extractor
        except ImportError:
            UNIPipe = None
    MINERU_AVAILABLE = magic_pdf is not None
except ImportError:
    MINERU_AVAILABLE = False
    UNIPipe = None
    logger.warning("MinerU (magic-pdf) not available. Table extraction will fail.")


@dataclass
class TableBoundingBox:
    """Bounding box coordinates for a table."""
    x: float
    y: float
    width: float
    height: float
    page: int

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "page": self.page,
        }


@dataclass
class ExtractedTable:
    """Represents an extracted table with metadata."""
    html: str
    bbox: TableBoundingBox
    page_number: int
    row_count: int
    col_count: int
    has_merged_cells: bool = False
    table_index: int = 0  # Index of table on the page

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "html": self.html,
            "bbox": self.bbox.to_dict(),
            "page_number": self.page_number,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "has_merged_cells": self.has_merged_cells,
            "table_index": self.table_index,
        }


class MineruTableExtractor:
    """
    Extracts tables from PDFs using MinerU with bounding box tracking.

    Features:
    - HTML table structure extraction
    - Bounding box coordinates for provenance
    - Merged cell detection and handling
    - Multi-page table stitching
    """

    def __init__(self, parse_method: str = "auto"):
        """
        Initialize the MinerU table extractor.

        Args:
            parse_method: Parsing method ('auto', 'ocr', 'txt'). Default: 'auto'

        Raises:
            ImportError: If MinerU is not installed
        """
        if not MINERU_AVAILABLE:
            raise ImportError(
                "MinerU (magic-pdf) is not installed. "
                "Install with: pip install magic-pdf[full]"
            )
        self.parse_method = parse_method
        logger.info(f"MineruTableExtractor initialized with parse_method={parse_method}")

    def extract_tables_from_pdf(
        self,
        pdf_path: str,
        stitch_multipage: bool = True
    ) -> List[ExtractedTable]:
        """
        Extract all tables from a PDF document.

        Args:
            pdf_path: Path to the PDF file
            stitch_multipage: Whether to stitch multi-page tables (default: True)

        Returns:
            List of ExtractedTable objects with HTML, bounding boxes, and metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If extraction fails
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Starting table extraction from: {pdf_path}")

        try:
            # Create temporary directory for MinerU output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "output"
                output_dir.mkdir(parents=True, exist_ok=True)

                # Extract tables using MinerU
                tables = self._run_mineru_extraction(
                    str(pdf_path),
                    str(output_dir)
                )

                logger.info(f"Extracted {len(tables)} tables from {pdf_path}")

                # Optionally stitch multi-page tables
                if stitch_multipage and len(tables) > 1:
                    tables = self._stitch_multipage_tables(tables)
                    logger.info(f"After stitching: {len(tables)} tables")

                return tables

        except Exception as e:
            logger.error(f"Failed to extract tables from {pdf_path}: {e}")
            raise

    def _run_mineru_extraction(
        self,
        pdf_path: str,
        output_dir: str
    ) -> List[ExtractedTable]:
        """
        Run MinerU extraction pipeline and parse results.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for MinerU output

        Returns:
            List of ExtractedTable objects
        """
        try:
            # Initialize MinerU reader/writer
            pdf_bytes = open(pdf_path, "rb").read()

            # Create output writer
            image_dir = os.path.join(output_dir, "images")
            os.makedirs(image_dir, exist_ok=True)
            image_writer = DiskReaderWriter(image_dir)

            # Run MinerU pipeline
            pipe = UNIPipe(pdf_bytes, {"_pdf_type": ""}, image_writer)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()

            # Get content data with tables
            content_list = pipe.pipe_mk_uni_format(image_dir, drop_mode="none")
            md_content = pipe.pipe_mk_markdown(image_dir, drop_mode="none")

            # Parse tables from content
            tables = self._parse_tables_from_content(
                content_list,
                md_content,
                pdf_path
            )

            return tables

        except Exception as e:
            logger.error(f"MinerU extraction failed: {e}")
            raise

    def _parse_tables_from_content(
        self,
        content_list: List[dict],
        md_content: str,
        pdf_path: str
    ) -> List[ExtractedTable]:
        """
        Parse tables from MinerU content output.

        Args:
            content_list: List of content blocks from MinerU
            md_content: Markdown content with table structures
            pdf_path: Path to source PDF (for logging)

        Returns:
            List of ExtractedTable objects
        """
        tables: List[ExtractedTable] = []
        table_index = 0

        for block in content_list:
            if not isinstance(block, dict):
                continue

            # Check if this block contains a table
            if block.get("type") == "table" or "table" in block.get("type", "").lower():
                try:
                    table = self._extract_table_from_block(block, table_index)
                    if table:
                        tables.append(table)
                        table_index += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to parse table {table_index} from {pdf_path}: {e}"
                    )
                    continue

        logger.debug(f"Parsed {len(tables)} tables from content")
        return tables

    def _extract_table_from_block(
        self,
        block: dict,
        table_index: int
    ) -> Optional[ExtractedTable]:
        """
        Extract a single table from a MinerU content block.

        Args:
            block: MinerU content block dictionary
            table_index: Index of this table in the document

        Returns:
            ExtractedTable object or None if extraction fails
        """
        try:
            # Extract HTML content
            html = block.get("html", "")
            if not html:
                # Try to get from 'text' or 'content' fields
                html = block.get("text", block.get("content", ""))

            if not html or not html.strip():
                logger.warning(f"Empty HTML for table {table_index}")
                return None

            # Extract bounding box
            bbox_data = block.get("bbox", block.get("box", {}))
            if isinstance(bbox_data, (list, tuple)) and len(bbox_data) >= 4:
                # Format: [x, y, width, height] or [x1, y1, x2, y2]
                x, y, w_or_x2, h_or_y2 = bbox_data[:4]
                # Assume x,y,width,height format
                width = w_or_x2 if w_or_x2 > x else w_or_x2 - x
                height = h_or_y2 if h_or_y2 > y else h_or_y2 - y
            elif isinstance(bbox_data, dict):
                x = bbox_data.get("x", bbox_data.get("x0", 0))
                y = bbox_data.get("y", bbox_data.get("y0", 0))
                width = bbox_data.get("width", bbox_data.get("w", 0))
                height = bbox_data.get("height", bbox_data.get("h", 0))
            else:
                # Default bbox if none provided
                x, y, width, height = 0, 0, 0, 0

            # Extract page number
            page_number = block.get("page", block.get("page_number", block.get("page_idx", 0)))
            if isinstance(page_number, int):
                page_number = page_number + 1  # Convert 0-indexed to 1-indexed

            bbox = TableBoundingBox(
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                page=page_number
            )

            # Detect merged cells and count rows/cols
            has_merged_cells = "colspan" in html.lower() or "rowspan" in html.lower()
            row_count = html.lower().count("<tr")
            col_count = self._estimate_col_count(html)

            return ExtractedTable(
                html=html,
                bbox=bbox,
                page_number=page_number,
                row_count=row_count,
                col_count=col_count,
                has_merged_cells=has_merged_cells,
                table_index=table_index
            )

        except Exception as e:
            logger.warning(f"Failed to extract table {table_index}: {e}")
            return None

    def _estimate_col_count(self, html: str) -> int:
        """
        Estimate column count from HTML table.

        Args:
            html: HTML table string

        Returns:
            Estimated number of columns
        """
        # Count <th> or <td> tags in first row
        html_lower = html.lower()
        first_row_start = html_lower.find("<tr")
        if first_row_start == -1:
            return 0

        first_row_end = html_lower.find("</tr>", first_row_start)
        if first_row_end == -1:
            return 0

        first_row = html_lower[first_row_start:first_row_end]
        col_count = first_row.count("<th") + first_row.count("<td")
        return col_count

    def _stitch_multipage_tables(
        self,
        tables: List[ExtractedTable]
    ) -> List[ExtractedTable]:
        """
        Stitch tables that span multiple pages.

        Heuristic: If consecutive tables on adjacent pages have similar column counts
        and the first has no closing structure, they're likely the same table.

        Args:
            tables: List of ExtractedTable objects

        Returns:
            List of ExtractedTable objects with stitched multi-page tables
        """
        if len(tables) <= 1:
            return tables

        stitched: List[ExtractedTable] = []
        i = 0

        while i < len(tables):
            current = tables[i]

            # Check if next table is on adjacent page with similar structure
            if i + 1 < len(tables):
                next_table = tables[i + 1]

                # Check stitching conditions
                is_adjacent_page = next_table.page_number == current.page_number + 1
                similar_cols = abs(current.col_count - next_table.col_count) <= 1

                if is_adjacent_page and similar_cols:
                    # Stitch tables
                    stitched_html = self._merge_table_html(
                        current.html,
                        next_table.html
                    )

                    # Create stitched table with updated metadata
                    stitched_table = ExtractedTable(
                        html=stitched_html,
                        bbox=current.bbox,  # Use first table's bbox
                        page_number=current.page_number,
                        row_count=current.row_count + next_table.row_count,
                        col_count=current.col_count,
                        has_merged_cells=current.has_merged_cells or next_table.has_merged_cells,
                        table_index=current.table_index
                    )

                    stitched.append(stitched_table)
                    logger.debug(
                        f"Stitched tables from pages {current.page_number} and {next_table.page_number}"
                    )
                    i += 2  # Skip both tables
                    continue

            # No stitching, add current table as-is
            stitched.append(current)
            i += 1

        return stitched

    def _merge_table_html(self, html1: str, html2: str) -> str:
        """
        Merge two HTML table strings by combining their rows.

        Args:
            html1: First table HTML
            html2: Second table HTML

        Returns:
            Merged HTML table string
        """
        # Simple approach: remove closing </table> from first and opening <table> from second
        html1_stripped = html1.strip()
        html2_stripped = html2.strip()

        # Remove closing tag from first table
        if html1_stripped.endswith("</table>"):
            html1_stripped = html1_stripped[:-8]

        # Remove opening tag from second table
        table_start = html2_stripped.lower().find("<table")
        if table_start != -1:
            # Find end of opening tag
            tag_end = html2_stripped.find(">", table_start)
            if tag_end != -1:
                html2_stripped = html2_stripped[tag_end + 1:]

        # Combine
        merged = html1_stripped + "\n" + html2_stripped

        # Ensure closing tag
        if not merged.strip().endswith("</table>"):
            merged += "\n</table>"

        return merged


def extract_tables_from_pdf(
    pdf_path: str,
    parse_method: str = "auto",
    stitch_multipage: bool = True
) -> List[ExtractedTable]:
    """
    Convenience function to extract tables from a PDF.

    Args:
        pdf_path: Path to the PDF file
        parse_method: Parsing method ('auto', 'ocr', 'txt'). Default: 'auto'
        stitch_multipage: Whether to stitch multi-page tables (default: True)

    Returns:
        List of ExtractedTable objects

    Raises:
        ImportError: If MinerU is not installed
        FileNotFoundError: If PDF file doesn't exist
        Exception: If extraction fails
    """
    extractor = MineruTableExtractor(parse_method=parse_method)
    return extractor.extract_tables_from_pdf(
        pdf_path=pdf_path,
        stitch_multipage=stitch_multipage
    )
