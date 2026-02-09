"""
ACM Register Extraction from Docling Markdown Output

Parses markdown content produced by Docling to extract structured
ACM (Asbestos Containing Material) records with hierarchical
Building > Room > Item relationships.

Supports fallback from MinerU table extraction to regex-based markdown parsing.
Uses the config-driven GenericParser (E1-S11) for all formats.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.extractors.parsers import get_parser

# Optional MinerU support - graceful degradation if not available
try:
    from open_notebook.extractors.mineru_table_extractor import (
        ExtractedTable,
        MineruTableExtractor,
    )

    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False
    logger.debug("MinerU not available - will use regex-based extraction only")


@dataclass
class ParseContext:
    """Tracks current parsing context during extraction.

    Note: area_type defaults to "Interior" as most ACM registers follow the pattern
    of listing interior spaces first and explicitly marking exterior/grounds areas.
    If no area type header is found, Interior is the most common assumption.
    """

    school_name: str = ""
    school_code: Optional[str] = None
    building_id: str = ""
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: str = "Interior"  # Default - most common case in ACM registers
    current_page: int = 1


@dataclass
class ExtractedACMRow:
    """Intermediate representation of an extracted ACM row."""

    # Context from parsing
    school_name: str
    school_code: Optional[str]
    building_id: str
    building_name: Optional[str]
    building_year: Optional[int]
    building_construction: Optional[str]
    room_id: Optional[str]
    room_name: Optional[str]
    room_area: Optional[float]
    area_type: str
    page_number: int

    # Row data
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None
    result: str = ""

    def to_acm_record_dict(self, source_id: str, classify: bool = True) -> dict:
        """Convert to dict suitable for ACMRecord creation.

        Args:
            source_id: ID of the source document
            classify: Whether to run product classification (default: True)

        Returns:
            Dict ready for ACMRecord creation
        """
        result = {
            "source_id": source_id,
            "school_name": self.school_name,
            "school_code": self.school_code,
            "building_id": self.building_id,
            "building_name": self.building_name,
            "building_year": self.building_year,
            "building_construction": self.building_construction,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "room_area": self.room_area,
            "area_type": self.area_type,
            "product": self.product,
            "material_description": self.material_description,
            "extent": self.extent,
            "location": self.location,
            "friable": self.friable,
            "material_condition": self.material_condition,
            "risk_status": self.risk_status,
            "result": self.result,
            "page_number": self.page_number,
        }

        # Normalize enum field values (E1-S12)
        # Note: hygienist_recommendations, sample_result, disturbance_potential
        # are populated by E1-S7 AI extraction — normalize those when available.
        try:
            from open_notebook.extractors.normalizers.enums import normalize_enum_value

            if result.get("material_condition"):
                result["material_condition"] = normalize_enum_value(
                    result["material_condition"], "condition"
                )
            if result.get("result"):
                result["result"] = normalize_enum_value(
                    result["result"], "sample_result"
                )
            if result.get("friable"):
                result["friable"] = normalize_enum_value(
                    result["friable"], "friability"
                )
        except Exception as e:
            logger.warning(f"Enum normalization failed for {self.product}: {e}")

        # Add product classification if enabled
        if classify:
            try:
                from open_notebook.extractors.normalizers.taxonomy import (
                    classify_product,
                )

                # Combine product and material description for better classification
                item_description = self.material_description
                if self.product:
                    item_description = f"{self.product} {item_description}"

                classification = classify_product(
                    item_description=item_description,
                    friability=self.friable,
                    product=self.product,
                )

                if classification.product_group and classification.product_type:
                    result["acm_product_group"] = classification.product_group
                    result["acm_product_type"] = classification.product_type
                    result["classification_confidence"] = classification.confidence
                    result["classification_method"] = classification.method
                    result["classification_override"] = False
            except Exception as e:
                logger.warning(f"Classification failed for {self.product}: {e}")

        return result


# ACM table detection - required headers (case-insensitive)
ACM_REQUIRED_HEADERS = {"product", "material description", "result"}
ACM_OPTIONAL_HEADERS = {
    "extent",
    "location",
    "friable",
    "material condition",
    "risk status",
    "risk",
}

# Regex patterns for structural markdown parsing
BUILDING_PATTERN = re.compile(
    r"^#+\s*(?:Building[:\s]*)?([A-Z]\d+[A-Z]?)\s*[-–]\s*([^-–\n]+?)(?:\s*[-–]\s*(\d{4}))?(?:\s*[-–]\s*([^-–\n]+?))?$",
    re.IGNORECASE | re.MULTILINE,
)

ROOM_PATTERN = re.compile(
    r"^#+\s*(?:Room[:\s]*)?([A-Z0-9]+-?R?\d+)\s*[-–]\s*([^-–\n]+?)(?:\s*[-–]\s*([\d.]+)\s*m²)?$",
    re.IGNORECASE | re.MULTILINE,
)

AREA_TYPE_PATTERN = re.compile(
    r"^#+\s*(?:Area\s*Type[:\s]*)?(\bExterior\b|\bInterior\b|\bGrounds\b)",
    re.IGNORECASE | re.MULTILINE,
)

SCHOOL_PATTERN = re.compile(
    r"^#\s*([^-–\n]+?)(?:\s*[-–]\s*(?:Asbestos|ACM|SAMP).*)?$",
    re.IGNORECASE | re.MULTILINE,
)

PAGE_PATTERN = re.compile(
    r"(?:[-—]+|<!--)\s*Page\s+(\d+)\s*(?:[-—]+|-->)", re.IGNORECASE
)


def extract_acm_records(
    markdown_content: Optional[str],
    source_id: str,
    pdf_path: Optional[str] = None,
    use_mineru: bool = True,
    classify: bool = True,
) -> List[dict]:
    """
    Extract ACM records from PDF or Docling markdown output.

    Extraction strategy:
    1. If use_mineru=True and pdf_path provided: Try MinerU table extraction
    2. If MinerU fails or unavailable: Fall back to regex-based markdown parsing
    3. Log which extraction method was used
    4. Optionally classify each record using Victorian BAR taxonomy

    Args:
        markdown_content: Markdown text from Docling (used as fallback)
        source_id: ID of the source document
        pdf_path: Path to source PDF file (optional, required for MinerU)
        use_mineru: Whether to attempt MinerU extraction (default: True)
        classify: Whether to run product classification (default: True)

    Returns:
        List of dicts ready for ACMRecord creation
    """
    # Try MinerU extraction first if enabled and PDF path provided
    if use_mineru and pdf_path and MINERU_AVAILABLE:
        try:
            logger.info(f"Attempting MinerU extraction for {pdf_path}")
            records = _extract_with_mineru(pdf_path, source_id)
            if records:
                logger.info(
                    f"Successfully extracted {len(records)} records using MinerU"
                )
                return records
            else:
                logger.warning(
                    "MinerU extraction returned no records, falling back to markdown parser"
                )
        except Exception as e:
            logger.warning(
                f"MinerU extraction failed: {e}. Falling back to markdown parser"
            )
    elif use_mineru and pdf_path and not MINERU_AVAILABLE:
        logger.warning(
            "MinerU extraction requested but not available. "
            "Falling back to markdown parser"
        )
    elif use_mineru and not pdf_path:
        logger.debug(
            "MinerU extraction enabled but no PDF path provided, using markdown parser"
        )

    # Fall back to regex-based markdown parsing
    # Single config-driven parser (E1-S11)
    selected_parser = get_parser()
    logger.info(
        f"Using regex-based markdown extraction for source {source_id} "
        f"(parser: {selected_parser.name})"
    )
    return _extract_from_markdown(
        markdown_content, source_id, classify=classify, parser=selected_parser
    )


def _extract_from_markdown(
    markdown_content: Optional[str],
    source_id: str,
    classify: bool = True,
    parser=None,
) -> List[dict]:
    """
    Extract ACM records from Docling markdown output (original regex-based method).

    Args:
        markdown_content: Markdown text from Docling
        source_id: ID of the source document
        classify: Whether to run product classification (default: True)
        parser: Selected consultant parser (uses generic if None)

    Returns:
        List of dicts ready for ACMRecord creation
    """
    if not markdown_content:
        logger.warning("Empty markdown content provided")
        return []

    context = ParseContext()
    extracted_rows: List[ExtractedACMRow] = []

    # Try to extract school name from title
    school_match = SCHOOL_PATTERN.search(markdown_content)
    if school_match:
        context.school_name = school_match.group(1).strip()
        logger.debug(f"Found school: {context.school_name}")

    # Split by lines for processing
    lines = markdown_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check for page markers
        page_match = PAGE_PATTERN.search(line)
        if page_match:
            context.current_page = int(page_match.group(1))
            logger.debug(f"Page marker found: {context.current_page}")

        # Check for area type header
        area_match = AREA_TYPE_PATTERN.match(line)
        if area_match:
            context.area_type = area_match.group(1).strip().title()
            logger.debug(f"Area type: {context.area_type}")

        # Check for building header
        building_match = BUILDING_PATTERN.match(line)
        if building_match:
            context.building_id = building_match.group(1).strip()
            context.building_name = building_match.group(2).strip()
            if building_match.group(3):
                try:
                    context.building_year = int(building_match.group(3))
                except ValueError:
                    logger.warning(f"Invalid building year: {building_match.group(3)}")
                    context.building_year = None
            else:
                context.building_year = None
            if building_match.group(4):
                context.building_construction = building_match.group(4).strip()
            else:
                context.building_construction = None
            # Reset room and area_type when building changes
            context.room_id = None
            context.room_name = None
            context.room_area = None
            context.area_type = "Interior"  # Reset to default
            logger.debug(f"Building: {context.building_id} - {context.building_name}")

        # Check for room header
        room_match = ROOM_PATTERN.match(line)
        if room_match:
            context.room_id = room_match.group(1).strip()
            context.room_name = room_match.group(2).strip()
            if room_match.group(3):
                try:
                    context.room_area = float(room_match.group(3))
                except ValueError:
                    pass
            logger.debug(f"Room: {context.room_id} - {context.room_name}")

        # Check for table start (line with pipes)
        if "|" in line and _looks_like_table_header(line, parser=parser):
            # Found potential table, parse it
            table_lines, end_idx = _extract_table_lines(lines, i)
            if table_lines:
                rows = _parse_acm_table(table_lines, context, parser=parser)
                extracted_rows.extend(rows)
            i = end_idx
            continue

        i += 1

    # Convert to dicts with optional classification
    result = [
        row.to_acm_record_dict(source_id, classify=classify) for row in extracted_rows
    ]

    # Generate enriched_text for each record (E1-S14)
    _enrich_record_dicts(result)

    logger.info(f"Extracted {len(result)} ACM records from source {source_id}")
    return result


def _extract_with_mineru(pdf_path: str, source_id: str) -> List[dict]:
    """
    Extract ACM records using MinerU table extraction.

    Args:
        pdf_path: Path to the PDF file
        source_id: ID of the source document

    Returns:
        List of dicts ready for ACMRecord creation

    Raises:
        Exception: If extraction fails
    """
    # Initialize MinerU extractor
    extractor = MineruTableExtractor(parse_method="auto")

    # Extract tables from PDF
    tables: List[ExtractedTable] = extractor.extract_tables_from_pdf(
        pdf_path=pdf_path, stitch_multipage=True
    )

    if not tables:
        logger.warning(f"No tables found in PDF: {pdf_path}")
        return []

    # Convert extracted tables to ACM records
    # Note: For now, we'll extract table structure but still rely on
    # the markdown content for full ACM record parsing. This is a
    # foundation for future HTML table parsing enhancement.
    logger.info(
        f"MinerU extracted {len(tables)} tables. "
        "Full HTML parsing not yet implemented - falling back to markdown."
    )

    # Return empty to trigger fallback
    # TODO: Implement HTML table parsing to ACM records in future iteration
    return []


def _looks_like_table_header(
    line: str,
    parser=None,
) -> bool:
    """Check if line looks like a markdown table header.

    Uses the parser's register headers for detection if available,
    otherwise falls back to the default ACM required headers.
    """
    cells = [c.strip().lower() for c in line.split("|") if c.strip()]
    joined = " ".join(cells)

    # Check for standard ACM required headers
    return any(header in joined for header in ACM_REQUIRED_HEADERS)


def _has_pipe_continuation(lines: List[str], from_idx: int) -> bool:
    """Check if pipe lines after a gap are a table continuation (not a new table).

    A new table starts with a header row followed by a separator (|---|).
    A continuation is just data rows without a new header+separator.
    Used by _extract_table_lines to determine if a table continues after a gap.
    """
    j = from_idx
    while j < len(lines):
        ahead = lines[j].strip()
        if ahead == "" or PAGE_PATTERN.search(ahead):
            j += 1
            continue
        if "|" not in ahead:
            return False
        # Found a pipe line - check if the NEXT line is a separator (|---|)
        # If so, this is a new table header, not a continuation
        if j + 1 < len(lines):
            next_line = lines[j + 1].strip()
            if "|" in next_line and "---" in next_line:
                return False  # New table (header + separator)
        return True  # Continuation row (no separator follows)
    return False


def _extract_table_lines(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    """Extract all lines belonging to a table starting at start_idx.

    Handles multi-page tables by continuing past page markers (Bug 2 fix).
    Page markers are included in the returned table_lines so that
    _parse_acm_table can update context.current_page per row.

    Args:
        lines: All lines from the markdown document
        start_idx: Index of the first table line (header row)

    Returns:
        Tuple of (table_lines, end_index) where:
        - table_lines: List of all lines in the table (including header, separator,
          and any page markers embedded in a multi-page table)
        - end_index: Index of the first line after the table
    """
    table_lines = []
    i = start_idx

    while i < len(lines):
        line = lines[i].strip()
        if "|" in line:
            table_lines.append(line)
            i += 1
        elif table_lines and PAGE_PATTERN.search(line):
            # Page marker within a multi-page table - include for tracking
            table_lines.append(line)
            i += 1
        elif line == "" and table_lines:
            # Empty line - check if table continues after gap (possibly past page markers)
            if _has_pipe_continuation(lines, i + 1):
                i += 1  # Skip empty line, continue collecting
            else:
                break
        elif table_lines:
            # Non-pipe, non-page-marker line ends table
            break
        else:
            i += 1
            break

    return table_lines, i


def _parse_acm_table(
    table_lines: List[str],
    context: ParseContext,
    parser=None,
) -> List[ExtractedACMRow]:
    """Parse markdown table lines into ExtractedACMRow objects."""
    if len(table_lines) < 2:
        return []

    # Parse header row
    header_line = table_lines[0]
    headers = [h.strip().lower() for h in header_line.split("|") if h.strip()]

    # Check if this is an ACM table
    joined_headers = " ".join(headers)
    is_acm_table = any(h in joined_headers for h in ACM_REQUIRED_HEADERS)

    if not is_acm_table:
        logger.debug(f"Skipping non-ACM table with headers: {headers}")
        return []

    # Map headers to field names
    header_map = _create_header_map(headers)

    rows = []
    # Skip header and separator lines
    data_start = 2 if len(table_lines) > 2 and "---" in table_lines[1] else 1

    for line in table_lines[data_start:]:
        # Check for page markers FIRST (before "---" check since page markers contain ---)
        page_match = PAGE_PATTERN.search(line)
        if page_match:
            context.current_page = int(page_match.group(1))
            continue

        if "---" in line:
            continue

        if not line or "|" not in line:
            continue

        cells = [c.strip() for c in line.split("|")]
        # Remove empty first/last cells from pipe splits
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) < 2:
            continue

        row = _create_row_from_cells(cells, header_map, context)
        if row and row.product:  # Only add if we have a product
            rows.append(row)

    return rows


def _create_header_map(headers: List[str]) -> Dict[str, int]:
    """Create mapping from field names to column indices."""
    mapping = {}

    for i, header in enumerate(headers):
        header_lower = header.lower()

        if "product" in header_lower:
            mapping["product"] = i
        elif "material" in header_lower and "desc" in header_lower:
            mapping["material_description"] = i
        elif "extent" in header_lower:
            mapping["extent"] = i
        elif "location" in header_lower:
            mapping["location"] = i
        elif "friable" in header_lower:
            mapping["friable"] = i
        elif "condition" in header_lower:
            mapping["material_condition"] = i
        elif "risk" in header_lower:
            mapping["risk_status"] = i
        elif "result" in header_lower:
            mapping["result"] = i

    return mapping


def _create_row_from_cells(
    cells: List[str], header_map: Dict[str, int], context: ParseContext
) -> Optional[ExtractedACMRow]:
    """Create ExtractedACMRow from table cells."""

    def get_cell(field: str) -> Optional[str]:
        idx = header_map.get(field)
        if idx is not None and idx < len(cells):
            val = cells[idx].strip()
            return val if val else None
        return None

    product = get_cell("product")
    material_desc = get_cell("material_description")
    result = get_cell("result")

    # Skip if missing required fields - both product AND material_description are required
    if not product or not material_desc:
        return None

    # Handle "No Asbestos" cases
    if result and "no asbestos" in result.lower():
        result = "Not Detected"
    elif result and "detected" in result.lower():
        result = "Detected"

    return ExtractedACMRow(
        school_name=context.school_name or "Unknown School",
        school_code=context.school_code,
        building_id=context.building_id or "Unknown",
        building_name=context.building_name,
        building_year=context.building_year,
        building_construction=context.building_construction,
        room_id=context.room_id,
        room_name=context.room_name,
        room_area=context.room_area,
        area_type=context.area_type,
        page_number=context.current_page,
        product=product or "",
        material_description=material_desc or "",
        extent=get_cell("extent"),
        location=get_cell("location"),
        friable=get_cell("friable"),
        material_condition=get_cell("material_condition"),
        risk_status=get_cell("risk_status"),
        result=result or "",
    )


def _enrich_record_dicts(record_dicts: List[dict]) -> None:
    """Generate enriched_text for each record dict (E1-S14).

    Creates temporary ACMRecord instances to use the enrichment method,
    then stores the result back in the dict.
    """
    from open_notebook.domain.acm import ACMRecord

    for record_dict in record_dicts:
        try:
            temp_record = ACMRecord(**record_dict)
            record_dict["enriched_text"] = temp_record.get_enriched_embedding_text()
        except Exception as e:
            logger.debug(f"Could not generate enriched_text: {e}")
