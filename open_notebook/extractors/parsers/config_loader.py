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
    SFDependencyChain,
    SFFieldDef,
    SFFieldSchemaConfig,
    SFSchemaBundle,
)

CONFIG_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "docs",
    "samplePDF",
    "instructions-sample",
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


def _find_enum_name(
    display_name: str, prop: dict, enums: dict[str, list[str]]
) -> Optional[str]:
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
        logger.warning(
            f"Could not load field schema JSON: {e}. Using hardcoded defaults."
        )
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
            logger.debug(
                f"Auto-generated internal_name '{internal_name}' for '{display_name}'"
            )

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
        FieldDef(
            internal_name="product",
            display_name="Specific Item/ACM Name",
            excel_column="X",
            col_index=24,
            field_type="string",
            required=True,
            group="acm_details",
        ),
        FieldDef(
            internal_name="material_condition",
            display_name="Condition",
            excel_column="AG",
            col_index=33,
            field_type="enum",
            required=True,
            group="assessment",
        ),
        FieldDef(
            internal_name="sample_result",
            display_name="Sample Result",
            excel_column="AE",
            col_index=31,
            field_type="enum",
            required=True,
            group="assessment",
        ),
        FieldDef(
            internal_name="building_name",
            display_name="Building Name",
            excel_column="E",
            col_index=5,
            field_type="string",
            required=True,
            group="building",
        ),
        FieldDef(
            internal_name="room_name",
            display_name="Room or Area",
            excel_column="V",
            col_index=22,
            field_type="string",
            required=True,
            group="location",
        ),
        FieldDef(
            internal_name="location",
            display_name="Location in Room",
            excel_column="W",
            col_index=23,
            field_type="string",
            required=True,
            group="location",
        ),
        FieldDef(
            internal_name="friable",
            display_name="Friability of material",
            excel_column="Y",
            col_index=25,
            field_type="enum",
            required=True,
            group="acm_details",
        ),
        FieldDef(
            internal_name="disturbance_potential",
            display_name="Disturbance Potential",
            excel_column="AH",
            col_index=34,
            field_type="enum",
            required=True,
            group="assessment",
        ),
    ]
    return FieldSchemaConfig(
        fields=default_fields,
        enums={
            "SampleResult": [
                "Positive",
                "Assumed Positive",
                "Negative",
                "Assumed Negative",
            ],
            "Condition": [
                "Poor",
                "Fair",
                "Stable",
                "Unknown",
                "N/A (negative)",
                "N/A (assumed negative)",
            ],
            "DisturbancePotential": [
                "High",
                "Moderate",
                "Low",
                "Unknown",
                "N/A (negative)",
                "N/A (assumed negative)",
            ],
            "Friability": ["Non-friable", "Friable"],
        },
        business_rules=list(DEFAULT_BUSINESS_RULES),
        version="1.0.0-fallback",
    )


# =============================================================================
# SF Schema Config (V3) — E30-S1
# =============================================================================


class SFSchemaLoadError(Exception):
    """Raised when SF schema source files cannot be parsed."""

    pass


SF_SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "V3", "output"
)

# E38-S0 (2026-04-12): canonical SF schema source moved from V3/output/*.md to
# config/sf-schema-snapshot.json + raw describe JSON. Markdown path retained
# as a legacy fallback until E38-S2 cleans up the V3/ directory.
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
SF_SNAPSHOT_PATH = os.path.join(REPO_ROOT, "config", "sf-schema-snapshot.json")

_SF_SCHEMA: Optional[SFSchemaBundle] = None


def load_sf_field_schema() -> SFSchemaBundle:
    """Load Salesforce field schema, preferring config/sf-schema-snapshot.json.

    E38-S0 (2026-04-12): canonical source is now the snapshot file created in
    Phase 2a of the SF reconciliation sprint. The snapshot points at the live
    vaea-demidev describe dumps in docs/sprint-artifacts/full-audit-2026-04-11/
    sf-describe/ for detailed field metadata (picklist values, length, nillable,
    dependent picklists).

    The snapshot captures only the *extractable* subset (~52 fields) of the
    SF schema, per DEC-001 (only literally-extractable-from-PDF fields count).
    The legacy V3/output/*.md loader returned all ~260 custom fields; this
    function returns only the extractable ones.

    Falls back to the legacy markdown loader if the snapshot file is missing
    (for safety during transitions). Returns a cached bundle on subsequent
    calls.

    Raises SFSchemaLoadError on malformed source files.
    """
    global _SF_SCHEMA
    if _SF_SCHEMA is not None:
        return _SF_SCHEMA

    if os.path.exists(SF_SNAPSHOT_PATH):
        _SF_SCHEMA = _load_sf_field_schema_from_snapshot(SF_SNAPSHOT_PATH)
        logger.info(
            f"Loaded SF schema from snapshot v{_SF_SCHEMA.version}: "
            f"building={len(_SF_SCHEMA.building_fields.fields)} extractable, "
            f"item={len(_SF_SCHEMA.item_fields.fields)} extractable, "
            f"{len(_SF_SCHEMA.picklists)} picklists, "
            f"{len(_SF_SCHEMA.dependencies)} dependency chains"
        )
        return _SF_SCHEMA

    logger.warning(
        f"SF schema snapshot not found at {SF_SNAPSHOT_PATH}; "
        "falling back to legacy V3/output/*.md loader. "
        "This is a Phase 2 transition fallback and should not fire in production."
    )
    _SF_SCHEMA = _load_sf_field_schema_legacy_markdown()
    return _SF_SCHEMA


