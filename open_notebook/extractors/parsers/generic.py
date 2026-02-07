"""
Generic / NSW SAMP Consultant Parser (Fallback)

Handles standard ACM register tables with columns like:
Product, Material Description, Result, Extent, Location, Friable, Condition, Risk Status.

This parser wraps the existing regex-based extraction logic from acm_extractor.py,
preserving full backward compatibility with NSW SAMP format documents.

detect() always returns True - this is the fallback parser when no specific
consultant format is detected.
"""

from typing import Dict, List, Optional

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
)

# Required headers for generic ACM table detection
GENERIC_REQUIRED_HEADERS = ["product", "material description", "result"]

# Optional headers
GENERIC_OPTIONAL_HEADERS = [
    "extent",
    "location",
    "friable",
    "material condition",
    "risk status",
    "risk",
]

# All expected headers in typical order
GENERIC_HEADERS = [
    "product",
    "material description",
    "extent",
    "location",
    "friable",
    "material condition",
    "risk status",
    "result",
]

# Mapping: column header text -> standard field name
# This replicates the logic in _create_header_map() from acm_extractor.py
GENERIC_COLUMN_MAPPING: Dict[str, str] = {
    "product": "product",
    "material description": "material_description",
    "extent": "extent",
    "location": "location",
    "friable": "friable",
    "material condition": "material_condition",
    "risk status": "risk_status",
    "risk": "risk_status",
    "condition": "material_condition",
    "result": "result",
}


class GenericParser(ConsultantParser):
    """Fallback parser for standard ACM register tables (NSW SAMP format).

    Always matches - used when no specific consultant parser detects the format.
    Preserves backward compatibility with the existing regex-based extraction.
    """

    @property
    def name(self) -> str:
        return "generic"

    def detect(self, text: str) -> bool:
        # Always returns True - this is the fallback parser
        return True

    def extract_metadata(self, pages: Dict[int, str]) -> DocumentMeta:
        return DocumentMeta(consultant_name="Generic")

    def extract_items(self, tables: List[dict]) -> List[RawACMItem]:
        items: List[RawACMItem] = []

        for table in tables:
            headers = [h.lower().strip() for h in table.get("headers", [])]
            rows = table.get("rows", [])

            # Check if this looks like an ACM table
            if not any(h in " ".join(headers) for h in GENERIC_REQUIRED_HEADERS):
                continue

            header_index: Dict[str, int] = {}
            for i, h in enumerate(headers):
                header_index[h] = i

            for row in rows:
                item = self._parse_row(row, header_index)
                if item:
                    items.append(item)

        return items

    def get_column_mapping(self) -> Dict[str, str]:
        return dict(GENERIC_COLUMN_MAPPING)

    def get_register_headers(self) -> List[str]:
        return list(GENERIC_HEADERS)

    def _parse_row(
        self, row: List[str], header_index: Dict[str, int]
    ) -> Optional[RawACMItem]:
        """Parse a single generic table row into a RawACMItem."""

        def get_cell(header_name: str) -> Optional[str]:
            idx = header_index.get(header_name)
            if idx is not None and idx < len(row):
                val = row[idx].strip()
                return val if val else None
            return None

        product = get_cell("product")
        material_desc = get_cell("material description")

        if not product or not material_desc:
            return None

        result = get_cell("result") or ""
        if "no asbestos" in result.lower():
            result = "Not Detected"
        elif "detected" in result.lower():
            result = "Detected"

        return RawACMItem(
            product=product,
            material_description=material_desc,
            result=result,
            extent=get_cell("extent"),
            location=get_cell("location"),
            friable=get_cell("friable"),
            material_condition=get_cell("material condition") or get_cell("condition"),
            risk_status=get_cell("risk status") or get_cell("risk"),
        )
