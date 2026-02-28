# Findings — E27-S2: SSE/AG-UI Pipeline Visibility

## Backend Architecture
- StageId enum: UPPERCASE values (STRUCTURE, PREFLIGHT, ORCHESTRATOR, EXTRACT, VALIDATE, CORRECT, STORE)
- STAGE_METADATA: maps StageId → {name, description, log_prefix}
- PipelineLogger constructor: (source_id, total_pages=0, command_id=None)
- AGUIEventEmitter: step_name strings in emit_step_started/emit_step_finished
- Graph order: extract_metadata → structure → inventory → tag_pages → orchestrate/prepare → extract → validate → correct ↔ validate → deduplicate → recover_no_access → save

## Docling runs OUTSIDE extraction graph (source_commands.py)
## recover_no_access_node runs INSIDE graph, has state access
