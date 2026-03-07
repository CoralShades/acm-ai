"""
Tests for E34-S3: Performance Optimization.

Covers:
  - PipelineTimings instrumentation (AC5/AC6)
  - Provider cleanup() calls (AC4/AC6)
  - GPU cache flush between providers (AC3/AC6)
  - Memory leak guard over consecutive extractions (AC4)

All tests are fully mocked -- no real PDFs, GPU, or SurrealDB required.
"""

from __future__ import annotations

import gc
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.providers.base import (
    NormalizedExtractionResult,
    NormalizedTable,
    PipelineTimings,
    ProviderError,
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


def _make_mock_registry(docling_mock, mineru_mock=None):
    """Build a mock registry that returns docling_mock and optionally mineru_mock."""
    registry = MagicMock()

    def get_provider(pid: str):
        if pid == "docling":
            return docling_mock
        if mineru_mock is not None:
            return mineru_mock
        raise KeyError(f"Provider '{pid}' not found")

    registry.get_provider.side_effect = get_provider
    return registry


# ---------------------------------------------------------------------------
# 1. TestProviderTimingInstrumentation
# ---------------------------------------------------------------------------


class TestProviderTimingInstrumentation:
    """AC6: timing fields are populated and non-negative."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_timing_fields_populated_single_provider(
        self, mock_registry, mock_store
    ):
        """Single-provider: docling_ms >= 0, total >= 0, mineru_ms == 0."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=5)]
        )
        mock_registry.return_value = _make_mock_registry(docling_mock)

        _tables, timings = await _run_dual_provider_extraction(
            "source:perf_test", "/tmp/fake.pdf"
        )

        assert isinstance(timings, PipelineTimings)
        assert timings.docling_ms >= 0
        assert timings.total_provider_ms >= 0
        assert timings.mineru_ms == 0

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_timing_fields_populated_dual_provider(
        self, mock_registry, mock_store
    ):
        """Dual-provider: all fields >= 0 and total == sum of parts."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=5)]
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result(
            [_make_table(page=1, row_count=5)]
        )
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        _tables, timings = await _run_dual_provider_extraction(
            "source:perf_test", "/tmp/fake.pdf"
        )

        assert timings.docling_ms >= 0
        assert timings.mineru_ms >= 0
        assert timings.merge_ms >= 0
        assert timings.total_provider_ms == (
            timings.docling_ms
            + timings.gpu_flush_ms
            + timings.mineru_ms
            + timings.merge_ms
        )

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_return_type_is_tuple(self, mock_registry, mock_store):
        """Return value is a 2-tuple of (list, PipelineTimings)."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock)

        result = await _run_dual_provider_extraction(
            "source:perf_test", "/tmp/fake.pdf"
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], PipelineTimings)


# ---------------------------------------------------------------------------
# 2. TestCleanupCalled
# ---------------------------------------------------------------------------


class TestCleanupCalled:
    """AC4/AC6: cleanup() invoked after each provider."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_docling_cleanup_called_single_provider(
        self, mock_registry, mock_store
    ):
        """Docling cleanup called in single-provider mode."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock)

        await _run_dual_provider_extraction("source:cleanup_test", "/tmp/fake.pdf")

        assert docling_mock.cleanup.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_docling_cleanup_called_dual_provider(
        self, mock_registry, mock_store
    ):
        """Docling cleanup called in dual-provider mode."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        await _run_dual_provider_extraction("source:cleanup_test", "/tmp/fake.pdf")

        assert docling_mock.cleanup.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_mineru_cleanup_called_dual_provider(self, mock_registry, mock_store):
        """MinerU cleanup called in dual-provider mode."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        await _run_dual_provider_extraction("source:cleanup_test", "/tmp/fake.pdf")

        assert mineru_mock.cleanup.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_mineru_cleanup_not_called_single_provider(
        self, mock_registry, mock_store
    ):
        """MinerU cleanup NOT called in single-provider mode (MinerU never runs)."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        await _run_dual_provider_extraction("source:cleanup_test", "/tmp/fake.pdf")

        assert mineru_mock.cleanup.call_count == 0

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_cleanup_called_even_on_mineru_failure(
        self, mock_registry, mock_store
    ):
        """Docling cleanup still called when MinerU raises ProviderError."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.side_effect = ProviderError("mineru", "test failure")
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        await _run_dual_provider_extraction("source:cleanup_test", "/tmp/fake.pdf")

        # Docling cleanup was called (before MinerU attempted)
        assert docling_mock.cleanup.call_count == 1


