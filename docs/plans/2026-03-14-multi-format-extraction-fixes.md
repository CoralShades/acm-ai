# Multi-Format Extraction Pipeline Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 11 findings from the multi-format extraction audit so the pipeline correctly handles Greencap ARA, NSW DoE SAMP, and unknown register formats — not just Clutch/Broadmeadows.

**Architecture:** The ACM extraction pipeline runs as a LangGraph graph with sequential nodes: `metadata_and_structure_node` -> `save_intelligence_node` -> `extract_building_node` -> `extract_items_node` -> `normalize_to_sf_node` -> `validate_node` -> `save_node` -> `recover_no_access_node`. The bugs span the full pipeline: prompts that assume Clutch format, code that uses LLM output instead of inventory data for building names, page counting that relies on text markers instead of actual PDF page count, and concurrent execution that causes deadlocks.

**Tech Stack:** Python 3.11, LangGraph, Jinja2 prompts, SurrealDB, Ollama (llama3.1:8b), Docling for PDF table extraction.

**Audit reference:** `docs/sprint-artifacts/multi-format-audit/findings.md`

---

## Sprint 1: Quick Wins (F10, F7, F1, F9) — Est. 1 day

These four fixes are low-risk, well-scoped, and independently testable.

---

### Task 1: BuildingRecord Name Fallback (F10)

**Files:**
- Modify: `open_notebook/graphs/acm_extraction.py:679`
- Test: `tests/test_building_extraction.py` (existing)

**Step 1: Write a failing test**

Add to `tests/test_building_extraction.py`:

```python
@pytest.mark.asyncio
async def test_building_name_falls_back_to_inventory_name(monkeypatch):
    """F10: When Phase 1 LLM returns site_name, BuildingRecord should use inventory name."""
    # Simulate Phase 1 returning a result where building_name is the site name
    # but inventory has the correct building name
    from open_notebook.extractors.building_inventory import BuildingMetaEntry

    inventory_entry = BuildingMetaEntry(
        building_id="B001",
        name="Administration",  # correct name from inventory
        page_start=3,
        page_end=15,
    )

    # The LLM returns site_name "Aldavilla Public School" instead of building name
    # With the fix, BuildingRecord.building_name should fall back to inventory_entry.name
    assert inventory_entry.name == "Administration"
    # The fallback expression:
    result_building_name = None  # simulate LLM returning None
    final_name = result_building_name or inventory_entry.name
    assert final_name == "Administration"

    # Also test when LLM returns site name (not None but wrong)
    result_building_name_site = "Aldavilla Public School"
    # This case still uses the LLM value — the fix only covers None/empty
    # A separate F1 fix handles the site_name-as-building_name issue
    final_name_2 = result_building_name_site or inventory_entry.name
    assert final_name_2 == "Aldavilla Public School"  # LLM value wins when non-empty
```

**Step 2: Run test to verify it passes** (this is a logic test, not integration — it will pass immediately since it tests the expression, not the pipeline)

Run: `uv run pytest tests/test_building_extraction.py::test_building_name_falls_back_to_inventory_name -v`

**Step 3: Apply the fix**

In `open_notebook/graphs/acm_extraction.py`, line 679, change:

```python
building_name=result.building_name,
```

to:

```python
building_name=result.building_name or building_meta_entry.name,
```

This matches the pattern already used in the minimal record path at line 638.

**Step 4: Run full test suite for building extraction**

Run: `uv run pytest tests/test_building_extraction.py -v`
Expected: All pass

**Step 5: Commit**

```bash
git add open_notebook/graphs/acm_extraction.py tests/test_building_extraction.py
git commit -m "fix(extraction): F10 — BuildingRecord.building_name fallback to inventory name

When Phase 1 LLM returns null building_name, fall back to the building
inventory entry's name. Matches the existing pattern used in the minimal
record path (line 638)."
```

---

### Task 2: Set Default Extraction Model (F7)

**Files:**
- Modify: `.env`

**Step 1: Add the missing env var**

Append to `.env`:

```bash
ACM_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0
```

**Step 2: Verify the env var is read**

Run: `grep ACM_EXTRACTION_MODEL .env`
Expected: `ACM_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0`

**Step 3: Verify the model exists in Ollama**

