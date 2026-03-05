"""E28: ARA-format 'Not Sampled' record recovery tests.

Tests the ``_recover_not_sampled_records_ara()`` function added in E28-S2
to recover unsampled items from ARA-format documents (e.g., Alexander District
Hospital) that the LLM misses during extraction.
"""

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.graphs.acm_extraction import (
    _recover_no_access_records,
    _recover_not_sampled_records_ara,
)

# ---------------------------------------------------------------------------
# Test fixtures — representative ARA-format text fragments
# ---------------------------------------------------------------------------

ARA_FIRE_DOOR_TEXT = """
Mortuary Buildings - Interior - Ground Level
5
Boiler Room
Fire Door - Fire Door Core
Asbestos
Not Sampled
Restricted Access
Presumed Positive
J169642-0
01-Photo0
10
1 Unit/s
Fair
Friable
Low
Low
"""

ARA_SHOWER_CUBICLE_TEXT = """
Old Alexandra Hospital - Interior - Ground Level
29
Bathroom Adjacent Labour Ward
Shower Cubicle - Flat Cement
Sheeting - Beneath shower tray
Asbestos
Not Sampled
Restricted Access
Presumed Positive
J169642-0
01-Photo0
43
1 m2
Good
Non
Friable
"""

ARA_EAVES_TEXT = """
VMO Accommodations - Exterior - Ground Level
16
External - Throughout
Eaves - Flat Cement Sheeting -
Painted white
Asbestos
Not Sampled
Height Restricted
Presumed Positive
J169642-0
01-Photo0
62
40 m2
"""

ARA_ELECTRICAL_TEXT = """
Old Alexandra Hospital - Interior - Ground Level
40
Former Laundry - External
Passage
Electrical Distribution Board -
Compressed Bituminous Electrical
Panel
Asbestos
Not Sampled
Live Electrical Hazard
Presumed Positive
"""

ARA_CEILING_TEXT = """
Old Alexandra Hospital - Interior - Ground Level
38
Flamable Liquids Store
Ceiling - Flat Cement Sheeting
Asbestos
Not Sampled
Height Restricted
Presumed Positive
"""

ARA_SAFE_TEXT = """
Old Alexandra Hospital - Interior - Ground Level
52
Reception
Safe - Insulation - Safe
Asbestos
Not Sampled
Restricted Access
Presumed Positive
"""

ARA_MULTI_ITEM_TEXT = """
Mortuary Buildings - Interior - Ground Level
5
Boiler Room
Fire Door - Fire Door Core
Asbestos
Not Sampled
Restricted Access
Presumed Positive
J169642-0
01-Photo0
10
1 Unit/s

6
Mortuary Room
Ceiling - Flat Cement Sheeting
Asbestos
Not Sampled
Height Restricted
Presumed Positive
J169642-0
01-Photo0
08
10 m2
"""

# A sampled (non "Not Sampled") ARA entry — should NOT be recovered
ARA_SAMPLED_POSITIVE_TEXT = """
Old Alexandra Hospital - Exterior - Ground Level
18
External - Adjacent Workshop Gable End
Gable lining - Flat Cement Sheeting
Asbestos
J169642-001-018
Positive
J169642-0
01-Photo0
54
1 m2
"""

