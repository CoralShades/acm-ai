"""Knowledge Graph API Router (E13-S2)

Provides graph data endpoints for React Flow visualization.
Returns nodes and edges in React Flow compatible format.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import repo_query

router = APIRouter()


# --- Response Models ---


class GraphNode(BaseModel):
    """React Flow compatible node."""

    id: str
    type: str  # school, building, room, acm
    position: Dict[str, float]  # {x, y}
    data: Dict[str, Any]


class GraphEdge(BaseModel):
    """React Flow compatible edge."""

    id: str
    source: str
    target: str
    type: str = "default"


class GraphResponse(BaseModel):
    """Full graph data for React Flow."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphStatsResponse(BaseModel):
    """Graph statistics summary."""

    school_count: int
    building_count: int
    room_count: int
    acm_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int


# --- Layout Helpers ---

# Simple hierarchical layout (top-down)
LEVEL_Y = {"school": 0, "building": 200, "room": 400, "acm": 600}
NODE_X_SPACING = 250
NODE_Y_SPACING = 200


def _build_graph_from_records(
    records: List[Dict[str, Any]],
    risk_filter: Optional[str] = None,
) -> GraphResponse:
    """Build React Flow graph from ACM records."""
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    edge_set: set[tuple[str, str]] = set()

    school_x: Dict[str, int] = {}
    building_x: Dict[str, int] = {}
    room_x: Dict[str, int] = {}
    acm_x_counter = 0

    for record in records:
        # Apply risk filter
        if risk_filter and record.get("risk_status", "").lower() != risk_filter.lower():
            continue

        source_id = record.get("source_id", "")
        school_name = record.get("school_name", "Unknown")
        school_code = record.get("school_code", school_name[:10])
        building_id_val = record.get("building_id", "Unknown")
        building_name = record.get("building_name", building_id_val)
        room_id_val = record.get("room_id", "")
        room_name = record.get("room_name", room_id_val or "Unknown Room")
        record_id = record.get("id", "")

        # School node
        school_node_id = f"school:{school_code}"
        if school_node_id not in nodes:
            x = len(school_x) * NODE_X_SPACING
            school_x[school_node_id] = x
            nodes[school_node_id] = GraphNode(
                id=school_node_id,
                type="school",
                position={"x": x, "y": LEVEL_Y["school"]},
                data={
                    "label": school_name,
                    "school_code": school_code,
                    "source_id": source_id,
                },
            )

        # Building node
        bld_node_id = f"building:{school_code}:{building_id_val}"
        if bld_node_id not in nodes:
            x = len(building_x) * NODE_X_SPACING
            building_x[bld_node_id] = x
            nodes[bld_node_id] = GraphNode(
                id=bld_node_id,
                type="building",
                position={"x": x, "y": LEVEL_Y["building"]},
                data={
                    "label": building_name,
                    "building_code": building_id_val,
                    "year": record.get("building_year"),
                    "construction": record.get("building_construction"),
                },
            )
            edge_pair = (school_node_id, bld_node_id)
            if edge_pair not in edge_set:
                edge_set.add(edge_pair)

        # Room node
        room_key = room_id_val or room_name
        room_node_id = f"room:{school_code}:{building_id_val}:{room_key}"
        if room_node_id not in nodes:
            x = len(room_x) * NODE_X_SPACING
            room_x[room_node_id] = x
            nodes[room_node_id] = GraphNode(
                id=room_node_id,
                type="room",
                position={"x": x, "y": LEVEL_Y["room"]},
                data={
                    "label": room_name,
                    "room_id": room_id_val,
                    "area": record.get("room_area"),
                    "floor_level": record.get("floor_level"),
                },
            )
            edge_pair = (bld_node_id, room_node_id)
            if edge_pair not in edge_set:
                edge_set.add(edge_pair)

        # ACM node
        acm_node_id = f"acm:{record_id}"
        if acm_node_id not in nodes:
            x = acm_x_counter * NODE_X_SPACING
            acm_x_counter += 1
            risk = record.get("risk_status", "").lower()
            nodes[acm_node_id] = GraphNode(
                id=acm_node_id,
                type="acm",
                position={"x": x, "y": LEVEL_Y["acm"]},
                data={
                    "label": record.get("product", "Unknown"),
                    "material": record.get("material_description", ""),
                    "result": record.get("result", ""),
                    "risk_status": record.get("risk_status"),
                    "friable": record.get("friable"),
                    "condition": record.get("material_condition"),
                    "risk_color": (
                        "#ef4444"
                        if risk == "high"
                        else "#eab308"
                        if risk == "medium"
                        else "#22c55e"
                    ),
                },
            )
            edge_pair = (room_node_id, acm_node_id)
            if edge_pair not in edge_set:
                edge_set.add(edge_pair)

    # Build edges list
    graph_edges = []
    for source, target in edge_set:
        graph_edges.append(
            GraphEdge(id=f"{source}|{target}", source=source, target=target)
        )

    return GraphResponse(nodes=list(nodes.values()), edges=graph_edges)


