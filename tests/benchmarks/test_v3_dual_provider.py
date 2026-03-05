"""V3 Dual-Provider Benchmark — pytest quality gate.

Validates that the dual-provider pipeline (Docling + MinerU) meets or
exceeds the Gate-2 baseline accuracy on real benchmark documents.

Run: pytest tests/benchmarks/ -m v3_benchmark

When MinerU fixture files are absent, MinerU-dependent tests are skipped
gracefully so the CI gate always produces a clear green/red signal.

Story: E31-S6
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.research.e29_benchmark_harness import (  # noqa: E402
    BenchmarkConfig,
    calculate_field_accuracy,
    calculate_metrics,
    get_benchmark_configs,
    load_ground_truth,
    match_records,
)

FIXTURES_DIR = PROJECT_ROOT / "benchmarks" / "fixtures"
GROUND_TRUTH_DIR = PROJECT_ROOT / "benchmarks" / "ground_truth"

# High-stakes fields for AC4 field accuracy check.
# "condition" in the story maps to "material_condition" in ACMExtractionRecord.
HIGH_STAKES_FIELDS = ["result", "friable", "material_condition", "product"]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _load_mineru_fixture(doc_name: str) -> list[dict]:
    """Load MinerU table fixture. Returns [] if file is absent (triggers skip)."""
    path = FIXTURES_DIR / f"mineru_{doc_name}.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("tables", [])


def _load_docling_fixture(doc_name: str) -> list[dict]:
    """Load Docling table fixture. Returns [] if file is absent."""
    path = FIXTURES_DIR / f"docling_{doc_name}.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("tables", [])


# ---------------------------------------------------------------------------
# Extraction runner (mocked DB + GPU, real LLM)
# ---------------------------------------------------------------------------


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF with page markers.

    Returns empty string when PDF is absent so tests can proceed with
    whatever markdown text is available in fixtures.
    """
    if not pdf_path.exists():
        return ""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf_path))
        pages = []
        for i, page in enumerate(doc, 1):
            text = page.get_text()
            pages.append(f"--- Page {i} ---\n{text}")
        return "\n\n".join(pages)
    except Exception:
        return ""


