"""
Salesforce-ready export utilities.

Maps ACMRecord and BuildingRecord fields to SF API names
for Data Loader-compatible CSV/Excel export.

Story: E33-S8 Salesforce-Ready Export UI
"""

from loguru import logger

# ---------------------------------------------------------------------------
# Field mapping tables
# Each tuple: (sf_api_name, building_record_or_acm_record_field_name)
# ---------------------------------------------------------------------------

BUILDING_SF_MAPPING: list[tuple[str, str]] = [
    # Core identification — External_ID__c is generated at export time
    ("External_ID__c", "external_id"),
    ("Building_Code__c", "building_code"),
    ("Building_Name__c", "building_name"),
    ("Building_Type__c", "building_type"),
    ("Building_Category__c", "building_category"),
    ("Building_Address__c", "building_address"),
    ("Suburb__c", "suburb"),
    ("Postcode__c", "postcode"),
    ("Estimated_Year_Build_New__c", "building_year"),
    ("Construction_Type__c", "building_construction"),
    ("Number_of_Levels__c", "number_of_levels"),
    ("Est_Building_Size_m2__c", "est_building_size_m2"),
    ("Frequency_of_Use__c", "frequency_of_use"),
    ("Daily_Duration__c", "daily_duration"),
    ("Level_of_Activity__c", "level_of_activity"),
    ("Public_Access__c", "public_access"),
    ("Mobile_Plant__c", "mobile_plant"),
    ("Owned_or_Leased__c", "owned_or_leased"),
    ("Roof_Type__c", "roof_type"),
    ("Asbestos_Register_Available__c", "asbestos_register_available"),
    ("Audit_Report_Available__c", "audit_report_available"),
    ("Date_of_Audit_Report__c", "date_of_audit_report"),
    ("Site_Name__c", "site_name"),
    ("Building_Unique_ID__c", "building_unique_id"),
    ("State__c", "state"),
    ("Country__c", "country"),
    ("Additional_Comments__c", "additional_comments"),
]

ITEM_SF_MAPPING: list[tuple[str, str]] = [
    # FK to parent Building__c — resolved at export time using External_ID linkage
    ("Building__r.External_ID__c", "building_external_id"),
    ("Room_ID__c", "room_id"),
    ("Room_Name__c", "room_name"),
    ("Floor_Level__c", "floor_level"),
    ("Internal_External__c", "area_type"),
    ("ACM_Name__c", "product"),
    ("ACM_Description__c", "material_description"),
    ("Extent__c", "extent"),
    ("Location__c", "location"),
    ("Friability_of_Material__c", "friable"),
    ("Condition__c", "material_condition"),
    ("Risk_Status__c", "risk_status"),
    ("Result__c", "result"),
    ("Sample_No__c", "sample_no"),
    ("Sample_Result__c", "sample_result"),
    ("Quantity__c", "quantity"),
    ("ACM_Labelled__c", "acm_labelled"),
    ("Disturbance_Potential__c", "disturbance_potential"),
    ("Identifying_Company__c", "identifying_company"),
    ("Hygienist_Recommendations__c", "hygienist_recommendations"),
    ("ACM_Classification__c", "acm_product_group"),
    ("ACM_Sub_Classification__c", "acm_product_type"),
]


# ---------------------------------------------------------------------------
# Header helpers
# ---------------------------------------------------------------------------


def get_building_sf_headers() -> list[str]:
    """Return ordered SF API column headers for a Building__c export."""
    return [sf_name for sf_name, _ in BUILDING_SF_MAPPING]


def get_item_sf_headers() -> list[str]:
    """Return ordered SF API column headers for an Item__c export."""
    return [sf_name for sf_name, _ in ITEM_SF_MAPPING]


# ---------------------------------------------------------------------------
# External ID generation
# ---------------------------------------------------------------------------


