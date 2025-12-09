# Tech Spec: E3-S4 - Store Page Numbers During Extraction

> **Story:** E3-S4
> **Epic:** Cell Citations & PDF Viewer
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Enhance the ACM extraction transformation to capture and store the PDF page number for each extracted record, enabling accurate citation links.

---

## User Story

**As a** system
**I want** to track which PDF page each ACM record came from
**So that** citations can link to the correct page

---

## Acceptance Criteria

- [ ] Extraction pipeline captures page numbers
- [ ] Page number stored in `acm_record.page_number`
- [ ] Works correctly for multi-page registers
- [ ] Falls back gracefully if page number unavailable

---

## Technical Design

### 1. Docling Output Analysis

Docling provides document structure with page information. The output format includes:

```json
{
  "pages": [
    {
      "page_number": 1,
      "elements": [
        {
          "type": "table",
          "bbox": [x, y, w, h],
          "content": "..."
        }
      ]
    }
  ]
}
```

Or in markdown format with page markers:
```markdown
<!-- Page 1 -->
| Building | Room | Product | Result |
|----------|------|---------|--------|
| A1 | 101 | Tiles | Detected |

<!-- Page 2 -->
| Building | Room | Product | Result |
|----------|------|---------|--------|
| A1 | 102 | Pipe | Not Detected |
```

### 2. Page Number Extraction Logic

In `open_notebook/transformations/acm_extraction.py`:

```python
import re
from typing import List, Optional, Tuple

def extract_acm_records_with_pages(
    content: str,
    source_id: str
) -> List[ACMRecord]:
    """Extract ACM records with page number tracking."""
    records = []
    current_page = 1

    # Split content by page markers
    page_pattern = r'<!--\s*Page\s*(\d+)\s*-->'
    sections = re.split(page_pattern, content)

    # Process sections (alternating between page numbers and content)
    i = 0
    while i < len(sections):
        section = sections[i]

        # Check if this is a page number marker
        if i > 0 and i % 2 == 1:
            current_page = int(section)
            i += 1
            continue

        # Parse tables in this section
        tables = extract_tables_from_section(section)

        for table in tables:
            if is_acm_register_table(table):
                table_records = parse_acm_table(table, source_id)
                for record in table_records:
                    record.page_number = current_page
                records.extend(table_records)

        i += 1

    return records
```

### 3. Alternative: JSON Docling Output

If using Docling's JSON output:

```python
def extract_from_docling_json(docling_output: dict, source_id: str) -> List[ACMRecord]:
    """Extract ACM records from Docling JSON with page numbers."""
    records = []

    for page in docling_output.get("pages", []):
        page_number = page.get("page_number", 1)

        for element in page.get("elements", []):
            if element.get("type") == "table":
                table_content = element.get("content", "")
                if is_acm_register_table(table_content):
                    table_records = parse_acm_table(table_content, source_id)
                    for record in table_records:
                        record.page_number = page_number
                    records.extend(table_records)

    return records
```

### 4. Table Continuation Handling

Handle tables that span multiple pages:

```python
def parse_multi_page_table(
    table_parts: List[Tuple[str, int]],  # (content, page_number)
    source_id: str
) -> List[ACMRecord]:
    """Parse a table that spans multiple pages."""
    records = []

    # First page has headers
    headers = extract_headers(table_parts[0][0])

    for content, page_number in table_parts:
        rows = extract_rows(content, headers)
        for row in rows:
            record = create_acm_record(row, source_id)
            record.page_number = page_number
            records.append(record)

    return records
```

### 5. Fallback Behavior

When page number is unavailable:

```python
def extract_acm_records(content: str, source_id: str) -> List[ACMRecord]:
    """Extract with graceful fallback for missing page numbers."""
    records = []

    # Try to detect page markers
    has_page_markers = bool(re.search(r'<!--\s*Page\s*\d+\s*-->', content))

    if has_page_markers:
        records = extract_acm_records_with_pages(content, source_id)
    else:
        # No page markers - extract without page numbers
        records = extract_acm_records_simple(content, source_id)
        # Log warning for debugging
        logger.warning(f"No page markers found in source {source_id}, page numbers unavailable")

    return records
```

---

## File Changes

| File | Change |
|------|--------|
| `open_notebook/transformations/acm_extraction.py` | Add page number tracking |
| `open_notebook/domain/acm.py` | Already has `page_number` field |

---

## Dependencies

- E1-S3: ACM Extraction Transformation (base implementation)

---

## Testing

1. Process PDF with page markers - verify page numbers stored
2. Process multi-page register - verify different pages tracked
3. Process PDF without page markers - verify graceful fallback
4. Verify page numbers in API response
5. Verify PDF viewer opens to correct page

### Test Data

Create test fixtures:
```python
MULTI_PAGE_CONTENT = """
<!-- Page 5 -->
| Building | Room | Product | Result |
|----------|------|---------|--------|
| Admin | A101 | Floor Tiles | Detected |

<!-- Page 6 -->
| Building | Room | Product | Result |
|----------|------|---------|--------|
| Admin | A102 | Ceiling | Not Detected |
"""

def test_page_number_extraction():
    records = extract_acm_records_with_pages(MULTI_PAGE_CONTENT, "source:test")
    assert records[0].page_number == 5
    assert records[1].page_number == 6
```

---

## Estimated Complexity

**Medium** - Requires understanding Docling output format and multi-page handling

---