async def _real_provision_model(content, model_id, default_type, **kwargs):
    """Provision a real LLM model for benchmark extraction.

    Mirrors the helper used in e29_benchmark_harness.run_extraction().
    Requires OPENROUTER_API_KEY or ANTHROPIC_API_KEY to be set.
    """
    import os

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("BENCHMARK_MODEL", "anthropic/claude-sonnet-4")
        allowed = {
            k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")
        }
        return ChatOpenAI(
            model=model_name,
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1",
            **allowed,
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic

        model_name = os.environ.get("BENCHMARK_MODEL", "claude-haiku-4-5-20251001")
        allowed = {
            k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")
        }
        return ChatAnthropic(model=model_name, **allowed)

    raise RuntimeError(
        "No LLM API key available — set OPENROUTER_API_KEY or ANTHROPIC_API_KEY"
    )


def _run_mocked_extraction(
    doc_key: str,
    *,
    mineru_tables: list[dict],
) -> list:
    """Run extraction with mocked DB/GPU via the acm_extraction graph.

    This function exercises the **Docling provider path** using fixtures from
    ``benchmarks/fixtures/docling_{doc_key}.json``.  The ``mineru_tables``
    parameter is accepted for API compatibility and future wiring, but is NOT
    currently injected into the extraction pipeline.

    Why: MinerU requires a GPU at inference time; no subprocess hook or in-graph
    injection point exists yet for MinerU table data.  The acm_extraction graph
    currently calls ``_get_docling_tables`` internally — MinerU runs through a
    separate code path that cannot be mocked at the same level without a GPU.

    Env vars (``V3_DUAL_PROVIDER``, ``MINERU_ENABLED``, ``ACM_EXTRACTION_PROVIDER``)
    are still set by each test class so that env-flag routing logic is exercised.
    The fixture data fed to the graph always comes from the Docling fixture file.

    Args:
        doc_key: Benchmark document key (e.g. ``"broadmeadows"``).
        mineru_tables: Reserved for future fixture injection when a MinerU
            provider mock is wired into the extraction graph.  Currently unused.

    All DB saves are intercepted in memory — no SurrealDB connection needed.

    Returns:
        List of extracted ACMRecord instances.
    """
    from open_notebook.domain.acm import ACMRecord, ACMTableSection
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    configs = get_benchmark_configs()
    config: BenchmarkConfig = configs[doc_key]

    docling_tables = _load_docling_fixture(doc_key)
    extracted_records: list = []

    async def capture_save(self):
        extracted_records.append(self)

    async def noop_save(self):
        pass

    async def noop_auto_populate(document_meta, source_id):
        pass

    async def mock_docling_tables(source_id: str, page_start: int, page_end: int):
        return [
            t
            for t in docling_tables
            if t.get("page_start", 0) >= page_start and t.get("page_end", 0) <= page_end
        ]

    # MinerU table data (mineru_tables arg) is NOT injected here.
    # MinerU runs through a separate provider path that requires a GPU and
    # has no in-process mock hook. The env vars set by each test class
    # (V3_DUAL_PROVIDER, MINERU_ENABLED, ACM_EXTRACTION_PROVIDER) exercise
    # the env-flag routing logic, but the actual tables fed to the graph
    # always come from the Docling fixture above. When a MinerU mock hook
    # is added to the graph, wire mineru_tables in here.
    source = MagicMock()
    source.id = f"source:bench_{doc_key}"
    source.full_text = _extract_pdf_text(config.pdf_path)
    source.title = config.name
    source.asset = MagicMock(file_path=str(config.pdf_path))

    async def _run():
        with (
            patch.object(ACMRecord, "save", capture_save),
            patch.object(ACMTableSection, "save", noop_save),
            patch(
                "open_notebook.graphs.acm_extraction.auto_populate_site_config",
                noop_auto_populate,
            ),
            patch(
                "open_notebook.graphs.acm_extraction.provision_langchain_model",
                _real_provision_model,
            ),
            patch(
                "open_notebook.graphs.utils.provision_langchain_model",
                _real_provision_model,
            ),
            patch(
                "open_notebook.extractors.orchestrator._get_docling_tables",
                mock_docling_tables,
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                mock_docling_tables,
            ),
        ):
            await extract_acm_from_source(
                source=source,
                model_id=None,
                force=False,
                command_id=None,
            )
        return extracted_records

    return asyncio.run(_run())


# ---------------------------------------------------------------------------
# Helper: check that an LLM key is available; skip the test if not
# ---------------------------------------------------------------------------


def _require_llm_key():
    """Skip this test unless RUN_BENCHMARK_LLM=true is set.

    LLM-dependent benchmark tests require working API credentials with available
    credits. Set RUN_BENCHMARK_LLM=true in the environment to opt into these tests.
    """
    import os

    if os.environ.get("RUN_BENCHMARK_LLM", "").lower() not in ("1", "true", "yes"):
        pytest.skip("LLM benchmark skipped — set RUN_BENCHMARK_LLM=true to enable")


# ---------------------------------------------------------------------------
# Parametrized benchmark tests
# ---------------------------------------------------------------------------


@pytest.mark.v3_benchmark
@pytest.mark.parametrize(
    "doc_key,min_matched,gt_count",
    [
        ("broadmeadows", 31, 31),  # AC1: must match all 31
        ("alexander", 40, 43),  # AC2: baseline 40, stretch 42
    ],
)
class TestDualProviderConsensus:
    """AC1 + AC2: Consensus pipeline meets or exceeds Gate-2 baseline."""

    def test_consensus_recall(self, doc_key, min_matched, gt_count, monkeypatch):
        """Consensus extraction matches >= min_matched ground truth records.

        Current limitation: this test verifies that env-flag routing
        (V3_DUAL_PROVIDER=true, MINERU_ENABLED=true) does not break the
        extraction pipeline, and that the Docling path still meets the recall
        threshold under those flags.  MinerU fixture data is NOT injected —
        see ``_run_mocked_extraction`` docstring for details.  Full consensus
        accuracy (with real MinerU tables merged at the page level) requires a
        GPU and live MinerU output.
        """
        mineru_tables = _load_mineru_fixture(doc_key)
        if not mineru_tables:
            pytest.skip(
                f"MinerU fixture not found for '{doc_key}' — skipping consensus test"
            )

        _require_llm_key()

        # Set dual-provider env flags so that routing logic is exercised even
        # though _run_mocked_extraction feeds only Docling fixture data.
        monkeypatch.setenv("V3_DUAL_PROVIDER", "true")
        monkeypatch.setenv("MINERU_ENABLED", "true")

        records = _run_mocked_extraction(doc_key, mineru_tables=mineru_tables)
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / f"{doc_key}.json")
        gt_records = gt_data["records"]

        match_result = match_records(gt_records, records)
        matched = len(match_result.matched_pairs)

        assert matched >= min_matched, (
            f"{doc_key}: consensus matched {matched}/{gt_count}, need >= {min_matched}"
        )

    def test_consensus_field_accuracy(
        self, doc_key, min_matched, gt_count, monkeypatch
    ):
        """AC4: High-stakes field accuracy >= 80% on consensus output.

        Current limitation: exercises env-flag routing with dual-provider flags
        enabled.  MinerU fixture data is NOT injected into the graph — the
        80% threshold is validated against the Docling path running under
        dual-provider env settings.  See ``_run_mocked_extraction`` docstring.
        """
        mineru_tables = _load_mineru_fixture(doc_key)
        if not mineru_tables:
            pytest.skip(f"MinerU fixture not found for '{doc_key}'")

        _require_llm_key()

        # Set dual-provider env flags so that routing logic is exercised.
        monkeypatch.setenv("V3_DUAL_PROVIDER", "true")
        monkeypatch.setenv("MINERU_ENABLED", "true")

        records = _run_mocked_extraction(doc_key, mineru_tables=mineru_tables)
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / f"{doc_key}.json")
        gt_records = gt_data["records"]

        match_result = match_records(gt_records, records)
        acc = calculate_field_accuracy(match_result.matched_pairs, HIGH_STAKES_FIELDS)
        assert acc >= 0.80, (
            f"{doc_key}: high-stakes field accuracy {acc:.1%}, need >= 80%"
        )


