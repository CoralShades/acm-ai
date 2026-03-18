"""Tests for the prompt evaluation harness.

Verifies that the eval harness:
1. Loads ground truth CSVs correctly
2. Matches records via sample_no and fuzzy matching
3. Scores fields accurately
4. Handles edge cases (empty fields, synonyms, normalization)
"""

import json
from pathlib import Path

import pytest

from scripts.eval.prompt_eval_harness import (
    EVAL_FIELDS,
    EvalResult,
    FieldScore,
    RecordMatch,
    _fuzzy_match,
    _normalize,
    _normalize_area_type,
    _normalize_condition,
    _normalize_floor_level,
    _normalize_friability,
    _normalize_product,
    _normalize_sample_no,
    evaluate,
    evaluate_fields,
    load_ground_truth,
    match_records,
)

GT_DIR = Path(__file__).parent.parent / "scripts/eval/ground_truth"


class TestNormalization:
    """Test normalization helpers."""

    def test_normalize_basic(self):
        assert _normalize("  Hello  World  ") == "hello world"

    def test_normalize_none(self):
        assert _normalize(None) == ""

    def test_normalize_product_synonym(self):
        assert _normalize_product("Flange Mastic") == "flange joints"
        assert _normalize_product("Fuse") == "fuse cartridge"
        assert _normalize_product("skirting board") == "skirting"

    def test_normalize_product_canonical(self):
        assert _normalize_product("Floor covering") == "floor covering"

    def test_normalize_product_unknown(self):
        assert _normalize_product("Some Unknown Product") == "some unknown product"

    def test_normalize_friability(self):
        assert _normalize_friability("Non-friable") == "Non-friable"
        assert _normalize_friability("NF") == "Non-friable"
        assert _normalize_friability("Friable") == "Friable"
        assert _normalize_friability("F") == "Friable"
        assert _normalize_friability(None) == ""

    def test_normalize_sample_no(self):
        assert _normalize_sample_no("As Per 34511-039-001") == "34511-039-001"
        assert _normalize_sample_no("Same as 34511-039-003") == "34511-039-003"
        assert _normalize_sample_no("34511-039-001") == "34511-039-001"

    def test_normalize_area_type(self):
        assert _normalize_area_type("Internal") == "Internal"
        assert _normalize_area_type("Interior") == "Internal"
        assert _normalize_area_type("External") == "External"
        assert _normalize_area_type("Exterior") == "External"

    def test_normalize_floor_level(self):
        assert _normalize_floor_level("Ground") == "Ground"
        assert _normalize_floor_level("Ground floor") == "Ground"
        assert _normalize_floor_level("Ground Floor") == "Ground"
        assert _normalize_floor_level("First") == "First"
        assert _normalize_floor_level("First floor") == "First"

    def test_normalize_condition(self):
        assert _normalize_condition("N/A (negative)") == "N/A"
        assert _normalize_condition("Good") == "Good"
        assert _normalize_condition("Stable") == "Good"


class TestFuzzyMatch:
    """Test fuzzy string matching."""

    def test_exact_match(self):
        assert _fuzzy_match("hello", "hello") == 1.0

    def test_empty_both(self):
        assert _fuzzy_match("", "") == 1.0

    def test_empty_one(self):
        assert _fuzzy_match("hello", "") == 0.0

    def test_similar(self):
        score = _fuzzy_match("Ground Floor", "Ground floor")
        assert score > 0.8

    def test_different(self):
        score = _fuzzy_match("Kitchen", "Exterior")
        assert score < 0.5


class TestRecordMatching:
    """Test record matching logic."""

    def test_sample_no_match(self):
        gt = [{"sample_no": "34511-039-001", "room_name": "Foyer", "product": "Floor"}]
        ext = [{"sample_no": "34511-039-001", "room_name": "Main Foyer", "product": "Floor covering"}]
        matches, unmatched_gt, unmatched_ext = match_records(gt, ext)
        assert len(matches) == 1
        assert matches[0].match_method == "sample_no"
        assert not unmatched_gt
        assert not unmatched_ext

    def test_as_per_match(self):
        gt = [{"sample_no": "As Per 34511-039-001", "room_name": "Kitchen", "product": "Floor"}]
        ext = [{"sample_no": "34511-039-001", "room_name": "Kitchen", "product": "Floor"}]
        matches, _, _ = match_records(gt, ext)
        assert len(matches) == 1

    def test_fuzzy_match(self):
        gt = [{"sample_no": "Not Sampled", "room_name": "Kitchen", "location": "Floor", "product": "Floor covering"}]
        ext = [{"sample_no": "", "room_name": "Kitchen", "location": "Floor", "product": "Floor covering"}]
        matches, _, _ = match_records(gt, ext)
        assert len(matches) == 1
        assert matches[0].match_method == "room_location_product"

    def test_no_match(self):
        gt = [{"sample_no": "X-001", "room_name": "Kitchen", "product": "Floor"}]
        ext = [{"sample_no": "Y-002", "room_name": "Exterior", "product": "Roof"}]
        matches, unmatched_gt, unmatched_ext = match_records(gt, ext)
        assert len(matches) == 0
        assert len(unmatched_gt) == 1
        assert len(unmatched_ext) == 1


