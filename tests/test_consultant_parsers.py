"""
Unit tests for the Extensible Consultant Parser Framework.

Tests cover:
- ConsultantParser ABC (cannot instantiate directly)
- PrensaParser detection, column mapping, metadata extraction
- GreencapParser detection, column mapping, metadata extraction
- GenericParser detection (always True), backward compatibility
- Parser registry: correct selection for each format
- Fallback: unknown format gets GenericParser

Story: E1-S11 Extensible Consultant Parser Framework
"""

from abc import ABC

import pytest

# ============================================================================
# Task 1: Base module tests
# ============================================================================


class TestConsultantParserABC:
    """Verify ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self):
        """ConsultantParser is abstract and cannot be instantiated."""
        from open_notebook.extractors.parsers.base import ConsultantParser

        with pytest.raises(TypeError):
            ConsultantParser()

    def test_is_abstract_class(self):
        """ConsultantParser inherits from ABC."""
        from open_notebook.extractors.parsers.base import ConsultantParser

        assert issubclass(ConsultantParser, ABC)

    def test_has_required_abstract_methods(self):
        """ConsultantParser defines all required abstract methods."""
        from open_notebook.extractors.parsers.base import ConsultantParser

        abstract_methods = ConsultantParser.__abstractmethods__
        expected = {"name", "detect", "extract_metadata", "extract_items", "get_column_mapping", "get_register_headers"}
        assert expected == abstract_methods


class TestRawACMItem:
    """Test RawACMItem dataclass."""

    def test_raw_acm_item_creation(self):
        """RawACMItem can be created with required fields."""
        from open_notebook.extractors.parsers.base import RawACMItem

        item = RawACMItem(product="Floor Tiles", material_description="Vinyl tiles", result="Detected")
        assert item.product == "Floor Tiles"
        assert item.material_description == "Vinyl tiles"
        assert item.result == "Detected"

    def test_raw_acm_item_optional_fields(self):
        """RawACMItem optional fields default to None."""
        from open_notebook.extractors.parsers.base import RawACMItem

        item = RawACMItem(product="Tiles", material_description="Vinyl", result="Detected")
        assert item.extent is None
        assert item.location is None
        assert item.friable is None
        assert item.material_condition is None
        assert item.risk_status is None

    def test_raw_acm_item_all_fields(self):
        """RawACMItem accepts all optional fields."""
        from open_notebook.extractors.parsers.base import RawACMItem

        item = RawACMItem(
            product="Tiles",
            material_description="Vinyl",
            result="Detected",
            extent="50m²",
            location="Floor",
            friable="Non Friable",
            material_condition="Good",
            risk_status="Low",
            sample_number="S001",
            disturbance_potential="Low",
            labelled="Y",
            control_priority="P3",
            comments="Monitor",
        )
        assert item.extent == "50m²"
        assert item.sample_number == "S001"
        assert item.control_priority == "P3"


class TestDocumentMeta:
    """Test DocumentMeta dataclass."""

    def test_document_meta_creation(self):
        """DocumentMeta can be created with consultant_name."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Prensa Pty Ltd")
        assert meta.consultant_name == "Prensa Pty Ltd"

    def test_document_meta_optional_fields(self):
        """DocumentMeta optional fields default to None."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Test")
        assert meta.site_name is None
        assert meta.site_address is None
        assert meta.report_date is None
        assert meta.report_reference is None


class TestSourceLocation:
    """Test SourceLocation dataclass."""

    def test_source_location_creation(self):
        """SourceLocation can be created with all fields."""
        from open_notebook.extractors.parsers.base import SourceLocation

        loc = SourceLocation(
            building_id="B01",
            building_name="Main Block",
            room_id="B01-R1",
            room_name="Office",
        )
        assert loc.building_id == "B01"
        assert loc.building_name == "Main Block"

    def test_source_location_defaults(self):
        """SourceLocation optional fields default correctly."""
        from open_notebook.extractors.parsers.base import SourceLocation

        loc = SourceLocation()
        assert loc.building_id is None
        assert loc.building_name is None
        assert loc.building_year is None
        assert loc.building_construction is None
        assert loc.room_id is None
        assert loc.room_name is None
        assert loc.room_area is None
        assert loc.area_type == "Interior"


# ============================================================================
# Task 2: PrensaParser tests
# ============================================================================


class TestPrensaParser:
    """Test detection, header mapping, metadata extraction for Prensa."""

    def test_detect_prensa_marker(self):
        """Detects 'Prensa Pty Ltd' marker in text."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        assert parser.detect("... Prensa Pty Ltd ... Division 5 report")

    def test_detect_division5_marker(self):
        """Detects 'Division 5 Asbestos Assessment' marker."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        assert parser.detect("Division 5 Asbestos Assessment Report 2024")

    def test_detect_non_prensa(self):
        """Returns False for non-Prensa text."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        assert not parser.detect("Greencap Asbestos Risk Assessment")
        assert not parser.detect("Some other consultant report")

    def test_name_property(self):
        """Parser name is 'prensa'."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        assert parser.name == "prensa"

    def test_column_mapping_complete(self):
        """Column mapping contains all 15 Prensa columns mapped to raw fields."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        mapping = parser.get_column_mapping()
        # Must have mappings for the key Prensa columns
        assert "area / level" in mapping
        assert "item description" in mapping
        assert len(mapping) == 15  # All 15 Prensa columns mapped

    def test_register_headers(self):
        """Returns the 15 expected Prensa headers."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        headers = parser.get_register_headers()
        assert len(headers) == 15
        assert "area / level" in headers
        assert "item description" in headers
        assert "risk status" in headers

    def test_extract_metadata(self):
        """Extracts document metadata from Prensa cover pages."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        pages = {
            1: "Prensa Pty Ltd\nDivision 5 Asbestos Assessment\nTest Primary School\nReport Date: 15/03/2024",
            2: "Table of Contents...",
        }
        meta = parser.extract_metadata(pages)
        assert meta.consultant_name == "Prensa Pty Ltd"
        assert meta.site_name == "Test Primary School"
        assert meta.report_date == "15/03/2024"

    def test_extract_items_from_table(self):
        """Extracts RawACMItem list from table data with all fields verified."""
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = PrensaParser()
        tables = [
            {
                "headers": ["area / level", "room & location", "feature", "item description",
                            "hazard type", "hazard status", "sample number", "friability",
                            "labelled y/n", "disturb. potential", "condition", "risk status",
                            "approx. quantity", "control priority", "comments & recommendations"],
                "rows": [
                    ["Ground floor", "Room 1", "Ceiling", "Ceiling tiles", "ACM",
                     "Detected", "S001", "Non Friable", "Y", "Low", "Good", "Low",
                     "50m²", "P3", "Monitor condition"],
                ],
            }
        ]
        items = parser.extract_items(tables)
        assert len(items) == 1
        item = items[0]
        assert item.product == "Ceiling tiles"
        assert item.material_description == "Ceiling Ceiling tiles"
        assert item.result == "Detected"
        assert item.extent == "50m²"
        assert item.location == "Ceiling"
        assert item.friable == "Non Friable"
        assert item.material_condition == "Good"
        assert item.risk_status == "Low"
        assert item.sample_number == "S001"
        assert item.disturbance_potential == "Low"
        assert item.labelled == "Y"
        assert item.control_priority == "P3"
        assert item.comments == "Monitor condition"


