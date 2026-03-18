# Multi-Consultant Story 1: Fix Critical Bugs — Detector Architecture Cleanup
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 3 | Wave: 1 | Dependencies: Pack 6 (SAMP→ARA rename) complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 7 Story 1**

## Skills to Load

/planning-with-files — persistent markdown plan
/systematic-debugging — structured root-cause for broken imports
/find-bugs — discover related broken patterns
/test-driven-development — TDD for detector regression tests
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Pack 6 (SAMP→ARA) complete — `samp_detector.py` renamed to `standard_detector.py`
- Read design doc: `docs/architecture/multi-consultant-format-design.md` (Section 3.1 HIGH patterns, Section 7 Story 1)
- No services needed — code-only changes

---

## Critical Context: Detectors Must Be Named By Structure, Not Consultant

**All documents are ARA (Asbestos Register Assessment) documents.** Different consultants produce different *table structures*. Detectors must be named by what they structurally detect, never by consultant name.

Current naming is wrong:

| Current | Detects | Should Be Named |
|---------|---------|----------------|
| `ClutchDetector` | Pipe-delimited tables (`\| Building Name: \|`) | `PipeTableDetector` |
| `ARADetector` | Text-header format (`Building Name:\n<value>`) | `TextHeaderDetector` |
| `StandardFormatDetector` | B###/D## coded building IDs | OK as-is (named by structure) |
| `LLMDetector` | Fallback LLM classification | OK as-is |

**The `ClutchDetector` has a broken import** — it imports `_CLUTCH_BUILDING_NAME_PATTERN` and `_CLUTCH_LEVEL_SUFFIX` from `building_inventory.py` but these symbols don't exist. This means any PDF with pipe-table format **silently crashes** and falls through to the wrong detector, getting the wrong column mapping and building extraction.

