"""
ACM Product Taxonomy Classification

Classifies ACM (Asbestos Containing Material) products into Victorian BAR
(Building Asbestos Register) taxonomy groups and types.

Classification Strategy:
1. Pattern-based regex matching for common ACM product types (primary method)
2. Falls back to LLM classification for ambiguous items (secondary method)
3. Selects appropriate taxonomy (Non-friable T1-T8 or Friable T1-T6) based on friability

References:
- docs/samplePDF/instructions-sample/register_taxonomy.nonfriable.json
- docs/samplePDF/instructions-sample/register_taxonomy.friable.json
"""

import json
import re
from pathlib import Path
from typing import Literal, NamedTuple, Optional

from loguru import logger


class ClassificationResult(NamedTuple):
    """Result of ACM product classification."""

    product_group: Optional[str]
    product_type: Optional[str]
    confidence: float
    method: Literal["pattern", "llm", "none"]


# Strip T-prefix (e.g., "T3 Vinyl products" → "Vinyl products") for SF alignment
_T_PREFIX_RE = re.compile(r"^T\d+\s+")


def _strip_t_prefix(group: Optional[str]) -> Optional[str]:
    """Strip BAR T-prefix from product group name for SF picklist alignment."""
    if group is None:
        return None
    return _T_PREFIX_RE.sub("", group)


# Taxonomy data loaded from JSON files
_NONFRIABLE_TAXONOMY: Optional[dict] = None
_FRIABLE_TAXONOMY: Optional[dict] = None


def _load_taxonomy_files() -> tuple[dict, dict]:
    """Load taxonomy JSON files. Cached after first load."""
    global _NONFRIABLE_TAXONOMY, _FRIABLE_TAXONOMY

    if _NONFRIABLE_TAXONOMY is not None and _FRIABLE_TAXONOMY is not None:
        return _NONFRIABLE_TAXONOMY, _FRIABLE_TAXONOMY

    # Find taxonomy files relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    nonfriable_path = (
        project_root
        / "docs"
        / "samplePDF"
        / "instructions-sample"
        / "register_taxonomy.nonfriable.json"
    )
    friable_path = (
        project_root
        / "docs"
        / "samplePDF"
        / "instructions-sample"
        / "register_taxonomy.friable.json"
    )

    try:
        with open(nonfriable_path, encoding="utf-8") as f:
            _NONFRIABLE_TAXONOMY = json.load(f)
        with open(friable_path, encoding="utf-8") as f:
            _FRIABLE_TAXONOMY = json.load(f)
        logger.debug(f"Loaded taxonomy files from {nonfriable_path.parent}")
    except FileNotFoundError as e:
        logger.warning(f"Taxonomy file not found: {e}. Using empty taxonomy.")
        _NONFRIABLE_TAXONOMY = {"groups": []}
        _FRIABLE_TAXONOMY = {"groups": []}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in taxonomy file: {e}")
        _NONFRIABLE_TAXONOMY = {"groups": []}
        _FRIABLE_TAXONOMY = {"groups": []}

    return _NONFRIABLE_TAXONOMY, _FRIABLE_TAXONOMY


def get_product_groups(friability: Optional[str] = None) -> list[dict]:
    """
    Get available product groups for a given friability.

    Args:
        friability: "Friable", "Non-friable", or None (defaults to Non-friable)

    Returns:
        List of product group dictionaries with keys: pc_code, product_group_header, product_types
    """
    nonfriable, friable = _load_taxonomy_files()

    if (
        friability
        and "friable" in friability.lower()
        and "non" not in friability.lower()
    ):
        return friable.get("groups", [])
    return nonfriable.get("groups", [])


def get_product_types(
    product_group: str, friability: Optional[str] = None
) -> list[str]:
    """
    Get product types for a specific product group.

    Args:
        product_group: Product group header (e.g., "T1 Cement products")
        friability: "Friable", "Non-friable", or None

    Returns:
        List of product type strings
    """
    groups = get_product_groups(friability)
    for group in groups:
        if group.get("product_group_header") == product_group:
            return group.get("product_types", [])
        # Also match by code (e.g., "T1")
        if product_group.startswith(group.get("pc_code", "")):
            return group.get("product_types", [])
    return []