def _load_sf_field_schema_from_snapshot(snapshot_path: str) -> SFSchemaBundle:
    """Build SFSchemaBundle from config/sf-schema-snapshot.json + raw describe JSON.

    Reads the snapshot for the extractable field list, then enriches each field
    with full metadata (length, nillable, custom, calc, picklistValues,
    controllerName) from the raw SF describe dumps pointed at by the snapshot's
    `source_files` map.

    Picklist values come directly from the raw describe (full lists, not just
    the snapshot's sampled values). Dependent picklist chains are derived from
    the raw describe's `controllerName` + `dependentPicklist` flags.

    Returns:
        A fully populated SFSchemaBundle with only the extractable subset.

    Raises:
        SFSchemaLoadError if the snapshot or a raw describe cannot be read.
    """
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SFSchemaLoadError(
            f"Cannot load SF schema snapshot {snapshot_path}: {e}"
        ) from e

    version = snapshot.get("version", "salesforce-v2-unknown")
    objects = snapshot.get("objects", {})
    source_files = snapshot.get("source_files", {})

    # Resolve raw describe paths (relative to repo root)
    building_raw_rel = source_files.get("Building__c_raw")
    item_raw_rel = source_files.get("Item__c_raw")
    if not building_raw_rel or not item_raw_rel:
        raise SFSchemaLoadError(
            f"Snapshot {snapshot_path} is missing source_files entries for "
            "Building__c_raw or Item__c_raw"
        )

    building_raw_path = os.path.join(REPO_ROOT, building_raw_rel)
    item_raw_path = os.path.join(REPO_ROOT, item_raw_rel)

    building_describe = _read_json_file(building_raw_path, "Building__c describe")
    item_describe = _read_json_file(item_raw_path, "Item__c describe")

    # Build per-object configs filtered to extractable fields
    building_config = _build_sf_field_schema_config(
        object_name="Building__c",
        object_label=objects.get("Building__c", {}).get("display_label", "Asset"),
        extractable=objects.get("Building__c", {}).get("extractable_fields", {}),
        describe=building_describe,
        version=version,
    )
    item_config = _build_sf_field_schema_config(
        object_name="Item__c",
        object_label=objects.get("Item__c", {}).get("display_label", "Hazmat Item"),
        extractable=objects.get("Item__c", {}).get("extractable_fields", {}),
        describe=item_describe,
        version=version,
    )

    # Combine picklists across both objects (building + item)
    combined_picklists: dict[str, list[str]] = {}
    combined_picklists.update(building_config.picklists)
    combined_picklists.update(item_config.picklists)

    # Build dependency chains from the describe metadata, filtered to
    # chains where every field is in our extractable set.
    dependencies = _build_dependency_chains_from_describes(
        building_describe=building_describe,
        item_describe=item_describe,
        extractable_building=building_config,
        extractable_item=item_config,
    )

    return SFSchemaBundle(
        version=version,
        building_fields=building_config,
        item_fields=item_config,
        picklists=combined_picklists,
        dependencies=dependencies,
    )


