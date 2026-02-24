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
        mock_record.result = "Positive"
        mock_record.page_number = 5
        mock_record.extraction_confidence = (
            "high"  # Must be string: "high", "medium", or "low"
        )
        # Classification fields (E1-S9)
        mock_record.acm_product_group = None
        mock_record.acm_product_type = None
        mock_record.classification_confidence = None
        mock_record.classification_method = None
        mock_record.classification_override = None
        # BAR compliance fields
        mock_record.sample_no = None
        mock_record.sample_result = None
        mock_record.quantity = None
        mock_record.acm_labelled = None
        mock_record.acm_label_details = None
        mock_record.identifying_company = None
        mock_record.disturbance_potential = None
        mock_record.hygienist_recommendations = None
        mock_record.normalized_action = None
        mock_record.data_issues = None
        mock_record.floor_level = None
        mock_record.no_access = None
        mock_record.smf_present = None
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

        response = client.post("/api/acm/extract", json={"source_id": "source:abc"})

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
        mock_record.result = "Positive"
        mock_record.page_number = 5
        mock_record.floor_level = None
        mock_record.sample_no = None
        mock_record.sample_result = None
        mock_record.quantity = None
        mock_record.acm_labelled = None
        mock_record.disturbance_potential = None
        mock_record.identifying_company = None
        mock_record.hygienist_recommendations = None

        mock_get_records.return_value = [mock_record]

        response = client.get("/api/acm/export?source_id=source:abc")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "Test_Source" in response.headers["content-disposition"]

        # Verify CSV content
        content = response.text
        assert "Building Code" in content
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


# =============================================================================
# E1-S9: ACM Product Classification API Tests
# =============================================================================


