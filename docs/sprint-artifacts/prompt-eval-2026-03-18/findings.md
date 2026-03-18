# Prompt Evaluation Framework — Findings

## Ground Truth Sources
- **Broadmeadows**: `docs/samplePDF/Clutch_Broadmeadows.csv` — 31 records (full BAR export)
- **Alexander**: `docs/samplePDF/Alexander_GroundTruth.csv` — 43 records (simplified CSV)

## Baseline v1 (Prior Ollama bulk extraction)
| Metric | Broadmeadows | Alexander |
|--------|-------------|-----------|
| Recall | 87.1% | 46.5% |
| Precision | 90.0% | 22.2% |
| Overall Accuracy | 64.4% | 64.5% |

## Baseline v2 (GPT-4o-mini extraction, 2026-03-18)
| Metric | Broadmeadows | Delta vs v1 |
|--------|-------------|-------------|
| Recall | 87.1% | 0 |
| Precision | 93.1% | +3.1pp |
| Overall Accuracy | **73.1%** | **+8.7pp** |

### Per-Field Comparison (Broadmeadows)
| Field | v1 Accuracy | v2 Accuracy | Delta |
|-------|-------------|-------------|-------|
| room_name | 44.4% | **74.1%** | **+29.7pp** |
| floor_level | 59.3% | 59.3% | 0 |
| location | 44.4% | **63.0%** | **+18.6pp** |
| product | 48.1% | 40.7% | -7.4pp |
| material_description | 44.4% | 33.3% | -11.1pp |
| friable | 29.6% | **92.6%** | **+63.0pp** |
| sample_no | 88.9% | 85.2% | -3.7pp |
| sample_result | 100% | 100% | 0 |
| area_type | 88.9% | **92.6%** | **+3.7pp** |
| material_condition | 80.0% | **81.8%** | **+1.8pp** |
| disturbance_potential | 80.0% | **81.8%** | **+1.8pp** |

## Bugs Fixed During This Session

### 1. Product "Other" mapping (orchestrator.py:584)
**Before**: `product=item.item_name or ""` → always "Other" when LLM uses the picklist
**After**: Prefers `if_other_item_name` when `item_name == "Other"`

### 2. Quantity type coercion (orchestrator.py:207, acm_schemas_v3.py:101)
**Before**: GPT-4o-mini returns `quantity: 3` (int) → Pydantic rejects entire extraction
**After**: Coerce int/float to str in both `_normalize_extraction_json()` and `ACMItemRecord.coerce_quantity()`

### 3. Ollama connectivity check (utils.py:936)
**Before**: Ollama always selected first if `OLLAMA_API_BASE` is set, even when unreachable
**After**: HTTP probe to `/api/tags` before selecting Ollama; falls through to cloud providers

### 4. OpenAI fallback provider (utils.py:960)
**Added** `OPENAI_API_KEY` as 4th priority in extraction provider chain with max_tokens cap at 16384

## Remaining Issues (for future work)
- **product (40.7%)**: LLM returns raw descriptions ("Skirting vinyl sheet") vs BAR picklist values ("Skirting")
- **material_description (33.3%)**: Similar taxonomy mismatch issue
- **floor_level (59.3%)**: Some mismatches remain ("First floor" vs "Level 1")
- **Alexander recall (46.5%)**: Needs re-extraction with working LLM to retest
