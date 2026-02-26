"""Extraction Settings Domain Model

Global configuration for ACM extraction pipeline behavior.
Stores extraction method preferences and Document Intelligence stage toggles.

Story: E12-S1 Extraction Method Settings UI
"""

from typing import ClassVar, Optional

from loguru import logger
from pydantic import Field

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class ExtractionSettings(ObjectModel):
    """Global extraction pipeline settings."""

    table_name: ClassVar[str] = "extraction_settings"

    # Extraction method: "mineru", "docling", "hybrid"
    extraction_method: str = Field(
        default="hybrid",
        description="Primary extraction method: mineru, docling, or hybrid",
    )
    # Whether to fall back to alternative method on failure
    fallback_enabled: bool = Field(
        default=True,
        description="Enable fallback to alternative extraction method on failure",
    )

    # Document Intelligence stages (E1-S16..S19)
    enable_toc_extraction: bool = Field(
        default=True, description="Extract table of contents structure"
    )
    enable_building_inventory: bool = Field(
        default=True, description="Compile building inventory from TOC"
    )
    enable_page_tagging: bool = Field(
        default=True, description="Tag pages with section classifications"
    )
    enable_metadata_enhancement: bool = Field(
        default=True, description="Enhance records with document metadata"
    )

    # Corrective RAG
    enable_corrective_rag: bool = Field(
        default=True, description="Enable corrective RAG validation loop"
    )
    max_correction_attempts: int = Field(
        default=2, description="Maximum correction attempts per chunk"
    )

    @classmethod
    async def get_instance(cls) -> "ExtractionSettings":
        """Get the singleton extraction settings record.

        Creates default settings if none exist.
        """
        try:
            result = await repo_query("SELECT * FROM extraction_settings LIMIT 1")
            if result:
                return cls.model_validate(result[0])
            # Create default settings
            settings = cls()
            await settings.save()
            return settings
        except Exception as e:
            logger.error(f"Failed to get extraction settings: {e}")
            raise DatabaseOperationError(
                f"Failed to get extraction settings: {e}"
            ) from e

    @classmethod
    async def reset_to_defaults(cls) -> "ExtractionSettings":
        """Reset extraction settings to defaults."""
        try:
            await repo_query("DELETE FROM extraction_settings")
            settings = cls()
            await settings.save()
            return settings
        except Exception as e:
            logger.error(f"Failed to reset extraction settings: {e}")
            raise DatabaseOperationError(
                f"Failed to reset extraction settings: {e}"
            ) from e
