"""Standard DET format detector.

Identifies standard DET format by ``## B00A - Admin Building`` style headers
and extracts buildings using the existing _BUILDING_HEADER regex.
"""

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.extractors.building_inventory import (
    _BUILDING_HEADER,
    BuildingComplexity,
    BuildingMeta,
    _classify_complexity,
    _extract_rooms_from_section,
    _find_page_at_position,
    _find_page_end,
    _get_building_section,
)
from open_notebook.extractors.document_structure import DocumentStructure


class StandardFormatDetector:
    """Detect and extract from standard DET format (B###/D## building headers)."""

    name: str = "standard"
    priority: int = 10

    def detect(self, content: str) -> bool:
        """Detect standard format by looking for B###/D## building headers."""
        return bool(_BUILDING_HEADER.search(content))

    def extract_buildings(
        self,
        content: str,
        doc_structure: Optional[DocumentStructure] = None,
    ) -> List[BuildingMeta]:
        """Extract buildings from standard format using B###/D## headers."""
        building_matches: List[Tuple[int, re.Match]] = []
        seen_ids: set = set()
        for match in _BUILDING_HEADER.finditer(content):
            bid = match.group(1)
            if bid not in seen_ids:
                building_matches.append((match.start(), match))
                seen_ids.add(bid)

        if not building_matches:
            return []

        buildings: List[BuildingMeta] = []
        for i, (pos, match) in enumerate(building_matches):
            building_id = match.group(1)
            name = match.group(2).strip() if match.group(2) else None
            year_str = match.group(3)
            year = int(year_str) if year_str else None
            construction = match.group(4).strip() if match.group(4) else None

            page_start = _find_page_at_position(content, pos)
            next_pos = (
                building_matches[i + 1][0] if i + 1 < len(building_matches) else None
            )
            section_text = _get_building_section(content, pos, next_pos)
            rooms = _extract_rooms_from_section(section_text, pos, content)
            page_end = _find_page_end(section_text, page_start, rooms)
            complexity, acm_estimate = _classify_complexity(section_text, len(rooms))

            buildings.append(
                BuildingMeta(
                    building_id=building_id,
                    name=name,
                    year=year,
                    construction=construction,
                    page_start=page_start,
                    page_end=page_end,
                    complexity=complexity,
                    rooms=rooms,
                    acm_item_count_estimate=acm_estimate if acm_estimate > 0 else None,
                )
            )

        return buildings

    def get_column_mapping(self) -> Optional[Dict[str, str]]:
        """Standard format uses standard column names — no special mapping needed."""
        return None
