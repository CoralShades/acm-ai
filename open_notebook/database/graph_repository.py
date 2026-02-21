"""Knowledge Graph Repository

CRUD operations for graph entity tables.

Story: E13-S1 Knowledge Graph Schema
"""

from typing import Optional

from open_notebook.database.repository import repo_query
from open_notebook.domain.graph_entities import Building, Room, School


async def get_schools() -> list[School]:
    """Get all schools."""
    results = await repo_query("SELECT * FROM school ORDER BY school_code")
    return [School.model_validate(r) for r in results]


async def get_school_by_code(school_code: str) -> Optional[School]:
    """Get a school by its code."""
    results = await repo_query(
        "SELECT * FROM school WHERE school_code = $code LIMIT 1",
        {"code": school_code},
    )
    return School.model_validate(results[0]) if results else None


async def get_buildings_for_school(school_code: str) -> list[Building]:
    """Get all buildings for a school."""
    results = await repo_query(
        "SELECT * FROM building WHERE school_code = $code ORDER BY building_code",
        {"code": school_code},
    )
    return [Building.model_validate(r) for r in results]


async def get_rooms_for_building(
    school_code: str, building_code: str
) -> list[Room]:
    """Get all rooms for a building."""
    results = await repo_query(
        "SELECT * FROM room WHERE school_code = $scode AND building_code = $bcode ORDER BY room_code",
        {"scode": school_code, "bcode": building_code},
    )
    return [Room.model_validate(r) for r in results]


async def get_graph_stats() -> dict:
    """Get counts of graph entities."""
    schools = await repo_query("SELECT count() FROM school GROUP ALL")
    buildings = await repo_query("SELECT count() FROM building GROUP ALL")
    rooms = await repo_query("SELECT count() FROM room GROUP ALL")
    return {
        "schools": schools[0].get("count", 0) if schools else 0,
        "buildings": buildings[0].get("count", 0) if buildings else 0,
        "rooms": rooms[0].get("count", 0) if rooms else 0,
    }
