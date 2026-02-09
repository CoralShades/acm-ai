"""
Tests for ACM Embedding Service and Semantic Search.

Story: E1-S6 Configure Local Embedding Pipeline
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.acm import ACMEmbeddingConfig, ACMRecord


class TestACMRecordEmbeddingFields:
    """Test ACMRecord embedding field additions."""

    def test_embedding_fields_exist(self):
        """Test that embedding fields are defined on ACMRecord."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )

        # New embedding fields should exist with None defaults
        assert hasattr(record, "embedding")
        assert hasattr(record, "embedding_text")
        assert hasattr(record, "embedding_model")
        assert hasattr(record, "embedded_at")

        assert record.embedding is None
        assert record.embedding_text is None
        assert record.embedding_model is None
        assert record.embedded_at is None

    def test_embedding_fields_can_be_set(self):
        """Test that embedding fields can be populated."""
        now = datetime.now(UTC)
        embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]

        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
            embedding=embedding_vector,
            embedding_text="Building: B001 | Product: Ceiling Tiles",
            embedding_model="ollama:mxbai-embed-large",
            embedded_at=now,
        )

        assert record.embedding == embedding_vector
        assert record.embedding_text == "Building: B001 | Product: Ceiling Tiles"
        assert record.embedding_model == "ollama:mxbai-embed-large"
        assert record.embedded_at == now


class TestACMRecordGetEmbeddingText:
    """Test ACMRecord.get_embedding_text() method."""

    def test_get_embedding_text_basic(self):
        """Test basic embedding text generation."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            building_name="Main Building",
            room_name="Room 101",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )

        text = record.get_embedding_text()

        assert "Building: Main Building" in text
        assert "Room: Room 101" in text
        assert "Product: Ceiling Tiles" in text
        assert "Material: Asbestos ceiling tiles" in text
        assert "Result: Detected" in text

    def test_get_embedding_text_with_all_fields(self):
        """Test embedding text with all relevant fields populated."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            building_name="Main Building",
            room_name="Room 101",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            location="Above dropped ceiling",
            extent="50 sqm",
            material_condition="Poor",
            risk_status="High",
            friable="Friable",
            result="Detected",
            hygienist_recommendations="Remove immediately",
        )

        text = record.get_embedding_text()

        assert "Building: Main Building" in text
        assert "Room: Room 101" in text
        assert "Product: Ceiling Tiles" in text
        assert "Material: Asbestos ceiling tiles" in text
        assert "Location: Above dropped ceiling" in text
        assert "Extent: 50 sqm" in text
        assert "Condition: Poor" in text
        assert "Risk: High" in text
        assert "Friable: Friable" in text
        assert "Result: Detected" in text
        assert "Recommendations: Remove immediately" in text

    def test_get_embedding_text_with_missing_optional_fields(self):
        """Test that missing optional fields are not included."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )

        text = record.get_embedding_text()

        # Should include required fields
        assert "Product: Ceiling Tiles" in text
        assert "Material: Asbestos ceiling tiles" in text
        assert "Result: Detected" in text

        # Should NOT include fields that are None
        assert "Building:" not in text  # building_name is None
        assert "Room:" not in text  # room_name is None
        assert "Location:" not in text
        assert "Risk:" not in text

    def test_get_embedding_text_empty_record(self):
        """Test embedding text for record with only required fields."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Unknown",
            material_description="Unknown material",
            result="Pending",
        )

        text = record.get_embedding_text()

        # Should still produce valid text
        assert len(text) > 0
        assert "Product: Unknown" in text


