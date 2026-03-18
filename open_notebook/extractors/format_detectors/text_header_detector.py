"""Text-header format detector.

Identifies text-header format by ``Building Name:\n<name>``
text headers and extracts buildings accordingly.
"""

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingMeta,
    _detect_ara_buildings,
    _find_ara_building_section_end,
    _find_page_at_position,
    _find_page_end,
)
from open_notebook.extractors.document_structure import DocumentStructure


class TextHeaderDetector:
    """Detect and extract from text-header format Asbestos Register."""

    name: str = "text_header"
    priority: int = 20

    def detect(self, content: str) -> bool:
        """Detect text-header format by 'Building Name:' text headers (not pipe-delimited)."""
        # Text-header format uses plain text "Building Name:" — exclude pipe-delimited (that's pipe_table)
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
        """Extract buildings from text-header format."""
        text_header_buildings = _detect_ara_buildings(content)
        if not text_header_buildings:
            return []

        logger.info(
            f"Text-header format detected: {len(text_header_buildings)} buildings found via "
            "'Building Name:' headers"
        )

        buildings: List[BuildingMeta] = []
        for i, (name, pos) in enumerate(text_header_buildings):
            next_pos = text_header_buildings[i + 1][1] if i + 1 < len(text_header_buildings) else None
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
        """Text-header format column mapping — uses slightly different column names."""
        return {
            "Building Element": "product (the ACM material/building element)",
            "Material Type": "acm_sub_classification (material type description)",
            "ACM Status": "sample_result (detection result)",
            "Risk Rating": "disturbance_potential (risk level)",
        }
