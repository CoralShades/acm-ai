"""Knowledge Graph Backfill Script

Idempotent backfill that creates graph entities and relations
from existing acm_record data.

Story: E13-S1 Knowledge Graph Schema
"""

import re

from loguru import logger

from open_notebook.database.repository import repo_query


def _safe_id(value: str) -> str:
    """Sanitize a value for use in a SurrealDB record ID."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", value.strip().lower())


async def backfill_knowledge_graph() -> dict:
    """Build graph entities from existing acm_record data.

    Returns dict with counts of created entities.
    """
    stats = {"schools": 0, "buildings": 0, "rooms": 0, "relations": 0}

    # Get all distinct school/building/room combos from acm_records
    records = await repo_query(
        "SELECT school_code, building_id, room_id, floor_level, source_id, id "
        "FROM acm_record WHERE building_id != NONE"
    )
    if not records:
        logger.info("No acm_record data found for backfill")
        return stats

    seen_schools: set[str] = set()
    seen_buildings: set[str] = set()
    seen_rooms: set[str] = set()

    for rec in records:
        school_code = rec.get("school_code") or "unknown"
        building_code = rec.get("building_id") or ""
        room_code = rec.get("room_id") or ""

        if not building_code:
            continue

        sch_id = _safe_id(school_code)
        bld_id = f"{sch_id}_{_safe_id(building_code)}"

        # Create school
        if sch_id not in seen_schools:
            await repo_query(
                "CREATE school SET "
                "id = $id, school_code = $code, created = time::now(), updated = time::now()",
                {"id": f"school:sch_{sch_id}", "code": school_code},
            )
            seen_schools.add(sch_id)
            stats["schools"] += 1

        # Create building
        if bld_id not in seen_buildings:
            await repo_query(
                "CREATE building SET "
                "id = $id, school_code = $scode, building_code = $bcode, "
                "created = time::now(), updated = time::now()",
                {
                    "id": f"building:bld_{bld_id}",
                    "scode": school_code,
                    "bcode": building_code,
                },
            )
            # school -> building relation
            await repo_query(
                "RELATE $from->school_has_building->$to",
                {
                    "from": f"school:sch_{sch_id}",
                    "to": f"building:bld_{bld_id}",
                },
            )
            seen_buildings.add(bld_id)
            stats["buildings"] += 1
            stats["relations"] += 1

        # Create room
        if room_code:
            rm_id = f"{bld_id}_{_safe_id(room_code)}"
            if rm_id not in seen_rooms:
                await repo_query(
                    "CREATE room SET "
                    "id = $id, school_code = $scode, building_code = $bcode, "
                    "room_code = $rcode, floor_level = $floor, "
                    "created = time::now(), updated = time::now()",
                    {
                        "id": f"room:rm_{rm_id}",
                        "scode": school_code,
                        "bcode": building_code,
                        "rcode": room_code,
                        "floor": rec.get("floor_level"),
                    },
                )
                # building -> room relation
                await repo_query(
                    "RELATE $from->building_has_room->$to",
                    {
                        "from": f"building:bld_{bld_id}",
                        "to": f"room:rm_{rm_id}",
                    },
                )
                seen_rooms.add(rm_id)
                stats["rooms"] += 1
                stats["relations"] += 1

            # room -> acm_record relation
            acm_id = rec.get("id")
            if acm_id:
                await repo_query(
                    "RELATE $from->room_has_acm->$to",
                    {"from": f"room:rm_{rm_id}", "to": acm_id},
                )
                stats["relations"] += 1

        # extracted_from relation
        source_id = rec.get("source_id")
        acm_id = rec.get("id")
        if source_id and acm_id:
            await repo_query(
                "RELATE $from->extracted_from->$to",
                {"from": acm_id, "to": source_id},
            )
            stats["relations"] += 1

    logger.info(f"Knowledge graph backfill complete: {stats}")
    return stats
