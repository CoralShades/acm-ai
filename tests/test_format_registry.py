"""Tests for the FormatDetector registry and format-specific detectors.

Covers:
- FormatRegistry: detector registration, priority ordering, detect_format()
- PipeTableDetector: detect(), extract_buildings(), get_column_mapping(), enrichment
- StandardFormatDetector: detect(), extract_buildings(), get_column_mapping()
- TextHeaderDetector: detect(), extract_buildings(), get_column_mapping()
"""

import pytest

# ---------------------------------------------------------------------------
# Sample content fixtures
# ---------------------------------------------------------------------------

SAMPLE_PIPE_TABLE_CONTENT = """
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

    def test_pipe_table_has_highest_priority(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        assert registry.detectors[0].name == "pipe_table"
        assert registry.detectors[0].priority == 5

    def test_get_detector_by_name(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        assert registry.get_detector("pipe_table") is not None
        assert registry.get_detector("standard") is not None
        assert registry.get_detector("text_header") is not None
        assert registry.get_detector("nonexistent") is None

    def test_detect_format_pipe_table(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        detector = registry.detect_format(SAMPLE_PIPE_TABLE_CONTENT)
        assert detector is not None
        assert detector.name == "pipe_table"

    def test_detect_format_standard(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        detector = registry.detect_format(SAMPLE_SAMP_CONTENT)
        assert detector is not None
        assert detector.name == "standard"

    def test_extract_buildings_via_registry(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        result = registry.extract_buildings(SAMPLE_PIPE_TABLE_CONTENT)
        assert result is not None
        format_name, buildings = result
        assert format_name == "pipe_table"
        assert len(buildings) == 3

    def test_extract_buildings_returns_none_for_unknown_format(self):
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        result = registry.extract_buildings(
            "This is plain text with no format indicators."
        )
        assert result is None


# ---------------------------------------------------------------------------
# PipeTableDetector tests
# ---------------------------------------------------------------------------


class TestPipeTableDetector:
    """Test PipeTableDetector detection, extraction, and enrichment."""

    def test_detect_pipe_table(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        assert detector.detect(SAMPLE_PIPE_TABLE_CONTENT) is True
        assert detector.detect(SAMPLE_SAMP_CONTENT) is False
        assert detector.detect(SAMPLE_ARA_CONTENT) is False

    def test_extract_buildings_count(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        buildings = detector.extract_buildings(SAMPLE_PIPE_TABLE_CONTENT)
        assert len(buildings) == 3
        names = [b.name for b in buildings]
        assert "Myrtle Street Clinic" in names
        assert "Mortuary Buildings" in names
        assert "Main Hospital Building" in names

    def test_enrichment_levels(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        buildings = detector.extract_buildings(SAMPLE_PIPE_TABLE_CONTENT)
        by_name = {b.name: b for b in buildings}

        myrtle = by_name["Myrtle Street Clinic"]
        assert myrtle.levels == 2

        main = by_name["Main Hospital Building"]
        assert main.levels == 3

        mortuary = by_name["Mortuary Buildings"]
        assert mortuary.levels == 1

    def test_parse_building_enrichment(self):
        """Verify _parse_building_enrichment extracts survey date and levels from context."""
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        # _parse_building_enrichment returns (levels, survey_date) tuple
        # Note: survey_date is parsed but BuildingMeta doesn't have a survey_date field,
        # so it's currently unused. This test verifies the parsing logic works.
        levels, survey_date = detector._parse_building_enrichment(
            SAMPLE_PIPE_TABLE_CONTENT,
            SAMPLE_PIPE_TABLE_CONTENT.index("Myrtle Street Clinic"),
        )
        assert levels == 2
        assert survey_date == "07-09-2020"

    def test_column_mapping(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        mapping = detector.get_column_mapping()
        assert mapping is not None
        assert "Location - Item Description" in mapping
        assert "Hazard Type" in mapping
        assert "Sample No." in mapping
        assert "Result" in mapping

    def test_synthetic_building_ids(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        buildings = detector.extract_buildings(SAMPLE_PIPE_TABLE_CONTENT)
        ids = [b.building_id for b in buildings]
        assert ids[0] == "B001"
        assert ids[1] == "B002"
        assert ids[2] == "B003"

    def test_page_ranges(self):
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        buildings = detector.extract_buildings(SAMPLE_PIPE_TABLE_CONTENT)
        by_name = {b.name: b for b in buildings}

        myrtle = by_name["Myrtle Street Clinic"]
        assert myrtle.page_start == 3

        main = by_name["Main Hospital Building"]
        assert main.page_start == 10

    def test_expanded_pipe_table_detect_window(self):
        """Pipe-table detection should work with up to 15000 chars before Site Details."""
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
        # Pad with 10000 chars of filler before the content
        padded = ("x" * 10000) + SAMPLE_PIPE_TABLE_CONTENT
        # Should still detect — Site Details is within 15000 chars
        assert detector.detect(padded) is True

    def test_greencap_variant_detection(self):
        """Greencap variant without Site Details should still be detected as PipeTable.

        When a document has ``| Building Name: | ... | Number of Levels: |``
        pipe-table rows (unique to PipeTable/Greencap), it should match even
        without the ``| Site Details |`` header.
        """
        from open_notebook.extractors.format_detectors.pipe_table_detector import (
            PipeTableDetector,
        )

        detector = PipeTableDetector()
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

    def test_greencap_not_detected_as_text_header(self):
        """Greencap pipe-table format should NOT be detected as text_header."""
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
        # Should match pipe_table (priority 5), NOT text_header (priority 20)
        assert detector.name == "pipe_table"


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
        assert detector.detect(SAMPLE_PIPE_TABLE_CONTENT) is False

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

    def test_detect_standard_format(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )
        detector = StandardFormatDetector()
        content = "## B00A - Admin Building - 1924 - Brick\nSome content"
        assert detector.detect(content) is True

    def test_no_detect_text_header(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )
        detector = StandardFormatDetector()
        content = "Building Name:\n  Test Building\n"
        assert detector.detect(content) is False

    def test_standard_no_column_mapping(self):
        from open_notebook.extractors.format_detectors.standard_detector import (
            StandardFormatDetector,
        )
        detector = StandardFormatDetector()
        assert detector.get_column_mapping() is None


# ---------------------------------------------------------------------------
# TextHeaderDetector tests
# ---------------------------------------------------------------------------


class TestTextHeaderDetector:
    """Test TextHeaderDetector detection and extraction."""

    def test_detect_text_header(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )
        detector = TextHeaderDetector()
        content = "Building Name:\n  Test Building\n\nSome content here"
        assert detector.detect(content) is True

    def test_pipe_table_detected_first_by_priority(self):
        """In the registry, pipe-table format is detected before text-header (priority 5 vs 20).

        Even if the text-header regex matches pipe-delimited content (due to the
        lookbehind only checking the immediately preceding character), the pipe-table
        detector runs first and claims the document.
        """
        from open_notebook.extractors.format_detectors import get_registry

        registry = get_registry()
        pipe_content = SAMPLE_PIPE_TABLE_CONTENT
        detector = registry.detect_format(pipe_content)
        assert detector is not None
        assert detector.name == "pipe_table"  # Not "text_header"

    def test_extract_text_header_buildings(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )
        detector = TextHeaderDetector()
        content = "Building Name:\n  Alpha Building\n\nSome ACM data\n\nBuilding Name:\n  Beta Building\n"
        buildings = detector.extract_buildings(content)
        assert len(buildings) == 2
        names = [b.name for b in buildings]
        assert "Alpha Building" in names
        assert "Beta Building" in names

    def test_text_header_column_mapping(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )
        detector = TextHeaderDetector()
        mapping = detector.get_column_mapping()
        assert mapping is not None
        assert "Building Element" in mapping

    def test_detect_ara_content(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )

        detector = TextHeaderDetector()
        assert detector.detect(SAMPLE_ARA_CONTENT) is True

    def test_extract_buildings(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )

        detector = TextHeaderDetector()
        buildings = detector.extract_buildings(SAMPLE_ARA_CONTENT)
        assert len(buildings) >= 1
        assert buildings[0].name == "Broadmeadows Police Station"

    def test_column_mapping(self):
        from open_notebook.extractors.format_detectors.text_header_detector import (
            TextHeaderDetector,
        )

        detector = TextHeaderDetector()
        mapping = detector.get_column_mapping()
        assert mapping is not None
        assert "Building Element" in mapping
        assert "ACM Status" in mapping


# ---------------------------------------------------------------------------
# Column mapping injection test
# ---------------------------------------------------------------------------


class TestColumnMappingInjection:
    """Test that column mapping is correctly threaded through to the prompt."""

    def test_v3_item_extraction_prompt_format_agnostic(self):
        """After MCS format-agnostic refactor, column_mapping is no longer rendered in template."""
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/v3_item_extraction")

        # Column mapping param is accepted but not rendered (format-agnostic prompts)
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

        # Prompt renders successfully with building context
        assert "B001" in rendered
        assert "Test Building" in rendered
        # Column mapping section no longer in template (format-agnostic since MCS refactor)
        assert "Document Column Mapping" not in rendered

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
