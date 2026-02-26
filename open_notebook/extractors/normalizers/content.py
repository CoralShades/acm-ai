"""Docling content normalization helpers for ACM extraction."""

import re
from typing import Dict, Tuple

from loguru import logger

_NORMALIZATION_RULES: Tuple[Tuple[str, str, str, int], ...] = (
    (
        r"\bAsbestos\s*\n\s*Assumed\s*\n\s*positive\b",
        "Asbestos Assumed positive",
        "asbestos_assumed_positive",
        re.IGNORECASE,
    ),
    (
        r"\bAsbestos\s*\n\s*Negative\b",
        "Asbestos Negative",
        "asbestos_negative",
        re.IGNORECASE,
    ),
    (
        r"\bAsbestos\s*\n\s*Positive\b",
        "Asbestos Positive",
        "asbestos_positive",
        re.IGNORECASE,
    ),
    (
        r"(Same\s+as)\s*\n\s*(34511-039-?\d+)",
        r"\1 \2",
        "same_as_sample_ref",
        re.IGNORECASE,
    ),
    (
        r"\bAssumed\s*\n\s*positive\b",
        "Assumed positive",
        "assumed_positive",
        re.IGNORECASE,
    ),
    (
        r"\bNo\s*\n\s*access\b",
        "No access",
        "no_access",
        re.IGNORECASE,
    ),
    (
        r"\bN/?A\s*\n\s*\(negative\)",
        "N/A (negative)",
        "na_negative",
        re.IGNORECASE,
    ),
    (
        r"\bNot\s*\n\s*sampled\b",
        "Not sampled",
        "not_sampled",
        re.IGNORECASE,
    ),
    (
        r"(\d{5})\s*\n\s*-\s*\n\s*(\d{3})\s*\n\s*-\s*\n\s*(\d{3})",
        r"\1-\2-\3",
        "split_sample_number",
        re.IGNORECASE,
    ),
)


def normalize_docling_text(text: str) -> str:
    """Normalize line-broken Docling values before LLM extraction.

    Args:
        text: Raw Docling text content.

    Returns:
        Text with targeted line-break fixes applied.
    """
    if not text:
        return text

    normalized = text
    fix_counts: Dict[str, int] = {}
    total_fixes = 0

    for pattern, replacement, fix_name, flags in _NORMALIZATION_RULES:
        normalized, count = re.subn(pattern, replacement, normalized, flags=flags)
        if count > 0:
            fix_counts[fix_name] = count
            total_fixes += count

    if total_fixes > 0:
        logger.info(
            "Docling normalization applied {total_fixes} fixes: {fix_counts}",
            total_fixes=total_fixes,
            fix_counts=fix_counts,
        )

    return normalized
