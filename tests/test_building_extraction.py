"""
Unit tests for extract_building_node (E32-S1).

All DB calls and LLM calls are mocked. Tests validate:
- Normal path: N buildings -> N BuildingRecord saves + N IDs in state
- Partial failure: middle building raises exception -> first/last still save
- Empty inventory: node returns empty list without error
- None LLM result: _v3_extract_building_meta returns None -> building skipped
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.acm import BuildingRecord
from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult
from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    BuildingMeta,
)
from open_notebook.graphs.acm_extraction import extract_building_node

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_state():
    """Minimal state dict for extract_building_node tests."""
    source = MagicMock()
    source.id = "source:test123"
    source.title = "TestDoc.pdf"
    source.full_text = "<!-- Page 1 -->\nBuilding content for B001...\n<!-- Page 6 -->\nBuilding content for B002..."
    return {
        "source": source,
        "model_id": "openai:gpt-4o-mini",
        "building_inventory": BuildingInventory(
            buildings=[
                BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
                BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            ],
            processing_groups=[],
            total_buildings=2,
        ),
        "pipeline_logger": None,
        "agui_emitter": None,
    }


def _make_extraction_result(**kwargs) -> BuildingExtractionResult:
    """Helper: create a BuildingExtractionResult with defaults."""
    defaults = {
        "building_name": "Test Building",
        "extraction_confidence": "high",
    }
    defaults.update(kwargs)
    return BuildingExtractionResult(**defaults)


def _make_fake_save(record_ids: list):
    """Create an async replacement for BuildingRecord.save() that sets self.id.

    ObjectModel.save() returns None and mutates self.id in place.
    We replicate that behavior so tests work correctly.
    """
    ids_iter = iter(record_ids)
    calls = []

    async def _save(self):
        self.id = next(ids_iter)
        calls.append(self)

    _save.calls = calls
    return _save


# ---------------------------------------------------------------------------
# Test: normal path — all buildings saved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],  # No existing buildings
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_normal_path_saves_all_buildings(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """3-building inventory -> 3 BuildingRecord saves + 3 IDs returned."""
    # Give state 3 buildings
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
            BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            BuildingMeta(building_id="B003", name="Hall", page_start=11, page_end=15),
        ],
        processing_groups=[],
        total_buildings=3,
    )
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = _make_extraction_result()
    fake_save = _make_fake_save(
        ["building_record:001", "building_record:002", "building_record:003"]
    )

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert len(result["building_records"]) == 3
    assert len(fake_save.calls) == 3
    assert mock_v3_extract.call_count == 3


# ---------------------------------------------------------------------------
# Test: partial failure — middle building raises, first and third still save
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_partial_failure_preserves_results(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """Second building raises RuntimeError -> first and third still produce records."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
            BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            BuildingMeta(building_id="B003", name="Hall", page_start=11, page_end=15),
        ],
        processing_groups=[],
        total_buildings=3,
    )
    mock_extract_content.return_value = "Some building content"
    # Second call raises an exception
    mock_v3_extract.side_effect = [
        _make_extraction_result(building_name="Main Building"),
        RuntimeError("LLM provider failure"),
        _make_extraction_result(building_name="Hall Building"),
    ]
    fake_save = _make_fake_save(["building_record:001", "building_record:003"])

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert len(result["building_records"]) == 2
    assert len(fake_save.calls) == 2


# ---------------------------------------------------------------------------
# Test: None building_inventory -> returns empty list without error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_inventory_returns_empty_list(mock_state):
    """state['building_inventory'] = None -> returns {'building_records': []}."""
    mock_state["building_inventory"] = None

    result = await extract_building_node(mock_state, config={})

    assert result == {"building_records": [], "building_meta_cache": {}}


# ---------------------------------------------------------------------------
# Test: BuildingInventory with empty buildings list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_none_inventory_buildings_returns_empty(mock_state):
    """BuildingInventory(buildings=[]) -> returns {'building_records': []}."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[],
        processing_groups=[],
        total_buildings=0,
    )

    result = await extract_building_node(mock_state, config={})

    assert result == {"building_records": [], "building_meta_cache": {}}


# ---------------------------------------------------------------------------
# Test: LLM returns None -> minimal BuildingRecord created (Bug Fix 11 Phase 3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_llm_returns_none_creates_minimal_building(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """_v3_extract_building_meta returns None -> minimal BuildingRecord saved (not skipped).

    Bug Fix 11 Phase 3: Instead of silently skipping a building when Phase 1 LLM
    fails, a minimal BuildingRecord is created using building_meta_entry fields so
    that FK linkage and frontend display still work.
    """
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = None
    fake_save = _make_fake_save(["building_record:001"])

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    # Minimal record must be saved and its ID included in the result
    assert len(result["building_records"]) == 1
    assert result["building_records"][0] == "building_record:001"
    assert len(fake_save.calls) == 1
    # meta_cache entry for this building_id should be None (no LLM result)
    assert result["building_meta_cache"].get("B001") is None


# ---------------------------------------------------------------------------
# Test: empty building content -> skipped, _v3_extract_building_meta not called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_empty_building_content_skips(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """_extract_building_content returns '' -> _v3_extract_building_meta not called."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "   "  # whitespace only

    result = await extract_building_node(mock_state, config={})

    assert result["building_records"] == []
    mock_v3_extract.assert_not_called()


# ---------------------------------------------------------------------------
# Test: returned dict has correct keys
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_state_dict_has_correct_keys(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """Returned dict always has key 'building_records' with a list value."""
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = _make_extraction_result()
    fake_save = _make_fake_save(["building_record:001", "building_record:002"])

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert isinstance(result["building_records"], list)
    assert len(result["building_records"]) == 2


# ---------------------------------------------------------------------------
# Test: F10/F1 — BuildingRecord.building_name prefers inventory name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_building_name_prefers_inventory_over_llm(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """F1/F10: BuildingRecord.building_name should use inventory name,
    not the Phase 1 LLM output which often returns the site name."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(
                building_id="B001",
                name="Administration",  # Correct name from inventory
                page_start=1,
                page_end=5,
            ),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "Some building content"
    # LLM returns the site name instead of the building name
    mock_v3_extract.return_value = _make_extraction_result(
        building_name="Aldavilla Public School"
    )
    fake_save = _make_fake_save(["building_record:001"])

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    assert len(result["building_records"]) == 1
    assert len(fake_save.calls) == 1
    # The saved record should use the inventory name, not the LLM output
    saved_record = fake_save.calls[0]
    assert saved_record.building_name == "Administration"


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
    new_callable=AsyncMock,
    return_value=[],
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_building_name_falls_back_to_llm_when_no_inventory_name(
    mock_extract_content,
    mock_v3_extract,
    mock_get_by_source,
    mock_state,
):
    """F10: When inventory has no name, fall back to LLM building_name."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(
                building_id="B001",
                name="",  # Empty inventory name
                page_start=1,
                page_end=5,
            ),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = _make_extraction_result(
        building_name="Main Building"
    )
    fake_save = _make_fake_save(["building_record:001"])

    with patch.object(BuildingRecord, "save", fake_save):
        result = await extract_building_node(mock_state, config={})

    assert len(result["building_records"]) == 1
    saved_record = fake_save.calls[0]
    assert saved_record.building_name == "Main Building"
