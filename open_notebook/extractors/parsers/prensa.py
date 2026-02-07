"""
Prensa Pty Ltd Consultant Parser

Handles "Division 5 Asbestos Assessment" PDF format with 15-column register tables.

Detection markers: "Prensa Pty Ltd", "Division 5 Asbestos Assessment"
Building pattern: floor-based (e.g., "Ground floor", "First floor", "Exterior")
"""

import re
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
)

# Detection markers (case-insensitive)
PRENSA_DETECTION_MARKERS = ["prensa pty ltd", "division 5 asbestos assessment"]

# 15 expected column headers (lowercase, as they appear in the register)
PRENSA_HEADERS = [
    "area / level",
    "room & location",
    "feature",
    "item description",
    "hazard type",
    "hazard status",
    "sample number",
    "friability",
    "labelled y/n",
    "disturb. potential",
    "condition",
    "risk status",
    "approx. quantity",
    "control priority",
    "comments & recommendations",
]

# Mapping: consultant column name -> standard raw field name
PRENSA_COLUMN_MAPPING: Dict[str, str] = {
    "area / level": "level",
    "room & location": "room_name",
    "feature": "location",
    "item description": "product",
    "hazard type": "hazard_type",
    "hazard status": "sample_result",
    "sample number": "sample_number",
    "friability": "friable",
    "labelled y/n": "labelled",
    "disturb. potential": "disturbance_potential",
    "condition": "material_condition",
    "risk status": "risk_status",
    "approx. quantity": "extent",
    "control priority": "control_priority",
    "comments & recommendations": "comments",
}

# Building detection: floor-based patterns
PRENSA_BUILDING_PATTERN = re.compile(
    r"^([A-Za-z]+\s*floor|Exterior|Ground floor|First floor)",
    re.IGNORECASE,
)


class PrensaParser(ConsultantParser):
    """Parser for Prensa Pty Ltd Division 5 Asbestos Assessment reports."""

    @property
    def name(self) -> str:
        return "prensa"

    def detect(self, text: str) -> bool:
        text_lower = text.lower()
        return any(marker in text_lower for marker in PRENSA_DETECTION_MARKERS)

    def extract_metadata(self, pages: Dict[int, str]) -> DocumentMeta:
        all_text = "\n".join(pages.get(p, "") for p in sorted(pages.keys()))
        meta = DocumentMeta(consultant_name="Prensa Pty Ltd")

        # Try to extract site name from early pages
        for page_num in sorted(pages.keys())[:3]:
            page_text = pages.get(page_num, "")
            lines = page_text.strip().split("\n")
            for line in lines:
                stripped = line.strip()
                # Look for school/site name (typically a line near the top
                # that isn't the consultant name or report type)
                if stripped and "prensa" not in stripped.lower() and "division 5" not in stripped.lower():
                    if not meta.site_name and len(stripped) > 5:
                        meta.site_name = stripped
                        break

        # Extract report date
        date_match = re.search(r"Report Date[:\s]*(.+)", all_text, re.IGNORECASE)
        if date_match:
            meta.report_date = date_match.group(1).strip()

        # Extract report reference
        ref_match = re.search(r"(?:Reference|Report No)[:\s]*(.+)", all_text, re.IGNORECASE)
        if ref_match:
            meta.report_reference = ref_match.group(1).strip()

        return meta

    def extract_items(self, tables: List[dict]) -> List[RawACMItem]:
        items: List[RawACMItem] = []

        for table in tables:
            headers = [h.lower().strip() for h in table.get("headers", [])]
            rows = table.get("rows", [])

            # Build index mapping: header text -> column index
            header_index: Dict[str, int] = {}
            for i, h in enumerate(headers):
                header_index[h] = i

            for row in rows:
                item = self._parse_row(row, header_index)
                if item:
                    items.append(item)

        return items

    def get_column_mapping(self) -> Dict[str, str]:
        return dict(PRENSA_COLUMN_MAPPING)

    def get_register_headers(self) -> List[str]:
        return list(PRENSA_HEADERS)

    def _parse_row(
        self, row: List[str], header_index: Dict[str, int]
    ) -> Optional[RawACMItem]:
        """Parse a single table row into a RawACMItem."""

        def get_cell(header_name: str) -> Optional[str]:
            idx = header_index.get(header_name)
            if idx is not None and idx < len(row):
                val = row[idx].strip()
                return val if val else None
            return None

        product = get_cell("item description")
        if not product:
            return None

        # For Prensa, material_description is derived from feature + item description
        feature = get_cell("feature") or ""
        material_description = f"{feature} {product}".strip() if feature else product

        hazard_status = get_cell("hazard status") or ""
        # Normalize result
        result = hazard_status
        if "no asbestos" in hazard_status.lower():
            result = "Not Detected"
        elif "detected" in hazard_status.lower():
            result = "Detected"

        return RawACMItem(
            product=product,
            material_description=material_description,
            result=result,
            extent=get_cell("approx. quantity"),
            location=get_cell("feature"),
            friable=get_cell("friability"),
            material_condition=get_cell("condition"),
            risk_status=get_cell("risk status"),
            sample_number=get_cell("sample number"),
            disturbance_potential=get_cell("disturb. potential"),
            labelled=get_cell("labelled y/n"),
            control_priority=get_cell("control priority"),
            comments=get_cell("comments & recommendations"),
        )
