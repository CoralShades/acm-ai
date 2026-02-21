"""
Tests for Parent Document Retrieval (E11-S1).

Tests ACMTableSection model, parent linking, search with parent context,
and backfill endpoint.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.acm import ACMRecord, ACMTableSection


class TestACMTableSectionModel:
    """Test ACMTableSection domain model creation and fields."""

    def test_create_table_section(self):
        """Test creating an ACMTableSection with all fields."""
        section = ACMTableSection(
            source_id="source:test123",
            page_start=14,
            page_end=16,
            raw_html="<table>...</table>",
            raw_text="Full table text content",
            building_name="B00A Main Block",
            table_type="register",
        )

        assert section.source_id == "source:test123"
        assert section.page_start == 14
        assert section.page_end == 16
        assert section.raw_html == "<table>...</table>"
        assert section.raw_text == "Full table text content"
        assert section.building_name == "B00A Main Block"
        assert section.table_type == "register"

    def test_create_table_section_minimal(self):
        """Test creating ACMTableSection with only required fields."""
        section = ACMTableSection(
            source_id="source:test123",
            page_start=1,
            page_end=3,
        )

        assert section.source_id == "source:test123"
        assert section.page_start == 1
        assert section.page_end == 3
        assert section.raw_html is None
        assert section.raw_text is None
        assert section.building_name is None
        assert section.table_type is None

    def test_source_id_auto_prefix(self):
        """Test that source_id gets 'source:' prefix if missing."""
        section = ACMTableSection(
            source_id="test123",
            page_start=1,
            page_end=5,
        )
        assert section.source_id == "source:test123"

    def test_source_id_validation_empty(self):
        """Test that empty source_id raises error."""
        from open_notebook.exceptions import InvalidInputError

        with pytest.raises(InvalidInputError):
            ACMTableSection(
                source_id="",
                page_start=1,
                page_end=5,
            )

    def test_table_name_is_correct(self):
        """Test that the class variable table_name is set correctly."""
        assert ACMTableSection.table_name == "acm_table_section"

    def test_table_type_values(self):
        """Test that various table_type values are accepted."""
        for table_type in ["register", "lab_report", "metadata", None]:
            section = ACMTableSection(
                source_id="source:test",
                page_start=1,
                page_end=2,
                table_type=table_type,
            )
            assert section.table_type == table_type


class TestACMTableSectionQueries:
    """Test ACMTableSection class methods (with mocked DB)."""

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source(self, mock_repo_query):
        """Test get_by_source returns table sections ordered by page_start."""
        mock_repo_query.return_value = [
            {
                "id": "acm_table_section:1",
                "source_id": "source:abc",
                "page_start": 1,
                "page_end": 5,
                "building_name": "B001",
                "table_type": "register",
            },
            {
                "id": "acm_table_section:2",
                "source_id": "source:abc",
                "page_start": 6,
                "page_end": 10,
                "building_name": "B002",
                "table_type": "register",
            },
        ]

        sections = await ACMTableSection.get_by_source("source:abc")

        assert len(sections) == 2
        assert sections[0].page_start == 1
        assert sections[1].page_start == 6
        mock_repo_query.assert_called_once()

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_empty(self, mock_repo_query):
        """Test get_by_source returns empty list when no sections exist."""
        mock_repo_query.return_value = []

        sections = await ACMTableSection.get_by_source("source:abc")
        assert sections == []

    @pytest.mark.asyncio
    async def test_get_by_source_empty_source_id(self):
        """Test get_by_source raises error for empty source_id."""
        from open_notebook.exceptions import InvalidInputError

        with pytest.raises(InvalidInputError):
            await ACMTableSection.get_by_source("")

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_page_range_found(self, mock_repo_query):
        """Test get_by_page_range finds section containing the page."""
        mock_repo_query.return_value = [
            {
                "id": "acm_table_section:1",
                "source_id": "source:abc",
                "page_start": 14,
                "page_end": 16,
                "building_name": "B00A",
                "table_type": "register",
            }
        ]

        section = await ACMTableSection.get_by_page_range("source:abc", page=15)

        assert section is not None
        assert section.page_start == 14
        assert section.page_end == 16
        assert section.building_name == "B00A"

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_page_range_not_found(self, mock_repo_query):
        """Test get_by_page_range returns None when no section contains page."""
        mock_repo_query.return_value = []

        section = await ACMTableSection.get_by_page_range("source:abc", page=99)
        assert section is None

    @pytest.mark.asyncio
    async def test_get_by_page_range_empty_source_id(self):
        """Test get_by_page_range raises error for empty source_id."""
        from open_notebook.exceptions import InvalidInputError

        with pytest.raises(InvalidInputError):
            await ACMTableSection.get_by_page_range("", page=5)

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_delete_by_source(self, mock_repo_query):
        """Test delete_by_source returns count of deleted sections."""
        mock_repo_query.return_value = [
            {"id": "acm_table_section:1"},
            {"id": "acm_table_section:2"},
        ]

        count = await ACMTableSection.delete_by_source("source:abc")
        assert count == 2


class TestACMRecordParentField:
    """Test parent_table_id field on ACMRecord."""

    def test_parent_table_id_default_none(self):
        """Test that parent_table_id defaults to None."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
        )
        assert record.parent_table_id is None

    def test_parent_table_id_can_be_set(self):
        """Test that parent_table_id can be set to a section reference."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
            parent_table_id="acm_table_section:abc123",
        )
        assert record.parent_table_id == "acm_table_section:abc123"

    def test_parent_table_id_in_prepare_save_data(self):
        """Test that _prepare_save_data converts parent_table_id to record ID."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Ceiling Tiles",
            material_description="Asbestos ceiling tiles",
            result="Detected",
            parent_table_id="acm_table_section:abc123",
        )
        data = record._prepare_save_data()
        # parent_table_id should be present and converted
        assert "parent_table_id" in data

    def test_backward_compatibility_without_parent(self):
        """Test that records without parent_table_id still work (backward compat)."""
        record = ACMRecord(
            source_id="source:test",
            school_name="Test School",
            building_id="B001",
            product="Floor Tiles",
            material_description="Vinyl floor tiles",
            result="Not Detected",
        )
        # Should work normally without parent
        assert record.parent_table_id is None
        text = record.get_embedding_text()
        assert "Floor Tiles" in text


