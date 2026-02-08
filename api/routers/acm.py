"""
ACM (Asbestos Containing Material) API Endpoints

Provides REST API for ACM record management including
listing, filtering, extraction, and export.
"""

import csv
import io
import math
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from api.command_service import CommandService
from api.models import (
    ACMExtractRequest,
    ACMExtractResponse,
    ACMRecordCreateRequest,
    ACMRecordListResponse,
    ACMRecordResponse,
    ACMRecordUpdateRequest,
    ACMSearchResponse,
    ACMSearchResultResponse,
    ACMStatsResponse,
    AgencyListResponse,
    ApplyTemplateRequest,
    BatchClassifyRequest,
    BatchClassifyResponse,
    ClassifyRequest,
    ClassifyResponse,
    NormalizeRequest,
    NormalizeResponse,
    SiteConfigRequest,
    SiteConfigResponse,
    SiteConfigTemplateResponse,
    TaxonomyGroupResponse,
    TaxonomyResponse,
)
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.acm import ACMRecord
from open_notebook.domain.site_config import SiteConfig

router = APIRouter()


@router.get("/records", response_model=ACMRecordListResponse)
async def list_acm_records(
    source_id: str = Query(..., description="Source ID to filter by (required)"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    risk_status: Optional[str] = Query(
        None, description="Filter by risk status (Low/Medium/High)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Records per page"),
):
    """
    List ACM records with filtering and pagination.

    Returns records for the specified source, with optional filtering
    by building, room, and risk status.
    """
    try:
        # Build query conditions
        conditions = ["source_id = $source_id"]
        params: dict = {"source_id": ensure_record_id(source_id)}

        if building_id:
            conditions.append("building_id = $building_id")
            params["building_id"] = building_id

        if room_id:
            conditions.append("room_id = $room_id")
            params["room_id"] = room_id

        if risk_status:
            conditions.append("risk_status = $risk_status")
            params["risk_status"] = risk_status

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = (
            f"SELECT count() as total FROM acm_record WHERE {where_clause} GROUP ALL"
        )
        count_result = await repo_query(count_query, params)
        total = count_result[0]["total"] if count_result else 0

        # Calculate pagination
        offset = (page - 1) * limit
        pages = math.ceil(total / limit) if total > 0 else 1

        # Get paginated records
        data_query = f"""
            SELECT * FROM acm_record
            WHERE {where_clause}
            ORDER BY building_id, room_id, id
            LIMIT $limit START $offset
        """
        params["limit"] = limit
        params["offset"] = offset

        records = await repo_query(data_query, params)

        # Convert to response models
        record_responses = []
        for r in records:
            record_responses.append(
                ACMRecordResponse(
                    id=str(r.get("id", "")),
                    source_id=str(r.get("source_id", "")),
                    school_name=r.get("school_name", ""),
                    school_code=r.get("school_code"),
                    building_id=r.get("building_id", ""),
                    building_name=r.get("building_name"),
                    building_year=r.get("building_year"),
                    building_construction=r.get("building_construction"),
                    room_id=r.get("room_id"),
                    room_name=r.get("room_name"),
                    room_area=r.get("room_area"),
                    area_type=r.get("area_type"),
                    product=r.get("product", ""),
                    material_description=r.get("material_description", ""),
                    extent=r.get("extent"),
                    location=r.get("location"),
                    friable=r.get("friable"),
                    material_condition=r.get("material_condition"),
                    risk_status=r.get("risk_status"),
                    result=r.get("result", ""),
                    page_number=r.get("page_number"),
                    extraction_confidence=r.get("extraction_confidence"),
                    acm_product_group=r.get("acm_product_group"),
                    acm_product_type=r.get("acm_product_type"),
                    classification_confidence=r.get("classification_confidence"),
                    classification_method=r.get("classification_method"),
                    classification_override=r.get("classification_override"),
                    created=str(r.get("created", "")) if r.get("created") else None,
                    updated=str(r.get("updated", "")) if r.get("updated") else None,
                )
            )

        return ACMRecordListResponse(
            records=record_responses,
            total=total,
            page=page,
            pages=pages,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing ACM records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{record_id}", response_model=ACMRecordResponse)
async def get_acm_record(record_id: str):
    """Get a single ACM record by ID."""
    try:
        record = await ACMRecord.get(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="ACM record not found")

        return ACMRecordResponse(
            id=str(record.id),
            source_id=str(record.source_id),
            school_name=record.school_name,
            school_code=record.school_code,
            building_id=record.building_id,
            building_name=record.building_name,
            building_year=record.building_year,
            building_construction=record.building_construction,
            room_id=record.room_id,
            room_name=record.room_name,
            room_area=record.room_area,
            area_type=record.area_type,
            product=record.product,
            material_description=record.material_description,
            extent=record.extent,
            location=record.location,
            friable=record.friable,
            material_condition=record.material_condition,
            risk_status=record.risk_status,
            result=record.result,
            page_number=record.page_number,
            extraction_confidence=record.extraction_confidence,
            acm_product_group=record.acm_product_group,
            acm_product_type=record.acm_product_type,
            classification_confidence=record.classification_confidence,
            classification_method=record.classification_method,
            classification_override=record.classification_override,
            created=str(record.created) if record.created else None,
            updated=str(record.updated) if record.updated else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ACM record {record_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ACMExtractResponse)
async def trigger_acm_extraction(request: ACMExtractRequest):
    """
    Trigger ACM extraction for a source document.

    Submits an async extraction job that parses the source's
    Docling output and creates ACM records.
    """
    try:
        # Import command modules to ensure they're registered
        import commands.acm_commands  # noqa: F401

        # Submit extraction command
        command_id = await CommandService.submit_command_job(
            "open_notebook", "acm_extract", {"source_id": request.source_id}
        )

        return ACMExtractResponse(
            command_id=str(command_id),
            status="submitted",
            message=f"ACM extraction started for source {request.source_id}",
        )

    except Exception as e:
        logger.error(f"Error triggering ACM extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_acm_records(
    source_id: str = Query(..., description="Source ID to export"),
):
    """
    Export ACM records as CSV file.

    Downloads all records for the specified source as a CSV file.
    """
    try:
        # Get all records for source
        records = await ACMRecord.get_by_source(source_id)

        if not records:
            raise HTTPException(
                status_code=404, detail="No ACM records found for source"
            )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [
            "Building ID",
            "Building Name",
            "Room ID",
            "Room Name",
            "Product",
            "Material Description",
            "Extent",
            "Location",
            "Friable",
            "Material Condition",
            "Risk Status",
            "Result",
            "Page Number",
        ]
        writer.writerow(headers)

        # Write data rows
        for record in records:
            writer.writerow(
                [
                    record.building_id,
                    record.building_name or "",
                    record.room_id or "",
                    record.room_name or "",
                    record.product,
                    record.material_description,
                    record.extent or "",
                    record.location or "",
                    record.friable or "",
                    record.material_condition or "",
                    record.risk_status or "",
                    record.result,
                    record.page_number or "",
                ]
            )

        # Create response
        output.seek(0)

        # Get source title for filename
        from open_notebook.domain.notebook import Source

        source = await Source.get(source_id)
        source_title = source.title if source else source_id
        filename = f"acm_export_{source_title}.csv".replace(" ", "_")

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting ACM records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Risk status colors for Excel
RISK_COLORS = {
    "Low": "C6EFCE",  # Green
    "Medium": "FFEB9C",  # Yellow/Orange
    "High": "FFC7CE",  # Red
}


@router.get("/export/excel")
async def export_acm_excel(
    source_id: str = Query(..., description="Source ID to export"),
):
    """
    Export ACM records as formatted Excel file.

    Downloads all records for the specified source as an Excel file
    with formatted headers, auto-sized columns, and risk status color coding.
    """
    try:
        # Get all records for source
        records = await ACMRecord.get_by_source(source_id)

        if not records:
            raise HTTPException(
                status_code=404, detail="No ACM records found for source"
            )

        # Get source title for filename
        from open_notebook.domain.notebook import Source

        source = await Source.get(source_id)
        source_title = source.title if source else source_id

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "ACM Register"

        # Define columns: (header, field, width)
        columns = [
            ("Building ID", "building_id", 12),
            ("Building Name", "building_name", 20),
            ("Room ID", "room_id", 10),
            ("Room Name", "room_name", 15),
            ("Product", "product", 20),
            ("Material Description", "material_description", 35),
            ("Extent", "extent", 15),
            ("Location", "location", 20),
            ("Friable", "friable", 10),
            ("Condition", "material_condition", 12),
            ("Risk Status", "risk_status", 12),
            ("Result", "result", 15),
            ("Page", "page_number", 8),
        ]

        # Header styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Write headers
        for col_idx, (header, _, width) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        # Write data rows
        for row_idx, record in enumerate(records, 2):
            for col_idx, (_, field, _) in enumerate(columns, 1):
                value = getattr(record, field, None)
                # Convert value to string if not None
                if value is not None:
                    value = str(value) if not isinstance(value, str) else value
                cell = ws.cell(row=row_idx, column=col_idx, value=value or "")
                cell.border = thin_border

                # Color code risk status
                if field == "risk_status" and value in RISK_COLORS:
                    cell.fill = PatternFill(
                        start_color=RISK_COLORS[value],
                        end_color=RISK_COLORS[value],
                        fill_type="solid",
                    )

        # Freeze header row
        ws.freeze_panes = "A2"

        # Auto-filter
        if records:
            ws.auto_filter.ref = ws.dimensions

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"acm_export_{source_title}_{date.today()}.xlsx".replace(" ", "_")

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting ACM records to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ACMStatsResponse)
async def get_acm_stats(
    source_id: Optional[str] = Query(None, description="Filter stats by source"),
):
    """
    Get ACM statistics summary.

    Returns counts of records by risk status and other metrics.
    """
    try:
        if source_id:
            stats = await ACMRecord.get_summary_by_source(source_id)
            return ACMStatsResponse(
                source_id=source_id,
                **stats,
            )
        else:
            # Global stats (all sources)
            result = await repo_query(
                """
                SELECT
                    count() as total_records,
                    count(risk_status = 'High' OR NULL) as high_risk_count,
                    count(risk_status = 'Medium' OR NULL) as medium_risk_count,
                    count(risk_status = 'Low' OR NULL) as low_risk_count,
                    array::distinct(building_id) as buildings,
                    array::distinct(room_id) as rooms
                FROM acm_record
                GROUP ALL
            """
            )

            if result:
                return ACMStatsResponse(
                    total_records=result[0].get("total_records", 0),
                    high_risk_count=result[0].get("high_risk_count", 0),
                    medium_risk_count=result[0].get("medium_risk_count", 0),
                    low_risk_count=result[0].get("low_risk_count", 0),
                    building_count=len(result[0].get("buildings", [])),
                    room_count=len([r for r in result[0].get("rooms", []) if r]),
                )
            else:
                return ACMStatsResponse(
                    total_records=0,
                    high_risk_count=0,
                    medium_risk_count=0,
                    low_risk_count=0,
                    building_count=0,
                    room_count=0,
                )

    except Exception as e:
        logger.error(f"Error getting ACM stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=ACMSearchResponse)
async def semantic_search_acm(
    query: str = Query(..., min_length=1, description="Natural language search query"),
    source_id: Optional[str] = Query(None, description="Filter to specific source"),
    building_id: Optional[str] = Query(None, description="Filter to specific building"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results to return"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
):
    """
    Semantic search across ACM records.

    Uses vector similarity to find records matching natural language queries.
    Requires records to have embeddings generated via the embedding pipeline.

    Example queries:
    - "high risk asbestos items"
    - "floor tiles in poor condition"
    - "accessible materials in corridors"
    """
    try:
        from api.services.acm_embedding_service import ACMEmbeddingService
        from open_notebook.domain.models import model_manager

        # Get embedding model
        embedding_model = await model_manager.get_embedding_model()
        if not embedding_model:
            raise HTTPException(
                status_code=400,
                detail="No embedding model configured. Please configure one in Settings."
            )

        # Embed the query
        try:
            query_embedding = (await embedding_model.aembed([query]))[0]
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed query: {str(e)}"
            )

        # Build filter clause
        filters = ["embedding IS NOT NULL"]
        params = {
            "query_embedding": query_embedding,
            "limit": limit,
        }

        if source_id:
            filters.append("source_id = $source_id")
            params["source_id"] = ensure_record_id(source_id)
        if building_id:
            filters.append("building_id = $building_id")
            params["building_id"] = building_id

        where_clause = " AND ".join(filters)

        # Execute vector similarity search
        # Note: SurrealDB vector::similarity::cosine returns 0-1 where 1 is most similar
        search_query = f"""
            SELECT *,
                   vector::similarity::cosine(embedding, $query_embedding) AS score
            FROM acm_record
            WHERE {where_clause}
            ORDER BY score DESC
            LIMIT $limit
        """

        results = await repo_query(search_query, params)

        # Filter by threshold and convert to response
        search_results = []
        for r in results:
            score = r.get("score", 0)
            if score >= threshold:
                search_results.append(
                    ACMSearchResultResponse(
                        id=str(r.get("id", "")),
                        source_id=str(r.get("source_id", "")),
                        school_name=r.get("school_name", ""),
                        building_id=r.get("building_id", ""),
                        building_name=r.get("building_name"),
                        room_id=r.get("room_id"),
                        room_name=r.get("room_name"),
                        product=r.get("product", ""),
                        material_description=r.get("material_description", ""),
                        extent=r.get("extent"),
                        location=r.get("location"),
                        material_condition=r.get("material_condition"),
                        risk_status=r.get("risk_status"),
                        result=r.get("result", ""),
                        score=round(score, 4),
                    )
                )

        logger.info(
            f"Semantic search for '{query}': {len(search_results)} results "
            f"(threshold={threshold}, limit={limit})"
        )

        return ACMSearchResponse(
            query=query,
            results=search_results,
            total=len(search_results),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/records", response_model=ACMRecordResponse)
async def create_acm_record(request: ACMRecordCreateRequest):
    """
    Create a new ACM record.

    Creates a single ACM record with the provided data.
    """
    try:
        # Create ACMRecord instance
        record = ACMRecord(
            source_id=request.source_id,
            school_name=request.school_name,
            school_code=request.school_code,
            building_id=request.building_id,
            building_name=request.building_name,
            building_year=request.building_year,
            building_construction=request.building_construction,
            room_id=request.room_id,
            room_name=request.room_name,
            room_area=request.room_area,
            area_type=request.area_type,
            product=request.product,
            material_description=request.material_description,
            extent=request.extent,
            location=request.location,
            friable=request.friable,
            material_condition=request.material_condition,
            risk_status=request.risk_status,
            result=request.result,
            page_number=request.page_number,
        )

        # Save to database
        await record.save()

        return ACMRecordResponse(
            id=str(record.id),
            source_id=str(record.source_id),
            school_name=record.school_name,
            school_code=record.school_code,
            building_id=record.building_id,
            building_name=record.building_name,
            building_year=record.building_year,
            building_construction=record.building_construction,
            room_id=record.room_id,
            room_name=record.room_name,
            room_area=record.room_area,
            area_type=record.area_type,
            product=record.product,
            material_description=record.material_description,
            extent=record.extent,
            location=record.location,
            friable=record.friable,
            material_condition=record.material_condition,
            risk_status=record.risk_status,
            result=record.result,
            page_number=record.page_number,
            extraction_confidence=None,
            created=str(record.created) if record.created else None,
            updated=str(record.updated) if record.updated else None,
        )

    except Exception as e:
        logger.error(f"Error creating ACM record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/records/{record_id}", response_model=ACMRecordResponse)
async def update_acm_record(record_id: str, request: ACMRecordUpdateRequest):
    """
    Update an existing ACM record.

    Only provided fields will be updated. All fields are optional.
    """
    try:
        # Fetch existing record
        record = await ACMRecord.get(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="ACM record not found")

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)

        for field, value in update_data.items():
            if hasattr(record, field):
                setattr(record, field, value)

        # Save changes
        await record.save()

        return ACMRecordResponse(
            id=str(record.id),
            source_id=str(record.source_id),
            school_name=record.school_name,
            school_code=record.school_code,
            building_id=record.building_id,
            building_name=record.building_name,
            building_year=record.building_year,
            building_construction=record.building_construction,
            room_id=record.room_id,
            room_name=record.room_name,
            room_area=record.room_area,
            area_type=record.area_type,
            product=record.product,
            material_description=record.material_description,
            extent=record.extent,
            location=record.location,
            friable=record.friable,
            material_condition=record.material_condition,
            risk_status=record.risk_status,
            result=record.result,
            page_number=record.page_number,
            extraction_confidence=None,
            created=str(record.created) if record.created else None,
            updated=str(record.updated) if record.updated else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ACM record {record_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/{record_id}")
async def delete_acm_record(record_id: str):
    """
    Delete an ACM record.

    Permanently removes the record from the database.
    """
    try:
        record = await ACMRecord.get(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="ACM record not found")

        await record.delete()

        return {"message": "ACM record deleted successfully", "id": record_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ACM record {record_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Site Configuration Endpoints (E1-S8 - Victorian BAR Compliance)
# =============================================================================


@router.get("/config", response_model=SiteConfigResponse)
async def get_site_config(
    source_id: str = Query(..., description="Source document ID"),
):
    """
    Get site configuration for a source document.

    Returns the configuration if it exists, or an empty config template.
    """
    try:
        config = await SiteConfig.get_by_source(source_id)

        if config:
            return SiteConfigResponse(
                id=config.id,
                source_id=config.source_id,
                department=config.department,
                agency=config.agency,
                building_type=config.building_type,
                owned_or_leased=config.owned_or_leased,
                frequency_of_use=config.frequency_of_use,
                public_access=config.public_access,
                building_unique_id=config.building_unique_id,
                missing_fields=config.get_missing_bar_fields(),
                is_bar_complete=config.is_bar_complete(),
                created=str(config.created) if config.created else None,
                updated=str(config.updated) if config.updated else None,
            )

        # Return empty config template for new sources
        return SiteConfigResponse(
            source_id=source_id,
            missing_fields=[
                "department",
                "agency",
                "building_type",
                "owned_or_leased",
                "frequency_of_use",
                "public_access",
            ],
            is_bar_complete=False,
        )

    except Exception as e:
        logger.error(f"Error fetching site config for {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", response_model=SiteConfigResponse)
async def save_site_config(request: SiteConfigRequest):
    """
    Create or update site configuration for a source document.

    Uses upsert logic - creates if not exists, updates if exists.
    """
    try:
        config = await SiteConfig.upsert(
            source_id=request.source_id,
            department=request.department,
            agency=request.agency,
            building_type=request.building_type,
            owned_or_leased=request.owned_or_leased,
            frequency_of_use=request.frequency_of_use,
            public_access=request.public_access,
            building_unique_id=request.building_unique_id,
        )

        return SiteConfigResponse(
            id=config.id,
            source_id=config.source_id,
            department=config.department,
            agency=config.agency,
            building_type=config.building_type,
            owned_or_leased=config.owned_or_leased,
            frequency_of_use=config.frequency_of_use,
            public_access=config.public_access,
            building_unique_id=config.building_unique_id,
            missing_fields=config.get_missing_bar_fields(),
            is_bar_complete=config.is_bar_complete(),
            created=str(config.created) if config.created else None,
            updated=str(config.updated) if config.updated else None,
        )

    except Exception as e:
        logger.error(f"Error saving site config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/templates", response_model=list[SiteConfigTemplateResponse])
async def list_site_config_templates(
    limit: int = Query(20, ge=1, le=100, description="Max templates to return"),
):
    """
    List available site configuration templates.

    Returns previously saved configurations that can be reused for new sources.
    """
    try:
        templates = await SiteConfig.get_templates(limit=limit)

        return [
            SiteConfigTemplateResponse(
                source_id=t.get("source_id", ""),
                source_title=t.get("source_title"),
                department=t.get("department"),
                agency=t.get("agency"),
                building_type=t.get("building_type"),
                owned_or_leased=t.get("owned_or_leased"),
                frequency_of_use=t.get("frequency_of_use"),
                public_access=t.get("public_access"),
            )
            for t in templates
        ]

    except Exception as e:
        logger.error(f"Error fetching site config templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/apply-template", response_model=SiteConfigResponse)
async def apply_site_config_template(request: ApplyTemplateRequest):
    """
    Apply a template configuration to a source document.

    Copies configuration from the template source to the target source.
    """
    try:
        # Get template config
        template = await SiteConfig.get_by_source(request.template_source_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template configuration not found for source {request.template_source_id}",
            )

        # Apply template to target source
        config = await SiteConfig.upsert(
            source_id=request.source_id,
            department=template.department,
            agency=template.agency,
            building_type=template.building_type,
            owned_or_leased=template.owned_or_leased,
            frequency_of_use=template.frequency_of_use,
            public_access=template.public_access,
            # Don't copy building_unique_id - should be unique per building
        )

        return SiteConfigResponse(
            id=config.id,
            source_id=config.source_id,
            department=config.department,
            agency=config.agency,
            building_type=config.building_type,
            owned_or_leased=config.owned_or_leased,
            frequency_of_use=config.frequency_of_use,
            public_access=config.public_access,
            building_unique_id=config.building_unique_id,
            missing_fields=config.get_missing_bar_fields(),
            is_bar_complete=config.is_bar_complete(),
            created=str(config.created) if config.created else None,
            updated=str(config.updated) if config.updated else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/agencies", response_model=AgencyListResponse)
async def list_agencies(
    department: Optional[str] = Query(None, description="Filter by department"),
):
    """
    List distinct agency values for autocomplete.

    Optionally filter by department.
    """
    try:
        agencies = await SiteConfig.get_agencies(department=department)
        return AgencyListResponse(agencies=agencies)

    except Exception as e:
        logger.error(f"Error fetching agencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ACM Product Classification Endpoints (E1-S9 - Victorian BAR Taxonomy)
# =============================================================================


@router.post("/classify", response_model=ClassifyResponse)
async def classify_acm_item(request: ClassifyRequest):
    """
    Classify a single ACM item into Victorian BAR taxonomy.

    Uses pattern-based matching first, then falls back to LLM if enabled.

    Example:
        POST /api/acm/classify
        {"item_description": "Vinyl floor tiles", "friability": "Non-friable"}

    Returns the product group (e.g., "T3 Vinyl products") and product type
    (e.g., "Vinyl Tiles") with a confidence score.
    """
    try:
        from open_notebook.extractors.normalizers.taxonomy import (
            classify_product,
            classify_product_async,
        )

        if request.use_llm_fallback:
            # Async version with LLM fallback
            result = await classify_product_async(
                item_description=request.item_description,
                friability=request.friability,
                product=request.product,
                use_llm_fallback=True,
            )
        else:
            # Sync pattern-only version
            result = classify_product(
                item_description=request.item_description,
                friability=request.friability,
                product=request.product,
            )

        return ClassifyResponse(
            product_group=result.product_group,
            product_type=result.product_type,
            confidence=result.confidence,
            method=result.method,
        )

    except Exception as e:
        logger.error(f"Error classifying ACM item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/batch", response_model=BatchClassifyResponse)
async def classify_batch(request: BatchClassifyRequest):
    """
    Classify all ACM records for a source document.

    Updates records in the database with classification results.
    Optionally skips records that already have classification.

    Example:
        POST /api/acm/classify/batch
        {"source_id": "source:abc123", "use_llm_fallback": true}
    """
    try:
        from open_notebook.extractors.normalizers.taxonomy import (
            classify_product,
            classify_product_async,
        )

        # Get all records for source
        records = await ACMRecord.get_by_source(request.source_id)

        if not records:
            return BatchClassifyResponse(
                total=0,
                classified=0,
                skipped=0,
                errors=0,
                results=[],
            )

        total = len(records)
        classified = 0
        skipped = 0
        errors = 0
        results = []

        for record in records:
            try:
                # Skip if already classified and skip_classified is True
                if request.skip_classified and record.acm_product_group:
                    skipped += 1
                    results.append({
                        "record_id": str(record.id),
                        "status": "skipped",
                        "reason": "already_classified",
                    })
                    continue

                # Combine product and material description for classification
                item_description = record.material_description
                if record.product:
                    item_description = f"{record.product} {item_description}"

                # Classify
                if request.use_llm_fallback:
                    result = await classify_product_async(
                        item_description=item_description,
                        friability=record.friable,
                        product=record.product,
                        use_llm_fallback=True,
                    )
                else:
                    result = classify_product(
                        item_description=item_description,
                        friability=record.friable,
                        product=record.product,
                    )

                if result.product_group and result.product_type:
                    # Update record
                    record.acm_product_group = result.product_group
                    record.acm_product_type = result.product_type
                    record.classification_confidence = result.confidence
                    record.classification_method = result.method
                    record.classification_override = False
                    await record.save()

                    classified += 1
                    results.append({
                        "record_id": str(record.id),
                        "status": "classified",
                        "product_group": result.product_group,
                        "product_type": result.product_type,
                        "confidence": result.confidence,
                        "method": result.method,
                    })
                else:
                    skipped += 1
                    results.append({
                        "record_id": str(record.id),
                        "status": "skipped",
                        "reason": "no_match",
                    })

            except Exception as e:
                errors += 1
                results.append({
                    "record_id": str(record.id),
                    "status": "error",
                    "error": str(e),
                })
                logger.warning(f"Error classifying record {record.id}: {e}")

        logger.info(
            f"Batch classification for {request.source_id}: "
            f"{classified} classified, {skipped} skipped, {errors} errors (total: {total})"
        )

        return BatchClassifyResponse(
            total=total,
            classified=classified,
            skipped=skipped,
            errors=errors,
            results=results,
        )

    except Exception as e:
        logger.error(f"Error in batch classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_recommendation_text(request: NormalizeRequest):
    """
    Normalize a consultant recommendation to a canonical action.

    Uses pattern-based matching against known consultant wording patterns
    to map free-text recommendations to standardized actions.

    Example:
        POST /api/acm/normalize
        {"recommendation": "Maintain in current condition and label"}

    Returns the canonical action (e.g., "maintain_in_situ") with confidence.
    """
    try:
        from open_notebook.extractors.normalizers.recommendations import (
            normalize_recommendation,
        )

        result = normalize_recommendation(request.recommendation)

        return NormalizeResponse(
            raw_text=result.raw_text,
            normalized_action=result.normalized_action,
            confidence=result.confidence,
            method=result.method,
        )

    except Exception as e:
        logger.error(f"Error normalizing recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/taxonomy", response_model=TaxonomyResponse)
async def get_taxonomy(
    friability: Optional[str] = Query(
        None, description="Friability type: 'Friable' or 'Non-friable' (default)"
    ),
):
    """
    Get available ACM product taxonomy.

    Returns the Victorian BAR product groups and types for the specified friability.
    Useful for UI dropdowns and validation.

    Example:
        GET /api/acm/taxonomy?friability=Non-friable
    """
    try:
        from open_notebook.extractors.normalizers.taxonomy import get_product_groups

        groups = get_product_groups(friability)

        # Determine friability label
        if friability and "friable" in friability.lower() and "non" not in friability.lower():
            friability_label = "Friable"
        else:
            friability_label = "Non-friable"

        return TaxonomyResponse(
            friability=friability_label,
            groups=[
                TaxonomyGroupResponse(
                    pc_code=g.get("pc_code", ""),
                    product_group_header=g.get("product_group_header", ""),
                    product_types=g.get("product_types", []),
                )
                for g in groups
            ],
        )

    except Exception as e:
        logger.error(f"Error fetching taxonomy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
