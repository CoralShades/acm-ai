"""
ACM (Asbestos Containing Material) API Endpoints

Provides REST API for ACM record management including
listing, filtering, extraction, and export.
"""

import csv
import io
import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from api.command_service import CommandService
from api.models import (
    ACMExtractRequest,
    ACMExtractResponse,
    ACMRecordCreateRequest,
    ACMRecordListResponse,
    ACMRecordResponse,
    ACMRecordUpdateRequest,
    ACMStatsResponse,
)
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.acm import ACMRecord

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
