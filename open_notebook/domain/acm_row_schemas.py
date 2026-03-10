"""Simplified per-row LLM extraction schemas for ACM items.

These schemas are intentionally minimal (9 fields) to work reliably with
small Ollama models (num_ctx=2048). The LLM fills only what it sees in the
row data. Deterministic Python mapping handles normalization, classification
validation, and conversion to ACMExtractionRecord.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ACMItemRow(BaseModel):
    """LLM output for a single ACM register row.

    9 fields only -- deliberately simple for Ollama extraction.
    The LLM extracts raw values; Python post-processing handles
    normalization and Salesforce picklist alignment.
    """

    room_name: Optional[str] = Field(
        None,
        description="Room or area name, e.g. 'Room 101', 'Library', 'Corridor'",
    )
    floor_level: Optional[str] = Field(
        None,
        description="Floor or level, e.g. 'Ground Floor', 'Level 1', 'Roof Space'",
    )
    item_location: Optional[str] = Field(
        None,
        description="Where in the room, e.g. 'Ceiling', 'Walls', 'Floor', 'Eaves'",
    )
    item_name: str = Field(
        description="Material/product name, e.g. 'Vinyl floor tiles', 'Cement sheet lining', 'Fibro eaves'"
    )
    friability: Optional[str] = Field(
        None,
        description="Friable or Non-friable (or F/NF, Yes/No)",
    )
    acm_classification: Optional[str] = Field(
        None,
        description="ACM classification if stated, e.g. 'Chrysotile', 'Amosite', 'Presumed'",
    )
    acm_sub_classification: Optional[str] = Field(
        None,
        description="Specific product sub-type if stated, e.g. 'Vinyl sheet', 'Cement flat sheet'",
    )
    condition: Optional[str] = Field(
        None,
        description="Material condition, e.g. 'Good', 'Fair', 'Poor', 'Severely Damaged'",
    )
    disturbance_potential: Optional[str] = Field(
        None,
        description="Likelihood of disturbance, e.g. 'Low', 'Medium', 'High'",
    )
