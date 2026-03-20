"""
Salesforce Dependent Picklist Validator.

Validates dependent picklist chains (Friability→Classification→SubClassification,
BuildingType→BuildingCategory) against SF schema loaded at runtime from config_loader.

Story: E30-S4 Dependent Picklist Validator
"""

from enum import Enum
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from open_notebook.extractors.parsers.config_loader import load_sf_field_schema
from open_notebook.extractors.parsers.field_config import (
    SFDependencyChain,
    SFSchemaBundle,
)


class ValidationPolicy(str, Enum):
    """Validation enforcement policy."""

    WARN = "warn"  # Non-blocking: surface issues as badges in AG Grid
    REJECT = "reject"  # Blocking: prevent export until resolved


class ChainValidationIssue(BaseModel):
    """A single dependent picklist chain validation issue."""

    chain_name: str  # "acm_chain" or "building_chain"
    controller_field: str  # SF API name of controller field
    controller_value: str  # Actual controller value
    dependent_field: str  # SF API name of dependent field
    dependent_value: str  # Actual dependent value
    valid_values: list[str]  # Expected valid values for the controller
    issue_type: str = "invalid_chain_value"
    policy_action: str = "warn"  # "warn" or "reject"


class ChainValidationResult(BaseModel):
    """Result of chain validation for a single record."""

    is_valid: bool
    issues: list[ChainValidationIssue] = []


# Internal field name → SF API name mapping for record key lookup.
# The validator accepts both internal names and SF API names.
_FIELD_ALIASES: dict[str, str] = {
    "friable": "Friability_of_Material__c",
    "acm_product_group": "ACM_Classification__c",
    "acm_product_type": "ACM_Sub_Classification__c",
    "building_type": "Building_Type__c",
    "building_category": "Building_Category__c",
    "sample_result": "Sample_Analysis_Result_Material_Status__c",
    "result": "Sample_Analysis_Result_Material_Status__c",
    "material_condition": "Condition__c",
    "disturbance_potential": "Disturbance_Potential_of_Material__c",
}


# Common alternate values that need mapping to SF picklist values.
# Handles legacy casing and alternate spellings from various extraction sources.
_VALUE_ALIASES: dict[str, dict[str, str]] = {
    "Friability_of_Material__c": {
        "Non Friable": "Non-friable",  # Space variant → hyphenated SF canonical
        "Friable": "Friable",
    },
    "Condition__c": {
        "Good": "Stable",  # Legacy "Good" → SF "Stable"
    },
    "Disturbance_Potential_of_Material__c": {
        "Medium": "Moderate",  # "Medium" → SF "Moderate"
    },
    "Sample_Analysis_Result_Material_Status__c": {},
}


# Internal field name → SF API name for flat (non-chain) enum validation.
SF_FLAT_ENUM_FIELD_MAP: dict[str, str] = {
    "sample_result": "Sample_Analysis_Result_Material_Status__c",
    "material_condition": "Condition__c",
    "friable": "Friability_of_Material__c",
    "disturbance_potential": "Disturbance_Potential_of_Material__c",
}

# Legacy values absent from SF picklists but common in ARA documents.
# These should be flagged for user review, not rejected or auto-corrected.
_LEGACY_VALUES: set[str] = {"Not Sampled", "No Access", "Unknown"}


def _normalize_to_sf_value(value: str, valid_values: list[str]) -> str:
    """Normalize a value to its SF-canonical casing using case-insensitive lookup.

    If the value is already an exact match, return it unchanged.
    If a case-insensitive match exists in valid_values, return the canonical SF value.
    If no match found, return the original value (will fail validation as expected).

    This handles the mismatch between taxonomy.py Title Case output and the
    sentence case used in Salesforce ACM_Sub_Classification__c picklist values.

    Args:
        value: The value to normalize.
        valid_values: The list of canonical SF picklist values for this controller.

    Returns:
        The canonical SF value if a case-insensitive match is found, else value.
    """
    if value in valid_values:
        return value
    value_lower = value.lower()
    for sf_value in valid_values:
        if sf_value.lower() == value_lower:
            return sf_value
    return value


