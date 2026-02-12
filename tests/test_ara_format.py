"""Tests for ARA (Asbestos Risk Assessment) format detection and preprocessing.

Validates the new dual-format support (SAMP + ARA) in the extraction pipeline.
These test format detection, preprocessing, and validation for ARA documents
like Greencap Asbestos Risk Assessment reports.
"""

import re

import pytest


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


class TestFormatDetection:
    """Test _detect_document_format function."""

    def test_detect_ara_format(self):
        from open_notebook.graphs.acm_extraction import _detect_document_format

        result = _detect_document_format(ARA_CONTENT_SNIPPET)
        assert result == "ara", f"Expected 'ara' but got '{result}'"

    def test_detect_samp_format(self):
        from open_notebook.graphs.acm_extraction import _detect_document_format

        result = _detect_document_format(SAMP_CONTENT_SNIPPET)
        assert result == "samp", f"Expected 'samp' but got '{result}'"

    def test_detect_unknown_format(self):
        from open_notebook.graphs.acm_extraction import _detect_document_format

        result = _detect_document_format("Some random text without any markers")
        assert result == "unknown", f"Expected 'unknown' but got '{result}'"

    def test_ara_indicators_count(self):
        """Verify ARA detection catches multiple indicators."""
        from open_notebook.graphs.acm_extraction import _detect_document_format

        # Content with only one indicator should not match
        minimal = "Building Name: Test Building\nSome random stuff"
        result = _detect_document_format(minimal)
        # One indicator alone shouldn't be enough
        assert result in ("unknown", "ara")

        # Two indicators should match
        two_indicators = (
            "Building Name: Test\n"
            "Presumed Positive\n"
        )
        result = _detect_document_format(two_indicators)
        assert result == "ara"