# ============================================================================
# Task 3: GreencapParser tests
# ============================================================================


class TestGreencapParser:
    """Test detection, header mapping, metadata extraction for Greencap."""

    def test_detect_greencap_marker(self):
        """Detects 'Greencap' marker in text."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        assert parser.detect("Greencap Asbestos Risk Assessment Report")

    def test_detect_non_greencap(self):
        """Returns False for non-Greencap text."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        assert not parser.detect("Prensa Pty Ltd Division 5 Assessment")
        assert not parser.detect("Some generic ACM report")

    def test_name_property(self):
        """Parser name is 'greencap'."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        assert parser.name == "greencap"

    def test_column_mapping_complete(self):
        """Column mapping contains all 14 Greencap columns mapped to raw fields."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        mapping = parser.get_column_mapping()
        assert len(mapping) == 14  # All 14 Greencap columns mapped

    def test_register_headers(self):
        """Returns the 14 expected Greencap headers."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        headers = parser.get_register_headers()
        assert len(headers) == 14
        assert "item no." in headers
        assert "risk rating" in headers

    def test_site_metadata_extraction(self):
        """Extracts site metadata (address, building size, age)."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        pages = {
            1: "Greencap\nAsbestos Risk Assessment\nFull Address: 123 Test St, Melbourne VIC\nEst. Building Size: 500m²\nEst. Building Age: 1970",
        }
        meta = parser.extract_metadata(pages)
        assert meta.consultant_name == "Greencap"
        assert meta.site_address == "123 Test St, Melbourne VIC"
        assert meta.building_size == "500m²"
        assert meta.building_age == "1970"

    def test_extract_items_from_table(self):
        """Extracts RawACMItem list from Greencap table data with all fields verified."""
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = GreencapParser()
        tables = [
            {
                "headers": ["item no.", "location - item description", "hazard type",
                            "sample no.", "item status", "photo no.", "est. extent",
                            "condition", "friability", "dist. potential", "risk rating",
                            "current label", "reinspect date", "control priority"],
                "rows": [
                    ["1", "Room 1 - Ceiling tiles", "ACM",
                     "S001", "Detected", "P1", "50m²",
                     "Good", "Non Friable", "Low", "Low",
                     "Y", "2025-01-01", "P3"],
                ],
            }
        ]
        items = parser.extract_items(tables)
        assert len(items) == 1
        item = items[0]
        assert item.product == "Ceiling tiles"
        assert item.location == "Room 1"
        assert item.material_description == "Ceiling tiles"
        assert item.result == "Detected"
        assert item.extent == "50m²"
        assert item.friable == "Non Friable"
        assert item.material_condition == "Good"
        assert item.risk_status == "Low"
        assert item.sample_number == "S001"
        assert item.disturbance_potential == "Low"
        assert item.labelled == "Y"
        assert item.control_priority == "P3"


