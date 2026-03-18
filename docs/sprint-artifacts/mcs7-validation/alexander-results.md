# MCS7 Validation — Alexander District Hospital Regression Results

**Date:** 2026-03-19
**Model:** llama3.1:8b (Ollama, localhost:11434)
**Source ID:** source:b6eswuntqoxyozgvv995
**Notebook:** notebook:8bnn3b8w6nsgoductcmj (MCS7 Alexander Regression)
**PDF:** docs/samplePDF/AlexanderHospital.pdf

## Final Extraction Results (SUCCESSFUL)

| Metric | Value |
|--------|-------|
| Pipeline Status | **COMPLETE** |
| Total Duration | 473.5s (~8 min) |
| Buildings Detected | 7 |
| Records Saved | **95/95** (0 errors) |
| Parent Sections | 7 |
| Model | ollama/llama3.1:8b |

## Per-Building Breakdown

| Building | Records |
|----------|---------|
| B00A | 3 |
| B00B | 18 |
| B00E (Old Alexandra Hospital) | 43 |
| Mortuary Buildings | 9 |
| Nurses Accommodation | 9 |
| Pathology Department | 8 |
| VMO Accommodations | 5 |
| **Total** | **95** |

## E28 Baseline Comparison

### Raw Numbers
| | E28 (Claude Sonnet) | MCS7 (llama3.1:8b) | Ground Truth |
|---|---|---|---|
| Total Records | 36 | 95 | 43 |
| Buildings | 7 | 7 | 7 |

### Over-Extraction Analysis
95 records vs 43 ground truth = **2.2x over-extraction**. The Ollama model produces:
- Duplicate records (e.g., rows 4-5 same sample Greencap 35766/11)
- Noise records from PDF metadata (e.g., "Est. Building Age:", "Construction Type:", "Hazard Type", "Roof Type")
- Split records where one item becomes multiple rows
- "200m²" appearing as a product (building area metadata extracted as a record)

### By Result Category
| Result | Count |
|--------|-------|
| Unknown | 33 |
| Positive | 20 |
| Negative | 19 |
| Presumed Positive | 10 |
| No Asbestos Detected (various) | 10 |
| Not Sampled | 1 |
| Other (material) | 1 |

### By Sample Result
| Sample Result | Count |
|---------------|-------|
| Negative | 53 |
| Positive | 21 |
| Assumed Positive | 11 |
| Negative - Treated as Positive | 10 |

### E28 Category Approximation
Direct category mapping is imprecise due to over-extraction, but approximate:

| Category | E28 Baseline | MCS7 (raw) | Ground Truth | Notes |
|----------|-------------|------------|--------------|-------|
| NATA-sampled | 18/19 | ~59 (many duplicates) | 19 | Over-extracted: same sample numbers appear multiple times |
| As Per | 7/7 | ~0 | 7 | "As Per" / "Similar To" records extracted but classified as sample_no text |
| Not Sampled | 11/17 | ~6 (undercounted) | 17 | Many "Not Sampled" items classified as "Presumed Positive" or "Unknown" |
| **Approximate unique** | **36/43** | **~40-50 unique** | **43** | After removing obvious noise/duplicates |

## Regression Assessment

### Verdict: PARTIAL PASS with caveats

| Criterion | Result | Status |
|-----------|--------|--------|
| Records saved to DB | 95 saved | **PASS** |
| Extraction pipeline completes | Yes (473.5s) | **PASS** |
| Ollama model used | llama3.1:8b confirmed | **PASS** |
| Buildings = 7 | 7 | **PASS** |
| Record count ≥ 36 (E28 baseline) | 95 ≥ 36 | **PASS** (but over-extracted) |
| Record quality comparable to E28 | Significant noise | **NEEDS IMPROVEMENT** |

### Key Observations

1. **Over-extraction is the main issue**: 95 records vs 43 ground truth. The Ollama model extracts PDF metadata, headers, and duplicate rows as ACM items. E28 with Claude Sonnet was much more selective (36 records, minimal noise).

2. **"Unknown" result category is large**: 33 records have result="Unknown" — these are likely noise records extracted from non-data rows (building metadata, section headers, etc.).

3. **Not Sampled items may be present but miscategorized**: Many "Presumed Positive" and "Assumed Positive" records may correspond to the E28 "Not Sampled" category, but field values differ.

4. **Building detection is accurate**: 7 buildings match ground truth exactly.

5. **Sample numbers are extracted but with noise**: Sample numbers like "J169642-001-001" are extracted correctly, but sometimes include prefixes like "Greencap" or "Similar To:" that weren't in the original.

## Pipeline Stages (Final Run)

| Stage | Status | Duration | Details |
|-------|--------|----------|---------|
| STRUCTURE | Complete | 35.1s | 7 buildings, pages 7-34 |
| ORCHESTRATOR | Complete | ~33s | 7/7 buildings saved |
| EXTRACT | Complete | ~360s | Raw records extracted |
| VALIDATE | Complete | <1s | Records validated |
| CORRECT (2 passes) | Complete | ~70s | LLM corrections applied |
| STORE | Complete | 3.6s | **95/95 saved, 0 errors** |

## Issues Encountered During Session

Multiple extraction attempts were needed due to infrastructure issues:
1. **Worker race condition**: 3+ worker instances claiming same commands
2. **SurrealDB schema type mismatch**: `source_id` and `building_record_id` fields had strict `record<>` types that rejected string values
3. **LangGraph checkpoint serialization**: `Source` and `PipelineLogger` objects in graph state not msgpack-serializable
4. **Record link null fix**: Setting `building_record_id=None` and `parent_table_id=None` before save resolved the SurrealDB issue

All issues were resolved by the team lead before the final successful run.

## Recommendations

1. **Post-extraction dedup/filtering**: Add a noise filter to remove records where:
   - `result` = "Unknown" AND no `sample_no` AND `product` looks like metadata
   - `product` matches building metadata patterns ("200m²", "Est. Building Age:", "Construction Type:")

2. **Category normalization**: Map Ollama's "Presumed Positive" / "Assumed Positive" to the standard "Not Sampled" category for consistent comparison

3. **Unique record matching**: Implement fuzzy dedup on (building, room, product, sample_no) to collapse the 95 records to ~43 unique items
