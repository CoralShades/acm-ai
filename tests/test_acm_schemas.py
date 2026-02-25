"""
Unit tests for ACMExtractionRecord and related Pydantic schemas.

Focuses on the null-coercion fixes required by Phase 3B:
  - data_issues: null  →  [] (LLM frequently outputs null for empty lists)
  - _normalize_extraction_json helper handles None and str variants
  - _merge_records in acm_extraction is null-safe for data_issues

Story: E20-S5 / Phase 3B schema-validation bugfix
"""

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# ACMExtractionRecord — data_issues null coercion
# ---------------------------------------------------------------------------


class TestACMExtractionRecordDataIssues:
    """Tests for data_issues field null→[] coercion (Phase 3B fix)."""

    _BASE = {
        "building_id": "B01",
        "product": "Vinyl Tiles",
        "result": "Positive",
    }

    def _make(self, **kwargs):
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        return ACMExtractionRecord(**{**self._BASE, **kwargs})

    # ------------------------------------------------------------------
    # Null / absent
    # ------------------------------------------------------------------

    def test_data_issues_null_coerces_to_empty_list(self):
        """LLM returning ``"data_issues": null`` must not raise ValidationError."""
        record = self._make(data_issues=None)
        assert record.data_issues == []

    def test_data_issues_absent_defaults_to_empty_list(self):
        """Omitting data_issues entirely must default to []."""
        record = self._make()
        assert record.data_issues == []

    # ------------------------------------------------------------------
    # Valid inputs
    # ------------------------------------------------------------------

    def test_data_issues_list_passthrough(self):
        """Non-empty list must be stored unchanged."""
        issues = ["missing_sample_no", "unresolved_condition"]
        record = self._make(data_issues=issues)
        assert record.data_issues == issues

    def test_data_issues_empty_list_ok(self):
        """Explicitly passing [] must work."""
        record = self._make(data_issues=[])
        assert record.data_issues == []

    # ------------------------------------------------------------------
    # Regression: full model_validate path mirrors LLM JSON → parse chain
    # ------------------------------------------------------------------

    def test_model_validate_with_null_data_issues(self):
        """model_validate() path used in fallback JSON parsing must accept null."""
        from open_notebook.extractors.acm_schemas import (
            ACMExtractionRecord,
            ACMExtractionResult,
        )

        raw = {
            "records": [
                {
                    "building_id": "B01",
                    "product": "Ceiling Tiles",
                    "result": "Positive",
                    "data_issues": None,
                }
            ],
            "status": "valid",
            "total_records": 1,
            "records_rejected": 0,
        }
        result = ACMExtractionResult.model_validate(raw)
        assert len(result.records) == 1
        assert result.records[0].data_issues == []

    def test_model_validate_with_multiple_null_records(self):
        """All 13 records mentioned in blocker report must pass (null data_issues)."""
        from open_notebook.extractors.acm_schemas import ACMExtractionResult

        records = [
            {
                "building_id": "B01",
                "product": f"Product {i}",
                "result": "Positive",
                "data_issues": None,
            }
            for i in range(13)
        ]
        raw = {"records": records, "status": "valid", "total_records": 13}
        result = ACMExtractionResult.model_validate(raw)
        assert len(result.records) == 13
        for record in result.records:
            assert record.data_issues == []


# ---------------------------------------------------------------------------
# _normalize_extraction_json — None and str variants
# ---------------------------------------------------------------------------


