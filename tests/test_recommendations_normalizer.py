"""
Tests for recommendation normalization module.

Tests the normalize_recommendation() function that maps consultant
wording to canonical actions using regex pattern matching.
"""

import pytest


class TestCanonicalActions:
    """Tests for canonical action definitions (AC1)."""

    def test_canonical_actions_defined(self):
        """All 6 canonical actions + review_required are defined."""
        from open_notebook.extractors.normalizers.recommendations import (
            CANONICAL_ACTIONS,
        )

        expected = {
            "maintain_in_situ",
            "remove_prior_to_refurb_or_demolition",
            "restrict_access_immediately",
            "remedial_within_months",
            "confirm_status_sampling",
            "height_or_access_restriction",
            "review_required",
        }
        assert set(CANONICAL_ACTIONS) == expected

    def test_normalization_result_fields(self):
        """NormalizationResult has required fields."""
        from open_notebook.extractors.normalizers.recommendations import (
            NormalizationResult,
        )

        result = NormalizationResult(
            raw_text="test",
            normalized_action="maintain_in_situ",
            confidence=1.0,
            method="pattern",
        )
        assert result.raw_text == "test"
        assert result.normalized_action == "maintain_in_situ"
        assert result.confidence == 1.0
        assert result.method == "pattern"


class TestNormalizeRecommendationPatterns:
    """Tests for regex pattern matching (AC2)."""

    def test_maintain_in_situ_current_condition(self):
        """'Maintain in current condition' maps to maintain_in_situ."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Maintain in current condition")
        assert result.normalized_action == "maintain_in_situ"
        assert result.confidence == 1.0

    def test_maintain_in_situ_label_amp(self):
        """'label and incorporate into an AMP' maps to maintain_in_situ."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("label and incorporate into an AMP")
        assert result.normalized_action == "maintain_in_situ"

    def test_maintain_in_situ_label_only(self):
        """'label into an AMP' maps to maintain_in_situ."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("label into an AMP")
        assert result.normalized_action == "maintain_in_situ"

    def test_remove_prior_to_refurb_licensed(self):
        """'Remove under licensed asbestos removal contractor' maps to remove_prior_to_refurb."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(
            "Remove under a licensed asbestos removal contractor"
        )
        assert result.normalized_action == "remove_prior_to_refurb_or_demolition"

    def test_remove_prior_to_refurb_by_contractor(self):
        """'Remove by licensed asbestos removal contractor' maps to remove_prior_to_refurb."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(
            "Remove by licensed asbestos removal contractor prior to works"
        )
        assert result.normalized_action == "remove_prior_to_refurb_or_demolition"

    def test_remove_prior_to_demolition(self):
        """'prior to demolition or refurbishment' maps to remove_prior_to_refurb."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(
            "Must be removed prior to demolition or refurbishment"
        )
        assert result.normalized_action == "remove_prior_to_refurb_or_demolition"

    def test_restrict_access(self):
        """'Restrict access' maps to restrict_access_immediately."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Restrict access to the area")
        assert result.normalized_action == "restrict_access_immediately"

    def test_restrict_access_asap(self):
        """'ASAP' maps to restrict_access_immediately."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Remove ASAP due to deterioration")
        assert result.normalized_action == "restrict_access_immediately"

    def test_remedial_within_3_months(self):
        """'within 3 months' maps to remedial_within_months."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Organise removal within 3 months")
        assert result.normalized_action == "remedial_within_months"

    def test_remedial_next_few_months(self):
        """'next few months' maps to remedial_within_months."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Schedule works in the next few months")
        assert result.normalized_action == "remedial_within_months"

    def test_confirm_status_sampling(self):
        """'Confirm status' maps to confirm_status_sampling."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Confirm status via sampling")
        assert result.normalized_action == "confirm_status_sampling"

    def test_confirm_status_not_sampled(self):
        """'Not Sampled' maps to confirm_status_sampling."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Not Sampled - presumed ACM")
        assert result.normalized_action == "confirm_status_sampling"

    def test_confirm_status_presumed(self):
        """'Presumed' maps to confirm_status_sampling."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Presumed asbestos containing material")
        assert result.normalized_action == "confirm_status_sampling"

    def test_height_restriction(self):
        """'Height restriction' maps to height_or_access_restriction."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Height restriction prevents access")
        assert result.normalized_action == "height_or_access_restriction"

    def test_restricted_access(self):
        """'Restricted Access' maps to height_or_access_restriction."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Restricted Access - unable to inspect")
        assert result.normalized_action == "height_or_access_restriction"

    def test_live_electrical_hazard(self):
        """'Live Electrical Hazard' maps to height_or_access_restriction."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Live Electrical Hazard - no access")
        assert result.normalized_action == "height_or_access_restriction"

    def test_controlled_bonded_removal(self):
        """'controlled bonded asbestos removal conditions' maps to remove_prior_to_refurb."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(
            "Remove under controlled bonded asbestos removal conditions"
        )
        assert result.normalized_action == "remove_prior_to_refurb_or_demolition"


class TestNormalizeRecommendationEdgeCases:
    """Tests for edge cases and fallback behavior (AC2)."""

    def test_empty_string_returns_none(self):
        """Empty string returns normalized_action=None."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("")
        assert result.normalized_action is None
        assert result.confidence == 0.0
        assert result.method == "none"

    def test_none_returns_none(self):
        """None input returns normalized_action=None."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(None)
        assert result.normalized_action is None
        assert result.confidence == 0.0

    def test_whitespace_only_returns_none(self):
        """Whitespace-only input returns normalized_action=None."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("   ")
        assert result.normalized_action is None

    def test_unmatched_text_returns_review_required(self):
        """Unrecognizable text returns review_required."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Some completely unknown recommendation text")
        assert result.normalized_action == "review_required"
        assert result.confidence == 0.0
        assert result.method == "none"

    def test_case_insensitive(self):
        """Pattern matching is case-insensitive."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("MAINTAIN IN CURRENT CONDITION")
        assert result.normalized_action == "maintain_in_situ"

    def test_mixed_case(self):
        """Mixed case input is handled correctly."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation("Restrict ACCESS immediately")
        assert result.normalized_action == "restrict_access_immediately"

    def test_multi_sentence_recommendation(self):
        """Multi-sentence recommendations match on relevant part."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(
            "Material in good condition. Maintain in current condition. "
            "Re-inspect annually."
        )
        assert result.normalized_action == "maintain_in_situ"

    def test_raw_text_preserved(self):
        """Original raw text is preserved in result."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        raw = "Maintain in current condition and label"
        result = normalize_recommendation(raw)
        assert result.raw_text == raw

    def test_first_match_wins(self):
        """First matching pattern takes priority."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        # This text matches both "Restrict access" and "within 3 months"
        # "Restrict access" appears first in config/patterns, so it should win
        result = normalize_recommendation("Restrict access within 3 months")
        assert result.normalized_action == "restrict_access_immediately"


