# Task Plan: Fix Langfuse Trace Explosion

## Problem
47.98K Langfuse traces generated for 1 extraction run.

## Root Cause (Confirmed)
`logfire.instrument_pydantic()` in `logfire_config.py:63` creates an OTel span for
EVERY Pydantic model_validate() call across the codebase. Each span arrives at
Langfuse's OTel endpoint without a parent trace context, so each becomes its own
top-level Langfuse trace. During ACM extraction: ~48K field validations = ~48K traces.

**Key facts:**
- OTel spans from Logfire and Langfuse SDK traces are separate namespaces
- No automatic correlation between Logfire trace_id and Langfuse SDK traceId
- `instrument_pydantic(record="all")` = default = every success AND failure
- `LOGFIRE_ENABLED=true` + `LANGCHAIN_TRACING_V2=true` + `LANGFUSE_ENABLED=true` = 3 tracers active

## Tasks

- [x] Identify root cause (logfire.instrument_pydantic() blanket instrumentation)
- [x] Fix logfire_config.py: remove instrument_pydantic() — commit 27bd2060
- [x] Set LOGFIRE_ENABLED=false as default in .env (opt-in only)
- [x] Commit and push fix
- [x] Update observability.md to document the trace explosion risk and selective instrumentation workaround
- [ ] Verify Langfuse trace count drops to normal after restart

## Decision: Which Fix?

**Chosen approach: Remove `instrument_pydantic()` entirely.**

Rationale:
- Even with `record="failure"`, failures still become top-level Langfuse traces
  with no parent context — not useful as standalone traces
- Explicit `logfire.span()` / `@logfire.instrument` decorators are more targeted
  and can be added where genuinely needed (e.g., around ACM schema parsing)
- Keeps Logfire configured for future explicit instrumentation
- Eliminates the explosion with zero loss of currently-used functionality
