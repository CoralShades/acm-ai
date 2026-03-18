"""Clutch/Greencap format detector.

Identifies Clutch Asbestos Register format by pipe-delimited table
headers (| Site Details |, | Building Name: |) and extracts buildings
with enriched metadata (levels, survey date).
"""

import re
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.extractors.building_inventory import (
    _CLUTCH_BUILDING_NAME_PATTERN,
    _CLUTCH_LEVEL_SUFFIX,
    BuildingMeta,
    _apply_boundary_overlap,
    _find_page_at_position,
)
from open_notebook.extractors.document_structure import DocumentStructure

# Clutch-specific metadata patterns (parsed from building header rows)
_CLUTCH_LEVELS_PATTERN = re.compile(
    r"\|\s*Number\s+of\s+Levels:\s*\|\s*(\d+)", re.IGNORECASE
)
_CLUTCH_SURVEY_DATE_PATTERN = re.compile(
    r"\|\s*Survey\s+Date:\s*\|\s*([^|]+)", re.IGNORECASE
)


class ClutchDetector:
    """Detect and extract from Clutch/Greencap Asbestos Register format."""

    name: str = "clutch"
    priority: int = 5  # Highest priority — most specific format

    def detect(self, content: str) -> bool:
        """Detect Clutch/Greencap format via pipe-table heuristics.

        Primary path (original Clutch):
        - ``| Site Details |`` in first 15000 chars
        - At least one of ``| Full Address: |`` or ``| Client Name: |``
        - ``| Building Name: |`` somewhere in first 20000 chars

        Secondary path (Greencap variant):
        - ``| Building Name: |`` followed by ``| Number of Levels: |`` on same row
        - This pattern is unique to Clutch/Greencap pipe-table format
        """
        head = content[:15000]
        has_site_details = bool(
            re.search(r"\|\s*Site\s+Details\s*\|", head, re.IGNORECASE)
        )
        has_full_address = bool(
            re.search(r"\|\s*Full\s+Address:\s*\|", head, re.IGNORECASE)
        )
        has_client_name = bool(
            re.search(r"\|\s*Client\s+Name:\s*\|", head, re.IGNORECASE)
        )
        has_building_name = bool(
            re.search(r"\|\s*Building\s+Name:\s*\|", content[:20000], re.IGNORECASE)
        )

        # Primary: classic Clutch with Site Details header
        if (
            has_site_details
            and (has_full_address or has_client_name)
            and has_building_name
        ):
            return True

        # Secondary: Greencap variant — Building Name + Number of Levels on same pipe row
        # This pattern is unique to Clutch/Greencap and distinguishes from ARA format
        has_clutch_building_row = bool(
            re.search(
                r"\|\s*Building\s+Name:\s*\|[^|]+\|\s*Number\s+of\s+Levels:\s*\|",
                content,
                re.IGNORECASE,
            )
        )
        if has_clutch_building_row:
            return True

        return False

    def extract_buildings(
        self,
        content: str,
        doc_structure: Optional[DocumentStructure] = None,
    ) -> List[BuildingMeta]:
        """Extract buildings from Clutch format with enriched metadata.

        Parses ``| Building Name: |`` headers, deduplicates by building name,
        and enriches with ``Number of Levels`` and ``Survey Date`` from the
        same header rows.
        """
        # Collect all occurrences of "Building Name:" table cells
        building_occurrences: dict[str, List[int]] = {}
        for match in _CLUTCH_BUILDING_NAME_PATTERN.finditer(content):
            raw_name = match.group(1).strip()
            name = _CLUTCH_LEVEL_SUFFIX.sub("", raw_name).strip()
            if not name:
                continue
            if name not in building_occurrences:
                building_occurrences[name] = []
            building_occurrences[name].append(match.start())

        if not building_occurrences:
            return []

        logger.info(
            f"Clutch format: found {len(building_occurrences)} unique buildings "
            f"from 'Building Name:' headers"
        )

        buildings: List[BuildingMeta] = []
        for idx, (name, positions) in enumerate(building_occurrences.items(), start=1):
            page_start = _find_page_at_position(content, positions[0])
            page_end = _find_page_at_position(content, positions[-1])

            # Parse enrichment data from the building's first occurrence context
            levels, survey_date = self._parse_building_enrichment(content, positions[0])

            buildings.append(
                BuildingMeta(
                    building_id=f"B{idx:03d}",
                    name=name,
                    levels=levels,
                    survey_date=survey_date,
                    page_start=page_start,
                    page_end=max(page_start, page_end),
                )
            )

        # Single-building fix: expand page_end to total_pages
        if len(buildings) == 1 and doc_structure:
            total = doc_structure.total_pages
            if total and buildings[0].page_end < total:
                buildings[0].page_end = total

        return buildings

    def get_column_mapping(self) -> Optional[Dict[str, str]]:
        """Clutch column names mapped to canonical extraction fields.

        Clutch registers use different column headers than SAMP format.
        This mapping tells the LLM what each column represents.
        """
        return {
            "Location - Item Description": "product (the ACM material/product name)",
            "Hazard Type": "acm_sub_classification (material type, e.g., 'Asbestos Cement')",
            "Sample No.": "nata_sample_no (the sample/reference number)",
            "Result": "sample_result (detection result: Detected, Not Detected, etc.)",
            "Condition": "condition (material condition: Stable, Fair, Poor)",
            "Risk Rating": "disturbance_potential (risk level: Low, Medium, High)",
            "Building Name": "building_name (the building this item belongs to)",
            "Room/Area": "room_or_area (room or area identifier)",
        }

    def _parse_building_enrichment(
        self, content: str, position: int
    ) -> tuple[Optional[int], Optional[str]]:
        """Parse Number of Levels and Survey Date from a building header row.

        Searches the line/context around the Building Name occurrence
        for enrichment metadata.
        """
        # Get a window of text around the building name occurrence
        window_start = max(0, position - 50)
        window_end = min(len(content), position + 500)
        window = content[window_start:window_end]

        levels: Optional[int] = None
        survey_date: Optional[str] = None

        levels_match = _CLUTCH_LEVELS_PATTERN.search(window)
        if levels_match:
            try:
                levels = int(levels_match.group(1))
            except ValueError:
                pass

        date_match = _CLUTCH_SURVEY_DATE_PATTERN.search(window)
        if date_match:
            survey_date = date_match.group(1).strip()
            # Clean up trailing whitespace/pipe artifacts
            survey_date = survey_date.rstrip(" |")
            if not survey_date:
                survey_date = None

        return levels, survey_date
