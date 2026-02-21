"""
Document Metadata Extraction.

Extracts comprehensive document metadata from cover pages, headers, and body
content of SAMP/BAR PDF documents. Runs as Stage -2 (before document structure
extraction) in the LangGraph extraction pipeline.

Story: E1-S19 Document Metadata Extraction Enhancement
"""

import re
from typing import Any, Dict, Optional, Set

from loguru import logger

from open_notebook.extractors.document_structure import _PAGE_PATTERN
from open_notebook.extractors.parsers.base import DocumentMeta, DocumentMetaLLM
from open_notebook.graphs.utils import provision_langchain_model

# Number of pages to extract for cover page analysis
COVER_PAGE_COUNT = 5

# ============================================================================
# Regex patterns for heuristic extraction
# ============================================================================

# Australian address patterns
_ADDRESS_PATTERN = re.compile(
    r"(\d+[-/]?\d*)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*\s+"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Court|Ct|"
    r"Crescent|Cres|Boulevard|Blvd|Way|Place|Pl))",
    re.MULTILINE | re.IGNORECASE,
)
_SUBURB_STATE_POSTCODE = re.compile(
    r"([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+"
    r"(?:VIC|NSW|QLD|SA|WA|TAS|NT|ACT)\s+(\d{4})",
    re.MULTILINE | re.IGNORECASE,
)

# Report reference patterns
_REPORT_REF_PATTERNS = [
    re.compile(r"(?:Report\s+(?:No|Number|Ref)\.?[:\s]+)([\w\-/]+)", re.IGNORECASE),
    re.compile(r"(?:Reference[:\s]+)([\w\-/]+)", re.IGNORECASE),
    re.compile(r"(?:Job\s+(?:No|Number)\.?[:\s]+)([\w\-/]+)", re.IGNORECASE),
    re.compile(r"(?:Project\s+(?:No|Number|Ref)\.?[:\s]+)([\w\-/]+)", re.IGNORECASE),
]

# Date patterns (Australian format)
_DATE_PATTERNS = [
    re.compile(r"(?<!\d)(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})(?!\d)"),
    re.compile(
        r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"((?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4})",
        re.IGNORECASE,
    ),
]

