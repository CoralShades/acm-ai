"""Tests for E26-S3 Docling table injection in orchestrator.

Tests _get_docling_tables(), _inject_docling_tables(), and the
integration of Docling table injection into extract_building().
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.orchestrator import (
    BuildingExtractionPlan,
    BuildingExtractionStats,
    ExtractionStrategy,
    _get_docling_tables,
    _inject_docling_tables,
    extract_building,
)

# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

SAMPLE_TABLES = [
    {
        "id": "acm_table_section:t1",
        "source_id": "source:abc123",
        "page_start": 5,
        "page_end": 5,
        "raw_text": (
            "| Floor | Room | Product | Result |\n"
            "|-------|------|---------|--------|\n"
            "| Ground | Corridor | Vinyl sheet | Negative |\n"
            "| Ground | Office | Ceiling tiles | Positive |"
        ),
        "raw_html": "<table><tr><td>...</td></tr></table>",
        "table_type": "docling_direct_api",
    },
    {
        "id": "acm_table_section:t2",
        "source_id": "source:abc123",
        "page_start": 6,
        "page_end": 6,
        "raw_text": (
            "| Floor | Room | Product | Result |\n"
            "|-------|------|---------|--------|\n"
            "| First | Switch Room | Fuses | Assumed positive |\n"
            "| First | Corridor | Vinyl sheet | Same as 34511-039-001 |"
        ),
        "raw_html": "<table><tr><td>...</td></tr></table>",
        "table_type": "docling_direct_api",
    },
]

BUILDING_CONTENT = (
    "--- Page 5 ---\n"
    "Ground floor Corridor Floor Vinyl sheet Negative\n"
    "Ground floor Office Ceiling tiles Positive\n"
    "--- Page 6 ---\n"
    "First floor Switch Room Fuses Assumed positive\n"
)


def _make_plan(
    building_id: str = "B001",
    page_range: tuple = (5, 7),
    strategy: ExtractionStrategy = ExtractionStrategy.FULL_LLM,
) -> BuildingExtractionPlan:
    return BuildingExtractionPlan(
        building_id=building_id,
        building_name="Admin Building",
        page_range=page_range,
        strategy=strategy,
    )


def _make_source(source_id: str = "source:abc123"):
    source = MagicMock()
    source.id = source_id
    source.full_text = BUILDING_CONTENT
    source.title = "Test School"
    return source


# ---------------------------------------------------------------------------
# Test _get_docling_tables
# ---------------------------------------------------------------------------


class TestGetDoclingTables:
    @pytest.mark.asyncio
    async def test_returns_tables_for_valid_page_range(self):
        """_get_docling_tables returns tables when query finds matches."""
        with patch(
            "open_notebook.database.repository.repo_query",
            new_callable=AsyncMock,
            return_value=SAMPLE_TABLES,
        ) as mock_query, patch(
            "open_notebook.database.repository.ensure_record_id",
            side_effect=lambda x: x,
        ):
            result = await _get_docling_tables("source:abc123", 5, 7)

        assert len(result) == 2
        assert result[0]["page_start"] == 5
        assert result[1]["page_start"] == 6
        mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_tables(self):
        """_get_docling_tables returns [] when no tables match the page range."""
        with patch(
            "open_notebook.database.repository.repo_query",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "open_notebook.database.repository.ensure_record_id",
            side_effect=lambda x: x,
        ):
            result = await _get_docling_tables("source:abc123", 20, 25)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_query_error(self):
        """_get_docling_tables returns [] on any error (non-fatal)."""
        with patch(
            "open_notebook.database.repository.repo_query",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection failed"),
        ), patch(
            "open_notebook.database.repository.ensure_record_id",
            side_effect=lambda x: x,
        ):
            result = await _get_docling_tables("source:abc123", 5, 7)

        assert result == []


# ---------------------------------------------------------------------------
# Test _inject_docling_tables
# ---------------------------------------------------------------------------


class TestInjectDoclingTables:
    def test_appends_after_building_content(self):
        """Injected content starts with original building_content."""
        result = _inject_docling_tables(BUILDING_CONTENT, SAMPLE_TABLES)

        assert result.startswith(BUILDING_CONTENT)
        assert len(result) > len(BUILDING_CONTENT)

    def test_includes_page_numbers(self):
        """Each table section includes the page number."""
        result = _inject_docling_tables(BUILDING_CONTENT, SAMPLE_TABLES)

        assert "### Table (Page 5)" in result
        assert "### Table (Page 6)" in result

    def test_includes_important_instruction(self):
        """Injected content includes the IMPORTANT instruction about special rows."""
        result = _inject_docling_tables(BUILDING_CONTENT, SAMPLE_TABLES)

        assert "**IMPORTANT**" in result
        assert "Same as" in result
        assert "Not Sampled" in result
        assert "No Access" in result

    def test_returns_original_when_tables_empty(self):
        """Returns original building_content unchanged when tables list is empty."""
        result = _inject_docling_tables(BUILDING_CONTENT, [])

        assert result == BUILDING_CONTENT

    def test_includes_structured_header(self):
        """Injected content includes the structured table data header."""
        result = _inject_docling_tables(BUILDING_CONTENT, SAMPLE_TABLES)

        assert "## Structured Table Data" in result

    def test_includes_raw_text_content(self):
        """Injected content includes the actual DataFrame markdown."""
        result = _inject_docling_tables(BUILDING_CONTENT, SAMPLE_TABLES)

        assert "Vinyl sheet" in result
        assert "Assumed positive" in result
        assert "Same as 34511-039-001" in result

    def test_skips_tables_without_raw_text(self):
        """Tables with no raw_text field are skipped gracefully."""
        tables = [
            {"page_start": 5, "raw_text": "| data |"},
            {"page_start": 6, "raw_text": ""},
            {"page_start": 7},  # no raw_text key
        ]
        result = _inject_docling_tables(BUILDING_CONTENT, tables)

        assert "### Table (Page 5)" in result
        # Page 6 has empty raw_text, page 7 has no raw_text — both skipped
        assert "### Table (Page 6)" not in result
        assert "### Table (Page 7)" not in result


# ---------------------------------------------------------------------------
# Test extract_building with Docling injection
# ---------------------------------------------------------------------------


class TestExtractBuildingDoclingIntegration:
    @pytest.mark.asyncio
    async def test_with_docling_tables_enriches_context(self):
        """extract_building injects Docling tables into LLM context when available."""
        plan = _make_plan()
        source = _make_source()
        state = {"source": source, "model_id": "test-model"}

        mock_result = MagicMock()
        mock_result.records = []

        with patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            new_callable=AsyncMock,
            return_value=SAMPLE_TABLES,
        ) as mock_get, patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_llm:
            records, stats = await extract_building(plan, BUILDING_CONTENT, state)

        # Verify _get_docling_tables was called with correct args
        mock_get.assert_called_once_with("source:abc123", 5, 7)

        # Verify the LLM received enriched content (contains structured header)
        llm_content_arg = mock_llm.call_args[0][0]
        assert "## Structured Table Data" in llm_content_arg
        assert "### Table (Page 5)" in llm_content_arg

    @pytest.mark.asyncio
    async def test_without_docling_tables_uses_original(self):
        """extract_building uses original content when no Docling tables exist."""
        plan = _make_plan()
        source = _make_source()
        state = {"source": source, "model_id": "test-model"}

        with patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_llm:
            records, stats = await extract_building(plan, BUILDING_CONTENT, state)

        # Verify the LLM received original content (no structured header)
        llm_content_arg = mock_llm.call_args[0][0]
        assert "## Structured Table Data" not in llm_content_arg

    @pytest.mark.asyncio
    async def test_docling_injection_failure_is_nonfatal(self):
        """extract_building continues with original content if Docling injection fails."""
        plan = _make_plan()
        source = _make_source()
        state = {"source": source, "model_id": "test-model"}

        with patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ), patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_llm:
            records, stats = await extract_building(plan, BUILDING_CONTENT, state)

        # Should still proceed — non-fatal
        llm_content_arg = mock_llm.call_args[0][0]
        assert "## Structured Table Data" not in llm_content_arg

    @pytest.mark.asyncio
    async def test_no_source_in_state_skips_injection(self):
        """extract_building skips Docling injection when state has no source."""
        plan = _make_plan()
        state = {"model_id": "test-model"}

        with patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            new_callable=AsyncMock,
        ) as mock_get, patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            return_value=[],
        ):
            records, stats = await extract_building(plan, BUILDING_CONTENT, state)

        # _get_docling_tables should NOT have been called
        mock_get.assert_not_called()