def normalize_record_to_sf(
    record: dict, schema_bundle: Optional[SFSchemaBundle] = None
) -> set[str]:
    """Normalize all SF-mappable fields to SF-canonical values in-place.

    Applies:
    1. Value alias mapping (_VALUE_ALIASES)
    2. Case-insensitive normalization to SF picklist canonical casing

    Handles both flat enum fields (via SF_FLAT_ENUM_FIELD_MAP) and the
    acm_product_type field (via chain validation lookups).

    Records use internal field names (friable, material_condition, etc.),
    NOT SF API names. This function reads from internal names and writes
    back to internal names.

    Args:
        record: Dict of ACM record field values (mutated in-place).
        schema_bundle: Optional pre-loaded SF schema. If None, loads from
            config_loader.

    Returns:
        Set of internal field names that were modified.
    """
    try:
        bundle = schema_bundle or load_sf_field_schema()
    except (ImportError, OSError) as e:
        logger.debug(f"SF normalization skipped (schema unavailable): {e}")
        return set()

    modified: set[str] = set()

    # 1. Normalize flat enum fields (sample_result, material_condition,
    #    friable, disturbance_potential)
    for internal_name, sf_api_name in SF_FLAT_ENUM_FIELD_MAP.items():
        value = record.get(internal_name)
        if not value:
            continue

        original = str(value).strip()
        if not original:
            continue

        normalized = original

        # Step 1a: Apply value alias mapping
        alias_map = _VALUE_ALIASES.get(sf_api_name)
        if alias_map and normalized in alias_map:
            normalized = alias_map[normalized]

        # Step 1b: Case-insensitive normalization against SF picklist
        sf_values: list[str] = (
            bundle.item_fields.picklists.get(sf_api_name)
            or bundle.building_fields.picklists.get(sf_api_name)
            or bundle.picklists.get(sf_api_name)
            or []
        )
        if sf_values:
            normalized = _normalize_to_sf_value(normalized, sf_values)

        if normalized != original:
            record[internal_name] = normalized
            modified.add(internal_name)
            logger.debug(
                f"SF normalization: {internal_name} '{original}' -> '{normalized}'"
            )

    # 2. Normalize acm_product_type (ACM_Sub_Classification__c).
    #    taxonomy.py outputs Title Case (e.g., "Flat Sheeting"), but SF uses
    #    sentence case ("Flat sheeting"). Use the SF picklist values as the
    #    canonical source (not chain mapping, which may also be Title Case).
    product_type = record.get("acm_product_type")
    if product_type:
        original_pt = str(product_type).strip()
        if original_pt:
            sf_sub_class_api = "ACM_Sub_Classification__c"
            # Get canonical SF picklist values for SubClassification
            sf_sub_values: list[str] = (
                bundle.item_fields.picklists.get(sf_sub_class_api)
                or bundle.picklists.get(sf_sub_class_api)
                or []
            )
            if sf_sub_values:
                normalized_pt = _normalize_to_sf_value(original_pt, sf_sub_values)
                if normalized_pt != original_pt:
                    record["acm_product_type"] = normalized_pt
                    modified.add("acm_product_type")
                    logger.debug(
                        f"SF normalization: acm_product_type "
                        f"'{original_pt}' -> '{normalized_pt}'"
                    )

    return modified


def _get_field_value(record: dict, sf_api_name: str) -> Optional[str]:
    """Get a field value from a record, trying SF API name first, then aliases.

    Applies value alias normalization for known mismatches (e.g.,
    "Non Friable" → SF "Non-friable").
    """
    val: Optional[str] = None

    # Try SF API name directly
    raw = record.get(sf_api_name)
    if raw is not None:
        val = str(raw).strip() if raw else None
    else:
        # Try internal aliases
        for internal_name, api_name in _FIELD_ALIASES.items():
            if api_name == sf_api_name:
                raw = record.get(internal_name)
                if raw is not None:
                    val = str(raw).strip() if raw else None
                    break

    if val is None:
        return None

    # Apply value alias normalization if needed
    bar_sf_map = _VALUE_ALIASES.get(sf_api_name)
    if bar_sf_map and val in bar_sf_map:
        val = bar_sf_map[val]

    return val


def _find_chain(
    dependencies: list[SFDependencyChain],
    controller: str,
    dependent: str,
) -> Optional[SFDependencyChain]:
    """Find a dependency chain by controller and dependent API names."""
    for chain in dependencies:
        if (
            chain.controller_api_name == controller
            and chain.dependent_api_name == dependent
        ):
            return chain
    return None


