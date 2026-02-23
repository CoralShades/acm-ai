# Task Plan: PR #55 Bug Fixes (2026-02-23)

**Goal:** Fix all critical/high issues from `docs/issues/pr55-qwen25-extraction-quality-review.md`
**Session:** Dev Agent (Amelia) — BMad dev workflow
**Planning dir:** `docs/issues/pr55-fixes/`

---

## Status Summary

| Issue | Status | File |
|-------|--------|------|
| C1 – NO_ACCESS cascade (single-pass regex) | ✅ DONE | `acm_extraction.py` |
| Test: `test_no_double_markers` → assert == 1 | ✅ DONE | `test_preprocess_samp.py` |
| T1 – `test_preprocess_samp.py` exists? | ✅ EXISTS + 14/14 pass | tests/ |
| T2 – `test_qwen_extraction.py` exists? | ✅ EXISTS + 13/13 pass | tests/ |
| C2 – `model_family = "default"` before try | ✅ DONE | `acm_extraction.py` |
| C3 – CancelledError + debug→warning | ✅ DONE | `acm_extraction.py` |
| C4 – Qwen try/except in orchestrator | ✅ DONE | `orchestrator.py` |
| H2 – Move `_is_qwen_model` → utils.py | ✅ DONE + isinstance guard added | `utils.py` |
| H1 – Temperature param at provision time | ✅ DONE | `acm_extraction.py` |
| H3 – Split except (ValidationError, Exception) | ✅ DONE | `acm_extraction.py` |
| H5 – Improve fallback logging | ✅ DONE | `acm_extraction.py` |
| H6 – JSONDecodeError → ValueError wrap | ✅ DONE | `utils.py` |
| V1 – Return type on parse_json_response | ✅ DONE | `utils.py` |
| H4 – DB migration stale qwen records | ⏭️ SKIP (requires migration, out of scope) | `migrations/` |
| BONUS – `_is_qwen_model` isinstance guard for mock safety | ✅ DONE | `utils.py` |

---

## Phases

### Phase 0 — Research (COMPLETE)
- [x] Read PR review doc
- [x] Read source files
- [x] Run tests to baseline
- [x] Audit what's fixed vs outstanding

### Phase 1 — C1: NO_ACCESS Single-Pass Regex (HIGHEST PRIORITY)
- [ ] Fix `_preprocess_samp_format()` in `acm_extraction.py` (lines ~367-386)
- [ ] Update `test_no_double_markers_for_longer_phrase` to `== 1`
- [ ] Run `test_preprocess_samp.py` → all pass

### Phase 2 — utils.py fixes (H6, V1)
- [ ] Wrap `json.loads` in `parse_json_response` to re-raise as ValueError
- [ ] Add `-> dict[str, Any]` return type
- [ ] Run `test_qwen_extraction.py` → all pass

### Phase 3 — H2: Move _is_qwen_model to utils.py
- [ ] Add `_is_qwen_model` to `utils.py`
- [ ] Remove from `acm_extraction.py`; add import from utils
- [ ] Remove deferred import in `orchestrator.py`; add top-level import from utils
- [ ] Verify import: `python -c "from open_notebook.extractors.orchestrator import plan_extraction"`

### Phase 4 — acm_extraction.py fixes (C2, C3, H1, H3, H5)
- [ ] C2: Add `model_family = "default"` before outer try
- [ ] C3: Add CancelledError re-raise + debug→warning in inner except
- [ ] H1: Replace temperature mutation with `temperature=0.0` param in `_llm_correct_records`
- [ ] H3: Split `except (ValidationError, Exception)` into two clauses
- [ ] H5: Improve fallback catch with source_id, chunk info, response preview

### Phase 5 — C4: Qwen error handling in orchestrator.py
- [ ] Wrap Qwen block with try/except (ValueError, ValidationError)
- [ ] Log building_id and response preview on failure before re-raise

### Phase 6 — Final verification
- [ ] `uv run ruff check open_notebook/` → no violations
- [ ] All tests pass: `test_preprocess_samp.py`, `test_qwen_extraction.py`
- [ ] Full suite: `tests/ -x`
- [ ] Import checks

---

## Key File Locations
- `open_notebook/graphs/acm_extraction.py` — main target
- `open_notebook/graphs/utils.py` — parse_json_response + _is_qwen_model (after move)
- `open_notebook/extractors/orchestrator.py` — C4 fix
- `tests/test_preprocess_samp.py` — assert fix
