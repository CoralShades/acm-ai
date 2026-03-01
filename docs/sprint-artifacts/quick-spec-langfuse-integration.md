# Quick Spec: Langfuse Integration

## Objective

Add opt-in Langfuse tracing for ACM extraction LangGraph runs and related command invocations, while preserving existing PipelineLogger + AG-UI behavior and avoiding extraction regressions.

## Scope

- Create `open_notebook/observability/langfuse_config.py` for:
  - `LANGFUSE_ENABLED` gate
  - handler factory
  - metadata builder (source/model/pipeline fields)
  - safe flush
- Add `open_notebook/observability/langfuse_bridge.py` to forward pipeline stage events as LangChain custom events.
- Wire Langfuse callback + metadata into graph invocation sites:
  - `open_notebook/graphs/acm_extraction.py`
  - `commands/source_commands.py`
- Pass LangGraph `RunnableConfig` through orchestrator nested model calls where available (`open_notebook/extractors/orchestrator.py`).
- Add Langfuse env vars to `.env.example`.
- Add benchmark dataset bootstrap script:
  - `scripts/observability/setup_langfuse_datasets.py`

## Non-Goals

- No modifications to extraction prompts, schemas, or decision logic.
- No hard requirement for Langfuse cloud (self-host URL supported via env).

## Design Decisions

1. **Opt-in only:** tracing activates only when `LANGFUSE_ENABLED=true` and keys are present.
2. **No callback replacement:** Langfuse is appended to callback lists.
3. **Metadata-first:** include source/model/pipeline context using runnable metadata and Langfuse-specific metadata keys.
4. **Failure isolation:** any Langfuse init/flush/dispatch error is non-fatal and never blocks extraction.

## Trace Metadata Contract

- `source_id`
- `document_type` (default `unknown`)
- `extraction_model`
- `pipeline_version` (default `E26+`)
- `docling_enabled`
- `command_id` (when available)
- Langfuse callback attributes via metadata:
  - `langfuse_session_id`
  - `langfuse_user_id`
  - `langfuse_tags`

## Benchmark Dataset Plan

Datasets created in Langfuse:
- `broadmeadows-31`
- `alexander-43`

Each dataset stores one benchmark item with:
- `input.source_pdf_path`
- `expected_output.records` (CSV rows)
- `expected_output.record_count`

## Verification Plan

- `LANGFUSE_ENABLED=false`: extraction behavior unchanged.
- `LANGFUSE_ENABLED=true`: traces are emitted and flushed.
- Orchestrator path still runs parallel building extraction without regression.
- `uv run ruff check .` passes.
- `uv run pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py` passes.
