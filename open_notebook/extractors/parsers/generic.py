"""
Generic Config-Driven ACM Parser.

A single universal parser driven by FieldSchemaConfig that replaces the
previous three-parser framework (PrensaParser, GreencapParser, GenericParser).

detect() always returns True — there is only one parser now.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

from typing import Dict, List, Optional

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
)
from open_notebook.extractors.parsers.field_config import FieldSchemaConfig

# Backward-compatible short header names used in existing markdown tables.
# These map to internal field names so old-format tables still parse.
_COMPAT_COLUMN_MAP: Dict[str, str] = {
    "product": "product",
    "material description": "material_description",
    "extent": "extent",
    "location": "location",
    "friable": "friable",
    "material condition": "material_condition",
    "condition": "material_condition",
    "risk status": "risk_status",
    "risk": "risk_status",
    "result": "result",
}

# Minimum headers needed to identify an ACM table (short names)
_REQUIRED_HEADERS = {"product", "material description", "result"}

# BAR display name equivalents for ACM table detection
_BAR_REQUIRED_HEADERS = {"specific item/acm name", "sample result"}


class GenericParser(ConsultantParser):
    """Config-driven parser for all ACM register table formats.

    Loads field configuration from FieldSchemaConfig to determine which
    columns to extract and how to map them. Falls back to backward-compatible
    short header names for existing markdown table formats.
    """

    def __init__(self, config: Optional[FieldSchemaConfig] = None):
        self.config = config
        if self.config is None:
            from open_notebook.extractors.parsers.config_loader import load_field_schema

            self.config = load_field_schema()

    @property
    def name(self) -> str:
        return "generic"

    def detect(self, text: str) -> bool:
        return True

    def extract_metadata(self, pages: Dict[int, str]) -> DocumentMeta:
        """Extract metadata from pages. Returns basic metadata for now.

        Full extraction is handled by metadata_extractor.py (E1-S19)
        in the LangGraph pipeline. This method remains for parser interface
        compatibility.
        """
        return DocumentMeta(consultant_name="Generic")

    def extract_items(self, tables: List[dict]) -> List[RawACMItem]:
        items: List[RawACMItem] = []
        column_mapping = self.get_column_mapping()

        for table in tables:
            headers = [h.lower().strip() for h in table.get("headers", [])]
            rows = table.get("rows", [])

            # Check if this looks like an ACM table using either short or BAR names
            joined = " ".join(headers)
            has_short = any(h in joined for h in _REQUIRED_HEADERS)
            has_bar = any(h in joined for h in _BAR_REQUIRED_HEADERS)
            if not has_short and not has_bar:
                continue

            # Build header index mapping internal_name → column index
            # using the full column mapping (compat + config-driven)
            field_index: Dict[str, int] = {}
            for i, h in enumerate(headers):
                if h in column_mapping:
                    internal = column_mapping[h]
                    if internal not in field_index:
                        field_index[internal] = i

            for row in rows:
                item = self._parse_row(row, field_index)
                if item:
                    items.append(item)

        return items

    def get_column_mapping(self) -> Dict[str, str]:
        """Return display_name (lowercase) → internal_name mapping.

        Includes both config-driven BAR field names and backward-compatible
        short names for existing markdown table formats.
        """
        mapping = dict(_COMPAT_COLUMN_MAP)
        for field in self.config.get_active_fields():
            mapping[field.display_name.lower()] = field.internal_name
        return mapping

    def get_register_headers(self) -> List[str]:
        """Return lowercase display names of all active fields."""
        return [f.display_name.lower() for f in self.config.get_active_fields()]

    def _parse_row(
        self, row: List[str], field_index: Dict[str, int]
    ) -> Optional[RawACMItem]:
        """Parse a single table row into a RawACMItem.

        Args:
            row: Cell values from a table row.
            field_index: Mapping of internal_name → column index.
        """

        def get_field(internal_name: str) -> Optional[str]:
            idx = field_index.get(internal_name)
            if idx is not None and idx < len(row):
                val = row[idx].strip()
                return val if val else None
            return None

        product = get_field("product")
        material_desc = get_field("material_description")

        if not product or not material_desc:
            return None

        result = get_field("result") or get_field("sample_result") or ""
        if "no asbestos" in result.lower():
            result = "Not Detected"
        elif "detected" in result.lower():
            result = "Detected"

        return RawACMItem(
            product=product,
            material_description=material_desc,
            result=result,
            extent=get_field("extent"),
            location=get_field("location"),
            friable=get_field("friable"),
            material_condition=get_field("material_condition"),
            risk_status=get_field("risk_status"),
        )
