# Tech-Spec: E1-S4 ACM API Endpoints

**Created:** 2025-12-07
**Status:** Ready for Development
**Epic:** E1 - ACM Data Extraction Pipeline
**Story:** S4 - Create ACM API Endpoints

---

## Overview

### Problem Statement

The frontend needs REST API endpoints to fetch, filter, and export ACM records. The ACMRecord domain model exists (E1-S2) and the extraction command exists (E1-S3), but there's no HTTP interface for the frontend to access this data.

### Solution

Create a FastAPI router at `/api/acm/` with endpoints for:
- Listing records with filtering/pagination
- Getting single record by ID
- Triggering extraction for a source
- Exporting records as CSV
- Getting summary statistics

### Scope

**In Scope:**
- FastAPI router with 5 endpoints
- Pydantic request/response models
- Integration with ACMRecord domain model
- CSV export functionality
- OpenAPI documentation

**Out of Scope:**
- Frontend components (E2)
- Excel export (E5-S2)
- Integration with source upload (E1-S5)

---

## Context for Development

### Codebase Patterns

#### 1. Router Pattern
Location: `api/routers/`

```python
from fastapi import APIRouter, HTTPException, Query
router = APIRouter()

@router.get("/items")
async def list_items():
    pass
```

#### 2. Pydantic Models Pattern
Location: `api/models.py`

```python
class ItemResponse(BaseModel):
    id: str
    name: str
    created: str

class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int
```

#### 3. Router Registration
Location: `api/main.py`

```python
from api.routers import acm
app.include_router(acm.router, prefix="/api/acm", tags=["acm"])
```

### Files to Reference

| File | Purpose |
|------|---------|
| `api/routers/sources.py` | Example router patterns |
| `api/models.py` | Pydantic model patterns |
| `api/main.py` | Router registration |
| `open_notebook/domain/acm.py` | ACMRecord model (E1-S2) |
| `commands/acm_commands.py` | Extraction command (E1-S3) |

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Create Pydantic models in `api/models.py`**
  - ACMRecordResponse
  - ACMRecordListResponse
  - ACMExtractRequest
  - ACMExtractResponse
  - ACMStatsResponse

- [ ] **Task 2: Create `api/routers/acm.py`**
  - Import dependencies
  - Create router instance
  - Implement 5 endpoints

- [ ] **Task 3: Register router in `api/main.py`**
  - Add import
  - Include router with prefix

- [ ] **Task 4: Implement GET /records endpoint**
  - Filter by source_id, building_id, risk_status
  - Pagination with page/limit
  - Return total count

- [ ] **Task 5: Implement GET /records/{id} endpoint**
  - Fetch single record
  - Return 404 if not found

- [ ] **Task 6: Implement POST /extract endpoint**
  - Submit extraction command
  - Return command_id for tracking

- [ ] **Task 7: Implement GET /export endpoint**
  - Generate CSV from records
  - Return as file download

- [ ] **Task 8: Implement GET /stats endpoint**
  - Return summary statistics
  - Counts by risk status

- [ ] **Task 9: Update OpenAPI docs**
  - Verify all endpoints documented
  - Test in Swagger UI

### Acceptance Criteria

- [ ] **AC1**: `GET /api/acm/records?source_id=xxx` returns records
  - Given: ACM records exist for source
  - When: Endpoint called with source_id
  - Then: Returns paginated list of records

- [ ] **AC2**: `GET /api/acm/records/{id}` returns single record
  - Given: ACM record exists
  - When: Endpoint called with record ID
  - Then: Returns full record details

- [ ] **AC3**: `POST /api/acm/extract` triggers extraction
  - Given: Source with processed content
  - When: Endpoint called with source_id
  - Then: Returns command_id, extraction starts

- [ ] **AC4**: Filtering by building_id, risk_status works
  - Given: Records with different buildings/risks
  - When: Filter parameters provided
  - Then: Only matching records returned

- [ ] **AC5**: Pagination works correctly
  - Given: Many records exist
  - When: page=2, limit=10 provided
  - Then: Returns correct page of results

- [ ] **AC6**: OpenAPI docs are complete
  - Given: All endpoints implemented
  - When: /docs accessed
  - Then: All endpoints visible with schemas

---

## Code Specification

### File: `api/models.py` (additions)

