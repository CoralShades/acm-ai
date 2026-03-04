"""Tests for E31-S5 — Dual-Provider Pipeline Integration.

Covers feature flag logic, dual-provider extraction orchestration,
page-level merge logic, consensus storage, and strategy registry entries.

All tests are fully mocked — no live SurrealDB or GPU required.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_table(
    table_index: int = 0,
    page: int = 1,
    row_count: int = 5,
    col_count: int = 3,
    columns: list[str] | None = None,
    html: str = "<table/>",
    markdown: str = "md",
    csv: str | None = "a,b,c",
) -> NormalizedTable:
    return NormalizedTable(
        table_index=table_index,
        page=page,
        row_count=row_count,
        col_count=col_count,
        columns=columns or ["A", "B", "C"],
        html=html,
        markdown=markdown,
        csv=csv,
    )


def _docling_result(tables: list[NormalizedTable]) -> NormalizedExtractionResult:
    return NormalizedExtractionResult(provider_id="docling", tables=tables)


def _mineru_result(tables: list[NormalizedTable]) -> NormalizedExtractionResult:
    return NormalizedExtractionResult(provider_id="mineru", tables=tables)


# ---------------------------------------------------------------------------
# 1. TestDualProviderFeatureFlag
# ---------------------------------------------------------------------------


class TestDualProviderFeatureFlag:
    """Tests for V3_DUAL_PROVIDER + MINERU_ENABLED interaction."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_mineru_not_called_when_v3_dual_provider_false(
        self, mock_registry, mock_store
    ):
        """When V3_DUAL_PROVIDER=false, only Docling runs regardless of MINERU_ENABLED."""
        from commands.source_commands import _run_dual_provider_extraction

        mock_docling = MagicMock()
        mock_docling.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=5)]
        )
        mock_registry.return_value.get_provider.return_value = mock_docling

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "single_provider"
        # Only one extract call (Docling) — MinerU not requested
        assert mock_docling.extract.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_mineru_not_called_when_mineru_disabled(
        self, mock_registry, mock_store
    ):
        """When MINERU_ENABLED=false, only Docling runs."""
        from commands.source_commands import _run_dual_provider_extraction

        mock_docling = MagicMock()
        mock_docling.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=3)]
        )
        mock_registry.return_value.get_provider.return_value = mock_docling

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert len(result) == 1
        assert all(r["consensus_tier"] == "single_provider" for r in result)
        assert mock_docling.extract.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_both_flags_must_be_true_for_dual_provider(
        self, mock_registry, mock_store
    ):
        """Both V3_DUAL_PROVIDER and MINERU_ENABLED must be true for dual extraction."""
        from commands.source_commands import _run_dual_provider_extraction

        mock_docling = MagicMock()
        mock_docling.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=4)]
        )
        mock_registry.return_value.get_provider.return_value = mock_docling

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert all(r["consensus_tier"] == "single_provider" for r in result)
        assert mock_docling.extract.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"MINERU_ENABLED": "true"}, clear=False)
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_v3_dual_provider_default_is_true(self, mock_registry, mock_store):
        """V3_DUAL_PROVIDER defaults to 'true'; with MINERU_ENABLED=true, MinerU is requested."""
        from commands.source_commands import _run_dual_provider_extraction
        from open_notebook.extractors.providers.base import ProviderError

        # Remove V3_DUAL_PROVIDER from env to test default behaviour
        env_without_flag = {
            k: v for k, v in os.environ.items() if k != "V3_DUAL_PROVIDER"
        }
        env_without_flag["MINERU_ENABLED"] = "true"

        mock_docling = MagicMock()
        mock_docling.extract.return_value = _docling_result([])
        mock_mineru = MagicMock()
        # Raise ProviderError so we can confirm it was attempted
        mock_mineru.extract.side_effect = ProviderError("mineru", "GPU not available")

        def get_provider(pid: str):
            if pid == "docling":
                return mock_docling
            return mock_mineru

        mock_registry.return_value.get_provider.side_effect = get_provider

        with patch.dict(os.environ, env_without_flag, clear=True):
            result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        # MinerU was attempted (get_provider called with "mineru")
        calls = [
            c.args[0] for c in mock_registry.return_value.get_provider.call_args_list
        ]
        assert "mineru" in calls