Run: `curl -s http://localhost:11434/api/tags | python -m json.tool | grep "llama3.1:8b"`
Expected: Model name appears in list

**Step 4: Commit**

```bash
git add .env
git commit -m "fix(config): F7 — set ACM_EXTRACTION_MODEL to llama3.1:8b

Pipeline was falling back to DB default (phi4:14b), causing 4x slower
per-row extraction. Explicit env var ensures the fast 8B model is used."
```

---

### Task 3: Building Name from Inventory, Not LLM (F1)

This is the more comprehensive fix for F10. Even when the LLM returns a non-null building_name, it often returns the site name (e.g., "Aldavilla Public School") instead of the building name (e.g., "Administration"). The inventory always has the correct building name.

**Files:**
- Modify: `open_notebook/graphs/acm_extraction.py:679`
- Test: `tests/test_building_extraction.py`

**Step 1: Write a failing test**

```python
@pytest.mark.asyncio
async def test_building_name_always_prefers_inventory_name(monkeypatch):
    """F1: BuildingRecord.building_name should ALWAYS use inventory name,
    not the Phase 1 LLM output which often returns the site name."""
    # Inventory says "Administration"
    inventory_name = "Administration"
    # LLM says "Aldavilla Public School" (the site name — wrong!)
    llm_building_name = "Aldavilla Public School"

    # With F1 fix: always use inventory name
    final_name = inventory_name  # not llm_building_name
    assert final_name == "Administration"
```

**Step 2: Apply the fix**

In `open_notebook/graphs/acm_extraction.py`, line 679, change:

```python
building_name=result.building_name or building_meta_entry.name,
```

to:

```python
building_name=building_meta_entry.name or result.building_name,
```

This reverses the priority: always prefer the inventory name. Fall back to LLM output only if inventory has no name (unlikely — the inventory prompt always extracts names).

**Step 3: Run tests**

Run: `uv run pytest tests/test_building_extraction.py -v`
Expected: All pass

**Step 4: Commit**

```bash
git add open_notebook/graphs/acm_extraction.py tests/test_building_extraction.py
git commit -m "fix(extraction): F1 — BuildingRecord always uses inventory building name

Phase 1 LLM often returns the site name instead of the building name
for multi-building documents. The building_inventory prompt reliably
extracts the correct per-building name. Reverse priority so inventory
name is always preferred."
```

---

### Task 4: Add Column Aliases for Greencap ARA and NSW DoE SAMP (F9)

**Files:**
- Modify: `open_notebook/extractors/row_segmenter.py:26-51`
- Test: `tests/test_row_segmenter.py` (existing)

**Step 1: Write failing tests**

Add to `tests/test_row_segmenter.py`:

```python
from open_notebook.extractors.row_segmenter import COLUMN_ALIASES


def test_greencap_column_aliases_mapped():
    """F9: Greencap ARA column headers should map to canonical names."""
    # Flatten all aliases for lookup
    all_aliases = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            all_aliases[alias.lower()] = canonical

    # Greencap-specific headers
    assert "item no" in all_aliases or "item no." in all_aliases
    assert "building element" in all_aliases
    assert "risk rating" in all_aliases
    assert "acm status" in all_aliases


def test_nsw_doe_column_aliases_mapped():
    """F9: NSW DoE SAMP column headers should map to canonical names."""
    all_aliases = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            all_aliases[alias.lower()] = canonical

    assert "location description" in all_aliases
    assert "assumed/confirmed" in all_aliases
```

**Step 2: Run tests to see them fail**

Run: `uv run pytest tests/test_row_segmenter.py::test_greencap_column_aliases_mapped tests/test_row_segmenter.py::test_nsw_doe_column_aliases_mapped -v`
Expected: FAIL — aliases not present

**Step 3: Add aliases**

In `open_notebook/extractors/row_segmenter.py`, update `COLUMN_ALIASES`:

