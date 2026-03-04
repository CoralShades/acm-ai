"""Integration tests for E29 benchmark harness.

Tests the harness components WITHOUT requiring LLM API calls:
- Ground truth loading and validation
- Record matching engine (3-tier)
- Metric calculations (recall, precision, field accuracy)
- Report generation
- Edge cases and error handling

Run: uv run pytest tests/integration/test_benchmark_harness.py -x -v
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path so scripts.research imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.research.e29_benchmark_harness import (  # noqa: E402
    COMPARISON_FIELDS,
    PRODUCT_SYNONYMS,
    BenchmarkConfig,
    BenchmarkResult,
    MatchResult,
    _load_docling_fixtures,
    _normalize,
    _normalize_product,
    _report_path,
    _results_path,
    calculate_field_accuracy,
    calculate_metrics,
    generate_report,
    get_benchmark_configs,
    load_ground_truth,
    match_records,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ground_truth():
    """Create a minimal ground truth dataset for testing."""
    return {
        "document": {
            "name": "Test Document",
            "pdf_path": "test.pdf",
            "source": "test",
            "total_buildings": 1,
            "total_records": 5,
            "consultant": "Test Co",
        },
        "match_keys": {
            "primary": "sample_no",
            "secondary": ["building_name", "room_name", "location", "product"],
            "tertiary": ["room_name", "location"],
        },
        "records": [
            {
                "building_name": "Building A",
                "room_name": "Room 101",
                "location": "Floor",
                "product": "Vinyl Tiles",
                "sample_no": "S-001",
                "sample_result": "Positive",
                "friable": "Non Friable",
            },
            {
                "building_name": "Building A",
                "room_name": "Room 102",
                "location": "Ceiling",
                "product": "Ceiling Tiles",
                "sample_no": "S-002",
                "sample_result": "Negative",
                "friable": "Non Friable",
            },
            {
                "building_name": "Building A",
                "room_name": "Room 103",
                "location": "Wall",
                "product": "Flat Sheeting",
                "sample_no": "S-003",
                "sample_result": "Positive",
                "friable": "Non Friable",
            },
            {
                "building_name": "Building B",
                "room_name": "Corridor",
                "location": "Floor",
                "product": "Floor covering",
                "sample_no": "Not Sampled",
                "sample_result": "Assumed Positive",
                "friable": "Non Friable",
            },
            {
                "building_name": "Building B",
                "room_name": "Kitchen",
                "location": "Under Sink",
                "product": "Pipe Insulation",
                "sample_no": "S-005",
                "sample_result": "Positive",
                "friable": "Friable",
            },
        ],
    }


def _make_extracted_record(**kwargs):
    """Create a mock extracted record (simulates ACMExtractionRecord)."""
    rec = MagicMock()
    defaults = {
        "building_name": "",
        "room_name": "",
        "location": "",
        "product": "",
        "sample_no": "",
        "sample_result": "",
        "friable": "",
        "material_description": "",
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(rec, k, v)
    return rec


# ---------------------------------------------------------------------------
# Test: Ground Truth Loading
# ---------------------------------------------------------------------------


class TestGroundTruthLoading:
    def test_load_broadmeadows(self):
        """AC-2: Broadmeadows ground truth exists with 31 records."""
        path = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "ground_truth" / "broadmeadows.json"
        if not path.exists():
            pytest.skip("broadmeadows.json not created yet")
        data = load_ground_truth(path)
        assert data["document"]["total_records"] == 31
        assert len(data["records"]) == 31

    def test_load_alexander(self):
        """AC-3: Alexander ground truth exists with 43 records."""
        path = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "ground_truth" / "alexander.json"
        if not path.exists():
            pytest.skip("alexander.json not created yet")
        data = load_ground_truth(path)
        assert data["document"]["total_records"] == 43
        assert len(data["records"]) == 43

    def test_load_third_document(self):
        """AC-4: Third document ground truth exists."""
        path = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "ground_truth" / "aldavilla_4601.json"
        if not path.exists():
            pytest.skip("aldavilla_4601.json not created yet")
        data = load_ground_truth(path)
        assert data["document"]["total_records"] == 4
        assert len(data["records"]) == 4

    def test_load_missing_file(self):
        """Harness handles missing ground truth gracefully."""
        with pytest.raises(FileNotFoundError):
            load_ground_truth(Path("/nonexistent/file.json"))

    def test_load_invalid_format(self, tmp_path):
        """Harness rejects invalid ground truth format."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('{"invalid": true}')
        with pytest.raises(ValueError, match="Invalid ground truth format"):
            load_ground_truth(bad_file)

    def test_load_valid_temp_file(self, tmp_path, sample_ground_truth):
        """Harness loads valid ground truth from any path."""
        gt_file = tmp_path / "test.json"
        gt_file.write_text(json.dumps(sample_ground_truth))
        data = load_ground_truth(gt_file)
        assert len(data["records"]) == 5