# Classification patterns: (regex, applies_to_friability, product_group, product_type)
# applies_to_friability: "any" | "Friable" | "Non-friable"
# If applies_to_friability is "any", the pattern works for both; group name differs by taxonomy
CLASSIFICATION_PATTERNS: list[tuple[str, str, str, str, str, str]] = [
    # Pattern format: (regex, applies_to, nonfriable_group, nonfriable_type, friable_group, friable_type)
    # === Vinyl Products (Non-friable T3, Friable T2) ===
    (
        r"vinyl\s*(sheet|flooring)",
        "any",
        "T3 Vinyl products",
        "Vinyl sheet",
        "T2 Vinyl products",
        "Vinyl sheet",
    ),
    (
        r"vinyl\s*.*tile",
        "any",
        "T3 Vinyl products",
        "Vinyl Tiles",
        "T2 Vinyl products",
        "Vinyl Tiles",
    ),
    (
        r"linoleum",
        "any",
        "T3 Vinyl products",
        "Vinyl sheet",
        "T2 Vinyl products",
        "Vinyl sheet",
    ),
    (
        r"hessian\s*backed\s*vinyl",
        "any",
        "T3 Vinyl products",
        "Hessian backed Vinyl sheet",
        "T2 Vinyl products",
        "Hessian backed Vinyl sheet",
    ),
    (
        r"vinyl.*adhesive",
        "any",
        "T3 Vinyl products",
        "Vinyl sheet and adhesive",
        "T2 Vinyl products",
        "Vinyl sheet and adhesive",
    ),
    # === Cement Products (Non-friable T1, Friable T1) ===
    # Note: Use \bfibro\b word boundary to avoid matching "fibrous"
    (
        r"(fibre|fiber)\s*cement|fc\s*sheet|\bfibro\b",
        "any",
        "T1 Cement products",
        "Flat Sheeting",
        "T1 Cement products",
        "Flat Sheeting",
    ),
    (
        r"corrugated.*roof|roof.*corrugated",
        "any",
        "T1 Cement products",
        "Corrugated Roof Sheeting",
        "T1 Cement products",
        "Corrugated Roof Sheeting",
    ),
    (
        r"weatherboard",
        "any",
        "T1 Cement products",
        "Weatherboards",
        "T1 Cement products",
        "Weatherboards",
    ),
    (
        r"flat\s*sheet",
        "any",
        "T1 Cement products",
        "Flat Sheeting",
        "T1 Cement products",
        "Flat Sheeting",
    ),
    (
        r"compressed\s*sheet",
        "any",
        "T1 Cement products",
        "Compressed Flat Sheeting",
        "T1 Cement products",
        "Compressed Flat Sheeting",
    ),
    (
        r"cement\s*pipe|flue\s*pipe",
        "any",
        "T1 Cement products",
        "Cement Pipe",
        "T1 Cement products",
        "Cement Pipe",
    ),
    (
        r"cement\s*flue|flue",
        "any",
        "T1 Cement products",
        "Cement Flue",
        "T1 Cement products",
        "Cement Flue",
    ),
    (
        r"ceiling\s*tile",
        "any",
        "T1 Cement products",
        "Ceiling Tiles",
        "T1 Cement products",
        "Ceiling Tiles",
    ),
    (
        r"ridge\s*capping|capping",
        "any",
        "T1 Cement products",
        "Ridge Capping",
        "T1 Cement products",
        "Ridge capping",
    ),
    (
        r"roof\s*tile",
        "any",
        "T1 Cement products",
        "Roof Tiles",
        "T1 Cement products",
        "Roof Tiles",
    ),
    (
        r"eave|soffit|lining",
        "any",
        "T1 Cement products",
        "Internal Lining",
        "T1 Cement products",
        "Internal Lining",
    ),
    (
        r"gutter",
        "any",
        "T1 Cement products",
        "Rainwater Guttering",
        "T1 Cement products",
        "Rainwater Guttering",
    ),
    (
        r"tilux",
        "any",
        "T1 Cement products",
        "Flat Sheeting",
        "T1 Cement products",
        "Tilux sheeting",
    ),
    (
        r"water\s*tank",
        "any",
        "T1 Cement products",
        "Water Tanks",
        "T1 Cement products",
        "Water Tanks",
    ),
    (r"vent", "any", "T1 Cement products", "Vents", "T1 Cement products", "Vents"),
    # === Bitumen Products (Non-friable T2 only) ===
    (
        r"bitumen|bituminous",
        "Non-friable",
        "T2 Bitumen products",
        "Bituminous Membrane",
        "",
        "",
    ),
    (r"malthoid", "Non-friable", "T2 Bitumen products", "Malthoid", "", ""),
    (r"asphalt", "Non-friable", "T2 Bitumen products", "Asphalt", "", ""),
    (r"galbestos", "Non-friable", "T2 Bitumen products", "Galbestos", "", ""),
    (
        r"blackjack",
        "Non-friable",
        "T2 Bitumen products",
        "Blackjack (Bitumen Adhesive)",
        "",
        "",
    ),
    # === Gasket Products (Non-friable T4, Friable T4) ===
    (
        r"mastic",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Mastic",
        "T4 Gasket products",
        "Mastic",
    ),
    (
        r"gasket",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Gasket(s)",
        "T4 Gasket products",
        "Gasket(s)",
    ),
    (
        r"caulk",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Caulking",
        "T4 Gasket products",
        "Caulking",
    ),
    (
        r"putty",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Putty",
        "T4 Gasket products",
        "Putty",
    ),
    (
        r"rope.*gasket|braided\s*gasket",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Rope or Braided Gasket",
        "T4 Gasket products",
        "Rope or Braided Gasket",
    ),
    (
        r"brake\s*pad",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Brake pads",
        "T4 Gasket products",
        "Brake pads",
    ),
    (
        r"clutch\s*plate",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Clutch Plates",
        "T4 Gasket products",
        "Clutch Plates",
    ),
    (
        r"rubber\s*gasket",
        "any",
        "T4 Gasket, friction products and adhesives",
        "Rubber Gasket",
        "T4 Gasket products",
        "Rubber Gasket",
    ),
    # === Insulation Products (Non-friable T8, Friable T3) ===
    (
        r"lagging|pipe\s*insulation",
        "any",
        "T8 Insulation",
        "Lagging",
        "T3 Insulation products",
        "Lagging",
    ),
    (
        r"millboard",
        "any",
        "T8 Insulation",
        "Millboard",
        "T3 Insulation products",
        "Millboard",
    ),
    (
        r"vermiculite",
        "any",
        "T8 Insulation",
        "Vermiculite",
        "T3 Insulation products",
        "Vermiculite",
    ),
    (
        r"loose\s*fill|ceiling\s*insulation",
        "any",
        "T8 Insulation",
        "Loose Fill Insulation",
        "T3 Insulation products",
        "Loose Fill Insulation",
    ),
    (r"limpet", "any", "T8 Insulation", "Limpet", "T3 Insulation products", "Limpet"),
    (
        r"aib|insulation\s*board",
        "any",
        "T8 Insulation",
        "Low Density Asbestos Fibre Board (Asbestos Insulated Board)",
        "T3 Insulation products",
        "AIB (insulation board)",
    ),
    (
        r"fire\s*door\s*core",
        "any",
        "T8 Insulation",
        "Fire Door Core",
        "T3 Insulation products",
        "Fire Door Core",
    ),
    (
        r"fire\s*rating|fire\s*rated",
        "any",
        "T8 Insulation",
        "Fire Rating Material",
        "T3 Insulation products",
        "Fire Rating Material",
    ),
    (
        r"sprayed\s*insulation|spray.*insulation",
        "Friable",
        "",
        "",
        "T3 Insulation products",
        "Sprayed Insulation",
    ),
    (
        r"ceramic\s*fibre",
        "any",
        "T8 Insulation",
        "Ceramic Fibre",
        "T3 Insulation products",
        "Ceramic Fibre",
    ),
    (
        r"hessian",
        "any",
        "T8 Insulation",
        "Hessian",
        "T3 Insulation products",
        "Hessian",
    ),
    (
        r"gland\s*packing",
        "any",
        "T8 Insulation",
        "Gland Packing",
        "T3 Insulation products",
        "Gland Packing",
    ),
    (
        r"strawboard",
        "any",
        "T8 Insulation",
        "Strawboard",
        "T3 Insulation products",
        "Strawboard",
    ),
    (r"tape", "any", "T8 Insulation", "Tape", "T3 Insulation products", "Tape"),
    # === Coatings (Non-friable T5 only) ===
    (
        r"paint|coating|textured\s*coat",
        "Non-friable",
        "T5 Coatings",
        "Textured Coating",
        "",
        "",
    ),
    # === Reinforced Plastics (Non-friable T6 only) ===
    (
        r"plastic|stair\s*nosing",
        "Non-friable",
        "T6 Reinforced plastics/resins (excluding bitumen products)",
        "Plastic",
        "",
        "",
    ),
    (
        r"toilet\s*seat",
        "Non-friable",
        "T6 Reinforced plastics/resins (excluding bitumen products)",
        "Toilet Seats",
        "",
        "",
    ),
    (
        r"electrical\s*meter",
        "Non-friable",
        "T6 Reinforced plastics/resins (excluding bitumen products)",
        "Electrical Meters",
        "",
        "",
    ),
    (
        r"electrical\s*component",
        "Non-friable",
        "T6 Reinforced plastics/resins (excluding bitumen products)",
        "Electrical Components",
        "",
        "",
    ),
    # === Textiles (Friable T5 only) ===
    (r"fire\s*blanket", "Friable", "", "", "T5 Textiles", "Fire blanket"),
    (r"cloth|textile", "Friable", "", "", "T5 Textiles", "Cloth"),
    (r"gloves", "Friable", "", "", "T5 Textiles", "Gloves"),
    (r"rope|string", "Friable", "", "", "T5 Textiles", "Rope and string"),
    # === Other (Non-friable T7, Friable T6) ===
    (r"mortar", "any", "T7 Other", "Mortar", "T6 Other", "Mortar"),
    (r"render", "any", "T7 Other", "Render", "T6 Other", "Render"),
    (r"plaster", "any", "T7 Other", "Plaster", "T6 Other", "Plaster"),
    (r"grout", "any", "T7 Other", "Grout", "T6 Other", "Grout"),
    (r"terrazzo", "any", "T7 Other", "Terrazzo", "T6 Other", "Terrazzo"),
    (r"masonry", "any", "T7 Other", "Masonry", "T6 Other", "Masonry"),
    (
        r"concrete|levelling\s*compound",
        "any",
        "T7 Other",
        "Concrete/levelling compound",
        "T6 Other",
        "Concrete Levelling Compound",
    ),
    (r"debris", "any", "T7 Other", "Debris", "T6 Other", "Debris"),
    (r"dust", "any", "T7 Other", "Dust", "T6 Other", "Dust"),
    (
        r"contaminated\s*soil",
        "any",
        "T7 Other",
        "Contaminated Soil (Non-friable Debris)",
        "T6 Other",
        "Contaminated Soil (Friable Debris)",
    ),
    (
        r"contaminated\s*material",
        "any",
        "T7 Other",
        "Contaminated Materials",
        "T6 Other",
        "Contaminated Materials",
    ),
    (
        r"carpet\s*underlay",
        "any",
        "T7 Other",
        "Contaminated Carpet Underlay",
        "T6 Other",
        "Contaminated Carpet Underlay",
    ),
    (
        r"fire\s*brick",
        "any",
        "T7 Other",
        "Fire brick",
        "T3 Insulation products",
        "Fire Brick",
    ),
    (r"cardboard", "any", "T7 Other", "Cardboard", "T6 Other", "Cardboard"),
    (r"paper", "any", "T7 Other", "Paper", "T5 Textiles", "Paper"),
]


