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


class TestSingleBuildingMerge:
    """Single-building documents should not produce phantom duplicates."""

    @pytest.mark.asyncio
    async def test_single_building_with_site_name_skips_merge(self):
        """When LLM returns 1 building and site_name is set, skip merge entirely."""
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
                content="## B00A - Broadmeadows Police Station\n--- Page 5 ---\n| Header |\n|---|\n| Data |",
                document_structure=None,
                model_id="test",
                document_metadata={"site_name": "Broadmeadows Police Station"},
            )

        assert result.total_buildings == 1
        assert result.buildings[0].building_id == "B001"

    @pytest.mark.asyncio
    async def test_single_building_both_sources_agree_skips_merge(self):
        """When LLM returns 1 building and heuristic also returns 1, skip merge."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        # Content that produces exactly 1 heuristic building
        content = "## B00A - Police Station\n--- Page 5 ---\n| H |\n|---|\n| D |"

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=content,
                document_structure=None,
                model_id="test",
            )

        assert result.total_buildings == 1


class TestFuzzyNameMatching:
    """Fuzzy name matching prevents phantom buildings with different names."""

    @pytest.mark.asyncio
    async def test_substring_match_prevents_duplicate(self):
        """Heuristic 'Broadmeadows Police Station' matches LLM 'Police Station'."""
        llm_result = BuildingInventory(
            buildings=[
                _make_building("B001", "Police Station", 5, 18),
                _make_building("B002", "Gymnasium", 19, 22),
            ],
            processing_groups=[],
            total_buildings=2,
        )

        # Heuristic will find "Broadmeadows Police Station" which is a superset
        content = (
            "## B00A - Broadmeadows Police Station\n"
            "--- Page 5 ---\n| H |\n|---|\n| D |\n"
            "--- Page 19 ---\n"
            "## B00B - Gymnasium\n| H |\n|---|\n| D |"
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=content,
                document_structure=None,
                model_id="test",
            )

        # Should NOT add a third "Broadmeadows Police Station" building
        assert result.total_buildings == 2

    @pytest.mark.asyncio
    async def test_site_name_match_prevents_duplicate(self):
        """Heuristic building matching site_name is recognized as same building."""
        llm_result = BuildingInventory(
            buildings=[_make_building("B001", "Main Building", 5, 18)],
            processing_groups=[],
            total_buildings=1,
        )

        content = (
            "## B00A - Broadmeadows Police Station\n"
            "--- Page 5 ---\n| H |\n|---|\n| D |\n"
            "--- Page 19 ---\n"
            "## D01 - Portable Classroom\n| H |\n|---|\n| D |"
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=content,
                document_structure=None,
                model_id="test",
                document_metadata={"site_name": "Broadmeadows Police Station"},
            )

        # "Broadmeadows Police Station" matches site_name → skipped
        # "Portable Classroom" is genuinely new → added
        # But single-building skip_merge kicks in (LLM=1, site_name set)
        assert result.total_buildings == 1


class TestMultiBuildingMerge:
    """Multi-building documents correctly merge genuinely different buildings."""

    @pytest.mark.asyncio
    async def test_genuine_new_building_is_added(self):
        """Heuristic building with no overlap or name match is added."""
        llm_result = BuildingInventory(
            buildings=[
                _make_building("B001", "Admin", 5, 10),
                _make_building("B002", "Library", 11, 15),
            ],
            processing_groups=[],
            total_buildings=2,
        )

        content = (
            "## B001 - Admin\n--- Page 5 ---\n| H |\n|---|\n| D |\n"
            "--- Page 11 ---\n## B002 - Library\n| H |\n|---|\n| D |\n"
            "--- Page 16 ---\n## D01 - Portable Classroom\n| H |\n|---|\n| D |"
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=llm_result,
        ):
            result = await compile_building_inventory(
                content=content,
                document_structure=None,
                model_id="test",
            )

        building_ids = {b.building_id for b in result.buildings}
        assert "D01" in building_ids
        assert result.total_buildings >= 3
