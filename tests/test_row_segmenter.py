"""Comprehensive tests for the Row Segmentation Engine.

Each test covers a specific edge case type (A through H) from the
ACM table extraction catalog, using realistic Australian school data.
"""

import pytest

from open_notebook.extractors.row_segmenter import (
    COLUMN_ALIASES,
    RawTableRow,
    detect_column_mapping,
    generate_debug_table,
    generate_row_html,
    scan_text_for_synthetics,
    segment_docling_table,
    segment_multiple_tables,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_header_cell(
    text: str,
    col_idx: int,
    row_idx: int = 0,
    col_span: int = 1,
) -> dict:
    """Create a Docling header cell dict."""
    return {
        "text": text,
        "column_header": True,
        "row_span": 1,
        "col_span": col_span,
        "start_row_offset_idx": row_idx,
        "end_row_offset_idx": row_idx + 1,
        "start_col_offset_idx": col_idx,
        "end_col_offset_idx": col_idx + col_span,
    }


def _make_data_cell(
    text: str,
    row_idx: int,
    col_idx: int,
    row_span: int = 1,
    col_span: int = 1,
) -> dict:
    """Create a Docling data cell dict."""
    return {
        "text": text,
        "column_header": False,
        "row_span": row_span,
        "col_span": col_span,
        "start_row_offset_idx": row_idx,
        "end_row_offset_idx": row_idx + row_span,
        "start_col_offset_idx": col_idx,
        "end_col_offset_idx": col_idx + col_span,
    }


def _standard_headers(num_cols: int = 5) -> list[dict]:
    """Create standard ACM register header row with 5 columns."""
    headers = ["Room", "Material", "Friable", "Condition", "Sample No"]
    return [_make_header_cell(h, i) for i, h in enumerate(headers[:num_cols])]


def _standard_5col_table() -> dict:
    """Create a standard 5-column, 5-row ACM table for Broadmeadows PS."""
    headers = _standard_headers(5)
    data_rows = [
        # Row 1 (row_idx=1): Room 101
        [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("No", 1, 2),
            _make_data_cell("Good", 1, 3),
            _make_data_cell("34511-039-001", 1, 4),
        ],
        # Row 2 (row_idx=2): Library
        [
            _make_data_cell("Library", 2, 0),
            _make_data_cell("Vinyl floor tiles", 2, 1),
            _make_data_cell("No", 2, 2),
            _make_data_cell("Fair", 2, 3),
            _make_data_cell("34511-039-002", 2, 4),
        ],
        # Row 3 (row_idx=3): Staff Room
        [
            _make_data_cell("Staff Room", 3, 0),
            _make_data_cell("Fibro eave lining", 3, 1),
            _make_data_cell("Yes", 3, 2),
            _make_data_cell("Poor", 3, 3),
            _make_data_cell("34511-039-003", 3, 4),
        ],
        # Row 4 (row_idx=4): Hall
        [
            _make_data_cell("Hall", 4, 0),
            _make_data_cell("Switchboard backing", 4, 1),
            _make_data_cell("No", 4, 2),
            _make_data_cell("Good", 4, 3),
            _make_data_cell("34511-039-004", 4, 4),
        ],
        # Row 5 (row_idx=5): Corridor
        [
            _make_data_cell("Corridor", 5, 0),
            _make_data_cell("Cement sheet wall", 5, 1),
            _make_data_cell("No", 5, 2),
            _make_data_cell("Good", 5, 3),
            _make_data_cell("34511-039-005", 5, 4),
        ],
    ]
    all_cells = headers.copy()
    for row in data_rows:
        all_cells.extend(row)

    return {
        "table_cells": all_cells,
        "num_rows": 6,  # 1 header + 5 data
        "num_cols": 5,
    }


# ---------------------------------------------------------------------------
# Type A: Standard Single-Page Table
# ---------------------------------------------------------------------------


class TestTypeAStandardTable:
    """Type A: Standard table with no edge cases."""

    def test_type_a_standard_table(self):
        """Five-row standard table produces 5 RawTableRow objects."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=3,
            table_index=0,
        )

        assert len(rows) == 5
        assert rows[0].cells["room_location"] == "Room 101"
        assert rows[0].cells["item_description"] == "Ceiling tiles"
        assert rows[0].page_number == 3
        assert rows[0].source_id == "src_001"
        assert rows[0].building_id == "bld_001"
        assert rows[0].table_index == 0
        assert rows[0].row_index == 0
        assert rows[0].edge_case_type == "A"
        assert rows[0].source_table_num_rows == 6
        assert rows[0].source_table_num_cols == 5

    def test_type_a_row_indices_sequential(self):
        """Row indices are 0-indexed and sequential."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        for i, row in enumerate(rows):
            assert row.row_index == i

    def test_type_a_raw_text(self):
        """Raw text concatenates cell values with pipe separator."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        assert "Room 101" in rows[0].raw_text
        assert "Ceiling tiles" in rows[0].raw_text

    def test_type_a_column_mapping(self):
        """Column mapping maps canonical to original header text."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        mapping = rows[0].column_mapping
        assert "room_location" in mapping
        assert "item_description" in mapping or "friability" in mapping


# ---------------------------------------------------------------------------
# Type B: Multi-Page Table Merge
# ---------------------------------------------------------------------------


class TestTypeBMultiPageMerge:
    """Type B: Tables with same num_cols merged across pages."""

    def test_type_b_multipage_merge(self):
        """Two tables with same cols produce merged row list."""
        table_1 = {
            "table_cells": _standard_headers(3)
            + [
                _make_data_cell("Room 101", 1, 0),
                _make_data_cell("Ceiling tiles", 1, 1),
                _make_data_cell("Good", 1, 2),
                _make_data_cell("Library", 2, 0),
                _make_data_cell("Vinyl floor", 2, 1),
                _make_data_cell("Fair", 2, 2),
            ],
            "num_rows": 3,
            "num_cols": 3,
            "page_number": 1,
        }
        table_2 = {
            "table_cells": _standard_headers(3)
            + [
                _make_data_cell("Staff Room", 1, 0),
                _make_data_cell("Fibro eaves", 1, 1),
                _make_data_cell("Poor", 1, 2),
                _make_data_cell("Hall", 2, 0),
                _make_data_cell("Switchboard", 2, 1),
                _make_data_cell("Good", 2, 2),
            ],
            "num_rows": 3,
            "num_cols": 3,
            "page_number": 2,
        }

        rows = segment_multiple_tables(
            [table_1, table_2],
            building_id="bld_main",
            source_id="src_001",
        )

        assert len(rows) == 4
        assert rows[0].cells["room_location"] == "Room 101"
        assert rows[2].cells["room_location"] == "Staff Room"
        # Row indices should be re-indexed
        assert rows[0].row_index == 0
        assert rows[3].row_index == 3

    def test_type_b_overlap_dedup(self):
        """Overlapping rows at page boundary are deduplicated."""
        headers_3 = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        table_1 = {
            "table_cells": headers_3
            + [
                _make_data_cell("Room 101", 1, 0),
                _make_data_cell("Ceiling tiles", 1, 1),
                _make_data_cell("Good", 1, 2),
                # Last row of page 1
                _make_data_cell("Library", 2, 0),
                _make_data_cell("Vinyl floor", 2, 1),
                _make_data_cell("Fair", 2, 2),
            ],
            "num_rows": 3,
            "num_cols": 3,
            "page_number": 1,
        }
        table_2 = {
            "table_cells": headers_3
            + [
                # Duplicate of last row of page 1
                _make_data_cell("Library", 1, 0),
                _make_data_cell("Vinyl floor", 1, 1),
                _make_data_cell("Fair", 1, 2),
                # New row
                _make_data_cell("Staff Room", 2, 0),
                _make_data_cell("Fibro eaves", 2, 1),
                _make_data_cell("Poor", 2, 2),
            ],
            "num_rows": 3,
            "num_cols": 3,
            "page_number": 2,
        }

        rows = segment_multiple_tables(
            [table_1, table_2],
            building_id="bld_main",
            source_id="src_001",
        )

        # Should have 3 rows (Library overlap deduplicated)
        assert len(rows) == 3
        room_names = [r.cells.get("room_location", "") for r in rows]
        assert room_names == ["Room 101", "Library", "Staff Room"]


# ---------------------------------------------------------------------------
# Type C: Merged Cells — Room Spanning Items
# ---------------------------------------------------------------------------


class TestTypeCMergedCells:
    """Type C: Room cell with row_span > 1 carried forward."""

    def test_type_c_merged_room(self):
        """Room cell spanning 3 rows populates carried_forward_fields."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        cells = headers + [
            # Room 101 spans 3 data rows (rows 1, 2, 3)
            _make_data_cell("Room 101", 1, 0, row_span=3),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("Good", 1, 2),
            # Row 2 — no room cell (spanned)
            _make_data_cell("Vinyl floor tiles", 2, 1),
            _make_data_cell("Fair", 2, 2),
            # Row 3 — no room cell (spanned)
            _make_data_cell("Wall lining", 3, 1),
            _make_data_cell("Poor", 3, 2),
        ]
        table = {"table_cells": cells, "num_rows": 4, "num_cols": 3}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=5,
        )

        assert len(rows) == 3
        # All three rows should have Room 101
        for row in rows:
            assert row.cells["room_location"] == "Room 101"
        # Rows 2 and 3 should show carried forward
        assert rows[0].carried_forward_fields == []
        assert "room_location" in rows[1].carried_forward_fields
        assert "room_location" in rows[2].carried_forward_fields
        assert "C" in (rows[1].edge_case_type or "")
        assert "C" in (rows[2].edge_case_type or "")

    def test_type_c_merged_level_and_room(self):
        """Both level and room columns merged simultaneously."""
        headers = [
            _make_header_cell("Level", 0),
            _make_header_cell("Room", 1),
            _make_header_cell("Material", 2),
        ]
        cells = headers + [
            # Level spans 4 data rows, Room spans 2
            _make_data_cell("Ground Floor", 1, 0, row_span=4),
            _make_data_cell("Room 101", 1, 1, row_span=2),
            _make_data_cell("Ceiling tiles", 1, 2),
            _make_data_cell("Vinyl floor", 2, 2),
            # Room 102 spans next 2 rows
            _make_data_cell("Room 102", 3, 1, row_span=2),
            _make_data_cell("Wall panels", 3, 2),
            _make_data_cell("Door frame", 4, 2),
        ]
        table = {"table_cells": cells, "num_rows": 5, "num_cols": 3}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=2,
        )

        assert len(rows) == 4
        # All rows get Ground Floor from span
        for row in rows:
            assert "Ground Floor" in row.cells.values()
        # Rows 0-1: Room 101, Rows 2-3: Room 102
        assert rows[1].carried_forward_fields  # room_location carried


# ---------------------------------------------------------------------------
# Type E1: Multi-Item Cell
# ---------------------------------------------------------------------------


class TestTypeE1MultiItemCell:
    """Type E1: Cell containing multiple items separated by newlines."""

    def test_type_e1_multiitem_flag(self):
        """Cell with newline + material keywords sets needs_llm_split."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell(
                "Vinyl floor tiles\nCement sheet wall\nFibro ceiling",
                1,
                1,
            ),
        ]
        table = {"table_cells": cells, "num_rows": 2, "num_cols": 2}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        assert len(rows) == 1
        assert rows[0].needs_llm_split is True
        assert "E1" in (rows[0].edge_case_type or "")

    def test_type_e1_no_flag_without_keywords(self):
        """Newline without material keywords does not flag E1."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Notes", 1),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Line one\nLine two", 1, 1),
        ]
        table = {"table_cells": cells, "num_rows": 2, "num_cols": 2}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        assert len(rows) == 1
        assert rows[0].needs_llm_split is False


# ---------------------------------------------------------------------------
# Type E2: Note Row
# ---------------------------------------------------------------------------


class TestTypeE2NoteRow:
    """Type E2: Full-span note row not emitted, attached to next data row."""

    def test_type_e2_note_row(self):
        """Note row stored as extraction_notes on subsequent data row."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("Good", 1, 2),
            # Note row spanning all 3 columns
            _make_data_cell(
                "All items in this section assumed positive",
                2,
                0,
                col_span=3,
            ),
            # Next data row should inherit the note
            _make_data_cell("Library", 3, 0),
            _make_data_cell("Floor tiles", 3, 1),
            _make_data_cell("Fair", 3, 2),
        ]
        table = {"table_cells": cells, "num_rows": 4, "num_cols": 3}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        # Note row should not be emitted
        assert len(rows) == 2
        # Note should be attached to the Library row
        assert rows[1].extraction_notes == "All items in this section assumed positive"
        assert rows[0].extraction_notes is None


