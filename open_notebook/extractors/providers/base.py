"""
Provider Adapter Framework — base types.

Defines the ExtractionProvider Protocol, normalized data containers,
and the ProviderError exception that all adapters must raise.

Story: E31-S2 Provider Adapter Framework
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass
class TableBBox:
    """Bounding box coordinates for a table within a PDF page."""

    x: float
    y: float
    width: float
    height: float
    page: int


@dataclass
class NormalizedTable:
    """Provider-agnostic representation of a single extracted table."""

    table_index: int
    page: int  # 1-based; -1 if unknown
    row_count: int
    col_count: int
    columns: List[str]
    html: str
    markdown: str
    csv: Optional[str] = None
    bbox: Optional[TableBBox] = None


@dataclass
class NormalizedExtractionResult:
    """Container returned by every ExtractionProvider.extract() call."""

    provider_id: str
    tables: List[NormalizedTable] = field(default_factory=list)
    extraction_time_ms: int = 0
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------


class ProviderError(Exception):
    """Raised by an adapter when extraction fails.

    Callers should catch ProviderError and handle non-fatally — the adapter
    guarantees that no other exception type escapes extract().
    """

    def __init__(
        self,
        provider_id: str,
        message: str,
        original: Optional[Exception] = None,
    ) -> None:
        super().__init__(f"[{provider_id}] {message}")
        self.provider_id = provider_id
        self.message = message
        self.original = original


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ExtractionProvider(Protocol):
    """Protocol for PDF extraction providers.

    Adapters implement this protocol to participate in the ProviderRegistry.
    All implementations must be importable even when the underlying library
    is not installed; ProviderError is raised at extract() time only.
    """

    @property
    def provider_id(self) -> str:
        """Stable string identifier for this provider (e.g. 'docling')."""
        ...

    def extract(
        self,
        pdf_path: str,
        *,
        pipeline_logger=None,  # Optional[PipelineLogger] — avoid import cycle
    ) -> NormalizedExtractionResult:
        """Extract tables from a PDF file.

        Args:
            pdf_path: Absolute path to the PDF file.
            pipeline_logger: Optional PipelineLogger for observability hooks.

        Returns:
            NormalizedExtractionResult — always returned even on partial failure.

        Raises:
            ProviderError: If extraction cannot proceed at all.
        """
        ...

    def supports_table_extraction(self) -> bool:
        """Return True if this provider can extract structured tables."""
        ...

    def get_field_confidence(self) -> Dict[str, float]:
        """Return per-field confidence map; empty dict if unsupported."""
        ...
