"""Knowledge Graph Backfill Script

Idempotent backfill that creates graph entities and relations
from existing acm_record data. Uses UPSERT to safely handle re-runs.

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

    Uses UPSERT for entities and deterministic relation IDs
    to ensure idempotent re-runs.

    Returns dict with counts of created/updated entities.
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

        # Upsert school
        if sch_id not in seen_schools:
            await repo_query(
                "UPSERT $id SET "
                "school_code = $code, updated = time::now(), "
                "created = created OR time::now()",
                {"id": f"school:sch_{sch_id}", "code": school_code},
            )
            seen_schools.add(sch_id)
            stats["schools"] += 1

        # Upsert building
        if bld_id not in seen_buildings:
            await repo_query(
                "UPSERT $id SET "
                "school_code = $scode, building_code = $bcode, "
                "updated = time::now(), created = created OR time::now()",
                {
                    "id": f"building:bld_{bld_id}",
                    "scode": school_code,
                    "bcode": building_code,
                },
            )
            # school -> building relation (deterministic ID)
            rel_id = f"shb_{sch_id}_{_safe_id(building_code)}"
            await repo_query(
                "UPSERT $rel_id SET "
                "in = $from, out = $to, updated = time::now(), "
                "created = created OR time::now()",
                {
                    "rel_id": f"school_has_building:{rel_id}",
                    "from": f"school:sch_{sch_id}",
                    "to": f"building:bld_{bld_id}",
                },
            )
            seen_buildings.add(bld_id)
            stats["buildings"] += 1
            stats["relations"] += 1

        # Upsert room
        if room_code:
            rm_id = f"{bld_id}_{_safe_id(room_code)}"
            if rm_id not in seen_rooms:
                await repo_query(
                    "UPSERT $id SET "
                    "school_code = $scode, building_code = $bcode, "
                    "room_code = $rcode, floor_level = $floor, "
                    "updated = time::now(), created = created OR time::now()",
                    {
                        "id": f"room:rm_{rm_id}",
                        "scode": school_code,
                        "bcode": building_code,
                        "rcode": room_code,
                        "floor": rec.get("floor_level"),
                    },
                )
                # building -> room relation (deterministic ID)
                bhr_id = f"bhr_{bld_id}_{_safe_id(room_code)}"
                await repo_query(
                    "UPSERT $rel_id SET "
                    "in = $from, out = $to, updated = time::now(), "
                    "created = created OR time::now()",
                    {
                        "rel_id": f"building_has_room:{bhr_id}",
                        "from": f"building:bld_{bld_id}",
                        "to": f"room:rm_{rm_id}",
                    },
                )
                seen_rooms.add(rm_id)
                stats["rooms"] += 1
                stats["relations"] += 1

            # room -> acm_record relation (deterministic ID from acm_id)
            acm_id = rec.get("id")
            if acm_id:
                # Extract the record part of the acm_id for a deterministic relation ID
                acm_short = str(acm_id).replace(":", "_")
                rha_id = f"rha_{rm_id}_{acm_short}"
                await repo_query(
                    "UPSERT $rel_id SET "
                    "in = $from, out = $to, updated = time::now(), "
                    "created = created OR time::now()",
                    {
                        "rel_id": f"room_has_acm:{rha_id}",
                        "from": f"room:rm_{rm_id}",
                        "to": acm_id,
                    },
                )
                stats["relations"] += 1

        # extracted_from relation (deterministic ID from acm_id)
        source_id = rec.get("source_id")
        acm_id = rec.get("id")
        if source_id and acm_id:
            acm_short = str(acm_id).replace(":", "_")
            ef_id = f"ef_{acm_short}"
            await repo_query(
                "UPSERT $rel_id SET "
                "in = $from, out = $to, updated = time::now(), "
                "created = created OR time::now()",
                {
                    "rel_id": f"extracted_from:{ef_id}",
                    "from": acm_id,
                    "to": source_id,
                },
            )
            stats["relations"] += 1

    logger.info(f"Knowledge graph backfill complete: {stats}")
    return stats
