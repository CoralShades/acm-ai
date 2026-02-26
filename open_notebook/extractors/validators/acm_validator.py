"""
ACM Record Validator.

Validates ACM extraction records against BAR enum values and business rules.
Used by the corrective RAG loop to identify fields needing correction.

Story: E1-S15 Corrective RAG Validation Loop
"""

from typing import Optional

from loguru import logger
from pydantic import BaseModel

from open_notebook.extractors.normalizers.enums import normalize_enum_value
from open_notebook.extractors.parsers.config_loader import load_field_schema


class ValidationIssue(BaseModel):
    """A single validation issue for a field."""

    field_name: str
    current_value: Optional[str] = None
    expected_format: str = ""
    valid_values: list[str] = []
    issue_type: str = ""  # "enum_mismatch", "business_rule", "required_field"


class ValidationResult(BaseModel):
    """Result of validating a single ACM record."""

    is_valid: bool
    issues: list[ValidationIssue] = []


class CorrectionStats(BaseModel):
    """Tracks correction statistics for an extraction run."""

    auto_corrected: int = 0
    llm_corrected: int = 0
    failed: int = 0
    total_validated: int = 0


# Enum field name → register_enums.json key mapping
_ENUM_FIELD_MAP: dict[str, str] = {
    "sample_result": "SampleResult",
    "material_condition": "Condition",
    "friable": "Friability",
    "disturbance_potential": "DisturbancePotential",
}

# Enum field name → enum normalizer field mapping
_ENUM_NORMALIZER_FIELD_MAP: dict[str, str] = {
    "sample_result": "sample_result",
    "material_condition": "condition",
    "friable": "friability",
    "disturbance_potential": "disturbance_potential",
}


_cached_enums: Optional[dict[str, list[str]]] = None


def _load_enum_values() -> dict[str, list[str]]:
    """Load authoritative enum values from field schema config.

    Caches the enum dict to avoid repeated dict extraction from config.
    """
    global _cached_enums
    if _cached_enums is not None:
        return _cached_enums
    config = load_field_schema()
    _cached_enums = config.enums
    return _cached_enums


def _append_data_issue(record: dict, message: str) -> None:
    """Append a data issue to record without creating duplicates."""
    raw_issues = record.get("data_issues")

    if isinstance(raw_issues, list):
        issues = raw_issues
    elif raw_issues is None:
        issues = []
        record["data_issues"] = issues
    elif isinstance(raw_issues, str):
        stripped = raw_issues.strip()
        issues = [stripped] if stripped else []
        record["data_issues"] = issues
    else:
        issues = [str(raw_issues)]
        record["data_issues"] = issues

    if message not in issues:
        issues.append(message)


def _normalize_enum_for_validation(field_name: str, raw_value: str) -> Optional[str]:
    """Normalize enum values while preserving passthrough for unknowns."""
    if field_name == "friable":
        lowered = raw_value.strip().lower().replace("-", " ")
        if lowered in {"friable", "f"}:
            return "Friable"
        if lowered in {"non friable", "nonfriable", "nf"}:
            return "Non Friable"
        if lowered in {"none", "n/a", "na", "unknown", "-"}:
            return None
        return raw_value.strip()

    normalizer_field = _ENUM_NORMALIZER_FIELD_MAP.get(field_name, field_name)
    return normalize_enum_value(raw_value, normalizer_field)


def validate_enum_fields(record: dict) -> list[ValidationIssue]:
    """Validate enum fields against authoritative BAR values.

    Checks sample_result, material_condition, friable, disturbance_potential
    against register_enums.json canonical values.

    Args:
        record: Dict of ACM record field values.

    Returns:
        List of ValidationIssue for invalid enum values.
    """
    enums = _load_enum_values()
    issues: list[ValidationIssue] = []

    for field_name, enum_key in _ENUM_FIELD_MAP.items():
        value = record.get(field_name)
        if value is None or value == "":
            continue

        raw_value = str(value).strip()
        if not raw_value:
            continue

        normalized_value = _normalize_enum_for_validation(field_name, raw_value)

        if normalized_value != raw_value:
            record[field_name] = normalized_value
            _append_data_issue(
                record,
                f"Normalized {field_name}: {raw_value} -> {normalized_value}",
            )
            logger.info(
                f"Normalized enum field {field_name}: '{raw_value}' -> "
                f"'{normalized_value}'"
            )

        if normalized_value is None:
            continue

        valid_values = enums.get(enum_key, [])
        if not valid_values:
            continue

        # Normalize for comparison: case-insensitive, treat hyphens as spaces
        def _norm(s: str) -> str:
            return s.strip().lower().replace("-", " ")

        value_norm = _norm(str(normalized_value))

        canonical_value = None
        for valid in valid_values:
            if _norm(valid) == value_norm:
                canonical_value = valid
                break

        if canonical_value is not None:
            if field_name == "friable":
                record[field_name] = normalized_value
            else:
                record[field_name] = canonical_value
            continue

        _append_data_issue(
            record,
            f"Unrecognized {field_name}: {normalized_value}",
        )
        logger.warning(
            f"Unrecognized enum field {field_name}: '{normalized_value}' "
            f"(raw='{raw_value}')"
        )

        issues.append(
            ValidationIssue(
                field_name=field_name,
                current_value=str(normalized_value),
                expected_format="enum",
                valid_values=valid_values,
                issue_type="enum_mismatch",
            )
        )

    return issues


