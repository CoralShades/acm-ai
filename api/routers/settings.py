from typing import Literal

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api.models import SettingsResponse, SettingsUpdate
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
