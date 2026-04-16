# Pipeline Audit Findings

## Root Causes (ordered by impact)

### RC-1: CRITICAL — Building page_end capped at +2 pages (LLM path)

**File:** `open_notebook/extractors/building_inventory.py:830-842`
**Impact:** Loss of 15-20 records (PRIMARY cause of 31->10)
**Evidence:** 
- LLM path: `_PAGE_END_EXPANSION_MARGIN = 2` → `expanded_end = min(current_end + 2, total)`
- Heuristic path: `buildings[0].page_end = total` (correct, at line 618-627)
- Both paths handle single-building docs, but the LLM path is used when the LLM succeeds

**Why it matters:** If LLM says Broadmeadows register ends at page 12 but it actually runs to page 18:
- LLM path gives page_end=14 (12+2) → pages 15-18 completely excluded
- All records on excluded pages are silently dropped
- `_extract_building_content()` and `_get_docling_tables()` both use page_end as filter

**Fix:** Change line 830-842 to match heuristic behavior: `bld.page_end = total`

---

### RC-2: HIGH — Heuristic cross-validation cannot extend existing building page ranges

**File:** `open_notebook/extractors/building_inventory.py:846-867`
**Impact:** Prevents self-healing when RC-1 underestimates

**Evidence:** Cross-validation only adds NEW buildings:
```python
if h_id_lower not in llm_ids and h_name_lower not in llm_names:
    inventory.buildings.append(h_building)  # Only adds, never extends
```

For single-building docs, heuristic finds same building with page_end=total_pages, but duplicate check prevents merging. LLM's truncated page_end persists.

**Fix:** After cross-validation, compare and use wider page range.

---

### RC-3: MEDIUM — Silent table rejection by _is_acm_table()

**File:** `open_notebook/extractors/row_segmenter.py:151-184, 759`
**Impact:** 0-5 records lost

**Evidence:** `_is_acm_table()` requires `item_description` fuzzy match from headers. Unrecognized headers (e.g., "ACM Description", "Suspected Material") cause table rejection. Mitigated by all-tables fallback when ALL fail (line 760-768), but partial failures are silent.

**Fix:** Add per-table rejection logging + expand COLUMN_ALIASES.

---

### RC-4: MEDIUM — Docling TableFormer misses small table fragments

**File:** `commands/source_commands.py:211-222`
**Impact:** 2 records (page 8 known issue)

**Evidence:** Gap detection warning exists but doesn't recover rows. `recover_no_access_node` (acm_extraction.py:2178) partially addresses this for No Access/Not Sampled patterns only.

---

### RC-5: LOW — Content truncation for metadata extraction

**File:** `open_notebook/graphs/acm_extraction.py:356-359`
**Impact:** Cascading effect on register_start_page accuracy

**Evidence:** `_METADATA_MAX_CHARS = 15_000` limits to ~5 pages. If register header not in first 5 pages, register_start_page could be wrong.

---

## Agent Report Summaries

### Pre-Extraction Agent (PEA findings)
- PEA-1 CRITICAL: _extract_building_content page marker matching issues
- PEA-2 CRITICAL: page_end +2 cap (= RC-1)
- PEA-3 HIGH: _trim_to_register clips front pages when register_start_page wrong
- PEA-4 HIGH: Page tags derive solely from inventory page ranges
- PEA-5 MEDIUM: Docling table page range gate mirrors building.page_end

### Row Segmenter Agent (RSA findings)
- RSA-1 CRITICAL: _is_acm_table() drops tables lacking item_description mapping (= RC-3)
- RSA-2 CRITICAL: Type H join discards duplicate-key rows
- RSA-3 HIGH: 50% header threshold misclassifies data rows
- RSA-4 HIGH: Single-cell full-width rows always skipped
- RSA-5 MEDIUM: "continued" in FOOTER_INDICATORS
- RSA-6 MEDIUM: Unmapped columns cause table rejection

### Worker Handoff Agent
- NO auto-chaining from process_source -> acm_extract
- Frontend explicitly triggers via POST /api/acm/extract
- 10 records confirm acm_extract DID fire (not handoff issue)