# ---------------------------------------------------------------------------
# 2. TestRunDualProviderExtraction
# ---------------------------------------------------------------------------


class TestRunDualProviderExtraction:
    """Tests for _run_dual_provider_extraction() orchestration."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_dual_provider_runs_docling_then_mineru(
        self, mock_registry, mock_store
    ):
        """Docling extract is called before MinerU extract (sequential execution)."""
        from commands.source_commands import _run_dual_provider_extraction

        call_order: list[str] = []

        docling_mock = MagicMock()
        mineru_mock = MagicMock()

        def docling_extract(*args, **kwargs):
            call_order.append("docling")
            return _docling_result([])

        def mineru_extract(*args, **kwargs):
            call_order.append("mineru")
            return _mineru_result([])

        docling_mock.extract.side_effect = docling_extract
        mineru_mock.extract.side_effect = mineru_extract

        def get_provider(pid: str):
            if pid == "docling":
                return docling_mock
            return mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        _, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert call_order == ["docling", "mineru"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_store_raw_extractions_called_twice_in_dual_mode(
        self, mock_registry, mock_store
    ):
        """_store_raw_extractions is called once per provider in dual mode."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table(page=1)])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table(page=2)])

        def get_provider(pid: str):
            if pid == "docling":
                return docling_mock
            return mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        _, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert mock_store.call_count == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_mineru_provider_error_falls_back_to_docling(
        self, mock_registry, mock_store
    ):
        """MinerU ProviderError → graceful fallback to Docling-only results."""
        from commands.source_commands import _run_dual_provider_extraction
        from open_notebook.extractors.providers.base import ProviderError

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=7)]
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.side_effect = ProviderError("mineru", "CUDA OOM")

        def get_provider(pid: str):
            if pid == "docling":
                return docling_mock
            return mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "single_provider"
        # _store_raw_extractions called once (Docling only — MinerU failed before storing)
        assert mock_store.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_single_provider_tables_have_correct_consensus_tier(
        self, mock_registry, mock_store
    ):
        """Single-provider path always produces consensus_tier='single_provider'."""
        from commands.source_commands import _run_dual_provider_extraction

        mock_docling = MagicMock()
        mock_docling.extract.return_value = _docling_result(
            [_make_table(page=1), _make_table(page=2, table_index=1)]
        )
        mock_registry.return_value.get_provider.return_value = mock_docling

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        assert len(result) == 2
        assert all(r["consensus_tier"] == "single_provider" for r in result)

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_dual_extraction_produces_merged_tables(
        self, mock_registry, mock_store
    ):
        """AC8 integration proxy: dual extraction -> consensus -> merged table sections.

        Docling returns tables on pages 1, 2.
        MinerU returns tables on pages 1, 3.
        Expected result: 3 merged tables (pages 1, 2, 3).
        Page 1: both providers present (agreement or conflict tier).
        Page 2: Docling only (single_provider).
        Page 3: MinerU only (single_provider).
        """
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result(
            [
                _make_table(table_index=0, page=1, row_count=10),
                _make_table(table_index=1, page=2, row_count=5),
            ]
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result(
            [
                _make_table(table_index=0, page=1, row_count=10),
                _make_table(table_index=1, page=3, row_count=8),
            ]
        )

        def get_provider(pid: str):
            if pid == "docling":
                return docling_mock
            return mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        result, _ = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

        # Three distinct pages in result
        assert len(result) == 3

        tiers_by_page = {r["page"]: r["consensus_tier"] for r in result}

        # Page 1: both providers -> agreement (divergence=0.0)
        assert tiers_by_page[1] in (
            "multi_provider_agreement",
            "multi_provider_conflict",
        )
        # Page 2: Docling only -> single_provider
        assert tiers_by_page[2] == "single_provider"
        # Page 3: MinerU only -> single_provider
        assert tiers_by_page[3] == "single_provider"

        # _store_raw_extractions called once for each provider
        assert mock_store.call_count == 2


# ---------------------------------------------------------------------------
# 3. TestMergeProviderTables
# ---------------------------------------------------------------------------


class TestMergeProviderTables:
    """Pure function tests for _merge_provider_tables()."""

    def test_agreement_page_tier(self):
        """row_divergence <= 0.40 → multi_provider_agreement."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result([_make_table(page=2, row_count=10, html="<d/>")])
        mineru = _mineru_result([_make_table(page=2, row_count=9, html="<m/>")])

        result = _merge_provider_tables(docling, mineru)

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "multi_provider_agreement"
        assert result[0]["html"] == "<m/>"  # MinerU HTML preferred
        assert result[0]["markdown"] == "md"  # Docling markdown preferred

    def test_conflict_page_tier(self):
        """row_divergence > 0.40 → multi_provider_conflict."""
        from commands.source_commands import _merge_provider_tables

        # divergence = |20-5|/20 = 0.75 > 0.40
        docling = _docling_result(
            [_make_table(page=1, row_count=20, html="<d/>", markdown="doc-md")]
        )
        mineru = _mineru_result(
            [_make_table(page=1, row_count=5, html="<m/>", markdown="min-md")]
        )

        result = _merge_provider_tables(docling, mineru)

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "multi_provider_conflict"

    def test_single_provider_docling_only_page(self):
        """Page with only Docling table gets consensus_tier='single_provider'."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result([_make_table(page=5, row_count=3)])
        mineru = _mineru_result([])

        result = _merge_provider_tables(docling, mineru)

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "single_provider"
        assert result[0]["consensus_scores"] is None

    def test_single_provider_mineru_only_page(self):
        """Page with only MinerU table gets consensus_tier='single_provider'."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result([])
        mineru = _mineru_result([_make_table(page=7, row_count=6)])

        result = _merge_provider_tables(docling, mineru)

        assert len(result) == 1
        assert result[0]["consensus_tier"] == "single_provider"
        assert result[0]["consensus_scores"] is None

    def test_mineru_html_preferred_when_available(self):
        """When both providers have HTML, MinerU's is stored as the merged html."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [_make_table(page=3, row_count=5, html="docling-html")]
        )
        mineru = _mineru_result([_make_table(page=3, row_count=5, html="mineru-html")])

        result = _merge_provider_tables(docling, mineru)

        assert result[0]["html"] == "mineru-html"

    def test_docling_markdown_retained_when_merging(self):
        """Docling markdown is preferred over MinerU markdown when merging."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [_make_table(page=4, row_count=5, markdown="docling-md")]
        )
        mineru = _mineru_result(
            [_make_table(page=4, row_count=5, markdown="mineru-md")]
        )

        result = _merge_provider_tables(docling, mineru)

        assert result[0]["markdown"] == "docling-md"

    def test_unknown_page_is_single_provider(self):
        """Tables with page <= 0 are always treated as single_provider."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [_make_table(table_index=0, page=-1, row_count=2, html="<d/>")]
        )
        mineru = _mineru_result(
            [_make_table(table_index=0, page=-1, row_count=2, html="<m/>")]
        )

        result = _merge_provider_tables(docling, mineru)

        # Both unknown-page tables appended as single_provider (no page-based grouping)
        assert all(r["consensus_tier"] == "single_provider" for r in result)

    def test_empty_providers_returns_empty_list(self):
        """Two empty provider results produce an empty merged list."""
        from commands.source_commands import _merge_provider_tables

        result = _merge_provider_tables(_docling_result([]), _mineru_result([]))

        assert result == []

    def test_fallback_to_docling_html_when_mineru_html_empty(self):
        """Empty MinerU html falls back to Docling html."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [_make_table(page=2, row_count=5, html="docling-html")]
        )
        mineru = _mineru_result([_make_table(page=2, row_count=5, html="")])

        result = _merge_provider_tables(docling, mineru)

        assert result[0]["html"] == "docling-html"

    def test_consensus_scores_values_correct(self):
        """Symmetric row counts → row_divergence=0.0, agreement=1.0, equal weights."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result([_make_table(page=1, row_count=10)])
        mineru = _mineru_result([_make_table(page=1, row_count=10)])

        result = _merge_provider_tables(docling, mineru)

        scores = result[0]["consensus_scores"]
        assert scores["row_divergence"] == pytest.approx(0.0)
        assert scores["agreement"] == pytest.approx(1.0)
        assert scores["docling"] == pytest.approx(0.5)
        assert scores["mineru"] == pytest.approx(0.5)

    def test_consensus_scores_zero_rows_guard(self):
        """Both providers returning 0 rows must not raise ZeroDivisionError."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [_make_table(page=1, row_count=0, col_count=0, columns=[])]
        )
        mineru = _mineru_result(
            [_make_table(page=1, row_count=0, col_count=0, columns=[])]
        )

        result = _merge_provider_tables(docling, mineru)

        scores = result[0]["consensus_scores"]
        assert scores["row_divergence"] == 0.0
        assert scores["agreement"] == pytest.approx(1.0)
        assert scores["docling"] == 0.0
        assert scores["mineru"] == 0.0

    def test_multiple_pages_merged_correctly(self):
        """Multi-page scenario: Docling=[1,2,3], MinerU=[1,3,4] → 4 merged tables."""
        from commands.source_commands import _merge_provider_tables

        docling = _docling_result(
            [
                _make_table(table_index=0, page=1, row_count=5),
                _make_table(table_index=1, page=2, row_count=3),
                _make_table(table_index=2, page=3, row_count=8),
            ]
        )
        mineru = _mineru_result(
            [
                _make_table(table_index=0, page=1, row_count=5),
                _make_table(table_index=1, page=3, row_count=7),
                _make_table(table_index=2, page=4, row_count=6),
            ]
        )

        result = _merge_provider_tables(docling, mineru)

        assert len(result) == 4
        tiers_by_page = {r["page"]: r["consensus_tier"] for r in result}
        # Page 1: both providers
        assert tiers_by_page[1] in (
            "multi_provider_agreement",
            "multi_provider_conflict",
        )
        # Page 2: Docling only
        assert tiers_by_page[2] == "single_provider"
        # Page 3: both providers
        assert tiers_by_page[3] in (
            "multi_provider_agreement",
            "multi_provider_conflict",
        )
        # Page 4: MinerU only
        assert tiers_by_page[4] == "single_provider"


# ---------------------------------------------------------------------------
# 4. TestStorageWithConsensus
# ---------------------------------------------------------------------------


class TestStorageWithConsensus:
    """Tests that _store_docling_tables() writes consensus fields to repo_create."""

    @pytest.mark.asyncio
    @patch("commands.source_commands.repo_create", new_callable=AsyncMock)
    @patch("commands.source_commands.ensure_record_id", side_effect=lambda x: x)
    async def test_store_docling_tables_writes_consensus_tier(
        self, mock_ensure, mock_create
    ):
        """_store_docling_tables passes consensus_tier to repo_create."""
        from commands.source_commands import _store_docling_tables

        tables = [
            {
                "page": 3,
                "html": "<table/>",
                "markdown": "md",
                "csv": "a,b",
                "consensus_tier": "multi_provider_agreement",
                "consensus_scores": {
                    "docling": 0.5,
                    "mineru": 0.5,
                    "agreement": 1.0,
                    "row_divergence": 0.0,
                },
            }
        ]
        await _store_docling_tables("source:abc", tables)

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[0][1]
        assert call_kwargs["consensus_tier"] == "multi_provider_agreement"
        assert call_kwargs["consensus_scores"]["agreement"] == 1.0

    @pytest.mark.asyncio
    @patch("commands.source_commands.repo_create", new_callable=AsyncMock)
    @patch("commands.source_commands.ensure_record_id", side_effect=lambda x: x)
    async def test_store_docling_tables_writes_consensus_scores(
        self, mock_ensure, mock_create
    ):
        """_store_docling_tables passes full consensus_scores dict to repo_create."""
        from commands.source_commands import _store_docling_tables

        scores = {
            "docling": 0.6,
            "mineru": 0.4,
            "agreement": 0.8,
            "row_divergence": 0.2,
        }
        tables = [
            {
                "page": 1,
                "html": "<table/>",
                "markdown": "md",
                "csv": None,
                "consensus_tier": "multi_provider_agreement",
                "consensus_scores": scores,
            }
        ]
        await _store_docling_tables("source:abc", tables)

        call_kwargs = mock_create.call_args[0][1]
        assert call_kwargs["consensus_scores"] == scores

    @pytest.mark.asyncio
    @patch("commands.source_commands.repo_create", new_callable=AsyncMock)
    @patch("commands.source_commands.ensure_record_id", side_effect=lambda x: x)
    async def test_store_docling_tables_none_consensus_for_single_provider(
        self, mock_ensure, mock_create
    ):
        """Single-provider tables store consensus_tier='single_provider' and scores=None."""
        from commands.source_commands import _store_docling_tables

        tables = [
            {
                "page": 1,
                "html": "<table/>",
                "markdown": "md",
                "csv": None,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
        ]
        await _store_docling_tables("source:abc", tables)

        call_kwargs = mock_create.call_args[0][1]
        assert call_kwargs["consensus_tier"] == "single_provider"
        assert call_kwargs["consensus_scores"] is None


# ---------------------------------------------------------------------------
# 5. TestStrategyRegistryF9F10
# ---------------------------------------------------------------------------


class TestStrategyRegistryF9F10:
    """Tests for F9 and F10 entries in the strategy registry."""

    def test_fallback_matrix_has_ten_entries(self):
        """FALLBACK_MATRIX has exactly 10 entries (F1–F10)."""
        from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX

        assert len(FALLBACK_MATRIX) == 10

    def test_f9_provider_conflict_contract_exists(self):
        """F9 contract is present in FALLBACK_MATRIX."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        assert FallbackId.F9_PROVIDER_CONFLICT in FALLBACK_MATRIX

    def test_f10_consensus_arbitration_contract_exists(self):
        """F10 contract is present in FALLBACK_MATRIX."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        assert FallbackId.F10_CONSENSUS_ARBITRATION in FALLBACK_MATRIX

    def test_f9_is_not_retry_eligible(self):
        """F9 contract is non-fatal and not retry-eligible."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        contract = FALLBACK_MATRIX[FallbackId.F9_PROVIDER_CONFLICT]
        assert contract.retry_eligible is False
        assert "non-fatal" in contract.severity

    def test_f10_is_not_retry_eligible(self):
        """F10 contract is informational and not retry-eligible."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        contract = FALLBACK_MATRIX[FallbackId.F10_CONSENSUS_ARBITRATION]
        assert contract.retry_eligible is False
        assert contract.severity == "informational"

    def test_f9_and_f10_exist_in_matrix(self):
        """Both F9 and F10 exist in FALLBACK_MATRIX."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        assert FallbackId.F9_PROVIDER_CONFLICT in FALLBACK_MATRIX
        assert FallbackId.F10_CONSENSUS_ARBITRATION in FALLBACK_MATRIX

    def test_all_ten_fallback_ids_in_matrix(self):
        """Every FallbackId enum member (all 10) has a corresponding matrix entry."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        for fid in FallbackId:
            assert fid in FALLBACK_MATRIX, f"{fid} missing from FALLBACK_MATRIX"

    def test_f9_telemetry_tag(self):
        """F9 telemetry tag is 'fallback.provider_conflict'."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        contract = FALLBACK_MATRIX[FallbackId.F9_PROVIDER_CONFLICT]
        assert contract.telemetry_tag == "fallback.provider_conflict"

    def test_f10_telemetry_tag(self):
        """F10 telemetry tag is 'fallback.consensus_arbitration'."""
        from open_notebook.extractors.strategy_registry import (
            FALLBACK_MATRIX,
            FallbackId,
        )

        contract = FALLBACK_MATRIX[FallbackId.F10_CONSENSUS_ARBITRATION]
        assert contract.telemetry_tag == "fallback.consensus_arbitration"
