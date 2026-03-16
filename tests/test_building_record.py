"""
Tests for BuildingRecord domain model and API endpoints (E30-S2).

Covers all acceptance criteria:
- AC1: 29+ SF Building__c fields present on BuildingRecord
- AC2: AliasChoices for BAR and SF field names
- AC3: internal_id generation pattern BLD#{source_short}_{seq:03d}
- AC4: building_record_id FK on ACMRecord
- AC5: CRUD API endpoints for /api/acm/buildings
- AC6: building_record_id filter on /api/acm/records
- AC7: get_by_source() classmethod
- AC8: Embedding fields on BuildingRecord
- AC9: Unit tests for model CRUD
- AC10: Indexes defined in migration (reviewed separately)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from open_notebook.domain.acm import ACMRecord, BuildingRecord
from open_notebook.exceptions import NotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create synchronous test client."""
    from api.main import app

    return TestClient(app)


def _make_building_dict(**kwargs):
    """Return a minimal valid building_record dict for mock DB responses."""
    defaults = {
        "id": "building_record:test001",
        "internal_id": "BLD#TESTSCHL_001",
        "source_id": "source:abc123",
        "building_code": "B01",
        "building_name": "Main Building",
        "created": "2026-01-01T00:00:00",
        "updated": "2026-01-01T00:00:00",
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# AC2, AC3, AC8: BuildingRecord model unit tests
# ---------------------------------------------------------------------------


class TestBuildingRecordModel:
    """Tests for BuildingRecord Pydantic model (no DB)."""

    def test_create_with_bar_field_names(self):
        """AC2: BuildingRecord accepts BAR field names."""
        record = BuildingRecord(
            internal_id="BLD#TESTSCHL_001",
            source_id="source:abc123",
            building_code="B01",
            building_name="Main Building",
            building_type="School",
        )
        assert record.building_name == "Main Building"
        assert record.building_type == "School"
        assert record.building_code == "B01"

    def test_create_with_sf_field_names(self):
        """AC2: BuildingRecord accepts SF API names via AliasChoices."""
        record = BuildingRecord(
            internal_id="BLD#TESTSCHL_001",
            source_id="source:abc123",
            **{
                "Building_Name__c": "Main Building",
                "Building_Type__c": "School",
                "Building_Code__c": "B01",
            },
        )
        assert record.building_name == "Main Building"
        assert record.building_type == "School"
        assert record.building_code == "B01"

    def test_create_with_sf_suburb_and_postcode(self):
        """AC2: SF field names for suburb and postcode work."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            **{"Suburb__c": "Kew", "Postcode__c": "3101"},
        )
        assert record.suburb == "Kew"
        assert record.postcode == "3101"

    def test_internal_id_validation_pattern_rejects_invalid(self):
        """AC3: internal_id must start with 'BLD#'."""
        with pytest.raises(Exception):
            BuildingRecord(
                internal_id="INVALID_001",
                source_id="source:abc123",
            )

    def test_internal_id_validation_rejects_empty(self):
        """AC3: Empty internal_id is rejected."""
        with pytest.raises(Exception):
            BuildingRecord(
                internal_id="",
                source_id="source:abc123",
            )

    def test_internal_id_valid_pattern(self):
        """AC3: Valid internal_id pattern accepted."""
        record = BuildingRecord(
            internal_id="BLD#SCHOOL_N_001",
            source_id="source:abc123",
        )
        assert record.internal_id == "BLD#SCHOOL_N_001"

    def test_internal_id_strips_whitespace(self):
        """AC3: internal_id strips surrounding whitespace."""
        record = BuildingRecord(
            internal_id="  BLD#TEST____001  ",
            source_id="source:abc123",
        )
        assert record.internal_id == "BLD#TEST____001"

    def test_source_id_auto_prefix(self):
        """AC7: source_id without prefix gets 'source:' prepended."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="abc123",
        )
        assert record.source_id == "source:abc123"

    def test_source_id_with_prefix_unchanged(self):
        """AC7: source_id already prefixed stays as-is."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
        )
        assert record.source_id == "source:abc123"

    def test_source_id_required(self):
        """AC7: Missing source_id raises validation error."""
        with pytest.raises(Exception):
            BuildingRecord(
                internal_id="BLD#TEST____001",
                source_id="",
            )

    def test_embedding_fields_present(self):
        """AC8: Embedding fields exist and accept values."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            embedding=[0.1, 0.2, 0.3],
            embedding_text="Main Building School",
            embedding_model="text-embedding-3-small",
            enriched_text="Building: Main Building | Type: School",
        )
        assert record.embedding == [0.1, 0.2, 0.3]
        assert record.embedding_text == "Main Building School"
        assert record.embedding_model == "text-embedding-3-small"
        assert record.enriched_text is not None

    def test_embedding_fields_default_none(self):
        """AC8: Embedding fields default to None."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
        )
        assert record.embedding is None
        assert record.embedding_text is None
        assert record.embedding_model is None
        assert record.embedded_at is None
        assert record.enriched_text is None

    def test_all_sf_fields_present(self):
        """AC1: BuildingRecord has 29+ SF Building__c fields."""
        sf_fields = [
            "building_code",
            "building_name",
            "building_year",
            "building_construction",
            "building_address",
            "suburb",
            "postcode",
            "building_type",
            "building_category",
            "building_address_lga",
            "building_address_region",
            "roof_type",
            "number_of_levels",
            "est_building_size_m2",
            "frequency_of_use",
            "daily_duration",
            "level_of_activity",
            "public_access",
            "mobile_plant",
            "owned_or_leased",
            "asbestos_register_available",
            "audit_report_available",
            "date_of_audit_report",
            "no_identified_acms",
            "no_identified_acms_note",
            "site_name",
            "school_uid",
            "building_unique_id",
            "external_id",
            "building_out_of_scope",
            "building_out_of_scope_comments",
            "demolished_status",
            "demolition_date",
            "demolition_type",
            "demolition_comments",
            "additional_comments",
            "within_your_portfolio",
            "psb_district_region",
            "state",
            "country",
            "gps_coordinates",
            "capital_works_project_details",
            "possible_capital_works_project",
        ]
        model_fields = set(BuildingRecord.model_fields.keys())
        for field in sf_fields:
            assert field in model_fields, f"Missing SF field: {field}"
        assert len(sf_fields) >= 29

    def test_table_name(self):
        """BuildingRecord.table_name is 'building_record'."""
        assert BuildingRecord.table_name == "building_record"

    def test_optional_fields_default_none(self):
        """All optional fields on BuildingRecord default to None."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
        )
        assert record.building_name is None
        assert record.building_type is None
        assert record.suburb is None
        assert record.number_of_levels is None
        assert record.building_out_of_scope is None

    def test_numeric_fields_accept_values(self):
        """number_of_levels (int) and est_building_size_m2 (float) accept values."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            number_of_levels=3,
            est_building_size_m2=450.5,
        )
        assert record.number_of_levels == 3
        assert record.est_building_size_m2 == 450.5

    def test_bool_field_accepts_value(self):
        """building_out_of_scope bool field accepts True/False."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            building_out_of_scope=True,
        )
        assert record.building_out_of_scope is True

    def test_prepare_save_data_includes_source_id_as_record(self):
        """AC8: _prepare_save_data converts source_id to proper record format."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
            building_name="Test",
        )
        data = record._prepare_save_data()
        assert data.get("source_id") is not None
        # Should be a record ID (string or RecordID object — both OK)
        assert "source" in str(data["source_id"])

    def test_prepare_save_data_excludes_none_values(self):
        """_prepare_save_data from base class skips None-valued fields."""
        record = BuildingRecord(
            internal_id="BLD#TEST____001",
            source_id="source:abc123",
        )
        data = record._prepare_save_data()
        # None fields should not appear
        assert "building_name" not in data
        assert "suburb" not in data


# ---------------------------------------------------------------------------
# AC3: internal_id generation (async, mocked DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBuildingRecordIDGeneration:
    """Tests for generate_internal_id classmethod."""

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    @patch("open_notebook.domain.notebook.repo_query", new_callable=AsyncMock)
    async def test_generate_internal_id_format(self, mock_nb_query, mock_acm_query):
        """AC3: Generated ID matches BLD#{source_short}_{seq:03d} pattern."""
        # Mock source fetch
        mock_nb_query.return_value = [
            {"id": "source:test", "name": "School Name Report.pdf"}
        ]
        # Mock no existing buildings
        mock_acm_query.return_value = []

        with patch("open_notebook.domain.notebook.Source") as mock_source_cls:
            mock_src = MagicMock()
            mock_src.title = "School Name Report.pdf"
            mock_source_cls.get = AsyncMock(return_value=mock_src)

            with patch.object(
                BuildingRecord, "get_by_source", new=AsyncMock(return_value=[])
            ):
                internal_id = await BuildingRecord.generate_internal_id("source:test")

        assert internal_id.startswith("BLD#")
        assert "_" in internal_id
        # seq part should be 3 digits
        seq_part = internal_id.split("_")[-1]
        assert len(seq_part) == 3
        assert seq_part.isdigit()

    async def test_generate_internal_id_first_is_001(self):
        """AC3: First building for a source gets seq 001."""
        with patch("open_notebook.domain.notebook.Source") as mock_source_cls:
            mock_src = MagicMock()
            mock_src.title = "SCHOOLNAME"
            mock_source_cls.get = AsyncMock(return_value=mock_src)

            with patch.object(
                BuildingRecord, "get_by_source", new=AsyncMock(return_value=[])
            ):
                internal_id = await BuildingRecord.generate_internal_id("source:test")

        assert internal_id.endswith("_001")

    async def test_generate_internal_id_second_is_002(self):
        """AC3: Second building for a source gets seq 002."""
        with patch("open_notebook.domain.notebook.Source") as mock_source_cls:
            mock_src = MagicMock()
            mock_src.title = "SCHOOLNAME"
            mock_source_cls.get = AsyncMock(return_value=mock_src)

            # One existing building already
            existing_building = MagicMock()
            with patch.object(
                BuildingRecord,
                "get_by_source",
                new=AsyncMock(return_value=[existing_building]),
            ):
                internal_id = await BuildingRecord.generate_internal_id("source:test")

        assert internal_id.endswith("_002")

    async def test_generate_internal_id_source_short_truncation(self):
        """AC3: Source title is truncated to 8 chars in internal_id."""
        with patch("open_notebook.domain.notebook.Source") as mock_source_cls:
            mock_src = MagicMock()
            mock_src.title = "A Very Long School Name Report.pdf"
            mock_source_cls.get = AsyncMock(return_value=mock_src)

            with patch.object(
                BuildingRecord, "get_by_source", new=AsyncMock(return_value=[])
            ):
                internal_id = await BuildingRecord.generate_internal_id("source:test")

        # Strip BLD# prefix, split by last underscore to get source_short
        after_prefix = internal_id[4:]  # Remove "BLD#"
        # Split on "_" — last element is seq, rest is source_short
        parts = after_prefix.rsplit("_", 1)
        source_short = parts[0]
        assert len(source_short) <= 8

    async def test_generate_internal_id_unknown_when_no_name(self):
        """AC3: Source with no title uses 'UNKNOWN' as source_short."""
        with patch("open_notebook.domain.notebook.Source") as mock_source_cls:
            mock_src = MagicMock()
            mock_src.title = None
            mock_source_cls.get = AsyncMock(return_value=mock_src)

            with patch.object(
                BuildingRecord, "get_by_source", new=AsyncMock(return_value=[])
            ):
                internal_id = await BuildingRecord.generate_internal_id("source:test")

        assert "UNKNOWN" in internal_id


