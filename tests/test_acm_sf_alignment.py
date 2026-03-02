"""
Unit tests for ACMRecord SF Item__c field alignment (E30-S3).

Verifies that:
  - BAR field names continue to work (backward compatibility / AC6)
  - SF API names work as validation aliases (AC1)
  - Mixed BAR + SF input works (AC1)
  - school_name is optional (AC4)
  - New result value "Negative - Treated as Positive" is accepted (AC5)
  - New fields labelled_sf, assea_risk_level, date_identified work (AC3)
  - Embedding fields are preserved unchanged (AC8)
  - model_dump() returns BAR (Python attr) names by default (AC6)
"""

import pytest
from pydantic import ValidationError

from open_notebook.domain.acm import ACMRecord
from open_notebook.extractors.acm_schemas import RESULT_VALUES

# ---------------------------------------------------------------------------
# Shared base data (minimum required BAR fields)
# ---------------------------------------------------------------------------

_BASE_BAR = {
    "source_id": "source:test001",
    "building_id": "B01",
    "product": "Vinyl Floor Tiles",
    "material_description": "Grey/white mottled vinyl tiles",
    "result": "Positive",
}

_BASE_SF = {
    "source_id": "source:test001",
    "Building_Code__c": "B01",
    "Item_Name__c": "Vinyl Floor Tiles",
    "Material_Description__c": "Grey/white mottled vinyl tiles",
    "Sample_Analysis_Result_Material_Status__c": "Positive",
}


# ---------------------------------------------------------------------------
# AC6 — BAR names work as before
# ---------------------------------------------------------------------------


class TestBarNames:
    """BAR field names must continue to work unchanged (backward compatibility)."""

    def test_construct_with_bar_names(self):
        """Construct ACMRecord using only BAR field names."""
        record = ACMRecord(**_BASE_BAR)
        assert record.building_id == "B01"
        assert record.product == "Vinyl Floor Tiles"
        assert record.material_description == "Grey/white mottled vinyl tiles"
        assert record.result == "Positive"

    def test_model_dump_uses_bar_names(self):
        """model_dump() must use Python attribute (BAR) names by default."""
        record = ACMRecord(**_BASE_BAR)
        dumped = record.model_dump()
        # BAR names present
        assert "building_id" in dumped
        assert "product" in dumped
        assert "material_description" in dumped
        assert "result" in dumped
        # SF names must NOT appear in the dump
        assert "Building_Code__c" not in dumped
        assert "Item_Name__c" not in dumped
        assert "Sample_Analysis_Result_Material_Status__c" not in dumped


# ---------------------------------------------------------------------------
# AC1 — SF aliases work via model_validate
# ---------------------------------------------------------------------------


