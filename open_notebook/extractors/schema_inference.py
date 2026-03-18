"""Schema inference for multi-consultant format adaptability.

Auto-detects table structure and maps column headers to Salesforce fields
from unknown PDF formats. Computes header signatures for caching.

Story: Multi-Consultant Story 2 — Schema Inference Node
Story: Multi-Consultant Story 6 — HITL Mapping Confirmation UI
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from langgraph.types import interrupt
from loguru import logger

from open_notebook.extractors.recovery_config import RecoveryConfig

# Confidence threshold below which HITL confirmation is triggered
HITL_CONFIDENCE_THRESHOLD = 0.8


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
    detected_format: Optional[str] = None  # e.g. "standard", "ara", "pipe_table"


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

# SF API name → ACMItemRow field name (the 13 fields the LLM outputs)
SF_TO_ITEM_ROW_FIELD: dict[str, str] = {
    "Room_or_Area__c": "room_name",
    "Item_Name__c": "item_name",
    "Friability_of_Material__c": "friability",
    "Condition__c": "condition",
    "NATA_Endorsed_Sample_no__c": "sample_number",
    "Sample_Analysis_Result_Material_Status__c": "sample_result",
    "Disturbance_Potential__c": "disturbance_potential",
    "Specific_Location__c": "item_location",
    "Asbestos_Type__c": "acm_classification",
}

# Default ACMItemRow field descriptions (matches the 13 hardcoded fields)
_DEFAULT_FIELD_DESCRIPTIONS: dict[str, str] = {
    "room_name": "room or area name, e.g. 'Room 101', 'Library', 'Corridor'",
    "floor_level": "floor or level, e.g. 'Ground Floor', 'Level 1', 'Roof Space'",
    "item_location": "position within the room, e.g. 'Ceiling', 'Walls', 'Floor'",
    "item_name": "string (required) — material/product name",
    "friability": "Friable or Non-friable",
    "acm_classification": "ACM classification, e.g. 'Chrysotile', 'Amosite'",
    "acm_sub_classification": "product sub-type, e.g. 'Vinyl sheet', 'Cement flat sheet'",
    "condition": "material condition, e.g. 'Good', 'Fair', 'Poor'",
    "disturbance_potential": "disturbance likelihood, e.g. 'Low', 'Medium', 'High'",
    "sample_number": "lab/sample ID, e.g. '34511-039-001'",
    "sample_result": "Positive, Negative, Assumed Positive, or Not Sampled",
    "acm_product": "product type, e.g. 'Floor covering', 'Skirting'",
    "internal_external": "Internal or External",
}


def build_extraction_fields(schema: "InferredSchema") -> list[dict[str, str]]:
    """Build extraction_fields list from InferredSchema for Jinja template.

    Returns a list of dicts with 'name' and 'description' keys, one per
    ACMItemRow field that has a corresponding SF mapping in the schema.
    Falls back to full default list if no useful mappings exist.
    """
    fields: list[dict[str, str]] = []
    seen_names: set[str] = set()

    # Map SF fields from schema to ACMItemRow field names
    for pdf_header, sf_field in schema.column_mapping.items():
        item_field = SF_TO_ITEM_ROW_FIELD.get(sf_field)
        if item_field and item_field not in seen_names:
            desc = _DEFAULT_FIELD_DESCRIPTIONS.get(
                item_field,
                SF_FIELD_CATALOG.get(sf_field, {}).get("description", ""),
            )
            # Include original PDF header in description for LLM context
            fields.append({
                "name": item_field,
                "description": f"{desc} (PDF column: '{pdf_header}')",
            })
            seen_names.add(item_field)

    # Always include core required fields if not already present
    for core_field in ("item_name", "room_name", "sample_result"):
        if core_field not in seen_names:
            fields.append({
                "name": core_field,
                "description": _DEFAULT_FIELD_DESCRIPTIONS[core_field],
            })
            seen_names.add(core_field)

    # If we got very few mapped fields, return None to trigger default behavior
    if len(fields) < 4:
        return []

    # Add remaining default fields not covered by the mapping
    for name, desc in _DEFAULT_FIELD_DESCRIPTIONS.items():
        if name not in seen_names:
            fields.append({"name": name, "description": desc})

    return fields


def _build_schema_from_profile(
    profile: dict, header_sig: str, detected_format: Optional[str] = None
) -> InferredSchema:
    """Build an InferredSchema from a cached format profile dict."""
    column_mapping = profile.get("column_mapping", {})
    canonical_mapping = profile.get("canonical_mapping", {})

    # Rebuild level regex from stored string
    level_regex = None
    level_regex_str = profile.get("level_regex")
    if level_regex_str:
        try:
            level_regex = re.compile(level_regex_str, re.IGNORECASE)
        except re.error:
            pass

    # Rebuild RecoveryConfig
    recovery = RecoveryConfig()
    if level_regex:
        recovery.level_re = level_regex
    stored_recovery = profile.get("recovery_config")
    if stored_recovery and isinstance(stored_recovery, dict):
        for attr in (
            "not_sampled_terms",
            "confirmation_terms",
            "restriction_terms",
            "lookback_lines",
            "lookahead_lines",
        ):
            if attr in stored_recovery:
                setattr(recovery, attr, stored_recovery[attr])

    return InferredSchema(
        column_mapping=column_mapping,
        canonical_mapping=canonical_mapping,
        level_regex=level_regex,
        recovery_config=recovery,
        confidence=float(profile.get("confidence", 0.0)),
        consultant_name=profile.get("consultant_name"),
        profile_id=profile.get("id"),
        header_signature=header_sig,
        detected_format=detected_format,
    )


async def schema_inference_node(state: dict) -> dict:
    """LangGraph node: infer schema from PDF table headers.

    Collects unique column headers from acm_table_section records,
    checks the format profile cache, and falls back to LLM inference
    on cache miss. Saves new profiles automatically.

    Graceful degradation: if no docling tables or LLM fails, returns
    state unchanged (inferred_schema=None).
    """
    try:
        from ai_prompter import Prompter
        from langchain_core.messages import SystemMessage

        from open_notebook.database.repository import ensure_record_id, repo_query
        from open_notebook.extractors.format_profile_repository import (
            get_profile_by_signature,
            increment_sample_count,
            save_profile,
        )
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
        # 4. Check format profile cache
        # ------------------------------------------------------------------
        cached_profile = await get_profile_by_signature(header_sig)
        if cached_profile and cached_profile.get("confidence", 0) >= 0.8:
            logger.info(
                f"schema_inference_node: CACHE HIT for signature {header_sig}, "
                f"consultant={cached_profile.get('consultant_name')}, "
                f"sample_count={cached_profile.get('sample_count', 1)}"
            )
            # Resolve detected_format from document_metadata
            cached_format = (
                state.get("document_metadata", {}).get("format_name")
                if state.get("document_metadata")
                else None
            )
            inferred_schema = _build_schema_from_profile(
                cached_profile, header_sig, detected_format=cached_format
            )
            await increment_sample_count(cached_profile["id"])
            return {"inferred_schema": inferred_schema}

        logger.info(f"schema_inference_node: CACHE MISS for signature {header_sig}, invoking LLM")

        # ------------------------------------------------------------------
        # 5. Invoke LLM for schema mapping (cache miss path)
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
        # 6. Parse LLM response into InferredSchema
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

        overall_confidence = float(result.get("overall_confidence", 0.0))
        consultant_name = result.get("detected_consultant")

        # Resolve detected_format from document_metadata or LLM response
        detected_format = (
            state.get("document_metadata", {}).get("format_name")
            if state.get("document_metadata")
            else None
        ) or result.get("detected_format")

        # ------------------------------------------------------------------
        # 7. HITL check: if confidence < threshold, interrupt for user review
        # ------------------------------------------------------------------
        if overall_confidence < HITL_CONFIDENCE_THRESHOLD:
            logger.info(
                f"schema_inference_node: confidence {overall_confidence:.2f} "
                f"< {HITL_CONFIDENCE_THRESHOLD}, triggering HITL review"
            )

            # Build the interrupt payload for user review.
            # interrupt() pauses graph execution — the value surfaces to the caller.
            # On resume, interrupt() returns the user's response.
            hitl_payload = {
                "type": "schema_mapping_review",
                "source_id": str(source.id),
                "mappings": [
                    {
                        "pdf_header": m.pdf_header,
                        "sf_field": m.sf_field,
                        "confidence": m.confidence,
                    }
                    for m in detailed_mappings
                ],
                "unmapped_headers": unmapped,
                "overall_confidence": overall_confidence,
                "detected_consultant": consultant_name,
                "header_signature": header_sig,
            }
            user_response = interrupt(hitl_payload)

            # --- Resumed from interrupt ---
            # user_response is the value passed via Command(resume=...)
            action = user_response.get("action", "approve")
            logger.info(
                f"schema_inference_node: HITL resumed with action={action}"
            )

            if action == "reject":
                # User rejected the mapping — fall back to COLUMN_ALIASES
                logger.info("schema_inference_node: user rejected mapping, skipping")
                return {}

            if action == "modify" and user_response.get("mappings"):
                # User modified the mappings — rebuild from their corrections
                column_mapping = {}
                canonical_mapping = {}
                detailed_mappings = []
                for m in user_response["mappings"]:
                    pdf_hdr = m.get("pdf_header", "")
                    sf_fld = m.get("sf_field", "")
                    conf = float(m.get("confidence", 1.0))
                    if pdf_hdr and sf_fld:
                        column_mapping[pdf_hdr] = sf_fld
                        detailed_mappings.append(
                            ColumnMapping(
                                pdf_header=pdf_hdr, sf_field=sf_fld, confidence=conf
                            )
                        )
                        canonical = SF_TO_CANONICAL.get(sf_fld)
                        if canonical and canonical in COLUMN_ALIASES:
                            canonical_mapping[pdf_hdr] = canonical
                # User-confirmed mappings are high confidence
                overall_confidence = 1.0

            # For "approve" action, keep the original LLM mappings as-is
            # but boost confidence to indicate user verification
            if action == "approve":
                overall_confidence = max(overall_confidence, 0.9)

            # Save as user-verified profile (after HITL confirmation)
            profile_id = await _save_format_profile(
                save_profile=save_profile,
                header_sig=header_sig,
                consultant_name=consultant_name,
                column_mapping=column_mapping,
                canonical_mapping=canonical_mapping,
                level_regex_str=level_regex_str,
                confidence=overall_confidence,
                verified_by_user=True,
            )
        else:
            # ------------------------------------------------------------------
            # 7b. High confidence — auto-save format profile (no HITL)
            # ------------------------------------------------------------------
            profile_id = await _save_format_profile(
                save_profile=save_profile,
                header_sig=header_sig,
                consultant_name=consultant_name,
                column_mapping=column_mapping,
                canonical_mapping=canonical_mapping,
                level_regex_str=level_regex_str,
                confidence=overall_confidence,
                verified_by_user=False,
            )

        # ------------------------------------------------------------------
        # 8. Build final InferredSchema
        # ------------------------------------------------------------------
        inferred_schema = InferredSchema(
            column_mapping=column_mapping,
            canonical_mapping=canonical_mapping,
            level_regex=level_regex,
            recovery_config=recovery,
            confidence=overall_confidence,
            consultant_name=consultant_name,
            header_signature=header_sig,
            profile_id=profile_id,
            mappings=detailed_mappings,
            unmapped_headers=unmapped,
            detected_format=detected_format,
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


async def _save_format_profile(
    *,
    save_profile,
    header_sig: str,
    consultant_name: Optional[str],
    column_mapping: dict[str, str],
    canonical_mapping: dict[str, str],
    level_regex_str: Optional[str],
    confidence: float,
    verified_by_user: bool,
) -> Optional[str]:
    """Save a format profile, returning the profile ID or None on failure."""
    try:
        saved = await save_profile(
            {
                "header_signature": header_sig,
                "consultant_name": consultant_name,
                "column_mapping": column_mapping,
                "canonical_mapping": canonical_mapping,
                "level_regex": level_regex_str,
                "recovery_config": None,
                "confidence": confidence,
                "verified_by_user": verified_by_user,
                "sample_count": 1,
            }
        )
        if saved and isinstance(saved, list) and len(saved) > 0:
            profile_id = saved[0].get("id")
            logger.info(f"schema_inference_node: saved format profile {profile_id}")
            return profile_id
        elif saved and isinstance(saved, dict):
            profile_id = saved.get("id")
            logger.info(f"schema_inference_node: saved format profile {profile_id}")
            return profile_id
    except Exception as save_err:
        logger.warning(
            f"schema_inference_node: failed to save format profile: {save_err}"
        )
    return None