## Pipeline Architecture Map

```
process_source command:
  source_graph (PyMuPDF text) → Docling Direct API (tables) → acm_table_section DB

acm_extract command (manual trigger):
  metadata_and_structure (1 LLM) → inventory (1 LLM) → save_intelligence
  → schema_inference (1 LLM) → extract_building (N LLM) → extract_items (N LLM)
  → normalize_to_sf → validate → correct (conditional) → deduplicate
  → recover_no_access → save → acm_record DB
```

### RC-6: HIGH — total_pages derived from truncated content

**File:** `open_notebook/graphs/acm_extraction.py:356-365`
**Impact:** page_end capped at ~10 instead of 19 for 18-page documents

**Evidence:** `metadata_and_structure_node` truncates content to 15K chars for the LLM prompt. But `extract_metadata_and_structure()` calls `_extract_total_pages()` on this truncated content, finding only pages 1-10 in the first ~5 pages. `document_structure.total_pages` is set to 10. The RC-1 fix then expands page_end to 10 (not 19), losing pages 11-18.

**Why:** The first gemma4:latest run happened to work because cross-validation (RC-2 fix) extended the range. But gemma4:31b gave a different building inventory that didn't trigger the extension.

**Fix applied:** After calling `extract_metadata_and_structure()` with truncated content, re-count total_pages from the FULL text and correct the structure. Committed `f24132c4`.

---

### RC-7: HIGH — recover_no_access_node skips when per_row_actually_ran

**File:** `open_notebook/graphs/acm_extraction.py:2708`
**Impact:** 2 No Access records lost on pages without Docling tables

**Evidence:** `recover_no_access_node` returns early when `per_row_actually_ran=True`:
```python
if state.get("per_row_actually_ran"):
    return state  # Skips text-based No Access recovery entirely
```
The per-row path processes Docling table rows and calls `scan_text_for_synthetics()` on `building_content`. While `scan_text_for_synthetics` has Type F2 patterns that SHOULD catch "No access at the time of the Assessment" and "No access due to locked door", the resulting synthetic rows go through per-row LLM extraction which may produce poor results (garbage room_name, null sample_result). The dedicated `_recover_no_access_records()` function produces cleaner No Access records but is never called.

**Fix:** Remove the early return. `_recover_no_access_records()` already deduplicates against existing records, so running it after per-row extraction is safe.

---

### RC-8: MEDIUM — Row segmenter drops ~6 entries from Docling tables

**File:** `open_notebook/extractors/row_segmenter.py` (segment_multiple_tables)
**Impact:** ~6 records lost from pages 5-7

**Evidence:** Raw text shows ~30 register entries on pages 5-7, but Docling produced only 24 segmented rows. Possible causes:
- Docling TableFormer merges multi-line cells, reducing apparent row count
- Row segmenter classifies some data rows as headers/footers (RSA-3: 50% header threshold)
- Row segmenter skips single-cell full-width rows (RSA-4)
- "continued" in FOOTER_INDICATORS drops continuation rows (RSA-5)

**Fix needed:** Investigate which entries are missing from Docling tables, add text-based recovery fallback.

---

## Production Test Results (2026-04-16)

### Broadmeadows — gemma4:latest on RTX 5090
| Metric | Before Fix | After Fix | Target |
|--------|-----------|-----------|--------|
| Records | 10 | **23** | 31 |
| Accuracy | 32% | **74%** | 100% |
| Time | ~45s | 250s | <60s |
| Confidence | unknown | 19 med + 4 low | all high |
| product filled | unknown | **20/23** | 23/23 |

> **CORRECTION (session 2):** Previous session reported "item_name=null" but the `acm_record` table
> has no `item_name` column. The actual field is `product` (mapped from `ACMItemRow.item_name`).
> 17 medium-confidence records have good product values (e.g., "Vinyl sheet (cream)", "Fibre cement sheet").
> 3 fallback records have "Unknown", 1 has literal string "null", 2 have partial data.