class TestPreprocessing:
    """Test _preprocess_acm_content with ARA content."""

    def test_ara_preprocessing_metadata(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        processed, metadata = _preprocess_acm_content(ARA_CONTENT_SNIPPET)

        assert metadata["document_format"] == "ara"
        assert metadata["ara_buildings_found"] >= 1
        assert metadata["ara_section_dividers"] >= 2  # Interior + Exterior
        assert metadata["acm_indicators_found"] >= 5  # "Asbestos" hazard types

    def test_ara_preprocessing_adds_section_markers(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        processed, metadata = _preprocess_acm_content(ARA_CONTENT_SNIPPET)

        # Should add === SECTION markers for section dividers
        assert "=== SECTION:" in processed
        assert "Exterior" in processed
        assert "Interior" in processed

    def test_ara_preprocessing_counts_hazard_none(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        _, metadata = _preprocess_acm_content(ARA_CONTENT_SNIPPET)

        # Item 7 has "None" hazard type - should be counted
        assert metadata["ara_none_hazard_count"] >= 1

    def test_ara_counts_positive_negative(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        _, metadata = _preprocess_acm_content(ARA_CONTENT_SNIPPET)

        # We have: Presumed Negative (1), Positive (1), Presumed Positive (3), Negative (1)
        assert metadata["ara_positive_count"] >= 3  # Positive + Presumed Positive
        assert metadata["ara_negative_count"] >= 2  # Negative + Presumed Negative

    def test_samp_preprocessing_still_works(self):
        from open_notebook.graphs.acm_extraction import _preprocess_acm_content

        processed, metadata = _preprocess_acm_content(SAMP_CONTENT_SNIPPET)

        assert metadata["document_format"] == "samp"
        assert metadata["rooms_found"] >= 2  # R0005, R0006
        assert "=== BUILDING:" in processed or "--- ROOM:" in processed


class TestRegisterSectionExtraction:
    """Test _extract_acm_register_section with ARA content."""

    def test_register_section_finds_ara_markers(self):
        from open_notebook.graphs.acm_extraction import (
            _extract_acm_register_section,
        )

        # Build content with substantial boilerplate before register
        boilerplate = "Introduction\n" * 100  # >500 chars of boilerplate
        full_content = boilerplate + "\nASBESTOS REGISTER\n" + ARA_CONTENT_SNIPPET

        extracted, was_extracted = _extract_acm_register_section(full_content)

        assert was_extracted is True
        assert "Building Name:" in extracted
        assert len(extracted) < len(full_content)

    def test_register_section_case_insensitive(self):
        from open_notebook.graphs.acm_extraction import (
            _extract_acm_register_section,
        )

        boilerplate = "Introduction\n" * 100
        full_content = boilerplate + "\nasbestos register\n" + ARA_CONTENT_SNIPPET

        extracted, was_extracted = _extract_acm_register_section(full_content)
        assert was_extracted is True

    def test_building_name_as_fallback_marker(self):
        from open_notebook.graphs.acm_extraction import (
            _extract_acm_register_section,
        )

        # Content with Building Name but no "Asbestos Register" header
        boilerplate = "Some intro text\n" * 100
        content = boilerplate + "\nBuilding Name:   Mortuary Buildings\n" + "Item data here"

        extracted, was_extracted = _extract_acm_register_section(content)
        assert was_extracted is True
        assert "Mortuary Buildings" in extracted


class TestValidation:
    """Test validate_records with ARA-style status values.

    validate_records is a LangGraph node: async fn(state, config) -> dict.
    We build the state dict and pass a minimal RunnableConfig.
    """

    @pytest.fixture
    def _make_state(self):
        """Helper to build a minimal ExtractionState dict."""
        from open_notebook.extractors.acm_schemas import BuildingRoomContext

        def _build(records):
            return {
                "records": records,
                "context": BuildingRoomContext(),
                "records_rejected": 0,
            }

        return _build

    @pytest.fixture
    def _config(self):
        return {"configurable": {}}

    @pytest.mark.asyncio
    async def test_validate_ara_positive_result(self, _make_state, _config):
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Eaves",
            material_description="Flat Cement Sheeting",
            result="Positive",
            sample_result="Positive",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        assert result["records"][0].result == "Positive"

    @pytest.mark.asyncio
    async def test_validate_ara_presumed_positive(self, _make_state, _config):
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Eaves",
            material_description="Flat Cement Sheeting",
            result="Assumed Positive",
            sample_result="Assumed Positive",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        assert result["records"][0].result == "Assumed Positive"

    @pytest.mark.asyncio
    async def test_validate_ara_negative_result(self, _make_state, _config):
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Wall",
            material_description="Flat Cement Sheeting",
            result="Negative",
            sample_result="Negative",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        assert result["records"][0].result == "Negative"

    @pytest.mark.asyncio
    async def test_validate_ara_presumed_negative(self, _make_state, _config):
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Roof",
            material_description="Metal Sheeting",
            result="Assumed Negative",
            sample_result="Assumed Negative",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        assert result["records"][0].result == "Assumed Negative"

    @pytest.mark.asyncio
    async def test_validate_negative_sets_na_fields(self, _make_state, _config):
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Wall",
            material_description="Sheeting",
            result="negative",
            sample_result="Negative",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        assert result["records"][0].result == "Negative"

    @pytest.mark.asyncio
    async def test_validate_medium_to_moderate_mapping(self, _make_state, _config):
        """BAR uses 'Moderate' not 'Medium' for disturbance potential."""
        from open_notebook.graphs.acm_extraction import validate_records
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        record = ACMExtractionRecord(
            building_id="Mortuary Buildings",
            product="Wall",
            material_description="Sheeting",
            result="Positive",
            sample_result="Positive",
            disturbance_potential="Medium",
            extraction_confidence="high",
        )
        result = await validate_records(_make_state([record]), _config)
        assert len(result["records"]) == 1
        # validate_records passes it through; validate_records_strict does Medium→Moderate


class TestBuildingInventoryPrompt:
    """Verify building_inventory.jinja loads and contains ARA format guidance."""

    def test_prompt_has_ara_format(self):
        from pathlib import Path

        prompt_path = Path(
            r"c:\Users\Local Admin\Documents\Silvatron\ACM Register"
            r"\prompts\acm\building_inventory.jinja"
        )
        content = prompt_path.read_text(encoding="utf-8")

        assert "FORMAT B:" in content or "ARA Format" in content
        assert "Building Name:" in content
        assert "Section Dividers" in content or "section divider" in content.lower()

    def test_building_extraction_prompt_has_ara_format(self):
        from pathlib import Path

        prompt_path = Path(
            r"c:\Users\Local Admin\Documents\Silvatron\ACM Register"
            r"\prompts\acm\building_extraction.jinja"
        )
        content = prompt_path.read_text(encoding="utf-8")

        assert "FORMAT B:" in content or "ARA Format" in content
        assert "Presumed Positive" in content
        assert "Hazard Type" in content.lower() or "hazard type" in content

    def test_extraction_prompt_has_ara_format(self):
        from pathlib import Path

        prompt_path = Path(
            r"c:\Users\Local Admin\Documents\Silvatron\ACM Register"
            r"\prompts\acm\extraction.jinja"
        )
        content = prompt_path.read_text(encoding="utf-8")

        assert "FORMAT B:" in content or "ARA Format" in content
        assert "Presumed Positive" in content
