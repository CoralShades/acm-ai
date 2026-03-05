"""
Tests for V3 Building Record Backfill (E35-S6).

Covers:
1. test_backfill_creates_building_records -- 3 records, 2 buildings -> 2 created, 3 linked
2. test_backfill_idempotent_skips_existing -- existing building -> skipped, FK still updated for NULL records
3. test_backfill_skips_v3_sources -- all records have building_record_id -> 0 created, all already_linked
4. test_backfill_dry_run -- no save() or UPDATE calls
5. test_backfill_api_endpoint -- TestClient POST, verify 200 + JSON shape
6. test_rollback_deletes_and_unlinks -- verify DELETE + UPDATE NONE queries
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from scripts.v3_building_backfill import BackfillResult, backfill_source
from scripts.v3_building_rollback import RollbackResult, rollback_source

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create synchronous test client."""
    from api.main import app

    return TestClient(app)


def _make_acm_record_dict(
    record_id: str = "acm_record:001",
    source_id: str = "source:abc123",
    building_id: str = "B01",
    building_record_id=None,
    **kwargs,
) -> dict:
    """Return a minimal valid acm_record dict for mock DB responses."""
    rec = {
        "id": record_id,
        "source_id": source_id,
        "building_id": building_id,
        "building_name": "Main Building",
        "building_year": 1990,
        "building_construction": "Brick",
        "building_address": "123 Test St",
        "suburb": "Testville",
        "postcode": "3000",
        "building_type": "School",
        "product": "Roof Sheeting",
        "material_description": "Corrugated cement",
        "result": "Detected",
    }
    if building_record_id is not None:
        rec["building_record_id"] = building_record_id
    rec.update(kwargs)
    return rec


# ---------------------------------------------------------------------------
# Test 1: backfill creates building records
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "scripts.v3_building_backfill.BuildingRecord.generate_internal_id",
    new_callable=AsyncMock,
)
@patch("scripts.v3_building_backfill.BuildingRecord.save", new_callable=AsyncMock)
@patch("scripts.v3_building_backfill.repo_query", new_callable=AsyncMock)
async def test_backfill_creates_building_records(
    mock_repo_query,
    mock_save,
    mock_gen_id,
):
    """3 records across 2 buildings -> 2 buildings created, 3 records linked."""
    # Setup: 3 acm_records, 2 unique building_ids
    records = [
        _make_acm_record_dict(record_id="acm_record:001", building_id="B01"),
        _make_acm_record_dict(record_id="acm_record:002", building_id="B01"),
        _make_acm_record_dict(
            record_id="acm_record:003",
            building_id="B02",
            building_name="Annex",
        ),
    ]

    # repo_query side effects:
    # 1. Fetch acm_records for source
    # 2. _find_existing_building for B01 -> not found
    # 3. UPDATE acm_record:001 FK
    # 4. UPDATE acm_record:002 FK
    # 5. _find_existing_building for B02 -> not found
    # 6. UPDATE acm_record:003 FK
    mock_repo_query.side_effect = [
        records,  # SELECT * FROM acm_record WHERE source_id = ...
        [],  # _find_existing_building for B01 -> none
        [],  # UPDATE acm_record:001
        [],  # UPDATE acm_record:002
        [],  # _find_existing_building for B02 -> none
        [],  # UPDATE acm_record:003
    ]

    mock_gen_id.side_effect = ["BLD#ABCDEF_001", "BLD#ABCDEF_002"]

    # Make save() set an id on the instance
    async def _fake_save(self_or_none=None):
        pass

    mock_save.side_effect = _fake_save

    # Patch BuildingRecord constructor to track created instances
    with patch(
        "scripts.v3_building_backfill.BuildingRecord",
        wraps=None,
    ) as mock_br_class:
        # We need the real BuildingRecord for construction but mock save/generate
        from open_notebook.domain.acm import BuildingRecord as RealBR

        # Create mock instances that have an .id attribute
        mock_instance_1 = MagicMock()
        mock_instance_1.id = "building_record:gen001"
        mock_instance_1.save = AsyncMock()

        mock_instance_2 = MagicMock()
        mock_instance_2.id = "building_record:gen002"
        mock_instance_2.save = AsyncMock()

        mock_br_class.side_effect = [mock_instance_1, mock_instance_2]
        mock_br_class.generate_internal_id = mock_gen_id

        result = await backfill_source("source:abc123")

    assert isinstance(result, BackfillResult)
    assert result.buildings_created == 2
    assert result.records_linked == 3
    assert result.records_already_linked == 0


