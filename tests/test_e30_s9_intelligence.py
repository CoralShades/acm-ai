"""
Tests for E30-S9: Persist Pre-Extraction Intelligence.

Covers:
- AC2: save_source_intelligence() upserts all 4 pre-extraction models
- AC3: get_source_intelligence() returns data or None
- AC4: save_intelligence_node is non-blocking (catches all exceptions)
- AC5: GET /api/acm/source-intelligence/{source_id} returns 200 or 404
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """FastAPI test client (password auth disabled by conftest)."""
    from api.main import app

    return TestClient(app)


def _make_mock_source(source_id: str = "source:test_intel_123") -> MagicMock:
    source = MagicMock()
    source.id = source_id
    return source


def _sample_intelligence_payload() -> dict:
    """Minimal intelligence payload covering all 4 models."""
    return {
        "document_meta": {
            "consultant_name": "Test Assessor Pty Ltd",
            "site_name": "Test School",
            "report_date": "2025-01-15",
        },
        "document_structure": {
            "document_type": "SAMP",
            "toc_present": False,
            "total_pages": 10,
            "register_start_page": 5,
            "building_ids": ["A1"],
            "sections": [],
        },
        "building_inventory": {
            "buildings": [
                {
                    "building_id": "A1",
                    "name": "Admin",
                    "page_start": 5,
                    "complexity": "simple",
                    "rooms": [],
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
            "document_type": "SAMP",
        },
        "page_tags": {
            "pages": [
                {
                    "page_number": 5,
                    "section_id": 4,
                    "section_title": "Register",
                    "confidence": 0.95,
                    "page_type": "content",
                }
            ],
            "total_pages": 10,
            "register_page_range": [5, 10],
        },
        "total_pages": 10,
        "total_buildings": 1,
        "document_type": "SAMP",
        "register_page_range": {"start": 5, "end": 10},
    }


# ---------------------------------------------------------------------------
# AC2: save_source_intelligence() upserts all 4 models
# ---------------------------------------------------------------------------


class TestSaveSourceIntelligence:
    """AC2: save_source_intelligence() upserts all 4 pre-extraction models."""

    @pytest.mark.asyncio
    async def test_upserts_all_four_models(self):
        """Calling save_source_intelligence issues a UPSERT query with all 4 model keys."""
        payload = _sample_intelligence_payload()
        captured_queries = []

        async def fake_repo_query(query_str, vars=None):
            captured_queries.append((query_str, vars))
            return [{"id": "source_intelligence:1", "source_id": "source:test_intel_123"}]

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import save_source_intelligence

            result = await save_source_intelligence("source:test_intel_123", payload)

        assert len(captured_queries) == 1
        query_str, vars_dict = captured_queries[0]
        assert "UPSERT source_intelligence" in query_str
        assert "document_meta" in query_str
        assert "document_structure" in query_str
        assert "building_inventory" in query_str
        assert "page_tags" in query_str
        # Confirm data dict passed with all 4 model keys present
        assert vars_dict is not None
        data = vars_dict["data"]
        assert "document_meta" in data
        assert "document_structure" in data
        assert "building_inventory" in data
        assert "page_tags" in data

    @pytest.mark.asyncio
    async def test_upsert_uses_where_source_id(self):
        """UPSERT query must use WHERE source_id to enforce unique constraint."""
        captured_queries = []

        async def fake_repo_query(query_str, vars=None):
            captured_queries.append(query_str)
            return []

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import save_source_intelligence

            await save_source_intelligence("source:test_intel_abc", {"document_meta": None})

        assert len(captured_queries) == 1
        assert "WHERE source_id" in captured_queries[0]

    @pytest.mark.asyncio
    async def test_upsert_includes_denormalized_summary_fields(self):
        """Denormalized total_pages, total_buildings, document_type, register_page_range are set."""
        payload = _sample_intelligence_payload()
        captured_vars = {}

        async def fake_repo_query(query_str, vars=None):
            captured_vars.update(vars or {})
            return []

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import save_source_intelligence

            await save_source_intelligence("source:test_intel_123", payload)

        data = captured_vars["data"]
        assert data.get("total_pages") == 10
        assert data.get("total_buildings") == 1
        assert data.get("document_type") == "SAMP"
        assert data.get("register_page_range") == {"start": 5, "end": 10}


# ---------------------------------------------------------------------------
# AC3: get_source_intelligence() returns data or None
# ---------------------------------------------------------------------------


class TestGetSourceIntelligence:
    """AC3: get_source_intelligence() returns persisted data or None."""

    @pytest.mark.asyncio
    async def test_returns_record_when_found(self):
        """Returns the first matching row when source_intelligence exists."""
        expected_row = {
            "id": "source_intelligence:1",
            "source_id": "source:test_intel_123",
            "document_meta": {"consultant_name": "Test Assessor"},
            "total_pages": 10,
        }

        async def fake_repo_query(query_str, vars=None):
            # repo_query returns a list-of-lists for SELECT queries in SurrealDB SDK
            return [[expected_row]]

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import get_source_intelligence

            result = await get_source_intelligence("source:test_intel_123")

        assert result is not None
        assert result["source_id"] == "source:test_intel_123"
        assert result["total_pages"] == 10

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Returns None when no record exists for the source_id."""

        async def fake_repo_query(query_str, vars=None):
            return [[]]  # Empty inner list = no rows

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import get_source_intelligence

            result = await get_source_intelligence("source:nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_filters_by_source_id(self):
        """SELECT query must filter on source_id."""
        captured_queries = []

        async def fake_repo_query(query_str, vars=None):
            captured_queries.append((query_str, vars))
            return [[]]

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import get_source_intelligence

            await get_source_intelligence("source:test_intel_filter")

        assert len(captured_queries) == 1
        query_str, vars_dict = captured_queries[0]
        assert "source_intelligence" in query_str
        assert "WHERE source_id" in query_str
        assert vars_dict is not None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_outer_list(self):
        """Returns None when repo_query returns empty outer list."""

        async def fake_repo_query(query_str, vars=None):
            return []

        with patch(
            "open_notebook.database.repository.repo_query",
            side_effect=fake_repo_query,
        ):
            from open_notebook.database.repository import get_source_intelligence

            result = await get_source_intelligence("source:empty")

        assert result is None


# ---------------------------------------------------------------------------
# AC4: save_intelligence_node is non-blocking (catches all exceptions)
# ---------------------------------------------------------------------------


class TestSaveIntelligenceNode:
    """AC4: save_intelligence graph node runs between tag_pages and orchestrate,
    and is non-blocking (catches all exceptions so the pipeline continues).
    """

    @pytest.mark.asyncio
    async def test_node_returns_empty_dict(self):
        """save_intelligence_node returns {} so it doesn't mutate graph state."""
        source = _make_mock_source()
        state = {
            "source": source,
            "document_metadata": None,
            "document_structure": None,
            "building_inventory": None,
            "page_tags": None,
            "agui_emitter": None,
            "pipeline_logger": None,
        }

        with patch(
            "open_notebook.graphs.acm_extraction.save_source_intelligence",
            new_callable=AsyncMock,
            return_value=[],
        ):
            from open_notebook.graphs.acm_extraction import save_intelligence_node

            result = await save_intelligence_node(state, {})

        assert result == {}

    @pytest.mark.asyncio
    async def test_node_is_non_blocking_on_db_failure(self):
        """save_intelligence_node does NOT raise even if DB call throws an exception."""
        source = _make_mock_source()
        state = {
            "source": source,
            "document_metadata": None,
            "document_structure": None,
            "building_inventory": None,
            "page_tags": None,
            "agui_emitter": None,
            "pipeline_logger": None,
        }

        async def always_raise(*args, **kwargs):
            raise RuntimeError("DB connection refused")

        with patch(
            "open_notebook.graphs.acm_extraction.save_source_intelligence",
            side_effect=always_raise,
        ):
            from open_notebook.graphs.acm_extraction import save_intelligence_node

            # Must not raise — the node is non-blocking
            result = await save_intelligence_node(state, {})

        assert result == {}

    @pytest.mark.asyncio
    async def test_node_calls_save_with_source_id(self):
        """save_intelligence_node passes the source's string ID to save_source_intelligence."""
        source = _make_mock_source("source:test_call_123")
        state = {
            "source": source,
            "document_metadata": None,
            "document_structure": None,
            "building_inventory": None,
            "page_tags": None,
            "agui_emitter": None,
            "pipeline_logger": None,
        }
        save_mock = AsyncMock(return_value=[])

        with patch(
            "open_notebook.graphs.acm_extraction.save_source_intelligence",
            new_callable=AsyncMock,
            side_effect=save_mock,
        ):
            from open_notebook.graphs.acm_extraction import save_intelligence_node

            await save_intelligence_node(state, {})

        save_mock.assert_called_once()
        call_args = save_mock.call_args
        assert call_args[0][0] == "source:test_call_123"

    def test_node_is_registered_in_graph(self):
        """save_intelligence node must be registered in the compiled LangGraph."""
        from open_notebook.graphs.acm_extraction import agent_state

        assert "save_intelligence" in agent_state.nodes

    def test_node_positioned_between_tag_pages_and_orchestrate(self):
        """Graph edges: tag_pages -> save_intelligence -> orchestrate (AC4)."""
        from open_notebook.graphs.acm_extraction import agent_state

        edges = agent_state.edges
        assert ("tag_pages", "save_intelligence") in edges or any(
            e == ("tag_pages", "save_intelligence") for e in edges
        ), "tag_pages must connect to save_intelligence"
        assert ("save_intelligence", "orchestrate") in edges or any(
            e == ("save_intelligence", "orchestrate") for e in edges
        ), "save_intelligence must connect to orchestrate"


# ---------------------------------------------------------------------------
# AC5: GET /api/acm/source-intelligence/{source_id} returns 200 or 404
# ---------------------------------------------------------------------------


class TestSourceIntelligenceEndpoint:
    """AC5: GET /api/acm/source-intelligence/{source_id} returns 200 with data or 404."""

    @patch("api.routers.acm.get_source_intelligence")
    def test_returns_200_with_data(self, mock_get, client):
        """Returns 200 with SourceIntelligenceResponse when data exists."""
        mock_get.return_value = {
            "id": "source_intelligence:1",
            "source_id": "source:abc123",
            "document_meta": {"consultant_name": "Test Assessor Pty Ltd"},
            "document_structure": None,
            "building_inventory": None,
            "page_tags": None,
            "total_pages": 10,
            "total_buildings": 2,
            "document_type": "SAMP",
            "register_page_range": {"start": 5, "end": 10},
            "created_at": "2025-01-15T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z",
        }

        response = client.get("/api/acm/source-intelligence/source:abc123")

        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "source:abc123"
        assert data["total_pages"] == 10
        assert data["document_type"] == "SAMP"

    @patch("api.routers.acm.get_source_intelligence")
    def test_returns_404_when_no_data(self, mock_get, client):
        """Returns 404 when no intelligence data exists for the source."""
        mock_get.return_value = None

        response = client.get("/api/acm/source-intelligence/source:nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @patch("api.routers.acm.get_source_intelligence")
    def test_response_includes_all_four_model_fields(self, mock_get, client):
        """Response body contains all 4 pre-extraction model fields."""
        mock_get.return_value = {
            "id": "source_intelligence:2",
            "source_id": "source:full123",
            "document_meta": {"consultant_name": "Assessor Co"},
            "document_structure": {"document_type": "SAMP", "total_pages": 20},
            "building_inventory": {"buildings": [], "total_buildings": 0},
            "page_tags": {"pages": [], "total_pages": 20},
            "total_pages": 20,
            "total_buildings": 0,
            "document_type": "SAMP",
            "register_page_range": None,
            "created_at": None,
            "updated_at": None,
        }

        response = client.get("/api/acm/source-intelligence/source:full123")

        assert response.status_code == 200
        data = response.json()
        assert "document_meta" in data
        assert "document_structure" in data
        assert "building_inventory" in data
        assert "page_tags" in data

    @patch("api.routers.acm.get_source_intelligence")
    def test_source_id_with_colon_is_accepted(self, mock_get, client):
        """source_id containing colons (SurrealDB format) is accepted via :path param."""
        mock_get.return_value = {
            "id": "source_intelligence:3",
            "source_id": "source:test:colon:123",
            "document_meta": None,
            "document_structure": None,
            "building_inventory": None,
            "page_tags": None,
            "total_pages": None,
            "total_buildings": None,
            "document_type": None,
            "register_page_range": None,
            "created_at": None,
            "updated_at": None,
        }

        response = client.get("/api/acm/source-intelligence/source:test:colon:123")

        assert response.status_code == 200
