"""
Unit tests for V3 Two-Phase Extraction Pydantic schemas.

Tests BuildingExtractionResult, ACMItemRecord, and ACMItemExtractionResult
from open_notebook/extractors/acm_schemas_v3.py.

Story: E30-S7 Two-Phase Extraction Prompts
"""

import pytest
from pydantic import ValidationError

from open_notebook.extractors.acm_schemas_v3 import (
    ACMItemExtractionResult,
    ACMItemRecord,
    BuildingExtractionResult,
)


class TestBuildingExtractionResult:
    """Tests for BuildingExtractionResult (Phase 1 output model)."""

    def test_minimal_creation(self):
        """BuildingExtractionResult() instantiates with all None fields, confidence=medium."""
        result = BuildingExtractionResult()
        assert result.building_name is None
        assert result.building_type is None
        assert result.building_category is None
        assert result.building_address is None
        assert result.suburb is None
        assert result.postcode is None
        assert result.estimated_year_built is None
        assert result.construction_type is None
        assert result.date_of_audit is None
        assert result.frequency_of_use is None
        assert result.identifying_company is None
        assert result.extraction_confidence == "medium"
        assert result.extraction_notes is None

    def test_full_creation(self):
        """All 11 optional fields populated; model_dump() returns correct keys."""
        result = BuildingExtractionResult(
            building_name="Main Block",
            building_type="Classroom",
            building_category="Educational and training facilities",
            building_address="123 Main Street",
            suburb="Reservoir",
            postcode="3073",
            estimated_year_built="1965",
            construction_type="Brick veneer",
            date_of_audit="March 2024",
            frequency_of_use="Daily",
            identifying_company="Safety Pty Ltd",
            extraction_confidence="high",
            extraction_notes="Header clearly identified building type",
        )
        assert result.building_name == "Main Block"
        assert result.building_type == "Classroom"
        assert result.building_category == "Educational and training facilities"
        assert result.building_address == "123 Main Street"
        assert result.suburb == "Reservoir"
        assert result.postcode == "3073"
        assert result.estimated_year_built == "1965"
        assert result.construction_type == "Brick veneer"
        assert result.date_of_audit == "March 2024"
        assert result.frequency_of_use == "Daily"
        assert result.identifying_company == "Safety Pty Ltd"
        assert result.extraction_confidence == "high"
        assert result.extraction_notes == "Header clearly identified building type"

        dumped = result.model_dump()
        assert "building_name" in dumped
        assert "building_type" in dumped
        assert "extraction_confidence" in dumped
        assert dumped["building_name"] == "Main Block"

    def test_confidence_default(self):
        """extraction_confidence defaults to 'medium'."""
        result = BuildingExtractionResult()
        assert result.extraction_confidence == "medium"

    def test_confidence_high(self):
        """extraction_confidence can be set to 'high'."""
        result = BuildingExtractionResult(extraction_confidence="high")
        assert result.extraction_confidence == "high"

    def test_confidence_low(self):
        """extraction_confidence can be set to 'low'."""
        result = BuildingExtractionResult(extraction_confidence="low")
        assert result.extraction_confidence == "low"

    def test_extraction_notes_optional(self):
        """extraction_notes=None is valid."""
        result = BuildingExtractionResult(extraction_notes=None)
        assert result.extraction_notes is None

    def test_model_dump_roundtrip(self):
        """model_validate(model_dump()) roundtrip succeeds."""
        original = BuildingExtractionResult(
            building_name="Test Building",
            building_type="Office",
            suburb="Melbourne",
            extraction_confidence="medium",
        )
        dumped = original.model_dump()
        restored = BuildingExtractionResult.model_validate(dumped)
        assert restored.building_name == original.building_name
        assert restored.building_type == original.building_type
        assert restored.suburb == original.suburb


