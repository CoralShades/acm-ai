"""Tests for the FormatDetector registry and format-specific detectors.

Covers:
- FormatRegistry: detector registration, priority ordering, detect_format()
- ClutchDetector: detect(), extract_buildings(), get_column_mapping(), enrichment
- StandardFormatDetector: detect(), extract_buildings(), get_column_mapping()
- ARADetector: detect(), extract_buildings(), get_column_mapping()
"""

import pytest

# ---------------------------------------------------------------------------
# Sample content fixtures
# ---------------------------------------------------------------------------

SAMPLE_CLUTCH_CONTENT = """
--- Page 1 ---

| Site Details     | Site Details                                           |
|------------------|--------------------------------------------------------|
| Full Address:    | 24 Cooper Street, Alexandra VIC 3714                   |
| Client Name:     | Alexander District Health                              |

--- Page 2 ---

| Location | High Risk | Medium Risk | Low Risk |
|----------|-----------|-------------|----------|
| Myrtle Street Clinic - Ground Level   | 0 | 0 | 2 |

--- Page 3 ---

| Building Name: | Myrtle Street Clinic | Number of Levels: | 2 | Survey Date: | 07-09-2020 |
|----------------|---------------------|-------------------|---|-------------|-------------|
| Item No. | Location - Item Description | Hazard Type | Sample No. | Result |
| 1 | Carpet Underlay - Bituminous | Asbestos | S001 | Detected |

--- Page 5 ---

| Building Name: | Mortuary Buildings | Number of Levels: | 1 | Survey Date: | 15-03-2021 |
|----------------|-------------------|-------------------|---|-------------|-------------|
| 2 | External Eaves Lining | Asbestos | S002 | Detected |

--- Page 10 ---

| Building Name: | Main Hospital Building | Number of Levels: | 3 | Survey Date: | 07-09-2020 |
|----------------|----------------------|-------------------|---|-------------|-------------|
| 3 | Vinyl Floor Tiles | Asbestos | S003 | Detected |

--- Page 20 ---
"""

SAMPLE_SAMP_CONTENT = """
--- Page 1 ---

## B00A - Admin Building - 1960 - Brick

#### B00A-R0001 - Classroom 1

| Product | Material Description | Result |
|---------|---------------------|--------|
| Floor tiles | Vinyl asbestos | Detected |

--- Page 5 ---

## B00B - Science Block - 1972 - Fibro

#### B00B-R0001 - Lab 1

| Product | Material Description | Result |
|---------|---------------------|--------|
| Wall lining | Fibro sheet | Detected |

--- Page 10 ---
"""