class TestACMEmbeddingConfig:
    """Test ACMEmbeddingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ACMEmbeddingConfig()

        assert config.enabled is True
        assert config.model_id is None
        assert config.batch_size == 50
        assert len(config.include_fields) > 0
        assert "product" in config.include_fields
        assert "material_description" in config.include_fields

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ACMEmbeddingConfig(
            enabled=False,
            model_id="custom-model",
            batch_size=100,
            include_fields=["product", "risk_status"],
        )

        assert config.enabled is False
        assert config.model_id == "custom-model"
        assert config.batch_size == 100
        assert config.include_fields == ["product", "risk_status"]


class TestACMEmbeddingService:
    """Test ACMEmbeddingService functionality."""

    @pytest.fixture
    def mock_embedding_model(self):
        """Create a mock embedding model."""
        model = AsyncMock()
        # Return different embeddings for each text
        model.aembed = AsyncMock(
            return_value=[
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
            ]
        )
        model.__str__ = MagicMock(return_value="mock-embedding-model")
        return model

    @pytest.fixture
    def sample_records(self):
        """Create sample ACM records for testing."""
        return [
            ACMRecord(
                source_id="source:test",
                school_name="Test School",
                building_id="B001",
                building_name="Building A",
                product="Ceiling Tiles",
                material_description="Asbestos tiles",
                result="Detected",
            ),
            ACMRecord(
                source_id="source:test",
                school_name="Test School",
                building_id="B002",
                building_name="Building B",
                product="Floor Tiles",
                material_description="Vinyl tiles",
                result="Not Detected",
            ),
        ]

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_success(
        self, mock_model_manager, mock_embedding_model, sample_records
    ):
        """Test successful embedding of records."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        service = ACMEmbeddingService()
        result = await service.embed_records(sample_records)

        assert len(result) == 2
        assert result[0].embedding == [0.1, 0.2, 0.3]
        assert result[1].embedding == [0.4, 0.5, 0.6]
        assert result[0].embedding_model == "mock-embedding-model"
        assert result[0].embedded_at is not None

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_disabled(self, mock_model_manager, sample_records):
        """Test that embedding is skipped when disabled."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        config = ACMEmbeddingConfig(enabled=False)
        service = ACMEmbeddingService(config)
        result = await service.embed_records(sample_records)

        # Records should be returned unchanged
        assert len(result) == 2
        assert result[0].embedding is None
        assert result[1].embedding is None

        # Should not have called the model
        mock_model_manager.get_embedding_model.assert_not_called()

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_no_model_configured(
        self, mock_model_manager, sample_records
    ):
        """Test error when no embedding model is configured."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_model_manager.get_embedding_model = AsyncMock(return_value=None)

        service = ACMEmbeddingService()

        with pytest.raises(ValueError, match="No embedding model configured"):
            await service.embed_records(sample_records)

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_empty_list(self, mock_model_manager):
        """Test embedding empty record list."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        service = ACMEmbeddingService()
        result = await service.embed_records([])

        assert result == []
        mock_model_manager.get_embedding_model.assert_not_called()

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_single_record(
        self, mock_model_manager, mock_embedding_model, sample_records
    ):
        """Test embedding a single record."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        service = ACMEmbeddingService()
        result = await service.embed_single(sample_records[0])

        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.embedding_model == "mock-embedding-model"

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_get_query_embedding(self, mock_model_manager, mock_embedding_model):
        """Test getting embedding for a search query."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_embedding_model.aembed = AsyncMock(return_value=[[0.7, 0.8, 0.9]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        service = ACMEmbeddingService()
        result = await service.get_query_embedding("high risk asbestos")

        assert result == [0.7, 0.8, 0.9]
        mock_embedding_model.aembed.assert_called_once_with(["high risk asbestos"])

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_uses_enriched_text(
        self, mock_model_manager, mock_embedding_model
    ):
        """Test that embed_records uses enriched text for embedding (E1-S14)."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        records = [
            ACMRecord(
                source_id="source:test",
                school_name="Test School",
                building_id="B001",
                building_name="Main Block",
                area_type="Ground Floor",
                room_name="Kitchen",
                page_number=5,
                product="Ceiling Tiles",
                material_description="Asbestos tiles",
                result="Detected",
            )
        ]

        service = ACMEmbeddingService()
        result = await service.embed_records(records)

        # The text passed to embedding model should be the enriched version
        call_args = mock_embedding_model.aembed.call_args[0][0]
        assert "Level: Ground Floor" in call_args[0]
        assert "Page: 5" in call_args[0]
        # Building/Room come from raw text (not duplicated in context prefix)
        assert "Building: Main Block" in call_args[0]
        assert "Room: Kitchen" in call_args[0]

        # enriched_text should be stored on the record
        assert result[0].enriched_text is not None
        assert "Level: Ground Floor" in result[0].enriched_text

        # embedding_text (raw) should also be stored
        assert result[0].embedding_text is not None

    @pytest.mark.asyncio
    @patch("api.services.acm_embedding_service.model_manager")
    async def test_embed_records_fallback_to_raw(
        self, mock_model_manager, mock_embedding_model
    ):
        """Test fallback: when enriched text is empty, uses raw embedding_text (E1-S14)."""
        from api.services.acm_embedding_service import ACMEmbeddingService

        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        # Record with no hierarchy context fields
        records = [
            ACMRecord(
                source_id="source:test",
                school_name="Test School",
                building_id="B001",
                product="Ceiling Tiles",
                material_description="Asbestos tiles",
                result="Detected",
            )
        ]

        service = ACMEmbeddingService()
        result = await service.embed_records(records)

        # With no context, enriched == raw, so embedding_text should still be set
        assert result[0].embedding is not None
        assert result[0].embedding_text is not None


