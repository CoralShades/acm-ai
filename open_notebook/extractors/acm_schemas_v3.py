"""
Pydantic Schemas for V3 Two-Phase ACM Extraction.

Defines SF-aligned models for Building__c and Item__c extraction.
These models are ADDITIVE — they do not replace ACMExtractionRecord.

Phase 1 output: BuildingExtractionResult
Phase 2 output: ACMItemExtractionResult (wraps list of ACMItemRecord)

Story: E30-S7 Two-Phase Extraction Prompts
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BuildingExtractionResult(BaseModel):
    """Phase 1 output: SF Building__c fields extracted from document header."""

    # Core identity
    building_name: Optional[str] = None  # Building_Name__c
    building_type: Optional[str] = None  # Building_Type__c (picklist)
    building_category: Optional[str] = None  # Building_Category__c (picklist)

    # Address
    building_address: Optional[str] = None  # Building_Address__c
    suburb: Optional[str] = None  # Suburb__c
    postcode: Optional[str] = None  # Postcode__c

    # Physical
    estimated_year_built: Optional[str] = None  # Estimated_Year_Build_New__c
    construction_type: Optional[str] = None  # Construction_Type__c

    # Audit details
    date_of_audit: Optional[str] = None  # Date_of_Audit_Report__c
    frequency_of_use: Optional[str] = None  # Frequency_of_Use__c (picklist)
    identifying_company: Optional[str] = (
        None  # Identifying_Hygiene_Consulting_Company__c
    )

    # Additional building details
    state: Optional[str] = Field(
        None, description="Australian state, e.g. 'VIC', 'NSW'"
    )
    number_of_levels: Optional[int] = Field(
        None, description="Number of building levels/storeys"
    )
    owned_or_leased: Optional[str] = Field(None, description="'Owned' or 'Leased'")
    building_sub_category: Optional[str] = Field(
        None, description="Sub-category dependent on Building_Category__c"
    )
    building_risk_rating: Optional[str] = Field(
        None, description="Overall risk rating, e.g. 'Low', 'Medium', 'High'"
    )

    # Quality metadata
    extraction_confidence: str = "medium"  # "high" | "medium" | "low"
    extraction_notes: Optional[str] = None


class ACMItemRecord(BaseModel):
    """Phase 2 output: One SF Item__c record (single ACM item in a building)."""

    # Location
    room_or_area: Optional[str] = None  # Room_or_Area__c
    internal_external: Optional[str] = None  # Internal_External__c (picklist)
    level: Optional[str] = None  # Level__c
    location_in_room: Optional[str] = None  # Location_in_Room__c

    # ACM classification chain
    friability_of_material: Optional[str] = (
        None  # Friability_of_Material__c (Non-friable | Friable)
    )
    acm_classification: Optional[str] = None  # ACM_Classification__c (product group)
    acm_sub_classification: Optional[str] = (
        None  # ACM_Sub_Classification__c (product type)
    )
    item_name: Optional[str] = None  # Item_Name__c (subsetted list)
    if_other_item_name: Optional[str] = None  # If_Other_Item_Name__c (free text)

    # Sample and assessment
    sample_result: Optional[str] = None  # Sample_Analysis_Result_Material_Status__c
    nata_sample_no: Optional[str] = None  # NATA_Endorsed_Sample_no__c
    condition: Optional[str] = None  # Condition__c (picklist)
    disturbance_potential: Optional[str] = None  # Disturbance_Potential_of_Material__c
    quantity: Optional[str] = (
        None  # Quantity__c (kept as str — LLMs return "2m²", "10 lm")
    )
    labelled: Optional[str] = None  # Labelled__c (Yes | No)
    labelled_details: Optional[str] = None  # Labelled_Details__c

    @field_validator("labelled", mode="before")
    @classmethod
    def coerce_labelled(cls, v):
        """Coerce bool→str: LLMs often return true/false instead of 'Yes'/'No'."""
        if isinstance(v, bool):
            return "Yes" if v else "No"
        return v

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        """Coerce int/float→str: LLMs may return numeric quantities without units."""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    # Notes
    hygienist_recommendations: Optional[str] = None
    additional_comments: Optional[str] = None

    # Pipeline flags
    no_access: bool = False
    extraction_confidence: str = "medium"
    data_issues: List[str] = Field(default_factory=list)
    page_number: Optional[int] = None


class ACMItemExtractionResult(BaseModel):
    """Phase 2 output wrapper: all Item__c records for one building."""

    records: List[ACMItemRecord] = Field(default_factory=list)
    status: str = "valid"  # "valid" | "no_acm_data" | "invalid" | "truncated"
    extraction_notes: Optional[str] = None