# --- Endpoints ---


@router.get("/graph/source/{source_id}", response_model=GraphResponse)
async def get_source_graph(
    source_id: str,
    risk_filter: Optional[str] = Query(None, description="Filter by risk level"),
):
    """Get full knowledge graph for a source document."""
    try:
        records = await repo_query(
            "SELECT * FROM acm_record WHERE source_id = $source_id",
            {"source_id": source_id},
        )
        return _build_graph_from_records(records or [], risk_filter)
    except Exception as e:
        logger.error(f"Error building source graph: {e}")
        raise HTTPException(status_code=500, detail="Error building source graph")


@router.get("/graph/school/{school_code}", response_model=GraphResponse)
async def get_school_graph(
    school_code: str,
    risk_filter: Optional[str] = Query(None, description="Filter by risk level"),
):
    """Get school-centric knowledge graph."""
    try:
        records = await repo_query(
            "SELECT * FROM acm_record WHERE school_code = $code",
            {"code": school_code},
        )
        return _build_graph_from_records(records or [], risk_filter)
    except Exception as e:
        logger.error(f"Error building school graph: {e}")
        raise HTTPException(status_code=500, detail="Error building school graph")


@router.get("/graph/building/{building_id}", response_model=GraphResponse)
async def get_building_graph(
    building_id: str,
    risk_filter: Optional[str] = Query(None, description="Filter by risk level"),
):
    """Get building-centric knowledge graph."""
    try:
        records = await repo_query(
            "SELECT * FROM acm_record WHERE building_id = $id",
            {"id": building_id},
        )
        return _build_graph_from_records(records or [], risk_filter)
    except Exception as e:
        logger.error(f"Error building building graph: {e}")
        raise HTTPException(status_code=500, detail="Error building building graph")


@router.get("/graph/stats/{source_id}", response_model=GraphStatsResponse)
async def get_graph_stats(source_id: str):
    """Get graph statistics for a source document."""
    try:
        records = await repo_query(
            "SELECT * FROM acm_record WHERE source_id = $source_id",
            {"source_id": source_id},
        )
        if not records:
            return GraphStatsResponse(
                school_count=0,
                building_count=0,
                room_count=0,
                acm_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
            )

        schools = set()
        buildings = set()
        rooms = set()
        high = medium = low = 0

        for r in records:
            schools.add(r.get("school_code", r.get("school_name", "")))
            buildings.add(r.get("building_id", ""))
            rooms.add(f"{r.get('building_id', '')}:{r.get('room_id', '')}")
            risk = (r.get("risk_status") or "").lower()
            if risk == "high":
                high += 1
            elif risk == "medium":
                medium += 1
            elif risk == "low":
                low += 1

        return GraphStatsResponse(
            school_count=len(schools),
            building_count=len(buildings),
            room_count=len(rooms),
            acm_count=len(records),
            high_risk_count=high,
            medium_risk_count=medium,
            low_risk_count=low,
        )
    except Exception as e:
        logger.error(f"Error computing graph stats: {e}")
        raise HTTPException(status_code=500, detail="Error computing graph stats")
