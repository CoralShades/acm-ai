"""
ACM (Asbestos Containing Material) Record Domain Model

Represents structured data extracted from ACM Register PDF documents.
Each record links to a source document and captures the hierarchical
structure: School > Building > Room > ACM Item.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import ClassVar, List, Literal, Optional

from loguru import logger
from pydantic import AliasChoices, ConfigDict, Field, field_validator


class ExtractionConfidence(str, Enum):
    """Confidence level for extracted ACM records."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ACMEmbeddingConfig:
    """Configuration for ACM embedding pipeline.

    Controls how ACM records are embedded for semantic search.
    Uses dataclass for lightweight configuration without Pydantic overhead.
    """

    enabled: bool = True
    model_id: Optional[str] = None  # Falls back to default embedding model if None
    batch_size: int = 50
    include_fields: List[str] = dataclass_field(
        default_factory=lambda: [
            "building_name",
            "room_name",
            "product",
            "material_description",
            "location",
            "extent",
            "material_condition",
            "risk_status",
            "friable",
            "result",
            "hygienist_recommendations",
        ]
    )


from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class ACMRecord(ObjectModel):
    """
    Domain model for ACM (Asbestos Containing Material) records.

    Represents a single ACM item extracted from an ARA (Asbestos Register
    Assessment) or ACM Register document.
    """

    table_name: ClassVar[str] = "acm_record"

    model_config = ConfigDict(populate_by_name=True)

    # Foreign key to source document
    source_id: str  # Will be record<source> in DB

    # School identification
    school_name: Optional[str] = None
    school_code: Optional[str] = None

    # Building hierarchy
    building_id: str = Field(
        ...,
        validation_alias=AliasChoices("building_id", "Building_Code__c"),
        description="Building identifier (Building_Code__c)",
    )
    building_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_name", "Building_Name__c"),
    )
    building_year: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("building_year", "Building_Year__c"),
    )
    building_construction: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_construction", "Building_Construction__c"
        ),
    )
    building_address: Optional[str] = Field(
        default=None,
        description="Street address of the building (from report header/metadata)",
    )
    suburb: Optional[str] = Field(
        default=None,
        description="Suburb or locality of the building",
    )
    postcode: Optional[str] = Field(
        default=None,
        description="Postcode of the building location",
    )
    building_type: Optional[str] = Field(
        default=None,
        description="Type of building (e.g., 'Permanent', 'Demountable', 'Heritage')",
    )

    # FK to building_record table (E30-S2, optional until E30-S5 data migration)
    building_record_id: Optional[str] = Field(
        default=None,
        description="FK to building_record table (record<building_record> in DB). "
        "Populated by E30-S5 data migration.",
    )

    # Room hierarchy
    room_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("room_id", "Room_ID__c"),
    )
    room_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("room_name", "Room_or_Area__c"),
    )
    room_area: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("room_area", "Room_Area__c"),
    )
    area_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("area_type", "Internal_External__c"),
        description="Area type: 'Interior', 'Exterior', 'Grounds' / 'Internal', 'External' (SF)",
    )
    floor_level: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("floor_level", "Level__c"),
        description="Floor level (e.g., 'Ground', 'Level 1', 'Roof')",
    )

    # Inspection metadata
    date_of_inspection: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("date_of_inspection", "Survey_Date__c"),
        description="Date of the inspection/audit (from report header or metadata)",
    )

    # ACM item data
    product: str = Field(
        ...,
        validation_alias=AliasChoices("product", "Item_Name__c"),
        description="ACM product name",
    )
    material_description: str = Field(
        ...,
        validation_alias=AliasChoices(
            "material_description", "Material_Description__c"
        ),
        description="Detailed description of the ACM material",
    )
    extent: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("extent", "Extent__c"),
    )
    location: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("location", "Location_in_Room__c"),
    )
    friable: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("friable", "Friability_of_Material__c"),
        description="Friability: 'Friable' or 'Non-friable'",
    )
    material_condition: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("material_condition", "Condition__c"),
    )
    risk_status: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("risk_status", "Risk_Rating__c"),
        description="Risk level: 'Low', 'Medium', 'High'",
    )
    result: str = Field(
        ...,
        validation_alias=AliasChoices(
            "result", "Sample_Analysis_Result_Material_Status__c"
        ),
        description="Asbestos sample result",
    )

    # Citation support
    page_number: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("page_number", "Page_Number__c"),
    )

    # Bounding box for provenance linking (MinerU integration)
    table_bbox: Optional[dict] = Field(
        default=None,
        description="Table bounding box coordinates: {x, y, width, height, page}",
    )

    # New fields for AI-powered extraction (Task 1: E1-S7)
    # All optional for backwards compatibility with existing records
    disturbance_potential: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "disturbance_potential", "Disturbance_Potential_of_Material__c"
        ),
        description="Likelihood of material disturbance (e.g., 'Low', 'Medium', 'High')",
    )
    sample_no: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("sample_no", "NATA_Endorsed_Sample_no__c"),
        description="Sample identification number from lab testing",
    )
    sample_result: Optional[str] = Field(
        default=None, description="Laboratory analysis result for the sample"
    )
    identifying_company: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "identifying_company", "Identifying_Hygiene_Consulting_Company__c"
        ),
        description="Hygiene consulting company that performed the inspection",
    )
    quantity: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("quantity", "Quantity__c"),
        description="Amount or extent of the material (e.g., '10 m²', '5 linear meters')",
    )
    acm_labelled: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("acm_labelled", "ACM_Labelled__c"),
        description="Whether the ACM has been labeled on-site",
    )
    acm_label_details: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("acm_label_details", "Labelled_Details__c"),
        description="Details about the ACM labeling (e.g., label type, date)",
    )
    hygienist_recommendations: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "hygienist_recommendations", "Hygienist_Recommendations__c"
        ),
        description="Recommendations from the hygienist for this material",
    )
    psb_supplied_acm_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("psb_supplied_acm_id", "ID_provided_by_metro__c"),
        description="Unique identifier supplied by PSB (if applicable)",
    )
    removal_status: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("removal_status", "Removal_Status__c"),
        description="Removal status (e.g., 'N/A', 'Pending', 'Complete', 'Encapsulated')",
    )
    date_of_removal: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("date_of_removal", "Removed_Date__c"),
        description="Date when the material was removed (if applicable)",
    )
    quantity_removed: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("quantity_removed", "Quantity_Removed__c"),
        description="Quantity of material removed (e.g., '10 m²', '5 linear meters')",
    )
    removal_notification_no: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "removal_notification_no", "Asbestos_Removal_Notification_No__c"
        ),
        description="Removal notification number for regulatory compliance",
    )
    epa_certificate_no: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "epa_certificate_no", "EPA_Waste_Transport_Certificate_No__c"
        ),
        description="EPA clearance certificate number after removal",
    )
    no_access: Optional[bool] = Field(
        default=False,
        validation_alias=AliasChoices("no_access", "No_Access__c"),
        description="Record has no access to the location",
    )
    smf_present: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("smf_present", "SMF_Present__c"),
        description="Synthetic Mineral Fibre present (Yes/No/Unknown)",
    )
    additional_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("additional_comments", "Additional_Comments__c"),
        description="Additional comments or notes about the ACM item",
    )

    # New SF Item__c fields (E30-S3)
    labelled_sf: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("labelled_sf", "Labelled__c"),
        description="SF picklist: 'Yes', 'No', 'Unknown' (maps to acm_labelled bool)",
    )
    assea_risk_level: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "assea_risk_level", "ASSEA_Survey_Guide_Risk_Level__c"
        ),
        description="ASSEA Survey Guide risk level (separate from risk_status)",
    )
    date_identified: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("date_identified", "Date_Identified__c"),
        description="Date the ACM was first identified/recorded",
    )

    # Extraction metadata
    extraction_confidence: Optional[str] = Field(
        default=None,
        description="Confidence level of the extraction: 'high', 'medium', or 'low'",
    )
    data_issues: Optional[List[str]] = Field(
        default=None,
        description="List of data quality issues identified during extraction",
    )

    # Validation tracking (AC6 — E32-S3)
    validation_status: Optional[str] = Field(
        default=None,
        description=(
            "Validation outcome: 'valid', 'corrected', 'failed_correction', 'invalid'. "
            "Populated during extraction pipeline."
        ),
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Validation error strings from final validation pass.",
    )
    correction_attempts: int = Field(
        default=0,
        description="Number of LLM correction attempts made for this record (max 3).",
    )

    # Recommendation normalization (E1-S12: Consultant wording normalization)
    normalized_action: Optional[str] = Field(
        default=None,
        description="Canonical action from recommendation normalization (e.g., 'maintain_in_situ')",
    )

    # Product Classification fields (E1-S9: ACM taxonomy)
    acm_product_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("acm_product_group", "ACM_Classification__c"),
        description="SF taxonomy product group (e.g., 'Vinyl products')",
    )
    acm_product_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("acm_product_type", "ACM_Sub_Classification__c"),
        description="ACM taxonomy product type (e.g., 'Vinyl Tiles')",
    )
    classification_confidence: Optional[float] = Field(
        default=None, description="Confidence score for the classification (0.0-1.0)"
    )
    classification_override: Optional[bool] = Field(
        default=None, description="Whether the classification was manually overridden"
    )
    classification_method: Optional[str] = Field(
        default=None, description="Classification method: 'pattern', 'llm', or 'manual'"
    )

    # Embedding fields for semantic search (E1-S6)
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding for semantic search"
    )
    embedding_text: Optional[str] = Field(
        default=None, description="Combined text used to generate the embedding"
    )
    embedding_model: Optional[str] = Field(
        default=None, description="Model ID used to generate the embedding"
    )
    embedded_at: Optional[datetime] = Field(
        default=None, description="Timestamp when embedding was generated"
    )
    enriched_text: Optional[str] = Field(
        default=None,
        description="Contextually enriched text with hierarchical metadata for embedding (E1-S14)",
    )

    # Parent document retrieval (E11-S1)
    parent_table_id: Optional[str] = Field(
        default=None,
        description="Reference to parent ACMTableSection for table-level context",
    )

    # Validators for required fields
    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        # Ensure proper record format
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("school_name")
    @classmethod
    def validate_school_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("building_id")
    @classmethod
    def validate_building_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("building_id cannot be empty")
        return v.strip()

    @field_validator("product")
    @classmethod
    def validate_product(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("product cannot be empty")
        return v.strip()

    @field_validator("material_description")
    @classmethod
    def validate_material_description(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("material_description cannot be empty")
        return v.strip()

    @field_validator("result")
    @classmethod
    def validate_result(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("result cannot be empty")
        return v.strip()

    @field_validator("extraction_confidence")
    @classmethod
    def validate_extraction_confidence(cls, v):
        """Validate extraction_confidence is one of: high, medium, low."""
        if v is None:
            return v
        valid_values = {"high", "medium", "low"}
        v_lower = v.lower().strip() if isinstance(v, str) else v
        if v_lower not in valid_values:
            raise InvalidInputError(
                f"extraction_confidence must be one of {valid_values}, got '{v}'"
            )
        return v_lower

    @field_validator("normalized_action")
    @classmethod
    def validate_normalized_action(cls, v):
        """Validate normalized_action is a known canonical action."""
        if v is None:
            return v
        from open_notebook.extractors.normalizers.recommendations import (
            CANONICAL_ACTIONS,
        )

        if v not in CANONICAL_ACTIONS:
            logger.warning(
                f"normalized_action '{v}' is not a recognized canonical action"
            )
        return v

    # Class methods for filtered queries
    @classmethod
    async def get_by_source(cls, source_id: str) -> List["ACMRecord"]:
        """Get all ACM records for a specific source document."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM acm_record WHERE source_id = $source_id ORDER BY building_id, room_id",
                {"source_id": ensure_record_id(source_id)},
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching ACM records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_building(
        cls, building_id: str, source_id: Optional[str] = None
    ) -> List["ACMRecord"]:
        """Get all ACM records for a specific building."""
        if not building_id:
            raise InvalidInputError("building_id is required")
        try:
            if source_id:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE building_id = $building_id AND source_id = $source_id ORDER BY room_id",
                    {
                        "building_id": building_id,
                        "source_id": ensure_record_id(source_id),
                    },
                )
            else:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE building_id = $building_id ORDER BY room_id",
                    {"building_id": building_id},
                )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching ACM records for building {building_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_risk_status(
        cls, risk_status: str, source_id: Optional[str] = None
    ) -> List["ACMRecord"]:
        """Get all ACM records with a specific risk status."""
        if not risk_status:
            raise InvalidInputError("risk_status is required")
        try:
            if source_id:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE risk_status = $risk_status AND source_id = $source_id",
                    {
                        "risk_status": risk_status,
                        "source_id": ensure_record_id(source_id),
                    },
                )
            else:
                result = await repo_query(
                    "SELECT * FROM acm_record WHERE risk_status = $risk_status",
                    {"risk_status": risk_status},
                )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(
                f"Error fetching ACM records with risk status {risk_status}: {e}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def get_summary_by_source(cls, source_id: str) -> dict:
        """Get summary statistics for ACM records in a source."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                """
                SELECT
                    count() as total_records,
                    count(risk_status = 'High' OR NULL) as high_risk_count,
                    count(risk_status = 'Medium' OR NULL) as medium_risk_count,
                    count(risk_status = 'Low' OR NULL) as low_risk_count,
                    array::distinct(building_id) as buildings,
                    array::distinct(room_id) as rooms
                FROM acm_record
                WHERE source_id = $source_id
                GROUP ALL
                """,
                {"source_id": ensure_record_id(source_id)},
            )
            if result:
                summary = result[0]
                return {
                    "total_records": summary.get("total_records", 0),
                    "high_risk_count": summary.get("high_risk_count", 0),
                    "medium_risk_count": summary.get("medium_risk_count", 0),
                    "low_risk_count": summary.get("low_risk_count", 0),
                    "building_count": len(summary.get("buildings", [])),
                    "room_count": len([r for r in summary.get("rooms", []) if r]),
                }
            return {
                "total_records": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "building_count": 0,
                "room_count": 0,
            }
        except Exception as e:
            logger.error(f"Error getting ACM summary for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all ACM records for a source. Returns count of deleted records."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE acm_record WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting ACM records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    # Instance methods
    async def get_source(self):
        """Get the source document this record was extracted from."""
        from open_notebook.domain.notebook import Source

        return await Source.get(self.source_id)

    def get_enriched_embedding_text(self) -> str:
        """Generate text with hierarchical context for embedding (E1-S14).

        Prepends Level and Page context (not already in raw text) to the
        raw embedding text. Building and Room are already in get_embedding_text()
        so they are not duplicated here.
        Skips context fields that are None.
        """
        context_parts = []
        if self.area_type:
            context_parts.append(f"Level: {self.area_type}")
        if self.page_number:
            context_parts.append(f"Page: {self.page_number}")

        raw_text = self.get_embedding_text()

        if context_parts and raw_text:
            return " | ".join(context_parts) + " | " + raw_text
        return raw_text or " | ".join(context_parts) or ""

    def get_embedding_text(self) -> str:
        """
        Generate text for embedding from key ACM record fields.

        Combines relevant fields to create searchable text for semantic search.
        Fields are selected based on their relevance for compliance queries.
        """
        # Fields to include in embedding (ordered by importance)
        field_mappings = [
            ("Building", self.building_name),
            ("Room", self.room_name),
            ("Product", self.product),
            ("Material", self.material_description),
            ("Location", self.location),
            ("Extent", self.extent),
            ("Condition", self.material_condition),
            ("Risk", self.risk_status),
            ("Friable", self.friable),
            ("Result", self.result),
            ("Recommendations", self.hygienist_recommendations),
        ]

        parts = []
        for label, value in field_mappings:
            if value:
                parts.append(f"{label}: {value}")

        return " | ".join(parts) if parts else ""

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id, parent_table_id, and building_record_id are proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        if data.get("parent_table_id"):
            data["parent_table_id"] = ensure_record_id(data["parent_table_id"])
        if data.get("building_record_id"):
            data["building_record_id"] = ensure_record_id(data["building_record_id"])
        return data


class BuildingRecord(ObjectModel):
    """
    Domain model for Building records.

    Represents a physical building extracted from ARA documents.
    Maps to the Salesforce Building__c object with AliasChoices
    for dual internal/SF field name support.

    Linked to ACMRecords via acm_record.building_record_id FK.
    """

    table_name: ClassVar[str] = "building_record"

    model_config = ConfigDict(populate_by_name=True)

    # --- Core identification ---
    internal_id: str = Field(
        ...,
        description="Server-generated ID: BLD#{source_short}_{seq:03d}",
    )
    source_id: str = Field(
        ...,
        description="FK to source document (record<source> in DB)",
    )
    building_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_code", "Building_Code__c"),
        description="Original building identifier from PDF (was building_id on ACMRecord)",
    )

    # --- Fields also on ACMRecord (building-level) ---
    building_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_name", "Building_Name__c"),
    )
    building_year: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_year", "Estimated_Year_Build_New__c"),
        description="Year built (SF picklist, stored as string)",
    )
    building_construction: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_construction", "Construction_Type__c"),
    )
    building_address: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_address", "Building_Address__c"),
    )
    suburb: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("suburb", "Suburb__c"),
    )
    postcode: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("postcode", "Postcode__c"),
    )
    building_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_type", "Building_Type__c"),
    )

    # --- Additional SF Building__c fields ---
    building_category: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_category", "Building_Category__c"),
        description="Dependent on Building_Type__c",
    )
    building_address_lga: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_address_lga", "Building_Address_LGA__c"
        ),
    )
    building_address_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_address_region", "Building_Address_Region__c"
        ),
    )
    roof_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("roof_type", "Roof_Type__c"),
    )
    number_of_levels: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("number_of_levels", "Number_of_Levels__c"),
    )
    est_building_size_m2: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices(
            "est_building_size_m2", "Est_Building_Size_m2__c"
        ),
    )
    frequency_of_use: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("frequency_of_use", "Frequency_of_Use__c"),
    )
    daily_duration: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("daily_duration", "Daily_Duration__c"),
    )
    level_of_activity: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("level_of_activity", "Level_of_Activity__c"),
    )
    public_access: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_access", "Public_Access__c"),
    )
    mobile_plant: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("mobile_plant", "Mobile_Plant__c"),
    )
    owned_or_leased: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("owned_or_leased", "Owned_or_Leased__c"),
    )
    asbestos_register_available: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "asbestos_register_available", "Asbestos_Register_Available__c"
        ),
    )
    audit_report_available: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "audit_report_available", "Audit_Report_Available__c"
        ),
    )
    date_of_audit_report: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "date_of_audit_report", "Date_of_Audit_Report__c"
        ),
    )
    no_identified_acms: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("no_identified_acms", "No_Identified_ACMs__c"),
    )
    no_identified_acms_note: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "no_identified_acms_note", "No_Identified_ACMs_Note__c"
        ),
    )
    site_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("site_name", "Site_Name__c"),
    )
    school_uid: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("school_uid", "School_UID__c"),
    )
    building_unique_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("building_unique_id", "Building_Unique_ID__c"),
    )
    external_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("external_id", "External_ID__c"),
    )
    building_out_of_scope: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_out_of_scope", "Building_Out_Of_Scope_New__c"
        ),
    )
    building_out_of_scope_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_out_of_scope_comments", "Building_Out_Of_Scope_Comments__c"
        ),
    )
    demolished_status: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolished_status", "Demolished_Status__c"),
    )
    demolition_date: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_date", "Demolition_Date__c"),
    )
    demolition_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_type", "Demolition_Type__c"),
    )
    demolition_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("demolition_comments", "Demolition_Comments__c"),
    )
    additional_comments: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("additional_comments", "Additional_Comments__c"),
    )
    within_your_portfolio: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "within_your_portfolio", "Within_Your_Portfolio__c"
        ),
    )
    psb_district_region: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("psb_district_region", "PSB_District_Region__c"),
    )
    state: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("state", "State__c"),
    )
    country: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("country", "Country__c"),
    )
    gps_coordinates: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "gps_coordinates", "GPS_Coordinates_provided_by_metro__c"
        ),
    )
    capital_works_project_details: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "capital_works_project_details",
            "Capital_Works_Project_Provide_Details__c",
        ),
    )
    possible_capital_works_project: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "possible_capital_works_project", "Possible_Capital_Works_Project__c"
        ),
    )
    building_sub_category: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_sub_category", "Building_Sub_Category__c"
        ),
    )
    building_risk_rating: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "building_risk_rating", "Building_Risk_Rating__c"
        ),
    )

    # --- Embedding fields (AC8) ---
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding for semantic search"
    )
    embedding_text: Optional[str] = Field(
        default=None, description="Combined text used to generate the embedding"
    )
    embedding_model: Optional[str] = Field(
        default=None, description="Model ID used to generate the embedding"
    )
    embedded_at: Optional[datetime] = Field(
        default=None, description="Timestamp when embedding was generated"
    )
    enriched_text: Optional[str] = Field(
        default=None, description="Contextually enriched text for embedding"
    )

    # --- Validators ---
    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("internal_id")
    @classmethod
    def validate_internal_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("internal_id cannot be empty")
        v = v.strip()
        if not v.startswith("BLD#"):
            raise InvalidInputError(f"internal_id must start with 'BLD#', got '{v}'")
        return v

    # --- Class methods ---
    @classmethod
    async def get_by_source(cls, source_id: str) -> List["BuildingRecord"]:
        """Get all building records for a specific source document."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM building_record WHERE source_id = $source_id ORDER BY internal_id",
                {"source_id": ensure_record_id(source_id)},
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching building records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_internal_id(cls, internal_id: str) -> Optional["BuildingRecord"]:
        """Get a building record by its internal_id."""
        if not internal_id:
            raise InvalidInputError("internal_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM building_record WHERE internal_id = $internal_id LIMIT 1",
                {"internal_id": internal_id},
            )
            return cls(**result[0]) if result else None
        except Exception as e:
            logger.error(
                f"Error fetching building record by internal_id {internal_id}: {e}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all building records for a source. Returns count of deleted records."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE building_record WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting building records for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def generate_internal_id(cls, source_id: str) -> str:
        """Generate BLD#{source_short}_{seq:03d} for a new building.

        source_short = first 8 chars of source name (uppercase, spaces to underscore).
        seq = count of existing BuildingRecords for this source + 1.
        """
        from open_notebook.domain.notebook import Source

        if isinstance(source_id, str) and not source_id.startswith("source:"):
            source_id = f"source:{source_id}"
        source = await Source.get(source_id)
        source_label = source.title or ""
        source_short = (
            source_label[:8].upper().replace(" ", "_") if source_label else "UNKNOWN"
        )
        existing = await cls.get_by_source(source_id)
        seq = len(existing) + 1
        return f"BLD#{source_short}_{seq:03d}"

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data


class ACMTableSection(ObjectModel):
    """Parent document model for ACM table sections (E11-S1).

    Represents a full table section extracted from a PDF, spanning one or more
    pages. Individual ACMRecords link back to their parent section via
    parent_table_id, enabling parent-document retrieval for richer search context.
    """

    table_name: ClassVar[str] = "acm_table_section"

    source_id: str  # record<source> in DB
    page_start: int
    page_end: int
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None
    building_name: Optional[str] = None
    table_type: Optional[str] = Field(
        default=None,
        description="Type of table section: 'register', 'lab_report', or 'metadata'",
    )
    consensus_tier: Optional[str] = Field(
        default=None,
        description="How consensus was reached: 'single_provider' | 'multi_provider_agreement' | 'multi_provider_conflict' | 'manual_override'",
    )
    consensus_scores: Optional[dict] = Field(
        default=None,
        description="Per-provider confidence scores and agreement score: {provider_id: float, ..., agreement: float}",
    )

    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @classmethod
    async def get_by_source(cls, source_id: str) -> List["ACMTableSection"]:
        """Get all table sections for a specific source document."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM acm_table_section WHERE source_id = $source_id ORDER BY page_start",
                {"source_id": ensure_record_id(source_id)},
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching table sections for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_page_range(
        cls, source_id: str, page: int
    ) -> Optional["ACMTableSection"]:
        """Find the table section that contains the given page number."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "SELECT * FROM acm_table_section WHERE source_id = $source_id AND page_start <= $page AND page_end >= $page LIMIT 1",
                {"source_id": ensure_record_id(source_id), "page": page},
            )
            return cls(**result[0]) if result else None
        except Exception as e:
            logger.error(
                f"Error fetching table section for source {source_id} page {page}: {e}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all table sections for a source. Returns count of deleted sections."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE acm_table_section WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting table sections for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data


class RawExtraction(ObjectModel):
    """Per-provider raw extraction output stored before consensus merge (E31-S4).

    One row per provider per page per extraction run. Stores the raw HTML,
    markdown, and structured JSON emitted by a provider adapter, along with
    bounding box and confidence data for provenance tracking.

    The officer_edits field accumulates an audit trail of manual corrections
    applied to this raw extraction row.
    """

    table_name: ClassVar[str] = "raw_extraction"

    # FK to source document
    source_id: str

    # Provider identification
    provider_id: str = Field(
        ...,
        description="Stable provider ID from ProviderRegistry (e.g. 'docling', 'mineru')",
    )
    extraction_backend: str = Field(
        ...,
        description="Provider + version string (e.g. 'docling:2.x', 'mineru:2.7')",
    )

    # Page-level data
    page_number: int = Field(
        ...,
        description="1-based page number from NormalizedTable.page",
    )

    # Raw outputs
    raw_html: Optional[str] = None
    raw_markdown: Optional[str] = None
    structured_json: Optional[str] = Field(
        default=None,
        description="JSON-serialised column headers + row data from NormalizedTable",
    )

    # Provenance
    bbox: Optional[dict] = Field(
        default=None,
        description="Bounding box dict {x, y, width, height, page} from NormalizedTable.bbox",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Overall table confidence (0.0-1.0) from the provider",
    )

    # Audit trail
    officer_edits: List[dict] = Field(
        default_factory=list,
        description="Ordered list of officer edit events applied to this raw row",
    )

    # Timestamp
    created_at: Optional[datetime] = None

    @field_validator("source_id", mode="before")
    @classmethod
    def validate_source_id(cls, v):
        if not v:
            raise InvalidInputError("source_id is required")
        if isinstance(v, str) and not v.startswith("source:"):
            return f"source:{v}"
        return str(v)

    @field_validator("provider_id")
    @classmethod
    def validate_provider_id(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("provider_id cannot be empty")
        return v.strip()

    @field_validator("page_number")
    @classmethod
    def validate_page_number(cls, v):
        if v < -1:
            raise InvalidInputError("page_number must be >= -1 (-1 means unknown)")
        return v

    @classmethod
    async def get_by_source(
        cls,
        source_id: str,
        provider: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List["RawExtraction"]:
        """Get raw extractions for a source, with optional provider and page filters."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            conditions = ["source_id = $source_id"]
            params: dict = {"source_id": ensure_record_id(source_id)}

            if provider:
                conditions.append("provider_id = $provider_id")
                params["provider_id"] = provider

            if page_number is not None:
                conditions.append("page_number = $page_number")
                params["page_number"] = page_number

            where_clause = " AND ".join(conditions)
            result = await repo_query(
                f"SELECT * FROM raw_extraction WHERE {where_clause} ORDER BY page_number, provider_id",
                params,
            )
            return [cls(**record) for record in result]
        except Exception as e:
            logger.error(f"Error fetching raw extractions for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_source(cls, source_id: str) -> int:
        """Delete all raw extractions for a source. Returns count deleted."""
        if not source_id:
            raise InvalidInputError("source_id is required")
        try:
            result = await repo_query(
                "DELETE raw_extraction WHERE source_id = $source_id RETURN BEFORE",
                {"source_id": ensure_record_id(source_id)},
            )
            return len(result) if result else 0
        except Exception as e:
            logger.error(f"Error deleting raw extractions for source {source_id}: {e}")
            raise DatabaseOperationError(e)

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data