class SalesforcePicklistValidator:
    """Validates dependent picklist chains against SF schema."""

    def __init__(self, schema_bundle: Optional[SFSchemaBundle] = None):
        """Initialize with SF schema bundle.

        Args:
            schema_bundle: Optional pre-loaded schema. If None, loads from
                config_loader at init time.
        """
        if schema_bundle is not None:
            self._bundle = schema_bundle
        else:
            self._bundle = load_sf_field_schema()

    def validate_acm_chain(
        self,
        record: dict,
        policy: ValidationPolicy = ValidationPolicy.WARN,
    ) -> list[ChainValidationIssue]:
        """Validate the Friability → Classification → SubClassification chain.

        Checks:
        1. Classification is valid for the given Friability value
        2. SubClassification is valid for the given Classification value

        Skips validation if controller field is missing from the record.
        Uses strict case-sensitive matching.
        """
        issues: list[ChainValidationIssue] = []

        friability = _get_field_value(record, "Friability_of_Material__c")
        classification = _get_field_value(record, "ACM_Classification__c")
        sub_classification = _get_field_value(record, "ACM_Sub_Classification__c")

        # Chain 1: Friability → Classification
        if friability and classification:
            chain = _find_chain(
                self._bundle.dependencies,
                "Friability_of_Material__c",
                "ACM_Classification__c",
            )
            if chain:
                valid_values = chain.mapping.get(friability)
                if valid_values is None:
                    # Unknown friability value
                    issues.append(
                        ChainValidationIssue(
                            chain_name="acm_chain",
                            controller_field="Friability_of_Material__c",
                            controller_value=friability,
                            dependent_field="ACM_Classification__c",
                            dependent_value=classification,
                            valid_values=list(chain.mapping.keys()),
                            issue_type="invalid_controller_value",
                            policy_action=policy.value,
                        )
                    )
                elif isinstance(valid_values, list):
                    # Strict case-sensitive match
                    if classification not in valid_values:
                        issues.append(
                            ChainValidationIssue(
                                chain_name="acm_chain",
                                controller_field="Friability_of_Material__c",
                                controller_value=friability,
                                dependent_field="ACM_Classification__c",
                                dependent_value=classification,
                                valid_values=valid_values,
                                issue_type="invalid_chain_value",
                                policy_action=policy.value,
                            )
                        )

        # Chain 2: Classification → SubClassification
        if classification and sub_classification:
            chain = _find_chain(
                self._bundle.dependencies,
                "ACM_Classification__c",
                "ACM_Sub_Classification__c",
            )
            if chain:
                valid_values = chain.mapping.get(classification)
                if valid_values is None:
                    # Classification not found in chain — skip (already caught above)
                    pass
                elif isinstance(valid_values, list):
                    # Normalize taxonomy Title Case output to SF-canonical casing.
                    # taxonomy.py may return "Flat Sheeting" while SF stores "Flat sheeting".
                    sub_classification = _normalize_to_sf_value(
                        sub_classification, valid_values
                    )
                    if sub_classification not in valid_values:
                        issues.append(
                            ChainValidationIssue(
                                chain_name="acm_chain",
                                controller_field="ACM_Classification__c",
                                controller_value=classification,
                                dependent_field="ACM_Sub_Classification__c",
                                dependent_value=sub_classification,
                                valid_values=valid_values,
                                issue_type="invalid_chain_value",
                                policy_action=policy.value,
                            )
                        )

        return issues

    def validate_building_chain(
        self,
        record: dict,
        policy: ValidationPolicy = ValidationPolicy.WARN,
    ) -> list[ChainValidationIssue]:
        """Validate the BuildingType → BuildingCategory chain.

        Uses strict case-sensitive matching.
        Skips validation if building_type is missing from the record.
        """
        issues: list[ChainValidationIssue] = []

        building_type = _get_field_value(record, "Building_Type__c")
        building_category = _get_field_value(record, "Building_Category__c")

        if not building_type or not building_category:
            return issues

        chain = _find_chain(
            self._bundle.dependencies,
            "Building_Type__c",
            "Building_Category__c",
        )
        if not chain:
            return issues

        expected_category = chain.mapping.get(building_type)
        if expected_category is None:
            # Unknown building type
            issues.append(
                ChainValidationIssue(
                    chain_name="building_chain",
                    controller_field="Building_Type__c",
                    controller_value=building_type,
                    dependent_field="Building_Category__c",
                    dependent_value=building_category,
                    valid_values=list(chain.mapping.keys()),
                    issue_type="invalid_controller_value",
                    policy_action=policy.value,
                )
            )
        elif isinstance(expected_category, str):
            # 1:1 mapping — strict case-sensitive match
            if building_category != expected_category:
                issues.append(
                    ChainValidationIssue(
                        chain_name="building_chain",
                        controller_field="Building_Type__c",
                        controller_value=building_type,
                        dependent_field="Building_Category__c",
                        dependent_value=building_category,
                        valid_values=[expected_category],
                        issue_type="invalid_chain_value",
                        policy_action=policy.value,
                    )
                )
        elif isinstance(expected_category, list):
            if building_category not in expected_category:
                issues.append(
                    ChainValidationIssue(
                        chain_name="building_chain",
                        controller_field="Building_Type__c",
                        controller_value=building_type,
                        dependent_field="Building_Category__c",
                        dependent_value=building_category,
                        valid_values=expected_category,
                        issue_type="invalid_chain_value",
                        policy_action=policy.value,
                    )
                )

        return issues

    def validate_all_chains(
        self,
        record: dict,
        policy: ValidationPolicy = ValidationPolicy.WARN,
    ) -> ChainValidationResult:
        """Run all chain validations and return combined result.

        With WARN policy, is_valid is always True (issues are informational).
        With REJECT policy, is_valid is False if any issues are found.
        """
        issues: list[ChainValidationIssue] = []
        issues.extend(self.validate_acm_chain(record, policy))
        issues.extend(self.validate_building_chain(record, policy))

        if policy == ValidationPolicy.REJECT:
            is_valid = len(issues) == 0
        else:
            # WARN policy: always valid, issues are informational
            is_valid = True

        if issues:
            logger.debug(
                f"Chain validation found {len(issues)} issues "
                f"(policy={policy.value}): "
                f"{[f'{i.controller_field}->{i.dependent_field}' for i in issues]}"
            )

        return ChainValidationResult(is_valid=is_valid, issues=issues)

    def validate_flat_enums(self, record: dict) -> list[ChainValidationIssue]:
        """Validate flat (non-chain) enum fields against SF picklist values.

        Checks sample_result, material_condition, friable, disturbance_potential
        against SF picklist canonical values.

        Special handling:
        - "Not Sampled" / "No Access": Legacy values flagged as needs_user_review
          (not rejected, not auto-corrected).

        Args:
            record: Dict of ACM record field values.

        Returns:
            List of ChainValidationIssue for invalid SF enum values.
        """
        issues: list[ChainValidationIssue] = []

        for internal_name, sf_api_name in SF_FLAT_ENUM_FIELD_MAP.items():
            value = _get_field_value(record, sf_api_name)
            if not value:
                continue

            # Get SF picklist values for this field
            # Try item_fields picklists first, then building_fields, then combined
            sf_values: list[str] = (
                self._bundle.item_fields.picklists.get(sf_api_name)
                or self._bundle.building_fields.picklists.get(sf_api_name)
                or self._bundle.picklists.get(sf_api_name)
                or []
            )

            if not sf_values:
                # No SF picklist data available for this field — skip
                continue

            # Legacy values: flag for user review (non-blocking)
            if value in _LEGACY_VALUES:
                issues.append(
                    ChainValidationIssue(
                        chain_name="flat_enum",
                        controller_field=sf_api_name,
                        controller_value=value,
                        dependent_field=sf_api_name,
                        dependent_value=value,
                        valid_values=sf_values,
                        issue_type="needs_user_review",
                        policy_action="warn",
                    )
                )
                continue

            # Case-insensitive match against SF picklist values
            normalized = _normalize_to_sf_value(value, sf_values)
            if normalized in sf_values:
                continue

            # No match — invalid SF enum value
            issues.append(
                ChainValidationIssue(
                    chain_name="flat_enum",
                    controller_field=sf_api_name,
                    controller_value=value,
                    dependent_field=sf_api_name,
                    dependent_value=value,
                    valid_values=sf_values,
                    issue_type="invalid_sf_enum",
                    policy_action="reject",
                )
            )

        return issues
