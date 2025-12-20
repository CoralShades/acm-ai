"""
Pydantic Schemas for AI-Powered ACM Extraction

These schemas are used with LangChain's structured output feature to extract
ACM records from PDF documents processed by Docling.

Story: E1-S7 AI-Powered ACM Extraction
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# Import ExtractionConfidence from domain to avoid duplication
from open_notebook.domain.acm import ExtractionConfidence


class ExtractionStatus(str, Enum):
    """Status of extraction result."""
    VALID = "valid"
    INVALID = "invalid"
    NO_ACM_DATA = "no_acm_data"


class BuildingRoomContext(BaseModel):
    """
    Context for building and room hierarchy.
    Persisted across chunks to maintain context during extraction.
    """
    school_name: str = Field(
        default="Unknown School",
        description="Name of the school or facility"
    )
    school_code: Optional[str] = Field(
        default=None,
        description="School code/identifier (e.g., 'PS123')"
    )
    building_id: Optional[str] = Field(
        default=None,
        description="Building identifier (e.g., 'A1', 'B2')"
    )
    building_name: Optional[str] = Field(
        default=None,
        description="Building name (e.g., 'Main Building', 'Science Wing')"
    )
    building_year: Optional[int] = Field(
        default=None,
        description="Year building was constructed"
    )
    building_construction: Optional[str] = Field(
        default=None,
        description="Construction type (e.g., 'Brick', 'Demountable')"
    )
    room_id: Optional[str] = Field(
        default=None,
        description="Room identifier (e.g., 'A1-R1', '101')"
    )
    room_name: Optional[str] = Field(
        default=None,
        description="Room name (e.g., 'Classroom', 'Office')"
    )
    room_area: Optional[float] = Field(
        default=None,
        description="Room area in square meters"
    )
    area_type: str = Field(
        default="Interior",
        description="Area type: 'Interior', 'Exterior', or 'Grounds'"
    )
    current_page: int = Field(
        default=1,
        description="Current page number being processed"
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
        description="Room identifier within the building (e.g., 'A1-R1', '101')"
    )
    product: str = Field(
        description="Type of product containing asbestos (e.g., 'Ceiling Tiles', 'Pipe Insulation'). REQUIRED."
    )
    material_description: str = Field(
        description="Detailed description of the material (e.g., 'Vinyl floor tiles, grey/white mottled pattern'). REQUIRED."
    )
    result: str = Field(
        description="Asbestos test result: 'Detected', 'Not Detected', 'Presumed', 'Unknown'. REQUIRED."
    )

    # Optional context fields
    building_name: Optional[str] = Field(
        default=None,
        description="Building name (e.g., 'Main Building', 'Administration Block')"
    )
    building_year: Optional[int] = Field(
        default=None,
        description="Year building was constructed"
    )
    building_construction: Optional[str] = Field(
        default=None,
        description="Construction type (e.g., 'Brick', 'Timber Frame')"
    )
    room_name: Optional[str] = Field(
        default=None,
        description="Room name (e.g., 'Classroom', 'Storeroom')"
    )
    room_area: Optional[float] = Field(
        default=None,
        description="Room area in square meters"
    )
    area_type: Optional[str] = Field(
        default="Interior",
        description="Area type: 'Interior', 'Exterior', or 'Grounds'"
    )

    # ACM item data
    extent: Optional[str] = Field(
        default=None,
        description="Extent/coverage of the material (e.g., 'Whole ceiling', 'Partial wall')"
    )
    location: Optional[str] = Field(
        default=None,
        description="Specific location within room (e.g., 'Ceiling', 'Under stairs')"
    )
    friable: Optional[str] = Field(
        default=None,
        description="Friability: 'Friable' or 'Non Friable'"
    )
    material_condition: Optional[str] = Field(
        default=None,
        description="Condition: 'Good', 'Fair', 'Poor', 'Damaged'"
    )
    risk_status: Optional[str] = Field(
        default=None,
        description="Risk level: 'Low', 'Medium', 'High'"
    )

    # New extraction fields (E1-S7)
    disturbance_potential: Optional[str] = Field(
        default=None,
        description="Likelihood of disturbance: 'Low', 'Medium', 'High'"
    )
    sample_no: Optional[str] = Field(
        default=None,
        description="Sample identification number"
    )
    sample_result: Optional[str] = Field(
        default=None,
        description="Laboratory analysis result"
    )
    identifying_company: Optional[str] = Field(
        default=None,
        description="Hygiene consulting company name"
    )
    quantity: Optional[str] = Field(
        default=None,
        description="Amount of material (e.g., '10 m²', '5 linear meters')"
    )
    acm_labelled: Optional[bool] = Field(
        default=None,
        description="Whether the ACM is labeled on-site"
    )
    acm_label_details: Optional[str] = Field(
        default=None,
        description="Label details if labeled"
    )
    hygienist_recommendations: Optional[str] = Field(
        default=None,
        description="Expert recommendations for this material"
    )
    psb_supplied_acm_id: Optional[str] = Field(
        default=None,
        description="PSB identifier if applicable"
    )
    removal_status: Optional[str] = Field(
        default=None,
        description="Removal status: 'N/A', 'Pending', 'Complete', 'Encapsulated'"
    )
    date_of_removal: Optional[str] = Field(
        default=None,
        description="Date of removal if applicable"
    )

    # Extraction metadata
    extraction_confidence: str = Field(
        default="medium",
        description="Confidence level: 'high', 'medium', 'low'"
    )
    data_issues: List[str] = Field(
        default_factory=list,
        description="List of data quality issues identified during extraction"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number where this record was found"
    )


class ACMExtractionResult(BaseModel):
    """
    Result of ACM extraction for a document or chunk.
    Contains multiple records and extraction metadata.
    """
    records: List[ACMExtractionRecord] = Field(
        default_factory=list,
        description="List of extracted ACM records. Empty if no ACM data found."
    )
    status: ExtractionStatus = Field(
        default=ExtractionStatus.VALID,
        description="Extraction status: 'valid', 'invalid', or 'no_acm_data'"
    )
    total_records: int = Field(
        default=0,
        description="Total number of records extracted"
    )
    records_rejected: int = Field(
        default=0,
        description="Number of records rejected during validation"
    )
    confidence_distribution: dict = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0},
        description="Count of records by confidence level"
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Additional notes about the extraction process"
    )

    def update_stats(self) -> "ACMExtractionResult":
        """Update computed statistics based on records."""
        self.total_records = len(self.records)
        self.confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        for record in self.records:
            conf = record.extraction_confidence.lower()
            if conf in self.confidence_distribution:
                self.confidence_distribution[conf] += 1
        return self


class ChunkExtractionInput(BaseModel):
    """Input for extracting ACM records from a document chunk."""
    content: str = Field(
        description="Text content to extract from"
    )
    page_number: int = Field(
        default=1,
        description="Starting page number for this chunk"
    )
    context: BuildingRoomContext = Field(
        default_factory=BuildingRoomContext,
        description="Building/room context from previous chunks"
    )
    chunk_index: int = Field(
        default=0,
        description="Index of this chunk (0-based)"
    )
    total_chunks: int = Field(
        default=1,
        description="Total number of chunks for this document"
    )


class ACMExtractionInput(BaseModel):
    """Input for the ACM extraction command."""
    source_id: str = Field(
        description="ID of the source document to extract from"
    )
    model_id: Optional[str] = Field(
        default=None,
        description="Optional model ID to use for extraction"
    )
    force: bool = Field(
        default=False,
        description="Force re-extraction even if records exist"
    )


class ACMExtractionOutput(BaseModel):
    """Output from the ACM extraction command."""
    source_id: str = Field(
        description="ID of the source document"
    )
    status: str = Field(
        description="Extraction status: 'success', 'failed', 'no_data'"
    )
    total_records: int = Field(
        default=0,
        description="Number of records extracted"
    )
    records_failed: int = Field(
        default=0,
        description="Number of records that failed validation and were rejected"
    )
    confidence_distribution: dict = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0},
        description="Count of records by confidence level"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if extraction failed"
    )
    extraction_time_ms: Optional[int] = Field(
        default=None,
        description="Time taken for extraction in milliseconds"
    )
