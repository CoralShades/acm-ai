"""
ACM Register Extraction from Docling Markdown Output

Parses markdown content produced by Docling to extract structured
ACM (Asbestos Containing Material) records with hierarchical
Building > Room > Item relationships.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from loguru import logger


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

    def to_acm_record_dict(self, source_id: str) -> dict:
        """Convert to dict suitable for ACMRecord creation."""
        return {
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

# Regex patterns - using possessive quantifiers and atomic groups to prevent ReDoS
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

PAGE_PATTERN = re.compile(r"(?:^|\n)[-—]+\s*Page\s+(\d+)\s*[-—]+", re.IGNORECASE)


def extract_acm_records(markdown_content: Optional[str], source_id: str) -> List[dict]:
    """
    Extract ACM records from Docling markdown output.

    Args:
        markdown_content: Markdown text from Docling
        source_id: ID of the source document

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
        if "|" in line and _looks_like_table_header(line):
            # Found potential table, parse it
            table_lines, end_idx = _extract_table_lines(lines, i)
            if table_lines:
                rows = _parse_acm_table(table_lines, context)
                extracted_rows.extend(rows)
            i = end_idx
            continue

        i += 1

    # Convert to dicts
    result = [row.to_acm_record_dict(source_id) for row in extracted_rows]
    logger.info(f"Extracted {len(result)} ACM records from source {source_id}")
    return result


def _looks_like_table_header(line: str) -> bool:
    """Check if line looks like a markdown table header."""
    cells = [c.strip().lower() for c in line.split("|") if c.strip()]
    # Check if any required ACM headers are present
    return any(header in " ".join(cells) for header in ACM_REQUIRED_HEADERS)


def _extract_table_lines(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    """Extract all lines belonging to a table starting at start_idx.

    Args:
        lines: All lines from the markdown document
        start_idx: Index of the first table line (header row)

    Returns:
        Tuple of (table_lines, end_index) where:
        - table_lines: List of all lines in the table (including header and separator)
        - end_index: Index of the first line after the table
    """
    table_lines = []
    i = start_idx

    while i < len(lines):
        line = lines[i].strip()
        if "|" in line:
            table_lines.append(line)
            i += 1
        elif line == "" and table_lines:
            # Empty line might end table, but check next line
            if i + 1 < len(lines) and "|" in lines[i + 1]:
                i += 1
            else:
                break
        elif table_lines:
            # Non-pipe line ends table
            break
        else:
            i += 1
            break

    return table_lines, i


def _parse_acm_table(
    table_lines: List[str], context: ParseContext
) -> List[ExtractedACMRow]:
    """Parse markdown table lines into ExtractedACMRow objects."""
    if len(table_lines) < 2:
        return []

    # Parse header row
    header_line = table_lines[0]
    headers = [h.strip().lower() for h in header_line.split("|") if h.strip()]

    # Check if this is an ACM table
    if not any(h in " ".join(headers) for h in ACM_REQUIRED_HEADERS):
        logger.debug(f"Skipping non-ACM table with headers: {headers}")
        return []

    # Map headers to field names
    header_map = _create_header_map(headers)

    rows = []
    # Skip header and separator lines
    data_start = 2 if len(table_lines) > 2 and "---" in table_lines[1] else 1

    for line in table_lines[data_start:]:
        if "---" in line:
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
