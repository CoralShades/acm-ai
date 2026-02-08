"""
BAR Field Schema Configuration Models.

Pydantic models for the configurable field schema that drives the generic
parser, AG Grid columns, and export field ordering.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

from typing import Optional

from pydantic import BaseModel


class FieldDef(BaseModel):
    """Definition of a single BAR register field."""

    internal_name: str
    display_name: str
    excel_column: str
    col_index: int
    field_type: str  # "string" | "number" | "date" | "enum"
    required: bool
    active: bool = True
    enum_name: Optional[str] = None
    group: Optional[str] = None


class BusinessRule(BaseModel):
    """A BAR compliance business rule."""

    rule_id: str
    description: str
    enabled: bool = True


class FieldSchemaConfig(BaseModel):
    """Complete field schema configuration."""

    fields: list[FieldDef]
    enums: dict[str, list[str]]
    business_rules: list[BusinessRule]
    version: str
    source_template: Optional[str] = None

    def get_display_to_internal_map(self) -> dict[str, str]:
        """Map BAR display names to internal field names."""
        return {f.display_name: f.internal_name for f in self.fields}

    def get_column_to_internal_map(self) -> dict[str, str]:
        """Map BAR Excel column letters to internal field names."""
        return {f.excel_column: f.internal_name for f in self.fields}

    def get_active_fields(self) -> list[FieldDef]:
        """Return only active fields."""
        return [f for f in self.fields if f.active]
