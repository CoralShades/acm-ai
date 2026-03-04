"""
BAR Field Schema Configuration Models.

Pydantic models for the configurable field schema that drives the generic
parser, AG Grid columns, and export field ordering.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

from typing import Any, Optional

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


# =============================================================================
# SF Field Schema Models (E30-S1 — V3 Foundation)
# =============================================================================


class SFFieldDef(BaseModel):
    """Definition of a single Salesforce object field."""

    api_name: str  # e.g. "Building_Type__c" — primary key
    label: str  # e.g. "Asset Type"
    field_type: str  # "string" | "picklist" | "boolean" | "date" | "datetime"
    # | "double" | "currency" | "reference" | "textarea"
    # | "id" | "location" | "url"
    length: Optional[int] = None
    nillable: bool = True
    custom: bool = False
    calc: bool = False  # Formula/rollup field
    updateable: bool = True
    notes: Optional[str] = None
    is_restricted_picklist: bool = False  # Derived from notes "Restricted picklist"
    is_dependent: bool = False  # Dependent on a controller picklist
    controller_field: Optional[str] = None  # API name of controller (if dependent)


class SFFieldSchemaConfig(BaseModel):
    """Complete Salesforce object field schema configuration."""

    object_name: str  # "Building__c" or "Item__c"
    object_label: str  # "Asset Class" or "Item"
    total_fields: int
    custom_fields: int
    picklist_fields: int
    fields: list[SFFieldDef]
    picklists: dict[str, list[str]]  # api_name -> [values]
    version: str = "salesforce-v1"


class SFDependencyChain(BaseModel):
    """A dependent picklist chain mapping."""

    controller_api_name: str  # e.g. "Friability_of_Material__c"
    dependent_api_name: str  # e.g. "ACM_Classification__c"
    # controller_value -> valid dependent value(s).
    # For item picklist chains: list[str] (multiple product types per classification).
    # For building type chain: str (single category per building type).
    mapping: dict[str, Any]


class SFSchemaBundle(BaseModel):
    """Full SF schema bundle stored in field_schema:sf_v1."""

    version: str = "salesforce-v1"
    building_fields: SFFieldSchemaConfig
    item_fields: SFFieldSchemaConfig
    picklists: dict[str, list[str]]  # Combined picklists across both objects
    dependencies: list[SFDependencyChain]  # All dependency chains
    loaded_at: Optional[str] = None  # ISO timestamp when loaded
