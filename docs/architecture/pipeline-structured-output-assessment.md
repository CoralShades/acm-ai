# Pipeline Structured Output Failure Assessment

**Date:** 2026-02-27
**Trigger:** E23-S4 validation revealed 4/4 LLM-dependent stages falling back from structured output
**Author:** Architecture review (post-E23 sprint close)

---

## 1. Executive Summary

All four LLM-dependent pipeline stages are **failing their primary structured output path** and falling back to either heuristic methods or manual JSON parsing. This is not a new regression — it is a systemic incompatibility between the schema complexity required by the extraction pipeline and the constrained-grammar limitations of `with_structured_output()` when routed through OpenRouter to Anthropic.

**Key finding:** The fallback paths are functional and the pipeline achieves 90.3% accuracy (28/31 Broadmeadows). The structured output failure adds ~40s latency per extraction run (failed attempt + retry) but does not block production use. The 3 missing records are **not caused by structured output failure** — they are LLM extraction limitations with brief inline entries.

**Recommendation:** P2 (nice to have). Accept the current fallback architecture, eliminate the dead `with_structured_output()` calls to save latency, and optimize the fallback quality. This is not a separate epic — it is a tactical cleanup suitable for a tech-debt story in the next sprint.

---

## 2. Root Cause Analysis

### 2.1 The Error

All four stages hit the same error from Anthropic (via OpenRouter):

```
Error code: 400
"The compiled grammar is too large, which would cause performance issues.
 Simplify your tool schemas or reduce the number of strict tools."
Provider: Anthropic
```

### 2.2 Why It Happens

LangChain's `with_structured_output(PydanticModel)` converts the Pydantic schema into a JSON Schema tool definition and sends it to the provider with `strict: true`. The provider compiles a **constrained decoding grammar** to enforce the schema during token generation. When the grammar exceeds the provider's size limit, it returns a 400 error.

#### The Chain of Causation

```
Pydantic schema → LangChain tool schema → OpenRouter → Anthropic provider
                                                        ↓
                                          "Grammar too large" (400)
                                                        ↓
                                          Exception caught by pipeline
                                                        ↓
                                          Fallback: heuristic or JSON parse
```

### 2.3 Schema Complexity by Stage

| Stage | Schema | Fields | Nested Types | Enums | Complexity |
|-------|--------|--------|-------------|-------|------------|
| **Structure extraction** | `DocumentStructureLLM` | 6 | `Section` → `SubSection` (2 levels) | `DocumentType` (4 values) | **Medium** |
| **Building inventory** | `BuildingInventory` | 4 | `BuildingMeta` → `RoomMeta` (2 levels) + `ProcessingGroup` | `BuildingComplexity` (2 values) | **Medium-High** |
| **Page tagging** | `PageTagBatch` | 1 | `PageTag` → `SubSectionTag` (2 levels) | `PageType` (4 values), `SectionTaxonomy` (8 values) | **Medium** |
| **Main extraction** | `ACMExtractionResult` | 6 | `ACMExtractionRecord` (40+ fields) + `ConfidenceDistribution` | `ExtractionStatus` (3 values) + field validators | **Very High** |

The main extraction schema (`ACMExtractionResult`) is the heaviest offender with 40+ fields per record, multiple enum constraints, and field-level validators. However, **all four schemas fail**, including the relatively simple `DocumentStructureLLM` (6 fields, no Dict). This suggests the grammar limit is hit at a lower threshold than expected, or that OpenRouter's Anthropic routing adds overhead to schema compilation.

### 2.4 Why DocumentStructureLLM Was Created

The codebase already has a `DocumentStructureLLM` model (lines 74-86 of `document_structure.py`) — a slimmed version of `DocumentStructure` that removes the `Dict[str, Any]` metadata field because "Azure OpenAI strict mode rejects Dict[str, Any] fields." Despite this explicit workaround, the schema still fails via OpenRouter/Anthropic.

### 2.5 OpenRouter vs. Anthropic Direct

The pipeline uses **OpenRouter** as an intermediary, not Anthropic's native API directly. Key differences:

| Aspect | OpenRouter + Anthropic | Anthropic Direct |
|--------|----------------------|-----------------|
| Structured output method | Tool-use / function-calling via OpenAI-compat API | Native `tool_use` with `anthropic-beta` header |
| Grammar compilation | Delegated to Anthropic provider (same limits) | Same limits apply |
| Provider routing | May route to Google/Azure backends that reject `anthropic-beta` header | N/A — always Anthropic |
| Error surface | Provider-specific 400 errors, schema rejection, header incompatibilities | Cleaner error messages |

