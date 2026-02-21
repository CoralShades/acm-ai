"""
Unit tests for the Config-Driven Parser Framework.

Tests cover:
- ConsultantParser ABC (cannot instantiate directly)
- GenericParser config-driven behavior
- Parser module: get_parser() returns GenericParser
- Backward compatibility with existing extraction

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
(Replaces old 3-parser framework tests)
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
        expected = {
            "name",
            "detect",
            "extract_metadata",
            "extract_items",
            "get_column_mapping",
            "get_register_headers",
        }
        assert expected == abstract_methods


class TestRawACMItem:
    """Test RawACMItem dataclass."""

    def test_raw_acm_item_creation(self):
        """RawACMItem can be created with required fields."""
        from open_notebook.extractors.parsers.base import RawACMItem

        item = RawACMItem(
            product="Floor Tiles", material_description="Vinyl tiles", result="Detected"
        )
        assert item.product == "Floor Tiles"
        assert item.material_description == "Vinyl tiles"
        assert item.result == "Detected"

    def test_raw_acm_item_optional_fields(self):
        """RawACMItem optional fields default to None."""
        from open_notebook.extractors.parsers.base import RawACMItem

        item = RawACMItem(
            product="Tiles", material_description="Vinyl", result="Detected"
        )
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
    """Test DocumentMeta Pydantic model."""

    def test_document_meta_creation(self):
        """DocumentMeta can be created with consultant_name."""
        from open_notebook.extractors.parsers.base import DocumentMeta

        meta = DocumentMeta(consultant_name="Generic")
        assert meta.consultant_name == "Generic"

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
# Task 2: GenericParser tests (config-driven)
# ============================================================================


class TestGenericParser:
    """Test config-driven GenericParser behavior."""

    def test_detect_always_true(self):
        """GenericParser.detect() always returns True."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.detect("Any random text")
        assert parser.detect("")
        assert parser.detect("Prensa Pty Ltd")

    def test_name_property(self):
        """Parser name is 'generic'."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.name == "generic"

    def test_column_mapping_matches_existing(self):
        """GenericParser column mapping includes standard ACM headers."""
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

    def test_column_mapping_includes_bar_fields(self):
        """Column mapping also includes full BAR display names."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        mapping = parser.get_column_mapping()
        assert "building name" in mapping
        assert mapping["building name"] == "building_name"
        assert "specific item/acm name" in mapping
        assert mapping["specific item/acm name"] == "product"

    def test_register_headers_include_required(self):
        """Register headers include BAR field display names."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        headers = parser.get_register_headers()
        assert "building name" in headers
        assert "specific item/acm name" in headers
        assert "sample result" in headers

    def test_register_headers_count(self):
        """Register headers include all 47 BAR fields."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        headers = parser.get_register_headers()
        assert len(headers) == 47


# ============================================================================
# Task 3: Parser module tests
# ============================================================================


class TestParserModule:
    """Test parser module get_parser() function."""

    def test_get_parser_returns_generic(self):
        """get_parser() returns GenericParser for any text."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = get_parser("Report by Prensa Pty Ltd")
        assert isinstance(parser, GenericParser)

    def test_get_parser_empty_text(self):
        """get_parser() returns GenericParser for empty text."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = get_parser("")
        assert isinstance(parser, GenericParser)

    def test_get_parser_no_args(self):
        """get_parser() works without arguments."""
        from open_notebook.extractors.parsers import get_parser
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = get_parser()
        assert isinstance(parser, GenericParser)

    def test_parser_has_config(self):
        """Returned parser has loaded field config."""
        from open_notebook.extractors.parsers import get_parser

        parser = get_parser()
        assert parser.config is not None
        assert len(parser.config.fields) == 47


# ============================================================================
# Task 4: Integration tests (backward compatibility)
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
