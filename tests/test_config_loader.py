"""
Tests for SF schema configuration loader.

Story: E30-S1 — SF Schema Config Loader (V3 Foundation)

Covers AC1–AC4, AC6, AC8, AC9 from the tech spec.
"""

import os

import pytest

# Load the actual markdown content once at module level for reuse in tests.
_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "V3", "output")
_BUILDING_MD_PATH = os.path.join(_BASE_DIR, "building_fields_summary.md")
_ITEM_MD_PATH = os.path.join(_BASE_DIR, "item_fields_summary.md")

with open(_BUILDING_MD_PATH, encoding="utf-8") as _f:
    BUILDING_MD_CONTENT = _f.read()

with open(_ITEM_MD_PATH, encoding="utf-8") as _f:
    ITEM_MD_CONTENT = _f.read()


# =============================================================================
# TestSFFieldParsing — AC1, AC2
# =============================================================================


class TestSFFieldParsing:
    """Tests for markdown field table parsing."""

    def test_building_fields_count(self):
        """AC1: Assert 143 building fields parsed."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        assert len(config.fields) == 143
        assert config.total_fields == 143

    def test_building_picklist_count(self):
        """AC1: Assert 18 picklist fields in building config."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        picklist_fields = [f for f in config.fields if f.field_type == "picklist"]
        assert len(picklist_fields) == 18

    def test_building_field_keyed_by_api_name(self):
        """AC1: API Name used as key, not Label."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        api_names = {f.api_name for f in config.fields}
        assert "Building_Type__c" in api_names
        assert "Building_Category__c" in api_names
        # Label should NOT be used as the key
        assert "Asset Type" not in api_names

    def test_item_fields_count(self):
        """AC2: Assert 154 item fields parsed."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        assert len(config.fields) == 154
        assert config.total_fields == 154

    def test_item_picklist_count(self):
        """AC2: Assert 23 picklist fields in item config."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        picklist_fields = [f for f in config.fields if f.field_type == "picklist"]
        assert len(picklist_fields) == 23

    def test_dependent_picklist_detected(self):
        """AC2: ACM_Classification__c marked as dependent."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        acm_class = next(
            f for f in config.fields if f.api_name == "ACM_Classification__c"
        )
        assert acm_class.is_dependent is True
        assert acm_class.controller_field == "Friability_of_Material__c"

    def test_restricted_picklist_detected(self):
        """AC1: Building_Type__c has is_restricted_picklist=True."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        bldg_type = next(
            f for f in config.fields if f.api_name == "Building_Type__c"
        )
        assert bldg_type.is_restricted_picklist is True

    def test_boolean_column_parsing(self):
        """AC8: Nillable=False when cell is empty (blank = False)."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        # Building_Type__c has Nillable='' (empty = False/not nillable)
        bldg_type = next(
            f for f in config.fields if f.api_name == "Building_Type__c"
        )
        assert bldg_type.nillable is False

    def test_formula_field_calc_true(self):
        """AC8: Calc=True for formula fields."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        # Department__c has Calc=Y
        dept = next(f for f in config.fields if f.api_name == "Department__c")
        assert dept.calc is True

    def test_building_object_label(self):
        """AC1: Building object label parsed correctly."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(BUILDING_MD_CONTENT, "Building__c")
        assert config.object_name == "Building__c"
        assert config.object_label == "Asset Class"

    def test_item_object_metadata(self):
        """AC2: Item object metadata parsed correctly."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        config = _parse_sf_field_table(ITEM_MD_CONTENT, "Item__c")
        assert config.object_name == "Item__c"
        assert config.custom_fields == 142


# =============================================================================
# TestDependencyChains — AC3, AC4
# =============================================================================


class TestDependencyChains:
    """Tests for hardcoded dependency chain builders."""

    def test_friability_chain_values(self):
        """AC3: Friability controller has exactly 2 values."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_friability_chain,
        )

        chain = _build_friability_chain()
        assert chain.controller_api_name == "Friability_of_Material__c"
        assert chain.dependent_api_name == "ACM_Classification__c"
        assert len(chain.mapping) == 2
        assert "Non-friable" in chain.mapping
        assert "Friable" in chain.mapping

    def test_non_friable_classifications(self):
        """AC3: Non-friable has 9 valid classifications."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_friability_chain,
        )

        chain = _build_friability_chain()
        non_friable = chain.mapping["Non-friable"]
        assert len(non_friable) == 9
        assert "Cement products" in non_friable
        assert "Insulation Products" in non_friable
        assert "Textiles" in non_friable

    def test_friable_classifications(self):
        """AC3: Friable has 9 valid classifications (with (f) suffix)."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_friability_chain,
        )

        chain = _build_friability_chain()
        friable = chain.mapping["Friable"]
        assert len(friable) == 9
        assert "Cement products (f)" in friable
        assert "Insulation products (f)" in friable

    def test_classification_to_subclassification_cement(self):
        """AC3: Cement products has correct product types."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_acm_classification_chain,
        )

        chain = _build_acm_classification_chain()
        cement_types = chain.mapping["Cement products"]
        assert "Corrugated Roof Sheeting" in cement_types
        assert "Flat Sheeting" in cement_types
        assert "Weatherboards" in cement_types

    def test_classification_to_subclassification_insulation_friable(self):
        """AC3: Insulation products (f) includes AIB."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_acm_classification_chain,
        )

        chain = _build_acm_classification_chain()
        insulation_f = chain.mapping["Insulation products (f)"]
        assert "AIB (Asbestos Insulated Board)" in insulation_f
        assert "Lagging" in insulation_f

    def test_acm_classification_chain_has_18_groups(self):
        """AC3: ACM classification chain covers all 18 product groups."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_acm_classification_chain,
        )

        chain = _build_acm_classification_chain()
        assert len(chain.mapping) == 18

    def test_building_type_chain_category_count(self):
        """AC4: Exactly 13 unique Building_Category__c values."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        assert chain.controller_api_name == "Building_Type__c"
        assert chain.dependent_api_name == "Building_Category__c"
        unique_categories = set(chain.mapping.values())
        assert len(unique_categories) == 13

    def test_building_type_school_category(self):
        """AC4: School building type maps to Educational and training facilities."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        assert chain.mapping["School"] == "Educational and training facilities"

    def test_building_type_hospital_category(self):
        """AC4: Hospital maps to Health services."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        assert chain.mapping["Hospital"] == "Health services"

    def test_building_type_total_values(self):
        """AC4: All building types from source data have a category assignment."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        # Source data has 137 building types (not 114 as originally estimated)
        assert len(chain.mapping) == 137

    def test_building_type_transport_category(self):
        """AC4: Train station maps to Transport."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        assert chain.mapping["Train station"] == "Transport"

    def test_building_type_agriculture_category(self):
        """AC4: Farm annexe maps to Agriculture."""
        from open_notebook.extractors.parsers.config_loader import (
            _build_building_type_chain,
        )

        chain = _build_building_type_chain()
        assert chain.mapping["Farm annexe"] == "Agriculture"