class TestACMRecordEnrichedTextField:
    """Test ACMRecord enriched_text field (E1-S14)."""

    def test_enriched_text_field_exists(self):
        """Test that enriched_text field is defined on ACMRecord."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )
        assert hasattr(record, "enriched_text")
        assert record.enriched_text is None

    def test_enriched_text_field_can_be_set(self):
        """Test that enriched_text field can be populated."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
            enriched_text="Building: Main Block | Product: Ceiling Tiles",
        )
        assert record.enriched_text == "Building: Main Block | Product: Ceiling Tiles"


class TestACMRecordGetEnrichedEmbeddingText:
    """Test ACMRecord.get_enriched_embedding_text() method (E1-S14)."""

    def test_enriched_text_with_full_context(self):
        """Test enriched text with all hierarchy fields populated."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            building_name="B00A Main Block",
            area_type="Ground Floor",
            room_name="R001 Kitchen",
            page_number=14,
            product="Vinyl Floor Tiles",
            material_description="Sheet vinyl flooring",
            material_condition="Good",
            risk_status="Medium",
            friable="Non-friable",
            result="Detected",
            hygienist_recommendations="Maintain in situ, label and monitor",
        )

        text = record.get_enriched_embedding_text()

        # Level and Page context should be prepended (not already in raw text)
        assert text.startswith("Level: Ground Floor")
        assert "Page: 14" in text

        # Building and Room come from raw text (not duplicated in context)
        assert "Building: B00A Main Block" in text
        assert "Room: R001 Kitchen" in text

        # Verify no duplication: Building/Room should appear exactly once
        assert text.count("Building: B00A Main Block") == 1
        assert text.count("Room: R001 Kitchen") == 1

        # Raw embedding fields should follow
        assert "Product: Vinyl Floor Tiles" in text
        assert "Material: Sheet vinyl flooring" in text
        assert "Condition: Good" in text
        assert "Risk: Medium" in text
        assert "Result: Detected" in text

    def test_enriched_text_with_partial_context(self):
        """Test enriched text when only area_type is set as extra context."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            building_name="Main Building",
            area_type="First Floor",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )

        text = record.get_enriched_embedding_text()

        assert "Level: First Floor" in text  # area_type adds context
        assert "Building: Main Building" in text  # from raw text
        assert "Page:" not in text  # page_number is None
        assert "Product: Ceiling Tiles" in text

    def test_enriched_text_with_no_context(self):
        """Test enriched text when no hierarchy fields set, falls back to raw text."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )

        enriched = record.get_enriched_embedding_text()
        raw = record.get_embedding_text()

        # With no hierarchy context, enriched should equal raw
        assert enriched == raw
        assert "Product: Ceiling Tiles" in enriched

    def test_enriched_text_empty_record(self):
        """Test enriched text for minimal record returns empty string."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Unknown",
            material_description="Unknown",
            result="Pending",
        )

        # Even minimal records should produce some text
        text = record.get_enriched_embedding_text()
        assert len(text) > 0

    def test_enriched_text_includes_raw_fields(self):
        """Verify raw field text is appended after context prefix."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            building_name="Block A",
            room_name="Room 5",
            area_type="Ground Floor",
            page_number=3,
            product="Pipe Insulation",
            material_description="Asbestos pipe lagging",
            location="Above ceiling",
            result="Detected",
        )

        text = record.get_enriched_embedding_text()
        raw = record.get_embedding_text()

        # The enriched text should contain ALL the raw fields
        assert raw in text or all(part in text for part in raw.split(" | "))
        # Level/Page context should appear before raw fields
        level_pos = text.find("Level: Ground Floor")
        product_pos = text.find("Product: Pipe Insulation")
        assert level_pos < product_pos


class TestSemanticSearchEndpoint:
    """Test ACM semantic search API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    @patch("open_notebook.domain.models.model_manager")
    @patch("api.routers.acm.repo_query")
    def test_search_success(self, mock_repo_query, mock_model_manager, client):
        """Test successful semantic search."""
        # Mock embedding model
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        # Mock search results
        mock_repo_query.return_value = [
            {
                "id": "acm_record:123",
                "source_id": "source:abc",
                "school_name": "Test School",
                "building_id": "B001",
                "building_name": "Main Building",
                "product": "Ceiling Tiles",
                "material_description": "Asbestos tiles",
                "risk_status": "High",
                "result": "Detected",
                "score": 0.85,
            }
        ]

        response = client.get("/api/acm/search?query=high+risk+asbestos")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "high risk asbestos"
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["score"] == 0.85

    @patch("open_notebook.domain.models.model_manager")
    def test_search_no_embedding_model(self, mock_model_manager, client):
        """Test search fails gracefully when no embedding model configured."""
        mock_model_manager.get_embedding_model = AsyncMock(return_value=None)

        response = client.get("/api/acm/search?query=test")

        assert response.status_code == 400
        assert "No embedding model configured" in response.json()["detail"]

    def test_search_missing_query(self, client):
        """Test that query parameter is required."""
        response = client.get("/api/acm/search")

        assert response.status_code == 422  # Validation error

    @patch("open_notebook.domain.models.model_manager")
    @patch("api.routers.acm.repo_query")
    def test_search_threshold_filtering(
        self, mock_repo_query, mock_model_manager, client
    ):
        """Test that results below threshold are filtered out."""
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        # Return results with varying scores
        mock_repo_query.return_value = [
            {
                "id": "acm_record:1",
                "source_id": "source:abc",
                "school_name": "School",
                "building_id": "B1",
                "product": "Tiles",
                "material_description": "ACM",
                "result": "Detected",
                "score": 0.9,
            },
            {
                "id": "acm_record:2",
                "source_id": "source:abc",
                "school_name": "School",
                "building_id": "B2",
                "product": "Pipes",
                "material_description": "ACM",
                "result": "Detected",
                "score": 0.3,  # Below default threshold of 0.5
            },
        ]

        response = client.get("/api/acm/search?query=asbestos")

        assert response.status_code == 200
        data = response.json()
        # Only the result above threshold should be returned
        assert data["total"] == 1
        assert data["results"][0]["score"] == 0.9

    @patch("open_notebook.domain.models.model_manager")
    @patch("api.routers.acm.repo_query")
    def test_search_with_source_filter(
        self, mock_repo_query, mock_model_manager, client
    ):
        """Test search with source_id filter."""
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        mock_repo_query.return_value = []

        response = client.get("/api/acm/search?query=test&source_id=source:specific")

        assert response.status_code == 200

        # Verify source_id was included in query parameters
        call_args = mock_repo_query.call_args
        # The params are in the second positional argument (call_args[0][1])
        assert "source_id" in str(call_args)  # source_id should be in the query