class TestSFNames:
    """SF API names must be accepted as validation aliases."""

    def test_construct_with_sf_names(self):
        """Construct ACMRecord using SF API names via model_validate."""
        record = ACMRecord.model_validate(_BASE_SF)
        assert record.building_id == "B01"
        assert record.product == "Vinyl Floor Tiles"
        assert record.material_description == "Grey/white mottled vinyl tiles"
        assert record.result == "Positive"

    def test_construct_mixed_bar_sf(self):
        """Mix of BAR and SF names must resolve correctly."""
        data = {
            "source_id": "source:test001",
            "Building_Code__c": "B01",       # SF name
            "product": "Vinyl Floor Tiles",  # BAR name
            "Material_Description__c": "Grey/white mottled vinyl tiles",  # SF name
            "result": "Positive",            # BAR name
        }
        record = ACMRecord.model_validate(data)
        assert record.building_id == "B01"
        assert record.product == "Vinyl Floor Tiles"
        assert record.material_description == "Grey/white mottled vinyl tiles"

    def test_sf_alias_area_type(self):
        """Internal_External__c must resolve to the area_type attribute."""
        data = {**_BASE_BAR, "Internal_External__c": "Interior"}
        record = ACMRecord.model_validate(data)
        assert record.area_type == "Interior"

    def test_all_35_sf_aliases_resolve(self):
        """All 35 mapped SF aliases must resolve to the correct BAR attribute."""
        sf_to_bar = {
            "Item_Name__c": ("product", "Vinyl Floor Tiles"),
            "Material_Description__c": ("material_description", "Grey tiles"),
            "Building_Code__c": ("building_id", "B01"),
            "Building_Name__c": ("building_name", "Main Block"),
            "Room_or_Area__c": ("room_name", "Classroom 1"),
            "Room_Area__c": ("room_area", 45.0),
            "Location_in_Room__c": ("location", "Ceiling"),
            "Friability_of_Material__c": ("friable", "Non Friable"),
            "Condition__c": ("material_condition", "Good"),
            "Risk_Rating__c": ("risk_status", "Low"),
            "Sample_Analysis_Result_Material_Status__c": ("result", "Negative"),
            "Extent__c": ("extent", "Whole ceiling"),
            "NATA_Endorsed_Sample_no__c": ("sample_no", "S001"),
            "Identifying_Hygiene_Consulting_Company__c": ("identifying_company", "Acme Hygiene"),
            "Quantity__c": ("quantity", "10 m²"),
            "ACM_Labelled__c": ("acm_labelled", True),
            "Labelled_Details__c": ("acm_label_details", "Yellow sticker"),
            "Level__c": ("floor_level", "Ground"),
            "Survey_Date__c": ("date_of_inspection", "2024-01-15"),
            "Hygienist_Recommendations__c": ("hygienist_recommendations", "Monitor annually"),
            "ID_provided_by_metro__c": ("psb_supplied_acm_id", "PSB-123"),
            "Removal_Status__c": ("removal_status", "N/A"),
            "Removed_Date__c": ("date_of_removal", "2023-06-01"),
            "Quantity_Removed__c": ("quantity_removed", "5 m²"),
            "Asbestos_Removal_Notification_No__c": ("removal_notification_no", "ARN-001"),
            "EPA_Waste_Transport_Certificate_No__c": ("epa_certificate_no", "EPA-001"),
            "No_Access__c": ("no_access", True),
            "Additional_Comments__c": ("additional_comments", "See report"),
            "Disturbance_Potential_of_Material__c": ("disturbance_potential", "Low"),
            "ACM_Classification__c": ("acm_product_group", "T3 Vinyl products"),
            "ACM_Sub_Classification__c": ("acm_product_type", "Vinyl Tiles"),
            "SMF_Present__c": ("smf_present", "No"),
            "Internal_External__c": ("area_type", "Interior"),
            "Building_Year__c": ("building_year", 1975),
            "Building_Construction__c": ("building_construction", "Brick"),
            "Page_Number__c": ("page_number", 3),
            "Room_ID__c": ("room_id", "R-101"),
        }

        # Build a single record with all SF names
        sf_data = {"source_id": "source:test001"}
        for sf_name, (bar_name, value) in sf_to_bar.items():
            sf_data[sf_name] = value

        record = ACMRecord.model_validate(sf_data)

        for sf_name, (bar_name, expected_value) in sf_to_bar.items():
            actual = getattr(record, bar_name)
            assert actual == expected_value, (
                f"SF alias '{sf_name}' → attr '{bar_name}': "
                f"expected {expected_value!r}, got {actual!r}"
            )


# ---------------------------------------------------------------------------
# AC4 — school_name is optional
# ---------------------------------------------------------------------------


class TestSchoolNameOptional:
    """school_name must be optional (SF records may not include it)."""

    def test_school_name_optional(self):
        """ACMRecord must be valid without school_name."""
        record = ACMRecord(**_BASE_BAR)
        assert record.school_name is None

    def test_school_name_still_works(self):
        """school_name is still accepted when provided."""
        record = ACMRecord(**{**_BASE_BAR, "school_name": "Springfield Primary School"})
        assert record.school_name == "Springfield Primary School"

    def test_school_name_strips_whitespace(self):
        """school_name validator strips leading/trailing whitespace."""
        record = ACMRecord(**{**_BASE_BAR, "school_name": "  East Suburb School  "})
        assert record.school_name == "East Suburb School"

    def test_school_name_empty_string_becomes_none(self):
        """An empty or whitespace-only school_name is coerced to None."""
        record = ACMRecord(**{**_BASE_BAR, "school_name": "   "})
        assert record.school_name is None


# ---------------------------------------------------------------------------
# AC5 — new result value
# ---------------------------------------------------------------------------


