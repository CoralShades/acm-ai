"""
Consultant Wording Normalization

Maps consultant recommendation text to canonical actions using regex
pattern matching. Supports loading custom patterns from JSON configuration.

Pattern Strategy:
1. Try patterns from consultant_wording_rules.json first (method="config")
2. Fall back to hardcoded DEFAULT_PATTERNS (method="pattern")
3. Return review_required if no patterns match (method="none")

References:
- docs/samplePDF/instructions-sample/consultant_wording_rules.json
"""

import json
import re
from pathlib import Path
from typing import Literal, NamedTuple, Optional

from loguru import logger

# Canonical actions that consultant recommendations map to
CANONICAL_ACTIONS = (
    "maintain_in_situ",
    "remove_prior_to_refurb_or_demolition",
    "restrict_access_immediately",
    "remedial_within_months",
    "confirm_status_sampling",
    "height_or_access_restriction",
    "review_required",
)


class NormalizationResult(NamedTuple):
    """Result of recommendation normalization."""

    raw_text: str
    normalized_action: Optional[str]  # canonical action or "review_required"
    confidence: float  # 1.0 for pattern match, 0.0 for no match
    method: Literal["pattern", "config", "none"]


# Default hardcoded patterns (fallback when JSON config unavailable)
DEFAULT_PATTERNS: list[tuple[str, str]] = [
    (r"\bMaintain in current condition\b", "maintain_in_situ"),
    (r"\blabel( and incorporate)? into an AMP\b", "maintain_in_situ"),
    (
        r"\bRemove (under|by) .*licensed asbestos removal contractor\b",
        "remove_prior_to_refurb_or_demolition",
    ),
    (
        r"\bprior to demolition or refurbishment\b",
        "remove_prior_to_refurb_or_demolition",
    ),
    (
        r"\bcontrolled bonded asbestos removal conditions\b",
        "remove_prior_to_refurb_or_demolition",
    ),
    (r"\bRestrict access\b|\bASAP\b", "restrict_access_immediately"),
    (r"\bwithin\s*3\s*months\b|\bnext few months\b", "remedial_within_months"),
    (r"\bConfirm status\b|\bNot Sampled\b|\bPresumed\b", "confirm_status_sampling"),
    (
        r"\bHeight restriction\b|\bRestricted Access\b|\bLive Electrical Hazard\b",
        "height_or_access_restriction",
    ),
]


# Cached wording rules from JSON
_WORDING_RULES: Optional[dict] = None


def _load_wording_rules() -> dict:
    """Load consultant wording rules JSON. Cached after first load."""
    global _WORDING_RULES
    if _WORDING_RULES is not None:
        return _WORDING_RULES

    project_root = Path(__file__).parent.parent.parent.parent
    rules_path = (
        project_root
        / "docs"
        / "samplePDF"
        / "instructions-sample"
        / "consultant_wording_rules.json"
    )

    try:
        with open(rules_path, encoding="utf-8") as f:
            _WORDING_RULES = json.load(f)
        logger.debug(f"Loaded wording rules from {rules_path}")
    except FileNotFoundError:
        logger.warning(f"Wording rules not found at {rules_path}. Using defaults.")
        _WORDING_RULES = {"consultant_phrases_to_actions": [], "universal_actions": []}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in wording rules: {e}")
        _WORDING_RULES = {"consultant_phrases_to_actions": [], "universal_actions": []}

    return _WORDING_RULES


def normalize_recommendation(raw_recommendation: Optional[str]) -> NormalizationResult:
    """
    Map consultant recommendation wording to a canonical action.

    Tries JSON-configured patterns first, then hardcoded defaults.
    Returns review_required if no patterns match.

    Args:
        raw_recommendation: Raw recommendation text from consultant report

    Returns:
        NormalizationResult with raw_text, normalized_action, confidence, method
    """
    if not raw_recommendation or not raw_recommendation.strip():
        return NormalizationResult(
            raw_text=raw_recommendation or "",
            normalized_action=None,
            confidence=0.0,
            method="none",
        )

    # Try JSON-configured patterns first
    rules = _load_wording_rules()
    for rule in rules.get("consultant_phrases_to_actions", []):
        pattern = rule.get("pattern", "")
        action = rule.get("action", "")
        if pattern and action:
            try:
                if re.search(pattern, raw_recommendation, re.IGNORECASE):
                    logger.debug(
                        f"Recommendation matched config pattern: '{raw_recommendation[:50]}' → {action}"
                    )
                    return NormalizationResult(
                        raw_text=raw_recommendation,
                        normalized_action=action,
                        confidence=1.0,
                        method="config",
                    )
            except re.error as e:
                logger.warning(f"Invalid regex in wording rules: '{pattern}': {e}")
                continue

    # Fall back to hardcoded patterns
    for pattern, action in DEFAULT_PATTERNS:
        if re.search(pattern, raw_recommendation, re.IGNORECASE):
            logger.debug(
                f"Recommendation matched default pattern: '{raw_recommendation[:50]}' → {action}"
            )
            return NormalizationResult(
                raw_text=raw_recommendation,
                normalized_action=action,
                confidence=1.0,
                method="pattern",
            )

    # No match found
    logger.debug(f"No pattern match for recommendation: '{raw_recommendation[:80]}'")
    return NormalizationResult(
        raw_text=raw_recommendation,
        normalized_action="review_required",
        confidence=0.0,
        method="none",
    )
