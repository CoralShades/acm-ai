"""
Tests for job lifecycle API endpoints.

Covers: GET /api/jobs/{source_id}/status
        GET /api/jobs/{source_id}/can-extract
        POST /api/jobs/{source_id}/cancel
        POST /api/jobs/{source_id}/restart
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client (password auth disabled by conftest env var)."""
    from api.main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_NEW_ROW = {
    "id": "command:abc123",
    "app": "open_notebook",
    "name": "acm_extract",
    "args": {"source_id": "source:test1"},
    "status": "new",
    "created": "2026-03-18T10:00:00Z",
    "updated": "2026-03-18T10:00:00Z",
}

_RUNNING_ROW = {**_NEW_ROW, "status": "running"}
_COMPLETED_ROW = {**_NEW_ROW, "status": "completed"}
_FAILED_ROW = {**_NEW_ROW, "status": "failed"}
_CANCELLED_ROW = {**_NEW_ROW, "status": "canceled"}


# ---------------------------------------------------------------------------
# GET /api/jobs/{source_id}/status
# ---------------------------------------------------------------------------


class TestGetJobStatus:
    @patch("api.routers.job_lifecycle.repo_query")
    def test_returns_latest_status(self, mock_query, client):
        """200 with command details when a command exists."""
        mock_query.return_value = [_RUNNING_ROW]

        response = client.get("/api/jobs/source:test1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["command_id"] == "command:abc123"
        assert data["status"] == "running"
        assert data["created_at"] == "2026-03-18T10:00:00Z"
        assert data["updated_at"] == "2026-03-18T10:00:00Z"

    @patch("api.routers.job_lifecycle.repo_query")
    def test_404_when_no_commands_exist(self, mock_query, client):
        """404 when no commands found for source."""
        mock_query.return_value = []

        response = client.get("/api/jobs/source:ghost/status")

        assert response.status_code == 404
        assert "No extraction commands found" in response.json()["detail"]

    @patch("api.routers.job_lifecycle.repo_query")
    def test_returns_terminal_status(self, mock_query, client):
        """200 for completed/failed jobs too."""
        mock_query.return_value = [_COMPLETED_ROW]

        response = client.get("/api/jobs/source:test1/status")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# GET /api/jobs/{source_id}/can-extract
# ---------------------------------------------------------------------------


class TestCanExtract:
    @patch("api.routers.job_lifecycle.repo_query")
    def test_can_extract_when_no_active_commands(self, mock_query, client):
        """can_extract true when no pending/running commands."""
        mock_query.return_value = []

        response = client.get("/api/jobs/source:test1/can-extract")

        assert response.status_code == 200
        data = response.json()
        assert data["can_extract"] is True
        assert "No active extraction" in data["reason"]

    @patch("api.routers.job_lifecycle.repo_query")
    def test_cannot_extract_when_running(self, mock_query, client):
        """can_extract false when a running command exists."""
        mock_query.return_value = [_RUNNING_ROW]

        response = client.get("/api/jobs/source:test1/can-extract")

        assert response.status_code == 200
        data = response.json()
        assert data["can_extract"] is False
        assert "already in progress" in data["reason"]
        assert "command:abc123" in data["reason"]

    @patch("api.routers.job_lifecycle.repo_query")
    def test_cannot_extract_when_new(self, mock_query, client):
        """can_extract false when a 'new' (pending) command exists."""
        mock_query.return_value = [_NEW_ROW]

        response = client.get("/api/jobs/source:test1/can-extract")

        assert response.status_code == 200
        data = response.json()
        assert data["can_extract"] is False


# ---------------------------------------------------------------------------
# POST /api/jobs/{source_id}/cancel
# ---------------------------------------------------------------------------


class TestCancelJob:
    @patch("api.routers.job_lifecycle.get_event_bus")
    @patch("api.routers.job_lifecycle.repo_query")
    def test_cancel_active_command(self, mock_query, mock_bus, client):
        """200 and cancelled=True when an active command is found."""
        # First call (_get_active_command_for_source): returns a running row
        # Second call (UPDATE statement): returns updated row
        mock_query.side_effect = [
            [_RUNNING_ROW],  # active command lookup
            [_CANCELLED_ROW],  # UPDATE result
        ]
        mock_event_bus = MagicMock()
        mock_event_bus.publish = AsyncMock(return_value=0)
        mock_bus.return_value = mock_event_bus

        response = client.post("/api/jobs/source:test1/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is True
        assert data["command_id"] == "command:abc123"

    @patch("api.routers.job_lifecycle.repo_query")
    def test_404_when_no_command_at_all(self, mock_query, client):
        """404 when no command exists for source at all."""
        # active lookup returns nothing, latest lookup also returns nothing
        mock_query.side_effect = [[], []]

        response = client.post("/api/jobs/source:ghost/cancel")

        assert response.status_code == 404

    @patch("api.routers.job_lifecycle.repo_query")
    def test_409_when_command_already_terminal(self, mock_query, client):
        """409 when latest command is already completed/failed/canceled."""
        # active lookup returns nothing (terminal), latest returns completed row
        mock_query.side_effect = [[], [_COMPLETED_ROW]]

        response = client.post("/api/jobs/source:test1/cancel")

        assert response.status_code == 409
        assert "terminal state" in response.json()["detail"]

    @patch("api.routers.job_lifecycle.get_event_bus")
    @patch("api.routers.job_lifecycle.repo_query")
    def test_cancel_emits_event(self, mock_query, mock_bus, client):
        """Cancel emits a job.cancelled event on the PipelineEventBus."""
        mock_query.side_effect = [[_RUNNING_ROW], [_CANCELLED_ROW]]
        mock_event_bus = MagicMock()
        mock_event_bus.publish = AsyncMock(return_value=1)
        mock_bus.return_value = mock_event_bus

        client.post("/api/jobs/source:test1/cancel")

        mock_event_bus.publish.assert_awaited_once()
        published_event = mock_event_bus.publish.call_args[0][0]
        assert published_event.type == "job.cancelled"
        assert published_event.operation_id == "command:abc123"


# ---------------------------------------------------------------------------
# POST /api/jobs/{source_id}/restart
# ---------------------------------------------------------------------------


class TestRestartJob:
    @patch("api.routers.job_lifecycle.CommandService.submit_command_job")
    @patch("api.routers.job_lifecycle.repo_query")
    def test_restart_when_no_active_command(self, mock_query, mock_submit, client):
        """200 and restarted=True when no active command exists."""
        mock_query.return_value = []  # no active command
        mock_submit.return_value = "command:new999"

        with patch.dict("sys.modules", {"commands.acm_commands": MagicMock()}):
            response = client.post("/api/jobs/source:test1/restart")

        assert response.status_code == 200
        data = response.json()
        assert data["restarted"] is True
        assert data["command_id"] == "command:new999"

    @patch("api.routers.job_lifecycle.repo_query")
    def test_409_when_extraction_already_running(self, mock_query, client):
        """409 when an active extraction is already in progress."""
        mock_query.return_value = [_RUNNING_ROW]

        response = client.post("/api/jobs/source:test1/restart")

        assert response.status_code == 409
        assert "already in progress" in response.json()["detail"]

    @patch("api.routers.job_lifecycle.CommandService.submit_command_job")
    @patch("api.routers.job_lifecycle.repo_query")
    def test_restart_passes_source_id_to_command(
        self, mock_query, mock_submit, client
    ):
        """Submitted command receives the correct source_id."""
        mock_query.return_value = []
        mock_submit.return_value = "command:new001"

        with patch.dict("sys.modules", {"commands.acm_commands": MagicMock()}):
            client.post("/api/jobs/source:test1/restart")

        mock_submit.assert_awaited_once_with(
            "open_notebook",
            "acm_extract",
            {"source_id": "source:test1", "force": False},
        )
