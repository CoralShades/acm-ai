"""
Unit tests for prompt_context_builder.py.

Tests build_picklist_context(), _select_item_name_groups(), and related helpers.

Story: E30-S7 Two-Phase Extraction Prompts
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from open_notebook.extractors.prompt_context_builder import (
    _format_picklist,
    _select_item_name_groups,
    build_picklist_context,
)

# ---------------------------------------------------------------------------
# Helpers to build mock schema bundle
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = [
    "building_type_options",
    "building_category_options",
    "frequency_of_use_options",
    "estimated_year_built_note",
    "friability_options",
    "acm_classification_options",
    "acm_sub_classification_options",
    "item_name_options",
    "condition_options",
    "disturbance_potential_options",
    "sample_result_options",
    "internal_external_options",
    "labelled_options",
]


def _make_mock_bundle(picklists: dict | None = None) -> MagicMock:
    """Create a minimal mock SFSchemaBundle with specified picklists."""
    bundle = MagicMock()
    bundle.picklists = picklists or {}
    return bundle


# ---------------------------------------------------------------------------
# _select_item_name_groups
# ---------------------------------------------------------------------------


class TestSelectItemNameGroups:
    """Tests for _select_item_name_groups() item name subsetting logic."""

    def test_cement_products_group(self):
        """Cement products returns ceiling/wall/roof/eave items."""
        result = _select_item_name_groups("Cement products")
        assert "Ceiling" in result
        assert "Roof" in result
        assert "Wall(s)" in result
        assert "Eave lining" in result

    def test_cement_products_friable(self):
        """Cement products (f) returns same set as non-friable."""
        result_nf = _select_item_name_groups("Cement products")
        result_f = _select_item_name_groups("Cement products (f)")
        # Both should contain the same base items (before catch-alls)
        assert "Ceiling" in result_f
        assert "Roof" in result_f
        assert "Wall(s)" in result_f
        # Core items should be identical between friable and non-friable
        for item in result_nf:
            if item not in ["Other", "Unknown", "Debris", "Dust", "Dust and debris"]:
                assert item in result_f

    def test_vinyl_products_group(self):
        """Vinyl products returns floor covering, skirting, beneath floor covering."""
        result = _select_item_name_groups("Vinyl products")
        assert "Floor covering" in result
        assert "Skirting" in result
        assert "Beneath floor covering" in result

    def test_vinyl_products_friable(self):
        """Vinyl products (f) returns floor items."""
        result = _select_item_name_groups("Vinyl products (f)")
        assert "Floor covering" in result
        assert "Skirting" in result

    def test_insulation_group(self):
        """Insulation Products returns pipework, ductwork, boiler items."""
        result = _select_item_name_groups("Insulation Products")
        assert "Pipework insulation" in result
        assert "Ductwork insulation" in result
        assert "Boiler" in result

    def test_insulation_group_friable(self):
        """Insulation products (f) returns insulation items."""
        result = _select_item_name_groups("Insulation products (f)")
        assert "Pipework insulation" in result
        assert "Ductwork insulation" in result

    def test_gasket_group(self):
        """Gasket group returns gasket/flange/expansion items."""
        result = _select_item_name_groups("Gasket, friction products and adhesives")
        assert "Gasket(s)" in result
        assert "Flange joints" in result
        assert "Expansion joint" in result

    def test_gasket_group_friable(self):
        """Gasket (f) group returns same items."""
        result = _select_item_name_groups("Gasket, friction products and adhesives (f)")
        assert "Gasket(s)" in result
        assert "Expansion joint" in result

    def test_coating_group(self):
        """Coatings group returns textured coating, render, plaster."""
        result = _select_item_name_groups("Coatings")
        assert "Textured coating" in result
        assert "Render" in result
        assert "Plaster" in result

    def test_coating_group_friable(self):
        """Coatings (f) group returns coating items."""
        result = _select_item_name_groups("Coatings (f)")
        assert "Textured coating" in result
        assert "Plaster" in result

    def test_none_classification(self):
        """None classification returns union of top 4 groups (cement + vinyl + insulation + gasket)."""
        result = _select_item_name_groups(None)
        # Should include items from all 4 default groups
        assert "Ceiling" in result  # cement
        assert "Floor covering" in result  # vinyl
        assert "Pipework insulation" in result  # insulation
        assert "Gasket(s)" in result  # gasket

    def test_unknown_classification(self):
        """Unknown/Other classification returns default groups."""
        result_other = _select_item_name_groups("Other")
        result_none = _select_item_name_groups(None)
        # Both should include items from all default groups
        assert "Ceiling" in result_other
        assert "Floor covering" in result_other
        assert "Pipework insulation" in result_other

    def test_always_includes_other(self):
        """Every group result includes 'Other' and 'Unknown' catch-all values."""
        for classification in [
            "Cement products",
            "Vinyl products",
            "Insulation Products",
            "Gasket, friction products and adhesives",
            "Coatings",
            None,
        ]:
            result = _select_item_name_groups(classification)
            assert "Other" in result, f"'Other' missing for {classification!r}"
            assert "Unknown" in result, f"'Unknown' missing for {classification!r}"

    def test_no_duplicates(self):
        """len(result) == len(set(result)) — no duplicate Item_Name values."""
        for classification in [
            "Cement products",
            "Cement products (f)",
            "Vinyl products",
            "Vinyl products (f)",
            "Insulation Products",
            "Insulation products (f)",
            "Gasket, friction products and adhesives",
            "Gasket, friction products and adhesives (f)",
            "Coatings",
            "Coatings (f)",
            None,
        ]:
            result = _select_item_name_groups(classification)
            assert len(result) == len(set(result)), (
                f"Duplicates found for {classification!r}: "
                f"{[x for x in result if result.count(x) > 1]}"
            )

    def test_cement_does_not_include_vinyl_items(self):
        """Cement group should not include vinyl floor items."""
        result = _select_item_name_groups("Cement products")
        assert "Floor covering" not in result
        assert "Skirting" not in result

    def test_vinyl_does_not_include_insulation_items(self):
        """Vinyl group should not include insulation items."""
        result = _select_item_name_groups("Vinyl products")
        assert "Pipework insulation" not in result
        assert "Ductwork insulation" not in result


# ---------------------------------------------------------------------------
# build_picklist_context
# ---------------------------------------------------------------------------


class TestBuildPicklistContext:
    """Tests for build_picklist_context() picklist injection."""

    def test_returns_required_keys(self):
        """Dict contains all 13 expected keys."""
        picklists = build_picklist_context(schema_bundle=None)
        for key in _REQUIRED_KEYS:
            assert key in picklists, f"Missing key: {key}"

    def test_all_values_are_strings(self):
        """All returned values are strings (newline-joined)."""
        picklists = build_picklist_context(schema_bundle=None)
        for key, value in picklists.items():
            assert isinstance(value, str), (
                f"Key {key!r} returned non-string: {type(value)}"
            )

    def test_friability_options(self):
        """Contains 'Non-friable' and 'Friable'."""
        picklists = build_picklist_context(schema_bundle=None)
        assert "Non-friable" in picklists["friability_options"]
        assert "Friable" in picklists["friability_options"]

    def test_condition_options(self):
        """Contains 'Stable', 'Poor', 'Fair', 'N/A (negative)'."""
        picklists = build_picklist_context(schema_bundle=None)
        cond = picklists["condition_options"]
        assert "Stable" in cond
        assert "Poor" in cond
        assert "Fair" in cond
        assert "N/A (negative)" in cond

    def test_sample_result_options(self):
        """Contains all 5 Sample_Analysis_Result_Material_Status__c values."""
        picklists = build_picklist_context(schema_bundle=None)
        sr = picklists["sample_result_options"]
        assert "Positive" in sr
        assert "Assumed Positive" in sr
        assert "Negative" in sr
        assert "Assumed Negative" in sr
        assert "Negative - Treated as Positive" in sr

    def test_internal_external_options(self):
        """Contains 'Internal', 'External', 'External & Internal'."""
        picklists = build_picklist_context(schema_bundle=None)
        ie = picklists["internal_external_options"]
        assert "Internal" in ie
        assert "External" in ie
        assert "External & Internal" in ie

    def test_labelled_options(self):
        """Contains 'Yes' and 'No'."""
        picklists = build_picklist_context(schema_bundle=None)
        lbl = picklists["labelled_options"]
        assert "Yes" in lbl
        assert "No" in lbl

    def test_estimated_year_built_note(self):
        """Returns string with '1700' and '2029' (range note, not all 230 years)."""
        picklists = build_picklist_context(schema_bundle=None)
        note = picklists["estimated_year_built_note"]
        assert "1700" in note
        assert "2029" in note
        # Should NOT be a massive list of years
        assert len(note) < 200

    def test_item_name_subsets_by_classification(self):
        """When acm_classification='Vinyl products', item_name_options contains 'Floor covering'."""
        picklists = build_picklist_context(
            schema_bundle=None, acm_classification="Vinyl products"
        )
        assert "Floor covering" in picklists["item_name_options"]

    def test_vinyl_does_not_contain_insulation(self):
        """Vinyl classification should not include insulation items in item_name_options."""
        picklists = build_picklist_context(
            schema_bundle=None, acm_classification="Vinyl products"
        )
        # Insulation items should NOT be in vinyl subset
        assert "Pipework insulation" not in picklists["item_name_options"]

    def test_item_name_default_without_classification(self):
        """Without classification, returns ~100 items from top 4 groups."""
        picklists = build_picklist_context(schema_bundle=None, acm_classification=None)
        item_options = picklists["item_name_options"]
        # Should contain items from cement, vinyl, insulation, gasket groups
        assert "Ceiling" in item_options  # cement
        assert "Floor covering" in item_options  # vinyl
        assert "Pipework insulation" in item_options  # insulation
        assert "Gasket(s)" in item_options  # gasket

    def test_with_none_schema_bundle(self):
        """Works with schema_bundle=None (uses fallbacks)."""
        picklists = build_picklist_context(schema_bundle=None)
        # Should not raise; should return all keys with fallback values
        assert len(picklists) == 13

    def test_with_mock_schema_bundle(self):
        """Works with a mock SFSchemaBundle that has minimal picklist data."""
        mock_bundle = _make_mock_bundle(
            picklists={
                "Building_Type__c": ["School", "Classroom", "Office"],
                "Building_Category__c": ["Educational and training facilities"],
                "Friability_of_Material__c": ["Non-friable", "Friable"],
                "Condition__c": ["Stable", "Fair", "Poor", "Unknown"],
                "Disturbance_Potential_of_Material__c": ["Low", "Moderate", "High"],
                "Sample_Analysis_Result_Material_Status__c": [
                    "Positive",
                    "Assumed Positive",
                    "Negative",
                    "Assumed Negative",
                    "Negative - Treated as Positive",
                ],
                "Internal_External__c": ["Internal", "External", "External & Internal"],
                "Labelled__c": ["Yes", "No"],
                "ACM_Classification__c": [
                    "Cement products",
                    "Vinyl products",
                    "Insulation Products",
                ],
                "ACM_Sub_Classification__c": ["Flat sheeting", "Vinyl sheet"],
                "Frequency_of_Use__c": ["Daily", "Weekly"],
            }
        )
        picklists = build_picklist_context(schema_bundle=mock_bundle)
        # Should use mock data for available picklists
        assert "School" in picklists["building_type_options"]
        assert "Classroom" in picklists["building_type_options"]
        assert (
            "Educational and training facilities"
            in picklists["building_category_options"]
        )
        assert "Non-friable" in picklists["friability_options"]
        assert "Friable" in picklists["friability_options"]

    def test_acm_classification_options_from_fallback(self):
        """Contains all ACM classification values from the mapping dict."""
        picklists = build_picklist_context(schema_bundle=None)
        acm = picklists["acm_classification_options"]
        assert "Cement products" in acm
        assert "Vinyl products" in acm
        assert "Insulation Products" in acm
        assert "Coatings" in acm

    def test_formatted_as_bullet_list(self):
        """Each option is prefixed with '- ' (format_picklist style)."""
        picklists = build_picklist_context(schema_bundle=None)
        # friability_options should have lines like "- Non-friable"
        lines = picklists["friability_options"].split("\n")
        for line in lines:
            if line.strip():
                assert line.startswith("- "), f"Line not formatted as bullet: {line!r}"

    def test_building_type_options_non_empty(self):
        """building_type_options is non-empty string."""
        picklists = build_picklist_context(schema_bundle=None)
        assert picklists["building_type_options"].strip() != ""


# ---------------------------------------------------------------------------
# _format_picklist
# ---------------------------------------------------------------------------


class TestFormatPicklist:
    """Tests for the private _format_picklist helper."""

    def test_single_value(self):
        """Single value formats to '- value'."""
        result = _format_picklist(["Non-friable"])
        assert result == "- Non-friable"

    def test_multiple_values(self):
        """Multiple values join with newlines, each prefixed with '- '."""
        result = _format_picklist(["Non-friable", "Friable"])
        assert result == "- Non-friable\n- Friable"

    def test_empty_list(self):
        """Empty list returns empty string."""
        result = _format_picklist([])
        assert result == ""

    def test_preserves_special_characters(self):
        """Values with special chars (parentheses, slashes) are preserved."""
        result = _format_picklist(["N/A (negative)", "External & Internal"])
        assert "N/A (negative)" in result
        assert "External & Internal" in result
