# MCS5: Format-Agnostic Prompts — Findings

## Architecture Decisions

### detected_format source
- `document_metadata.format_name` is set by format detectors in the pipeline
- `InferredSchema` doesn't yet carry `detected_format` — needs a new field
- Schema inference node already reads `format_name` from `document_metadata` for its LLM prompt

### Prompt rendering chain
- `building_inventory.jinja`: Rendered in `building_inventory.py:compile_building_inventory()` with `data=document_metadata`
- `v3_building_extraction.jinja`: Rendered in `orchestrator.py:_v3_extract_building()` with `data={"building_context": ..., "picklists": ...}`
- `row_extraction.jinja`: Rendered in `row_extractor.py:_render_system_prompt()` with `data={}`

### extraction_fields design
- Current: 13 hardcoded fields in `ACMItemRow` schema, matched 1:1 in `row_extraction.jinja`
- Target: Dynamic field list from `InferredSchema.column_mapping` values, falling back to default 13
- The Jinja template shows field descriptions to the LLM; the Pydantic schema (`ACMItemRow`) remains fixed
- Dynamic fields = *which fields to emphasize in the prompt*, not changing the output schema

### Format values
- `"standard"` — DET coded building IDs (B001, D01)
- `"ara"` — ARA text headers ("Building Name: ...")
- `"pipe_table"` — Greencap/Clutch pipe-delimited tables
- `"unknown"` or `None` — fallback, show all guidance