class TestACMItemRecord:
    """Tests for ACMItemRecord (Phase 2 individual item model)."""

    def test_minimal_creation(self):
        """ACMItemRecord() instantiates with all defaults."""
        record = ACMItemRecord()
        assert record.room_or_area is None
        assert record.internal_external is None
        assert record.level is None
        assert record.location_in_room is None
        assert record.friability_of_material is None
        assert record.acm_classification is None
        assert record.acm_sub_classification is None
        assert record.item_name is None
        assert record.if_other_item_name is None
        assert record.sample_result is None
        assert record.nata_sample_no is None
        assert record.condition is None
        assert record.disturbance_potential is None
        assert record.quantity is None
        assert record.labelled is None
        assert record.labelled_details is None
        assert record.hygienist_recommendations is None
        assert record.additional_comments is None

    def test_data_issues_default(self):
        """data_issues defaults to [] (not None)."""
        record = ACMItemRecord()
        assert record.data_issues == []
        assert isinstance(record.data_issues, list)

    def test_no_access_default(self):
        """no_access defaults to False."""
        record = ACMItemRecord()
        assert record.no_access is False

    def test_quantity_float(self):
        """quantity=10.5 is valid, quantity=None is valid."""
        record_with_qty = ACMItemRecord(quantity=10.5)
        assert record_with_qty.quantity == 10.5

        record_no_qty = ACMItemRecord(quantity=None)
        assert record_no_qty.quantity is None

    def test_quantity_zero(self):
        """quantity=0.0 is valid."""
        record = ACMItemRecord(quantity=0.0)
        assert record.quantity == 0.0

    def test_full_sf_fields(self):
        """All 17+ fields populated; model_dump() round-trips correctly."""
        record = ACMItemRecord(
            room_or_area="Boiler Room",
            internal_external="Internal",
            level="Ground",
            location_in_room="Ceiling",
            friability_of_material="Non-friable",
            acm_classification="Cement products",
            acm_sub_classification="Flat sheeting",
            item_name="Ceiling",
            if_other_item_name=None,
            sample_result="Positive",
            nata_sample_no="34511-001",
            condition="Stable",
            disturbance_potential="Low",
            quantity=20.5,
            labelled="Yes",
            labelled_details="Label on north wall",
            hygienist_recommendations="Monitor annually",
            additional_comments="Good condition overall",
            no_access=False,
            extraction_confidence="high",
            data_issues=["Minor formatting issue"],
            page_number=12,
        )
        assert record.room_or_area == "Boiler Room"
        assert record.friability_of_material == "Non-friable"
        assert record.item_name == "Ceiling"
        assert record.quantity == 20.5
        assert record.labelled == "Yes"
        assert record.page_number == 12

        dumped = record.model_dump()
        restored = ACMItemRecord.model_validate(dumped)
        assert restored.room_or_area == record.room_or_area
        assert restored.friability_of_material == record.friability_of_material
        assert restored.quantity == record.quantity
        assert restored.data_issues == record.data_issues

    def test_no_access_true(self):
        """no_access=True is valid."""
        record = ACMItemRecord(no_access=True)
        assert record.no_access is True

    def test_extraction_confidence_default(self):
        """extraction_confidence defaults to 'medium'."""
        record = ACMItemRecord()
        assert record.extraction_confidence == "medium"


