# PR #55 — Qwen 2.5 & Extraction Quality Review

**Source:** Automated multi-agent code review (Feb 23, 2026)
**Branch under review:** `release` → `main` (PR #55 "Release: Sprint Feature Complete")
**Agents run:** code-reviewer · silent-failure-hunter · pr-test-analyzer
**Sprint context:** E18-S5 (NO ACCESS extraction), E18-S7 (Qwen 2.5 support), E18-S8 (taxonomy normalization)

---

## Summary

PR #55 introduces Qwen 2.5 model support across the extraction pipeline and adds three extraction quality improvements: NO ACCESS marker injection, fuse cartridge synonym normalization, and Qwen direct-JSON parsing. The review found **4 critical issues**, **6 high-severity issues**, **2 critical test gaps**, and **1 direct CLAUDE.md violation**.

The most severe finding is a cascade bug in `NO_ACCESS_PHRASES` replacement that produces corrupted preprocessed text — directly undermining the sprint's primary goal. Two promised test files (`test_preprocess_samp.py` and `test_qwen_extraction.py`) are absent from the branch.

---

## Critical Issues — Fix Before Merge

### C1. NO_ACCESS_PHRASES cascade creates multiple corrupt markers

**File:** `open_notebook/graphs/acm_extraction.py` — `_preprocess_samp_format()`
**Severity:** CRITICAL (confidence 96)

The `NO_ACCESS_PHRASES` list is applied sequentially with `re.sub`. After the first phrase is replaced with `NO_ACCESS_MARKER + "\n" + original_phrase`, the marker string contains the word `"No access"`. Subsequent iterations then match `"No access"` inside the already-injected marker text, producing 2–3 markers per entry.

For `"No access due to locked door"`:
- Iteration 1: `"No access due to locked door"` → 1 marker injected
- Iteration 2: `"No access due to"` matches inside the appended original phrase → 2nd marker
- Iteration 3: `"No access"` matches again → 3rd marker

The test `test_no_double_markers_for_longer_phrase` uses `>= 1` assertion specifically to avoid catching this regression. **This means the sprint's NO ACCESS extraction will produce spurious records.**

**Fix — replace sequential substitution with a single combined regex:**
```python
combined_pattern = "|".join(re.escape(p) for p in NO_ACCESS_PHRASES)
processed = re.sub(
    combined_pattern,
    lambda m: NO_ACCESS_MARKER + "\n" + m.group(0),
    processed,
    flags=re.IGNORECASE,
)
```

Also update `test_no_double_markers_for_longer_phrase` to assert `== 1` (not `>= 1`).

---

### C2. `model_family` is undefined if `_is_qwen_model` raises after provisioning succeeds

**File:** `open_notebook/graphs/acm_extraction.py` — `extract_records()`
**Severity:** CRITICAL (crash risk)

The PR structure is:
```python
try:
    model = await provision_langchain_model(...)
    is_qwen = _is_qwen_model(model)           # can raise AttributeError
    model_family = "qwen" if is_qwen else "default"
    ...
except Exception as e:
    return {"error": f"Model provisioning failed: {e}"}

# OUTSIDE the try/except:
system_prompt = prompter.render(data={..., "model_family": model_family, ...})
```

If `_is_qwen_model` throws (e.g., `AttributeError`), the except block returns early — but `model_family` was never assigned. The prompt rendering line then raises an unhandled `NameError`.

**Fix:**
```python
model_family = "default"   # safe default BEFORE try block
is_qwen = False

try:
    model = await provision_langchain_model(...)
    is_qwen = _is_qwen_model(model)
    model_family = "qwen" if is_qwen else "default"
    ...
```

---

### C3. `_early_qwen` detection silently swallowed by bare `except Exception:` at `debug` level

**File:** `open_notebook/graphs/acm_extraction.py` — `extract_records()`, inner try block
**Severity:** CRITICAL (silent degradation)

```python
try:
    _domain_model = await Model.get(model_id)
    _max_tokens = _domain_model.get_max_output_tokens(fallback=16384)
    _early_qwen = "qwen2.5" in (_domain_model.name or "").lower()
except Exception:
    logger.debug("Could not fetch Model capabilities...")
```

The bare `except Exception:` catches: DB connection errors, `asyncio.CancelledError` (breaks cooperative cancellation), `AttributeError` from unexpected model shapes. When it fires, `_early_qwen` stays `False`, silently disabling the Qwen path — logged only at `debug` (invisible in production).

**Fix:**
```python
from asyncio import CancelledError

try:
    _domain_model = await Model.get(model_id)
    _max_tokens = _domain_model.get_max_output_tokens(fallback=16384)
    _early_qwen = "qwen2.5" in (_domain_model.name or "").lower()
except CancelledError:
    raise  # never suppress cancellation
except Exception:
    logger.warning(
        f"Could not fetch Model capabilities for {model_id}; "
        "falling back to max_tokens=16384, Qwen2.5 path disabled"
    )
```

---

### C4. Qwen path in `_llm_extract_building` drops entire building on parse failure

**File:** `open_notebook/extractors/orchestrator.py` — `_llm_extract_building()`
**Severity:** CRITICAL (silent data loss)

The new `if is_qwen:` block has no try/except. A `ValueError` from `parse_json_response` (model returns prose) propagates to the outer `except Exception` in `extract_building`, which logs "extraction failed" and silently drops the entire building. Unlike `extract_records`, there is no fallback to structured output and no retry.

**Fix:** Add a try/except inside the Qwen block that logs the response preview before re-raising:
```python
if is_qwen:
    try:
        raw_response = await model.ainvoke(messages)
        response_text = (
            raw_response.content if hasattr(raw_response, "content")
            else str(raw_response)
        )
        parsed = parse_json_response(response_text)
        result = ACMExtractionResult.model_validate(parsed)
    except (ValueError, ValidationError) as qwen_err:
        logger.error(
            f"Building {plan.building_id} Qwen JSON parsing failed: {qwen_err}. "
            f"Response preview: {response_text[:200] if 'response_text' in dir() else 'N/A'}"
        )
        raise
```

---

## High-Severity Issues

### H1. Temperature mutation silently does nothing on frozen Pydantic models

**File:** `open_notebook/graphs/acm_extraction.py` — `_llm_correct_records()`

```python
if _is_qwen_model(model) and hasattr(model, "temperature"):
    model.temperature = 0.0   # silently fails on Pydantic v2 frozen models
```

LangChain v0.2+ uses Pydantic v2 frozen models — attribute assignment silently does nothing. Qwen correction runs at temperature 0.1 in production with no indication the override was ignored.

**Fix:** Use `_early_qwen` (or detect from model name) before provisioning and pass `temperature=0.0` directly to `provision_langchain_model`.

---

### H2. Circular import: `orchestrator.py` ↔ `acm_extraction.py`

`acm_extraction.py` imports from `orchestrator.py` at module level. The PR adds a deferred import going the other direction:
```python
from open_notebook.graphs.acm_extraction import _is_qwen_model  # inside function body
```

This creates a circular dependency that is fragile at runtime. **Fix:** Move `_is_qwen_model` to `open_notebook/graphs/utils.py` alongside `supports_tool_calling` and `parse_json_response`.

---

### H3. `except (ValidationError, Exception)` is logically `except Exception`

**File:** `open_notebook/graphs/acm_extraction.py` — line ~1207

`ValidationError` is a subclass of `Exception`. The combined clause catches everything, including timeouts and import errors, all logged at `warning`. Qwen JSON parse failures are indistinguishable from schema validation failures.

**Fix:** Split into separate except clauses with appropriate severity levels.

---

### H4. Stale `supports_tool_calling=True` for existing Qwen 2.5 DB records

**File:** `api/model_provisioning.py`

Removing `"qwen2.5"` from the `supports_tool_calling` heuristic only affects new model records. `find_or_create_model` returns early for existing records. Pre-provisioned Qwen 2.5 models retain `supports_tool_calling=True` in SurrealDB.

**Fix:** Add a migration or startup check to clear stale `supports_tool_calling` values for Qwen 2.5 models.

---

### H5. Fallback catch missing response text and context

**File:** `open_notebook/graphs/acm_extraction.py`

```python
except Exception as fallback_err:
    logger.warning(f"Fallback JSON parsing failed: {fallback_err}")
```

No source ID, no chunk index, no response text preview. Makes production debugging impossible.

**Fix:**
```python
except (ValueError, ValidationError) as fallback_err:
    logger.warning(
        f"Fallback JSON parsing failed for source={source_id} "
        f"chunk={current_index + 1}/{len(chunks)}: {fallback_err}. "
        f"Response preview: {response_text[:300]!r}"
    )
```

---

### H6. `parse_json_response` undocumented `json.JSONDecodeError` exception

**File:** `open_notebook/graphs/utils.py`

When the brace-depth matcher finds a structurally complete but syntactically invalid fragment, `json.loads` raises `json.JSONDecodeError`, not the documented `ValueError`. Callers catching only `ValueError` see unhandled exceptions.

**Fix:** Wrap `json.loads` and re-raise as `ValueError`:
```python
try:
    return json.loads(json_str)
except json.JSONDecodeError as e:
    raise ValueError(f"Found JSON-like structure but failed to parse: {e}") from e
```

---

## CLAUDE.md Violation

### V1. `parse_json_response` missing return type annotation

**File:** `open_notebook/graphs/utils.py:111`
**Rule:** `python-backend.md` — "Type hints: Required for all function parameters and returns"

```python
def parse_json_response(response_text: str):           # WRONG
def parse_json_response(response_text: str) -> dict[str, Any]:  # CORRECT
```

---

## Critical Test Gaps — Must Create Before Merge

### T1. `tests/test_preprocess_samp.py` is absent from the branch

The sprint artifact and PR description claim 14 tests were created covering:
- `NO_ACCESS_PHRASES` injection (including phrase ordering invariant)
- `PRODUCT_NORMALIZATIONS` regex
- Double-marker prevention

The file **does not exist**. These are the primary functional changes in the sprint, entirely untested at unit level.

**Must create with at minimum:**
```python
def test_no_access_single_marker_per_phrase():
    # Verify no duplicate markers for any phrase variant

def test_no_access_phrase_ordering_invariant():
    # Longer phrases must match before shorter ones

def test_product_normalization_fuse_cartridge():
    # "Fuse" → "Fuse Cartridge" normalization

def test_product_normalization_flange_joint():
    # flange/joint variants normalize correctly
```

---

### T2. `tests/test_qwen_extraction.py` is absent from the branch

Per sprint spec: unit tests for `_is_qwen_model()` and `parse_json_response()`. These gate fundamentally different execution paths and are untested.

**Must create with at minimum:**
```python
def test_is_qwen_model_ollama_format():    # "qwen2.5:32b" → True
def test_is_qwen_model_openrouter_format():  # "qwen/qwen2.5-32b-instruct" → True
def test_is_qwen_model_excludes_qwen3():   # "qwen3:32b" → False (documented exclusion)
def test_is_qwen_model_non_qwen():         # "gpt-4o" → False
def test_parse_json_response_fenced_block():
def test_parse_json_response_no_json_raises_value_error():
def test_parse_json_response_invalid_json_raises_value_error():
```

---

### T3. Deleted tests not replaced

`test_acm_ai_extraction.py` (deleted) — covered: chunking logic, deduplication keys, merge confidence, External/Internal area_type dedup, result normalization.

`test_acm_chat_context.py` (deleted) — covered: ACM prompt template conditional rendering, question-type detection patterns.

Neither is replaced in the PR's new test files. Review the deleted content and ensure critical behavioral tests are ported.

---

## Suggestions

- `verify_model_setup.py`: Show HTTP response body on errors; show response preview when JSON parsing fails; print unknown-provider error to `stderr` not `stdout`
- `_is_qwen_model`: Add `debug` log when no model name attribute is found (silent `False` return)
- `test_broadmeadows_e2e.py`: Add self-contained unit tests for `_match_extracted_to_expected()` three-tier logic (currently only covered via integration test requiring API key)
- `_split_building_by_rooms` ARA fallback path: add test coverage

---

## Positive Observations

- `test_taxonomy.py` is thorough with genuine behavioral tests across all product classification categories
- `test_broadmeadows_e2e.py` is a strong quality gate using a real reference PDF with correct "consumed extracted" matching
- `TOOL_CALLING_BLOCKLIST` in `utils.py` is explicit and centralised
- `parse_json_response` utility eliminates ~30 lines of duplicated logic
- `verify_model_setup.py` exits with non-zero status for CI use
- The Qwen path in `extract_records` logs record count — makes the code path observable

---

## Fix Priority Order

| Priority | Issue | File | Est. Complexity |
|----------|-------|------|-----------------|
| 1 | C1 — NO_ACCESS cascade bug + test fix | `acm_extraction.py` | Low |
| 2 | T1 — Create `test_preprocess_samp.py` | `tests/` | Medium |
| 3 | T2 — Create `test_qwen_extraction.py` | `tests/` | Medium |
| 4 | C2 — `model_family` undefined risk | `acm_extraction.py` | Low |
| 5 | C3 — CancelledError + debug→warning | `acm_extraction.py` | Low |
| 6 | C4 — Qwen path error handling in orchestrator | `orchestrator.py` | Low |
| 7 | H2 — Move `_is_qwen_model` to `utils.py` | `utils.py`, `orchestrator.py`, `acm_extraction.py` | Low |
| 8 | H1 — Temperature override fix | `acm_extraction.py` | Low |
| 9 | H3 — Split except clauses | `acm_extraction.py` | Low |
| 10 | H4 — DB migration for stale records | `migrations/` | Medium |
| 11 | H5, H6, V1 — Logging + type annotation | `acm_extraction.py`, `utils.py` | Low |
| 12 | T3 — Port deleted test behaviors | `tests/` | Medium |

---

## Verification Checklist

After implementing fixes, run:

```bash
# Backend tests
uv run pytest tests/test_preprocess_samp.py -v      # must pass (new file)
uv run pytest tests/test_qwen_extraction.py -v      # must pass (new file)
uv run pytest tests/test_taxonomy.py -v             # must still pass
uv run pytest tests/test_broadmeadows_e2e.py -v -m integration  # requires API key
uv run pytest tests/ -x                             # full suite, stop on first fail

# Lint
uv run ruff check open_notebook/graphs/acm_extraction.py
uv run ruff check open_notebook/graphs/utils.py
uv run ruff check open_notebook/extractors/orchestrator.py
uv run mypy open_notebook/graphs/utils.py

# Confirm no circular import
python -c "from open_notebook.extractors.orchestrator import plan_extraction"
python -c "from open_notebook.graphs.acm_extraction import extract_records"
```