# Consultant patterns
_CONSULTANT_PATTERNS = [
    re.compile(r"(?:Prepared\s+by[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:Consultant[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:Assessed\s+by[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
]

# Inspector/Assessor patterns
_INSPECTOR_PATTERNS = [
    re.compile(r"(?:Inspector[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:Assessor[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:Surveyed\s+by[:\s]+)(.+?)(?:\n|$)", re.IGNORECASE),
]

# Inspection date pattern
_INSPECTION_DATE_PATTERN = re.compile(
    r"(?:Inspection\s+Date[:\s]+)(.+?)(?:\n|$)",
    re.IGNORECASE,
)


# ============================================================================
# Cover page extraction
# ============================================================================


def _extract_cover_pages(content: str, max_pages: int = COVER_PAGE_COUNT) -> str:
    """Extract the first N pages of content for cover page analysis.

    Args:
        content: Full document markdown content.
        max_pages: Maximum number of pages to extract.

    Returns:
        Text of the first N pages.
    """
    page_positions = list(_PAGE_PATTERN.finditer(content))

    if not page_positions:
        return content

    # Find the position after max_pages page markers
    if len(page_positions) <= max_pages:
        return content

    # Return content up to the start of page (max_pages + 1)
    cutoff = page_positions[max_pages].start()
    return content[:cutoff]


# ============================================================================
# Heuristic extraction
# ============================================================================


def _heuristic_extract(content: str) -> DocumentMeta:
    """Extract metadata using regex heuristics.

    Reliable for structured fields like dates, references, and addresses.

    Args:
        content: Document text (typically first few pages).

    Returns:
        DocumentMeta with heuristically extracted fields.
    """
    if not content or not content.strip():
        return DocumentMeta(consultant_name="Unknown")

    # Extract consultant name
    consultant_name = None
    for pattern in _CONSULTANT_PATTERNS:
        match = pattern.search(content)
        if match:
            consultant_name = match.group(1).strip()
            break

    # Extract address
    site_address = None
    address_match = _ADDRESS_PATTERN.search(content)
    if address_match:
        site_address = address_match.group(0).strip()

    # Extract suburb and postcode
    suburb = None
    postcode = None
    suburb_match = _SUBURB_STATE_POSTCODE.search(content)
    if suburb_match:
        suburb = suburb_match.group(1).strip()
        postcode = suburb_match.group(2).strip()

    # Extract report reference
    report_reference = None
    for pattern in _REPORT_REF_PATTERNS:
        match = pattern.search(content)
        if match:
            report_reference = match.group(1).strip()
            break

    # Extract report date
    report_date = None
    for pattern in _DATE_PATTERNS:
        match = pattern.search(content)
        if match:
            report_date = match.group(1).strip()
            break

    # Extract inspector names
    inspector_names = []
    for pattern in _INSPECTOR_PATTERNS:
        for match in pattern.finditer(content):
            name = match.group(1).strip()
            if name and name not in inspector_names:
                inspector_names.append(name)

    # Extract inspection dates
    inspection_dates = []
    for match in _INSPECTION_DATE_PATTERN.finditer(content):
        date_str = match.group(1).strip()
        if date_str and date_str not in inspection_dates:
            inspection_dates.append(date_str)

    return DocumentMeta(
        consultant_name=consultant_name or "Unknown",
        site_address=site_address,
        suburb=suburb,
        postcode=postcode,
        report_reference=report_reference,
        report_date=report_date,
        inspector_names=inspector_names if inspector_names else None,
        inspection_dates=inspection_dates if inspection_dates else None,
    )


# ============================================================================
# LLM extraction
# ============================================================================


async def _llm_extract_metadata(
    content: str,
    model_id: Optional[str] = None,
) -> DocumentMeta:
    """Use LLM with structured output for metadata extraction.

    Args:
        content: Cover page text content.
        model_id: Optional model ID override.

    Returns:
        DocumentMeta from LLM analysis.
    """
    from ai_prompter import Prompter
    from langchain_core.messages import HumanMessage, SystemMessage

    prompter = Prompter(prompt_template="acm/metadata_extraction")
    system_prompt = prompter.render(data={"cover_pages": content})

    # TODO: Use model.get_max_output_tokens() when Model domain object is available here
    # 2048 is appropriate for metadata extraction (small structured output)
    model = await provision_langchain_model(
        content,
        model_id,
        "extraction",
        temperature=0.1,
        max_tokens=2048,
    )

    chain = model.with_structured_output(DocumentMetaLLM)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content="Extract the document metadata from the cover pages provided."
        ),
    ]
    llm_result: DocumentMetaLLM = await chain.ainvoke(messages)
    return DocumentMeta.from_llm(llm_result)


# ============================================================================
# Merge and confidence
# ============================================================================


def _merge_metadata(
    llm_result: Optional[DocumentMeta],
    heuristic_result: DocumentMeta,
) -> DocumentMeta:
    """Merge LLM and heuristic results. LLM takes priority.

    Args:
        llm_result: Metadata from LLM extraction (may be None).
        heuristic_result: Metadata from heuristic extraction.

    Returns:
        Merged DocumentMeta with LLM fields taking priority.
    """
    if llm_result is None:
        return heuristic_result

    merged_data: Dict[str, Any] = {}
    llm_dict = llm_result.model_dump()
    heuristic_dict = heuristic_result.model_dump()

    # Exclude meta fields from merge
    exclude = {"field_confidence", "additional"}

    for key in llm_dict:
        if key in exclude:
            continue
        llm_val = llm_dict.get(key)
        heuristic_val = heuristic_dict.get(key)
        # LLM takes priority if non-None and non-default
        if llm_val is not None and llm_val != "Unknown":
            merged_data[key] = llm_val
        elif heuristic_val is not None and heuristic_val != "Unknown":
            merged_data[key] = heuristic_val

    # Merge additional dicts
    merged_additional = dict(heuristic_result.additional)
    merged_additional.update(llm_result.additional)
    merged_data["additional"] = merged_additional

    # Ensure consultant_name is always present
    if "consultant_name" not in merged_data or not merged_data["consultant_name"]:
        merged_data["consultant_name"] = "Unknown"

    return DocumentMeta(**merged_data)