# ---------------------------------------------------------------------------
# Test 2: backfill idempotent -- skips existing buildings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("scripts.v3_building_backfill.repo_query", new_callable=AsyncMock)
async def test_backfill_idempotent_skips_existing(mock_repo_query):
    """Existing building -> skipped, FK still updated for NULL records."""
    records = [
        _make_acm_record_dict(record_id="acm_record:001", building_id="B01"),
        _make_acm_record_dict(
            record_id="acm_record:002",
            building_id="B01",
            building_record_id="building_record:existing",
        ),
    ]

    mock_repo_query.side_effect = [
        records,  # SELECT * FROM acm_record
        # _find_existing_building -> found
        [{"id": "building_record:existing"}],
        # UPDATE acm_record:001 (no FK yet)
        [],
        # acm_record:002 already has FK -> skipped in code, no query
    ]

    result = await backfill_source("source:abc123")

    assert result.buildings_created == 0
    assert result.buildings_skipped == 1
    assert result.records_linked == 1
    assert result.records_already_linked == 1


# ---------------------------------------------------------------------------
# Test 3: backfill skips V3 sources (all records already linked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("scripts.v3_building_backfill.repo_query", new_callable=AsyncMock)
async def test_backfill_skips_v3_sources(mock_repo_query):
    """All records have building_record_id -> 0 created, all already_linked."""
    records = [
        _make_acm_record_dict(
            record_id="acm_record:001",
            building_id="B01",
            building_record_id="building_record:bld001",
        ),
        _make_acm_record_dict(
            record_id="acm_record:002",
            building_id="B01",
            building_record_id="building_record:bld001",
        ),
    ]

    mock_repo_query.side_effect = [
        records,  # SELECT * FROM acm_record
        # _find_existing_building -> found
        [{"id": "building_record:bld001"}],
        # No UPDATE calls -- both already have FK
    ]

    result = await backfill_source("source:abc123")

    assert result.buildings_created == 0
    assert result.buildings_skipped == 1
    assert result.records_linked == 0
    assert result.records_already_linked == 2


# ---------------------------------------------------------------------------
# Test 4: backfill dry_run -- no save() or UPDATE calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("scripts.v3_building_backfill.repo_query", new_callable=AsyncMock)
async def test_backfill_dry_run(mock_repo_query):
    """Dry-run mode: counts only, no save() or UPDATE calls."""
    records = [
        _make_acm_record_dict(record_id="acm_record:001", building_id="B01"),
        _make_acm_record_dict(record_id="acm_record:002", building_id="B02"),
    ]

    mock_repo_query.side_effect = [
        records,  # SELECT * FROM acm_record
        [],  # _find_existing_building for B01 -> none
        [],  # _find_existing_building for B02 -> none
    ]

    result = await backfill_source("source:abc123", dry_run=True)

    assert result.buildings_created == 2
    assert result.records_linked == 2

    # Verify no UPDATE or save calls happened beyond the SELECTs
    # The mock should have been called exactly 3 times (1 SELECT + 2 find_existing)
    assert mock_repo_query.call_count == 3


# ---------------------------------------------------------------------------
# Test 5: API endpoint
# ---------------------------------------------------------------------------


@patch("api.routers.acm.BackfillBuildingsRequest", autospec=True)
def test_backfill_api_endpoint(mock_req_class, client):
    """POST /api/acm/backfill-buildings returns 200 + correct JSON shape."""
    mock_result = BackfillResult(
        sources_processed=1,
        buildings_created=3,
        buildings_skipped=1,
        records_linked=10,
        records_already_linked=2,
    )

    with patch(
        "scripts.v3_building_backfill.backfill_all",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock_backfill_all:
        response = client.post("/api/acm/backfill-buildings", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["buildings_created"] == 3
    assert data["buildings_skipped"] == 1
    assert data["records_linked"] == 10
    assert "message" in data
    assert "3 buildings created" in data["message"]


# ---------------------------------------------------------------------------
# Test 6: rollback deletes and unlinks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("scripts.v3_building_rollback.repo_query", new_callable=AsyncMock)
async def test_rollback_deletes_and_unlinks(mock_repo_query):
    """Rollback: verify DELETE + UPDATE NONE queries are issued."""
    mock_repo_query.side_effect = [
        # Fetch building_records for source
        [
            {"id": "building_record:bld001"},
            {"id": "building_record:bld002"},
        ],
        # Count linked acm_records for bld001
        [{"total": 3}],
        # UPDATE acm_record SET building_record_id = NONE for bld001
        [],
        # DELETE building_record bld001
        [],
        # Count linked acm_records for bld002
        [{"total": 2}],
        # UPDATE acm_record SET building_record_id = NONE for bld002
        [],
        # DELETE building_record bld002
        [],
    ]

    result = await rollback_source("source:abc123")

    assert isinstance(result, RollbackResult)
    assert result.buildings_deleted == 2
    assert result.records_unlinked == 5

    # Verify the DELETE queries were issued
    delete_calls = [
        call
        for call in mock_repo_query.call_args_list
        if "DELETE building_record" in str(call)
    ]
    assert len(delete_calls) == 2

    # Verify the UPDATE NONE queries were issued
    unlink_calls = [
        call
        for call in mock_repo_query.call_args_list
        if "building_record_id = NONE" in str(call)
    ]
    assert len(unlink_calls) == 2