```python
# Add to existing api/models.py

# ACM API Models
class ACMRecordResponse(BaseModel):
    """Single ACM record response."""
    id: str
    source_id: str
    school_name: str
    school_code: Optional[str] = None
    building_id: str
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: Optional[str] = None
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None
    result: str
    page_number: Optional[int] = None
    extraction_confidence: Optional[float] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class ACMRecordListResponse(BaseModel):
    """Paginated list of ACM records."""
    records: List[ACMRecordResponse]
    total: int
    page: int
    pages: int
    limit: int


class ACMExtractRequest(BaseModel):
    """Request to trigger ACM extraction."""
    source_id: str = Field(..., description="Source ID to extract ACM data from")


class ACMExtractResponse(BaseModel):
    """Response from extraction trigger."""
    command_id: str = Field(..., description="Command ID to track progress")
    status: str = Field(default="submitted", description="Initial status")
    message: str = Field(default="ACM extraction started")


class ACMStatsResponse(BaseModel):
    """ACM statistics summary."""
    total_records: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    building_count: int
    room_count: int
    source_id: Optional[str] = None
```

### File: `api/routers/acm.py`

```python
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
from surreal_commands import submit_command

from api.models import (
    ACMExtractRequest,
    ACMExtractResponse,
    ACMRecordListResponse,
    ACMRecordResponse,
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
    risk_status: Optional[str] = Query(None, description="Filter by risk status (Low/Medium/High)"),
    search: Optional[str] = Query(None, description="Search across text fields"),
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
        params = {"source_id": ensure_record_id(source_id)}

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
        count_query = f"SELECT count() as total FROM acm_record WHERE {where_clause} GROUP ALL"
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
            record_responses.append(ACMRecordResponse(
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
            ))

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
        # Submit extraction command
        command_id = submit_command(
            "open_notebook",
            "acm_extract",
            {"source_id": request.source_id}
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
    format: str = Query("csv", description="Export format (csv only for now)"),
):
    """
    Export ACM records as CSV file.

    Downloads all records for the specified source as a CSV file.
    """
    try:
        # Get all records for source
        records = await ACMRecord.get_by_source(source_id)

        if not records:
            raise HTTPException(status_code=404, detail="No ACM records found for source")

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [
            "Building ID", "Building Name", "Room ID", "Room Name",
            "Product", "Material Description", "Extent", "Location",
            "Friable", "Material Condition", "Risk Status", "Result",
            "Page Number"
        ]
        writer.writerow(headers)

        # Write data rows
        for record in records:
            writer.writerow([
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
            ])

        # Create response
        output.seek(0)

        # Get source title for filename
        from open_notebook.domain.notebook import Source
        source = await Source.get(source_id)
        filename = f"acm_export_{source.title or source_id}.csv".replace(" ", "_")

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
            result = await repo_query("""
                SELECT
                    count() as total_records,
                    count(risk_status = 'High' OR NULL) as high_risk_count,
                    count(risk_status = 'Medium' OR NULL) as medium_risk_count,
                    count(risk_status = 'Low' OR NULL) as low_risk_count,
                    array::distinct(building_id) as buildings,
                    array::distinct(room_id) as rooms
                FROM acm_record
                GROUP ALL
            """)

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
```

### File: `api/main.py` (additions)

```python
# Add to imports
from api.routers import acm

# Add to router includes (after existing routers)
app.include_router(acm.router, prefix="/api/acm", tags=["acm"])
```

---

## Additional Context

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E1-S2 (ACMRecord Model) | Story | Must be complete |
| E1-S3 (Extraction Command) | Story | For /extract endpoint |
| FastAPI | Library | Already installed |
| surreal-commands | Library | For command submission |

### Testing Strategy

1. **Unit Tests**: Test each endpoint with mock data
2. **Integration Tests**: Full flow with real database
3. **Manual Testing**: Use Swagger UI at /docs

### API Usage Examples

```bash
# List records for a source
GET /api/acm/records?source_id=source:123&page=1&limit=50

# Get single record
GET /api/acm/records/acm_record:abc123

# Trigger extraction
POST /api/acm/extract
{"source_id": "source:123"}

# Export to CSV
GET /api/acm/export?source_id=source:123

# Get statistics
GET /api/acm/stats?source_id=source:123
```

---

## Next Stories After This

| Story | Description | Depends On |
|-------|-------------|------------|
| E1-S5 | Integrate into Source Processing | This story |
| E2-S2 | ACMSpreadsheet Component | This story |
| E5-S1 | CSV Export | Already included |

---

*Tech-Spec generated by create-tech-spec workflow*