**Critically:** The codebase already has `_apply_openrouter_preferences()` (utils.py:36-100) which restricts Anthropic models to the Anthropic provider only, preventing the `anthropic-beta` header rejection from Google backends. The grammar size limit is inherent to Anthropic's constrained decoding, not an OpenRouter issue.

### 2.6 The `require_parameters: true` Setting

The OpenRouter routing in `utils.py:79` sets `require_parameters: true`, which forces the provider to support all request parameters including structured output. This is correct — it ensures we don't silently route to a provider that ignores the tool schema. But it also means the grammar compilation failure surfaces as a hard error instead of being silently ignored.

---

## 3. Per-Stage Impact Assessment

### 3.1 Stage: Document Structure Extraction

| Property | Value |
|----------|-------|
| **File** | `open_notebook/extractors/document_structure.py` |
| **LLM call** | `_llm_extract_structure()` — line 144: `model.with_structured_output(DocumentStructureLLM)` |
| **Fallback** | `_heuristic_fallback()` — regex-based detection of page markers, register section, building IDs |
| **Fallback quality** | **Good.** Correctly extracts `total_pages`, `register_start_page`, `building_ids`. Sets `document_type=UNKNOWN` (vs. LLM which would set SAMP/ARA). |
| **Accuracy lost** | **Minimal.** `document_type=UNKNOWN` is cosmetic — it does not affect downstream extraction. `register_start_page` and `building_ids` are detected correctly by regex for SAMP format. |
| **Downstream effect** | None visible. Content trimming and building detection work correctly with heuristic output. |
| **Latency penalty** | ~5-10s (failed LLM call + timeout + fallback execution) |
| **Broadmeadows impact** | None of the 3 missing records are attributable to structure extraction failure. |

### 3.2 Stage: Building Inventory Compilation