# ---------------------------------------------------------------------------
# Type E3: Sub-Header Row
# ---------------------------------------------------------------------------


class TestTypeE3SubHeaderLevel:
    """Type E3: Sub-header row updating current_level for subsequent rows."""

    def test_type_e3_subheader_level(self):
        """Sub-header row sets current_level for rows below it."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        cells = headers + [
            # Sub-header: GROUND FLOOR (spans all cols)
            _make_data_cell("GROUND FLOOR", 1, 0, col_span=3),
            # Data rows under Ground Floor
            _make_data_cell("Room 101", 2, 0),
            _make_data_cell("Ceiling tiles", 2, 1),
            _make_data_cell("Good", 2, 2),
            # Sub-header: FIRST FLOOR
            _make_data_cell("FIRST FLOOR", 3, 0, col_span=3),
            # Data rows under First Floor
            _make_data_cell("Room 201", 4, 0),
            _make_data_cell("Wall panels", 4, 1),
            _make_data_cell("Fair", 4, 2),
        ]
        table = {"table_cells": cells, "num_rows": 5, "num_cols": 3}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        # Sub-headers should not be emitted
        assert len(rows) == 2
        assert rows[0].current_level == "GROUND FLOOR"
        assert rows[0].cells["room_location"] == "Room 101"
        assert rows[1].current_level == "FIRST FLOOR"
        assert rows[1].cells["room_location"] == "Room 201"

    def test_type_e3_initial_level_preserved(self):
        """Initial level passed to segment_docling_table is used."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Ceiling tiles", 1, 1),
        ]
        table = {"table_cells": cells, "num_rows": 2, "num_cols": 2}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
            initial_level="BASEMENT",
        )

        assert len(rows) == 1
        assert rows[0].current_level == "BASEMENT"

    def test_type_e3_various_level_keywords(self):
        """Various level keywords are recognized as sub-headers."""
        keywords = [
            "LEVEL 1",
            "GROUND",
            "FIRST FLOOR",
            "SECOND FLOOR",
            "ROOF SPACE",
            "BASEMENT",
            "EXTERNAL",
            "MEZZANINE LEVEL",
        ]
        for keyword in keywords:
            headers = [_make_header_cell("Room", 0), _make_header_cell("Material", 1)]
            cells = headers + [
                _make_data_cell(keyword, 1, 0, col_span=2),
                _make_data_cell("Room 101", 2, 0),
                _make_data_cell("Tiles", 2, 1),
            ]
            table = {"table_cells": cells, "num_rows": 3, "num_cols": 2}
            rows = segment_docling_table(
                table,
                building_id="bld_001",
                source_id="src_001",
                page_number=1,
            )
            assert len(rows) == 1, f"Failed for keyword: {keyword}"
            assert rows[0].current_level == keyword