**Root cause validation:**
- RC-1 fix confirmed: page range now covers pages 5-18 (was capped at +2)
- RC-2 fix confirmed: cross-validation extended B001 range [13-18] → [5-18]
- RC-3 logging confirmed: 3 table rejections on pages 11-13 now visible

**Remaining gaps (corrected):**
1. **~8 records missing** — 2 No Access entries on page 8 (Docling gap) + ~6 entries from pages 5-7 lost at row segmentation
2. **Page 8 No Access recovery**: `recover_no_access_node` skips when `per_row_actually_ran=True` (RC-7)
3. **6 low-confidence records**: 3 fallback "Unknown", 1 literal "null", 1 concatenated garbage, 1 missing room
4. **250s/645s extraction time** — per-row serial LLM calls are the bottleneck
5. **Pages 9-13 are NOT register data** — lab analysis reports, correctly excluded

### Broadmeadows — gemma4:31b on RTX 5090 (final, post-RC-6)
| Metric | Result | Target |
|--------|--------|--------|
| Records | **23** | 31 |
| Time | 645s (10m 45s) | <60s |
| Confidence | 17 med + 6 low | all high |
| Page range | [5-19] ✓ | [5-19] |
| product filled (medium) | **17/17** ✓ | 17/17 |
| product filled (low) | 3/6 (partial) | 6/6 |

**Detailed product field analysis (23 records):**
- 17 medium: "Vinyl sheet", "mastic (grey)", "Fibre cement sheet", "Fuses", "Hessian back sheet vinyl (dark grey)", etc. — **GOOD quality**
- 1 medium: `product: "null"` (literal string) — LLM returned string "null" for item_name
- 6 low: 3× "Unknown" (fallback), "Flange mastic (brown)" (good), "Vinyl sheet (beige)" (good), 1× concatenated garbage

**Ground truth page analysis:**
- Pages 5-7: ~30 register entries in text, 24 rows in Docling tables, ~6 lost at segmentation
- Page 8: 2 "No Access" entries, no Docling table detected
- Pages 9-10: Lab analysis cover/letter (NOT register data)
- Pages 11-12: Lab sample results table (NOT register data)
- Page 13+: Assessment report text (NOT register data)

### Broadmeadows — gemma4:31b on RTX 5090 (Run #4, post-RC-7+RC-8)
| Metric | Run #3 | Run #4 | Target |
|--------|--------|--------|--------|
| Records | 23 | **36** | 31 |
| Rows segmented | 24 | **34** | - |
| Time | 645s | 907s (15m 7s) | <60s |
| Confidence | 17 med + 6 low | **24 med + 12 low** | all high |
| product filled (medium) | 17/17 | **23/24** | 24/24 |
| product filled (low) | 3/6 | 7/12 | 12/12 |

**RC-8 confirmed:** 34 rows segmented from 3 Docling tables (up from 24) — column-count coalescing merged 18/18/19-col tables into single Type B group.

**RC-7 confirmed:** 3 "Not Sampled" records recovered (Lift Foyer, Ceiling Space, Main Foyer) — text-based No Access scan ran despite per_row_actually_ran=True.

**Dedup issues found:**
1. Fibre cement sheet in East roof fan room: sample_no "34511-039- 016" vs "34511-039-016" (whitespace near dash) → not deduplicated
2. Low-confidence fallback records with null room_id not merged with medium records having room_id

**True unique count after manual dedup: ~33-34 records (vs 31 ground truth)**

**Data quality breakdown (36 records):**
- 24 medium: 23 with good product + room + sample data, 1 with literal "null" product
- 12 low: 5× "Unknown" (fallback), 3 with "Not Sampled" (No Access), 2 with good product, 1 garbage concatenation, 1 partial

**Fix applied:** RC-9 — strip spaces around dashes in sample_no for dedup key (acm_extraction.py:254)

---

### RC-9: LOW — Dedup key sample_no whitespace near dashes

**File:** `open_notebook/graphs/acm_extraction.py:254`
**Impact:** 1 duplicate record not caught

