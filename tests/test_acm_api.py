"""
Tests for ACM API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client after environment variables have been cleared by conftest."""
    from api.main import app

    return TestClient(app)


class TestListACMRecords:
    """Test suite for GET /api/acm/records endpoint."""

    @patch("api.routers.acm.repo_query")
    def test_list_records_success(self, mock_repo_query, client):
        """Test listing ACM records with required source_id."""
        # Mock count query result
        mock_repo_query.side_effect = [
            [{"total": 2}],  # Count query
            [  # Data query
                {
                    "id": "acm_record:123",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B001",
                    "product": "Ceiling Tiles",
                    "material_description": "Asbestos ceiling tiles",
                    "result": "Detected",
                    "created": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-01T00:00:00Z",
                },
                {
                    "id": "acm_record:456",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B002",
                    "product": "Floor Tiles",
                    "material_description": "Vinyl floor tiles",
                    "result": "Not Detected",
                    "created": "2024-01-02T00:00:00Z",
                    "updated": "2024-01-02T00:00:00Z",
                },
            ],
        ]

        response = client.get("/api/acm/records?source_id=source:abc")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["records"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 100

    def test_list_records_missing_source_id(self, client):
        """Test that source_id is required."""
        response = client.get("/api/acm/records")

        assert response.status_code == 422  # Validation error

    @patch("api.routers.acm.repo_query")
    def test_list_records_with_filters(self, mock_repo_query, client):
        """Test listing ACM records with optional filters."""
        mock_repo_query.side_effect = [
            [{"total": 1}],  # Count query
            [  # Data query
                {
                    "id": "acm_record:123",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B001",
                    "risk_status": "High",
                    "product": "Ceiling Tiles",
                    "material_description": "Asbestos ceiling tiles",
                    "result": "Detected",
                },
            ],
        ]

        response = client.get(
            "/api/acm/records?source_id=source:abc&building_id=B001&risk_status=High"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("api.routers.acm.repo_query")
    def test_list_records_pagination(self, mock_repo_query, client):
        """Test pagination parameters."""
        mock_repo_query.side_effect = [
            [{"total": 50}],  # Count query
            [],  # Data query (page 2)
        ]

        response = client.get("/api/acm/records?source_id=source:abc&page=2&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 10
        assert data["pages"] == 5


class TestGetACMRecord:
    """Test suite for GET /api/acm/records/{record_id} endpoint."""

    @patch("api.routers.acm.ACMRecord.get", new_callable=AsyncMock)
    def test_get_record_success(self, mock_get, client):
        """Test getting a single ACM record."""
        mock_record = MagicMock()
        mock_record.id = "acm_record:123"
        mock_record.source_id = "source:abc"
        mock_record.school_name = "Test School"
        mock_record.school_code = None
        mock_record.building_id = "B001"
        mock_record.building_name = "Main Building"
        mock_record.building_year = 1970
        mock_record.building_construction = "Brick"
        mock_record.room_id = "R101"
        mock_record.room_name = "Classroom"
        mock_record.room_area = 100.0
        mock_record.area_type = "Interior"
        mock_record.product = "Ceiling Tiles"
        mock_record.material_description = "Asbestos ceiling tiles"
        mock_record.extent = "100%"
        mock_record.location = "Ceiling"
        mock_record.friable = "Non Friable"
        mock_record.material_condition = "Good"
        mock_record.risk_status = "Low"
        mock_record.result = "Detected"
        mock_record.page_number = 5
        mock_record.extraction_confidence = 0.95
        mock_record.created = "2024-01-01T00:00:00Z"
        mock_record.updated = "2024-01-01T00:00:00Z"

        mock_get.return_value = mock_record

        response = client.get("/api/acm/records/acm_record:123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "acm_record:123"
        assert data["school_name"] == "Test School"
        assert data["building_id"] == "B001"

    @patch("api.routers.acm.ACMRecord.get", new_callable=AsyncMock)
    def test_get_record_not_found(self, mock_get, client):
        """Test 404 when record not found."""
        mock_get.return_value = None

        response = client.get("/api/acm/records/acm_record:nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestTriggerACMExtraction:
    """Test suite for POST /api/acm/extract endpoint."""

    @patch("api.routers.acm.CommandService.submit_command_job", new_callable=AsyncMock)
    def test_trigger_extraction_success(self, mock_submit, client):
        """Test triggering ACM extraction."""
        mock_submit.return_value = "command:12345"

        response = client.post(
            "/api/acm/extract", json={"source_id": "source:abc"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["command_id"] == "command:12345"
        assert data["status"] == "submitted"
        assert "source:abc" in data["message"]

    def test_trigger_extraction_missing_source_id(self, client):
        """Test validation error when source_id is missing."""
        response = client.post("/api/acm/extract", json={})

        assert response.status_code == 422


class TestExportACMRecords:
    """Test suite for GET /api/acm/export endpoint."""

    @patch("open_notebook.domain.notebook.Source.get", new_callable=AsyncMock)
    @patch("api.routers.acm.ACMRecord.get_by_source", new_callable=AsyncMock)
    def test_export_records_success(self, mock_get_records, mock_get_source, client):
        """Test exporting ACM records as CSV."""
        # Mock source
        mock_source = MagicMock()
        mock_source.title = "Test Source"
        mock_get_source.return_value = mock_source

        # Mock records
        mock_record = MagicMock()
        mock_record.building_id = "B001"
        mock_record.building_name = "Main Building"
        mock_record.room_id = "R101"
        mock_record.room_name = "Classroom"
        mock_record.product = "Ceiling Tiles"
        mock_record.material_description = "Asbestos ceiling tiles"
        mock_record.extent = "100%"
        mock_record.location = "Ceiling"
        mock_record.friable = "Non Friable"
        mock_record.material_condition = "Good"
        mock_record.risk_status = "Low"
        mock_record.result = "Detected"
        mock_record.page_number = 5

        mock_get_records.return_value = [mock_record]

        response = client.get("/api/acm/export?source_id=source:abc")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "Test_Source" in response.headers["content-disposition"]

        # Verify CSV content
        content = response.text
        assert "Building ID" in content
        assert "B001" in content
        assert "Ceiling Tiles" in content

    @patch("api.routers.acm.ACMRecord.get_by_source", new_callable=AsyncMock)
    def test_export_records_not_found(self, mock_get_records, client):
        """Test 404 when no records found for source."""
        mock_get_records.return_value = []

        response = client.get("/api/acm/export?source_id=source:nonexistent")

        assert response.status_code == 404

    def test_export_records_missing_source_id(self, client):
        """Test validation error when source_id is missing."""
        response = client.get("/api/acm/export")

        assert response.status_code == 422


class TestGetACMStats:
    """Test suite for GET /api/acm/stats endpoint."""

    @patch("api.routers.acm.ACMRecord.get_summary_by_source", new_callable=AsyncMock)
    def test_get_stats_by_source(self, mock_get_summary, client):
        """Test getting ACM stats filtered by source."""
        mock_get_summary.return_value = {
            "total_records": 100,
            "high_risk_count": 10,
            "medium_risk_count": 30,
            "low_risk_count": 60,
            "building_count": 5,
            "room_count": 20,
        }

        response = client.get("/api/acm/stats?source_id=source:abc")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 100
        assert data["high_risk_count"] == 10
        assert data["source_id"] == "source:abc"

    @patch("api.routers.acm.repo_query")
    def test_get_stats_global(self, mock_repo_query, client):
        """Test getting global ACM stats."""
        mock_repo_query.return_value = [
            {
                "total_records": 500,
                "high_risk_count": 50,
                "medium_risk_count": 150,
                "low_risk_count": 300,
                "buildings": ["B001", "B002", "B003"],
                "rooms": ["R101", "R102", None, "R103"],
            }
        ]

        response = client.get("/api/acm/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 500
        assert data["building_count"] == 3
        assert data["room_count"] == 3  # None should be filtered out
        assert data["source_id"] is None

    @patch("api.routers.acm.repo_query")
    def test_get_stats_empty(self, mock_repo_query, client):
        """Test getting stats when no records exist."""
        mock_repo_query.return_value = []

        response = client.get("/api/acm/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 0
        assert data["high_risk_count"] == 0
