"""BAR Template Domain Model

Stores uploaded Victorian Government BAR Excel template metadata,
including parsed column structure for export compliance validation.

Story: E5-S3 BAR Template Management
"""

from datetime import UTC, datetime
from typing import ClassVar, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class BARTemplateColumn(BaseModel):
    """A single column parsed from a BAR template header row."""

    column_letter: str = Field(description="Excel column letter (A, B, AA, etc.)")
    column_name: str = Field(description="Header text from template")
    field_type: Optional[str] = Field(
        default=None, description="Inferred type: text, enum, date, number"
    )
    is_required: bool = Field(default=False)


class BARTemplate(ObjectModel):
    """BAR Excel template with parsed column structure."""

    table_name: ClassVar[str] = "bar_template"

    filename: str = Field(description="Original upload filename")
    version_label: str = Field(description="Version label (e.g., v2024.1)")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    is_active: bool = Field(default=False)
    column_count: int = Field(default=0)
    columns: List[BARTemplateColumn] = Field(default_factory=list)
    raw_header_row: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)

    @classmethod
    async def get_active(cls) -> Optional["BARTemplate"]:
        """Get the currently active BAR template."""
        try:
            result = await repo_query(
                "SELECT * FROM bar_template WHERE is_active = true LIMIT 1"
            )
            if result:
                return cls.model_validate(result[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get active BAR template: {e}")
            raise DatabaseOperationError(f"Failed to get active template: {e}") from e

    @classmethod
    async def deactivate_all(cls) -> int:
        """Deactivate all templates. Returns count of deactivated."""
        try:
            result = await repo_query(
                "UPDATE bar_template SET is_active = false WHERE is_active = true"
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Failed to deactivate templates: {e}")
            raise DatabaseOperationError(f"Failed to deactivate templates: {e}") from e

    async def activate(self) -> "BARTemplate":
        """Set this template as active, deactivating all others."""
        await BARTemplate.deactivate_all()
        self.is_active = True
        await self.save()
        return self

    @classmethod
    async def get_by_id(cls, template_id: str) -> Optional["BARTemplate"]:
        """Get a template by ID."""
        try:
            rid = ensure_record_id(template_id, "bar_template")
            result = await repo_query(
                "SELECT * FROM bar_template WHERE id = $id LIMIT 1",
                {"id": rid},
            )
            if result:
                return cls.model_validate(result[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get BAR template {template_id}: {e}")
            raise DatabaseOperationError(f"Failed to get template: {e}") from e
