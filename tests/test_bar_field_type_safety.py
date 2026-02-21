"""Tests for BAR field type safety validators (E2-S11)."""

import pytest
from pydantic import ValidationError

from api.models import ACMRecordCreateRequest, ACMRecordUpdateRequest

# --- Result validator ---


class TestResultValidator:
    def test_valid_values(self):
        for val in ["Positive", "Assumed Positive", "Negative", "Assumed Negative", "Unknown"]:
            req = ACMRecordCreateRequest(
                source_id="s:1", school_name="Test", building_id="B1",
                product="Tiles", material_description="Vinyl", result=val,
            )
            assert req.result == val

    def test_case_insensitive(self):
        req = ACMRecordCreateRequest(
            source_id="s:1", school_name="Test", building_id="B1",
            product="Tiles", material_description="Vinyl", result="positive",
        )
        assert req.result == "Positive"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="result must be one of"):
            ACMRecordCreateRequest(
                source_id="s:1", school_name="Test", building_id="B1",
                product="Tiles", material_description="Vinyl", result="Maybe",
            )


# --- Friable validator ---


class TestFriableValidator:
    def test_valid_values(self):
        req = ACMRecordUpdateRequest(friable="Friable")
        assert req.friable == "Friable"

    def test_non_friable_variant(self):
        req = ACMRecordUpdateRequest(friable="non-friable")
        assert req.friable == "Non Friable"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="friable must be one of"):
            ACMRecordUpdateRequest(friable="Sometimes")


# --- Risk status validator ---


class TestRiskStatusValidator:
    def test_normalizes_case(self):
        req = ACMRecordUpdateRequest(risk_status="low")
        assert req.risk_status == "Low"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="risk_status must be one of"):
            ACMRecordUpdateRequest(risk_status="Critical")


# --- Material condition validator ---


class TestMaterialConditionValidator:
    def test_valid_values(self):
        for val in ["Good", "Fair", "Poor", "Damaged"]:
            req = ACMRecordUpdateRequest(material_condition=val)
            assert req.material_condition == val

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="material_condition must be one of"):
            ACMRecordUpdateRequest(material_condition="Excellent")


# --- Area type validator ---


class TestAreaTypeValidator:
    def test_valid_values(self):
        for val in ["Interior", "Exterior", "Grounds"]:
            req = ACMRecordUpdateRequest(area_type=val)
            assert req.area_type == val

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="area_type must be one of"):
            ACMRecordUpdateRequest(area_type="Roof")


# --- None values pass through ---


class TestNonePassthrough:
    def test_optional_fields_accept_none(self):
        req = ACMRecordUpdateRequest(
            friable=None, risk_status=None, material_condition=None, area_type=None
        )
        assert req.friable is None
        assert req.risk_status is None
        assert req.material_condition is None
        assert req.area_type is None