# ---------------------------------------------------------------------------
# Test: Record Matching
# ---------------------------------------------------------------------------


class TestRecordMatching:
    def test_tier1_sample_number_match(self):
        """Records match by sample_no (primary tier)."""
        gt = [
            {"building_name": "A", "room_name": "Room 1", "location": "Floor",
             "product": "Tiles", "sample_no": "S-001", "sample_result": "Pos", "friable": "NF"},
        ]
        extracted = [
            _make_extracted_record(
                building_name="Building A",  # Different name
                room_name="Room One",  # Different name
                location="Floor",
                product="Vinyl Tiles",  # Different name
                sample_no="S-001",  # Same sample_no
            ),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1
        assert len(result.unmatched_gt) == 0

    def test_tier1_as_per_reference(self):
        """'As Per' sample references are resolved correctly."""
        gt = [
            {"building_name": "A", "room_name": "R1", "location": "Floor",
             "product": "T", "sample_no": "As Per S-001", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(sample_no="S-001"),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1

    def test_tier2_composite_key_match(self):
        """Records match by building_name|room_name|location|product."""
        gt = [
            {"building_name": "Main", "room_name": "Office", "location": "Ceiling",
             "product": "Ceiling Tiles", "sample_no": "", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(
                building_name="Main",
                room_name="Office",
                location="Ceiling",
                product="Ceiling Tiles",
            ),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1

    def test_tier2_synonym_match(self):
        """Product synonyms are resolved during matching."""
        gt = [
            {"building_name": "A", "room_name": "R1", "location": "AHU",
             "product": "Flange joints", "sample_no": "", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(
                building_name="A",
                room_name="R1",
                location="AHU",
                product="Mastic",  # Synonym of "flange joints"
            ),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1

    def test_tier3_room_location_fuzzy(self):
        """Fuzzy matching by room+location when product differs."""
        gt = [
            {"building_name": "A", "room_name": "Switch Room", "location": "Switchboard",
             "product": "Fuse cartridge", "sample_no": "Not Sampled", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(
                building_name="A",
                room_name="Switch Room",
                location="Switchboard",
                product="Fuses",  # Different product name entirely
            ),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1

    def test_partial_match_with_extras(self):
        """Some records match, some don't — both sides have unmatched."""
        gt = [
            {"building_name": "A", "room_name": "R1", "location": "F",
             "product": "P1", "sample_no": "S-001", "sample_result": "", "friable": ""},
            {"building_name": "A", "room_name": "R2", "location": "C",
             "product": "P2", "sample_no": "S-002", "sample_result": "", "friable": ""},
            {"building_name": "A", "room_name": "R3", "location": "W",
             "product": "P3", "sample_no": "S-003", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(sample_no="S-001", room_name="R1", product="P1"),
            _make_extracted_record(sample_no="S-999", room_name="R99", product="PX"),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 1
        assert len(result.unmatched_gt) == 2
        assert len(result.unmatched_extracted) == 1

    def test_no_matches(self):
        """No records match at all."""
        gt = [
            {"building_name": "A", "room_name": "R1", "location": "F",
             "product": "P1", "sample_no": "S-999", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(
                building_name="Z", room_name="RZ", location="X",
                product="PZ", sample_no="S-000",
            ),
        ]
        result = match_records(gt, extracted)
        assert len(result.matched_pairs) == 0
        assert len(result.unmatched_gt) == 1
        assert len(result.unmatched_extracted) == 1

    def test_empty_inputs(self):
        """Handle empty ground truth or extracted lists."""
        result = match_records([], [])
        assert len(result.matched_pairs) == 0

        result = match_records([{"sample_no": "S-1", "room_name": "R", "location": "L",
                                  "product": "P", "building_name": "B",
                                  "sample_result": "", "friable": ""}], [])
        assert len(result.unmatched_gt) == 1

    def test_consumed_records_not_double_matched(self):
        """Each extracted record can only match one GT record."""
        gt = [
            {"building_name": "A", "room_name": "R1", "location": "Floor",
             "product": "Tiles", "sample_no": "", "sample_result": "", "friable": ""},
            {"building_name": "A", "room_name": "R1", "location": "Floor",
             "product": "Tiles", "sample_no": "", "sample_result": "", "friable": ""},
        ]
        extracted = [
            _make_extracted_record(
                building_name="A", room_name="R1", location="Floor", product="Tiles",
            ),
        ]
        result = match_records(gt, extracted)
        # Only one can match since there's only one extracted record
        assert len(result.matched_pairs) == 1
        assert len(result.unmatched_gt) == 1


# ---------------------------------------------------------------------------
# Test: Metric Calculations
# ---------------------------------------------------------------------------


class TestMetricCalculations:
    def test_perfect_recall_precision(self):
        """All records matched: recall=1.0, precision=1.0."""
        gt = [{"room_name": "R1", "location": "L1", "product": "P1",
               "sample_no": "S1", "building_name": "B", "sample_result": "Pos", "friable": "NF"}]
        ext = [_make_extracted_record(
            room_name="R1", location="L1", product="P1",
            sample_no="S1", building_name="B", sample_result="Pos", friable="NF",
        )]
        match_result = MatchResult(
            matched_pairs=[(gt[0], ext[0])],
            unmatched_gt=[],
            unmatched_extracted=[],
        )
        result = calculate_metrics(gt, ext, match_result, 10.0, 1000, 0.01, "Test")
        assert result.recall == 1.0
        assert result.precision == 1.0

    def test_partial_recall(self):
        """8 matched out of 10 GT: recall=0.8."""
        gt_recs = [{"room_name": f"R{i}", "location": "L", "product": "P",
                     "sample_no": f"S{i}", "building_name": "B",
                     "sample_result": "", "friable": ""} for i in range(10)]
        ext_recs = [_make_extracted_record(sample_no=f"S{i}") for i in range(9)]
        matched = [(gt_recs[i], ext_recs[i]) for i in range(8)]
        match_result = MatchResult(
            matched_pairs=matched,
            unmatched_gt=gt_recs[8:],
            unmatched_extracted=[ext_recs[8]],
        )
        result = calculate_metrics(gt_recs, ext_recs, match_result, 5.0, 500, 0.005, "Test")
        assert result.recall == pytest.approx(0.8)
        assert result.precision == pytest.approx(8.0 / 9.0, abs=0.01)

    def test_zero_extracted(self):
        """No records extracted: recall=0, precision=0."""
        gt = [{"room_name": "R1", "sample_no": "S1", "building_name": "B",
               "location": "L", "product": "P", "sample_result": "", "friable": ""}]
        match_result = MatchResult(matched_pairs=[], unmatched_gt=gt, unmatched_extracted=[])
        result = calculate_metrics(gt, [], match_result, 1.0, 0, 0.0, "Test")
        assert result.recall == 0.0
        assert result.precision == 0.0

    def test_field_accuracy_perfect(self):
        """All fields match: field_accuracy=1.0."""
        pairs = [(
            {"building_name": "B", "room_name": "R", "location": "L",
             "product": "P", "sample_no": "S", "sample_result": "Pos", "friable": "NF"},
            _make_extracted_record(
                building_name="B", room_name="R", location="L",
                product="P", sample_no="S", sample_result="Pos", friable="NF",
            ),
        )]
        acc = calculate_field_accuracy(pairs)
        assert acc == 1.0

    def test_field_accuracy_partial(self):
        """Some fields match, some don't."""
        pairs = [(
            {"building_name": "B", "room_name": "R", "location": "L",
             "product": "P", "sample_no": "S-001", "sample_result": "Positive", "friable": "NF"},
            _make_extracted_record(
                building_name="B", room_name="R", location="L",
                product="P", sample_no="S-001", sample_result="Negative", friable="Friable",
            ),
        )]
        acc = calculate_field_accuracy(pairs)
        # 5 out of 7 fields match (building_name, room_name, location, product, sample_no)
        assert acc == pytest.approx(5.0 / 7.0, abs=0.01)

    def test_field_accuracy_synonym_product(self):
        """Product synonyms count as matches in field accuracy."""
        pairs = [(
            {"building_name": "B", "room_name": "R", "location": "L",
             "product": "Flange joints", "sample_no": "", "sample_result": "", "friable": ""},
            _make_extracted_record(
                building_name="B", room_name="R", location="L",
                product="Mastic", sample_no="", sample_result="", friable="",
            ),
        )]
        acc = calculate_field_accuracy(pairs)
        # building_name, room_name, location all match; product matches via synonym
        # sample_no, sample_result, friable are all empty-empty → skipped
        assert acc == 1.0

    def test_field_accuracy_empty_pairs(self):
        """No matched pairs: field_accuracy=0."""
        assert calculate_field_accuracy([]) == 0.0


# ---------------------------------------------------------------------------
# Test: Report Generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    def test_report_structure(self):
        """Report contains required sections and formatting."""
        results = [
            BenchmarkResult(
                document_name="Test Doc",
                ground_truth_count=10,
                extracted_count=9,
                matched_count=8,
                recall=0.8,
                precision=0.889,
                field_accuracy=0.75,
                latency_s=15.0,
                token_usage=5000,
                cost_usd=0.025,
            ),
        ]
        report = generate_report(results)

        assert "# E29 Baseline Benchmark Report" in report
        assert "## Summary" in report
        assert "Test Doc" in report
        assert "80.0%" in report  # recall
        assert "## Gate 1 Readiness" in report

    def test_report_multiple_docs(self):
        """Report handles multiple benchmark documents."""
        results = [
            BenchmarkResult(
                document_name=f"Doc {i}",
                ground_truth_count=10,
                extracted_count=10,
                matched_count=10,
                recall=1.0,
                precision=1.0,
                field_accuracy=1.0,
                latency_s=10.0,
                token_usage=1000,
                cost_usd=0.01,
            )
            for i in range(3)
        ]
        report = generate_report(results)

        assert "PASS" in report  # Gate 1 criteria
        assert "Doc 0" in report
        assert "Doc 1" in report
        assert "Doc 2" in report

    def test_report_with_errors(self):
        """Report includes error details for failed benchmarks."""
        results = [
            BenchmarkResult(
                document_name="Failed Doc",
                ground_truth_count=10,
                extracted_count=0,
                matched_count=0,
                recall=0.0,
                precision=0.0,
                field_accuracy=0.0,
                latency_s=0.0,
                token_usage=0,
                cost_usd=0.0,
                error="LLM API timeout",
            ),
        ]
        report = generate_report(results)
        assert "LLM API timeout" in report
        assert "FAIL" in report

    def test_report_with_unmatched(self):
        """Report lists missing and extra records."""
        results = [
            BenchmarkResult(
                document_name="Partial Doc",
                ground_truth_count=5,
                extracted_count=4,
                matched_count=3,
                recall=0.6,
                precision=0.75,
                field_accuracy=0.8,
                latency_s=20.0,
                token_usage=3000,
                cost_usd=0.015,
                unmatched_gt=[
                    {"building_name": "B", "room_name": "R1", "location": "L1",
                     "product": "P1", "sample_no": "S-99"},
                    {"building_name": "B", "room_name": "R2", "location": "L2",
                     "product": "P2", "sample_no": "S-98"},
                ],
                unmatched_extracted=["R3/P3"],
            ),
        ]
        report = generate_report(results)
        assert "Missing Records" in report
        assert "Extra Records" in report
        assert "R1" in report
        assert "R3/P3" in report


# ---------------------------------------------------------------------------
# Test: Config Registry
# ---------------------------------------------------------------------------


class TestConfigRegistry:
    def test_three_benchmarks_registered(self):
        """At least 3 benchmark documents are registered."""
        configs = get_benchmark_configs()
        assert len(configs) >= 3

    def test_broadmeadows_config(self):
        configs = get_benchmark_configs()
        assert "broadmeadows" in configs
        assert configs["broadmeadows"].expected_records == 31

    def test_alexander_config(self):
        configs = get_benchmark_configs()
        assert "alexander" in configs
        assert configs["alexander"].expected_records == 43

    def test_aldavilla_config(self):
        configs = get_benchmark_configs()
        assert "aldavilla" in configs
        assert configs["aldavilla"].expected_records == 4


# ---------------------------------------------------------------------------
# Test: Normalization (R1-AC2, R1-AC3)
# ---------------------------------------------------------------------------


class TestNormalization:
    def test_room_name_case_insensitive(self):
        """R1-AC2: Room names match regardless of case."""
        assert _normalize("Room 1") == _normalize("room 1")
        assert _normalize("room 1") == _normalize("ROOM 1")
        assert _normalize("Room 1") == _normalize("ROOM 1")

    def test_room_name_whitespace_normalization(self):
        """R1-AC2: Extra whitespace is collapsed."""
        assert _normalize("Room  1") == _normalize("Room 1")
        assert _normalize("  Room 1  ") == _normalize("Room 1")
        assert _normalize("Room\t1") == _normalize("Room 1")

    def test_material_description_case_normalization(self):
        """R1-AC3: Material descriptions are case-insensitive."""
        assert _normalize("Floor Covering") == _normalize("floor covering")
        assert _normalize("CEILING TILES") == _normalize("ceiling tiles")

    def test_material_synonym_mapping(self):
        """R1-AC3: Product synonyms resolve to canonical form."""
        assert _normalize_product("Mastic") == "flange joints"
        assert _normalize_product("Flange joints") == "flange joints"
        assert _normalize_product("flange mastic") == "flange joints"

    def test_product_synonym_fuse(self):
        """Fuse variants resolve correctly."""
        assert _normalize_product("Fuses") == "fuse cartridge"
        assert _normalize_product("Fuse") == "fuse cartridge"
        assert _normalize_product("Fuse cartridge") == "fuse cartridge"

    def test_product_synonym_unknown_preserved(self):
        """Unknown products are returned as-is (normalized case)."""
        assert _normalize_product("Pipe Insulation") == "pipe insulation"
        assert _normalize_product("Unknown Special Material") == "unknown special material"

    def test_normalize_empty_string(self):
        """Empty strings normalize cleanly."""
        assert _normalize("") == ""
        assert _normalize("   ") == ""
        assert _normalize_product("") == ""


# ---------------------------------------------------------------------------
# Test: Docling Fixtures (R1-AC1)
# ---------------------------------------------------------------------------


class TestDoclingFixtures:
    def test_docling_fixture_loading_broadmeadows(self):
        """Broadmeadows fixture exists and parses correctly."""
        tables = _load_docling_fixtures("broadmeadows")
        assert len(tables) > 0, "Broadmeadows fixture should have at least one table"

    def test_docling_fixture_loading_alexander(self):
        """Alexander fixture exists and parses correctly."""
        tables = _load_docling_fixtures("alexander")
        assert len(tables) > 0, "Alexander fixture should have at least one table"

    def test_docling_fixture_loading_missing(self):
        """Missing fixture returns empty list (graceful fallback)."""
        tables = _load_docling_fixtures("nonexistent_document")
        assert tables == []

    def test_docling_fixture_format_broadmeadows(self):
        """Broadmeadows fixture has required fields."""
        tables = _load_docling_fixtures("broadmeadows")
        for table in tables:
            assert "page_start" in table, "Missing page_start"
            assert "raw_text" in table, "Missing raw_text"
            assert "table_type" in table, "Missing table_type"
            assert table["table_type"] == "docling_direct_api"
            assert isinstance(table["page_start"], int)
            assert len(table["raw_text"]) > 0

    def test_docling_fixture_format_alexander(self):
        """Alexander fixture has required fields and per-building tables."""
        tables = _load_docling_fixtures("alexander")
        for table in tables:
            assert "page_start" in table
            assert "raw_text" in table
            assert "table_type" in table
            assert table["table_type"] == "docling_direct_api"
        # Alexander has 5 buildings → expect 5 tables
        assert len(tables) == 5

    def test_output_tag_file_paths(self):
        """--output-tag produces correctly named result/report files."""
        results = _results_path("gate2")
        report = _report_path("gate2")
        assert results.name == "gate2_results.json"
        assert report.name == "e29-gate2-benchmark-report.md"

    def test_output_tag_default_baseline(self):
        """Default tag 'baseline' produces backward-compatible paths."""
        results = _results_path("baseline")
        report = _report_path("baseline")
        assert results.name == "baseline_results.json"
        assert report.name == "e29-baseline-benchmark-report.md"
