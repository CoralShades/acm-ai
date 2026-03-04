"""
Unit tests for SF export field mapping and External ID generation.

Story: E33-S8 Salesforce-Ready Export UI

Tests cover:
  - SF API header lists for Building__c and Item__c
  - External_ID__c generation (priority order + fallback)
  - building_to_sf_row: field mapping with and without site config
  - item_to_sf_row: field mapping with building_external_id linkage
  - _format_value: edge cases (None, bool, list, plain value)
"""

import pytest

from open_notebook.extractors.exporters.sf_export import (
    BUILDING_SF_MAPPING,
    ITEM_SF_MAPPING,
    _format_value,
    building_to_sf_row,
    generate_external_id,
    get_building_sf_headers,
    get_item_sf_headers,
    item_to_sf_row,
)

# ---------------------------------------------------------------------------
# Simple mock objects (avoid Pydantic / DB overhead in pure unit tests)
# ---------------------------------------------------------------------------


class _MockBuilding:
    """Minimal stand-in for BuildingRecord."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _MockACMRecord:
    """Minimal stand-in for ACMRecord."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _MockSiteConfig:
    """Minimal stand-in for SiteConfig."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# ---------------------------------------------------------------------------
# Header list tests
# ---------------------------------------------------------------------------


class TestHeaderLists:
    """get_building_sf_headers() and get_item_sf_headers() must return ordered lists."""

    def test_building_headers_non_empty(self):
        headers = get_building_sf_headers()
        assert len(headers) > 0

    def test_item_headers_non_empty(self):
        headers = get_item_sf_headers()
        assert len(headers) > 0

    def test_building_headers_match_mapping(self):
        """Headers must be exactly the SF API names from BUILDING_SF_MAPPING."""
        expected = [sf for sf, _ in BUILDING_SF_MAPPING]
        assert get_building_sf_headers() == expected

    def test_item_headers_match_mapping(self):
        """Headers must be exactly the SF API names from ITEM_SF_MAPPING."""
        expected = [sf for sf, _ in ITEM_SF_MAPPING]
        assert get_item_sf_headers() == expected

    def test_building_headers_include_external_id(self):
        assert "External_ID__c" in get_building_sf_headers()

    def test_item_headers_include_building_fk(self):
        assert "Building__r.External_ID__c" in get_item_sf_headers()

    def test_building_headers_are_strings(self):
        for h in get_building_sf_headers():
            assert isinstance(h, str)

    def test_item_headers_are_strings(self):
        for h in get_item_sf_headers():
            assert isinstance(h, str)


# ---------------------------------------------------------------------------
# generate_external_id tests
# ---------------------------------------------------------------------------


class TestGenerateExternalId:
    """generate_external_id() must resolve External_ID__c correctly."""

    def test_uses_external_id_when_set(self):
        b = _MockBuilding(
            external_id="EXT-001",
            building_unique_id=None,
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:abc123")
        assert result == "EXT-001"

    def test_uses_building_unique_id_as_fallback(self):
        b = _MockBuilding(
            external_id=None,
            building_unique_id="UID-999",
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:abc123")
        assert result == "UID-999"

    def test_generates_fallback_from_source_and_code(self):
        b = _MockBuilding(
            external_id=None,
            building_unique_id=None,
            building_code="B02",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:MYSOURCE")
        # source_short = "MYSOURCE" (first 8 chars after the colon)
        assert result == "MYSOURCE_B02"

    def test_fallback_truncates_source_to_8_chars(self):
        b = _MockBuilding(
            external_id=None,
            building_unique_id=None,
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:AVERYLONGSOURCEID")
        # source_short = first 8 chars of "AVERYLON..."
        assert result.startswith("AVERYLONG_") or result.startswith("AVERYLON_")

    def test_prefers_external_id_over_building_unique_id(self):
        """external_id takes highest priority."""
        b = _MockBuilding(
            external_id="FIRST",
            building_unique_id="SECOND",
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:x")
        assert result == "FIRST"

    def test_fallback_uses_internal_id_when_no_building_code(self):
        b = _MockBuilding(
            external_id=None,
            building_unique_id=None,
            building_code=None,
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:SRC123")
        assert "BLD#SRC_001" in result

    def test_result_is_always_a_string(self):
        b = _MockBuilding(
            external_id=None,
            building_unique_id=None,
            building_code="X1",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:test")
        assert isinstance(result, str)

    def test_empty_external_id_treated_as_missing(self):
        """Empty string external_id should fall through to next option."""
        b = _MockBuilding(
            external_id="",
            building_unique_id="UID-FALLBACK",
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        result = generate_external_id(b, "source:test")
        assert result == "UID-FALLBACK"


# ---------------------------------------------------------------------------
# building_to_sf_row tests
# ---------------------------------------------------------------------------


class TestBuildingToSfRow:
    """building_to_sf_row() must produce a dict with correct SF key names."""

    def _make_building(self, **overrides):
        defaults = dict(
            external_id=None,
            building_unique_id=None,
            building_code="B01",
            building_name="Main Block",
            building_type="School",
            building_category=None,
            building_address="1 Main Street",
            suburb="Melbourne",
            postcode="3000",
            building_year="1975",
            building_construction="Brick",
            number_of_levels=2,
            est_building_size_m2=500.0,
            frequency_of_use="Every day",
            daily_duration="8 hours (typical working day)",
            level_of_activity="Moderate",
            public_access="Yes",
            mobile_plant=None,
            owned_or_leased="Owned",
            roof_type="Metal",
            asbestos_register_available="Yes",
            audit_report_available="Yes",
            date_of_audit_report="2022-01-15",
            site_name="Parkside Campus",
            building_unique_id_field=None,
            additional_comments=None,
            internal_id="BLD#TEST_001",
        )
        defaults.update(overrides)
        return _MockBuilding(**defaults)

    def test_returns_dict(self):
        b = self._make_building()
        row = building_to_sf_row(b, "source:test")
        assert isinstance(row, dict)

    def test_all_sf_headers_present(self):
        b = self._make_building()
        row = building_to_sf_row(b, "source:test")
        for sf_name in get_building_sf_headers():
            assert sf_name in row, f"Missing SF key: {sf_name}"

    def test_external_id_generated_when_missing(self):
        b = self._make_building(
            external_id=None, building_unique_id=None, building_code="B01"
        )
        row = building_to_sf_row(b, "source:TESTSRC")
        assert row["External_ID__c"] != ""

    def test_external_id_used_when_present(self):
        b = self._make_building(external_id="MANUAL-EXT-001")
        row = building_to_sf_row(b, "source:test")
        assert row["External_ID__c"] == "MANUAL-EXT-001"

    def test_building_name_mapped(self):
        b = self._make_building(building_name="Admin Block")
        row = building_to_sf_row(b, "source:test")
        assert row["Building_Name__c"] == "Admin Block"

    def test_none_field_becomes_empty_string(self):
        b = self._make_building(building_category=None)
        row = building_to_sf_row(b, "source:test")
        assert row["Building_Category__c"] == ""

    def test_without_site_config(self):
        b = self._make_building()
        row = building_to_sf_row(b, "source:test", site_config=None)
        # Should NOT have Department__c or Agency__c unless site_config was provided
        assert "Department__c" not in row or row.get("Department__c") == ""

    def test_site_config_department_merged(self):
        b = self._make_building()
        sc = _MockSiteConfig(department="DET", agency=None, site_name=None)
        row = building_to_sf_row(b, "source:test", site_config=sc)
        assert row["Department__c"] == "DET"

    def test_site_config_agency_merged(self):
        b = self._make_building()
        sc = _MockSiteConfig(department=None, agency="Victoria Police", site_name=None)
        row = building_to_sf_row(b, "source:test", site_config=sc)
        assert row["Agency__c"] == "Victoria Police"

    def test_site_config_site_name_overrides(self):
        b = self._make_building(site_name="Original")
        sc = _MockSiteConfig(department=None, agency=None, site_name="Override Name")
        row = building_to_sf_row(b, "source:test", site_config=sc)
        assert row["Site_Name__c"] == "Override Name"

    def test_site_config_none_fields_not_added(self):
        """None values in site_config should not overwrite existing row values."""
        b = self._make_building(site_name="FromBuilding")
        sc = _MockSiteConfig(department=None, agency=None, site_name=None)
        row = building_to_sf_row(b, "source:test", site_config=sc)
        # site_name should remain from the building
        assert row["Site_Name__c"] == "FromBuilding"

    def test_all_values_are_strings(self):
        b = self._make_building()
        row = building_to_sf_row(b, "source:test")
        for key, val in row.items():
            assert isinstance(val, str), f"Value for {key!r} is not a string: {val!r}"


# ---------------------------------------------------------------------------
# item_to_sf_row tests
# ---------------------------------------------------------------------------


class TestItemToSfRow:
    """item_to_sf_row() must produce a dict with correct SF key names."""

    def _make_record(self, **overrides):
        defaults = dict(
            building_id="B01",
            room_id="R01",
            room_name="Classroom 1",
            floor_level="Ground",
            area_type="Internal",
            product="Vinyl Floor Tiles",
            material_description="Grey mottled vinyl tiles with adhesive",
            extent="20 m²",
            location="Floor",
            friable="Non-friable",
            material_condition="Stable",
            risk_status="Low",
            result="Positive",
            sample_no="S001",
            sample_result="Positive",
            quantity="20",
            acm_labelled=True,
            disturbance_potential="Low",
            identifying_company="SafeAir Pty Ltd",
            hygienist_recommendations="Monitor annually",
            acm_product_group="Vinyl products",
            acm_product_type="Vinyl tiles",
        )
        defaults.update(overrides)
        return _MockACMRecord(**defaults)

    def test_returns_dict(self):
        record = self._make_record()
        row = item_to_sf_row(record, "BLDEXT001")
        assert isinstance(row, dict)

    def test_all_sf_headers_present(self):
        record = self._make_record()
        row = item_to_sf_row(record, "BLDEXT001")
        for sf_name in get_item_sf_headers():
            assert sf_name in row, f"Missing SF key: {sf_name}"

    def test_building_fk_set_correctly(self):
        record = self._make_record()
        row = item_to_sf_row(record, "EXT-BLD-001")
        assert row["Building__r.External_ID__c"] == "EXT-BLD-001"

    def test_product_mapped_to_acm_name(self):
        record = self._make_record(product="Ceiling Tiles")
        row = item_to_sf_row(record, "EXT001")
        assert row["ACM_Name__c"] == "Ceiling Tiles"

    def test_material_description_mapped(self):
        record = self._make_record(material_description="White asbestos ceiling tiles")
        row = item_to_sf_row(record, "EXT001")
        assert row["ACM_Description__c"] == "White asbestos ceiling tiles"

    def test_bool_acm_labelled_formatted(self):
        """Bool True should become 'true' (SF-compatible lowercase)."""
        record = self._make_record(acm_labelled=True)
        row = item_to_sf_row(record, "EXT001")
        assert row["ACM_Labelled__c"] == "true"

    def test_bool_false_acm_labelled_formatted(self):
        record = self._make_record(acm_labelled=False)
        row = item_to_sf_row(record, "EXT001")
        assert row["ACM_Labelled__c"] == "false"

    def test_none_field_becomes_empty_string(self):
        record = self._make_record(sample_no=None)
        row = item_to_sf_row(record, "EXT001")
        assert row["Sample_No__c"] == ""

    def test_all_values_are_strings(self):
        record = self._make_record()
        row = item_to_sf_row(record, "EXT001")
        for key, val in row.items():
            assert isinstance(val, str), f"Value for {key!r} is not a string: {val!r}"

    def test_external_id_linkage_consistency(self):
        """
        AC4: Item__c.Building__r.External_ID__c must match the External_ID__c
        used in the parent Building__c row.
        """
        building = _MockBuilding(
            external_id="CONSISTENT-EXT-001",
            building_unique_id=None,
            building_code="B01",
            internal_id="BLD#SRC_001",
        )
        record = self._make_record(building_id="B01")

        from open_notebook.extractors.exporters.sf_export import (
            building_to_sf_row,
            generate_external_id,
        )

        b_ext_id = generate_external_id(building, "source:test")
        b_row = building_to_sf_row(building, "source:test")
        i_row = item_to_sf_row(record, b_ext_id)

        assert b_row["External_ID__c"] == i_row["Building__r.External_ID__c"]


# ---------------------------------------------------------------------------
# _format_value tests
# ---------------------------------------------------------------------------


class TestFormatValue:
    """_format_value() must serialize Python values to strings."""

    def test_none_returns_empty_string(self):
        assert _format_value(None) == ""

    def test_bool_true_returns_lowercase_true(self):
        assert _format_value(True) == "true"

    def test_bool_false_returns_lowercase_false(self):
        assert _format_value(False) == "false"

    def test_string_returned_unchanged(self):
        assert _format_value("hello") == "hello"

    def test_integer_returned_as_string(self):
        assert _format_value(42) == "42"

    def test_float_returned_as_string(self):
        assert _format_value(3.14) == "3.14"

    def test_list_joined_with_semicolons(self):
        assert _format_value(["a", "b", "c"]) == "a; b; c"

    def test_empty_list_returns_empty_string(self):
        assert _format_value([]) == ""

    def test_list_with_mixed_types(self):
        result = _format_value([1, "two", 3.0])
        assert result == "1; two; 3.0"

    def test_zero_is_not_treated_as_none(self):
        assert _format_value(0) == "0"

    def test_empty_string_returned_unchanged(self):
        assert _format_value("") == ""
