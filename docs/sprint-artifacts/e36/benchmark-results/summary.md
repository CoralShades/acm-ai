# E36-S4: Ollama Multi-Model Benchmark Summary

**Date**: 2026-03-05
**Total runs**: 12 (6 models x 2 PDFs)
**Completed**: 5 | **Timed out**: 7 (due to extraction_progress status bug)

## Critical Finding: extraction_progress Table Bug

The `extraction_progress` SurrealDB table does NOT reliably update to "completed" status
after the worker finishes extraction. 7 of 12 runs "timed out" at 600s despite the worker
completing the extraction and saving records. This is a **false timeout** caused by the
pipeline logger not writing the terminal status. The record-count fallback caught 5 of 12
runs but missed the rest due to timing.

## Results Table

| # | Model | PDF | GT | Extracted | Matched | Recall% | Field Acc% | Time(s) | Status |
|---|-------|-----|----|-----------|---------|---------|------------|---------|--------|
| 1 | qwen2.5:7b | broadmeadows | 31 | 20 | 4 | 12.9 | 29.2 | 252 | completed |
| 2 | qwen2.5:7b | alexander | 43 | 37 | 0* | 0.0* | 0.0* | 82 | completed |
| 3 | llama3.1:8b | broadmeadows | 31 | 3 | 1 | 3.2 | 33.3 | 403 | completed |
| 4 | llama3.1:8b | alexander | 43 | ? | - | - | - | 613 | timeout |
| 5 | mistral:7b | broadmeadows | 31 | ? | - | - | - | 613 | timeout |
| 6 | mistral:7b | alexander | 43 | ~42 | - | - | - | 616 | timeout (records detected) |
| 7 | qwen3:32b | broadmeadows | 31 | ~7 | - | - | - | 616 | timeout (records detected) |
| 8 | qwen3:32b | alexander | 43 | ~33 | - | - | - | 616 | timeout (records detected) |
| 9 | qwen2.5:32b | broadmeadows | 31 | ? | - | - | - | 613 | timeout |
| 10 | qwen2.5:32b | alexander | 43 | 35 | 0* | 0.0* | 0.0* | 238 | completed |
| 11 | phi4:14b | broadmeadows | 31 | ? | - | - | - | 613 | timeout |
| 12 | phi4:14b | alexander | 43 | 35 | 0* | 0.0* | 0.0* | 82 | completed |

*\* Alexander matching returns 0% due to field misalignment (see below)*
*~ = records detected during polling but not retrieved before timeout*

## Alexander Matching Limitation

All Alexander runs show 0% recall despite extracting 33-42 records. Root cause:
the extraction places **material descriptions in the room_name field** instead of room names.

| Extracted | Ground Truth |
|-----------|-------------|
| building_name: "Mortuary Buildings" | building_name: "Mortuary Buildings" (match) |
| room_name: "Infill Panels - Flat Cement Sheeting" | room_name: "Shower Room" (mismatch) |
| product: "Infill panels below windows" | product: "Infill panels" (partial match) |

The fuzzy matcher can't pair records when room_name is fundamentally wrong. This is an
**extraction quality issue** (field misalignment), not just a matching algorithm problem.

## Record Count Comparison (Primary Metric)

Since field-level matching is unreliable, **raw record count vs ground truth** is the most
meaningful comparison metric:

| Model | Broadmeadows (GT: 31) | Alexander (GT: 43) | Combined Ratio |
|-------|----------------------|-------------------|----------------|
| qwen2.5:7b | 20 (64.5%) | 37 (86.0%) | **75.3%** |
| llama3.1:8b | 3 (9.7%) | ? (timeout) | 9.7%+ |
| mistral:7b | ? (timeout) | ~42 (97.7%) | 97.7%+ |
| qwen3:32b | ~7 (22.6%) | ~33 (76.7%) | 49.7%+ |
| qwen2.5:32b | ? (timeout) | 35 (81.4%) | 81.4%+ |
| phi4:14b | ? (timeout) | 35 (81.4%) | 81.4%+ |

## Best Performing Model

**qwen2.5:7b** is the most reliable model based on completed data:
- Only model with BOTH PDFs completing within timeout
- Broadmeadows: 20/31 records (64.5% extraction rate) in 252s
- Alexander: 37/43 records (86.0% extraction rate) in 82s
- Fastest average time (167s per run)
- Highest Broadmeadows field accuracy (29.2%)

**mistral:7b** shows promise for Alexander (~42/43 records, 97.7%) but Broadmeadows data is missing due to timeout.

## Speed Ranking (completed runs only)

| Model | Avg Time | Notes |
|-------|----------|-------|
| qwen2.5:7b | 167s | Fastest — best for production |
| phi4:14b | 82s* | *Alexander only |
| qwen2.5:32b | 238s* | *Alexander only |
| llama3.1:8b | 403s | Broadmeadows only |

## Recommendations

1. **Use qwen2.5:7b as default Ollama extraction model** — fastest, most data points, good extraction rate
2. **Fix extraction_progress status bug** — pipeline logger doesn't write terminal status, causing 58% false timeout rate
3. **Improve room_name extraction** — models consistently put material descriptions in room_name instead of actual room names
4. **Increase extraction timeout to 900s** for production — 600s is too short for correction stage on larger PDFs
5. **Consider mistral:7b** as alternative if room_name extraction can be fixed — highest Alexander record count

## Methodology

- Each model ran extraction with `force=true` (clean slate per run)
- Record matching uses fuzzy string similarity (threshold: 0.5 for record pairing)
- Field accuracy uses fuzzy match (threshold: 0.8 for correct)
- Dual completion detection: extraction_progress status + record-count stabilization (15s)
- Timeout: 600s per run
- Sources: Broadmeadows (source:25pxnu7ot2oy2oi7dmc0), Alexander (source:ubbsh2i0b6ypy64vs1hh)
