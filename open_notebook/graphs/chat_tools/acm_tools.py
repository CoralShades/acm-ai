"""ACM structured data tools for LangGraph chat agents.

These tools enable chat agents to query structured ACM (Asbestos Containing
Material) records from SurrealDB. Each tool returns formatted results with
record IDs suitable for citation in chat responses.

All tools are async — they run in the same async context as the LangGraph
graph nodes, ensuring contextvars (source_id scoping) propagate correctly.
"""

import json
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.graphs.tool_context import get_tool_scope, set_tool_scope


def set_tool_context(
    source_id: Optional[str] = None, notebook_id: Optional[str] = None
):
    """Set the scope context for tools. Called by the agent graph before tool execution."""
    set_tool_scope(source_id=source_id, notebook_id=notebook_id)


def _get_scope():
    """Get current source_id and notebook_id from tool context."""
    return get_tool_scope()


def _format_record_summary(record: dict) -> dict:
    """Format an ACM record into a compact summary for tool output."""
    record_id = record.get("id", "unknown")
    return {
        "record_id": str(record_id),
        "building": record.get("building_name") or record.get("building_id") or "-",
        "room": record.get("room_name") or record.get("room_id") or "-",
        "product": record.get("product") or "-",
        "material": (record.get("material_description") or "-")[:50],
        "risk_status": record.get("risk_status") or "-",
        "result": record.get("result") or "-",
        "condition": record.get("material_condition") or "-",
        "friable": record.get("friable") or "-",
        "page": record.get("page_number"),
    }


def _build_source_filter(source_id: Optional[str], notebook_id: Optional[str]) -> str:
    """Build a SurrealQL WHERE clause for source/notebook scoping."""
    if source_id:
        return "source_id = $source_id"
    elif notebook_id:
        return "source_id IN (SELECT out FROM reference WHERE in = $notebook_id)"
    return "true"


def _build_vars(source_id: Optional[str], notebook_id: Optional[str], **extra) -> dict:
    """Build query variables with proper record ID formatting."""
    vars_ = {}
    if source_id:
        vars_["source_id"] = ensure_record_id(source_id)
    if notebook_id:
        vars_["notebook_id"] = ensure_record_id(notebook_id)
    vars_.update(extra)
    return vars_


@tool
async def search_acm_by_risk(risk_status: str, limit: int = 20) -> str:
    """Search ACM records by risk level (High, Medium, or Low).

    Use this tool when the user asks about risk levels, dangerous materials,
    safety concerns, or high/medium/low risk items.

    Args:
        risk_status: Risk level to filter by - must be "High", "Medium", or "Low"
        limit: Maximum number of records to return (default 20)
    """
    source_id, notebook_id = _get_scope()

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)
        query = f"""
            SELECT * FROM acm_record
            WHERE {filter_clause} AND risk_status = $risk_status
            ORDER BY building_id, room_id
            LIMIT $limit
        """
        vars_ = _build_vars(
            source_id, notebook_id, risk_status=risk_status, limit=limit
        )
        records = await repo_query(query, vars_)
        summaries = [_format_record_summary(r) for r in records]

        # Also get total count
        count_query = f"""
            SELECT count() as total FROM acm_record
            WHERE {filter_clause} AND risk_status = $risk_status
            GROUP ALL
        """
        count_vars = _build_vars(source_id, notebook_id, risk_status=risk_status)
        count_result = await repo_query(count_query, count_vars)
        total = count_result[0].get("total", 0) if count_result else 0

        return json.dumps(
            {
                "tool": "search_acm_by_risk",
                "risk_status": risk_status,
                "records": summaries,
                "showing": len(summaries),
                "total": total,
            }
        )
    except Exception as e:
        logger.error(f"search_acm_by_risk error: {e}")
        return json.dumps({"error": str(e), "records": []})


@tool
async def search_acm_by_building(building_name: str, limit: int = 20) -> str:
    """Search ACM records by building name.

    Use this tool when the user asks about a specific building, wing, or block.
    Searches by building_name using case-insensitive partial matching.

    Args:
        building_name: Building name or partial name to search for
        limit: Maximum number of records to return (default 20)
    """
    source_id, notebook_id = _get_scope()

    if not building_name or not building_name.strip():
        return json.dumps(
            {
                "error": "building_name is required. Provide a building name to search for.",
                "records": [],
            }
        )

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)
        query = f"""
            SELECT * FROM acm_record
            WHERE {filter_clause}
            AND (
                (building_name IS NOT NONE AND string::lowercase(building_name) CONTAINS string::lowercase($building_name))
                OR (building_id IS NOT NONE AND string::lowercase(building_id) CONTAINS string::lowercase($building_name))
            )
            ORDER BY room_id
            LIMIT $limit
        """
        vars_ = _build_vars(
            source_id, notebook_id, building_name=building_name, limit=limit
        )
        records = await repo_query(query, vars_)
        summaries = [_format_record_summary(r) for r in records]
        return json.dumps(
            {
                "tool": "search_acm_by_building",
                "building_name": building_name,
                "records": summaries,
                "showing": len(summaries),
            }
        )
    except Exception as e:
        logger.error(f"search_acm_by_building error: {e}")
        return json.dumps({"error": str(e), "records": []})


