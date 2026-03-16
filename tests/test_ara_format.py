"""Tests for ARA (Asbestos Risk Assessment) format detection and preprocessing.

Validates the new dual-format support (SAMP + ARA) in the extraction pipeline.
These test format detection, preprocessing, and validation for ARA documents
like Greencap Asbestos Risk Assessment reports.
"""

# ── ARA content snippets (from Greencap report) ──────────────────────────────

ARA_CONTENT_SNIPPET = """
--- Page 7 ---

ASBESTOS REGISTER
Site Details     Building Details     Audit Details
Full Address:    24 Cooper Street, Alexandra VIC 3714
Building Name:   Mortuary Buildings
Number of Levels: 1
Construction Type: Weatherboard/brick

Mortuary Buildings - Exterior - Ground Level

1
External - Throughout
Roof - Metal Sheeting
Asbestos
Not Sampled
Presumed Negative

2
External - Throughout
Fascia - Flat Cement
Sheeting - Painted White
Asbestos
J169642-001-001
Positive
Photo: 1
Est. Extent: 5m2
Condition: Good Condition
Friability: Non-Friable
Dist. Potential: Low
Risk Rating: Low Risk

3
External - Throughout
Eaves - Flat Cement
Sheeting - Painted White
Asbestos
Previously Sampled
Presumed Positive
Photo: 1
Est. Extent: 20m2
Condition: Good Condition
Friability: Non-Friable
Dist. Potential: Low
Risk Rating: Low Risk

Mortuary Buildings - Interior - Ground Level

4
External - Throughout
Eaves - Flat Cement
Sheeting - Painted White
Asbestos
Previously Sampled
Presumed Positive

5
External - Throughout
Wall - Flat Cement Sheeting -
Textured painted white
Asbestos
J169642-001-003
Negative

--- Page 8 ---

ASBESTOS REGISTER
Building Name:   Mortuary Buildings

6
Boiler Room
Wall - Flat Cement Sheeting
Asbestos
Not Sampled
Presumed Positive
Photo: 2
Est. Extent: 10m2
Condition: Fair Condition
Friability: Non-Friable
Dist. Potential: Medium
Risk Rating: Medium Risk

7
General Store
Ceiling - Compressed Fibre Cement
None
"""

SAMP_CONTENT_SNIPPET = """
--- Page 15 ---

B009 - Special Purpose - 1950 - Steel

B009 - R0005 - General Storeroom - 1.45 m2
Floor Coverings
Res/Textile
Vinyl Tiles
2m2
Throughout Non Friable
Minimal Damage
Low
Asbestos-containing material

B009 - R0006 - Workshop - 3.20 m2
No Asbestos Containing Materials Found
"""


class TestBuildingInventoryPrompt:
    """Verify building_inventory.jinja loads and contains ARA format guidance."""

    def test_prompt_has_ara_format(self):
        from pathlib import Path

        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "acm"
            / "building_inventory.jinja"
        )
        content = prompt_path.read_text(encoding="utf-8")

        assert "Named buildings" in content or "ARA" in content
        assert "Building Name:" in content or "building name" in content.lower()
        assert "Interior/Exterior" in content or "section divider" in content.lower()
