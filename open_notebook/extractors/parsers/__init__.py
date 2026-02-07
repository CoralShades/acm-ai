"""
Consultant Parser Registry

Provides automatic parser selection for different consultant PDF formats.
Parsers are tried in priority order; GenericParser is always the fallback.
"""

from typing import List

from loguru import logger

from open_notebook.extractors.parsers.base import (
    ConsultantParser,
    DocumentMeta,
    RawACMItem,
    SourceLocation,
)
from open_notebook.extractors.parsers.generic import GenericParser
from open_notebook.extractors.parsers.greencap import GreencapParser
from open_notebook.extractors.parsers.prensa import PrensaParser

# Parser registry in priority order. GenericParser MUST be last (fallback).
PARSER_REGISTRY: List[ConsultantParser] = [
    PrensaParser(),
    GreencapParser(),
    GenericParser(),
]


def get_parser(pdf_text: str) -> ConsultantParser:
    """Select the appropriate parser for the given PDF text.

    Iterates through PARSER_REGISTRY in order and returns the first
    parser whose detect() returns True. GenericParser always matches
    as the fallback.

    Args:
        pdf_text: Full text content of the PDF document.

    Returns:
        The first matching ConsultantParser instance.
    """
    for parser in PARSER_REGISTRY:
        if parser.detect(pdf_text):
            logger.info(f"Selected parser: {parser.name}")
            return parser

    # Should never reach here since GenericParser.detect() always returns True
    logger.warning("No parser matched (unexpected) - using GenericParser")
    return GenericParser()


__all__ = [
    "ConsultantParser",
    "DocumentMeta",
    "GenericParser",
    "GreencapParser",
    "PARSER_REGISTRY",
    "PrensaParser",
    "RawACMItem",
    "SourceLocation",
    "get_parser",
]
