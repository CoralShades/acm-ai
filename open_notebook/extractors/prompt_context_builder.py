"""
Prompt Context Builder for V3 Two-Phase ACM Extraction.

Builds injectable picklist strings for V3 Jinja templates.
Uses SF schema bundle (from E30-S1 config loader) to extract live
picklist values; falls back to hardcoded minimal values if unavailable.

Story: E30-S7 Two-Phase Extraction Prompts
"""

from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from open_notebook.extractors.parsers.field_config import SFSchemaBundle

# ---------------------------------------------------------------------------
# Hardcoded Item_Name__c groups (picklist values are stable)
# ---------------------------------------------------------------------------

_CEMENT_ITEMS: List[str] = [
    "Ceiling",
    "Ceiling Lining",
    "Ceiling tiles",
    "Ceiling and awning",
    "Ceiling and vertical infill panel",
    "Ceiling and walls",
    "Ceiling cavity",
    "Ceiling Strapping",
    "Roof",
    "Roof cavity",
    "Roof covering",
    "Roofing",
    "Wall(s)",
    "Wall lining",
    "Wall cladding",
    "Wall covering",
    "Wall panelling",
    "Eave lining",
    "Eave and awning",
    "Eave and porch ceiling",
    "Soffit",
    "Soffit penetration",
    "Gable lining",
    "Flue",
    "Down pipe",
    "Gutter",
    "Ridge capping",
    "Cladding",
    "Infill panels",
    "Infill panels below windows",
    "Fascia",
    "Flashing",
    "Corrugated sheeting",
    "Flat sheeting",
]

_VINYL_ITEMS: List[str] = [
    "Floor covering",
    "Floor covering (beneath carpet)",
    "Floor covering (lower layer)",
    "Floor covering (upper layer)",
    "Floor covering adhesive",
    "Floor covering lining",
    "Flooring",
    "Floor",
    "Floor (below screed)",
    "Floor and walls",
    "Floor Cavity/void",
    "Floor underlay",
    "Floor penetration",
    "Skirting",
    "Beneath floor covering",
    "Beneath carpet",
    "Beneath slab(s)",
]

_INSULATION_ITEMS: List[str] = [
    "Pipework insulation",
    "Pipework",
    "Pipework brackets",
    "Pipework flange joints",
    "Pipework joint",
    "Ductwork insulation",
    "Ductwork",
    "Ductwork flange joint",
    "Boiler",
    "Boiler gasket",
    "Insulation",
    "Internal insulation (suspected)",
    "Ceiling cavity",
    "Roof cavity",
    "Return air plenum",
    "Air conditioning re-heat unit",
    "Air conditioning trunking",
    "Air handling unit",
    "Calorifier",
    "Hot water system",
    "Heater",
    "Heater flue",
    "Heating coils",
    "Lagging",
]

_GASKET_ITEMS: List[str] = [
    "Gasket(s)",
    "Flange joints",
    "Expansion joint",
    "Valve",
    "Boiler gasket",
    "Pump flange joints",
    "Gland Packing",
    "Seal",
    "Oven door seal",
    "Door seal",
    "Joint",
    "Pebblecrete joint",
    "Penetration packing",
    "Penetration sealant",
    "Rope and string",
]

_COATING_ITEMS: List[str] = [
    "Textured coating",
    "Render",
    "Plaster",
    "Mortar",
    "Grout",
    "Paint",
    "Putty",
    "Silicone",
    "Mastic",
    "Caulking",
]

_ACM_CLASS_TO_ITEMS: Dict[str, List[str]] = {
    "Cement products": _CEMENT_ITEMS,
    "Cement products (f)": _CEMENT_ITEMS,
    "Vinyl products": _VINYL_ITEMS,
    "Vinyl products (f)": _VINYL_ITEMS,
    "Insulation Products": _INSULATION_ITEMS,
    "Insulation products (f)": _INSULATION_ITEMS,
    "Gasket, friction products and adhesives": _GASKET_ITEMS,
    "Gasket, friction products and adhesives (f)": _GASKET_ITEMS,
    "Coatings": _COATING_ITEMS,
    "Coatings (f)": _COATING_ITEMS,
}


def _dedupe_ordered(items: List[str]) -> List[str]:
    """Remove duplicates from a list while preserving insertion order."""
    seen: set = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


_DEFAULT_ITEM_GROUPS: List[str] = _dedupe_ordered(
    _CEMENT_ITEMS + _VINYL_ITEMS + _INSULATION_ITEMS + _GASKET_ITEMS
)

# Catch-all items always appended to any subsetted group
_CATCH_ALL_ITEMS: List[str] = ["Other", "Unknown", "Debris", "Dust", "Dust and debris"]

# ---------------------------------------------------------------------------
# Fallback picklist values used when schema_bundle is unavailable
# ---------------------------------------------------------------------------

