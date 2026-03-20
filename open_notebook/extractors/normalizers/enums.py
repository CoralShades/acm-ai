"""
Enum Value Normalization

Normalizes ACM field values (SampleResult, Condition, DisturbancePotential)
to their canonical SF-canonical forms. Handles case variations, abbreviations,
and consultant-specific synonyms.

References:
- docs/samplePDF/instructions-sample/register_enums.json
"""

from typing import Optional

from loguru import logger

# Sample Result synonyms → canonical SF values
SAMPLE_RESULT_SYNONYMS: dict[str, str] = {
    "positive": "Positive",
    "pos": "Positive",
    "detected": "Positive",
    "negative": "Negative",
    "neg": "Negative",
    "not detected": "Negative",
    "negative, organic fibres detected": "Negative",
    "negative organic fibres detected": "Negative",
    "presumed": "Assumed Positive",
    "presumed positive": "Assumed Positive",
    "assumed": "Assumed Positive",
    "assumed positive": "Assumed Positive",
    "negative, assumed positive": "Assumed Positive",
    "not sampled": "Assumed Positive",
    "negative - treated as positive": "Negative - Treated as Positive",
    "treated as positive": "Negative - Treated as Positive",
    "unknown": "Unknown",
    "not analysed": "Unknown",
    "not analyzed": "Unknown",
    "no access": "No Access",
}

# Condition synonyms → canonical SF values (E30-S6: "Good" → "Stable")
CONDITION_SYNONYMS: dict[str, Optional[str]] = {
    "good": "Stable",
    "stable": "Stable",
    "fair": "Fair",
    "poor": "Poor",
    "unknown": "Unknown",
    "-": None,
    "n/a": None,
    "na": None,
}

# Disturbance Potential synonyms → canonical SF values
# NOTE: SF uses "Moderate" not "Medium"
DISTURBANCE_SYNONYMS: dict[str, Optional[str]] = {
    "low": "Low",
    "medium": "Moderate",
    "moderate": "Moderate",
    "high": "High",
    "unknown": "Unknown",
    "-": None,
    "n/a": None,
}

# Risk Status synonyms → canonical extraction values
# NOTE: risk_status uses "Medium" (not disturbance "Moderate")
RISK_STATUS_SYNONYMS: dict[str, Optional[str]] = {
    "high": "High",
    "h": "High",
    "medium": "Medium",
    "med": "Medium",
    "m": "Medium",
    "moderate": "Medium",
    "low": "Low",
    "l": "Low",
    "none": None,
    "n/a": None,
    "na": None,
    "unknown": None,
    "-": None,
}

# Map field_name → synonym dictionary
_SYNONYM_MAP: dict[str, dict] = {
    "sample_result": SAMPLE_RESULT_SYNONYMS,
    "condition": CONDITION_SYNONYMS,
    "disturbance_potential": DISTURBANCE_SYNONYMS,
    "risk_status": RISK_STATUS_SYNONYMS,
}


def normalize_enum_value(raw_value: Optional[str], field_name: str) -> Optional[str]:
    """
    Normalize an ACM enum field value to its canonical SF form.

    Handles case-insensitive matching, abbreviations, and consultant-specific
    synonyms. Unknown values pass through as-is (stripped).

    Args:
        raw_value: Raw field value from extraction
        field_name: Field identifier ("sample_result", "condition",
                    "disturbance_potential", "friability")

    Returns:
        Canonical value, None for N/A values, or raw value if unrecognized
    """
    if raw_value is None:
        return None

    stripped = raw_value.strip()
    if not stripped:
        return None

    # Friability: reuse existing taxonomy._normalize_friability()
    if field_name == "friability":
        from open_notebook.extractors.normalizers.taxonomy import _normalize_friability

        return _normalize_friability(stripped)

    # Look up synonym dictionary for the field
    synonyms = _SYNONYM_MAP.get(field_name)
    if synonyms is None:
        # Unknown field — return value as-is
        return stripped

    # Case-insensitive lookup
    lower = stripped.lower()
    if lower in synonyms:
        result = synonyms[lower]
        if result != stripped:
            logger.debug(f"Normalized {field_name}: '{raw_value}' → '{result}'")
        return result

    # Not in synonyms — return as-is (stripped)
    return stripped
