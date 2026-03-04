"""
Capability Registry + Fallback Contract.

Centralizes all extraction strategy routing decisions and fallback contracts
(F1-F8) from the architecture delta into a testable lookup table. This is a
registry, not an abstraction layer — all routing decisions are statically
defined and deterministic.

Story: E29-S4 Capability Registry + Fallback Contract
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from open_notebook.extractors.building_inventory import BuildingMeta
    from open_notebook.extractors.orchestrator import ExtractionStrategy
    from open_notebook.extractors.page_tagger import PageTaggingResult


# ---------------------------------------------------------------------------
# Fallback Identifiers (telemetry tags)
# ---------------------------------------------------------------------------


class FallbackId(str, Enum):
    """Identifier for each fallback scenario in the extraction pipeline."""

    F1_NO_INVENTORY = "fallback.no_inventory"
    F2_NO_DOCLING_TABLES = "fallback.no_docling_tables"
    F3_JSON_PARSE = "fallback.json_parse"
    F4_EMPTY_EXTRACTION = "fallback.empty_extraction"
    F5_VALIDATION_FAILURE = "fallback.validation_failure"
    F6_CORRECTION_EXHAUSTED = "fallback.correction_exhausted"
    F7_LLM_ERROR = "fallback.llm_error"
    F8_DOCLING_FAILURE = "fallback.docling_failure"


# ---------------------------------------------------------------------------
# Fallback Contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FallbackContract:
    """Immutable contract describing a single fallback scenario."""

    id: FallbackId
    detection: str
    behavior: str
    severity: str
    telemetry_tag: str
    retry_eligible: bool


# ---------------------------------------------------------------------------
# Retry Contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryContract:
    """Immutable contract for retry behavior."""

    max_retries: int = 3
    backoff_seconds: float = 5.0


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

FALLBACK_MATRIX: dict[FallbackId, FallbackContract] = {
    FallbackId.F1_NO_INVENTORY: FallbackContract(
        id=FallbackId.F1_NO_INVENTORY,
        detection="inventory is None or len(inventory.buildings) == 0",
        behavior="Create synthetic whole-document extraction plan",
        severity="non-fatal (degraded)",
        telemetry_tag="fallback.no_inventory",
        retry_eligible=False,
    ),
    FallbackId.F2_NO_DOCLING_TABLES: FallbackContract(
        id=FallbackId.F2_NO_DOCLING_TABLES,
        detection="_get_docling_tables() returns empty list",
        behavior="Continue text-only extraction using full_text content",
        severity="non-fatal (degraded)",
        telemetry_tag="fallback.no_docling_tables",
        retry_eligible=False,
    ),
    FallbackId.F3_JSON_PARSE: FallbackContract(
        id=FallbackId.F3_JSON_PARSE,
        detection="parse_json_response() raises JSONDecodeError or TruncationError",
        behavior="Resilient parser: strip fences, scan brace depth, select largest valid object",
        severity="non-fatal (retry-eligible)",
        telemetry_tag="fallback.json_parse",
        retry_eligible=True,
    ),
    FallbackId.F4_EMPTY_EXTRACTION: FallbackContract(
        id=FallbackId.F4_EMPTY_EXTRACTION,
        detection="Parsed response has len(records) == 0",
        behavior="Log warning + continue (building may legitimately have no ACM)",
        severity="non-fatal",
        telemetry_tag="fallback.empty_extraction",
        retry_eligible=False,
    ),
    FallbackId.F5_VALIDATION_FAILURE: FallbackContract(
        id=FallbackId.F5_VALIDATION_FAILURE,
        detection="ACMExtractionResult.model_validate() raises ValidationError",
        behavior="Targeted correction: send failed records + validation errors to LLM (max 3 retries)",
        severity="retry-bounded",
        telemetry_tag="fallback.validation_failure",
        retry_eligible=True,
    ),
    FallbackId.F6_CORRECTION_EXHAUSTED: FallbackContract(
        id=FallbackId.F6_CORRECTION_EXHAUSTED,
        detection="correction_count >= max_retries",
        behavior="Accept records that passed validation; drop records that still fail",
        severity="non-fatal (degraded)",
        telemetry_tag="fallback.correction_exhausted",
        retry_eligible=False,
    ),
    FallbackId.F7_LLM_ERROR: FallbackContract(
        id=FallbackId.F7_LLM_ERROR,
        detection="HTTP 5xx or asyncio.TimeoutError from LLM call",
        behavior="Retry once after 5s backoff; if second failure, skip building and log",
        severity="non-fatal (degraded)",
        telemetry_tag="fallback.llm_error",
        retry_eligible=True,
    ),
    FallbackId.F8_DOCLING_FAILURE: FallbackContract(
        id=FallbackId.F8_DOCLING_FAILURE,
        detection="Exception during DocumentConverter.convert()",
        behavior="Continue with PyMuPDF full_text only (Docling tables unavailable)",
        severity="non-fatal (degraded)",
        telemetry_tag="fallback.docling_failure",
        retry_eligible=False,
    ),
}

CORRECTION_RETRY_CONTRACT = RetryContract(max_retries=3, backoff_seconds=5.0)
"""Retry contract for the validation/correction loop (AC-5: max 3 retries)."""

LLM_RETRY_CONTRACT = RetryContract(max_retries=1, backoff_seconds=5.0)
"""Retry contract for LLM provider errors (F7: retry once then skip)."""


# ---------------------------------------------------------------------------
# Telemetry emission
# ---------------------------------------------------------------------------


def emit_fallback_telemetry(
    fallback_id: FallbackId,
    building_name: str,
    reason: str,
) -> str:
    """Log a structured fallback activation event and return the telemetry tag.

    Args:
        fallback_id: Which fallback scenario was activated.
        building_name: Name or ID of the building being processed.
        reason: Human-readable reason for the fallback activation.

    Returns:
        The telemetry tag string (e.g. ``"fallback.no_inventory"``).
    """
    contract = FALLBACK_MATRIX[fallback_id]
    logger.info(
        f"[{contract.telemetry_tag}] building={building_name} "
        f"reason={reason} severity={contract.severity}"
    )
    return contract.telemetry_tag


# ---------------------------------------------------------------------------
# Retry budget check
# ---------------------------------------------------------------------------


def check_retry_budget(attempt: int, contract: RetryContract) -> bool:
    """Check whether a retry is allowed within the given contract.

    Args:
        attempt: Current attempt number (0-based).
        contract: The retry contract to check against.

    Returns:
        ``True`` if ``attempt < contract.max_retries``, ``False`` otherwise.
    """
    return attempt < contract.max_retries


# ---------------------------------------------------------------------------
# Strategy selection (re-export for centralized access)
# ---------------------------------------------------------------------------


def select_strategy(
    building: "BuildingMeta",
    page_tags: Optional["PageTaggingResult"] = None,
) -> "ExtractionStrategy":
    """Select extraction strategy for a building.

    Delegates to ``_select_strategy()`` in orchestrator.py for the actual
    logic. This function provides a centralized access point so callers
    don't need to import orchestrator internals.
    """
    from open_notebook.extractors.orchestrator import _select_strategy

    return _select_strategy(building, page_tags)