# =============================================================================
# TestSFSchemaLoader — AC6
# =============================================================================


class TestSFSchemaLoader:
    """Tests for the top-level load_sf_field_schema() function."""

    def test_load_returns_schema_bundle(self):
        """AC6: load_sf_field_schema returns SFSchemaBundle."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )
        from open_notebook.extractors.parsers.field_config import SFSchemaBundle

        bundle = load_sf_field_schema()
        assert isinstance(bundle, SFSchemaBundle)
        assert bundle.version == "salesforce-v1"

    def test_load_is_cached(self):
        """AC6: Second call returns same object (in-memory cache)."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )

        bundle1 = load_sf_field_schema()
        bundle2 = load_sf_field_schema()
        assert bundle1 is bundle2

    def test_bundle_has_three_dependency_chains(self):
        """AC3+AC4: Bundle contains all three dependency chains."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )

        bundle = load_sf_field_schema()
        chain_controllers = {c.controller_api_name for c in bundle.dependencies}
        assert "Friability_of_Material__c" in chain_controllers
        assert "ACM_Classification__c" in chain_controllers
        assert "Building_Type__c" in chain_controllers

    def test_bundle_building_fields_count(self):
        """AC1+AC6: Bundle building_fields has 143 fields."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )

        bundle = load_sf_field_schema()
        assert len(bundle.building_fields.fields) == 143

    def test_bundle_item_fields_count(self):
        """AC2+AC6: Bundle item_fields has 154 fields."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )

        bundle = load_sf_field_schema()
        assert len(bundle.item_fields.fields) == 154

    def test_bundle_has_picklists(self):
        """AC6: Bundle combined picklists are populated."""
        from open_notebook.extractors.parsers.config_loader import (
            load_sf_field_schema,
        )

        bundle = load_sf_field_schema()
        assert "Building_Type__c" in bundle.picklists
        assert "Friability_of_Material__c" in bundle.picklists
        assert len(bundle.picklists["Friability_of_Material__c"]) == 2


# =============================================================================
# TestSFSchemaEdgeCases — AC8
# =============================================================================


class TestSFSchemaEdgeCases:
    """Tests for edge case handling in the SF schema parser."""

    def test_malformed_row_missing_column(self):
        """AC8: Malformed row (wrong number of columns) is skipped with warning."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        malformed_md = (
            "# Test__c — Field Reference\n"
            "\n"
            "**Object:** Test__c (label: Test)\n"
            "**Total fields:** 1  **Custom fields:** 1  **Picklist fields:** 0\n"
            "\n"
            "## Field Table\n"
            "\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc"
            " | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------"
            "|------------|-------|\n"
            "| 1 | Missing_Columns__c | Too Short |\n"
            "| 2 | Valid_Field__c | Valid Label | string | 255 | Y | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(malformed_md, "Test__c")
        # Malformed row is skipped; valid row is parsed
        assert len(config.fields) == 1
        assert config.fields[0].api_name == "Valid_Field__c"

    def test_empty_picklist_section(self):
        """AC8: Object with 0 picklist fields produces empty picklists dict."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        no_picklist_md = (
            "# Test__c — Field Reference\n"
            "\n"
            "**Object:** Test__c (label: Test)\n"
            "**Total fields:** 1  **Custom fields:** 1  **Picklist fields:** 0\n"
            "\n"
            "## Field Table\n"
            "\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc"
            " | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------"
            "|------------|-------|\n"
            "| 1 | Name__c | Name | string | 255 | Y | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(no_picklist_md, "Test__c")
        assert config.picklists == {}
        assert config.picklist_fields == 0

    def test_missing_source_file_raises(self):
        """AC8: Missing source file raises SFSchemaLoadError (not FileNotFoundError)."""
        from open_notebook.extractors.parsers.config_loader import (
            SFSchemaLoadError,
            _parse_sf_field_table_from_path,
        )

        with pytest.raises(SFSchemaLoadError):
            _parse_sf_field_table_from_path("/nonexistent/path/missing.md", "Test__c")

    def test_empty_cell_length_is_none(self):
        """AC8: Empty Length cell parses to None."""
        from open_notebook.extractors.parsers.config_loader import (
            _parse_sf_field_table,
        )

        row_md = (
            "# Test__c — Field Reference\n"
            "\n"
            "**Object:** Test__c (label: Test)\n"
            "**Total fields:** 1  **Custom fields:** 0  **Picklist fields:** 0\n"
            "\n"
            "## Field Table\n"
            "\n"
            "| # | API Name | Label | Type | Length | Nillable | Custom | Calc"
            " | Updateable | Notes |\n"
            "|---|----------|-------|------|--------|----------|--------|------"
            "|------------|-------|\n"
            "| 1 | Boolean_Field__c | Boolean | boolean |  |  | Y |  | Y |  |\n"
        )
        config = _parse_sf_field_table(row_md, "Test__c")
        assert config.fields[0].length is None
        assert config.fields[0].nillable is False  # Empty = False


# =============================================================================
# TestItemNameLookup — AC9
# =============================================================================


class TestItemNameLookup:
    """Tests for Item_Name__c product group lookup helper."""

    def test_item_names_for_cement_products(self):
        """AC9: Returns known cement product item names."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Cement products")
        assert "Ceiling" in names or "Wall(s)" in names
        assert len(names) > 10

    def test_item_names_for_insulation(self):
        """AC9: Returns item names for insulation group."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Insulation Products")
        assert "Insulation" in names
        assert "Boiler" in names

    def test_item_names_for_insulation_friable(self):
        """AC9: Returns item names for friable insulation group (same as non-friable)."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Insulation products (f)")
        # Should resolve to same Insulation Products group
        assert len(names) > 0

    def test_item_names_unknown_group_returns_empty(self):
        """AC9: Unknown product group returns empty list."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("NonExistentGroup")
        assert names == []

    def test_item_names_total_coverage(self):
        """AC9: ITEM_NAME_TO_PRODUCT_GROUP dict has sufficient coverage."""
        from open_notebook.extractors.parsers.config_loader import (
            ITEM_NAME_TO_PRODUCT_GROUP,
        )

        # The dict must have at least 100 unique item names (conservative bound
        # to avoid brittle exact count while still ensuring comprehensive coverage)
        assert len(ITEM_NAME_TO_PRODUCT_GROUP) >= 100

    def test_get_item_names_sorted(self):
        """AC9: Result is sorted alphabetically."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Cement products")
        assert names == sorted(names)

    def test_item_names_for_vinyl_products(self):
        """AC9: Returns item names for vinyl products group."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Vinyl products")
        # Floor covering items map to vinyl
        assert "Floor covering" in names or "Flooring" in names

    def test_item_names_for_other(self):
        """AC9: Returns item names for Other group."""
        from open_notebook.extractors.parsers.config_loader import (
            get_item_names_by_product_group,
        )

        names = get_item_names_by_product_group("Other")
        assert "Other" in names
        assert "Unknown" in names