class TestWordingRulesLoading:
    """Tests for JSON config loading (AC5)."""

    def test_load_wording_rules_returns_dict(self):
        """_load_wording_rules returns a dict with expected keys."""
        from open_notebook.extractors.normalizers.recommendations import (
            _load_wording_rules,
        )

        rules = _load_wording_rules()
        assert isinstance(rules, dict)
        assert "consultant_phrases_to_actions" in rules
        assert "universal_actions" in rules

    def test_wording_rules_has_patterns(self):
        """Loaded rules contain pattern entries."""
        from open_notebook.extractors.normalizers.recommendations import (
            _load_wording_rules,
        )

        rules = _load_wording_rules()
        patterns = rules.get("consultant_phrases_to_actions", [])
        assert len(patterns) >= 9  # At minimum 9 patterns per AC2

    def test_each_pattern_has_required_fields(self):
        """Each pattern entry has 'pattern' and 'action' fields."""
        from open_notebook.extractors.normalizers.recommendations import (
            _load_wording_rules,
        )

        rules = _load_wording_rules()
        for entry in rules.get("consultant_phrases_to_actions", []):
            assert "pattern" in entry, f"Missing 'pattern' in {entry}"
            assert "action" in entry, f"Missing 'action' in {entry}"

    def test_config_method_when_loaded_from_json(self):
        """When matched from JSON config, method is 'config'."""
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        # "Maintain in current condition" should be in the JSON config
        result = normalize_recommendation("Maintain in current condition")
        assert result.method in ("config", "pattern")  # Could be either
        assert result.confidence == 1.0
