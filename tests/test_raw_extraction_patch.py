"""
Tests for PATCH /api/acm/raw-extractions/{source_id}/{extraction_id} (E33-S5).

Covers:
  - Appending officer edits to an existing raw extraction row
  - Overwriting structured_json alongside appending edits
  - 403 when source_id in path does not match the record's source_id
  - 404 when extraction_id does not exist
  - Valid request with empty edits list (structured_json update only)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    from api.main import app

    return TestClient(app)


def _make_mock_extraction(
    extraction_id: str = "raw_extraction:abc123",
    source_id: str = "source:s1",
    officer_edits: list | None = None,
    structured_json: str | None = None,
) -> MagicMock:
    """Build a MagicMock that mimics a RawExtraction domain object."""
    mock = MagicMock()
    mock.id = extraction_id
    mock.source_id = source_id
    mock.provider_id = "docling"
    mock.extraction_backend = "docling:2.x"
    mock.page_number = 1
    mock.raw_html = None
    mock.raw_markdown = None
    mock.structured_json = structured_json
    mock.bbox = None
    mock.confidence = None
    mock.officer_edits = officer_edits if officer_edits is not None else []
    mock.created_at = None
    mock.save = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


class TestPatchRawExtraction:
    """Tests for PATCH /api/acm/raw-extractions/{source_id}/{extraction_id}."""

    @patch("api.routers.acm.RawExtraction.get", new_callable=AsyncMock)
    def test_patch_raw_extraction_appends_edits(self, mock_get, client):
        """PATCH with valid body appends to officer_edits and returns 200."""
        mock_extraction = _make_mock_extraction(
            extraction_id="raw_extraction:abc123",
            source_id="source:s1",
            officer_edits=[],
        )
        mock_get.return_value = mock_extraction

        response = client.patch(
            "/api/acm/raw-extractions/s1/raw_extraction:abc123",
            json={
                "edits": [
                    {
                        "field": "Location",
                        "old_value": "Room A",
                        "new_value": "Room B",
                        "user": "officer@example.com",
                        "timestamp": "2026-03-05T12:00:00Z",
                    }
                ]
            },
        )

        assert response.status_code == 200
        mock_extraction.save.assert_awaited_once()

        data = response.json()
        assert len(data["officer_edits"]) == 1
        assert data["officer_edits"][0]["field"] == "Location"
        assert data["officer_edits"][0]["new_value"] == "Room B"

    @patch("api.routers.acm.RawExtraction.get", new_callable=AsyncMock)
    def test_patch_raw_extraction_updates_structured_json(self, mock_get, client):
        """PATCH with structured_json overwrites it; edits are still appended."""
        original_json = '{"headers": ["A"], "rows": [["old"]]}'
        updated_json = '{"headers": ["A"], "rows": [["new"]]}'

        mock_extraction = _make_mock_extraction(
            extraction_id="raw_extraction:abc123",
            source_id="source:s1",
            officer_edits=[],
            structured_json=original_json,
        )
        mock_get.return_value = mock_extraction

        response = client.patch(
            "/api/acm/raw-extractions/s1/raw_extraction:abc123",
            json={
                "structured_json": updated_json,
                "edits": [
                    {
                        "field": "A",
                        "old_value": "old",
                        "new_value": "new",
                        "user": "officer@example.com",
                        "timestamp": "2026-03-05T12:00:00Z",
                    }
                ],
            },
        )

        assert response.status_code == 200
        mock_extraction.save.assert_awaited_once()

        data = response.json()
        assert data["structured_json"] == updated_json
        assert len(data["officer_edits"]) == 1
        assert data["officer_edits"][0]["old_value"] == "old"

    @patch("api.routers.acm.RawExtraction.get", new_callable=AsyncMock)
    def test_patch_raw_extraction_source_mismatch_returns_403(self, mock_get, client):
        """403 when source_id in path does not match the record's source_id."""
        # Record belongs to source:different, but path says source:s1
        mock_extraction = _make_mock_extraction(
            extraction_id="raw_extraction:abc123",
            source_id="source:different",
        )
        mock_get.return_value = mock_extraction

        response = client.patch(
            "/api/acm/raw-extractions/s1/raw_extraction:abc123",
            json={"edits": []},
        )

        assert response.status_code == 403
        assert "source_id mismatch" in response.json()["detail"]
        mock_extraction.save.assert_not_awaited()

    @patch("api.routers.acm.RawExtraction.get", new_callable=AsyncMock)
    def test_patch_raw_extraction_not_found_returns_404(self, mock_get, client):
        """404 when extraction_id does not exist."""
        from open_notebook.exceptions import NotFoundError

        mock_get.side_effect = NotFoundError("raw_extraction:nonexistent not found")

        response = client.patch(
            "/api/acm/raw-extractions/s1/raw_extraction:nonexistent",
            json={"edits": []},
        )

        assert response.status_code == 404
        assert "Raw extraction not found" in response.json()["detail"]

    @patch("api.routers.acm.RawExtraction.get", new_callable=AsyncMock)
    def test_patch_raw_extraction_empty_edits_valid(self, mock_get, client):
        """Empty edits list with structured_json update is valid and returns 200."""
        original_json = '{"headers": ["Col"], "rows": [["value"]]}'
        new_json = '{"headers": ["Col"], "rows": [["corrected"]]}'

        mock_extraction = _make_mock_extraction(
            extraction_id="raw_extraction:abc123",
            source_id="source:s1",
            officer_edits=[],
            structured_json=original_json,
        )
        mock_get.return_value = mock_extraction

        response = client.patch(
            "/api/acm/raw-extractions/s1/raw_extraction:abc123",
            json={
                "structured_json": new_json,
                "edits": [],
            },
        )

        assert response.status_code == 200
        mock_extraction.save.assert_awaited_once()

        data = response.json()
        assert data["structured_json"] == new_json
        # No edits were appended
        assert data["officer_edits"] == []
