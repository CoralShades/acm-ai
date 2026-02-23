# Bug Fix: 0-Pages in Pipeline Logger Start Banner

**Status:** Done
**Date:** 2026-02-23
**Severity:** Low (display-only; extraction functioned correctly but log showed misleading "0 pages")

## Problem

When starting ACM extraction, the pipeline logged:

```
[PIPELINE] ================================================================
[PIPELINE] Starting extraction for source:xxx (0 pages)
[PIPELINE] ================================================================
```

The `0 pages` was incorrect — the document had been successfully processed (e.g. 33,595 chars
of full_text) but the page count always showed 0.

## Root Cause

`extract_acm_from_source` in `open_notebook/graphs/acm_extraction.py` contained a custom
page-counting regex that differed from the comprehensive `_PAGE_PATTERN` used everywhere else
in the pipeline:

```python
# BEFORE (broken) — missing PAGE N OF M format, uses count not max
page_markers = re.findall(
    r"(?:[-—]+\s*Page\s+\d+|<!--\s*Page\s+\d+\s*-->)",
    source.full_text,
    re.IGNORECASE,
)
total_pages = len(page_markers) if page_markers else 0
```

Two bugs:

1. **Missing format**: The pattern does not match `PAGE N OF M` (ARA/Greencap footer format).
   Many Victorian SAMP documents use this style; the rest of the pipeline correctly handles it
   via `_PAGE_PATTERN` in `document_structure.py`.

2. **Wrong metric**: Used `len(markers)` (count of page-marker lines found) instead of
   `max(page_numbers)` (the highest page number encountered), which is the standard used
   by `_extract_total_pages()`.

## Fix

**File:** `open_notebook/graphs/acm_extraction.py`

Replaced the custom inline regex with a call to the shared `_extract_total_pages()` utility
from `document_structure.py`, which:
- Handles all three page-marker formats: `--- Page N ---`, `<!-- Page N -->`, `PAGE N OF M`
- Returns the maximum page number seen (not a raw count)
- Is the single source of truth for page counting across the entire pipeline

Added a `logger.warning` when `total_pages == 0` and `source.full_text` is non-empty, so
operators can distinguish "document has no markers" from "page counting code is broken".

```python
# AFTER (correct)
total_pages = _extract_total_pages(source.full_text) if source.full_text else 0
if source.full_text and total_pages == 0:
    logger.warning(
        f"[PIPELINE] No page markers found in source {source.id} "
        f"({len(source.full_text)} chars). Page count will show 0 in logs. "
        "Chunking will fall back to character-based splitting."
    )
```

## Relationship to Embedding Bug

The 0-pages issue is **independent** of the Ollama embedding connection bug
(`bug-embedding-ollama-connection`). `acm_commands.py` already waits up to 120 seconds for
`source.full_text` to be populated before calling `extract_acm_from_source`, so the source
text is always present when page counting runs. The 0-pages bug exists purely because the
regex pattern was incomplete.

## Verification

```bash
uv run ruff check open_notebook/graphs/acm_extraction.py
# → All checks passed!
```

After the fix, the log will show the correct page count for ARA/Greencap style documents:

```
[PIPELINE] Starting extraction for source:xxx (34 pages)
```

For documents with no page markers (e.g. short notes), the banner correctly shows 0 and a
warning is logged to explain why.

## Integration Validation (2026-02-23)

**STEP 3 PASS** — Broadmeadows Police Station SAMP extraction confirmed showing correct page count:

```
[PIPELINE] Starting extraction for source:broadmeadows_e2e_test (19 pages)
...
[PIPELINE] EXTRACTION COMPLETE | 24 records in 372.8s
[PIPELINE]   Pages: 19 | Chunks: 1 | Buildings: 0
```

The pipeline log now correctly shows `(19 pages)` instead of `(0 pages)`.
The `_extract_total_pages()` utility correctly handled the `--- Page N ---` markers in the
Broadmeadows PDF and returned the maximum page number (19).

**Previous broken behaviour** (from old extraction progress log, Feb 21):
```
[PIPELINE] Starting extraction for source:2kztcmafrmg1zvyq2z48 (0 pages)
```

This confirms the fix is working correctly in the live extraction pipeline.
