"""
Unit tests for TableFormer feature flag in source graph content_process().

Tests verify that the DOCLING_TABLE_STRUCTURE environment variable correctly
controls TableFormer activation in the Docling document processing pipeline.

See: docs/architecture/adr-tableformer-integration.md (Decision D1)
See: docs/sprint-artifacts/e24-s1-activate-tableformer.md
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestContentProcessTableFormer:
    """Test suite for TableFormer feature flag behavior in content_process()."""

    @pytest.fixture
    def mock_state(self):
        """Create a minimal SourceState-like dict for content_process()."""
        return {
            "content_state": {
                "url": "https://example.com/test.pdf",
                "file_path": "/tmp/test.pdf",
            },
        }

    @pytest.mark.asyncio
    async def test_content_process_tableformer_enabled(self, monkeypatch, mock_state):
        """When DOCLING_TABLE_STRUCTURE=true, content_state gets TableFormer keys."""
        monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", "true")

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            # Mock ModelManager to avoid DB calls
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            # Verify the content_state was configured for TableFormer
            content_state = mock_extract.call_args[0][0]
            assert content_state["document_engine"] == "docling"
            assert content_state["docling_table_structure"] is True
            assert content_state["docling_table_mode"] == "accurate"

    @pytest.mark.asyncio
    async def test_content_process_tableformer_enabled_case_insensitive(
        self, monkeypatch, mock_state
    ):
        """Feature flag should be case-insensitive (TRUE, True, true all work)."""
        monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", "TRUE")

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            content_state = mock_extract.call_args[0][0]
            assert content_state["document_engine"] == "docling"
            assert content_state["docling_table_structure"] is True

    @pytest.mark.asyncio
    async def test_content_process_tableformer_custom_mode(
        self, monkeypatch, mock_state
    ):
        """DOCLING_TABLE_MODE env var controls the TableFormer mode."""
        monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", "true")
        monkeypatch.setenv("DOCLING_TABLE_MODE", "fast")

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            content_state = mock_extract.call_args[0][0]
            assert content_state["docling_table_mode"] == "fast"

    @pytest.mark.asyncio
    async def test_content_process_tableformer_disabled(self, monkeypatch, mock_state):
        """When DOCLING_TABLE_STRUCTURE=false, no TableFormer keys set."""
        monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", "false")

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            content_state = mock_extract.call_args[0][0]
            assert content_state["document_engine"] == "auto"
            assert "docling_table_structure" not in content_state
            assert "docling_table_mode" not in content_state

    @pytest.mark.asyncio
    async def test_content_process_tableformer_default_off(
        self, monkeypatch, mock_state
    ):
        """When env var absent, TableFormer is disabled (safe default)."""
        monkeypatch.delenv("DOCLING_TABLE_STRUCTURE", raising=False)

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            content_state = mock_extract.call_args[0][0]
            assert content_state["document_engine"] == "auto"
            assert "docling_table_structure" not in content_state
            assert "docling_table_mode" not in content_state

    @pytest.mark.asyncio
    async def test_content_process_url_engine_unchanged(self, monkeypatch, mock_state):
        """URL engine setting is not affected by TableFormer flag."""
        monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", "true")

        with (
            patch(
                "open_notebook.graphs.source.extract_content",
                new_callable=AsyncMock,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.source.ModelManager",
            ) as mock_mm,
        ):
            mock_manager = MagicMock()
            mock_defaults = MagicMock()
            mock_defaults.default_speech_to_text_model = None
            mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
            mock_mm.return_value = mock_manager

            mock_extract.return_value = mock_state["content_state"]

            from open_notebook.graphs.source import content_process

            await content_process(mock_state)

            content_state = mock_extract.call_args[0][0]
            assert content_state["url_engine"] == "auto"
            assert content_state["output_format"] == "markdown"

    @pytest.mark.asyncio
    async def test_content_process_output_format_always_markdown(
        self, monkeypatch, mock_state
    ):
        """Output format is always markdown regardless of TableFormer flag."""
        for flag_value in ["true", "false"]:
            monkeypatch.setenv("DOCLING_TABLE_STRUCTURE", flag_value)

            with (
                patch(
                    "open_notebook.graphs.source.extract_content",
                    new_callable=AsyncMock,
                ) as mock_extract,
                patch(
                    "open_notebook.graphs.source.ModelManager",
                ) as mock_mm,
            ):
                mock_manager = MagicMock()
                mock_defaults = MagicMock()
                mock_defaults.default_speech_to_text_model = None
                mock_manager.get_defaults = AsyncMock(return_value=mock_defaults)
                mock_mm.return_value = mock_manager

                mock_extract.return_value = mock_state["content_state"]

                from open_notebook.graphs.source import content_process

                await content_process(mock_state)

                content_state = mock_extract.call_args[0][0]
                assert content_state["output_format"] == "markdown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
