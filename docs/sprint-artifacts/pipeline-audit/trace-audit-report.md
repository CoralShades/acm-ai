# ACM Extraction Pipeline Trace Audit Report

**Date**: 2026-03-07
**Traces analyzed**: `676f94a068d4408dd6a06b71587a8467`, `c4fdb2a08a4c3a4acb0423ee11885367`
**Source**: `source:6z1w7desg87je2b6hkek`
**Model**: `qwen2.5:7b` (Ollama)
**Pipeline version**: E26+ (V3 two-phase extraction with SF-aligned prompts)

---

## 1. Execution Order Table

| # | Node | SystemMessage Size | HumanMessage Size | Output Quality | Duration |
|---|------|--------------------|-------------------|----------------|----------|
| 1 | metadata_extraction | 10,196 ch | 60 ch | Partial (some fields empty) | 5.7s |
| 2 | structure_extraction | **413,781 ch** | 73 ch | **HALLUCINATED** ("Sample Document" by "John Doe") | 25.9s |
| 3 | building_inventory | **413,979 ch** | 90 ch | **HALLUCINATED** (generic rooms "A1, B2, C3") | 27.6s |
| 4 | page_tagging | **413,090 ch** | 45 ch | **HALLUCINATED** (generic sections) | 8.7s |
| 5 | building_extraction #1 | **414,582 ch** | 55 ch | **HALLUCINATED** ("Central Park Tower", New York) | 5.7s |
| 6 | building_extraction #2 | **414,582 ch** | 55 ch | **EMPTY** (all fields blank) | 2.3s |
| 7 | item_extraction #1 | 59,373 ch | 55 ch | Partial — wrong picklist values | 39.5s |
| 8 | item_extraction #2 | 59,367 ch | 55 ch | Mixed | 43.2s |
| 9 | item_extraction #3 | 59,367 ch | 55 ch | Mixed | 88.4s |
| 10 | item_extraction #4 | 59,367 ch | 55 ch | Mixed | 156.7s |
| 11 | item_extraction #5 | 59,367 ch | 55 ch | Hit 32K token output limit | 312.1s |
| 12 | item_extraction #6 | 59,367 ch | 55 ch | Mixed | 455.8s |
| 13 | item_extraction #7 | 59,367 ch | 55 ch | Hit 32K token output limit | 734.2s |
| 14 | item_extraction #8 | 59,367 ch | 55 ch | Mixed | 969.1s |
| 15 | (duplicate Phase 1) | — | — | Duplicate of #5/#6 | — |
| 16 | correction #1 | 3,401 ch | 47 ch | Works: `"Good Condition"→"Stable"` | 19.6s |
| 17 | correction #2 | 3,127 ch | 47 ch | Works: `"material_condition"→"Stable"` | 1.4s |
| 18 | correction #3 | 3,127 ch | 47 ch | Works | 8.3s |
| 19 | correction #4 | 3,127 ch | 47 ch | Works | 112.7s |
| 20 | correction #5 | 3,127 ch | 47 ch | Works | 460.2s |

**Total pipeline time**: ~72 minutes (4286s)

---

## 2. Issue Catalog

### Issue 1: SystemMessage/HumanMessage Inversion (CRITICAL — Root Cause)

**Severity**: P0 — causes hallucinated outputs for all pre-extraction and building extraction calls

**Evidence**: Observations 2–6 all have SystemMessage > 413K chars. The entire document content is rendered into the Jinja2 template via `{{ content }}`, and the rendered string becomes the SystemMessage. The HumanMessage is a trivial one-liner (55–90 chars).

**Code pattern** (repeated in 6 files):
```python
system_prompt = prompter.render(data={"content": building_content, ...})
messages = [
    SystemMessage(content=system_prompt),       # 413K chars
    HumanMessage(content="Extract..."),          # 55 chars
]
```

**Impact**: qwen2.5:7b (8K default context, 32K max) cannot process 413K system prompts. It ignores the content entirely and outputs fictional data.

**Files affected**:
- `metadata_extractor.py:224` — `{{ cover_pages }}` in template
- `document_structure.py:133` — `{{ content }}` in template
- `building_inventory.py:491` — `{{ content }}` in template
- `page_tagger.py:336` — `{{ batch_pages }}` loop in template
- `orchestrator.py:762` — `{{ content }}` in v3_building_extraction template
- `orchestrator.py:848` — `{{ content }}` in v3_item_extraction template

---

### Issue 2: Duplicate Phase 1 LLM Call (HIGH)

**Severity**: P1 — wastes N additional LLM calls (one per building)

**Evidence**: `extract_items_node` at line 1370 re-calls `_v3_extract_building_meta()` for each building. The comment says "Phase 1 is cheap (small prompt)" but with 413K system prompts, it's neither cheap nor correct.

**Code**:
```python
# acm_extraction.py:1366-1375
# Re-run Phase 1 to get building_meta_result for picklist subsetting.
building_meta_result = await _v3_extract_building_meta(
    building_content=building_content,
    plan=plan,
    state=state,
    schema_bundle=schema_bundle,
)
```