@tool
async def search_acm_by_room(
    room_name: str, building_name: Optional[str] = None, limit: int = 20
) -> str:
    """Search ACM records by room name, optionally within a specific building.

    Use this tool when the user asks about a specific room, classroom, office,
    or area within a building.

    Args:
        room_name: Room name or partial name to search for
        building_name: Optional building name to narrow search
        limit: Maximum number of records to return (default 20)
    """
    source_id, notebook_id = _get_scope()

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)
        building_filter = ""
        if building_name:
            building_filter = "AND building_name IS NOT NONE AND string::lowercase(building_name) CONTAINS string::lowercase($building_name)"

        query = f"""
            SELECT * FROM acm_record
            WHERE {filter_clause}
            AND (
                (room_name IS NOT NONE AND string::lowercase(room_name) CONTAINS string::lowercase($room_name))
                OR (room_id IS NOT NONE AND string::lowercase(room_id) CONTAINS string::lowercase($room_name))
            )
            {building_filter}
            ORDER BY building_id, room_id
            LIMIT $limit
        """
        vars_ = _build_vars(source_id, notebook_id, room_name=room_name, limit=limit)
        if building_name:
            vars_["building_name"] = building_name
        records = await repo_query(query, vars_)
        summaries = [_format_record_summary(r) for r in records]
        return json.dumps(
            {
                "tool": "search_acm_by_room",
                "room_name": room_name,
                "building_name": building_name,
                "records": summaries,
                "showing": len(summaries),
            }
        )
    except Exception as e:
        logger.error(f"search_acm_by_room error: {e}")
        return json.dumps({"error": str(e), "records": []})


@tool
async def search_acm_by_material(material_keyword: str, limit: int = 20) -> str:
    """Search ACM records by material type or product description.

    Use this tool when the user asks about specific materials like asbestos,
    vinyl, cement, insulation, floor tiles, pipe lagging, etc.

    Args:
        material_keyword: Material keyword to search for (e.g. "vinyl", "cement", "insulation")
        limit: Maximum number of records to return (default 20)
    """
    source_id, notebook_id = _get_scope()

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)
        query = f"""
            SELECT * FROM acm_record
            WHERE {filter_clause}
            AND (
                (product IS NOT NONE AND string::lowercase(product) CONTAINS string::lowercase($keyword))
                OR (material_description IS NOT NONE AND string::lowercase(material_description) CONTAINS string::lowercase($keyword))
            )
            ORDER BY building_id, room_id
            LIMIT $limit
        """
        vars_ = _build_vars(
            source_id, notebook_id, keyword=material_keyword, limit=limit
        )
        records = await repo_query(query, vars_)
        summaries = [_format_record_summary(r) for r in records]
        return json.dumps(
            {
                "tool": "search_acm_by_material",
                "material_keyword": material_keyword,
                "records": summaries,
                "showing": len(summaries),
            }
        )
    except Exception as e:
        logger.error(f"search_acm_by_material error: {e}")
        return json.dumps({"error": str(e), "records": []})


