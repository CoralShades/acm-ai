"""
Tests for field-config API endpoints.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
Task 8.6: Test API endpoints (GET/PUT /api/acm/field-config)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from api.main import app

    return TestClient(app)


class TestGetFieldConfig:
    """Test GET /api/acm/field-config endpoint."""

    def test_get_field_config_returns_200(self, client):
        """GET returns current field schema config."""
        response = client.get("/api/acm/field-config")
        assert response.status_code == 200

    def test_get_field_config_has_fields(self, client):
        """Response contains 47 fields from BAR schema."""
        response = client.get("/api/acm/field-config")
        data = response.json()
        assert "fields" in data
        assert len(data["fields"]) == 47

    def test_get_field_config_has_enums(self, client):
        """Response contains enum definitions."""
        response = client.get("/api/acm/field-config")
        data = response.json()
        assert "enums" in data
        assert "SampleResult" in data["enums"]

    def test_get_field_config_has_business_rules(self, client):
        """Response contains business rules."""
        response = client.get("/api/acm/field-config")
        data = response.json()
        assert "business_rules" in data
        assert len(data["business_rules"]) >= 4

    def test_get_field_config_has_version(self, client):
        """Response contains version string."""
        response = client.get("/api/acm/field-config")
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_get_field_config_field_structure(self, client):
        """Each field has expected structure."""
        response = client.get("/api/acm/field-config")
        data = response.json()
        field = data["fields"][0]
        assert "internal_name" in field
        assert "display_name" in field
        assert "excel_column" in field
        assert "col_index" in field
        assert "field_type" in field
        assert "required" in field
        assert "active" in field


class TestUpdateFieldConfig:
    """Test PUT /api/acm/field-config endpoint."""

    @pytest.fixture(autouse=True)
    def mock_db(self):
        from unittest.mock import AsyncMock, patch

        with patch(
            "api.routers.acm.repo_query", new_callable=AsyncMock, return_value=[]
        ):
            yield

    def test_update_field_config_toggle_active(self, client):
        """PUT can toggle a field's active status."""
        # First get current config
        response = client.get("/api/acm/field-config")
        data = response.json()

        # Toggle first field's active status
        data["fields"][0]["active"] = False

        response = client.put("/api/acm/field-config", json=data)
        assert response.status_code == 200

        updated = response.json()
        assert updated["fields"][0]["active"] is False

    def test_update_field_config_preserves_structure(self, client):
        """PUT preserves all fields and structure."""
        response = client.get("/api/acm/field-config")
        data = response.json()

        response = client.put("/api/acm/field-config", json=data)
        assert response.status_code == 200

        updated = response.json()
        assert len(updated["fields"]) == len(data["fields"])
        assert updated["version"] == data["version"]

    def test_update_field_config_invalid_body(self, client):
        """PUT with invalid body returns 422."""
        response = client.put("/api/acm/field-config", json={"invalid": True})
        assert response.status_code == 422


class TestResetFieldConfig:
    """Test POST /api/acm/field-config/reset endpoint."""

    @pytest.fixture(autouse=True)
    def mock_db(self):
        from unittest.mock import AsyncMock, patch

        with patch(
            "api.routers.acm.repo_query", new_callable=AsyncMock, return_value=[]
        ):
            yield

    def test_reset_returns_default_config(self, client):
        """POST reset restores default config from JSON files."""
        response = client.post("/api/acm/field-config/reset")
        assert response.status_code == 200

        data = response.json()
        assert len(data["fields"]) == 47
        assert data["version"] == "1.0.0"

    def test_reset_after_modification(self, client):
        """Reset restores defaults after modifications."""
        # Modify config
        response = client.get("/api/acm/field-config")
        data = response.json()
        data["fields"][0]["active"] = False
        client.put("/api/acm/field-config", json=data)

        # Reset
        response = client.post("/api/acm/field-config/reset")
        assert response.status_code == 200

        data = response.json()
        # All fields should be active again by default
        assert all(f["active"] for f in data["fields"])