# ============================================================================
# Task 4: GenericParser tests
# ============================================================================


class TestGenericParser:
    """Test fallback behavior and backward compatibility."""

    def test_detect_always_true(self):
        """GenericParser.detect() always returns True."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.detect("Any random text")
        assert parser.detect("")
        assert parser.detect("Prensa Pty Ltd")  # Even consultant-specific text

    def test_name_property(self):
        """Parser name is 'generic'."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.name == "generic"

    def test_column_mapping_matches_existing(self):
        """GenericParser column mapping matches the existing header map logic."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        mapping = parser.get_column_mapping()
        # Must map the standard ACM column headers to field names
        assert "product" in mapping
        assert "material description" in mapping
        assert "result" in mapping
        # Verify mapped field names
        assert mapping["product"] == "product"
        assert mapping["material description"] == "material_description"
        assert mapping["result"] == "result"

    def test_register_headers_include_required(self):
        """Register headers include all required ACM headers."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        headers = parser.get_register_headers()
        assert "product" in headers
        assert "material description" in headers
        assert "result" in headers

    def test_register_headers_include_optional(self):
        """Register headers include optional ACM headers."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        headers = parser.get_register_headers()
        assert "extent" in headers
        assert "location" in headers
        assert "friable" in headers


# ============================================================================
# Task 5: Parser Registry tests
# ============================================================================


class TestParserRegistry:
    """Test auto-selection and registry ordering."""

    def test_prensa_selected_for_prensa_text(self):
        """Registry returns PrensaParser for Prensa text."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.prensa import PrensaParser

        parser = get_parser("Report by Prensa Pty Ltd - Division 5")
        assert isinstance(parser, PrensaParser)

    def test_greencap_selected_for_greencap_text(self):
        """Registry returns GreencapParser for Greencap text."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.greencap import GreencapParser

        parser = get_parser("Greencap Asbestos Risk Assessment")
        assert isinstance(parser, GreencapParser)

    def test_generic_selected_for_unknown(self):
        """Registry returns GenericParser for unrecognized text."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = get_parser("Some unknown consultant report about ACM")
        assert isinstance(parser, GenericParser)

    def test_registry_order(self):
        """PARSER_REGISTRY has correct priority order."""
        from open_notebook.extractors.parsers import PARSER_REGISTRY
        from open_notebook.extractors.parsers.generic import GenericParser
        from open_notebook.extractors.parsers.greencap import GreencapParser
        from open_notebook.extractors.parsers.prensa import PrensaParser

        assert len(PARSER_REGISTRY) >= 3
        assert isinstance(PARSER_REGISTRY[0], PrensaParser)
        assert isinstance(PARSER_REGISTRY[1], GreencapParser)
        # GenericParser is last
        assert isinstance(PARSER_REGISTRY[-1], GenericParser)

    def test_generic_always_last(self):
        """GenericParser is always the last parser in the registry."""
        from open_notebook.extractors.parsers import PARSER_REGISTRY
        from open_notebook.extractors.parsers.generic import GenericParser

        assert isinstance(PARSER_REGISTRY[-1], GenericParser)

    def test_empty_text_gets_generic(self):
        """Empty text falls through to GenericParser."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = get_parser("")
        assert isinstance(parser, GenericParser)


# ============================================================================
# Task 6: Integration tests (backward compatibility)
# ============================================================================


class TestIntegration:
    """Test that integration with acm_extractor preserves backward compatibility."""

    @pytest.fixture
    def sample_markdown(self):
        """Standard NSW SAMP markdown content."""
        return """# Test School - Asbestos Register

