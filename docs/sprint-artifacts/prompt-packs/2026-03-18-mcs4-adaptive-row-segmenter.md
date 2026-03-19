# Multi-Consultant Story 4: Adaptive Row Segmenter
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 5 | Wave: 3 (parallel with Stories 3, 5) | Dependencies: Story 2 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 5.4, 5.5, Section 7 Story 4**

## Skills to Load

/planning-with-files — persistent markdown plan
/systematic-debugging — understand existing segmenter behavior before refactoring
/test-driven-development — TDD for refactored functions
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Story 2 complete (`InferredSchema` with `column_mapping`, `RecoveryConfig` exist)
- Read design doc Sections 5.4 (Adaptive Segmenter) and 5.5 (RecoveryConfig)

---

## Glossary

| Term | Definition |
|------|-----------|
| `COLUMN_ALIASES` | Flat dict in `row_segmenter.py` mapping raw column names to canonical field names (11 entries) |
| `_LEVEL_REGEX` | Regex matching English floor names (Ground, First, Second, etc.) — currently hardcoded |
| `detect_column_mapping()` | Function that fuzzy-matches PDF headers against COLUMN_ALIASES |
| `extra_mappings` | New parameter: explicit mapping from InferredSchema overrides fuzzy matching |
| `RecoveryConfig` | Dataclass with format-specific recovery settings (not_sampled_terms, restriction_terms) |
| `_recover_no_access_records()` | Recovery function for "No Access" records — currently hardcoded to Broadmeadows patterns |
| `_recover_not_sampled_records_ara()` | Recovery function for ARA "Not Sampled" records — currently hardcoded to Alexander patterns |
| Backward-compatible | Existing behavior unchanged when no InferredSchema provided |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Sections 5.4, 5.5, 6 (Extension Points)
- `open_notebook/extractors/row_segmenter.py` — COLUMN_ALIASES, detect_column_mapping(), segment_docling_table(), _LEVEL_REGEX
- `open_notebook/graphs/acm_extraction.py` — `_recover_no_access_records()`, `_recover_not_sampled_records_ara()`
- `open_notebook/graphs/utils.py` — `_split_content_by_char_budget()`, `_BUDGET_ROOM_RE`, `_BUDGET_ARA_RE`
- `open_notebook/extractors/recovery_config.py` — RecoveryConfig from Story 2

**Modify:**
- `open_notebook/extractors/row_segmenter.py` — add `extra_mappings` to `detect_column_mapping()`, add `level_regex` to `segment_docling_table()`
- `open_notebook/graphs/acm_extraction.py` — refactor `_recover_no_access_records()` and `_recover_not_sampled_records_ara()` to accept `RecoveryConfig`
- `open_notebook/graphs/utils.py` — accept boundary pattern in `_split_content_by_char_budget()`
- `open_notebook/extractors/orchestrator.py` — pass `InferredSchema` through pipeline

**Create:**
- `tests/test_adaptive_segmenter.py` — tests for new parameters

---

## Plan

Create `docs/sprint-artifacts/mcs4-adaptive-segmenter/task_plan.md`:
- [ ] Add `extra_mappings: dict[str, str] | None = None` to `detect_column_mapping()`
- [ ] Implement priority order: extra_mappings → COLUMN_ALIASES fuzzy → pass-through
- [ ] Add `level_regex: re.Pattern | None = None` to `segment_docling_table()`
- [ ] Implement `effective_level_re = level_regex or _LEVEL_REGEX`
- [ ] Refactor `_recover_no_access_records()` — accept `RecoveryConfig`, use its `not_sampled_terms`, `restriction_terms`
- [ ] Refactor `_recover_not_sampled_records_ara()` — accept `RecoveryConfig`, use its `section_header_re`
- [ ] Update `_split_content_by_char_budget()` — accept `content_boundary_re: re.Pattern | None`
- [ ] Wire `InferredSchema` through orchestrator → segmenter → recovery functions
- [ ] Write tests: `detect_column_mapping()` with and without `extra_mappings`
- [ ] Write tests: `segment_docling_table()` with custom `level_regex`
- [ ] Write tests: recovery functions with custom `RecoveryConfig`
- [ ] Verify backward compatibility: all existing tests still pass with no extra params
- [ ] Run full test suite + lint

---

## Agent Strategy: TMUX

```
Pane 0 (left):   Segmenter refactor — row_segmenter.py changes
Pane 1 (right):  Recovery refactor — acm_extraction.py recovery functions
Pane 2 (bottom): Test runner — continuous pytest
```

---

## Context7 Directives

1. resolve-library-id for "pydantic" → query-docs for "dataclass field default_factory"

---

## Verification Checklist

- [ ] `detect_column_mapping(headers, extra_mappings={"Room/Area": "room"})` uses explicit mapping
- [ ] `detect_column_mapping(headers)` (no extra_mappings) behaves identically to current code
- [ ] `segment_docling_table(json, level_regex=custom_re)` uses custom regex
- [ ] `segment_docling_table(json)` (no level_regex) uses `_LEVEL_REGEX` as before
- [ ] `_recover_no_access_records()` with default RecoveryConfig produces same results as before
- [ ] `_recover_not_sampled_records_ara()` with default RecoveryConfig produces same results as before
- [ ] `uv run pytest tests/test_adaptive_segmenter.py -v` — all pass
- [ ] `uv run pytest tests/ -x` — full suite passes (backward compatibility)
- [ ] `uv run ruff check .` — lint clean
- [ ] Broadmeadows benchmark: 31/31 records (no regression)

---

## Commit Template

```
refactor(extraction): make row segmenter and recovery functions format-adaptive

- Add extra_mappings param to detect_column_mapping() (priority over COLUMN_ALIASES)
- Add level_regex param to segment_docling_table() (override _LEVEL_REGEX)
- Refactor _recover_no_access_records() to accept RecoveryConfig
- Refactor _recover_not_sampled_records_ara() to accept RecoveryConfig
- All changes backward-compatible — defaults match existing hardcoded values
- Multi-Consultant Story 4 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
