"""ARA (Asbestos Risk Assessment) format detector.

Identifies ARA/Greencap/Prensa format by ``Building Name:\n<name>``
text headers and extracts buildings accordingly.
"""

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingMeta,
    _find_ara_building_section_end,
    _find_page_at_position,
    _find_page_end,
)
from open_notebook.extractors.document_structure import DocumentStructure


class ARADetector:
    """Detect and extract from ARA/Greencap format."""

    name: str = "ara"
    priority: int = 20

    def detect(self, content: str) -> bool:
        """Detect ARA format by 'Building Name:' text headers (not pipe-delimited)."""
        # ARA uses plain text "Building Name:" — exclude pipe-delimited (that's Clutch)
        pattern = re.compile(
            r"(?<!\|)\s*Building Name:\s*\n\s*(.+?)(?:\n|$)"
            r"|"
            r"(?<!\|)\s*Building Name:\s+(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        matches = list(pattern.finditer(content[:20000]))
        return len(matches) >= 1

    def extract_buildings(
        self,
        content: str,
        doc_structure: Optional[DocumentStructure] = None,
    ) -> List[BuildingMeta]:
        """Extract buildings from ARA format."""
        ara_buildings = self._detect_ara_buildings(content)
        if not ara_buildings:
            return []

        logger.info(
            f"ARA format detected: {len(ara_buildings)} buildings found via "
            "'Building Name:' headers"
        )

        buildings: List[BuildingMeta] = []
        for i, (name, pos) in enumerate(ara_buildings):
            next_pos = ara_buildings[i + 1][1] if i + 1 < len(ara_buildings) else None
            section_end = _find_ara_building_section_end(content, name, pos, next_pos)
            section_text = content[pos:section_end]

            page_start = _find_page_at_position(content, pos)
            page_end = _find_page_end(section_text, page_start, [])

            complexity = BuildingComplexity.COMPLEX
            acm_count = section_text.lower().count("\nasbestos\n")

            buildings.append(
                BuildingMeta(
                    building_id=name,
                    name=name,
                    page_start=page_start,
                    page_end=page_end,
                    complexity=complexity,
                    acm_item_count_estimate=acm_count if acm_count > 0 else None,
                )
            )

        return buildings

    def get_column_mapping(self) -> Optional[Dict[str, str]]:
        """ARA column mapping — Greencap uses slightly different column names."""
        return {
            "Building Element": "product (the ACM material/building element)",
            "Material Type": "acm_sub_classification (material type description)",
            "ACM Status": "sample_result (detection result)",
            "Risk Rating": "disturbance_potential (risk level)",
        }

    def _detect_ara_buildings(self, content: str) -> List[Tuple[str, int]]:
        """Detect ARA-format buildings from 'Building Name:' header blocks."""
        ara_building_pattern = re.compile(
            r"Building Name:\s*\n\s*(.+?)(?:\n|$)"
            r"|"
            r"Building Name:\s+(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        seen_names: set = set()
        results: List[Tuple[str, int]] = []

        for match in ara_building_pattern.finditer(content):
            name = (match.group(1) or match.group(2) or "").strip()
            if name and name not in seen_names:
                seen_names.add(name)
                results.append((name, match.start()))

        return results
