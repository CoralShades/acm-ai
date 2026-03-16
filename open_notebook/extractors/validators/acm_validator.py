"""
ACM Record Validator.

Validates ACM extraction records against SF picklist values (primary) and
legacy enum values (audit-only). Used by the corrective RAG loop to identify
fields needing correction.

Story: E1-S15 Corrective RAG Validation Loop
Story: E30-S4 Dependent Picklist Validator (SF chain integration)
Story: E32-S7 SF-First Validation Pipeline
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
    chain_warnings: list[
        ValidationIssue
    ] = []  # WARN-policy SF chain issues (non-blocking)
    bar_warnings: list[
        ValidationIssue
    ] = []  # Legacy enum audit issues (non-blocking, never triggers correction)


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


def normalize_to_sf_canonical(record: dict) -> set[str]:
    """Normalize record values to SF-canonical forms.

    Applies value alias mapping and case-insensitive normalization.
    Graceful degradation: returns empty set if SF schema is unavailable.

    Args:
        record: Dict of ACM record field values (mutated in-place).

    Returns:
        Set of internal field names that were modified.
    """
    try:
        from open_notebook.extractors.validators.sf_picklist_validator import (
            normalize_record_to_sf,
        )

        return normalize_record_to_sf(record)
    except (ImportError, OSError) as e:
        logger.debug(f"SF normalization skipped: {e}")
        return set()


def sf_valid_fields(record: dict) -> set[str]:
    """Return set of internal field names that pass SF flat enum validation.

    Used by the correction loop to freeze SF-valid fields from LLM overwrites.
    Graceful degradation: returns empty set if SF schema is unavailable.

    Args:
        record: Dict of ACM record field values.

    Returns:
        Set of internal field names that pass SF flat enum validation.
    """
    try:
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SF_FLAT_ENUM_FIELD_MAP,
            SalesforcePicklistValidator,
        )

        sf_validator = SalesforcePicklistValidator()
        sf_issues = sf_validator.validate_flat_enums(record)
        # Fields with issues are NOT sf-valid
        invalid_sf_api_names = {i.dependent_field for i in sf_issues}
        # Return internal field names that have values and no SF issues
        valid: set[str] = set()
        for internal_name, sf_api_name in SF_FLAT_ENUM_FIELD_MAP.items():
            value = record.get(internal_name)
            if value and sf_api_name not in invalid_sf_api_names:
                valid.add(internal_name)
        return valid
    except (ImportError, OSError) as e:
        logger.debug(f"SF valid field check skipped: {e}")
        return set()


def _normalize_enum_for_validation(field_name: str, raw_value: str) -> Optional[str]:
    """Normalize enum values while preserving passthrough for unknowns."""
    if field_name == "friable":
        lowered = raw_value.strip().lower().replace("-", " ")
        if lowered in {"friable", "f"}:
            return "Friable"
        if lowered in {"non friable", "nonfriable", "nf"}:
            return "Non-friable"
        if lowered in {"none", "n/a", "na", "unknown", "-"}:
            return None
        return raw_value.strip()

    normalizer_field = _ENUM_NORMALIZER_FIELD_MAP.get(field_name, field_name)
    return normalize_enum_value(raw_value, normalizer_field)


def validate_enum_fields(record: dict) -> list[ValidationIssue]:
    """Validate enum fields against authoritative enum values.

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
    """Validate ACM business rules.

    Rules:
        BR-001: Negative result → condition should be N/A (negative)
        BR-002: Negative result → disturbance_potential should be N/A (negative)
        BR-003: Assumed Negative → same as Negative (with assumed negative variant)
        BR-004: Positive/Assumed Positive result → friable should be populated

    Args:
        record: Dict of ACM record field values.

    Returns:
        List of ValidationIssue for business rule violations.
    """
    issues: list[ValidationIssue] = []
    sample_result = record.get("sample_result")

    if not sample_result:
        return issues

    # BR-001/BR-002: Negative results require N/A fields
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

    # BR-004: Positive results require friability populated.
    # Includes SF compound values that are positive-managed.
    # NOTE: "Negative - Treated as Positive" is intentionally excluded from
    # negative_values above — it is positive-managed and friability IS required
    # for these records (same as "Positive"/"Assumed Positive").
    positive_values = {
        "Positive",
        "Assumed Positive",
        "Positive - Non-friable",  # SF compound value (AC5)
        "Positive - Friable",  # SF compound value (AC5)
        "Negative - Treated as Positive",  # Positive-managed despite negative analytical result
    }
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