def validate_business_rules(record: dict) -> list[ValidationIssue]:
    """Validate BAR business rules.

    Rules:
        BAR-001: Negative result → condition should be N/A (negative)
        BAR-002: Negative result → disturbance_potential should be N/A (negative)
        BAR-003: Assumed Negative → same as Negative (with assumed negative variant)
        BAR-004: Positive/Assumed Positive result → friable should be populated

    Args:
        record: Dict of ACM record field values.

    Returns:
        List of ValidationIssue for business rule violations.
    """
    issues: list[ValidationIssue] = []
    sample_result = record.get("sample_result")

    if not sample_result:
        return issues

    # BAR-001/BAR-002: Negative results require N/A fields
    negative_values = {"Negative", "Assumed Negative"}
    if sample_result in negative_values:
        na_value = (
            "N/A (negative)"
            if sample_result == "Negative"
            else "N/A (assumed negative)"
        )

        condition = record.get("material_condition")
        if condition and condition not in {"N/A (negative)", "N/A (assumed negative)"}:
            issues.append(
                ValidationIssue(
                    field_name="material_condition",
                    current_value=condition,
                    expected_format="business_rule",
                    valid_values=[na_value],
                    issue_type="business_rule",
                )
            )

        disturbance = record.get("disturbance_potential")
        if disturbance and disturbance not in {
            "N/A (negative)",
            "N/A (assumed negative)",
        }:
            issues.append(
                ValidationIssue(
                    field_name="disturbance_potential",
                    current_value=disturbance,
                    expected_format="business_rule",
                    valid_values=[na_value],
                    issue_type="business_rule",
                )
            )

    # BAR-004: Positive results require friability
    positive_values = {"Positive", "Assumed Positive"}
    if sample_result in positive_values:
        friable = record.get("friable")
        if not friable:
            issues.append(
                ValidationIssue(
                    field_name="friable",
                    current_value=None,
                    expected_format="business_rule",
                    valid_values=["Non-friable", "Friable"],
                    issue_type="business_rule",
                )
            )

    return issues


def validate_required_fields(record: dict) -> list[ValidationIssue]:
    """Validate required fields are present and non-empty.

    Required: building_id, product, material_description.

    Args:
        record: Dict of ACM record field values.

    Returns:
        List of ValidationIssue for missing required fields.
    """
    required = ["building_id", "product", "material_description"]
    issues: list[ValidationIssue] = []

    for field in required:
        value = record.get(field)
        if not value:
            issues.append(
                ValidationIssue(
                    field_name=field,
                    current_value=value,
                    expected_format="required",
                    valid_values=[],
                    issue_type="required_field",
                )
            )

    return issues


def validate_acm_record(record: dict) -> ValidationResult:
    """Validate a full ACM record against enums, business rules, and required fields.

    Orchestrates all validators and returns a combined result.

    Args:
        record: Dict of ACM record field values.

    Returns:
        ValidationResult with is_valid flag and aggregated issues.
    """
    all_issues: list[ValidationIssue] = []

    all_issues.extend(validate_required_fields(record))
    all_issues.extend(validate_enum_fields(record))
    all_issues.extend(validate_business_rules(record))

    is_valid = len(all_issues) == 0

    if not is_valid:
        logger.debug(
            f"Record validation failed with {len(all_issues)} issues: "
            f"{[i.field_name for i in all_issues]}"
        )

    return ValidationResult(is_valid=is_valid, issues=all_issues)
