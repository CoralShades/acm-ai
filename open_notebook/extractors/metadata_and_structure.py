"""
Combined Metadata & Structure Extraction (S4: Merge Pre-Extraction LLM Calls).

Merges the metadata extraction (E1-S19) and structure extraction (E1-S16)
into a single LLM call, reducing pre-extraction from 4 LLM calls to 2.

Also provides synthesize_page_tags() which replaces the page tagging LLM call
by deriving page tags from BuildingInventory + DocumentStructure.
"""

from typing import Optional, Set, Tuple

from loguru import logger
from pydantic import BaseModel

from open_notebook.extractors.building_inventory import BuildingInventory
from open_notebook.extractors.document_structure import (
    DocumentStructure,
    DocumentStructureLLM,
    _extract_total_pages,
    _heuristic_fallback,
)
from open_notebook.extractors.metadata_extractor import (
    _compute_confidence,
    _extract_cover_pages,
    _heuristic_extract,
    _merge_metadata,
)
from open_notebook.extractors.page_tagger import (
    _SECTION_TITLES,
    PageTag,
    PageTaggingResult,
    PageType,
    SectionTaxonomy,
    _compute_register_range,
)
from open_notebook.extractors.parsers.base import DocumentMeta, DocumentMetaLLM


class MetadataAndStructureLLM(BaseModel):
    """Combined LLM output for metadata + structure extraction."""

    metadata: DocumentMetaLLM
    structure: DocumentStructureLLM


async def extract_metadata_and_structure(
    content: str,
    model_id: Optional[str] = None,
) -> Tuple[Optional[DocumentMeta], DocumentStructure]:
    """Extract both metadata and structure in a single LLM call.

    Args:
        content: Full document markdown content.
        model_id: Optional model ID override.

    Returns:
        Tuple of (DocumentMeta or None, DocumentStructure).
    """
    if not content or not content.strip():
        return None, DocumentStructure()

    total_pages = _extract_total_pages(content)

    # Always run heuristic metadata extraction (fast, reliable)
    cover_text = _extract_cover_pages(content)
    heuristic_meta = _heuristic_extract(cover_text)

    # Try combined LLM extraction
    llm_meta = None
    llm_fields: Set[str] = set()
    structure = None

    try:
        llm_meta, structure = await _llm_extract_combined(content, model_id)
        if llm_meta:
            for name, value in llm_meta.model_dump().items():
                if name not in {"field_confidence", "additional"} and value is not None:
                    llm_fields.add(name)
    except Exception as e:
        logger.warning(f"Combined metadata+structure LLM extraction failed: {e}")

    # Merge metadata (LLM + heuristic)
    merged_meta = _merge_metadata(llm_meta, heuristic_meta)
    merged_meta.field_confidence = _compute_confidence(merged_meta, llm_fields)

    # Fallback structure if LLM failed
    if structure is None:
        logger.warning("Using heuristic fallback for document structure")
        structure = _heuristic_fallback(content)

    # Override total_pages from regex markers (more reliable than LLM)
    if total_pages > 0:
        structure.total_pages = total_pages

    logger.info(
        f"Combined extraction: consultant={merged_meta.consultant_name}, "
        f"type={structure.document_type}, register_start={structure.register_start_page}, "
        f"buildings={len(structure.building_ids)}, pages={structure.total_pages}"
    )

    return merged_meta, structure


async def _llm_extract_combined(
    content: str,
    model_id: Optional[str] = None,
) -> Tuple[Optional[DocumentMeta], DocumentStructure]:
    """Single LLM call for combined metadata + structure extraction."""
    from ai_prompter import Prompter
    from langchain_core.messages import HumanMessage, SystemMessage

    from open_notebook.graphs.utils import (
        _apply_ollama_extraction_settings,
        _verify_provider_routing,
        parse_json_response,
        provision_langchain_model,
    )

    prompter = Prompter(prompt_template="acm/metadata_and_structure")
    system_prompt = prompter.render(data={})

    model = await provision_langchain_model(
        content,
        model_id,
        "extraction",
        temperature=0.1,
        max_tokens=16384,
    )

    # Force format="json" for Ollama models (prevents conversational text output)
    _apply_ollama_extraction_settings(model)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                "## Document Content\n\n"
                f"{content}\n\n"
                "Extract both the document metadata and structure from the content above."
            )
        ),
    ]

    raw_response = await model.ainvoke(messages)

    # Verify provider routing (non-blocking)
    try:
        await _verify_provider_routing(raw_response, "metadata_and_structure")
    except Exception:
        pass

    response_text = (
        raw_response.content if hasattr(raw_response, "content") else str(raw_response)
    )
    parsed = parse_json_response(response_text)

    combined = MetadataAndStructureLLM.model_validate(parsed)
    meta = DocumentMeta.from_llm(combined.metadata)
    structure = DocumentStructure(**combined.structure.model_dump())

    return meta, structure


def synthesize_page_tags(
    inventory: BuildingInventory,
    structure: DocumentStructure,
) -> PageTaggingResult:
    """Synthesize page tags from inventory + structure (replaces LLM page tagging).

    For each building in inventory, marks its page range as ASBESTOS_REGISTER.
    Pages before register_start_page are marked INTRODUCTION.
    """
    tags = []
    register_pages: set[int] = set()

    # Mark building pages as register
    for b in inventory.buildings:
        end = b.page_end or b.page_start
        for p in range(b.page_start, end + 1):
            if p not in register_pages:
                register_pages.add(p)
                tags.append(
                    PageTag(
                        page_number=p,
                        section_id=SectionTaxonomy.ASBESTOS_REGISTER,
                        section_title=_SECTION_TITLES[
                            SectionTaxonomy.ASBESTOS_REGISTER
                        ],
                        confidence=0.8,
                        page_type=PageType.CONTENT,
                    )
                )

    # Mark pre-register pages as introduction
    register_start = structure.register_start_page
    if register_start and register_start > 1:
        for p in range(1, register_start):
            if p not in register_pages:
                tags.append(
                    PageTag(
                        page_number=p,
                        section_id=SectionTaxonomy.INTRODUCTION,
                        section_title=_SECTION_TITLES[SectionTaxonomy.INTRODUCTION],
                        confidence=0.5,
                        page_type=PageType.CONTENT,
                    )
                )

    # Sort by page number
    tags.sort(key=lambda t: t.page_number)

    register_range = _compute_register_range(tags)

    return PageTaggingResult(
        pages=tags,
        total_pages=structure.total_pages,
        register_page_range=register_range,
    )