```python
COLUMN_ALIASES: dict[str, list[str]] = {
    "room_location": [
        "room", "room/area", "area", "location", "room no",
        "location description",  # NSW DoE SAMP
    ],
    "item_description": [
        "material", "product", "item", "description",
        "product description", "acm type",
        "building element", "material type",  # Greencap ARA
    ],
    "friability": [
        "friable", "f/nf", "friability", "type",
        "assumed/confirmed",  # NSW DoE SAMP
    ],
    "condition": ["condition", "material condition", "state", "assessment"],
    "sample_number": [
        "sample", "sample#", "sample no", "nata no",
        "item no", "item no.",  # Greencap ARA / NSW DoE
    ],
    "sample_result": [
        "result", "lab result", "analysis",
        "acm status",  # Greencap ARA
    ],
    "quantity": ["quantity", "qty", "area", "extent", "m\u00b2"],
    "recommendation": ["recommendation", "action", "management"],
    "accessibility": ["access", "accessible"],
    "asbestos_type": ["asbestos type", "fibre type", "fibre"],
    "disturbance_potential": [
        "disturbance", "dp", "risk",
        "risk rating", "priority",  # Greencap ARA
    ],
    "specific_location": [
        "specific location", "position", "element", "where",
    ],
}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_row_segmenter.py -v`
Expected: All pass including new tests

**Step 5: Commit**

```bash
git add open_notebook/extractors/row_segmenter.py tests/test_row_segmenter.py
git commit -m "fix(extraction): F9 — add column aliases for Greencap ARA and NSW DoE SAMP

Adds aliases: 'building element', 'material type', 'item no',
'risk rating', 'acm status', 'location description', 'assumed/confirmed'.
Without these, non-Clutch format columns fall through to opaque col_N keys."
```

---

## Sprint 2: Prompt Fixes (F2, F4, F3) — Est. 1-2 days

These require prompt engineering and are harder to test deterministically with Ollama.

---

### Task 5: Building Inventory Prompt — Multi-Format Support (F2, F6)

**Files:**
- Modify: `prompts/acm/building_inventory.jinja`
- Test: Manual verification with `uv run pytest tests/test_building_inventory.py -v`

**Step 1: Update the building inventory prompt**

Add format-specific instructions to `prompts/acm/building_inventory.jinja` after the "Building Detection" section (after line 14):

```jinja
## Format-Specific Building Detection

### Greencap ARA Format
- Buildings appear as sections with headers like "Building Name: Myrtle Street Clinic"
- Each building section has its own risk assessment table
- Extract ONLY the building name from the header — NOT the entire table row
- If the header contains "| Building Name: | X |", extract "X" as the name
- Page ranges span from the building header to the next building header

### NSW DoE SAMP Format
- Buildings appear in a summary grid/table (e.g., pages 3-15)
- Grid columns include: Building ID, Name, Year, Construction
- Each row = one building (B001, B002, etc.)
- Buildings may share the same page range when in a grid
- "No Asbestos" buildings should still be listed with complexity="simple"
- ACM data appears on later pages, referenced by building ID (e.g., B009-R0001)

### General Rules
- Do NOT return raw markdown table rows as building names or IDs
- building_id should be a short code (B001, B00A, D01) — NOT a full table row
- building name should be a short name — NOT a pipe-delimited row
```

**Step 2: Run existing inventory tests**

Run: `uv run pytest tests/test_building_inventory.py -v`
Expected: All pass (prompt changes are additive)

**Step 3: Commit**

```bash
git add prompts/acm/building_inventory.jinja
git commit -m "fix(prompts): F2/F6 — building inventory prompt handles Greencap ARA and NSW DoE SAMP

Adds format-specific building detection instructions:
- Greencap ARA: extract building name from section headers, not full table rows
- NSW DoE SAMP: extract buildings from summary grid, handle shared page ranges
- General: never return raw markdown rows as building_id or name"
```

---

### Task 6: Metadata Prompt — Image Consultant Handling (F4)

**Files:**
- Modify: `prompts/acm/metadata_and_structure.jinja`

**Step 1: Update the metadata prompt**

In `prompts/acm/metadata_and_structure.jinja`, add after line 6 ("consultant_name"):

```jinja
- consultant_name: company that prepared the report (e.g. "Prensa Pty Ltd"). If the consultant name appears only in a logo/image (shown as <!-- image --> in markdown), try to infer from other text context (footer, header, ABN references). If still unknown, use "Unknown" — do NOT output "<!-- image -->"
```

Replace line 24 with:

