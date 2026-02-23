"""
Pydantic Schemas for AI-Powered ACM Extraction

These schemas are used with LangChain's structured output feature to extract
ACM records from PDF documents processed by Docling.

Story: E1-S7 AI-Powered ACM Extraction
"""

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# Import ExtractionConfidence from domain to avoid duplication
from open_notebook.domain.acm import ExtractionConfidence

# BAR field enums — canonical allowed values
RESULT_VALUES = {"Positive", "Assumed Positive", "Negative", "Assumed Negative", "Unknown"}
FRIABLE_VALUES = {"Friable", "Non Friable"}
RISK_STATUS_VALUES = {"Low", "Medium", "High"}
MATERIAL_CONDITION_VALUES = {"Good", "Fair", "Poor", "Damaged"}
AREA_TYPE_VALUES = {"Interior", "Exterior", "Grounds"}

# N/A patterns — LLMs return these for fields not applicable to negative results
_NA_PATTERNS = {"n/a", "na", "not applicable", "-", "none", ""}


def _is_na(value: str) -> bool:
    """Check if a value represents N/A (not applicable)."""
    stripped = value.strip().lower()
    return stripped in _NA_PATTERNS or "n/a" in stripped


class ExtractionStatus(str, Enum):
    """Status of extraction result."""

    VALID = "valid"
    INVALID = "invalid"
    NO_ACM_DATA = "no_acm_data"


class TableBoundingBox(BaseModel):
    """Bounding box for table provenance linking."""

    x: Optional[float] = Field(default=None, description="X coordinate")
    y: Optional[float] = Field(default=None, description="Y coordinate")
    width: Optional[float] = Field(default=None, description="Width")
    height: Optional[float] = Field(default=None, description="Height")
    page: Optional[int] = Field(default=None, description="Page number")


class ConfidenceDistribution(BaseModel):
    """Distribution of extraction confidence levels."""

    high: int = Field(default=0, description="Count of high confidence records")
    medium: int = Field(default=0, description="Count of medium confidence records")
    low: int = Field(default=0, description="Count of low confidence records")


class BuildingRoomContext(BaseModel):
    """
    Context for building and room hierarchy.
    Persisted across chunks to maintain context during extraction.
    """

    school_name: str = Field(
        default="Unknown School", description="Name of the school or facility"
    )
    school_code: Optional[str] = Field(
        default=None, description="School code/identifier (e.g., 'PS123')"
    )
    building_id: Optional[str] = Field(
        default=None, description="Building identifier (e.g., 'A1', 'B2')"
    )
    building_name: Optional[str] = Field(
        default=None,
        description="Building name (e.g., 'Main Building', 'Science Wing')",
    )
    building_year: Optional[int] = Field(
        default=None, description="Year building was constructed"
    )
    building_construction: Optional[str] = Field(
        default=None, description="Construction type (e.g., 'Brick', 'Demountable')"
    )
    room_id: Optional[str] = Field(
        default=None, description="Room identifier (e.g., 'A1-R1', '101')"
    )
    room_name: Optional[str] = Field(
        default=None, description="Room name (e.g., 'Classroom', 'Office')"
    )
    room_area: Optional[float] = Field(
        default=None, description="Room area in square meters"
    )
    area_type: str = Field(
        default="Interior",
        description="Area type: 'Interior', 'Exterior', or 'Grounds'",
    )
    current_page: int = Field(
        default=1, description="Current page number being processed"
    )


