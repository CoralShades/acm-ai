"""
Unit tests for the ACM Corrective RAG Validator.

Tests enum validation, business rule validation, required field checks,
and full record validation orchestration.

Story: E1-S15 Corrective RAG Validation Loop
"""

import pytest

from open_notebook.extractors.validators.acm_validator import (
    CorrectionStats,
    ValidationIssue,
    ValidationResult,
    validate_acm_record,
    validate_business_rules,
    validate_enum_fields,
    validate_required_fields,
)


class TestValidateEnumFields:
    """Test suite for validate_enum_fields() — AC #1, #2."""

    def test_valid_enum_values_pass(self):
        """Valid canonical BAR enum values should produce no issues."""
        record = {
            "sample_result": "Positive",
            "material_condition": "Good",
            "friable": "Non-friable",
            "disturbance_potential": "High",
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 0

    def test_invalid_enum_values_caught(self):
        """Invalid enum values should produce validation issues."""
        record = {
            "sample_result": "Bonded",
            "material_condition": "Excellent",
            "friable": "Maybe",
            "disturbance_potential": "Level 3 Risk",
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 4
        fields_flagged = {i.field_name for i in issues}
        assert fields_flagged == {
            "sample_result",
            "material_condition",
            "friable",
            "disturbance_potential",
        }

    def test_none_values_pass(self):
        """None values should not trigger validation issues."""
        record = {
            "sample_result": None,
            "material_condition": None,
            "friable": None,
            "disturbance_potential": None,
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 0

    def test_empty_string_passes(self):
        """Empty strings should not trigger validation issues."""
        record = {
            "sample_result": "",
            "material_condition": "",
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 0

    def test_na_negative_values_pass(self):
        """N/A (negative) and N/A (assumed negative) should be valid."""
        record = {
            "material_condition": "N/A (negative)",
            "disturbance_potential": "N/A (assumed negative)",
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 0

    def test_mixed_valid_and_invalid(self):
        """Only invalid fields should produce issues."""
        record = {
            "sample_result": "Positive",
            "material_condition": "Excellent",  # Invalid
            "friable": "Non-friable",
            "disturbance_potential": "Medium",  # Invalid — BAR uses "Moderate"
        }
        issues = validate_enum_fields(record)
        assert len(issues) == 2
        fields_flagged = {i.field_name for i in issues}
        assert "material_condition" in fields_flagged
        assert "disturbance_potential" in fields_flagged

    def test_issue_contains_valid_values(self):
        """Validation issue should include valid enum values for correction guidance."""
        record = {"sample_result": "Bonded"}
        issues = validate_enum_fields(record)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.field_name == "sample_result"
        assert issue.current_value == "Bonded"
        assert len(issue.valid_values) > 0
        assert "Positive" in issue.valid_values


class TestValidateBusinessRules:
    """Test suite for validate_business_rules() — AC #1, #2."""

    def test_negative_result_requires_na_condition(self):
        """Negative result should flag non-N/A condition."""
        record = {
            "sample_result": "Negative",
            "material_condition": "Good",
            "disturbance_potential": "Low",
        }
        issues = validate_business_rules(record)
        condition_issues = [i for i in issues if i.field_name == "material_condition"]
        disturbance_issues = [
            i for i in issues if i.field_name == "disturbance_potential"
        ]
        assert len(condition_issues) == 1
        assert len(disturbance_issues) == 1

    def test_negative_result_with_na_passes(self):
        """Negative result with N/A (negative) should pass."""
        record = {
            "sample_result": "Negative",
            "material_condition": "N/A (negative)",
            "disturbance_potential": "N/A (negative)",
        }
        issues = validate_business_rules(record)
        assert len(issues) == 0

    def test_assumed_negative_requires_na(self):
        """Assumed Negative result should also flag non-N/A fields."""
        record = {
            "sample_result": "Assumed Negative",
            "material_condition": "Fair",
            "disturbance_potential": "Moderate",
        }
        issues = validate_business_rules(record)
        assert len(issues) >= 2

    def test_positive_result_requires_friability(self):
        """Positive result should flag empty friability."""
        record = {
            "sample_result": "Positive",
            "friable": None,
        }
        issues = validate_business_rules(record)
        friability_issues = [i for i in issues if i.field_name == "friable"]
        assert len(friability_issues) == 1

    def test_positive_result_with_friability_passes(self):
        """Positive result with friable populated should pass."""
        record = {
            "sample_result": "Positive",
            "friable": "Non-friable",
        }
        issues = validate_business_rules(record)
        friability_issues = [i for i in issues if i.field_name == "friable"]
        assert len(friability_issues) == 0

    def test_no_sample_result_skips_rules(self):
        """Missing sample_result should skip business rule checks."""
        record = {
            "sample_result": None,
            "material_condition": "Good",
        }
        issues = validate_business_rules(record)
        assert len(issues) == 0


class TestValidateRequiredFields:
    """Test suite for validate_required_fields() — AC #1."""

    def test_all_required_present(self):
        """All required fields present should produce no issues."""
        record = {
            "building_id": "B001",
            "product": "Floor Tiles",
            "material_description": "Vinyl tiles",
        }
        issues = validate_required_fields(record)
        assert len(issues) == 0

    def test_missing_required_fields(self):
        """Missing required fields should produce issues."""
        record = {
            "building_id": None,
            "product": "",
            "material_description": "Vinyl tiles",
        }
        issues = validate_required_fields(record)
        assert len(issues) == 2
        fields_flagged = {i.field_name for i in issues}
        assert "building_id" in fields_flagged
        assert "product" in fields_flagged


class TestValidateACMRecord:
    """Test suite for validate_acm_record() — orchestration of all validators."""

    def test_valid_record_passes(self):
        """Fully valid record should have is_valid=True and no issues."""
        record = {
            "building_id": "B001",
            "product": "Floor Tiles",
            "material_description": "Vinyl tiles",
            "sample_result": "Positive",
            "material_condition": "Good",
            "friable": "Non-friable",
            "disturbance_potential": "Low",
        }
        result = validate_acm_record(record)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_record_with_enum_errors(self):
        """Record with invalid enum values should have is_valid=False."""
        record = {
            "building_id": "B001",
            "product": "Floor Tiles",
            "material_description": "Vinyl tiles",
            "sample_result": "Positive",
            "material_condition": "Excellent",  # Invalid
            "friable": "Non-friable",
            "disturbance_potential": "Medium",  # Invalid
        }
        result = validate_acm_record(record)
        assert result.is_valid is False
        assert len(result.issues) == 2

    def test_record_with_business_rule_violations(self):
        """Record violating business rules should have is_valid=False."""
        record = {
            "building_id": "B001",
            "product": "Floor Tiles",
            "material_description": "Vinyl tiles",
            "sample_result": "Negative",
            "material_condition": "Good",  # BAR says should be N/A (negative)
            "disturbance_potential": "Low",  # BAR says should be N/A (negative)
        }
        result = validate_acm_record(record)
        assert result.is_valid is False
        assert len(result.issues) >= 2

    def test_record_with_mixed_issues(self):
        """Record with multiple issue types aggregated correctly."""
        record = {
            "building_id": None,  # Missing required
            "product": "Floor Tiles",
            "material_description": "Vinyl tiles",
            "sample_result": "Bonded",  # Invalid enum
        }
        result = validate_acm_record(record)
        assert result.is_valid is False
        assert len(result.issues) >= 2


class TestValidationModels:
    """Test Pydantic validation models."""

    def test_validation_issue_model(self):
        """ValidationIssue should store field details."""
        issue = ValidationIssue(
            field_name="sample_result",
            current_value="Bonded",
            expected_format="enum",
            valid_values=["Positive", "Negative"],
            issue_type="enum_mismatch",
        )
        assert issue.field_name == "sample_result"
        assert issue.current_value == "Bonded"
        assert "Positive" in issue.valid_values

    def test_validation_result_model(self):
        """ValidationResult aggregates issues."""
        issues = [
            ValidationIssue(
                field_name="sample_result",
                current_value="Bonded",
                expected_format="enum",
                valid_values=["Positive"],
                issue_type="enum_mismatch",
            )
        ]
        result = ValidationResult(is_valid=False, issues=issues)
        assert result.is_valid is False
        assert len(result.issues) == 1

    def test_correction_stats_model(self):
        """CorrectionStats tracks counts."""
        stats = CorrectionStats(
            auto_corrected=5,
            llm_corrected=2,
            failed=1,
            total_validated=8,
        )
        assert stats.auto_corrected == 5
        assert stats.total_validated == 8

    def test_correction_stats_defaults(self):
        """CorrectionStats defaults to zeros."""
        stats = CorrectionStats()
        assert stats.auto_corrected == 0
        assert stats.llm_corrected == 0
        assert stats.failed == 0
        assert stats.total_validated == 0


class TestCorrectionPromptTemplate:
    """Test correction prompt template rendering — AC #2."""

    def test_correction_prompt_renders(self):
        """Correction prompt should render with record and issues."""
        from ai_prompter import Prompter

        record = {
            "building_id": "B001",
            "product": "Floor Tiles",
            "sample_result": "Bonded",
            "disturbance_potential": "Medium Risk",
        }
        issues = [
            {
                "field_name": "sample_result",
                "current_value": "Bonded",
                "valid_values": [
                    "Positive",
                    "Assumed Positive",
                    "Negative",
                    "Assumed Negative",
                ],
                "issue_type": "enum_mismatch",
            },
            {
                "field_name": "disturbance_potential",
                "current_value": "Medium Risk",
                "valid_values": ["High", "Moderate", "Low", "Unknown"],
                "issue_type": "enum_mismatch",
            },
        ]

        import json

        prompter = Prompter(prompt_template="acm/correction")
        rendered = prompter.render(
            data={
                "record_json": json.dumps(record, indent=2),
                "validation_issues": issues,
            }
        )

        assert "Bonded" in rendered
        assert "Medium Risk" in rendered
        assert "sample_result" in rendered
        assert "disturbance_potential" in rendered
        assert "Positive" in rendered
        assert "Moderate" in rendered

    def test_correction_prompt_contains_valid_values(self):
        """Rendered prompt should list valid enum values for each issue."""
        import json

        from ai_prompter import Prompter

        issues = [
            {
                "field_name": "friable",
                "current_value": "Bonded",
                "valid_values": ["Non-friable", "Friable"],
                "issue_type": "enum_mismatch",
            }
        ]

        prompter = Prompter(prompt_template="acm/correction")
        rendered = prompter.render(
            data={
                "record_json": json.dumps({"friable": "Bonded"}),
                "validation_issues": issues,
            }
        )

        assert "Non-friable" in rendered
        assert "Friable" in rendered


class TestNormalizerFirstCorrection:
    """Test Layer 1 deterministic correction via normalize_enum_value() — AC #4."""

    def test_medium_normalizes_to_moderate(self):
        """'Medium' should normalize to 'Moderate' via Layer 1 without LLM."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        result = normalize_enum_value("Medium", "disturbance_potential")
        assert result == "Moderate"

    def test_detected_normalizes_to_positive(self):
        """'Detected' should normalize to 'Positive' via Layer 1."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        result = normalize_enum_value("Detected", "sample_result")
        assert result == "Positive"

    def test_not_detected_normalizes_to_negative(self):
        """'Not Detected' should normalize to 'Negative' via Layer 1."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        result = normalize_enum_value("Not Detected", "sample_result")
        assert result == "Negative"

    def test_bonded_not_normalized_by_layer1(self):
        """'Bonded' is not a known synonym and should pass through as-is."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        result = normalize_enum_value("Bonded", "sample_result")
        # "bonded" is not in SAMPLE_RESULT_SYNONYMS, passes through
        assert result == "Bonded"

    def test_friability_bonded_normalizes_to_non_friable(self):
        """'Bonded' should normalize to 'Non-friable' via friability normalizer."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        result = normalize_enum_value("Bonded", "friability")
        assert result == "Non-friable"


class TestCorrectiveLoopRouter:
    """Test should_correct routing logic — AC #3, #6."""

    def test_should_correct_routes_to_correct_when_issues_exist(self):
        """Records with validation issues should route to 'correct'."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import should_correct

        record = ACMExtractionRecord(
            building_id="B001",
            product="Floor Tiles",
            material_description="Vinyl tiles",
            result="Positive",
            sample_result="Bonded",  # Invalid enum
            material_condition="Good",
            friable="Non-friable",
            disturbance_potential="Low",
        )

        state = {
            "records": [record],
            "correction_attempt": 0,
            "max_correction_attempts": 2,
            "enable_corrective_loop": True,
        }

        result = should_correct(state)
        assert result == "correct"

    def test_should_correct_routes_to_deduplicate_when_valid(self):
        """Records with no issues should route to 'deduplicate'."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import should_correct

        record = ACMExtractionRecord(
            building_id="B001",
            product="Floor Tiles",
            material_description="Vinyl tiles",
            result="Positive",
            sample_result="Positive",
            material_condition="Good",
            friable="Non-friable",
            disturbance_potential="Low",
        )

        state = {
            "records": [record],
            "correction_attempt": 0,
            "max_correction_attempts": 2,
            "enable_corrective_loop": True,
        }

        result = should_correct(state)
        assert result == "deduplicate"

    def test_loop_terminates_after_max_attempts(self):
        """Should route to 'deduplicate' when max_correction_attempts reached — AC #3."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import should_correct

        record = ACMExtractionRecord(
            building_id="B001",
            product="Floor Tiles",
            material_description="Vinyl tiles",
            result="Positive",
            sample_result="Bonded",  # Still invalid after max attempts
            material_condition="Good",
            friable="Non-friable",
            disturbance_potential="Low",
        )

        state = {
            "records": [record],
            "correction_attempt": 2,  # Already at max
            "max_correction_attempts": 2,
            "enable_corrective_loop": True,
        }

        result = should_correct(state)
        assert result == "deduplicate"

    def test_disabled_loop_skips_correction(self):
        """enable_corrective_loop=False should skip correction entirely — AC #6."""
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord
        from open_notebook.graphs.acm_extraction import should_correct

        record = ACMExtractionRecord(
            building_id="B001",
            product="Floor Tiles",
            material_description="Vinyl tiles",
            result="Positive",
            sample_result="Bonded",  # Has issues, but loop disabled
            material_condition="Good",
            friable="Non Friable",
            disturbance_potential="Low",
        )

        state = {
            "records": [record],
            "correction_attempt": 0,
            "max_correction_attempts": 2,
            "enable_corrective_loop": False,
        }

        result = should_correct(state)
        assert result == "deduplicate"

    def test_empty_records_routes_to_deduplicate(self):
        """No records should route to 'deduplicate'."""
        from open_notebook.graphs.acm_extraction import should_correct

        state = {
            "records": [],
            "correction_attempt": 0,
            "max_correction_attempts": 2,
            "enable_corrective_loop": True,
        }

        result = should_correct(state)
        assert result == "deduplicate"


class TestCorrectionStatsAccumulation:
    """Test CorrectionStats accumulation across multiple records — AC #5, #8."""

    def test_stats_accumulate_auto_corrections(self):
        """Stats should count each auto-correction separately."""
        stats = CorrectionStats()

        # Simulate 3 auto-corrections
        for _ in range(3):
            stats.auto_corrected += 1

        assert stats.auto_corrected == 3
        assert stats.llm_corrected == 0
        assert stats.failed == 0

    def test_stats_accumulate_mixed_corrections(self):
        """Stats should track auto, llm, and failed independently."""
        stats = CorrectionStats(
            auto_corrected=5,
            llm_corrected=2,
            failed=1,
            total_validated=10,
        )

        # Add more corrections
        stats.auto_corrected += 3
        stats.llm_corrected += 1
        stats.total_validated += 5

        assert stats.auto_corrected == 8
        assert stats.llm_corrected == 3
        assert stats.failed == 1
        assert stats.total_validated == 15

    def test_correction_stats_dict_pattern(self):
        """Stats dict pattern used in ExtractionState should work correctly."""
        # This mirrors the actual pattern in acm_extraction.py
        correction_stats = {
            "auto_corrected": 0,
            "llm_corrected": 0,
            "failed": 0,
            "total_validated": 0,
        }

        # Simulate corrections
        correction_stats["auto_corrected"] = (
            correction_stats.get("auto_corrected", 0) + 1
        )
        correction_stats["total_validated"] = (
            correction_stats.get("total_validated", 0) + 1
        )
        correction_stats["llm_corrected"] = correction_stats.get("llm_corrected", 0) + 1
        correction_stats["total_validated"] = (
            correction_stats.get("total_validated", 0) + 1
        )
        correction_stats["failed"] = correction_stats.get("failed", 0) + 1
        correction_stats["total_validated"] = (
            correction_stats.get("total_validated", 0) + 1
        )

        assert correction_stats["auto_corrected"] == 1
        assert correction_stats["llm_corrected"] == 1
        assert correction_stats["failed"] == 1
        assert correction_stats["total_validated"] == 3
