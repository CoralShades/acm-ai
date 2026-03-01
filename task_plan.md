# Task Plan — E29-S1: JSON Parser Resilience

## Objective
Implement resilient `parse_json_response()` handling in `open_notebook/graphs/utils.py` per AC-1..AC-5:
- AC-1: Markdown fence stripping before brace-depth scan
- AC-2: Preamble text does not affect extraction
- AC-3: Multiple JSON blocks → select largest valid complete object
- AC-4: Truncated JSON raises `TruncationError` (not `ValueError`)
- AC-5: All existing test patterns still pass (backward-compat)

## Status
- Sprint-status: `ready-for-dev` → will set `in-progress` at T1 start
- No existing `tests/test_json_parser.py` — will create new
- Existing backward-compat tests in `tests/test_qwen_extraction.py:63-113` (7 tests)

## Callers (backward-compat surface)
1. `acm_extraction.py:1301,1450` — extraction + fallback paths
2. `orchestrator.py:557,623` — per-building orchestration + schema fallback
3. `page_tagger.py:379` — page tag batch parsing
4. `document_structure.py:168` — structure analysis
5. `building_inventory.py:502` — inventory parsing
All callers: `try: parse_json_response(text)` → expect `dict` return or `ValueError` raise.
New `TruncationError` is a subclass of `ValueError`, so existing `except ValueError` handlers remain valid.

## Current Implementation (utils.py:497-536)
1. Try `re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", ...)` — fenced JSON (DOTALL)
2. If fenced match → `json.loads(match.group(1))`
3. Else → brace-depth scan from first `{` to balanced `}`
4. Return `dict` or raise `ValueError`

### Bug in current implementation
- Fenced regex uses `\{.*?\}` (non-greedy) which fails on multi-line JSON with nested `{}`
- Example: `` ```json\n{"a":{"b":1}}\n``` `` → regex captures `{"a":{"b":1}` (stops at first `}`) → parse fails
- Fix: strip fences first, then use brace-depth scan on content

## Tasks

### T1: Set sprint-status to in-progress
- Edit `sprint-status.yaml`: `e29-s1-json-parser-resilience: in-progress`
- Edit story file status table

### T2: Add TruncationError exception class
- File: `open_notebook/graphs/utils.py`
- Add `class TruncationError(ValueError)` near line 496 (before `parse_json_response`)
- Subclass `ValueError` for backward-compat with existing `except ValueError` handlers

### T3: Rewrite parse_json_response with resilient logic
- File: `open_notebook/graphs/utils.py:497+`
- Algorithm:
  1. Strip markdown fences: `re.sub(r"```(?:json|JSON)?\s*\n?", "", text)` to remove all fence markers
  2. Extract ALL complete JSON objects via brace-depth scan (handle `{` to balanced `}`)
     - Track brace depth, handle strings (skip braces inside `"..."` including `\"` escapes)
  3. For each candidate, try `json.loads()` — keep valid ones
  4. If multiple valid objects → return the largest (by `len(json.dumps())`)
  5. If zero valid objects but brace-depth > 0 at EOF → raise `TruncationError`
  6. If zero valid objects and no braces found → raise `ValueError("No JSON object found")`
- Backward-compat guarantees:
  - Pure JSON → works (brace scan finds it)
  - Fenced JSON → works (fences stripped first)
  - Preamble JSON → works (brace scan skips preamble text)
  - Return type: `dict[str, Any]` unchanged

### T4: Write comprehensive test suite
- File: `tests/test_json_parser.py` (new)
- Test classes:
  1. `TestFenceStripping` (AC-1):
     - `` ```json\n{"a":1}\n``` `` → `{"a": 1}`
     - `` ```\n{"a":1}\n``` `` → `{"a": 1}` (no json label)
     - `` ```json\n{"a":{"b":1}}\n``` `` → nested JSON in fences
     - `` ```JSON\n{"a":1}\n``` `` → case-insensitive fence label
  2. `TestPreambleHandling` (AC-2):
     - `"Here is the result:\n{...}"` → extracts JSON
     - `"The output is:\n\n{...}\n\nHope that helps!"` → JSON with preamble AND suffix
     - Multi-line preamble with explanatory text
  3. `TestMultiBlock` (AC-3):
     - Two JSON objects: small `{"a":1}` + large `{"records":[...], "status":"valid"}` → returns larger
     - Three JSON objects → returns largest valid
     - One valid + one invalid → returns the valid one
  4. `TestTruncation` (AC-4):
     - `'{"records":[{"a":1},{"b":2'` → raises `TruncationError`
     - `'{"records":[{"a":1},{"b":'` → raises `TruncationError`
     - `TruncationError` is subclass of `ValueError`
  5. `TestBackwardCompat` (AC-5):
     - All 7 existing test patterns from `test_qwen_extraction.py:63-113` replicated
     - Pure JSON, preamble, nested, no-json raises, empty raises
  6. `TestEdgeCases`:
     - JSON array `[1,2,3]` — currently function returns `dict`, arrays not supported → verify behavior
     - Unicode in JSON values
     - JSON with string values containing `{` and `}` (braces in strings)

