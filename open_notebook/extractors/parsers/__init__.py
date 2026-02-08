"""
ACM Parser Module.

Provides a single config-driven GenericParser that handles all consultant
PDF formats via field schema configuration.

Story: E1-S11 Generic Configurable Parser with BAR Field Schema
"""

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
    SourceLocation,
)
from open_notebook.extractors.parsers.config_loader import load_field_schema
from open_notebook.extractors.parsers.generic import GenericParser


def get_parser(pdf_text: str = "") -> GenericParser:
    """Return the GenericParser with loaded field config.

    The pdf_text parameter is accepted for backward compatibility but
    is no longer used for parser selection — there is only one parser now.
    """
    config = load_field_schema()
    return GenericParser(config=config)


__all__ = [
    "ConsultantParser",
    "DocumentMeta",
    "GenericParser",
    "RawACMItem",
    "SourceLocation",
    "get_parser",
    "load_field_schema",
]