**Misdetection risk:** The detectors run by priority (pipe-table=5, standard=10, text-header=20). But since the pipe-table detector crashes, pipe-table documents fall to `StandardFormatDetector` (wrong — no B### headers) → then to `ARADetector` (partially matches if `Building Name:` appears as text too). Result: wrong column mapping, wrong building boundaries, degraded extraction.

**The same consultant (e.g., Greencap) might produce either pipe-table OR text-header format** depending on site/version. Naming detectors after consultants creates false associations. The LLM detector prompt (line 56) also lists `"clutch"` as a known format — this must change.

---

## Glossary

| Term | Definition |
|------|-----------|
| Format detector | Module in `format_detectors/` that identifies **table structure** from PDF content |
| PipeTableDetector | Detects pipe-delimited table format (`\| Building Name: \| ... \| Number of Levels: \|`) — renamed from ClutchDetector |
| TextHeaderDetector | Detects text-header format (`Building Name:\n<value>`) — renamed from ARADetector |
| StandardFormatDetector | Detects DET-style B###/D## building ID headers — already correctly named |
| LLMDetector | Fallback LLM-based format classifier when heuristic detectors fail |
| `_detect_ara_buildings()` | Function duplicated in both `building_inventory.py` and the text-header detector |
| FormatRegistry | Singleton in `__init__.py` that registers detectors and runs them by priority |

---

## Current State

- `clutch_detector.py` imports `_CLUTCH_BUILDING_NAME_PATTERN` and `_CLUTCH_LEVEL_SUFFIX` from `building_inventory.py` — **these symbols don't exist** → `ImportError` crashes the detector silently
- `_auto_register()` in `__init__.py` imports and registers `ClutchDetector` — this crashes at import time
- `_detect_ara_buildings()` is duplicated in both `building_inventory.py:391` AND `ara_detector.py:89`
- `llm_detector.py` line 56 tells the LLM that `"clutch"` is a known format name
- No regression tests exist for any detector
- All detector names use consultant names instead of structural descriptions

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — full design
- `open_notebook/extractors/format_detectors/__init__.py` — registry, `_auto_register()`
- `open_notebook/extractors/format_detectors/clutch_detector.py` — broken import, pipe-table detection logic
- `open_notebook/extractors/format_detectors/ara_detector.py` — text-header detection, duplicated `_detect_ara_buildings`
- `open_notebook/extractors/format_detectors/standard_detector.py` — B###/D## detection
- `open_notebook/extractors/format_detectors/llm_detector.py` — LLM fallback with wrong format names
- `open_notebook/extractors/building_inventory.py` — has `_detect_ara_buildings()` original + missing symbols

**Rename + Fix:**
- `clutch_detector.py` → `pipe_table_detector.py` — rename class to `PipeTableDetector`, fix broken imports, rename `name` to `"pipe_table"`
- `ara_detector.py` → `text_header_detector.py` — rename class to `TextHeaderDetector`, rename `name` to `"text_header"`, keep `_detect_ara_buildings` as canonical
- `__init__.py` — update imports and registrations for renamed detectors
- `llm_detector.py` — update format names in LLM prompt: `"clutch"` → `"pipe_table"`, `"ara"` → `"text_header"`

**Modify:**
- `building_inventory.py` — remove duplicated `_detect_ara_buildings()`, delegate to text-header detector. Define `_PIPE_TABLE_BUILDING_NAME_PATTERN` and `_PIPE_TABLE_LEVEL_SUFFIX` (the symbols the pipe-table detector needs)

**Create:**
- `tests/test_format_detectors.py` — regression tests for all detectors

---

## Plan

Create `docs/sprint-artifacts/mcs1-fix-bugs/task_plan.md`:
- [ ] Read all 4 detector modules + `building_inventory.py` to understand current state
- [ ] Define the missing symbols in `building_inventory.py` (or in the pipe-table detector itself): `_PIPE_TABLE_BUILDING_NAME_PATTERN` regex for `| Building Name: | <value> |` and `_PIPE_TABLE_LEVEL_SUFFIX` regex
- [ ] Rename `clutch_detector.py` → `pipe_table_detector.py`, class `PipeTableDetector`, `name = "pipe_table"`
- [ ] Fix the broken import — update to use the new symbol names
- [ ] Rename `ara_detector.py` → `text_header_detector.py`, class `TextHeaderDetector`, `name = "text_header"`
- [ ] Deduplicate `_detect_ara_buildings()` — canonical in `text_header_detector.py`, delegate from `building_inventory.py`
- [ ] Update `__init__.py` — new imports, registrations: `PipeTableDetector()`, `StandardFormatDetector()`, `TextHeaderDetector()`
- [ ] Update `llm_detector.py` line 56 — format names: `"pipe_table"` (pipe-delimited tables), `"text_header"` (Building Name: text headers), `"standard"` (B###/D## headers)
- [ ] Search codebase for any other references to `"clutch"`, `ClutchDetector`, `"ara"` as format name (not document type) — update all
- [ ] Write regression tests for `PipeTableDetector` (pipe-delimited detection + building extraction)
- [ ] Write regression tests for `TextHeaderDetector` (text-header detection + building extraction)
- [ ] Write regression tests for `StandardFormatDetector` (B###/D## detection)
- [ ] Write regression test for `LLMDetector` fallback
- [ ] Run full test suite: `uv run pytest tests/ -x`
- [ ] Run lint: `uv run ruff check .`

---

## Agent Strategy: TMUX

```
Pane 0 (left):   Implementation — rename files, fix imports, define missing symbols
Pane 1 (right):  Test runner — continuous `uv run pytest tests/test_format_detectors.py -v`
Pane 2 (bottom): Research — grep for all references to old names, trace import chains
```

---

## Context7 Directives

1. resolve-library-id for "pydantic" → query-docs for "model_validate dataclass Protocol"
2. resolve-library-id for "docling" → query-docs for "DoclingDocument TableItem table extraction"

---

## Verification Checklist

- [ ] `clutch_detector.py` no longer exists — replaced by `pipe_table_detector.py`
- [ ] `ara_detector.py` no longer exists — replaced by `text_header_detector.py`
- [ ] `python -c "from open_notebook.extractors.format_detectors.pipe_table_detector import PipeTableDetector"` — no ImportError
- [ ] `python -c "from open_notebook.extractors.format_detectors.text_header_detector import TextHeaderDetector"` — no ImportError
- [ ] `_detect_ara_buildings()` exists in only ONE location (canonical in `text_header_detector.py`)
- [ ] `building_inventory.py` delegates to `text_header_detector.py` for text-header building detection
- [ ] `llm_detector.py` prompt uses `"pipe_table"`, `"text_header"`, `"standard"` — no `"clutch"` or `"ara"` as format names
- [ ] `grep -ri "clutch" open_notebook/` returns 0 results
- [ ] `grep -ri "ClutchDetector" .` returns 0 results (except git history)
- [ ] `uv run pytest tests/test_format_detectors.py -v` — all detector tests pass
- [ ] `uv run pytest tests/ -x` — full suite passes (no regression)
- [ ] `uv run ruff check .` — lint clean
- [ ] Each detector has ≥3 test cases (positive match, negative match, edge case)

---

## Commit Template

```
refactor(detectors): rename detectors by structure not consultant, fix broken pipe-table import

- Rename clutch_detector → pipe_table_detector (PipeTableDetector, name="pipe_table")
- Rename ara_detector → text_header_detector (TextHeaderDetector, name="text_header")
- Fix broken import: define _PIPE_TABLE_BUILDING_NAME_PATTERN (was undefined)
- Deduplicate _detect_ara_buildings() — canonical in text_header_detector
- Update LLM detector prompt with structural format names
- Add regression tests for all 3 detectors + LLM fallback
- Multi-Consultant Story 1 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