# ---------------------------------------------------------------------------
# Type F: Not Sampled / No Access (text scan)
# ---------------------------------------------------------------------------


class TestTypeFSynthetic:
    """Type F: Synthetic rows from Not Sampled / No Access text patterns."""

    def test_type_f_not_sampled(self):
        """'Location - Not Sampled' creates a synthetic row."""
        text = "Boiler Room — Not Sampled\nSwitch Room – Not Sampled"
        rows = scan_text_for_synthetics(
            text,
            building_id="bld_001",
            source_id="src_001",
        )

        assert len(rows) >= 2
        assert all(r.is_synthetic for r in rows)
        assert all(r.edge_case_type == "F" for r in rows)
        room_names = [r.cells.get("room_location", "") for r in rows]
        assert "Boiler Room" in room_names
        assert "Switch Room" in room_names

    def test_type_f_no_access(self):
        """'Location - No Access' creates a synthetic row."""
        text = "Store Room - No Access"
        rows = scan_text_for_synthetics(
            text,
            building_id="bld_001",
            source_id="src_001",
        )

        assert len(rows) >= 1
        assert rows[0].cells["room_location"] == "Store Room"
        assert rows[0].cells["sample_result"] == "No Access"
        assert rows[0].is_synthetic is True
        assert rows[0].confidence < 1.0


