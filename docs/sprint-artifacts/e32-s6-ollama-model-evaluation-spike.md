# E32-S6: Ollama Model Evaluation Spike — Tech Spec

## Story Summary

Research spike to evaluate three Ollama local models (llama3.1:8b, qwen2.5:7b, mistral:7b)
against Claude Sonnet on a 50-record ACM sample. The output is a benchmark script and a
documented recommendation of 1-2 models for production use in classification and enrichment
tasks within the Ollama-first extraction pipeline.

## Acceptance Criteria

- AC1: Test llama3.1:8b, qwen2.5:7b, mistral:7b for classification tasks (ACM_Classification, ACM_Sub_Classification, Friability)
- AC2: Test same models for enrichment tasks (room description normalization, Location_Details normalization, Room_Ref standardization)
- AC3: Benchmark accuracy vs Claude Sonnet on 50-record sample
- AC4: Document latency per model, VRAM usage, accuracy per task type
- AC5: Select 1-2 models for production use; note the recommendation in the capability registry section of `open_notebook/domain/models.py` comment block
- AC6: Spike results documented in `docs/spikes/ollama-model-evaluation.md`

---

## Technical Approach

### Overview

This is a self-contained research script. It does NOT modify any production code paths.
The script (`scripts/research/ollama_model_eval.py`) calls Ollama directly via its
OpenAI-compatible API at `http://localhost:11434/v1` using the `esperanto` `AIFactory`
with provider `"ollama"`. Claude Sonnet is the baseline, called via the same
`AIFactory` with provider `"anthropic"`.

The script:
1. Builds or loads a 50-record synthetic ACM sample (see "Test Data" section)
2. Runs two task types — classification and enrichment — against each model
3. Compares outputs to ground truth, measuring accuracy and latency
4. Reports VRAM usage from Ollama's `/api/ps` endpoint
5. Outputs a JSON result file and prints a markdown summary table

### Key Design Decisions

**Ollama API access.** Use Esperanto `AIFactory.create_language(provider="ollama", ...)`.
Ollama's base URL is `http://localhost:11434`. The script must check Ollama availability
with a simple HTTP GET to `http://localhost:11434/api/tags` before running. If Ollama is
unavailable, print a clear error and exit with code 1 (no silent mock-results).

**Baseline model.** Claude Sonnet (`claude-sonnet-4-20250514`) via Esperanto provider
`"anthropic"`. Requires `ANTHROPIC_API_KEY` in environment. If the key is absent, the
script skips the Sonnet baseline and notes it in the report.

**Task types.**

*Classification task* — given a raw ACM record (product name + material description),
ask the model to output a JSON object with three fields:
- `acm_classification`: one of the known ACM classification values from the domain
- `acm_sub_classification`: sub-classification value
- `friability`: "Friable" | "Non Friable" | null

*Enrichment task* — given a raw location string or room reference, ask the model to:
- Normalize `Location_Details` to standard form (e.g., "Roof void" → "Roof Void")
- Standardize `Room_Ref` (remove special characters, trim whitespace, apply title case)

**Accuracy scoring.**
- Classification: exact match on all three fields = 1.0, partial match = fractional score
- Enrichment: normalized string similarity (exact match after strip/lower = 1.0; otherwise 0.0 for this spike — keep it simple)
- Overall accuracy = mean score across all 50 records per task

**Latency.** Wall-clock time from `requests.post` to response received, measured per
record. Report mean and p95 (sorted list, index at 95th percentile). For Ollama models,
also capture tokens-per-second from Ollama response metadata if available.

**VRAM.** After loading each model (by running one warm-up inference), call
`GET http://localhost:11434/api/ps` and capture `size_vram` for the running model.
If the field is absent, record `null`.

**Output.** Write results to `scripts/research/results/ollama_eval_results.json`
(create the directory if it does not exist). Also print a markdown table to stdout.

**No DB, no pipeline.** This script runs standalone. Import `dotenv` and load `.env`
for API keys. Do not import anything from `open_notebook.database`. Minimize imports.

**qwen2.5:7b tool-calling note.** The existing codebase already has a `TOOL_CALLING_BLOCKLIST`
in `open_notebook/graphs/utils.py` that includes `"qwen2.5"`. For this spike, do NOT use
tool calling — use plain text prompts and parse the JSON from the response manually using
a simple regex/json.loads approach (mirrors `parse_json_response` in utils.py). This avoids
the tool-calling limitation and tests the models' raw JSON output capability.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `scripts/research/ollama_model_eval.py` | CREATE | Evaluation script — runs all models, produces JSON + markdown report |
| `scripts/research/results/.gitkeep` | CREATE | Ensure results directory is tracked (add to .gitignore for *.json) |
| `docs/spikes/ollama-model-evaluation.md` | CREATE | Spike results document — methodology, results table, recommendation |

**No production code changes.** The only optional follow-on is updating the comment
block in `open_notebook/domain/models.py` `_PROVIDER_DEFAULTS` to note the recommended
model(s), and updating `open_notebook/graphs/utils.py` `provision_extraction_fallback_model`
to list the winning Ollama model first in the Ollama candidates list. These are 2-line
changes and can be done as part of this story if a winner is clear.

