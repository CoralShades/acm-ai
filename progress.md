# Progress — E27-S2: SSE/AG-UI Pipeline Visibility

## Session: 2026-02-28
### Status: COMPLETE

### Backend
- `pipeline_events.py`: Added `DOCLING_EXTRACTION` and `NO_ACCESS_RECOVERY` to StageId enum + STAGE_METADATA
- `source_commands.py`: Instrumented `_extract_tables_with_docling()` with optional PipelineLogger (stage_enter/complete/fail)
- `acm_extraction.py`: Instrumented `recover_no_access_node()` with PipelineLogger + AGUIEventEmitter (stage_enter/complete/skip)
- `agent.json`: Updated A2A agent card with extraction capabilities, 9 pipeline stages, docling + recovery methods

### Frontend
- `pipeline.ts`: StageId type expanded to 9 values, PIPELINE_STAGE_ORDER + PIPELINE_STAGE_LABELS updated
- `StageProgressPill.tsx`: STAGE_LABELS includes DOCLING_EXTRACTION and NO_ACCESS_RECOVERY
- `ExtractionProgressPanel.tsx`: STAGE_CONFIG includes new stages with TableProperties + Search icons

### Tests
- 10 new tests in `test_pipeline_sse_new_stages.py` — all pass
- Updated `test_pipeline_observability.py` stage count (7 → 9) — all pass
- Full suite: 1048 pass, 0 fail (1 pre-existing docling storage test excluded)

### Validation
- Ruff lint: PASS
- Frontend tsc --noEmit: PASS
- Frontend npm run build: PASS
