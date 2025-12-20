"""
ACM (Asbestos Containing Material) Record Domain Model

Represents structured data extracted from ACM Register PDF documents.
Each record links to a source document and captures the hierarchical
structure: School > Building > Room > ACM Item.
"""

from enum import Enum
from typing import ClassVar, List, Literal, Optional

from loguru import logger
from pydantic import Field, field_validator


class ExtractionConfidence(str, Enum):
    """Confidence level for extracted ACM records."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class ACMRecord(ObjectModel):
    """
    Domain model for ACM (Asbestos Containing Material) records.

    Represents a single ACM item extracted from a SAMP (Site Asbestos
    Management Plan) or ACM Register document.
    """

    table_name: ClassVar[str] = "acm_record"

    # Foreign key to source document
    source_id: str  # Will be record<source> in DB

    # School identification
    school_name: str
    school_code: Optional[str] = None

    # Building hierarchy
    building_id: str
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None

    # Room hierarchy
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: Optional[str] = None  # "Interior", "Exterior", "Grounds"

    # ACM item data
    product: str
    material_description: str
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None  # "Friable", "Non Friable"
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None  # "Low", "Medium", "High"
    result: str  # "Detected", "Not Detected", etc.

    # Citation support
    page_number: Optional[int] = None

    # New fields for AI-powered extraction (Task 1: E1-S7)
    # All optional for backwards compatibility with existing records
    disturbance_potential: Optional[str] = Field(
        default=None,
        description="Likelihood of material disturbance (e.g., 'Low', 'Medium', 'High')"
    )
    sample_no: Optional[str] = Field(
        default=None,
        description="Sample identification number from lab testing"
    )
    sample_result: Optional[str] = Field(
        default=None,
        description="Laboratory analysis result for the sample"
    )
    identifying_company: Optional[str] = Field(
        default=None,
        description="Hygiene consulting company that performed the inspection"
    )
    quantity: Optional[str] = Field(
        default=None,
        description="Amount or extent of the material (e.g., '10 m²', '5 linear meters')"
    )
    acm_labelled: Optional[bool] = Field(
        default=None,
        description="Whether the ACM has been labeled on-site"
    )
    acm_label_details: Optional[str] = Field(
        default=None,
        description="Details about the ACM labeling (e.g., label type, date)"
    )
    hygienist_recommendations: Optional[str] = Field(
        default=None,
        description="Recommendations from the hygienist for this material"
    )
    psb_supplied_acm_id: Optional[str] = Field(
        default=None,
        description="Unique identifier supplied by PSB (if applicable)"
    )
    removal_status: Optional[str] = Field(
        default=None,
        description="Removal status (e.g., 'N/A', 'Pending', 'Complete', 'Encapsulated')"
    )
    date_of_removal: Optional[str] = Field(
        default=None,
        description="Date when the material was removed (if applicable)"
    )

    # Extraction metadata
    extraction_confidence: Optional[str] = Field(
        default=None,
        description="Confidence level of the extraction: 'high', 'medium', or 'low'"
    )
    data_issues: Optional[List[str]] = Field(
        default=None,
        description="List of data quality issues identified during extraction"
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
        if not v or not v.strip():
            raise InvalidInputError("school_name cannot be empty")
        return v.strip()

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

    def _prepare_save_data(self) -> dict:
        """Override to ensure source_id is proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        return data
