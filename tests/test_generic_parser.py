"""
Tests for the config-driven GenericParser.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

import pytest


class TestGenericParserInit:
    """Test GenericParser initialization with config."""

    def test_init_with_config(self):
        from open_notebook.extractors.parsers.config_loader import load_field_schema
        from open_notebook.extractors.parsers.generic import GenericParser

        config = load_field_schema()
        parser = GenericParser(config=config)
        assert parser.name == "generic"

    def test_init_without_config_loads_default(self):
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.name == "generic"
        # Should auto-load config
        assert parser.config is not None
        assert len(parser.config.fields) == 47

    def test_detect_always_true(self):
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        assert parser.detect("Any text") is True
        assert parser.detect("") is True


class TestGenericParserColumnMapping:
    """Test config-driven column mapping."""

    def test_get_column_mapping_from_config(self):
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        mapping = parser.get_column_mapping()
        # Should map display names (lowercase) to internal names
        assert "building name" in mapping
        assert mapping["building name"] == "building_name"
        assert "specific item/acm name" in mapping
        assert mapping["specific item/acm name"] == "product"

    def test_get_register_headers_from_config(self):
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        headers = parser.get_register_headers()
        # Should return lowercase display names of active fields
        assert len(headers) == 47
        assert "building name" in headers
        assert "specific item/acm name" in headers

    def test_column_mapping_includes_backward_compat(self):
        """Backward-compatible short names still map correctly."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        mapping = parser.get_column_mapping()
        # Short names used in old generic parser headers
        assert "product" in mapping
        assert mapping["product"] == "product"
        assert "material description" in mapping
        assert mapping["material description"] == "material_description"
        assert "result" in mapping
        assert mapping["result"] == "result"


class TestGenericParserExtraction:
    """Test extract_items with different table formats."""

    def test_extract_standard_acm_table(self):
        """Standard NSW SAMP format table extraction."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        tables = [
            {
                "headers": [
                    "Product",
                    "Material Description",
                    "Extent",
                    "Location",
                    "Friable",
                    "Condition",
                    "Risk",
                    "Result",
                ],
                "rows": [
                    [
                        "Floor Tiles",
                        "Vinyl asbestos tiles",
                        "50m²",
                        "Floor",
                        "Non Friable",
                        "Good",
                        "Low",
                        "Detected",
                    ],
                ],
            }
        ]
        items = parser.extract_items(tables)
        assert len(items) == 1
        item = items[0]
        assert item.product == "Floor Tiles"
        assert item.material_description == "Vinyl asbestos tiles"

    def test_extract_skips_non_acm_table(self):
        """Non-ACM tables are skipped."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        tables = [
            {
                "headers": ["Name", "Date", "Status"],
                "rows": [["John", "2024", "Active"]],
            }
        ]
        items = parser.extract_items(tables)
        assert len(items) == 0

    def test_extract_skips_empty_product(self):
        """Rows without product are skipped."""
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        tables = [
            {
                "headers": ["Product", "Material Description", "Result"],
                "rows": [
                    ["", "Vinyl tiles", "Detected"],
                    ["Floor Tiles", "Vinyl tiles", "Detected"],
                ],
            }
        ]
        items = parser.extract_items(tables)
        assert len(items) == 1

    def test_extract_metadata(self):
        from open_notebook.extractors.parsers.generic import GenericParser

        parser = GenericParser()
        meta = parser.extract_metadata({1: "Some page"})
        assert meta.consultant_name == "Generic"


class TestGenericParserBackwardCompatibility:
    """Test that the new parser produces compatible output with existing extraction."""

    @pytest.fixture
    def sample_markdown(self):
        return """# Test School - Asbestos Register

## Building: B00A - Admin Block - 1924

#### Room: B00A-R0001 - Main Office - 45.5m²

| Product | Material Description | Extent | Location | Friable | Condition | Risk | Result |
|---------|---------------------|--------|----------|---------|-----------|------|--------|
| Floor Tiles | Vinyl asbestos tiles | 50m² | Floor | Non Friable | Good | Low | Detected |
"""

    def test_extraction_pipeline_produces_records(self, sample_markdown):
        """Full pipeline still works with new parser."""
        from open_notebook.extractors.acm_extractor import extract_acm_records

        result = extract_acm_records(sample_markdown, "source:123")
        assert len(result) == 1
        record = result[0]
        assert record["source_id"] == "source:123"
        assert record["school_name"] == "Test School"
        assert record["building_id"] == "B00A"
        assert record["product"] == "Floor Tiles"

    def test_multi_building_extraction(self):
        """Multi-building extraction still works."""
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

    def test_empty_content(self):
        from open_notebook.extractors.acm_extractor import extract_acm_records

        assert extract_acm_records("", "source:123") == []
        assert extract_acm_records(None, "source:123") == []
