"""
Tests for E31-S4: Raw Extraction Table + Storage.

Covers:
  - RawExtraction domain model validation
  - Repository query methods (mocked)
  - GET /api/acm/raw-extractions/{source_id} endpoint (mocked)
  - ACMTableSection consensus fields
  - _store_raw_extractions() wiring in source_commands
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Domain Model Tests
# ---------------------------------------------------------------------------


class TestRawExtractionModel:
    """Unit tests for the RawExtraction domain model."""

    def test_raw_extraction_validate_source_id_adds_prefix(self):
        """source_id without prefix gets 'source:' prepended."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="abc123",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=1,
        )
        assert r.source_id == "source:abc123"

    def test_raw_extraction_validate_source_id_accepts_prefixed(self):
        """source_id already prefixed is not double-prefixed."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="source:abc123",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=1,
        )
        assert r.source_id == "source:abc123"

    def test_raw_extraction_validate_source_id_required(self):
        """Empty source_id raises ValidationError."""
        from open_notebook.domain.acm import RawExtraction

        with pytest.raises((ValidationError, Exception)):
            RawExtraction(
                source_id="",
                provider_id="docling",
                extraction_backend="docling:2.x",
                page_number=1,
            )

    def test_raw_extraction_empty_provider_id_raises(self):
        """Empty provider_id raises ValidationError or InvalidInputError."""
        from open_notebook.domain.acm import RawExtraction

        with pytest.raises((ValidationError, Exception)):
            RawExtraction(
                source_id="source:abc",
                provider_id="",
                extraction_backend="docling:2.x",
                page_number=1,
            )

    def test_raw_extraction_page_number_minus_one_allowed(self):
        """page_number=-1 (unknown page) is valid."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="source:abc",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=-1,
        )
        assert r.page_number == -1

    def test_raw_extraction_page_number_invalid(self):
        """page_number < -1 raises an error (ValidationError or InvalidInputError)."""
        from open_notebook.domain.acm import RawExtraction

        with pytest.raises((ValidationError, Exception)):
            RawExtraction(
                source_id="source:abc",
                provider_id="docling",
                extraction_backend="docling:2.x",
                page_number=-2,
            )

    def test_raw_extraction_officer_edits_defaults_to_empty_list(self):
        """officer_edits defaults to []."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="source:abc",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=1,
        )
        assert r.officer_edits == []

    def test_raw_extraction_bbox_is_optional(self):
        """bbox defaults to None when not provided."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="source:abc",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=1,
        )
        assert r.bbox is None

    def test_raw_extraction_provider_id_whitespace_stripped(self):
        """provider_id with surrounding whitespace is stripped."""
        from open_notebook.domain.acm import RawExtraction

        r = RawExtraction(
            source_id="source:abc",
            provider_id="  docling  ",
            extraction_backend="docling:2.x",
            page_number=1,
        )
        assert r.provider_id == "docling"

    def test_raw_extraction_table_name(self):
        """table_name class variable is 'raw_extraction'."""
        from open_notebook.domain.acm import RawExtraction

        assert RawExtraction.table_name == "raw_extraction"


# ---------------------------------------------------------------------------
# Repository Query Tests
# ---------------------------------------------------------------------------


class TestRawExtractionRepository:
    """Tests for RawExtraction class methods that query the database."""

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_calls_correct_query(self, mock_query):
        """get_by_source issues SELECT with source_id condition."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = [
            {
                "id": "raw_extraction:001",
                "source_id": "source:abc",
                "provider_id": "docling",
                "extraction_backend": "docling:2.x",
                "page_number": 1,
                "officer_edits": [],
            }
        ]
        results = await RawExtraction.get_by_source("source:abc")
        assert len(results) == 1
        assert results[0].provider_id == "docling"
        mock_query.assert_called_once()
        call_args = mock_query.call_args[0][0]
        assert "source_id = $source_id" in call_args

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_with_provider_filter(self, mock_query):
        """get_by_source with provider= adds provider_id condition and param."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = []
        await RawExtraction.get_by_source("source:abc", provider="mineru")
        call_args = mock_query.call_args[0][0]
        assert "provider_id = $provider_id" in call_args
        params = mock_query.call_args[0][1]
        assert params["provider_id"] == "mineru"

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_with_page_filter(self, mock_query):
        """get_by_source with page_number= adds page_number condition."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = []
        await RawExtraction.get_by_source("source:abc", page_number=3)
        call_args = mock_query.call_args[0][0]
        assert "page_number = $page_number" in call_args

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_delete_by_source_returns_count(self, mock_query):
        """delete_by_source returns count of deleted rows."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = [
            {"id": "raw_extraction:1"},
            {"id": "raw_extraction:2"},
        ]
        count = await RawExtraction.delete_by_source("source:abc")
        assert count == 2

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_delete_by_source_empty_returns_zero(self, mock_query):
        """delete_by_source returns 0 when DB returns None."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = None
        count = await RawExtraction.delete_by_source("source:abc")
        assert count == 0

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_no_provider_no_page_filter(self, mock_query):
        """get_by_source with no filters only passes source_id param (no provider/page params)."""
        from open_notebook.domain.acm import RawExtraction

        mock_query.return_value = []
        await RawExtraction.get_by_source("source:abc")
        # The SQL query contains 'provider_id' in ORDER BY clause, so check params instead
        params = mock_query.call_args[0][1]
        assert "provider_id" not in params
        assert "page_number" not in params
        assert "source_id" in params


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create test client."""
    from api.main import app

    return TestClient(app)