SAMPLE_ARA_CONTENT = """
--- Page 1 ---

Building Name:
Broadmeadows Police Station

| Item No | Building Element | Material Type | ACM Status | Risk Rating |
|---------|-----------------|---------------|------------|-------------|
| 1 | Eaves soffit | Fibro cement | Detected | Low |

--- Page 5 ---

Building Name:
  Broadmeadows Police Station

| Item No | Building Element | Material Type | ACM Status | Risk Rating |
|---------|-----------------|---------------|------------|-------------|
| 2 | Internal walls | Fibro board | Assumed Positive | Medium |

--- Page 10 ---
"""


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestFormatRegistry:
    """Test the FormatRegistry singleton and auto-registration."""

    def test_registry_has_detectors(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        assert len(registry.detectors) >= 3

    def test_detectors_sorted_by_priority(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        priorities = [d.priority for d in registry.detectors]
        assert priorities == sorted(priorities)

    def test_clutch_has_highest_priority(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        assert registry.detectors[0].name == "clutch"
        assert registry.detectors[0].priority == 5

    def test_get_detector_by_name(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        assert registry.get_detector("clutch") is not None
        assert registry.get_detector("standard") is not None
        assert registry.get_detector("ara") is not None
        assert registry.get_detector("nonexistent") is None

    def test_detect_format_clutch(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        detector = registry.detect_format(SAMPLE_CLUTCH_CONTENT)
        assert detector is not None
        assert detector.name == "clutch"

    def test_detect_format_standard(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        detector = registry.detect_format(SAMPLE_SAMP_CONTENT)
        assert detector is not None
        assert detector.name == "standard"

    def test_extract_buildings_via_registry(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        result = registry.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        assert result is not None
        format_name, buildings = result
        assert format_name == "clutch"
        assert len(buildings) == 3

    def test_extract_buildings_returns_none_for_unknown_format(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        result = registry.extract_buildings(
            "This is plain text with no format indicators."
        )
        assert result is None


# ---------------------------------------------------------------------------
# ClutchDetector tests
# ---------------------------------------------------------------------------


class TestClutchDetector:
    """Test ClutchDetector detection, extraction, and enrichment."""

    def test_detect_clutch(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        assert detector.detect(SAMPLE_CLUTCH_CONTENT) is True
        assert detector.detect(SAMPLE_SAMP_CONTENT) is False
        assert detector.detect(SAMPLE_ARA_CONTENT) is False

    def test_extract_buildings_count(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        buildings = detector.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        assert len(buildings) == 3
        names = [b.name for b in buildings]
        assert "Myrtle Street Clinic" in names
        assert "Mortuary Buildings" in names
        assert "Main Hospital Building" in names

    def test_enrichment_levels(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        buildings = detector.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        by_name = {b.name: b for b in buildings}

        myrtle = by_name["Myrtle Street Clinic"]
        assert myrtle.levels == 2

        main = by_name["Main Hospital Building"]
        assert main.levels == 3

        mortuary = by_name["Mortuary Buildings"]
        assert mortuary.levels == 1

    def test_enrichment_survey_date(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        buildings = detector.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        by_name = {b.name: b for b in buildings}

        myrtle = by_name["Myrtle Street Clinic"]
        assert myrtle.survey_date == "07-09-2020"

        mortuary = by_name["Mortuary Buildings"]
        assert mortuary.survey_date == "15-03-2021"

    def test_column_mapping(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        mapping = detector.get_column_mapping()
        assert mapping is not None
        assert "Location - Item Description" in mapping
        assert "Hazard Type" in mapping
        assert "Sample No." in mapping
        assert "Result" in mapping

    def test_synthetic_building_ids(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        buildings = detector.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        ids = [b.building_id for b in buildings]
        assert ids[0] == "B001"
        assert ids[1] == "B002"
        assert ids[2] == "B003"

    def test_page_ranges(self):
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        buildings = detector.extract_buildings(SAMPLE_CLUTCH_CONTENT)
        by_name = {b.name: b for b in buildings}

        myrtle = by_name["Myrtle Street Clinic"]
        assert myrtle.page_start == 3

        main = by_name["Main Hospital Building"]
        assert main.page_start == 10

    def test_expanded_clutch_detect_window(self):
        """Clutch detection should work with up to 15000 chars before Site Details."""
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        # Pad with 10000 chars of filler before the content
        padded = ("x" * 10000) + SAMPLE_CLUTCH_CONTENT
        # Should still detect — Site Details is within 15000 chars
        assert detector.detect(padded) is True

    def test_greencap_variant_detection(self):
        """Greencap variant without Site Details should still be detected as Clutch.

        When a document has ``| Building Name: | ... | Number of Levels: |``
        pipe-table rows (unique to Clutch/Greencap), it should match even
        without the ``| Site Details |`` header.
        """
        from open_notebook.extractors.format_detectors.clutch_detector import (
            ClutchDetector,
        )

        detector = ClutchDetector()
        # Greencap content WITHOUT Site Details but WITH Building Name + Levels rows
        greencap_content = """
--- Page 1 ---

## Greencap

ASBESTOS RISK ASSESSMENT
ALEXANDER DISTRICT HOSPITAL
24 COOPER STREET, ALEXANDRA VIC 3714

--- Page 5 ---

| Building Name: | Myrtle Street Clinic | Number of Levels: | 2 | Survey Date: | 07-09-2020 |
|----------------|---------------------|-------------------|---|-------------|-------------|
| Item No. | Location - Item Description | Hazard Type | Sample No. | Result |
| 1 | Carpet Underlay | Asbestos | S001 | Detected |
"""
        assert detector.detect(greencap_content) is True

    def test_greencap_not_detected_as_ara(self):
        """Greencap pipe-table format should NOT be detected as ARA."""
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        greencap_content = """
--- Page 5 ---

| Building Name: | Main Hospital Building | Number of Levels: | 3 | Survey Date: | 07-09-2020 |
|----------------|----------------------|-------------------|---|-------------|-------------|
| 3 | Vinyl Floor Tiles | Asbestos | S003 | Detected |
"""
        detector = registry.detect_format(greencap_content)
        assert detector is not None
        # Should match Clutch (priority 5), NOT ARA (priority 20)
        assert detector.name == "clutch"


# ---------------------------------------------------------------------------
# StandardFormatDetector tests
# ---------------------------------------------------------------------------


class TestStandardFormatDetector:
    """Test StandardFormatDetector detection and extraction."""

    def test_detect_standard(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )

        detector = StandardFormatDetector()
        assert detector.detect(SAMPLE_SAMP_CONTENT) is True
        assert detector.detect(SAMPLE_CLUTCH_CONTENT) is False

    def test_extract_buildings(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )

        detector = StandardFormatDetector()
        buildings = detector.extract_buildings(SAMPLE_SAMP_CONTENT)
        assert len(buildings) == 2
        ids = [b.building_id for b in buildings]
        assert "B00A" in ids
        assert "B00B" in ids

    def test_building_names_and_years(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )

        detector = StandardFormatDetector()
        buildings = detector.extract_buildings(SAMPLE_SAMP_CONTENT)
        by_id = {b.building_id: b for b in buildings}

        assert by_id["B00A"].name == "Admin Building"
        assert by_id["B00A"].year == 1960
        assert by_id["B00A"].construction == "Brick"

        assert by_id["B00B"].name == "Science Block"
        assert by_id["B00B"].year == 1972

    def test_no_column_mapping(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )

        detector = StandardFormatDetector()
        assert detector.get_column_mapping() is None


# ---------------------------------------------------------------------------
# ARADetector tests
# ---------------------------------------------------------------------------


class TestARADetector:
    """Test ARADetector detection and extraction."""

    def test_detect_ara(self):
        from open_notebook.extractors.format_detectors.ara_detector import (
            ARADetector,
        )

        detector = ARADetector()
        assert detector.detect(SAMPLE_ARA_CONTENT) is True

    def test_extract_buildings(self):
        from open_notebook.extractors.format_detectors.ara_detector import (
            ARADetector,
        )

        detector = ARADetector()
        buildings = detector.extract_buildings(SAMPLE_ARA_CONTENT)
        assert len(buildings) >= 1
        assert buildings[0].name == "Broadmeadows Police Station"

    def test_column_mapping(self):
        from open_notebook.extractors.format_detectors.ara_detector import (
            ARADetector,
        )

        detector = ARADetector()
        mapping = detector.get_column_mapping()
        assert mapping is not None
        assert "Building Element" in mapping
        assert "ACM Status" in mapping


# ---------------------------------------------------------------------------
# Column mapping injection test
# ---------------------------------------------------------------------------


class TestColumnMappingInjection:
    """Test that column mapping is correctly threaded through to the prompt."""

    def test_v3_item_extraction_prompt_includes_mapping(self):
        """Verify the Jinja template renders column mapping when provided."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/v3_item_extraction")

        # Render with column mapping
        rendered = prompter.render(
            data={
                "building_context": {
                    "building_id": "B001",
                    "building_name": "Test Building",
                    "page_start": 1,
                    "page_end": 5,
                    "complexity": "complex",
                },
                "building_meta": {},
                "picklists": {
                    "friability_options": "Non-friable, Friable",
                    "acm_classification_options": "Vinyl products",
                    "sample_result_options": "Positive, Negative",
                    "condition_options": "Stable, Fair, Poor",
                    "disturbance_potential_options": "Low, Medium, High",
                    "internal_external_options": "Internal, External",
                    "labelled_options": "Yes, No",
                    "item_name_options": "Floor covering, Wall lining",
                },
                "column_mapping": {
                    "Location - Item Description": "product",
                    "Hazard Type": "acm_sub_classification",
                },
            }
        )

        assert "Document Column Mapping" in rendered
        assert "Location - Item Description" in rendered
        assert "Hazard Type" in rendered

    def test_v3_item_extraction_prompt_no_mapping(self):
        """Verify no column mapping section when mapping is not provided."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/v3_item_extraction")

        rendered = prompter.render(
            data={
                "building_context": {
                    "building_id": "B00A",
                    "building_name": "Admin",
                    "page_start": 1,
                    "page_end": 5,
                    "complexity": "complex",
                },
                "building_meta": {},
                "picklists": {
                    "friability_options": "",
                    "acm_classification_options": "",
                    "sample_result_options": "",
                    "condition_options": "",
                    "disturbance_potential_options": "",
                    "internal_external_options": "",
                    "labelled_options": "",
                    "item_name_options": "",
                },
            }
        )

        assert "Document Column Mapping" not in rendered
