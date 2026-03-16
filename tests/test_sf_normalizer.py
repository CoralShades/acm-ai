"""Tests for SF picklist normalization (pre-validation deterministic node)."""

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.normalizers.sf_normalizer import (
    normalize_extraction_record,
    normalize_extraction_records,
)


def _make_record(**kwargs) -> ACMExtractionRecord:
    """Create an ACMExtractionRecord bypassing validators to test raw values.

    Uses model_construct() so Pydantic validators don't pre-normalize values.
    """
    defaults = {
        "building_id": "B1",
        "product": "Tiles",
        "result": "Positive",
        "data_issues": [],
    }
    defaults.update(kwargs)
    return ACMExtractionRecord.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Value mapping tests
# ---------------------------------------------------------------------------


class TestValueMappings:
    """Test value mappings via normalize_extraction_record."""

    def test_good_to_stable(self):
        record = _make_record(material_condition="Good")
        modified = normalize_extraction_record(record)
        assert record.material_condition == "Stable"
        assert "material_condition" in modified

    def test_medium_to_moderate(self):
        record = _make_record(disturbance_potential="Medium")
        modified = normalize_extraction_record(record)
        assert record.disturbance_potential == "Moderate"
        assert "disturbance_potential" in modified

    def test_non_friable_space_to_hyphen(self):
        record = _make_record(friable="Non Friable")
        modified = normalize_extraction_record(record)
        assert record.friable == "Non-friable"
        assert "friable" in modified

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("stable", "Stable"),
            ("STABLE", "Stable"),
        ],
    )
    def test_case_normalization(self, input_val, expected):
        record = _make_record(material_condition=input_val)
        normalize_extraction_record(record)
        assert record.material_condition == expected

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("positive", "Positive"),
            ("neg", "Negative"),
            ("detected", "Positive"),
            ("not detected", "Negative"),
        ],
    )
    def test_sample_result_synonyms(self, input_val, expected):
        record = _make_record(sample_result=input_val)
        normalize_extraction_record(record)
        assert record.sample_result == expected


# ---------------------------------------------------------------------------
# Negative result business rule
# ---------------------------------------------------------------------------


class TestNegativeBusinessRule:
    def test_negative_clears_condition(self):
        record = _make_record(
            result="Negative",
            sample_result="Negative",
            material_condition="Stable",
            disturbance_potential="Low",
        )
        normalize_extraction_record(record)
        assert record.material_condition == "N/A (negative)"
        assert record.disturbance_potential == "N/A (negative)"

    def test_assumed_negative_clears_condition(self):
        record = _make_record(
            result="Assumed Negative",
            sample_result="Assumed Negative",
            material_condition="Fair",
            disturbance_potential="High",
        )
        normalize_extraction_record(record)
        assert record.material_condition == "N/A (assumed negative)"
        assert record.disturbance_potential == "N/A (assumed negative)"

    def test_negative_already_na_untouched(self):
        record = _make_record(
            result="Negative",
            sample_result="Negative",
            material_condition="N/A (negative)",
            disturbance_potential="N/A (negative)",
        )
        modified = normalize_extraction_record(record)
        assert "material_condition" not in modified
        assert "disturbance_potential" not in modified

    def test_positive_does_not_clear(self):
        record = _make_record(
            result="Positive",
            material_condition="Stable",
            disturbance_potential="Low",
        )
        normalize_extraction_record(record)
        assert record.material_condition == "Stable"
        assert record.disturbance_potential == "Low"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_already_normalized_passthrough(self):
        record = _make_record(
            material_condition="Stable",
            disturbance_potential="Moderate",
            friable="Non-friable",
        )
        modified = normalize_extraction_record(record)
        assert record.material_condition == "Stable"
        assert record.disturbance_potential == "Moderate"
        assert record.friable == "Non-friable"
        assert len(modified) == 0

    def test_double_normalize_idempotent(self):
        record = _make_record(material_condition="Good")
        normalize_extraction_record(record)
        assert record.material_condition == "Stable"
        modified2 = normalize_extraction_record(record)
        assert record.material_condition == "Stable"
        assert len(modified2) == 0


# ---------------------------------------------------------------------------
# Non-fatal on errors
# ---------------------------------------------------------------------------


class TestNonFatal:
    def test_totally_broken_record(self):
        """Non-fatal when record has unexpected structure."""

        class FakeRecord:
            pass

        result = normalize_extraction_record(FakeRecord())
        assert result == []


# ---------------------------------------------------------------------------
# Batch function
# ---------------------------------------------------------------------------


class TestBatchNormalization:
    def test_batch_stats(self):
        records = [
            _make_record(material_condition="Good"),
            _make_record(material_condition="Stable"),
            _make_record(disturbance_potential="Medium"),
        ]
        stats = normalize_extraction_records(records)
        assert stats["total_records"] == 3
        assert stats["records_modified"] >= 2
        assert stats["fields_modified"] >= 2

    def test_empty_list(self):
        stats = normalize_extraction_records([])
        assert stats["total_records"] == 0
        assert stats["records_modified"] == 0
        assert stats["fields_modified"] == 0


# ---------------------------------------------------------------------------
# Data issues tracking
# ---------------------------------------------------------------------------


class TestDataIssues:
    def test_appends_data_issues(self):
        record = _make_record(material_condition="Good")
        normalize_extraction_record(record)
        assert record.data_issues is not None
        assert any("SF normalized" in issue for issue in record.data_issues)

    def test_no_duplicates(self):
        record = _make_record(material_condition="Good")
        normalize_extraction_record(record)
        normalize_extraction_record(record)
        sf_issues = [i for i in (record.data_issues or []) if "SF normalized" in i]
        assert len(sf_issues) <= 1


# ---------------------------------------------------------------------------
# Graph node test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_graph_node_returns_records():
    """The graph node returns dict with records key."""
    from open_notebook.graphs.acm_extraction import normalize_to_sf_node

    records = [_make_record(material_condition="Good")]
    state = {"records": records}
    result = await normalize_to_sf_node(state, {})
    assert "records" in result
    assert len(result["records"]) == 1
    assert result["records"][0].material_condition == "Stable"


@pytest.mark.asyncio
async def test_graph_node_empty_records():
    from open_notebook.graphs.acm_extraction import normalize_to_sf_node

    result = await normalize_to_sf_node({"records": []}, {})
    assert result == {"records": []}
