"""Tests for ACMItemRow -> ACMExtractionRecord deterministic mapping.

Uses realistic Australian ACM register data for test fixtures.
"""

import pytest

from open_notebook.domain.acm_row_mappers import (
    is_friable_bool,
    map_item_row_to_extraction_record,
    normalize_friability,
)
from open_notebook.domain.acm_row_schemas import ACMItemRow

# ---------------------------------------------------------------------------
# normalize_friability
# ---------------------------------------------------------------------------


class TestNormalizeFriability:
    """Test friability normalization for all known input variants."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("F", "Friable"),
            ("f", "Friable"),
            ("Friable", "Friable"),
            ("friable", "Friable"),
            ("Yes", "Friable"),
            ("yes", "Friable"),
            ("NF", "Non-friable"),
            ("nf", "Non-friable"),
            ("Non-friable", "Non-friable"),
            ("non-friable", "Non-friable"),
            ("Non-Friable", "Non-friable"),
            ("Non Friable", "Non-friable"),
            ("non friable", "Non-friable"),
            ("No", "Non-friable"),
            ("no", "Non-friable"),
            (None, None),
            ("", None),
            ("  ", None),
        ],
    )
    def test_normalize_friability_variants(self, raw: str, expected: str) -> None:
        assert normalize_friability(raw) == expected


# ---------------------------------------------------------------------------
# is_friable_bool
# ---------------------------------------------------------------------------


class TestIsFriableBool:
    """Test boolean conversion of friability strings."""

    def test_friable_returns_true(self) -> None:
        assert is_friable_bool("Friable") is True

    def test_non_friable_returns_false(self) -> None:
        assert is_friable_bool("Non-friable") is False

    def test_none_returns_false(self) -> None:
        assert is_friable_bool(None) is False


# ---------------------------------------------------------------------------
# map_item_row_to_extraction_record — standard items
# ---------------------------------------------------------------------------


class TestMapStandardItem:
    """Test mapping a typical non-friable ACM item (vinyl floor tiles)."""

    def test_map_standard_item(self) -> None:
        row = ACMItemRow(
            room_name="Room 101",
            floor_level="Ground Floor",
            item_location="Floor",
            item_name="Vinyl floor tiles",
            friability="NF",
            acm_classification=None,
            acm_sub_classification=None,
            condition="Good",
            disturbance_potential="Low",
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="building:abc123",
            source_id="source:xyz789",
            page_number=3,
        )

        # Location fields mapped correctly
        assert record.room_name == "Room 101"
        assert record.floor_level == "Ground Floor"
        assert record.location == "Floor"

        # Product
        assert record.product == "Vinyl floor tiles"

        # Friability normalized
        assert record.friable == "Non-friable"

        # Condition: "Good" -> "Stable" via normalize_enum_value
        assert record.material_condition == "Stable"

        # Disturbance: "Low" -> "Low"
        assert record.disturbance_potential == "Low"

        # Building FK
        assert record.building_id == "building:abc123"
        assert record.building_record_id == "building:abc123"

        # Page number
        assert record.page_number == 3

        # Default result for per-row extraction
        assert record.result == "Unknown"


class TestMapFriableItem:
    """Test mapping a friable insulation item."""

    def test_map_friable_item(self) -> None:
        row = ACMItemRow(
            room_name="Boiler Room",
            floor_level="Basement",
            item_location="Pipes",
            item_name="Pipe insulation lagging",
            friability="Friable",
            acm_classification=None,
            acm_sub_classification=None,
            condition="Poor",
            disturbance_potential="High",
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="building:boiler1",
            source_id="source:doc456",
        )

        assert record.friable == "Friable"
        assert record.product == "Pipe insulation lagging"
        # classify_product should match "lagging|pipe insulation" pattern
        # which maps to Friable T3 "Insulation products" / "Lagging"
        assert record.material_description is not None  # sub-classification populated
        assert record.material_condition == "Poor"
        assert record.disturbance_potential == "High"


# ---------------------------------------------------------------------------
# Missing optional fields
# ---------------------------------------------------------------------------


class TestMapMissingOptionalFields:
    """Test that records are created even when only item_name is provided."""

    def test_map_missing_optional_fields(self) -> None:
        row = ACMItemRow(item_name="Cement sheet cladding")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="building:min1",
            source_id="source:min1",
        )

        # Required fields present
        assert record.product == "Cement sheet cladding"
        assert record.building_id == "building:min1"
        assert record.result == "Unknown"

        # Optional fields are None
        assert record.room_name is None
        assert record.floor_level is None
        assert record.location is None
        assert record.friable is None
        assert record.material_condition is None
        assert record.disturbance_potential is None


# ---------------------------------------------------------------------------
# classify_product integration
# ---------------------------------------------------------------------------


class TestClassifyProductIntegration:
    """Test that classify_product results flow through to the record."""

    def test_vinyl_tiles_classified(self) -> None:
        """Vinyl floor tiles should match the taxonomy pattern."""
        row = ACMItemRow(
            item_name="Vinyl floor tiles",
            friability="Non-friable",
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:1",
            source_id="src:1",
        )

        # classify_product returns "Vinyl products" (T3 stripped) for "vinyl.*tile"
        # with confidence 0.9, so deterministic result should be used
        assert record.material_description == "Vinyl Tiles"

    def test_cement_sheet_classified(self) -> None:
        """Cement sheet should classify as Cement products / Flat Sheeting."""
        row = ACMItemRow(
            item_name="Fibre cement flat sheet",
            friability="NF",
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:2",
            source_id="src:2",
        )
        # Pattern matches "flat sheet" -> Cement products / Flat Sheeting
        assert record.material_description is not None


class TestClassifyProductLowConfidenceUsesLlmHint:
    """When classify_product returns low confidence, use LLM hints."""

    def test_unknown_material_uses_llm_classification(self) -> None:
        """For an unrecognized material, LLM classification hint is used."""
        row = ACMItemRow(
            item_name="Exotic composite panel type X",
            friability="Non-friable",
            acm_classification="Chrysotile bonded",
            acm_sub_classification="Composite panel",
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:3",
            source_id="src:3",
        )

        # classify_product returns confidence 0.0 for unrecognized material,
        # so LLM hints should be used as fallback
        # Classification: deterministic confidence < 0.7 -> use LLM hint
        # No assertion on exact value since classify_product may or may not
        # match -- but data_issues should note the taxonomy miss
        assert any("No taxonomy match" in issue for issue in record.data_issues)
        # Sub-classification: deterministic confidence < 0.5 -> use LLM hint
        assert record.material_description == "Composite panel"


# ---------------------------------------------------------------------------
# Condition normalization
# ---------------------------------------------------------------------------


class TestConditionNormalization:
    """Test condition field normalization via normalize_enum_value."""

    @pytest.mark.parametrize(
        "raw_condition,expected",
        [
            ("Good", "Stable"),  # "Good" -> "Stable" per CONDITION_SYNONYMS
            ("good", "Stable"),
            ("Stable", "Stable"),
            ("Fair", "Fair"),
            ("fair", "Fair"),
            ("Poor", "Poor"),
            ("poor", "Poor"),
            ("Unknown", "Unknown"),
        ],
    )
    def test_condition_normalization(self, raw_condition: str, expected: str) -> None:
        row = ACMItemRow(
            item_name="Vinyl tiles",
            condition=raw_condition,
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:cond",
            source_id="src:cond",
        )
        assert record.material_condition == expected


# ---------------------------------------------------------------------------
# Disturbance potential normalization
# ---------------------------------------------------------------------------


class TestDisturbanceNormalization:
    """Test disturbance potential normalization via normalize_enum_value."""

    @pytest.mark.parametrize(
        "raw_dp,expected",
        [
            ("Low", "Low"),
            ("low", "Low"),
            ("Medium", "Moderate"),  # SF uses "Moderate" not "Medium"
            ("medium", "Moderate"),
            ("High", "High"),
            ("high", "High"),
            ("Moderate", "Moderate"),
        ],
    )
    def test_disturbance_normalization(self, raw_dp: str, expected: str) -> None:
        row = ACMItemRow(
            item_name="Cement pipe",
            disturbance_potential=raw_dp,
        )
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:dp",
            source_id="src:dp",
        )
        assert record.disturbance_potential == expected


# ---------------------------------------------------------------------------
# FK fields and metadata
# ---------------------------------------------------------------------------


class TestBuildingIdAndSourceIdSet:
    """Verify building_id and building_record_id are set from parameters."""

    def test_building_id_and_source_id_set(self) -> None:
        row = ACMItemRow(item_name="Corrugated roof sheeting")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="building_record:abc",
            source_id="source:xyz",
        )
        assert record.building_id == "building_record:abc"
        assert record.building_record_id == "building_record:abc"


class TestExtractionConfidenceSet:
    """Verify extraction confidence defaults to 'medium' for per-row extraction."""

    def test_extraction_confidence_set(self) -> None:
        row = ACMItemRow(item_name="Weatherboard cladding")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:conf",
            source_id="src:conf",
        )
        assert record.extraction_confidence == "medium"


class TestRowIndexInDataIssues:
    """Verify row_index is tracked in data_issues when provided."""

    def test_row_index_tracked(self) -> None:
        row = ACMItemRow(item_name="Vinyl sheet")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:ri",
            source_id="src:ri",
            row_index=7,
        )
        assert any("row_index: 7" in issue for issue in record.data_issues)


class TestPageNumberSet:
    """Verify page_number is populated when provided."""

    def test_page_number_set(self) -> None:
        row = ACMItemRow(item_name="Ceiling tiles")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:pg",
            source_id="src:pg",
            page_number=12,
        )
        assert record.page_number == 12

    def test_page_number_none_by_default(self) -> None:
        row = ACMItemRow(item_name="Ceiling tiles")
        record = map_item_row_to_extraction_record(
            row=row,
            building_id="bld:pg2",
            source_id="src:pg2",
        )
        assert record.page_number is None