**Evidence:** OCR produces "34511-039- 016" vs "34511-039-016". The `split()+join()` normalization preserves spaces adjacent to dashes.

**Fix:** `re.sub(r"\s*-\s*", "-", sample)` after whitespace normalization.

---

### RC-10: HIGH — Ollama format="json" allows free-form JSON (no schema enforcement)

**File:** `open_notebook/graphs/utils.py:273`, `open_notebook/graphs/acm_extraction.py:1266`
**Impact:** 29% per-row extraction failure rate with gemma4:31b (10/34 rows in Run #4)

**Evidence:** `_apply_ollama_extraction_settings()` sets `format="json"` which tells Ollama "output valid JSON" but doesn't constrain the structure. gemma4:31b frequently produces non-JSON output or JSON with wrong structure, causing `parse_json_response()` to raise `ValueError("No JSON object found")`.

**Root cause:** Ollama supports `format=<json_schema_dict>` which uses grammar-constrained generation to guarantee output matches the schema. This was available since Ollama 0.5.0 but never wired into the pipeline.

**Fix:** Pass `ACMItemRow.model_json_schema()` to `format` parameter:
- `_apply_ollama_extraction_settings()` accepts optional `schema_dict`
- `_inject_response_format()` passes schema through for Ollama
- `extract_items_node` sets schema on per-row model
- Tested: gemma4:31b on RunPod → valid JSON, all 16 fields, `anyOf` works

**Expected impact:** 0% parse failure rate (grammar constrains every token)

**Run #6 result (RC-10, schema with required item_name):** Same 29% failure rate (10/34). All failures returned `raw_response_preview=<empty>` — the grammar sampler deadlocked when it couldn't produce a required item_name value. The `required: ["item_name"]` constraint prevented the sampler from emitting ANY valid JSON.

**RC-10b fix (commit 23d2a05a):** Made `item_name: Optional[str]` and removed `required` from the schema passed to Ollama. Run #7: same 10/34 failures — required fields weren't the issue.

**RC-10c fix (commit 469959f2):** Replaced full Pydantic schema (3369 chars, 16 `anyOf` patterns, `title`/`description`/`default`) with minimal schema (625 chars, just `{type: "string"}` per property). Run #8: **6/34 failures (18%)** — 4 fewer failures. The simpler grammar prevents sampler deadlock. Failed rows shifted to 27, 29, 31-34 (end of first table + all of second table).

**Root cause confirmed:** Ollama's grammar compiler generates EBNF from the JSON schema. Complex `anyOf` patterns (16 instances of `[{type: "string"}, {type: "null"}]`) produce a grammar too large for the sampler to navigate reliably. Minimal `{type: "string"}` per property generates a small, efficient grammar.

**Trade-off:** Model produces literal "null" strings instead of JSON null (grammar only allows strings). Needs post-processing cleanup.

---

### RC-10d/e: HIGH — Empty Ollama responses at temperature=0 (deterministic degeneration)

**File:** `open_notebook/extractors/row_extractor.py:130-207`
**Impact:** 29-87% failure rate depending on document complexity (10/34 Broadmeadows, ~80/102 Alexander)

**Evidence (RC-10d):** Hybrid retry (schema grammar → format="json") produced IDENTICAL empty responses for the same rows. Both attempt 1 and attempt 2 returned `raw_response_preview=<empty>` with HTTP 200 and ~14.5s processing time. Ollama processes the input but the model generates 0 content tokens.

**Root cause confirmed:** With `temperature=0`, gemma4:31b deterministically picks the same degenerate first token (stop/EOS) for certain row inputs. Direct Ollama API calls with the SAME format and row data SUCCEED (47-87 tokens) — the difference is that direct API tests don't use `temperature=0`. The ChatOllama pipeline defaults to `temperature=0` which makes the failure deterministic and reproducible across retries.

**RC-10d (commit 51e50a1a):** Hybrid retry (schema→json format switch) — INEFFECTIVE. Alexander Run #10: B001=50%, B002=80%, B003=88%, B004=50% failure rate. Format switch alone doesn't break the deterministic path.

**RC-10e fix (commit 482eaa0b):** On retry, bump `temperature=0` → `temperature=0.3` alongside format="json". The small temperature introduces enough randomness to break the deterministic degenerate token selection. Also restores original format+temperature in `finally` block so subsequent rows get schema grammar at temperature=0.

**Expected impact:** Reduce failure rate from 29% to <10% on Broadmeadows, from ~87% to <30% on Alexander (first attempt still fails, retry with temp=0.3 should succeed for most rows).

---

### RC-11: MEDIUM — Concurrent extraction overwhelms single-GPU Ollama

**Impact:** 100% failure rate when running 2+ extractions concurrently

**Evidence:** Run #5 with Broadmeadows + Alexander concurrent (4+ extraction loops) → zero successful rows. Ollama serializes CUDA compute but KV cache thrashing between 4+ conversations degrades output quality to non-JSON.

**Fix:** Set `ACM_MAX_CONCURRENT_BUILDINGS=1` in `.env` for Ollama deployments. Or run extractions sequentially (not concurrent sources).

---

### RC-12: CRITICAL — gemma4 family has systemic structured output defect (CONFIRMED UPSTREAM)

**Upstream issues:**
- ollama/ollama#15502 — gemma4:31b repetition loop in constrained JSON with free-text strings
- ollama/ollama#15260 — think=false breaks format constraint for gemma4
- ollama/ollama#15428 — gemma4:26b empty response on long system prompts
- google-deepmind/gemma#622 — model-level token repetition tendency (filed by #15502 author)

**Impact:** 29-87% per-row extraction failure depending on document complexity

**Evidence (from #15502, 39 trials across 13 test configurations):**
- Three conditions ALL required to trigger: (1) gemma4:31b, (2) format= with JSON schema, (3) free-text string fields
- gemma3:27b does NOT have this bug — 0/3 repetition, 3/3 valid JSON in same test
- repeat_penalty has NO effect (tested 1.0, 1.15, 1.5 — same failure rate)
- Including schema in prompt text helps for SHORT outputs but fails for longer ones
- Bug confirmed in BOTH gemma4:31b (Dense) and gemma4:26b (MoE)
- Root cause is in the MODEL, not Ollama — same issue in Google AI Studio

**Our pipeline matches all three trigger conditions:**
1. gemma4:31b ✓
2. format= with minimal JSON schema (625 chars) ✓
3. 16 free-text string fields (item_name, item_description, room_name, etc.) ✓

**Why temperature tuning failed (RC-10d/e/f):**
The logit distribution collapse is structural to gemma4's token generation. Temperature modifies sampling probabilities but cannot fix the underlying degenerate distribution. This explains why 0, 0.3, 0.7 all produce identical ~50% failure rates.

**Fix options (ranked by confidence):**
1. Switch to gemma3:27b — confirmed NOT affected, available on both local and RunPod
2. Remove format= entirely — use prompt-only JSON guidance with regex post-processing
3. Switch model family — llama3.1:8b, qwen3:32b, etc.
4. Wait for Google/Ollama fix — unknown timeline, model-level issue

---

## Key Code Locations

| Component | File | Lines |
|-----------|------|-------|
| Docling table extraction | commands/source_commands.py | 90-224 |
| Building inventory (LLM) | open_notebook/extractors/building_inventory.py | 772-887 |
| Building inventory (heuristic) | open_notebook/extractors/building_inventory.py | 490-650 |
| Page_end +2 cap (BUG) | open_notebook/extractors/building_inventory.py | 830-842 |
| Page_end=total fix (heuristic) | open_notebook/extractors/building_inventory.py | 618-627 |
| Row segmenter | open_notebook/extractors/row_segmenter.py | 710-810 |
| Per-row extractor | open_notebook/extractors/row_extractor.py | 319-459 |
| Graph topology | open_notebook/graphs/acm_extraction.py | 3028-3076 |
| extract_items_node | open_notebook/graphs/acm_extraction.py | 1084-1384 |
| recover_no_access | open_notebook/graphs/acm_extraction.py | 2670+ |