def _read_json_file(path: str, label: str) -> dict:
    """Read and parse a JSON file; raise SFSchemaLoadError on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise SFSchemaLoadError(f"{label} file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise SFSchemaLoadError(f"Cannot parse {label} JSON at {path}: {e}") from e
    except OSError as e:
        raise SFSchemaLoadError(f"Cannot read {label} file {path}: {e}") from e


def _build_sf_field_schema_config(
    object_name: str,
    object_label: str,
    extractable: dict,
    describe: dict,
    version: str,
) -> SFFieldSchemaConfig:
    """Build SFFieldSchemaConfig for one object from snapshot + describe.

    Iterates the snapshot's extractable_fields map, looks up each field in
    the raw describe to pull full metadata (length, nillable, picklistValues,
    controllerName, calc, updateable), and constructs SFFieldDef objects.

    Fields that are in the snapshot but absent from the describe are skipped
    with a warning — this would indicate snapshot drift and should be fixed
    by regenerating the snapshot.
    """
    describe_fields_by_name = {f["name"]: f for f in describe.get("fields", [])}

    sf_fields: list[SFFieldDef] = []
    picklists: dict[str, list[str]] = {}

    for api_name, snapshot_meta in extractable.items():
        raw = describe_fields_by_name.get(api_name)
        if raw is None:
            logger.warning(
                f"Snapshot references {object_name}.{api_name} but the raw "
                "describe does not contain this field. Snapshot may be stale; "
                "regenerate via a fresh sf sobject describe."
            )
            continue

        # Translate describe "type" to our internal field_type string.
        raw_type = raw.get("type", "string").lower()

        is_restricted = bool(raw.get("restrictedPicklist"))
        is_dependent = bool(raw.get("dependentPicklist"))
        controller_field = raw.get("controllerName") or None

        notes_parts: list[str] = []
        if is_restricted:
            notes_parts.append("Restricted picklist")
        if is_dependent and controller_field:
            notes_parts.append(f"Dependent on {controller_field}")
        snapshot_note = snapshot_meta.get("note")
        if snapshot_note:
            notes_parts.append(str(snapshot_note))

        sf_fields.append(
            SFFieldDef(
                api_name=api_name,
                label=raw.get("label") or snapshot_meta.get("label") or api_name,
                field_type=raw_type,
                length=raw.get("length"),
                nillable=bool(raw.get("nillable", True)),
                custom=bool(raw.get("custom", True)),
                calc=bool(raw.get("calculated", False)),
                updateable=bool(raw.get("updateable", True)),
                notes="; ".join(notes_parts) if notes_parts else None,
                is_restricted_picklist=is_restricted,
                is_dependent=is_dependent,
                controller_field=controller_field,
            )
        )

        # Extract picklist values directly from the raw describe
        if raw_type == "picklist":
            values = [
                pv["value"]
                for pv in raw.get("picklistValues", [])
                if pv.get("active", True)
            ]
            if values:
                picklists[api_name] = values

    # Ensure Item_Name__c also carries the BAR -> product group lookup keys
    # when present as an extractable picklist (preserves legacy behavior so
    # consumers that iterate ITEM_NAME_TO_PRODUCT_GROUP keep working).
    if object_name == "Item__c" and "Item_Name__c" in picklists:
        existing = set(picklists["Item_Name__c"])
        for name in ITEM_NAME_TO_PRODUCT_GROUP.keys():
            if name not in existing:
                picklists["Item_Name__c"].append(name)

    # Count how many extractable fields are custom vs formula vs picklist.
    total = len(sf_fields)
    custom = sum(1 for f in sf_fields if f.custom)
    picklist_count = sum(1 for f in sf_fields if f.field_type == "picklist")

    return SFFieldSchemaConfig(
        object_name=object_name,
        object_label=object_label,
        total_fields=total,
        custom_fields=custom,
        picklist_fields=picklist_count,
        fields=sf_fields,
        picklists=picklists,
        version=version,
    )


def _build_dependency_chains_from_describes(
    building_describe: dict,
    item_describe: dict,
    extractable_building: SFFieldSchemaConfig,
    extractable_item: SFFieldSchemaConfig,
) -> list[SFDependencyChain]:
    """Derive dependent picklist chains from raw describe metadata.

    Looks for any picklist field with `dependentPicklist=true` and a non-null
    `controllerName`, then uses the project's existing chain builders to
    populate the `mapping` dict (which contains the curated
    controller-value -> dependent-value pairings).

    Only chains where BOTH the controller and dependent fields are in the
    extractable set are returned. This keeps the dependency validator focused
    on fields the extraction path actually writes.
    """
    chains: list[SFDependencyChain] = []

    # Collect all (controller, dependent) pairs from the describes
    pairs: list[tuple[str, str, str]] = []  # (object, controller, dependent)
    for obj_name, describe in (
        ("Building__c", building_describe),
        ("Item__c", item_describe),
    ):
        for f in describe.get("fields", []):
            if f.get("type") == "picklist" and f.get("dependentPicklist"):
                controller = f.get("controllerName")
                if controller:
                    pairs.append((obj_name, controller, f["name"]))

    extractable_field_names_by_object = {
        "Building__c": {f.api_name for f in extractable_building.fields},
        "Item__c": {f.api_name for f in extractable_item.fields},
    }

    for obj_name, controller, dependent in pairs:
        field_names = extractable_field_names_by_object[obj_name]
        if controller not in field_names or dependent not in field_names:
            continue

        # Use the existing in-code chain builders for the canonical mapping.
        # These tables ship the curated controller_value -> dependent_values
        # pairings that match the live SF dependency data in demidev.
        if (
            controller == "Friability_of_Material__c"
            and dependent == "ACM_Classification__c"
        ):
            chains.append(_build_friability_chain())
        elif (
            controller == "ACM_Classification__c"
            and dependent == "ACM_Sub_Classification__c"
        ):
            chains.append(_build_acm_classification_chain())
        elif (
            controller == "Building_Type__c" and dependent == "Building_Category__c"
        ):
            chains.append(_build_building_type_chain())
        else:
            # Any other chain we discover gets an empty mapping; callers
            # that require curated pairings should add a builder.
            chains.append(
                SFDependencyChain(
                    controller_api_name=controller,
                    dependent_api_name=dependent,
                    mapping={},
                )
            )

    return chains


def _load_sf_field_schema_legacy_markdown() -> SFSchemaBundle:
    """Legacy loader: parse V3/output/*.md for the full pre-pivot field list.

    This is the pre-E38-S0 implementation, retained only for safety when the
    snapshot file is absent. Do not rely on it in production — it returns
    fields that no longer exist on the live SF schema, and was the root cause
    of the Phase 5 'snapshot is INERT' finding.
    """
    building_path = os.path.join(SF_SCHEMA_DIR, "building_fields_summary.md")
    item_path = os.path.join(SF_SCHEMA_DIR, "item_fields_summary.md")

    building_config = _parse_sf_field_table_from_path(building_path, "Building__c")
    item_config = _parse_sf_field_table_from_path(item_path, "Item__c")

    combined_picklists: dict[str, list[str]] = {}
    combined_picklists.update(building_config.picklists)
    combined_picklists.update(item_config.picklists)
    if "Item_Name__c" not in combined_picklists:
        combined_picklists["Item_Name__c"] = list(ITEM_NAME_TO_PRODUCT_GROUP.keys())

    dependencies = [
        _build_friability_chain(),
        _build_acm_classification_chain(),
        _build_building_type_chain(),
    ]

    bundle = SFSchemaBundle(
        version="salesforce-v1-legacy-markdown",
        building_fields=building_config,
        item_fields=item_config,
        picklists=combined_picklists,
        dependencies=dependencies,
    )
    logger.info(
        f"Loaded SF schema via legacy markdown path: "
        f"building={len(building_config.fields)} fields, "
        f"item={len(item_config.fields)} fields, "
        f"{len(combined_picklists)} picklists"
    )
    return bundle


def _parse_sf_field_table_from_path(
    file_path: str, object_name: str
) -> SFFieldSchemaConfig:
    """Load a *_fields_summary.md file and parse into SFFieldSchemaConfig.

    Raises SFSchemaLoadError if the file cannot be read.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError as e:
        raise SFSchemaLoadError(f"SF schema file not found: {file_path}") from e
    except OSError as e:
        raise SFSchemaLoadError(f"Cannot read SF schema file {file_path}: {e}") from e

    return _parse_sf_field_table(content, object_name)


def _parse_sf_field_table(
    markdown_content: str, object_name: str
) -> SFFieldSchemaConfig:
    """Parse a *_fields_summary.md markdown table into SFFieldSchemaConfig.

    Keyed on 'API Name' column (not Label).
    Handles:
    - Optional spaces around | delimiters
    - Empty cells (treats as None/default)
    - Boolean columns Y/blank -> True/False
    - 'Restricted picklist' detection from Notes column
    - 'Dependent on <api_name>' detection from Notes column
    """
    lines = markdown_content.splitlines()

    # Parse header metadata
    object_label = object_name
    total_fields = 0
    custom_fields = 0
    picklist_count = 0

    for line in lines:
        # e.g. "**Object:** Building__c (label: Asset Class)"
        if line.startswith("**Object:**"):
            m = re.search(r"\(label:\s*([^)]+)\)", line)
            if m:
                object_label = m.group(1).strip()
        # e.g. "**Total fields:** 143  **Custom fields:** 130  **Picklist fields:** 18"
        m_total = re.search(r"\*\*Total fields:\*\*\s*(\d+)", line)
        if m_total:
            total_fields = int(m_total.group(1))
        m_custom = re.search(r"\*\*Custom fields:\*\*\s*(\d+)", line)
        if m_custom:
            custom_fields = int(m_custom.group(1))
        m_picklist = re.search(r"\*\*Picklist fields:\*\*\s*(\d+)", line)
        if m_picklist:
            picklist_count = int(m_picklist.group(1))

    # Locate table header
    header_start = -1
    for i, line in enumerate(lines):
        if "| # | API Name |" in line or "| # |API Name|" in line:
            header_start = i
            break

    if header_start == -1:
        raise SFSchemaLoadError(
            f"Cannot find field table header in {object_name} markdown"
        )

    # Skip header row and separator row
    data_start = header_start + 2

    fields: list[SFFieldDef] = []
    for line in lines[data_start:]:
        stripped = line.strip()
        # Stop at blank line or next heading
        if not stripped or stripped.startswith("#"):
            # Only stop at the "## Picklist Fields" section heading
            if stripped.startswith("## Picklist"):
                break
            if not stripped:
                continue

        if not stripped.startswith("|"):
            continue

        # Split on | — the format is "| # | API Name | ..."
        parts = [p.strip() for p in stripped.split("|")]
        # Remove leading and trailing empty strings from split
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]

        # Expect exactly 10 columns:
        # # | API Name | Label | Type | Length | Nillable | Custom | Calc | Updateable | Notes
        if len(parts) < 10:
            if len(parts) >= 2 and parts[1]:  # Has at least an API name
                logger.warning(
                    f"Skipping malformed row in {object_name} "
                    f"(expected 10 cols, got {len(parts)}): {stripped[:80]}"
                )
            continue

        # Skip separator row (contains "---")
        if parts[0].startswith("---") or parts[1].startswith("---"):
            continue

        col_num = parts[0]
        api_name = parts[1]
        label = parts[2]
        field_type = parts[3].lower() if parts[3] else "string"
        length_str = parts[4]
        nillable_str = parts[5]
        custom_str = parts[6]
        calc_str = parts[7]
        updateable_str = parts[8]
        notes = parts[9] if len(parts) > 9 else ""

        # Validate row number (skip header-like rows)
        if not col_num or col_num == "#" or col_num.startswith("---"):
            continue

        # Parse length
        length: Optional[int] = None
        if length_str:
            try:
                length = int(length_str)
            except ValueError:
                length = None

        # Parse boolean columns: Y = True, empty = False
        nillable = nillable_str.upper() == "Y"
        custom = custom_str.upper() == "Y"
        calc = calc_str.upper() == "Y"
        updateable = updateable_str.upper() == "Y"

        # Detect restricted picklist
        is_restricted = "Restricted picklist" in notes

        # Detect dependent picklist and controller field
        is_dependent = False
        controller_field: Optional[str] = None
        dep_match = re.search(r"Dependent on\s+(\w+__c)", notes)
        if dep_match:
            is_dependent = True
            controller_field = dep_match.group(1)

        fields.append(
            SFFieldDef(
                api_name=api_name,
                label=label,
                field_type=field_type,
                length=length,
                nillable=nillable,
                custom=custom,
                calc=calc,
                updateable=updateable,
                notes=notes if notes else None,
                is_restricted_picklist=is_restricted,
                is_dependent=is_dependent,
                controller_field=controller_field,
            )
        )

    # Extract picklists from the "## Picklist Fields" section
    picklists = _extract_picklist_values(markdown_content)

    return SFFieldSchemaConfig(
        object_name=object_name,
        object_label=object_label,
        total_fields=total_fields or len(fields),
        custom_fields=custom_fields,
        picklist_fields=picklist_count,
        fields=fields,
        picklists=picklists,
        version="salesforce-v1",
    )


def _extract_picklist_values(markdown_content: str) -> dict[str, list[str]]:
    """Extract picklist value lists from the Picklist Fields section of a
    *_fields_summary.md file.

    Sections follow the pattern:
        ### API_Name__c — Label (restricted) (dependent on ...)
        *Description*

        - Value 1
        - Value 2
    """
    picklists: dict[str, list[str]] = {}

    # Find the Picklist section
    picklist_section_match = re.search(
        r"^## Picklist Fields", markdown_content, re.MULTILINE
    )
    if not picklist_section_match:
        return picklists

    section_text = markdown_content[picklist_section_match.start() :]
    lines = section_text.splitlines()

    current_api_name: Optional[str] = None
    current_values: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect a new picklist section heading: ### API_Name__c — ...
        if stripped.startswith("###"):
            # Save previous
            if current_api_name and current_values:
                picklists[current_api_name] = current_values

            # Extract API name from heading
            # Format: "### API_Name__c — Label (restricted) (dependent on ...)"
            heading_match = re.match(r"###\s+(\w+__c|\w+)\s*[—-]", stripped)
            if heading_match:
                current_api_name = heading_match.group(1)
                current_values = []
            else:
                current_api_name = None
                current_values = []
            continue

        # Collect values: "- Value"
        if stripped.startswith("- ") and current_api_name:
            value = stripped[2:].strip()
            if value and not value.startswith("[Years:"):
                current_values.append(value)

    # Save the last section
    if current_api_name and current_values:
        picklists[current_api_name] = current_values

    return picklists


def _build_friability_chain() -> SFDependencyChain:
    """Build Friability_of_Material__c -> ACM_Classification__c dependency.

    Returns all 18 valid classification values grouped by the 2 friability values.
    Data hardcoded from picklist-dependency-mappings.md.
    """
    return SFDependencyChain(
        controller_api_name="Friability_of_Material__c",
        dependent_api_name="ACM_Classification__c",
        mapping={
            "Non-friable": [
                "Bitumen products",
                "Cement products",
                "Coatings",
                "Gasket, friction products and adhesives",
                "Insulation Products",
                "Other",
                "Reinforced plastics/resins (excluding bitumen products)",
                "Textiles",
                "Vinyl products",
            ],
            "Friable": [
                "Bitumen products (f)",
                "Cement products (f)",
                "Coatings (f)",
                "Gasket, friction products and adhesives (f)",
                "Insulation products (f)",
                "Other (f)",
                "Reinforced plastics/resins (excluding bitumen products) (f)",
                "Textiles (f)",
                "Vinyl products (f)",
            ],
        },
    )


def _build_acm_classification_chain() -> SFDependencyChain:
    """Build ACM_Classification__c -> ACM_Sub_Classification__c dependency.

    36 valid (friability, classification) combinations with product type lists.
    Data hardcoded from picklist-dependency-mappings.md.
    """
    return SFDependencyChain(
        controller_api_name="ACM_Classification__c",
        dependent_api_name="ACM_Sub_Classification__c",
        mapping={
            # NON-FRIABLE product groups
            "Cement products": [
                "Ceiling Tiles",
                "Cement Flue",
                "Cement Pipe",
                "Cement Strapping",
                "Communications Pit",
                "Compressed Flat Sheeting",
                "Contaminated Soil (Non-friable Debris)",
                "Corrugated Roof Sheeting",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Electrical Arc Shields",
                "Faux Brick Cladding",
                "Faux Timber Sheeting",
                "Flat Sheeting",
                "Flue Cap",
                "Internal Lining",
                "Laminated Cement Sheeting (Tilux)",
                "Moulded Sheet",
                "Pebble Rendered Cement Sheeting",
                "Profiled Roof Sheeting",
                "Rainwater Guttering",
                "Ridge Capping",
                "Roof Tiles",
                "Toilet Cisterns",
                "Unknown",
                "Valley Gutters",
                "Vents",
                "Water Tanks",
                "Weatherboards",
            ],
            "Bitumen products": [
                "Acoustic Pad",
                "Adhesive or Glue",
                "Asphalt",
                "Bitumen Coated Paper",
                "Bitumen Coated Polystyrene",
                "Bitumen Coating",
                "Bitumen Washer",
                "Bituminous Membrane",
                "Bituminous adhesive (BlackJack)",
                "Brake Pads",
                "Caulking",
                "Compressed Electrical Panels",
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Electrical Cable Shrouding",
                "Electrical Components",
                "Galbestos (Asbestos coated metal sheet)",
                "Internal Lining",
                "Malthoid",
                "Mastic",
                "Pipe Lagging Residues",
                "Toilet Cisterns",
                "Toilet Seats",
                "Unknown",
                "Washers/Bitumen Washers",
            ],
            "Vinyl products": [
                "Contaminated Soil (Non-friable Debris)",
                "Dust",
                "Dust and Debris",
                "Hessian backed vinyl sheet",
                "Millboard or paper-backed vinyl sheet",
                "Unknown",
                "Vinyl sheet",
                "Vinyl sheet and adhesive",
                "Vinyl tiles",
                "Vinyl tiles and adhesive",
            ],
            "Gasket, friction products and adhesives": [
                "Brake pads",
                "CAF gasket(s)",
                "CAF gasket debris",
                "Caulking",
                "Clutch Plates",
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Dust and Debris",
                "Gland Packing",
                "Gasket(s)",
                "Gasket debris",
                "Mastic",
                "Putty",
                "Rope or Braided Gasket",
                "Rubber Gasket",
                "Rubber Products",
                "Silicone",
                "Unknown",
                "Washers",
            ],
            "Coatings": [
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Dust and Debris",
                "Paint",
                "Textured Coating",
                "Unknown",
            ],
            "Reinforced plastics/resins (excluding bitumen products)": [
                "Compressed Electrical Panels",
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Electrical Components",
                "Plastic",
                "Resinous Block",
                "Rubber Products",
                "Toilet Cisterns",
                "Toilet Seats",
                "Unknown",
                "Water Tanks",
            ],
            "Other": [
                "Cardboard",
                "Concrete levelling compound",
                "Contaminated Carpet Underlay",
                "Contaminated Materials",
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Fibrous Material",
                "Fire brick",
                "Fire curtains",
                "Gauze mats",
                "Granular Material",
                "Grout",
                "Masonry",
                "Mattresses",
                "Mineral Fibre Tiles",
                "Mortar",
                "Naturally Occurring",
                "Paper",
                "Plaster",
                "Putty",
                "Render",
                "Resinous Block",
                "Terrazzo",
                "Unknown",
            ],
            "Insulation Products": [
                "Acoustic pad",
                "Calico Wrap",
                "Ceiling Tiles",
                "Ceramic Fibre",
                "Contaminated Soil (Non-friable Debris)",
                "Debris",
                "Doonas",
                "Dust",
                "Dust and Debris",
                "Electrical Arc Shields",
                "Electrical Cable Shrouding",
                "Electrical Components",
                "Fire Door Core",
                "Fire Rating Material",
                "Fireproof Pillows",
                "Foam Insulation",
                "Gauze Mats",
                "Gland Packing",
                "Hessian",
                "Horsehair",
                "Insulation",
                "Insulation Product Dust and Debris",
                "Internal Insulation (Suspected)",
                "Internal Lining",
                "Lagging",
                "Limpet (Sprayed Insulation)",
                "Loose Fill Insulation",
                "Low Density Asbestos Fibre Board (AIB)",
                "Millboard",
                "Millboard or paper-backed vinyl sheet",
                "Pipe Lagging Residues",
                "SMF",
                "SMF Insulation",
                "Sprayed Insulation",
                "Sprayed insulation (Limpet)",
                "Strawboard",
                "Strawboard lined with millboard",
                "Strawboard with cement sheet lining",
                "Tape",
                "Unknown",
                "Vermiculite",
            ],
            "Textiles": [
                "Calico Wrap",
                "Carpet",
                "Cloth",
                "Contaminated Carpet Underlay",
                "Contaminated Materials",
                "Doonas",
                "Fire blanket",
                "Fire curtains",
                "Fire-fighting clothing",
                "Gauze mats",
                "Gloves",
                "Hessian",
                "Horsehair",
                "Mattresses",
                "Paper",
                "Polyester",
                "Rope and String",
                "Woven product",
            ],
            # FRIABLE product groups
            "Cement products (f)": [
                "Ceiling Tiles",
                "Cement Flue",
                "Cement Pipe",
                "Cement Strapping",
                "Communications Pit",
                "Compressed Flat Sheeting",
                "Contaminated Soil (Friable Debris)",
                "Corrugated Roof Sheeting",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Electrical Arc Shields",
                "Faux Brick Cladding",
                "Faux Timber Sheeting",
                "Flat Sheeting",
                "Flue Cap",
                "Internal Lining",
                "Laminated Cement Sheeting (Tilux)",
                "Moulded Sheet",
                "Pebble Rendered Cement Sheeting",
                "Profiled Roof Sheeting",
                "Rainwater Guttering",
                "Ridge Capping",
                "Roof Tiles",
                "Toilet Cisterns",
                "Unknown",
                "Valley Gutters",
                "Vents",
                "Water Tanks",
                "Weatherboards",
            ],
            "Vinyl products (f)": [
                "Contaminated Soil (Friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Hessian backed Vinyl sheet",
                "Millboard or paper-backed vinyl sheet",
                "Unknown",
                "Vinyl sheet",
                "Vinyl sheet and adhesive",
                "Vinyl Tiles",
                "Vinyl tiles and adhesive",
            ],
            "Insulation products (f)": [
                "AIB (Asbestos Insulated Board)",
                "Calico Wrap",
                "Ceiling Tiles",
                "Ceramic Fibre",
                "Contaminated Soil (Friable Debris)",
                "Debris",
                "Doonas",
                "Dust",
                "Dust and Debris",
                "Electrical Arc Shields",
                "Electrical Cable Shrouding",
                "Electrical Components",
                "Fibrous Material",
                "Fire Brick",
                "Fire Door Core",
                "Fire Rating Material",
                "Fireproof Pillows",
                "Foam Insulation",
                "Gauze Mats",
                "Gland Packing",
                "Hessian",
                "Horsehair",
                "Insulation",
                "Insulation Product Dust and Debris",
                "Internal Insulation (Suspected)",
                "Internal Lining",
                "Lagging",
                "Limpet",
                "Loose Fill Insulation",
                "Low Density Asbestos Fibre Board (AIB)",
                "Mattresses",
                "Millboard",
                "Pipe Lagging Residues",
                "SMF Insulation",
                "Sprayed Insulation",
                "Strawboard",
                "Tape",
                "Unknown",
                "Vermiculite",
            ],
            "Gasket, friction products and adhesives (f)": [
                "Adhesive or Glue",
                "Brake Pads",
                "CAF gasket(s)",
                "CAF gasket debris",
                "Caulking",
                "Clutch Plates",
                "Contaminated Soil (Friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Flange Gaskets",
                "Gasket Debris",
                "Gasket(s)",
                "Gland Packing",
                "Mastic",
                "Putty",
                "Rope and String",
                "Rope or Braided Gasket",
                "Rubber Gasket",
                "Unknown",
            ],
            "Textiles (f)": [
                "Cloth",
                "Fire blanket",
                "Fire-fighting clothing",
                "Gloves",
                "Paper",
                "Rope and String",
            ],
            "Other (f)": [
                "Cardboard",
                "Ceiling Tiles",
                "Concrete Levelling Compound",
                "Contaminated Carpet Underlay",
                "Contaminated Materials",
                "Contaminated Soil (Friable Debris)",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Fibrous Material",
                "Granular Material",
                "Grout",
                "Masonry",
                "Mattresses",
                "Mineral Fibre Tiles",
                "Mortar",
                "Naturally Occurring",
                "Plaster",
                "Render",
                "Resinous Block",
                "Terrazzo",
                "Unknown",
            ],
            "Bitumen products (f)": [
                "Acoustic Pad",
                "Asphalt",
                "Bitumen Coated Paper",
                "Bitumen Coating",
                "Bitumen Washer",
                "Bituminous adhesive (BlackJack)",
                "Bituminous Membrane",
                "Malthoid",
            ],
            "Coatings (f)": [
                "Paint",
                "Textured Coating",
                "Debris",
                "Dust",
                "Dust and Debris",
                "Unknown",
            ],
            "Reinforced plastics/resins (excluding bitumen products) (f)": [
                "Compressed Electrical Panels",
                "Electrical Components",
                "Plastic",
                "Resinous Block",
                "Rubber Products",
                "Unknown",
            ],
        },
    )


def _build_building_type_chain() -> SFDependencyChain:
    """Build Building_Type__c -> Building_Category__c dependency.

    114 building types -> 13 categories.
    The mapping is 1:1 (each building type has exactly one category),
    so values are str (not list[str]) for direct string comparison.
    Data hardcoded from picklist-dependency-mappings.md.
    """
    # Mapping: building_type -> category (str, not list)
    mapping: dict[str, str] = {}

    # Agriculture
    for btype in [
        "Farm annexe",
        "Farm depot house",
        "Fruit shed",
        "Grain storage shed",
        "Hay shed",
        "Hothouse",
        "Polyhouse",
        "Poultry pen",
        "Stables",
        "Stockyard",
    ]:
        mapping[btype] = "Agriculture"

    # Commercial and retail
    for btype in [
        "Commercial",
        "Docklands studios",
        "Film vault",
        "Retail",
        "Shop / Kiosk",
    ]:
        mapping[btype] = "Commercial and retail"

    # Correctional and justice facilities
    for btype in ["Court", "Juvenile", "Prison"]:
        mapping[btype] = "Correctional and justice facilities"

    # Defence and emergency services
    for btype in [
        "Airbase",
        "Ambulance garage",
        "Ambulance station",
        "CFA/FRV",
        "Fire pump shed",
        "Police Station",
    ]:
        mapping[btype] = "Defence and emergency services"

    # Educational and training facilities
    for btype in [
        "Building nursery",
        "Child care",
        "Children's centre",
        "Classroom",
        "Education centre",
        "School",
        "TAFE",
        "Teacher house",
        "Training centre",
        "Youth camp",
    ]:
        mapping[btype] = "Educational and training facilities"

    # Factories, warehouses and shops
    for btype in [
        "Canteen",
        "Factory",
        "Storage Shed",
        "Storeroom",
        "Warehouse",
        "Workshop",
    ]:
        mapping[btype] = "Factories, warehouses and shops"

    # Health services
    for btype in [
        "Aged Care",
        "Bush nursing",
        "Community Health Centre",
        "Consulting rooms",
        "Day centre",
        "Dental clinic",
        "Health centre",
        "Hospital",
        "Nursing home",
        "Rehab",
        "Specialist clinic",
    ]:
        mapping[btype] = "Health services"

    # Housing and accommodation
    for btype in [
        "Accommodation unit",
        "Apartment",
        "Curator house",
        "Flat",
        "Hostel",
        "House",
        "Housing - disability",
        "Housing - Other",
        "Lodge",
        "Residence",
    ]:
        mapping[btype] = "Housing and accommodation"

    # IT and communications
    for btype in ["Communication tower", "Computer centre", "Radio tower"]:
        mapping[btype] = "IT and communications"

    # Offices and professional services
    for btype in [
        "Administration",
        "Conference centre",
        "Head office",
        "HQ",
        "Office",
        "Ranger's office",
        "Reception",
        "Research facility",
    ]:
        mapping[btype] = "Offices and professional services"

    # Public and family services
    for btype in [
        "Activities shelter",
        "Amenities",
        "Art centre",
        "Assembly hall",
        "Band room",
        "Basketball court",
        "Community centre",
        "Community hall",
        "Concert hall",
        "Gallery",
        "Gymnasium",
        "Hall",
        "Information centre",
        "Leisure centre",
        "Library",
        "Multipurpose hall",
        "Museum",
        "Pavilion",
        "Recreation and sport",
        "Recreation centre",
        "Rotunda",
        "Tennis pavilion",
        "Theatre",
        "Visitor centre",
    ]:
        mapping[btype] = "Public and family services"

    # Transport
    for btype in [
        "Bridge",
        "Car",
        "Control building",
        "Control centre (train network)",
        "Control centre (tram network)",
        "Control room",
        "Crew room",
        "Depot",
        "Forklift",
        "Level crossing",
        "Roadway",
        "Train maintenance facility",
        "Train station",
        "Train station precinct",
        "Train substation",
        "Train yard",
        "Tram depot",
        "Tram substation",
        "Transport depot",
        "Truck",
        "Tunnel",
        "Van",
    ]:
        mapping[btype] = "Transport"

    # Unknown/other
    for btype in [
        "Barrier or Fencing",
        "Bicycle enclosure",
        "Building",
        "Building room",
        "Business interruption",
        "Facility",
        "Garage",
        "Main building",
        "Other",
        "Pipe",
        "Plant and equipment",
        "Plant room",
        "Pump house",
        "Shed",
        "Shelter",
        "Shelter shed",
        "Shipping Container",
        "Toilet",
        "Tower",
    ]:
        mapping[btype] = "Unknown/other"

    # Note: Teacher house appears in both Educational and Housing per the source doc.
    # The picklist-dependency-mappings.md lists it under Educational first.
    # Teacher house is already set to "Educational and training facilities" above.

    return SFDependencyChain(
        controller_api_name="Building_Type__c",
        dependent_api_name="Building_Category__c",
        mapping=mapping,
    )


# Item_Name__c product group mapping (not a dependent picklist).
# Maps each of the 294 Item_Name__c picklist values to their primary
# ACM_Classification__c (product group). Used by get_item_names_by_product_group().
# Source: docs/reference/product-taxonomy.md + picklist-dependency-mappings.md
ITEM_NAME_TO_PRODUCT_GROUP: dict[str, str] = {
    # Cement products items (structural/sheeting/piping)
    "Access hatch": "Cement products",
    "Architrave": "Cement products",
    "Awning lining": "Cement products",
    "Backing panel": "Cement products",
    "Batten(s)": "Cement products",
    "Behind heater": "Cement products",
    "Board": "Cement products",
    "Boxing": "Cement products",
    "Bulkhead": "Cement products",
    "Cabinet lining": "Cement products",
    "Capping": "Cement products",
    "Ceiling": "Cement products",
    "Ceiling and awning": "Cement products",
    "Ceiling and vertical infill panel": "Cement products",
    "Ceiling and walls": "Cement products",
    "Ceiling cavity": "Cement products",
    "Ceiling Lining": "Cement products",
    "Ceiling Strapping": "Cement products",
    "Ceiling tiles": "Cement products",
    "Chimney": "Cement products",
    "Cladding": "Cement products",
    "Cladding brackets": "Cement products",
    "Clerestorey eaves": "Cement products",
    "Columns": "Cement products",
    "Communications pit": "Cement products",
    "Conduit": "Cement products",
    "Cornices": "Cement products",
    "Cover": "Cement products",
    "Cover battens": "Cement products",
    "Cubicle partition(s)": "Cement products",
    "Culvert cover": "Cement products",
    "Dado wall": "Cement products",
    "Decking": "Cement products",
    "Door frame": "Cement products",
    "Down pipe": "Cement products",
    "Drain cover": "Cement products",
    "Eave and awning": "Cement products",
    "Eave and porch ceiling": "Cement products",
    "Eave lining": "Cement products",
    "End caps": "Cement products",
    "Expansion joint": "Cement products",
    "Extraction cover": "Cement products",
    "Fascia": "Cement products",
    "Fencing": "Cement products",
    "Flashing": "Cement products",
    "Floor": "Cement products",
    "Floor (below screed)": "Cement products",
    "Floor and walls": "Cement products",
    "Floor Cavity/void": "Cement products",
    "Formwork": "Cement products",
    "Framework (timber/metal)": "Cement products",
    "Gable lining": "Cement products",
    "Gutter": "Cement products",
    "Infill panels": "Cement products",
    "Infill panels below windows": "Cement products",
    "Internal components": "Cement products",
    "Internal lining": "Cement products",
    "Kickboards": "Cement products",
    "Lid": "Cement products",
    "Lining": "Cement products",
    "Lining to ceramic tiles": "Cement products",
    "Lining to tiles": "Cement products",
    "Louvres": "Cement products",
    "Lower walls": "Cement products",
    "Other": "Other",
    "Panel(s)": "Cement products",
    "Parapet wall": "Cement products",
    "Partitions": "Cement products",
    "Partition Wall(s)": "Cement products",
    "Pebblecrete joint": "Cement products",
    "Plinth": "Cement products",
    "Porch": "Cement products",
    "Porch ceiling": "Cement products",
    "Porch floor": "Cement products",
    "Porch stoop": "Cement products",
    "Retaining wall": "Cement products",
    "Ridge capping": "Cement products",
    "Riser": "Cement products",
    "Roof": "Cement products",
    "Roof cavity": "Cement products",
    "Roof covering": "Cement products",
    "Roofing": "Cement products",
    "Sign": "Cement products",
    "Skirting": "Cement products",
    "Soffit": "Cement products",
    "Soffit penetration": "Cement products",
    "Stairwell": "Cement products",
    "Strapping/beading": "Cement products",
    "Subfloor": "Cement products",
    "Suspended ceiling": "Cement products",
    "Tile backing": "Cement products",
    "Throughout": "Cement products",
    "Upper wall(s)": "Cement products",
    "Vent": "Cement products",
    "Vent cover": "Cement products",
    "Verandah": "Cement products",
    "Void": "Cement products",
    "Wall(s)": "Cement products",
    "Wall and gable lining": "Cement products",
    "Wall beading": "Cement products",
    "Wall cavity/void": "Cement products",
    "Wall cladding": "Cement products",
    "Wall covering": "Cement products",
    "Wall lining": "Cement products",
    "Wall panelling": "Cement products",
    "Walls and ceiling": "Cement products",
    "Water tank": "Cement products",
    "Window frame": "Cement products",
    "Window infill panels": "Cement products",
    "Window sill": "Cement products",
    # Bitumen products items (waterproofing/coatings/electrical)
    "Air conditioning re-heat unit": "Bitumen products",
    "Air conditioning trunking": "Bitumen products",
    "Air handling unit": "Bitumen products",
    "Baffle": "Bitumen products",
    "Bench top": "Cement products",
    "Benchtop lining": "Cement products",
    "Boiler": "Insulation Products",
    "Boiler gasket": "Gasket, friction products and adhesives",
    "Brake lining": "Gasket, friction products and adhesives",
    "Cable tray": "Bitumen products",
    "Calorifier": "Insulation Products",
    "Cistern": "Bitumen products",
    "Cistern boxing": "Bitumen products",
    "Clutch pad": "Gasket, friction products and adhesives",
    "Coils (electrical)": "Bitumen products",
    "Cold water service": "Insulation Products",
    "Compressor(s)": "Insulation Products",
    "Contact panel": "Bitumen products",
    "Counter top": "Cement products",
    "Door": "Cement products",
    "Door seal": "Gasket, friction products and adhesives",
    "Draining board": "Cement products",
    "Drip Guard": "Bitumen products",
    "Duct cover": "Insulation Products",
    "Ductwork": "Insulation Products",
    "Ductwork flange joint": "Gasket, friction products and adhesives",
    "Ductwork insulation": "Insulation Products",
    "Dumb waiter": "Bitumen products",
    "Electrical board": "Bitumen products",
    "Electrical cupboard": "Bitumen products",
    "Electrical cupboard door": "Bitumen products",
    "Electrical cupboard lining": "Bitumen products",
    "Electrical cables": "Bitumen products",
    "Electrical components": "Bitumen products",
    "Electrical meter": "Bitumen products",
    "Electrical terminal block": "Bitumen products",
    "Engine/motor": "Gasket, friction products and adhesives",
    "Exhaust": "Bitumen products",
    "Filing cabinet": "Bitumen products",
    "Flange joints": "Gasket, friction products and adhesives",
    "Flash guards": "Bitumen products",
    "Fume cupboard": "Cement products",
    "Furnace": "Insulation Products",
    "Fuse box": "Bitumen products",
    "Fuse cartridge": "Bitumen products",
    "Gas meter": "Bitumen products",
    "Gatic": "Cement products",
    "Gatic cover": "Cement products",
    "Header tank": "Insulation Products",
    "Heater": "Insulation Products",
    "Heater flue": "Insulation Products",
    "Heating coils": "Insulation Products",
    "Heat mats": "Insulation Products",
    "Hot plate": "Bitumen products",
    "Hot water system": "Insulation Products",
    "HRC Fuse": "Bitumen products",
    "Illegal dump": "Other",
    "Incinerator": "Insulation Products",
    "Incinerator flue": "Insulation Products",
    "Incubator lining": "Insulation Products",
    "In cupboard": "Cement products",
    "Inspection hatch": "Cement products",
    "Insulation": "Insulation Products",
    "Ironing board": "Textiles",
    "Joint": "Gasket, friction products and adhesives",
    "Kiln lining": "Insulation Products",
    "Lift car": "Insulation Products",
    "Lift landing doors": "Insulation Products",
    "Lift motor": "Insulation Products",
    "Light fitting": "Bitumen products",
    "Lightswitch": "Bitumen products",
    "Membrane": "Bitumen products",
    "Meter box": "Bitumen products",
    "Naturally occuring": "Other",
    "Oven": "Insulation Products",
    "Oven door seal": "Gasket, friction products and adhesives",
    "Overspray": "Coatings",
    "Packing material": "Gasket, friction products and adhesives",
    "Penetration packing": "Insulation Products",
    "Penetration sealant": "Gasket, friction products and adhesives",
    "Pie warmer": "Insulation Products",
    "Pipework": "Insulation Products",
    "Pipework brackets": "Insulation Products",
    "Pipework flange joints": "Gasket, friction products and adhesives",
    "Pipework insulation": "Insulation Products",
    "Pipework joint": "Gasket, friction products and adhesives",
    "Pit": "Cement products",
    "Plant and equipment": "Other",
    "Pothead pitch": "Bitumen products",
    "Pump flange joints": "Gasket, friction products and adhesives",
    "Rainwater goods": "Cement products",
    "Reheat unit (to ductwork)": "Insulation Products",
    "Residual debris": "Other",
    "Return air plenum": "Insulation Products",
    "Rock sample": "Other",
    "Safe": "Insulation Products",
    "Sanitary incinerator": "Insulation Products",
    "Seal": "Gasket, friction products and adhesives",
    "Seat": "Bitumen products",
    "Sewer Pit": "Cement products",
    "Shelving": "Cement products",
    "Sink unit": "Cement products",
    "Soil debris": "Other",
    "Speaker": "Bitumen products",
    "Splashback": "Cement products",
    "Splashback lining": "Cement products",
    "Stored item(s)": "Other",
    "Stump packing": "Other",
    "Switch (Pitch)": "Bitumen products",
    "Switchboard": "Bitumen products",
    "Switchboard cupboard lining": "Bitumen products",
    "Switchboard insulation": "Insulation Products",
    "Switchboard internal wall linings": "Bitumen products",
    "Switchboard lining": "Bitumen products",
    "Table top": "Cement products",
    "Textured coating": "Coatings",
    "Toilet cistern": "Bitumen products",
    "Toilet seat": "Bitumen products",
    "Trolley": "Other",
    "Underside of bath": "Bitumen products",
    "Underside of floor": "Cement products",
    "Underside of roof": "Cement products",
    "Unknown": "Other",
    "Urinal": "Cement products",
    "Urinal backing": "Cement products",
    "Valve": "Gasket, friction products and adhesives",
    "Waste pipe": "Cement products",
    "Water pipe": "Insulation Products",
    "Waterproofing": "Bitumen products",
    "Washer": "Gasket, friction products and adhesives",
    # Floor coverings (vinyl)
    "Beneath carpet": "Vinyl products",
    "Beneath floor covering": "Vinyl products",
    "Beneath sink": "Vinyl products",
    "Floor covering": "Vinyl products",
    "Floor covering (beneath carpet)": "Vinyl products",
    "Floor covering (lower layer)": "Vinyl products",
    "Floor covering (upper layer)": "Vinyl products",
    "Floor covering adhesive": "Vinyl products",
    "Floor covering lining": "Vinyl products",
    "Floor underlay": "Vinyl products",
    "Flooring": "Vinyl products",
    # Fire-related / Insulation
    "Arc Shield": "Insulation Products",
    "BBQ Top": "Other",
    "Bain marie": "Insulation Products",
    "Bagged waste": "Other",
    "Basin": "Cement products",
    "Bath surround panels": "Cement products",
    "Ballustrade": "Cement products",
    "Beneath render": "Coatings",
    "Beneath roof": "Cement products",
    "Beneath slab(s)": "Cement products",
    "Beams": "Cement products",
    "Chalk board": "Cement products",
    "Chiller unit": "Insulation Products",
    "Core sample": "Other",
    "Contaminated soil": "Other",
    "Cupboard": "Cement products",
    "Debris": "Other",
    "Desk": "Cement products",
    "Dust": "Other",
    "Dust and debris": "Other",
    "Fire blanket": "Textiles",
    "Fire curtain": "Textiles",
    "Fire door(s)": "Insulation Products",
    "Fire door frame": "Insulation Products",
    "Fire fighting equipment": "Textiles",
    "Fire hose cupboard lining": "Insulation Products",
    "Fireplace": "Insulation Products",
    "Fireproof cupboard": "Insulation Products",
    "Fire proofing": "Insulation Products",
    "Flammable good cabinet": "Insulation Products",
    "Gasket(s)": "Gasket, friction products and adhesives",
    "Gas mask": "Textiles",
    "Gauze mats": "Insulation Products",
    "Gland Packing": "Gasket, friction products and adhesives",
    "Glove": "Textiles",
    "Gutter debris": "Cement products",
    "Hessian": "Insulation Products",
    # Shower/bath
    "Shower and bath surrounds": "Cement products",
    "Shower Cubicle": "Cement products",
    "Shower screen": "Cement products",
}


def get_item_names_by_product_group(acm_classification: str) -> list[str]:
    """Return all Item_Name__c values for a given ACM_Classification value.

    Args:
        acm_classification: e.g. "Cement products", "Insulation Products",
                            "Cement products (f)", "Insulation products (f)"

    Returns:
        Sorted list of item names belonging to that product group.
    """
    # For friable groups (those ending in (f)), use the same mapping as non-friable
    # since ITEM_NAME_TO_PRODUCT_GROUP maps to the non-friable group name
    lookup_group = acm_classification
    # Strip friable suffix for lookup purposes — item names don't differ by friability
    if lookup_group.endswith(" (f)"):
        lookup_group = lookup_group[:-4]
        # Normalize case for matching (e.g. "Insulation products (f)" -> "Insulation Products")
        # Find best match in existing keys
        non_friable_groups = {g for g in set(ITEM_NAME_TO_PRODUCT_GROUP.values())}
        matched = next(
            (g for g in non_friable_groups if g.lower() == lookup_group.lower()),
            None,
        )
        if matched:
            lookup_group = matched

    return sorted(
        name
        for name, group in ITEM_NAME_TO_PRODUCT_GROUP.items()
        if group == lookup_group
    )
