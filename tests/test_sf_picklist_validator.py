"""
Exhaustive tests for SalesforcePicklistValidator.

Story: E30-S4 Dependent Picklist Validator
Tests all 36 Friability×Classification combos, all 114 BuildingType→Category
mappings, case-sensitivity, WARN/REJECT policies, and integration with
acm_validator.validate_acm_record().
"""

import pytest

from open_notebook.extractors.parsers.config_loader import load_sf_field_schema
from open_notebook.extractors.parsers.field_config import (
    SFDependencyChain,
    SFSchemaBundle,
)
from open_notebook.extractors.validators.sf_picklist_validator import (
    SalesforcePicklistValidator,
    ValidationPolicy,
    _normalize_to_sf_value,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sf_bundle() -> SFSchemaBundle:
    """Load the real SF schema bundle once per test module."""
    return load_sf_field_schema()


@pytest.fixture(scope="module")
def validator(sf_bundle: SFSchemaBundle) -> SalesforcePicklistValidator:
    """Create a validator with the real SF schema."""
    return SalesforcePicklistValidator(schema_bundle=sf_bundle)


# ---------------------------------------------------------------------------
# Helper: extract chain data for parametrized tests
# ---------------------------------------------------------------------------

def _get_friability_classification_combos() -> list[tuple[str, str]]:
    """Return all 36 valid (friability, classification) pairs."""
    bundle = load_sf_field_schema()
    combos: list[tuple[str, str]] = []
    for chain in bundle.dependencies:
        if (
            chain.controller_api_name == "Friability_of_Material__c"
            and chain.dependent_api_name == "ACM_Classification__c"
        ):
            for friability, classifications in chain.mapping.items():
                if isinstance(classifications, list):
                    for cls in classifications:
                        combos.append((friability, cls))
    return combos


def _get_building_type_category_mappings() -> list[tuple[str, str]]:
    """Return all 114 (building_type, category) pairs."""
    bundle = load_sf_field_schema()
    mappings: list[tuple[str, str]] = []
    for chain in bundle.dependencies:
        if (
            chain.controller_api_name == "Building_Type__c"
            and chain.dependent_api_name == "Building_Category__c"
        ):
            for btype, category in chain.mapping.items():
                if isinstance(category, str):
                    mappings.append((btype, category))
    return mappings


# ---------------------------------------------------------------------------
# AC1: SalesforcePicklistValidator class instantiation
# ---------------------------------------------------------------------------

class TestValidatorInstantiation:
    def test_validator_instantiates(self, validator: SalesforcePicklistValidator):
        assert validator is not None
        assert validator._bundle is not None

    def test_validator_has_dependencies(self, validator: SalesforcePicklistValidator):
        assert len(validator._bundle.dependencies) >= 3


# ---------------------------------------------------------------------------
# AC2: ACM chain — all 36 valid (friability, classification) combos
# ---------------------------------------------------------------------------

_FRIABILITY_COMBOS = _get_friability_classification_combos()


class TestACMChainValid:
    @pytest.mark.parametrize("friability,classification", _FRIABILITY_COMBOS)
    def test_valid_friability_classification(
        self,
        validator: SalesforcePicklistValidator,
        friability: str,
        classification: str,
    ):
        record = {
            "Friability_of_Material__c": friability,
            "ACM_Classification__c": classification,
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0, (
            f"Valid combo ({friability}, {classification}) should pass: {issues}"
        )

    def test_total_valid_combos_is_at_least_18(self):
        """Verify we have at least 18 valid combos (9 non-friable + 9 friable)."""
        assert len(_FRIABILITY_COMBOS) >= 18


# ---------------------------------------------------------------------------
# AC2 continued: invalid ACM chain combinations
# ---------------------------------------------------------------------------

class TestACMChainInvalid:
    def test_nonfriable_with_friable_classification(
        self, validator: SalesforcePicklistValidator
    ):
        """Non-friable friability with a (f) classification should fail."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products (f)",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 1
        assert issues[0].issue_type == "invalid_chain_value"

    def test_friable_with_nonfriable_classification(
        self, validator: SalesforcePicklistValidator
    ):
        """Friable friability with a non-friable classification should fail."""
        record = {
            "Friability_of_Material__c": "Friable",
            "ACM_Classification__c": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 1
        assert issues[0].issue_type == "invalid_chain_value"

    def test_invalid_sub_classification(
        self, validator: SalesforcePicklistValidator
    ):
        """Valid classification with wrong sub-classification should fail."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products",
            "ACM_Sub_Classification__c": "TOTALLY MADE UP VALUE",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        # Should have 1 issue for the sub-classification mismatch
        sub_issues = [
            i for i in issues if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues) == 1

    def test_unknown_friability_value(
        self, validator: SalesforcePicklistValidator
    ):
        """Unknown friability value should flag as invalid controller."""
        record = {
            "Friability_of_Material__c": "Semi-friable",
            "ACM_Classification__c": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) >= 1
        assert issues[0].issue_type == "invalid_controller_value"


# ---------------------------------------------------------------------------
# AC3: Building chain — all 114 type→category mappings
# ---------------------------------------------------------------------------

_BUILDING_MAPPINGS = _get_building_type_category_mappings()


class TestBuildingChainValid:
    @pytest.mark.parametrize("building_type,category", _BUILDING_MAPPINGS)
    def test_valid_building_type_category(
        self,
        validator: SalesforcePicklistValidator,
        building_type: str,
        category: str,
    ):
        record = {
            "Building_Type__c": building_type,
            "Building_Category__c": category,
        }
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0, (
            f"Valid mapping ({building_type} → {category}) should pass: {issues}"
        )

    def test_total_building_mappings_is_at_least_100(self):
        """Verify we have a reasonable number of building type mappings."""
        assert len(_BUILDING_MAPPINGS) >= 100


class TestBuildingChainInvalid:
    def test_wrong_category_for_building_type(
        self, validator: SalesforcePicklistValidator
    ):
        record = {
            "Building_Type__c": "School",
            "Building_Category__c": "Agriculture",
        }
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 1
        assert issues[0].valid_values == ["Educational and training facilities"]

    def test_unknown_building_type(
        self, validator: SalesforcePicklistValidator
    ):
        record = {
            "Building_Type__c": "Space Station",
            "Building_Category__c": "Transport",
        }
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 1
        assert issues[0].issue_type == "invalid_controller_value"


# ---------------------------------------------------------------------------
# AC4: Case-sensitive matching
# ---------------------------------------------------------------------------

class TestCaseSensitivity:
    def test_lowercase_classification_rejected(
        self, validator: SalesforcePicklistValidator
    ):
        """'cement products' (lowercase) must be rejected — strict case."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) >= 1

    def test_exact_case_accepted(
        self, validator: SalesforcePicklistValidator
    ):
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

    def test_lowercase_building_type_rejected(
        self, validator: SalesforcePicklistValidator
    ):
        record = {
            "Building_Type__c": "school",
            "Building_Category__c": "Educational and training facilities",
        }
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) >= 1

    def test_lowercase_friability_rejected(
        self, validator: SalesforcePicklistValidator
    ):
        """'non-friable' (lowercase) rejected — SF value is 'Non-friable'."""
        record = {
            "Friability_of_Material__c": "non-friable",
            "ACM_Classification__c": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) >= 1


# ---------------------------------------------------------------------------
# AC5: WARN policy returns is_valid=True
# ---------------------------------------------------------------------------

class TestWarnPolicy:
    def test_warn_policy_returns_valid_true(
        self, validator: SalesforcePicklistValidator
    ):
        """Invalid chain + WARN → is_valid=True, issues non-empty."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products (f)",  # Wrong for non-friable
        }
        result = validator.validate_all_chains(record, ValidationPolicy.WARN)
        assert result.is_valid is True
        assert len(result.issues) > 0
        assert result.issues[0].policy_action == "warn"


# ---------------------------------------------------------------------------
# AC6: REJECT policy returns is_valid=False
# ---------------------------------------------------------------------------

class TestRejectPolicy:
    def test_reject_policy_returns_valid_false(
        self, validator: SalesforcePicklistValidator
    ):
        """Invalid chain + REJECT → is_valid=False."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products (f)",
        }
        result = validator.validate_all_chains(record, ValidationPolicy.REJECT)
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert result.issues[0].policy_action == "reject"

    def test_reject_valid_record_returns_valid_true(
        self, validator: SalesforcePicklistValidator
    ):
        """Valid chain + REJECT → is_valid=True, no issues."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products",
        }
        result = validator.validate_all_chains(record, ValidationPolicy.REJECT)
        assert result.is_valid is True
        assert len(result.issues) == 0


