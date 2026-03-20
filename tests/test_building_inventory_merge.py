"""Tests for building inventory cross-validation merge logic.

Verifies the fix for phantom building detection where LLM and heuristic
produce different IDs/names for the same building.
"""

from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    BuildingMeta,
    compile_building_inventory,
)


def _make_building(bid: str, name: str, page_start: int, page_end: int) -> BuildingMeta:
    return BuildingMeta(
        building_id=bid,
        name=name,
        page_start=page_start,
        page_end=page_end,
    )


# Content without DET-style building code headers (## B00A, ## D01)
# so the heuristic parser doesn't find additional buildings.
PLAIN_CONTENT = "--- Page 5 ---\n| Header |\n|---|\n| Data |"
PLAIN_CONTENT_MULTI = (
    "--- Page 5 ---\n| H |\n|---|\n| D |\n"
    "--- Page 19 ---\n| H |\n|---|\n| D |"
)

# Content WITH DET-style building codes — heuristic WILL detect these
CODED_CONTENT = (
    "## B001 - Admin\n--- Page 5 ---\n| H |\n|---|\n| D |\n"
    "--- Page 11 ---\n## B002 - Library\n| H |\n|---|\n| D |\n"
    "--- Page 16 ---\n## D01 - Portable Classroom\n| H |\n|---|\n| D |"
)


class TestSingleBuildingMerge:
    """Single-building documents should not produce phantom duplicates."""

    @pytest.mark.asyncio
    async def test_single_building_with_site_name_skips_merge(self):
        """When LLM returns 1 building and content has no building codes, result is 1."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=PLAIN_CONTENT,
                document_structure=None,
                model_id="test",
                document_metadata={"site_name": "Broadmeadows Police Station"},
            )

        assert result.total_buildings == 1
        assert result.buildings[0].building_id == "B001"

    @pytest.mark.asyncio
    async def test_single_building_heuristic_finds_coded_header(self):
        """When content has a building code header, heuristic detects it and merges."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        # Content with B00A header — heuristic will detect this as a second building
        coded_content = "## B00A - Broadmeadows Police Station\n--- Page 5 ---\n| H |\n|---|\n| D |"

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=coded_content,
                document_structure=None,
                model_id="test",
                document_metadata={"site_name": "Broadmeadows Police Station"},
            )

        # Heuristic parser detects B00A from content header and merges it in
        assert result.total_buildings == 2
        building_ids = {b.building_id for b in result.buildings}
        assert "B001" in building_ids
        assert "B00A" in building_ids

    @pytest.mark.asyncio
    async def test_single_building_both_sources_agree_skips_merge(self):
        """When LLM returns 1 building and no heuristic buildings found, result is 1."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=PLAIN_CONTENT,
                document_structure=None,
                model_id="test",
            )

        assert result.total_buildings == 1


class TestFuzzyNameMatching:
    """Fuzzy name matching prevents phantom buildings with different names."""

    @pytest.mark.asyncio
    async def test_substring_match_prevents_duplicate(self):
        """Heuristic building matching LLM by name substring is not duplicated."""
        llm_result = BuildingInventory(
            buildings=[
                _make_building("B001", "Police Station", 5, 18),
                _make_building("B002", "Gymnasium", 19, 22),
            ],
            processing_groups=[],
            total_buildings=2,
        )

        # No building codes in content — heuristic won't find extra buildings
        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=PLAIN_CONTENT_MULTI,
                document_structure=None,
                model_id="test",
            )

        assert result.total_buildings == 2

    @pytest.mark.asyncio
    async def test_site_name_match_prevents_duplicate(self):
        """With site_name set and no heuristic findings, LLM result stands."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=PLAIN_CONTENT,
                document_structure=None,
                model_id="test",
                document_metadata={"site_name": "Broadmeadows Police Station"},
            )

        assert result.total_buildings == 1


class TestMultiBuildingMerge:
    """Multi-building documents correctly merge genuinely different buildings."""

    @pytest.mark.asyncio
    async def test_genuine_new_building_is_added(self):
        """Heuristic building with no LLM match is added to inventory."""
        llm_result = BuildingInventory(
            buildings=[
                _make_building("B001", "Admin", 5, 10),
                _make_building("B002", "Library", 11, 15),
            ],
            processing_groups=[],
            total_buildings=2,
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=CODED_CONTENT,
                document_structure=None,
                model_id="test",
            )

        building_ids = {b.building_id for b in result.buildings}
        assert "D01" in building_ids
        assert result.total_buildings >= 3
