# E31-S8 Tech Spec: Pre-Extraction Quality Hardening

**Story ID:** E31-S8
**Sprint:** V3-5
**Story Points:** 3
**Risk Level:** MEDIUM
**Type:** backend
**Status:** In Progress

---

## Problem Statement

Three pre-existing extraction quality gaps were identified in the Broadmeadows demo audit:

1. **AC1: total_pages = 0** — `_extract_total_pages()` uses regex to find text-based page markers. PDFs without matching page markers (e.g. Broadmeadows) return 0, breaking page-range calculations downstream.

2. **AC2: No retry on LLM failure** — `_llm_extract_structure()` in `document_structure.py` falls to heuristic on the first LLM failure with no retry. A single transient API error causes silent quality degradation.

3. **AC3: field_confidence not top-level** — `DocumentMeta.field_confidence` is persisted inside `document_meta` object in `source_intelligence`, but not as a dedicate top-level field accessible for quick queries.

4. **AC4: consultant_name searches full doc** — When page markers are absent, `_extract_cover_pages()` falls back to returning the entire document. Consultant-name patterns then match on non-cover-page content, yielding wrong values.

---

## Acceptance Criteria

- **AC1:** `extract_structure` node uses PyMuPDF page count from `source.asset.file_path` as fallback when regex finds 0 page markers — `total_pages > 0` for Broadmeadows PDF
- **AC2:** `_llm_extract_structure()` retried up to 2 times on exception before heuristic fallback activates; heuristic activation logged at WARNING level
- **AC3:** `field_confidence` dict added as top-level column in `source_intelligence` table (migration 42); `save_source_intelligence()` persists it; `save_intelligence_node` populates it
- **AC4:** `_extract_cover_pages()` bounded to first 3 pages when page markers absent (fallback: first `COVER_PAGE_CHARS` characters); `COVER_PAGE_COUNT` changed from 5 → 3
- **AC5:** Existing extraction tests pass — no regression on Broadmeadows 31/31 record count

---

## File Changes

| File | Change |
|------|--------|
| `open_notebook/extractors/document_structure.py` | MODIFIED — `_llm_extract_structure()` retry logic (AC2) |
| `open_notebook/extractors/metadata_extractor.py` | MODIFIED — `COVER_PAGE_COUNT = 3`, fallback char limit (AC4) |
| `open_notebook/graphs/acm_extraction.py` | MODIFIED — PyMuPDF page-count fallback in `extract_structure` node (AC1) |
| `open_notebook/database/repository.py` | MODIFIED — add `field_confidence` to UPSERT (AC3) |
| `migrations/42.surrealql` | NEW — add `field_confidence` column to `source_intelligence` (AC3) |
| `migrations/42_down.surrealql` | NEW — remove `field_confidence` column (AC3) |

---

## Implementation Details

### AC1 — PyMuPDF Page Count Fallback

In `extract_structure` node (`acm_extraction.py`), after calling `extract_document_structure()`, if `structure.total_pages == 0` and `source.asset` has a `file_path`, use PyMuPDF (`fitz`) to get the actual page count:

```python
# Fallback: use PyMuPDF page count if regex found 0 pages
if structure.total_pages == 0 and source.asset and source.asset.file_path:
    try:
        import fitz  # PyMuPDF
        with fitz.open(source.asset.file_path) as pdf:
            structure.total_pages = len(pdf)
        logger.info(f"PyMuPDF page count fallback: {structure.total_pages} pages")
    except Exception as e:
        logger.debug(f"PyMuPDF fallback failed: {e}")
```

### AC2 — LLM Structure Extraction Retry

In `document_structure.py`, wrap `_llm_extract_structure()` call in `extract_document_structure()` with up to 2 retries:

```python
MAX_STRUCTURE_RETRIES = 2

for attempt in range(MAX_STRUCTURE_RETRIES):
    try:
        structure = await _llm_extract_structure(content, model_id)
        ...
        return structure
    except Exception as e:
        if attempt < MAX_STRUCTURE_RETRIES - 1:
            logger.warning(f"LLM structure extraction attempt {attempt+1} failed: {e}. Retrying...")
        else:
            logger.warning(f"LLM structure extraction failed after {MAX_STRUCTURE_RETRIES} attempts: {e}. Using heuristic fallback.")
            fallback = _heuristic_fallback(content)
            return fallback
```

### AC3 — field_confidence as Top-Level Column

**Migration 42:**
```sql
DEFINE FIELD IF NOT EXISTS field_confidence ON TABLE source_intelligence TYPE option<object>;
```

**repository.py** — extend UPSERT to include `field_confidence`:
```python
query = (
    "UPSERT source_intelligence SET "
    "source_id = $data.source_id, "
    "document_meta = $data.document_meta, "
    ...
    "field_confidence = $data.field_confidence, "
    "updated_at = $data.updated_at "
    "WHERE source_id = $data.source_id;"
)
```

**save_intelligence_node** — include field_confidence in data dict:
```python
data: Dict[str, Any] = {
    ...
    "field_confidence": doc_meta.field_confidence if doc_meta else None,
}
```

### AC4 — Cover Page Window Bounded to 3 Pages

In `metadata_extractor.py`:
```python
COVER_PAGE_COUNT = 3  # Changed from 5 → 3
COVER_PAGE_CHARS = 8000  # Fallback char limit when no page markers exist

def _extract_cover_pages(content: str, max_pages: int = COVER_PAGE_COUNT) -> str:
    page_positions = list(_PAGE_PATTERN.finditer(content))
    if not page_positions:
        # No page markers — bound to first COVER_PAGE_CHARS characters
        return content[:COVER_PAGE_CHARS]
    ...
```

---

## Test Coverage

- `tests/test_document_structure.py` — test retry logic (mock LLM failure then success)
- `tests/test_e2e_extraction.py` — field_confidence in persisted intelligence
- `tests/test_orchestrator.py` — save_intelligence_node includes field_confidence
- `tests/test_page_tagger.py` — no regression
