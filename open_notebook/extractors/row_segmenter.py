"""Row segmentation engine for DoclingDocument JSON tables.

Parses DoclingDocument table JSON into individual RawTableRow objects,
handling merged cells, multi-page tables, sub-headers, notes, and
consultant-specific column layouts.

No LLM calls — all deterministic Python with Jaro-Winkler fuzzy matching.
"""

import html
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

from open_notebook.extractors.consensus.matcher import _jaro_winkler
from open_notebook.extractors.normalizers.content import normalize_docling_text

# ---------------------------------------------------------------------------
# Column alias mapping — canonical name → list of known aliases
# ---------------------------------------------------------------------------

COLUMN_ALIASES: dict[str, list[str]] = {
    "room_location": [
        "room",
        "room/area",
        "area",
        "location",
        "room no",
        "location description",  # NSW DoE SAMP
    ],
    "item_description": [
        "material",
        "product",
        "item",
        "description",
        "product description",
        "acm type",
        "building element",  # Greencap ARA
        "material type",  # Greencap ARA
    ],
    "friability": [
        "friable",
        "f/nf",
        "friability",
        "type",
        "assumed/confirmed",  # NSW DoE SAMP
    ],
    "condition": ["condition", "material condition", "state", "assessment"],
    "sample_number": [
        "sample",
        "sample#",
        "sample no",
        "nata no",
        "item no",
        "item no.",  # Greencap ARA / NSW DoE
    ],
    "sample_result": [
        "result",
        "lab result",
        "analysis",
        "acm status",  # Greencap ARA
    ],
    "quantity": ["quantity", "qty", "area", "extent", "m²"],
    "recommendation": ["recommendation", "action", "management"],
    "accessibility": ["access", "accessible"],
    "asbestos_type": ["asbestos type", "fibre type", "fibre"],
    "disturbance_potential": [
        "disturbance",
        "dp",
        "risk",
        "risk rating",  # Greencap ARA
        "priority",  # Greencap ARA
    ],
    "specific_location": [
        "specific location",
        "position",
        "element",
        "where",
    ],
}

# Material keywords that indicate a multi-item cell (Type E1)
_MATERIAL_KEYWORDS = (
    "tile",
    "sheet",
    "fibro",
    "cement",
    "vinyl",
    "insulation",
    "coating",
    "gasket",
    "rope",
    "board",
)

# Sub-header level regex (Type E3)
_LEVEL_REGEX = re.compile(
    r"^(LEVEL|GROUND|FIRST|SECOND|THIRD|ROOF|BASEMENT|EXTERNAL|INTERNAL|MEZZANINE)\b",
    re.IGNORECASE,
)

# Jaro-Winkler similarity threshold for column matching
_JW_THRESHOLD = 0.70


# ---------------------------------------------------------------------------
# RawTableRow model
# ---------------------------------------------------------------------------


class RawTableRow(BaseModel):
    """One row from a PDF table, ready for per-row LLM extraction."""

    # Source tracking
    source_id: str
    building_id: str
    table_index: int = Field(description="Which table within building (0-indexed)")
    row_index: int = Field(description="Row position within table (0-indexed)")
    page_number: int = Field(description="PDF page from Docling prov.page_no")

    # Content (from DoclingDocument JSON)
    cells: dict[str, str] = Field(
        description="Column header -> cell value. Canonical names where mapped."
    )
    raw_text: str = Field(description="Plain text concatenation for fallback/debug")

    # Column mapping
    column_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Canonical -> original header",
    )

    # Segmentation metadata
    confidence: float = Field(default=1.0)
    needs_llm_split: bool = Field(default=False, description="Multi-item cell, Type E1")
    is_synthetic: bool = Field(
        default=False,
        description="From text scan, not table (Type D/F)",
    )
    carried_forward_fields: list[str] = Field(
        default_factory=list,
        description="Merged cell inheritance (Type C)",
    )
    edge_case_type: Optional[str] = Field(
        default=None, description="A, B, C, D, E1, E2, E3, F, G, H"
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Context from note/sub-header rows",
    )
    current_level: Optional[str] = Field(
        default=None,
        description="Floor/level from sub-header (Type E3)",
    )

    # Provenance from Docling JSON
    source_table_num_rows: Optional[int] = Field(default=None)
    source_table_num_cols: Optional[int] = Field(default=None)
    bbox: Optional[dict] = Field(
        default=None, description="Bounding box from Docling prov"
    )

    # HTML debug
    debug_html: Optional[str] = Field(
        default=None, description="HTML <tr> for visual debugging"
    )


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