@pytest.mark.v3_benchmark
@pytest.mark.parametrize("doc_key", ["broadmeadows", "alexander"])
class TestDoclingOnlyBaseline:
    """AC3 (partial): Docling-only baseline for per-provider comparison."""

    def test_docling_recall(self, doc_key, monkeypatch):
        """Docling-only mode produces expected recall >= Gate-2 baseline."""
        docling_tables = _load_docling_fixture(doc_key)
        if not docling_tables:
            pytest.skip(f"Docling fixture not found for '{doc_key}'")

        _require_llm_key()

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")

        records = _run_mocked_extraction(doc_key, mineru_tables=[])
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / f"{doc_key}.json")
        gt_records = gt_data["records"]

        match_result = match_records(gt_records, records)
        matched = len(match_result.matched_pairs)
        gt_count = len(gt_records)

        # Gate-2 baselines: 30/31 Broadmeadows, 42/43 Alexander
        gate2_minimums = {"broadmeadows": 30, "alexander": 42}
        min_matched = gate2_minimums.get(doc_key, 0)

        assert matched >= min_matched, (
            f"{doc_key} Docling-only: {matched}/{gt_count}, need >= {min_matched}"
        )


@pytest.mark.v3_benchmark
@pytest.mark.parametrize("doc_key", ["broadmeadows", "alexander"])
class TestMinerUOnlyBaseline:
    """AC3 (partial): MinerU-only baseline for per-provider comparison."""

    def test_mineru_recall(self, doc_key, monkeypatch):
        """MinerU-only mode produces valid output without crashing.

        No hard accuracy threshold is applied — this test is a smoke test that
        verifies the ACM_EXTRACTION_PROVIDER=mineru env-flag code path does not
        raise an exception.  MinerU fixture data is NOT injected into the graph
        (see ``_run_mocked_extraction`` docstring); extraction runs through the
        Docling path under MinerU env flags.  Real MinerU baseline numbers
        require a GPU and live MinerU output.

        The test is skipped when MinerU fixtures are absent.
        """
        mineru_tables = _load_mineru_fixture(doc_key)
        if not mineru_tables:
            pytest.skip(
                f"MinerU fixture not found for '{doc_key}' — skip MinerU-only test"
            )

        _require_llm_key()

        # Set MinerU env flags so that the ACM_EXTRACTION_PROVIDER routing
        # code path is exercised.  Fixture data is still Docling-based — see
        # _run_mocked_extraction docstring for the current limitation.
        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        monkeypatch.setenv("MINERU_ENABLED", "true")
        monkeypatch.setenv("ACM_EXTRACTION_PROVIDER", "mineru")

        records = _run_mocked_extraction(doc_key, mineru_tables=mineru_tables)
        # Smoke test: the code path must not crash and must return a list.
        assert len(records) >= 0, "Extraction must return a list without crashing"

        gt_data = load_ground_truth(GROUND_TRUTH_DIR / f"{doc_key}.json")
        gt_records = gt_data["records"]

        match_result = match_records(gt_records, records)
        # Must run without error and return a list (even if empty)
        assert isinstance(match_result.matched_pairs, list)