def TestClient(app):
    """Import TestClient lazily to avoid import errors at collection time."""
    from fastapi.testclient import TestClient as _TestClient

    return _TestClient(app)


class TestRawExtractionsEndpoint:
    """Tests for GET /api/acm/raw-extractions/{source_id}."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    @patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
    def test_list_raw_extractions_success(self, mock_get, client):
        """Returns 200 with extractions list and total."""
        from open_notebook.domain.acm import RawExtraction

        mock_record = RawExtraction(
            id="raw_extraction:001",
            source_id="source:abc",
            provider_id="docling",
            extraction_backend="docling:2.x",
            page_number=2,
            raw_html="<table></table>",
            raw_markdown="| a |",
            officer_edits=[],
        )
        mock_get.return_value = [mock_record]

        response = client.get("/api/acm/raw-extractions/source:abc")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["source_id"] == "source:abc"
        assert data["extractions"][0]["provider_id"] == "docling"

    @patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
    def test_list_raw_extractions_provider_filter_passed_through(self, mock_get, client):
        """provider query param is forwarded to get_by_source."""
        mock_get.return_value = []
        response = client.get("/api/acm/raw-extractions/source:abc?provider=mineru")
        assert response.status_code == 200
        mock_get.assert_called_once_with("source:abc", provider="mineru", page_number=None)

    @patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
    def test_list_raw_extractions_empty_source(self, mock_get, client):
        """Returns 200 with empty list when no extractions exist."""
        mock_get.return_value = []
        response = client.get("/api/acm/raw-extractions/source:xyz")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["extractions"] == []

    @patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
    def test_list_raw_extractions_db_error_returns_500(self, mock_get, client):
        """DB error results in 500 response."""
        mock_get.side_effect = Exception("DB connection failed")
        response = client.get("/api/acm/raw-extractions/source:abc")
        assert response.status_code == 500

    @patch("api.routers.acm.RawExtraction.get_by_source", new_callable=AsyncMock)
    def test_list_raw_extractions_page_number_filter(self, mock_get, client):
        """page_number query param is forwarded to get_by_source."""
        mock_get.return_value = []
        response = client.get("/api/acm/raw-extractions/source:abc?page_number=3")
        assert response.status_code == 200
        mock_get.assert_called_once_with("source:abc", provider=None, page_number=3)


# ---------------------------------------------------------------------------
# ACMTableSection Consensus Field Tests
# ---------------------------------------------------------------------------


class TestACMTableSectionConsensus:
    """Tests for consensus_tier and consensus_scores fields added to ACMTableSection."""

    def test_acm_table_section_accepts_consensus_tier(self):
        """ACMTableSection accepts consensus_tier field."""
        from open_notebook.domain.acm import ACMTableSection

        section = ACMTableSection(
            source_id="source:abc",
            page_start=1,
            page_end=2,
            consensus_tier="single_provider",
        )
        assert section.consensus_tier == "single_provider"

    def test_acm_table_section_consensus_fields_default_none(self):
        """consensus_tier and consensus_scores default to None."""
        from open_notebook.domain.acm import ACMTableSection

        section = ACMTableSection(
            source_id="source:abc",
            page_start=1,
            page_end=2,
        )
        assert section.consensus_tier is None
        assert section.consensus_scores is None

    def test_acm_table_section_accepts_consensus_scores_dict(self):
        """ACMTableSection accepts consensus_scores as a dict."""
        from open_notebook.domain.acm import ACMTableSection

        scores = {"docling": 0.95, "mineru": 0.88, "agreement": 0.92}
        section = ACMTableSection(
            source_id="source:abc",
            page_start=1,
            page_end=2,
            consensus_scores=scores,
        )
        assert section.consensus_scores == scores

    def test_acm_table_section_all_consensus_tiers_accepted(self):
        """All valid consensus tier strings are accepted (no enum restriction)."""
        from open_notebook.domain.acm import ACMTableSection

        tiers = [
            "single_provider",
            "multi_provider_agreement",
            "multi_provider_conflict",
            "manual_override",
        ]
        for tier in tiers:
            section = ACMTableSection(
                source_id="source:abc",
                page_start=1,
                page_end=2,
                consensus_tier=tier,
            )
            assert section.consensus_tier == tier


# ---------------------------------------------------------------------------
# Source Commands Wiring Tests
# ---------------------------------------------------------------------------


class TestStoreRawExtractions:
    """Tests for _store_raw_extractions() helper in source_commands."""

    @pytest.mark.asyncio
    @patch("commands.source_commands.RawExtraction")
    async def test_store_raw_extractions_saves_one_per_table(self, mock_cls):
        """_store_raw_extractions creates one RawExtraction per table."""
        from commands.source_commands import _store_raw_extractions
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
        )

        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        result = NormalizedExtractionResult(
            provider_id="docling",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=1,
                    row_count=5,
                    col_count=3,
                    columns=["A", "B", "C"],
                    html="<table/>",
                    markdown="",
                ),
                NormalizedTable(
                    table_index=1,
                    page=2,
                    row_count=3,
                    col_count=3,
                    columns=["A", "B", "C"],
                    html="<table/>",
                    markdown="",
                ),
            ],
        )

        count = await _store_raw_extractions("source:abc", result)
        assert count == 2
        assert mock_instance.save.call_count == 2

    @pytest.mark.asyncio
    @patch("commands.source_commands.RawExtraction")
    async def test_store_raw_extractions_empty_tables_returns_zero(self, mock_cls):
        """_store_raw_extractions returns 0 when there are no tables."""
        from commands.source_commands import _store_raw_extractions
        from open_notebook.extractors.providers.base import NormalizedExtractionResult

        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        result = NormalizedExtractionResult(
            provider_id="docling",
            tables=[],
        )

        count = await _store_raw_extractions("source:abc", result)
        assert count == 0
        assert mock_instance.save.call_count == 0

    @pytest.mark.asyncio
    @patch("commands.source_commands.RawExtraction")
    async def test_store_raw_extractions_backend_label_format(self, mock_cls):
        """extraction_backend is set to '{provider_id}:2.x'."""
        from commands.source_commands import _store_raw_extractions
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
        )

        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        result = NormalizedExtractionResult(
            provider_id="mineru",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=1,
                    row_count=2,
                    col_count=2,
                    columns=["X", "Y"],
                    html="<table/>",
                    markdown="",
                ),
            ],
        )

        await _store_raw_extractions("source:abc", result)

        # Verify extraction_backend passed to constructor
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["extraction_backend"] == "mineru:2.x"

    @pytest.mark.asyncio
    @patch("commands.source_commands.RawExtraction")
    async def test_store_raw_extractions_bbox_none_when_table_bbox_none(self, mock_cls):
        """bbox_dict is None when table.bbox is None."""
        from commands.source_commands import _store_raw_extractions
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
        )

        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        result = NormalizedExtractionResult(
            provider_id="docling",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=1,
                    row_count=2,
                    col_count=2,
                    columns=["X", "Y"],
                    html="<table/>",
                    markdown="",
                    bbox=None,
                ),
            ],
        )

        await _store_raw_extractions("source:abc", result)
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["bbox"] is None

    @pytest.mark.asyncio
    @patch("commands.source_commands.RawExtraction")
    async def test_store_raw_extractions_bbox_dict_when_table_has_bbox(self, mock_cls):
        """bbox_dict is populated from TableBBox when available."""
        from commands.source_commands import _store_raw_extractions
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
            TableBBox,
        )

        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        result = NormalizedExtractionResult(
            provider_id="docling",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=3,
                    row_count=2,
                    col_count=2,
                    columns=["X", "Y"],
                    html="<table/>",
                    markdown="",
                    bbox=TableBBox(x=10.0, y=20.0, width=100.0, height=50.0, page=3),
                ),
            ],
        )

        await _store_raw_extractions("source:abc", result)
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["bbox"] == {
            "x": 10.0,
            "y": 20.0,
            "width": 100.0,
            "height": 50.0,
            "page": 3,
        }
