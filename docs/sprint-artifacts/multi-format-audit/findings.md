# Findings: Multi-Format Extraction Pipeline Audit
Date: 2026-03-14

## What Was Discovered

### Critical Findings

**F1. Building names use site_name instead of inventory building name** (CRITICAL)
- `building_record.building_name` is set to the site/hospital name (e.g., "Alexander District Hospital", "Aldavilla Public School") for ALL buildings, instead of using the actual building name from `building_inventory` (e.g., "Myrtle Street Clinic", "Administration").
- **Affected sources**: Alexander (10/10 buildings wrong), Aldavilla (8/10 buildings wrong — only BLD007 "General Learning/Building Services" and BLD010 "Storage" got correct names)
- **File**: `open_notebook/graphs/acm_extraction.py` — `extract_building_node()` line ~618 — `_v3_extract_building_meta()` is called but the building_name stored to `building_record` doesn't use the inventory's `name` field
- **Impact**: Blocks correct building-level grouping in the frontend. Users see 10 buildings all named "Aldavilla Public School" instead of "Administration", "Pupil Facilities", "Library", etc.
- **Fix type**: Code change — when saving `BuildingRecord`, use `inventory_building.name` not the metadata site name

**F2. Alexander building inventory returns raw markdown table rows** (CRITICAL)
- The building inventory LLM returns entire markdown pipe-delimited rows as building names and IDs instead of extracting the building name
- Example: `building_id = "| Myrtle Street Clinic | Number of Levels: | 1 | 1 | | Survey Date: | 07-09-2020 |..."`
- Should be: `building_id = "B001"`, `name = "Myrtle Street Clinic"`
- **Root cause**: Greencap ARA format has per-building sections with a header row containing building name, levels, survey date. The LLM prompt doesn't handle this table-within-text format.
- **File**: `prompts/acm/building_inventory.jinja` — prompt doesn't specify how to handle building headers embedded in markdown tables
- **Impact**: 10 buildings detected instead of 5; building names are garbage; page ranges are all page 1 (wrong)

**F3. Alexander total_pages=4 but PDF is 24 pages** (CRITICAL)
- The pipeline thinks Alexander PDF is only 4 pages. Extraction only processed pages 1-4, missing pages 5-24 which contain ALL the ACM register data.
- **Root cause**: Page count comes from `_extract_total_pages()` which counts page markers in `source.full_text`. If the Docling/PyMuPDF extraction only produced content for pages 1-4 (header pages), the rest would be missed.
- **File**: `open_notebook/graphs/acm_extraction.py` — `_extract_total_pages()` and the initial page tagging
- **Impact**: 0/43 records extracted (100% miss rate)

**F4. Consultant detected as `<!-- image -->` for Alexander** (HIGH)
- The metadata extraction LLM returned `<!-- image -->` as the consultant name instead of "Greencap Pty Ltd"
- The Greencap PDF has the consultant name in an image/logo, not in text
- **File**: `open_notebook/extractors/metadata_and_structure.py` / `prompts/acm/metadata_and_structure.jinja`
- **Impact**: Wrong consultant name in metadata; may affect downstream extraction strategy

**F5. Aldavilla page ranges not differentiated per building** (HIGH)
- All 10 buildings have the same page range (3-15 for B001-B009, 14-15 for B010)
- This means EVERY building gets ALL tables, leading to cross-building contamination in per-row extraction
- The SAMP format has a building summary grid where all buildings are listed in a table on the same pages, not in separate sections
- **File**: `prompts/acm/building_inventory.jinja` — prompt assumes each building has its own page range
- **Impact**: Each building extracts ALL items instead of its own; expect many duplicates or incorrect building assignments

**F6. 3980 building count discrepancy: 20 in structure → 1 in inventory** (HIGH)
- `metadata_and_structure_node` found 20 building_ids (B00A through B00W) but `building_inventory` collapsed them to just 1 building ("General Learning", B00L)
- **Root cause**: The building inventory LLM may not understand the SAMP building grid format and picked only one building
- **Impact**: 19/20 buildings missed, all ACM items assigned to 1 building

**F7. Default extraction model is phi4:14b instead of llama3.1:8b** (MEDIUM)
- `ACM_EXTRACTION_MODEL` not set in `.env`, so the pipeline uses the DB default extraction model: `phi4:14b-q4_K_M`
- phi4 at 14B is ~4x slower than llama3.1:8b for per-row extraction
- Per-row extraction with 10 buildings × many rows × phi4 takes 60+ minutes vs ~15 min with llama3.1
- **Fix**: Add `ACM_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0` to `.env`