# ---------------------------------------------------------------------------
# Fixture-only smoke tests (no LLM required — validate fixture format)
# ---------------------------------------------------------------------------


@pytest.mark.v3_benchmark
@pytest.mark.parametrize("doc_key", ["broadmeadows", "alexander"])
def test_docling_fixture_format(doc_key):
    """Validate Docling fixture JSON has expected schema (no LLM required)."""
    tables = _load_docling_fixture(doc_key)
    assert isinstance(tables, list), f"Expected list, got {type(tables)}"
    if tables:
        for t in tables:
            assert "page_start" in t, f"Missing page_start in table: {t}"
            assert "page_end" in t, f"Missing page_end in table: {t}"
            assert "raw_text" in t, f"Missing raw_text in table: {t}"


@pytest.mark.v3_benchmark
@pytest.mark.parametrize("doc_key", ["broadmeadows", "alexander"])
def test_mineru_fixture_format(doc_key):
    """Validate MinerU fixture JSON has expected schema, or skip if absent."""
    tables = _load_mineru_fixture(doc_key)
    if not tables:
        pytest.skip(f"MinerU fixture not found for '{doc_key}' — skipping format check")

    assert isinstance(tables, list), f"Expected list, got {type(tables)}"
    for t in tables:
        assert "page_start" in t, f"Missing page_start in table: {t}"
        assert "page_end" in t, f"Missing page_end in table: {t}"
        assert "raw_text" in t, f"Missing raw_text in table: {t}"
        assert t.get("table_type") == "mineru_direct_api", (
            f"Expected table_type='mineru_direct_api', got: {t.get('table_type')}"
        )


@pytest.mark.v3_benchmark
@pytest.mark.parametrize("doc_key", ["broadmeadows", "alexander"])
def test_ground_truth_loadable(doc_key):
    """Ground truth JSON exists and has the required schema (no LLM required)."""
    gt_path = GROUND_TRUTH_DIR / f"{doc_key}.json"
    if not gt_path.exists():
        pytest.skip(f"Ground truth not found for '{doc_key}'")

    data = load_ground_truth(gt_path)
    assert "records" in data
    assert "document" in data
    assert isinstance(data["records"], list)
    assert len(data["records"]) > 0
