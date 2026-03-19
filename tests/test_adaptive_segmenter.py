"""Tests for adaptive segmenter features: extra_mappings, custom level_regex,
RecoveryConfig defaults, and backward compatibility.

Multi-Consultant Story 4 — verifies the new parameters added to
detect_column_mapping, segment_docling_table, and segment_multiple_tables.
"""

import re

import pytest

from open_notebook.extractors.recovery_config import RecoveryConfig
from open_notebook.extractors.row_segmenter import (
    detect_column_mapping,
    segment_docling_table,
    segment_multiple_tables,
)

# ---------------------------------------------------------------------------
# Fixture helpers (same pattern as test_row_segmenter.py)
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
    """Create standard ACM register header row with up to 5 columns."""
    headers = ["Room", "Material", "Friable", "Condition", "Sample No"]
    return [_make_header_cell(h, i) for i, h in enumerate(headers[:num_cols])]


def _standard_5col_table() -> dict:
    """Create a standard 5-column, 5-row ACM table."""
    headers = _standard_headers(5)
    data_rows = [
        [
            _make_data_cell("Room 101", 1, 0),
            _make_data_cell("Ceiling tiles", 1, 1),
            _make_data_cell("No", 1, 2),
            _make_data_cell("Good", 1, 3),
            _make_data_cell("34511-039-001", 1, 4),
        ],
        [
            _make_data_cell("Library", 2, 0),
            _make_data_cell("Vinyl floor tiles", 2, 1),
            _make_data_cell("No", 2, 2),
            _make_data_cell("Fair", 2, 3),
            _make_data_cell("34511-039-002", 2, 4),
        ],
        [
            _make_data_cell("Staff Room", 3, 0),
            _make_data_cell("Fibro eave lining", 3, 1),
            _make_data_cell("Yes", 3, 2),
            _make_data_cell("Poor", 3, 3),
            _make_data_cell("34511-039-003", 3, 4),
        ],
        [
            _make_data_cell("Hall", 4, 0),
            _make_data_cell("Switchboard backing", 4, 1),
            _make_data_cell("No", 4, 2),
            _make_data_cell("Good", 4, 3),
            _make_data_cell("34511-039-004", 4, 4),
        ],
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
        "num_rows": 6,
        "num_cols": 5,
    }


# ---------------------------------------------------------------------------
# TestExtraMappings
# ---------------------------------------------------------------------------


class TestExtraMappings:
    """Tests for the extra_mappings parameter on detect_column_mapping."""

    def test_extra_mappings_priority_over_fuzzy(self):
        """Explicit extra_mappings override fuzzy COLUMN_ALIASES matching.

        'Building Element' is a Greencap alias for item_description in
        COLUMN_ALIASES. When extra_mappings maps it to specific_location,
        the explicit mapping should win.
        """
        header_cells = [
            {"text": "Building Element"},
            {"text": "Condition"},
        ]
        mapping = detect_column_mapping(
            header_cells,
            extra_mappings={"Building Element": "specific_location"},
        )

        # The explicit mapping should place "Building Element" under specific_location
        assert "specific_location" in mapping
        assert mapping["specific_location"] == "Building Element"
        # It should NOT be mapped to item_description (the fuzzy match)
        assert mapping.get("item_description") != "Building Element"

    def test_extra_mappings_combined_with_fuzzy(self):
        """Extra mappings and fuzzy matching coexist for different headers.

        'Aktivitet' has no fuzzy match -- extra_mappings provides the mapping.
        'Room' and 'Condition' should still match via fuzzy COLUMN_ALIASES.
        """
        header_cells = [
            {"text": "Aktivitet"},
            {"text": "Room"},
            {"text": "Condition"},
        ]
        mapping = detect_column_mapping(
            header_cells,
            extra_mappings={"Aktivitet": "item_description"},
        )

        # Explicit mapping
        assert "item_description" in mapping
        assert mapping["item_description"] == "Aktivitet"
        # Fuzzy matches
        assert "room_location" in mapping
        assert mapping["room_location"] == "Room"
        assert "condition" in mapping
        assert mapping["condition"] == "Condition"

    def test_extra_mappings_none_is_backward_compatible(self):
        """Passing extra_mappings=None produces same result as omitting it."""
        header_cells = [
            {"text": "Room"},
            {"text": "Material"},
            {"text": "Condition"},
        ]
        mapping_without = detect_column_mapping(header_cells)
        mapping_with_none = detect_column_mapping(header_cells, extra_mappings=None)

        assert mapping_without == mapping_with_none

    def test_extra_mappings_empty_dict(self):
        """Passing extra_mappings={} behaves identically to None."""
        header_cells = [
            {"text": "Room"},
            {"text": "Material"},
            {"text": "Condition"},
        ]
        mapping_none = detect_column_mapping(header_cells, extra_mappings=None)
        mapping_empty = detect_column_mapping(header_cells, extra_mappings={})

        assert mapping_none == mapping_empty


# ---------------------------------------------------------------------------
# TestCustomLevelRegex
# ---------------------------------------------------------------------------


