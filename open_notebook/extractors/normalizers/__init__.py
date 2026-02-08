"""
Normalizers Package

Contains modules for normalizing and classifying ACM (Asbestos Containing Material) data
according to Victorian BAR (Building Asbestos Register) taxonomy standards.

Modules:
- taxonomy: Product classification into BAR taxonomy groups (E1-S9)
- recommendations: Consultant wording normalization to canonical actions (E1-S12)
- enums: Enum value normalization for SampleResult, Condition, etc. (E1-S12)
"""

from .enums import normalize_enum_value
from .recommendations import (
    CANONICAL_ACTIONS,
    NormalizationResult,
    normalize_recommendation,
)
from .taxonomy import (
    ClassificationResult,
    classify_product,
    classify_product_async,
    classify_with_llm,
    get_product_groups,
    get_product_types,
)

__all__ = [
    # Taxonomy (E1-S9)
    "ClassificationResult",
    "classify_product",
    "classify_product_async",
    "classify_with_llm",
    "get_product_groups",
    "get_product_types",
    # Recommendations (E1-S12)
    "CANONICAL_ACTIONS",
    "NormalizationResult",
    "normalize_recommendation",
    # Enums (E1-S12)
    "normalize_enum_value",
]