### T5: Run lint + test verification
- `uv run ruff check open_notebook/graphs/utils.py`
- `uv run ruff check tests/test_json_parser.py`
- `uv run pytest tests/test_json_parser.py -x -v`
- `uv run pytest tests/test_qwen_extraction.py::TestParseJsonResponse -x -v` (backward-compat)

### T6: Update story file Post-Dev Notes
- Implementation summary
- Changed files list
- Test evidence (pass counts)
- Risks/follow-ups

### T7: Set sprint-status to review + append worklog

## Risks
- Brace-depth scanner must handle JSON strings with escaped quotes `\"` and braces inside strings
- Multi-block selection: "largest" by serialized length — simple and deterministic
- `TruncationError(ValueError)` subclass ensures callers using `except ValueError` still work

## Files Changed
| File | Action |
|------|--------|
| `open_notebook/graphs/utils.py` | Modify (~60 lines) |
| `tests/test_json_parser.py` | Add (new, ~150 lines) |
| `docs/sprint-artifacts/e29-s1-json-parser-resilience.md` | Update (Post-Dev Notes) |
| `docs/sprint-artifacts/sprint-status.yaml` | Update (status) |

---

# Task Plan — E29-S2: Benchmark Harness + Baseline Capture

## Objective
Build automated benchmark harness, create ground-truth JSON for >=3 documents, capture baseline metrics (recall, precision, field accuracy, latency, token cost), and publish baseline report. Gate 1 exit artifact.

## Status
- Sprint-status: `ready-for-dev` → will set `in-progress` at T1 start
- S1 is `in-progress` (parallel OK — different files)
- `benchmarks/` directory does NOT exist yet
- `scripts/research/e29_benchmark_harness.py` does NOT exist yet

## Ground Truth Sources

| Document | PDF | Ground Truth Source | Records | Buildings |
|----------|-----|-------------------|---------|-----------|
| Broadmeadows | `docs/samplePDF/Clutch_Broadmeadows.pdf` | `docs/samplePDF/Clutch_Broadmeadows.csv` (43-col BAR) | 31 | 1 |
| Alexander | `docs/samplePDF/Clucth_Alexander_District_Hospital.pdf` | `docs/samplePDF/Alexander_GroundTruth.csv` (7-col minimal) | 43 | 5 |
| Third (TBD) | `docs/samplePDF/1124_AsbestosRegister.pdf` or `3980` or `4601` | Must create | TBD | TBD |

## Ground Truth JSON Schema

```json
{
  "document": {
    "name": "string",
    "pdf_path": "relative/to/repo/root",
    "source": "CSV path or 'manual extraction'",
    "total_buildings": 1,
    "total_records": 31,
    "consultant": "string"
  },
  "match_keys": {
    "primary": "sample_no",
    "secondary": ["building_name", "room_name", "location", "product"],
    "tertiary": ["room_name", "location"]
  },
  "records": [
    {
      "building_name": "string",
      "room_name": "string",
      "location": "string",
      "product": "string",
      "sample_no": "string",
      "sample_result": "string",
      "friable": "string",
      "internal_external": "string (optional)",
      "level": "string (optional)"
    }
  ]
}
```

## Metric Definitions

| Metric | Formula | Notes |
|--------|---------|-------|
| `recall` | matched / ground_truth_total | How many ground-truth records were found |
| `precision` | matched / extracted_total | How many extracted records are genuine |
| `field_accuracy` | sum(field_matches) / (matched * num_fields) | Per-field match rate across matched records |
| `latency_s` | extraction_time_ms / 1000 | From `ACMExtractionOutput.extraction_time_ms` |
| `token_usage` | sum(prompt + completion tokens) | Intercepted from LLM calls |
| `cost_usd` | Calculated from token_usage + model pricing | Informational |

## Record Matching Strategy (3-tier, from test_broadmeadows_e2e.py)