# ---------------------------------------------------------------------------
# AC4: ACMRecord.building_record_id FK
# ---------------------------------------------------------------------------


class TestACMRecordBuildingFK:
    """Tests for building_record_id FK field on ACMRecord."""

    def _make_acm_record(self, **kwargs):
        defaults = {
            "source_id": "source:abc",
            "building_id": "B01",
            "product": "Roof Sheeting",
            "material_description": "Corrugated cement",
            "result": "Detected",
        }
        defaults.update(kwargs)
        return ACMRecord(**defaults)

    def test_building_record_id_default_none(self):
        """AC4: building_record_id defaults to None."""
        record = self._make_acm_record()
        assert record.building_record_id is None

    def test_building_record_id_accepts_value(self):
        """AC4: building_record_id accepts building_record:xxx format."""
        record = self._make_acm_record(building_record_id="building_record:xyz")
        assert record.building_record_id == "building_record:xyz"

    def test_prepare_save_data_includes_building_record_id(self):
        """AC4: _prepare_save_data converts building_record_id to record format."""
        record = self._make_acm_record(building_record_id="building_record:xyz")
        data = record._prepare_save_data()
        assert "building_record_id" in data

    def test_acm_record_without_building_record_id_saves_ok(self):
        """AC4: ACMRecord without building_record_id has None (no save error at model level)."""
        record = self._make_acm_record()
        assert record.building_record_id is None
        # _prepare_save_data should not include the None field
        data = record._prepare_save_data()
        assert "building_record_id" not in data

    def test_existing_building_id_field_unchanged(self):
        """Regression: Existing building_id string field still works."""
        record = self._make_acm_record(building_id="B999")
        assert record.building_id == "B999"
        # building_record_id is separate — not affected
        assert record.building_record_id is None


