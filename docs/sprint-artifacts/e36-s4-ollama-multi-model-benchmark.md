# E36-S4: Ollama Multi-Model Benchmark

## Story Info
- **ID**: E36-S4
- **Epic**: E36 (E2E Verification & Agent Orchestration)
- **SP**: 5 | **Risk**: HIGH | **Type**: verification
- **Dependencies**: E36-S2 (DONE)

## Objective
Benchmark 6 Ollama models against 2 ground-truth PDFs to identify the best-performing local model for ACM extraction.

## Test Matrix

| # | Model | PDF | Ground Truth Records |
|---|-------|-----|---------------------|
| 1 | qwen2.5:7b | Broadmeadows | 31 |
| 2 | qwen2.5:7b | Alexander | 43 |
| 3 | llama3.1:8b | Broadmeadows | 31 |
| 4 | llama3.1:8b | Alexander | 43 |
| 5 | mistral:7b | Broadmeadows | 31 |
| 6 | mistral:7b | Alexander | 43 |
| 7 | qwen3:32b | Broadmeadows | 31 |
| 8 | qwen3:32b | Alexander | 43 |
| 9 | qwen2.5:32b | Broadmeadows | 31 |
| 10 | qwen2.5:32b | Alexander | 43 |
| 11 | phi4:14b | Broadmeadows | 31 |
| 12 | phi4:14b | Alexander | 43 |

## Acceptance Criteria

| AC | Description | Evidence |
|----|-------------|----------|
| AC1 | 12 extraction runs completed (6 models x 2 PDFs) | Benchmark script output log |
| AC2 | Each run compared against ground truth | Per-run detail files with match analysis |
| AC3 | Per-run detail files in benchmark-results/ | File listing of 12 detail files |
| AC4 | Summary table with accuracy % per model per PDF | summary.md with comparison table |
| AC5 | Log analysis per run in logs/ | log-sentinel-e36s4.md |
| AC6 | Best-performing model identified | Summary conclusion section |

## Methodology

### Benchmark Sources
- **Broadmeadows**: `source:25pxnu7ot2oy2oi7dmc0` (Clutch_Broadmeadows (25).pdf)
- **Alexander**: `source:ubbsh2i0b6ypy64vs1hh` (Clucth_Alexander_District_Hospital.pdf)

### Ground Truth
- **Broadmeadows**: `tests/e2e/fixtures/samps/broadmeadows-expected-results.json` (31 records)
- **Alexander**: `docs/samplePDF/Alexander_GroundTruth.csv` (43 records)

### Model Record IDs
| Model | Record ID |
|-------|-----------|
| qwen2.5:7b | model:6uszykjp9wrwe2jkwsea |
| llama3.1:8b | model:m7tdn5b7lavy0z1yg14j |
| mistral:7b | model:wmmp7o4sgz0qs09bo9p6 |
| qwen3:32b | model:jb3rgqhs31vws1zth4h2 |
| qwen2.5:32b | model:znay2wr8u9q39lxj2q37 |
| phi4:14b | model:wpfnb5ks1sq5ncqbqjzb |

### Per-Run Workflow
1. `PUT /api/models/defaults` — set `default_extraction_model` to model record ID
2. `POST /api/acm/extract` — trigger with `force=true` (deletes previous records)
3. Poll `GET /api/acm/extraction-progress/{command_id}` until terminal status
4. `GET /api/acm/records?source_id=X&limit=500` — retrieve extracted records
5. Compare to ground truth: record count, field-level matching
6. Write per-run detail file to `docs/sprint-artifacts/e36/benchmark-results/`

### Accuracy Metrics
- **Record Recall**: extracted_count / ground_truth_count
- **Field Accuracy**: For matched records, % of fields matching ground truth
- **Match Fields**: building_name, room_name, product (fuzzy match for record pairing)
- **Score Fields**: room_name, product, sample_result/result, friable, material_condition, risk_status, sample_no

## File Changes

| File | Action |
|------|--------|
| `scripts/benchmark_ollama.py` | CREATE — benchmark runner script |
| `docs/sprint-artifacts/e36/benchmark-results/summary.md` | CREATE — comparison table |
| `docs/sprint-artifacts/e36/benchmark-results/*.md` | CREATE — 12 per-run detail files |
| `docs/sprint-artifacts/e36/evidence/log-sentinel-e36s4.md` | CREATE — log analysis |
| `docs/sprint-artifacts/e36/evidence/e36-s4/` | CREATE — evidence directory |
| `docs/sprint-artifacts/e36-s4-ollama-multi-model-benchmark.md` | CREATE — this tech spec |

## Dev Agent Record
- Build status: PENDING
- Files verified: PENDING
- Browser/API evidence: PENDING
