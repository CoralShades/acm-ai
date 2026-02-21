"""Export Field Mapping Domain Model

Maps ACMRecord fields to BAR export columns.

Story: E5-S4 Export Field Mapping Configuration
"""

import json
from pathlib import Path
from typing import ClassVar, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class FieldMappingEntry(BaseModel):
    """Single column mapping: BAR column -> ACMRecord field."""

    bar_column: str = Field(description="BAR export column name")
    bar_column_index: int = Field(description="0-based column position in BAR export")
    acm_field: Optional[str] = Field(
        default=None, description="ACMRecord field name, or None if unmapped"
    )
    is_computed: bool = Field(
        default=False, description="Whether this is a computed/derived field"
    )
    formula: Optional[str] = Field(
        default=None, description="Formula description for computed fields"
    )


class FieldMapping(ObjectModel):
    """Export field mapping configuration."""

    table_name: ClassVar[str] = "field_mapping"

    name: str = Field(default="default", description="Mapping profile name")
    is_active: bool = Field(default=True, description="Whether this mapping is active")
    mappings: List[FieldMappingEntry] = Field(
        default_factory=list, description="Column mappings"
    )
    notes: Optional[str] = None

    @classmethod
    def load_default_mappings(cls) -> List[FieldMappingEntry]:
        """Load default BAR column mappings from JSON."""
        json_path = Path(__file__).parent / "default_bar_mapping.json"
        if not json_path.exists():
            logger.warning("Default BAR mapping JSON not found")
            return []
        data = json.loads(json_path.read_text())
        return [FieldMappingEntry.model_validate(entry) for entry in data]

    @classmethod
    async def get_active(cls) -> "FieldMapping":
        """Get the active field mapping, creating default if none exists."""
        try:
            result = await repo_query(
                "SELECT * FROM field_mapping WHERE is_active = true LIMIT 1"
            )
            if result:
                return cls.model_validate(result[0])
            # Create default
            mapping = cls(
                name="default",
                is_active=True,
                mappings=cls.load_default_mappings(),
            )
            await mapping.save()
            return mapping
        except Exception as e:
            logger.error(f"Failed to get active field mapping: {e}")
            raise DatabaseOperationError(
                f"Failed to get active field mapping: {e}"
            ) from e

    @classmethod
    async def reset_to_defaults(cls) -> "FieldMapping":
        """Reset to default BAR mapping."""
        try:
            await repo_query("DELETE FROM field_mapping")
            mapping = cls(
                name="default",
                is_active=True,
                mappings=cls.load_default_mappings(),
            )
            await mapping.save()
            return mapping
        except Exception as e:
            logger.error(f"Failed to reset field mapping: {e}")
            raise DatabaseOperationError(
                f"Failed to reset field mapping: {e}"
            ) from e
