"""
Tests for enum value normalization module.

Tests the normalize_enum_value() function that standardizes
ACM field values (SampleResult, Condition, DisturbancePotential)
to their canonical BAR-compliant forms.
"""

import pytest


class TestSampleResultNormalization:
    """Tests for SampleResult enum normalization (AC3)."""

    def test_positive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("positive", "sample_result") == "Positive"

    def test_pos(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("pos", "sample_result") == "Positive"

    def test_detected(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("detected", "sample_result") == "Positive"

    def test_negative(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("negative", "sample_result") == "Negative"

    def test_neg(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("neg", "sample_result") == "Negative"

    def test_not_detected(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("not detected", "sample_result") == "Negative"

    def test_presumed(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("presumed", "sample_result") == "Assumed Positive"

    def test_presumed_positive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert (
            normalize_enum_value("presumed positive", "sample_result")
            == "Assumed Positive"
        )

    def test_assumed(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("assumed", "sample_result") == "Assumed Positive"

    def test_assumed_positive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert (
            normalize_enum_value("assumed positive", "sample_result")
            == "Assumed Positive"
        )

    def test_not_sampled(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert (
            normalize_enum_value("not sampled", "sample_result") == "Assumed Positive"
        )

    def test_case_insensitive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("POSITIVE", "sample_result") == "Positive"
        assert normalize_enum_value("Negative", "sample_result") == "Negative"

    def test_already_canonical(self):
        """Values already in canonical form pass through."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("Positive", "sample_result") == "Positive"

    def test_unknown_value_passes_through(self):
        """Unrecognized values return as-is (stripped)."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("some unknown", "sample_result") == "some unknown"


class TestConditionNormalization:
    """Tests for Condition enum normalization (AC3)."""

    def test_good(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("good", "condition") == "Good"

    def test_fair(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("fair", "condition") == "Fair"

    def test_poor(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("poor", "condition") == "Poor"

    def test_unknown(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("unknown", "condition") == "Unknown"

    def test_dash_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("-", "condition") is None

    def test_na_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("n/a", "condition") is None

    def test_na_no_slash_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("na", "condition") is None

    def test_case_insensitive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("GOOD", "condition") == "Good"
        assert normalize_enum_value("Poor", "condition") == "Poor"


class TestDisturbancePotentialNormalization:
    """Tests for DisturbancePotential enum normalization (AC3)."""

    def test_low(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("low", "disturbance_potential") == "Low"

    def test_medium_becomes_moderate(self):
        """BAR uses 'Moderate' not 'Medium'."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("medium", "disturbance_potential") == "Moderate"

    def test_moderate(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("moderate", "disturbance_potential") == "Moderate"

    def test_high(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("high", "disturbance_potential") == "High"

    def test_unknown(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("unknown", "disturbance_potential") == "Unknown"

    def test_dash_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("-", "disturbance_potential") is None

    def test_na_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("n/a", "disturbance_potential") is None

    def test_case_insensitive(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("LOW", "disturbance_potential") == "Low"
        assert normalize_enum_value("HIGH", "disturbance_potential") == "High"


class TestEdgeCases:
    """Tests for edge cases across all enum types."""

    def test_none_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value(None, "sample_result") is None
        assert normalize_enum_value(None, "condition") is None
        assert normalize_enum_value(None, "disturbance_potential") is None

    def test_empty_string_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("", "sample_result") is None
        assert normalize_enum_value("", "condition") is None

    def test_whitespace_only_returns_none(self):
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("   ", "sample_result") is None

    def test_unknown_field_name_passes_through(self):
        """Unknown field_name returns value as-is."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("test", "unknown_field") == "test"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("  good  ", "condition") == "Good"
        assert normalize_enum_value("  low  ", "disturbance_potential") == "Low"

    def test_friability_reuses_taxonomy(self):
        """Friability normalization reuses taxonomy._normalize_friability()."""
        from open_notebook.extractors.normalizers.enums import normalize_enum_value

        assert normalize_enum_value("non-friable", "friability") == "Non-friable"
        assert normalize_enum_value("friable", "friability") == "Friable"
        assert normalize_enum_value("NF", "friability") == "Non-friable"
        assert normalize_enum_value("F", "friability") == "Friable"
