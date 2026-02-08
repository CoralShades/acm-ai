"""
Field Schema Configuration Loader.

Loads BAR field schema from JSON files (register_row.schema.json + register_enums.json),
transforms them into FieldSchemaConfig, and caches the result.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

import json
import os
import re
from typing import Optional

from loguru import logger

from open_notebook.extractors.parsers.field_config import (
    BusinessRule,
    FieldDef,
    FieldSchemaConfig,
)

CONFIG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docs", "samplePDF", "instructions-sample"
)

_FIELD_SCHEMA: Optional[FieldSchemaConfig] = None

# Hardcoded mapping: BAR display name → ACMRecord internal_name
# These are not always predictable from the display name, so we maintain
# an explicit lookup table per the story Dev Notes.
DISPLAY_NAME_TO_INTERNAL: dict[str, str] = {
    "Department": "department",
    "Agency": "agency",
    "Sub Agency": "sub_agency",
    "Site Name (if applicable)": "site_name",
    "Building Name": "building_name",
    "Building Type": "building_type",
    "Building Address": "building_address",
    "Suburb": "suburb",
    "Postcode": "postcode",
    "Owned or Leased": "owned_or_leased",
    "Building Unique ID": "building_unique_id",
    "Frequency of use": "frequency_of_use",
    "Public Access?": "public_access",
    "Date of Inspection": "date_of_inspection",
    "Estimated Year Built": "building_year",
    "Est. Building Size (m2)": "building_size_m2",
    "Number of Levels": "number_of_levels",
    "Construction Type": "building_construction",
    "Roof Type": "roof_type",
    "Internal / External": "area_type",
    "Level": "level",
    "Room or Area": "room_name",
    "Location in Room": "location",
    "Specific Item/ACM Name": "product",
    "Friability of material": "friable",
    "FIRABILITY NAME EXCEL": "friability_display",
    "ACM Product Group": "acm_product_group",
    "ACM GROUP NAME EXCEL": "acm_group_display",
    "ACM Product Type": "acm_product_type",
    "NATA Endorsed Sample number (if available)": "sample_no",
    "Sample Result": "sample_result",
    "Identifying Hygiene or Consulting Company": "identifying_company",
    "Condition": "material_condition",
    "Disturbance Potential": "disturbance_potential",
    "Quantity": "quantity",
    "Labelled": "acm_labelled",
    "Label Details": "acm_label_details",
    "Hygienist Recommendations": "hygienist_recommendations",
    "Additional Comments": "additional_comments",
    "PSB Supplied ACM ID": "psb_supplied_acm_id",
    "Assumed Removed?": "assumed_removed",
    "Date of Removal": "date_of_removal",
    "Quantity Removed": "quantity_removed",
    "Asbestos Removal Notification No": "removal_notification_no",
    "EPA Waste Transport Certificate No": "epa_certificate_no",
    "Removal Comments": "removal_comments",
    "Photo Reference Number": "photo_reference",
}

# Field type derivation: map JSON schema types to simpler field_type strings
_TYPE_MAP = {
    "string": "string",
    "number": "number",
}

# BAR business rules
DEFAULT_BUSINESS_RULES = [
    BusinessRule(
        rule_id="negative_clears_condition",
        description='When Sample Result is "Negative", set Condition to "N/A (negative)"',
    ),
    BusinessRule(
        rule_id="assumed_negative_clears_condition",
        description='When Sample Result is "Assumed Negative", set Condition to "N/A (assumed negative)"',
    ),
    BusinessRule(
        rule_id="negative_clears_disturbance",
        description='When Sample Result is "Negative", set Disturbance Potential to "N/A (negative)"',
    ),
    BusinessRule(
        rule_id="assumed_negative_clears_disturbance",
        description='When Sample Result is "Assumed Negative", set Disturbance Potential to "N/A (assumed negative)"',
    ),
]

# Field groupings for UI
_FIELD_GROUPS: dict[str, str] = {
    "department": "organization",
    "agency": "organization",
    "sub_agency": "organization",
    "site_name": "organization",
    "building_name": "building",
    "building_type": "building",
    "building_address": "building",
    "suburb": "building",
    "postcode": "building",
    "owned_or_leased": "building",
    "building_unique_id": "building",
    "frequency_of_use": "building",
    "public_access": "building",
    "date_of_inspection": "building",
    "building_year": "building",
    "building_size_m2": "building",
    "number_of_levels": "building",
    "building_construction": "building",
    "roof_type": "building",
    "area_type": "location",
    "level": "location",
    "room_name": "location",
    "location": "location",
    "product": "acm_details",
    "friable": "acm_details",
    "friability_display": "acm_details",
    "acm_product_group": "acm_details",
    "acm_group_display": "acm_details",
    "acm_product_type": "acm_details",
    "sample_no": "assessment",
    "sample_result": "assessment",
    "identifying_company": "assessment",
    "material_condition": "assessment",
    "disturbance_potential": "assessment",
    "quantity": "assessment",
    "acm_labelled": "assessment",
    "acm_label_details": "assessment",
    "hygienist_recommendations": "assessment",
    "additional_comments": "assessment",
    "psb_supplied_acm_id": "documentation",
    "assumed_removed": "removal",
    "date_of_removal": "removal",
    "quantity_removed": "removal",
    "removal_notification_no": "removal",
    "epa_certificate_no": "removal",
    "removal_comments": "removal",
    "photo_reference": "documentation",
}


def _derive_field_type(display_name: str, prop: dict) -> str:
    """Derive field_type from JSON schema property."""
    # Check for enum
    if "enum" in prop:
        return "enum"
    # Check for date format
    if prop.get("format") == "date":
        return "date"
    # Check type array
    types = prop.get("type", [])
    if isinstance(types, str):
        types = [types]
    for t in types:
        if t in _TYPE_MAP:
            return _TYPE_MAP[t]
    return "string"


def _find_enum_name(display_name: str, prop: dict, enums: dict[str, list[str]]) -> Optional[str]:
    """Find the enum name for a field if it has controlled values."""
    if "enum" not in prop:
        return None
    prop_values = set(v for v in prop["enum"] if v is not None)
    if not prop_values:
        return None
    # Match against loaded enums: exact match first, then subset
    best_match: Optional[str] = None
    best_overlap = 0
    for enum_name, enum_values in enums.items():
        enum_set = set(enum_values)
        if prop_values == enum_set:
            return enum_name  # Exact match
        overlap = len(prop_values & enum_set)
        if overlap > best_overlap and overlap >= len(prop_values) * 0.8:
            best_match = enum_name
            best_overlap = overlap
    return best_match


def load_field_schema() -> FieldSchemaConfig:
    """Load BAR field schema from JSON config files.

    Returns cached config on subsequent calls.
    Falls back to hardcoded defaults if JSON files are missing.
    """
    global _FIELD_SCHEMA
    if _FIELD_SCHEMA is not None:
        return _FIELD_SCHEMA

    schema_path = os.path.join(CONFIG_DIR, "register_row.schema.json")
    enums_path = os.path.join(CONFIG_DIR, "register_enums.json")

    try:
        with open(schema_path) as f:
            schema = json.load(f)
        with open(enums_path) as f:
            enums = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load field schema JSON: {e}. Using hardcoded defaults.")
        _FIELD_SCHEMA = _build_default_config()
        return _FIELD_SCHEMA

    # Build FieldDef list from x_excel.field_specs
    field_specs = schema.get("x_excel", {}).get("field_specs", [])
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    fields: list[FieldDef] = []
    for spec in field_specs:
        display_name = spec["name"]
        internal_name = DISPLAY_NAME_TO_INTERNAL.get(display_name)
        if not internal_name:
            # Fallback: auto-generate snake_case
            internal_name = re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_")
            logger.debug(f"Auto-generated internal_name '{internal_name}' for '{display_name}'")

        prop = properties.get(display_name, {})
        field_type = _derive_field_type(display_name, prop)
        enum_name = _find_enum_name(display_name, prop, enums)

        fields.append(
            FieldDef(
                internal_name=internal_name,
                display_name=display_name,
                excel_column=spec["col_letter"],
                col_index=spec["col_index"],
                field_type=field_type,
                required=display_name in required_fields,
                active=True,
                enum_name=enum_name,
                group=_FIELD_GROUPS.get(internal_name),
            )
        )

    config = FieldSchemaConfig(
        fields=fields,
        enums=enums,
        business_rules=list(DEFAULT_BUSINESS_RULES),
        version="1.0.0",
        source_template=schema.get("x_excel", {}).get("source_workbook"),
    )

    _FIELD_SCHEMA = config
    logger.info(f"Loaded field schema: {len(fields)} fields, {len(enums)} enums")
    return _FIELD_SCHEMA


def _build_default_config() -> FieldSchemaConfig:
    """Build a minimal default config when JSON files are unavailable."""
    default_fields = [
        FieldDef(internal_name="product", display_name="Specific Item/ACM Name", excel_column="X", col_index=24, field_type="string", required=True, group="acm_details"),
        FieldDef(internal_name="material_condition", display_name="Condition", excel_column="AG", col_index=33, field_type="enum", required=True, group="assessment"),
        FieldDef(internal_name="sample_result", display_name="Sample Result", excel_column="AE", col_index=31, field_type="enum", required=True, group="assessment"),
        FieldDef(internal_name="building_name", display_name="Building Name", excel_column="E", col_index=5, field_type="string", required=True, group="building"),
        FieldDef(internal_name="room_name", display_name="Room or Area", excel_column="V", col_index=22, field_type="string", required=True, group="location"),
        FieldDef(internal_name="location", display_name="Location in Room", excel_column="W", col_index=23, field_type="string", required=True, group="location"),
        FieldDef(internal_name="friable", display_name="Friability of material", excel_column="Y", col_index=25, field_type="enum", required=True, group="acm_details"),
        FieldDef(internal_name="disturbance_potential", display_name="Disturbance Potential", excel_column="AH", col_index=34, field_type="enum", required=True, group="assessment"),
    ]
    return FieldSchemaConfig(
        fields=default_fields,
        enums={
            "SampleResult": ["Positive", "Assumed Positive", "Negative", "Assumed Negative"],
            "Condition": ["Poor", "Fair", "Good", "Unknown", "N/A (negative)", "N/A (assumed negative)"],
            "DisturbancePotential": ["High", "Moderate", "Low", "Unknown", "N/A (negative)", "N/A (assumed negative)"],
            "Friability": ["Non-friable", "Friable"],
        },
        business_rules=list(DEFAULT_BUSINESS_RULES),
        version="1.0.0-fallback",
    )
