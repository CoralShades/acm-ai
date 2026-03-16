---
paths:
  - "open_notebook/observability/**/*"
  - "scripts/observability/**/*"
  - "scripts/dump_state_json.py"
  - "scripts/generate_model_diagrams.py"
---

# Observability Operations Rules

## 1. Non-Fatal Tracing

ALL tracing code MUST be wrapped in try/except. Tracing must NEVER break extraction or any other app functionality. Pattern:

```python
try:
    dispatch_custom_event(...)
except Exception as exc:
    logger.debug("Tracing skipped: {}", str(exc))
```

## 2. instrument_pydantic() Restriction

NEVER call `logfire.instrument_pydantic()` without `include={...}`. Blanket instrumentation causes ~48K traces per extraction run (Docling creates 1 PdfTextCell per PDF character).

Safe set:
```python
logfire.instrument_pydantic(
    include={
        "ACMExtractionRecord",
        "BuildingRoomContext",
        "ACMItemRecord",
        "ACMExtractionResult",
        "ACMItemExtractionResult",
        "NormalizedExtractionResult",
    }
)
```

## 3. langfuse_tracing() Required for New Endpoints

New FastAPI router endpoints that invoke LangGraph graphs MUST use the `langfuse_tracing()` context manager pattern:

```python
with langfuse_tracing("graph_name", source_id=source_id) as (cb, meta):
    config = merge_langfuse_into_config(base_config, cb, meta)
    result = await graph.ainvoke(input_state, config=config)
```

## 4. Callback Placement

Callbacks belong at the **invocation site** (routers, commands), NEVER inside graph node functions. LangGraph propagates callbacks automatically via config.

## 5. No Modification of Pre-Existing Wiring

Do NOT modify Langfuse wiring in:
- `open_notebook/graphs/acm_extraction.py`
- `commands/source_commands.py`

These have working, tested integrations.

## 6. OTel Protocol

Use `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` (traces-specific, OTLP/HTTP). Do NOT use the generic `OTEL_EXPORTER_OTLP_ENDPOINT` or gRPC variants. Langfuse OTel endpoint only accepts traces, not metrics.

## 7. Environment Variable Conventions

All observability features are opt-in:
- `LANGFUSE_ENABLED=true` — Langfuse tracing
- `LOGFIRE_ENABLED=true` — Logfire -> Langfuse OTel bridge
- `LANGCHAIN_TRACING_V2=true` — LangSmith auto-tracing

Never default these to `true`. App must work with all disabled.
