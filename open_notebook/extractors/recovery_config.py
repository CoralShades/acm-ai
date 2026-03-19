"""Format-specific recovery configuration.

Extracted from hardcoded patterns in acm_extraction.py to enable
per-consultant customization of record recovery behavior.

Story: Multi-Consultant Story 2 — Schema Inference Node
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecoveryConfig:
    """Format-specific configuration for record recovery functions.

    Default values match the existing hardcoded patterns in acm_extraction.py
    to ensure backward compatibility.
    """

    # "Not Sampled" synonyms (acm_extraction.py:2295)
    not_sampled_terms: list[str] = field(
        default_factory=lambda: [
            "Not Sampled",
            "Not Accessible",
            "Access Denied",
            "No Access",
        ]
    )
    # Confirmation terms (what follows "Not Sampled")
    confirmation_terms: list[str] = field(
        default_factory=lambda: [
            "Presumed Positive",
            "Assumed Positive",
            "Assumed",
        ]
    )
    # Access restriction vocabulary (acm_extraction.py:2321)
    restriction_terms: list[str] = field(
        default_factory=lambda: [
            "Restricted Access",
            "Height Restricted",
            "Live Electrical",
            "Confined Space",
            "Inaccessible",
        ]
    )
    # Section header regex (ARA: "Name - Interior/Exterior - Level")
    section_header_re: Optional[re.Pattern] = None
    # Level detection regex override
    level_re: Optional[re.Pattern] = None
    # Product keyword set for no-access recovery
    product_keywords: Optional[set[str]] = None
    # Scan window sizes
    lookback_lines: int = 5
    lookahead_lines: int = 3
    # Content boundary pattern for Ollama chunking
    content_boundary_re: Optional[re.Pattern] = None
