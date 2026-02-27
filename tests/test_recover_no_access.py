"""Unit tests for _recover_no_access_records() post-LLM fallback."""

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.graphs.acm_extraction import _recover_no_access_records


def _make_record(**kwargs) -> ACMExtractionRecord:
    """Helper to create a minimal ACMExtractionRecord."""
    defaults = {
        "building_id": "B001",
        "product": "Floor covering",
        "result": "Negative",
    }
    defaults.update(kwargs)
    return ACMExtractionRecord(**defaults)


# Page 8 text from Broadmeadows PyMuPDF output (simplified but structurally accurate)
BROADMEADOWS_PAGE8_TEXT = """\
--- Page 8 ---
Prensa Pty Ltd.
GF, 5 Burwood Road
Hawthorn, VIC, 3122
Ph.: (03) 9508 0100
Asbestos Register
Job No: 34511-039
Area /
Level
Room & Location
Feature
Item
Description
Hazard
Type
Hazard
Status
Sample
Number
Friability
Labelled
Y/N
Source of
Asbestos
That is Not
Fixed or
Installed
Workplace
Activities
Likely to
Disturb
Asbestos
Disturb.
Potential
Condition
Risk
Status
Approx.
Quantity
Control
Priority
Comments & Recommendations
Date of
Identification
Reinspect
Date
Photograph
Site Address: Broadmeadows Police Station
Client: Victoria Police
Ground
floor
Lift foyer
Lift
Internal lining
-
-
-
-
-
-
-
-
-
-
-
 -
No access at the time of the Assessment
-
Apr-25
Ground
floor
Main foyer
Room
adjacent
disabled
toilet
 -
 -
 -
 -
 -
-
 -
 -
 -
 -
 -
 -
 -
No access due to locked door.
 -
Apr-25
No photo available
Broadmeadows Police Station Register 34511-039 V2
4
LXM:34511-039:May 2020
--- Page 9 ---
"""


class TestRecoverNoAccessRecords:
    """Tests for the post-LLM no-access recovery fallback."""

    def test_recovers_two_no_access_records_from_page8(self):
        """Should recover both Lift Foyer and Main Foyer no-access records."""
        existing_records = []
        recovered = _recover_no_access_records(
            BROADMEADOWS_PAGE8_TEXT, existing_records, "B001", "Broadmeadows"
        )

        assert len(recovered) == 2

        # Record #30: Lift Foyer / Lift / Internal lining
        r30 = recovered[0]
        assert r30.room_name.lower() == "lift foyer"
        assert r30.location is not None
        assert "lift" in r30.location.lower()
        assert r30.product.lower() == "internal lining"
        assert r30.result == "Assumed Positive"
        assert r30.no_access is True
        assert r30.building_id == "B001"

        # Record #31: Main Foyer / Room adjacent disabled toilet / Unknown
        r31 = recovered[1]
        assert r31.room_name.lower() == "main foyer"
        assert r31.location is not None
        assert "disabled" in r31.location.lower() or "toilet" in r31.location.lower()
        assert r31.result == "Assumed Positive"
        assert r31.no_access is True

    def test_does_not_recover_already_extracted(self):
        """Should skip records that already exist in extracted_records."""
        existing = [
            _make_record(
                room_name="Lift Foyer",
                location="Lift",
                product="Internal lining",
                result="Assumed Positive",
            ),
        ]
        recovered = _recover_no_access_records(
            BROADMEADOWS_PAGE8_TEXT, existing, "B001", "Broadmeadows"
        )

        # Should only recover Main Foyer, not Lift Foyer
        assert len(recovered) == 1
        assert recovered[0].room_name.lower() == "main foyer"

    def test_does_not_recover_when_all_exist(self):
        """Should return empty list when all no-access records already extracted."""
        existing = [
            _make_record(
                room_name="Lift Foyer",
                location="Lift",
                product="Internal lining",
                result="Assumed Positive",
            ),
            _make_record(
                room_name="Main Foyer",
                location="Room adjacent disabled toilet",
                product="Unknown",
                result="Assumed Positive",
            ),
        ]
        recovered = _recover_no_access_records(
            BROADMEADOWS_PAGE8_TEXT, existing, "B001", "Broadmeadows"
        )

        assert len(recovered) == 0

    def test_empty_text_returns_empty(self):
        """Should return empty list for empty full_text."""
        recovered = _recover_no_access_records("", [], "B001", "Broadmeadows")
        assert recovered == []

    def test_no_no_access_phrases_returns_empty(self):
        """Should return empty list when text has no 'no access' phrases."""
        text = """--- Page 1 ---
Ground floor
Switch Room
Switchboard
Fuse cartridge
Non-friable
Good
Low
--- Page 2 ---"""
        recovered = _recover_no_access_records(text, [], "B001", "Broadmeadows")
        assert recovered == []

    def test_recovered_records_have_correct_fields(self):
        """Recovered records should have all required ACMExtractionRecord fields."""
        recovered = _recover_no_access_records(
            BROADMEADOWS_PAGE8_TEXT, [], "B001", "Broadmeadows"
        )

        for rec in recovered:
            assert rec.building_id == "B001"
            assert rec.building_name == "Broadmeadows"
            assert rec.result == "Assumed Positive"
            assert rec.sample_result == "Assumed Positive"
            assert rec.sample_no == "Not Sampled"
            assert rec.no_access is True
            assert rec.extraction_confidence == "low"
            assert len(rec.data_issues) > 0
            assert "fallback" in rec.data_issues[0].lower()

    def test_height_restriction_also_recovered(self):
        """Should also recover 'Height restriction' entries."""
        text = """Site Address: Test
Ground
floor
Utility Room
Above ceiling
Pipe insulation
-
-
-
Height restriction
-
"""
        recovered = _recover_no_access_records(text, [], "B001", "Test")
        assert len(recovered) == 1
        assert recovered[0].room_name.lower() == "utility room"