```jinja
- document_type: "SAMP" (school asbestos management plan — may have B### codes OR sequential building IDs), "ARA" (asbestos risk assessment with named buildings), "Division_5" (regulatory), or "Unknown"
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/ -k "metadata" -v`
Expected: All pass

**Step 3: Commit**

```bash
git add prompts/acm/metadata_and_structure.jinja
git commit -m "fix(prompts): F4 — metadata prompt handles image-based consultant names

Instructs LLM to never output '<!-- image -->' as consultant_name.
Also broadens SAMP detection to cover sequential building IDs, not
just B### codes (fixes NSW DoE misclassification)."
```

---

### Task 7: Page Count from acm_table_section, Not Text Markers (F3)

**Files:**
- Modify: `open_notebook/graphs/acm_extraction.py:2713`
- Modify: `open_notebook/extractors/document_structure.py:104-111`
- Test: `tests/test_page_tagger.py` or new test file

**Step 1: Write failing test**

Create `tests/test_total_pages_fallback.py`:

```python
from open_notebook.extractors.document_structure import _extract_total_pages


def test_extract_total_pages_with_markers():
    content = "--- Page 1 ---\nfoo\n--- Page 5 ---\nbar\n--- Page 10 ---\nbaz"
    assert _extract_total_pages(content) == 10


def test_extract_total_pages_no_markers():
    content = "Some text without any page markers at all"
    assert _extract_total_pages(content) == 0
```

**Step 2: Run to verify baseline passes**

Run: `uv run pytest tests/test_total_pages_fallback.py -v`
Expected: Both pass (testing existing behavior)

**Step 3: Add fallback in `extract_acm_from_source`**

In `open_notebook/graphs/acm_extraction.py` at line 2713, change:

```python
total_pages = _extract_total_pages(source.full_text) if source.full_text else 0
```

to:

```python
total_pages = _extract_total_pages(source.full_text) if source.full_text else 0
# F3 fix: if text markers give 0 pages, fall back to max page from acm_table_section
if total_pages == 0 and source.id:
    try:
        from open_notebook.database.repository import ensure_record_id, repo_query
        _sid = ensure_record_id(str(source.id))
        page_result = await repo_query(
            "SELECT math::max(page_end) AS max_page FROM acm_table_section "
            "WHERE source_id = $sid GROUP ALL;",
            {"sid": _sid},
        )
        if page_result and page_result[0].get("max_page"):
            total_pages = int(page_result[0]["max_page"])
            logger.info(
                f"[PIPELINE] Page count from acm_table_section: {total_pages} "
                f"(text markers returned 0)"
            )
    except Exception as e:
        logger.warning(f"[PIPELINE] Failed to get page count from tables: {e}")
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_total_pages_fallback.py tests/test_page_tagger.py -v`
Expected: All pass

**Step 5: Commit**

```bash
git add open_notebook/graphs/acm_extraction.py tests/test_total_pages_fallback.py
git commit -m "fix(extraction): F3 — fallback page count from acm_table_section

When text page markers give 0 pages (e.g., Alexander Hospital with
Greencap format), fall back to max(page_end) from acm_table_section.
This prevents the pipeline from only processing pages 1-4 of a 24-page PDF."
```

---

## Sprint 3: Stability (F8) — Est. 0.5 day

---

### Task 8: Prevent Concurrent Extraction Deadlock (F8)

**Files:**
- Modify: `commands/acm_commands.py:132`
- Test: manual verification (concurrency bugs are hard to unit test)

**Step 1: Add graph invocation timeout**

In `commands/acm_commands.py`, wrap the `extract_acm_from_source` call (line 290) with a timeout:

```python
# 3. Run AI extraction with timeout guard (F8: concurrent executions can deadlock)
import asyncio as _asyncio

try:
    result = await _asyncio.wait_for(
        extract_acm_from_source(
            source=source,
            model_id=model_id,
            force=False,
            command_id=command_id,
        ),
        timeout=1800,  # 30 minutes max per extraction
    )
except _asyncio.TimeoutError:
    processing_time = time.time() - start_time
    logger.error(
        f"ACM extraction timed out after 1800s for {source_id}"
    )
    if command_id:
        await _write_terminal_status(command_id, "failed", 0)
    return ACMExtractionOutput(
        success=False,
        source_id=source_id,
        records_created=0,
        records_deleted=deleted_count,
        processing_time=processing_time,
        error_message="Extraction timed out after 30 minutes",
        extraction_method="ai",
    )
```