class ACMExtractionRecord(BaseModel):
    """
    A single ACM record extracted by the LLM.
    This is the schema used for structured output extraction.
    """

    # Required context fields
    building_id: str = Field(
        description="Building identifier (e.g., 'A1', 'B2'). REQUIRED."
    )
    room_id: Optional[str] = Field(
        default=None,
        description="Room identifier within the building (e.g., 'A1-R1', '101')",
    )
    product: str = Field(
        description="Type of product containing asbestos (e.g., 'Ceiling Tiles', 'Pipe Insulation'). REQUIRED."
    )
    material_description: str = Field(
        description="Detailed description of the material (e.g., 'Vinyl floor tiles, grey/white mottled pattern'). REQUIRED."
    )
    result: str = Field(
        description="Asbestos test result using BAR vocabulary: 'Positive', 'Assumed Positive', 'Negative', 'Assumed Negative', 'Unknown'. REQUIRED."
    )

    # Optional context fields
    building_name: Optional[str] = Field(
        default=None,
        description="Building name (e.g., 'Main Building', 'Administration Block')",
    )
    building_year: Optional[int] = Field(
        default=None, description="Year building was constructed"
    )
    building_construction: Optional[str] = Field(
        default=None, description="Construction type (e.g., 'Brick', 'Timber Frame')"
    )
    room_name: Optional[str] = Field(
        default=None, description="Room name (e.g., 'Classroom', 'Storeroom')"
    )
    room_area: Optional[float] = Field(
        default=None, description="Room area in square meters"
    )
    area_type: Optional[str] = Field(
        default="Interior",
        description="Area type: 'Interior', 'Exterior', or 'Grounds'",
    )

    # ACM item data
    extent: Optional[str] = Field(
        default=None,
        description="Extent/coverage of the material (e.g., 'Whole ceiling', 'Partial wall')",
    )
    location: Optional[str] = Field(
        default=None,
        description="Specific location within room (e.g., 'Ceiling', 'Under stairs')",
    )
    friable: Optional[str] = Field(
        default=None, description="Friability: 'Friable' or 'Non Friable'"
    )
    material_condition: Optional[str] = Field(
        default=None, description="Condition: 'Good', 'Fair', 'Poor', 'Damaged'"
    )
    risk_status: Optional[str] = Field(
        default=None, description="Risk level: 'Low', 'Medium', 'High'"
    )

    # New extraction fields (E1-S7)
    disturbance_potential: Optional[str] = Field(
        default=None, description="Likelihood of disturbance: 'Low', 'Medium', 'High'"
    )
    sample_no: Optional[str] = Field(
        default=None, description="Sample identification number"
    )
    sample_result: Optional[str] = Field(
        default=None, description="Laboratory analysis result"
    )
    identifying_company: Optional[str] = Field(
        default=None, description="Hygiene consulting company name"
    )
    quantity: Optional[str] = Field(
        default=None,
        description="Amount of material (e.g., '10 m²', '5 linear meters')",
    )
    acm_labelled: Optional[bool] = Field(
        default=None, description="Whether the ACM is labeled on-site"
    )
    acm_label_details: Optional[str] = Field(
        default=None, description="Label details if labeled"
    )
    floor_level: Optional[str] = Field(
        default=None, description="Floor level (e.g., 'Ground', 'Level 1', 'Roof')"
    )
    hygienist_recommendations: Optional[str] = Field(
        default=None, description="Expert recommendations for this material"
    )
    psb_supplied_acm_id: Optional[str] = Field(
        default=None, description="PSB identifier if applicable"
    )
    removal_status: Optional[str] = Field(
        default=None,
        description="Removal status: 'N/A', 'Pending', 'Complete', 'Encapsulated'",
    )
    date_of_removal: Optional[str] = Field(
        default=None, description="Date of removal if applicable"
    )

    @field_validator("result", mode="before")
    @classmethod
    def validate_result(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().title()
        # Handle "Assumed positive" -> "Assumed Positive" etc.
        if normalized not in RESULT_VALUES:
            # Try case-insensitive match
            for valid in RESULT_VALUES:
                if v.strip().lower() == valid.lower():
                    return valid
            raise ValueError(f"result must be one of {sorted(RESULT_VALUES)}, got '{v}'")
        return normalized

    @field_validator("friable", mode="before")
    @classmethod
    def validate_friable(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if _is_na(v):
            return None
        stripped = v.strip()
        for valid in FRIABLE_VALUES:
            if stripped.lower() == valid.lower():
                return valid
        # Accept common variants
        if stripped.lower() in ("non-friable", "nonfriable"):
            return "Non Friable"
        raise ValueError(f"friable must be one of {sorted(FRIABLE_VALUES)}, got '{v}'")

    @field_validator("risk_status", mode="before")
    @classmethod
    def validate_risk_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if _is_na(v):
            return None
        normalized = v.strip().title()
        if normalized in RISK_STATUS_VALUES:
            return normalized
        raise ValueError(f"risk_status must be one of {sorted(RISK_STATUS_VALUES)}, got '{v}'")

    @field_validator("material_condition", mode="before")
    @classmethod
    def validate_material_condition(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if _is_na(v):
            return None
        normalized = v.strip().title()
        if normalized in MATERIAL_CONDITION_VALUES:
            return normalized
        raise ValueError(
            f"material_condition must be one of {sorted(MATERIAL_CONDITION_VALUES)}, got '{v}'"
        )

    @field_validator("area_type", mode="before")
    @classmethod
    def validate_area_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if _is_na(v):
            return None
        normalized = v.strip().title()
        if normalized in AREA_TYPE_VALUES:
            return normalized
        raise ValueError(f"area_type must be one of {sorted(AREA_TYPE_VALUES)}, got '{v}'")

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        match = re.match(r"^\s*(-?\d+(?:\.\d+)?)", str(v))
        if match:
            numeric = float(match.group(1))
            if numeric < 0:
                raise ValueError(f"quantity cannot be negative, got '{v}'")
        return v

    # Extraction metadata
    extraction_confidence: str = Field(
        default="medium", description="Confidence level: 'high', 'medium', 'low'"
    )
    data_issues: List[str] = Field(
        default_factory=list,
        description="List of data quality issues identified during extraction",
    )
    page_number: Optional[int] = Field(
        default=None, description="Page number where this record was found"
    )
    # Note: table_bbox is added post-extraction by MinerU, not by LLM


class ACMExtractionResult(BaseModel):
    """
    Result of ACM extraction for a document or chunk.
    Contains multiple records and extraction metadata.
    """

    records: List[ACMExtractionRecord] = Field(
        default_factory=list,
        description="List of extracted ACM records. Empty if no ACM data found.",
    )
    status: ExtractionStatus = Field(
        default=ExtractionStatus.VALID,
        description="Extraction status: 'valid', 'invalid', or 'no_acm_data'",
    )
    total_records: int = Field(
        default=0, description="Total number of records extracted"
    )
    records_rejected: int = Field(
        default=0, description="Number of records rejected during validation"
    )
    confidence_distribution: ConfidenceDistribution = Field(
        default_factory=ConfidenceDistribution,
        description="Count of records by confidence level",
    )
    extraction_notes: Optional[str] = Field(
        default=None, description="Additional notes about the extraction process"
    )

    def update_stats(self) -> "ACMExtractionResult":
        """Update computed statistics based on records."""
        self.total_records = len(self.records)
        self.confidence_distribution = ConfidenceDistribution()
        for record in self.records:
            conf = record.extraction_confidence.lower()
            if conf == "high":
                self.confidence_distribution.high += 1
            elif conf == "medium":
                self.confidence_distribution.medium += 1
            elif conf == "low":
                self.confidence_distribution.low += 1
        return self


class ChunkExtractionInput(BaseModel):
    """Input for extracting ACM records from a document chunk."""

    content: str = Field(description="Text content to extract from")
    page_number: int = Field(
        default=1, description="Starting page number for this chunk"
    )
    context: BuildingRoomContext = Field(
        default_factory=BuildingRoomContext,
        description="Building/room context from previous chunks",
    )
    chunk_index: int = Field(default=0, description="Index of this chunk (0-based)")
    total_chunks: int = Field(
        default=1, description="Total number of chunks for this document"
    )


class ACMExtractionInput(BaseModel):
    """Input for the ACM extraction command."""

    source_id: str = Field(description="ID of the source document to extract from")
    model_id: Optional[str] = Field(
        default=None, description="Optional model ID to use for extraction"
    )
    force: bool = Field(
        default=False, description="Force re-extraction even if records exist"
    )


class ACMExtractionOutput(BaseModel):
    """Output from the ACM extraction command."""

    source_id: str = Field(description="ID of the source document")
    status: str = Field(description="Extraction status: 'success', 'failed', 'no_data'")
    total_records: int = Field(default=0, description="Number of records extracted")
    records_failed: int = Field(
        default=0,
        description="Number of records that failed validation and were rejected",
    )
    confidence_distribution: ConfidenceDistribution = Field(
        default_factory=ConfidenceDistribution,
        description="Count of records by confidence level",
    )
    error: Optional[str] = Field(
        default=None, description="Error message if extraction failed"
    )
    extraction_time_ms: Optional[int] = Field(
        default=None, description="Time taken for extraction in milliseconds"
    )
    correction_stats: Optional[dict] = Field(
        default=None,
        description="Corrective RAG stats: {auto_corrected, llm_corrected, failed, total_validated}",
    )
    orchestrator_stats: Optional[dict] = Field(
        default=None,
        description="Orchestrator stats: per-building extraction plan, strategy distribution, timing",
    )
    pipeline_run: Optional[dict] = Field(
        default=None,
        description="Pipeline run state: stage timings, metrics, models used (E1-S21)",
    )
    token_limit_exceeded: bool = Field(
        default=False,
        description="Whether input exceeded model context window (E1-S23)",
    )
    chunk_count: int = Field(
        default=1,
        description="Number of chunks used for extraction (1 = no chunking needed) (E1-S23)",
    )
