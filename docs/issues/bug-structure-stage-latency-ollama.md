# STRUCTURE Stage 148-208s Latency on Ollama (N8)

> **Discovered**: 2026-03-12 (Bug Fix 11 live extraction verification)
> **Source**: acm-extraction.log 03:33, 09:01; LangSmith trace `eed83b6e`
> **Priority**: P2
> **Status**: Partially resolved — commit `476c285e` (2026-03-14)
> **Blocks**: Pipeline performance on Ollama; metadata quality for consultant and building detection

## Problem

The `metadata_and_structure` stage takes 148-208 seconds on Ollama (llama3.1:8b) for 27-page documents, producing poor quality output (`consultant=Unknown`, `document_type=Unknown`, empty `sections[]`, empty `building_ids[]`). Comparable documents processed with the same model at other times take ~20 seconds.

LangSmith trace analysis (trace `eed83b6e`, L2 finding) confirms:
- `metadata_and_structure` node: 136.8s (40% of total 343.9s pipeline)
- 12,044 tokens (11,409 prompt, 635 completion)
- Output quality: `consultant_name="Unknown"`, `document_type="Unknown"`, `toc_present=false`
- The `inventory` node (10.9s) and `extract_building` node (5.9s) correctly identified the consultant and building from the same document — suggesting the metadata prompt is the issue, not the model.

## Evidence

- `acm-extraction.log` 03:33-03:37: STRUCTURE took 208 seconds for `l6xcf7tlv78bo3vrdeqj`
- `acm-extraction.log` 09:01-09:04: STRUCTURE took 148 seconds for `8u2ht8upok65bcz7vvd3`
- Both produced `consultant=Unknown, register_start=None, buildings=0`
- LangSmith trace `eed83b6e`: 135.7s for ChatOllama call with 11k prompt tokens
- Compare: Broadmead.pdf at 01:27 took ~20s for STRUCTURE with same model

## Impact

- 40% of pipeline wall time wasted on a stage that produces garbage output
- Poor metadata cascades: `consultant=Unknown` means no consultant-specific parsing
- `register_start=None` means the pipeline can't skip non-register pages

## Fix Approach

1. Investigate prompt size — 11,409 prompt tokens may be too large for llama3.1:8b's effective context
2. Consider truncating document content for metadata extraction (first 5 pages + TOC should suffice)
3. Increase `OLLAMA_NUM_CTX` for the metadata stage specifically
4. Add timeout guard: if STRUCTURE takes >60s, log warning and consider using inventory results as fallback

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add content truncation for metadata extraction prompt |
| `prompts/acm/` | Review metadata extraction prompt for efficiency |

## Partial Resolution (2026-03-14)

Commit `476c285e` applied fixes addressing items 1 and partly 3:

- **`prompts/acm/metadata_and_structure.jinja`**: Rewritten from 141 → 56 lines (removes verbose field descriptions, retains JSON schema + key rules). Reduces system prompt token count significantly.
- **`prompts/acm/building_inventory.jinja`**: Rewritten from 130 → 58 lines for the same reason.
- **`open_notebook/extractors/metadata_and_structure.py`** + **`building_inventory.py`**: Added `_apply_ollama_extraction_settings(model)` after model provisioning to enforce `format="json"`. This resolves the primary quality failure (`consultant=Unknown`, empty sections).

Verification result on Broadmeadows: STRUCTURE stage now returns valid metadata (building detected, consultant partially resolved via phi4:14b). Execution time was 203s total (not broken out per-stage post-fix).

**Remaining**: Items 2 (content truncation to first N pages) and 4 (timeout guard) are not yet implemented. Content truncation would further reduce latency for large documents.