def _normalize_friability(friability: Optional[str]) -> str:
    """
    Normalize friability value to standard format.

    Args:
        friability: Raw friability string (various formats)

    Returns:
        "Friable" or "Non-friable"
    """
    if not friability:
        return "Non-friable"

    friability_lower = friability.lower().strip()

    # Handle variations
    if "non" in friability_lower or "nf" == friability_lower:
        return "Non-friable"
    if "friable" in friability_lower or "f" == friability_lower:
        return "Friable"

    # Default to non-friable for unknown values
    return "Non-friable"


def classify_product(
    item_description: str,
    friability: Optional[str] = None,
    product: Optional[str] = None,
) -> ClassificationResult:
    """
    Classify an ACM item into Victorian BAR taxonomy.

    Uses pattern-based regex matching as the primary classification method.
    Falls back to LLM classification if no pattern matches (when implemented).

    Args:
        item_description: Material description or combined product/material text
        friability: "Friable", "Non-friable", "Non Friable", or None
        product: Optional product field (combined with item_description for matching)

    Returns:
        ClassificationResult with product_group, product_type, confidence, and method

    Example:
        >>> result = classify_product("Vinyl floor tiles", friability="Non-friable")
        >>> result.product_group
        'Vinyl products'
        >>> result.product_type
        'Vinyl Tiles'
        >>> result.method
        'pattern'
    """
    if not item_description or not item_description.strip():
        return ClassificationResult(
            product_group=None, product_type=None, confidence=0.0, method="none"
        )

    # Normalize friability
    normalized_friability = _normalize_friability(friability)
    is_friable = normalized_friability == "Friable"

    # Combine product and description for matching
    search_text = item_description.lower()
    if product:
        search_text = f"{product.lower()} {search_text}"

    # Try pattern matching
    for pattern_tuple in CLASSIFICATION_PATTERNS:
        regex_pattern, applies_to, nf_group, nf_type, f_group, f_type = pattern_tuple

        # Check if pattern applies to this friability
        if applies_to == "Friable" and not is_friable:
            continue
        if applies_to == "Non-friable" and is_friable:
            continue

        # Try regex match
        if re.search(regex_pattern, search_text, re.IGNORECASE):
            # Select appropriate group/type based on friability
            if is_friable:
                if f_group:  # Pattern has friable-specific classification
                    return ClassificationResult(
                        product_group=_strip_t_prefix(f_group),
                        product_type=f_type,
                        confidence=0.9,
                        method="pattern",
                    )
            else:
                if nf_group:  # Pattern has non-friable-specific classification
                    return ClassificationResult(
                        product_group=_strip_t_prefix(nf_group),
                        product_type=nf_type,
                        confidence=0.9,
                        method="pattern",
                    )

    # No pattern match - return no classification (LLM fallback to be implemented)
    # For now, return with method="none" indicating classification needed
    return ClassificationResult(
        product_group=None, product_type=None, confidence=0.0, method="none"
    )