def detect_column_mapping(header_cells: list[dict]) -> dict[str, str]:
    """Detect canonical column names from Docling header cells via fuzzy matching.

    Args:
        header_cells: List of Docling header cell dicts (must contain ``text`` field).

    Returns:
        Dict mapping canonical column name -> original header text.
        If no canonical match is found for a header, the original header text
        is used as both key and value.
    """
    mapping: dict[str, str] = {}
    # Track which canonical names have already been claimed
    claimed: set[str] = set()

    for cell in header_cells:
        header_text = cell.get("text", "").strip()
        if not header_text:
            continue

        header_lower = header_text.lower()
        best_canonical: Optional[str] = None
        best_score = 0.0

        for canonical, aliases in COLUMN_ALIASES.items():
            if canonical in claimed:
                continue
            for alias in aliases:
                score = _jaro_winkler(header_lower, alias.lower())
                if score > best_score:
                    best_score = score
                    best_canonical = canonical

        if best_canonical is not None and best_score >= _JW_THRESHOLD:
            mapping[best_canonical] = header_text
            claimed.add(best_canonical)
        else:
            # Keep original header text as-is
            mapping[header_text] = header_text

    return mapping


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_span_registry(
    cells: list[dict], num_cols: int
) -> dict[tuple[int, int], str]:
    """Build a registry of spanned cell values.

    For cells with ``row_span > 1`` or ``col_span > 1``, maps every
    covered ``(row, col)`` position to the cell's text value.

    Args:
        cells: List of Docling cell dicts.
        num_cols: Total column count for the table.

    Returns:
        Dict keyed by ``(row_idx, col_idx)`` with the cell text as value.
    """
    registry: dict[tuple[int, int], str] = {}
    for cell in cells:
        row_span = cell.get("row_span", 1)
        col_span = cell.get("col_span", 1)
        if row_span <= 1 and col_span <= 1:
            continue
        start_row = cell.get("start_row_offset_idx", 0)
        end_row = cell.get("end_row_offset_idx", start_row + row_span)
        start_col = cell.get("start_col_offset_idx", 0)
        end_col = cell.get("end_col_offset_idx", start_col + col_span)
        text = cell.get("text", "")
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                registry[(r, c)] = text
    return registry


def _has_material_keywords(text: str) -> bool:
    """Check if text contains newlines AND material keywords (Type E1)."""
    if "\n" not in text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in _MATERIAL_KEYWORDS)


def _row_raw_text(cells_dict: dict[str, str]) -> str:
    """Concatenate cell values into a plain text string."""
    return " | ".join(v for v in cells_dict.values() if v.strip())


# ---------------------------------------------------------------------------
# Core segmentation
# ---------------------------------------------------------------------------