| Property | Value |
|----------|-------|
| **File** | `open_notebook/extractors/building_inventory.py` |
| **LLM call** | `_llm_compile_inventory()` — line 478: `model.with_structured_output(BuildingInventory)` |
| **Fallback** | `_heuristic_fallback()` — regex detection of `_BUILDING_HEADER` and `_ROOM_HEADER` patterns, page position mapping, complexity classification |
| **Fallback quality** | **Good for SAMP, moderate for ARA.** SAMP building headers (B###) and room codes (R####) are reliably captured by regex. ARA format uses `_detect_ara_buildings()` which depends on "Building Name:" header blocks. |
| **Accuracy lost** | Potentially loses: building year, construction type, purpose, area_m2, levels (fields that require text comprehension, not regex). These are informational — not used by downstream extraction. |
| **Downstream effect** | Processing groups and page ranges are correctly computed from heuristic output. The orchestrator uses page ranges for per-building extraction — these are correct. |
| **Latency penalty** | ~5-10s |
| **Broadmeadows impact** | None. The 3 missing records are "Not Sampled" brief inline entries — building inventory correctly identifies all buildings. |

**Note:** Even in the LLM-success path, `compile_building_inventory()` (lines 536-567) always runs `_heuristic_fallback()` on the FULL content as a cross-validation step and merges heuristic-discovered buildings that the LLM missed. The LLM path is already a "LLM + heuristic merge" — not pure LLM.

### 3.3 Stage: Page-Level Section Tagging

| Property | Value |
|----------|-------|
| **File** | `open_notebook/extractors/page_tagger.py` |
| **LLM call** | `_llm_tag_batch()` — line 356: `model.with_structured_output(PageTagBatch)`, called per batch of 5 pages |
| **Fallback** | `_heuristic_tag_all()` → `_heuristic_tag_page()` per page — uses building inventory page ranges, document structure sections, regex patterns for section headings, building headers, special pages |
| **Fallback quality** | **Good.** The heuristic uses both `building_inventory` and `document_structure` from upstream stages (which already ran successfully via their own heuristics). Building inventory page ranges give 0.85 confidence for register pages. |
| **Accuracy lost** | `content_summary` per page is not generated. Section transitions between methodology and register may be off by 1-2 pages. |
| **Downstream effect** | Page tags are used for `register_page_range` which feeds into content trimming in `prepare_context`. The heuristic correctly identifies register pages via building headers. |
| **Latency penalty** | ~10-20s (multiple batches × failed attempt each) |
| **Broadmeadows impact** | None. Register page range is correctly identified by heuristic. |

### 3.4 Stage: Main Extraction (ACM Records)

| Property | Value |
|----------|-------|
| **File** | `open_notebook/graphs/acm_extraction.py` (line 1304) + `open_notebook/extractors/orchestrator.py` (line 530) |
| **LLM call** | `model.with_structured_output(ACMExtractionResult)` |
| **Fallback** | Two-stage: (1) `model.ainvoke(messages)` → free text response, (2) `parse_json_response()` → extract JSON, (3) `ACMExtractionResult.model_validate()` |
| **Fallback quality** | **Good.** The LLM receives the same prompt and produces JSON in its response text. `parse_json_response()` handles fenced code blocks and brace-depth matching. Pydantic validators run on the parsed JSON. |
| **Accuracy lost** | **Marginal.** Without grammar-enforced output, the LLM can produce: trailing commas (handled by parser), missing closing braces (handled by brace-depth), non-JSON preamble text (handled by extraction). Field-level accuracy is identical — the same prompt produces the same content understanding. |
| **Downstream effect** | Records successfully extracted: 31 raw → 28 after dedup (90.3% match). |
| **Latency penalty** | ~15-20s (one failed `with_structured_output()` call before fallback) |
| **Broadmeadows impact** | None. The 3 missing records are content-understanding failures, not parsing failures. The fallback JSON parser successfully extracted 31 records. |

---

## 4. Does Structured Output Failure Explain the 3 Missing Records?

**No.** The 3 missing Broadmeadows records are:

1. **Level 1 / Switch Room / Fuse cartridge** — "Not Sampled" brief inline entry
2. **Ground / Lift Foyer / Lift / Internal lining** — "Not Sampled" brief inline entry
3. **Ground / Main Foyer / Disabled Toilet** — "Not Sampled" / "No Access" brief entry

These are all characterized by:
- Minimal tabular data (no NATA sample number, no lab result)
- Brief text format that the LLM treats as non-records despite explicit prompt rules
- Present in the PDF but without the standard field sequences the extraction prompt targets

The fallback JSON parser successfully extracted **31 records** from the LLM's free-text JSON response. The dedup step merged 3 duplicates → 28. The 3 missing entries were never produced by the LLM in the first place — this is a prompt/content-understanding issue, not a structured output issue.

---

## 5. Aggregate Latency Impact

| Stage | Wasted Attempt | Fallback | Total Overhead |
|-------|---------------|----------|---------------|
| Structure extraction | ~5s | ~1s (heuristic) | ~6s |
| Building inventory | ~5s | ~1s (heuristic) | ~6s |
| Page tagging | ~15s (3 batches × 5s) | ~1s (heuristic) | ~16s |
| Main extraction | ~15s | ~0s (same model call, different parsing) | ~15s |
| **Total** | | | **~43s wasted** |

On a 222s total extraction run, ~43s (19%) is wasted on `with_structured_output()` calls that will never succeed. This is the primary optimization opportunity.

---

## 6. Recommendations

### Recommendation 1: Eliminate Dead `with_structured_output()` Calls — P1

**What:** For stages 1-3 (structure, inventory, page tagging), skip `with_structured_output()` entirely and go straight to `model.ainvoke()` + `parse_json_response()` + Pydantic validation. The heuristic fallback is already being used anyway — but adding a JSON-parse primary path would let the LLM contribute meaningful intelligence (document type, building metadata, content summaries) that the heuristic cannot provide.

**For stage 4 (main extraction):** Skip `with_structured_output()` and go directly to the existing fallback path. The fallback JSON parser is already the production path and has been validated at 90.3% accuracy.

**Effort:** Small — each stage needs ~20 lines of change (replace `chain = model.with_structured_output(Schema)` / `await chain.ainvoke(messages)` with `raw = await model.ainvoke(messages)` / `parsed = parse_json_response(raw.content)` / `result = Schema.model_validate(parsed)`).

**Impact:** Eliminates ~43s latency, removes misleading error logs, simplifies error handling. No accuracy change.

**Implementation pattern (already exists for Qwen):**
```python
# Current (fails, triggers fallback):
chain = model.with_structured_output(DocumentStructureLLM)
result = await chain.ainvoke(messages)

# Proposed (direct JSON, same as Qwen path):
raw_response = await model.ainvoke(messages)
parsed = parse_json_response(raw_response.content)
result = DocumentStructureLLM.model_validate(parsed)
```

### Recommendation 2: Keep Heuristic Fallbacks as Safety Nets — P2

**What:** Retain all `_heuristic_fallback()` functions as fallback for when the LLM call itself fails (network error, auth error, rate limit). But position them behind the JSON-parse path, not as the primary fallback.

**New cascade:**
```
1. model.ainvoke() + parse_json_response() + Pydantic validation  (primary)
2. _heuristic_fallback()                                           (safety net)
```

### Recommendation 3: Add `is_provider_schema_error()` Detection to Pre-Extraction Stages — P2

**What:** The orchestrator (line 558) already detects provider schema errors and routes to fallback. The three pre-extraction stages (`document_structure.py`, `building_inventory.py`, `page_tagger.py`) catch a generic `Exception` and fall through to heuristic. Add the same `is_provider_schema_error()` check with explicit logging.

### Recommendation 4: Do NOT Switch to Anthropic Direct API — Not Recommended

**Why not:** The grammar size limit is inherent to Anthropic's constrained decoding engine, not an OpenRouter intermediary issue. Switching to `provider="anthropic"` directly would hit the same `"compiled grammar is too large"` error. The only way to make `with_structured_output()` work is to simplify the schemas below the grammar threshold — which would mean splitting `ACMExtractionRecord` into multiple smaller tool calls, a significant architectural refactor with uncertain ROI.

### Recommendation 5: Do NOT Simplify Schemas — Not Recommended

**Why not:** The 40+ fields on `ACMExtractionRecord` are all business-required BAR (Building Asbestos Register) fields. Splitting extraction into multiple LLM calls (e.g., "extract building context", "extract material data", "extract risk data") would multiply LLM costs, increase latency, and introduce field-correlation failures. The current single-call-per-building approach with JSON parsing is working well.

### Recommendation 6: Consider Schema-Light `with_structured_output()` for Pre-Extraction — P3

**What:** If future Claude model versions increase the grammar size limit, or if the pre-extraction schemas are simplified (e.g., removing nested `SubSection` types), `with_structured_output()` could be re-enabled for the simpler stages. The main extraction schema (`ACMExtractionResult`) will likely always exceed the limit.

---

## 7. Priority and Scoping

| Item | Priority | Epic | Effort |
|------|----------|------|--------|
| Eliminate dead `with_structured_output()` calls (all 4 stages) | **P1** | Tech debt story (E24 or standalone) | 1-2 hours |
| Restructure pre-extraction to use JSON-parse primary path | **P1** | Same story | 2-3 hours |
| Add `is_provider_schema_error()` to pre-extraction stages | **P2** | Same story | 30 min |
| Keep heuristics as safety net (no change needed) | **P2** | N/A | 0 |
| Simplify schemas / switch providers | **Not recommended** | — | — |

**Verdict:** This is a **single tech-debt story** suitable for the next sprint, not a separate epic. Total effort: ~4-6 hours including tests. Priority: **P1** for the latency savings, **P2** for the code hygiene.

---

## 8. Appendix: Evidence Sources

| Document | Key Finding |
|----------|-------------|
| `docs/reviews/e23-validation-results.md` | 4/4 stages in fallback, 28/31 accuracy |
| `docs/PIPELINE-AUDIT-FEB-25/pipeline-analysis-20260225.md` | "Grammar too large" root cause, fallback path analysis |
| `docs/v2-integration/acm-ai-knowledge-base.md` | Structured output issue documented, Qwen JSON-mode pattern |
| `docs/sprint-artifacts/audit-multi-provider-2026-02-23.md` | OR-8 confirms fallback works, EH-4 identifies no simpler-prompt retry |
| `open_notebook/graphs/utils.py:22-33` | OpenRouter provider routing preferences |
| `open_notebook/graphs/utils.py:271-323` | `is_provider_schema_error()` detection |
| `open_notebook/extractors/acm_schemas.py` | ACMExtractionRecord: 40+ fields, complex validators |
| `open_notebook/extractors/document_structure.py:74-86` | `DocumentStructureLLM` already attempted schema simplification |