# ---------------------------------------------------------------------------
# Type G: Column Aliases (fuzzy matching)
# ---------------------------------------------------------------------------


class TestTypeGColumnAliases:
    """Type G: Fuzzy header matching via Jaro-Winkler."""

    def test_detect_column_mapping(self):
        """Various header texts are mapped to canonical column names."""
        header_cells = [
            {"text": "Room/Area"},
            {"text": "Product Description"},
            {"text": "F/NF"},
            {"text": "Material Condition"},
            {"text": "Sample#"},
            {"text": "Lab Result"},
        ]
        mapping = detect_column_mapping(header_cells)

        assert "room_location" in mapping
        assert "item_description" in mapping
        assert "friability" in mapping
        assert "condition" in mapping
        assert "sample_number" in mapping
        assert "sample_result" in mapping

    def test_detect_column_mapping_exact(self):
        """Exact matches produce correct mapping."""
        header_cells = [
            {"text": "room"},
            {"text": "material"},
            {"text": "condition"},
        ]
        mapping = detect_column_mapping(header_cells)

        assert "room_location" in mapping
        assert mapping["room_location"] == "room"

    def test_detect_column_mapping_unknown_header(self):
        """Unknown headers are preserved as-is."""
        header_cells = [
            {"text": "Room"},
            {"text": "Zzyzx Blorp"},
        ]
        mapping = detect_column_mapping(header_cells)

        assert "room_location" in mapping
        # The unknown header should be kept as its own key
        assert "Zzyzx Blorp" in mapping

    def test_type_g_canonical_names_used_in_cells(self):
        """Table with aliased headers produces cells with canonical keys."""
        headers = [
            _make_header_cell("Room/Area", 0),
            _make_header_cell("Product Description", 1),
            _make_header_cell("Material Condition", 2),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("Good", 1, 2),
        ]
        table = {"table_cells": cells, "num_rows": 2, "num_cols": 3}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        assert len(rows) == 1
        assert "room_location" in rows[0].cells
        assert "item_description" in rows[0].cells
        assert "condition" in rows[0].cells