class TestACMItemExtractionResult:
    """Tests for ACMItemExtractionResult (Phase 2 output wrapper)."""

    def test_empty_result(self):
        """ACMItemExtractionResult() has records=[], status='valid'."""
        result = ACMItemExtractionResult()
        assert result.records == []
        assert result.status == "valid"
        assert result.extraction_notes is None

    def test_with_records(self):
        """List of 3 ACMItemRecord items accepted."""
        items = [
            ACMItemRecord(room_or_area="Room 1", item_name="Ceiling"),
            ACMItemRecord(room_or_area="Room 2", item_name="Floor covering"),
            ACMItemRecord(room_or_area="Room 3", item_name="Pipework insulation"),
        ]
        result = ACMItemExtractionResult(records=items)
        assert len(result.records) == 3
        assert result.records[0].room_or_area == "Room 1"
        assert result.records[2].item_name == "Pipework insulation"

    def test_status_values(self):
        """'valid', 'no_acm_data', 'invalid' all accepted as strings."""
        r1 = ACMItemExtractionResult(status="valid")
        assert r1.status == "valid"

        r2 = ACMItemExtractionResult(status="no_acm_data")
        assert r2.status == "no_acm_data"

        r3 = ACMItemExtractionResult(status="invalid")
        assert r3.status == "invalid"

    def test_model_dump_roundtrip(self):
        """model_validate(model_dump()) roundtrip succeeds."""
        items = [
            ACMItemRecord(
                room_or_area="Corridor",
                sample_result="Negative",
                friability_of_material="Non-friable",
                condition="Stable",
            )
        ]
        original = ACMItemExtractionResult(
            records=items, status="valid", extraction_notes="Clean extraction"
        )
        dumped = original.model_dump()
        restored = ACMItemExtractionResult.model_validate(dumped)
        assert len(restored.records) == 1
        assert restored.records[0].room_or_area == "Corridor"
        assert restored.status == "valid"
        assert restored.extraction_notes == "Clean extraction"

    def test_model_validate_with_bool_labelled_and_null_data_issues(self):
        """End-to-end: normalize + model_validate with Ollama-style JSON."""
        from open_notebook.extractors.orchestrator import _normalize_extraction_json

        raw = {
            "records": [
                {
                    "room_or_area": "Room 1",
                    "item_name": "Ceiling tiles",
                    "labelled": False,
                    "data_issues": None,
                },
                {
                    "room_or_area": "Room 2",
                    "item_name": "Floor",
                    "labelled": True,
                    "data_issues": "missing sample",
                },
            ],
            "status": "valid",
        }
        _normalize_extraction_json(raw)
        result = ACMItemExtractionResult.model_validate(raw)
        assert len(result.records) == 2
        assert result.records[0].labelled == "No"
        assert result.records[0].data_issues == []
        assert result.records[1].labelled == "Yes"
        assert result.records[1].data_issues == ["missing sample"]


class TestBroadmeadowsBenchmarkStructure:
    """Verifies test structure for benchmark validation (AC6).

    NOTE: These are structure-only tests. The actual LLM call is NOT made.
    They verify that the two-phase pipeline can be invoked with correct inputs.
    """

    def test_phase1_can_receive_building_content(self):
        """Verify BuildingExtractionResult can be instantiated with typical Broadmeadows header fields."""
        result = BuildingExtractionResult(
            building_name="Broadmeadows Police Complex",
            building_address="21-25 Pearcedale Parade",
            suburb="Broadmeadows",
            postcode="3047",
            building_type="Police Station",
        )
        assert result.building_name == "Broadmeadows Police Complex"
        assert result.suburb == "Broadmeadows"
        assert result.postcode == "3047"
        assert result.building_type == "Police Station"

    def test_phase2_can_receive_item_records(self):
        """Verify ACMItemExtractionResult can hold typical item records."""
        item = ACMItemRecord(
            room_or_area="Boiler Room",
            item_name="Pipework insulation",
            acm_classification="Insulation Products",
            sample_result="Positive",
            friability_of_material="Non-friable",
            condition="Stable",
        )
        result = ACMItemExtractionResult(records=[item])
        assert len(result.records) == 1
        assert result.records[0].item_name == "Pipework insulation"
        assert result.records[0].acm_classification == "Insulation Products"


class TestAlexanderBenchmarkStructure:
    """Verifies test structure for Alexander benchmark (AC7)."""

    def test_normalize_v3_records_handles_ara_format(self):
        """Alexander uses ARA format — item records have room_or_area not room_id."""
        item = ACMItemRecord(
            room_or_area="External",
            internal_external="External",
            item_name="Eave lining",
            acm_sub_classification="Flat sheeting",
            sample_result="Assumed Positive",
            friability_of_material="Non-friable",
        )
        result = ACMItemExtractionResult(records=[item])
        # Stub plan
        from open_notebook.extractors.orchestrator import (
            BuildingExtractionPlan,
            ExtractionStrategy,
        )

        plan = BuildingExtractionPlan(
            building_id="B001",
            building_name="Main Building",
            page_range=(1, 10),
            strategy=ExtractionStrategy.FULL_LLM,
            complexity="complex",
        )
        from open_notebook.extractors.orchestrator import _normalize_v3_records

        normalized = _normalize_v3_records(None, result, plan)
        assert len(normalized) == 1
        assert normalized[0].product == "Eave lining"
        assert normalized[0].area_type == "Exterior"
        assert normalized[0].material_description == "Flat sheeting"
        assert normalized[0].sample_result == "Assumed Positive"
        assert normalized[0].building_id == "B001"
