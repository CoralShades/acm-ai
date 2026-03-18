"""Format Profile Registry API Endpoints.

CRUD endpoints for consultant format profiles — cached column header
to Salesforce field mappings keyed by header signature.

Story: Multi-Consultant Story 3 — Format Profile Registry
Story: Multi-Consultant Story 6 — HITL Mapping Confirmation UI
"""

from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.extractors.format_profile_repository import (
    delete_profile,
    get_profile_by_signature,
    list_profiles,
    save_profile,
)
from open_notebook.extractors.hitl_registry import get_hitl_registry
from open_notebook.extractors.schema_inference import compute_header_signature

router = APIRouter()


class FormatProfileCreateRequest(BaseModel):
    """Request body for manually creating a format profile."""

    headers: list[str] = Field(
        ..., description="Column header strings to compute signature from"
    )
    consultant_name: Optional[str] = Field(
        None, description="Name of the consulting firm"
    )
    column_mapping: dict[str, str] = Field(
        ..., description="Mapping of PDF header → SF field API name"
    )
    canonical_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of PDF header → canonical name for segmenter",
    )
    level_regex: Optional[str] = Field(
        None, description="Optional regex for level/floor detection"
    )
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Confidence score (manual = 1.0)"
    )


class FormatProfileResponse(BaseModel):
    """Response body for a format profile."""

    id: Optional[str] = None
    header_signature: str
    consultant_name: Optional[str] = None
    column_mapping: dict[str, str]
    canonical_mapping: dict[str, str] = {}
    level_regex: Optional[str] = None
    recovery_config: Optional[dict[str, Any]] = None
    confidence: float = 0.0
    verified_by_user: bool = False
    sample_count: int = 1
    created: Optional[str] = None
    updated: Optional[str] = None


@router.get("/format-profiles", response_model=list[FormatProfileResponse])
async def get_format_profiles():
    """List all cached format profiles, ordered by usage count."""
    try:
        profiles = await list_profiles()
        return [_normalize_profile(p) for p in profiles]
    except Exception as e:
        logger.error(f"Failed to list format profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/format-profiles", response_model=FormatProfileResponse, status_code=201)
async def create_format_profile(request: FormatProfileCreateRequest):
    """Manually create a format profile for a known consultant format."""
    try:
        header_sig = compute_header_signature(request.headers)

        # Check for existing profile with same signature
        existing = await get_profile_by_signature(header_sig)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Profile already exists for this header signature: {existing.get('id')}",
            )

        profile_data = {
            "header_signature": header_sig,
            "consultant_name": request.consultant_name,
            "column_mapping": request.column_mapping,
            "canonical_mapping": request.canonical_mapping,
            "level_regex": request.level_regex,
            "recovery_config": None,
            "confidence": request.confidence,
            "verified_by_user": True,  # Manual creation = user-verified
            "sample_count": 0,
        }

        result = await save_profile(profile_data)
        if isinstance(result, list) and len(result) > 0:
            return _normalize_profile(result[0])
        elif isinstance(result, dict):
            return _normalize_profile(result)
        raise HTTPException(status_code=500, detail="Failed to create profile")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create format profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/format-profiles/{profile_id}")
async def delete_format_profile(profile_id: str):
    """Delete a format profile by record ID."""
    try:
        full_id = (
            profile_id
            if profile_id.startswith("consultant_format_profile:")
            else f"consultant_format_profile:{profile_id}"
        )
        await delete_profile(full_id)
        return {"deleted": full_id}
    except Exception as e:
        logger.error(f"Failed to delete format profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# MCS6: HITL Mapping Confirmation
# ---------------------------------------------------------------------------


class HITLMappingItem(BaseModel):
    """A single column mapping in a HITL response."""

    pdf_header: str
    sf_field: str
    confidence: float = 1.0


class HITLResumeRequest(BaseModel):
    """Request body for resuming extraction after HITL review."""

    operation_id: str = Field(..., description="Operation ID of the paused extraction")
    action: str = Field(
        ...,
        description="User action: 'approve', 'modify', or 'reject'",
        pattern="^(approve|modify|reject)$",
    )
    mappings: Optional[List[HITLMappingItem]] = Field(
        None,
        description="Modified mappings (required when action='modify')",
    )


class HITLResumeResponse(BaseModel):
    """Response body after submitting HITL decision."""

    operation_id: str
    action: str
    resumed: bool


class HITLPendingResponse(BaseModel):
    """Response body for a pending HITL request."""

    operation_id: str
    interrupt_data: dict[str, Any]


@router.post("/hitl/resume", response_model=HITLResumeResponse)
async def resume_hitl_mapping(request: HITLResumeRequest):
    """Resume a paused extraction after HITL schema mapping review.

    The extraction pipeline pauses when schema inference confidence < 0.8.
    This endpoint delivers the user's mapping decision (approve/modify/reject)
    back to the waiting pipeline, which then resumes extraction.
    """
    registry = get_hitl_registry()

    if not registry.is_pending(request.operation_id):
        raise HTTPException(
            status_code=404,
            detail=f"No pending HITL request for operation {request.operation_id}",
        )

    if request.action == "modify" and not request.mappings:
        raise HTTPException(
            status_code=422,
            detail="Mappings are required when action is 'modify'",
        )

    response_data: dict[str, Any] = {"action": request.action}
    if request.mappings:
        response_data["mappings"] = [m.model_dump() for m in request.mappings]

    submitted = registry.submit_response(request.operation_id, response_data)

    if not submitted:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to submit response for operation {request.operation_id}",
        )

    logger.info(
        f"HITL resume submitted for operation {request.operation_id}: "
        f"action={request.action}"
    )

    return HITLResumeResponse(
        operation_id=request.operation_id,
        action=request.action,
        resumed=True,
    )


@router.get("/hitl/pending", response_model=list[HITLPendingResponse])
async def list_pending_hitl():
    """List all operations with pending HITL mapping review requests."""
    registry = get_hitl_registry()
    pending_ids = registry.list_pending()
    results = []
    for op_id in pending_ids:
        interrupt_data = registry.get_interrupt_data(op_id)
        if interrupt_data:
            results.append(
                HITLPendingResponse(
                    operation_id=op_id,
                    interrupt_data=interrupt_data,
                )
            )
    return results


def _normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Normalize a profile dict for API response (handle datetime serialization)."""
    result = dict(profile)
    for ts_field in ("created", "updated", "created_at", "updated_at"):
        if ts_field in result and result[ts_field] is not None:
            result[ts_field] = str(result[ts_field])
    # Map created_at/updated_at to created/updated for consistency
    if "created_at" in result:
        result.setdefault("created", result.pop("created_at"))
    if "updated_at" in result:
        result.setdefault("updated", result.pop("updated_at"))
    return result
