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
from pydantic import Field, field_validator


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

    # Bounding box for provenance linking (MinerU integration)
    table_bbox: Optional[dict] = Field(
        default=None,
        description="Table bounding box coordinates: {x, y, width, height, page}",
    )

    # New fields for AI-powered extraction (Task 1: E1-S7)
    # All optional for backwards compatibility with existing records
    disturbance_potential: Optional[str] = Field(
        default=None,
        description="Likelihood of material disturbance (e.g., 'Low', 'Medium', 'High')",
    )
    sample_no: Optional[str] = Field(
        default=None, description="Sample identification number from lab testing"
    )
    sample_result: Optional[str] = Field(
        default=None, description="Laboratory analysis result for the sample"
    )
    identifying_company: Optional[str] = Field(
        default=None,
        description="Hygiene consulting company that performed the inspection",
    )
    quantity: Optional[str] = Field(
        default=None,
        description="Amount or extent of the material (e.g., '10 m²', '5 linear meters')",
    )
    acm_labelled: Optional[bool] = Field(
        default=None, description="Whether the ACM has been labeled on-site"
    )
    acm_label_details: Optional[str] = Field(
        default=None,
        description="Details about the ACM labeling (e.g., label type, date)",
    )
    hygienist_recommendations: Optional[str] = Field(
        default=None, description="Recommendations from the hygienist for this material"
    )
    psb_supplied_acm_id: Optional[str] = Field(
        default=None, description="Unique identifier supplied by PSB (if applicable)"
    )
    removal_status: Optional[str] = Field(
        default=None,
        description="Removal status (e.g., 'N/A', 'Pending', 'Complete', 'Encapsulated')",
    )
    date_of_removal: Optional[str] = Field(
        default=None, description="Date when the material was removed (if applicable)"
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

    # Recommendation normalization (E1-S12: Consultant wording normalization)
    normalized_action: Optional[str] = Field(
        default=None,
        description="Canonical action from recommendation normalization (e.g., 'maintain_in_situ')",
    )

    # Product Classification fields (E1-S9: Victorian BAR taxonomy)
    acm_product_group: Optional[str] = Field(
        default=None,
        description="BAR taxonomy product group (e.g., 'T3 Vinyl products')",
    )
    acm_product_type: Optional[str] = Field(
        default=None, description="BAR taxonomy product type (e.g., 'Vinyl Tiles')"
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
        """Override to ensure source_id and parent_table_id are proper record format."""
        data = super()._prepare_save_data()
        if data.get("source_id"):
            data["source_id"] = ensure_record_id(data["source_id"])
        if data.get("parent_table_id"):
            data["parent_table_id"] = ensure_record_id(data["parent_table_id"])
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
