"""Tests for Multi-Consultant Story 5: Format-Agnostic Prompts.

Verifies that:
1. building_inventory.jinja renders format-specific sections based on detected_format
2. row_extraction.jinja renders dynamic extraction_fields when provided
3. row_extraction.jinja renders default 13 fields when no extraction_fields provided
4. v3_building_extraction.jinja shows format-appropriate worked example
5. Format example YAML files are valid and loadable
6. build_extraction_fields() produces correct output from InferredSchema
7. InferredSchema.detected_format field works correctly
"""

from pathlib import Path

import pytest
import yaml
from ai_prompter import Prompter

from open_notebook.extractors.schema_inference import (
    InferredSchema,
    build_extraction_fields,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render(template_name: str, data: dict) -> str:
    """Render a Jinja template from prompts/acm/."""
    return Prompter(prompt_template=f"acm/{template_name}").render(data=data)


# ---------------------------------------------------------------------------
# building_inventory.jinja — format-conditional sections
# ---------------------------------------------------------------------------


class TestBuildingInventoryPrompt:
    """Test building_inventory.jinja format-conditional rendering."""

    def test_standard_format(self):
        result = _render("building_inventory", {"detected_format": "standard"})
        assert "Standard DET Format" in result
        assert "B###-R####" in result or "section headers with coded IDs" in result
        assert "Pipe-Table Format" not in result
        assert "ARA Text-Header Format" not in result

    def test_ara_format(self):
        result = _render("building_inventory", {"detected_format": "ara"})
        assert "ARA Text-Header Format" in result
        assert "Building Name:" in result
        assert "Standard DET Format" not in result
        assert "Pipe-Table Format" not in result

    def test_pipe_table_format(self):
        result = _render("building_inventory", {"detected_format": "pipe_table"})
        assert "Pipe-Table Format" in result
        assert "| Building Name:" in result
        assert "Standard DET Format" not in result
        assert "ARA Text-Header Format" not in result

    def test_unknown_format_shows_all(self):
        result = _render("building_inventory", {"detected_format": "unknown"})
        assert "Unknown Format" in result
        assert "coded building IDs" in result
        assert "Building Name:" in result

    def test_none_format_shows_all(self):
        """When detected_format is None (backward compat), show generic guidance."""
        result = _render("building_inventory", {})
        assert "Unknown Format" in result or "Check All Patterns" in result

    def test_format_name_fallback(self):
        """Template also accepts format_name (from document_metadata)."""
        result = _render("building_inventory", {"format_name": "ara"})
        assert "ARA Text-Header Format" in result

    def test_detected_format_overrides_format_name(self):
        """detected_format takes precedence over format_name."""
        result = _render("building_inventory", {
            "detected_format": "standard",
            "format_name": "ara",
        })
        assert "Standard DET Format" in result
        assert "ARA Text-Header Format" not in result

    def test_metadata_context_preserved(self):
        """Existing metadata fields still render correctly."""
        result = _render("building_inventory", {
            "site_name": "Test Site",
            "consultant_name": "Test Consultant",
            "detected_format": "standard",
        })
        assert "Test Site" in result
        assert "Test Consultant" in result


# ---------------------------------------------------------------------------
# row_extraction.jinja — dynamic extraction_fields
# ---------------------------------------------------------------------------


class TestRowExtractionPrompt:
    """Test row_extraction.jinja dynamic field rendering."""

    def test_default_fields_when_no_extraction_fields(self):
        """Default 13 fields rendered when no extraction_fields provided."""
        result = _render("row_extraction", {})
        assert "room_name" in result
        assert "item_name" in result
        assert "friability" in result
        assert "sample_result" in result
        assert "internal_external" in result

    def test_dynamic_fields_rendered(self):
        """Custom extraction_fields override the default schema."""
        fields = [
            {"name": "item_name", "description": "Material name (PDF column: 'Material')"},
            {"name": "room_name", "description": "Room (PDF column: 'Location')"},
            {"name": "condition", "description": "Condition (PDF column: 'State')"},
        ]
        result = _render("row_extraction", {"extraction_fields": fields})
        assert "PDF column: 'Material'" in result
        assert "PDF column: 'Location'" in result
        assert "PDF column: 'State'" in result
        # Default descriptions should NOT appear
        assert "Internal or External" not in result

    def test_empty_extraction_fields_uses_default(self):
        """Empty list falls through to default fields."""
        result = _render("row_extraction", {"extraction_fields": []})
        assert "room_name" in result
        assert "internal_external" in result


# ---------------------------------------------------------------------------
# v3_building_extraction.jinja — format-conditional examples
# ---------------------------------------------------------------------------


class TestV3BuildingExtractionPrompt:
    """Test v3_building_extraction.jinja format-conditional examples."""

    def _render_with_stubs(self, detected_format=None):
        """Render v3_building_extraction with minimal stub data."""
        return _render("v3_building_extraction", {
            "building_context": {
                "building_id": "B001",
                "building_name": "Test Building",
                "page_start": 1,
                "page_end": 5,
            },
            "picklists": {
                "building_type_options": "Option1, Option2",
                "building_category_options": "Cat1, Cat2",
                "frequency_of_use_options": "Daily, Weekly",
                "estimated_year_built_note": "4-digit year",
            },
            "detected_format": detected_format,
        })

    def test_ara_format_shows_ara_example(self):
        result = self._render_with_stubs("ara")
        assert "ARA Text-Header Format" in result
        assert "Broadmeadows Police Complex" in result
        assert "Standard DET Format" not in result

    def test_pipe_table_format_shows_pipe_example(self):
        result = self._render_with_stubs("pipe_table")
        assert "Pipe-Table Format" in result
        assert "Eastern Community Centre" in result or "Greencap" in result
        assert "ARA Text-Header Format" not in result

    def test_standard_format_shows_det_example(self):
        result = self._render_with_stubs("standard")
        assert "Standard DET Format" in result
        assert "Reservoir Primary School" in result or "Main Classroom Block" in result

    def test_none_format_shows_default(self):
        """When no detected_format, standard DET example is shown (backward compat)."""
        result = self._render_with_stubs(None)
        assert "Standard DET Format" in result

    def test_unknown_format_shows_default(self):
        result = self._render_with_stubs("unknown")
        assert "Standard DET Format" in result


# ---------------------------------------------------------------------------
# Format example YAML files — validity
# ---------------------------------------------------------------------------


class TestFormatExampleYAMLFiles:
    """Verify format example YAML files are valid and loadable."""

    EXAMPLES_DIR = Path(__file__).parent.parent / "prompts" / "acm" / "format_examples"

    @pytest.mark.parametrize("filename", ["standard.yaml", "ara.yaml", "pipe_table.yaml"])
    def test_yaml_file_exists_and_loads(self, filename):
        path = self.EXAMPLES_DIR / filename
        assert path.exists(), f"{filename} not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "format_name" in data
        assert "building_detection" in data
        assert "item_extraction" in data

    @pytest.mark.parametrize("filename,expected_format", [
        ("standard.yaml", "standard"),
        ("ara.yaml", "ara"),
        ("pipe_table.yaml", "pipe_table"),
    ])
    def test_yaml_format_name_matches(self, filename, expected_format):
        path = self.EXAMPLES_DIR / filename
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["format_name"] == expected_format


# ---------------------------------------------------------------------------
# build_extraction_fields() — schema to field list
# ---------------------------------------------------------------------------


class TestBuildExtractionFields:
    """Test build_extraction_fields() from InferredSchema."""

    def test_returns_fields_from_schema_mapping(self):
        schema = InferredSchema(
            column_mapping={
                "Room/Area": "Room_or_Area__c",
                "Material": "Item_Name__c",
                "Condition": "Condition__c",
                "Sample No": "NATA_Endorsed_Sample_no__c",
                "Result": "Sample_Analysis_Result_Material_Status__c",
            },
            canonical_mapping={},
        )
        fields = build_extraction_fields(schema)
        assert len(fields) > 0
        field_names = [f["name"] for f in fields]
        assert "room_name" in field_names
        assert "item_name" in field_names
        assert "condition" in field_names
        assert "sample_number" in field_names
        assert "sample_result" in field_names

    def test_includes_pdf_header_in_description(self):
        schema = InferredSchema(
            column_mapping={
                "F/NF": "Friability_of_Material__c",
                "Material": "Item_Name__c",
                "Room/Area": "Room_or_Area__c",
                "Condition": "Condition__c",
                "Result": "Sample_Analysis_Result_Material_Status__c",
            },
            canonical_mapping={},
        )
        fields = build_extraction_fields(schema)
        friability_field = next(f for f in fields if f["name"] == "friability")
        assert "F/NF" in friability_field["description"]

    def test_empty_mapping_returns_empty(self):
        schema = InferredSchema(
            column_mapping={},
            canonical_mapping={},
        )
        fields = build_extraction_fields(schema)
        assert fields == []

    def test_too_few_mappings_returns_empty(self):
        """If only 1-2 fields map, return empty (use defaults instead)."""
        schema = InferredSchema(
            column_mapping={"Material": "Item_Name__c"},
            canonical_mapping={},
        )
        fields = build_extraction_fields(schema)
        assert fields == []

    def test_always_includes_core_fields(self):
        """Core fields (item_name, room_name, sample_result) always present."""
        schema = InferredSchema(
            column_mapping={
                "Condition": "Condition__c",
                "F/NF": "Friability_of_Material__c",
                "DP": "Disturbance_Potential__c",
                "Location": "Specific_Location__c",
            },
            canonical_mapping={},
        )
        fields = build_extraction_fields(schema)
        field_names = [f["name"] for f in fields]
        assert "item_name" in field_names
        assert "room_name" in field_names
        assert "sample_result" in field_names


# ---------------------------------------------------------------------------
# InferredSchema.detected_format field
# ---------------------------------------------------------------------------


class TestInferredSchemaDetectedFormat:
    """Test InferredSchema.detected_format field."""

    def test_default_is_none(self):
        schema = InferredSchema(
            column_mapping={},
            canonical_mapping={},
        )
        assert schema.detected_format is None

    def test_can_set_detected_format(self):
        schema = InferredSchema(
            column_mapping={},
            canonical_mapping={},
            detected_format="ara",
        )
        assert schema.detected_format == "ara"

    def test_all_format_values(self):
        for fmt in ("standard", "ara", "pipe_table", "unknown"):
            schema = InferredSchema(
                column_mapping={},
                canonical_mapping={},
                detected_format=fmt,
            )
            assert schema.detected_format == fmt