# ---------------------------------------------------------------------------
# AC7, AC9: BuildingRecord class methods (mocked DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBuildingRecordClassMethods:
    """Tests for BuildingRecord async class methods (mocked DB calls)."""

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_returns_records(self, mock_query):
        """AC7: get_by_source returns list of BuildingRecord instances."""
        mock_query.return_value = [
            _make_building_dict(internal_id="BLD#TESTSCHL_001"),
            _make_building_dict(
                id="building_record:test002", internal_id="BLD#TESTSCHL_002"
            ),
        ]
        results = await BuildingRecord.get_by_source("source:abc123")
        assert len(results) == 2
        assert all(isinstance(r, BuildingRecord) for r in results)
        assert results[0].internal_id == "BLD#TESTSCHL_001"

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_source_empty(self, mock_query):
        """AC7: get_by_source returns empty list when no records."""
        mock_query.return_value = []
        results = await BuildingRecord.get_by_source("source:abc123")
        assert results == []

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_internal_id_found(self, mock_query):
        """AC3: get_by_internal_id returns matching record."""
        mock_query.return_value = [_make_building_dict()]
        result = await BuildingRecord.get_by_internal_id("BLD#TESTSCHL_001")
        assert result is not None
        assert result.internal_id == "BLD#TESTSCHL_001"

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_get_by_internal_id_not_found(self, mock_query):
        """AC3: get_by_internal_id returns None when not found."""
        mock_query.return_value = []
        result = await BuildingRecord.get_by_internal_id("BLD#NONEXIST_001")
        assert result is None

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_delete_by_source(self, mock_query):
        """AC9: delete_by_source returns count of deleted records."""
        mock_query.return_value = [
            _make_building_dict(),
            _make_building_dict(id="building_record:test002"),
        ]
        count = await BuildingRecord.delete_by_source("source:abc123")
        assert count == 2

    @patch("open_notebook.domain.acm.repo_query", new_callable=AsyncMock)
    async def test_delete_by_source_empty(self, mock_query):
        """AC9: delete_by_source returns 0 when nothing to delete."""
        mock_query.return_value = []
        count = await BuildingRecord.delete_by_source("source:abc123")
        assert count == 0