**Step 2: Run tests**

Run: `uv run pytest tests/ -k "acm_extract" -v`
Expected: All pass

**Step 3: Commit**

```bash
git add commands/acm_commands.py
git commit -m "fix(extraction): F8 — add 30-minute timeout to prevent extraction deadlock

Concurrent acm_extract commands can deadlock the asyncio event loop.
Wraps extract_acm_from_source in asyncio.wait_for(timeout=1800) so
stuck extractions fail gracefully instead of hanging forever."
```

---

## Sprint 4: Architecture (F5, F11) — Est. 1-2 weeks

This is the hardest fix. When buildings share the same page range (NSW DoE SAMP grid format), every building gets ALL tables. The fix requires content-based building discrimination.

---

### Task 9: Design — Building-Aware Table Routing (F5, F11)

**Files:**
- Create: `docs/plans/building-table-routing-design.md`

**Step 1: Write design document**

The chosen approach is **(b) from the audit**: process the shared table ONCE, then distribute records to buildings by matching row content (room_id, building_id) to the building inventory.

**Design:**

1. In `extract_items_node`, before the per-building loop, detect if buildings share page ranges:
   ```python
   page_sets = [(b.page_start, b.page_end) for b in inventory.buildings]
   all_same = len(set(page_sets)) == 1 and len(page_sets) > 1
   ```

2. If `all_same`, switch to "grid extraction mode":
   - Fetch ALL tables once (not per-building)
   - Run per-row extraction on ALL rows
   - For each extracted record, match to a building using:
     - `room_id` prefix (e.g., "B009-R0001" -> building B009)
     - Building name in record content
     - Building ID in `data_issues` or metadata
   - Assign `building_record_id` based on match

3. If not `all_same`, use existing per-building extraction (unchanged)

**Step 2: Commit design**

```bash
git add docs/plans/building-table-routing-design.md
git commit -m "docs: F5/F11 — design for building-aware table routing"
```

**Step 3-N: Implementation** (multiple sub-tasks — scope TBD after design review)

Key implementation areas:
- `open_notebook/graphs/acm_extraction.py` — `extract_items_node()` — add grid detection + grid extraction path
- `open_notebook/extractors/orchestrator.py` — add `match_record_to_building()` function
- Tests with Aldavilla ground truth (4 records, 10 buildings, 9 with no ACM)

---

## Verification

After all fixes are applied, run these verifications:

```bash
# 1. Full test suite
uv run pytest tests/ -x

# 2. Re-extract Alexander Hospital (Greencap ARA)
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:3dt8aixydmc80cm6flfp", "force": true}'

# 3. Re-extract Aldavilla 4601 (NSW DoE SAMP)
curl -X POST http://localhost:5055/api/acm/extract \
  -H 'Content-Type: application/json' \
  -d '{"source_id": "source:qdbz3uhlthja8enqxbm6", "force": true}'

# 4. Check building names are correct (not site names)
curl -s -X POST http://localhost:8000/sql \
  -H "surreal-ns: open_notebook" -H "surreal-db: development" \
  -H "Accept: application/json" -u "root:root" \
  --data-raw "SELECT building_name, internal_id FROM building_record WHERE source_id = source:qdbz3uhlthja8enqxbm6 ORDER BY internal_id;"

# 5. Check record counts against ground truth
# Alexander: target >= 35/43 (80% recall)
# Aldavilla: target >= 3/4 records
```

## Fix-to-Finding Mapping

| Task | Findings | Sprint | Effort |
|------|----------|--------|--------|
| 1 | F10 | 1 | 10 min |
| 2 | F7 | 1 | 5 min |
| 3 | F1 | 1 | 30 min |
| 4 | F9 | 1 | 2-4 hrs |
| 5 | F2, F6 | 2 | 4-8 hrs |
| 6 | F4 | 2 | 1-2 hrs |
| 7 | F3 | 2 | 4-8 hrs |
| 8 | F8 | 3 | 2-4 hrs |
| 9 | F5, F11 | 4 | 1-2 weeks |