---

## Implementation Notes

### Script Structure (`scripts/research/ollama_model_eval.py`)

```
scripts/research/ollama_model_eval.py
```

Top-level sections:

```
1. Imports and PROJECT_ROOT setup (mirror e29_benchmark_harness.py pattern)
2. Constants: OLLAMA_BASE_URL, MODELS_TO_TEST, BASELINE_MODEL, RESULTS_DIR
3. check_ollama_available() -> bool
4. get_ollama_vram(model_name: str) -> int | None
5. build_test_sample() -> list[dict]  (50 synthetic ACM records)
6. run_classification_task(model, records) -> TaskResult
7. run_enrichment_task(model, records) -> TaskResult
8. run_eval_for_model(model_name, provider, records) -> ModelResult
9. print_markdown_table(results: list[ModelResult])
10. save_json_results(results: list[ModelResult])
11. main()
```

### Test Data (`build_test_sample`)

Generate 50 synthetic ACM records as Python dicts. Each record must have:
- `product`: str — e.g. "Ceiling Tiles", "Pipe Lagging", "Floor Tiles"
- `material_description`: str — free text description
- `location_raw`: str — raw location string to normalize
- `room_ref_raw`: str — raw room reference
- `ground_truth_classification`: str
- `ground_truth_sub_classification`: str
- `ground_truth_friability`: "Friable" | "Non Friable"
- `ground_truth_location`: str — normalized form
- `ground_truth_room_ref`: str — standardized form

Use a hardcoded list of realistic but synthetic records (no real school data).
Include variety: mix of friable/non-friable, different classifications, edge cases
like null sub-classification, unusual location strings, mixed-case room refs.

Minimum 10 distinct product types across the 50 records.

### Prompt Design

**Classification prompt (system):**
```
You are an ACM (Asbestos Containing Material) classification expert.
Given an ACM product name and material description, output ONLY a JSON object
with exactly these fields:
- "acm_classification": the ACM material classification
- "acm_sub_classification": the sub-classification, or null if unknown
- "friability": "Friable", "Non Friable", or null

Do not include any explanation. Output only valid JSON.
```

**Classification prompt (user):**
```
Product: {product}
Material Description: {material_description}

Classify this ACM item.
```

**Enrichment prompt (system):**
```
You are an ACM data normalization assistant.
Given raw location and room reference strings from an asbestos register,
output ONLY a JSON object with:
- "location_normalized": the standardized location string (title case, no special chars)
- "room_ref_standardized": the standardized room reference (title case, trimmed)
```

**Enrichment prompt (user):**
```
Location (raw): {location_raw}
Room Reference (raw): {room_ref_raw}

Normalize these values.
```

### Esperanto Model Instantiation

```python
from esperanto import AIFactory

# Ollama model
model = AIFactory.create_language(
    model_name="llama3.1:8b",
    provider="ollama",
    config={"temperature": 0.0, "max_tokens": 512},
)
lc_model = model.to_langchain()

# Anthropic baseline
model = AIFactory.create_language(
    model_name="claude-sonnet-4-20250514",
    provider="anthropic",
    config={"temperature": 0.0, "max_tokens": 512},
)
lc_model = model.to_langchain()
```

Then invoke with LangChain messages:
```python
from langchain_core.messages import HumanMessage, SystemMessage
response = lc_model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
raw_text = response.content
```

Parse JSON from `raw_text` using a simple fallback:
```python
import json, re
def parse_json(text: str) -> dict:
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(text)
```

### VRAM Measurement

```python
import requests

def get_ollama_vram(model_name: str) -> int | None:
    try:
        resp = requests.get("http://localhost:11434/api/ps", timeout=5)
        for m in resp.json().get("models", []):
            if m.get("name", "").startswith(model_name.split(":")[0]):
                return m.get("size_vram")
    except Exception:
        return None
```

### Latency Measurement

```python
import time
start = time.perf_counter()
response = lc_model.invoke([...])
latency_s = time.perf_counter() - start
```

Collect all per-record latencies into a list, then compute:
```python
latencies.sort()
mean_latency = sum(latencies) / len(latencies)
p95_latency = latencies[int(len(latencies) * 0.95)]
```

### Results Data Structure

```python
@dataclass
class TaskResult:
    task_name: str           # "classification" or "enrichment"
    accuracy: float          # 0.0 - 1.0
    mean_latency_s: float
    p95_latency_s: float
    error_count: int         # records that failed to parse JSON

@dataclass
class ModelResult:
    model_name: str
    provider: str
    vram_bytes: int | None
    classification: TaskResult
    enrichment: TaskResult
```

### Markdown Table Output Format