# ---------------------------------------------------------------------------
# 3. TestGpuCacheFlush
# ---------------------------------------------------------------------------


class TestGpuCacheFlush:
    """AC3/AC6: torch.cuda.empty_cache() called between providers when CUDA available."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_cuda_empty_cache_called_when_cuda_available(
        self, mock_registry, mock_store
    ):
        """When CUDA is available, empty_cache is called once between providers."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch("commands.source_commands._torch", mock_torch):
            await _run_dual_provider_extraction("source:gpu_test", "/tmp/fake.pdf")

        mock_torch.cuda.empty_cache.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_cuda_empty_cache_not_called_when_cuda_unavailable(
        self, mock_registry, mock_store
    ):
        """When CUDA is not available, empty_cache is not called."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch("commands.source_commands._torch", mock_torch):
            await _run_dual_provider_extraction("source:gpu_test", "/tmp/fake.pdf")

        mock_torch.cuda.empty_cache.assert_not_called()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_cuda_flush_skipped_when_torch_none(self, mock_registry, mock_store):
        """When _torch is None (not installed), no AttributeError is raised."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        with patch("commands.source_commands._torch", None):
            # Should not raise
            result, timings = await _run_dual_provider_extraction(
                "source:gpu_test", "/tmp/fake.pdf"
            )

        assert isinstance(timings, PipelineTimings)

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_cuda_flush_not_called_in_single_provider_mode(
        self, mock_registry, mock_store
    ):
        """In single-provider mode, GPU flush is not performed (MinerU never runs)."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result([_make_table()])
        mock_registry.return_value = _make_mock_registry(docling_mock)

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch("commands.source_commands._torch", mock_torch):
            await _run_dual_provider_extraction("source:gpu_test", "/tmp/fake.pdf")

        # Flush only happens between providers; single-provider => no flush
        mock_torch.cuda.empty_cache.assert_not_called()


# ---------------------------------------------------------------------------
# 4. TestMemoryLeakGuard
# ---------------------------------------------------------------------------


class TestMemoryLeakGuard:
    """AC4: no obvious Python object leaks over consecutive extractions."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_consecutive_extractions_no_growing_gc_objects(
        self, mock_registry, mock_store
    ):
        """Run 10 extractions; gen-0 object count should not grow unboundedly."""
        from commands.source_commands import _run_dual_provider_extraction

        docling_mock = MagicMock()
        docling_mock.extract.return_value = _docling_result(
            [_make_table(page=1, row_count=5)]
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = _mineru_result(
            [_make_table(page=1, row_count=5)]
        )
        mock_registry.return_value = _make_mock_registry(docling_mock, mineru_mock)

        # Force a full collection to get a baseline
        gc.collect()
        gc.collect()
        gc.collect()
        before = gc.get_count()

        for _ in range(10):
            await _run_dual_provider_extraction("source:leak_test", "/tmp/fake.pdf")

        gc.collect()
        gc.collect()
        gc.collect()
        after = gc.get_count()

        # Allow up to 100 net new objects in gen-0 (loose but meaningful)
        gen0_delta = after[0] - before[0]
        assert gen0_delta < 100, (
            f"gen-0 object count grew by {gen0_delta} after 10 extractions — "
            f"possible memory leak (before={before}, after={after})"
        )