## Building: B00A - Admin Block - 1924

#### Room: B00A-R0001 - Main Office - 45.5m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Tiles | Vinyl asbestos tiles | 50m² | Floor | Non Friable | Good | Low | Detected |
"""

    def test_existing_extraction_still_works(self, sample_markdown):
        """Existing extract_acm_records API produces same results after refactor."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(sample_markdown, "source:123")

        assert len(result) == 1
        record = result[0]
        assert record["source_id"] == "source:123"
        assert record["school_name"] == "Test School"
        assert record["building_id"] == "B00A"
        assert record["building_name"] == "Admin Block"
        assert record["building_year"] == 1924
        assert record["product"] == "Floor Tiles"
        assert record["material_description"] == "Vinyl asbestos tiles"
        assert record["result"] == "Positive"  # "Detected" normalized to BAR canonical

    def test_multiple_buildings_extraction(self):
        """Multi-building extraction still works after refactor."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# School

## Building: B1 - Block A

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |

## Building: B2 - Block B

| Product | Material Description | Result |
|---------|---------------------|--------|
| Lagging | Pipe wrap | Detected |
"""
        result = extract_acm_records(markdown, "source:123")

        assert len(result) == 2
        assert result[0]["building_id"] == "B1"
        assert result[1]["building_id"] == "B2"

    def test_empty_content_returns_empty(self):
        """Empty content still returns empty list."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        assert extract_acm_records("", "source:123") == []
        assert extract_acm_records(None, "source:123") == []

    def test_non_acm_tables_still_skipped(self):
        """Non-ACM tables are still skipped."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        markdown = """# Doc

| Name | Date |
|------|------|
| John | 2024 |

## Building: B1 - Block

| Product | Material Description | Result |
|---------|---------------------|--------|
| Tiles | Vinyl | Detected |
"""
        result = extract_acm_records(markdown, "source:123")
        assert len(result) == 1
        assert result[0]["product"] == "Tiles"