1. **Primary**: Match by `sample_no` (normalized, handles "As Per ..." refs)
2. **Secondary**: Composite key `building_name|room_name|location|product` (normalized, synonym-aware)
3. **Tertiary**: Partial key `room_name|location` (fuzzy fallback, 1:1 consumption)

## Tasks

### T1: Set sprint-status to in-progress [~5m]
- Edit `sprint-status.yaml`: `e29-s2-benchmark-harness-baseline-capture: in-progress`
- Edit story file status table: Status → `in-progress`, Started → date

### T2: Create benchmarks/ directory structure [~10m]
- `benchmarks/__init__.py` (empty)
- `benchmarks/conftest.py` (pytest fixtures for ground truth loading)
- `benchmarks/ground_truth/` (directory)

### T3: Convert Broadmeadows CSV → ground truth JSON [~30m]
- Input: `docs/samplePDF/Clutch_Broadmeadows.csv` (43-col BAR, 31 rows)
- Output: `benchmarks/ground_truth/broadmeadows.json`
- Script: write a one-time CSV→JSON converter in the harness
- Map CSV columns to JSON schema:
  - `Room or Area` → `room_name`
  - `Location in Room` → `location`
  - `Specific Item/ACM Name` → `product`
  - `NATA Endorsed Sample number (if available)` → `sample_no`
  - `Sample Result` → `sample_result`
  - `Friability of material` → `friable`
  - `Internal / External` → `internal_external`
  - `Level` → `level`
  - `Building Name` → `building_name`
- Validate: 31 records, 1 building

### T4: Convert Alexander CSV → ground truth JSON [~30m]
- Input: `docs/samplePDF/Alexander_GroundTruth.csv` (7-col minimal, 43 rows)
- Output: `benchmarks/ground_truth/alexander.json`
- Map CSV columns:
  - `building_name` → `building_name`
  - `room_name` → `room_name`
  - `location` → `location`
  - `product` → `product`
  - `sample_no` → `sample_no`
  - `sample_result` → `sample_result`
  - `friable` → `friable`
- Note: Alexander CSV has comment lines starting with `#` — skip them
- Validate: 43 records, 5 buildings

### T5: Select and create third document ground truth [~45m]
- Evaluate candidates: `1124_AsbestosRegister.pdf`, `3980_AsbestosRegister.pdf`, `4601_AsbestosRegister.pdf`
- Selection criteria: smallest record count preferred (faster benchmark cycles)
- Approach: Extract PDF text with PyMuPDF, manually count and catalogue ACM records
- Output: `benchmarks/ground_truth/<name>.json`
- Minimum viable: identify building(s), rooms, products, sample numbers from PDF text
- If PDF is too complex, use smallest subset approach with documented limitations

### T6: Implement benchmark harness core [~90m]
- File: `scripts/research/e29_benchmark_harness.py`
- Architecture:
  ```
  BenchmarkConfig      — document name, pdf_path, ground_truth_path
  BenchmarkResult      — per-document metrics (recall, precision, field_accuracy, latency, tokens, cost)
  BenchmarkHarness     — orchestrates extraction + comparison + metric calculation
  RecordMatcher        — 3-tier matching engine (extracted from test_broadmeadows_e2e.py pattern)
  MetricsCalculator    — recall/precision/field_accuracy computation
  ReportGenerator      — markdown report writer
  ```

#### T6.1: BenchmarkConfig + document registry
- Dataclass with: name, pdf_path, ground_truth_path, expected_records, expected_buildings
- Registry of known benchmark documents (Broadmeadows, Alexander, third)
- CLI arg parsing: `--all`, `--doc <name>`, `--report-only`

#### T6.2: Ground truth loader
- Load JSON, validate schema, return typed list of ground-truth records
- Handle both 43-col (Broadmeadows) and 7-col (Alexander) formats uniformly

#### T6.3: Extraction runner (mocked DB)
- Same pattern as `test_broadmeadows_e2e.py`:
  - Mock `ACMRecord.save` to capture records
  - Mock `ACMTableSection.save` as noop
  - Mock `auto_populate_site_config` as noop
  - Use real `provision_langchain_model` (actual LLM calls)
- Capture: extracted records list, ACMExtractionOutput (for timing, stats)
- Token tracking: patch `_verify_provider_routing` or intercept LLM response metadata

#### T6.4: RecordMatcher
- Port matching logic from `test_broadmeadows_e2e.py:_match_extracted_to_expected`
- Generalize for multi-building documents
- Add product synonym map (extensible)
- Return: matched_pairs, unmatched_extracted, unmatched_ground_truth