def _compute_confidence(
    meta: DocumentMeta,
    llm_fields: Optional[Set[str]] = None,
) -> Dict[str, str]:
    """Compute per-field confidence scoring.

    Args:
        meta: The final merged DocumentMeta.
        llm_fields: Set of field names that were extracted by LLM.

    Returns:
        Dict mapping field_name -> "extracted" | "inferred" | "missing".
    """
    if llm_fields is None:
        llm_fields = set()

    confidence: Dict[str, str] = {}
    exclude = {"field_confidence", "additional"}

    for name, value in meta.model_dump().items():
        if name in exclude:
            continue
        if value is None:
            confidence[name] = "missing"
        elif name in llm_fields:
            confidence[name] = "extracted"
        else:
            confidence[name] = "inferred"

    return confidence


# ============================================================================
# SiteConfig auto-fill
# ============================================================================


async def auto_populate_site_config(
    document_meta: DocumentMeta,
    source_id: str,
) -> None:
    """Auto-fill SiteConfig fields from extracted metadata.

    Only fills fields that are currently empty/null. Never overwrites
    user-entered values.

    Args:
        document_meta: Extracted document metadata.
        source_id: Source document ID for SiteConfig lookup.
    """
    from open_notebook.domain.site_config import SiteConfig

    mappings = document_meta.get_site_config_mappings()
    if not mappings:
        return

    # Check existing config and filter out fields that already have values
    existing = await SiteConfig.get_by_source(source_id)

    if existing:
        fields_to_fill = {}
        for field_name, value in mappings.items():
            current = getattr(existing, field_name, None)
            if not current:
                fields_to_fill[field_name] = value
        if not fields_to_fill:
            return
        # Update existing record directly to avoid double DB lookup
        for field_name, value in fields_to_fill.items():
            setattr(existing, field_name, value)
        await existing.save()
        logger.info(
            f"Auto-filled SiteConfig for source {source_id}: "
            f"{list(fields_to_fill.keys())}"
        )
    else:
        # No existing config - create via upsert
        await SiteConfig.upsert(source_id, **mappings)
        logger.info(
            f"Auto-filled SiteConfig for source {source_id}: {list(mappings.keys())}"
        )


# ============================================================================
# Main extraction function
# ============================================================================


async def extract_document_metadata(
    content: Optional[str],
    model_id: Optional[str] = None,
) -> Optional[DocumentMeta]:
    """Extract document metadata from content.

    Uses LLM with structured output for extraction, with heuristic regex
    fallback for reliability. Both results are merged with LLM taking priority.

    Args:
        content: Full document markdown content.
        model_id: Optional model ID override for LLM.

    Returns:
        DocumentMeta with extracted fields, or None if content is empty.
    """
    if not content or not content.strip():
        return None

    # Extract cover pages (first 3-5 pages)
    cover_text = _extract_cover_pages(content)

    # Always run heuristic extraction (fast, reliable)
    heuristic_result = _heuristic_extract(cover_text)

    # Try LLM extraction
    llm_result = None
    llm_fields: Set[str] = set()
    try:
        llm_result = await _llm_extract_metadata(cover_text, model_id)
        # Track which fields the LLM populated
        for name, value in llm_result.model_dump().items():
            if name not in {"field_confidence", "additional"} and value is not None:
                llm_fields.add(name)
    except Exception as e:
        logger.warning(f"LLM metadata extraction failed: {e}. Using heuristic only.")

    # Merge results
    merged = _merge_metadata(llm_result, heuristic_result)

    # Compute confidence
    merged.field_confidence = _compute_confidence(merged, llm_fields)

    logger.info(
        f"Document metadata extracted: consultant={merged.consultant_name}, "
        f"fields={len(merged.get_extracted_fields())}, "
        f"confidence_breakdown="
        f"{sum(1 for v in merged.field_confidence.values() if v == 'extracted')} extracted, "
        f"{sum(1 for v in merged.field_confidence.values() if v == 'inferred')} inferred, "
        f"{sum(1 for v in merged.field_confidence.values() if v == 'missing')} missing"
    )

    return merged