def segment_docling_table(
    table_data: dict,
    building_id: str,
    source_id: str,
    page_number: int,
    table_index: int = 0,
    initial_level: Optional[str] = None,
) -> list[RawTableRow]:
    """Segment a single Docling table JSON into individual rows.

    Args:
        table_data: A single Docling table JSON object with keys
            ``table_cells``, ``num_rows``, ``num_cols``.
        building_id: Building identifier for provenance.
        source_id: Source document identifier.
        page_number: PDF page number from Docling provenance.
        table_index: 0-indexed table position within the building.
        initial_level: Optional initial floor/level context.

    Returns:
        List of ``RawTableRow`` objects, one per data row.
    """
    all_cells = table_data.get("table_cells", [])
    num_rows = table_data.get("num_rows", 0)
    num_cols = table_data.get("num_cols", 0)

    if not all_cells or num_rows == 0:
        return []

    # 1. Separate headers from data cells
    header_cells: list[dict] = []
    data_cells: list[dict] = []
    header_rows: set[int] = set()

    for cell in all_cells:
        if cell.get("column_header", False):
            header_cells.append(cell)
            start_r = cell.get("start_row_offset_idx", 0)
            end_r = cell.get("end_row_offset_idx", start_r + 1)
            for r in range(start_r, end_r):
                header_rows.add(r)
        else:
            data_cells.append(cell)

    if not data_cells:
        return []

    # 2. Detect column mapping from headers
    column_mapping = detect_column_mapping(header_cells)

    # Build reverse mapping: col_index -> canonical name
    # Header cells are sorted by start_col_offset_idx
    sorted_headers = sorted(
        header_cells,
        key=lambda c: c.get("start_col_offset_idx", 0),
    )
    col_index_to_canonical: dict[int, str] = {}
    for hcell in sorted_headers:
        h_text = hcell.get("text", "").strip()
        start_col = hcell.get("start_col_offset_idx", 0)
        col_span = hcell.get("col_span", 1)
        # Find which canonical name this header mapped to
        canonical_for_header: Optional[str] = None
        for canonical, original in column_mapping.items():
            if original == h_text:
                canonical_for_header = canonical
                break
        if canonical_for_header:
            for c in range(start_col, start_col + col_span):
                col_index_to_canonical[c] = canonical_for_header

    # 3. Build span registry
    span_registry = _build_span_registry(all_cells, num_cols)

    # 4. Group data cells by row
    rows_by_idx: dict[int, list[dict]] = {}
    for cell in data_cells:
        row_idx = cell.get("start_row_offset_idx", 0)
        if row_idx in header_rows:
            continue
        rows_by_idx.setdefault(row_idx, []).append(cell)

    # 5. Process rows
    rows: list[RawTableRow] = []
    current_level = initial_level
    pending_notes: Optional[str] = None
    row_counter = 0

    for row_idx in sorted(rows_by_idx.keys()):
        row_cells = rows_by_idx[row_idx]

        # Check for single-cell spanning entire row (E2 / E3)
        if len(row_cells) == 1:
            cell = row_cells[0]
            col_span = cell.get("col_span", 1)
            if col_span >= num_cols:
                text = cell.get("text", "").strip()
                if not text:
                    continue

                # Type E3: sub-header (level indicator)
                if _LEVEL_REGEX.match(text):
                    current_level = text
                    continue

                # Type E2: note row
                pending_notes = text
                continue

        # Build cells dict using canonical column names
        cells_dict: dict[str, str] = {}
        carried_forward: list[str] = []
        edge_cases: set[str] = set()
        has_llm_split = False

        for cell in row_cells:
            col_idx = cell.get("start_col_offset_idx", 0)
            text = cell.get("text", "")
            canonical = col_index_to_canonical.get(col_idx)
            key = canonical if canonical else f"col_{col_idx}"
            normalized = normalize_docling_text(text)
            cells_dict[key] = normalized

            # Type E1: multi-item cell
            if _has_material_keywords(text):
                has_llm_split = True
                edge_cases.add("E1")

        # Fill missing columns from span registry (Type C)
        for c in range(num_cols):
            canonical = col_index_to_canonical.get(c)
            key = canonical if canonical else f"col_{c}"
            if key not in cells_dict and (row_idx, c) in span_registry:
                text = span_registry[(row_idx, c)]
                cells_dict[key] = normalize_docling_text(text)
                carried_forward.append(key)
                edge_cases.add("C")

        if carried_forward:
            edge_cases.add("C")

        # Determine edge case type
        if not edge_cases:
            edge_case_type = "A"
        elif len(edge_cases) == 1:
            edge_case_type = next(iter(edge_cases))
        else:
            # Multiple edge cases, join them
            edge_case_type = "+".join(sorted(edge_cases))

        raw_text = _row_raw_text(cells_dict)

        row = RawTableRow(
            source_id=source_id,
            building_id=building_id,
            table_index=table_index,
            row_index=row_counter,
            page_number=page_number,
            cells=cells_dict,
            raw_text=raw_text,
            column_mapping=column_mapping,
            confidence=1.0,
            needs_llm_split=has_llm_split,
            is_synthetic=False,
            carried_forward_fields=carried_forward,
            edge_case_type=edge_case_type,
            extraction_notes=pending_notes,
            current_level=current_level,
            source_table_num_rows=num_rows,
            source_table_num_cols=num_cols,
        )
        row.debug_html = generate_row_html(row)
        rows.append(row)

        # Reset pending notes after attaching
        pending_notes = None
        row_counter += 1

    return rows