class TestClassifyACMItem:
    """Test suite for POST /api/acm/classify endpoint."""

    def test_classify_single_item_pattern_match(self, client):
        """Test classification of single item with pattern match - uses real classifier."""
        response = client.post(
            "/api/acm/classify",
            json={
                "item_description": "Vinyl floor tiles",
                "friability": "Non-friable",
                "use_llm_fallback": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_group"] == "T3 Vinyl products"
        assert data["product_type"] == "Vinyl Tiles"
        assert data["confidence"] == 0.9
        assert data["method"] == "pattern"

    def test_classify_with_llm_fallback_pattern_match(self, client):
        """Test classification with LLM fallback enabled - pattern match first."""
        response = client.post(
            "/api/acm/classify",
            json={
                "item_description": "Fibre cement sheeting",
                "friability": "Non-friable",
                "use_llm_fallback": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Pattern should match, no need for LLM
        assert data["method"] == "pattern"
        assert data["product_group"] == "T1 Cement products"

    def test_classify_no_match(self, client):
        """Test classification when no pattern matches and LLM disabled."""
        response = client.post(
            "/api/acm/classify",
            json={
                "item_description": "Unknown xyz material 12345",
                "use_llm_fallback": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_group"] is None
        assert data["product_type"] is None
        assert data["method"] == "none"

    def test_classify_missing_description(self, client):
        """Test validation error when item_description is missing."""
        response = client.post("/api/acm/classify", json={"friability": "Non-friable"})

        assert response.status_code == 422

    def test_classify_with_product_field(self, client):
        """Test classification with optional product field."""
        response = client.post(
            "/api/acm/classify",
            json={
                "item_description": "Wall cladding",
                "product": "Fibro",
                "friability": "Non-friable",
                "use_llm_fallback": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_group"] == "T1 Cement products"


class TestNormalizeRecommendation:
    """Test suite for POST /api/acm/normalize endpoint."""

    def test_normalize_maintain_in_situ(self, client):
        """Test normalization of maintain-in-situ wording."""
        response = client.post(
            "/api/acm/normalize",
            json={"recommendation": "Maintain in current condition and label"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["normalized_action"] == "maintain_in_situ"
        assert data["confidence"] > 0
        assert data["method"] in ("pattern", "config")
        assert data["raw_text"] == "Maintain in current condition and label"

    def test_normalize_remove_prior(self, client):
        """Test normalization of removal recommendation."""
        response = client.post(
            "/api/acm/normalize",
            json={
                "recommendation": "Remove under controlled bonded asbestos removal conditions"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["normalized_action"] == "remove_prior_to_refurb_or_demolition"

    def test_normalize_restrict_access(self, client):
        """Test normalization of restrict access recommendation."""
        response = client.post(
            "/api/acm/normalize", json={"recommendation": "Restrict access ASAP"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["normalized_action"] == "restrict_access_immediately"

    def test_normalize_unknown_returns_review_required(self, client):
        """Test that unknown text returns review_required."""
        response = client.post(
            "/api/acm/normalize",
            json={"recommendation": "Something completely unknown xyz 12345"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["normalized_action"] == "review_required"
        assert data["method"] == "none"
        assert data["confidence"] == 0.0

    def test_normalize_missing_recommendation(self, client):
        """Test validation error when recommendation is missing."""
        response = client.post("/api/acm/normalize", json={})

        assert response.status_code == 422

    def test_normalize_empty_recommendation(self, client):
        """Test validation error for empty recommendation."""
        response = client.post("/api/acm/normalize", json={"recommendation": ""})

        assert response.status_code == 422


class TestBatchClassifyACM:
    """Test suite for POST /api/acm/classify/batch endpoint."""

    @patch("api.routers.acm.ACMRecord.get_by_source", new_callable=AsyncMock)
    def test_batch_classify_success(self, mock_get_records, client):
        """Test batch classification of all records for a source."""
        # Mock records - use real classify_product
        mock_record1 = MagicMock()
        mock_record1.id = "acm_record:1"
        mock_record1.product = "Ceiling Tiles"
        mock_record1.material_description = "Cement ceiling tiles"
        mock_record1.friable = "Non-friable"
        mock_record1.acm_product_group = None
        mock_record1.save = AsyncMock()

        mock_record2 = MagicMock()
        mock_record2.id = "acm_record:2"
        mock_record2.product = "Floor Tiles"
        mock_record2.material_description = "Vinyl floor tiles"
        mock_record2.friable = "Non-friable"
        mock_record2.acm_product_group = None
        mock_record2.save = AsyncMock()

        mock_get_records.return_value = [mock_record1, mock_record2]

        response = client.post(
            "/api/acm/classify/batch",
            json={
                "source_id": "source:abc",
                "use_llm_fallback": False,
                "skip_classified": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["classified"] == 2
        assert data["skipped"] == 0
        assert data["errors"] == 0

    @patch("api.routers.acm.ACMRecord.get_by_source", new_callable=AsyncMock)
    def test_batch_classify_empty_source(self, mock_get_records, client):
        """Test batch classification when source has no records."""
        mock_get_records.return_value = []

        response = client.post(
            "/api/acm/classify/batch", json={"source_id": "source:empty"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["classified"] == 0

    @patch("api.routers.acm.ACMRecord.get_by_source", new_callable=AsyncMock)
    def test_batch_classify_skip_already_classified(self, mock_get_records, client):
        """Test that skip_classified=True skips already classified records."""
        # Record already classified
        mock_record = MagicMock()
        mock_record.id = "acm_record:1"
        mock_record.product = "Ceiling Tiles"
        mock_record.material_description = "Cement ceiling tiles"
        mock_record.friable = "Non-friable"
        mock_record.acm_product_group = "T1 Cement products"  # Already classified

        mock_get_records.return_value = [mock_record]

        response = client.post(
            "/api/acm/classify/batch",
            json={"source_id": "source:abc", "skip_classified": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["skipped"] == 1
        assert data["classified"] == 0

    def test_batch_classify_missing_source_id(self, client):
        """Test validation error when source_id is missing."""
        response = client.post(
            "/api/acm/classify/batch", json={"use_llm_fallback": True}
        )

        assert response.status_code == 422


class TestGetTaxonomy:
    """Test suite for GET /api/acm/taxonomy endpoint."""

    def test_get_taxonomy_nonfriable(self, client):
        """Test getting non-friable taxonomy - uses real taxonomy."""
        response = client.get("/api/acm/taxonomy?friability=Non-friable")

        assert response.status_code == 200
        data = response.json()
        assert data["friability"] == "Non-friable"
        assert len(data["groups"]) == 8  # T1-T8 for non-friable
        # Verify T1 Cement products is present
        t1_group = next((g for g in data["groups"] if g["pc_code"] == "T1"), None)
        assert t1_group is not None
        assert "Flat Sheeting" in t1_group["product_types"]

    def test_get_taxonomy_friable(self, client):
        """Test getting friable taxonomy."""
        response = client.get("/api/acm/taxonomy?friability=Friable")

        assert response.status_code == 200
        data = response.json()
        assert data["friability"] == "Friable"
        assert len(data["groups"]) == 6  # T1-T6 for friable

    def test_get_taxonomy_default(self, client):
        """Test getting default taxonomy (non-friable)."""
        response = client.get("/api/acm/taxonomy")

        assert response.status_code == 200
        data = response.json()
        assert data["friability"] == "Non-friable"
        assert len(data["groups"]) == 8


class TestACMRecordResponseClassificationFields:
    """Test that ACM record responses include classification fields."""

    @patch("api.routers.acm.ACMRecord.get", new_callable=AsyncMock)
    def test_get_record_includes_classification(self, mock_get, client):
        """Test that GET /api/acm/records/{id} returns classification fields."""
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
        mock_record.product = "Vinyl Floor Tiles"
        mock_record.material_description = "Vinyl tiles with asbestos"
        mock_record.extent = "100%"
        mock_record.location = "Floor"
        mock_record.friable = "Non Friable"
        mock_record.material_condition = "Good"
        mock_record.risk_status = "Low"
        mock_record.result = "Positive"
        mock_record.page_number = 5
        mock_record.extraction_confidence = "high"
        # Classification fields
        mock_record.acm_product_group = "T3 Vinyl products"
        mock_record.acm_product_type = "Vinyl Tiles"
        mock_record.classification_confidence = 0.9
        mock_record.classification_method = "pattern"
        mock_record.classification_override = False
        # BAR compliance fields
        mock_record.sample_no = None
        mock_record.sample_result = None
        mock_record.quantity = None
        mock_record.acm_labelled = None
        mock_record.acm_label_details = None
        mock_record.identifying_company = None
        mock_record.disturbance_potential = None
        mock_record.hygienist_recommendations = None
        mock_record.normalized_action = None
        mock_record.data_issues = None
        mock_record.floor_level = None
        mock_record.no_access = None
        mock_record.smf_present = None
        mock_record.created = "2024-01-01T00:00:00Z"
        mock_record.updated = "2024-01-01T00:00:00Z"

        mock_get.return_value = mock_record

        response = client.get("/api/acm/records/acm_record:123")

        assert response.status_code == 200
        data = response.json()

        # Verify classification fields are present
        assert data["acm_product_group"] == "T3 Vinyl products"
        assert data["acm_product_type"] == "Vinyl Tiles"
        assert data["classification_confidence"] == 0.9
        assert data["classification_method"] == "pattern"
        assert data["classification_override"] is False

    @patch("api.routers.acm.repo_query")
    def test_list_records_includes_classification(self, mock_repo_query, client):
        """Test that GET /api/acm/records returns classification fields."""
        mock_repo_query.side_effect = [
            [{"total": 1}],  # Count query
            [  # Data query
                {
                    "id": "acm_record:123",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B001",
                    "product": "Vinyl Floor Tiles",
                    "material_description": "Vinyl tiles",
                    "result": "Detected",
                    "acm_product_group": "T3 Vinyl products",
                    "acm_product_type": "Vinyl Tiles",
                    "classification_confidence": 0.9,
                    "classification_method": "pattern",
                    "classification_override": False,
                },
            ],
        ]

        response = client.get("/api/acm/records?source_id=source:abc")

        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 1

        record = data["records"][0]
        assert record["acm_product_group"] == "T3 Vinyl products"
        assert record["acm_product_type"] == "Vinyl Tiles"
        assert record["classification_confidence"] == 0.9
        assert record["classification_method"] == "pattern"
        assert record["classification_override"] is False
