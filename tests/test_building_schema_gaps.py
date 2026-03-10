"""Tests for the 5 missing Building__c fields added to BuildingExtractionResult
and the 2 new fields added to BuildingRecord.

Story: E35-S7 — Building schema gap fill
"""

import pytest

from open_notebook.domain.acm import BuildingRecord
from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult

# ---------------------------------------------------------------------------
# BuildingExtractionResult tests
# ---------------------------------------------------------------------------


class TestBuildingExtractionResultNewFields:
    """BuildingExtractionResult validates with 5 new optional fields."""

    def test_defaults_are_none(self):
        result = BuildingExtractionResult()
        assert result.state is None
        assert result.number_of_levels is None
        assert result.owned_or_leased is None
        assert result.building_sub_category is None
        assert result.building_risk_rating is None

    def test_state_accepts_valid_values(self):
        for state_code in ("VIC", "NSW", "QLD", "SA", "WA", "TAS", "NT", "ACT"):
            result = BuildingExtractionResult(state=state_code)
            assert result.state == state_code

    def test_number_of_levels_accepts_integer(self):
        result = BuildingExtractionResult(number_of_levels=3)
        assert result.number_of_levels == 3

    def test_number_of_levels_accepts_none(self):
        result = BuildingExtractionResult(number_of_levels=None)
        assert result.number_of_levels is None

    def test_owned_or_leased_accepts_valid_values(self):
        for value in ("Owned", "Leased"):
            result = BuildingExtractionResult(owned_or_leased=value)
            assert result.owned_or_leased == value

    def test_building_sub_category_free_text(self):
        result = BuildingExtractionResult(building_sub_category="Primary School")
        assert result.building_sub_category == "Primary School"

    def test_building_risk_rating_accepts_valid_values(self):
        for rating in ("Low", "Medium", "High"):
            result = BuildingExtractionResult(building_risk_rating=rating)
            assert result.building_risk_rating == rating

    def test_full_payload_round_trips(self):
        payload = {
            "building_name": "Test Building",
            "building_type": "Classroom",
            "state": "VIC",
            "number_of_levels": 2,
            "owned_or_leased": "Owned",
            "building_sub_category": "Primary School",
            "building_risk_rating": "Medium",
            "extraction_confidence": "high",
        }
        result = BuildingExtractionResult(**payload)
        assert result.state == "VIC"
        assert result.number_of_levels == 2
        assert result.owned_or_leased == "Owned"
        assert result.building_sub_category == "Primary School"
        assert result.building_risk_rating == "Medium"

    def test_existing_fields_unaffected(self):
        """Ensure pre-existing fields still work correctly after the schema addition."""
        result = BuildingExtractionResult(
            building_name="Old Block",
            building_type="Classroom",
            suburb="Fitzroy",
            postcode="3065",
            frequency_of_use="Daily",
        )
        assert result.building_name == "Old Block"
        assert result.building_type == "Classroom"
        assert result.suburb == "Fitzroy"
        assert result.postcode == "3065"
        assert result.frequency_of_use == "Daily"


# ---------------------------------------------------------------------------
# BuildingRecord tests — 2 new domain-model fields
# ---------------------------------------------------------------------------


class TestBuildingRecordNewFields:
    """BuildingRecord accepts building_sub_category and building_risk_rating."""

    def _minimal_record(self, **kwargs) -> BuildingRecord:
        base = {
            "internal_id": "BLD#001",
            "source_id": "source:test",
        }
        base.update(kwargs)
        return BuildingRecord(**base)

    def test_new_fields_default_to_none(self):
        record = self._minimal_record()
        assert record.building_sub_category is None
        assert record.building_risk_rating is None

    def test_building_sub_category_can_be_set(self):
        record = self._minimal_record(building_sub_category="Primary School")
        assert record.building_sub_category == "Primary School"

    def test_building_risk_rating_can_be_set(self):
        for rating in ("Low", "Medium", "High"):
            record = self._minimal_record(building_risk_rating=rating)
            assert record.building_risk_rating == rating

    def test_building_sub_category_sf_alias(self):
        """Accepts Salesforce API name via validation_alias."""
        record = BuildingRecord.model_validate(
            {
                "internal_id": "BLD#002",
                "source_id": "source:test",
                "Building_Sub_Category__c": "Secondary School",
            }
        )
        assert record.building_sub_category == "Secondary School"

    def test_building_risk_rating_sf_alias(self):
        """Accepts Salesforce API name via validation_alias."""
        record = BuildingRecord.model_validate(
            {
                "internal_id": "BLD#003",
                "source_id": "source:test",
                "Building_Risk_Rating__c": "High",
            }
        )
        assert record.building_risk_rating == "High"

    def test_existing_state_field_unaffected(self):
        """state field already existed in BuildingRecord — must still work."""
        record = self._minimal_record(state="QLD")
        assert record.state == "QLD"

    def test_existing_number_of_levels_unaffected(self):
        record = self._minimal_record(number_of_levels=4)
        assert record.number_of_levels == 4

    def test_existing_owned_or_leased_unaffected(self):
        record = self._minimal_record(owned_or_leased="Leased")
        assert record.owned_or_leased == "Leased"


# ---------------------------------------------------------------------------
# Integration: BuildingExtractionResult → BuildingRecord field mapping
# ---------------------------------------------------------------------------


class TestExtractionResultToBuildingRecordMapping:
    """Verifies that all 5 new fields flow from extraction result to domain record."""

    def test_new_fields_flow_through(self):
        result = BuildingExtractionResult(
            building_name="Integration Test Building",
            state="NSW",
            number_of_levels=5,
            owned_or_leased="Leased",
            building_sub_category="Office Block",
            building_risk_rating="Low",
        )

        record = BuildingRecord(
            internal_id="BLD#INT001",
            source_id="source:test-integration",
            building_name=result.building_name,
            state=result.state,
            number_of_levels=result.number_of_levels,
            owned_or_leased=result.owned_or_leased,
            building_sub_category=result.building_sub_category,
            building_risk_rating=result.building_risk_rating,
        )

        assert record.state == "NSW"
        assert record.number_of_levels == 5
        assert record.owned_or_leased == "Leased"
        assert record.building_sub_category == "Office Block"
        assert record.building_risk_rating == "Low"

    def test_none_fields_do_not_break_record_construction(self):
        """Missing new fields should not raise validation errors."""
        result = BuildingExtractionResult(
            building_name="Sparse Building",
            # all 5 new fields left as None (default)
        )

        record = BuildingRecord(
            internal_id="BLD#SPARSE",
            source_id="source:test-sparse",
            building_name=result.building_name,
            state=result.state,
            number_of_levels=result.number_of_levels,
            owned_or_leased=result.owned_or_leased,
            building_sub_category=result.building_sub_category,
            building_risk_rating=result.building_risk_rating,
        )

        assert record.state is None
        assert record.number_of_levels is None
        assert record.owned_or_leased is None
        assert record.building_sub_category is None
        assert record.building_risk_rating is None