class TestSearchWithParentContext:
    """Test search API with include_parent parameter."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    @patch("api.routers.acm.repo_query")
    @patch("api.routers.acm.ACMTableSection.get_by_source", new_callable=AsyncMock)
    @patch(
        "open_notebook.domain.models.model_manager.get_embedding_model",
        new_callable=AsyncMock,
    )
    def test_search_without_parent_default(
        self, mock_embedding_model, mock_get_by_source, mock_repo_query, client
    ):
        """Test that search without include_parent doesn't include parent context."""
        # Mock embedding model
        mock_model = MagicMock()
        mock_model.aembed = AsyncMock(return_value=[[0.1] * 1536])
        mock_embedding_model.return_value = mock_model

        # Mock search results
        mock_repo_query.return_value = [
            {
                "id": "acm_record:1",
                "source_id": "source:abc",
                "school_name": "Test School",
                "building_id": "B001",
                "building_name": "Main Block",
                "product": "Ceiling Tiles",
                "material_description": "Asbestos",
                "result": "Detected",
                "score": 0.95,
            }
        ]

        response = client.get("/api/acm/search?query=ceiling+tiles")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        # parent_context should be None when include_parent is not set
        result = data["results"][0]
        assert result["parent_context"] is None
        # get_by_source should NOT have been called (include_parent is false)
        mock_get_by_source.assert_not_called()

    @patch("api.routers.acm.repo_query")
    @patch("api.routers.acm.ACMTableSection.get_by_source", new_callable=AsyncMock)
    @patch(
        "open_notebook.domain.models.model_manager.get_embedding_model",
        new_callable=AsyncMock,
    )
    def test_search_with_parent_true(
        self, mock_embedding_model, mock_get_by_source, mock_repo_query, client
    ):
        """Test that search with include_parent=true includes parent context."""
        # Mock embedding model
        mock_model = MagicMock()
        mock_model.aembed = AsyncMock(return_value=[[0.1] * 1536])
        mock_embedding_model.return_value = mock_model

        # Mock search results
        mock_repo_query.return_value = [
            {
                "id": "acm_record:1",
                "source_id": "source:abc",
                "school_name": "Test School",
                "building_id": "B001",
                "building_name": "Main Block",
                "product": "Ceiling Tiles",
                "material_description": "Asbestos",
                "result": "Detected",
                "page_number": 15,
                "parent_table_id": "acm_table_section:sec1",
                "score": 0.95,
            }
        ]

        # Mock batch parent section lookup
        mock_section = ACMTableSection(
            source_id="source:abc",
            page_start=14,
            page_end=16,
            building_name="B00A Main Block",
            table_type="register",
            raw_text="Full table text...",
        )
        mock_section.id = "acm_table_section:sec1"
        mock_get_by_source.return_value = [mock_section]

        response = client.get("/api/acm/search?query=ceiling+tiles&include_parent=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        result = data["results"][0]
        assert "parent_context" in result
        assert result["parent_context"]["building_name"] == "B00A Main Block"
        assert result["parent_context"]["page_start"] == 14
        assert result["parent_context"]["page_end"] == 16
        assert result["parent_context"]["table_type"] == "register"


class TestSaveRecordsParentCreation:
    """Test that save_records creates parent table sections from BuildingInventory."""

    @pytest.mark.asyncio
    @patch("open_notebook.domain.acm.ACMTableSection.save", new_callable=AsyncMock)
    async def test_save_records_creates_sections_from_inventory(self, mock_save):
        """Test that save_records creates ACMTableSection for each building."""
        from open_notebook.graphs.acm_extraction import save_records

        # Make save() set an id on the instance
        async def set_id(self_ref=None):
            pass

        mock_save.side_effect = lambda: None
        # Patch save to assign an id
        saved_sections = []
        original_save = ACMTableSection.save

        async def capture_save(self):
            self.id = "acm_table_section:sec1"
            saved_sections.append(self)

        # Build a minimal source
        mock_source = MagicMock()
        mock_source.id = "source:test123"
        mock_source.full_text = (
            "--- Page 14 ---\nTable data here\n--- Page 15 ---\nMore data"
        )

        # Build inventory with one building
        building = MagicMock()
        building.building_id = "B001"
        building.name = "Main Block"
        building.page_start = 14
        building.page_end = 15
        inventory = MagicMock()
        inventory.buildings = [building]

        # Build a real extraction record (Pydantic model)
        from open_notebook.extractors.acm_schemas import ACMExtractionRecord

        test_record = ACMExtractionRecord(
            building_id="B001",
            building_name="Main Block",
            room_id="R01",
            room_name="Corridor",
            area_type="Interior",
            product="Floor Tiles",
            material_description="Vinyl tiles",
            result="Detected",
            page_number=14,
        )

        state = {
            "records": [test_record],
            "source": mock_source,
            "context": MagicMock(school_name="Test School", school_code=None),
            "building_inventory": inventory,
            "start_time": 0,
            "records_rejected": 0,
        }

        with (
            patch.object(ACMTableSection, "save", capture_save),
            patch("open_notebook.graphs.acm_extraction.ACMRecord") as MockACMRecord,
            patch(
                "open_notebook.graphs.acm_extraction.auto_populate_site_config",
                new_callable=AsyncMock,
            ),
        ):
            mock_acm = MagicMock()
            mock_acm.save = AsyncMock()
            mock_acm.get_enriched_embedding_text = MagicMock(return_value="enriched")
            MockACMRecord.return_value = mock_acm

            result = await save_records(state, MagicMock())

        # Verify section was created with raw_text populated
        assert len(saved_sections) == 1
        section = saved_sections[0]
        assert section.source_id == "source:test123"
        assert section.page_start == 14
        assert section.page_end == 15
        assert section.building_name == "B001 Main Block"
        assert section.raw_text is not None  # raw_text should be populated from source


class TestBackfillEndpoint:
    """Test POST /api/acm/backfill-parents endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    @patch("api.routers.acm.repo_query")
    def test_backfill_parents_success(self, mock_repo_query, client):
        """Test backfill endpoint links records to parent sections."""
        # First call: get records without parent
        # Second call: find matching section
        # Third call: update record
        mock_repo_query.side_effect = [
            # Records without parent_table_id
            [
                {
                    "id": "acm_record:1",
                    "source_id": "source:abc",
                    "page_number": 15,
                },
                {
                    "id": "acm_record:2",
                    "source_id": "source:abc",
                    "page_number": 20,
                },
            ],
            # Section for record 1 (page 15)
            [
                {
                    "id": "acm_table_section:sec1",
                    "source_id": "source:abc",
                    "page_start": 14,
                    "page_end": 16,
                }
            ],
            # Update record 1
            [{"id": "acm_record:1"}],
            # Section for record 2 (page 20)
            [
                {
                    "id": "acm_table_section:sec2",
                    "source_id": "source:abc",
                    "page_start": 18,
                    "page_end": 22,
                }
            ],
            # Update record 2
            [{"id": "acm_record:2"}],
        ]

        response = client.post("/api/acm/backfill-parents")

        assert response.status_code == 200
        data = response.json()
        assert data["records_updated"] == 2

    @patch("api.routers.acm.repo_query")
    def test_backfill_parents_with_source_filter(self, mock_repo_query, client):
        """Test backfill endpoint with source_id filter."""
        mock_repo_query.side_effect = [
            [],  # No records found
        ]

        response = client.post(
            "/api/acm/backfill-parents",
            json={"source_id": "source:specific"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["records_updated"] == 0

    @patch("api.routers.acm.repo_query")
    def test_backfill_no_matching_section(self, mock_repo_query, client):
        """Test backfill when record has no matching section."""
        mock_repo_query.side_effect = [
            # Records without parent
            [
                {
                    "id": "acm_record:1",
                    "source_id": "source:abc",
                    "page_number": 99,  # No section for this page
                },
            ],
            # No section found
            [],
        ]

        response = client.post("/api/acm/backfill-parents")

        assert response.status_code == 200
        data = response.json()
        assert data["records_updated"] == 0
