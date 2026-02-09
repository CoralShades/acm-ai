"""ACM context utilities for chat functionality.

This module provides utilities for detecting ACM question types and formatting
ACM context based on question patterns to improve AI responses.
"""

import re
from typing import Any, List, Protocol, runtime_checkable


@runtime_checkable
class ACMRecordProtocol(Protocol):
    """Protocol for ACM record objects - works with any ACMRecord-like object."""

    building_id: str | None
    building_name: str | None
    room_id: str | None
    room_name: str | None
    product: str | None
    material_description: str | None
    risk_status: str | None
    result: str | None


def detect_question_type(message: str) -> str:
    """Detect the type of ACM question being asked.

    This function analyzes the user message to determine the type of ACM-related
    question, which can be used to optimize context formatting.

    The detection uses priority ordering where more specific patterns
    are checked before more general ones.

    Args:
        message: The user's message/question

    Returns:
        Question type string: 'location_query', 'risk_query', 'terminology_query',
        'action_query', 'summary_query', or 'general'
    """
    message_lower = message.lower()

    # Risk queries - asking about safety, hazards, or risk levels
    # High priority - check before location since "is building safe" should be risk
    if re.search(
        r"\b(risk|danger|safe|hazard|hazardous|high[\s-]?risk|low[\s-]?risk|medium[\s-]?risk)\b",
        message_lower,
    ):
        return "risk_query"

    # Location queries - asking about specific buildings or rooms
    # High priority since "What's in Building A" should be location, not terminology
    if re.search(r"\b(building|room|floor|wing|block|section)\b", message_lower):
        return "location_query"

    # Action queries - asking about what to do or compliance
    if re.search(
        r"\b(remove|action|do we need|should we|remediat|encapsulat|needs? to|recommend)",
        message_lower,
    ):
        return "action_query"

    # Summary queries - asking for overview or counts
    if re.search(
        r"\b(summary|overview|total|count|how many|list all|show all)\b", message_lower
    ):
        return "summary_query"

    # Terminology queries - asking for definitions or explanations
    # "what is", "define", "explain" patterns
    if re.search(
        r"\b(what is|what are|what does|define|explain|meaning of|meaning)\b",
        message_lower,
    ):
        return "terminology_query"

    # Location queries can also match "area" but only if nothing else matched
    if re.search(r"\b(area)\b", message_lower):
        return "location_query"

    return "general"


def format_acm_context_for_question(records: List[Any], question_type: str) -> str:
    """Format ACM context based on question type.

    This function formats ACM records in a way that's optimized for the type
    of question being asked.

    Args:
        records: List of ACM records to format
        question_type: The detected question type

    Returns:
        Formatted markdown string with ACM context
    """
    if not records:
        return ""

    if question_type == "risk_query":
        return _format_risk_summary(records)

    elif question_type == "location_query":
        return _format_by_location(records)

    elif question_type == "summary_query":
        return _format_summary(records)

    else:
        # Default: table format for general, terminology, and action queries
        return _format_as_table(records)


def _format_risk_summary(records: List[Any]) -> str:
    """Format records grouped by risk status."""
    by_risk: dict[str, list[Any]] = {}
    for r in records:
        risk = r.risk_status or "Unknown"
        by_risk.setdefault(risk, []).append(r)

    lines = ["## ACM Risk Summary", ""]

    # Order by severity
    for risk in ["High", "Medium", "Low", "Unknown"]:
        if risk in by_risk:
            risk_records = by_risk[risk]
            count = len(risk_records)
            item_word = "item" if count == 1 else "items"
            lines.append(f"### {risk} Risk ({count} {item_word})")
            lines.append("")
            # Limit per category for readability
            for r in risk_records[:10]:
                building = r.building_name or r.building_id or "Unknown"
                room = r.room_name or r.room_id or "-"
                product = r.product or "Unknown material"
                lines.append(f"- **{building}/{room}**: {product}")
            if len(risk_records) > 10:
                lines.append(f"- *...and {len(risk_records) - 10} more*")
            lines.append("")

    return "\n".join(lines)


def _format_by_location(records: List[Any]) -> str:
    """Format records grouped by building location."""
    by_building: dict[str, list[Any]] = {}
    for r in records:
        building = r.building_name or r.building_id or "Unknown"
        by_building.setdefault(building, []).append(r)

    lines = ["## ACM by Location", ""]

    for building, items in sorted(by_building.items()):
        lines.append(f"### {building}")
        lines.append("")
        lines.append("| Room | Product | Risk |")
        lines.append("|------|---------|------|")
        for r in items:
            room = r.room_name or r.room_id or "-"
            product = r.product or "-"
            risk = r.risk_status or "-"
            lines.append(f"| {room} | {product} | {risk} |")
        lines.append("")

    return "\n".join(lines)


def _format_summary(records: List[Any]) -> str:
    """Format a summary overview of all records."""
    # Count by risk
    risk_counts: dict[str, int] = {}
    for r in records:
        risk = r.risk_status or "Unknown"
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    # Count by building
    building_counts: dict[str, int] = {}
    for r in records:
        building = r.building_name or r.building_id or "Unknown"
        building_counts[building] = building_counts.get(building, 0) + 1

    lines = [
        "## ACM Summary Overview",
        "",
        f"**Total Records:** {len(records)}",
        "",
        "### By Risk Level",
        "",
    ]

    for risk in ["High", "Medium", "Low", "Unknown"]:
        if risk in risk_counts:
            lines.append(f"- **{risk}**: {risk_counts[risk]} items")

    lines.extend(["", "### By Building", ""])

    for building, count in sorted(
        building_counts.items(), key=lambda x: x[1], reverse=True
    ):
        lines.append(f"- **{building}**: {count} items")

    lines.append("")

    return "\n".join(lines)


def _format_as_table(records: List[Any]) -> str:
    """Format records as a simple table."""
    lines = [
        "## ACM Register Data",
        "",
        "| Building | Room | Product | Material | Risk | Result |",
        "|----------|------|---------|----------|------|--------|",
    ]

    for r in records[:50]:  # Limit to 50 for readability
        building = r.building_name or r.building_id or "-"
        room = r.room_name or r.room_id or "-"
        product = r.product or "-"
        # Truncate material description
        material = r.material_description or "-"
        if len(material) > 30:
            material = material[:30] + "..."
        risk = r.risk_status or "-"
        result = r.result or "-"

        lines.append(
            f"| {building} | {room} | {product} | {material} | {risk} | {result} |"
        )

    if len(records) > 50:
        lines.extend(["", f"*({len(records)} total records, showing first 50)*"])

    return "\n".join(lines)