_FALLBACK_FRIABILITY: List[str] = ["Non-friable", "Friable"]
_FALLBACK_SAMPLE_RESULT: List[str] = [
    "Positive",
    "Assumed Positive",
    "Negative",
    "Assumed Negative",
    "Negative - Treated as Positive",
]
_FALLBACK_CONDITION: List[str] = [
    "Poor",
    "Fair",
    "Stable",
    "Unknown",
    "N/A (negative)",
    "N/A (assumed negative)",
]
_FALLBACK_DISTURBANCE_POTENTIAL: List[str] = [
    "Low",
    "Moderate",
    "High",
    "Unknown",
    "N/A (negative)",
    "N/A (assumed negative)",
]
_FALLBACK_INTERNAL_EXTERNAL: List[str] = ["Internal", "External", "External & Internal"]
_FALLBACK_LABELLED: List[str] = ["Yes", "No"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_picklist_context(
    schema_bundle: Optional["SFSchemaBundle"],
    acm_classification: Optional[str] = None,
) -> Dict[str, str]:
    """Build injectable picklist strings for V3 Jinja templates.

    Args:
        schema_bundle: Loaded SF schema bundle (from E30-S1 config loader).
            If None, falls back to hardcoded minimal values.
        acm_classification: ACM_Classification__c value from Phase 1 result.
            Used to subset Item_Name__c options for Phase 2. If None, returns
            top 4 product group names (~100 values).

    Returns:
        Dict with keys: building_type_options, building_category_options,
        frequency_of_use_options, estimated_year_built_note,
        friability_options, acm_classification_options,
        acm_sub_classification_options, item_name_options,
        condition_options, disturbance_potential_options,
        sample_result_options, internal_external_options,
        labelled_options.
        All picklist values are newline-joined strings (one per line with "- " prefix).
    """
    picklists: Dict[str, list] = {}

    if schema_bundle is not None:
        try:
            # Merge building + item picklists from the bundle
            picklists = dict(schema_bundle.picklists)
        except Exception:
            picklists = {}

    def _get(api_name: str, fallback: List[str]) -> List[str]:
        """Get picklist values from schema bundle or fallback."""
        if api_name in picklists and picklists[api_name]:
            return list(picklists[api_name])
        return list(fallback)

    # Building-level picklists
    building_type_values = _get("Building_Type__c", ["School", "Classroom", "Office"])
    building_category_values = _get(
        "Building_Category__c", ["Educational and training facilities"]
    )
    frequency_of_use_values = _get(
        "Frequency_of_Use__c", ["Daily", "Weekly", "Occasional", "Rarely"]
    )

    # ACM classification picklists
    acm_class_values = _get(
        "ACM_Classification__c",
        list(_ACM_CLASS_TO_ITEMS.keys()),
    )
    acm_sub_class_values = _get("ACM_Sub_Classification__c", [])

    # Assessment picklists
    friability_values = _get("Friability_of_Material__c", _FALLBACK_FRIABILITY)
    condition_values = _get("Condition__c", _FALLBACK_CONDITION)
    disturbance_values = _get(
        "Disturbance_Potential_of_Material__c", _FALLBACK_DISTURBANCE_POTENTIAL
    )
    sample_result_values = _get(
        "Sample_Analysis_Result_Material_Status__c", _FALLBACK_SAMPLE_RESULT
    )
    internal_external_values = _get("Internal_External__c", _FALLBACK_INTERNAL_EXTERNAL)
    labelled_values = _get("Labelled__c", _FALLBACK_LABELLED)

    # Item_Name__c subsetting
    item_name_values = _select_item_name_groups(acm_classification)

    # Estimated_Year_Built: show range note instead of all 230 years
    estimated_year_built_note = (
        "4-digit year between 1700-2029 (e.g., 1960, 1975, 2005)"
    )

    return {
        "building_type_options": _format_picklist(building_type_values),
        "building_category_options": _format_picklist(building_category_values),
        "frequency_of_use_options": _format_picklist(frequency_of_use_values),
        "estimated_year_built_note": estimated_year_built_note,
        "friability_options": _format_picklist(friability_values),
        "acm_classification_options": _format_picklist(acm_class_values),
        "acm_sub_classification_options": _format_picklist(acm_sub_class_values),
        "item_name_options": _format_picklist(item_name_values),
        "condition_options": _format_picklist(condition_values),
        "disturbance_potential_options": _format_picklist(disturbance_values),
        "sample_result_options": _format_picklist(sample_result_values),
        "internal_external_options": _format_picklist(internal_external_values),
        "labelled_options": _format_picklist(labelled_values),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _select_item_name_groups(acm_classification: Optional[str]) -> List[str]:
    """Return relevant Item_Name__c values based on ACM_Classification__c.

    Groups:
      - Cement products / (f)     -> ceiling/wall/roof/eave/soffit items
      - Vinyl products / (f)      -> floor covering items + skirting
      - Insulation Products / (f) -> pipe/duct insulation items
      - Gasket...adhesives / (f)  -> gasket/flange/expansion items
      - Coatings / (f)            -> textured coating/render/plaster
      - Other / None              -> top 4 groups combined (~100 values)

    Always appends catch-all items: Other, Unknown, Debris, Dust, Dust and debris.
    Result contains no duplicates.
    """
    if acm_classification is not None and acm_classification in _ACM_CLASS_TO_ITEMS:
        base_items = list(_ACM_CLASS_TO_ITEMS[acm_classification])
    else:
        base_items = list(_DEFAULT_ITEM_GROUPS)

    # Append catch-all items (avoid duplicates)
    seen = set(base_items)
    result = list(base_items)
    for item in _CATCH_ALL_ITEMS:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return result


def _format_picklist(values: List[str]) -> str:
    """Join picklist values with newlines, one per line with '- ' prefix."""
    return "\n".join(f"- {v}" for v in values)