def generate_external_id(building: object, source_id: str) -> str:
    """Generate External_ID__c for a building if one is not already stored.

    Resolution order:
      1. building.external_id (if set)
      2. building.building_unique_id (if set)
      3. Synthesised "{source_short}_{building_code}" fallback

    Args:
        building: BuildingRecord instance.
        source_id: Source document ID used for the fallback.

    Returns:
        A non-empty string to use as External_ID__c.
    """
    external_id = getattr(building, "external_id", None)
    if external_id:
        return str(external_id)

    building_unique_id = getattr(building, "building_unique_id", None)
    if building_unique_id:
        return str(building_unique_id)

    # Fallback: derive from source_id + building_code
    source_part = source_id.split(":")[-1][:8] if ":" in source_id else source_id[:8]
    code = (
        getattr(building, "building_code", None)
        or getattr(building, "internal_id", None)
        or "unknown"
    )
    generated = f"{source_part}_{code}"
    logger.debug(
        f"Building has no external_id or building_unique_id — "
        f"generated External_ID__c: {generated!r}"
    )
    return generated


# ---------------------------------------------------------------------------
# Row conversion helpers
# ---------------------------------------------------------------------------


def building_to_sf_row(
    building: object,
    source_id: str,
    site_config: object | None = None,
) -> dict[str, str]:
    """Convert a BuildingRecord to a dict keyed by SF API names.

    Args:
        building: BuildingRecord instance.
        source_id: Source document ID (used for External_ID generation).
        site_config: Optional SiteConfig for officer-configured merge fields (AC5).

    Returns:
        Dict mapping SF API names to string values ready for CSV/Excel output.
    """
    row: dict[str, str] = {}

    for sf_name, field_name in BUILDING_SF_MAPPING:
        if sf_name == "External_ID__c":
            row[sf_name] = generate_external_id(building, source_id)
        elif sf_name == "State__c":
            # State is not on BuildingRecord; leave blank unless site_config supplies it
            row[sf_name] = ""
        elif sf_name == "Country__c":
            # Country is not on BuildingRecord; leave blank unless site_config supplies it
            row[sf_name] = ""
        else:
            val = getattr(building, field_name, None)
            row[sf_name] = _format_value(val)

    # AC5: Merge officer-configured fields from SiteConfig
    if site_config is not None:
        _merge_site_config(row, site_config)

    return row


def item_to_sf_row(record: object, building_external_id: str) -> dict[str, str]:
    """Convert an ACMRecord to a dict keyed by SF API names.

    Args:
        record: ACMRecord instance.
        building_external_id: The External_ID__c of the parent building,
            used to populate Building__r.External_ID__c for SF relationship linking.

    Returns:
        Dict mapping SF API names to string values ready for CSV/Excel output.
    """
    row: dict[str, str] = {}

    for sf_name, field_name in ITEM_SF_MAPPING:
        if sf_name == "Building__r.External_ID__c":
            row[sf_name] = building_external_id
        else:
            val = getattr(record, field_name, None)
            row[sf_name] = _format_value(val)

    return row


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _merge_site_config(row: dict[str, str], site_config: object) -> None:
    """Merge officer-configured SiteConfig fields into a building export row.

    Modifies *row* in place.

    Args:
        row: Building export dict (SF API name keys).
        site_config: SiteConfig instance.
    """
    department = getattr(site_config, "department", None)
    if department:
        row["Department__c"] = str(department)

    agency = getattr(site_config, "agency", None)
    if agency:
        row["Agency__c"] = str(agency)

    # SiteConfig.site_name overrides any extracted value
    site_name = getattr(site_config, "site_name", None)
    if site_name:
        row["Site_Name__c"] = str(site_name)


def _format_value(val: object) -> str:
    """Serialize a Python field value to a plain string for export.

    - None → empty string
    - bool → "true" / "false" (lowercase, SF-compatible)
    - list → semicolon-separated values
    - everything else → str()
    """
    if val is None:
        return ""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, list):
        return "; ".join(str(v) for v in val)
    return str(val)
