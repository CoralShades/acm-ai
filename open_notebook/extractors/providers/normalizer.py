"""
Result normalizer: converts HTML or markdown table strings to NormalizedTable.

Utility functions used by adapters that produce HTML-first or markdown-first
output, ensuring a consistent NormalizedTable shape regardless of source format.

Story: E31-S2 Provider Adapter Framework
"""

from __future__ import annotations

import re
from typing import List

from open_notebook.extractors.providers.base import NormalizedTable


def _extract_cell_text(cell_html: str) -> str:
    """Strip HTML tags from a table cell string."""
    return re.sub(r"<[^>]+>", "", cell_html).strip()


def normalize_html_table(
    html: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable:
    """Parse an HTML <table> string into a NormalizedTable.

    Uses BeautifulSoup when available, falling back to a lightweight regex
    approach to avoid hard-failing when bs4 is not installed.

    Args:
        html: Full HTML <table>...</table> string.
        table_index: 0-based index within the source document.
        page: 1-based page number; -1 if unknown.

    Returns:
        NormalizedTable with html, markdown, and row/col counts populated.
        csv field is left None (conversion from HTML not attempted here).

    Raises:
        ValueError: If the HTML cannot be parsed as a table.
    """
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        table_tag = soup.find("table")
        if table_tag is None:
            raise ValueError("No <table> element found in HTML string")

        rows_data: List[List[str]] = []
        for tr in table_tag.find_all("tr"):
            cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
            if cells:
                rows_data.append(cells)

        if not rows_data:
            raise ValueError("HTML table contains no rows")

        columns = rows_data[0]
        data_rows = rows_data[1:]
        row_count = len(data_rows)
        col_count = len(columns)

    except ImportError:
        # Regex fallback — handles simple tables without bs4
        th_pattern = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.IGNORECASE | re.DOTALL)
        tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)

        tr_matches = tr_pattern.findall(html)
        if not tr_matches:
            raise ValueError("No <tr> elements found in HTML string")

        rows_data = []
        for tr_content in tr_matches:
            cells = [_extract_cell_text(m) for m in th_pattern.findall(tr_content)]
            if cells:
                rows_data.append(cells)

        if not rows_data:
            raise ValueError("HTML table contains no parseable rows")

        columns = rows_data[0]
        data_rows = rows_data[1:]
        row_count = len(data_rows)
        col_count = len(columns)

    # Build markdown representation
    markdown = _build_markdown(columns, data_rows)

    return NormalizedTable(
        table_index=table_index,
        page=page,
        row_count=row_count,
        col_count=col_count,
        columns=columns,
        html=html,
        markdown=markdown,
        csv=None,
        bbox=None,
    )


def normalize_markdown_table(
    markdown: str,
    table_index: int = 0,
    page: int = -1,
) -> NormalizedTable:
    """Parse a pipe-delimited markdown table into a NormalizedTable.

    Args:
        markdown: Markdown table string (may include separator row).
        table_index: 0-based index within the source document.
        page: 1-based page number; -1 if unknown.

    Returns:
        NormalizedTable with html, markdown, and row/col counts populated.

    Raises:
        ValueError: If the string doesn't contain a valid markdown table.
    """
    separator_pattern = re.compile(r"^\s*\|?[\s\-:|]+\|[\s\-:|]*$")

    lines = [ln.strip() for ln in markdown.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("Empty markdown table string")

    # Filter separator rows
    data_lines = [ln for ln in lines if not separator_pattern.match(ln)]

    if not data_lines:
        raise ValueError("Markdown table contains only separator rows")

    def _parse_row(line: str) -> List[str]:
        # Strip leading/trailing pipes then split on |
        stripped = line.strip("|").strip()
        return [cell.strip() for cell in stripped.split("|")]

    header_line = data_lines[0]
    columns = _parse_row(header_line)

    if not columns:
        raise ValueError("Could not parse header row from markdown table")

    data_rows = [_parse_row(ln) for ln in data_lines[1:]]
    row_count = len(data_rows)
    col_count = len(columns)

    # Build HTML representation
    html = _build_html(columns, data_rows)

    return NormalizedTable(
        table_index=table_index,
        page=page,
        row_count=row_count,
        col_count=col_count,
        columns=columns,
        html=html,
        markdown=markdown,
        csv=None,
        bbox=None,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_markdown(columns: List[str], data_rows: List[List[str]]) -> str:
    """Build a pipe-delimited markdown table from columns and rows."""
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in data_rows]
    return "\n".join([header, separator] + rows)


def _build_html(columns: List[str], data_rows: List[List[str]]) -> str:
    """Build a minimal HTML table from columns and rows."""
    th_cells = "".join(f"<th>{col}</th>" for col in columns)
    header_row = f"<tr>{th_cells}</tr>"
    body_rows = ""
    for row in data_rows:
        td_cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows += f"<tr>{td_cells}</tr>"
    return f"<table><thead>{header_row}</thead><tbody>{body_rows}</tbody></table>"