@tool
async def get_acm_stats() -> str:
    """Get summary statistics for ACM records.

    Use this tool when the user asks for an overview, summary, totals,
    counts, or general statistics about ACM data.

    Returns total records, risk level counts, building count, and room count.
    """
    source_id, notebook_id = _get_scope()

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)
        query = f"""
            SELECT
                count() as total_records,
                count(risk_status = 'High' OR NULL) as high_risk,
                count(risk_status = 'Medium' OR NULL) as medium_risk,
                count(risk_status = 'Low' OR NULL) as low_risk,
                array::distinct(building_name) as buildings,
                array::distinct(room_name) as rooms
            FROM acm_record
            WHERE {filter_clause}
            GROUP ALL
        """
        vars_ = _build_vars(source_id, notebook_id)
        result = await repo_query(query, vars_)

        if result:
            stats = result[0]
            buildings = [b for b in (stats.get("buildings") or []) if b]
            rooms = [r for r in (stats.get("rooms") or []) if r]
            return json.dumps(
                {
                    "tool": "get_acm_stats",
                    "total_records": stats.get("total_records", 0),
                    "high_risk": stats.get("high_risk", 0),
                    "medium_risk": stats.get("medium_risk", 0),
                    "low_risk": stats.get("low_risk", 0),
                    "building_count": len(buildings),
                    "buildings": buildings[:20],
                    "room_count": len(rooms),
                }
            )
        return json.dumps({"tool": "get_acm_stats", "total_records": 0})
    except Exception as e:
        logger.error(f"get_acm_stats error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_acm_record_detail(record_id: str) -> str:
    """Get full details of a specific ACM record by its ID.

    Use this tool when you need complete information about a specific record,
    including all fields like recommendations, sample results, classification, etc.

    Args:
        record_id: The ACM record ID (e.g. "acm_record:abc123")
    """
    try:
        query = "SELECT * FROM $record_id"
        result = await repo_query(query, {"record_id": ensure_record_id(record_id)})

        if not result:
            return json.dumps({"error": f"Record {record_id} not found"})

        record = result[0]
        # Return all non-null, non-embedding fields
        detail = {}
        skip_fields = {
            "embedding",
            "embedding_text",
            "embedding_model",
            "embedded_at",
            "enriched_text",
        }
        for key, value in record.items():
            if key not in skip_fields and value is not None:
                detail[key] = (
                    str(value)
                    if not isinstance(value, (str, int, float, bool, list))
                    else value
                )

        return json.dumps(
            {
                "tool": "get_acm_record_detail",
                "record_id": str(record_id),
                "record": detail,
            }
        )
    except Exception as e:
        logger.error(f"get_acm_record_detail error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def list_acm_buildings(limit: int = 50) -> str:
    """List all buildings in the current job with record counts and risk summary.

    Use this tool when the user asks for a list of buildings, building overview,
    or wants to know what buildings are in the document.

    Args:
        limit: Maximum number of buildings to return (default 50)
    """
    source_id, notebook_id = _get_scope()

    try:
        filter_clause = _build_source_filter(source_id, notebook_id)

        # Get building records if they exist
        building_query = f"""
            SELECT
                id, internal_id, building_name, building_address, suburb,
                building_type, building_year, number_of_levels, site_name
            FROM building_record
            WHERE {filter_clause.replace("source_id", "source_id")}
            LIMIT $limit
        """
        vars_ = _build_vars(source_id, notebook_id, limit=limit)
        buildings = await repo_query(building_query, vars_)

        # Get per-building record counts and risk stats from acm_record
        stats_query = f"""
            SELECT
                building_name,
                count() as record_count,
                count(risk_status = 'High' OR NULL) as high_risk,
                count(risk_status = 'Medium' OR NULL) as medium_risk,
                count(risk_status = 'Low' OR NULL) as low_risk
            FROM acm_record
            WHERE {filter_clause}
            GROUP BY building_name
        """
        stats_vars = _build_vars(source_id, notebook_id)
        stats = await repo_query(stats_query, stats_vars)

        # Build stats lookup
        stats_by_name = {}
        for s in stats:
            name = s.get("building_name", "")
            if name:
                stats_by_name[name] = s

        result_buildings = []
        if buildings:
            for b in buildings:
                name = b.get("building_name", "")
                s = stats_by_name.get(name, {})
                result_buildings.append(
                    {
                        "building_id": str(b.get("id", "")),
                        "internal_id": b.get("internal_id", ""),
                        "building_name": name,
                        "address": b.get("building_address", ""),
                        "suburb": b.get("suburb", ""),
                        "building_type": b.get("building_type", ""),
                        "building_year": b.get("building_year", ""),
                        "number_of_levels": b.get("number_of_levels"),
                        "site_name": b.get("site_name", ""),
                        "record_count": s.get("record_count", 0),
                        "high_risk_count": s.get("high_risk", 0),
                        "medium_risk_count": s.get("medium_risk", 0),
                        "low_risk_count": s.get("low_risk", 0),
                    }
                )
        else:
            # Fallback: derive buildings from acm_record if no building_record rows
            for name, s in stats_by_name.items():
                result_buildings.append(
                    {
                        "building_name": name,
                        "record_count": s.get("record_count", 0),
                        "high_risk_count": s.get("high_risk", 0),
                        "medium_risk_count": s.get("medium_risk", 0),
                        "low_risk_count": s.get("low_risk", 0),
                    }
                )

        return json.dumps(
            {
                "tool": "list_acm_buildings",
                "buildings": result_buildings,
                "total_buildings": len(result_buildings),
            }
        )
    except Exception as e:
        logger.error(f"list_acm_buildings error: {e}")
        return json.dumps({"error": str(e), "buildings": []})


@tool
async def get_source_metadata() -> str:
    """Get metadata about the current document/source and its extraction.

    Use this tool when the user asks about the document itself: who created it,
    when it was uploaded, how many pages, what consultant did the survey, etc.

    Returns source info, intelligence data (consultant, site, building names),
    and extraction statistics.
    """
    source_id, notebook_id = _get_scope()

    if not source_id:
        return json.dumps({"error": "No source context set."})

    try:
        sid = ensure_record_id(source_id)

        # Get source record
        source_result = await repo_query(
            "SELECT name, page_count, total_pages, state, asset_type, created, updated "
            "FROM source WHERE id = $sid LIMIT 1",
            {"sid": sid},
        )

        # Get intelligence record
        intel_result = await repo_query(
            "SELECT consultant, site_name, site_address, building_names, "
            "document_type, estimated_buildings, estimated_pages, metadata_json "
            "FROM source_intelligence WHERE source_id = $sid LIMIT 1",
            {"sid": sid},
        )

        # Get extraction stats
        stats_result = await repo_query(
            "SELECT count() as total_records FROM acm_record "
            "WHERE source_id = $sid GROUP ALL",
            {"sid": sid},
        )

        building_count_result = await repo_query(
            "SELECT count() as total FROM building_record "
            "WHERE source_id = $sid GROUP ALL",
            {"sid": sid},
        )

        source_data = source_result[0] if source_result else {}
        intel_data = intel_result[0] if intel_result else {}
        total_records = stats_result[0].get("total_records", 0) if stats_result else 0
        total_buildings = (
            building_count_result[0].get("total", 0) if building_count_result else 0
        )

        # Clean up RecordID objects
        for key, val in source_data.items():
            if not isinstance(val, (str, int, float, bool, list, type(None))):
                source_data[key] = str(val)
        for key, val in intel_data.items():
            if not isinstance(val, (str, int, float, bool, list, type(None))):
                intel_data[key] = str(val)

        return json.dumps(
            {
                "tool": "get_source_metadata",
                "source": source_data,
                "intelligence": intel_data,
                "extraction_stats": {
                    "total_records": total_records,
                    "total_buildings": total_buildings,
                },
            }
        )
    except Exception as e:
        logger.error(f"get_source_metadata error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def semantic_search_acm(query: str, limit: int = 10) -> str:
    """Search ACM records using semantic similarity (vector search).

    Use this tool for natural language searches that don't fit exact field
    filters, such as "materials near electrical panels" or "damaged ceiling products".

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)
    """
    source_id, notebook_id = _get_scope()

    try:
        # Get embedding for the query
        from open_notebook.domain.models import model_manager

        embedding_model = await model_manager.get_embedding_model()
        if not embedding_model:
            return json.dumps(
                {
                    "error": "No embedding model configured. Semantic search unavailable.",
                    "records": [],
                }
            )
        # Esperanto embedding models may use embed_query() or embed()
        if hasattr(embedding_model, "embed_query"):
            query_embedding = embedding_model.embed_query(query)
        elif hasattr(embedding_model, "embed"):
            query_embedding = embedding_model.embed(query)
        elif hasattr(embedding_model, "embed_documents"):
            query_embedding = embedding_model.embed_documents([query])[0]
        else:
            return json.dumps(
                {
                    "error": f"Embedding model {type(embedding_model).__name__} has no embed method.",
                    "records": [],
                }
            )

        filter_clause = _build_source_filter(source_id, notebook_id)
        surql = f"""
            SELECT
                *,
                vector::similarity::cosine(embedding, $query_embedding) as similarity
            FROM acm_record
            WHERE {filter_clause}
            AND embedding IS NOT NONE
            AND vector::similarity::cosine(embedding, $query_embedding) >= 0.3
            ORDER BY similarity DESC
            LIMIT $limit
        """
        vars_ = _build_vars(
            source_id,
            notebook_id,
            query_embedding=query_embedding,
            limit=limit,
        )
        records = await repo_query(surql, vars_)

        summaries = []
        for r in records:
            summary = _format_record_summary(r)
            summary["similarity"] = round(r.get("similarity", 0), 3)
            summaries.append(summary)

        return json.dumps(
            {
                "tool": "semantic_search_acm",
                "query": query,
                "records": summaries,
                "showing": len(summaries),
            }
        )
    except Exception as e:
        logger.error(f"semantic_search_acm error: {e}")
        return json.dumps({"error": str(e), "records": []})