# ---------------------------------------------------------------------------
# Type H: Split / Fragmented Tables
# ---------------------------------------------------------------------------


class TestTypeHSplitTables:
    """Type H: Tables with different num_cols joined on shared key column."""

    def test_type_h_split_tables(self):
        """Two tables with different cols but shared Room column are joined."""
        table_a = {
            "table_cells": [
                _make_header_cell("Room", 0),
                _make_header_cell("Material", 1),
                _make_header_cell("Condition", 2),
                _make_data_cell("Room 101", 1, 0),
                _make_data_cell("Ceiling tiles", 1, 1),
                _make_data_cell("Good", 1, 2),
                _make_data_cell("Library", 2, 0),
                _make_data_cell("Floor tiles", 2, 1),
                _make_data_cell("Fair", 2, 2),
            ],
            "num_rows": 3,
            "num_cols": 3,
            "page_number": 1,
        }
        table_b = {
            "table_cells": [
                _make_header_cell("Room", 0),
                _make_header_cell("Sample No", 1),
                _make_data_cell("Room 101", 1, 0),
                _make_data_cell("34511-039-001", 1, 1),
                _make_data_cell("Library", 2, 0),
                _make_data_cell("34511-039-002", 2, 1),
            ],
            "num_rows": 3,
            "num_cols": 2,
            "page_number": 1,
        }

        rows = segment_multiple_tables(
            [table_a, table_b],
            building_id="bld_001",
            source_id="src_001",
        )

        assert len(rows) == 2
        # Room 101 should have both material and sample number
        room101 = next(r for r in rows if r.cells.get("room_location") == "Room 101")
        assert "item_description" in room101.cells
        assert "sample_number" in room101.cells
        assert room101.edge_case_type == "H"