# SAMP-format text — ARA recovery should NOT match this
SAMP_NO_ACCESS_TEXT = """
Ground
floor
Main Foyer
Room adjacent
disabled toilet
Unknown
-
-
No access.
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestARANotSampledRecovery:
    def test_fire_door_recovered(self):
        """Fire door 'Not Sampled' row recovered from ARA full_text."""
        records = _recover_not_sampled_records_ara(
            ARA_FIRE_DOOR_TEXT, [], "unknown", ""
        )
        assert len(records) >= 1
        rec = records[0]
        assert (
            "fire door" in rec.product.lower() or "fire door" in rec.room_name.lower()
        )
        assert rec.result == "Assumed Positive"
        assert rec.sample_result == "Assumed Positive"
        assert rec.sample_no == "Not Sampled"
        assert rec.no_access is True
        assert rec.building_name == "Mortuary Buildings"

    def test_shower_cubicle_recovered(self):
        """Shower cubicle 'Assumed positive' row recovered."""
        records = _recover_not_sampled_records_ara(
            ARA_SHOWER_CUBICLE_TEXT, [], "unknown", ""
        )
        assert len(records) >= 1
        rec = records[0]
        assert "shower" in rec.product.lower() or "shower" in rec.room_name.lower()
        assert rec.result == "Assumed Positive"
        assert rec.no_access is True

    def test_eaves_recovered(self):
        """Eaves (height restricted) recovered."""
        records = _recover_not_sampled_records_ara(ARA_EAVES_TEXT, [], "unknown", "")
        assert len(records) >= 1
        rec = records[0]
        assert (
            "eaves" in rec.product.lower()
            or "eaves" in rec.material_description.lower()
        )
        assert rec.building_name == "VMO Accommodations"
        assert rec.area_type == "Exterior"

    def test_electrical_board_recovered(self):
        """Electrical distribution board (live electrical hazard) recovered."""
        records = _recover_not_sampled_records_ara(
            ARA_ELECTRICAL_TEXT, [], "unknown", ""
        )
        assert len(records) >= 1
        rec = records[0]
        assert (
            "electrical" in rec.product.lower()
            or "electrical" in rec.material_description.lower()
        )
        assert "Live Electrical" in rec.data_issues[0]

    def test_ceiling_recovered(self):
        """Ceiling 'Not Sampled' (height restricted) recovered."""
        records = _recover_not_sampled_records_ara(ARA_CEILING_TEXT, [], "unknown", "")
        assert len(records) >= 1
        rec = records[0]
        assert "ceiling" in rec.product.lower()

    def test_safe_recovered(self):
        """Safe insulation (restricted access) recovered."""
        records = _recover_not_sampled_records_ara(ARA_SAFE_TEXT, [], "unknown", "")
        assert len(records) >= 1
        rec = records[0]
        assert "safe" in rec.product.lower() or "insulation" in rec.product.lower()

    def test_multiple_items_recovered(self):
        """Multiple Not Sampled items in same building section recovered."""
        records = _recover_not_sampled_records_ara(
            ARA_MULTI_ITEM_TEXT, [], "unknown", ""
        )
        assert len(records) >= 2, (
            f"Expected >=2, got {len(records)}: {[r.product for r in records]}"
        )

    def test_no_duplicate_recovery(self):
        """Recovery does not duplicate records already extracted by LLM."""
        existing = [
            ACMExtractionRecord(
                building_id="unknown",
                product="Fire Door",
                material_description="Fire Door Core",
                result="Assumed Positive",
                room_name="Boiler Room",
                location="Fire Door",
                sample_no="Not Sampled",
                sample_result="Assumed Positive",
            )
        ]
        records = _recover_not_sampled_records_ara(
            ARA_FIRE_DOOR_TEXT, existing, "unknown", ""
        )
        # Should not duplicate the fire door
        fire_door_count = sum(
            1 for r in records if "fire door" in (r.product or "").lower()
        )
        assert fire_door_count == 0, (
            f"Fire door should not be duplicated, got {fire_door_count}"
        )

    def test_sampled_positive_not_recovered(self):
        """Sampled positive items (with NATA sample number) should NOT be recovered."""
        records = _recover_not_sampled_records_ara(
            ARA_SAMPLED_POSITIVE_TEXT, [], "unknown", ""
        )
        assert len(records) == 0, (
            f"Should not recover sampled items, got {len(records)}"
        )

    def test_samp_path_unaffected(self):
        """Legacy SAMP path recovery unaffected by ARA changes."""
        # The SAMP text should be processed by the SAMP scan in _recover_no_access_records
        # The ARA scan should NOT produce records from SAMP text (no "Asbestos" + "Not Sampled" pattern)
        records = _recover_not_sampled_records_ara(
            SAMP_NO_ACCESS_TEXT, [], "B009", "Main Building"
        )
        assert len(records) == 0, (
            f"ARA scan should not match SAMP text, got {len(records)}"
        )

    def test_samp_recovery_still_works(self):
        """The parent _recover_no_access_records still finds SAMP-format entries."""
        records = _recover_no_access_records(
            SAMP_NO_ACCESS_TEXT, [], "B009", "Main Building"
        )
        # SAMP scan should find the "No access." entry
        assert len(records) >= 1, "SAMP recovery should still work"
        assert records[0].no_access is True

    def test_building_context_from_section_header(self):
        """Building name extracted from ARA section header."""
        records = _recover_not_sampled_records_ara(ARA_EAVES_TEXT, [], "unknown", "")
        assert len(records) >= 1
        assert records[0].building_name == "VMO Accommodations"

    def test_area_type_from_section_header(self):
        """Area type (Interior/Exterior) extracted from ARA section header."""
        records = _recover_not_sampled_records_ara(ARA_EAVES_TEXT, [], "unknown", "")
        assert len(records) >= 1
        assert records[0].area_type == "Exterior"