def _convert_chain_issues(chain_issues: list) -> list[ValidationIssue]:
    """Convert ChainValidationIssue objects to ValidationIssue for pipeline compat."""
    issues: list[ValidationIssue] = []
    for ci in chain_issues:
        issues.append(
            ValidationIssue(
                field_name=ci.dependent_field,
                current_value=ci.dependent_value,
                expected_format="sf_chain"
                if ci.chain_name != "flat_enum"
                else "sf_enum",
                valid_values=ci.valid_values,
                issue_type=ci.issue_type,
            )
        )
    return issues


def validate_sf_chains(record: dict) -> list[ValidationIssue]:
    """Validate SF dependent picklist chains if SF schema is available.

    Runs the SalesforcePicklistValidator with WARN policy (non-blocking)
    and converts ChainValidationIssues to ValidationIssues for compatibility
    with the existing validation pipeline.

    .. deprecated:: E32-S7
        Kept for backward compatibility. Use validate_acm_record() which now
        calls SF validation directly with REJECT policy.

    Args:
        record: Dict of ACM record field values.

    Returns:
        List of ValidationIssue for chain validation failures (WARN-policy,
        non-blocking — should not flip is_valid to False).
    """
    try:
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SalesforcePicklistValidator,
            ValidationPolicy,
        )

        validator = SalesforcePicklistValidator()
        result = validator.validate_all_chains(record, ValidationPolicy.WARN)
        return _convert_chain_issues(result.issues)
    except (ImportError, OSError) as e:
        logger.debug(f"SF chain validation skipped: {e}")
        return []


def validate_acm_record(record: dict) -> ValidationResult:
    """Validate a full ACM record with SF-first validation pipeline.

    Orchestrates all validators. SF picklist validation is the primary
    blocking authority. Legacy enum validation is demoted to audit-only
    (bar_warnings, never triggers correction).

    Validation order:
    0. Normalize to SF-canonical values (alias mapping, casing)
    1. Required fields — blocking
    2. SF flat enum validation — blocking (primary authority)
    3. SF chain validation (REJECT policy) — blocking
    4. Business rules — blocking (SF N/A values)
    5. Legacy enum validation — audit-only (bar_warnings, non-blocking)

    Graceful degradation: if SF schema files are unavailable, falls back to
    legacy enum path as blocking (existing behavior preserved).

    Args:
        record: Dict of ACM record field values.

    Returns:
        ValidationResult with is_valid flag and aggregated issues.
    """
    # Step 0: Normalize to SF-canonical values before validation
    normalize_to_sf_canonical(record)

    all_issues: list[ValidationIssue] = []
    bar_warnings: list[ValidationIssue] = []
    chain_warnings: list[ValidationIssue] = []

    # 1. Required fields — always blocking
    all_issues.extend(validate_required_fields(record))

    # 2-3. SF validation (primary authority)
    try:
        from open_notebook.extractors.parsers.config_loader import SFSchemaLoadError
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SalesforcePicklistValidator,
            ValidationPolicy,
        )

        sf_validator = SalesforcePicklistValidator()

        # 2. SF flat enum validation — blocking
        sf_flat_issues = sf_validator.validate_flat_enums(record)
        all_issues.extend(_convert_chain_issues(sf_flat_issues))

        # 3. SF chain validation — REJECT policy (blocking)
        sf_chain_result = sf_validator.validate_all_chains(
            record, ValidationPolicy.REJECT
        )
        all_issues.extend(_convert_chain_issues(sf_chain_result.issues))

        # 5. Legacy enum validation — demoted to audit-only (non-blocking)
        bar_warnings.extend(validate_enum_fields(record))

    except (ImportError, OSError, SFSchemaLoadError) as e:
        # Graceful degradation: SF unavailable, fall back to legacy enum as blocking
        logger.debug(f"SF validation unavailable, falling back to legacy path: {e}")
        all_issues.extend(validate_enum_fields(record))
        chain_warnings = validate_sf_chains(record)

    # 4. Business rules — always blocking
    all_issues.extend(validate_business_rules(record))

    is_valid = len(all_issues) == 0

    if not is_valid:
        logger.debug(
            f"Record validation failed with {len(all_issues)} issues: "
            f"{[i.field_name for i in all_issues]}"
        )
    if bar_warnings:
        logger.debug(
            f"Record has {len(bar_warnings)} legacy audit warnings (non-blocking): "
            f"{[i.field_name for i in bar_warnings]}"
        )

    return ValidationResult(
        is_valid=is_valid,
        issues=all_issues,
        chain_warnings=chain_warnings,
        bar_warnings=bar_warnings,
    )