```
| Model           | Provider  | VRAM  | Class. Acc | Enrich. Acc | Class. Latency (p95) | Enrich. Latency (p95) |
|-----------------|-----------|-------|------------|-------------|---------------------|----------------------|
| llama3.1:8b     | ollama    | 5.2GB | 72%        | 81%         | 3.4s                | 2.1s                 |
| qwen2.5:7b      | ollama    | 5.0GB | 78%        | 85%         | 2.8s                | 1.9s                 |
| mistral:7b      | ollama    | 4.8GB | 65%        | 77%         | 3.1s                | 2.3s                 |
| claude-sonnet   | anthropic | n/a   | 96%        | 98%         | 1.8s                | 1.2s                 |
```

### Documentation File (`docs/spikes/ollama-model-evaluation.md`)

The dev agent writes this file AFTER running the script with real data. Structure:

```markdown
# Ollama Model Evaluation — Spike Results

## Evaluation Date
YYYY-MM-DD

## Methodology
[Brief description: 50 synthetic records, two task types, Sonnet baseline]

## Models Tested
- llama3.1:8b
- qwen2.5:7b
- mistral:7b
- claude-sonnet-4-20250514 (baseline)

## Results

### Classification Task
[Markdown table from script output]

### Enrichment Task
[Markdown table from script output]

## VRAM Usage
[Table: model → VRAM GB]

## Recommendation
**Production models: [1-2 model names]**

Rationale: [1-2 sentences explaining the choice based on accuracy/VRAM tradeoff]

## Impact on Capability Registry
- Update `provision_extraction_fallback_model()` in `open_notebook/graphs/utils.py`
  to list `[winning model]` first in the Ollama candidates
- Add entry to `_PROVIDER_DEFAULTS` in `open_notebook/domain/models.py` if not present

## Accuracy Gap vs Claude Sonnet
[Delta table: classification gap, enrichment gap — to quantify production risk]
```

### Optional: Capability Registry Update

If a clear winner emerges (accuracy >= 75% on both tasks), update
`open_notebook/graphs/utils.py` in `provision_extraction_fallback_model`:

```python
# Ollama local fallbacks — qwen2.5:7b recommended (E32-S6 spike)
if os.getenv("OLLAMA_API_BASE"):
    candidates.extend(
        [
            ("ollama", "qwen2.5:7b"),   # move winning model first
            ("ollama", "qwen2.5:32b"),
            ("ollama", "qwen3:32b"),
        ]
    )
```

This is a 2-line change. Only do this if the spike data supports it.

---

## Test Plan

This is a spike — verification is outcome-based, not unit-test-based.

**AC1/AC2 — Models tested.**
Run the script and confirm all three Ollama models complete both task types without
crashing. The JSON result file must contain entries for all three models.

**AC3 — Baseline comparison.**
Confirm the JSON result file contains a `claude-sonnet-4-20250514` entry with
accuracy metrics for both tasks. If Anthropic key unavailable, note in report and
mark AC3 as "skipped — no API key".

**AC4 — Metrics captured.**
Confirm JSON result has `mean_latency_s`, `p95_latency_s`, `vram_bytes`,
`accuracy` for each model x task combination.

**AC5 — Recommendation made.**
The `docs/spikes/ollama-model-evaluation.md` must have a "Recommendation" section
naming 1-2 models. If no model exceeds 70% accuracy on both tasks, recommend
"none — escalate to E32-S7 investigation" and note in the sprint retrospective.

**AC6 — Docs file exists.**
`docs/spikes/ollama-model-evaluation.md` must exist and be non-empty.

### Verification Commands

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Run the spike (Ollama must be running)
uv run python scripts/research/ollama_model_eval.py

# Verify outputs exist
ls scripts/research/results/ollama_eval_results.json
ls docs/spikes/ollama-model-evaluation.md

# Lint check (no production code changes so this is quick)
uv run ruff check scripts/research/ollama_model_eval.py
```

### If Ollama Is Not Available

The script must detect this and print:
```
ERROR: Ollama is not running at http://localhost:11434.
Start Ollama with: ollama serve
Then pull models:
  ollama pull llama3.1:8b
  ollama pull qwen2.5:7b
  ollama pull mistral:7b
Exiting.
```
Do not proceed with mocked results — the spike deliverable requires real model data.

---

## Dev Agent Record

**Status**: Ready for dev
**Risk**: LOW
**Estimated effort**: 2 SP
**Sprint**: V3-3
**Dependencies**: GATE:SCHEMA_FREEZE (unlocked 2026-03-03)
**Key files to create**:
- `scripts/research/ollama_model_eval.py`
- `docs/spikes/ollama-model-evaluation.md`

**Pre-flight checklist for dev agent:**
- [ ] Ollama running at `http://localhost:11434`
- [ ] Models pulled: `ollama pull llama3.1:8b && ollama pull qwen2.5:7b && ollama pull mistral:7b`
- [ ] `ANTHROPIC_API_KEY` in `.env` (for Sonnet baseline)
- [ ] `uv run python scripts/research/ollama_model_eval.py` completes without crash
- [ ] `scripts/research/results/ollama_eval_results.json` written
- [ ] `docs/spikes/ollama-model-evaluation.md` populated with real results and recommendation
- [ ] `uv run ruff check scripts/research/ollama_model_eval.py` passes
