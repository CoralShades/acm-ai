"""
Unit tests for E34-S2 Bulk Operations backend endpoints.

Covers:
    - test_bulk_edit: POST /api/acm/bulk-edit updates all specified records
    - test_bulk_validate: POST /api/acm/bulk-validate re-runs SF validation per record
    - test_export_building_filter: GET /api/acm/export/csv filters by building_ids
"""

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client with a live app instance."""
    from api.main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event_bus_mock():
    """Return a mock PipelineEventBus with an async publish method."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


# ---------------------------------------------------------------------------
# AC2 — POST /api/acm/bulk-edit
# ---------------------------------------------------------------------------


class TestBulkEdit:
    """POST /api/acm/bulk-edit sets field = value for all record_ids."""

    @pytest.fixture(autouse=True)
    def _mocks(self):
        """Patch repo_query and PipelineEventBus so no DB is needed."""
        with (
            patch(
                "api.routers.acm.repo_query",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_rq,
            patch(
                "open_notebook.extractors.pipeline_event_bus.get_event_bus",
                return_value=_make_event_bus_mock(),
            ),
        ):
            self.mock_repo_query = mock_rq
            yield

    def test_bulk_edit_returns_updated_count(self, client):
        """Response body contains updated_count == number of record_ids sent."""
        payload = {
            "record_ids": ["acm_record:001", "acm_record:002", "acm_record:003"],
            "field": "material_condition",
            "value": "Good",
            "operation_id": "op-test-001",
        }
        response = client.post(
            "/api/acm/bulk-edit?source_id=source:test001",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3
        assert data["operation_id"] == "op-test-001"

    def test_bulk_edit_calls_repo_for_each_record(self, client):
        """repo_query UPDATE is called once per record_id (plus SSE publishes)."""
        payload = {
            "record_ids": ["acm_record:aaa", "acm_record:bbb"],
            "field": "material_condition",
            "value": "Poor",
            "operation_id": "op-test-002",
        }
        client.post(
            "/api/acm/bulk-edit?source_id=source:test001",
            json=payload,
        )
        # Each UPDATE call contains "UPDATE" in the query string
        update_calls = [
            c for c in self.mock_repo_query.call_args_list if "UPDATE" in str(c.args[0])
        ]
        assert len(update_calls) == 2

    def test_bulk_edit_empty_records_returns_zero(self, client):
        """An empty record_ids list returns updated_count = 0."""
        payload = {
            "record_ids": [],
            "field": "material_condition",
            "value": "Good",
            "operation_id": "op-test-003",
        }
        response = client.post(
            "/api/acm/bulk-edit?source_id=source:test001",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json()["updated_count"] == 0

    def test_bulk_edit_missing_source_id_returns_422(self, client):
        """source_id query param is required — 422 when omitted."""
        payload = {
            "record_ids": ["acm_record:001"],
            "field": "material_condition",
            "value": "Good",
            "operation_id": "op-test-004",
        }
        response = client.post("/api/acm/bulk-edit", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# AC3 — POST /api/acm/bulk-validate
# ---------------------------------------------------------------------------


class TestBulkValidate:
    """POST /api/acm/bulk-validate re-runs SF validation on specified records."""

    @pytest.fixture(autouse=True)
    def _mocks(self):
        """Mock repo_query to return a fake record, mock validate_acm_record."""
        fake_record = {
            "id": "acm_record:001",
            "source_id": "source:test001",
            "building_id": "BLD001",
            "product": "Vinyl Tiles",
            "result": "Positive",
        }

        fake_validation_ok = MagicMock()
        fake_validation_ok.is_valid = True
        fake_validation_ok.errors = []

        # repo_query returns:
        # - [fake_record] for SELECT * calls (one per record_id)
        # - []            for final remaining count SELECT
        select_results = [fake_record]

        async def _repo_query_side_effect(query, params=None):
            if "SELECT count()" in query:
                return []  # 0 remaining errors
            if "SELECT *" in query:
                return [fake_record]
            return []  # UPDATE calls

        with (
            patch(
                "api.routers.acm.repo_query",
                side_effect=_repo_query_side_effect,
            ),
            patch(
                "open_notebook.extractors.validators.acm_validator.validate_acm_record",
                return_value=fake_validation_ok,
            ),
        ):
            yield

    def test_bulk_validate_returns_fixed_count(self, client):
        """fixed_count equals number of records that passed validation."""
        payload = {
            "record_ids": ["acm_record:001", "acm_record:002"],
        }
        response = client.post("/api/acm/bulk-validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["fixed_count"] == 2
        assert data["remaining_errors"] == 0

    def test_bulk_validate_empty_list_returns_zero(self, client):
        """Empty record_ids list returns fixed_count = 0."""
        response = client.post("/api/acm/bulk-validate", json={"record_ids": []})
        assert response.status_code == 200
        assert response.json()["fixed_count"] == 0

    def test_bulk_validate_invalid_records_not_counted(self, client):
        """Records that fail validation are NOT counted in fixed_count."""
        fake_error = MagicMock()
        fake_error.message = "Missing required field"

        fake_validation_fail = MagicMock()
        fake_validation_fail.is_valid = False
        fake_validation_fail.errors = [fake_error]

        fake_record = {
            "id": "acm_record:bad",
            "source_id": "source:test001",
        }

        async def _failing_repo_query(query, params=None):
            if "SELECT count()" in query:
                return [{"cnt": 1}]
            if "SELECT *" in query:
                return [fake_record]
            return []

        with (
            patch("api.routers.acm.repo_query", side_effect=_failing_repo_query),
            patch(
                "open_notebook.extractors.validators.acm_validator.validate_acm_record",
                return_value=fake_validation_fail,
            ),
        ):
            response = client.post(
                "/api/acm/bulk-validate",
                json={"record_ids": ["acm_record:bad"]},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["fixed_count"] == 0
        assert data["remaining_errors"] == 1


# ---------------------------------------------------------------------------
# AC4 — GET /api/acm/export/csv with building_ids filter
# ---------------------------------------------------------------------------


class TestExportBuildingFilter:
    """GET /api/acm/export/csv filters returned records when building_ids is set."""

    _RECORDS_ALL = [
        {"building_id": "BLD001", "product": "Vinyl Tiles", "result": "Positive"},
        {"building_id": "BLD001", "product": "Pipe Lagging", "result": "Positive"},
        {"building_id": "BLD002", "product": "Ceiling Tiles", "result": "Negative"},
    ]

    @pytest.fixture(autouse=True)
    def _mock_get_by_source(self):
        """Patch ACMRecord.get_by_source and Source.get to avoid any DB calls."""
        fake_source = MagicMock()
        fake_source.title = "Test Source"

        with (
            patch(
                "api.routers.acm.ACMRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=self._RECORDS_ALL,
            ),
            patch(
                "open_notebook.domain.notebook.Source.get",
                new_callable=AsyncMock,
                return_value=fake_source,
            ),
        ):
            yield

    def test_export_no_filter_returns_all_records(self, client):
        """Without building_ids, all 3 records are returned in the CSV."""
        response = client.get("/api/acm/export/csv?source_id=source:test001")
        assert response.status_code == 200
        # CSV has header + 3 data rows → 4 lines (trailing newline may exist)
        text = response.text
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert len(lines) == 4  # 1 header + 3 records

    def test_export_with_building_id_filter_returns_subset(self, client):
        """When building_ids=BLD001, only 2 matching records are included."""
        response = client.get(
            "/api/acm/export/csv?source_id=source:test001&building_ids=BLD001"
        )
        assert response.status_code == 200
        text = response.text
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert len(lines) == 3  # 1 header + 2 BLD001 records
        assert "Ceiling Tiles" not in text

    def test_export_with_nonexistent_building_returns_404(self, client):
        """When building_ids filters out all records, 404 is returned."""
        response = client.get(
            "/api/acm/export/csv?source_id=source:test001&building_ids=BLD_NONEXISTENT"
        )
        assert response.status_code == 404

    def test_export_multiple_building_ids_union(self, client):
        """Multiple building_ids params combine as a union (OR) filter."""
        response = client.get(
            "/api/acm/export/csv?source_id=source:test001"
            "&building_ids=BLD001&building_ids=BLD002"
        )
        assert response.status_code == 200
        text = response.text
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert len(lines) == 4  # 1 header + all 3 records