# ---------------------------------------------------------------------------
# Edge cases: empty and header-only tables
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary conditions and degenerate inputs."""

    def test_empty_table(self):
        """Empty table produces no rows."""
        table = {"table_cells": [], "num_rows": 0, "num_cols": 0}
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        assert rows == []

    def test_header_only_table(self):
        """Table with only header rows produces no data rows."""
        table = {
            "table_cells": _standard_headers(5),
            "num_rows": 1,
            "num_cols": 5,
        }
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        assert rows == []

    def test_single_table_via_multiple(self):
        """Single table passed to segment_multiple_tables works."""
        table = _standard_5col_table()
        table["page_number"] = 1
        rows = segment_multiple_tables(
            [table],
            building_id="bld_001",
            source_id="src_001",
        )
        assert len(rows) == 5

    def test_empty_text_scan(self):
        """Empty text produces no synthetic rows."""
        rows = scan_text_for_synthetics(
            "",
            building_id="bld_001",
            source_id="src_001",
        )
        assert rows == []


# ---------------------------------------------------------------------------
# HTML debug output
# ---------------------------------------------------------------------------


class TestDebugHtmlGeneration:
    """Debug HTML output for visual inspection."""

    def test_debug_html_generation(self):
        """Each row has debug_html with <tr> and <td> elements."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        for row in rows:
            assert row.debug_html is not None
            assert row.debug_html.startswith("<tr")
            assert "<td>" in row.debug_html
            assert "</tr>" in row.debug_html

    def test_debug_html_flags(self):
        """Rows with edge cases include data-flags attribute."""
        # Create a row with merged cell to get data-flags
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
        ]
        cells = headers + [
            _make_data_cell("Room 101", 1, 0, row_span=2),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("Floor tiles", 2, 1),
        ]
        table = {"table_cells": cells, "num_rows": 3, "num_cols": 2}

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )

        assert len(rows) == 2
        # Second row should have data-flags with merged info
        assert 'data-flags="' in rows[1].debug_html
        assert "merged:" in rows[1].debug_html

    def test_generate_debug_table(self):
        """Full debug table includes caption, thead, and tbody."""
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
        )
        html_output = generate_debug_table(rows, "Main Block")

        assert "<table>" in html_output
        assert "<caption>Main Block</caption>" in html_output
        assert "<thead>" in html_output
        assert "<tbody>" in html_output
        assert html_output.count("<tr") >= 6  # 1 header + 5 data rows

    def test_generate_debug_table_empty(self):
        """Empty row list produces table with 'no rows' caption."""
        html_output = generate_debug_table([], "Main Block")
        assert "no rows" in html_output

    def test_generate_row_html_synthetic(self):
        """Synthetic rows have 'synthetic' in data-flags."""
        row = RawTableRow(
            source_id="src_001",
            building_id="bld_001",
            table_index=0,
            row_index=0,
            page_number=0,
            cells={"room_location": "Boiler Room"},
            raw_text="Boiler Room — Not Sampled",
            is_synthetic=True,
            edge_case_type="F",
        )
        row_html = generate_row_html(row)
        assert "synthetic" in row_html
        assert "type:F" in row_html

    def test_generate_row_html_needs_split(self):
        """Row with needs_llm_split has 'needs_split' in data-flags."""
        row = RawTableRow(
            source_id="src_001",
            building_id="bld_001",
            table_index=0,
            row_index=0,
            page_number=1,
            cells={"item_description": "Tiles\nSheets"},
            raw_text="Tiles | Sheets",
            needs_llm_split=True,
            edge_case_type="E1",
        )
        row_html = generate_row_html(row)
        assert "needs_split" in row_html


# ---------------------------------------------------------------------------
# Type D: Hierarchical text (scan_text_for_synthetics)
# ---------------------------------------------------------------------------


class TestTypeDHierarchicalText:
    """Type D: Hierarchical text parsed into synthetic rows."""

    def test_type_d_hierarchical_items(self):
        """Indented items under rooms are parsed as synthetic rows."""
        text = (
            "  Ground Floor:\n"
            "    Room 101:\n"
            "      - Ceiling tiles with asbestos\n"
            "      - Vinyl floor covering\n"
            "    Room 102:\n"
            "      - Wall panel lining\n"
        )
        rows = scan_text_for_synthetics(
            text,
            building_id="bld_001",
            source_id="src_001",
        )

        # Should find items under rooms
        assert len(rows) >= 2
        assert all(r.is_synthetic for r in rows)
        assert all(r.edge_case_type == "D" for r in rows)


# ---------------------------------------------------------------------------
# F9: Column alias coverage for Greencap ARA and NSW DoE SAMP
# ---------------------------------------------------------------------------


def test_greencap_column_aliases_mapped():
    """F9: Greencap ARA column headers should map to canonical names."""
    all_aliases = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            all_aliases[alias.lower()] = canonical

    assert "item no" in all_aliases or "item no." in all_aliases
    assert "building element" in all_aliases
    assert "risk rating" in all_aliases
    assert "acm status" in all_aliases
    assert "material type" in all_aliases
    assert "priority" in all_aliases


def test_nsw_doe_column_aliases_mapped():
    """F9: NSW DoE SAMP column headers should map to canonical names."""
    all_aliases = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            all_aliases[alias.lower()] = canonical

    assert "location description" in all_aliases
    assert "assumed/confirmed" in all_aliases
