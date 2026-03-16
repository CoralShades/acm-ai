"""Deterministic mappers from per-row LLM output to pipeline records.

Handles all normalization, classification, and Salesforce picklist alignment
that was removed from the LLM prompt. This is the "hard work" layer:
  - Friability string -> canonical "Friable" / "Non-friable"
  - item_name -> classify_product() -> Classification + Sub-Classification
  - condition/disturbance -> normalize_enum_value() -> SF picklist values
  - LLM hints used as fallback when deterministic classification is low confidence
"""

from typing import Optional

from loguru import logger

from open_notebook.domain.acm_row_schemas import ACMItemRow
from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.normalizers.enums import normalize_enum_value
from open_notebook.extractors.normalizers.taxonomy import (
    ClassificationResult,
    classify_product,
)

# Case-insensitive mapping of raw friability inputs to canonical values.
_FRIABILITY_MAP: dict[str, str] = {
    "f": "Friable",
    "friable": "Friable",
    "yes": "Friable",
    "nf": "Non-friable",
    "non-friable": "Non-friable",
    "non friable": "Non-friable",
    "nonfriable": "Non-friable",
    "no": "Non-friable",
}


def normalize_friability(raw: Optional[str]) -> Optional[str]:
    """Normalize a raw friability string to canonical form.

    Handles common abbreviations and alternate spellings from LLM output
    and PDF table data. Case-insensitive matching.

    Args:
        raw: Raw friability string from LLM extraction.

    Returns:
        "Friable", "Non-friable", or None if input is None/empty.

    Examples:
        >>> normalize_friability("F")
        'Friable'
        >>> normalize_friability("NF")
        'Non-friable'
        >>> normalize_friability("Yes")
        'Friable'
        >>> normalize_friability(None)
    """
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    key = stripped.lower().replace("-", " ").replace("  ", " ").strip()
    # Re-normalize after stripping hyphens for the lookup
    canonical = _FRIABILITY_MAP.get(key)
    if canonical is not None:
        return canonical
    # Also try the original lowered value (preserves hyphens)
    canonical = _FRIABILITY_MAP.get(stripped.lower())
    if canonical is not None:
        return canonical
    logger.warning(f"Unknown friability value: '{raw}' — passing through as None")
    return None


def is_friable_bool(friability_str: Optional[str]) -> bool:
    """Convert a friability string to a boolean.

    Args:
        friability_str: Canonical friability value ("Friable" or "Non-friable")
            or None.

    Returns:
        True if friability_str is "Friable", False otherwise (including None).
    """
    return friability_str == "Friable"


def map_item_row_to_extraction_record(
    row: ACMItemRow,
    building_id: str,
    source_id: str,
    page_number: Optional[int] = None,
    row_index: Optional[int] = None,
) -> ACMExtractionRecord:
    """Map a simplified ACMItemRow to a full ACMExtractionRecord.

    Performs all deterministic normalization that was removed from the LLM
    prompt to keep it simple for small Ollama models:
      a. Friability string -> canonical "Friable" / "Non-friable"
      b. item_name -> classify_product() -> classification + sub-classification
      c. condition -> normalize_enum_value() -> SF picklist value
      d. disturbance_potential -> normalize_enum_value() -> SF value
      e. LLM classification hint used when deterministic confidence >= 0.7
      f. LLM sub-classification used as fallback when deterministic confidence < 0.5

    Args:
        row: Simplified LLM extraction output (13 fields).
        building_id: Building record ID or identifier.
        source_id: Source document ID.
        page_number: Optional PDF page number for provenance.
        row_index: Optional row index within the table (for debugging).

    Returns:
        Fully populated ACMExtractionRecord ready for the validation pipeline.
    """
    # (a) Normalize friability
    normalized_friability = normalize_friability(row.friability)
    friable = is_friable_bool(normalized_friability)

    # (b) Classify product using deterministic taxonomy patterns
    classification_result: ClassificationResult = classify_product(
        item_description=row.item_name,
        friability=normalized_friability,
        product=row.acm_classification,  # Use LLM classification as product hint
    )

    # (e) Determine final classification: prefer deterministic if confidence >= 0.7
    final_classification: Optional[str] = None
    if classification_result.confidence >= 0.7:
        final_classification = classification_result.product_group
    elif row.acm_classification:
        # Use LLM hint as fallback for classification
        final_classification = row.acm_classification
        logger.debug(
            f"Using LLM classification hint '{row.acm_classification}' "
            f"(deterministic confidence={classification_result.confidence:.2f})"
        )

    # (f) Determine final sub-classification
    final_sub_classification: Optional[str] = None
    if classification_result.confidence >= 0.5:
        final_sub_classification = classification_result.product_type
    elif row.acm_sub_classification:
        # Use LLM sub-classification as fallback
        final_sub_classification = row.acm_sub_classification
        logger.debug(
            f"Using LLM sub-classification hint '{row.acm_sub_classification}' "
            f"(deterministic confidence={classification_result.confidence:.2f})"
        )

    # (c) Normalize condition -> SF picklist value
    # normalize_enum_value with field "condition" maps "Good" -> "Stable", etc.
    normalized_condition = normalize_enum_value(row.condition, "condition")

    # (d) Normalize disturbance potential -> SF value
    # normalize_enum_value with field "disturbance_potential" maps "Medium" -> "Moderate"
    normalized_disturbance = normalize_enum_value(
        row.disturbance_potential, "disturbance_potential"
    )

    # Build data_issues for tracking
    data_issues: list[str] = []
    if classification_result.method == "none" and row.item_name:
        data_issues.append(f"No taxonomy match for item_name: '{row.item_name}'")
    if row_index is not None:
        data_issues.append(f"row_index: {row_index}")

    # (g) Ensure material_description is never None — ACMRecord requires it
    safe_material_description = (
        final_sub_classification or row.acm_sub_classification or row.item_name or "Unknown"
    )

    # Build the full ACMExtractionRecord
    record = ACMExtractionRecord(
        # Building identity
        building_id=building_id,
        building_record_id=building_id,
        # Location
        room_name=row.room_name,
        floor_level=row.floor_level,
        location=row.item_location,
        area_type=row.internal_external,
        # Product / material
        product=row.acm_product or row.item_name,
        material_description=safe_material_description,
        # Friability
        friable=normalized_friability,
        # Result — use extracted sample_result, fallback to "Unknown"
        result=row.sample_result or "Unknown",
        # Sample number
        sample_no=row.sample_number,
        sample_result=row.sample_result,
        # Condition & disturbance
        material_condition=normalized_condition,
        disturbance_potential=normalized_disturbance,
        # Pipeline metadata
        extraction_confidence="medium",
        data_issues=data_issues,
        page_number=page_number,
    )

    return record