**F8. Extraction pipeline hangs with concurrent command execution** (HIGH)
- When 2+ acm_extract commands run concurrently in the same worker, the extract_items_node hangs indefinitely
- Aldavilla and 3980 extraction both stuck for 40+ minutes after "Building extraction: 10/10 saved" — no item extraction started, Ollama idle
- The worker process (PID 300664) is alive but not making LLM calls
- **Root cause hypothesis**: `asyncio.gather` in `extract_items_node` + concurrent graph invocations may create a deadlock or resource starvation in the shared event loop
- **File**: `open_notebook/graphs/acm_extraction.py:1197` — `asyncio.gather(*[_extract_items_for_building(b) for b in inventory.buildings])`
- **Impact**: Multi-source extraction batches fail silently — commands stay "running" forever
- **Fix type**: Code change — either (a) serialize command processing in the worker, or (b) add a timeout to graph invocations

**F9. Column aliases in row_segmenter.py are Clutch-format specific** (HIGH)
- `COLUMN_ALIASES` dict (line 26-51) only covers Clutch/Broadmeadows column headers
- Missing Greencap ARA headers: "Item No.", "Building Element", "Material Type", "ACM Status", "Risk Rating"
- Missing NSW DoE SAMP headers: "Location Description" (fuzzy match ~0.65 Jaro-Winkler, below 0.70 threshold)
- No canonical for `item_number` field — Greencap/NSW DoE both have this as a distinct identifier
- **File**: `open_notebook/extractors/row_segmenter.py:26-51`
- **Impact**: Columns from non-Clutch formats fall through to opaque `col_0`, `col_1` keys, degrading per-row extraction accuracy
- **Fix type**: Config change — add aliases for Greencap and NSW DoE column headers

**F10. BuildingRecord.building_name missing fallback to inventory name** (HIGH)
- Normal path at `acm_extraction.py:675-679` stores `result.building_name` from Phase 1 LLM without fallback
- Minimal record path at `acm_extraction.py:633-638` correctly uses `building_meta_entry.name` as fallback
- When Phase 1 LLM returns site name (e.g., "Aldavilla Public School") instead of building name, BuildingRecord gets wrong name
- **File**: `open_notebook/graphs/acm_extraction.py:675-679`
- **Fix**: Add `building_name=result.building_name or building_meta_entry.name`

**F11. SAMP grid format causes N×M record duplication** (CRITICAL — architectural)
- When all buildings share the same page range (e.g., 3-15), `_get_docling_tables()` returns identical table set for every building
- Each building's per-row extraction processes ALL tables from ALL buildings
- Result: N buildings × M total items = N×M output records (10× duplication for Aldavilla)
- **File**: `open_notebook/extractors/orchestrator.py:54-60` — page-only query filter
- **No per-building discriminator exists** — only page range filtering, which is identical for all buildings
- **Fix type**: Architecture change — need building-level table assignment or content-based discrimination

### Positive Findings

