"""
Consultant Parser Abstract Base Class and shared data types.

The system uses a single config-driven GenericParser (see generic.py) that
handles all ACM PDF formats via FieldSchemaConfig from BAR field definitions.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class RawACMItem:
    """Intermediate representation of a raw ACM item extracted by a parser.

    Contains fields common across consultant formats, mapped from
    consultant-specific column names to standardized field names.
    """

    product: str
    material_description: str
    result: str

    # Optional fields that may or may not be present depending on format
    extent: Optional[str] = None
    location: Optional[str] = None
    friable: Optional[str] = None
    material_condition: Optional[str] = None
    risk_status: Optional[str] = None
    sample_number: Optional[str] = None
    disturbance_potential: Optional[str] = None
    labelled: Optional[str] = None
    control_priority: Optional[str] = None
    comments: Optional[str] = None

    # Context fields populated during extraction
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    area_type: Optional[str] = None
    page_number: Optional[int] = None


class DocumentMeta(BaseModel):
    """Document-level metadata extracted from report cover/header pages.

    Enhanced in E1-S19 with additional fields for comprehensive metadata
    extraction, confidence scoring, and SiteConfig auto-fill support.
    """

    # Original fields (preserved from dataclass version)
    consultant_name: str
    site_name: Optional[str] = None
    site_address: Optional[str] = None
    report_date: Optional[str] = None
    report_reference: Optional[str] = None
    building_size: Optional[str] = None
    building_age: Optional[str] = None
    additional: Dict[str, str] = Field(default_factory=dict)

    # New fields (E1-S19)
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    organization: Optional[str] = None
    inspection_dates: Optional[List[str]] = None
    inspector_names: Optional[List[str]] = None
    document_scope: Optional[str] = None
    methodology: Optional[str] = None
    revision_date: Optional[str] = None
    regional_classification: Optional[str] = None

    # Confidence scoring per field (E1-S19)
    field_confidence: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_llm(cls, llm_result: "DocumentMetaLLM") -> "DocumentMeta":
        """Convert LLM-friendly model to full model."""
        return cls(**llm_result.model_dump())

    def get_extracted_fields(self) -> Dict[str, Any]:
        """Return only non-None data fields (excludes meta fields)."""
        exclude_fields = {"field_confidence", "additional"}
        result = {}
        for name, value in self.model_dump().items():
            if name in exclude_fields:
                continue
            if value is not None:
                result[name] = value
        return result

    def get_site_config_mappings(self) -> Dict[str, Any]:
        """Return fields that map to SiteConfig.

        Only returns non-None values. Caller should only apply to empty
        SiteConfig fields.
        """
        mappings: Dict[str, Any] = {}
        if self.organization:
            mappings["agency"] = self.organization
        return mappings


class DocumentMetaLLM(BaseModel):
    """LLM-friendly version of DocumentMeta without Dict fields.

    Azure OpenAI strict mode rejects Dict[str, str] fields because they
    produce open schemas (additionalProperties: true). This slim model
    excludes `additional` and `field_confidence` for LLM structured output.
    Convert to full DocumentMeta via DocumentMeta.from_llm().
    """

    consultant_name: str
    site_name: Optional[str] = None
    site_address: Optional[str] = None
    report_date: Optional[str] = None
    report_reference: Optional[str] = None
    building_size: Optional[str] = None
    building_age: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    organization: Optional[str] = None
    inspection_dates: Optional[List[str]] = None
    inspector_names: Optional[List[str]] = None
    document_scope: Optional[str] = None
    methodology: Optional[str] = None
    revision_date: Optional[str] = None
    regional_classification: Optional[str] = None


@dataclass
class SourceLocation:
    """Provenance tracking for extracted items within a document."""

    building_id: Optional[str] = None
    building_name: Optional[str] = None
    building_year: Optional[int] = None
    building_construction: Optional[str] = None
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    room_area: Optional[float] = None
    area_type: str = "Interior"


class ConsultantParser(ABC):
    """Abstract base class for consultant-specific PDF parsers.

    Each consultant firm produces ACM reports in their own format with
    different column names, header patterns, and metadata structures.
    Subclasses handle the format-specific details while the extraction
    pipeline uses the common interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this consultant parser (e.g., 'prensa', 'greencap')."""
        ...

    @abstractmethod
    def detect(self, text: str) -> bool:
        """Return True if this parser handles the given PDF text.

        Args:
            text: Full text content of the PDF document.

        Returns:
            True if this parser should be used for this document.
        """
        ...

    @abstractmethod
    def extract_metadata(self, pages: Dict[int, str]) -> DocumentMeta:
        """Extract document-level metadata from page text.

        Args:
            pages: Mapping of page number to page text content.

        Returns:
            DocumentMeta with extracted metadata.
        """
        ...

    @abstractmethod
    def extract_items(self, tables: List[dict]) -> List[RawACMItem]:
        """Extract raw ACM items from parsed table data.

        Args:
            tables: List of table dicts with 'headers' (list[str]) and
                    'rows' (list[list[str]]) keys.

        Returns:
            List of RawACMItem instances.
        """
        ...

    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Map consultant-specific column names to standard raw field names.

        Returns:
            Dict mapping consultant column name -> standard field name.
            Standard fields: product, material_description, result, extent,
            location, friable, material_condition, risk_status, etc.
        """
        ...

    @abstractmethod
    def get_register_headers(self) -> List[str]:
        """Return expected column headers for this consultant's format.

        Returns:
            List of lowercase header strings in the order they typically appear.
        """
        ...