class TestFieldEvaluation:
    """Test per-field accuracy scoring."""

    def test_exact_match_scores(self):
        gt = [{"room_name": "Kitchen", "product": "Floor covering", "sample_no": "X-001"}]
        ext = [{"room_name": "Kitchen", "product": "Floor covering", "sample_no": "X-001"}]
        matches = [RecordMatch(gt_index=0, ext_index=0, match_method="test", match_score=1.0)]
        scores = evaluate_fields(matches, gt, ext)
        assert scores["room_name"].exact_matches == 1
        assert scores["room_name"].accuracy == 1.0

    def test_empty_gt_skipped(self):
        gt = [{"room_name": "Kitchen", "floor_level": ""}]
        ext = [{"room_name": "Kitchen", "floor_level": "Ground"}]
        matches = [RecordMatch(gt_index=0, ext_index=0, match_method="test", match_score=1.0)]
        scores = evaluate_fields(matches, gt, ext)
        assert scores["floor_level"].gt_empty == 1
        assert scores["floor_level"].accuracy == 1.0  # N/A -> treated as perfect

    def test_missing_extraction_counted(self):
        gt = [{"room_name": "Kitchen", "friable": "Non-friable"}]
        ext = [{"room_name": "Kitchen", "friable": None}]
        matches = [RecordMatch(gt_index=0, ext_index=0, match_method="test", match_score=1.0)]
        scores = evaluate_fields(matches, gt, ext)
        assert scores["friable"].ext_empty == 1
        assert scores["friable"].accuracy == 0.0


class TestGroundTruthLoading:
    """Test ground truth CSV loading."""

    @pytest.mark.skipif(
        not (GT_DIR / "broadmeadows.csv").exists(),
        reason="Ground truth CSV not generated yet",
    )
    def test_load_broadmeadows(self):
        gt = load_ground_truth("broadmeadows")
        assert len(gt) == 31
        # Check field names
        for field in EVAL_FIELDS:
            assert field in gt[0], f"Missing field: {field}"

    @pytest.mark.skipif(
        not (GT_DIR / "alexander.csv").exists(),
        reason="Ground truth CSV not generated yet",
    )
    def test_load_alexander(self):
        gt = load_ground_truth("alexander")
        assert len(gt) == 43


class TestFullEvaluation:
    """Test the full evaluation pipeline."""

    def test_perfect_extraction(self):
        gt = [
            {"room_name": "Kitchen", "product": "Floor covering", "sample_no": "X-001",
             "sample_result": "Negative", "friable": "Non-friable", "location": "Floor",
             "floor_level": "Ground", "material_description": "Vinyl", "area_type": "Internal",
             "material_condition": "Good", "disturbance_potential": "Low"},
        ]
        result = evaluate("test", gt, gt)
        assert result.recall == 1.0
        assert result.matched_count == 1

    def test_empty_extraction(self):
        gt = [{"room_name": "Kitchen", "product": "Floor", "sample_no": "X-001"}]
        result = evaluate("test", gt, [])
        assert result.recall == 0.0
        assert result.matched_count == 0

    def test_result_serialization(self):
        gt = [{"room_name": "Kitchen", "product": "Floor", "sample_no": "X-001"}]
        result = evaluate("test", gt, gt)
        d = result.to_dict()
        assert "recall" in d
        assert "field_scores" in d
        # Should be JSON-serializable
        json.dumps(d)

    @pytest.mark.skipif(
        not (GT_DIR / "broadmeadows_extracted.json").exists(),
        reason="Extracted records not cached yet",
    )
    def test_broadmeadows_baseline(self):
        """Regression test: Broadmeadows recall should not drop below baseline."""
        gt = load_ground_truth("broadmeadows")
        with open(GT_DIR / "broadmeadows_extracted.json") as f:
            ext = json.load(f)
        result = evaluate("broadmeadows", gt, ext)
        # Baseline: 87.1% recall (27/31)
        assert result.recall >= 0.80, f"Recall dropped below 80%: {result.recall:.1%}"
        # Sample_result should stay at 100%
        assert result.field_scores["sample_result"].accuracy >= 0.95
