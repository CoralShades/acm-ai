"""Format Detector Registry.

Provides a protocol-based format detection system that identifies
consultant-specific ACM document formats and supplies format-aware
configuration (column mappings, building extraction logic).

Each detector implements the FormatDetector protocol and registers
itself with the global FormatRegistry on import.
"""

from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable

from loguru import logger

from open_notebook.extractors.building_inventory import BuildingMeta
from open_notebook.extractors.document_structure import DocumentStructure


@runtime_checkable
class FormatDetector(Protocol):
    """Protocol for consultant-format detectors."""

    name: str
    priority: int  # lower = higher priority

    def detect(self, content: str) -> bool:
        """Return True if this format is detected in the content."""
        ...

    def extract_buildings(
        self,
        content: str,
        doc_structure: Optional[DocumentStructure] = None,
    ) -> List[BuildingMeta]:
        """Extract buildings using format-specific logic. Returns empty list if not applicable."""
        ...

    def get_column_mapping(self) -> Optional[Dict[str, str]]:
        """Return a mapping of format-specific column names to canonical field names.

        Keys are the column headers found in this format's tables.
        Values are the canonical SF field names the LLM should map them to.
        Returns None if this format uses standard column names.
        """
        ...


class FormatRegistry:
    """Registry of format detectors, sorted by priority."""

    def __init__(self) -> None:
        self._detectors: List[FormatDetector] = []

    def register(self, detector: FormatDetector) -> None:
        """Register a detector and re-sort by priority."""
        self._detectors.append(detector)
        self._detectors.sort(key=lambda d: d.priority)
        logger.debug(
            f"Registered format detector: {detector.name} (priority={detector.priority})"
        )

    def detect_format(self, content: str) -> Optional[FormatDetector]:
        """Run detectors in priority order, return first match or None."""
        for detector in self._detectors:
            try:
                if detector.detect(content):
                    logger.info(f"Format detected: {detector.name}")
                    return detector
            except Exception as e:
                logger.warning(f"Format detector {detector.name} failed: {e}")
        return None

    def extract_buildings(
        self,
        content: str,
        doc_structure: Optional[DocumentStructure] = None,
    ) -> Optional[Tuple[str, List[BuildingMeta]]]:
        """Detect format and extract buildings. Returns (format_name, buildings) or None."""
        detector = self.detect_format(content)
        if detector is None:
            return None
        buildings = detector.extract_buildings(content, doc_structure)
        if buildings:
            return (detector.name, buildings)
        return None

    def get_detector(self, name: str) -> Optional[FormatDetector]:
        """Look up a detector by name."""
        for d in self._detectors:
            if d.name == name:
                return d
        return None

    @property
    def detectors(self) -> List[FormatDetector]:
        """Return all registered detectors (sorted by priority)."""
        return list(self._detectors)


# Global singleton registry
_registry = FormatRegistry()


def get_registry() -> FormatRegistry:
    """Get the global format registry."""
    return _registry


# Auto-register detectors on import
def _auto_register() -> None:
    """Import all detector modules to trigger registration."""
    from open_notebook.extractors.format_detectors.ara_detector import ARADetector
    from open_notebook.extractors.format_detectors.clutch_detector import ClutchDetector
    from open_notebook.extractors.format_detectors.samp_detector import SAMPDetector

    _registry.register(ClutchDetector())
    _registry.register(SAMPDetector())
    _registry.register(ARADetector())


_auto_register()