async def classify_with_llm(
    item_description: str,
    friability: Optional[str] = None,
    product: Optional[str] = None,
) -> ClassificationResult:
    """
    Classify an ACM item using LLM with few-shot prompting.

    This is the fallback classification method when pattern matching fails.
    Uses Esperanto for multi-provider LLM abstraction.

    Args:
        item_description: Material description text
        friability: "Friable" or "Non-friable"
        product: Optional product field

    Returns:
        ClassificationResult with confidence score
    """
    try:
        from ai_prompter import Prompter
        from langchain_core.messages import HumanMessage, SystemMessage

        from open_notebook.domain.models import model_manager
    except ImportError as e:
        logger.warning(f"LLM classification dependencies not available: {e}")
        return ClassificationResult(
            product_group=None, product_type=None, confidence=0.0, method="none"
        )

    if not item_description or not item_description.strip():
        return ClassificationResult(
            product_group=None, product_type=None, confidence=0.0, method="none"
        )

    # Normalize friability
    normalized_friability = _normalize_friability(friability)

    try:
        # Render the classification prompt
        prompter = Prompter(prompt_template="acm/classification")
        system_prompt = prompter.render(
            data={
                "item_description": item_description,
                "product": product,
                "friability": normalized_friability,
            }
        )

        # Get default extraction model (or fallback to transformation model)
        model = await model_manager.get_default_model("extraction")
        if model is None:
            model = await model_manager.get_default_model("transformation")

        if model is None:
            logger.warning("No LLM model available for classification")
            return ClassificationResult(
                product_group=None, product_type=None, confidence=0.0, method="none"
            )

        # Convert to LangChain and invoke
        langchain_model = model.to_langchain()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Classify this ACM item: {item_description}"),
        ]
        response = await langchain_model.ainvoke(messages)

        # Parse JSON response
        response_text = response.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        result = json.loads(response_text)

        product_group = _strip_t_prefix(result.get("product_group"))
        product_type = result.get("product_type")
        confidence = float(result.get("confidence", 0.5))

        if product_group and product_type:
            logger.debug(
                f"LLM classified '{item_description}' as {product_group}/{product_type} "
                f"(confidence: {confidence})"
            )
            return ClassificationResult(
                product_group=product_group,
                product_type=product_type,
                confidence=confidence,
                method="llm",
            )
        else:
            return ClassificationResult(
                product_group=None, product_type=None, confidence=0.0, method="none"
            )

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM classification response: {e}")
        return ClassificationResult(
            product_group=None, product_type=None, confidence=0.0, method="none"
        )
    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return ClassificationResult(
            product_group=None, product_type=None, confidence=0.0, method="none"
        )


async def classify_product_async(
    item_description: str,
    friability: Optional[str] = None,
    product: Optional[str] = None,
    use_llm_fallback: bool = True,
) -> ClassificationResult:
    """
    Classify an ACM item with pattern matching and optional LLM fallback.

    This is the recommended async function for classification as it tries
    pattern matching first (fast) and only falls back to LLM (slow) if needed.

    Args:
        item_description: Material description text
        friability: "Friable", "Non-friable", or None
        product: Optional product field
        use_llm_fallback: Whether to use LLM if pattern matching fails

    Returns:
        ClassificationResult with product_group, product_type, confidence, and method

    Example:
        >>> result = await classify_product_async("Unknown material", use_llm_fallback=True)
        >>> result.method
        'llm'  # or 'pattern' if pattern matched
    """
    # Try pattern matching first (fast, synchronous)
    result = classify_product(item_description, friability, product)

    # If pattern matched, return the result
    if result.method == "pattern":
        return result

    # If no pattern match and LLM fallback is enabled, try LLM
    if use_llm_fallback:
        return await classify_with_llm(item_description, friability, product)

    # Return the no-match result
    return result
