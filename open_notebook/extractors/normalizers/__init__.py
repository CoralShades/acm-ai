"""
Normalizers Package

Contains modules for normalizing and classifying ACM (Asbestos Containing Material) data
according to Victorian BAR (Building Asbestos Register) taxonomy standards.
"""

from .taxonomy import (
    ClassificationResult,
    classify_product,
    classify_product_async,
    classify_with_llm,
    get_product_groups,
    get_product_types,
)

__all__ = [
    "ClassificationResult",
    "classify_product",
    "classify_product_async",
    "classify_with_llm",
    "get_product_groups",
    "get_product_types",
]
