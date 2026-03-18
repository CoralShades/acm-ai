"""Schema inference for multi-consultant format adaptability.

Auto-detects table structure and maps column headers to Salesforce fields
from unknown PDF formats. Computes header signatures for caching.

Story: Multi-Consultant Story 2 — Schema Inference Node
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from open_notebook.extractors.recovery_config import RecoveryConfig


@dataclass
class ColumnMapping:
    """Single column header mapping with confidence."""

    pdf_header: str  # Original header text from PDF
    sf_field: str  # Target Salesforce API field name
    confidence: float  # 0.0 - 1.0


@dataclass
class InferredSchema:
    """Result of schema inference — maps PDF columns to SF fields.

    Produced by the schema inference node; consumed by:
    - row_segmenter (column_mapping, canonical_mapping, level_regex)
    - recovery functions (recovery_config)
    - orchestrator (format-aware extraction)
    """

    column_mapping: dict[str, str]  # pdf_header → sf_field_api_name
    canonical_mapping: dict[str, str]  # pdf_header → canonical_name (for segmenter)
    level_regex: Optional[re.Pattern] = None  # format-specific floor/level pattern
    recovery_config: RecoveryConfig = field(default_factory=RecoveryConfig)
    confidence: float = 0.0  # overall confidence score
    consultant_name: Optional[str] = None  # detected consultant firm
    profile_id: Optional[str] = None  # SurrealDB record ID if cached
    header_signature: Optional[str] = None  # sorted hash for cache lookup
    mappings: list[ColumnMapping] = field(
        default_factory=list
    )  # detailed per-column mappings
    unmapped_headers: list[str] = field(
        default_factory=list
    )  # headers that couldn't be mapped


def compute_header_signature(headers: list[str]) -> str:
    """Compute a stable hash signature from column headers.

    Sorts headers alphabetically, lowercases, joins with pipe separator,
    and returns SHA-256 hex digest (first 16 chars for readability).

    Args:
        headers: List of raw column header strings from PDF.

    Returns:
        16-char hex hash string.
    """
    normalized = sorted(h.strip().lower() for h in headers if h.strip())
    signature_str = "|".join(normalized)
    return hashlib.sha256(signature_str.encode("utf-8")).hexdigest()[:16]


# SF field catalog — the target fields that PDF headers can map to.
# Used in the LLM prompt to guide schema inference.
# Keys = SF API name, Values = human-readable description + common PDF aliases.
SF_FIELD_CATALOG: dict[str, dict[str, Any]] = {
    "Room_or_Area__c": {
        "label": "Room or Area",
        "description": "Room number, area name, or location within building",
        "common_aliases": [
            "Room",
            "Room/Area",
            "Area",
            "Location",
            "Room No",
            "Location Description",
        ],
    },
    "Item_Name__c": {
        "label": "Item/Material Name",
        "description": "ACM product or material description",
        "common_aliases": [
            "Material",
            "Product",
            "Item",
            "Description",
            "Product Description",
            "ACM Type",
            "Building Element",
            "Material Type",
        ],
    },
    "Friability_of_Material__c": {
        "label": "Friability",
        "description": "Whether the material is friable or non-friable",
        "common_aliases": [
            "Friable",
            "F/NF",
            "Friability",
            "Type",
            "Assumed/Confirmed",
        ],
    },
    "Condition__c": {
        "label": "Condition",
        "description": "Physical condition of the ACM material",
        "common_aliases": [
            "Condition",
            "Material Condition",
            "State",
            "Assessment",
        ],
    },
    "NATA_Endorsed_Sample_no__c": {
        "label": "Sample Number",
        "description": "NATA endorsed sample or lab reference number",
        "common_aliases": [
            "Sample",
            "Sample#",
            "Sample No",
            "NATA No",
            "Item No",
            "Item No.",
            "Lab No",
        ],
    },
    "Sample_Analysis_Result_Material_Status__c": {
        "label": "Sample Result",
        "description": "Laboratory analysis result or ACM status",
        "common_aliases": [
            "Result",
            "Lab Result",
            "Analysis",
            "ACM Status",
            "Analysis Result",
        ],
    },
    "Quantity__c": {
        "label": "Quantity",
        "description": "Amount or area of ACM material",
        "common_aliases": ["Quantity", "Qty", "Area", "Extent", "m\u00b2"],
    },
    "Hygienist_Recommendations__c": {
        "label": "Recommendations",
        "description": "Hygienist or consultant recommendations for management",
        "common_aliases": [
            "Recommendation",
            "Action",
            "Management",
            "Hygienist Recommendations",
        ],
    },
    "Accessibility__c": {
        "label": "Accessibility",
        "description": "Whether the ACM is accessible for sampling/inspection",
        "common_aliases": ["Access", "Accessible", "Accessibility"],
    },
    "Asbestos_Type__c": {
        "label": "Asbestos Type",
        "description": "Type of asbestos fibre identified",
        "common_aliases": ["Asbestos Type", "Fibre Type", "Fibre"],
    },
    "Disturbance_Potential__c": {
        "label": "Disturbance Potential",
        "description": "Risk rating or disturbance potential of the ACM",
        "common_aliases": [
            "Disturbance",
            "DP",
            "Risk",
            "Risk Rating",
            "Priority",
        ],
    },
    "Specific_Location__c": {
        "label": "Specific Location",
        "description": "Detailed location within room (e.g., ceiling, wall, floor)",
        "common_aliases": [
            "Specific Location",
            "Position",
            "Element",
            "Where",
        ],
    },
    "Building_Code__c": {
        "label": "Building Code",
        "description": "Building identifier or code",
        "common_aliases": ["Building", "Bldg", "Bldg No", "Asset Code"],
    },
}

# Reverse lookup: SF API name → canonical name (keys of COLUMN_ALIASES in row_segmenter)
SF_TO_CANONICAL: dict[str, str] = {
    "Room_or_Area__c": "room_location",
    "Item_Name__c": "item_description",
    "Friability_of_Material__c": "friability",
    "Condition__c": "condition",
    "NATA_Endorsed_Sample_no__c": "sample_number",
    "Sample_Analysis_Result_Material_Status__c": "sample_result",
    "Quantity__c": "quantity",
    "Hygienist_Recommendations__c": "recommendation",
    "Accessibility__c": "accessibility",
    "Asbestos_Type__c": "asbestos_type",
    "Disturbance_Potential__c": "disturbance_potential",
    "Specific_Location__c": "specific_location",
    "Building_Code__c": "building_code",
}


async def schema_inference_node(state: dict) -> dict:
    """LangGraph node: infer schema from PDF table headers.

    Collects unique column headers from acm_table_section records,
    invokes LLM to map them to SF fields, and returns InferredSchema.

    Graceful degradation: if no docling tables or LLM fails, returns
    state unchanged (inferred_schema=None).
    """
    try:
        from ai_prompter import Prompter
        from langchain_core.messages import SystemMessage

        from open_notebook.database.repository import ensure_record_id, repo_query
        from open_notebook.extractors.row_segmenter import COLUMN_ALIASES
        from open_notebook.graphs.utils import (
            parse_json_response,
            provision_langchain_model,
        )

        source = state.get("source")
        if source is None:
            logger.warning("schema_inference_node: no source in state, skipping")
            return {}

        source_id = source.id
        logger.info(f"schema_inference_node: querying tables for source {source_id}")

        # ------------------------------------------------------------------
        # 1. Query ALL acm_table_section records for this source
        # ------------------------------------------------------------------
        results = await repo_query(
            "SELECT docling_document_json FROM acm_table_section WHERE source_id = $source_id",
            {"source_id": ensure_record_id(source_id)},
        )

        if not results:
            logger.info("schema_inference_node: no acm_table_section records found, skipping")
            return {}

        # ------------------------------------------------------------------
        # 2. Extract unique column headers and sample data rows
        # ------------------------------------------------------------------
        unique_headers: list[str] = []
        seen_headers: set[str] = set()
        sample_rows: list[dict[str, str]] = []
        max_sample_rows = 3

        for row in results:
            doc_json = row.get("docling_document_json")
            if not doc_json:
                continue

            table_cells = doc_json.get("table_cells", [])
            if not table_cells:
                continue

            # Collect header cells
            for cell in table_cells:
                if cell.get("column_header", False):
                    text = cell.get("text", "").strip()
                    if text and text.lower() not in seen_headers:
                        seen_headers.add(text.lower())
                        unique_headers.append(text)

            # Collect sample data rows (non-header cells grouped by row)
            if len(sample_rows) < max_sample_rows:
                data_cells = [c for c in table_cells if not c.get("column_header", False)]
                # Group by row_span start or row index
                row_groups: dict[int, dict[str, str]] = {}
                for cell in data_cells:
                    row_idx = cell.get("start_row_offset_idx", cell.get("row", 0))
                    col_idx = cell.get("start_col_offset_idx", cell.get("col", 0))
                    text = cell.get("text", "").strip()
                    if row_idx not in row_groups:
                        row_groups[row_idx] = {}
                    # Use column header as key if available, else col index
                    col_header = None
                    if col_idx < len(unique_headers):
                        col_header = unique_headers[col_idx]
                    row_groups[row_idx][col_header or f"col_{col_idx}"] = text

                for row_idx in sorted(row_groups.keys()):
                    if len(sample_rows) >= max_sample_rows:
                        break
                    if row_groups[row_idx]:  # skip empty rows
                        sample_rows.append(row_groups[row_idx])

        if not unique_headers:
            logger.info("schema_inference_node: no column headers found in tables, skipping")
            return {}

        logger.info(
            f"schema_inference_node: found {len(unique_headers)} unique headers: {unique_headers}"
        )

        # ------------------------------------------------------------------
        # 3. Compute header signature
        # ------------------------------------------------------------------
        header_sig = compute_header_signature(unique_headers)

        # ------------------------------------------------------------------
        # 4. Invoke LLM for schema mapping
        # ------------------------------------------------------------------
        prompter = Prompter(prompt_template="acm/schema_inference")
        prompt_text = prompter.render(
            data={
                "headers": unique_headers,
                "sample_rows": sample_rows,
                "sf_field_catalog": [
                    {"api_name": k, **v} for k, v in SF_FIELD_CATALOG.items()
                ],
                "detected_format": (
                    state.get("document_metadata", {}).get("format_name")
                    if state.get("document_metadata")
                    else None
                ),
            }
        )

        model = await provision_langchain_model(
            prompt_text, state.get("model_id"), "extraction", temperature=0
        )
        response = await model.ainvoke([SystemMessage(content=prompt_text)])
        result = parse_json_response(response.content)

        if not result or "mappings" not in result:
            logger.warning("schema_inference_node: LLM returned invalid response, skipping")
            return {}

        # ------------------------------------------------------------------
        # 5. Parse LLM response into InferredSchema
        # ------------------------------------------------------------------
        column_mapping: dict[str, str] = {}
        canonical_mapping: dict[str, str] = {}
        detailed_mappings: list[ColumnMapping] = []
        unmapped = result.get("unmapped_headers", [])

        for m in result["mappings"]:
            pdf_hdr = m.get("pdf_header", "")
            sf_fld = m.get("sf_field", "")
            conf = float(m.get("confidence", 0.0))

            if pdf_hdr and sf_fld:
                column_mapping[pdf_hdr] = sf_fld
                detailed_mappings.append(
                    ColumnMapping(pdf_header=pdf_hdr, sf_field=sf_fld, confidence=conf)
                )

                # Build canonical mapping: pdf_header → canonical_name
                canonical = SF_TO_CANONICAL.get(sf_fld)
                if canonical and canonical in COLUMN_ALIASES:
                    canonical_mapping[pdf_hdr] = canonical

        # Build level regex if suggested
        level_regex = None
        level_regex_str = result.get("level_regex_suggestion")
        if level_regex_str:
            try:
                level_regex = re.compile(level_regex_str, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"schema_inference_node: invalid level_regex from LLM: {e}")

        # Build RecoveryConfig with level regex if available
        recovery = RecoveryConfig()
        if level_regex:
            recovery.level_re = level_regex

        inferred_schema = InferredSchema(
            column_mapping=column_mapping,
            canonical_mapping=canonical_mapping,
            level_regex=level_regex,
            recovery_config=recovery,
            confidence=float(result.get("overall_confidence", 0.0)),
            consultant_name=result.get("detected_consultant"),
            header_signature=header_sig,
            mappings=detailed_mappings,
            unmapped_headers=unmapped,
        )

        logger.info(
            f"schema_inference_node: inferred schema with {len(column_mapping)} mappings, "
            f"confidence={inferred_schema.confidence:.2f}, "
            f"consultant={inferred_schema.consultant_name}, "
            f"signature={header_sig}"
        )

        return {"inferred_schema": inferred_schema}

    except Exception as e:
        logger.warning(
            f"schema_inference_node: failed with {type(e).__name__}: {e}, "
            "continuing with inferred_schema=None"
        )
        return {}
