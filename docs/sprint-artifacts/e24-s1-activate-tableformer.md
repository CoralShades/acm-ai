---
epic: Epic 24
story_id: E24-S1
title: Activate TableFormer in Source Processing
status: done
priority: P0
effort: S/M (2 SP)
depends_on: none
completed: 2026-02-27
commit: 3c31fda
---

As a compliance officer,
I want Docling's TableFormer model activated during PDF processing,
So that table structures in survey reports are accurately preserved and my extraction accuracy improves.

## Acceptance Criteria

- [x] When `DOCLING_TABLE_STRUCTURE=true`, Docling uses TableFormer for PDF documents
- [x] When `DOCLING_TABLE_STRUCTURE=false` (default), behavior is unchanged from current baseline
- [x] `DOCLING_TABLE_MODE` environment variable controls mode (`accurate` default, `fast` available)
- [ ] `source.full_text` contains enhanced markdown with better table cell alignment, merged cell preservation, and multi-line value handling *(deferred to E24-S2 validation)*
- [ ] Processing completes within 60s for a typical SAMP PDF (~30 pages) *(deferred to E24-S2 validation)*
- [x] Automatic fallback: if TableFormer model fails to load, Docling reverts to basic markdown mode *(Docling built-in behavior)*
- [x] Logger outputs `"TableFormer enabled: docling_table_structure=True, mode=accurate"` when flag is active
- [x] `.env.example` updated with `DOCLING_TABLE_STRUCTURE` and `DOCLING_TABLE_MODE` entries

## Technical Notes

### Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/source.py` | Add TableFormer configuration in `content_process()` |
| `.env.example` | Add `DOCLING_TABLE_STRUCTURE=false` and `DOCLING_TABLE_MODE=accurate` |

### Implementation Pattern

Follow Winston's technical design (Section 2A):

```python
import os

# Inside content_process():
table_structure_enabled = os.environ.get(
    "DOCLING_TABLE_STRUCTURE", "false"
).lower() == "true"

if table_structure_enabled:
    content_state["document_engine"] = "docling"
    content_state["docling_table_structure"] = True
    content_state["docling_table_mode"] = os.environ.get(
        "DOCLING_TABLE_MODE", "accurate"
    )
    logger.info("TableFormer enabled: docling_table_structure=True, mode=accurate")
else:
    content_state["document_engine"] = (
        content_settings.default_content_processing_engine_doc or "auto"
    )
```

### Key Design Decisions

1. **Environment variable control** — enables A/B testing without code changes
2. **Explicit `document_engine = "docling"`** — required when activating TableFormer (auto may select non-Docling)
3. **Default OFF** — ship with `false` default for safe rollout; promote after validation (E24-S2)

### Timing Safety

TableFormer runs inside `content_process()` (Docling's internal pipeline), NOT as a separate post-processing step. Processing time increases from ~5s to ~20-35s, well within the 120s `acm_extract` polling timeout in `acm_commands.py`.

### Tests

- Unit: `content_process()` sets correct `content_state` keys when env var is true
- Unit: `content_process()` does NOT set TableFormer keys when env var is false/absent
- Integration: Process a PDF with flag on, verify `full_text` contains enhanced table markdown

## Dependencies

- None (zero new dependencies — torch 2.10.0, Docling, TableFormer all installed)

## References

- ADR-001: `docs/architecture/adr-tableformer-integration.md` (Decision D1)
- Technical Design Section 2A: `docs/architecture/tableformer-technical-design.md`
- Research Spike: `docs/research/tableformer-research-spike-20260227.md`

## Dev Notes

### Implementation (2026-02-27) — Commit 3c31fda

**Files Changed (3):**

| File | Change |
|------|--------|
| `open_notebook/graphs/source.py` | Added `import os` + TableFormer configuration block in `content_process()` replacing the static `document_engine` assignment |
| `.env.example` | Added `DOCLING_TABLE_STRUCTURE=false` and `DOCLING_TABLE_MODE=accurate` with full documentation |
| `tests/test_source_graph.py` | **New** — 7 unit tests covering feature flag on/off/absent/case-insensitive/custom-mode |

**Implementation Details:**

The existing `content_state["document_engine"] = "auto"` line (L57-59) was replaced with an environment-variable-controlled block:

- Reads `DOCLING_TABLE_STRUCTURE` env var (default: `"false"`)
- When `"true"` (case-insensitive): forces `document_engine = "docling"`, sets `docling_table_structure = True`, reads `DOCLING_TABLE_MODE` (default: `"accurate"`)
- When `"false"` or absent: original behavior preserved (`content_settings.default_content_processing_engine_doc or "auto"`)
- Logs activation message via `logger.info()` when enabled

**Test Results:**

| Check | Result |
|-------|--------|
| `uv run ruff check` | All checks passed |
| `tests/test_source_graph.py` (7 tests) | 7/7 passed |
| Full test suite (1004 deterministic tests) | 1004 passed, 0 failed, 2 xfailed |
| `cd frontend && npm run build` | Compiled successfully (27 pages) |

**Pre-existing Failures (not caused by this change):**
- `test_broadmeadows_e2e.py` — 28/31 (90.3%), the known baseline this epic targets
- `test_page_tagger.py::test_tag_pages_heuristic_fallback` — flaky live LLM test
- `test_page_tagger.py::test_tag_pages_with_building_inventory` — flaky live LLM test

**What was NOT changed (per spec):**
- No changes to `acm_extraction.py` (LangGraph pipeline)
- No changes to `orchestrator.py`
- No changes to prompts
- No new dependencies added
- Default is `false` — safe rollout