# ---------------------------------------------------------------------------
# Multi-table handling
# ---------------------------------------------------------------------------


def _row_similarity(row_a: dict[str, str], row_b: dict[str, str]) -> float:
    """Compute average Jaro-Winkler similarity across shared keys.

    Args:
        row_a: First row cells dict.
        row_b: Second row cells dict.

    Returns:
        Average similarity score in [0.0, 1.0].
    """
    shared_keys = set(row_a.keys()) & set(row_b.keys())
    if not shared_keys:
        return 0.0
    total = sum(_jaro_winkler(row_a[k].lower(), row_b[k].lower()) for k in shared_keys)
    return total / len(shared_keys)


def _find_shared_key_column(
    mapping_a: dict[str, str], mapping_b: dict[str, str]
) -> Optional[str]:
    """Find a shared canonical column between two column mappings.

    Args:
        mapping_a: Column mapping for table A.
        mapping_b: Column mapping for table B.

    Returns:
        Canonical column name if a shared key exists, else None.
    """
    shared = set(mapping_a.keys()) & set(mapping_b.keys())
    # Prefer room_location or sample_number as join keys
    for preferred in ("room_location", "sample_number", "item_description"):
        if preferred in shared:
            return preferred
    return next(iter(shared)) if shared else None


def segment_multiple_tables(
    tables: list[dict],
    building_id: str,
    source_id: str,
    building_page_range: tuple[int, int] | None = None,
) -> list[RawTableRow]:
    """Segment multiple Docling tables for a single building.

    Handles multi-page table merging (Type B) and split-table joining (Type H).

    Args:
        tables: List of Docling table JSON objects.
        building_id: Building identifier.
        source_id: Source document identifier.
        building_page_range: Optional ``(start_page, end_page)`` to filter
            tables by page number.

    Returns:
        Flat list of ``RawTableRow`` objects.
    """
    if not tables:
        return []

    # Filter by page range if provided
    if building_page_range is not None:
        start_page, end_page = building_page_range
        filtered = []
        for t in tables:
            page = t.get("page_number", 0)
            if start_page <= page <= end_page:
                filtered.append(t)
        if not filtered:
            logger.warning(
                "Page filter returned 0 tables for building %s (range %s-%s) — "
                "falling back to all %d tables",
                building_id or "?",
                start_page,
                end_page,
                len(tables),
            )
        tables = filtered if filtered else tables

    if len(tables) == 1:
        page = tables[0].get("page_number", 1)
        return segment_docling_table(
            tables[0],
            building_id=building_id,
            source_id=source_id,
            page_number=page,
        )

    # Group by num_cols
    groups: dict[int, list[dict]] = {}
    for t in tables:
        nc = t.get("num_cols", 0)
        groups.setdefault(nc, []).append(t)

    all_rows: list[RawTableRow] = []

    if len(groups) == 1:
        # Type B: same num_cols → multi-page merge
        col_count = next(iter(groups))
        group_tables = groups[col_count]
        merged_rows: list[RawTableRow] = []
        current_level: Optional[str] = None

        for idx, t in enumerate(group_tables):
            page = t.get("page_number", 1)
            table_rows = segment_docling_table(
                t,
                building_id=building_id,
                source_id=source_id,
                page_number=page,
                table_index=idx,
                initial_level=current_level,
            )
            if not table_rows:
                continue

            # Update current_level from last row's level
            if table_rows:
                last_level = table_rows[-1].current_level
                if last_level:
                    current_level = last_level

            # Deduplicate overlap rows (Type B)
            if merged_rows and table_rows:
                last_merged = merged_rows[-1]
                first_new = table_rows[0]
                sim = _row_similarity(last_merged.cells, first_new.cells)
                if sim > 0.90:
                    table_rows = table_rows[1:]

            for r in table_rows:
                r.edge_case_type = "B" if idx > 0 else r.edge_case_type
            merged_rows.extend(table_rows)

        # Re-index rows
        for i, r in enumerate(merged_rows):
            r.row_index = i
        all_rows = merged_rows

    else:
        # Type H: different num_cols → JOIN on shared key column
        group_list = list(groups.values())
        # Segment each group separately first
        segmented_groups: list[list[RawTableRow]] = []
        table_idx_offset = 0
        for group in group_list:
            group_rows: list[RawTableRow] = []
            for t in group:
                page = t.get("page_number", 1)
                rows = segment_docling_table(
                    t,
                    building_id=building_id,
                    source_id=source_id,
                    page_number=page,
                    table_index=table_idx_offset,
                )
                group_rows.extend(rows)
                table_idx_offset += 1
            segmented_groups.append(group_rows)

        if len(segmented_groups) < 2:
            for sg in segmented_groups:
                all_rows.extend(sg)
        else:
            # Try to JOIN the first two groups on a shared key
            group_a = segmented_groups[0]
            group_b = segmented_groups[1]

            if group_a and group_b:
                mapping_a = group_a[0].column_mapping
                mapping_b = group_b[0].column_mapping
                shared_key = _find_shared_key_column(mapping_a, mapping_b)

                if shared_key:
                    # Index group_b rows by shared key value
                    b_index: dict[str, RawTableRow] = {}
                    for rb in group_b:
                        key_val = rb.cells.get(shared_key, "").strip().lower()
                        if key_val:
                            b_index[key_val] = rb

                    for ra in group_a:
                        key_val = ra.cells.get(shared_key, "").strip().lower()
                        if key_val and key_val in b_index:
                            # Merge cells from group_b into group_a row
                            rb = b_index[key_val]
                            for k, v in rb.cells.items():
                                if k not in ra.cells or not ra.cells[k].strip():
                                    ra.cells[k] = v
                            ra.edge_case_type = "H"
                            ra.column_mapping.update(rb.column_mapping)
                        all_rows.append(ra)

                    # Add unmatched group_b rows
                    matched_keys = {
                        r.cells.get(shared_key, "").strip().lower() for r in group_a
                    }
                    for rb in group_b:
                        key_val = rb.cells.get(shared_key, "").strip().lower()
                        if key_val not in matched_keys:
                            rb.edge_case_type = "H"
                            all_rows.append(rb)
                else:
                    # No shared key — just concat
                    all_rows.extend(group_a)
                    all_rows.extend(group_b)

            # Append remaining groups (3+)
            for sg in segmented_groups[2:]:
                all_rows.extend(sg)

        # Re-index
        for i, r in enumerate(all_rows):
            r.row_index = i

    return all_rows


