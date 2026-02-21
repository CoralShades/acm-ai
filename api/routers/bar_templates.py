"""BAR Template Management API Router.

Story: E5-S3 BAR Template Management
"""

from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel

from api.services.bar_template_service import parse_bar_template
from open_notebook.domain.bar_template import BARTemplate, BARTemplateColumn

router = APIRouter(prefix="/api/bar-templates", tags=["bar-templates"])


# --- Response Models ---


class BARTemplateColumnResponse(BaseModel):
    column_letter: str
    column_name: str
    field_type: Optional[str] = None
    is_required: bool = False


class BARTemplateResponse(BaseModel):
    id: Optional[str] = None
    filename: str
    version_label: str
    uploaded_at: Optional[str] = None
    is_active: bool = False
    column_count: int = 0
    columns: List[BARTemplateColumnResponse] = []
    raw_header_row: List[str] = []
    notes: Optional[str] = None


def _to_response(template: BARTemplate) -> BARTemplateResponse:
    return BARTemplateResponse(
        id=template.id,
        filename=template.filename,
        version_label=template.version_label,
        uploaded_at=template.uploaded_at.isoformat() if template.uploaded_at else None,
        is_active=template.is_active,
        column_count=template.column_count,
        columns=[
            BARTemplateColumnResponse(
                column_letter=c.column_letter,
                column_name=c.column_name,
                field_type=c.field_type,
                is_required=c.is_required,
            )
            for c in template.columns
        ],
        raw_header_row=template.raw_header_row,
        notes=template.notes,
    )


# --- Endpoints ---


@router.get("", response_model=List[BARTemplateResponse])
async def list_templates():
    """List all uploaded BAR templates."""
    templates = await BARTemplate.get_all(order_by="uploaded_at DESC")
    return [_to_response(t) for t in templates]


@router.post("/upload", response_model=BARTemplateResponse)
async def upload_template(file: UploadFile = File(...)):
    """Upload and parse a new BAR template (.xlsx/.xlsm)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "xlsm"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx and .xlsm files are supported",
        )

    try:
        content = await file.read()
        max_size = 10 * 1024 * 1024  # 10 MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({len(content)} bytes). Maximum size is 10 MB.",
            )
        template = parse_bar_template(content, file.filename)
        await template.save()
        logger.info(f"Uploaded BAR template: {template.filename} ({template.column_count} columns)")
        return _to_response(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload BAR template: {e}")
        raise HTTPException(status_code=500, detail="Failed to process template file")


@router.get("/{template_id}", response_model=BARTemplateResponse)
async def get_template(template_id: str):
    """Get a specific BAR template by ID."""
    template = await BARTemplate.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_response(template)


@router.put("/{template_id}/activate", response_model=BARTemplateResponse)
async def activate_template(template_id: str):
    """Set a template as the active template for exports."""
    template = await BARTemplate.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await template.activate()
    logger.info(f"Activated BAR template: {template.filename}")
    return _to_response(template)


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """Delete a non-active template."""
    template = await BARTemplate.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the active template. Activate another template first.",
        )

    await template.delete()
    logger.info(f"Deleted BAR template: {template.filename}")
    return {"status": "deleted", "id": template_id}
