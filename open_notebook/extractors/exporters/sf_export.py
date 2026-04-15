"""Salesforce-ready export utilities.

Maps ACMRecord and BuildingRecord fields to SF API names for Data
Loader-compatible CSV/Excel export. Field names MUST match the live
Salesforce schema in vaea-demidev — see config/sf-schema-snapshot.json
and docs/sprint-artifacts/full-audit-2026-04-11/PHASE-1-FINDINGS.md.

Why a rewrite (2026-04-11): the original mappings (E33-S8) accumulated
~17 fabricated field names that don't exist in SF (Room_ID__c, ACM_Name__c,
Extent__c, Location__c, Risk_Status__c, ACM_Labelled__c, and more). Every
export would fail Data Loader validation. The tables below were regenerated
from the live describe dump.
"""

import hashlib

from loguru import logger

# ---------------------------------------------------------------------------
# Field mapping tables — verified against vaea-demidev describe 2026-04-11
# Each tuple: (sf_api_name, python_field_name)
# ---------------------------------------------------------------------------

BUILDING_SF_MAPPING: list[tuple[str, str]] = [
    # Upsert key — valid external ID field (string, externalId=true, length=255)
    ("External_ID__c", "external_id"),
    # Required custom fields
    ("Building_Name__c", "building_name"),
    ("Building_Type__c", "building_type"),
    ("Frequency_of_Use__c", "frequency_of_use"),
    ("Public_Access__c", "public_access"),
    # Extractable from ARA PDF cover page / site description
    ("Building_Category__c", "building_category"),  # dependent on Building_Type__c
    ("Building_Address__c", "building_address"),
    ("Suburb__c", "suburb"),
    ("Postcode__c", "postcode"),
    ("State__c", "state"),
    ("Country__c", "country"),
    ("Estimated_Year_Build_New__c", "building_year"),  # picklist, 330 values
    ("Construction_Type__c", "building_construction"),
    ("Number_of_Levels__c", "number_of_levels"),  # picklist 1-99
    ("Roof_Type__c", "roof_type"),
    ("Owned_or_Leased__c", "owned_or_leased"),
    ("Asbestos_Register_Available__c", "asbestos_register_available"),
    ("Audit_Report_Available__c", "audit_report_available"),
    ("Date_of_Audit_Report__c", "date_of_audit_report"),
    ("Site_Name__c", "site_name"),
    ("School_UID__c", "school_uid"),
    ("Building_Unique_ID__c", "building_unique_id"),
    ("Within_Your_Portfolio__c", "within_your_portfolio"),
    ("GPS_Coordinates_provided_by_metro__c", "gps_coordinates"),
    # Merged from SiteConfig at export time (department + agency combined)
    ("Responsible_Agency_Department__c", "responsible_agency_department"),
    ("Additional_Comments__c", "additional_comments"),
]

ITEM_SF_MAPPING: list[tuple[str, str]] = [
    # Parent lookup via Building external ID (master-detail, required=true, cascade=true)
    # Item__c.External_ID__c is textarea+externalId=false in demidev — NOT usable as
    # upsert key. Item__c export is INSERT-only until VAEA SF admin fixes the field
    # type (see PHASE-1-FINDINGS.md §4). This row gives Data Loader the parent link.
    ("Building__r.External_ID__c", "building_external_id"),
    # Extractable from table rows
    ("Item_Name__c", "product"),  # restricted picklist, 294 values
    ("If_Other_Item_Name__c", "material_description"),  # fallback when picklist miss
    ("Friability_of_Material__c", "friable"),  # 2 values, controls ACM_Classification__c
    ("ACM_Classification__c", "acm_product_group"),  # dependent on Friability, 18 values
    ("ACM_Sub_Classification__c", "acm_product_type"),  # dependent on Group, 133 values
    ("Condition__c", "material_condition"),  # needs BAR->SF: Good -> Stable
    ("Disturbance_Potential_of_Material__c", "disturbance_potential"),  # Medium -> Moderate
    ("Sample_Analysis_Result_Material_Status__c", "sample_result"),
    ("NATA_Endorsed_Sample_no__c", "sample_no"),
    ("Identifying_Hygiene_Consulting_Company__c", "identifying_company"),
    ("Quantity__c", "quantity"),
    ("Units_of_Measure__c", "extent"),  # note: ACMRecord.extent carries the unit string
    ("Internal_External__c", "area_type"),
    ("Level__c", "floor_level"),
    ("Room_or_Area__c", "room_name"),
    ("Location_in_Room__c", "location"),
    ("Labelled__c", "labelled_sf"),  # ACMRecord has both acm_labelled (bool) and labelled_sf (Yes/No string)
    ("Labelled_Details__c", "acm_label_details"),
    ("Survey_Date__c", "date_identified"),
    ("Additional_Comments__c", "additional_comments"),
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
    """Generate a stable External_ID__c for a building.

    Resolution order (2026-04-11 — deterministic hash-based):
      1. building.external_id (if already set) — honour stored value
      2. building.building_unique_id (if set) — consultant-provided ID
      3. Deterministic hash: "ACM_" + sha256(source_id + building_name)[:16]

    The hash-based fallback is stable across re-extractions of the same
    PDF: identical inputs always produce identical IDs, so SF upsert
    updates in place instead of creating duplicates.

    Args:
        building: BuildingRecord instance.
        source_id: Source document ID (stable per PDF).

    Returns:
        A non-empty string <= 255 chars suitable for External_ID__c.
    """
    external_id = getattr(building, "external_id", None)
    if external_id:
        return str(external_id)

    building_unique_id = getattr(building, "building_unique_id", None)
    if building_unique_id:
        return str(building_unique_id)

    # Deterministic hash fallback: sha256(source_id + building_name)
    # Same PDF extracted twice -> same external ID -> SF upsert updates in place.
    name_part = (
        getattr(building, "building_name", None)
        or getattr(building, "internal_id", None)
        or "unknown"
    )
    digest = hashlib.sha256(f"{source_id}|{name_part}".encode()).hexdigest()[:16]
    generated = f"ACM_{digest}"
    logger.debug(
        f"Building has no external_id or building_unique_id — "
        f"generated deterministic External_ID__c: {generated!r}"
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
        elif sf_name == "Labelled__c":
            # labelled_sf (str "Yes"/"No") takes priority; fall back to acm_labelled (bool)
            labelled_sf = getattr(record, "labelled_sf", None)
            if labelled_sf is not None:
                row[sf_name] = str(labelled_sf)
            else:
                acm_labelled = getattr(record, "acm_labelled", None)
                if acm_labelled is True:
                    row[sf_name] = "Yes"
                elif acm_labelled is False:
                    row[sf_name] = "No"
                else:
                    row[sf_name] = ""
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
    agency = getattr(site_config, "agency", None)

    # SF Building__c has one combined field for agency/department.
    # Combine both parts if available; use whichever is set if only one exists.
    parts = [p for p in [department, agency] if p]
    if parts:
        row["Responsible_Agency_Department__c"] = " / ".join(parts)

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
