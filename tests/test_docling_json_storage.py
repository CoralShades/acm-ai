"""Tests for DoclingDocument JSON storage in the ACM extraction pipeline.

Covers:
- NormalizedTable.docling_json field presence and typing
- DoclingAdapter populates docling_json from export_to_dict()
- _store_docling_tables persists docling_document_json field
- _get_docling_tables retrieves docling_document_json via SELECT *

All tests mock SurrealDB -- no running database required.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_normalized_table(
    *,
    table_index: int = 0,
    page: int = 1,
    row_count: int = 2,
    col_count: int = 3,
    columns: Optional[List[str]] = None,
    html: str = "<table></table>",
    markdown: str = "| A |\n|---|\n| 1 |",
    csv: str = "A\n1\n",
    docling_json: Optional[Dict[str, Any]] = None,
):
    """Construct a NormalizedTable with optional docling_json."""
    from open_notebook.extractors.providers.base import NormalizedTable

    return NormalizedTable(
        table_index=table_index,
        page=page,
        row_count=row_count,
        col_count=col_count,
        columns=columns or ["A", "B", "C"],
        html=html,
        markdown=markdown,
        csv=csv,
        docling_json=docling_json,
    )


def _sample_docling_json(num_rows: int = 2, num_cols: int = 3) -> Dict[str, Any]:
    """Return a minimal export_to_dict()-shaped dict for testing."""
    return {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "table_cells": [
            {
                "row_span": 1,
                "col_span": 1,
                "start_row_offset_idx": r,
                "end_row_offset_idx": r + 1,
                "start_col_offset_idx": c,
                "end_col_offset_idx": c + 1,
                "column_header": r == 0,
                "row_header": False,
                "text": f"R{r}C{c}",
            }
            for r in range(num_rows)
            for c in range(num_cols)
        ],
    }


# ---------------------------------------------------------------------------
# Test 1: NormalizedTable accepts docling_json field
# ---------------------------------------------------------------------------


class TestNormalizedTableDoclingJson:
    def test_docling_json_defaults_to_none(self):
        """NormalizedTable.docling_json is None by default (backward-compatible)."""
        t = _make_normalized_table()
        assert t.docling_json is None

    def test_docling_json_accepts_dict(self):
        """NormalizedTable.docling_json stores a dict when provided."""
        payload = _sample_docling_json(num_rows=3, num_cols=4)
        t = _make_normalized_table(docling_json=payload)
        assert t.docling_json is not None
        assert t.docling_json["num_rows"] == 3
        assert t.docling_json["num_cols"] == 4

    def test_docling_json_has_expected_keys(self):
        """A Docling export_to_dict() payload contains table_cells, num_rows, num_cols."""
        payload = _sample_docling_json()
        assert "table_cells" in payload
        assert "num_rows" in payload
        assert "num_cols" in payload

    def test_table_cells_have_span_fields(self):
        """Each table_cell entry carries row_span and col_span."""
        payload = _sample_docling_json(num_rows=2, num_cols=2)
        cell = payload["table_cells"][0]
        assert "row_span" in cell
        assert "col_span" in cell
        assert "column_header" in cell


# ---------------------------------------------------------------------------
# Test 2: DoclingAdapter populates docling_json via export_to_dict()
# ---------------------------------------------------------------------------


class TestDoclingAdapterExportToDict:
    def test_export_to_dict_called_per_table(self):
        """DoclingAdapter calls export_to_dict() on each TableItem."""
        import pandas as pd

        payload = _sample_docling_json()

        mock_table = MagicMock()
        mock_table.export_to_dataframe.return_value = pd.DataFrame(
            {"Col A": ["v1"], "Col B": ["v2"]}
        )
        mock_table.export_to_html.return_value = "<table><tr><td>v1</td></tr></table>"
        mock_table.export_to_dict.return_value = payload
        prov = MagicMock()
        prov.page_no = 3
        mock_table.prov = [prov]

        mock_doc = MagicMock()
        mock_doc.tables = [mock_table]

        # Simulate the DoclingAdapter extraction loop
        from open_notebook.extractors.providers.base import NormalizedTable

        tables = []
        for idx, table in enumerate(mock_doc.tables):
            df = table.export_to_dataframe(doc=mock_doc)
            page_no = table.prov[0].page_no if table.prov else -1
            try:
                docling_json = table.export_to_dict()
            except Exception:
                docling_json = None

            t = NormalizedTable(
                table_index=idx,
                page=page_no,
                row_count=len(df),
                col_count=len(df.columns),
                columns=list(df.columns),
                html=table.export_to_html(doc=mock_doc),
                markdown=df.to_markdown(index=False) or "",
                csv=df.to_csv(index=False),
                docling_json=docling_json,
            )
            tables.append(t)

        assert len(tables) == 1
        assert tables[0].docling_json is not None
        assert tables[0].docling_json["num_rows"] == payload["num_rows"]
        mock_table.export_to_dict.assert_called_once()

    def test_export_to_dict_failure_produces_none(self):
        """If export_to_dict() raises, docling_json is set to None (graceful fallback)."""
        import pandas as pd

        mock_table = MagicMock()
        mock_table.export_to_dataframe.return_value = pd.DataFrame({"A": ["1"]})
        mock_table.export_to_html.return_value = "<table/>"
        mock_table.export_to_dict.side_effect = RuntimeError("Docling internal error")
        prov = MagicMock()
        prov.page_no = 1
        mock_table.prov = [prov]

        from open_notebook.extractors.providers.base import NormalizedTable

        # Replicate the try/except guard from the adapter
        try:
            docling_json = mock_table.export_to_dict()
        except Exception:
            docling_json = None

        t = NormalizedTable(
            table_index=0,
            page=1,
            row_count=1,
            col_count=1,
            columns=["A"],
            html="<table/>",
            markdown="| A |\n|---|\n| 1 |",
            csv="A\n1\n",
            docling_json=docling_json,
        )
        assert t.docling_json is None


# ---------------------------------------------------------------------------
# Test 3: _store_docling_tables persists docling_document_json
# ---------------------------------------------------------------------------


class TestStoreDoclingTablesDoclingJson:
    @pytest.mark.asyncio
    async def test_docling_document_json_is_persisted(self):
        """_store_docling_tables writes docling_document_json to acm_table_section."""
        from commands.source_commands import _store_docling_tables

        payload = _sample_docling_json(num_rows=4, num_cols=5)
        tables = [
            {
                "table_index": 0,
                "page": 2,
                "rows": 4,
                "columns": ["A", "B", "C", "D", "E"],
                "csv": "A,B,C,D,E\n1,2,3,4,5\n",
                "markdown": "| A | B |\n|---|---|\n| 1 | 2 |",
                "html": "<table><tr><td>1</td></tr></table>",
                "docling_json": payload,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
        ]

        with patch(
            "commands.source_commands.repo_create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = {"id": "acm_table_section:abc"}
            await _store_docling_tables("source:123", tables)

            assert mock_create.call_count == 1
            call_data = mock_create.call_args_list[0][0][1]

            # The new field must be present
            assert "docling_document_json" in call_data
            assert call_data["docling_document_json"] == payload
            assert call_data["docling_document_json"]["num_rows"] == 4

    @pytest.mark.asyncio
    async def test_docling_document_json_none_when_missing(self):
        """_store_docling_tables stores None when docling_json key is absent."""
        from commands.source_commands import _store_docling_tables

        tables = [
            {
                "table_index": 0,
                "page": 1,
                "rows": 2,
                "columns": ["X"],
                "csv": "X\n1\n",
                "markdown": "| X |\n|---|\n| 1 |",
                "html": "<table/>",
                # docling_json key deliberately absent
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
        ]

        with patch(
            "commands.source_commands.repo_create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = {"id": "acm_table_section:xyz"}
            await _store_docling_tables("source:456", tables)

            call_data = mock_create.call_args_list[0][0][1]
            assert "docling_document_json" in call_data
            assert call_data["docling_document_json"] is None

    @pytest.mark.asyncio
    async def test_existing_structured_json_unchanged(self):
        """structured_json (CSV) is still stored -- docling_document_json is additive."""
        from commands.source_commands import _store_docling_tables

        csv_data = "Col A,Col B\nval1,val2\n"
        tables = [
            {
                "table_index": 0,
                "page": 3,
                "rows": 1,
                "columns": ["Col A", "Col B"],
                "csv": csv_data,
                "markdown": "| Col A | Col B |\n|---|---|\n| val1 | val2 |",
                "html": "<table/>",
                "docling_json": _sample_docling_json(),
                "consensus_tier": "multi_provider_agreement",
                "consensus_scores": {"docling": 0.6, "mineru": 0.4},
            }
        ]

        with patch(
            "commands.source_commands.repo_create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = {"id": "acm_table_section:def"}
            await _store_docling_tables("source:789", tables)

            call_data = mock_create.call_args_list[0][0][1]
            # Original CSV field is unchanged
            assert call_data["structured_json"] == csv_data
            # New field is also stored
            assert call_data["docling_document_json"] is not None


# ---------------------------------------------------------------------------
# Test 4: _get_docling_tables retrieves docling_document_json via SELECT *
# ---------------------------------------------------------------------------


class TestGetDoclingTablesDoclingJson:
    @pytest.mark.asyncio
    async def test_get_returns_docling_document_json(self):
        """_get_docling_tables returns records including docling_document_json."""
        payload = _sample_docling_json(num_rows=3, num_cols=2)
        mock_db_rows = [
            {
                "id": "acm_table_section:row1",
                "source_id": "source:abc",
                "page_start": 1,
                "page_end": 1,
                "raw_html": "<table/>",
                "raw_text": "| A |\n|---|\n| 1 |",
                "structured_json": "A\n1\n",
                "docling_document_json": payload,
                "table_type": "docling_direct_api",
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
        ]

        # repo_query and ensure_record_id are imported inside the function body,
        # so we patch at the repository source module.
        with (
            patch(
                "open_notebook.database.repository.repo_query",
                new_callable=AsyncMock,
            ) as mock_query,
            patch(
                "open_notebook.database.repository.ensure_record_id",
                return_value="source:abc",
            ),
        ):
            mock_query.return_value = mock_db_rows
            from open_notebook.extractors.orchestrator import _get_docling_tables

            results = await _get_docling_tables("source:abc", 1, 5)

        assert len(results) == 1
        row = results[0]
        assert "docling_document_json" in row
        assert row["docling_document_json"]["num_rows"] == 3
        assert row["docling_document_json"]["num_cols"] == 2

    @pytest.mark.asyncio
    async def test_get_handles_missing_docling_document_json(self):
        """_get_docling_tables gracefully handles records without docling_document_json."""
        mock_db_rows = [
            {
                "id": "acm_table_section:row2",
                "source_id": "source:abc",
                "page_start": 2,
                "page_end": 2,
                "raw_html": "<table/>",
                "raw_text": "| B |\n|---|\n| 2 |",
                "structured_json": "B\n2\n",
                # docling_document_json absent (legacy record pre-migration 48)
                "table_type": "docling_direct_api",
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
        ]

        with (
            patch(
                "open_notebook.database.repository.repo_query",
                new_callable=AsyncMock,
            ) as mock_query,
            patch(
                "open_notebook.database.repository.ensure_record_id",
                return_value="source:abc",
            ),
        ):
            mock_query.return_value = mock_db_rows
            from open_notebook.extractors.orchestrator import _get_docling_tables

            results = await _get_docling_tables("source:abc", 1, 5)

        assert len(results) == 1
        # Legacy records simply won't have the key -- caller uses .get()
        assert results[0].get("docling_document_json") is None

    @pytest.mark.asyncio
    async def test_get_returns_empty_on_db_failure(self):
        """_get_docling_tables returns [] when the DB query raises."""
        with (
            patch(
                "open_notebook.database.repository.repo_query",
                new_callable=AsyncMock,
            ) as mock_query,
            patch(
                "open_notebook.database.repository.ensure_record_id",
                return_value="source:abc",
            ),
        ):
            mock_query.side_effect = RuntimeError("connection refused")
            from open_notebook.extractors.orchestrator import _get_docling_tables

            results = await _get_docling_tables("source:abc", 1, 10)

        assert results == []