# ---------------------------------------------------------------------------
# Text scan for synthetic rows (Type D / Type F)
# ---------------------------------------------------------------------------

# Type F patterns: location — "Not Sampled" or "No Access"
_TYPE_F_PATTERN = re.compile(
    r"(.+?)\s*[—–\-]\s*[\"']?(Not Sampled|No Access)[\"']?",
    re.IGNORECASE,
)

# Type D patterns: hierarchical text (Building/Level/Room/Item indentation)
_TYPE_D_BUILDING = re.compile(r"^(Building|Block|Wing)\s*[:\-]?\s*(.+)", re.IGNORECASE)
_TYPE_D_LEVEL = re.compile(
    r"^\s{2,4}(Level|Floor|Ground|First|Second|Third|Roof|Basement|External)\s*[:\-]?\s*(.*)",
    re.IGNORECASE,
)
_TYPE_D_ROOM = re.compile(r"^\s{4,8}(Room|Area|Space)\s*[:\-]?\s*(.+)", re.IGNORECASE)
_TYPE_D_ITEM = re.compile(r"^\s{6,12}[•\-\*]\s*(.+)", re.IGNORECASE)


def scan_text_for_synthetics(
    markdown: str,
    building_id: str,
    source_id: str,
) -> list[RawTableRow]:
    """Scan raw markdown text for synthetic ACM rows.

    Detects Type F (Not Sampled / No Access) and Type D (hierarchical text)
    patterns in free-form text outside of tables.

    Args:
        markdown: Raw markdown text content to scan.
        building_id: Building identifier.
        source_id: Source document identifier.

    Returns:
        List of synthetic ``RawTableRow`` objects.
    """
    if not markdown:
        return []

    rows: list[RawTableRow] = []
    row_counter = 0

    # Type F: "Location — Not Sampled" / "Location — No Access"
    for match in _TYPE_F_PATTERN.finditer(markdown):
        location = match.group(1).strip()
        status = match.group(2).strip()
        cells = {
            "room_location": location,
            "sample_result": status,
        }
        row = RawTableRow(
            source_id=source_id,
            building_id=building_id,
            table_index=0,
            row_index=row_counter,
            page_number=0,
            cells=cells,
            raw_text=f"{location} — {status}",
            is_synthetic=True,
            edge_case_type="F",
            confidence=0.7,
        )
        row.debug_html = generate_row_html(row)
        rows.append(row)
        row_counter += 1

    # Type D: hierarchical text parsing
    current_level: Optional[str] = None
    current_room: Optional[str] = None
    lines = markdown.splitlines()

    for line in lines:
        level_match = _TYPE_D_LEVEL.match(line)
        if level_match:
            current_level = level_match.group(0).strip()
            continue

        room_match = _TYPE_D_ROOM.match(line)
        if room_match:
            current_room = room_match.group(2).strip()
            continue

        item_match = _TYPE_D_ITEM.match(line)
        if item_match and current_room:
            item_text = item_match.group(1).strip()
            cells: dict[str, str] = {
                "room_location": current_room,
                "item_description": item_text,
            }
            row = RawTableRow(
                source_id=source_id,
                building_id=building_id,
                table_index=0,
                row_index=row_counter,
                page_number=0,
                cells=cells,
                raw_text=f"{current_room}: {item_text}",
                is_synthetic=True,
                edge_case_type="D",
                current_level=current_level,
                confidence=0.5,
            )
            row.debug_html = generate_row_html(row)
            rows.append(row)
            row_counter += 1

    return rows


