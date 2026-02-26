"""Docling content normalization helpers for ACM extraction."""

import re
from typing import Dict, List, Tuple

from loguru import logger

_NORMALIZATION_RULES: Tuple[Tuple[str, str, str, int], ...] = (
    (
        r"\bAsbestos\s*\n\s*Assumed\s*\n\s*positive\b",
        "Asbestos Assumed positive",
        "asbestos_assumed_positive",
        re.IGNORECASE,
    ),
    (
        r"\bAsbestos\s*\n\s*Negative\b",
        "Asbestos Negative",
        "asbestos_negative",
        re.IGNORECASE,
    ),
    (
        r"\bAsbestos\s*\n\s*Positive\b",
        "Asbestos Positive",
        "asbestos_positive",
        re.IGNORECASE,
    ),
    (
        r"(Same\s+as)\s*\n\s*(34511-039-?\d+)",
        r"\1 \2",
        "same_as_sample_ref",
        re.IGNORECASE,
    ),
    (
        r"(34511-039-?)\s*\n\s*(\d{3})",
        r"\1\2",
        "split_sample_suffix",
        re.IGNORECASE,
    ),
    (
        r"\bAssumed\s*\n\s*positive\b",
        "Assumed positive",
        "assumed_positive",
        re.IGNORECASE,
    ),
    (
        r"\bNo\s*\n\s*access\b",
        "No access",
        "no_access",
        re.IGNORECASE,
    ),
    (
        r"\bN/?A\s*\n\s*\(negative\)",
        "N/A (negative)",
        "na_negative",
        re.IGNORECASE,
    ),
    (
        r"\bNot\s*\n\s*sampled\b",
        "Not sampled",
        "not_sampled",
        re.IGNORECASE,
    ),
    (
        r"\bFront\s*Desk\s*\n\s*Area\b",
        "Front Desk Area",
        "split_room_front_desk_area",
        re.IGNORECASE,
    ),
    (
        r"\bMain\s*\n\s*Foyer\b",
        "Main Foyer",
        "split_room_main_foyer",
        re.IGNORECASE,
    ),
    (
        r"\bSwitch\s*\n\s*Room\b",
        "Switch Room",
        "split_room_switch_room",
        re.IGNORECASE,
    ),
    (
        r"\bBoiler\s*\n\s*Room\b",
        "Boiler Room",
        "split_room_boiler_room",
        re.IGNORECASE,
    ),
    (
        r"\bLift\s*\n\s*Foyer\b",
        "Lift Foyer",
        "split_room_lift_foyer",
        re.IGNORECASE,
    ),
    (
        r"(\d{5})\s*\n\s*-\s*\n\s*(\d{3})\s*\n\s*-\s*\n\s*(\d{3})",
        r"\1-\2-\3",
        "split_sample_number",
        re.IGNORECASE,
    ),
)

_ROW_CONTINUATION_START = (
    "same as",
    "as per",
    "assumed",
    "not",
    "no",
    "n/a",
)

_ROW_CONTINUATION_END = (
    "positive",
    "sampled",
    "access",
    "(negative)",
)


def _is_markdown_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_separator_row(cells: List[str]) -> bool:
    return all(re.fullmatch(r"[:\-\s]+", cell or "") for cell in cells)


def _split_table_cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _should_merge_row_pair(current_cells: List[str], next_cells: List[str]) -> bool:
    if len(current_cells) != len(next_cells):
        return False
    if _is_separator_row(current_cells) or _is_separator_row(next_cells):
        return False

    for current_cell, next_cell in zip(current_cells, next_cells):
        current_lower = current_cell.lower()
        next_lower = next_cell.lower()

        if current_lower.startswith(_ROW_CONTINUATION_START):
            return True
        if next_lower.startswith(_ROW_CONTINUATION_END):
            return True
        if current_lower.endswith("-") and next_lower.isdigit():
            return True
        if re.fullmatch(r"\d{5}-\d{3}-?", current_lower) and re.fullmatch(
            r"\d{3}", next_lower
        ):
            return True

    return False


def reconstruct_markdown_table_rows(content: str) -> str:
    """Reconstruct Docling markdown rows split across adjacent table lines.

    This targets rows where cell values are split vertically, for example:
    | Front Desk | Filing | Assumed |
    | Area       | Cabinet| Positive |
    """
    if not content:
        return content

    lines = content.splitlines()
    reconstructed: List[str] = []
    merge_count = 0
    index = 0

    while index < len(lines):
        current = lines[index]
        if index + 1 >= len(lines):
            reconstructed.append(current)
            index += 1
            continue

        next_line = lines[index + 1]

        if _is_markdown_table_row(current) and _is_markdown_table_row(next_line):
            current_cells = _split_table_cells(current)
            next_cells = _split_table_cells(next_line)

            if _should_merge_row_pair(current_cells, next_cells):
                merged_cells = [
                    f"{left} {right}".strip()
                    for left, right in zip(current_cells, next_cells)
                ]
                reconstructed.append("| " + " | ".join(merged_cells) + " |")
                merge_count += 1
                index += 2
                continue

        reconstructed.append(current)
        index += 1

    if merge_count > 0:
        logger.info(
            "Docling table-row reconstruction merged {merge_count} split rows",
            merge_count=merge_count,
        )

    return "\n".join(reconstructed)


def normalize_docling_text(text: str) -> str:
    """Normalize line-broken Docling values before LLM extraction.

    Args:
        text: Raw Docling text content.

    Returns:
        Text with targeted line-break fixes applied.
    """
    if not text:
        return text

    normalized = text
    fix_counts: Dict[str, int] = {}
    total_fixes = 0

    for pattern, replacement, fix_name, flags in _NORMALIZATION_RULES:
        normalized, count = re.subn(pattern, replacement, normalized, flags=flags)
        if count > 0:
            fix_counts[fix_name] = count
            total_fixes += count

    reconstructed = reconstruct_markdown_table_rows(normalized)
    if reconstructed != normalized:
        fix_counts["markdown_row_reconstruction"] = (
            fix_counts.get("markdown_row_reconstruction", 0) + 1
        )
        total_fixes += 1
        normalized = reconstructed

    if total_fixes > 0:
        logger.info(
            "Docling normalization applied {total_fixes} fixes: {fix_counts}",
            total_fixes=total_fixes,
            fix_counts=fix_counts,
        )

    return normalized