class TestResultValues:
    """Result field must accept the new 'Negative - Treated as Positive' value."""

    def test_result_negative_treated_positive(self):
        """New result value 'Negative - Treated as Positive' must be in RESULT_VALUES."""
        assert "Negative - Treated as Positive" in RESULT_VALUES

    def test_result_existing_values_unchanged(self):
        """All original RESULT_VALUES must still be present."""
        original_values = {
            "Positive",
            "Assumed Positive",
            "Negative",
            "Assumed Negative",
            "Not Sampled",
            "No Access",
            "Unknown",
        }
        assert original_values.issubset(RESULT_VALUES)

    def test_acm_record_accepts_new_result(self):
        """ACMRecord accepts 'Negative - Treated as Positive' for the result field."""
        record = ACMRecord(**{**_BASE_BAR, "result": "Negative - Treated as Positive"})
        assert record.result == "Negative - Treated as Positive"


# ---------------------------------------------------------------------------
# AC3 — new SF fields
# ---------------------------------------------------------------------------


class TestNewSFFields:
    """New fields labelled_sf, assea_risk_level, and date_identified."""

    def test_new_field_labelled_sf(self):
        """labelled_sf field must default to None and accept string values."""
        record = ACMRecord(**_BASE_BAR)
        assert record.labelled_sf is None

        record_with_value = ACMRecord(**{**_BASE_BAR, "labelled_sf": "Yes"})
        assert record_with_value.labelled_sf == "Yes"

    def test_new_field_labelled_sf_via_sf_alias(self):
        """Labelled__c alias must map to labelled_sf attribute."""
        record = ACMRecord.model_validate({**_BASE_BAR, "Labelled__c": "No"})
        assert record.labelled_sf == "No"

    def test_new_field_assea_risk_level(self):
        """assea_risk_level field must default to None and accept string values."""
        record = ACMRecord(**_BASE_BAR)
        assert record.assea_risk_level is None

        record_with_value = ACMRecord(**{**_BASE_BAR, "assea_risk_level": "Medium"})
        assert record_with_value.assea_risk_level == "Medium"

    def test_new_field_assea_risk_level_via_sf_alias(self):
        """ASSEA_Survey_Guide_Risk_Level__c alias must map to assea_risk_level."""
        record = ACMRecord.model_validate(
            {**_BASE_BAR, "ASSEA_Survey_Guide_Risk_Level__c": "High"}
        )
        assert record.assea_risk_level == "High"

    def test_new_field_date_identified(self):
        """date_identified field must default to None and accept string values."""
        record = ACMRecord(**_BASE_BAR)
        assert record.date_identified is None

        record_with_value = ACMRecord(**{**_BASE_BAR, "date_identified": "2020-03-01"})
        assert record_with_value.date_identified == "2020-03-01"

    def test_new_field_date_identified_via_sf_alias(self):
        """Date_Identified__c alias must map to date_identified."""
        record = ACMRecord.model_validate(
            {**_BASE_BAR, "Date_Identified__c": "2021-07-15"}
        )
        assert record.date_identified == "2021-07-15"


# ---------------------------------------------------------------------------
# AC8 — embedding fields preserved
# ---------------------------------------------------------------------------


class TestEmbeddingFieldsPreserved:
    """Embedding fields must be untouched by alias changes."""

    def test_embedding_fields_preserved(self):
        """Embedding fields must still exist with correct types and defaults."""
        record = ACMRecord(**_BASE_BAR)

        # All embedding fields default to None
        assert record.embedding is None
        assert record.embedding_text is None
        assert record.embedding_model is None
        assert record.embedded_at is None
        assert record.enriched_text is None

    def test_embedding_fields_accept_values(self):
        """Embedding fields must still accept values when provided."""
        record = ACMRecord(
            **{
                **_BASE_BAR,
                "embedding": [0.1, 0.2, 0.3],
                "embedding_text": "Vinyl Floor Tiles in Classroom 1",
                "embedding_model": "text-embedding-3-small",
            }
        )
        assert record.embedding == [0.1, 0.2, 0.3]
        assert record.embedding_text == "Vinyl Floor Tiles in Classroom 1"
        assert record.embedding_model == "text-embedding-3-small"

    def test_embedding_fields_have_no_sf_aliases(self):
        """Embedding fields must not have SF aliases (they are internal)."""
        from pydantic.fields import FieldInfo

        record_fields = ACMRecord.model_fields
        embedding_field_names = [
            "embedding",
            "embedding_text",
            "embedding_model",
            "embedded_at",
            "enriched_text",
        ]
        for field_name in embedding_field_names:
            field_info: FieldInfo = record_fields[field_name]
            # validation_alias should be None (no AliasChoices added)
            assert field_info.validation_alias is None, (
                f"Field '{field_name}' should not have a validation_alias, "
                f"but got {field_info.validation_alias!r}"
            )
