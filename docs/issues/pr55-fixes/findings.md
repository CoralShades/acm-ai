# Findings: PR #55 Bug Fix Session (2026-02-23)

## Baseline Test State
- `test_preprocess_samp.py` — 14 tests, all PASS (but test_no_double_markers uses `>= 1`, masks the bug)
- `test_qwen_extraction.py` — 13 tests, all PASS
- Python: Windows venv at `.venv/Scripts/python.exe` (WSL2 can't run Linux Python for these tests)

## C1 — NO_ACCESS Cascade Bug
**File:** `open_notebook/graphs/acm_extraction.py` lines 367–386
**Current code:** Sequential `for phrase in NO_ACCESS_PHRASES: re.sub(...)` loop.
**Problem:** After phrase "No access due to locked door" is replaced with `MARKER + "\n" + phrase`,
the text now contains "No access" (in the appended original phrase). Subsequent iterations match
"No access" inside the already-injected marker → 2–3 markers per entry.
**Fix:** Replace loop with single combined alternation regex (longest-first ordering ensures correct match).

## C2 — model_family NameError risk
**File:** `acm_extraction.py`, `extract_records()` around line 1085
**Problem:** `model_family` is only assigned inside the `try` block (line 1109). If `_is_qwen_model` raises, the except block returns early — but `model_family` is referenced OUTSIDE the try (line 1138). → NameError
**Fix:** Initialize `model_family = "default"` BEFORE outer try block.

## C3 — CancelledError swallowed
**File:** `acm_extraction.py`, inner try/except around line 1090–1098
**Problem:** `except Exception:` catches asyncio.CancelledError; only logs at DEBUG level.
**Fix:** Add `except CancelledError: raise` before generic except; change debug→warning.

## C4 — Qwen block in orchestrator has no error handling
**File:** `open_notebook/extractors/orchestrator.py` lines 404–417
**Problem:** `parse_json_response` can raise ValueError; ValidationError can come from model_validate.
These propagate to outer `except Exception` in extract_building → silently drops building.
**Fix:** Wrap Qwen block with try/except (ValueError, ValidationError) with logging + re-raise.

## H1 — Temperature mutation on frozen Pydantic model
**File:** `acm_extraction.py` `_llm_correct_records()` line 1842
**Current:** `model.temperature = 0.0` after provisioning — silently fails on frozen Pydantic v2.
**Fix:** Use `_early_qwen`-style detection to detect Qwen before provisioning.
But `_llm_correct_records` doesn't have early model info. Solution: detect from model_id string
OR use `_is_qwen_model` result. The safest fix per PR spec: pass `temperature=0.0` via
provision call when model is detected as Qwen. The `_is_qwen_model` detection happens AFTER
provision, so we need a pre-provision check. Since `_llm_correct_records` has `model_id`,
we can check the domain model name before provisioning (same pattern as `_early_qwen`).

## H2 — Circular import
**Current:** `_is_qwen_model` defined in `acm_extraction.py`; `orchestrator.py` does deferred import from there.
**Fix:** Move to `utils.py` (alongside `parse_json_response`). Both files import from utils already.

## H3 — except (ValidationError, Exception) is logically except Exception
**File:** `acm_extraction.py` line 1279
**Fix:** Split into `except ValidationError` and `except Exception` with different severity/message.

## H5 — Fallback catch missing context
**File:** `acm_extraction.py` line 1352
**Current:** `except Exception as fallback_err: logger.warning(f"Fallback JSON parsing failed: {fallback_err}")`
**Fix:** Include source_id, chunk info, response_text preview.

## H6 + V1 — parse_json_response in utils.py
**H6:** `json.loads` can raise `json.JSONDecodeError` (not ValueError). Callers only catch ValueError.
**Fix:** Wrap in try/except json.JSONDecodeError → re-raise as ValueError.
**V1:** Missing `-> dict[str, Any]` return type annotation.
