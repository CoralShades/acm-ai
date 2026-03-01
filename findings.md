# Findings — E29-S1: JSON Parser Resilience

## Current parse_json_response Behavior (utils.py:497-536)
1. Fenced regex: `r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```"` (DOTALL, non-greedy)
2. If match → `json.loads(match.group(1))`
3. Else → brace-depth scan from first `{`
4. Return `dict` or raise `ValueError`

## Bug: Non-greedy fenced regex
- `\{.*?\}` stops at FIRST `}`, so `{"a":{"b":1}}` → captures `{"a":{"b":1}` → parse fails
- Fix: remove regex fence detection, strip fence markers first, then always use brace-depth scan

## Callers (5 sites)
| File | Line | Context |
|------|------|---------|
| `acm_extraction.py` | 1301 | Direct JSON extraction |
| `acm_extraction.py` | 1450 | Schema fallback path |
| `orchestrator.py` | 557 | Per-building extraction |
| `orchestrator.py` | 623 | Schema fallback path |
| `page_tagger.py` | 379 | Page tag batch parsing |
| `document_structure.py` | 168 | Structure analysis |
| `building_inventory.py` | 502 | Inventory parsing |

All use pattern: `parsed = parse_json_response(text)` with `except ValueError` or `except (ValueError, json.JSONDecodeError)`.

## TruncationError Design
- `class TruncationError(ValueError)` — subclass ensures backward-compat
- Raised when brace-depth > 0 at EOF (JSON started but never closed)
- Message includes: partial content preview, depth at EOF

## Multi-Block Selection
- Extract ALL complete JSON objects via brace-depth scan
- Try `json.loads()` on each candidate
- Return largest valid object (by `len(json.dumps(obj))`)
- Deterministic: same input → same output

## Existing Tests (test_qwen_extraction.py:63-113)
7 tests covering: fenced, unfenced, preamble, nested, no-json, empty-string
All must continue to pass (AC-5).

---

# Findings — E29-S2: Benchmark Harness + Baseline Capture

## Extraction Pipeline Entry Points
- `extract_acm_from_source()` in `acm_extraction.py:2943` — main entry, returns `ACMExtractionOutput`
- `acm_extract` command in `acm_commands.py:93` — command handler that calls the above
- Graph: extract_metadata → structure → inventory → tag_pages → [conditional] → orchestrate/prepare → validate → correct → deduplicate → recover_no_access → save

## ACMExtractionOutput Fields (Available for Harness)
- `extraction_time_ms: Optional[int]` — wall-clock time (line 481)
- `orchestrator_stats: Optional[dict]` — per-building plan, strategy, timing (line 488)
- `pipeline_run: Optional[dict]` — PipelineRunState with stage timings (line 492)
- `total_records: int` — extracted count (line 469)
- `records_failed: int` — rejected count (line 470)
- `correction_stats: Optional[dict]` — corrective RAG stats (line 484)

## Token Tracking State
- **No centralized token accumulator exists**
- `_verify_provider_routing()` in `utils.py:282-383` queries OpenRouter Generation API per-call
- Logs `tokens_prompt`, `tokens_completion`, `total_cost`, `latency` per LLM call
- These are logged but NOT aggregated or returned in ACMExtractionOutput
- **Harness strategy**: Intercept logging output OR patch `_verify_provider_routing` to accumulate

## Existing E2E Test Pattern (`test_broadmeadows_e2e.py`)
Template for mocked-DB extraction:
```python
patch.object(ACMRecord, "save", capture_save)
patch.object(ACMTableSection, "save", noop)
patch("...auto_populate_site_config", noop)
patch("...provision_langchain_model", real_provision_model)  # both acm_extraction + utils
```
- Records captured via mock `save()`
- 3-tier matching: sample_no → composite key → room+location
- Product synonym map for known LLM output variations

## Ground Truth CSV Formats
- **Broadmeadows**: 43-column standard BAR, DictReader-compatible, 31 rows
  - Key columns: `Room or Area`, `Location in Room`, `Specific Item/ACM Name`, `NATA Endorsed Sample number`, `Sample Result`, `Friability of material`, `Internal / External`, `Level`, `Building Name`
- **Alexander**: 7-column minimal with `#`-comment header lines, 43 rows
  - Columns: `building_name`, `room_name`, `location`, `product`, `sample_no`, `sample_result`, `friable`

## Third Document Candidates
| PDF | Size | Notes |
|-----|------|-------|
| `1124_AsbestosRegister.pdf` | 604 KB | Unknown — needs manual inspection |
| `3980_AsbestosRegister.pdf` | 645 KB | Unknown — needs manual inspection |
| `4601_AsbestosRegister.pdf` | 567 KB | Smallest — preferred for minimal effort |

## ACMExtractionRecord Key Fields for Matching
Required: `building_id`, `product`, `result`
Matching-relevant: `building_name`, `room_name`, `location`, `sample_no`, `sample_result`, `friable`, `internal_external` (via `area_type`), `floor_level`