# ---------------------------------------------------------------------------
# HTML debug output
# ---------------------------------------------------------------------------


def generate_row_html(row: RawTableRow) -> str:
    """Generate an HTML ``<tr>`` element for a single row.

    Includes ``data-flags`` attributes for visual debugging of edge cases.

    Args:
        row: The ``RawTableRow`` to render.

    Returns:
        HTML string for the table row.
    """
    cells_html = "".join(f"<td>{html.escape(v)}</td>" for v in row.cells.values())
    flags: list[str] = []
    if row.carried_forward_fields:
        flags.append(f"merged:{','.join(row.carried_forward_fields)}")
    if row.needs_llm_split:
        flags.append("needs_split")
    if row.is_synthetic:
        flags.append("synthetic")
    if row.edge_case_type:
        flags.append(f"type:{row.edge_case_type}")
    flag_attr = f' data-flags="{html.escape(" ".join(flags))}"' if flags else ""
    return f"<tr{flag_attr}>{cells_html}</tr>"


def generate_debug_table(rows: list[RawTableRow], building_name: str) -> str:
    """Generate a full HTML debug table for a building.

    Args:
        rows: List of ``RawTableRow`` objects for the building.
        building_name: Building name for the table caption.

    Returns:
        Complete HTML table string.
    """
    if not rows:
        return (
            f"<table><caption>{html.escape(building_name)} (no rows)</caption></table>"
        )

    # Collect all column keys from the first row
    columns = list(rows[0].cells.keys()) if rows else []

    thead = "<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in columns) + "</tr>"

    tbody_rows: list[str] = []
    for row in rows:
        row_html = row.debug_html or generate_row_html(row)
        tbody_rows.append(row_html)

    return (
        f"<table>"
        f"<caption>{html.escape(building_name)}</caption>"
        f"<thead>{thead}</thead>"
        f"<tbody>{''.join(tbody_rows)}</tbody>"
        f"</table>"
    )