#### T6.5: MetricsCalculator
- recall = len(matched) / len(ground_truth)
- precision = len(matched) / len(extracted)
- field_accuracy: for each matched pair, compare fields (room_name, location, product, sample_no, sample_result, friable) → match rate
- latency_s: from ACMExtractionOutput.extraction_time_ms
- token_usage / cost: from intercepted LLM metadata

#### T6.6: ReportGenerator
- Output: markdown table per document + summary table
- Template:
  ```markdown
  # E29 Baseline Benchmark Report
  ## Summary
  | Document | Records (GT) | Extracted | Recall | Precision | Field Acc | Latency | Tokens | Cost |
  ## Per-Document Details
  ### Broadmeadows
  - Matched records: ...
  - Missing records: ...
  - Extra records: ...
  - Field accuracy breakdown: ...
  ```

### T7: Write integration tests [~45m]
- File: `tests/integration/test_benchmark_harness.py`
- Tests (no LLM calls — all mock data):

#### T7.1: test_ground_truth_loading
- Load broadmeadows.json → 31 records
- Load alexander.json → 43 records
- Invalid JSON → graceful error

#### T7.2: test_record_matching_accuracy
- Mock: 5 ground-truth records + 5 extracted records with known overlap
- Verify: correct matched/unmatched counts
- Edge: synonym matching, "As Per" sample numbers

#### T7.3: test_metric_calculations
- Given: 8 matched, 10 GT, 9 extracted
- recall = 0.8, precision = 0.889
- field_accuracy: mock field comparison

#### T7.4: test_report_generation
- Given: mock BenchmarkResult
- Output: valid markdown with expected table structure
- Contains: all metric columns, per-document sections

#### T7.5: test_harness_handles_missing_ground_truth
- Skip doc with missing ground-truth file + emit warning

### T8: Run full benchmark suite (LIVE — requires LLM API) [~30m]
- Command: `uv run python scripts/research/e29_benchmark_harness.py --all`
- Capture: baseline results JSON + markdown report
- Save: `docs/reviews/e29-baseline-benchmark-report.md`
- Verify: 3 entries in results

### T9: Verify CI entrypoint [~10m]
- `uv run pytest tests/integration/test_benchmark_harness.py -x -v` (unit tests pass without API)
- `uv run pytest benchmarks/ -x -v` (if any pytest-runnable benchmark tests exist)
- Document both entrypoints in story

### T10: Lint + full test suite [~10m]
- `uv run ruff check .`
- `uv run pytest tests/integration/test_benchmark_harness.py -x -v`

### T11: Update story Post-Dev Notes + sprint-status [~10m]
- E29-S2 story file: fill Post-Dev Notes with metric outputs, artifact paths
- sprint-status.yaml: `e29-s2-benchmark-harness-baseline-capture: review`
- Append session notes to findings.md / progress.md

## Files Changed (Planned)

| File | Action | Est Lines |
|------|--------|-----------|
| `benchmarks/__init__.py` | Add (new) | ~5 |
| `benchmarks/conftest.py` | Add (new) | ~30 |
| `benchmarks/ground_truth/broadmeadows.json` | Add (new) | ~200 |
| `benchmarks/ground_truth/alexander.json` | Add (new) | ~300 |
| `benchmarks/ground_truth/<third>.json` | Add (new) | ~50-200 |
| `scripts/research/e29_benchmark_harness.py` | Add (new) | ~400 |
| `tests/integration/__init__.py` | Add (new) | ~1 |
| `tests/integration/test_benchmark_harness.py` | Add (new) | ~200 |
| `docs/reviews/e29-baseline-benchmark-report.md` | Add (new, generated) | ~100 |
| `docs/sprint-artifacts/e29-s2-benchmark-harness-baseline-capture.md` | Update (Post-Dev Notes) | ~30 |
| `docs/sprint-artifacts/sprint-status.yaml` | Update (status) | ~2 |

## Risks

| Risk | Mitigation |
|------|------------|
| Third doc ground truth is labor-intensive | Keep scope minimal (smallest PDF), document as provisional |
| LLM non-determinism | Pin temperature=0, report median of multiple runs if variance high |
| Token capture fragile (OpenRouter Generation API) | Fallback: estimate from tiktoken input + output lengths |
| S1 not merged → Alexander baseline inaccurate | Document as known limitation; Gate 1 blocks on S1 anyway |

## Dependencies
- `fitz` (PyMuPDF) for PDF text extraction — already in deps
- `dotenv` for API key loading — already in deps
- LLM API key (OPENROUTER_API_KEY or ANTHROPIC_API_KEY) — for T8 only
- S1 NOT required for S2 development, only for Gate 1 pass