**P1. Aldavilla building count correct** (10/10 detected)
**P2. Aldavilla building inventory has correct names** — "Administration", "Special Purpose", etc. (the bug is in how they're stored to building_record, not in the inventory itself)
**P3. Aldavilla B009 rooms correctly identified** — 8 rooms matching ground truth
**P4. docling_document_json populated for Aldavilla (5/5) and 3980 (25/25 after force re-extraction)**
**P5. 3980 Docling re-extraction worked** — force=true correctly detected stale tables (missing JSON), deleted them, and re-ran Docling to populate JSON

## Format Compatibility Matrix

| Capability | Broadmeadows (Clutch) | Alexander (Greencap) | Aldavilla (NSW DoE) | 3980 (Unknown) |
|------------|----------------------|---------------------|--------------------|--------------------|
| Building detection | 1/1 ✅ | 10/5 ❌ (too many) | 10/10 ✅ | 1/? ❌ (only 1 of 20) |
| Building names correct | ✅ | ❌ (raw markdown rows) | ❌ (site name used) | ❌ (site name used) |
| Page range assignment | ✅ | ❌ (all page 1) | ❌ (all 3-15, same) | ⚠️ (1-36, entire doc) |
| Table extraction (Docling) | ✅ (9 tables) | ❌ (0 tables, page 1-4 only) | ✅ (5 tables) | ✅ (25 tables) |
| docling_document_json | ✅ (8/9) | ❌ (0/0, no tables) | ✅ (5/5) | ✅ (25/25) |
| Per-row extraction | ✅ | ❌ (no tables) | ⏳ (running, phi4 slow) | ⏳ (running, phi4 slow) |
| Field mapping | ✅ | N/A | ⏳ | ⏳ |
| Records vs ground truth | 33/31 ✅ | 0/43 ❌ | ⏳/4 | N/A |
| sample_no match rate | N/A | N/A | ⏳/4 | N/A |

Legend: ✅ Pass | ❌ Fail | ⚠️ Partial | ⏳ Pending (extraction still running)

## Per-Format Gap Analysis

### Alexander Hospital (Greencap ARA)

**Summary**: Complete extraction failure. 0/43 records, 10 buildings detected instead of 5, all with garbage names.

**Root causes (in pipeline order):**

1. **Metadata extraction** (`metadata_and_structure.jinja`):
   - Consultant detected as `<!-- image -->` (image-based logo, not text)
   - Document type: "Unknown" (should be ARA)
   - `register_start`: null (can't find where ACM tables begin)

2. **Building inventory** (`building_inventory.jinja`):
   - Returns 10 buildings instead of 5 (Greencap truth: Myrtle Street Clinic, Mortuary Buildings, Pathology Dept, VMO Accommodations, Old Alexandra Hospital)
   - Building names are raw markdown table rows, not extracted names
   - All page ranges are page 1 (should span pages 5-24)
   - "Main Hospital Building" appears 5 times as separate buildings (should be 1: "Old Alexandra Hospital")

3. **Page calculation** (`_extract_total_pages()`):
   - total_pages = 4 (actual: 24 pages)
   - register_range = (1, 4) — misses pages 5-24 entirely

4. **Docling extraction**: Only processed pages 1-4 → 0 tables extracted (previous run had 17 tables because it used the full document)

5. **Per-row extraction**: Never ran (0 tables → 0 rows → 0 records)

**Greencap format characteristics that break the pipeline:**
- Portrait layout with per-building sections (not a single landscape register table)
- Building names in table headers, not in a separate building list
- Consultant name in image/logo, not text
- Each building section has its own risk assessment table

### Aldavilla 4601 (NSW DoE SAMP)

**Summary**: Extraction in progress. 10 buildings correctly detected but names stored as site name. All page ranges identical (3-15). docling_document_json populated.

**Root causes:**

1. **Building names** (`extract_building_node` → `building_record` save):
   - Inventory correctly identifies building names (Administration, Pupil Facilities, Library, etc.)
   - But `building_record.building_name` stores "Aldavilla Public School" for 8/10 buildings
   - Root cause: `_v3_extract_building_meta()` returns site name, not inventory building name

2. **Page ranges** (all buildings get pages 3-15):
   - SAMP format lists buildings in a shared summary grid on pages 3-15
   - Individual buildings don't have dedicated page ranges
   - This causes every building to match ALL tables → potential cross-building contamination

3. **"No Asbestos" handling**: TBD (depends on extraction results)
   - Ground truth: 9 buildings have "No Asbestos", only B009 "Special Purpose" has 4 ACM items
   - Need to verify if pipeline creates phantom records for no-ACM buildings

### 3980 Register (Unknown)

**Summary**: Extraction in progress. Only 1 of 20 buildings detected. 25 tables with docling JSON populated.

**Root causes:**

1. **Building count**: `metadata_and_structure_node` found 20 building_ids but building_inventory collapsed to 1 ("General Learning")
   - The LLM couldn't parse the building grid format

2. **Metadata quality**: consultant=Unknown, site_name=missing, site_address contains raw text
   - Very poor metadata extraction quality

3. **No ground truth**: Cannot measure recall/precision. This is a diagnostic-only source.

## Decisions Made

1. **Extractions left running** — using phi4:14b (slow but will produce results for analysis)
2. **Alexander extraction failure is a pipeline issue**, not a data issue — the PDF has valid data but the pipeline can't handle the Greencap ARA format

## Fix Recommendations

### Priority 1: Building Name Bug (F1) — Code Change

**File**: `open_notebook/graphs/acm_extraction.py` — `extract_building_node()` ~line 618
**Fix**: When saving `BuildingRecord`, use `building_inventory_entry.name` for `building_name` instead of the metadata site name.
**Impact**: Fixes Aldavilla (8/10 buildings), 3980 (1 building), and future multi-building extractions.
**Effort**: Small (1-2 hours)

### Priority 2: Building Inventory Prompt (F2) — Prompt Tuning

**File**: `prompts/acm/building_inventory.jinja`
**Fix**: Add format-specific instructions for:
- Greencap ARA: "Look for building sections with headers like 'Building Name: X'. Extract just the building name, not the entire table row."
- NSW DoE SAMP: "Buildings may be listed in a summary grid. Extract each building as a separate entry with its building_id (e.g., B001)."
**Impact**: Fixes Alexander (building count and names), 3980 (building count)
**Effort**: Medium (4-8 hours, needs testing across formats)

### Priority 3: Page Count / Range Fix (F3) — Code + Prompt

**File**: `open_notebook/graphs/acm_extraction.py` — `_extract_total_pages()` and `metadata_and_structure_node`
**Fix**: Don't rely solely on page markers in text. Use the source PDF page count (available from Docling) as the authoritative total_pages.
**Impact**: Fixes Alexander (4 → 24 pages) and any other source with sparse page markers
**Effort**: Medium (4-8 hours)

### Priority 4: Add ACM_EXTRACTION_MODEL to .env (F7) — Config

**Fix**: Add `ACM_EXTRACTION_MODEL=llama3.1:8b-instruct-q8_0` to `.env`
**Impact**: 4x faster per-row extraction
**Effort**: Trivial (5 minutes)

### Priority 5: Add Column Aliases for New Formats (F9) — Config

**File**: `open_notebook/extractors/row_segmenter.py:26-51`
**Fix**: Add aliases:
- `room_location`: add "Location Description"
- `item_description`: add "Building Element", "Material Type"
- `sample_number`: add "Item No."
- New canonical `item_number` for item identifiers
- New canonical `risk_rating` for "Risk Rating", "Priority"
- New canonical `acm_status` for "ACM Status", "Assumed/Confirmed"
**Impact**: Enables per-row extraction for Greencap ARA and NSW DoE SAMP formats
**Effort**: Small (2-4 hours)

### Priority 6: BuildingRecord Name Fallback (F10) — Code Change

**File**: `open_notebook/graphs/acm_extraction.py:675-679`
**Fix**: `building_name=result.building_name or building_meta_entry.name`
**Impact**: Ensures building names always come from inventory when Phase 1 LLM returns site name
**Effort**: Trivial (10 minutes)

### Priority 7: Concurrent Extraction Hang (F8) — Code Change

**File**: `commands/acm_commands.py` or worker configuration
**Fix**: Either serialize acm_extract command processing (one at a time) or add timeouts to graph invocations
**Impact**: Prevents stuck extractions when multiple sources are extracted simultaneously
**Effort**: Small-Medium (4-8 hours)

### Priority 8: Shared Page Range / N×M Duplication (F5, F11) — Architecture

**Issue**: When all buildings share the same page range, each building gets ALL tables → N×M duplication
**Fix**: Either:
- (a) Parse table content to identify which building each row belongs to (e.g., match room IDs to building inventory)
- (b) Create an alternative "grid extraction" path for SAMP format that processes the shared table once and distributes records to buildings by building_id column
- (c) Post-extraction deduplication by matching records to buildings using room/item metadata
**Impact**: Required for any SAMP-format PDF where buildings share pages
**Effort**: Large (1-2 sprints)

## Code-Level Gap Summary (from subagent audit)

| Gap | File:Line | Severity | Formats Affected |
|-----|-----------|----------|------------------|
| Missing column aliases | `row_segmenter.py:26-51` | HIGH | Greencap, NSW DoE |
| Document type misclassification | `metadata_and_structure.jinja:24-31` | MEDIUM | NSW DoE |
| Identical page ranges for all buildings | `building_inventory.jinja:9-14, 24-26` | CRITICAL | NSW DoE SAMP |
| Sample number field assumes lab ID | `row_extraction.jinja:15` | HIGH | Greencap, NSW DoE |
| BuildingRecord name no fallback | `acm_extraction.py:675-679` | HIGH | NSW DoE, sparse ARA |
| Page-only table filter (no building discriminator) | `orchestrator.py:54-60` | CRITICAL | NSW DoE SAMP |

**Common Root Cause**: The entire per-building extraction architecture assumes buildings occupy distinct, non-overlapping page ranges. NSW DoE SAMP with multi-building grid tables on shared pages violates this assumption, causing cascading failures from prompt → data access → record creation.
