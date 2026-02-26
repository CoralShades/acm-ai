"""Tests for MinerU activation logic in source processing command."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from commands import source_commands
from open_notebook.database.repository import ensure_record_id


class _CapturingSection:
    """Lightweight ACMTableSection test double."""

    saved_payloads = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def save(self):
        self.__class__.saved_payloads.append(self.kwargs)


class TestResolveSourcePdfPath:
    def test_returns_none_without_asset(self):
        source = SimpleNamespace(id="source:test", asset=None)

        assert source_commands._resolve_source_pdf_path(source) is None

    def test_returns_none_for_non_pdf(self):
        source = SimpleNamespace(
            id="source:test", asset=SimpleNamespace(file_path="/tmp/file.txt")
        )

        assert source_commands._resolve_source_pdf_path(source) is None

    def test_returns_pdf_path_for_pdf_asset(self):
        source = SimpleNamespace(
            id="source:test", asset=SimpleNamespace(file_path="/tmp/file.pdf")
        )

        assert source_commands._resolve_source_pdf_path(source) == "/tmp/file.pdf"


class TestStoreMineruTables:
    @pytest.mark.asyncio
    async def test_skips_when_source_has_no_pdf(self):
        source = SimpleNamespace(
            id="source:test", asset=SimpleNamespace(file_path="/tmp/file.txt")
        )

        with patch.object(
            source_commands,
            "_update_table_extraction_metadata",
            new=AsyncMock(),
        ) as mock_metadata:
            count = await source_commands._store_mineru_tables(source)

        assert count == 0
        mock_metadata.assert_awaited_once_with("source:test", "docling", 0)

    @pytest.mark.asyncio
    async def test_falls_back_when_mineru_extraction_raises(self):
        source = SimpleNamespace(
            id="source:test", asset=SimpleNamespace(file_path="/tmp/file.pdf")
        )
        mock_extractor = MagicMock()
        mock_extractor.extract_tables_from_pdf.side_effect = RuntimeError("boom")

        with (
            patch.object(
                source_commands,
                "_update_table_extraction_metadata",
                new=AsyncMock(),
            ) as mock_metadata,
            patch(
                "open_notebook.extractors.mineru_table_extractor.MineruTableExtractor",
                return_value=mock_extractor,
            ),
        ):
            count = await source_commands._store_mineru_tables(source)

        assert count == 0
        mock_metadata.assert_awaited_once_with("source:test", "docling", 0)

    @pytest.mark.asyncio
    async def test_saves_html_tables_and_sets_hybrid_metadata(self):
        source = SimpleNamespace(
            id="source:test", asset=SimpleNamespace(file_path="/tmp/file.pdf")
        )
        mock_extractor = MagicMock()
        mock_extractor.extract_tables_from_pdf.return_value = [
            SimpleNamespace(page_number=3, html="<table><tr><td>A</td></tr></table>"),
            SimpleNamespace(page_number=4, html="<table><tr><td>B</td></tr></table>"),
            SimpleNamespace(page_number=5, html=""),
        ]

        _CapturingSection.saved_payloads = []

        with (
            patch.object(
                source_commands,
                "_update_table_extraction_metadata",
                new=AsyncMock(),
            ) as mock_metadata,
            patch.object(source_commands, "repo_query", new=AsyncMock()) as mock_query,
            patch.object(source_commands, "ACMTableSection", _CapturingSection),
            patch(
                "open_notebook.extractors.mineru_table_extractor.MineruTableExtractor",
                return_value=mock_extractor,
            ),
        ):
            count = await source_commands._store_mineru_tables(source)

        assert count == 2
        assert len(_CapturingSection.saved_payloads) == 2
        assert _CapturingSection.saved_payloads[0]["page_start"] == 3
        assert _CapturingSection.saved_payloads[0]["table_type"] == (
            source_commands.MINERU_TABLE_TYPE
        )
        assert _CapturingSection.saved_payloads[1]["page_start"] == 4

        assert mock_query.await_count == 1
        delete_query, delete_params = mock_query.await_args.args
        assert "DELETE acm_table_section" in delete_query
        assert delete_params["source_id"] == ensure_record_id("source:test")

        mock_metadata.assert_awaited_once_with("source:test", "hybrid", 2)