class TestNormalizeExtractionJson:
    """Tests for the orchestrator JSON normalisation helper."""

    def _normalize(self, parsed: dict) -> dict:
        from open_notebook.extractors.orchestrator import _normalize_extraction_json

        return _normalize_extraction_json(parsed)

    def test_null_data_issues_normalised_to_empty_list(self):
        parsed = {
            "records": [{"building_id": "B01", "product": "Tiles", "data_issues": None}]
        }
        result = self._normalize(parsed)
        assert result["records"][0]["data_issues"] == []

    def test_string_data_issues_normalised_to_list(self):
        parsed = {
            "records": [
                {
                    "building_id": "B01",
                    "product": "Tiles",
                    "data_issues": "missing sample no",
                }
            ]
        }
        result = self._normalize(parsed)
        assert result["records"][0]["data_issues"] == ["missing sample no"]

    def test_empty_string_data_issues_normalised_to_empty_list(self):
        parsed = {
            "records": [{"building_id": "B01", "product": "Tiles", "data_issues": ""}]
        }
        result = self._normalize(parsed)
        assert result["records"][0]["data_issues"] == []

    def test_list_data_issues_left_unchanged(self):
        issues = ["issue_a", "issue_b"]
        parsed = {
            "records": [
                {"building_id": "B01", "product": "Tiles", "data_issues": issues}
            ]
        }
        result = self._normalize(parsed)
        assert result["records"][0]["data_issues"] == issues

    def test_no_data_issues_key_gets_default_empty_list(self):
        """When key is absent, dict.get() returns None so the None branch fires
        and sets data_issues=[] — same defensive behaviour as the explicit-null case."""
        parsed = {"records": [{"building_id": "B01", "product": "Tiles"}]}
        result = self._normalize(parsed)
        # Normaliser adds the key so Pydantic always receives a concrete list.
        assert result["records"][0]["data_issues"] == []

    def test_empty_records_list_is_safe(self):
        parsed = {"records": []}
        result = self._normalize(parsed)
        assert result["records"] == []

    def test_multiple_records_all_normalised(self):
        parsed = {
            "records": [
                {"building_id": "B01", "product": "P1", "data_issues": None},
                {"building_id": "B01", "product": "P2", "data_issues": "bad value"},
                {"building_id": "B01", "product": "P3", "data_issues": ["ok"]},
            ]
        }
        result = self._normalize(parsed)
        assert result["records"][0]["data_issues"] == []
        assert result["records"][1]["data_issues"] == ["bad value"]
        assert result["records"][2]["data_issues"] == ["ok"]


# ---------------------------------------------------------------------------
# _merge_records — null-safe data_issues merge
# ---------------------------------------------------------------------------


class TestMergeRecordsDataIssuesNullSafe:
    """Tests for the null-safe _merge_records helper in acm_extraction."""

    def _make_record(self, confidence: str, data_issues):
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        return ACMExtractionRecord(
            building_id="B01",
            product="Tiles",
            result="Positive",
            extraction_confidence=confidence,
            data_issues=data_issues,
        )

    def test_merge_both_have_issues(self):
        from open_notebook.graphs.acm_extraction import _merge_records

        existing = self._make_record("medium", ["issue_a"])
        new = self._make_record("high", ["issue_b"])
        merged = _merge_records(existing, new)
        assert set(merged.data_issues) == {"issue_a", "issue_b"}

    def test_merge_existing_has_none(self):
        """Existing record loaded from DB may have data_issues=None — must not crash."""
        from open_notebook.graphs.acm_extraction import _merge_records

        existing = self._make_record("medium", [])
        # Force None directly to simulate old DB record bypassing validator
        existing.data_issues = None  # type: ignore[assignment]
        new = self._make_record("high", ["issue_b"])
        merged = _merge_records(existing, new)
        assert merged.data_issues == ["issue_b"]

    def test_merge_new_has_none(self):
        from open_notebook.graphs.acm_extraction import _merge_records

        existing = self._make_record("high", ["issue_a"])
        new = self._make_record("medium", [])
        new.data_issues = None  # type: ignore[assignment]
        merged = _merge_records(existing, new)
        assert merged.data_issues == ["issue_a"]

    def test_merge_both_none(self):
        from open_notebook.graphs.acm_extraction import _merge_records

        existing = self._make_record("medium", [])
        existing.data_issues = None  # type: ignore[assignment]
        new = self._make_record("high", [])
        new.data_issues = None  # type: ignore[assignment]
        merged = _merge_records(existing, new)
        assert merged.data_issues == []

    def test_merge_deduplicates_issues(self):
        from open_notebook.graphs.acm_extraction import _merge_records

        existing = self._make_record("medium", ["dup", "unique_a"])
        new = self._make_record("high", ["dup", "unique_b"])
        merged = _merge_records(existing, new)
        assert set(merged.data_issues) == {"dup", "unique_a", "unique_b"}
        assert len(merged.data_issues) == 3  # no duplicates