**Fix**: Cache Phase 1 results in `ExtractionState` during `extract_building_node`, look up in `extract_items_node`.

---

### Issue 3: Content Embedded in Jinja Templates (HIGH)

**Severity**: P1 — architectural anti-pattern that causes Issue 1

**Evidence**: All 6 Jinja templates include a `{{ content }}` or `{{ cover_pages }}` or `{{ batch_pages }}` variable that renders the full (or partial) document into the template body. The rendered string becomes the SystemMessage.

**Templates affected**:
| Template | Variable | Typical Size |
|----------|----------|-------------|
| `metadata_extraction.jinja` | `{{ cover_pages }}` | ~8K chars |
| `structure_extraction.jinja` | `{{ content }}` | ~413K chars |
| `building_inventory.jinja` | `{{ content }}` | ~413K chars |
| `page_tagging.jinja` | `{{ batch_pages }}` loop | ~413K chars |
| `v3_building_extraction.jinja` | `{{ content }}` | ~414K chars |
| `v3_item_extraction.jinja` | `{{ content }}` | ~59K chars |

**Fix**: Remove content variables from templates. Pass content in HumanMessage from the caller.

---

### Issue 4: Four Sequential Pre-Extraction Calls with Full Document (MEDIUM)

**Severity**: P2 — inefficient but functional if message structure is fixed

**Evidence**: Observations 1–4 are sequential calls that each process the entire document. For a 400K-char document with a 7B model, this is wasteful even with correct message structure.

**Proposed fix (S4)**: Merge metadata+structure into call 1, keep inventory as call 2, drop page_tagging.

---

### Issue 5: No Building-Level Parallelization (MEDIUM)

**Severity**: P2 — buildings extracted sequentially

**Evidence**: Observations 7–14 (item extractions) run sequentially. For 8 buildings, total item extraction time is ~2800s. With parallelization (semaphore=3), expected time ~900s.

**Proposed fix (S5)**: `asyncio.gather()` with semaphore in `extract_items_node`.

---

### Issue 6: Logfire Trace Explosion (LOW)

**Severity**: P3 — noise in traces, no impact on extraction quality

**Evidence**: 19 out of 39 observations in the trace are Pydantic validation spans from Docling models (BoundingBox, TableCell). These are NOT ACM models.

**Status**: Already mitigated in commit `27bd2060` (removed `instrument_pydantic()`). S9 will add selective instrumentation.

---

### Issue 7: LLM Correction Loop Waste (MEDIUM)

**Severity**: P2 — 5 LLM calls to fix one trivial string mapping

**Evidence**: Observations 16–20 are correction loop calls that map `"Good Condition"→"Stable"`. The existing `normalize_enum_value()` function already handles this deterministically.

**Proposed fix (S7)**: Add dedicated `normalize_to_sf` node before validate. Remove LLM correction loop.

---

## 3. Prompt Analysis

### Message Structure Per Node

| Node | SystemMessage Content | HumanMessage Content |
|------|----------------------|---------------------|
| metadata_extraction | Instructions + `{{ cover_pages }}` (~8K) | "Extract the document metadata from the cover pages provided." |
| structure_extraction | Instructions + `{{ content }}` (~413K) | "Extract the document structure, table of contents, and section hierarchy." |
| building_inventory | Instructions + `{{ content }}` (~413K) | "Compile a building inventory with page ranges, room codes, and complexity classifications." |
| page_tagging | Instructions + `{{ batch_pages }}` loop (~413K) | "Classify each page into its document section." |
| v3_building_extraction | Instructions + picklists + `{{ content }}` (~414K) | "Extract the building metadata from the document header." |
| v3_item_extraction | Instructions + picklists + building_meta + `{{ content }}` (~59K) | "Extract all ACM item records from the building content." |

### Correct Structure (after S2 fix)

| Node | SystemMessage Content | HumanMessage Content |
|------|----------------------|---------------------|
| metadata_extraction | Instructions only (~2K) | Cover page text (~8K) |
| structure_extraction | Instructions only (~2.5K) | Full document content (~413K) |
| building_inventory | Instructions only (~3K) | Register section content (~413K) |
| page_tagging | Instructions only (~1.5K) | Batch of pages (variable) |
| v3_building_extraction | Instructions + picklists (~3K) | Building section content (variable) |
| v3_item_extraction | Instructions + picklists (~5K) | Building section content (variable) |

---

## 4. Root Cause Summary

The **root cause** of hallucinated outputs is the SystemMessage/HumanMessage inversion (Issue 1). When 413K characters of document content are rendered into the SystemMessage via Jinja templates, the qwen2.5:7b model cannot process it and outputs fictional data.

This is compounded by:
- Content being embedded in Jinja templates (Issue 3) — makes the anti-pattern implicit and hard to spot
- Duplicate Phase 1 calls (Issue 2) — doubles the hallucination surface
- No parallelization (Issue 5) — extends total pipeline time to 72 minutes

**Fix priority**:
1. **S2** (this session): Fix message structure — moves content to HumanMessage
2. **S3** (this session): Cache Phase 1 results — eliminates duplicate calls
3. **S4–S9** (future sessions): Merge pre-extraction, parallelize, add SF normalization
