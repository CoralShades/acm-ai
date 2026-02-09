"""
Tests for field schema configuration models and loader.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

import pytest

# ============================================================================
# Task 1: Config model tests
# ============================================================================


class TestFieldDef:
    """Test FieldDef Pydantic model."""

    def test_create_field_def_with_required_fields(self):
        from open_notebook.extractors.parsers.field_config import FieldDef

        field = FieldDef(
            internal_name="building_name",
            display_name="Building Name",
            excel_column="E",
            col_index=5,
            field_type="string",
            required=True,
        )
        assert field.internal_name == "building_name"
        assert field.display_name == "Building Name"
        assert field.excel_column == "E"
        assert field.col_index == 5
        assert field.field_type == "string"
        assert field.required is True

    def test_field_def_defaults(self):
        from open_notebook.extractors.parsers.field_config import FieldDef

        field = FieldDef(
            internal_name="test",
            display_name="Test",
            excel_column="A",
            col_index=1,
            field_type="string",
            required=False,
        )
        assert field.active is True
        assert field.enum_name is None
        assert field.group is None

    def test_field_def_with_enum(self):
        from open_notebook.extractors.parsers.field_config import FieldDef

        field = FieldDef(
            internal_name="sample_result",
            display_name="Sample Result",
            excel_column="AE",
            col_index=31,
            field_type="enum",
            required=True,
            enum_name="SampleResult",
            group="acm_details",
        )
        assert field.enum_name == "SampleResult"
        assert field.group == "acm_details"


class TestBusinessRule:
    """Test BusinessRule Pydantic model."""

    def test_create_business_rule(self):
        from open_notebook.extractors.parsers.field_config import BusinessRule

        rule = BusinessRule(
            rule_id="negative_clears_condition",
            description="When Sample Result is Negative, set Condition to N/A",
        )
        assert rule.rule_id == "negative_clears_condition"
        assert rule.enabled is True

    def test_business_rule_disabled(self):
        from open_notebook.extractors.parsers.field_config import BusinessRule

        rule = BusinessRule(
            rule_id="test_rule",
            description="Test",
            enabled=False,
        )
        assert rule.enabled is False


class TestFieldSchemaConfig:
    """Test FieldSchemaConfig Pydantic model."""

    def test_create_config(self):
        from open_notebook.extractors.parsers.field_config import (
            BusinessRule,
            FieldDef,
            FieldSchemaConfig,
        )

        config = FieldSchemaConfig(
            fields=[
                FieldDef(
                    internal_name="building_name",
                    display_name="Building Name",
                    excel_column="E",
                    col_index=5,
                    field_type="string",
                    required=True,
                ),
            ],
            enums={"SampleResult": ["Positive", "Negative"]},
            business_rules=[
                BusinessRule(
                    rule_id="test",
                    description="Test rule",
                ),
            ],
            version="1.0.0",
        )
        assert len(config.fields) == 1
        assert "SampleResult" in config.enums
        assert len(config.business_rules) == 1
        assert config.version == "1.0.0"
        assert config.source_template is None

    def test_display_name_to_internal_name_map(self):
        """Helper method maps display names to internal names."""
        from open_notebook.extractors.parsers.field_config import (
            FieldDef,
            FieldSchemaConfig,
        )

        config = FieldSchemaConfig(
            fields=[
                FieldDef(
                    internal_name="building_name",
                    display_name="Building Name",
                    excel_column="E",
                    col_index=5,
                    field_type="string",
                    required=True,
                ),
                FieldDef(
                    internal_name="product",
                    display_name="Specific Item/ACM Name",
                    excel_column="X",
                    col_index=24,
                    field_type="string",
                    required=True,
                ),
            ],
            enums={},
            business_rules=[],
            version="1.0.0",
        )
        mapping = config.get_display_to_internal_map()
        assert mapping["Building Name"] == "building_name"
        assert mapping["Specific Item/ACM Name"] == "product"

    def test_excel_column_to_internal_name_map(self):
        """Helper method maps BAR column letters to internal names."""
        from open_notebook.extractors.parsers.field_config import (
            FieldDef,
            FieldSchemaConfig,
        )

        config = FieldSchemaConfig(
            fields=[
                FieldDef(
                    internal_name="building_name",
                    display_name="Building Name",
                    excel_column="E",
                    col_index=5,
                    field_type="string",
                    required=True,
                ),
            ],
            enums={},
            business_rules=[],
            version="1.0.0",
        )
        mapping = config.get_column_to_internal_map()
        assert mapping["E"] == "building_name"

    def test_active_fields_only(self):
        """get_active_fields returns only fields with active=True."""
        from open_notebook.extractors.parsers.field_config import (
            FieldDef,
            FieldSchemaConfig,
        )

        config = FieldSchemaConfig(
            fields=[
                FieldDef(
                    internal_name="active_field",
                    display_name="Active",
                    excel_column="A",
                    col_index=1,
                    field_type="string",
                    required=False,
                    active=True,
                ),
                FieldDef(
                    internal_name="inactive_field",
                    display_name="Inactive",
                    excel_column="B",
                    col_index=2,
                    field_type="string",
                    required=False,
                    active=False,
                ),
            ],
            enums={},
            business_rules=[],
            version="1.0.0",
        )
        active = config.get_active_fields()
        assert len(active) == 1
        assert active[0].internal_name == "active_field"


# ============================================================================
# Task 2: Config loader tests
# ============================================================================


class TestConfigLoader:
    """Test loading field schema from JSON files."""

    def test_load_field_schema_from_json(self):
        """Loads config from actual JSON files, producing 47 fields."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        assert len(config.fields) == 47

    def test_loaded_config_has_correct_version(self):
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        assert config.version == "1.0.0"

    def test_loaded_fields_have_internal_names(self):
        """Every field has a non-empty internal_name."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        for field in config.fields:
            assert field.internal_name, (
                f"Field {field.display_name} has no internal_name"
            )

    def test_loaded_fields_have_column_letters(self):
        """Every field has a BAR column letter."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        for field in config.fields:
            assert field.excel_column, (
                f"Field {field.internal_name} has no excel_column"
            )

    def test_loaded_enums_present(self):
        """Config contains enum picklists from register_enums.json."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        assert "SampleResult" in config.enums
        assert "Condition" in config.enums
        assert "DisturbancePotential" in config.enums
        assert "Friability" in config.enums

    def test_enum_values_correct(self):
        """SampleResult enum has expected BAR values."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        sr = config.enums["SampleResult"]
        assert "Positive" in sr
        assert "Negative" in sr
        assert "Assumed Positive" in sr
        assert "Assumed Negative" in sr

    def test_business_rules_loaded(self):
        """Config includes business rules."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        assert len(config.business_rules) >= 4
        rule_ids = [r.rule_id for r in config.business_rules]
        assert "negative_clears_condition" in rule_ids
        assert "negative_clears_disturbance" in rule_ids

    def test_display_name_mapping_covers_key_fields(self):
        """Key ACM fields are mapped correctly."""
        from open_notebook.extractors.parsers.config_loader import load_field_schema

        config = load_field_schema()
        mapping = config.get_display_to_internal_map()
        assert mapping["Building Name"] == "building_name"
        assert mapping["Specific Item/ACM Name"] == "product"
        assert mapping["Sample Result"] == "sample_result"
        assert mapping["Room or Area"] == "room_name"
        assert mapping["Internal / External"] == "area_type"

    def test_config_caching(self):
        """load_field_schema returns cached config on second call."""
        from open_notebook.extractors.parsers import config_loader

        # Reset cache
        config_loader._FIELD_SCHEMA = None
        config1 = config_loader.load_field_schema()
        config2 = config_loader.load_field_schema()
        assert config1 is config2  # Same object (cached)

    def test_graceful_fallback_on_missing_files(self):
        """Returns a default config if JSON files are missing."""
        from open_notebook.extractors.parsers import config_loader

        # Reset cache and temp override path
        config_loader._FIELD_SCHEMA = None
        original_path = config_loader.CONFIG_DIR
        config_loader.CONFIG_DIR = "/nonexistent/path"
        try:
            config = config_loader.load_field_schema()
            # Should return a non-empty default config
            assert len(config.fields) > 0
        finally:
            config_loader.CONFIG_DIR = original_path
            config_loader._FIELD_SCHEMA = None  # Reset cache