# ---------------------------------------------------------------------------
# AC5, AC6: API endpoint tests (synchronous TestClient, mocked domain)
# ---------------------------------------------------------------------------


class TestBuildingRecordAPI:
    """Tests for /api/acm/buildings CRUD endpoints."""

    @patch("api.routers.acm.BuildingRecord")
    def test_list_buildings_success(self, mock_br_class, client):
        """AC5: GET /api/acm/buildings returns building list."""
        mock_br = MagicMock()
        mock_br.model_dump.return_value = _make_building_dict()
        mock_br_class.get_by_source = AsyncMock(return_value=[mock_br])

        response = client.get("/api/acm/buildings?source_id=source:abc123")

        assert response.status_code == 200
        data = response.json()
        assert "buildings" in data
        assert "total" in data
        assert data["total"] == 1

    @patch("api.routers.acm.BuildingRecord")
    def test_list_buildings_requires_source_id(self, mock_br_class, client):
        """AC5: GET /api/acm/buildings without source_id returns 422."""
        response = client.get("/api/acm/buildings")
        assert response.status_code == 422

    @patch("api.routers.acm.BuildingRecord")
    def test_create_building_success(self, mock_br_class, client):
        """AC5: POST /api/acm/buildings creates building with auto-generated ID."""
        mock_br_class.generate_internal_id = AsyncMock(return_value="BLD#SOURCE_T_001")
        mock_building_instance = MagicMock()
        mock_building_instance.model_dump.return_value = {
            **_make_building_dict(internal_id="BLD#SOURCE_T_001"),
        }
        mock_br_class.return_value = mock_building_instance
        mock_building_instance.save = AsyncMock()

        response = client.post(
            "/api/acm/buildings",
            json={
                "source_id": "source:abc123",
                "building_code": "B01",
                "building_name": "New Building",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["internal_id"] == "BLD#SOURCE_T_001"

    @patch("api.routers.acm.BuildingRecord")
    def test_get_building_success(self, mock_br_class, client):
        """AC5: GET /api/acm/buildings/{id} returns single building."""
        mock_br = MagicMock()
        mock_br.model_dump.return_value = _make_building_dict()
        mock_br_class.get = AsyncMock(return_value=mock_br)

        response = client.get("/api/acm/buildings/building_record:test001")

        assert response.status_code == 200
        data = response.json()
        assert data["internal_id"] == "BLD#TESTSCHL_001"

    @patch("api.routers.acm.BuildingRecord")
    def test_get_building_not_found(self, mock_br_class, client):
        """AC5: GET /api/acm/buildings/{invalid} returns 404."""
        mock_br_class.get = AsyncMock(side_effect=NotFoundError("Not found"))

        response = client.get("/api/acm/buildings/building_record:nonexistent")

        assert response.status_code == 404

    @patch("api.routers.acm.BuildingRecord")
    def test_update_building_success(self, mock_br_class, client):
        """AC5: PUT /api/acm/buildings/{id} updates building."""
        mock_br = MagicMock()
        updated_dump = {**_make_building_dict(), "building_name": "Updated via API"}
        mock_br.model_dump.return_value = updated_dump
        mock_br_class.get = AsyncMock(return_value=mock_br)
        mock_br.save = AsyncMock()

        response = client.put(
            "/api/acm/buildings/building_record:test001",
            json={"building_name": "Updated via API"},
        )

        assert response.status_code == 200
        assert response.json()["building_name"] == "Updated via API"

    @patch("api.routers.acm.BuildingRecord")
    def test_delete_building_success(self, mock_br_class, client):
        """AC5: DELETE /api/acm/buildings/{id} deletes building."""
        mock_br = MagicMock()
        mock_br.delete = AsyncMock(return_value=True)
        mock_br_class.get = AsyncMock(return_value=mock_br)

        response = client.delete("/api/acm/buildings/building_record:test001")

        assert response.status_code == 200
        assert response.json()["deleted"] is True
        assert response.json()["id"] == "building_record:test001"

    @patch("api.routers.acm.BuildingRecord")
    def test_delete_building_not_found(self, mock_br_class, client):
        """AC5: DELETE /api/acm/buildings/{invalid} returns 404."""
        mock_br_class.get = AsyncMock(side_effect=NotFoundError("Not found"))

        response = client.delete("/api/acm/buildings/building_record:nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# AC6: building_record_id filter on /api/acm/records
# ---------------------------------------------------------------------------


class TestACMRecordBuildingFilter:
    """Tests for building_record_id filter on existing /api/acm/records endpoint."""

    @patch("api.routers.acm.repo_query")
    def test_filter_by_building_record_id(self, mock_repo_query, client):
        """AC6: ?building_record_id param filters ACM records by FK."""
        mock_repo_query.side_effect = [
            [{"total": 1}],  # count query
            [
                {
                    "id": "acm_record:123",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B01",
                    "building_record_id": "building_record:bld001",
                    "product": "Ceiling Tiles",
                    "material_description": "Asbestos ceiling tiles",
                    "result": "Detected",
                    "created": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-01T00:00:00Z",
                }
            ],
        ]

        response = client.get(
            "/api/acm/records",
            params={
                "source_id": "source:abc",
                "building_record_id": "building_record:bld001",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["records"]) == 1

        # Check that the query was called with building_record_id parameter
        call_args_list = mock_repo_query.call_args_list
        # At least one call should contain building_record_id in params
        combined_params = {}
        for call in call_args_list:
            if len(call.args) > 1 and isinstance(call.args[1], dict):
                combined_params.update(call.args[1])
        assert "building_record_id" in combined_params

    @patch("api.routers.acm.repo_query")
    def test_list_records_without_building_record_id_unchanged(
        self, mock_repo_query, client
    ):
        """Regression: /api/acm/records without building_record_id still works."""
        mock_repo_query.side_effect = [
            [{"total": 1}],
            [
                {
                    "id": "acm_record:123",
                    "source_id": "source:abc",
                    "school_name": "Test School",
                    "building_id": "B01",
                    "product": "Ceiling Tiles",
                    "material_description": "Asbestos ceiling tiles",
                    "result": "Detected",
                    "created": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-01T00:00:00Z",
                }
            ],
        ]

        response = client.get("/api/acm/records?source_id=source:abc")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ---------------------------------------------------------------------------
# Regression: ACMRecord without building_record_id still works
# ---------------------------------------------------------------------------


class TestRegressionBackwardsCompatibility:
    """Regression tests to confirm no existing functionality is broken."""

    def test_acm_record_without_building_record_id_creates_ok(self):
        """Regression: ACMRecord creation without building_record_id succeeds."""
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
        )
        assert record.building_record_id is None
        assert record.building_id == "B01"

    def test_building_record_id_does_not_conflict_with_building_id(self):
        """Regression: building_id and building_record_id are independent fields."""
        record = ACMRecord(
            source_id="source:abc",
            building_id="B01",
            product="Roof Sheeting",
            material_description="Corrugated cement",
            result="Detected",
            building_record_id="building_record:xyz123",
        )
        assert record.building_id == "B01"
        assert record.building_record_id == "building_record:xyz123"

    def test_building_record_model_fields_count(self):
        """BuildingRecord has at least 29 SF building fields plus core fields."""
        all_fields = set(BuildingRecord.model_fields.keys())
        # Core fields: id, created, updated, internal_id, source_id, building_code
        # Plus 29+ SF fields + 5 embedding fields
        assert len(all_fields) >= 35
