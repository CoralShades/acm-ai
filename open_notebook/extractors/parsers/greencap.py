"""
Greencap Consultant Parser

Handles "Asbestos Risk Assessment" PDF format with 14-column register tables.

Detection marker: "Greencap" in text
Building pattern: "Building Name: <name>"
Site metadata: "Full Address:", "Est. Building Size:", "Est. Building Age:"
"""

import re
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
)

# Detection marker (case-insensitive)
GREENCAP_DETECTION_MARKER = "greencap"

# 14 expected column headers (lowercase)
GREENCAP_HEADERS = [
    "item no.",
    "location - item description",
    "hazard type",
    "sample no.",
    "item status",
    "photo no.",
    "est. extent",
    "condition",
    "friability",
    "dist. potential",
    "risk rating",
    "current label",
    "reinspect date",
    "control priority",
]

# Mapping: consultant column name -> standard raw field name
GREENCAP_COLUMN_MAPPING: Dict[str, str] = {
    "item no.": "item_number",
    "location - item description": "product",
    "hazard type": "hazard_type",
    "sample no.": "sample_number",
    "item status": "sample_result",
    "photo no.": "photo_number",
    "est. extent": "extent",
    "condition": "material_condition",
    "friability": "friable",
    "dist. potential": "disturbance_potential",
    "risk rating": "risk_status",
    "current label": "labelled",
    "reinspect date": "reinspect_date",
    "control priority": "control_priority",
}

# Metadata extraction patterns
GREENCAP_SITE_METADATA_PATTERNS = {
    "site_address": re.compile(r"Full Address[:\s]+(.+)", re.IGNORECASE),
    "building_size": re.compile(r"Est\.\s*Building Size[:\s]+(.+)", re.IGNORECASE),
    "building_age": re.compile(r"Est\.\s*Building Age[:\s]+(.+)", re.IGNORECASE),
}

# Building name detection
GREENCAP_BUILDING_PATTERN = re.compile(r"Building Name[:\s]+(.+)", re.IGNORECASE)


class GreencapParser(ConsultantParser):
    """Parser for Greencap Asbestos Risk Assessment reports."""

    @property
    def name(self) -> str:
        return "greencap"

    def detect(self, text: str) -> bool:
        return GREENCAP_DETECTION_MARKER in text.lower()

    def extract_metadata(self, pages: Dict[int, str]) -> DocumentMeta:
        all_text = "\n".join(pages.get(p, "") for p in sorted(pages.keys()))
        meta = DocumentMeta(consultant_name="Greencap")

        # Extract site metadata from patterns
        for field_name, pattern in GREENCAP_SITE_METADATA_PATTERNS.items():
            match = pattern.search(all_text)
            if match:
                setattr(meta, field_name, match.group(1).strip())

        # Extract site name from building name or report header
        building_match = GREENCAP_BUILDING_PATTERN.search(all_text)
        if building_match:
            meta.site_name = building_match.group(1).strip()

        # Extract report date
        date_match = re.search(r"(?:Date|Report Date)[:\s]+(.+)", all_text, re.IGNORECASE)
        if date_match:
            meta.report_date = date_match.group(1).strip()

        return meta

    def extract_items(self, tables: List[dict]) -> List[RawACMItem]:
        items: List[RawACMItem] = []

        for table in tables:
            headers = [h.lower().strip() for h in table.get("headers", [])]
            rows = table.get("rows", [])

            header_index: Dict[str, int] = {}
            for i, h in enumerate(headers):
                header_index[h] = i

            for row in rows:
                item = self._parse_row(row, header_index)
                if item:
                    items.append(item)

        return items

    def get_column_mapping(self) -> Dict[str, str]:
        return dict(GREENCAP_COLUMN_MAPPING)

    def get_register_headers(self) -> List[str]:
        return list(GREENCAP_HEADERS)

    def _parse_row(
        self, row: List[str], header_index: Dict[str, int]
    ) -> Optional[RawACMItem]:
        """Parse a single Greencap table row into a RawACMItem."""

        def get_cell(header_name: str) -> Optional[str]:
            idx = header_index.get(header_name)
            if idx is not None and idx < len(row):
                val = row[idx].strip()
                return val if val else None
            return None

        # In Greencap format, "location - item description" contains both
        location_desc = get_cell("location - item description")
        if not location_desc:
            return None

        # Split "location - item description" into location and product
        # Format is typically "Room/Location - Material description"
        parts = location_desc.split(" - ", 1)
        if len(parts) == 2:
            location = parts[0].strip()
            product = parts[1].strip()
        else:
            location = None
            product = location_desc

        material_description = product  # In Greencap, product IS the description

        item_status = get_cell("item status") or ""
        result = item_status
        if "no asbestos" in item_status.lower():
            result = "Not Detected"
        elif "detected" in item_status.lower():
            result = "Detected"

        return RawACMItem(
            product=product,
            material_description=material_description,
            result=result,
            extent=get_cell("est. extent"),
            location=location,
            friable=get_cell("friability"),
            material_condition=get_cell("condition"),
            risk_status=get_cell("risk rating"),
            sample_number=get_cell("sample no."),
            disturbance_potential=get_cell("dist. potential"),
            labelled=get_cell("current label"),
            control_priority=get_cell("control priority"),
        )
