---
epic: Epic 24
story_id: E24-S1
title: Activate TableFormer in Source Processing
status: drafted
priority: P0
effort: S/M (2 SP)
depends_on: none
---

As a compliance officer,
I want Docling's TableFormer model activated during PDF processing,
So that table structures in survey reports are accurately preserved and my extraction accuracy improves.

## Acceptance Criteria

- [ ] When `DOCLING_TABLE_STRUCTURE=true`, Docling uses TableFormer for PDF documents
- [ ] When `DOCLING_TABLE_STRUCTURE=false` (default), behavior is unchanged from current baseline
- [ ] `DOCLING_TABLE_MODE` environment variable controls mode (`accurate` default, `fast` available)
- [ ] `source.full_text` contains enhanced markdown with better table cell alignment, merged cell preservation, and multi-line value handling
- [ ] Processing completes within 60s for a typical SAMP PDF (~30 pages)
- [ ] Automatic fallback: if TableFormer model fails to load, Docling reverts to basic markdown mode
- [ ] Logger outputs `"TableFormer enabled: docling_table_structure=True, mode=accurate"` when flag is active
- [ ] `.env.example` updated with `DOCLING_TABLE_STRUCTURE` and `DOCLING_TABLE_MODE` entries

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

<!-- Implementation notes will be added by the dev agent -->
