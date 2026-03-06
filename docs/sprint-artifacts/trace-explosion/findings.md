# Findings: Langfuse Trace Explosion

## Symptom
47.98K Langfuse traces generated for a single ACM extraction run.

## Evidence Gathered (Confirmed by Langfuse API query)

### Actual trace names in Langfuse (from API subagent)
- ~24,000 traces: "Pydantic **PdfTextCell** validate_python succeeded"
- ~24,000 traces: "Pydantic **BoundingRectangle** validate_python succeeded"
- Total in DB: 81,912 traces from a single extraction session (2026-03-06 ~14:47 UTC)
- Each trace: 1 span, 0.001ms latency — purely Logfire instrumentation overhead
- Source: **Docling PDF parser** — PdfTextCell = 1 per character in PDF
  (~1,200 chars/page × 20 pages = 24K cells × 2 models = 48K traces)

### .env state at time of explosion
```
LOGFIRE_ENABLED=true          ← user had enabled this
LANGFUSE_ENABLED=true
LANGCHAIN_TRACING_V2=true     ← LangSmith also active
```

### Root cause: logfire_config.py line 63
```python
logfire.instrument_pydantic()   # instruments ALL Pydantic models, record="all" default
```

This patches every Pydantic BaseModel's `model_validate()` / `__init__` to emit a
Logfire OTel span. Spans are exported to Langfuse via `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`.

### Why each validation = its own Langfuse trace
Logfire generates its own `trace_id` per call context (asyncio task/thread).
Each validation in a different async context = different trace_id = different Langfuse trace.
The Langfuse SDK's CallbackHandler traces have their OWN trace_id (Langfuse SDK namespace).
There is NO automatic bridge between Logfire OTel trace_id and Langfuse SDK traceId.

### Scale of the problem
ACM extraction validates:
- BuildingRoomContext per chunk (many chunks)
- ACMExtractionRecord per extracted item
- ACMExtractionResult (container)
- ACMItemExtractionResult (V3 schema)
- Many nested Pydantic models
- Plus all LangChain/LangGraph internal Pydantic models (ChatOllama config, etc.)
~48K validations for a typical multi-page document.

## What Logfire instrument_pydantic() actually does
- Patches `BaseModel.__init__`, `model_validate`, `model_validate_json`
- Creates a span for EVERY call, including successful ones (record="all")
- Span has no parent unless called inside an explicit logfire.span() context
- Async LangGraph nodes each run in their own asyncio task = separate trace_id

## Why OTel + Langfuse SDK can't correlate automatically
- Langfuse SDK (CallbackHandler) uses Langfuse's own trace_id system
- OTel uses the W3C TraceContext spec (traceparent header)
- These are different systems — correlation requires explicit propagation
- Langfuse v3 supports OTel natively but the CallbackHandler doesn't propagate
  W3C trace context to child operations

## Fix Options Evaluated

| Option | Pros | Cons |
|--------|------|------|
| Remove `instrument_pydantic()` | Eliminates explosion, keeps Logfire configured | Loses blanket validation tracing |
| `instrument_pydantic(record="failure")` | Only fails logged | Still creates top-level traces per failure, not nested |
| `LOGFIRE_ENABLED=false` | Simple | Removes Logfire entirely |
| Propagate OTel context from Langfuse SDK | Proper integration | Major refactor, Langfuse SDK doesn't expose trace_id as OTel context |

**Chosen: Remove `instrument_pydantic()`. Keep Logfire for future explicit spans.**