class TestCustomLevelRegex:
    """Tests for the level_regex parameter on segment_docling_table."""

    def test_custom_level_regex_matches(self):
        """Custom level_regex detects non-English sub-headers like 'Etage 1'.

        The default _LEVEL_REGEX would NOT match 'Etage 1' (French floor name).
        A custom regex should treat it as a sub-header and set current_level.
        """
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        cells = headers + [
            # Sub-header: "Etage 1" spanning all columns
            _make_data_cell("Etage 1", 1, 0, col_span=3),
            # Data row under Etage 1
            _make_data_cell("Salle 101", 2, 0),
            _make_data_cell("Dalles de plafond", 2, 1),
            _make_data_cell("Bon", 2, 2),
        ]
        table = {"table_cells": cells, "num_rows": 3, "num_cols": 3}

        custom_re = re.compile(
            r"^(Etage|Rez-de-chauss[ée]e)\b", re.IGNORECASE
        )

        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=1,
            level_regex=custom_re,
        )

        # "Etage 1" should be consumed as a sub-header, not emitted as data
        assert len(rows) == 1
        assert rows[0].current_level == "Etage 1"
        assert rows[0].cells["room_location"] == "Salle 101"

    def test_default_level_regex_when_none(self):
        """Passing level_regex=None uses the default _LEVEL_REGEX.

        Same behavior as existing test_type_e3_subheader_level.
        """
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
            _make_header_cell("Condition", 2),
        ]
        cells = headers + [
            _make_data_cell("GROUND FLOOR", 1, 0, col_span=3),
            _make_data_cell("Room 101", 2, 0),
            _make_data_cell("Ceiling tiles", 2, 1),
            _make_data_cell("Good", 2, 2),
            _make_data_cell("FIRST FLOOR", 3, 0, col_span=3),
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
            level_regex=None,
        )

        assert len(rows) == 2
        assert rows[0].current_level == "GROUND FLOOR"
        assert rows[1].current_level == "FIRST FLOOR"

    def test_custom_level_regex_in_multiple_tables(self):
        """level_regex propagates through segment_multiple_tables."""
        headers = [
            _make_header_cell("Room", 0),
            _make_header_cell("Material", 1),
        ]

        table_1 = {
            "table_cells": headers
            + [
                _make_data_cell("Etage 1", 1, 0, col_span=2),
                _make_data_cell("Salle 101", 2, 0),
                _make_data_cell("Dalles", 2, 1),
            ],
            "num_rows": 3,
            "num_cols": 2,
            "page_number": 1,
        }
        table_2 = {
            "table_cells": headers
            + [
                _make_data_cell("Etage 2", 1, 0, col_span=2),
                _make_data_cell("Salle 201", 2, 0),
                _make_data_cell("Mur", 2, 1),
            ],
            "num_rows": 3,
            "num_cols": 2,
            "page_number": 2,
        }

        custom_re = re.compile(r"^Etage\b", re.IGNORECASE)

        rows = segment_multiple_tables(
            [table_1, table_2],
            building_id="bld_001",
            source_id="src_001",
            level_regex=custom_re,
        )

        assert len(rows) == 2
        assert rows[0].current_level == "Etage 1"
        assert rows[0].cells["room_location"] == "Salle 101"
        assert rows[1].current_level == "Etage 2"
        assert rows[1].cells["room_location"] == "Salle 201"


# ---------------------------------------------------------------------------
# TestRecoveryConfigIntegration
# ---------------------------------------------------------------------------


class TestRecoveryConfigIntegration:
    """Tests for RecoveryConfig default values."""

    def test_recovery_config_default_matches_hardcoded(self):
        """RecoveryConfig defaults include the expected not-sampled terms.

        These should match the hardcoded patterns used in the recovery
        functions of acm_extraction.py.
        """
        config = RecoveryConfig()

        # Verify not_sampled_terms include standard vocabulary
        assert "Not Sampled" in config.not_sampled_terms
        assert "No Access" in config.not_sampled_terms
        assert "Not Accessible" in config.not_sampled_terms
        assert "Access Denied" in config.not_sampled_terms

        # Verify confirmation_terms
        assert "Presumed Positive" in config.confirmation_terms
        assert "Assumed Positive" in config.confirmation_terms
        assert "Assumed" in config.confirmation_terms

        # Verify restriction_terms
        assert "Restricted Access" in config.restriction_terms
        assert "Inaccessible" in config.restriction_terms

        # Verify scan window defaults
        assert config.lookback_lines == 5
        assert config.lookahead_lines == 3

        # Optional overrides default to None
        assert config.section_header_re is None
        assert config.level_re is None
        assert config.product_keywords is None
        assert config.content_boundary_re is None


# ---------------------------------------------------------------------------
# TestBackwardCompatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Verify existing behavior is preserved when new params are not supplied."""

    def test_all_existing_patterns_still_work(self):
        """segment_docling_table with NO new params matches existing behavior.

        Standard 5-column table should produce 5 rows with correct canonical
        column names, matching what the original tests expect.
        """
        table = _standard_5col_table()
        rows = segment_docling_table(
            table,
            building_id="bld_001",
            source_id="src_001",
            page_number=3,
            table_index=0,
        )

        # Same assertions as TestTypeAStandardTable
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

        # Verify sequential row indices
        for i, row in enumerate(rows):
            assert row.row_index == i

        # Verify column mapping present
        mapping = rows[0].column_mapping
        assert "room_location" in mapping
        assert "item_description" in mapping