class TestReEmbedEndpoint:
    """Test ACM re-embed API endpoint (E1-S14)."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    @patch("api.services.acm_embedding_service.model_manager")
    @patch("open_notebook.database.repository.repo_query")
    @patch("open_notebook.domain.acm.ACMRecord.save")
    def test_re_embed_all_records(
        self, mock_save, mock_repo_query, mock_model_manager, client
    ):
        """Test re-embedding all records."""
        # Mock embedding model
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_embedding_model.__str__ = MagicMock(return_value="mock-model")
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        # Mock repo_query to return one record without embedding
        mock_repo_query.return_value = [
            {
                "id": "acm_record:1",
                "source_id": "source:abc",
                "school_name": "Test School",
                "building_id": "B001",
                "building_name": "Main Block",
                "product": "Tiles",
                "material_description": "Asbestos",
                "result": "Detected",
                "embedding": None,
            }
        ]

        mock_save.return_value = None

        response = client.post("/api/acm/re-embed", json={"force": False})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["records_processed"] >= 0

    @patch("api.services.acm_embedding_service.model_manager")
    @patch("open_notebook.domain.acm.ACMRecord.get_by_source")
    @patch("open_notebook.domain.acm.ACMRecord.save")
    def test_re_embed_filtered_by_source(
        self, mock_save, mock_get_by_source, mock_model_manager, client
    ):
        """Test re-embedding filtered by source_id."""
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_embedding_model.__str__ = MagicMock(return_value="mock-model")
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        mock_get_by_source.return_value = [
            ACMRecord(
                id="acm_record:1",
                source_id="source:abc",
                school_name="Test School",
                building_id="B001",
                building_name="Block A",
                product="Tiles",
                material_description="Asbestos",
                result="Detected",
            )
        ]

        mock_save.return_value = None

        response = client.post(
            "/api/acm/re-embed", json={"source_id": "source:abc", "force": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_get_by_source.assert_called_once()

    @patch("api.services.acm_embedding_service.model_manager")
    @patch("open_notebook.domain.acm.ACMRecord.get_by_source")
    @patch("open_notebook.domain.acm.ACMRecord.save")
    def test_re_embed_force(
        self, mock_save, mock_get_by_source, mock_model_manager, client
    ):
        """Test force flag re-embeds already-embedded records (E1-S14 AC#6)."""
        mock_embedding_model = AsyncMock()
        mock_embedding_model.aembed = AsyncMock(return_value=[[0.7, 0.8, 0.9]])
        mock_embedding_model.__str__ = MagicMock(return_value="mock-model")
        mock_model_manager.get_embedding_model = AsyncMock(
            return_value=mock_embedding_model
        )

        # Record that already has an embedding — should be skipped without force
        already_embedded = ACMRecord(
            id="acm_record:2",
            source_id="source:abc",
            school_name="Test School",
            building_id="B001",
            building_name="Block A",
            product="Tiles",
            material_description="Asbestos",
            result="Detected",
            embedding=[0.1, 0.2, 0.3],
            embedding_model="old-model",
        )

        mock_get_by_source.return_value = [already_embedded]
        mock_save.return_value = None

        # Without force, already-embedded records should be skipped
        response = client.post(
            "/api/acm/re-embed", json={"source_id": "source:abc", "force": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["records_processed"] == 0

        # With force, already-embedded records should be re-embedded
        mock_get_by_source.return_value = [already_embedded]
        response = client.post(
            "/api/acm/re-embed", json={"source_id": "source:abc", "force": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["records_processed"] >= 1