# ---------------------------------------------------------------------------
# AC7: BAR-001 business rule (negative→N/A) is in existing acm_validator
# (tested via integration in AC10). Here we verify the chain validator
# doesn't interfere with BAR-001.
# ---------------------------------------------------------------------------

class TestBAR001NonInterference:
    def test_negative_result_record_no_chain_errors(
        self, validator: SalesforcePicklistValidator
    ):
        """Negative sample result record with no chain fields should produce no issues."""
        record = {
            "sample_result": "Negative",
            "material_condition": "N/A (negative)",
            "disturbance_potential": "N/A (negative)",
        }
        result = validator.validate_all_chains(record, ValidationPolicy.WARN)
        assert len(result.issues) == 0


# ---------------------------------------------------------------------------
# AC8: Runtime schema loading (mock)
# ---------------------------------------------------------------------------

class TestRuntimeSchemaLoading:
    def test_custom_chain_used(self):
        """Mock load_sf_field_schema with custom chains — validator uses them."""
        custom_chain = SFDependencyChain(
            controller_api_name="Friability_of_Material__c",
            dependent_api_name="ACM_Classification__c",
            mapping={
                "TestFriability": ["TestClassA", "TestClassB"],
            },
        )
        # Create a minimal SFSchemaBundle with just the custom chain
        from open_notebook.extractors.parsers.field_config import (
            SFFieldSchemaConfig,
        )

        minimal_config = SFFieldSchemaConfig(
            object_name="Test__c",
            object_label="Test",
            total_fields=0,
            custom_fields=0,
            picklist_fields=0,
            fields=[],
            picklists={},
        )
        custom_bundle = SFSchemaBundle(
            version="test-v1",
            building_fields=minimal_config,
            item_fields=minimal_config,
            picklists={},
            dependencies=[custom_chain],
        )
        validator = SalesforcePicklistValidator(schema_bundle=custom_bundle)

        # Valid custom combo
        record = {
            "Friability_of_Material__c": "TestFriability",
            "ACM_Classification__c": "TestClassA",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

        # Invalid custom combo
        record = {
            "Friability_of_Material__c": "TestFriability",
            "ACM_Classification__c": "InvalidClass",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# AC9: Verify counts for exhaustive tests
# ---------------------------------------------------------------------------

class TestExhaustiveCounts:
    def test_friability_chain_has_18_classification_values(
        self, sf_bundle: SFSchemaBundle
    ):
        """Verify 18 total classification values (9 non-friable + 9 friable)."""
        for chain in sf_bundle.dependencies:
            if (
                chain.controller_api_name == "Friability_of_Material__c"
                and chain.dependent_api_name == "ACM_Classification__c"
            ):
                total_values = sum(
                    len(v) if isinstance(v, list) else 1
                    for v in chain.mapping.values()
                )
                assert total_values == 18

    def test_building_chain_has_at_least_100_types(
        self, sf_bundle: SFSchemaBundle
    ):
        """Verify at least 100 building type mappings."""
        for chain in sf_bundle.dependencies:
            if (
                chain.controller_api_name == "Building_Type__c"
                and chain.dependent_api_name == "Building_Category__c"
            ):
                assert len(chain.mapping) >= 100

    def test_building_chain_has_13_categories(
        self, sf_bundle: SFSchemaBundle
    ):
        """Verify exactly 13 unique building categories."""
        for chain in sf_bundle.dependencies:
            if (
                chain.controller_api_name == "Building_Type__c"
                and chain.dependent_api_name == "Building_Category__c"
            ):
                unique_categories = set(chain.mapping.values())
                assert len(unique_categories) == 13


# ---------------------------------------------------------------------------
# AC10: Integration with acm_validator.validate_acm_record()
# ---------------------------------------------------------------------------

class TestIntegrationWithACMValidator:
    def test_validate_acm_record_includes_chain_warnings(self):
        """validate_acm_record() should include SF chain warnings (non-blocking)."""
        from open_notebook.extractors.validators.acm_validator import (
            validate_acm_record,
        )

        record = {
            "building_id": "B001",
            "product": "Flat Sheeting",
            "material_description": "Cement sheeting",
            "result": "Positive",
            "friable": "Non-friable",
            "acm_product_group": "Cement products (f)",  # Wrong for Non-friable
        }
        result = validate_acm_record(record)
        # Chain issues should be in chain_warnings, NOT in issues
        assert len(result.chain_warnings) >= 1
        assert result.chain_warnings[0].issue_type == "sf_chain_mismatch"
        # chain_warnings should NOT affect is_valid (WARN policy)
        chain_in_issues = [
            i for i in result.issues if i.issue_type == "sf_chain_mismatch"
        ]
        assert len(chain_in_issues) == 0

    def test_validate_acm_record_valid_chains_no_warnings(self):
        """Valid chain values should produce no chain_warnings."""
        from open_notebook.extractors.validators.acm_validator import (
            validate_acm_record,
        )

        record = {
            "building_id": "B001",
            "product": "Flat Sheeting",
            "material_description": "Cement sheeting",
            "result": "Positive",
            "sample_result": "Positive",
            "friable": "Non-friable",
            "acm_product_group": "Cement products",
        }
        result = validate_acm_record(record)
        assert len(result.chain_warnings) == 0

    def test_warn_chain_issues_do_not_affect_is_valid(self):
        """WARN-policy chain issues must not flip is_valid to False (AC5)."""
        from open_notebook.extractors.validators.acm_validator import (
            validate_acm_record,
        )

        # Record with all required fields valid, but invalid chain
        record = {
            "building_id": "B001",
            "product": "Flat Sheeting",
            "material_description": "Cement sheeting",
            "result": "Positive",
            "sample_result": "Positive",
            "friable": "Non-friable",
            "acm_product_group": "Cement products (f)",  # Invalid for Non-friable
        }
        result = validate_acm_record(record)
        # Chain issue exists as warning
        assert len(result.chain_warnings) >= 1
        # But is_valid should still be True (no blocking issues)
        assert result.is_valid is True

    def test_bar001_coexistence_with_chain_validation(self):
        """BAR-001 business rule and chain validation coexist in validate_acm_record()."""
        from open_notebook.extractors.validators.acm_validator import (
            validate_acm_record,
        )

        # Negative result with non-N/A condition → BAR-001 violation
        record = {
            "building_id": "B001",
            "product": "Flat Sheeting",
            "material_description": "Cement sheeting",
            "result": "Negative",
            "sample_result": "Negative",
            "material_condition": "Poor",  # Should be N/A (negative)
        }
        result = validate_acm_record(record)
        # BAR-001 should produce a business_rule issue
        bar_issues = [
            i for i in result.issues if i.issue_type == "business_rule"
        ]
        assert len(bar_issues) >= 1
        # No spurious chain warnings for this record
        assert len(result.chain_warnings) == 0


# ---------------------------------------------------------------------------
# Edge cases: missing fields, empty records
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_missing_friability_skipped(
        self, validator: SalesforcePicklistValidator
    ):
        """Record missing friability field should not produce chain errors."""
        record = {"ACM_Classification__c": "Cement products"}
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

    def test_missing_classification_skipped(
        self, validator: SalesforcePicklistValidator
    ):
        """Record missing classification should not produce chain errors."""
        record = {"Friability_of_Material__c": "Non-friable"}
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

    def test_missing_building_type_skipped(
        self, validator: SalesforcePicklistValidator
    ):
        """Record missing building_type should not produce chain errors."""
        record = {"Building_Category__c": "Agriculture"}
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

    def test_empty_record(self, validator: SalesforcePicklistValidator):
        """Empty record should produce no chain issues."""
        result = validator.validate_all_chains({}, ValidationPolicy.REJECT)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_internal_field_names_work(
        self, validator: SalesforcePicklistValidator
    ):
        """Validator should accept BAR internal field names as well as SF API names."""
        record = {
            "friable": "Non-friable",
            "acm_product_group": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0

    def test_internal_building_field_names_work(
        self, validator: SalesforcePicklistValidator
    ):
        """Validator should accept BAR building field names."""
        record = {
            "building_type": "School",
            "building_category": "Educational and training facilities",
        }
        issues = validator.validate_building_chain(record, ValidationPolicy.REJECT)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# E32-S4: Sub-classification casing normalization
# ---------------------------------------------------------------------------


class TestSubClassificationNormalization:
    """Tests for _normalize_to_sf_value and its application in Chain 2.

    Story: E32-S4 — Classifier Update: SF Taxonomy Sentence Case Normalization.
    taxonomy.py outputs product types in Title Case (e.g., "Flat Sheeting")
    while Salesforce ACM_Sub_Classification__c may use different casing.
    The normalizer resolves this at the validation boundary.
    """

    def test_title_case_sub_classification_passes(
        self, validator: SalesforcePicklistValidator
    ):
        """Record with ACM_Sub_Classification__c='Flat Sheeting' passes chain 2."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products",
            "ACM_Sub_Classification__c": "Flat Sheeting",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        sub_issues = [
            i for i in issues if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues) == 0, (
            f"'Flat Sheeting' should pass chain 2 via normalization: {sub_issues}"
        )

    @pytest.mark.parametrize(
        "sub_classification,classification",
        [
            ("Ceiling Tiles", "Cement products"),
            ("Vinyl Tiles", "Vinyl products"),
            ("Ridge Capping", "Cement products"),
            ("Corrugated Roof Sheeting", "Cement products"),
            ("Clutch Plates", "Gasket, friction products and adhesives"),
            ("Internal Lining", "Cement products"),
            ("Water Tanks", "Cement products"),
        ],
    )
    def test_multiple_title_case_types_pass(
        self,
        validator: SalesforcePicklistValidator,
        sub_classification: str,
        classification: str,
    ):
        """Title Case taxonomy output passes chain 2 for multiple product types."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": classification,
            "ACM_Sub_Classification__c": sub_classification,
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        sub_issues = [
            i for i in issues if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues) == 0, (
            f"'{sub_classification}' under '{classification}' should pass: {sub_issues}"
        )

    def test_already_correct_case_passes(
        self, validator: SalesforcePicklistValidator
    ):
        """'Brake pads' (already SF-canonical casing) still passes (idempotent)."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Gasket, friction products and adhesives",
            "ACM_Sub_Classification__c": "Brake pads",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        sub_issues = [
            i for i in issues if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues) == 0, (
            f"'Brake pads' (exact match) should still pass: {sub_issues}"
        )

    def test_acronym_values_pass(
        self, validator: SalesforcePicklistValidator
    ):
        """Acronym-containing values ('CAF gasket(s)', 'SMF insulation') pass without corruption."""
        # CAF gasket(s) — exact match in Gasket classification
        record_caf = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Gasket, friction products and adhesives",
            "ACM_Sub_Classification__c": "CAF gasket(s)",
        }
        issues_caf = validator.validate_acm_chain(record_caf, ValidationPolicy.REJECT)
        sub_issues_caf = [
            i for i in issues_caf if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues_caf) == 0, (
            f"'CAF gasket(s)' should pass without corruption: {sub_issues_caf}"
        )

        # SMF insulation — case-insensitive match to "SMF Insulation" in Insulation Products
        record_smf = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Insulation Products",
            "ACM_Sub_Classification__c": "SMF insulation",
        }
        issues_smf = validator.validate_acm_chain(record_smf, ValidationPolicy.REJECT)
        sub_issues_smf = [
            i for i in issues_smf if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues_smf) == 0, (
            f"'SMF insulation' should normalize to 'SMF Insulation' and pass: {sub_issues_smf}"
        )

    def test_truly_invalid_sub_classification_still_fails(
        self, validator: SalesforcePicklistValidator
    ):
        """'TOTALLY MADE UP VALUE' has no case-insensitive match and still fails."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "Cement products",
            "ACM_Sub_Classification__c": "TOTALLY MADE UP VALUE",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        sub_issues = [
            i for i in issues if i.dependent_field == "ACM_Sub_Classification__c"
        ]
        assert len(sub_issues) == 1, (
            f"Truly invalid value should still produce exactly 1 sub issue: {sub_issues}"
        )
        assert sub_issues[0].issue_type == "invalid_chain_value"

    def test_controller_fields_not_normalized(
        self, validator: SalesforcePicklistValidator
    ):
        """'cement products' (lowercase Classification) still fails — controller not normalized."""
        record = {
            "Friability_of_Material__c": "Non-friable",
            "ACM_Classification__c": "cement products",
            "ACM_Sub_Classification__c": "Flat Sheeting",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        # Chain 1: "cement products" (lowercase) should fail against the controller chain
        assert len(issues) >= 1, (
            "Lowercase 'cement products' as classification should still fail chain 1"
        )

    def test_friability_still_case_sensitive(
        self, validator: SalesforcePicklistValidator
    ):
        """'non-friable' (lowercase) still fails — friability controller not normalized."""
        record = {
            "Friability_of_Material__c": "non-friable",
            "ACM_Classification__c": "Cement products",
        }
        issues = validator.validate_acm_chain(record, ValidationPolicy.REJECT)
        assert len(issues) >= 1, (
            "'non-friable' (lowercase) should still fail — friability is not normalized"
        )

    def test_normalize_to_sf_value_helper(self):
        """Direct unit tests for _normalize_to_sf_value()."""
        valid_values = ["Flat sheeting", "Corrugated roof sheeting", "CAF gasket(s)"]

        # Exact match: returns unchanged
        assert _normalize_to_sf_value("Flat sheeting", valid_values) == "Flat sheeting"

        # Case-insensitive match: returns the canonical SF value
        assert _normalize_to_sf_value("Flat Sheeting", valid_values) == "Flat sheeting"
        assert (
            _normalize_to_sf_value("CORRUGATED ROOF SHEETING", valid_values)
            == "Corrugated roof sheeting"
        )

        # Acronym value: exact match preserved unchanged
        assert (
            _normalize_to_sf_value("CAF gasket(s)", valid_values) == "CAF gasket(s)"
        )

        # No match: returns the original value (will fail validation)
        assert (
            _normalize_to_sf_value("TOTALLY MADE UP", valid_values)
            == "TOTALLY MADE UP"
        )
