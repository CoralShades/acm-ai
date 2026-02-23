from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from api.models import SettingsResponse, SettingsUpdate
from open_notebook.database.repository import repo_query
from open_notebook.domain.content_settings import ContentSettings
from open_notebook.domain.extraction_settings import ExtractionSettings
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class ExtractionSettingsResponse(BaseModel):
    extraction_method: str = "hybrid"
    fallback_enabled: bool = True
    enable_toc_extraction: bool = True
    enable_building_inventory: bool = True
    enable_page_tagging: bool = True
    enable_metadata_enhancement: bool = True
    enable_corrective_rag: bool = True
    max_correction_attempts: int = 2


class ExtractionSettingsUpdate(BaseModel):
    extraction_method: Literal["mineru", "docling", "hybrid"] | None = None
    fallback_enabled: bool | None = None
    enable_toc_extraction: bool | None = None
    enable_building_inventory: bool | None = None
    enable_page_tagging: bool | None = None
    enable_metadata_enhancement: bool | None = None
    enable_corrective_rag: bool | None = None
    max_correction_attempts: int | None = Field(default=None, ge=1, le=10)

router = APIRouter()


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get all application settings."""
    try:
        settings: ContentSettings = await ContentSettings.get_instance()  # type: ignore[assignment]

        return SettingsResponse(
            default_content_processing_engine_doc=settings.default_content_processing_engine_doc,
            default_content_processing_engine_url=settings.default_content_processing_engine_url,
            default_embedding_option=settings.default_embedding_option,
            auto_delete_files=settings.auto_delete_files,
            youtube_preferred_languages=settings.youtube_preferred_languages,
        )
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching settings: {str(e)}"
        )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(settings_update: SettingsUpdate):
    """Update application settings."""
    try:
        settings: ContentSettings = await ContentSettings.get_instance()  # type: ignore[assignment]

        # Update only provided fields
        if settings_update.default_content_processing_engine_doc is not None:
            # Cast to proper literal type
            from typing import Literal, cast

            settings.default_content_processing_engine_doc = cast(
                Literal["auto", "docling", "simple"],
                settings_update.default_content_processing_engine_doc,
            )
        if settings_update.default_content_processing_engine_url is not None:
            from typing import Literal, cast

            settings.default_content_processing_engine_url = cast(
                Literal["auto", "firecrawl", "jina", "simple"],
                settings_update.default_content_processing_engine_url,
            )
        if settings_update.default_embedding_option is not None:
            from typing import Literal, cast

            settings.default_embedding_option = cast(
                Literal["ask", "always", "never"],
                settings_update.default_embedding_option,
            )
        if settings_update.auto_delete_files is not None:
            from typing import Literal, cast

            settings.auto_delete_files = cast(
                Literal["yes", "no"], settings_update.auto_delete_files
            )
        if settings_update.youtube_preferred_languages is not None:
            settings.youtube_preferred_languages = (
                settings_update.youtube_preferred_languages
            )

        await settings.update()

        return SettingsResponse(
            default_content_processing_engine_doc=settings.default_content_processing_engine_doc,
            default_content_processing_engine_url=settings.default_content_processing_engine_url,
            default_embedding_option=settings.default_embedding_option,
            auto_delete_files=settings.auto_delete_files,
            youtube_preferred_languages=settings.youtube_preferred_languages,
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating settings: {str(e)}"
        )


def _extraction_to_response(s: ExtractionSettings) -> ExtractionSettingsResponse:
    return ExtractionSettingsResponse(
        extraction_method=s.extraction_method,
        fallback_enabled=s.fallback_enabled,
        enable_toc_extraction=s.enable_toc_extraction,
        enable_building_inventory=s.enable_building_inventory,
        enable_page_tagging=s.enable_page_tagging,
        enable_metadata_enhancement=s.enable_metadata_enhancement,
        enable_corrective_rag=s.enable_corrective_rag,
        max_correction_attempts=s.max_correction_attempts,
    )


@router.get(
    "/settings/extraction", response_model=ExtractionSettingsResponse
)
async def get_extraction_settings():
    """Get extraction pipeline settings."""
    try:
        settings = await ExtractionSettings.get_instance()
        return _extraction_to_response(settings)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/extraction", response_model=ExtractionSettingsResponse
)
async def update_extraction_settings(update: ExtractionSettingsUpdate):
    """Update extraction pipeline settings."""
    try:
        settings = await ExtractionSettings.get_instance()
        for field_name, value in update.model_dump(exclude_none=True).items():
            setattr(settings, field_name, value)
        await settings.update()
        return _extraction_to_response(settings)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/settings/extraction/reset", response_model=ExtractionSettingsResponse
)
async def reset_extraction_settings():
    """Reset extraction settings to defaults."""
    try:
        settings = await ExtractionSettings.reset_to_defaults()
        return _extraction_to_response(settings)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Extraction Stage Model Configuration (E12-S2) ---


class StageModelAssignment(BaseModel):
    """Per-stage model assignment for extraction pipeline."""

    structure_analysis: Optional[str] = None
    building_inventory: Optional[str] = None
    acm_extraction: Optional[str] = None
    page_tagging: Optional[str] = None
    product_classification: Optional[str] = None
    corrective_validation: Optional[str] = None


STAGE_RECORD_ID = "extraction_stage_models:⟨active⟩"


@router.get(
    "/settings/extraction/stage-models", response_model=StageModelAssignment
)
async def get_extraction_stage_models():
    """Get per-stage model assignments for extraction pipeline."""
    try:
        result = await repo_query(f"SELECT * FROM ONLY {STAGE_RECORD_ID}")
        if result:
            data = result[0] if isinstance(result, list) else result
            return StageModelAssignment(
                structure_analysis=data.get("structure_analysis"),
                building_inventory=data.get("building_inventory"),
                acm_extraction=data.get("acm_extraction"),
                page_tagging=data.get("page_tagging"),
                product_classification=data.get("product_classification"),
                corrective_validation=data.get("corrective_validation"),
            )
        return StageModelAssignment()
    except Exception as e:
        logger.error(f"Error fetching stage models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/extraction/stage-models", response_model=StageModelAssignment
)
async def update_extraction_stage_models(update: StageModelAssignment):
    """Update per-stage model assignments."""
    try:
        data = update.model_dump(exclude_none=True)
        await repo_query(
            f"UPSERT {STAGE_RECORD_ID} SET "
            "structure_analysis = $structure_analysis, "
            "building_inventory = $building_inventory, "
            "acm_extraction = $acm_extraction, "
            "page_tagging = $page_tagging, "
            "product_classification = $product_classification, "
            "corrective_validation = $corrective_validation, "
            "updated = time::now()",
            {
                "structure_analysis": data.get("structure_analysis"),
                "building_inventory": data.get("building_inventory"),
                "acm_extraction": data.get("acm_extraction"),
                "page_tagging": data.get("page_tagging"),
                "product_classification": data.get("product_classification"),
                "corrective_validation": data.get("corrective_validation"),
            },
        )
        return update
    except Exception as e:
        logger.error(f"Error updating stage models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/extraction/stage-models/reset")
async def reset_extraction_stage_models():
    """Reset all stage model assignments to use default extraction model."""
    try:
        await repo_query(f"DELETE {STAGE_RECORD_ID}")
        return {"message": "Stage model assignments reset to defaults"}
    except Exception as e:
        logger.error(f"Error resetting stage models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Processing Configuration (E12-S3) ---


class ProcessingConfigResponse(BaseModel):
    """Processing pipeline configuration."""

    chunk_size: int = 4000
    confidence_threshold: float = 0.7
    max_correction_attempts: int = 3
    batch_size: int = 3
    per_page_timeout: int = 60
    total_document_timeout: int = 15
    store_raw_json: bool = True
    auto_classify: bool = True
    auto_normalize: bool = True

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        if not 2000 <= v <= 8000:
            raise ValueError("chunk_size must be between 2000 and 8000")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        return v

    @field_validator("max_correction_attempts")
    @classmethod
    def validate_max_corrections(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("max_correction_attempts must be between 1 and 5")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("batch_size must be between 1 and 10")
        return v

    @field_validator("per_page_timeout")
    @classmethod
    def validate_page_timeout(cls, v: int) -> int:
        if not 10 <= v <= 120:
            raise ValueError("per_page_timeout must be between 10 and 120")
        return v

    @field_validator("total_document_timeout")
    @classmethod
    def validate_doc_timeout(cls, v: int) -> int:
        if not 1 <= v <= 30:
            raise ValueError("total_document_timeout must be between 1 and 30")
        return v


class ProcessingConfigUpdate(BaseModel):
    """Partial update model for processing config."""

    chunk_size: Optional[int] = Field(default=None, ge=2000, le=8000)
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_correction_attempts: Optional[int] = Field(default=None, ge=1, le=5)
    batch_size: Optional[int] = Field(default=None, ge=1, le=10)
    per_page_timeout: Optional[int] = Field(default=None, ge=10, le=120)
    total_document_timeout: Optional[int] = Field(default=None, ge=1, le=30)
    store_raw_json: Optional[bool] = None
    auto_classify: Optional[bool] = None
    auto_normalize: Optional[bool] = None


PROCESSING_RECORD_ID = "processing_config:active"


@router.get(
    "/settings/processing", response_model=ProcessingConfigResponse
)
async def get_processing_config():
    """Get processing pipeline configuration."""
    try:
        result = await repo_query(
            "SELECT * FROM ONLY $id",
            {"id": PROCESSING_RECORD_ID},
        )
        if result:
            data = result[0] if isinstance(result, list) else result
            return ProcessingConfigResponse(
                chunk_size=data.get("chunk_size", 4000),
                confidence_threshold=data.get("confidence_threshold", 0.7),
                max_correction_attempts=data.get("max_correction_attempts", 3),
                batch_size=data.get("batch_size", 3),
                per_page_timeout=data.get("per_page_timeout", 60),
                total_document_timeout=data.get("total_document_timeout", 15),
                store_raw_json=data.get("store_raw_json", True),
                auto_classify=data.get("auto_classify", True),
                auto_normalize=data.get("auto_normalize", True),
            )
        return ProcessingConfigResponse()
    except Exception as e:
        logger.error(f"Error fetching processing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/processing", response_model=ProcessingConfigResponse
)
async def update_processing_config(update: ProcessingConfigUpdate):
    """Update processing pipeline configuration (partial update)."""
    try:
        # Get current config as base
        current = await repo_query(
            "SELECT * FROM ONLY $id",
            {"id": PROCESSING_RECORD_ID},
        )
        defaults = ProcessingConfigResponse()
        base = {}
        if current:
            data = current[0] if isinstance(current, list) else current
            base = {f: data.get(f, getattr(defaults, f)) for f in defaults.model_fields}
        else:
            base = defaults.model_dump()

        # Merge provided fields
        for field_name, value in update.model_dump(exclude_none=True).items():
            base[field_name] = value

        # Validate merged result
        merged = ProcessingConfigResponse(**base)
        data = merged.model_dump()

        await repo_query(
            "UPSERT $id SET "
            "chunk_size = $chunk_size, "
            "confidence_threshold = $confidence_threshold, "
            "max_correction_attempts = $max_correction_attempts, "
            "batch_size = $batch_size, "
            "per_page_timeout = $per_page_timeout, "
            "total_document_timeout = $total_document_timeout, "
            "store_raw_json = $store_raw_json, "
            "auto_classify = $auto_classify, "
            "auto_normalize = $auto_normalize, "
            "updated = time::now()",
            {"id": PROCESSING_RECORD_ID, **data},
        )
        return merged
    except Exception as e:
        logger.error(f"Error updating processing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/processing/reset", response_model=ProcessingConfigResponse)
async def reset_processing_config():
    """Reset processing configuration to defaults."""
    try:
        await repo_query("DELETE $id", {"id": PROCESSING_RECORD_ID})
        return ProcessingConfigResponse()
    except Exception as e:
        logger.error(f"Error resetting processing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
